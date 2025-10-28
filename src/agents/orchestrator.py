"""Master Orchestrator for intent classification and routing."""

from typing import Optional
from langchain_core.messages import AIMessage, HumanMessage

from src.agents.base import BaseAgent
from src.graph.state import AgentState
from tools.llm.client.base import BaseLLM
from tools.logger import get_logger

logger = get_logger(__name__)


class MasterOrchestrator(BaseAgent):
    """High-level intent classifier and router.

    Analyzes query clarity and decides whether to:
    1. Ask for clarification (vague/ambiguous queries)
    2. Route to research (clear queries needing information)
    """

    def __init__(
        self,
        llm_client: BaseLLM,
        langfuse_client: Optional[any] = None,
        agent_config: Optional[dict] = None
    ):
        """Initialize orchestrator.

        Args:
            llm_client: LLM client configured with orchestrator-dotprompt model
            langfuse_client: Optional Langfuse client for observability
            agent_config: Optional agent configuration (name, prompt)
        """
        super().__init__("MasterOrchestrator")
        self.llm_client = llm_client
        self.langfuse_client = langfuse_client
        self.agent_config = agent_config or {}
        self.agent_name = self.agent_config.get("name", "orchestrator")
        self.prompt_config = self.agent_config.get("prompt", {})

    def execute(self, state: AgentState) -> AgentState:
        """Analyze query and decide routing with three-layer protection against clarification loops.

        Protection layers:
        1. Counter limit: Max clarifications before forcing research
        2. Pattern detection: Detect AI->Human after clarification agent
        3. LLM decision: Context-aware prompt for intelligent routing

        Args:
            state: Current agent state

        Returns:
            State with next_agent set to "clarification" or "research"
        """
        # Limit message history to prevent token overflow
        max_history = self.agent_config.get("max_history", 10)
        messages = state["messages"][-max_history:] if len(state["messages"]) > max_history else state["messages"]
        logger.debug(f"Processing {len(messages)} messages (max_history={max_history})")

        # ========================================================================
        # LAYER 1: Counter Limit (Emergency Brake)
        # ========================================================================
        max_clarifications = self.agent_config.get("max_clarifications", 2)
        clarification_count = state.get("clarification_count", 0)

        if clarification_count >= max_clarifications:
            logger.warning(
                f"LAYER 1 TRIGGERED: Max clarifications reached "
                f"({clarification_count}/{max_clarifications}) - forcing research to prevent infinite loop"
            )
            state["next_agent"] = "research"
            state["clarification_needed"] = False
            state["clarification_count"] = 0  # Reset counter
            state["iteration"] += 1
            return state

        # ========================================================================
        # LAYER 2: Pattern Detection (Clarification Follow-up)
        # ========================================================================
        # If the last agent was clarification and user is responding,
        # route directly to research (user has provided context)
        if len(messages) >= 2:
            prev_msg = messages[-2]
            current_msg = messages[-1]
            last_agent = state.get("last_agent")

            # Check if:
            # 1. Previous message was from AI (clarification question)
            # 2. Current message is from Human (user response)
            # 3. Last agent was specifically the clarification agent
            if (isinstance(prev_msg, AIMessage) and
                isinstance(current_msg, HumanMessage) and
                last_agent == "clarification"):

                logger.info(
                    f"LAYER 2 TRIGGERED: Clarification follow-up detected "
                    f"(last_agent={last_agent}, pattern=AI->Human) - routing to research"
                )
                state["next_agent"] = "research"
                state["clarification_needed"] = False
                state["clarification_count"] = 0  # Reset since user provided context
                state["iteration"] += 1
                return state

        # ========================================================================
        # LAYER 3: LLM Decision (Context-Aware Routing)
        # ========================================================================
        # Get current query and history
        query = messages[-1].content
        history = self._format_history(messages[:-1])

        logger.info(f"LAYER 3: LLM analyzing query: {query[:100]}...")

        # Prepare prompt variables
        prompt_variables = {
            "query": query,
            "history": history,
        }

        try:
            # Debug: Log Langfuse configuration
            logger.debug(f"Langfuse client available: {self.langfuse_client is not None}")
            logger.debug(f"Prompt config: {self.prompt_config}")

            # Fetch prompt from Langfuse (if available)
            if self.langfuse_client and self.prompt_config.get("provider") == "langfuse":
                try:
                    # Get prompt config
                    prompt_id = self.prompt_config.get("id", "orchestrator_intent")
                    prompt_version = self.prompt_config.get("version")
                    prompt_env = self.prompt_config.get("environment", "dev")

                    logger.info(f"Fetching Langfuse prompt: name={prompt_id}, version={prompt_version}, label={prompt_env}")

                    prompt = self.langfuse_client.get_prompt(
                        name=prompt_id,
                        version=prompt_version,
                        label=prompt_env
                    )
                    logger.info(f"✓ Langfuse prompt fetched successfully")

                    # Compile template with variables
                    compiled_prompt = prompt.compile(**prompt_variables)

                    logger.debug(f"Using compiled prompt from Langfuse")

                    # Generate decision (use agent's configured model, not Langfuse model)
                    decision = self.llm_client.generate(
                        prompt=compiled_prompt
                    )

                    # Trace generation with session_id and configured name
                    session_id = state.get("session_id")
                    self.langfuse_client.trace_generation(
                        name=self.agent_name,
                        input_data=prompt_variables,
                        output=decision,
                        model=self.llm_client.completion_model,
                        metadata={"agent": "MasterOrchestrator"},
                        session_id=session_id
                    )
                    logger.info(f"✓ Langfuse trace recorded (name={self.agent_name}, session={session_id})")
                except Exception as e:
                    logger.error(f"✗ Langfuse prompt fetch FAILED: {type(e).__name__}: {e}", exc_info=True)
                    # Fallback to direct LLM call
                    logger.warning("Falling back to direct LLM call (dotprompt)")
                    decision = self.llm_client.generate(
                        prompt_variables=prompt_variables
                    )
            else:
                # No Langfuse, use direct LLM call
                if not self.langfuse_client:
                    logger.warning("Langfuse client not available")
                if self.prompt_config.get("provider") != "langfuse":
                    logger.warning(f"Prompt provider is not langfuse: {self.prompt_config.get('provider')}")
                logger.info("Using direct LLM call (no Langfuse)")
                decision = self.llm_client.generate(
                    prompt_variables=prompt_variables
                )

            logger.debug(f"LLM decision: {decision}")

            # Parse decision
            if "CLARIFICATION" in decision.upper():
                state["next_agent"] = "clarification"
                state["clarification_needed"] = True
                state["missing_context"] = ["Query is vague or ambiguous"]
                state["clarification_count"] = clarification_count + 1  # Increment counter
                logger.info(f"Routing to: clarification (count: {state['clarification_count']}/{max_clarifications})")
            else:
                state["next_agent"] = "research"
                state["clarification_needed"] = False
                state["clarification_count"] = 0  # Reset counter when routing to research
                logger.info("Routing to: research")

            state["iteration"] += 1
            return state

        except Exception as e:
            logger.error(f"Orchestrator failed: {e}", exc_info=True)
            # Default to research on error
            state["next_agent"] = "research"
            state["clarification_needed"] = False
            state["iteration"] += 1
            return state

    def _format_history(self, messages: list) -> str:
        """Format message history for prompt.

        Args:
            messages: List of messages

        Returns:
            Formatted history string
        """
        if not messages:
            return "No previous conversation."

        formatted = []
        for msg in messages:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            formatted.append(f"{role}: {msg.content}")

        return "\n".join(formatted)
