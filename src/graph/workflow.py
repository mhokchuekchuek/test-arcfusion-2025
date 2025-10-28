"""LangGraph workflow for multi-agent system."""

from typing import Literal, Optional

from langgraph.checkpoint.redis import RedisSaver
from langgraph.graph import END, StateGraph

from src.agents.clarification import ClarificationAgent
from src.agents.orchestrator import MasterOrchestrator
from src.agents.research import ResearchSupervisor
from src.agents.synthesis import AnswerSynthesisAgent
from src.graph.state import AgentState
from tools.logger import get_logger

logger = get_logger(__name__)


class AgentWorkflow:
    """Hierarchical multi-agent workflow using LangGraph.

    Graph structure:
    - Entry: orchestrator (intent classification)
    - Branch 1: clarification → END
    - Branch 2: research → synthesis → END
    """

    def __init__(
        self,
        orchestrator_llm,
        clarification_llm,
        synthesis_llm,
        research_llm,
        research_tools: list,
        redis_client=None,
        langfuse_client: Optional[any] = None,
        agent_configs: Optional[dict] = None,
    ):
        """Initialize agent workflow.

        Args:
            orchestrator_llm: LLM client for orchestrator (orchestrator-dotprompt)
            clarification_llm: LLM client for clarification (clarification-dotprompt)
            synthesis_llm: LLM client for synthesis (synthesis-dotprompt)
            research_llm: LangChain model for research agent (research-dotprompt)
            research_tools: List of tools (PDFRetrievalTool, WebSearchTool)
            redis_client: Optional Redis client for checkpointer persistence
            langfuse_client: Optional Langfuse client for observability
            agent_configs: Optional agent configurations (name + prompt) for each agent
        """
        logger.info("Initializing agent workflow...")

        # Store langfuse client
        self.langfuse_client = langfuse_client

        # Get agent configs or use defaults
        configs = agent_configs or {}

        # Initialize agents with observability and agent configs
        self.orchestrator = MasterOrchestrator(
            orchestrator_llm,
            langfuse_client,
            configs.get("orchestrator", {})
        )
        self.clarification = ClarificationAgent(
            clarification_llm,
            langfuse_client,
            configs.get("clarification", {})
        )
        self.synthesis = AnswerSynthesisAgent(
            synthesis_llm,
            langfuse_client,
            configs.get("synthesis", {})
        )
        self.research = ResearchSupervisor(
            research_llm,
            research_tools,
            langfuse_client,
            configs.get("research", {})
        )

        # Initialize checkpointer if Redis client provided
        self.checkpointer = None
        if redis_client:
            try:
                # Extract underlying Redis client if wrapped in MemoryClient
                raw_redis_client = getattr(redis_client, 'client', redis_client)
                self.checkpointer = RedisSaver(redis_client=raw_redis_client)
                self.checkpointer.setup()
                logger.info("RedisSaver checkpointer initialized and set up")
            except Exception as e:
                logger.warning(f"Failed to initialize RedisSaver: {e}. Proceeding without checkpointer.")

        # Build and compile graph with checkpointer
        self.graph = self._build_graph(checkpointer=self.checkpointer)
        logger.info("Agent workflow initialized successfully")

    def _build_graph(self, checkpointer=None):
        """Build the LangGraph workflow.

        Args:
            checkpointer: Optional RedisSaver checkpointer for persistence

        Returns:
            Compiled LangGraph with checkpointer
        """
        logger.info("Building agent graph...")

        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("orchestrator", self.orchestrator.execute)
        workflow.add_node("clarification", self.clarification.execute)
        workflow.add_node("research", self.research.execute)
        workflow.add_node("synthesis", self.synthesis.execute)

        # Set entry point
        workflow.set_entry_point("orchestrator")

        # Conditional routing from orchestrator
        def route_after_orchestrator(state: AgentState) -> Literal["clarification", "research"]:
            """Route based on orchestrator decision."""
            next_agent = state["next_agent"]
            logger.debug(f"Routing after orchestrator: {next_agent}")
            return next_agent

        workflow.add_conditional_edges(
            "orchestrator",
            route_after_orchestrator,
            {
                "clarification": "clarification",
                "research": "research",
            }
        )

        # Clarification ends (waits for user)
        workflow.add_edge("clarification", END)

        # Research → Synthesis → END
        workflow.add_edge("research", "synthesis")
        workflow.add_edge("synthesis", END)

        # Compile graph with checkpointer
        logger.info("Compiling agent graph with checkpointer...")
        return workflow.compile(checkpointer=checkpointer)

    def invoke(self, state: AgentState, config: dict = None) -> AgentState:
        """Execute the workflow.

        Args:
            state: Initial agent state
            config: Optional config with thread_id for persistence
                    Format: {"configurable": {"thread_id": "session-123"}}

        Returns:
            Final agent state after execution
        """
        logger.info("Invoking agent workflow...")
        result = self.graph.invoke(state, config=config)
        logger.info("Agent workflow completed")
        return result

    def get_thread_state(self, thread_id: str) -> dict:
        """Get current state for a thread.

        Args:
            thread_id: The thread/session ID

        Returns:
            Current state dictionary with messages

        Raises:
            ValueError: If checkpointer is not initialized
        """
        if not self.checkpointer:
            raise ValueError("Checkpointer not initialized. Cannot retrieve thread state.")

        config = {"configurable": {"thread_id": thread_id}}
        state_snapshot = self.graph.get_state(config)
        logger.debug(f"Retrieved state for thread {thread_id}: {len(state_snapshot.values.get('messages', []))} messages")
        return state_snapshot.values

    def get_thread_history(self, thread_id: str) -> list:
        """Get conversation history for a thread.

        Args:
            thread_id: The thread/session ID

        Returns:
            List of checkpoints for the thread

        Raises:
            ValueError: If checkpointer is not initialized
        """
        if not self.checkpointer:
            raise ValueError("Checkpointer not initialized. Cannot retrieve thread history.")

        config = {"configurable": {"thread_id": thread_id}}
        checkpoints = list(self.checkpointer.list(config))
        logger.debug(f"Retrieved {len(checkpoints)} checkpoints for thread {thread_id}")
        return checkpoints

    def delete_thread(self, thread_id: str) -> None:
        """Delete all checkpoints/history for a thread.

        Args:
            thread_id: The thread/session ID to delete

        Raises:
            ValueError: If checkpointer is not initialized
        """
        if not self.checkpointer:
            raise ValueError("Checkpointer not initialized. Cannot delete thread.")

        self.checkpointer.delete_thread(thread_id)
        logger.info(f"Deleted thread: {thread_id}")

    def thread_exists(self, thread_id: str) -> bool:
        """Check if a thread has any checkpoints.

        Args:
            thread_id: The thread/session ID to check

        Returns:
            True if thread exists with checkpoints, False otherwise
        """
        if not self.checkpointer:
            return False

        try:
            checkpoints = self.get_thread_history(thread_id)
            return len(checkpoints) > 0
        except Exception:
            return False
