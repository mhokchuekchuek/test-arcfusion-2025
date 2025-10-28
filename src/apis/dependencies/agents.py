"""Agent workflow initialization."""

from typing import Optional

from langchain_openai import ChatOpenAI

from src.agents.tools.pdf_retrieval import PDFRetrievalTool
from src.agents.tools.web_search import WebSearchTool
from src.configs import Settings
from src.graph.workflow import AgentWorkflow
from tools.llm.client.selector import LLMClientSelector
from tools.llm.websearch.tavily.main import TavilyWebSearchClient
from tools.logger import get_logger
from tools.observability.selector import ObservabilitySelector

logger = get_logger(__name__)


def initialize_agent_workflow(settings: Settings, rag_service, redis_client) -> AgentWorkflow:
    """Initialize agent workflow from settings.

    Args:
        settings: Application settings
        rag_service: RAGService instance (for PDF retrieval tool)
        redis_client: Redis client for checkpointer persistence

    Returns:
        Initialized AgentWorkflow
    """
    logger.info("Initializing agent workflow...")

    # Initialize Langfuse observability client (if enabled)
    langfuse_client: Optional[any] = None
    if settings.observability.langfuse.enabled:
        try:
            langfuse_client = ObservabilitySelector.create(
                provider=settings.observability.langfuse.provider,
                public_key=settings.observability.langfuse.public_key,
                secret_key=settings.observability.langfuse.secret_key,
                host=settings.observability.langfuse.host,
            )
            logger.info("Langfuse observability client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Langfuse client: {e}. Continuing without observability.")

    # Create LLM clients for each agent (using config from langgraph.yaml)
    # Force using YAML config - no fallback defaults
    orchestrator_llm = LLMClientSelector.create(
        provider=settings.rag.llm.provider,
        proxy_url=settings.llm.proxy_url,
        api_key=settings.api_keys.litellm_proxy_key,
        completion_model=f"{settings.orchestrator.model}",
        embedding_model=settings.rag.llm.embedding_model,
        temperature=settings.orchestrator.temperature,
        max_tokens=settings.rag.llm.max_tokens,
    )

    clarification_llm = LLMClientSelector.create(
        provider=settings.rag.llm.provider,
        proxy_url=settings.llm.proxy_url,
        api_key=settings.api_keys.litellm_proxy_key,
        completion_model=f"{settings.clarification.model}",
        embedding_model=settings.rag.llm.embedding_model,
        temperature=settings.clarification.temperature,
        max_tokens=settings.rag.llm.max_tokens,
    )

    synthesis_llm = LLMClientSelector.create(
        provider=settings.rag.llm.provider,
        proxy_url=settings.llm.proxy_url,
        api_key=settings.api_keys.litellm_proxy_key,
        completion_model=f"{settings.synthesis.model}",
        embedding_model=settings.rag.llm.embedding_model,
        temperature=settings.synthesis.temperature,
        max_tokens=settings.rag.llm.max_tokens,
    )

    # Create LangChain model for research agent (uses create_agent)
    research_llm = ChatOpenAI(
        model=f"{settings.research.model}",
        openai_api_key=settings.api_keys.litellm_proxy_key,
        openai_api_base=settings.llm.proxy_url,
        temperature=settings.research.temperature,
    )

    # Create tools
    pdf_tool = PDFRetrievalTool(
        rag_service=rag_service,
        session_id="default",  # Will be updated per request
        min_similarity_score=settings.rag.retrieval.min_similarity_score
    )

    tavily_client = TavilyWebSearchClient(
        api_key=settings.api_keys.tavily_api_key
    )
    web_tool = WebSearchTool(
        websearch_client=tavily_client,
        max_results=5
    )

    research_tools = [pdf_tool, web_tool]

    # Prepare agent configs (all config from langgraph.yaml) for each agent
    # Force using YAML config - no fallback defaults
    agent_configs = {
        "orchestrator": {
            "prompt": settings.orchestrator.prompt if hasattr(settings.orchestrator, "prompt") else None,
            "name": settings.orchestrator.name,
            "max_history": settings.orchestrator.max_history,
        },
        "clarification": {
            "prompt": settings.clarification.prompt if hasattr(settings.clarification, "prompt") else None,
            "name": settings.clarification.name,
            "max_history": settings.clarification.max_history,
        },
        "synthesis": {
            "prompt": settings.synthesis.prompt if hasattr(settings.synthesis, "prompt") else None,
            "name": settings.synthesis.name,
            "max_history": settings.synthesis.max_history,
        },
        "research": {
            "prompt": settings.research.prompt if hasattr(settings.research, "prompt") else None,
            "name": settings.research.name,
            "max_history": settings.research.max_history,
            "max_iterations": settings.research.max_iterations,
        },
    }

    # Create workflow with redis_client for checkpointer
    workflow = AgentWorkflow(
        orchestrator_llm=orchestrator_llm,
        clarification_llm=clarification_llm,
        synthesis_llm=synthesis_llm,
        research_llm=research_llm,
        research_tools=research_tools,
        redis_client=redis_client,
        langfuse_client=langfuse_client,
        agent_configs=agent_configs,
    )

    logger.info("Agent workflow initialized successfully")
    return workflow
