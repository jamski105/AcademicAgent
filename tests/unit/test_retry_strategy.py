#!/usr/bin/env python3
"""
Unit-Tests für retry_strategy.py
Testet Exponential-Backoff und Retry-Handler
"""

import pytest
import sys
import time
from pathlib import Path

# Füge scripts/ zu Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from retry_strategy import (
    exponential_backoff,
    linear_backoff,
    RetryHandler,
    retry_with_backoff,
    RetryProfiles
)


class TestExponentialBackoff:
    """Tests für Exponential-Backoff-Funktion"""

    def test_first_attempt_returns_base_delay(self):
        """Testet dass erster Versuch Base-Delay zurückgibt"""
        delay = exponential_backoff(attempt=0, base_delay=2, jitter=False)
        assert delay == 2.0

    def test_second_attempt_doubles_delay(self):
        """Testet dass zweiter Versuch Delay verdoppelt"""
        delay = exponential_backoff(attempt=1, base_delay=2, jitter=False)
        assert delay == 4.0

    def test_third_attempt_quadruples_delay(self):
        """Testet dass dritter Versuch Delay vervierfacht"""
        delay = exponential_backoff(attempt=2, base_delay=2, jitter=False)
        assert delay == 8.0

    def test_respects_max_delay(self):
        """Testet dass Max-Delay respektiert wird"""
        delay = exponential_backoff(attempt=10, base_delay=2, max_delay=30, jitter=False)
        assert delay == 30.0

    def test_adds_jitter_when_enabled(self):
        """Testet dass Jitter hinzugefügt wird"""
        delay_without_jitter = exponential_backoff(attempt=2, base_delay=2, jitter=False)
        delay_with_jitter = exponential_backoff(attempt=2, base_delay=2, jitter=True)

        # Mit Jitter sollte Delay leicht unterschiedlich sein
        # (kann gleich sein wenn Jitter zufällig 0 ist, aber meist unterschiedlich)
        assert delay_with_jitter >= delay_without_jitter
        assert delay_with_jitter <= delay_without_jitter * 1.1


class TestLinearBackoff:
    """Tests für Linear-Backoff-Funktion"""

    def test_first_attempt_returns_increment(self):
        """Testet dass erster Versuch Increment zurückgibt"""
        delay = linear_backoff(attempt=0, increment=5, jitter=False)
        assert delay == 5.0

    def test_second_attempt_adds_increment(self):
        """Testet dass zweiter Versuch Increment addiert"""
        delay = linear_backoff(attempt=1, increment=5, jitter=False)
        assert delay == 10.0

    def test_third_attempt_adds_twice_increment(self):
        """Testet dass dritter Versuch 2x Increment addiert"""
        delay = linear_backoff(attempt=2, increment=5, jitter=False)
        assert delay == 15.0

    def test_respects_max_delay(self):
        """Testet dass Max-Delay respektiert wird"""
        delay = linear_backoff(attempt=10, increment=5, max_delay=30, jitter=False)
        assert delay == 30.0


