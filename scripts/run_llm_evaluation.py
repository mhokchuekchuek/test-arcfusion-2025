#!/usr/bin/env python3
"""Run LLM-as-a-Judge evaluation on all scenarios.

Automatically runs predefined scenarios, evaluates responses with LLM-as-a-Judge,
and logs scores to Langfuse for quality monitoring.

Usage:
    python scripts/run_llm_evaluation.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation.evaluator import Evaluator
from tools.logger import get_logger

logger = get_logger(__name__)


def main():
    """Run all evaluation scenarios."""
    try:
        print("\n" + "="*60)
        print("LLM-as-a-Judge Evaluation Runner")
        print("="*60 + "\n")

        logger.info("Starting evaluation process")

        # Initialize evaluator (auto-loads config)
        print("Initializing evaluator...")
        evaluator = Evaluator()
        print(f"✓ Evaluator initialized")
        print(f"  API: {evaluator.config.evaluation.api_url}")
        print(f"  Judge Model: {evaluator.config.evaluation.llm.model}")
        print(f"  Langfuse: {evaluator.config.evaluation.observability.langfuse.host}\n")

        # Get waiting time (default 30s)
        waiting_time = 30
        print(f"Running all scenarios (Langfuse flush wait: {waiting_time}s)...\n")

        # Run all scenarios
        results = evaluator.run_all_scenarios(waiting_time=waiting_time)

        # Print summary
        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60 + "\n")

        if not results:
            print("No evaluation results")
            return 0

        for result in results:
            print(f"\n{result['scenario']} ({result['category']}):")
            print(f"  Session ID: {result['session_id']}")

            # Workflow Validation
            if 'workflow' in result and result['workflow']:
                workflow = result['workflow']
                workflow_pass = workflow.get('pass', False)
                print(f"  Workflow: {'✓ PASS' if workflow_pass else '✗ FAIL'}")

                # Show agent validation details
                if 'agents' in workflow:
                    agents = workflow['agents']
                    agents_pass = agents.get('pass', False)
                    print(f"    Agents: {'✓' if agents_pass else '✗'}")
                    if 'included' in agents:
                        for agent in agents['included']:
                            print(f"      ✓ {agent}")
                    if 'excluded' in agents:
                        for agent in agents['excluded']:
                            print(f"      ✓ {agent} (excluded)")
                    if 'missing' in agents and agents['missing']:
                        for agent in agents['missing']:
                            print(f"      ✗ Missing: {agent}")
                    if 'unexpected' in agents and agents['unexpected']:
                        for agent in agents['unexpected']:
                            print(f"      ✗ Unexpected: {agent}")

                # Show tool validation details
                if 'tools' in workflow:
                    tools = workflow['tools']
                    tools_pass = tools.get('pass', False)
                    print(f"    Tools: {'✓' if tools_pass else '✗'}")
                    if 'included' in tools:
                        for tool in tools['included']:
                            print(f"      ✓ {tool}")
                    if 'excluded' in tools:
                        for tool in tools['excluded']:
                            print(f"      ✓ {tool} (excluded)")
                    if 'missing' in tools and tools['missing']:
                        for tool in tools['missing']:
                            print(f"      ✗ Missing: {tool}")
                    if 'unexpected' in tools and tools['unexpected']:
                        for tool in tools['unexpected']:
                            print(f"      ✗ Unexpected: {tool}")

            # Quality Evaluation
            if result['success'] and 'quality' in result and result['quality']:
                print(f"  Quality:")
                quality = result['quality']
                for metric, value in quality.items():
                    if metric != "reasoning" and isinstance(value, (int, float)):
                        print(f"    {metric}: {value:.2f}")
                if 'reasoning' in quality:
                    print(f"    reasoning: {quality['reasoning']}")
            elif not result['success']:
                print(f"  Status: ✗ Failed - {result.get('error', 'Unknown error')}")

        # Count results
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        workflow_passed = sum(1 for r in results if r.get('workflow', {}).get('pass', False))

        print(f"\n{'='*60}")
        print(f"Total: {len(results)} scenarios")
        print(f"Workflow Passed: {workflow_passed}/{len(results)}")
        print(f"Quality Evaluation Successful: {successful}")
        print(f"Quality Evaluation Failed: {failed}")
        print(f"{'='*60}")

        print(f"\n✓ All evaluations complete")
        print(f"✓ Scores logged to Langfuse")
        print(f"✓ View results at: {evaluator.config.evaluation.observability.langfuse.host}\n")

        return 0 if failed == 0 else 1

    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}", exc_info=True)
        print(f"\n✗ Error: {str(e)}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
