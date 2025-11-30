"""Health check endpoint router"""
from fastapi import APIRouter, Depends
from app.models import HealthResponse
from app.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the service is running and healthy"
)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Health check endpoint.

    Returns basic information about the service status.

    Args:
        settings: Injected settings instance

    Returns:
        HealthResponse with service status
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        app_name=settings.app_name
    )