class TestRetryHandler:
    """Tests für RetryHandler-Klasse"""

    def test_succeeds_on_first_attempt(self):
        """Testet dass Success beim ersten Versuch funktioniert"""
        handler = RetryHandler(max_retries=3, base_delay=0.1)

        def successful_function():
            return "success"

        result = handler.execute(successful_function)

        assert result == "success"
        assert handler.attempts == 1

    def test_retries_on_failure_then_succeeds(self):
        """Testet dass Retry bei Failure funktioniert"""
        handler = RetryHandler(max_retries=3, base_delay=0.1)

        call_count = [0]

        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("Temporary error")
            return "success"

        result = handler.execute(flaky_function)

        assert result == "success"
        assert call_count[0] == 3
        assert handler.attempts == 3

    def test_raises_after_max_retries(self):
        """Testet dass Exception nach Max-Retries geraised wird"""
        handler = RetryHandler(max_retries=2, base_delay=0.1)

        def always_failing_function():
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            handler.execute(always_failing_function)

        assert handler.attempts == 3  # 1 initial + 2 retries

    def test_does_not_retry_non_retryable_exception(self):
        """Testet dass nicht-retrybare Exceptions nicht retried werden"""
        handler = RetryHandler(
            max_retries=3,
            base_delay=0.1,
            retryable_exceptions=[ConnectionError]
        )

        def function_with_type_error():
            raise TypeError("Type error")

        with pytest.raises(TypeError):
            handler.execute(function_with_type_error)

        # Sollte sofort fehlschlagen ohne Retry
        assert handler.attempts == 1

    def test_exponential_strategy(self):
        """Testet Exponential-Strategie"""
        handler = RetryHandler(
            max_retries=2,
            base_delay=1,
            strategy="exponential"
        )

        delays = []
        for i in range(3):
            delay = handler.get_delay(i)
            delays.append(delay)

        # Delays sollten exponentiell wachsen
        assert delays[1] > delays[0]
        assert delays[2] > delays[1]
        assert delays[1] >= delays[0] * 1.8  # ~2x (mit Jitter)

    def test_linear_strategy(self):
        """Testet Linear-Strategie"""
        handler = RetryHandler(
            max_retries=2,
            base_delay=5,
            strategy="linear"
        )

        delays = []
        for i in range(3):
            delay = handler.get_delay(i)
            delays.append(delay)

        # Delays sollten linear wachsen
        assert delays[1] > delays[0]
        assert delays[2] > delays[1]


class TestRetryDecorator:
    """Tests für retry_with_backoff Decorator"""

    def test_decorator_retries_function(self):
        """Testet dass Decorator Funktion retried"""
        call_count = [0]

        @retry_with_backoff(max_retries=3, base_delay=0.1)
        def flaky_api_call():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("API unavailable")
            return {"status": "ok"}

        result = flaky_api_call()

        assert result == {"status": "ok"}
        assert call_count[0] == 2

    def test_decorator_preserves_function_metadata(self):
        """Testet dass Decorator Funktions-Metadata erhält"""

        @retry_with_backoff(max_retries=2)
        def documented_function():
            """This function has documentation"""
            return 42

        assert documented_function.__name__ == "documented_function"
        assert "documentation" in documented_function.__doc__


class TestRetryProfiles:
    """Tests für vordefinierte Retry-Profile"""

    def test_network_request_profile(self):
        """Testet Network-Request-Profil"""
        handler = RetryProfiles.network_request()

        assert handler.max_retries == 5
        assert handler.strategy == "exponential"
        assert handler.base_delay == 2.0

    def test_browser_navigation_profile(self):
        """Testet Browser-Navigation-Profil"""
        handler = RetryProfiles.browser_navigation()

        assert handler.max_retries == 3
        assert handler.strategy == "linear"
        assert handler.base_delay == 3.0

    def test_database_query_profile(self):
        """Testet Database-Query-Profil"""
        handler = RetryProfiles.database_query()

        assert handler.max_retries == 4
        assert handler.strategy == "exponential"

    def test_captcha_retry_profile(self):
        """Testet CAPTCHA-Retry-Profil"""
        handler = RetryProfiles.captcha_retry()

        assert handler.max_retries == 2
        assert handler.base_delay == 30.0


class TestContextTracking:
    """Tests für Kontext-Tracking"""

    def test_tracks_total_delay(self):
        """Testet dass Total-Delay getrackt wird"""
        handler = RetryHandler(max_retries=2, base_delay=0.1)

        call_count = [0]

        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Fail")
            return "success"

        handler.execute(flaky_function)

        # Total-Delay sollte ungefähr base_delay sein (ein Retry)
        assert handler.total_delay >= 0.1
        assert handler.total_delay < 0.3  # Mit Jitter

    def test_passes_context_to_logger(self):
        """Testet dass Kontext an Logger übergeben wird"""
        handler = RetryHandler(max_retries=1, base_delay=0.1)

        def test_function():
            return "ok"

        result = handler.execute(
            test_function,
            context={"database": "IEEE", "phase": 2}
        )

        assert result == "ok"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
