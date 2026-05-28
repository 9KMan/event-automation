"""CLI entrypoint for event_automation."""
import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

# Try to load .env file
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()

from event_automation.config import config
from event_automation.orchestration import Router, Batcher, RetryHandler, DoubleCheck, ConflictHandler
from event_automation.workflows import CulturalWorkflow, SportsWorkflow, ConcertWorkflow
from event_automation.llm import LLMClient, PromptTemplates, OutputParser, LLMCache
from event_automation.data import Intake, ReviewOutput, Export
from event_automation.controls import RunControls
from event_automation.models import Event

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_run(args):
    """Run all workflows."""
    logger.info("Starting event automation run...")

    # Check API key
    if not config.LLM_API_KEY:
        logger.error("LLM_API_KEY not set. Please configure your .env file.")
        sys.exit(1)

    # Initialize components
    llm_client = LLMClient()
    run_controls = RunControls()

    # Load events if intake path provided
    events = []
    if args.intake:
        try:
            intake = Intake()
            events = intake.load_events(args.intake)
            logger.info(f"Loaded {len(events)} events from {args.intake}")
        except Exception as e:
            logger.error(f"Failed to load events: {e}")
            sys.exit(1)

    # Define workflows
    workflows = {
        "cultural": lambda: CulturalWorkflow().run(
            [e for e in events if e.category == "cultural"], llm_client
        ),
        "sports": lambda: SportsWorkflow().run(
            [e for e in events if e.category == "sports"], llm_client
        ),
        "concert": lambda: ConcertWorkflow().run(
            [e for e in events if e.category == "concert"], llm_client
        ),
    }

    # Run all
    results = run_controls.run_all(workflows)

    # Summary
    total = sum(len(r) for r in results.values())
    logger.info(f"Run complete: {total} events processed across {len(results)} categories")
    logger.info(f"LLM calls: {llm_client.call_count}, tokens: {llm_client.total_tokens}")

    # Export if output path provided
    if args.output:
        try:
            exporter = Export()
            exporter.export_events(events, args.output)
            logger.info(f"Exported events to {args.output}")
        except Exception as e:
            logger.error(f"Failed to export: {e}")

    # Generate review if requested
    if args.review:
        try:
            # Collect review items from results
            from event_automation.models import ReviewItem

            review_items = []
            for category, category_results in results.items():
                for result in category_results:
                    # Create review items for low confidence or conflicts
                    if result.confidence < 0.6 or result.proposed_status in ["conflict", "uncertain"]:
                        # This is simplified - in production you'd correlate with original events
                        pass

            reviewer = ReviewOutput()
            review_bytes = reviewer.generate_review(review_items)
            if review_bytes:
                with open(args.review, "wb") as f:
                    f.write(review_bytes)
                logger.info(f"Generated review at {args.review}")
        except Exception as e:
            logger.error(f"Failed to generate review: {e}")

    logger.info("Run command completed")


def cmd_pause(args):
    """Pause active runs."""
    run_controls = RunControls()
    run_controls.pause()
    logger.info("Pause command issued")


def cmd_status(args):
    """Show current state."""
    run_controls = RunControls()
    status = run_controls.get_status()

    print(f"State: {status['state']}")
    print(f"Categories: {', '.join(status['categories']) or 'none'}")
    for cat, count in status["result_counts"].items():
        print(f"  {cat}: {count} results")


def main():
    """Main entrypoint."""
    parser = argparse.ArgumentParser(
        description="Lean Agentic Event Data Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run all workflows")
    run_parser.add_argument(
        "--intake", "-i", help="Path to event data file (CSV or JSON)"
    )
    run_parser.add_argument(
        "--output", "-o", help="Path to export output file (CSV or JSON)"
    )
    run_parser.add_argument(
        "--review", "-r", help="Path to review spreadsheet output (XLSX)"
    )
    run_parser.set_defaults(func=cmd_run)

    # Pause command
    pause_parser = subparsers.add_parser("pause", help="Pause active runs")
    pause_parser.set_defaults(func=cmd_pause)

    # Status command
    status_parser = subparsers.add_parser("status", help="Show current state")
    status_parser.set_defaults(func=cmd_status)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()