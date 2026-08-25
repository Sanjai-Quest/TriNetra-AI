"""
Step 3: Redis Caching Layer Verification
Verifies cache key formats, TTL enforcement, and cache hit rate (>80%).
Keys tested:
  - buyer_trust:{buyer_id} -> 1 hour TTL
  - seller_reliability:{seller_id} -> 1 hour TTL
  - category_fraud_rate:{cat} -> 24 hour TTL
  - price_risk_multiplier:{bracket} -> 24 hour TTL
  - dispute_risk_score:{id} -> 24 hour TTL
"""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from trinetra_risk_scoring import RiskScoringService, InMemoryCache, Dispute


class TestRedisCachingLayer(unittest.TestCase):

    def setUp(self):
        self.cache = InMemoryCache()
        self.service = RiskScoringService(redis_client=self.cache)

    def test_basic_write_and_read(self):
        self.cache.set("test_key", 0.75, ttl_seconds=60)
        val = self.cache.get("test_key")
        self.assertEqual(val, 0.75)

    def test_ttl_expiration(self):
        self.cache.set("expire_key", 0.99, ttl_seconds=1)
        self.assertIsNotNone(self.cache.get("expire_key"))
        time.sleep(1.1)
        self.assertIsNone(self.cache.get("expire_key"))

    def test_buyer_trust_cached_on_subsequent_calls(self):
        # 1st call -> computed & cached
        res1 = self.service.get_buyer_trust_score("buyer-999", return_count=10, total_orders=100)
        self.assertFalse(res1.cached)
        self.assertEqual(res1.value, 0.10)

        # 2nd call -> returned from cache
        res2 = self.service.get_buyer_trust_score("buyer-999")
        self.assertTrue(res2.cached)
        self.assertEqual(res2.value, 0.10)

    def test_category_fraud_baseline_cached(self):
        res1 = self.service.get_category_fraud_baseline("electronics")
        self.assertFalse(res1.cached)
        self.assertEqual(res1.value, 0.08)

        res2 = self.service.get_category_fraud_baseline("electronics")
        self.assertTrue(res2.cached)
        self.assertEqual(res2.value, 0.08)

    def test_seller_reliability_cached(self):
        res1 = self.service.get_seller_reliability("seller-777", refund_disputes=5, total_sales=100)
        self.assertFalse(res1.cached)
        self.assertEqual(res1.value, 0.05)

        res2 = self.service.get_seller_reliability("seller-777")
        self.assertTrue(res2.cached)
        self.assertEqual(res2.value, 0.05)

    def test_price_risk_cached(self):
        res1 = self.service.get_price_risk(1200)
        self.assertFalse(res1.cached)
        self.assertEqual(res1.value, 0.10)

        res2 = self.service.get_price_risk(1200)
        self.assertTrue(res2.cached)
        self.assertEqual(res2.value, 0.10)

    def test_cache_hit_rate_exceeds_eighty_percent(self):
        """Simulate 100 repeated lookups and verify hit rate > 80%."""
        dispute = Dispute(
            id="disp-cached-1",
            buyer_id="buyer-cached-1",
            seller_id="seller-cached-1",
            category="electronics",
            price=2500,
            buyer_return_count=5,
            buyer_total_orders=100,
            seller_dispute_count=2,
            seller_total_sales=100,
        )

        for _ in range(100):
            self.service.compute_risk_score(dispute)

        total_requests = self.cache.hits + self.cache.misses
        hit_rate = self.cache.hits / total_requests if total_requests > 0 else 0.0

        print(f"\n[Cache Hit Rate Test] Total requests: {total_requests}, Hits: {self.cache.hits}, Misses: {self.cache.misses}, Hit Rate: {hit_rate:.1%}")
        self.assertGreater(hit_rate, 0.80, f"Hit rate {hit_rate:.1%} is below 80% requirement!")


if __name__ == "__main__":
    unittest.main()
