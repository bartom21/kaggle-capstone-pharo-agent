# Architecture Documentation

## Overview

The Pharo Reviewer Agent API is a multi-agent system designed to automate code review and refactoring for Pharo Smalltalk methods. It leverages Google's ADK (Agent Development Kit) to orchestrate specialized agents that work together to analyze, refactor, validate, and deploy improved code.

## System Architecture

### High-Level Flow

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /api/v1/refactor
       ▼
┌─────────────────────────────────────┐
│      FastAPI Application            │
│  ┌───────────────────────────────┐  │
│  │    RefactorRouter             │  │
│  │  (Concurrency Lock Check)     │  │
│  └───────────┬───────────────────┘  │
│              ▼                       │
│  ┌───────────────────────────────┐  │
│  │     AgentService              │  │
│  │  (Multi-Agent Pipeline)       │  │
│  └───────────┬───────────────────┘  │
└──────────────┼──────────────────────┘
               │
               ▼
┌───────────────────────────────────────┐
│   Pharo MCP Server (stdio)            │
│   - Code retrieval                    │
│   - Syntax validation                 │
│   - Code compilation                  │
└───────────────────────────────────────┘
```

## Multi-Agent Pipeline

The system uses a sequential pipeline of specialized agents, each with a specific responsibility:

### 1. ReviewerAgent

**Role:** Senior code reviewer analyzing for OOP best practices

**Input:**
- `class_name`: The Pharo class containing the method
- `method_name`: The method to review

**Process:**
1. Uses MCP tools to retrieve current method implementation from Pharo
2. Analyzes code against OOP principles:
   - Single Responsibility Principle
   - Encapsulation
   - Polymorphism
   - Tell Don't Ask
   - Proper abstraction
3. Identifies specific issues and violations

**Output:**
- Detailed code review with specific issues identified
- Stored in `code_review` key

### 2. InitialWriterAgent

**Role:** Generates refactored code based on review feedback

**Input:**
- `code_review`: Feedback from ReviewerAgent
- `class_name` and `method_name` for context

**Process:**
1. Reads the review feedback
2. Generates improved Pharo Smalltalk code
3. Addresses all identified issues
4. Follows Smalltalk syntax conventions

**Output:**
- Raw Smalltalk code (no markdown formatting)
- Stored in `refactored_code` key

### 3. ValidationLoop (LoopAgent)

**Role:** Iterative quality assurance and refinement

**Configuration:**
- Maximum iterations: 3 (configurable via `MAX_VALIDATION_ITERATIONS`)
- Loop condition: Exits when RefinerAgent calls `exit_validation_loop` tool

#### 3a. ValidatorAgent

**Role:** Senior Pharo engineer performing comprehensive code review

**Input:**
- `refactored_code`: Code from InitialWriterAgent or RefinerAgent

**Review Criteria (ALL must pass for approval):**

1. **Meaningful Names**
   - Variable and parameter names must be intention-revealing
   - Rejects generic names: `a`, `b`, `x`, `temp`, `val`, `obj`
   - Requires descriptive, domain-specific names

2. **OOP Principles**
   - Single Responsibility Principle (one reason to change)
   - Proper encapsulation (data hiding)
   - Polymorphism where appropriate

3. **Smalltalk Idioms**
   - Tell Don't Ask (object-oriented messaging)
   - Proper message sending patterns
   - Appropriate use of blocks and closures

4. **Code Quality**
   - Clarity and readability
   - Maintainability
   - Proper abstraction level
   - No unnecessary complexity

5. **Simplicity**
   - Is this the simplest solution that could work?
   - No over-engineering

**Output Format:**
- `"APPROVED"` - Code meets ALL criteria (exact match required)
- `"NEEDS IMPROVEMENT: [specific feedback]"` - Any deficiencies found
- Stored in `validation_result` key

**Important Notes:**
- This is NOT just syntax validation
- This is a comprehensive code quality review
- Standards are intentionally strict to ensure high-quality refactoring
- Provides specific, actionable feedback for improvements

#### 3b. RefinerAgent

**Role:** Addresses review feedback and improves code

**Input:**
- `refactored_code`: Current code version
- `validation_result`: Feedback from ValidatorAgent

**Process:**

**Case 1: Code Approved**
- Validation result starts with `"APPROVED"`
- Calls `exit_validation_loop` tool immediately
- No code output

**Case 2: Needs Improvement**
- Validation result starts with `"NEEDS IMPROVEMENT:"`
- Analyzes specific feedback carefully
- Implements suggested improvements
- Maintains proper Pharo Smalltalk syntax
- Follows OOP best practices

**Output:**
- Raw Smalltalk code (no markdown formatting)
- Updates `refactored_code` key for next iteration
- Or exits loop if approved

**Loop Behavior:**
- Iteration 1: Validate → Refine → Validate again
- Iteration 2: Validate → Refine → Validate again
- Iteration 3: Validate → Refine → Final validation
- After 3 iterations, loop exits regardless of approval status

### 4. ReleaseAgent

**Role:** Compiles validated code into Pharo image

**Input:**
- `refactored_code`: Final approved code
- `class_name` and `method_name` for compilation

**Process:**
1. Uses MCP tools to compile code in Pharo
2. Updates the method in the live image
3. Handles compilation errors if any occur

**Output:**
- `"RELEASED: {method_name}"` on success
- Error message on failure
- Stored in `release_status` key

## Configuration

Key configuration parameters (in `app/config.py`):

```python
# Agent Configuration
max_validation_iterations: int = 3  # Validation loop iterations
model_id: str = "gemini-2.0-flash-exp"  # LLM model

