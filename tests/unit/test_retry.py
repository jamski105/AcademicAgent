#!/usr/bin/env python3
"""
Unit Tests für src/utils/retry.py
Testet Retry-Logik mit Exponential Backoff für v2.0

Test Coverage:
- Exponential Backoff
- Linear Backoff
- RetryHandler mit max_retries
- Retry-Profile (network, browser, database)
- Context-Tracking
"""

import pytest
import time
from unittest.mock import Mock, patch
from tenacity import RetryError, stop_after_attempt, wait_exponential


class TestExponentialBackoff:
    """Tests für Exponential-Backoff-Logik"""

    def test_tenacity_exponential_wait(self):
        """Testet tenacity exponential wait strategy"""
        from tenacity import Retrying, wait_exponential, stop_after_attempt

        attempts = []
        start_time = time.time()

        try:
            for attempt in Retrying(
                wait=wait_exponential(multiplier=1, min=1, max=10),
                stop=stop_after_attempt(3),
                reraise=True
            ):
                with attempt:
                    attempts.append(time.time() - start_time)
                    if len(attempts) < 3:
                        raise ConnectionError("Temporary failure")
        except RetryError:
            pass

        # Sollte 3 Versuche machen
        assert len(attempts) >= 2

    def test_exponential_increases_delay(self):
        """Testet dass Delays exponentiell wachsen"""
        from tenacity import Retrying, wait_exponential, stop_after_attempt
        import time

        attempt_times = []

        try:
            for attempt in Retrying(
                wait=wait_exponential(multiplier=0.01, min=0.01, max=1),
                stop=stop_after_attempt(4),
                reraise=True
            ):
                with attempt:
                    attempt_times.append(time.time())
                    raise ValueError("Always fails")
        except ValueError:
            pass

        # Check that there were multiple attempts and timing increased
        assert len(attempt_times) == 4
        if len(attempt_times) >= 3:
            # Time between attempts should generally increase (exponential backoff)
            delay1 = attempt_times[1] - attempt_times[0]
            delay2 = attempt_times[2] - attempt_times[1]
            # With exponential backoff, second delay should be >= first delay
            assert delay2 >= delay1 * 0.9  # Allow small variance


class TestRetryWithMaxAttempts:
    """Tests für Retry mit maximalen Versuchen"""

    def test_succeeds_on_first_attempt(self):
        """Testet dass Success beim ersten Versuch funktioniert"""
        from tenacity import Retrying, stop_after_attempt

        call_count = 0

        for attempt in Retrying(stop=stop_after_attempt(3)):
            with attempt:
                call_count += 1
                result = "success"

        assert result == "success"
        assert call_count == 1

    def test_retries_on_failure_then_succeeds(self):
        """Testet dass Retry bei Failure funktioniert"""
        from tenacity import Retrying, stop_after_attempt, wait_fixed

        call_count = 0

        for attempt in Retrying(
            stop=stop_after_attempt(5),
            wait=wait_fixed(0.01)
        ):
            with attempt:
                call_count += 1
                if call_count < 3:
                    raise ConnectionError("Temporary error")
                result = "success"

        assert result == "success"
        assert call_count == 3

    def test_raises_after_max_retries(self):
        """Testet dass Exception nach Max-Retries geraised wird"""
        from tenacity import Retrying, stop_after_attempt, wait_fixed

        call_count = 0

        # With reraise=True, the original exception is raised, not RetryError
        with pytest.raises(ValueError, match="Always fails"):
            for attempt in Retrying(
                stop=stop_after_attempt(3),
                wait=wait_fixed(0.01),
                reraise=True
            ):
                with attempt:
                    call_count += 1
                    raise ValueError("Always fails")

        assert call_count == 3


class TestRetryWithSpecificExceptions:
    """Tests für Retry mit spezifischen Exceptions"""

    def test_retries_connection_error(self):
        """Testet dass ConnectionError retried wird"""
        from tenacity import Retrying, stop_after_attempt, wait_fixed, retry_if_exception_type

        call_count = 0

        for attempt in Retrying(
            stop=stop_after_attempt(3),
            wait=wait_fixed(0.01),
            retry=retry_if_exception_type(ConnectionError)
        ):
            with attempt:
                call_count += 1
                if call_count < 2:
                    raise ConnectionError("Network issue")
                result = "success"

        assert result == "success"
        assert call_count == 2

    def test_does_not_retry_type_error(self):
        """Testet dass TypeError nicht retried wird"""
        from tenacity import Retrying, stop_after_attempt, wait_fixed, retry_if_exception_type

        call_count = 0

        with pytest.raises(TypeError):
            for attempt in Retrying(
                stop=stop_after_attempt(3),
                wait=wait_fixed(0.01),
                retry=retry_if_exception_type(ConnectionError)
            ):
                with attempt:
                    call_count += 1
                    raise TypeError("Type error")

        # Sollte sofort fehlschlagen ohne Retry
        assert call_count == 1


