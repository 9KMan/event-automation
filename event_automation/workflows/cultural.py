"""Cultural Verification Workflow."""
import logging
from typing import List, Any

from event_automation.models import Event, VerificationResult
from event_automation.llm.prompts import PromptTemplates
from event_automation.llm.output_parser import OutputParser
from event_automation.data.intake import Intake

logger = logging.getLogger(__name__)


class CulturalWorkflow:
    """Cultural Verification Workflow.

    Verifies upcoming editions of cultural events, confirms dates/details,
    surfaces future editions, and flags conflicts.
    """

    def __init__(self, historical_data_path: str = None):
        """
        Initialize CulturalWorkflow.

        Args:
            historical_data_path: Path to historical event data for context
        """
        self.historical_data_path = historical_data_path
        self.prompts = PromptTemplates()
        self.parser = OutputParser()

    async def run(self, events: List[Event], llm_client: Any) -> List[VerificationResult]:
        """
        Run the cultural verification workflow.

        Args:
            events: List of cultural events to verify
            llm_client: LLM client for making API calls

        Returns:
            List of VerificationResult objects
        """
        if not events:
            logger.info("No cultural events to verify")
            return []

        logger.info(f"Running cultural verification workflow on {len(events)} events")

        # Load historical data for context
        historical_events = self._load_historical_data()

        # Build verification prompt with historical context
        prompt = self.prompts.get_cultural_prompt(events, historical_events)

        # Call LLM
        system_prompt = (
            "You are a cultural events verification assistant. "
            "Analyze events against historical patterns and verify dates/details. "
            "Return a JSON array of verification results."
        )

        try:
            response = await llm_client.complete(prompt=prompt, system_prompt=system_prompt)

            # Parse and validate output
            results = self.parser.parse_cultural_output(response)

            # Log results
            verified = sum(1 for r in results if r.proposed_status == "verified")
            conflicts = sum(1 for r in results if r.proposed_status == "conflict")
            uncertain = sum(1 for r in results if r.proposed_status == "uncertain")

            logger.info(
                f"Cultural verification complete: {len(results)} events, "
                f"{verified} verified, {conflicts} conflicts, {uncertain} uncertain"
            )

            return results

        except Exception as e:
            logger.error(f"Cultural verification workflow failed: {e}")
            raise

    def _load_historical_data(self) -> List[Event]:
        """Load historical event data for context."""
        if not self.historical_data_path:
            return []

        try:
            intake = Intake()
            return intake.load_events(self.historical_data_path)
        except Exception as e:
            logger.warning(f"Could not load historical data: {e}")
            return []