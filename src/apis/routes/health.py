"""Health check routes."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    """Root endpoint.

    Returns:
        dict: Welcome message with API info
    """
    return {
        "message": "PDF Chat Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@router.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        dict: Service health status
    """
    return {
        "status": "healthy",
        "service": "pdf-chat-agent",
        "version": "1.0.0"
    }
