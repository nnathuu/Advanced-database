import redis
import time
import json

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

print("\n EXERCISE 3: CACHE-ASIDE ")

import json

# Simulated database
database = {
    "product:1": {
        "name": "Laptop",
        "price": 1500
    }
}

db_calls = 0

# Simulate database query
def get_from_database(key):
    global db_calls
    db_calls += 1

    time.sleep(0.05)  # Simulate 50ms database latency

    return database.get(key)

# Test without cache
db_calls = 0
start = time.perf_counter()

for _ in range(100):
    get_from_database("product:1")

no_cache_time = time.perf_counter() - start
no_cache_calls = db_calls

# Test with cache-aside
r.delete("cache:product:1")
db_calls = 0

def get_with_cache(key):
    cache_key = f"cache:{key}"

    cached = r.get(cache_key)

    if cached is not None:
        return json.loads(cached)

    data = get_from_database(key)

    if data is not None:
        r.set(cache_key, json.dumps(data), ex=60)

    return data

start = time.perf_counter()

for _ in range(100):
    get_with_cache("product:1")

cache_time = time.perf_counter() - start
cache_calls = db_calls

# Compare performance
print("\nWithout cache:")
print(f"Database calls: {no_cache_calls}")
print(f"Total time: {no_cache_time:.4f} seconds")

print("\nWith cache-aside:")
print(f"Database calls: {cache_calls}")
print(f"Total time: {cache_time:.4f} seconds")

speedup = no_cache_time / cache_time
saved_percent = (1 - cache_time / no_cache_time) * 100

print(f"\nSpeedup: {speedup:.2f}x")
print(f"Time saved: {saved_percent:.2f}%")
