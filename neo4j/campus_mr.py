"""CampusGraph: course prerequisites and friendship graph in Neo4j.

Commands:
    python campus_extended.py setup        # Wipe and reload the dataset
    python campus_extended.py check        # Run Task 1-7 and extension checks
    python campus_extended.py extensions   # Run extension checks only
    python campus_extended.py cycle-demo   # Add a deliberately wrong edge and detect cycle
    python campus_extended.py clean-cycle  # Remove the deliberately wrong edge
    python campus_extended.py gds           # Run PageRank and Louvain (requires Neo4j GDS)

Default connection:
    bolt://localhost:7687
    username: neo4j
    password: learnneo4j

Override with environment variables NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD.
"""

import os
import sys
from neo4j import GraphDatabase

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
AUTH = (
    os.getenv("NEO4J_USER", "neo4j"),
    os.getenv("NEO4J_PASSWORD", "learnneo4j"),
)
driver = GraphDatabase.driver(URI, auth=AUTH)


# ---------------------------------------------------------------------------
# Dataset

COURSES = [  # (code, title, credits)
    ("CS101", "Intro to Programming", 3),
    ("MATH101", "Calculus", 3),
    ("MATH102", "Linear Algebra", 3),
    ("STAT101", "Probability and Statistics", 3),
    ("CS102", "Data Structures", 3),
    ("DB201", "Databases", 3),
    ("VIZ201", "Data Visualization", 2),
    ("ML201", "Machine Learning", 4),
    ("DE301", "Data Engineering", 3),
    ("DB301", "NoSQL Databases", 3),
    ("DL301", "Deep Learning", 4),
    ("NLP401", "Natural Language Processing", 3),
    ("CAP401", "Capstone Project", 6),
]

REQUIRES = [  # (course, prerequisite)
    ("MATH102", "MATH101"),
    ("STAT101", "MATH101"),
    ("CS102", "CS101"),
    ("DB201", "CS102"),
    ("VIZ201", "CS101"),
    ("VIZ201", "STAT101"),
    ("ML201", "CS102"),
    ("ML201", "MATH102"),
    ("ML201", "STAT101"),
    ("DE301", "DB201"),
    ("DE301", "CS102"),
    ("DB301", "DB201"),
    ("DL301", "ML201"),
    ("NLP401", "DL301"),
    ("CAP401", "DB301"),
    ("CAP401", "ML201"),
]

STUDENTS = [  # (id, name, year)
    ("S01", "An", 3),
    ("S02", "Binh", 2),
    ("S03", "Chi", 3),
    ("S04", "Dung", 1),
    ("S05", "Giang", 2),
    ("S06", "Hoa", 3),
    ("S07", "Khoa", 2),
    ("S08", "Lan", 1),
    ("S09", "Minh", 3),
    ("S10", "Phuong", 2),
]

PASSED = {  # student -> {course: grade}
    "S01": {"CS101": 8.5, "MATH101": 7.0, "CS102": 8.0, "MATH102": 6.5, "STAT101": 7.5, "DB201": 9.0},
    "S02": {"CS101": 7.0, "MATH101": 8.0, "STAT101": 8.5, "VIZ201": 9.0},
    "S03": {"CS101": 9.0, "MATH101": 9.5, "MATH102": 9.0, "STAT101": 8.0, "CS102": 8.5, "ML201": 9.0, "DB201": 7.5},
    "S04": {"CS101": 6.5, "MATH101": 7.5},
    "S05": {"CS101": 8.0, "CS102": 7.5, "DB201": 8.0, "MATH101": 6.0},
    "S06": {"CS101": 9.5, "MATH101": 8.5, "MATH102": 8.0, "STAT101": 9.0, "CS102": 9.0, "DB201": 8.5, "DB301": 9.0, "ML201": 8.0},
    "S07": {"CS101": 7.5, "MATH101": 7.0, "STAT101": 6.5, "CS102": 7.0},
    "S08": {"CS101": 8.0},
    "S09": {"CS101": 8.0, "MATH101": 8.0, "MATH102": 7.5, "STAT101": 7.0, "CS102": 8.0, "DB201": 8.0, "ML201": 7.5, "DL301": 8.5, "VIZ201": 8.0},
    "S10": {"CS101": 9.0, "MATH101": 9.0, "STAT101": 8.0, "VIZ201": 8.5, "CS102": 7.5},
}