# Pharo MCP Server
pharo_mcp_timeout: int = 1200  # 20 minutes (increased for complex operations)
pharo_server_url: str = "http://localhost:8086"
```

### Why 1200 Second Timeout?

The MCP timeout was increased from 30 to 1200 seconds because:
- Agent operations can involve multiple LLM calls
- Complex code analysis and generation takes time
- Multiple validation iterations compound the duration
- Network latency to Pharo server
- Better to allow completion than premature timeout

## Data Flow

```
Input: { class_name, method_name }
  ↓
ReviewerAgent
  ↓
Output: { code_review }
  ↓
InitialWriterAgent
  ↓
Output: { refactored_code }
  ↓
ValidationLoop (max 3 iterations)
  ↓
  ValidatorAgent
    ↓
  Output: { validation_result }
    ↓
  RefinerAgent
    ↓
  Decision:
    - "APPROVED" → exit_validation_loop()
    - "NEEDS IMPROVEMENT" → refactored_code (iterate)
  ↓
ReleaseAgent
  ↓
Final Output: {
  code_review,
  refactored_code,
  validation_result,
  release_status
}
```

## Concurrency Control

### The Problem

The MCP server communicates via a **single stdio pipe**. Multiple concurrent agent pipelines would:
- Interleave stdio messages
- Corrupt the communication protocol
- Cause unpredictable failures

### The Solution

**Lock-based serialization** in `AgentService`:

```python
class AgentService:
    _lock = asyncio.Lock()  # Class-level lock

    async def refactor_method(self, ...):
        if self._lock.locked():
            raise AgentBusyException()

        async with self._lock:
            # Only one pipeline runs at a time
            result = await agent.run(...)
