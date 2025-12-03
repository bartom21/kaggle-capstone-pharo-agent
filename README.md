# Ailan: The Pharo Smalltalk Agent

> **Google + Kaggle Agentic AI Course - Capstone Project**

**Ailan** combines "AI" and "Alan"—honoring **Alan Kay**, the visionary creator of Smalltalk. Just as Kay pioneered object-oriented programming and dynamic environments, Ailan brings the power of modern AI agents to the Smalltalk ecosystem.

## The Problem: Legacy Systems Left Behind in the AI Revolution

Modern developers working with languages like Python, JavaScript, or TypeScript enjoy integrated AI assistants—Cursor, Windsurf, GitHub Copilot—that dramatically boost productivity. These tools don't just autocomplete; they refactor, generate tests, and even deploy code. Meanwhile, **legacy system developers are stuck in the past**, working without any AI assistance in their IDEs.

This productivity gap is real and growing. Teams maintaining legacy systems are becoming less productive relative to their modern counterparts, and engineers on these teams risk being left behind professionally as the AI revolution accelerates.

### A Real-World Problem

I face this issue firsthand as a Smalltalk developer at **JPMorgan Chase**, working on **Kapital**—a trade and risk financial management system built on VisualWorks Smalltalk. While my teammates supporting other applications leverage agentic AI capabilities daily, my team has zero AI integration. We can't use AI tools simply because our environment doesn't support them.

This isn't a niche problem. Countless enterprises still run critical systems on Smalltalk, COBOL, and other legacy platforms. The companies depend on these systems, but the developers maintaining them are starved of the tools that define modern software engineering.

##[Full Pitch Presentation](https://www.canva.com/design/DAG6Ty6aSSE/cto48ZDdru_G9OWIezixIg/edit?utm_content=DAG6Ty6aSSE&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)

### Why the Enterprise Agents Track?

This solution addresses a real enterprise challenge: the productivity gap in large organizations running legacy systems. Enterprise agents enable the complex, multi-step workflows needed to safely refactor mission-critical code—bringing AI capabilities to developers and systems that need them most.

## The Solution: Bringing Agentic AI to Legacy Environments