# FRIEND is stored once; queries use undirected pattern matching because friendship is mutual.
FRIENDS = [
    ("S01", "S02"),
    ("S01", "S05"),
    ("S02", "S04"),
    ("S04", "S08"),
    ("S05", "S07"),
    ("S07", "S10"),
    ("S03", "S06"),
    ("S03", "S09"),
    ("S06", "S09"),
    ("S09", "S10"),
    ("S08", "S10"),
]


# ---------------------------------------------------------------------------
# Setup

def setup():
    """Wipe the database, create constraints and load the dataset."""
    def q(cypher, **params):
        return driver.execute_query(cypher, params)

    q("MATCH (n) DETACH DELETE n")
    q("CREATE CONSTRAINT student_id IF NOT EXISTS FOR (s:Student) REQUIRE s.id IS UNIQUE")
    q("CREATE CONSTRAINT course_code IF NOT EXISTS FOR (c:Course) REQUIRE c.code IS UNIQUE")

    q(
        """
        UNWIND $rows AS r
        MERGE (c:Course {code: r[0]})
        SET c.title = r[1], c.credits = r[2]
        """,
        rows=[list(c) for c in COURSES],
    )
    q(
        """
        UNWIND $rows AS r
        MATCH (c:Course {code: r[0]}), (p:Course {code: r[1]})
        MERGE (c)-[:REQUIRES]->(p)
        """,
        rows=[list(r) for r in REQUIRES],
    )
    q(
        """
        UNWIND $rows AS r
        MERGE (s:Student {id: r[0]})
        SET s.name = r[1], s.year = r[2]
        """,
        rows=[list(s) for s in STUDENTS],
    )
    q(
        """
        UNWIND $rows AS r
        MATCH (s:Student {id: r.sid}), (c:Course {code: r.code})
        MERGE (s)-[p:PASSED]->(c)
        SET p.grade = r.grade
        """,
        rows=[
            {"sid": sid, "code": code, "grade": grade}
            for sid, courses in PASSED.items()
            for code, grade in courses.items()
        ],
    )
    q(
        """
        UNWIND $rows AS r
        MATCH (a:Student {id: r[0]}), (b:Student {id: r[1]})
        MERGE (a)-[:FRIEND]->(b)
        """,
        rows=[list(friend) for friend in FRIENDS],
    )

    counts = driver.execute_query(
        "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY label"
    ).records
    print("Database loaded:", {r["label"]: r["n"] for r in counts})


# ---------------------------------------------------------------------------
# Original Tasks 1-7

def passed_courses(student_id):
    """Task 1. Courses passed by a student, best grade first, then by code."""
    result = driver.execute_query(
        """
        MATCH (:Student {id: $sid})-[p:PASSED]->(c:Course)
        RETURN c.code AS code, p.grade AS grade
        ORDER BY grade DESC, code
        """,
        sid=student_id,
    )
    return [(r["code"], r["grade"]) for r in result.records]


def prerequisite_chain(code):
    """Task 2. Direct and indirect prerequisites with minimum depth."""
    result = driver.execute_query(
        """
        MATCH path = (:Course {code: $code})-[:REQUIRES*1..]->(pre:Course)
        WITH pre, min(length(path)) AS depth
        RETURN pre.code AS code, depth
        ORDER BY depth, code
        """,
        code=code,
    )
    return [(r["code"], r["depth"]) for r in result.records]


def eligible_courses(student_id):
    """Task 3. Courses not passed whose direct prerequisites are all passed."""
    result = driver.execute_query(
        """
        MATCH (s:Student {id: $sid})
        MATCH (c:Course)
        WHERE NOT EXISTS {
            MATCH (s)-[:PASSED]->(c)
        }
        AND NOT EXISTS {
            MATCH (c)-[:REQUIRES]->(pre:Course)
            WHERE NOT EXISTS {
                MATCH (s)-[:PASSED]->(pre)
            }
        }
        RETURN c.code AS code
        ORDER BY code
        """,
        sid=student_id,
    )
    return [r["code"] for r in result.records]


