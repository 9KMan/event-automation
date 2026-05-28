"""RetryHandler - Exponential backoff for transient failures."""
import logging
import time
from functools import wraps
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryHandler:
    """Exponential backoff for transient failures."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """
        Initialize RetryHandler.

        Args:
            max_retries: Maximum number of retry attempts (default 3)
            base_delay: Base delay in seconds for exponential backoff (default 1.0)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay

    def with_retry(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator that retries a function with exponential backoff.

        Args:
            func: Function to retry

        Returns:
            Wrapped function with retry logic
        """
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(self.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < self.max_retries:
                        delay = self.base_delay * (2 ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {self.max_retries + 1} attempts failed for {func.__name__}"
                        )

            raise last_exception

        return wrapper

    async def with_retry_async(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Async version of with_retry decorator.

        Args:
            func: Async function to retry

        Returns:
            Wrapped async function with retry logic
        """
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            import asyncio

            last_exception = None

            for attempt in range(self.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < self.max_retries:
                        delay = self.base_delay * (2 ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {self.max_retries + 1} attempts failed for {func.__name__}"
                        )

            raise last_exception

        return wrapper


def with_retry(func: Callable[..., T] = None, max_retries: int = 3) -> Callable[..., T]:
    """
    Decorator for exponential backoff retry.

    Usage:
        @with_retry
        def my_function():
            ...

        @with_retry(max_retries=5)
        def my_function():
            ...
    """
    if func is None:
        # Called with arguments: @with_retry(max_retries=5)
        def decorator(f: Callable[..., T]) -> Callable[..., T]:
            handler = RetryHandler(max_retries=max_retries)
            return handler.with_retry(f)

        return decorator
    else:
        # Called without arguments: @with_retry
        handler = RetryHandler(max_retries=max_retries)
        return handler.with_retry(func)