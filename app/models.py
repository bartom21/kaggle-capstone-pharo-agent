"""Pydantic models for request/response validation"""
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator


class RefactorRequest(BaseModel):
    """Request model for refactoring a Pharo method"""

    class_name: str = Field(
        ...,
        description="Name of the Pharo class containing the method",
        min_length=1,
        examples=["Calculator"]
    )
    method_name: str = Field(
        ...,
        description="Name of the method to refactor",
        min_length=1,
        examples=["sum:with:", "add:to:"]
    )

    @field_validator('class_name', 'method_name')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure fields are not just whitespace"""
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "class_name": "Calculator",
                    "method_name": "sum:with:"
                }
            ]
        }
    }


class RefactorResponse(BaseModel):
    """Response model for refactoring operation"""

    success: bool = Field(
        ...,
        description="Whether the refactoring operation completed successfully"
    )
    class_name: str = Field(
        ...,
        description="Name of the class that was refactored"
    )
    method_name: str = Field(
        ...,
        description="Name of the method that was refactored"
    )
    result: Optional[Any] = Field(
        None,
        description="Detailed result from the agent pipeline"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if operation failed"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "class_name": "Calculator",
                    "method_name": "sum:with:",
                    "result": {
                        "code_review": "...",
                        "refactored_code": "...",
                        "release_status": "RELEASED: sum:with:"
                    }
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""

    status: str = Field(
        ...,
        description="Health status of the service"
    )
    version: str = Field(
        ...,
        description="Application version"
    )
    app_name: str = Field(
        ...,
        description="Application name"
    )


class ErrorResponse(BaseModel):
    """Response model for errors"""

    detail: str = Field(
        ...,
        description="Error details"
    )
    status_code: int = Field(
        ...,
        description="HTTP status code"
    )
