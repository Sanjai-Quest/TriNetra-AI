"""
Redis pattern cache for TriNetra Phase 2 Fraud Detection Engine.
Caches customer fraud patterns to avoid expensive DB queries on every claim.
"""

import json
import logging
import os
from typing import Any, Dict, Optional
from uuid import UUID

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

REDIS_URL      = os.getenv("REDIS_URL", "redis://:trinetra_redis_pass@localhost:6379/0")
CACHE_TTL_SECS = int(os.getenv("REDIS_CACHE_TTL_SECS", "86400"))  # 24 hours


class RedisCache:
    """
    Async Redis client for fraud pattern caching.

    Stores serialized fraud pattern JSON against customer UUIDs.
    All keys are namespaced under 'trinetra:'.

    Usage:
        cache = RedisCache()
        await cache.connect()
        await cache.set_customer_pattern(customer_id, {"return_count_90d": 7})
        pattern = await cache.get_customer_pattern(customer_id)
    """

    KEY_PREFIX = "trinetra:"

    def __init__(self) -> None:
        self._client: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        self._client = await aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        logger.info("Redis cache connected.")

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    # ── Health ──────────────────────────────────────────────────────────────

    async def ping(self) -> bool:
        try:
            return await self._client.ping()
        except Exception:
            return False

    # ── Generic operations ──────────────────────────────────────────────────

    def _key(self, namespace: str, identifier: str) -> str:
        return f"{self.KEY_PREFIX}{namespace}:{identifier}"

    async def set(self, namespace: str, identifier: str, value: Dict[str, Any], ttl: int = CACHE_TTL_SECS) -> None:
        key = self._key(namespace, identifier)
        await self._client.setex(key, ttl, json.dumps(value, default=str))

    async def get(self, namespace: str, identifier: str) -> Optional[Dict[str, Any]]:
        key = self._key(namespace, identifier)
        raw = await self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def delete(self, namespace: str, identifier: str) -> None:
        key = self._key(namespace, identifier)
        await self._client.delete(key)

    # ── Customer Fraud Pattern Cache ─────────────────────────────────────────

    async def set_customer_pattern(self, customer_id: UUID, pattern: Dict[str, Any]) -> None:
        """Cache a customer's fraud risk pattern (return counts, orgs, risk score)."""
        await self.set("fraud_pattern", str(customer_id), pattern)
        logger.debug("Cached fraud pattern for customer: %s", customer_id)

    async def get_customer_pattern(self, customer_id: UUID) -> Optional[Dict[str, Any]]:
        """Retrieve a cached customer fraud pattern. Returns None on cache miss."""
        pattern = await self.get("fraud_pattern", str(customer_id))
        if pattern:
            logger.debug("Cache HIT for customer pattern: %s", customer_id)
        else:
            logger.debug("Cache MISS for customer pattern: %s", customer_id)
        return pattern

    async def invalidate_customer_pattern(self, customer_id: UUID) -> None:
        """Invalidate a customer's cached pattern (call when new claim is filed)."""
        await self.delete("fraud_pattern", str(customer_id))

    # ── Verdict Cache ────────────────────────────────────────────────────────

    async def cache_verdict(self, claim_id: UUID, verdict: Dict[str, Any]) -> None:
        """Cache a generated verdict for quick retrieval by the dashboard."""
        await self.set("verdict", str(claim_id), verdict, ttl=3600)  # 1 hour

    async def get_verdict(self, claim_id: UUID) -> Optional[Dict[str, Any]]:
        return await self.get("verdict", str(claim_id))


# ─── Singleton ────────────────────────────────────────────────────────────────
_cache: Optional[RedisCache] = None


async def get_redis_cache() -> RedisCache:
    global _cache
    if _cache is None:
        _cache = RedisCache()
        await _cache.connect()
    return _cache
