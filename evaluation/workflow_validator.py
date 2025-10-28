"""Workflow validator for evaluation scenarios.

Validates that the correct agents and tools were used based on scenario expectations.
"""

from typing import Dict, Any, List, Optional
from tools.logger import get_logger

logger = get_logger(__name__)


class WorkflowValidator:
    """Validates agent and tool selection against scenario expectations."""

    def __init__(self, langfuse_client):
        """Initialize workflow validator.

        Args:
            langfuse_client: Langfuse client for fetching traces
        """
        self.langfuse_client = langfuse_client

    def validate(self, scenario, session_id: str) -> Dict[str, Any]:
        """Validate workflow against scenario expectations.

        Args:
            scenario: Scenario object with expected_workflow
            session_id: Session ID to fetch trace

        Returns:
            Validation results with pass/fail and details

        Example:
            >>> validator = WorkflowValidator(langfuse_client)
            >>> result = validator.validate(scenario, "eval-123-20251028")
            >>> print(result['pass'])  # True or False
        """
        logger.info(f"Validating workflow for session: {session_id}")

        try:
            # Fetch trace from Langfuse
            trace_data = self._fetch_trace(session_id)
            if not trace_data:
                return {
                    'pass': False,
                    'error': 'Could not fetch trace from Langfuse',
                    'agents': {},
                    'tools': {}
                }

            # Extract agents and tools used
            agents_used = self._extract_agents(trace_data)
            tools_used = self._extract_tools(trace_data)

            logger.debug(f"Agents used: {agents_used}")
            logger.debug(f"Tools used: {tools_used}")

            # Validate against expectations
            expected = scenario.expected_workflow

            agents_validation = self._validate_agents(agents_used, expected)
            tools_validation = self._validate_tools(tools_used, expected)

            # Overall pass if both pass
            overall_pass = agents_validation['pass'] and tools_validation['pass']

            return {
                'pass': overall_pass,
                'agents': agents_validation,
                'tools': tools_validation,
                'agents_used': agents_used,
                'tools_used': tools_used
            }

        except Exception as e:
            logger.error(f"Workflow validation failed: {e}", exc_info=True)
            return {
                'pass': False,
                'error': str(e),
                'agents': {},
                'tools': {}
            }

    def _fetch_trace(self, session_id: str, max_retries: int = 10, retry_delay: int = 3) -> Optional[Dict[str, Any]]:
        """Fetch trace from Langfuse by session_id with retry logic.

        Args:
            session_id: Session ID
            max_retries: Maximum number of retry attempts (default: 10)
            retry_delay: Seconds to wait between retries (default: 3)

        Returns:
            Trace data dict or None if not found after all retries
        """
        import time
        from langfuse import get_client

        langfuse = get_client()

        for attempt in range(max_retries):
            try:
                # Fetch traces filtered by session_id
                traces_response = langfuse.api.trace.list(limit=1, session_id=session_id)

                if traces_response and hasattr(traces_response, 'data') and len(traces_response.data) > 0:
                    trace = traces_response.data[0]
                    logger.info(f"✓ Fetched trace on attempt {attempt + 1}: {trace.id}")

                    # Fetch observations for the trace
                    observations_response = langfuse.api.observations.get_many(trace_id=trace.id, limit=100)

                    return {
                        'trace': trace,
                        'observations': observations_response.data if observations_response and hasattr(observations_response, 'data') else []
                    }

                # Trace not found yet, wait and retry
                if attempt < max_retries - 1:
                    logger.debug(f"Trace not found (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                    time.sleep(retry_delay)

            except Exception as e:
                logger.warning(f"Error fetching trace (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        logger.warning(f"No trace found for session_id: {session_id} after {max_retries} attempts")
        return None

    def _extract_agents(self, trace_data: Dict[str, Any]) -> List[str]:
        """Extract agent names from trace observations.

        Args:
            trace_data: Trace data with observations

        Returns:
            List of agent names used
        """
        agents = set()
        observations = trace_data.get('observations', [])

        for obs in observations:
            # Agents are typically generations with specific names
            if obs.type == "GENERATION":
                name = obs.name
                # Extract agent name (e.g., "orchestrator", "research", "clarification")
                if name in ["orchestrator", "research", "clarification", "synthesis"]:
                    agents.add(name)

        return sorted(list(agents))

    def _extract_tools(self, trace_data: Dict[str, Any]) -> List[str]:
        """Extract tool names from trace observations.

        Args:
            trace_data: Trace data with observations

        Returns:
            List of tool names used
        """
        tools = set()
        observations = trace_data.get('observations', [])

        logger.debug(f"Extracting tools from {len(observations)} observations")

        for obs in observations:
            # Debug: log observation details
            obs_type = getattr(obs, 'type', None)
            obs_name = getattr(obs, 'name', None)
            logger.debug(f"  Observation: type={obs_type}, name={obs_name}")

            # Tools can be logged as different observation types
            # Check for tool names in: SPAN, GENERATION, or metadata
            if obs_name in ["pdf_retrieval", "web_search"]:
                tools.add(obs_name)
                logger.debug(f"    ✓ Found tool: {obs_name}")

            # Also check metadata for tool usage
            if hasattr(obs, 'metadata') and obs.metadata:
                metadata = obs.metadata
                if isinstance(metadata, dict):
                    # Check if metadata contains tools_used
                    if 'tools_used' in metadata:
                        tool_list = metadata['tools_used']
                        if isinstance(tool_list, list):
                            for tool in tool_list:
                                if tool in ["pdf_retrieval", "web_search"]:
                                    tools.add(tool)
                                    logger.debug(f"    ✓ Found tool in metadata: {tool}")

        logger.debug(f"Extracted tools: {sorted(list(tools))}")
        return sorted(list(tools))

    def _validate_agents(self, agents_used: List[str], expected) -> Dict[str, Any]:
        """Validate agents against expectations.

        Args:
            agents_used: List of agents that were used
            expected: WorkflowExpectation object

        Returns:
            Validation result
        """
        agents_set = set(agents_used)
        should_include = set(expected.agents_should_include)
        should_exclude = set(expected.agents_should_exclude)

        # Check inclusions
        missing = should_include - agents_set
        # Check exclusions
        unwanted = agents_set & should_exclude

        passed = len(missing) == 0 and len(unwanted) == 0

        return {
            'pass': passed,
            'expected': expected.agents_should_include,
            'excluded': expected.agents_should_exclude,
            'missing': sorted(list(missing)),
            'unwanted': sorted(list(unwanted))
        }

    def _validate_tools(self, tools_used: List[str], expected) -> Dict[str, Any]:
        """Validate tools against expectations.

        Args:
            tools_used: List of tools that were used
            expected: WorkflowExpectation object

        Returns:
            Validation result
        """
        tools_set = set(tools_used)
        should_include = set(expected.tools_should_include)
        should_exclude = set(expected.tools_should_exclude)

        # Check inclusions
        missing = should_include - tools_set
        # Check exclusions
        unwanted = tools_set & should_exclude

        passed = len(missing) == 0 and len(unwanted) == 0

        return {
            'pass': passed,
            'expected': expected.tools_should_include,
            'excluded': expected.tools_should_exclude,
            'missing': sorted(list(missing)),
            'unwanted': sorted(list(unwanted))
        }
