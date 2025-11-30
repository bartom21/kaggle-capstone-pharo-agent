# Pharo Reviewer Agent API - Project Structure

## Clean Production-Ready Structure

```
pharo-reviewer-agent/
├── app/                          # FastAPI application
│   ├── __init__.py
│   ├── main.py                   # Application entry point
│   ├── config.py                 # Settings management
│   ├── models.py                 # Pydantic request/response models
│   ├── exceptions.py             # Custom exceptions & handlers
│   ├── logging_config.py         # Logging configuration
│   ├── routers/                  # API endpoints
│   │   ├── __init__.py
│   │   ├── health.py             # GET /health
│   │   └── refactor.py           # POST /api/v1/refactor
│   └── services/                 # Business logic
│       ├── __init__.py
│       └── agent_service.py      # Multi-agent pipeline
│
├── .env                          # Environment configuration (DO NOT COMMIT)
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── example_client.py             # Example Python client with retry logic
├── MIGRATION_GUIDE.md            # Migration from script to FastAPI
├── README.md                     # Complete documentation
├── requirements.txt              # Python dependencies
└── run.py                        # Convenience server runner
```

## Key Files

### Core Application
- **app/main.py**: FastAPI app with CORS, error handlers, lifespan
- **app/config.py**: Pydantic Settings for configuration
- **app/services/agent_service.py**: Multi-agent pipeline with lock

### API Layer  
- **app/routers/refactor.py**: Main refactoring endpoint
- **app/routers/health.py**: Health check endpoint
- **app/models.py**: Request/response validation

### Utilities
- **run.py**: `python run.py --dev` to start server
- **example_client.py**: Working example with retry logic
- **.env.example**: Template for environment variables

## Architecture

### Multi-Agent Pipeline
1. **ReviewerAgent**: Analyzes code for OOP violations
2. **InitialWriterAgent**: Generates refactored code
3. **ValidationLoop** (max 3 iterations):
   - ValidatorAgent: Validates syntax
   - RefinerAgent: Fixes errors or exits
4. **ReleaseAgent**: Compiles to Pharo image

### Concurrency Control
- **Lock**: `asyncio.Lock()` protects single MCP stdio connection
- **Behavior**: Only ONE request processes at a time
- **503 Response**: Concurrent requests receive "Service Unavailable"
- **Client Retry**: Exponential backoff recommended

### Configuration
- Environment variables via `.env`
- Pydantic Settings for type-safe config
- API key injection for Gemini
