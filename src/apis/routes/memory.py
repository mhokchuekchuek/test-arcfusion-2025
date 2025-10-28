"""Memory management API endpoints."""

from typing import Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage

from tools.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


# Response Models
class Message(BaseModel):
    """Conversation message model."""

    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp (ISO 8601)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Message metadata")


class SessionHistoryResponse(BaseModel):
    """Session history response model."""

    session_id: str = Field(..., description="Session identifier")
    message_count: int = Field(..., description="Total messages in session")
    messages: list[Message] = Field(..., description="Conversation messages")


class SessionClearedResponse(BaseModel):
    """Session cleared response model."""

    message: str = Field(..., description="Success message")
    session_id: str = Field(..., description="Cleared session identifier")


@router.get("/{session_id}", response_model=SessionHistoryResponse)
async def get_session_history(
    request: Request,
    session_id: str,
) -> SessionHistoryResponse:
    """Get conversation history for a session (debugging).

    Args:
        request: FastAPI request
        session_id: Session identifier

    Returns:
        SessionHistoryResponse with messages

    Raises:
        HTTPException 404: Session not found

    Example:
        ```bash
        curl http://localhost:8000/memory/user-123-abc
        ```
    """
    logger.info(f"Get session history request: session_id={session_id}")

    try:
        # Get agent workflow from app state
        agent_workflow = request.app.state.agent_workflow

        # Check if thread exists
        if not agent_workflow.thread_exists(session_id):
            logger.warning(f"Session not found: {session_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}",
            )

        # Get current state for thread using graph.get_state()
        state = agent_workflow.get_thread_state(session_id)

        # Extract messages from state
        messages = []
        for msg in state.get("messages", []):
            if isinstance(msg, (HumanMessage, AIMessage)):
                role = "user" if isinstance(msg, HumanMessage) else "assistant"
                messages.append({
                    "role": role,
                    "content": msg.content,
                    "timestamp": datetime.now().isoformat(),  # State doesn't store message timestamps
                    "metadata": {}
                })

        response = SessionHistoryResponse(
            session_id=session_id,
            message_count=len(messages),
            messages=[Message(**msg) for msg in messages],
        )

        logger.info(f"Retrieved session history: {len(messages)} messages")
        return response

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to get session history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session history: {str(e)}",
        )


@router.delete("/{session_id}", response_model=SessionClearedResponse)
async def clear_session(
    request: Request,
    session_id: str,
) -> SessionClearedResponse:
    """Clear conversation history for a session.

    Args:
        request: FastAPI request
        session_id: Session identifier

    Returns:
        SessionClearedResponse with success message

    Raises:
        HTTPException 404: Session not found

    Example:
        ```bash
        curl -X DELETE http://localhost:8000/memory/user-123-abc
        ```
    """
    logger.info(f"Clear session request: session_id={session_id}")

    try:
        # Get agent workflow from app state
        agent_workflow = request.app.state.agent_workflow

        # Check if thread exists
        if not agent_workflow.thread_exists(session_id):
            logger.warning(f"Session not found: {session_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}",
            )

        # Delete thread from checkpointer
        agent_workflow.delete_thread(session_id)

        response = SessionClearedResponse(
            message="Session cleared successfully",
            session_id=session_id,
        )

        logger.info(f"Session cleared: {session_id}")
        return response

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to clear session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear session: {str(e)}",
        )
