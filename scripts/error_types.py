#!/usr/bin/env python3

"""
Error Types & Recovery Strategies - AcademicAgent
Structured error handling with automatic recovery
"""

from enum import Enum
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
import time


class ErrorType(Enum):
    """Structured error types"""

    # Browser/CDP errors
    CDP_CONNECTION = "CDP_CONNECTION"
    BROWSER_CRASH = "BROWSER_CRASH"
    NAVIGATION_TIMEOUT = "NAVIGATION_TIMEOUT"
    ELEMENT_NOT_FOUND = "ELEMENT_NOT_FOUND"

    # Authentication errors
    LOGIN_REQUIRED = "LOGIN_REQUIRED"
    CAPTCHA_DETECTED = "CAPTCHA_DETECTED"
    SESSION_EXPIRED = "SESSION_EXPIRED"

    # Network errors
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    DNS_ERROR = "DNS_ERROR"

    # Database errors
    DATABASE_UNAVAILABLE = "DATABASE_UNAVAILABLE"
    PAYWALL = "PAYWALL"
    NO_ACCESS = "NO_ACCESS"

    # Data errors
    INVALID_CONFIG = "INVALID_CONFIG"
    MISSING_FILE = "MISSING_FILE"
    PARSE_ERROR = "PARSE_ERROR"

    # Phase errors
    PHASE_TIMEOUT = "PHASE_TIMEOUT"
    PHASE_INCOMPLETE = "PHASE_INCOMPLETE"

    # Unknown
    UNKNOWN = "UNKNOWN"


class RecoveryStrategy(Enum):
    """Recovery strategies"""

    RETRY = "RETRY"  # Automatic retry
    RETRY_WITH_DELAY = "RETRY_WITH_DELAY"  # Retry after delay
    USER_INTERVENTION = "USER_INTERVENTION"  # Needs user action
    SKIP = "SKIP"  # Skip and continue
    FALLBACK = "FALLBACK"  # Use fallback strategy
    ABORT = "ABORT"  # Abort operation


@dataclass
class ErrorConfig:
    """Error configuration"""

    error_type: ErrorType
    max_retries: int = 3
    retry_delay_seconds: int = 5
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY
    user_message: Optional[str] = None
    recovery_action: Optional[Callable] = None


# Error configurations with recovery strategies
ERROR_CONFIGS: Dict[ErrorType, ErrorConfig] = {
    ErrorType.CDP_CONNECTION: ErrorConfig(
        error_type=ErrorType.CDP_CONNECTION,
        max_retries=3,
        retry_delay_seconds=5,
        recovery_strategy=RecoveryStrategy.RETRY_WITH_DELAY,
        user_message=(
            "Chrome-CDP-Verbindung verloren. Automatischer Neustart wird versucht..."
        ),
    ),
    ErrorType.BROWSER_CRASH: ErrorConfig(
        error_type=ErrorType.BROWSER_CRASH,
        max_retries=2,
        retry_delay_seconds=10,
        recovery_strategy=RecoveryStrategy.USER_INTERVENTION,
        user_message=(
            "Browser abgestürzt. Bitte starte Chrome neu mit:\n"
            "  bash scripts/smart_chrome_setup.sh\n"
            "Drücke dann ENTER um fortzufahren."
        ),
    ),
    ErrorType.LOGIN_REQUIRED: ErrorConfig(
        error_type=ErrorType.LOGIN_REQUIRED,
        max_retries=1,
        retry_delay_seconds=0,
        recovery_strategy=RecoveryStrategy.USER_INTERVENTION,
        user_message=(
            "Login erforderlich. Bitte:\n"
            "  1. Wechsle zum Chrome-Fenster\n"
            "  2. Melde dich mit deinen Zugangsdaten an\n"
            "  3. Drücke ENTER wenn fertig"
        ),
    ),
    ErrorType.CAPTCHA_DETECTED: ErrorConfig(
        error_type=ErrorType.CAPTCHA_DETECTED,
        max_retries=1,
        retry_delay_seconds=30,
        recovery_strategy=RecoveryStrategy.USER_INTERVENTION,
        user_message=(
            "CAPTCHA erkannt. Bitte:\n"
            "  1. Wechsle zum Chrome-Fenster\n"
            "  2. Löse das CAPTCHA\n"
            "  3. Drücke ENTER wenn fertig"
        ),
    ),
    ErrorType.RATE_LIMIT: ErrorConfig(
        error_type=ErrorType.RATE_LIMIT,
        max_retries=3,
        retry_delay_seconds=60,
        recovery_strategy=RecoveryStrategy.RETRY_WITH_DELAY,
        user_message="Rate-Limit erreicht. Warte 60 Sekunden vor erneutem Versuch...",
    ),
    ErrorType.NAVIGATION_TIMEOUT: ErrorConfig(
        error_type=ErrorType.NAVIGATION_TIMEOUT,
        max_retries=2,
        retry_delay_seconds=10,
        recovery_strategy=RecoveryStrategy.RETRY_WITH_DELAY,
        user_message="Navigations-Timeout. Versuche erneut...",
    ),
    ErrorType.ELEMENT_NOT_FOUND: ErrorConfig(
        error_type=ErrorType.ELEMENT_NOT_FOUND,
        max_retries=3,
        retry_delay_seconds=5,
        recovery_strategy=RecoveryStrategy.FALLBACK,
        user_message="UI-Element nicht gefunden. Versuche Fallback-Selektoren...",
    ),
    ErrorType.DATABASE_UNAVAILABLE: ErrorConfig(
        error_type=ErrorType.DATABASE_UNAVAILABLE,
        max_retries=2,
        retry_delay_seconds=30,
        recovery_strategy=RecoveryStrategy.SKIP,
        user_message=(
            "Datenbank nicht verfügbar. Überspringe und fahre mit anderen "
            "Datenbanken fort..."
        ),
    ),
    ErrorType.PAYWALL: ErrorConfig(
        error_type=ErrorType.PAYWALL,
        max_retries=0,
        retry_delay_seconds=0,
        recovery_strategy=RecoveryStrategy.SKIP,
        user_message="Paywall erkannt. Überspringe Quelle...",
    ),
    ErrorType.SESSION_EXPIRED: ErrorConfig(
        error_type=ErrorType.SESSION_EXPIRED,
        max_retries=1,
        retry_delay_seconds=0,
        recovery_strategy=RecoveryStrategy.USER_INTERVENTION,
        user_message=(
            "Session abgelaufen. Bitte:\n"
            "  1. Wechsle zum Chrome-Fenster\n"
            "  2. Melde dich erneut an\n"
            "  3. Drücke ENTER wenn fertig"
        ),
    ),
    ErrorType.INVALID_CONFIG: ErrorConfig(
        error_type=ErrorType.INVALID_CONFIG,
        max_retries=0,
        retry_delay_seconds=0,
        recovery_strategy=RecoveryStrategy.ABORT,
        user_message="Ungültige Konfiguration. Bitte korrigiere und starte neu.",
    ),
}


