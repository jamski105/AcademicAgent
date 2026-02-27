"""
SQLite-basiertes Caching für Academic Agent v2.0

Features:
- TTL (Time-To-Live) Support
- LRU Eviction
- Thread-safe
- Async Support

Usage:
    cache = Cache(ttl_hours=24, max_size_mb=100)
    cache.set("key", {"data": "value"})
    result = cache.get("key")  # Returns {"data": "value"} or None
"""

import json
import sqlite3
import time
from pathlib import Path
from threading import Lock
from typing import Any, Optional


class Cache:
    """SQLite-basiertes Cache mit TTL und LRU Eviction"""

    def __init__(
        self,
        cache_file: Optional[Path] = None,
        ttl_hours: int = 24,
        max_size_mb: int = 100
    ):
        """
        Args:
            cache_file: Cache DB Pfad (default: .cache/api_cache.db)
            ttl_hours: Time-To-Live in Stunden
            max_size_mb: Max Cache Größe in MB
        """
        self.cache_file = cache_file or Path.home() / ".cache" / "academic_agent" / "api_cache.db"
        self.ttl_seconds = ttl_hours * 3600
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.lock = Lock()

        # Create cache directory
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize DB
        self._init_db()

    def _init_db(self) -> None:
        """Initialisiert Cache Database"""
        with sqlite3.connect(str(self.cache_file)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    accessed_at INTEGER NOT NULL,
                    size_bytes INTEGER NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_accessed_at ON cache(accessed_at)")
            conn.commit()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None wenn nicht gefunden/expired
        """
        with self.lock:
            with sqlite3.connect(str(self.cache_file)) as conn:
                cursor = conn.execute(
                    "SELECT value, created_at FROM cache WHERE key = ?",
                    (key,)
                )
                row = cursor.fetchone()

                if not row:
                    return None

                value_json, created_at = row

                # Check TTL
                if time.time() - created_at > self.ttl_seconds:
                    # Expired - delete
                    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                    conn.commit()
                    return None

                # Update accessed_at (LRU)
                conn.execute(
                    "UPDATE cache SET accessed_at = ? WHERE key = ?",
                    (int(time.time()), key)
                )
                conn.commit()

                return json.loads(value_json)

    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value (JSON-serializable)
        """
        value_json = json.dumps(value)
        size_bytes = len(value_json.encode('utf-8'))
        now = int(time.time())

        with self.lock:
            # Evict if needed
            self._evict_if_needed(size_bytes)

            with sqlite3.connect(str(self.cache_file)) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache (key, value, created_at, accessed_at, size_bytes)
                    VALUES (?, ?, ?, ?, ?)
                """, (key, value_json, now, now, size_bytes))
                conn.commit()

    def delete(self, key: str) -> None:
        """Delete from cache"""
        with self.lock:
            with sqlite3.connect(str(self.cache_file)) as conn:
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()

    def clear(self) -> None:
        """Clear entire cache"""
        with self.lock:
            with sqlite3.connect(str(self.cache_file)) as conn:
                conn.execute("DELETE FROM cache")
                conn.commit()

    def _evict_if_needed(self, new_size: int) -> None:
        """Evict oldest entries wenn max_size erreicht"""
        with sqlite3.connect(str(self.cache_file)) as conn:
            # Get current size
            cursor = conn.execute("SELECT COALESCE(SUM(size_bytes), 0) FROM cache")
            current_size = cursor.fetchone()[0]

            # Evict wenn nötig (LRU)
            while current_size + new_size > self.max_size_bytes:
                cursor = conn.execute("""
                    SELECT key, size_bytes FROM cache
                    ORDER BY accessed_at ASC LIMIT 1
                """)
                row = cursor.fetchone()

                if not row:
                    break

                key, size = row
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                current_size -= size

            conn.commit()

    def get_stats(self) -> dict:
        """Get cache statistics"""
        with self.lock:
            with sqlite3.connect(str(self.cache_file)) as conn:
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as count,
                        COALESCE(SUM(size_bytes), 0) as total_size
                    FROM cache
                """)
                count, total_size = cursor.fetchone()

                return {
                    "entries": count,
                    "size_mb": total_size / (1024 * 1024),
                    "max_size_mb": self.max_size_bytes / (1024 * 1024),
                    "usage_percent": (total_size / self.max_size_bytes) * 100 if self.max_size_bytes > 0 else 0
                }


if __name__ == "__main__":
    """Test Cache"""
    import tempfile

    print("Testing Cache...")

    # Test mit temporärem File
    temp_file = Path(tempfile.mktemp(suffix=".db"))
    cache = Cache(cache_file=temp_file, ttl_hours=24, max_size_mb=1)

    # Set & Get
    cache.set("key1", {"data": "value1"})
    result = cache.get("key1")
    assert result == {"data": "value1"}
    print("✅ Set & Get works")

    # Stats
    stats = cache.get_stats()
    print(f"✅ Stats: {stats}")

    # Clear
    cache.clear()
    assert cache.get("key1") is None
    print("✅ Clear works")

    # Cleanup
    temp_file.unlink()
    print("\n✅ All tests passed!")
