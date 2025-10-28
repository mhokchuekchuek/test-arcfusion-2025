"""Clarification Agent for handling vague/ambiguous queries."""

from typing import Optional
from langchain_core.messages import AIMessage, HumanMessage

from src.agents.base import BaseAgent
from src.graph.state import AgentState
from tools.llm.client.base import BaseLLM
from tools.logger import get_logger

logger = get_logger(__name__)


class ClarificationAgent(BaseAgent):
    """Detects vagueness and generates clarifying questions."""

    def __init__(
        self,
        llm_client: BaseLLM,
        langfuse_client: Optional[any] = None,
        agent_config: Optional[dict] = None
    ):
        """Initialize clarification agent.

        Args:
            llm_client: LLM client configured with clarification-dotprompt model
            langfuse_client: Optional Langfuse client for observability
            agent_config: Optional agent configuration (name, prompt)
        """
        super().__init__("ClarificationAgent")
        self.llm_client = llm_client
        self.langfuse_client = langfuse_client
        self.agent_config = agent_config or {}
        self.agent_name = self.agent_config.get("name", "clarification")
        self.prompt_config = self.agent_config.get("prompt", {})

    def execute(self, state: AgentState) -> AgentState:
        """Generate clarifying question for vague query.

        Args:
            state: Current agent state

        Returns:
            State with clarifying question as final_answer
        """
        # Limit message history to prevent token overflow
        max_history = self.agent_config.get("max_history", 10)
        messages = state["messages"][-max_history:] if len(state["messages"]) > max_history else state["messages"]
        logger.debug(f"Processing {len(messages)} messages (max_history={max_history})")

        query = messages[-1].content
        history = self._format_history(messages[:-1])

        logger.info(f"Generating clarification for query: {query[:100]}...")

        try:
            # Prepare prompt variables
            prompt_variables = {
                "query": query,
                "history": history,
            }

            # Fetch prompt from Langfuse (if available)
            if self.langfuse_client and self.prompt_config.get("provider") == "langfuse":
                try:
                    # Get prompt config
                    prompt_id = self.prompt_config.get("id", "clarification")
                    prompt_version = self.prompt_config.get("version")
                    prompt_env = self.prompt_config.get("environment", "dev")

                    prompt = self.langfuse_client.get_prompt(
                        name=prompt_id,
                        version=prompt_version,
                        label=prompt_env
                    )
                    # Compile template with variables
                    compiled_prompt = prompt.compile(**prompt_variables)

                    # Generate clarification (use agent's configured model)
                    clarification = self.llm_client.generate(
                        prompt=compiled_prompt
                    )

                    # Trace generation with session_id and configured name
                    session_id = state.get("session_id")
                    self.langfuse_client.trace_generation(
                        name=self.agent_name,
                        input_data=prompt_variables,
                        output=clarification,
                        model=self.llm_client.completion_model,
                        metadata={"agent": "ClarificationAgent"},
                        session_id=session_id
                    )
                    logger.info(f"✓ Langfuse trace recorded (name={self.agent_name}, session={session_id})")
                except Exception as e:
                    logger.warning(f"Langfuse prompt fetch failed, using fallback: {e}")
                    # Fallback to direct LLM call
                    clarification = self.llm_client.generate(
                        prompt_variables=prompt_variables
                    )
            else:
                # No Langfuse, use direct LLM call
                clarification = self.llm_client.generate(
                    prompt_variables=prompt_variables
                )

            logger.info("Clarification question generated")

            # Add clarification to messages
            state["messages"].append(AIMessage(content=clarification))
            state["final_answer"] = clarification
            state["next_agent"] = "END"
            state["last_agent"] = "clarification"  # Track that clarification agent executed

            return state

        except Exception as e:
            logger.error(f"Clarification agent failed: {e}", exc_info=True)
            # Fallback clarification
            fallback = "Could you please provide more details about your question?"
            state["messages"].append(AIMessage(content=fallback))
            state["final_answer"] = fallback
            state["next_agent"] = "END"
            state["last_agent"] = "clarification"  # Track that clarification agent executed
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
