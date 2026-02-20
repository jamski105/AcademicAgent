#!/usr/bin/env python3
"""
Retry Enforcement Decorator - Erzwingt exponential backoff für Network-Ops

ZWECK:
    Verhindert dass Agents Retry-Logic umgehen können.
    Wrapper für CDP-Calls, WebFetch, und andere Network-Operations.

VERWENDUNG:
    from scripts.enforce_retry import with_retry

    @with_retry(max_retries=5)
    def navigate_to_database(url):
        # CDP navigation call
        return cdp_helper.navigate(url)

    # Automatischer Retry mit exponential backoff bei Timeouts/Errors

INTEGRATION:
    - Browser-Agent MUSS diesen Decorator für ALLE CDP-Navigations nutzen
    - Orchestrator kann verify via Logging ob Retries stattfanden
"""

import time
import functools
from typing import Callable, Any, Optional, List, Type
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from retry_strategy import RetryHandler, exponential_backoff, RetryEnforcementError
    from logger import get_logger
except ImportError:
    # Fallback if imports fail
    RetryHandler = None
    get_logger = None

    # Define locally if import failed
    class RetryEnforcementError(Exception):
        """Raised when retry enforcement fails"""
        pass


def with_retry(
    max_retries: int = 5,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    retryable_exceptions: Optional[List[Type[Exception]]] = None,
    operation_name: str = "network_operation",
    run_id: Optional[str] = None
):
    """
    Decorator that enforces retry logic with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds (doubles each retry)
        max_delay: Maximum delay between retries
        retryable_exceptions: List of exception types to retry on
                             (default: TimeoutError, ConnectionError)
        operation_name: Name of operation for logging
        run_id: Research run ID for logging

    Returns:
        Decorated function with automatic retry logic

    Example:
        @with_retry(max_retries=3, operation_name="CDP_navigate")
        def navigate(url):
            return cdp_helper.navigate(url)

        # Automatically retries up to 3 times with exponential backoff
    """
    # Default retryable exceptions
    if retryable_exceptions is None:
        retryable_exceptions = [
            TimeoutError,
            ConnectionError,
            ConnectionRefusedError,
        ]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Initialize logger if available
            logger = None
            if get_logger and run_id:
                try:
                    logger = get_logger("retry_enforcer", f"runs/{run_id}")
                except:
                    pass

            # Try with RetryHandler if available
            if RetryHandler:
                handler = RetryHandler(
                    max_retries=max_retries,
                    base_delay=base_delay,
                    max_delay=max_delay,
                    strategy="exponential"
                )
                handler.retryable_exceptions = retryable_exceptions

                try:
                    result = handler.execute(func, *args, **kwargs)

                    # Log success
                    if logger:
                        logger.info(
                            f"Operation succeeded",
                            operation=operation_name,
                            attempts=handler.attempts,
                            total_delay=handler.total_delay
                        )

                    return result

                except Exception as e:
                    # Log failure
                    if logger:
                        logger.error(
                            f"Operation failed after retries",
                            operation=operation_name,
                            max_retries=max_retries,
                            error=str(e)
                        )
                    raise

            # Fallback: Manual retry implementation
            else:
                last_exception = None

                for attempt in range(max_retries + 1):
                    try:
                        result = func(*args, **kwargs)

                        # Success - log if logger available
                        if logger:
                            logger.info(
                                f"Operation succeeded",
                                operation=operation_name,
                                attempts=attempt + 1
                            )

                        return result

                    except tuple(retryable_exceptions) as e:
                        last_exception = e

                        if attempt < max_retries:
                            # Calculate delay with exponential backoff
                            delay = min(base_delay * (2 ** attempt), max_delay)

                            if logger:
                                logger.warning(
                                    f"Retrying after error",
                                    operation=operation_name,
                                    attempt=attempt + 1,
                                    max_retries=max_retries,
                                    delay_seconds=delay,
                                    error=str(e)
                                )

                            time.sleep(delay)
                        else:
                            # Max retries reached
                            if logger:
                                logger.error(
                                    f"Max retries reached",
                                    operation=operation_name,
                                    max_retries=max_retries,
                                    error=str(e)
                                )

                # All retries exhausted
                raise RetryEnforcementError(
                    f"Operation '{operation_name}' failed after {max_retries} retries"
                ) from last_exception

        return wrapper
    return decorator


# Pre-configured decorators for common operations

def with_cdp_retry(run_id: Optional[str] = None):
    """Decorator for CDP operations (navigation, screenshots, etc.)"""
    return with_retry(
        max_retries=5,
        base_delay=2.0,
        max_delay=60.0,
        operation_name="CDP_operation",
        run_id=run_id
    )


def with_webfetch_retry(run_id: Optional[str] = None):
    """Decorator for WebFetch operations"""
    return with_retry(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        operation_name="WebFetch",
        run_id=run_id
    )


def with_download_retry(run_id: Optional[str] = None):
    """Decorator for PDF download operations"""
    return with_retry(
        max_retries=5,
        base_delay=3.0,
        max_delay=120.0,
        operation_name="PDF_download",
        run_id=run_id
    )


# Verification function for orchestrator
def verify_retry_enforcement(log_file: Path, operation_name: str) -> dict:
    """
    Verify that retry enforcement was used for an operation

    Args:
        log_file: Path to agent log file
        operation_name: Name of operation to verify

    Returns:
        {
            'enforced': bool,
            'attempts': int,
            'total_delay': float,
            'success': bool
        }
    """
    import json

    enforced = False
    attempts = 0
    total_delay = 0.0
    success = False

    try:
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())

                    if log_entry.get('metadata', {}).get('operation') == operation_name:
                        if 'attempts' in log_entry.get('metadata', {}):
                            enforced = True
                            attempts = log_entry['metadata']['attempts']
                            total_delay = log_entry['metadata'].get('total_delay', 0.0)

                            if 'succeeded' in log_entry['message'].lower():
                                success = True
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass

    return {
        'enforced': enforced,
        'attempts': attempts,
        'total_delay': total_delay,
        'success': success
    }


if __name__ == '__main__':
    # Test/Demo
    print("Retry Enforcement Decorator - Demo")
    print("=" * 50)

    @with_retry(max_retries=3, operation_name="demo_operation")
    def flaky_function(fail_count=2):
        """Demo function that fails N times before succeeding"""
        if not hasattr(flaky_function, 'call_count'):
            flaky_function.call_count = 0

        flaky_function.call_count += 1

        if flaky_function.call_count <= fail_count:
            print(f"  Attempt {flaky_function.call_count}: FAIL (raising TimeoutError)")
            raise TimeoutError(f"Simulated timeout (attempt {flaky_function.call_count})")

        print(f"  Attempt {flaky_function.call_count}: SUCCESS")
        return "Success!"

    try:
        result = flaky_function(fail_count=2)
        print(f"\nResult: {result}")
        print(f"Total attempts: {flaky_function.call_count}")
    except Exception as e:
        print(f"\nFailed: {e}")
