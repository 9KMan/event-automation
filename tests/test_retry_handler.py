"""Unit tests for RetryHandler."""
import pytest
import time
from unittest.mock import patch, MagicMock

from event_automation.orchestration.retry_handler import RetryHandler, with_retry


class TestRetryHandler:
    """Tests for RetryHandler class."""

    def test_successful_call_no_retries(self):
        """Test that successful calls don't trigger retries."""
        handler = RetryHandler(max_retries=3)

        def successful_func():
            return "success"

        wrapper = handler.with_retry(successful_func)
        result = wrapper()

        assert result == "success"

    def test_retry_on_failure(self):
        """Test that failures trigger retries with exponential backoff."""
        handler = RetryHandler(max_retries=2, base_delay=0.1)
        call_count = 0

        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        wrapper = handler.with_retry(flaky_func)
        start = time.time()
        result = wrapper()
        elapsed = time.time() - start

        assert result == "success"
        assert call_count == 3

        # With base_delay=0.1 and 2 retries: delays of 0.2 and 0.4 = 0.6 total minimum
        # Allow some margin for test execution
        assert elapsed >= 0.5

    def test_max_retries_exceeded(self):
        """Test that max retries are respected."""
        handler = RetryHandler(max_retries=2, base_delay=0.01)
        call_count = 0

        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        wrapper = handler.with_retry(always_fail)

        with pytest.raises(ValueError, match="Always fails"):
            wrapper()

        assert call_count == 3  # Initial + 2 retries

    def test_retry_handler_default_values(self):
        """Test retry handler with default values."""
        handler = RetryHandler()

        assert handler.max_retries == 3
        assert handler.base_delay == 1.0

    def test_custom_max_retries(self):
        """Test custom max_retries parameter."""
        handler = RetryHandler(max_retries=5)
        assert handler.max_retries == 5


class TestWithRetryDecorator:
    """Tests for with_retry decorator."""

    def test_decorator_no_args(self):
        """Test @with_retry with no arguments."""
        @with_retry
        def might_fail():
            return "success"

        result = might_fail()
        assert result == "success"

    def test_decorator_with_max_retries(self):
        """Test @with_retry(max_retries=N)."""
        call_count = 0

        @with_retry(max_retries=1)
        def might_fail():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Fail once")
            return "success"

        result = might_fail()
        assert result == "success"
        assert call_count == 2

    def test_decorator_fail_all_retries(self):
        """Test that decorator raises after all retries."""
        call_count = 0

        @with_retry(max_retries=2)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fail")

        with pytest.raises(ValueError):
            always_fail()

        assert call_count == 3

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""
        @with_retry
        def my_function():
            """My docstring."""
            return "result"

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."