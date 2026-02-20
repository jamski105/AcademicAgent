#!/usr/bin/env python3
"""
Retry-Strategie mit Exponential Backoff für AcademicAgent
Bietet adaptive Retry-Delays für Network-Requests und Browser-Operationen

Verwendung:
    from scripts.retry_strategy import exponential_backoff, RetryHandler

    # Einfache Backoff-Berechnung
    delay = exponential_backoff(attempt=2, base_delay=1, max_delay=60)

    # Vollständiger Retry-Handler mit Kontext
    handler = RetryHandler(max_retries=5, base_delay=2)
    result = handler.execute(my_function, *args, **kwargs)
"""

import time
import random
import logging
from typing import Callable, Any, Optional, Dict
from functools import wraps

# Logger einrichten
logger = logging.getLogger(__name__)


class RetryEnforcementError(Exception):
    """Raised when retry enforcement fails after exhausting all retries"""
    pass


def exponential_backoff(
    attempt: int,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """
    Berechnet Exponential-Backoff-Delay mit optionalem Jitter

    Args:
        attempt: Retry-Versuch (0-basiert, 0 = erster Versuch)
        base_delay: Basis-Delay in Sekunden (default: 2s)
        max_delay: Maximaler Delay in Sekunden (default: 60s)
        jitter: Ob zufälliger Jitter hinzugefügt werden soll (default: True)

    Returns:
        Delay in Sekunden

    Beispiele:
        >>> exponential_backoff(0, base_delay=2)  # ~2s
        >>> exponential_backoff(1, base_delay=2)  # ~4s
        >>> exponential_backoff(2, base_delay=2)  # ~8s
        >>> exponential_backoff(5, base_delay=2, max_delay=30)  # 30s (capped)
    """
    # Exponentieller Delay: base_delay * 2^attempt
    delay = min(base_delay * (2 ** attempt), max_delay)

    # Füge zufälligen Jitter hinzu (0-10% des Delays)
    # Verhindert "Thundering Herd" wenn mehrere Clients gleichzeitig retry
    if jitter:
        jitter_amount = random.uniform(0, 0.1 * delay)
        delay += jitter_amount

    return delay


def linear_backoff(
    attempt: int,
    increment: float = 5.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """
    Berechnet Linear-Backoff-Delay (für weniger aggressive Retries)

    Args:
        attempt: Retry-Versuch (0-basiert)
        increment: Delay-Inkrement in Sekunden (default: 5s)
        max_delay: Maximaler Delay in Sekunden (default: 60s)
        jitter: Ob zufälliger Jitter hinzugefügt werden soll

    Returns:
        Delay in Sekunden
    """
    delay = min(increment * (attempt + 1), max_delay)

    if jitter:
        jitter_amount = random.uniform(0, 0.1 * delay)
        delay += jitter_amount

    return delay


class RetryHandler:
    """
    Retry-Handler mit konfigurierbarer Backoff-Strategie

    Features:
        - Exponential/Linear Backoff
        - Configurable max retries
        - Exception-basierte Retry-Logik
        - Detailliertes Logging
        - Kontext-Tracking (für Debugging)
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 2.0,
        max_delay: float = 60.0,
        strategy: str = "exponential",
        retryable_exceptions: Optional[list] = None,
        logger_instance: Optional[logging.Logger] = None
    ):
        """
        Initialisiert Retry-Handler

        Args:
            max_retries: Maximale Anzahl Retries (default: 3)
            base_delay: Basis-Delay in Sekunden (default: 2s)
            max_delay: Maximaler Delay (default: 60s)
            strategy: "exponential" oder "linear" (default: "exponential")
            retryable_exceptions: Liste von Exception-Typen die retried werden sollen
                                  (default: alle Exceptions)
            logger_instance: Optional Logger-Instanz (default: module logger)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.retryable_exceptions = retryable_exceptions or [Exception]
        self.logger = logger_instance or logger

        # Stats
        self.attempts = 0
        self.total_delay = 0.0

    def should_retry(self, exception: Exception) -> bool:
        """
        Prüft ob Exception retry-bar ist

        Args:
            exception: Exception-Instanz

        Returns:
            True wenn retry erlaubt
        """
        for exc_type in self.retryable_exceptions:
            if isinstance(exception, exc_type):
                return True
        return False

    def get_delay(self, attempt: int) -> float:
        """Berechnet Delay für Retry-Versuch"""
        if self.strategy == "exponential":
            return exponential_backoff(
                attempt,
                base_delay=self.base_delay,
                max_delay=self.max_delay
            )
        elif self.strategy == "linear":
            return linear_backoff(
                attempt,
                increment=self.base_delay,
                max_delay=self.max_delay
            )
        else:
            raise ValueError(f"Unbekannte Strategie: {self.strategy}")

    def execute(
        self,
        func: Callable,
        *args,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Führt Funktion mit Retry-Logik aus

        Args:
            func: Auszuführende Funktion
            *args: Positional arguments für func
            context: Optional Dict mit Kontext (für Logging)
            **kwargs: Keyword arguments für func

        Returns:
            Rückgabewert von func

        Raises:
            Exception: Falls alle Retries fehlschlagen
        """
        context = context or {}
        last_exception = None

        for attempt in range(self.max_retries + 1):
            self.attempts += 1

            try:
                self.logger.info(
                    f"Versuch {attempt + 1}/{self.max_retries + 1} "
                    f"für {func.__name__} {context}"
                )

                result = func(*args, **kwargs)

                if attempt > 0:
                    self.logger.info(
                        f"✅ Erfolg nach {attempt + 1} Versuchen "
                        f"(Total Delay: {self.total_delay:.1f}s)"
                    )

                return result

            except Exception as e:
                last_exception = e

                # Prüfe ob retry erlaubt
                if not self.should_retry(e):
                    self.logger.error(
                        f"❌ Nicht-retrybare Exception: {type(e).__name__}: {str(e)}"
                    )
                    raise

                # Prüfe ob noch Retries übrig
                if attempt >= self.max_retries:
                    self.logger.error(
                        f"❌ Maximale Retries erreicht ({self.max_retries}). "
                        f"Letzte Exception: {type(e).__name__}: {str(e)}"
                    )
                    raise RetryEnforcementError(
                        f"Operation failed after {self.max_retries} retries"
                    ) from e

                # Berechne Delay und warte
                delay = self.get_delay(attempt)
                self.total_delay += delay

                self.logger.warning(
                    f"⚠️  Versuch {attempt + 1} fehlgeschlagen: {type(e).__name__}: {str(e)}"
                )
                self.logger.info(
                    f"⏸️  Warte {delay:.1f}s vor Retry (Strategie: {self.strategy})..."
                )

                time.sleep(delay)

        # Sollte nie erreicht werden, aber zur Sicherheit
        if last_exception:
            raise RetryEnforcementError(
                f"Operation failed after {self.max_retries} retries"
            ) from last_exception
        else:
            raise RetryEnforcementError("Operation failed with unknown error")


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    strategy: str = "exponential",
    retryable_exceptions: Optional[list] = None
):
    """
    Decorator für automatisches Retry mit Backoff

    Verwendung:
        @retry_with_backoff(max_retries=5, base_delay=1)
        def my_network_call():
            response = requests.get("https://api.example.com")
            return response.json()

    Args:
        max_retries: Maximale Anzahl Retries
        base_delay: Basis-Delay in Sekunden
        max_delay: Maximaler Delay
        strategy: "exponential" oder "linear"
        retryable_exceptions: Liste von retry-baren Exceptions
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = RetryHandler(
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                strategy=strategy,
                retryable_exceptions=retryable_exceptions
            )
            return handler.execute(func, *args, **kwargs)
        return wrapper
    return decorator


# ============================================
# Vordefinierte Retry-Profile
# ============================================

class RetryProfiles:
    """Vordefinierte Retry-Profile für häufige Use-Cases"""

    @staticmethod
    def network_request() -> RetryHandler:
        """
        Profil für Network-Requests (API-Calls, WebFetch)
        - Max 5 Retries
        - Exponential Backoff (2s, 4s, 8s, 16s, 32s)
        """
        return RetryHandler(
            max_retries=5,
            base_delay=2.0,
            max_delay=60.0,
            strategy="exponential"
        )

    @staticmethod
    def browser_navigation() -> RetryHandler:
        """
        Profil für Browser-Navigation (CDP-Operationen)
        - Max 3 Retries
        - Linear Backoff (3s, 6s, 9s)
        """
        return RetryHandler(
            max_retries=3,
            base_delay=3.0,
            max_delay=30.0,
            strategy="linear"
        )

    @staticmethod
    def database_query() -> RetryHandler:
        """
        Profil für Datenbank-Suchen
        - Max 4 Retries
        - Exponential Backoff (5s, 10s, 20s, 40s)
        """
        return RetryHandler(
            max_retries=4,
            base_delay=5.0,
            max_delay=60.0,
            strategy="exponential"
        )

    @staticmethod
    def captcha_retry() -> RetryHandler:
        """
        Profil für CAPTCHA-Retries (mit manueller User-Intervention)
        - Max 2 Retries
        - Linear Backoff (30s, 60s)
        """
        return RetryHandler(
            max_retries=2,
            base_delay=30.0,
            max_delay=60.0,
            strategy="linear"
        )


# ============================================
# Beispiel-Verwendung
# ============================================

if __name__ == "__main__":
    # Setup Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("🧪 Teste Retry-Strategien...\n")

    # Test 1: Exponential Backoff Delays
    print("Test 1: Exponential Backoff Delays")
    for i in range(6):
        delay = exponential_backoff(i, base_delay=2, max_delay=60)
        print(f"  Versuch {i}: {delay:.2f}s")
    print()

    # Test 2: Linear Backoff Delays
    print("Test 2: Linear Backoff Delays")
    for i in range(6):
        delay = linear_backoff(i, increment=5, max_delay=60)
        print(f"  Versuch {i}: {delay:.2f}s")
    print()

    # Test 3: RetryHandler mit fehlschlagender Funktion
    print("Test 3: RetryHandler (3 Fails, dann Success)")

    call_count = 0

    def flaky_function():
        global call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError(f"Verbindungsfehler (Versuch {call_count})")
        return "Erfolg!"

    handler = RetryHandler(max_retries=5, base_delay=0.5)
    try:
        result = handler.execute(flaky_function)
        print(f"\n✅ Ergebnis: {result}")
        print(f"📊 Statistiken: {handler.attempts} Versuche, {handler.total_delay:.2f}s Total Delay")
    except Exception as e:
        print(f"\n❌ Fehlgeschlagen: {e}")

    print()

    # Test 4: Decorator-Verwendung
    print("Test 4: Retry-Decorator")

    @retry_with_backoff(max_retries=3, base_delay=0.5)
    def api_call_simulation():
        import random
        if random.random() < 0.7:  # 70% Fehlerrate
            raise ConnectionError("API nicht erreichbar")
        return {"status": "ok", "data": [1, 2, 3]}

    try:
        result = api_call_simulation()
        print(f"✅ API-Call erfolgreich: {result}")
    except Exception as e:
        print(f"❌ API-Call fehlgeschlagen: {e}")

    print()

    # Test 5: Profile-Verwendung
    print("Test 5: Vordefinierte Profile")

    network_handler = RetryProfiles.network_request()
    print(f"  Network Request Profile: max_retries={network_handler.max_retries}, "
          f"strategy={network_handler.strategy}")

    browser_handler = RetryProfiles.browser_navigation()
    print(f"  Browser Navigation Profile: max_retries={browser_handler.max_retries}, "
          f"strategy={browser_handler.strategy}")

    print("\n✅ Alle Tests abgeschlossen!")
