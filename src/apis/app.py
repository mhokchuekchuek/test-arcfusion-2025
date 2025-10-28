"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.apis.dependencies.rag import initialize_rag_service
from src.apis.dependencies.agents import initialize_agent_workflow
from src.apis.routes import chat, health, memory
from src.configs import Settings
from tools.database.vector.selector import VectorStoreSelector
from tools.database.memory.selector import MemoryClientSelector
from tools.logger.logger import get_logger, setup_logging

# Setup logging at import time
setup_logging(level="DEBUG", format_type="text")

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown.

    Initialize tools (LLM client, vector store) on startup and store
    them in app.state for dependency injection.
    """
    # Startup - initialize tools
    logger.info("Initializing services...")

    # Load configuration
    settings = Settings()
    app.state.settings = settings

    # Initialize vector store
    app.state.vector_store = VectorStoreSelector.create(
        provider=settings.rag.vectordb.provider,
        host=settings.vectordb.qdrant.host,
        port=settings.vectordb.qdrant.port,
        collection_name=settings.vectordb.qdrant.collection_name,
    )

    # Initialize Redis client for LangGraph checkpointer
    app.state.redis_client = MemoryClientSelector.create(
        provider="redis",  # Use Redis for agent state persistence
        host=settings.memorydb.redis.host,
        port=settings.memorydb.redis.port,
        password=settings.memorydb.redis.password,
        db=settings.memorydb.redis.db,
    )

    # Initialize RAG service (creates own dependencies)
    app.state.rag_service = initialize_rag_service(settings)

    # Initialize agent workflow with Redis client for checkpointer
    app.state.agent_workflow = initialize_agent_workflow(
        settings,
        app.state.rag_service,
        app.state.redis_client
    )

    logger.info("Services initialized successfully")

    yield

    # Shutdown - cleanup
    logger.info("Shutting down services...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    # Load settings
    settings = Settings()

    app = FastAPI(
        title="PDF Chat Agent API",
        description="API for PDF document chat with RAG capabilities",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS from settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(memory.router)

    return app
