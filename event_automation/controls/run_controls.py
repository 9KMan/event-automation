"""Run/Pause/Re-run controls."""
import logging
import threading
from typing import Optional, Dict, List, Callable, Any

logger = logging.getLogger(__name__)


class RunControls:
    """Run/Pause/Re-run controls using a simple state machine."""

    STATE_IDLE = "idle"
    STATE_RUNNING = "running"
    STATE_PAUSED = "paused"

    def __init__(self):
        """Initialize RunControls."""
        self._state = self.STATE_IDLE
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused by default
        self._current_workflow = None
        self._workflow_results: Dict[str, List[Any]] = {}
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        """Get current state."""
        return self._state

    def is_running(self) -> bool:
        """Check if currently running."""
        return self._state == self.STATE_RUNNING

    def is_paused(self) -> bool:
        """Check if paused."""
        return self._state == self.STATE_PAUSED

    def run_all(self, workflows: Dict[str, Callable]) -> Dict[str, List[Any]]:
        """
        Execute all workflows.

        Args:
            workflows: Dict mapping category to async workflow function

        Returns:
            Dict mapping category to list of results
        """
        with self._lock:
            if self._state == self.STATE_RUNNING:
                logger.warning("Workflows already running")
                return self._workflow_results

            self._state = self.STATE_RUNNING
            self._pause_event.set()
            self._workflow_results = {}

        logger.info(f"Starting all workflows: {list(workflows.keys())}")

        try:
            import asyncio

            async def run_workflows():
                tasks = []
                for category, workflow_func in workflows.items():
                    task = asyncio.create_task(self._run_workflow(category, workflow_func))
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)
                return results

            results = asyncio.run(run_workflows())

            # Map results back to categories
            for category, result in zip(workflows.keys(), results):
                if isinstance(result, Exception):
                    logger.error(f"Workflow {category} failed: {result}")
                    self._workflow_results[category] = []
                else:
                    self._workflow_results[category] = result

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")

        finally:
            with self._lock:
                self._state = self.STATE_IDLE

        logger.info("All workflows completed")
        return self._workflow_results

    async def _run_workflow(self, category: str, workflow_func: Callable) -> List[Any]:
        """Run a single workflow with pause support."""
        logger.info(f"Starting workflow: {category}")

        try:
            # Check if paused before starting
            self._pause_event.wait()

            result = await workflow_func()
            logger.info(f"Workflow {category} completed")
            return result

        except Exception as e:
            logger.error(f"Workflow {category} failed: {e}")
            return []

    def pause(self) -> None:
        """Halt active runs (no new LLM calls)."""
        with self._lock:
            if self._state == self.STATE_RUNNING:
                self._state = self.STATE_PAUSED
                self._pause_event.clear()
                logger.info("Workflows paused")
            else:
                logger.warning(f"Cannot pause: not running (state={self._state})")

    def resume(self) -> None:
        """Resume paused workflows."""
        with self._lock:
            if self._state == self.STATE_PAUSED:
                self._state = self.STATE_RUNNING
                self._pause_event.set()
                logger.info("Workflows resumed")
            else:
                logger.warning(f"Cannot resume: not paused (state={self._state})")

    def rerun_category(self, category: str, workflow_func: Callable) -> List[Any]:
        """
        Re-execute specific workflow.

        Args:
            category: Category to re-run (cultural, sports, concert)
            workflow_func: Async workflow function to execute

        Returns:
            List of results
        """
        logger.info(f"Re-running workflow: {category}")

        if self._state == self.STATE_PAUSED:
            logger.warning("Cannot rerun while paused")
            return []

        import asyncio

        async def run_single():
            return await workflow_func()

        try:
            result = asyncio.run(run_single())
            with self._lock:
                self._workflow_results[category] = result
            logger.info(f"Workflow {category} rerun complete")
            return result
        except Exception as e:
            logger.error(f"Workflow {category} rerun failed: {e}")
            return []

    def get_status(self) -> Dict[str, str]:
        """
        Get current status.

        Returns:
            Dict with state and workflow results summary
        """
        with self._lock:
            return {
                "state": self._state,
                "categories": list(self._workflow_results.keys()),
                "result_counts": {
                    cat: len(results) for cat, results in self._workflow_results.items()
                },
            }