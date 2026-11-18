import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

print("\n EXERCISE 1: LEADERBOARD")

r.delete("game:leaderboard")

leaderboard = "game:leaderboard"

players = {
    "Alice": 1500,
    "Bob": 1200,
    "Charlie": 1200,
    "David": 900,
    "Emma": 800
}

# Add players and scores to Sorted Set
r.zadd(leaderboard, players)

# Get top 3 players
top_players = r.zrevrange(leaderboard, 0, 2, withscores=True)

print("\nTop 3 players:")
for rank, (name, score) in enumerate(top_players, start=1):
    print(f"Rank {rank}: {name} - {int(score)} points")

# Display ranking with ties
ranking = r.zrevrange(leaderboard, 0, -1, withscores=True)

print("\nFull leaderboard:")
previous_score = None
rank = 0

for position, (name, score) in enumerate(ranking, start=1):
    if score != previous_score:
        rank = position

    print(f"Rank {rank}: {name} - {int(score)} points")
    previous_score = score