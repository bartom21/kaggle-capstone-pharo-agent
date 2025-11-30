"""Refactoring endpoint router"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.models import RefactorRequest, RefactorResponse
from app.services import AgentService, get_agent_service
from app.logging_config import get_logger
from app.exceptions import AgentExecutionError

router = APIRouter(prefix="/api/v1", tags=["refactoring"])
logger = get_logger(__name__)


@router.post(
    "/refactor",
    response_model=RefactorResponse,
    status_code=status.HTTP_200_OK,
    summary="Refactor a Pharo method",
    description="Analyzes and refactors a Pharo Smalltalk method using AI agents",
    responses={
        200: {
            "description": "Refactoring completed successfully",
            "model": RefactorResponse
        },
        422: {
            "description": "Validation error - invalid input"
        },
        500: {
            "description": "Internal server error during refactoring"
        },
        503: {
            "description": "Service unavailable - agent is busy processing another request"
        }
    }
)
async def refactor_method(
    refactor_request: RefactorRequest,
    agent_service: AgentService = Depends(get_agent_service)
) -> RefactorResponse:
    """
    Refactor a Pharo Smalltalk method.

    This endpoint runs a complete AI-powered refactoring pipeline that:
    1. Reviews the method for OOP best practices violations
    2. Generates refactored code addressing identified issues
    3. Validates the refactored code syntax
    4. Iteratively refines the code if validation fails
    5. Releases the final validated code to the Pharo image

    **IMPORTANT**: This endpoint can only process ONE request at a time due to
    the shared MCP stdio connection. If the agent is busy, it returns HTTP 503.

    Args:
        refactor_request: RefactorRequest containing class_name and method_name
        agent_service: Injected agent service instance

    Returns:
        RefactorResponse with refactoring results

    Raises:
        HTTPException: 503 if busy, 500 if refactoring fails
    """
    # Check if agent is already processing a request
    if agent_service.is_busy():
        logger.warning(
            f"Agent busy, rejecting request: {refactor_request.class_name}>>{refactor_request.method_name}"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent is busy processing another request. Please try again later."
        )

    logger.info(
        f"Received refactoring request: {refactor_request.class_name}>>{refactor_request.method_name}"
    )

    try:
        # Execute refactoring pipeline (with internal lock protection)
        result = await agent_service.refactor_method(
            class_name=refactor_request.class_name,
            method_name=refactor_request.method_name
        )

        if not result["success"]:
            logger.error(
                f"Refactoring failed for {refactor_request.class_name}>>{refactor_request.method_name}: "
                f"{result.get('error', 'Unknown error')}"
            )
            raise AgentExecutionError(
                f"Refactoring failed: {result.get('error', 'Unknown error')}"
            )

        logger.info(
            f"Refactoring completed successfully: {refactor_request.class_name}>>{refactor_request.method_name}"
        )

        return RefactorResponse(**result)

    except AgentExecutionError:
        raise
    except Exception as e:
        logger.exception(
            f"Unexpected error during refactoring: {refactor_request.class_name}>>{refactor_request.method_name}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during refactoring: {str(e)}"
        )
