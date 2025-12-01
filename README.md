# Pharo Reviewer Agent API

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

1. **ReviewerAgent**: Analyzes code for OOP violations and best practice issues
2. **InitialWriterAgent**: Generates refactored code based on review feedback
3. **ValidationLoop**: (LoopAgent with max 3 iterations)
   - **ValidatorAgent**: Senior Pharo engineer reviewing code quality with strict standards
     - Reviews naming conventions (rejects generic names like a, b, temp)
     - Enforces OOP principles (SRP, Encapsulation, Polymorphism)
     - Checks Smalltalk idioms (Tell Don't Ask, proper message sending)
     - Validates code quality, clarity, and maintainability
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

## Setup

### Prerequisites

1. **Pharo Smalltalk** with PharoSmalltalkInteropServer running on port 8086
2. **Python 3.8+**
3. **Google AI API Key**

### Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create `.env` file:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and add your Google API key:
   ```
   GOOGLE_API_KEY=your_actual_api_key
   PHARO_SERVER_URL=http://localhost:8086
   ```

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