```

**Client Handling:**
- HTTP 503 (Service Unavailable) if locked
- Clients implement exponential backoff retry
- Ensures safe, sequential processing

## Error Handling

### Exception Hierarchy

```python
AgentServiceException (base)
├── AgentBusyException → HTTP 503
├── PharoServerException → HTTP 502
└── ValidationException → HTTP 500
```

### Error Scenarios

1. **Agent Busy**: Another request in progress → 503
2. **MCP Connection Failed**: Pharo server down → 502
3. **Validation Loop Exhausted**: Failed after 3 iterations → 500
4. **Compilation Error**: Pharo compilation failed → 500
5. **Invalid Request**: Missing parameters → 422

## Key Design Decisions

### Why Senior Engineer Persona for Validator?

**Previous Approach:** Simple syntax validation using eval
- Only caught syntax errors
- Allowed poor naming (a, b, temp)
- Missed OOP violations
- Generated low-quality refactorings

**Current Approach:** Comprehensive quality review
- Enforces best practices
- Rejects poor naming
- Validates OOP principles
- Ensures high-quality output

**Trade-off:**
- More iterations needed (uses validation loop)
- Higher LLM costs
- But produces significantly better code

### Why LoopAgent for Validation?

**Alternatives Considered:**
1. Single validation pass → May miss issues, no refinement
2. Manual iteration in service → Complex control flow, harder to maintain
3. Recursive agent calls → Stack depth issues, harder to limit

**LoopAgent Benefits:**
- Built-in iteration limiting (max 3)
- Clean separation of validator and refiner roles
- Automatic state management
- Easy to monitor progress

### Why Separate Validator and Refiner?

**Single Agent Approach:**
- Agent validates its own code → bias
- Harder to enforce strict standards
- Mixed responsibilities

**Separate Agents:**
- Validator: uncompromising standards
- Refiner: implements improvements
- Clear separation of concerns
- Better quality assurance

## Performance Considerations

### Typical Pipeline Duration

- ReviewerAgent: 5-15 seconds
- InitialWriterAgent: 5-10 seconds
- ValidationLoop (1-3 iterations):
  - ValidatorAgent: 3-8 seconds per iteration
  - RefinerAgent: 5-10 seconds per iteration
- ReleaseAgent: 2-5 seconds

**Total:** 20-60 seconds per request (depending on iterations)

### Optimization Opportunities

1. **Parallel Agent Execution** (future)
   - Currently sequential for simplicity
   - Could parallelize independent agents
   - Requires careful state management

2. **Caching** (future)
   - Cache review results for unchanged methods
   - Cache validation results
   - Requires invalidation strategy

3. **Model Selection**
   - Current: `gemini-2.0-flash-exp` (fast, lower cost)
   - Could use Pro models for complex refactorings
   - Configurable per agent type

## Monitoring and Observability

### Logging

Structured logging at key points:
- Request received
- Agent start/completion
- Validation iterations
- Errors and exceptions
- Final results

### Health Checks

`GET /health` endpoint monitors:
- API availability
- Configuration validity
- (Future: MCP connection status)

## Security Considerations

1. **Input Validation**
   - Pydantic models validate all inputs
   - Prevents injection attacks

2. **Resource Limits**
   - Validation loop capped at 3 iterations
   - MCP timeout prevents infinite waits
   - Concurrency lock prevents resource exhaustion

3. **Error Messages**
   - No sensitive information leaked
   - Generic error messages to clients
   - Detailed logs server-side only

## Future Enhancements

### Planned Features

1. **Parallel Validation**
   - Multiple MCP connections
   - Remove global lock
   - Queue-based request handling

2. **Metrics and Analytics**
   - Validation success rates
   - Average iterations needed
   - Common failure patterns
   - Performance metrics

3. **Configurable Quality Standards**
   - Different validator strictness levels
   - Project-specific coding standards
   - Custom validation rules

4. **Batch Processing**
   - Refactor multiple methods at once
   - Class-level refactoring
   - Package-level analysis

5. **Human-in-the-Loop**
   - Approval workflow for releases
   - Manual review before compilation
   - Feedback incorporation

### Research Directions

1. **Self-Improving Agents**
   - Learn from past refactorings
   - Adapt to codebase style
   - Improve validation heuristics

2. **Multi-Model Ensembles**
   - Different models for different agents
   - Consensus-based validation
   - Fallback models for errors

3. **Code Understanding**
   - Cross-method analysis
   - Architectural pattern detection
   - Refactoring suggestions proactively
