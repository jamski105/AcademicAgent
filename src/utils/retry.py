"""
Retry Logic für Academic Agent v2.3+

Nutzt tenacity für robuste Retry-Mechanik:
- Exponential Backoff
- Retry bei spezifischen Status Codes
- Max Attempts
- Async Support

Usage:
    # Decorator
    @retry_on_api_error
    def fetch_data():
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    # Manual
    result = retry_api_call(lambda: api.search(...))
"""

from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    RetryError
)
import logging

# Setup Logging
logger = logging.getLogger(__name__)

# Type hints
T = TypeVar('T')


# ============================================
# Exception Classes
# ============================================

class APIError(Exception):
    """Base API Error"""
    pass


class RateLimitError(APIError):
    """Rate Limit erreicht (429)"""
    pass


class ServerError(APIError):
    """Server Error (5xx)"""
    pass


class TemporaryError(APIError):
    """Temporary Error (retryable)"""
    pass


# ============================================
# Retry Decorators
# ============================================

def retry_on_api_error(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    min_wait: float = 1.0,
    max_wait: float = 10.0
):
    """
    Retry Decorator für API-Calls

    Retry bei:
    - RateLimitError (429)
    - ServerError (500, 502, 503, 504)
    - TemporaryError

    Args:
        max_attempts: Max Retry-Versuche
        backoff_factor: Exponential Backoff Factor
        min_wait: Min Wartezeit (Sekunden)
        max_wait: Max Wartezeit (Sekunden)

    Example:
        @retry_on_api_error(max_attempts=3)
        def fetch_papers(query):
            response = requests.get(api_url, params={"q": query})
            if response.status_code == 429:
                raise RateLimitError()
            response.raise_for_status()
            return response.json()
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(
            multiplier=backoff_factor,
            min=min_wait,
            max=max_wait
        ),
        retry=retry_if_exception_type((
            RateLimitError,
            ServerError,
            TemporaryError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )


def retry_on_network_error(
    max_attempts: int = 3,
    backoff_factor: float = 2.0
):
    """
    Retry Decorator für Network Errors

    Retry bei:
    - ConnectionError
    - TimeoutError
    - OSError

    Args:
        max_attempts: Max Retry-Versuche
        backoff_factor: Exponential Backoff Factor
    """
    import requests.exceptions

    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=backoff_factor, min=1, max=10),
        retry=retry_if_exception_type((
            ConnectionError,
            TimeoutError,
            OSError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )


# ============================================
# Manual Retry Functions
# ============================================

def retry_api_call(
    func: Callable[[], T],
    max_attempts: int = 3,
    backoff_factor: float = 2.0
) -> T:
    """
    Manuelle Retry-Logik für API-Calls

    Args:
        func: Funktion die ausgeführt werden soll
        max_attempts: Max Retry-Versuche
        backoff_factor: Exponential Backoff Factor

    Returns:
        Result von func()

    Raises:
        RetryError: Wenn alle Attempts fehlschlagen

    Example:
        result = retry_api_call(
            lambda: api.search(query),
            max_attempts=3
        )
    """
    @retry_on_api_error(max_attempts=max_attempts, backoff_factor=backoff_factor)
    def _wrapped():
        return func()

    return _wrapped()


def retry_with_backoff(max_attempts: int = 3, backoff_factor: float = 2.0):
    """
    Simple retry decorator with exponential backoff

    Convenience wrapper for retry_on_api_error that catches all exceptions.
    Useful for general-purpose retrying.

    Args:
        max_attempts: Max retry attempts
        backoff_factor: Exponential backoff factor

    Example:
        @retry_with_backoff(max_attempts=3)
        def fetch_data():
            return api.get("/data")
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=backoff_factor, min=1, max=10),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )


def retry_with_fallback(
    primary: Callable[[], T],
    fallback: Callable[[], T],
    max_attempts: int = 3
) -> T:
    """
    Retry mit Fallback-Function

    Args:
        primary: Primäre Funktion
        fallback: Fallback-Funktion (wenn primary fehlschlägt)
        max_attempts: Max Attempts für primary

    Returns:
        Result von primary() oder fallback()

    Example:
        result = retry_with_fallback(
            primary=lambda: crossref_api.search(query),
            fallback=lambda: openalex_api.search(query)
        )
    """
    try:
        return retry_api_call(primary, max_attempts=max_attempts)
    except (RetryError, Exception) as e:
        logger.warning(f"Primary function failed after {max_attempts} attempts. Using fallback. Error: {e}")
        return fallback()


# ============================================
# HTTP Status Code Helpers
# ============================================

def should_retry_status_code(status_code: int) -> bool:
    """
    Prüft ob HTTP Status Code retry-bar ist

    Args:
        status_code: HTTP Status Code

    Returns:
        True wenn retryable, False sonst
    """
    RETRYABLE_CODES = {
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504,  # Gateway Timeout
    }
    return status_code in RETRYABLE_CODES


def raise_for_status_with_retry(response) -> None:
    """
    Raise Exception basierend auf Status Code

    Args:
        response: requests.Response object

    Raises:
        RateLimitError: Bei 429
        ServerError: Bei 5xx
        HTTPError: Bei anderen Errors
    """
    if response.status_code == 429:
        raise RateLimitError(f"Rate limit exceeded: {response.text}")
    elif 500 <= response.status_code < 600:
        raise ServerError(f"Server error ({response.status_code}): {response.text}")
    else:
        response.raise_for_status()


# ============================================
# Config-based Retry
# ============================================

def create_retry_decorator_from_config(retry_config: dict):
    """
    Erstellt Retry Decorator aus Config

    Args:
        retry_config: Retry Config Dict (aus api_config.yaml)

    Returns:
        Retry Decorator

    Example:
        retry_config = {
            "max_attempts": 3,
            "backoff_factor": 2.0,
            "retry_on_status_codes": [429, 500, 502, 503, 504]
        }
        decorator = create_retry_decorator_from_config(retry_config)

        @decorator
        def my_api_call():
            ...
    """
    return retry_on_api_error(
        max_attempts=retry_config.get("max_attempts", 3),
        backoff_factor=retry_config.get("backoff_factor", 2.0)
    )


# ============================================
# Testing
# ============================================

def _run_tests():
    """
    Test Retry Logic

    Run:
        python src/utils/retry.py
    """
    import time

    print("Testing retry logic...")

    # Test 1: Successful call
    @retry_on_api_error(max_attempts=3)
    def successful_call():
        print("  - Executing successful_call()")
        return "success"

    result = successful_call()
    print(f"✅ Test 1 passed: {result}")

    # Test 2: Retry after failure
    attempt_count = 0

    @retry_on_api_error(max_attempts=3, min_wait=0.1, max_wait=1)
    def failing_call():
        nonlocal attempt_count
        attempt_count += 1
        print(f"  - Attempt {attempt_count}")
        if attempt_count < 3:
            raise TemporaryError("Temporary failure")
        return "success after retries"

    try:
        result = failing_call()
        print(f"✅ Test 2 passed: {result} (after {attempt_count} attempts)")
    except RetryError:
        print(f"❌ Test 2 failed: Max attempts reached")

    # Test 3: Status code check
    assert should_retry_status_code(429) == True
    assert should_retry_status_code(500) == True
    assert should_retry_status_code(200) == False
    print("✅ Test 3 passed: Status code checks")

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    _run_tests()
