"""Agent service layer - encapsulates all agent logic"""
import os
import asyncio
from typing import Any, Optional
from functools import lru_cache

from google.adk.agents import Agent, SequentialAgent, LoopAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext
from mcp import StdioServerParameters

from app.config import Settings


class AgentService:
    """
    Service class for managing the refactoring agent pipeline.

    IMPORTANT: This service uses a singleton MCP toolset with a stdio connection
    to the Pharo server. The lock ensures only one request processes at a time,
    preventing corruption of the shared stdio pipe.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._toolset: Optional[McpToolset] = None
        self._pipeline: Optional[SequentialAgent] = None
        self._lock = asyncio.Lock()  # Protects the single MCP stdio connection

        # Set Google API key from settings
        if settings.google_api_key:
            os.environ['GOOGLE_API_KEY'] = settings.google_api_key

    def _init_toolset(self) -> McpToolset:
        """Initialize the Pharo MCP toolset"""
        if self._toolset is None:
            self._toolset = McpToolset(
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command=self.settings.pharo_mcp_server_command,
                        args=self.settings.pharo_mcp_server_args,
                        env={"PHARO_SERVER_URL": self.settings.pharo_server_url},
                        cwd=self.settings.pharo_mcp_server_cwd
                    ),
                    timeout=self.settings.pharo_mcp_timeout,
                )
            )
        return self._toolset

    @staticmethod
    def save_context(tool_context: ToolContext, class_name: str, method_name: str) -> str:
        """Save the target class and method name to the shared session state"""
        if tool_context and hasattr(tool_context, 'session'):
            tool_context.session.state['class_name'] = class_name
            tool_context.session.state['method_name'] = method_name
            return f"Context saved. Class: {class_name}, Method: {method_name}"
        return "Error: Could not save context (missing session)."

    @staticmethod
    def exit_validation_loop(tool_context: ToolContext) -> dict[str, str]:
        """Signal the parent LoopAgent to stop iterating when code is valid"""
        if tool_context and hasattr(tool_context, 'actions'):
            tool_context.actions.escalate = True
            return {"status": "approved", "message": "Code validated. Exiting validation loop."}
        return {"status": "error", "message": "Failed to exit loop: tool_context missing."}

    @staticmethod
    def generate_compilation_script(class_name: str, code: str) -> str:
        """
        Generate a safe Pharo compilation script using Character cr for newlines.

        Args:
            class_name: The target Pharo class
            code: The raw source code

        Returns:
            A Pharo expression string that compiles the code safely
        """
        if not code:
            return ""

        lines = code.splitlines()
        pharo_lines = [f"'{line.replace("'", "''")}'" for line in lines]
        code_expression = ", Character cr asString, ".join(pharo_lines)
        full_script = f"{class_name} compile: ({code_expression})"

        return full_script

    def _create_reviewer_agent(self, toolset: McpToolset) -> Agent:
        """Create the reviewer agent"""
        return Agent(
            name="ReviewerAgent",
            model=Gemini(model=self.settings.model_id),
            instruction="""You are an expert Smalltalk code reviewer specializing in Pharo Smalltalk.

Your Process:
1. **Save Context**: IMMEDIATELY call `save_context` with the class and method name from the user prompt.
2. **Fetch Code**: Use `get_method_source` to retrieve the method's source code.
3. **Analyze**: Analyze the code for OOP best practices violations.
4. **Report**: Provide a structured review.

Focus your analysis on:
- **Single Responsibility Principle**: Does the method do one thing well?
- **Encapsulation**: Are implementation details exposed?
- **Naming**: Are method and variable names intention-revealing?
- **Method Length**: Is the method too long (>10 lines suggests extraction opportunity)?
- **Coupling**: Does it access too many external objects?
- **Tell, Don't Ask**: Does it interrogate objects instead of telling them what to do?
- **Primitive Obsession**: Should domain concepts be extracted as objects?
- **Feature Envy**: Does the method operate more on another class's data?

Always provide:
- **Severity**: LOW, MEDIUM, or HIGH
- **Issues**: Specific problems found (if any)
- **Suggestions**: Concrete refactoring recommendations (if needed)""",
            tools=[toolset, FunctionTool(self.save_context)],
            output_key="code_review",
        )

    def _create_initial_writer_agent(self) -> Agent:
        """Create the initial writer agent"""
        return Agent(
            name="InitialWriterAgent",
            model=Gemini(model=self.settings.model_id),
            instruction="""You are an expert Smalltalk developer specializing in Pharo Smalltalk.

Based on this code review: {code_review}

Write the refactored Smalltalk code that addresses all the issues mentioned in the review.

CRITICAL: Output ONLY raw Smalltalk code. Do NOT wrap it in markdown code blocks.

WRONG (do not do this):
```smalltalk
methodName
    ^ result
```

CORRECT (do this):
methodName
    ^ result