This project **bridges the gap** by embedding agentic AI capabilities directly into the Smalltalk environment. Instead of hoping legacy IDEs will eventually support AI (they won't), we bring AI to where the developers work.

### Why Agents?

Simple autocomplete isn't enough for legacy codebases—you need context-aware systems that can:
- **Understand domain-specific patterns** (e.g., Smalltalk's message-passing paradigms)
- **Perform multi-step workflows** (review → refactor → validate → deploy)
- **Integrate seamlessly** with existing development workflows
- **Ensure quality** through validation loops before releasing changes

Agentic systems excel at exactly this: orchestrating specialized AI agents to tackle complex, multi-step tasks autonomously.

### The Core Innovation

This project integrates an **agentic refactoring system** directly into **Pharo Smalltalk** via a menu tool. Developers can:

1. Right-click a method in Pharo
2. Request a refactor from the agentic system
3. The multi-agent pipeline reviews, refactors, validates, and pushes code directly into the Pharo image

No context switching. No manual copying. The AI works **inside** the legacy environment.

This was made possible by building on the [Pharo Smalltalk Interop MCP Server](https://github.com/mumez/pharo-smalltalk-interop-mcp-server) by mumez, which enables communication between the agentic system and the Pharo environment.

### Impact

By bringing agentic capabilities to Smalltalk, this project:
- **Levels the playing field** for legacy developers
- **Increases productivity** in maintaining critical enterprise systems
- **Demonstrates a blueprint** for integrating AI into other legacy environments
- **Preserves career viability** for developers in legacy ecosystems

---

## Technical Overview

A production-ready FastAPI application that provides AI-powered code review and refactoring for Pharo Smalltalk methods using Google's ADK multi-agent system.

## Features

- **Automated Code Review**: Analyzes Pharo methods for OOP best practices violations
- **Intelligent Refactoring**: Generates improved code addressing identified issues
- **Syntax Validation**: Validates refactored code before deployment
- **Iterative Refinement**: Automatically fixes syntax errors through validation loops
- **Safe Deployment**: Compiles validated code directly into Pharo image
- **RESTful API**: Clean, well-documented API endpoints
- **Production Ready**: Includes logging, error handling, and health checks
- **Concurrency Control**: Lock-based protection for single MCP stdio connection

## Architecture

The application follows FastAPI best practices with a clean separation of concerns:

```
app/
├── __init__.py
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration management (Pydantic Settings)
├── models.py              # Request/response schemas (Pydantic models)
├── exceptions.py          # Custom exceptions and error handlers
├── logging_config.py      # Logging configuration
├── routers/
│   ├── __init__.py
│   ├── refactor.py        # Refactoring endpoint
│   └── health.py          # Health check endpoint
└── services/
    ├── __init__.py
    └── agent_service.py   # Agent pipeline business logic
```

## Multi-Agent Pipeline

The refactoring pipeline consists of 5 specialized agents working in sequence:

```
┌─────────────────────────────────────────────────────────────────┐
│                     AGENTIC SYSTEM FLOW                         │
└─────────────────────────────────────────────────────────────────┘

Input: { class_name, method_name }
   │
   ▼
┌──────────────────────────────────────────────────────────────┐
│  1. REVIEWER AGENT                                           │
│  Role: Senior code reviewer                                  │
│  • Retrieves method from Pharo via MCP tools                 │
│  • Analyzes OOP violations (SRP, Encapsulation, etc.)        │
│  • Identifies best practice issues                           │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼ Output: { code_review }
┌──────────────────────────────────────────────────────────────┐
│  2. INITIAL WRITER AGENT                                     │
│  Role: Code generator                                        │
│  • Reads review feedback                                     │
│  • Generates refactored Smalltalk code                       │
│  • Addresses all identified issues                           │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼ Output: { refactored_code }
┌──────────────────────────────────────────────────────────────┐
│  3. VALIDATION LOOP (max 3 iterations)                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  3a. VALIDATOR AGENT                                   │ │
│  │  Role: Senior Pharo engineer (strict standards)        │ │
│  │  • Reviews naming conventions                          │ │
│  │  • Enforces OOP principles                             │ │
│  │  • Checks Smalltalk idioms (Tell Don't Ask)            │ │
│  │  • Validates code quality & maintainability            │ │
│  └──────────────────┬─────────────────────────────────────┘ │
│                     │                                        │
│                     ▼ Output: { validation_result }          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  3b. REFINER AGENT                                     │ │
│  │  Role: Code improver                                   │ │
│  │  • If APPROVED → exit_validation_loop()                │ │
│  │  • If NEEDS IMPROVEMENT → refine code → iterate       │ │
│  └──────────────────┬─────────────────────────────────────┘ │
│                     │                                        │
│                     └──────┐ Loop until approved             │
│                            │ or max iterations               │
└────────────────────────────┼────────────────────────────────┘
                             │
                             ▼ Final: { refactored_code, validation_result }
┌──────────────────────────────────────────────────────────────┐
│  4. RELEASE AGENT                                            │
│  Role: Code deployer                                         │
│  • Compiles code into Pharo image via MCP tools              │
│  • Updates method in live environment                        │
│  • Handles compilation errors                               │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
Final Output: {
  code_review,
  refactored_code,
  validation_result,
  release_status
}
```

### Agent Roles Summary

1. **ReviewerAgent**: Analyzes code for OOP violations and best practice issues
2. **InitialWriterAgent**: Generates refactored code based on review feedback
3. **ValidationLoop**: (LoopAgent with max 3 iterations)
   - **ValidatorAgent**: Senior Pharo engineer reviewing code quality with strict standards
   - **RefinerAgent**: Addresses review feedback and improves code quality
4. **ReleaseAgent**: Compiles validated code to Pharo image

## ⚠️ Important: Concurrency Control

**This application uses a LOCK to protect the MCP stdio connection.**

The MCP toolset communicates with the Pharo server via a **single stdio pipe**. Multiple concurrent requests would corrupt this connection. Therefore:

- ✅ Only **ONE request** processes at a time
- ✅ The `AgentService` uses `asyncio.Lock()` to serialize access
- ✅ Concurrent requests receive **HTTP 503 (Service Unavailable)**
- ✅ Clients should implement retry logic with exponential backoff

**Why the lock?**
```python
# Without lock: Multiple requests → Single stdio pipe → Corruption ❌
# With lock: Queue requests → One at a time → Safe ✅
async with self._lock:
    # Only one agent pipeline runs at a time
    result = await agent_service.refactor_method(...)
```

## How to Reproduce This Project

This guide walks you through setting up the complete agentic refactoring system from scratch.

### Prerequisites

- **Pharo Smalltalk** (version 11 or later recommended)
- **Python 3.8+**
- **Node.js and npm** (for running the MCP server)
- **Google AI API Key** ([Get one here](https://aistudio.google.com/apikey))
- **Git**

---

### Step 1: Set Up Pharo Smalltalk Interop Server

The Pharo Interop Server exposes Smalltalk code manipulation capabilities via HTTP endpoints.

1. **Open a Pharo image** (if you don't have one, download from [pharo.org](https://pharo.org/download))

2. **Clone the PharoSmalltalkInteropServer** repository:
   ```bash
   git clone https://github.com/bartom21/PharoSmalltalkInteropServer
   ```
   > **Credits:** Forked from [mumez/PharoSmalltalkInteropServer](https://github.com/mumez/PharoSmalltalkInteropServer)

3. **Load the server into your Pharo image:**
   - Open the Pharo Playground
   - Execute the installation script from the repository's README
   - Start the HTTP server (typically runs on `http://localhost:8086`)

4. **Verify the server is running:**
   ```bash
   curl http://localhost:8086/health
   ```

---

### Step 2: Set Up the MCP Server

The MCP (Model Context Protocol) server bridges communication between the agentic system and Pharo.

1. **Clone the MCP server** repository:
   ```bash
   git clone https://github.com/bartom21/pharo-smalltalk-interop-mcp-server
   cd pharo-smalltalk-interop-mcp-server
   ```
   > **Credits:** Forked from [mumez/pharo-smalltalk-interop-mcp-server](https://github.com/mumez/pharo-smalltalk-interop-mcp-server)

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure the MCP server:**
   - Ensure it points to your Pharo Interop Server (default: `http://localhost:8086`)
   - Follow configuration instructions in the repository's README

4. **The MCP server will be invoked automatically** by the FastAPI application via stdio communication (no need to run it manually)

---

### Step 3: Install the Pharo Client Menu Extension

The Ailan-Pharo-Client adds a convenient menu option in Pharo to send refactor requests directly from the IDE.

1. **Clone the Ailan-Pharo-Client** repository:
   ```bash
   git clone https://github.com/bartom21/Ailan-Pharo-Client
   ```

2. **Load the packages into your Pharo image:**
   - Open the Pharo Iceberg tool (Git integration)
   - Add the cloned repository
   - Load the packages into your image

3. **Verify installation:**
   - Right-click on any method in the Pharo System Browser
   - You should see a new menu option for sending refactor requests to the agent system

---

### Step 4: Set Up and Run the FastAPI Agent Service

This is the core agentic system that orchestrates code review, refactoring, and deployment.

1. **Clone this repository:**
   ```bash
   git clone <this-repository-url>
   cd kaggle-capstone-pharo-agent
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create environment configuration:**
   ```bash
   cp .env.example .env
   ```

4. **Edit `.env` and configure:**
   ```bash
   GOOGLE_API_KEY=your_actual_api_key_here
   PHARO_SERVER_URL=http://localhost:8086
   ```

5. **Run the FastAPI server:**
   ```bash
   # Development mode with auto-reload
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

   # Or using the convenience script
   python run.py --dev
   ```

6. **Verify the API is running:**
   ```bash
   curl http://localhost:8000/health
   ```

   You should see:
   ```json
   {
     "status": "healthy",
     "version": "1.0.0",
     "app_name": "Pharo Reviewer Agent API"
   }
   ```

7. **Access the API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

---

### Step 5: Test the Complete System

Now everything is connected! Let's test the end-to-end workflow.

#### Option A: Test from Pharo (Recommended)

1. Open the Pharo System Browser
2. Navigate to any class method
3. Right-click on the method
4. Select the refactor option from the Ailan menu
5. Wait for the agentic system to process
6. The refactored code will be automatically compiled into your image

#### Option B: Test via API

```bash
curl -X POST "http://localhost:8000/api/v1/refactor" \
  -H "Content-Type: application/json" \
  -d '{
    "refactor_request": {
      "class_name": "YourClassName",
      "method_name": "yourMethodName"
    }
  }'
```

---

### Architecture Overview

Once everything is running, here's how the components interact:

```
┌─────────────────────┐
│  Pharo IDE          │
│  (with Ailan menu)  │
└──────────┬──────────┘
           │ HTTP Request
           ▼
┌─────────────────────────────┐
│  FastAPI Agent Service      │
│  (Multi-agent pipeline)     │
└──────────┬──────────────────┘
           │ stdio
           ▼
┌─────────────────────────────┐
│  MCP Server                 │
│  (Protocol translation)     │
└──────────┬──────────────────┘
           │ HTTP
           ▼
┌─────────────────────────────┐
│  Pharo Interop Server       │
│  (Code manipulation)        │
└─────────────────────────────┘
```

---

### Troubleshooting

**Issue: MCP server connection fails**
- Ensure Pharo Interop Server is running on port 8086
- Check the MCP server configuration points to the correct URL

**Issue: 503 Service Unavailable**
- The system processes one request at a time due to stdio limitations
- Wait for the current request to complete or implement retry logic (see API Usage section)

**Issue: Method not found in Pharo**
- Verify the class and method names are correct
- Ensure the method exists in your Pharo image

**Issue: Google API errors**
- Verify your `GOOGLE_API_KEY` in `.env` is valid
- Check you haven't exceeded API rate limits

---

## Running the Application

### Development Mode

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the convenience script
python run.py --dev
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Usage

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "app_name": "Pharo Reviewer Agent API"
}
```

### Refactor Method

**Endpoint:** `POST /api/v1/refactor`

**Important:** The request body must be wrapped in a `refactor_request` key:

```bash
curl -X POST "http://localhost:8000/api/v1/refactor" \
  -H "Content-Type: application/json" \
  -d '{
    "refactor_request": {
      "class_name": "Calculator",
      "method_name": "sum:with:"
    }
  }'
```

**Response (Success):**
```json
{
  "success": true,
  "class_name": "Calculator",
  "method_name": "sum:with:",
  "result": {
    "code_review": "...",
    "refactored_code": "...",
    "validation_result": "APPROVED",
    "release_status": "RELEASED: sum:with:"
  }
}
```

**Response (Busy - HTTP 503):**
```json
{
  "detail": "Agent is busy processing another request. Please try again later."
}
```

### Python Client with Retry Logic

Since the API can only process one request at a time, implement retry logic:

```python
import requests
import time

def refactor_with_retry(class_name: str, method_name: str, max_retries: int = 5):
    """Refactor with exponential backoff for 503 responses"""
    url = "http://localhost:8000/api/v1/refactor"
    payload = {
        "refactor_request": {
            "class_name": class_name,
            "method_name": method_name
        }
    }

    for attempt in range(max_retries):
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 503:
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"Agent busy, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_time)
        else:
            response.raise_for_status()

    raise Exception(f"Failed after {max_retries} retries")

# Usage
result = refactor_with_retry("Calculator", "add:to:")
if result["success"]:
    print(f"✅ Refactoring successful!")
    print(f"Status: {result['result']['release_status']}")
else:
    print(f"❌ Error: {result['error']}")
```

## Best Practices Implemented

✅ **Dependency Injection**: Using FastAPI's `Depends()` for service injection
✅ **Configuration Management**: Environment-based config with Pydantic Settings
✅ **Request Validation**: Automatic validation with Pydantic models
✅ **Error Handling**: Custom exceptions with proper HTTP status codes
✅ **Logging**: Structured logging to console and file
✅ **API Documentation**: Auto-generated OpenAPI/Swagger docs
✅ **Type Safety**: Full type hints throughout codebase
✅ **Separation of Concerns**: Clean architecture with routers/services/models
✅ **CORS Support**: Configurable CORS middleware
✅ **Health Checks**: Standard health endpoint for monitoring
✅ **Concurrency Control**: Lock-based protection for shared resources
