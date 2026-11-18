import time
from cassandra.cluster import Cluster

CONTACT_POINTS = ["127.0.0.1"]
KEYSPACE = "practice"
PRODUCT_ID = "product-001"
REQUESTS = 100



def setup(session):
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 3}}
    """)
    session.set_keyspace(KEYSPACE)
    session.execute("""
        CREATE TABLE IF NOT EXISTS products_by_id (
            product_id text PRIMARY KEY,
            product_name text,
            price double,
            stock int
        )
    """)



def main():
    cluster = Cluster(CONTACT_POINTS)
    session = cluster.connect()
    try:
        setup(session)


        # Ensure the demo product exists before timing the reads.
        session.execute("""
            INSERT INTO products_by_id (product_id, product_name, price, stock)
            VALUES (%s, %s, %s, %s)
        """, (PRODUCT_ID, "Laptop", 1500.0, 12))


        query = session.prepare("""
            SELECT product_id, product_name, price, stock
            FROM products_by_id WHERE product_id = ?
        """)


        def database_read():
            return session.execute(query, (PRODUCT_ID,)).one()



        # A) No cache: every request goes to Cassandra.
        start = time.perf_counter()
        for _ in range(REQUESTS):
            database_read()
        direct_time = time.perf_counter() - start



        # B) Cache-aside: Python dictionary is the application-side cache.
        cache = {}
        cache_hits = 0
        cache_misses = 0

        def cache_aside_read(product_id):
            nonlocal cache_hits, cache_misses
            if product_id in cache:
                cache_hits += 1
                return cache[product_id]


            cache_misses += 1
            data = session.execute(query, (product_id,)).one()
            cache[product_id] = data
            return data


        start = time.perf_counter()
        for _ in range(REQUESTS):
            cache_aside_read(PRODUCT_ID)
        cache_time = time.perf_counter() - start



        print("\n CACHE-ASIDE: 100 REPEATED REQUESTS")
        print(f"Direct Cassandra reads: {REQUESTS}")
        print(f"Direct-read time:      {direct_time:.6f} seconds")
        print(f"Cache-aside time:      {cache_time:.6f} seconds")
        print(f"Cache hits:             {cache_hits}")
        print(f"Cache misses:            {cache_misses}")
        if cache_time > 0:
            print(f"Speedup:                {direct_time / cache_time:.2f}x")
        print("Cached product:", cache[PRODUCT_ID])
    finally:
        session.shutdown()
        cluster.shutdown()



if __name__ == "__main__":
    main()
