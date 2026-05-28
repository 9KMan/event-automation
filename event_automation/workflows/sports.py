"""Sports Verification Workflow."""
import logging
from typing import List, Any

from event_automation.models import Event, VerificationResult
from event_automation.llm.prompts import PromptTemplates
from event_automation.llm.output_parser import OutputParser

logger = logging.getLogger(__name__)


class SportsWorkflow:
    """Sports Verification Workflow.

    Ingests fixture schedules, detects changes, and surfaces discrepancies
    for the approved league universe.
    """

    def __init__(self):
        """Initialize SportsWorkflow."""
        self.prompts = PromptTemplates()
        self.parser = OutputParser()

    async def run(self, events: List[Event], llm_client: Any) -> List[VerificationResult]:
        """
        Run the sports verification workflow.

        Args:
            events: List of sports events/fixtures to verify
            llm_client: LLM client for making API calls

        Returns:
            List of VerificationResult objects
        """
        if not events:
            logger.info("No sports events to verify")
            return []

        logger.info(f"Running sports verification workflow on {len(events)} events")

        # Build sports verification prompt
        prompt = self.prompts.get_sports_prompt(events)

        # Call LLM
        system_prompt = (
            "You are a sports fixture verification assistant. "
            "Analyze events against known league records and fixture feeds. "
            "Detect schedule changes, new fixtures, and time/date modifications. "
            "Return a JSON array of verification results."
        )

        try:
            response = await llm_client.complete(prompt=prompt, system_prompt=system_prompt)

            # Parse and validate output
            results = self.parser.parse_sports_output(response)

            # Log results
            verified = sum(1 for r in results if r.proposed_status == "verified")
            discrepancies = sum(1 for r in results if r.proposed_status == "conflict")
            needs_review = sum(1 for r in results if r.proposed_status == "needs_review")

            logger.info(
                f"Sports verification complete: {len(results)} events, "
                f"{verified} verified, {discrepancies} discrepancies, {needs_review} need review"
            )

            return results

        except Exception as e:
            logger.error(f"Sports verification workflow failed: {e}")
            raise