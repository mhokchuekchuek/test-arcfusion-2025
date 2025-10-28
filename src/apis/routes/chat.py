"""Chat API endpoints for RAG."""

from typing import Any
import uuid

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

from src.graph.state import create_initial_state
from tools.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request model."""

    message: str = Field(..., min_length=1, description="User question or message")
    session_id: str | None = Field(
        None, description="Session identifier (auto-generated if not provided)"
    )
    top_k: int = Field(
        5, ge=1, le=20, description="Number of document chunks to retrieve"
    )


class Source(BaseModel):
    """Document source model."""

    text: str = Field(..., description="Document text chunk")
    source: str = Field(..., description="Source filename")
    page: int = Field(..., description="Page number")
    score: float = Field(..., description="Relevance score")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ChatResponse(BaseModel):
    """Chat response model."""

    answer: str = Field(..., description="Generated answer")
    sources: list[Source] = Field(..., description="Source documents used")
    session_id: str = Field(..., description="Session identifier")
    message_count: int = Field(..., description="Total messages in session")


@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
    request: Request,
    chat_request: ChatRequest,
) -> ChatResponse:
    """Ask questions using multi-agent workflow with Langfuse tracing.

    Uses hierarchical ReAct architecture with:
    - Master orchestrator for intent classification
    - Clarification agent for vague queries
    - Research agent with PDF + Web search tools (using full RAG service)
    - Answer synthesis agent

    Args:
        request: FastAPI request
        chat_request: Chat request with message, session_id, top_k

    Returns:
        ChatResponse with answer, sources, session info

    Raises:
        HTTPException 400: Invalid request parameters
        HTTPException 404: No documents found in vector database
        HTTPException 500: Generation failed

    Example:
        ```bash
        curl -X POST http://localhost:8000/chat \\
          -H "Content-Type: application/json" \\
          -d '{
            "message": "What is RAG?",
            "session_id": "user-123-abc",
            "top_k": 5
          }'
        ```
    """
    logger.info(
        f"Chat request: message='{chat_request.message[:50]}...', "
        f"session_id={chat_request.session_id}, top_k={chat_request.top_k}"
    )

    try:
        # Get agent workflow from app state
        agent_workflow = request.app.state.agent_workflow

        # Generate session_id if not provided
        session_id = chat_request.session_id or str(uuid.uuid4())

        # Check if this is a continuation of an existing conversation
        if agent_workflow.thread_exists(session_id):
            # Load existing state to preserve clarification_count, last_agent, etc.
            logger.debug(f"Loading existing state for thread {session_id}")
            existing_state = agent_workflow.get_thread_state(session_id)

            # Append new user message to existing messages
            new_message = HumanMessage(content=chat_request.message)
            existing_state["messages"] = list(existing_state["messages"]) + [new_message]

            logger.debug(
                f"Continuing conversation: {len(existing_state['messages'])} total messages, "
                f"clarification_count={existing_state.get('clarification_count', 0)}, "
                f"last_agent={existing_state.get('last_agent')}"
            )

            state_to_invoke = existing_state
        else:
            # New conversation: create initial state
            logger.debug(f"Creating new conversation for thread {session_id}")
            state_to_invoke = create_initial_state(
                messages=[HumanMessage(content=chat_request.message)],
                session_id=session_id
            )

        # Execute workflow with thread_id config for checkpointer
        config = {"configurable": {"thread_id": session_id}}
        final_state = agent_workflow.invoke(state_to_invoke, config=config)

        logger.debug(f"Workflow completed. Final state has {len(final_state['messages'])} messages")
        logger.debug(f"Final answer: {final_state.get('final_answer', 'NO ANSWER')[:100]}...")

        # Extract answer and sources from final state
        answer = final_state.get("final_answer", "No answer generated")

        # For now, return empty sources (we'll extract from context if needed)
        sources = []

        chat_response = ChatResponse(
            answer=answer,
            sources=sources,
            session_id=session_id,
            message_count=len(final_state["messages"]),
        )

        logger.info(
            f"Chat response generated: session={chat_response.session_id}, "
            f"sources={len(chat_response.sources)}, messages={chat_response.message_count}"
        )

        return chat_response

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Chat endpoint failed: {e}", exc_info=True)

        # Check for specific error types
        error_msg = str(e)
        if "no documents" in error_msg.lower() or "empty collection" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No documents found in vector database. Please ingest PDFs first.",
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer: {error_msg}",
        )
