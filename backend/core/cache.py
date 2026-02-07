import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


class CacheEntry(Generic[T]):
    """A single cached value with optional TTL."""

    def __init__(self, value: T, ttl_seconds: Optional[int] = None):
        self.value = value
        self.expires_at: Optional[datetime] = None
        if ttl_seconds is not None:
            self.expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


class CacheBackend(ABC):
    """Abstract cache backend interface."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def clear(self) -> None:
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass


class InMemoryCache(CacheBackend):
    """Thread-safe in-memory cache with TTL support and background cleanup."""

    def __init__(self, cleanup_interval: int = 300):
        self._store: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start_cleanup(self):
        """Start the background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(self._cleanup_interval)
            async with self._lock:
                expired_keys = [k for k, v in self._store.items() if v.is_expired()]
                for k in expired_keys:
                    del self._store[k]
                if expired_keys:
                    logger.debug(f"Cache cleanup: removed {len(expired_keys)} expired entries")

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if entry.is_expired():
                del self._store[key]
                return None
            return entry.value

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        async with self._lock:
            self._store[key] = CacheEntry(value, ttl_seconds)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()

    async def exists(self, key: str) -> bool:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return False
            if entry.is_expired():
                del self._store[key]
                return False
            return True

    async def size(self) -> int:
        async with self._lock:
            return len(self._store)


# Global cache instance
_cache: Optional[InMemoryCache] = None


def get_cache() -> InMemoryCache:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        _cache = InMemoryCache()
    return _cache


def set_cache_backend(cache: InMemoryCache) -> None:
    """Replace the global cache (useful for testing)."""
    global _cache
    _cache = cache
