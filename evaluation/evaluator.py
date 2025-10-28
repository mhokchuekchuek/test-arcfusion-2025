"""Evaluation runner for agent responses.

Runs scenarios through the agent workflow and evaluates quality with LLM-as-a-Judge.
Integrated with Langfuse for score tracking and quality monitoring.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from evaluation.config import load_evaluation_config
from evaluation.llm_judge import LLMJudge
from evaluation.workflow_validator import WorkflowValidator
from evaluation.scenarios import autonomous, clarification, pdf_only, out_of_scope
from tools.llm.client.selector import LLMClientSelector
from tools.logger import get_logger
from tools.observability.selector import ObservabilitySelector

logger = get_logger(__name__)


class Evaluator:
    """Evaluation runner for agent workflow quality assessment."""

    def __init__(self):
        """Initialize evaluator from config.

        All settings loaded from configs/ directory.
        Override via environment variables if needed.

        Example:
            >>> evaluator = Evaluator()
            >>> results = evaluator.run_all_scenarios()
        """
        logger.info("Initializing Evaluator from config")

        # Load config
        config = load_evaluation_config()
        self.config = config

        # Get API URL from config
        self.api_url = config.evaluation.api_url
        logger.info(f"Using API URL: {self.api_url}")

        logger.debug(f"Creating LLM client for evaluation")
        # LLM client for evaluation (GPT-4, temperature=0)
        self.llm_client = LLMClientSelector.create(
            provider=config.evaluation.llm.provider,
            proxy_url=config.evaluation.llm.proxy_url,
            api_key=config.evaluation.llm.api_key,
            completion_model=config.evaluation.llm.model,
            temperature=config.evaluation.llm.temperature,
            max_tokens=config.evaluation.llm.max_tokens
        )

        logger.debug(f"Creating Langfuse client")
        # Langfuse client for score logging
        # Fallback to OBSERVABILITY__LANGFUSE__* env vars if evaluation-specific vars not set
        langfuse_config = config.evaluation.observability.langfuse
        public_key = langfuse_config.public_key or config.get("observability.langfuse.public_key")
        secret_key = langfuse_config.secret_key or config.get("observability.langfuse.secret_key")
        host = langfuse_config.host

        self.langfuse_client = ObservabilitySelector.create(
            provider=langfuse_config.provider,
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )

        # Initialize LLM Judge
        self.llm_judge = LLMJudge(
            llm_client=self.llm_client,
            langfuse_client=self.langfuse_client
        )

        # Initialize Workflow Validator
        self.workflow_validator = WorkflowValidator(
            langfuse_client=self.langfuse_client
        )

        logger.info("Evaluator ready")

    def run_scenario(self, scenario) -> Optional[Dict[str, Any]]:
        """Run a scenario through the chat API.

        Args:
            scenario: Scenario object with query and expectations

        Returns:
            API response dict or None if failed
        """
        logger.info(f"Running scenario: {scenario.name}")

        # Add timestamp suffix for unique session IDs
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        session_id = f"eval-{scenario.id}-{timestamp}"

        response = requests.post(
            f"{self.api_url}/chat",
            json={
                "message": scenario.query,
                "session_id": session_id
            },
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200:
            logger.error(f"API request failed: {response.status_code}")
            return None

        return response.json()

    def evaluate_quality(self, scenario, result) -> Optional[Dict[str, Any]]:
        """Evaluate response quality using unified evaluation prompt.

        Args:
            scenario: Scenario object with expected_answer_criteria
            result: API response

        Returns:
            Quality scores or None if failed
        """
        query = scenario.query
        answer = result['answer']
        sources = result.get('sources', [])
        session_id = result['session_id']
        expected_criteria = scenario.expected_answer_criteria

        logger.info(f"Evaluating quality for: {scenario.name}")

        try:
            scores = self.llm_judge.evaluate_quality(
                query=query,
                expected_criteria=expected_criteria,
                answer=answer,
                sources=sources,
                session_id=session_id
            )
            return scores
        except Exception as e:
            logger.error(f"Quality evaluation failed: {e}", exc_info=True)
            return None

    def evaluate_autonomous(self, scenario, result) -> Optional[Dict[str, Any]]:
        """Evaluate autonomous multi-step scenario.

        Args:
            scenario: Scenario object
            result: API response

        Returns:
            Evaluation scores or None if failed
        """
        query = scenario.query
        answer = result['answer']
        sources = result.get('sources', [])

        # Format required steps
        required_steps = "1. Search academic papers (pdf_retrieval)\n2. Search the web (web_search)\n3. Synthesize information"

        # Expected tools
        expected_tools = scenario.expected_workflow.tools_should_include

        # Use session_id for scoring (Langfuse will link to trace automatically)
        session_id = result['session_id']

        # Run evaluation
        try:
            scores = self.llm_judge.evaluate_autonomous(
                query=query,
                answer=answer,
                sources=sources,
                tool_calls=expected_tools,
                required_steps=required_steps,
                expected_tools=expected_tools,
                session_id=session_id
            )
            return scores
        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            return None

    def evaluate_clarification(self, scenario, result) -> Optional[Dict[str, Any]]:
        """Evaluate clarification scenario.

        Args:
            scenario: Scenario object
            result: API response

        Returns:
            Evaluation scores or None if failed
        """
        query = scenario.query
        clarification_questions = result['answer']
        history = f"User: {query}"
        session_id = result['session_id']

        # Run evaluation
        try:
            scores = self.llm_judge.evaluate_clarification(
                query=query,
                clarification_questions=clarification_questions,
                history=history,
                session_id=session_id
            )
            return scores
        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            return None

    def evaluate_pdf_only(self, scenario, result) -> Optional[Dict[str, Any]]:
        """Evaluate PDF-only scenario.

        Args:
            scenario: Scenario object
            result: API response

        Returns:
            Evaluation scores or None if failed
        """
        query = scenario.query
        answer = result['answer']
        sources = result.get('sources', [])
        session_id = result['session_id']

        # Get expected content from scenario
        expected_content = getattr(scenario, 'expected_content', 'Information about the query topic')

        # Run evaluation
        try:
            scores = self.llm_judge.evaluate_pdf_only(
                query=query,
                expected_content=expected_content,
                answer=answer,
                sources=sources,
                session_id=session_id
            )
            return scores
        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            return None

    def run_all_scenarios(self, waiting_time: int = 30) -> List[Dict[str, Any]]:
        """Run all evaluation scenarios with workflow validation + quality evaluation.

        Args:
            waiting_time: Seconds to wait for Langfuse trace submission (default: 30)

        Returns:
            List of evaluation results with workflow and quality scores

        Example:
            >>> evaluator = Evaluator()
            >>> results = evaluator.run_all_scenarios()
            >>> # Or with custom wait time
            >>> results = evaluator.run_all_scenarios(waiting_time=20)
            >>> for result in results:
            ...     print(f"{result['scenario']}: workflow={result['workflow']['pass']}, quality={result['quality']}")
        """
        logger.info("Starting evaluation of all scenarios")
        results = []

        # Collect all scenarios
        all_scenarios = [
            *[(s, 'autonomous') for s in autonomous.SCENARIOS],
            *[(s, 'clarification') for s in clarification.SCENARIOS],
            *[(s, 'pdf_only') for s in pdf_only.SCENARIOS],
            *[(s, 'out_of_scope') for s in out_of_scope.SCENARIOS],
        ]

        print(f"Total scenarios to evaluate: {len(all_scenarios)}")
        print("-" * 60)

        for idx, (scenario, category) in enumerate(all_scenarios, 1):
            print(f"\n[{idx}/{len(all_scenarios)}] Running: {scenario.name} ({category})")
            logger.info(f"Running scenario: {scenario.name} ({category})")

            # Run scenario through API
            print(f"  → Sending query to API...")
            result = self.run_scenario(scenario)
            if not result:
                print(f"  ✗ API call failed")
                results.append({
                    'scenario': scenario.name,
                    'scenario_id': scenario.id,
                    'category': category,
                    'success': False,
                    'error': 'API call failed',
                    'session_id': f"eval-{scenario.id}"
                })
                continue

            session_id = result['session_id']
            print(f"  ✓ Got response (session: {session_id})")

            # 1. Workflow Validation
            print(f"  → Validating workflow...")
            workflow_result = self.workflow_validator.validate(scenario, session_id)
            workflow_pass = workflow_result.get('pass', False) if workflow_result else False
            print(f"  {'✓' if workflow_pass else '✗'} Workflow validation: {'PASS' if workflow_pass else 'FAIL'}")

            # 2. Quality Evaluation
            print(f"  → Evaluating quality with LLM judge...")
            quality_scores = self.evaluate_quality(scenario, result)
            if quality_scores:
                print(f"  ✓ Quality evaluation complete")
            else:
                print(f"  ✗ Quality evaluation failed")

            # Store results
            results.append({
                'scenario': scenario.name,
                'scenario_id': scenario.id,
                'category': category,
                'success': quality_scores is not None,
                'workflow': workflow_result,
                'quality': quality_scores,
                'session_id': session_id
            })

        # Summary
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        workflow_passed = sum(1 for r in results if r.get('workflow', {}).get('pass', False))

        logger.info(
            f"Evaluation complete: {successful} succeeded, {failed} failed "
            f"(workflow: {workflow_passed}/{len(results)} passed)"
        )

        # Flush Langfuse traces to ensure they're submitted before script exits
        print(f"\n{'='*60}")
        print(f"Flushing traces to Langfuse...")
        print(f"{'='*60}")
        logger.info(f"Flushing Langfuse traces (waiting {waiting_time}s for submission)...")

        try:
            if self.langfuse_client:
                print(f"  → Calling langfuse.flush()...")
                self.langfuse_client.flush()
                print(f"  ✓ Flush called successfully")
                logger.info("Langfuse client flushed successfully")
        except Exception as e:
            print(f"  ⚠ Warning: Failed to flush Langfuse client: {e}")
            logger.warning(f"Failed to flush Langfuse client: {e}")

        # Wait for async traces to be fully submitted
        print(f"  → Waiting {waiting_time} seconds for trace submission...")
        for i in range(waiting_time):
            if (i + 1) % 10 == 0:
                print(f"    ... {i + 1}s / {waiting_time}s")
            time.sleep(1)
        print(f"  ✓ Wait complete ({waiting_time}s elapsed)")
        logger.info("Trace submission wait complete")

        return results