def suggest_friends(student_id, k=3):
    """Task 4 + Extension 3. Rank non-friends by shared courses + 2*mutual friends.

    Returns (name, shared_courses, mutual_friends, score).
    """
    result = driver.execute_query(
        """
        MATCH (me:Student {id: $sid})
        MATCH (other:Student)
        WHERE other.id <> me.id
          AND NOT EXISTS {
              MATCH (me)-[:FRIEND]-(other)
          }

        OPTIONAL MATCH (me)-[:PASSED]->(c:Course)<-[:PASSED]-(other)
        WITH me, other, count(DISTINCT c) AS shared_courses

        OPTIONAL MATCH (me)-[:FRIEND]-(mutual:Student)-[:FRIEND]-(other)
        WITH other, shared_courses, count(DISTINCT mutual) AS mutual_friends

        WITH other, shared_courses, mutual_friends,
             shared_courses + 2 * mutual_friends AS score
        RETURN other.name AS name,
               shared_courses,
               mutual_friends,
               score
        ORDER BY score DESC, name
        LIMIT $k
        """,
        sid=student_id,
        k=k,
    )
    return [
        (r["name"], r["shared_courses"], r["mutual_friends"], r["score"])
        for r in result.records
    ]


def connection(a_id, b_id):
    """Task 5. Names along the shortest FRIEND path (ignore direction)."""
    result = driver.execute_query(
        """
        MATCH (a:Student {id: $a_id}), (b:Student {id: $b_id})
        MATCH path = shortestPath((a)-[:FRIEND*]-(b))
        RETURN [n IN nodes(path) | n.name] AS names
        """,
        a_id=a_id,
        b_id=b_id,
    )
    return result.records[0]["names"] if result.records else []


def bottleneck_courses(k=3):
    """Task 6. Courses depended on by the most other courses."""
    result = driver.execute_query(
        """
        MATCH (dependent:Course)-[:REQUIRES*1..]->(base:Course)
        WITH base, count(DISTINCT dependent) AS dependents
        RETURN base.code AS code, dependents
        ORDER BY dependents DESC, code
        LIMIT $k
        """,
        k=k,
    )
    return [(r["code"], r["dependents"]) for r in result.records]


def _record_pass_tx(tx, student_id, code, grade):
    """Transaction helper for Task 7."""
    check_result = tx.run(
        """
        MATCH (s:Student {id: $sid})
        SET s._write_lock = coalesce(s._write_lock, 0) + 1
        WITH s
        OPTIONAL MATCH (c:Course {code: $code})
        WITH s, c
        OPTIONAL MATCH (c)-[:REQUIRES]->(pre:Course)
        WHERE NOT EXISTS {
            MATCH (s)-[:PASSED]->(pre)
        }
        WITH s, c, collect(DISTINCT pre.code) AS missing
        RETURN s.id AS student_id, c.code AS course_code, missing
        """,
        sid=student_id,
        code=code,
    ).single()

    if check_result is None:
        raise ValueError(f"unknown student: {student_id}")
    if check_result["course_code"] is None:
        raise ValueError(f"unknown course: {code}")
    if check_result["missing"]:
        raise ValueError(f"missing prerequisites: {sorted(check_result['missing'])}")

    tx.run(
        """
        MATCH (s:Student {id: $sid}), (c:Course {code: $code})
        MERGE (s)-[p:PASSED]->(c)
        SET p.grade = $grade
        """,
        sid=student_id,
        code=code,
        grade=grade,
    ).consume()


def record_pass(student_id, code, grade):
    """Task 7. Record a pass in one write transaction; reject missing prerequisites."""
    with driver.session() as session:
        session.execute_write(_record_pass_tx, student_id, code, grade)


# ---------------------------------------------------------------------------
# Extensions 1-2


