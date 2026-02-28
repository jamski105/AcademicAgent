"""
Rate Limiter für Academic Agent v2.3+

Sliding Window Token-Bucket Rate Limiter
- Thread-safe
- Async-Support
- Adaptive Limits (Standard vs Enhanced Mode)

Usage:
    # Sync
    limiter = RateLimiter(requests_per_second=50)
    limiter.acquire()  # Blockiert bis Token verfügbar

    # Async
    async_limiter = AsyncRateLimiter(requests_per_second=10)
    await async_limiter.acquire()
"""

import asyncio
import time
from threading import Lock
from typing import Optional


class RateLimiter:
    """
    Thread-safe Sliding Window Rate Limiter (Sync)

    Nutzt Token-Bucket Algorithmus für präzises Rate-Limiting
    """

    def __init__(
        self,
        requests_per_second: float,
        burst_size: Optional[int] = None,
        daily_limit: Optional[int] = None
    ):
        """
        Args:
            requests_per_second: Max Requests pro Sekunde
            burst_size: Max Burst Size (default: requests_per_second)
            daily_limit: Optional tägliches Limit (für OpenAlex Anonymous)
        """
        self.rate = requests_per_second
        self.burst_size = burst_size or int(requests_per_second)
        self.daily_limit = daily_limit

        # Token Bucket State
        self.tokens = float(self.burst_size)
        self.last_update = time.time()
        self.lock = Lock()

        # Daily Limit Tracking
        self.daily_count = 0
        self.daily_reset_time = time.time() + 86400  # +24h

    def _refill_tokens(self, now: float) -> None:
        """Refills tokens basierend auf verstrichener Zeit"""
        elapsed = now - self.last_update
        new_tokens = elapsed * self.rate
        self.tokens = min(self.burst_size, self.tokens + new_tokens)
        self.last_update = now

    def _reset_daily_if_needed(self, now: float) -> None:
        """Reset daily count wenn 24h vergangen"""
        if now >= self.daily_reset_time:
            self.daily_count = 0
            self.daily_reset_time = now + 86400

    def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens (blockiert bis verfügbar)

        Args:
            tokens: Anzahl Tokens (default: 1)
            timeout: Max Wartezeit in Sekunden (None = unbegrenzt)

        Returns:
            True wenn erfolgreich, False bei Timeout

        Raises:
            ValueError: Wenn daily_limit erreicht
        """
        start_time = time.time()

        while True:
            with self.lock:
                now = time.time()

                # Daily Limit Check
                self._reset_daily_if_needed(now)
                if self.daily_limit and self.daily_count >= self.daily_limit:
                    raise ValueError(
                        f"Daily limit reached ({self.daily_limit}). "
                        f"Resets at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.daily_reset_time))}"
                    )

                # Refill Tokens
                self._refill_tokens(now)

                # Acquire wenn genug Tokens
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    self.daily_count += tokens
                    return True

            # Timeout Check
            if timeout and (time.time() - start_time) >= timeout:
                return False

            # Wait kurz bevor nächster Versuch
            time.sleep(0.01)  # 10ms

    def try_acquire(self, tokens: int = 1) -> bool:
        """
        Versucht tokens zu acquiren (non-blocking)

        Returns:
            True wenn erfolgreich, False sonst
        """
        with self.lock:
            now = time.time()
            self._reset_daily_if_needed(now)
            self._refill_tokens(now)

            if self.tokens >= tokens:
                self.tokens -= tokens
                if self.daily_limit:
                    self.daily_count += tokens
                return True
            return False

    def wait_if_needed(self, tokens: int = 1) -> None:
        """
        Waits if rate limit would be exceeded (alias for acquire).

        This is a convenience method that matches the naming convention
        used in some API clients. It simply calls acquire() internally.

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Raises:
            ValueError: If daily limit is reached
        """
        self.acquire(tokens=tokens)

    def get_wait_time(self, tokens: int = 1) -> float:
        """
        Berechnet Wartezeit bis tokens verfügbar

        Returns:
            Wartezeit in Sekunden
        """
        with self.lock:
            now = time.time()
            self._refill_tokens(now)

            if self.tokens >= tokens:
                return 0.0

            needed = tokens - self.tokens
            return needed / self.rate

    def reset(self) -> None:
        """Reset State (für Testing)"""
        with self.lock:
            self.tokens = float(self.burst_size)
            self.last_update = time.time()
            self.daily_count = 0
            self.daily_reset_time = time.time() + 86400


class AsyncRateLimiter:
    """
    Async-kompatible Version des Rate Limiters

    Nutzt asyncio.Lock statt threading.Lock
    """

    def __init__(
        self,
        requests_per_second: float,
        burst_size: Optional[int] = None,
        daily_limit: Optional[int] = None
    ):
        """
        Args:
            requests_per_second: Max Requests pro Sekunde
            burst_size: Max Burst Size (default: requests_per_second)
            daily_limit: Optional tägliches Limit
        """
        self.rate = requests_per_second
        self.burst_size = burst_size or int(requests_per_second)
        self.daily_limit = daily_limit

        # Token Bucket State
        self.tokens = float(self.burst_size)
        self.last_update = time.time()
        self.lock = asyncio.Lock()

        # Daily Limit Tracking
        self.daily_count = 0
        self.daily_reset_time = time.time() + 86400

    def _refill_tokens(self, now: float) -> None:
        """Refills tokens basierend auf verstrichener Zeit"""
        elapsed = now - self.last_update
        new_tokens = elapsed * self.rate
        self.tokens = min(self.burst_size, self.tokens + new_tokens)
        self.last_update = now

    def _reset_daily_if_needed(self, now: float) -> None:
        """Reset daily count wenn 24h vergangen"""
        if now >= self.daily_reset_time:
            self.daily_count = 0
            self.daily_reset_time = now + 86400

    async def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens (async)

        Args:
            tokens: Anzahl Tokens
            timeout: Max Wartezeit

        Returns:
            True wenn erfolgreich, False bei Timeout
        """
        start_time = time.time()

        while True:
            async with self.lock:
                now = time.time()

                # Daily Limit Check
                self._reset_daily_if_needed(now)
                if self.daily_limit and self.daily_count >= self.daily_limit:
                    raise ValueError(
                        f"Daily limit reached ({self.daily_limit}). "
                        f"Resets at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.daily_reset_time))}"
                    )

                # Refill Tokens
                self._refill_tokens(now)

                # Acquire wenn genug Tokens
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    self.daily_count += tokens
                    return True

            # Timeout Check
            if timeout and (time.time() - start_time) >= timeout:
                return False

            # Wait kurz (async)
            await asyncio.sleep(0.01)

    async def try_acquire(self, tokens: int = 1) -> bool:
        """Non-blocking acquire (async)"""
        async with self.lock:
            now = time.time()
            self._reset_daily_if_needed(now)
            self._refill_tokens(now)

            if self.tokens >= tokens:
                self.tokens -= tokens
                if self.daily_limit:
                    self.daily_count += tokens
                return True
            return False

    async def wait_if_needed(self, tokens: int = 1) -> None:
        """
        Waits if rate limit would be exceeded (async alias for acquire).

        This is a convenience method that matches the naming convention
        used in some API clients. It simply calls acquire() internally.

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Raises:
            ValueError: If daily limit is reached
        """
        await self.acquire(tokens=tokens)

    def get_wait_time(self, tokens: int = 1) -> float:
        """Berechnet Wartezeit (sync, weil Lock nicht benötigt wird für Estimation)"""
        now = time.time()
        elapsed = now - self.last_update
        current_tokens = min(self.burst_size, self.tokens + elapsed * self.rate)

        if current_tokens >= tokens:
            return 0.0

        needed = tokens - current_tokens
        return needed / self.rate


