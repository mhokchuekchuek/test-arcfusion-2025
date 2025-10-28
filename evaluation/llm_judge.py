"""LLM-as-a-Judge evaluation for answer quality.

Evaluates agent responses using LLM-based scoring with prompts from /prompts/evaluation/.
Integrates with Langfuse for scoring and tracking.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.llm.client.selector import LLMClientSelector
from tools.logger import get_logger
from tools.observability.selector import ObservabilitySelector

logger = get_logger(__name__)


class LLMJudge:
    """LLM-as-a-Judge evaluator using evaluation prompts."""

    def __init__(
        self,
        llm_client,
        langfuse_client: Optional[Any] = None,
        prompts_dir: str = "prompts/evaluation"
    ):
        """Initialize LLM Judge.

        Args:
            llm_client: LLM client for running evaluation prompts
            langfuse_client: Optional Langfuse client for logging scores
            prompts_dir: Directory containing evaluation prompts
        """
        self.llm_client = llm_client
        self.langfuse_client = langfuse_client
        self.prompts_dir = Path(prompts_dir)

        logger.info("LLMJudge initialized")

    def load_evaluation_prompt(self, category: str) -> str:
        """Load evaluation prompt from Langfuse.

        Args:
            category: Evaluation category (autonomous, clarification, pdf_only, web_search)

        Returns:
            Prompt template string

        Raises:
            ValueError: If prompt not found in Langfuse
        """
        # Construct prompt name following uploader naming convention
        # e.g., "evaluation_autonomous" for prompts/evaluation/autonomous/v1.prompt
        prompt_name = f"evaluation_{category}"

        try:
            # Fetch prompt from Langfuse with label 'dev' (matching upload label)
            prompt_obj = self.langfuse_client.get_prompt(name=prompt_name, label="dev")
            return prompt_obj.prompt

        except Exception as e:
            logger.error(f"Failed to load prompt '{prompt_name}' from Langfuse: {e}")
            raise ValueError(
                f"Evaluation prompt '{prompt_name}' not found in Langfuse. "
                f"Please upload prompts first: python scripts/upload_prompts_to_langfuse.py"
            )

    def fill_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Fill template with variables using {{variable}} syntax.

        Args:
            template: Template string with {{variable}} placeholders
            variables: Dictionary of variable values

        Returns:
            Filled template string
        """
        result = template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))

        return result

    def evaluate_quality(
        self,
        query: str,
        expected_criteria: str,
        answer: str,
        sources: List[Dict],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate response quality using unified evaluation prompt.

        Args:
            query: Original user query
            expected_criteria: Expected answer criteria from scenario
            answer: System's answer
            sources: List of sources used
            session_id: Optional Langfuse session ID for scoring

        Returns:
            Quality scores (answer_quality, factual_correctness, completeness)
        """
        logger.info(f"Evaluating quality for query: '{query[:50]}...'")

        # Load unified quality evaluation prompt
        template = self.load_evaluation_prompt("quality")
        prompt = self.fill_template(template, {
            "query": query,
            "expected_criteria": expected_criteria,
            "answer": answer,
            "sources": json.dumps(sources, indent=2)
        })

        # Run evaluation
        response = self.llm_client.generate(prompt=prompt)

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            content = response.strip()
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0].strip()

            scores = json.loads(content)
            logger.info(f"Evaluation complete: {scores}")

            # Log to Langfuse if available
            if self.langfuse_client and session_id:
                self._log_scores_to_langfuse(
                    session_id=session_id,
                    category="quality",
                    scores=scores
                )

            return scores

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evaluation JSON: {e}")
            logger.debug(f"Raw response: {response}")
            return {
                "answer_quality": 0.0,
                "factual_correctness": 0.0,
                "completeness": 0.0,
                "reasoning": "Failed to parse evaluation response",
                "error": "Failed to parse evaluation response",
                "raw_response": response
            }

    def evaluate_autonomous(
        self,
        query: str,
        answer: str,
        sources: List[Dict],
        tool_calls: List[str],
        required_steps: str,
        expected_tools: List[str],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate autonomous multi-step execution.

        Args:
            query: Original user query
            answer: System's answer
            sources: List of sources used
            tool_calls: List of tool names called
            required_steps: Description of required steps
            expected_tools: List of expected tool names
            session_id: Optional Langfuse session ID for scoring

        Returns:
            Evaluation scores and reasoning
        """
        logger.info(f"Evaluating autonomous execution for query: '{query[:50]}...'")

        # Load and fill template
        template = self.load_evaluation_prompt("autonomous")
        prompt = self.fill_template(template, {
            "query": query,
            "required_steps": required_steps,
            "answer": answer,
            "sources": json.dumps(sources, indent=2),
            "tool_calls": json.dumps(tool_calls),
            "expected_tools": json.dumps(expected_tools)
        })

        # Run evaluation
        response = self.llm_client.generate(prompt=prompt)

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            content = response.strip()
            if content.startswith("```"):
                # Remove markdown code blocks
                lines = content.split("\n")
                content = "\n".join([line for line in lines if not line.startswith("```")])

            scores = json.loads(content)
            logger.info(f"Evaluation complete: {scores}")

            # Log to Langfuse if available
            if self.langfuse_client and session_id:
                self._log_scores_to_langfuse(
                    session_id=session_id,
                    category="autonomous",
                    scores=scores
                )

            return scores

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evaluation response: {e}")
            logger.debug(f"Response content: {response}")
            return {
                "error": "Failed to parse evaluation response",
                "raw_response": response
            }

    def evaluate_clarification(
        self,
        query: str,
        clarification_questions: str,
        history: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate clarification agent response quality.

        Args:
            query: Original user query
            clarification_questions: Questions generated by clarification agent
            history: Conversation history
            session_id: Optional Langfuse session ID for scoring

        Returns:
            Evaluation scores and reasoning
        """
        logger.info(f"Evaluating clarification for query: '{query[:50]}...'")

        template = self.load_evaluation_prompt("clarification")
        prompt = self.fill_template(template, {
            "query": query,
            "clarification_questions": clarification_questions,
            "history": history
        })

        response = self.llm_client.generate(prompt=prompt)

        try:
            content = response.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join([line for line in lines if not line.startswith("```")])

            scores = json.loads(content)
            logger.info(f"Evaluation complete: {scores}")

            if self.langfuse_client and session_id:
                self._log_scores_to_langfuse(
                    session_id=session_id,
                    category="clarification",
                    scores=scores
                )

            return scores

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evaluation response: {e}")
            return {
                "error": "Failed to parse evaluation response",
                "raw_response": response
            }

    def evaluate_pdf_only(
        self,
        query: str,
        expected_content: str,
        answer: str,
        sources: List[Dict],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate PDF-only retrieval quality.

        Args:
            query: Original user query
            expected_content: Expected information in answer
            answer: System's answer
            sources: List of sources cited
            session_id: Optional Langfuse session ID for scoring

        Returns:
            Evaluation scores and reasoning
        """
        logger.info(f"Evaluating PDF-only for query: '{query[:50]}...'")

        template = self.load_evaluation_prompt("pdf_only")
        prompt = self.fill_template(template, {
            "query": query,
            "expected_content": expected_content,
            "answer": answer,
            "sources": json.dumps(sources, indent=2)
        })

        response = self.llm_client.generate(prompt=prompt)

        try:
            content = response.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join([line for line in lines if not line.startswith("```")])

            scores = json.loads(content)
            logger.info(f"Evaluation complete: {scores}")

            if self.langfuse_client and session_id:
                self._log_scores_to_langfuse(
                    session_id=session_id,
                    category="pdf_only",
                    scores=scores
                )

            return scores

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evaluation response: {e}")
            return {
                "error": "Failed to parse evaluation response",
                "raw_response": response
            }

    def _log_scores_to_langfuse(
        self,
        session_id: str,
        category: str,
        scores: Dict[str, Any]
    ):
        """Log evaluation scores to Langfuse.

        Uses session_id to link scores to traces automatically.

        Args:
            session_id: Session ID (Langfuse will find the trace)
            category: Evaluation category
            scores: Evaluation scores dictionary
        """
        try:
            # Log individual metric scores using Langfuse SDK
            for metric_name, score_value in scores.items():
                if metric_name == "reasoning":
                    continue  # Skip reasoning, logged as comment

                if isinstance(score_value, (int, float)):
                    self.langfuse_client.client.create_score(
                        name=f"{category}_{metric_name}",
                        value=score_value,
                        trace_id=session_id,
                        data_type="NUMERIC",
                        comment=scores.get("reasoning", "")
                    )

            # Log overall category score (average of metrics)
            numeric_scores = [v for k, v in scores.items()
                            if isinstance(v, (int, float)) and k != "reasoning"]
            if numeric_scores:
                overall_score = sum(numeric_scores) / len(numeric_scores)
                self.langfuse_client.client.create_score(
                    name=f"{category}_overall",
                    value=overall_score,
                    trace_id=session_id,
                    data_type="NUMERIC",
                    comment=f"Average of {len(numeric_scores)} metrics. {scores.get('reasoning', '')}"
                )

            # Flush to ensure scores are sent
            self.langfuse_client.flush()
            logger.info(f"Logged {len(numeric_scores) + 1} scores to Langfuse for session {session_id}")

        except Exception as e:
            logger.warning(f"Failed to log scores to Langfuse: {e}")
