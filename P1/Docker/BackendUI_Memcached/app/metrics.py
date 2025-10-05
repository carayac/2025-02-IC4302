from prometheus_client import Counter

cache_hit = Counter("cache_hit", "Cache hits", ["bd", "cache"])
cache_miss = Counter("cache_miss", "Cache misses", ["bd", "cache"])