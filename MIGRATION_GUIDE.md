# Migration Guide: Script to FastAPI

This document explains the conversion from the original script-based agent to a production-ready FastAPI application.

## What Changed?

### 1. **Concurrency Control (CRITICAL)**

**Problem**: The MCP toolset uses a **single stdio connection** to the Pharo server. Multiple concurrent requests would corrupt this connection.

**Solution**: Added `asyncio.Lock()` to serialize access.

```python
# In app/services/agent_service.py
class AgentService:
    def __init__(self, settings: Settings):
        self._lock = asyncio.Lock()  # ⭐ Prevents concurrent access

    async def refactor_method(self, class_name: str, method_name: str):
        async with self._lock:  # ⭐ Only ONE request at a time
            # ... run agent pipeline
```

**Behavior**:
- ✅ First request: Processes normally
- ⚠️ Concurrent requests: Receive HTTP 503 (Service Unavailable)
- 🔄 Clients should implement retry logic with exponential backoff

### 2. **Project Structure**

**Before** (script-based):
```
refactoring_pipeline_with_loop.py    # Everything in one file
```

**After** (FastAPI):
```
app/
├── main.py                 # FastAPI app
├── config.py              # Settings management
├── models.py              # Request/response schemas
├── exceptions.py          # Error handling
├── logging_config.py      # Logging setup
├── routers/
│   ├── refactor.py        # POST /api/v1/refactor
│   └── health.py          # GET /health
└── services/
    └── agent_service.py   # Agent pipeline logic
```

### 3. **Configuration Management**

**Before**:
```python
# Hardcoded in script
MODEL_ID = "gemini-3-pro-preview"
pharo_server_url = os.getenv('PHARO_SERVER_URL', 'http://localhost:8086')
```

**After**:
```python
# app/config.py - Pydantic Settings
class Settings(BaseSettings):
    model_id: str = "gemini-3-pro-preview"
    pharo_server_url: str = "http://localhost:8086"
    # ... all configuration

    class Config:
        env_file = ".env"
```

### 4. **Request/Response Validation**

**Before**:
```python
# Manual input
class_name = input("Enter class name: ")
```

**After**:
```python
# Pydantic models with automatic validation
class RefactorRequest(BaseModel):
    class_name: str = Field(..., min_length=1)
    method_name: str = Field(..., min_length=1)
```

### 5. **Error Handling**

**Before**:
```python
except Exception as e:
    print(f"Error: {e}")
```

**After**:
```python
# Custom exceptions with proper HTTP status codes
class AgentExecutionError(RefactoringError):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)

# FastAPI exception handlers
@app.exception_handler(RefactoringError)
async def refactoring_error_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, ...)
```

### 6. **Logging**

**Before**:
```python
print(f"Processing {class_name}>>{method_name}...")
```

**After**:
```python
# Structured logging to console + file
logger = get_logger(__name__)
logger.info(f"Processing {class_name}>>{method_name}")
# Logs saved to logs/app.log
```

## API Endpoints

### Health Check
```bash
GET /health
```

### Refactor Method (Main Endpoint)
```bash
POST /api/v1/refactor
Content-Type: application/json

{
  "class_name": "Calculator",
  "method_name": "sum:with:"
}
```

**Responses**:
- `200 OK`: Success
- `422 Unprocessable Entity`: Invalid request
- `500 Internal Server Error`: Agent execution failed
- `503 Service Unavailable`: Agent is busy (retry later)

## Running the Application

### Development
```bash
python run.py --dev
# or
uvicorn app.main:app --reload
```

### Production
```bash
python run.py --workers 4
# or
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access Points
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Client Usage

### Simple Request
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/refactor",
    json={"class_name": "Calculator", "method_name": "sum:with:"}
)
result = response.json()
```

### With Retry Logic (Recommended)
```python
# See example_client.py for full implementation
result = refactor_with_retry("Calculator", "sum:with:", max_retries=5)
```

## Key Benefits

1. ✅ **Production Ready**: Proper error handling, logging, health checks
2. ✅ **Type Safe**: Pydantic models ensure data validation
3. ✅ **Scalable**: Clean architecture allows easy extension
4. ✅ **Observable**: Structured logging and health endpoints
5. ✅ **Documented**: Auto-generated OpenAPI docs
6. ✅ **Safe**: Lock-based concurrency control
7. ✅ **Testable**: Services separated from API layer

## Important Notes

### Concurrency Limitation

⚠️ **The API can only process ONE request at a time** due to the single MCP stdio connection.

**Why?**
- MCP toolset → stdio pipe → Pharo server
- Multiple concurrent requests → pipe corruption
- Lock ensures serialized access

**Client Best Practice**:
```python
# Implement exponential backoff for 503 responses
for attempt in range(max_retries):
    response = requests.post(url, json=payload)
    if response.status_code == 503:
        time.sleep(2 ** attempt)  # 1s, 2s, 4s, 8s, 16s
    else:
        break
```

### Singleton Pattern

The `AgentService` is a singleton (cached via `@lru_cache()`), ensuring:
- One MCP toolset instance
- One agent pipeline
- One lock for all requests

```python
@lru_cache()
def get_agent_service(settings: Settings = None) -> AgentService:
    return AgentService(settings)
```

## Migration Checklist

If you're migrating your own script to FastAPI:

- [ ] Extract configuration to Pydantic Settings
- [ ] Create request/response models
- [ ] Move business logic to service layer
- [ ] Add proper error handling
- [ ] Implement structured logging
- [ ] Add health check endpoint
- [ ] **Add lock for shared resources** ⭐
- [ ] Create API documentation
- [ ] Write client examples with retry logic
- [ ] Update deployment scripts

## Questions?

Check the documentation:
- README.md - Full setup and usage guide
- http://localhost:8000/docs - Interactive API docs
- example_client.py - Working client implementation
