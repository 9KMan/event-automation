"""Response caching for cost minimization."""
import hashlib
import json
import logging
import os
import threading
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class LLMCache:
    """Response caching for cost minimization."""

    def __init__(self, cache_dir: Optional[str] = None, max_entries: int = 10000):
        """
        Initialize LLMCache.

        Args:
            cache_dir: Directory for persistent cache storage (optional)
            max_entries: Maximum number of entries in memory cache
        """
        self.cache_dir = cache_dir or self._get_default_cache_dir()
        self.max_entries = max_entries
        self._memory_cache: Dict[str, str] = {}
        self._lock = threading.Lock()

    def get_cache(self, event_hash: str, source_hash: str) -> Optional[str]:
        """
        Get cached response.

        Args:
            event_hash: Hash of event data
            source_hash: Hash of source data

        Returns:
            Cached response string or None if not found
        """
        key = self._make_key(event_hash, source_hash)

        # Check memory cache first
        with self._lock:
            if key in self._memory_cache:
                logger.debug(f"Cache hit (memory): {key[:16]}...")
                return self._memory_cache[key]

        # Check disk cache
        cache_file = self._get_cache_file(key)
        if cache_file and cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    response = f.read()
                logger.debug(f"Cache hit (disk): {key[:16]}...")
                # Add to memory cache
                with self._lock:
                    self._memory_cache[key] = response
                return response
            except Exception as e:
                logger.warning(f"Failed to read cache from disk: {e}")

        logger.debug(f"Cache miss: {key[:16]}...")
        return None

    def set_cache(self, event_hash: str, source_hash: str, response: str) -> None:
        """
        Set cached response.

        Args:
            event_hash: Hash of event data
            source_hash: Hash of source data
            response: Response string to cache
        """
        key = self._make_key(event_hash, source_hash)

        # Add to memory cache
        with self._lock:
            self._memory_cache[key] = response
            # Enforce max entries
            if len(self._memory_cache) > self.max_entries:
                # Remove oldest entry (FIFO)
                oldest = next(iter(self._memory_cache))
                del self._memory_cache[oldest]

        # Write to disk cache
        if self.cache_dir:
            try:
                cache_file = self._get_cache_file(key, create_dir=True)
                if cache_file:
                    with open(cache_file, "w") as f:
                        f.write(response)
                    logger.debug(f"Cached response: {key[:16]}...")
            except Exception as e:
                logger.warning(f"Failed to write cache to disk: {e}")

    def clear(self) -> None:
        """Clear all caches (memory and disk)."""
        with self._lock:
            self._memory_cache.clear()

        if self.cache_dir and os.path.exists(self.cache_dir):
            try:
                for file in Path(self.cache_dir).glob("*.cache"):
                    file.unlink()
                logger.info("Cache cleared")
            except Exception as e:
                logger.warning(f"Failed to clear disk cache: {e}")

    def _make_key(self, event_hash: str, source_hash: str) -> str:
        """Make cache key from event and source hashes."""
        combined = f"{event_hash}:{source_hash}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _get_cache_file(self, key: str, create_dir: bool = False) -> Optional[Path]:
        """Get cache file path for a key."""
        if not self.cache_dir:
            return None

        cache_dir = Path(self.cache_dir)
        if create_dir and not cache_dir.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)

        return cache_dir / f"{key}.cache"

    def _get_default_cache_dir(self) -> Optional[str]:
        """Get default cache directory."""
        # Use a temp directory or app data directory
        return None  # Disabled by default, enable via constructor

    @staticmethod
    def hash_data(data: dict) -> str:
        """Hash data dictionary for cache key."""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()