Requirements:
- Output raw Pharo Smalltalk code only
- NO markdown (no ``` backticks)
- NO explanations or commentary
- Start directly with the method signature
- Use proper Pharo Smalltalk syntax
- Include method comments where appropriate
- Follow all suggestions from the review""",
            output_key="refactored_code",
        )

    def _create_validator_agent(self, toolset: McpToolset) -> Agent:
        """Create the validator agent"""
        return Agent(
            name="ValidatorAgent",
            model=Gemini(model=self.settings.model_id),
            instruction="""You are a Senior Pharo Smalltalk Engineer with deep expertise in OOP best practices. You have exceptionally high standards for code quality.

Refactored code to review: {refactored_code}

Your task is to review this refactored code with strict, uncompromising standards.

Review Criteria (ALL must be met for approval):
- **Meaningful Names**: Variable and parameter names must be intention-revealing (reject generic names like a, b, x, temp, etc.)
- **OOP Principles**: Single Responsibility, Encapsulation, Polymorphism
- **Smalltalk Idioms**: Tell Don't Ask, proper message sending patterns
- **Code Quality**: Clarity, maintainability, proper abstraction
- **Simplicity**: Is this the simplest solution?

Output Format:
- IF the code is excellent and meets ALL criteria above, respond with EXACTLY: "APPROVED"
- IF ANY improvements are needed, respond with: "NEEDS IMPROVEMENT: [specific, actionable feedback on what to change and why]"

Be critical and specific. Do not approve code with poor naming or violations of best practices.""",
            tools=[toolset],
            output_key="validation_result",
        )

    def _create_refiner_agent(self) -> Agent:
        """Create the refiner agent"""
        return Agent(
            name="RefinerAgent",
            model=Gemini(model=self.settings.model_id),
            instruction="""You refine Smalltalk code based on senior engineer review feedback.

Current Code: {refactored_code}
Review Feedback: {validation_result}

Your task:
- IF the validation starts with "APPROVED", you MUST call the `exit_validation_loop` tool immediately. Do not output any code.
- OTHERWISE: Carefully address the feedback and improve the code based on the specific suggestions provided.

When refining:
- Take the reviewer's feedback seriously and implement their suggestions
- Maintain proper Pharo Smalltalk syntax
- Keep the code clean and following OOP best practices

CRITICAL: Output ONLY raw Smalltalk code. Do NOT wrap in markdown code blocks.

WRONG (do not do this):
```smalltalk
methodName
    ^ result
```

CORRECT (do this):
methodName
    ^ result

IMPORTANT:
1. Do NOT include class prefix (Calculator>>). Output ONLY the method code.""",
            output_key="refactored_code",
            tools=[FunctionTool(self.exit_validation_loop)],
        )

    def _create_release_agent(self, toolset: McpToolset) -> Agent:
        """Create the release agent"""
        return Agent(
            name="ReleaseAgent",
            model=Gemini(model=self.settings.model_id),
            instruction="""You are the Release Manager for Pharo Smalltalk.

Your goal is to apply the final refactored code to the image.

Input Context:
1. Class Name: {class_name}  <-- Retrieved directly from session memory
2. Validated Code: {refactored_code}

Your Task:
1. **Generate Script**: Call the `generate_compilation_script` tool with the `class_name` and `refactored_code`.
   - This tool returns a safe, programmatic Pharo expression (e.g., `Class compile: 'line1', Character cr asString, 'line2'`).

2. **Execute**: Use the `eval` tool to execute the **EXACT String** returned by step 1.
   - Do NOT try to modify the script manually.
   - Do NOT wrap it in extra quotes.
   - Pass the script string directly to the `eval` tool.

3. **Output**:
   - If eval returns the method selector (or a success object): Respond "RELEASED: [Method Name]"
   - If eval fails: Respond "RELEASE FAILED: [Error]"
""",
            tools=[toolset, FunctionTool(self.generate_compilation_script)],
            output_key="release_status",
        )

    def _create_pipeline(self) -> SequentialAgent:
        """Create the complete refactoring pipeline"""
        toolset = self._init_toolset()

        reviewer_agent = self._create_reviewer_agent(toolset)
        initial_writer_agent = self._create_initial_writer_agent()
        validator_agent = self._create_validator_agent(toolset)
        refiner_agent = self._create_refiner_agent()
        release_agent = self._create_release_agent(toolset)

        validation_loop = LoopAgent(
            name="ValidationLoop",
            sub_agents=[validator_agent, refiner_agent],
            max_iterations=self.settings.max_validation_iterations,
        )

        return SequentialAgent(
            name="PharoRefactoringPipeline",
            sub_agents=[reviewer_agent, initial_writer_agent, validation_loop, release_agent],
        )

    def get_pipeline(self) -> SequentialAgent:
        """Get or create the refactoring pipeline"""
        if self._pipeline is None:
            self._pipeline = self._create_pipeline()
        return self._pipeline

    async def refactor_method(self, class_name: str, method_name: str) -> dict[str, Any]:
        """
        Run the complete refactoring pipeline with exclusive lock.

        CRITICAL: This method acquires a lock to ensure only ONE request
        processes at a time. This is necessary because the MCP toolset uses
        a single stdio connection to the Pharo server, which cannot handle
        concurrent requests without corruption.

        Args:
            class_name: Name of the Pharo class
            method_name: Name of the method

        Returns:
            Dictionary with refactoring results
        """
        # Acquire lock to prevent concurrent access to MCP stdio connection
        async with self._lock:
            try:
                prompt = f"Review and refactor the method '{method_name}' in class '{class_name}'."
                pipeline = self.get_pipeline()
                runner = InMemoryRunner(agent=pipeline)
                response = await runner.run_debug(prompt)

                return {
                    "success": True,
                    "class_name": class_name,
                    "method_name": method_name,
                    "result": response
                }

            except Exception as e:
                return {
                    "success": False,
                    "class_name": class_name,
                    "method_name": method_name,
                    "error": str(e)
                }

    def is_busy(self) -> bool:
        """
        Check if the service is currently processing a request.

        Returns:
            True if locked (busy), False if available
        """
        return self._lock.locked()


@lru_cache()
def get_agent_service(settings: Settings = None) -> AgentService:
    """Get cached agent service instance"""
    if settings is None:
        from app.config import get_settings
        settings = get_settings()
    return AgentService(settings)
