"""FastAPI application entry point"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.config import get_settings
from app.logging_config import setup_logging, get_logger
from app.routers import health, refactor
from app.exceptions import (
    RefactoringError,
    refactoring_error_handler,
    validation_exception_handler,
    generic_exception_handler
)

# Initialize settings
settings = get_settings()

# Setup logging
setup_logging(log_level="DEBUG" if settings.debug else "INFO")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Pharo Server URL: {settings.pharo_server_url}")
    logger.info(f"Model ID: {settings.model_id}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    AI-powered Pharo Smalltalk code refactoring service.

    This API provides automated code review and refactoring capabilities for Pharo Smalltalk methods
    using Google's ADK multi-agent system with Gemini models.

    ## Features

    - **Code Review**: Analyzes methods for OOP best practices violations
    - **Automated Refactoring**: Generates improved code addressing identified issues
    - **Syntax Validation**: Validates refactored code before release
    - **Iterative Refinement**: Automatically fixes syntax errors through validation loops
    - **Safe Deployment**: Compiles validated code directly into Pharo image

    ## Workflow

    1. Submit a class name and method name
    2. ReviewerAgent analyzes the code
    3. WriterAgent generates refactored code
    4. ValidationLoop validates and refines the code
    5. ReleaseAgent compiles the final code to the Pharo image
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Register exception handlers
app.add_exception_handler(RefactoringError, refactoring_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include routers
app.include_router(health.router)
app.include_router(refactor.router)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirects to docs"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