def credits_to_reach(student_id, code):
    """
    Extension 1.
    Calculate total credits of all direct and indirect
    prerequisites that the student has not passed.
    """
    result = driver.execute_query(
        """
        MATCH (s:Student {id: $sid})
        MATCH (target:Course {code: $code})

        OPTIONAL MATCH (target)-[:REQUIRES*1..]->(pre:Course)

        WITH s, collect(DISTINCT pre) AS all_prerequisites

        WITH s, [
            c IN all_prerequisites
            WHERE c IS NOT NULL
            AND NOT EXISTS {
                MATCH (s)-[:PASSED]->(c)
            }
        ] AS missing_prerequisites

        RETURN reduce(
            total = 0,
            c IN missing_prerequisites |
            total + coalesce(c.credits, 0)
        ) AS total_credits
        """,
        sid=student_id,
        code=code,
    )

    if not result.records:
        raise ValueError("Unknown student or course")

    return result.records[0]["total_credits"]



def find_prerequisite_cycles():
    """Extension 2. Return cycles in the REQUIRES graph as lists of course codes."""
    result = driver.execute_query(
        """
        MATCH path = (c:Course)-[:REQUIRES*1..]->(c)
        RETURN DISTINCT [n IN nodes(path) | n.code] AS cycle
        ORDER BY cycle
        """
    )
    return [r["cycle"] for r in result.records]


def add_demo_cycle():
    """Add one deliberately incorrect prerequisite edge for cycle demonstration."""
    driver.execute_query(
        """
        MATCH (a:Course {code: 'MATH101'}), (b:Course {code: 'ML201'})
        MERGE (a)-[:REQUIRES]->(b)
        """
    )
    print("Demo edge added: MATH101 -[:REQUIRES]-> ML201")
    print("Detected cycles:", find_prerequisite_cycles())


def remove_demo_cycle():
    """Remove the deliberately incorrect edge added by add_demo_cycle()."""
    driver.execute_query(
        """
        MATCH (a:Course {code: 'MATH101'})-[r:REQUIRES]->(b:Course {code: 'ML201'})
        DELETE r
        """
    )
    print("Demo edge removed.")


# ---------------------------------------------------------------------------
# Extension 4: Graph Data Science (GDS)

def gds_create_projection(graph_name="campusFriends"):
    """Create an undirected in-memory graph projection of student friendships."""
    result = driver.execute_query(
        """
        CALL gds.graph.project(
            $graph_name,
            'Student',
            {FRIEND: {orientation: 'UNDIRECTED'}}
        )
        YIELD graphName, nodeCount, relationshipCount
        RETURN graphName, nodeCount, relationshipCount
        """,
        graph_name=graph_name,
    )
    return [dict(record) for record in result.records]


def gds_pagerank(graph_name="campusFriends"):
    """Run PageRank and return students ranked by network importance."""
    result = driver.execute_query(
        """
        CALL gds.pageRank.stream($graph_name)
        YIELD nodeId, score
        RETURN gds.util.asNode(nodeId).name AS student, score
        ORDER BY score DESC, student
        """,
        graph_name=graph_name,
    )
    return [(r["student"], r["score"]) for r in result.records]


def gds_louvain(graph_name="campusFriends"):
    """Run Louvain and return each student's detected community."""
    result = driver.execute_query(
        """
        CALL gds.louvain.stream($graph_name)
        YIELD nodeId, communityId
        RETURN gds.util.asNode(nodeId).name AS student, communityId
        ORDER BY communityId, student
        """,
        graph_name=graph_name,
    )
    return [(r["student"], r["communityId"]) for r in result.records]


def gds_drop_projection(graph_name="campusFriends"):
    """Drop an in-memory graph projection if it exists."""
    result = driver.execute_query(
        """
        CALL gds.graph.exists($graph_name)
        YIELD exists
        RETURN exists
        """,
        graph_name=graph_name,
    )
    if result.records and result.records[0]["exists"]:
        driver.execute_query(
            "CALL gds.graph.drop($graph_name)", graph_name=graph_name
        )
        print(f"Dropped GDS graph: {graph_name}")