class ErrorHandler:
    """Error handler with automatic recovery"""

    def __init__(self, logger=None):
        self.logger = logger
        self.error_counts: Dict[ErrorType, int] = {}

    def handle_error(
        self,
        error_type: ErrorType,
        context: Optional[Dict[str, Any]] = None,
        custom_message: Optional[str] = None,
    ) -> RecoveryStrategy:
        """
        Handle error and return recovery strategy

        Returns:
            RecoveryStrategy to execute
        """
        config = ERROR_CONFIGS.get(
            error_type,
            ErrorConfig(
                error_type=ErrorType.UNKNOWN,
                recovery_strategy=RecoveryStrategy.ABORT,
            ),
        )

        # Track error count
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1

        # Check if max retries exceeded
        if self.error_counts[error_type] > config.max_retries:
            if self.logger:
                self.logger.error(
                    f"Max retries exceeded for {error_type.value}",
                    error_type=error_type.value,
                    retry_count=self.error_counts[error_type],
                    context=context,
                )
            print(
                f"\n❌ Maximale Retries für {error_type.value} überschritten. Abbruch."
            )
            return RecoveryStrategy.ABORT

        # Log error
        if self.logger:
            self.logger.warning(
                f"Error: {error_type.value}",
                error_type=error_type.value,
                retry_count=self.error_counts[error_type],
                context=context,
            )

        # Display user message
        message = custom_message or config.user_message
        if message:
            print(f"\n⚠️  {message}\n")

        # Execute recovery strategy
        strategy = config.recovery_strategy

        if strategy == RecoveryStrategy.RETRY_WITH_DELAY:
            print(f"Versuche erneut in {config.retry_delay_seconds} Sekunden...")
            time.sleep(config.retry_delay_seconds)

        elif strategy == RecoveryStrategy.USER_INTERVENTION:
            input()  # Wait for user to press ENTER

        elif strategy == RecoveryStrategy.FALLBACK:
            if self.logger:
                self.logger.info("Versuche Fallback-Strategie")

        return strategy

    def reset_error_count(self, error_type: ErrorType):
        """Reset error count for type"""
        if error_type in self.error_counts:
            self.error_counts[error_type] = 0

    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of all errors"""
        return {
            error_type.value: count
            for error_type, count in self.error_counts.items()
        }


# Decorator for automatic error handling
def with_error_handling(error_type: ErrorType, logger=None):
    """
    Decorator for automatic error handling

    Example:
        @with_error_handling(ErrorType.CDP_CONNECTION, logger)
        def connect_to_browser():
            # Code that might fail
            pass
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            handler = ErrorHandler(logger)

            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    strategy = handler.handle_error(
                        error_type, context={"exception": str(e)}
                    )

                    if strategy == RecoveryStrategy.ABORT:
                        raise

                    if strategy == RecoveryStrategy.SKIP:
                        return None

                    # Otherwise, retry

        return wrapper

    return decorator


# Example usage
if __name__ == "__main__":
    from logger import get_logger

    logger = get_logger("error_handler_demo", console=True, level="DEBUG")
    handler = ErrorHandler(logger)

    # Simulate CDP connection error
    print("Simulating CDP connection error...")
    strategy = handler.handle_error(ErrorType.CDP_CONNECTION)
    print(f"Strategy: {strategy}\n")

    # Simulate CAPTCHA
    print("Simulating CAPTCHA detection...")
    strategy = handler.handle_error(ErrorType.CAPTCHA_DETECTED)
    print(f"Strategy: {strategy}\n")

    # Simulate rate limit
    print("Simulating rate limit...")
    strategy = handler.handle_error(ErrorType.RATE_LIMIT)
    print(f"Strategy: {strategy}\n")

    # Error summary
    print("Error Summary:")
    print(handler.get_error_summary())

    print("\n✅ Error handler demo complete")
