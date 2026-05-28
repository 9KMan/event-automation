"""Concert Discovery Workflow."""
import logging
from typing import List, Any

from event_automation.models import Event, VerificationResult
from event_automation.llm.prompts import PromptTemplates
from event_automation.llm.output_parser import OutputParser

logger = logging.getLogger(__name__)


class ConcertWorkflow:
    """Concert Discovery Workflow.

    Monitors approved source universe for major tours, supports human approval,
    and extracts approved event details.
    """

    def __init__(self):
        """Initialize ConcertWorkflow."""
        self.prompts = PromptTemplates()
        self.parser = OutputParser()

    async def run(self, events: List[Event], llm_client: Any) -> List[VerificationResult]:
        """
        Run the concert discovery workflow.

        Args:
            events: List of potential concert/tour events
            llm_client: LLM client for making API calls

        Returns:
            List of VerificationResult objects
        """
        if not events:
            logger.info("No concert events to process")
            return []

        logger.info(f"Running concert discovery workflow on {len(events)} events")

        # Build concert discovery prompt
        prompt = self.prompts.get_concert_prompt(events)

        # Call LLM
        system_prompt = (
            "You are a concert discovery assistant. "
            "Analyze potential tour events and extract approved event details. "
            "Identify major tours, surface candidates for human approval, "
            "and extract confirmed event details. "
            "Return a JSON array of verification results."
        )

        try:
            response = await llm_client.complete(prompt=prompt, system_prompt=system_prompt)

            # Parse and validate output
            results = self.parser.parse_concert_output(response)

            # Log results
            new_discoveries = sum(1 for r in results if r.proposed_status == "new_discovery")
            verified = sum(1 for r in results if r.proposed_status == "verified")
            needs_approval = sum(1 for r in results if r.proposed_status == "needs_review")

            logger.info(
                f"Concert discovery complete: {len(results)} events, "
                f"{new_discoveries} new discoveries, {verified} verified, "
                f"{needs_approval} need approval"
            )

            return results

        except Exception as e:
            logger.error(f"Concert discovery workflow failed: {e}")
            raise