def run_gds_analysis():
    """Create projection, run PageRank and Louvain, then drop projection."""
    graph_name = "campusFriends"
    try:
        print("Projection:", gds_create_projection(graph_name))
        print("\nPageRank:")
        for student, score in gds_pagerank(graph_name):
            print(f"  {student}: {score:.6f}")
        print("\nLouvain communities:")
        for student, community_id in gds_louvain(graph_name):
            print(f"  {student}: community {community_id}")
    finally:
        gds_drop_projection(graph_name)


# ---------------------------------------------------------------------------
# Self-check

def check():
    """Reload the original dataset, then check Tasks 1-7 and extensions 1-3."""
    setup()

    def expect_error(fn):
        try:
            fn()
        except ValueError as exc:
            return str(exc)
        return None

    def after_record():
        record_pass("S08", "CS102", 7.0)
        record_pass("S08", "CS102", 7.5)  # Same pass updates, does not duplicate.
        row = driver.execute_query(
            """
            MATCH (:Student {id: 'S08'})-[p:PASSED]->(:Course {code: 'CS102'})
            RETURN count(p) AS n, max(p.grade) AS g
            """
        ).records[0]
        return (row["n"], row["g"], eligible_courses("S08"))

    tests = [
        ("1 passed_courses", lambda: passed_courses("S04"),
         [("MATH101", 7.5), ("CS101", 6.5)]),
        ("2 prerequisite_chain", lambda: prerequisite_chain("DE301"),
         [("CS102", 1), ("DB201", 1), ("CS101", 2)]),
        ("3 eligible_courses", lambda: eligible_courses("S01"),
         ["DB301", "DE301", "ML201", "VIZ201"]),
        ("4 suggest_friends (scored)", lambda: suggest_friends("S02"),
         [("Giang", 2, 1, 4), ("Minh", 4, 0, 4), ("Phuong", 4, 0, 4)]),
        ("5 connection", lambda: connection("S01", "S08"),
         ["An", "Binh", "Dung", "Lan"]),
        ("6 bottleneck_courses", lambda: bottleneck_courses(),
         [("CS101", 9), ("CS102", 7), ("MATH101", 7)]),
        ("7a record_pass refuses", lambda: expect_error(
            lambda: record_pass("S04", "ML201", 8.0)),
         "missing prerequisites: ['CS102', 'MATH102', 'STAT101']"),
        ("7b record_pass writes", after_record,
         (1, 7.5, ["DB201", "MATH101"])),
        ("Extension 1 credits_to_reach", lambda: credits_to_reach("S08", "ML201"), 9),
        ("Extension 2 no cycle in clean dataset", lambda: find_prerequisite_cycles(), []),
    ]

    print("\n--- TASK AND EXTENSION CHECKS ---")
    for name, fn, expected in tests:
        try:
            actual = fn()
            status = "PASS" if actual == expected else "FAIL"
            print(f"{status} {name}")
            if actual != expected:
                print(f"    expected: {expected}")
                print(f"    got:      {actual}")
        except Exception as exc:
            print(f"ERROR {name}: {type(exc).__name__}: {exc}")

    print("\nExtension 3 example (S02):")
    print(suggest_friends("S02"))
    print("\nNote: GDS PageRank/Louvain are run separately with: python campus_extended.py gds")


def check_extensions():
    """Run extensions against the currently loaded database without resetting it."""
    print("Extension 1 - credits_to_reach(S08, ML201):",
          credits_to_reach("S08", "ML201"))
    print("Extension 2 - prerequisite cycles:", find_prerequisite_cycles())
    print("Extension 3 - scored friend suggestions for S02:",
          suggest_friends("S02"))


# ---------------------------------------------------------------------------
# Command line

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "check"
    commands = {
        "setup": setup,
        "check": check,
        "extensions": check_extensions,
        "cycle-demo": add_demo_cycle,
        "clean-cycle": remove_demo_cycle,
        "gds": run_gds_analysis,
    }

    try:
        if command not in commands:
            print("Unknown command:", command)
            print("Available commands:", ", ".join(commands))
            sys.exit(1)
        commands[command]()
    finally:
        driver.close()