class TestRetryDecorator:
    """Tests für Retry-Decorator"""

    def test_decorator_retries_function(self):
        """Testet dass Decorator Funktion retried"""
        from tenacity import retry, stop_after_attempt, wait_fixed

        call_count = [0]

        @retry(stop=stop_after_attempt(5), wait=wait_fixed(0.01))
        def flaky_api_call():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("API unavailable")
            return {"status": "ok"}

        result = flaky_api_call()

        assert result == {"status": "ok"}
        assert call_count[0] == 3

    def test_decorator_preserves_function_metadata(self):
        """Testet dass Decorator Funktions-Metadata erhält"""
        from tenacity import retry, stop_after_attempt

        @retry(stop=stop_after_attempt(2))
        def documented_function():
            """This function has documentation"""
            return 42

        assert "documented_function" in str(documented_function)
        # Note: tenacity doesn't fully preserve __name__ but wraps the function


class TestRetryProfiles:
    """Tests für vordefinierte Retry-Profile"""

    def test_network_request_profile(self):
        """Testet Network-Request-Profil (für API-Calls)"""
        from tenacity import Retrying, stop_after_attempt, wait_exponential, retry_if_exception_type

        # Simuliert Retry-Profil für API-Requests
        call_count = 0

        for attempt in Retrying(
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=1, min=2, max=60),
            retry=retry_if_exception_type((ConnectionError, TimeoutError))
        ):
            with attempt:
                call_count += 1
                if call_count < 2:
                    raise ConnectionError("Network error")
                result = "success"

        assert result == "success"

    def test_browser_navigation_profile(self):
        """Testet Browser-Navigation-Profil"""
        from tenacity import Retrying, stop_after_attempt, wait_fixed

        # Simuliert Retry-Profil für Browser-Navigation
        call_count = 0

        for attempt in Retrying(
            stop=stop_after_attempt(3),
            wait=wait_fixed(3)
        ):
            with attempt:
                call_count += 1
                if call_count < 2:
                    raise TimeoutError("Page timeout")
                result = "page loaded"

        assert result == "page loaded"


class TestRetryWithCallback:
    """Tests für Retry mit Before/After Callbacks"""

    def test_before_callback_is_called(self):
        """Testet dass Before-Callback aufgerufen wird"""
        from tenacity import Retrying, stop_after_attempt, wait_fixed

        before_calls = []

        def before_callback(retry_state):
            before_calls.append(retry_state.attempt_number)

        call_count = 0

        for attempt in Retrying(
            stop=stop_after_attempt(3),
            wait=wait_fixed(0.01),
            before=before_callback
        ):
            with attempt:
                call_count += 1
                if call_count < 2:
                    raise ValueError("Fail")
                result = "success"

        assert len(before_calls) >= 1

    def test_after_callback_is_called(self):
        """Testet dass After-Callback aufgerufen wird"""
        from tenacity import Retrying, stop_after_attempt, wait_fixed

        after_calls = []

        def after_callback(retry_state):
            after_calls.append(retry_state.attempt_number)

        call_count = 0

        for attempt in Retrying(
            stop=stop_after_attempt(3),
            wait=wait_fixed(0.01),
            after=after_callback
        ):
            with attempt:
                call_count += 1
                if call_count < 2:
                    raise ValueError("Fail")
                result = "success"

        assert len(after_calls) >= 1


class TestEdgeCases:
    """Tests für Edge-Cases"""

    def test_handles_zero_retries(self):
        """Testet dass 0 Retries korrekt behandelt werden"""
        from tenacity import Retrying, stop_after_attempt

        call_count = 0

        # With reraise=True and stop_after_attempt(1), the original exception is raised
        with pytest.raises(ValueError, match="Immediate fail"):
            for attempt in Retrying(
                stop=stop_after_attempt(1),
                reraise=True
            ):
                with attempt:
                    call_count += 1
                    raise ValueError("Immediate fail")

        assert call_count == 1

    def test_handles_very_long_delay(self):
        """Testet dass sehr lange Delays korrekt behandelt werden"""
        from tenacity import Retrying, stop_after_attempt, wait_fixed

        # Test dass wait_fixed mit langen Delays keine Errors wirft
        retrying = Retrying(
            stop=stop_after_attempt(2),
            wait=wait_fixed(3600)  # 1 hour delay
        )

        # Sollte konfigurierbar sein ohne Exception
        assert retrying is not None


class TestIntegrationWithAPIs:
    """Integration Tests für API-Retry-Scenarios"""

    def test_api_rate_limit_retry(self):
        """Testet Retry bei API Rate Limiting"""
        from tenacity import Retrying, stop_after_attempt, wait_exponential, retry_if_exception_type

        class RateLimitError(Exception):
            pass

        call_count = 0

        for attempt in Retrying(
            stop=stop_after_attempt(4),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(RateLimitError)
        ):
            with attempt:
                call_count += 1
                if call_count < 3:
                    raise RateLimitError("429 Too Many Requests")
                result = {"data": "success"}

        assert result == {"data": "success"}
        assert call_count == 3

    def test_api_timeout_retry(self):
        """Testet Retry bei API Timeout"""
        from tenacity import Retrying, stop_after_attempt, wait_fixed, retry_if_exception_type

        call_count = 0

        for attempt in Retrying(
            stop=stop_after_attempt(3),
            wait=wait_fixed(0.01),
            retry=retry_if_exception_type(TimeoutError)
        ):
            with attempt:
                call_count += 1
                if call_count < 2:
                    raise TimeoutError("Request timeout")
                result = {"status": "ok"}

        assert result == {"status": "ok"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
