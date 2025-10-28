"""RAG service initialization."""

from src.configs import Settings
from src.rag.retriever.document_retriever import DocumentRetriever
from src.rag.service import RAGService
from tools.database.vector.selector import VectorStoreSelector
from tools.llm.client.selector import LLMClientSelector
from tools.logger import get_logger

logger = get_logger(__name__)


def initialize_rag_service(settings: Settings) -> RAGService:
    """Initialize RAG service from settings.

    Creates a lightweight RAG service with retriever and optional LLM.
    No session memory - agents handle conversation state via LangGraph.

    Args:
        settings: Application settings

    Returns:
        Initialized RAG service
    """
    logger.info("Initializing RAG service...")

    # Create RAG-specific LLM client
    rag_llm_client = LLMClientSelector.create(
        provider=settings.rag.llm.provider,
        proxy_url=settings.llm.proxy_url,
        api_key=settings.api_keys.litellm_proxy_key,
        completion_model=settings.rag.llm.completion_model,
        embedding_model=settings.rag.llm.embedding_model,
        temperature=settings.rag.llm.temperature,
        max_tokens=settings.rag.llm.max_tokens,
    )

    # Create vector store
    vector_store = VectorStoreSelector.create(
        provider=settings.rag.vectordb.provider,
        host=settings.vectordb.qdrant.host,
        port=settings.vectordb.qdrant.port,
        collection_name=settings.vectordb.qdrant.collection_name,
    )

    # Initialize document retriever
    document_retriever = DocumentRetriever(rag_llm_client, vector_store)

    # Create lightweight RAG service (no session memory)
    rag_service = RAGService(
        document_retriever=document_retriever,
        llm_client=rag_llm_client,
    )

    logger.info(f"RAG service initialized (model={settings.rag.llm.completion_model})")
    return rag_service
