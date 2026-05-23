"""
Simple TTL-based in-memory cache for FastAPI.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cached data with TTL."""

    data: Any
    timestamp: datetime
    ttl_minutes: int

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        expiry = self.timestamp + timedelta(minutes=self.ttl_minutes)
        return datetime.utcnow() > expiry

    def expires_at(self) -> str:
        """Return expiry timestamp as ISO string."""
        expiry = self.timestamp + timedelta(minutes=self.ttl_minutes)
        return expiry.isoformat()


class SimpleCache:
    """
    Thread-safe TTL-based cache using dict + timestamps.
    """

    def __init__(self):
        """Initialize cache."""
        self._cache: Dict[str, CacheEntry] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached data if exists and not expired.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found or expired
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if entry.is_expired():
            logger.debug(f"Cache expired for key: {key}")
            del self._cache[key]
            return None

        logger.debug(f"Cache hit for key: {key}")
        return entry.data

    def set(self, key: str, data: Any, ttl_minutes: int = 60) -> None:
        """
        Set cached data with TTL.

        Args:
            key: Cache key
            data: Data to cache
            ttl_minutes: Time-to-live in minutes (default 60)
        """
        self._cache[key] = CacheEntry(
            data=data,
            timestamp=datetime.utcnow(),
            ttl_minutes=ttl_minutes,
        )
        logger.debug(f"Cache set for key: {key} (TTL: {ttl_minutes}m)")

    def clear(self, key: str) -> None:
        """
        Clear cache entry.

        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache cleared for key: {key}")

    def clear_all(self) -> None:
        """Clear entire cache."""
        self._cache.clear()
        logger.debug("Cache cleared (all entries)")

    def status(self) -> Dict[str, Any]:
        """
        Get cache status (count, entries, sizes).

        Returns:
            Dict with cache statistics
        """
        # Remove expired entries
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for k in expired_keys:
            del self._cache[k]

        entries = []
        total_size = 0
        for key, entry in self._cache.items():
            # Estimate size (rough approximation)
            try:
                size = len(str(entry.data).encode("utf-8"))
            except Exception:
                size = 0

            total_size += size
            entries.append(
                {
                    "key": key,
                    "ttl_minutes": entry.ttl_minutes,
                    "created_at": entry.timestamp.isoformat(),
                    "expires_at": entry.expires_at(),
                    "size_bytes": size,
                }
            )

        return {
            "count": len(entries),
            "total_size_bytes": total_size,
            "entries": sorted(entries, key=lambda x: x["created_at"], reverse=True),
        }


# Global cache instance
_cache: Optional[SimpleCache] = None


def get_cache() -> SimpleCache:
    """Get or create global cache instance."""
    global _cache
    if _cache is None:
        _cache = SimpleCache()
    return _cache
