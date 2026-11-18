from cassandra.cluster import Cluster

CONTACT_POINTS = ["127.0.0.1"]
KEYSPACE = "practice"
GAME_ID = "demo-game"


def setup(session):
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 3}}
    """)
    session.set_keyspace(KEYSPACE)
    session.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard_by_game (
            game_id text,
            score int,
            player_id text,
            player_name text,
            PRIMARY KEY ((game_id), score, player_id)
        ) WITH CLUSTERING ORDER BY (score DESC, player_id ASC)
    """)


def main():
    cluster = Cluster(CONTACT_POINTS)
    session = cluster.connect()
    try:
        setup(session)


        # Reset this game's demo data so repeated runs give the same result.
        session.execute("DELETE FROM leaderboard_by_game WHERE game_id = %s", (GAME_ID,))


        players = [
            (GAME_ID, 1500, "101", "Alice"),
            (GAME_ID, 1200, "102", "Bob"),
            (GAME_ID, 1500, "103", "Charlie"),
            (GAME_ID, 1000, "104", "David"),
            (GAME_ID, 1200, "105", "Emma"),
            (GAME_ID, 900, "106", "Frank"),
        ]

        insert = session.prepare("""
            INSERT INTO leaderboard_by_game (game_id, score, player_id, player_name)
            VALUES (?, ?, ?, ?)
        """)
        for player in players:
            session.execute(insert, player)


        # Cassandra returns rows in clustering order: score DESC, player_id ASC.
        rows = session.execute(
            "SELECT player_id, player_name, score FROM leaderboard_by_game WHERE game_id = %s",
            (GAME_ID,)
        )

        print("\n LEADERBOARD")
        previous_score = None
        rank = 0
        ranked_players = []
        for position, row in enumerate(rows, start=1):
            if row.score != previous_score:
                rank = position
            ranked_players.append((rank, row.player_name, row.score))
            print(f"Rank {rank}: {row.player_name} - {row.score} points")
            previous_score = row.score

        print("\n TOP 3 RANKS (including ties)")
        for rank, name, score in ranked_players:
            if rank > 3:
                break
            print(f"Rank {rank}: {name} - {score} points")
    finally:
        session.shutdown()
        cluster.shutdown()



if __name__ == "__main__":
    main()
