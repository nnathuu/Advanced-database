from cassandra.cluster import Cluster

CONTACT_POINTS = ["127.0.0.1"]
KEYSPACE = "practice"



USERS = [
    {"user_id": "101", "name": "Alice", "age": 21, "city": "Hanoi"},
    {"user_id": "102", "name": "Bob", "age": 22, "city": "Hanoi"},
    {"user_id": "103", "name": "Charlie", "age": 20, "city": "Danang"},
    {"user_id": "104", "name": "David", "age": 23, "city": "HCM"},
]



def setup(session):
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 3}}
    """)
    session.set_keyspace(KEYSPACE)


    # Table for retrieving one user profile by user_id.
    session.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id text PRIMARY KEY,
            name text,
            age int,
            city text
        )
    """)

    # Query-oriented table: partition by city to find users in a city efficiently.
    session.execute("""
        CREATE TABLE IF NOT EXISTS users_by_city (
            city text,
            user_id text,
            name text,
            age int,
            PRIMARY KEY ((city), user_id)
        )
    """)



def main():
    cluster = Cluster(CONTACT_POINTS)
    session = cluster.connect()
    try:
        setup(session)

        insert_profile = session.prepare("""
            INSERT INTO user_profiles (user_id, name, age, city)
            VALUES (?, ?, ?, ?)
        """)
        insert_city = session.prepare("""
            INSERT INTO users_by_city (city, user_id, name, age)
            VALUES (?, ?, ?, ?)
        """)


        for user in USERS:
            session.execute(insert_profile, (
                user["user_id"], user["name"], user["age"], user["city"]
            ))
            session.execute(insert_city, (
                user["city"], user["user_id"], user["name"], user["age"]
            ))

        target_city = "Hanoi"
        rows = session.execute(
            "SELECT user_id, name, age, city FROM users_by_city WHERE city = %s",
            (target_city,)
        )

        print(f"\n USERS IN {target_city.upper()}")
        for row in rows:
            print(f"ID: {row.user_id} | Name: {row.name} | Age: {row.age} | City: {row.city}")

        # Example: retrieve one profile directly by primary key.
        profile = session.execute(
            "SELECT user_id, name, age, city FROM user_profiles WHERE user_id = %s",
            ("101",)
        ).one()
        print("\n PROFILE OF USER 101 ")
        print(profile)
    finally:
        session.shutdown()
        cluster.shutdown()



if __name__ == "__main__":
    main()
