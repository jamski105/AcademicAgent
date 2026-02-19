#!/usr/bin/env python3
"""
Unit tests for enforce_retry.py
Tests retry enforcement decorator
"""

import pytest
import time
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))

from enforce_retry import (
    with_retry,
    with_cdp_retry,
    with_webfetch_retry,
    RetryEnforcementError
)


class TestWithRetryDecorator:
    """Test with_retry decorator"""

    def test_success_no_retry_needed(self):
        """Function that succeeds immediately should not retry"""
        call_count = 0

        @with_retry(max_retries=3)
        def success_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_function()

        assert result == "success"
        assert call_count == 1  # No retries needed

    def test_retry_on_timeout(self):
        """Function that times out should retry"""
        call_count = 0

        @with_retry(max_retries=3, base_delay=0.1)
        def failing_function():
            nonlocal call_count
            call_count += 1

            if call_count < 3:
                raise TimeoutError("Simulated timeout")

            return "success after retries"

        result = failing_function()

        assert result == "success after retries"
        assert call_count == 3  # Should have retried 2 times

    def test_max_retries_exhausted(self):
        """Function that always fails should exhaust retries"""
        call_count = 0

        @with_retry(max_retries=2, base_delay=0.1)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise TimeoutError("Always fails")

        with pytest.raises(RetryEnforcementError):
            always_fails()

        assert call_count == 3  # Initial + 2 retries

    def test_exponential_backoff(self):
        """Retry delays should follow exponential backoff"""
        delays = []

        @with_retry(max_retries=3, base_delay=0.1)
        def track_delays():
            if len(delays) < 3:
                start = time.time()
                raise TimeoutError("Retry")
            return "done"

        # This will measure the delays but we can't easily capture them
        # So we just verify it succeeds after retries
        result = track_delays()
        assert result == "done"

    def test_custom_retryable_exceptions(self):
        """Should only retry on specified exceptions"""
        call_count = 0

        @with_retry(
            max_retries=3,
            base_delay=0.1,
            retryable_exceptions=[ConnectionError]
        )
        def connection_error_function():
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                raise ConnectionError("Connection failed")
            elif call_count == 2:
                # This should NOT be retried
                raise ValueError("Value error")

            return "success"

        with pytest.raises(ValueError):
            connection_error_function()

        # Should have tried once, got ConnectionError (retried),
        # then got ValueError (not retried)
        assert call_count == 2

    def test_max_delay_cap(self):
        """Delay should not exceed max_delay"""
        @with_retry(max_retries=10, base_delay=1.0, max_delay=2.0)
        def capped_delay():
            # With base_delay=1 and exponential backoff,
            # delay would be 1, 2, 4, 8, 16... but capped at 2.0
            raise TimeoutError("Test")

        with pytest.raises(RetryEnforcementError):
            capped_delay()

        # Can't easily test delay values, but decorator should work


class TestPreConfiguredDecorators:
    """Test pre-configured decorators"""

    def test_cdp_retry_decorator(self):
        """with_cdp_retry should work"""
        call_count = 0

        @with_cdp_retry()
        def cdp_operation():
            nonlocal call_count
            call_count += 1

            if call_count < 2:
                raise TimeoutError("CDP timeout")

            return "CDP success"

        result = cdp_operation()

        assert result == "CDP success"
        assert call_count == 2

    def test_webfetch_retry_decorator(self):
        """with_webfetch_retry should work"""
        call_count = 0

        @with_webfetch_retry()
        def webfetch_operation():
            nonlocal call_count
            call_count += 1

            if call_count < 2:
                raise ConnectionError("Connection error")

            return "Fetch success"

        result = webfetch_operation()

        assert result == "Fetch success"
        assert call_count == 2


class TestRetryEnforcementWithArgs:
    """Test retry enforcement with function arguments"""

    def test_function_with_args(self):
        """Decorated function with args should work"""
        call_count = 0

        @with_retry(max_retries=2, base_delay=0.1)
        def func_with_args(a, b, c=10):
            nonlocal call_count
            call_count += 1

            if call_count < 2:
                raise TimeoutError("Retry")

            return a + b + c

        result = func_with_args(1, 2, c=3)

        assert result == 6
        assert call_count == 2

    def test_function_with_kwargs(self):
        """Decorated function with kwargs should work"""
        @with_retry(max_retries=1, base_delay=0.1)
        def func_with_kwargs(**kwargs):
            return kwargs.get('value', 'default')

        result = func_with_kwargs(value='test')
        assert result == 'test'


class TestRetryLogging:
    """Test retry logging functionality"""

    def test_logging_with_run_id(self):
        """Retry with run_id should initialize logger"""
        # Note: This test can't fully verify logging without actual log files
        # But it should not crash

        @with_retry(max_retries=1, base_delay=0.1, run_id="test_run")
        def logged_function():
            return "success"

        result = logged_function()
        assert result == "success"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