# ============================================
# Factory Functions
# ============================================

def create_rate_limiter_from_config(
    config: dict,
    mode: str = "standard"
) -> RateLimiter:
    """
    Erstellt Rate Limiter aus Config

    Args:
        config: Rate Limit Config Dict (aus api_config.yaml)
        mode: "standard" oder "enhanced"

    Returns:
        RateLimiter instance
    """
    return RateLimiter(
        requests_per_second=config["requests_per_second"],
        daily_limit=config.get("daily_limit")
    )


def create_async_rate_limiter_from_config(
    config: dict,
    mode: str = "standard"
) -> AsyncRateLimiter:
    """
    Erstellt Async Rate Limiter aus Config

    Args:
        config: Rate Limit Config Dict
        mode: "standard" oder "enhanced"

    Returns:
        AsyncRateLimiter instance
    """
    return AsyncRateLimiter(
        requests_per_second=config["requests_per_second"],
        daily_limit=config.get("daily_limit")
    )


# ============================================
# Testing
# ============================================

if __name__ == "__main__":
    """
    Test Rate Limiter

    Run:
        python src/utils/rate_limiter.py
    """
    print("Testing RateLimiter...")

    # Test: 50 req/s (wie CrossRef)
    limiter = RateLimiter(requests_per_second=50)

    start = time.time()
    for i in range(10):
        limiter.acquire()
        print(f"Request {i+1} at {time.time() - start:.3f}s")

    elapsed = time.time() - start
    print(f"\n✅ 10 requests in {elapsed:.3f}s")
    print(f"Rate: {10/elapsed:.1f} req/s (expected: 50 req/s)")
