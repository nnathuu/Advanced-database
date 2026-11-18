import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

print("\n EXERCISE 2: USER PROFILES")

users = {
    "101": {"name": "An", "age": 20, "city": "Hanoi"},
    "102": {"name": "Binh", "age": 21, "city": "Hanoi"},
    "103": {"name": "Chi", "age": 22, "city": "Danang"},
    "104": {"name": "Dung", "age": 20, "city": "Danang"},
    "105": {"name": "Huy", "age": 23, "city": "Hanoi"}
}

# Store user profiles and city indexes
for user_id, profile in users.items():
    r.hset(f"user:{user_id}", mapping=profile)
    r.sadd(f"city:{profile['city']}", user_id)

# Find users by city
def find_users_by_city(city):
    user_ids = r.smembers(f"city:{city}")
    result = []

    for user_id in sorted(user_ids):
        profile = r.hgetall(f"user:{user_id}")
        result.append({"id": user_id, **profile})

    return result

# Search users in Hanoi
hanoi_users = find_users_by_city("Hanoi")

print("\nUsers in Hanoi:")
for user in hanoi_users:
    print(user)

# Search users in Danang
danang_users = find_users_by_city("Danang")

print("\nUsers in Danang:")
for user in danang_users:
    print(user)