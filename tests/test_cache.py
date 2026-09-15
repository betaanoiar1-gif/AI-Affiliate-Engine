import time

from core.cache import TTLCache


def test_ttl_cache_round_trip_and_expiry():
    cache = TTLCache(":memory:")
    key = TTLCache.key("test", "value")
    cache.set(key, {"x": 1}, ttl_seconds=0.02)
    assert cache.get(key) == {"x": 1}
    time.sleep(0.03)
    assert cache.get(key) is None
    cache.close()
