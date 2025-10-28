"""Research Supervisor using ReAct pattern for autonomous tool selection."""

from typing import List, Optional
from langchain.agents import create_agent
from langchain.tools import BaseTool

from src.agents.base import BaseAgent
from src.graph.state import AgentState
from tools.logger import get_logger

logger = get_logger(__name__)


class ResearchSupervisor(BaseAgent):
    """Research agent using ReAct pattern for autonomous tool selection.

    This agent can:
    - Plan multi-step operations
    - Choose appropriate tools (PDF, Web)
    - Chain multiple tools in sequence
    - Reflect on results and decide when done

    Uses LangChain v1.0 create_agent (replaces deprecated create_react_agent).
    Built on LangGraph for durable execution, streaming, persistence.
    """

    def __init__(
        self,
        llm,
        tools: List[BaseTool],
        langfuse_client: Optional[any] = None,
        agent_config: Optional[dict] = None
    ):
        """Initialize research supervisor.

        Args:
            llm: LangChain-compatible model (e.g., ChatOpenAI) configured with research-dotprompt
            tools: List of tools (PDFRetrievalTool, WebSearchTool)
            langfuse_client: Optional Langfuse client for observability
            agent_config: Optional agent configuration (name, prompt)
        """
        super().__init__("ResearchSupervisor")
        self.llm = llm
        self.tools = tools
        self.langfuse_client = langfuse_client
        self.agent_config = agent_config or {}
        self.agent_name = self.agent_config.get("name", "research")
        self.prompt_config = self.agent_config.get("prompt", {})

        # Load system prompt from Langfuse
        system_prompt = None
        if self.langfuse_client and self.prompt_config:
            try:
                # Prompt name follows uploader convention: agent_research
                # (from prompts/agent/research/v1.prompt → agent_research)
                prompt_id = self.prompt_config.get("id", "agent_research")
                prompt_version = self.prompt_config.get("version")
                prompt_env = self.prompt_config.get("environment", "dev")

                logger.info(f"Fetching research prompt from Langfuse: name={prompt_id}, label={prompt_env}")

                prompt_obj = self.langfuse_client.get_prompt(
                    name=prompt_id,
                    version=prompt_version,
                    label=prompt_env
                )
                system_prompt = prompt_obj.prompt
                logger.info(f"✓ Research prompt loaded from Langfuse")
            except Exception as e:
                logger.warning(f"Failed to load prompt from Langfuse: {e}. Using default behavior.")

        # Create agent using modern v1.0 API
        # create_agent is built on LangGraph and provides ReAct loop automatically
        self.agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,  # Pass the system prompt
        )
        logger.info(f"ResearchSupervisor initialized with create_agent (prompt={'Langfuse' if system_prompt else 'default'})")

    def execute(self, state: AgentState) -> AgentState:
        """Execute research with ReAct loop.

        Args:
            state: Current agent state

        Returns:
            Updated state with research observations and final output
        """
        try:
            logger.info("Starting research agent execution")
            logger.debug(f"Input state has {len(state['messages'])} messages")

            # Limit message history to prevent token overflow
            max_history = self.agent_config.get("max_history", 10)
            messages_to_send = state["messages"][-max_history:] if len(state["messages"]) > max_history else state["messages"]
            logger.debug(f"Sending {len(messages_to_send)} messages to research agent (max_history={max_history})")

            # Invoke agent with limited message history
            result = self.agent.invoke({
                "messages": messages_to_send
            })

            logger.debug(f"Agent returned {len(result['messages'])} messages")

            # Extract tool call information from messages for context
            observations = []
            tool_history = []

            # Count how many messages we sent to identify NEW messages in the result
            original_message_count = len(messages_to_send)

            for i, msg in enumerate(result["messages"]):
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    # Extract ALL tool calls from this message (not just the first one)
                    for tool_call in msg.tool_calls:
                        tool_name = tool_call.get('name', 'unknown')
                        if tool_name not in tool_history:  # Avoid duplicates
                            tool_history.append(tool_name)
                            logger.debug(f"Tool call detected: {tool_name}")
                            observations.append(f"Used tool: {tool_name}")

            # Store in context
            state["context"]["observations"] = observations
            state["context"]["tool_history"] = tool_history

            # Get final output from last message
            final_output = result["messages"][-1].content
            state["context"]["final_output"] = final_output

            # Trace research execution (if Langfuse available)
            if self.langfuse_client:
                try:
                    session_id = state.get("session_id")
                    self.langfuse_client.trace_generation(
                        name=self.agent_name,
                        input_data={"messages": [m.content for m in state["messages"][:original_message_count]]},
                        output=final_output,
                        model=str(self.llm.model_name) if hasattr(self.llm, 'model_name') else "research-model",
                        metadata={
                            "agent": "ResearchSupervisor",
                            "tools_used": tool_history,
                            "num_observations": len(observations)
                        },
                        session_id=session_id
                    )
                    logger.info(f"✓ Langfuse trace recorded (name={self.agent_name}, session={session_id})")
                except Exception as e:
                    logger.warning(f"Failed to trace research execution: {e}")

            # IMPORTANT: Only append the FINAL AI response, not intermediate tool messages
            # The agent returns all messages including tool calls/responses, but we only want
            # the final answer for the next agent in the workflow
            # Find the last AI message (the final answer after tool use)
            final_ai_message = None
            for msg in reversed(result["messages"]):
                if hasattr(msg, 'type') and msg.type == 'ai':
                    # Make sure it's a final answer, not a tool call request
                    if not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                        final_ai_message = msg
                        break

            if final_ai_message:
                state["messages"].append(final_ai_message)
                logger.debug(f"Added final AI response to state")
            else:
                logger.warning("No final AI message found in research result")
                # Fallback: add last message
                state["messages"].append(result["messages"][-1])

            # Move to synthesis
            state["next_agent"] = "synthesis"
            state["last_agent"] = "research"  # Track that research agent executed
            state["iteration"] += 1

            logger.info(f"Research completed. Tools used: {tool_history}. Total messages now: {len(state['messages'])}")
            return state

        except Exception as e:
            logger.error(f"Research agent failed: {e}", exc_info=True)
            # On error, move to synthesis with error context
            state["context"]["observations"] = [f"Research failed: {str(e)}"]
            state["context"]["final_output"] = "Unable to complete research due to an error."
            state["next_agent"] = "synthesis"
            state["iteration"] += 1
            return state
