"""Answer Synthesis Agent for formatting final answers."""

from typing import Optional
from langchain_core.messages import AIMessage, HumanMessage

from src.agents.base import BaseAgent
from src.graph.state import AgentState
from tools.llm.client.base import BaseLLM
from tools.logger import get_logger

logger = get_logger(__name__)


class AnswerSynthesisAgent(BaseAgent):
    """Synthesizes final answer from research observations."""

    def __init__(
        self,
        llm_client: BaseLLM,
        langfuse_client: Optional[any] = None,
        agent_config: Optional[dict] = None
    ):
        """Initialize synthesis agent.

        Args:
            llm_client: LLM client configured with synthesis-dotprompt model
            langfuse_client: Optional Langfuse client for observability
            agent_config: Optional agent configuration (name, prompt)
        """
        super().__init__("AnswerSynthesisAgent")
        self.llm_client = llm_client
        self.langfuse_client = langfuse_client
        self.agent_config = agent_config or {}
        self.agent_name = self.agent_config.get("name", "synthesis")
        self.prompt_config = self.agent_config.get("prompt", {})

    def execute(self, state: AgentState) -> AgentState:
        """Synthesize coherent answer from tool results.

        Args:
            state: Current agent state

        Returns:
            State with synthesized final_answer and confidence_score
        """
        # Limit message history to prevent token overflow
        max_history = self.agent_config.get("max_history", 10)
        messages = state["messages"][-max_history:] if len(state["messages"]) > max_history else state["messages"]
        logger.debug(f"Processing {len(messages)} messages (max_history={max_history})")

        # Get the original user query (first HumanMessage in limited history)
        query = "Unknown query"
        for msg in messages:
            if isinstance(msg, HumanMessage):
                query = msg.content
                break

        observations = state["context"].get("observations", [])
        final_output = state["context"].get("final_output", "")

        logger.info(f"Synthesizing answer from {len(observations)} observations")

        try:
            # Combine observations with final output
            all_observations = "\n\n".join(observations)
            if final_output:
                all_observations += f"\n\nFinal Output:\n{final_output}"

            # Prepare prompt variables
            prompt_variables = {
                "query": query,
                "observations": all_observations if all_observations else "No observations available.",
            }

            # Fetch prompt from Langfuse (if available)
            if self.langfuse_client and self.prompt_config.get("provider") == "langfuse":
                try:
                    # Get prompt config
                    prompt_id = self.prompt_config.get("id", "synthesis")
                    prompt_version = self.prompt_config.get("version")
                    prompt_env = self.prompt_config.get("environment", "dev")

                    prompt = self.langfuse_client.get_prompt(
                        name=prompt_id,
                        version=prompt_version,
                        label=prompt_env
                    )
                    # Compile template with variables
                    compiled_prompt = prompt.compile(**prompt_variables)

                    # Generate answer (use agent's configured model)
                    answer = self.llm_client.generate(
                        prompt=compiled_prompt
                    )

                    # Trace generation with session_id and configured name
                    session_id = state.get("session_id")
                    self.langfuse_client.trace_generation(
                        name=self.agent_name,
                        input_data=prompt_variables,
                        output=answer,
                        model=self.llm_client.completion_model,
                        metadata={"agent": "AnswerSynthesisAgent"},
                        session_id=session_id
                    )
                    logger.info(f"✓ Langfuse trace recorded (name={self.agent_name}, session={session_id})")
                except Exception as e:
                    logger.warning(f"Langfuse prompt fetch failed, using fallback: {e}")
                    # Fallback to direct LLM call
                    answer = self.llm_client.generate(
                        prompt_variables=prompt_variables
                    )
            else:
                # No Langfuse, use direct LLM call
                answer = self.llm_client.generate(
                    prompt_variables=prompt_variables
                )

            logger.info("Answer synthesized successfully")

            # Calculate confidence score
            confidence = self._calculate_confidence(observations)

            # Update state
            state["messages"].append(AIMessage(content=answer))
            state["final_answer"] = answer
            state["confidence_score"] = confidence
            state["next_agent"] = "END"
            state["last_agent"] = "synthesis"  # Track that synthesis agent executed

            return state

        except Exception as e:
            logger.error(f"Synthesis agent failed: {e}", exc_info=True)
            # Fallback answer
            fallback = final_output if final_output else "I encountered an error while processing your request."
            state["messages"].append(AIMessage(content=fallback))
            state["final_answer"] = fallback
            state["confidence_score"] = 0.0
            state["next_agent"] = "END"
            return state

    def _calculate_confidence(self, observations: list) -> float:
        """Calculate confidence score based on observations.

        Args:
            observations: List of observation strings

        Returns:
            Confidence score between 0.0 and 1.0
        """
        num_observations = len(observations)
        if num_observations == 0:
            return 0.0
        elif num_observations == 1:
            return 0.6
        elif num_observations == 2:
            return 0.8
        else:
            return 0.95
