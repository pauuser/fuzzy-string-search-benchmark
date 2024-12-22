import psycopg
import pandas as pd

from typing import List, Dict, Union

DB_CONFIG: Dict[str, str] = {
    "dbname": "employees",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432",
}

SURNAME_FILTER: str = "'вано'"
NAME_FILTER: str = "'ван'"
FATHERNAME_FILTER: str = "'ександрович'"

METHODS: List[Dict[str, Union[str, bool]]] = [
    {
        "name": "levenshtein_1",
        "filter": f"levenshtein(e.surname, {SURNAME_FILTER}) < 4",
    },
    {
        "name": "levenshtein_2",
        "filter": (
            f"levenshtein(e.surname, {SURNAME_FILTER}) < 4 AND "
            f"levenshtein(e.name, {NAME_FILTER}) < 4"
        ),
    },
    {
        "name": "levenshtein_3",
        "filter": (
            f"levenshtein(e.surname, {SURNAME_FILTER}) < 4 AND "
            f"levenshtein(e.name, {NAME_FILTER}) < 4 AND "
            f"levenshtein(e.fathername, {FATHERNAME_FILTER}) < 4"
        ),
    },
    {
        "name": "levenshtein_less_equal_1",
        "filter": f"levenshtein_less_equal(e.surname, {SURNAME_FILTER}, 3) < 4",
    },
    {
        "name": "levenshtein_less_equal_2",
        "filter": (
            f"levenshtein_less_equal(e.surname, {SURNAME_FILTER}, 3) < 4 AND "
            f"levenshtein_less_equal(e.name, {NAME_FILTER}, 3) < 4"
        ),
    },
    {
        "name": "levenshtein_less_equal_3",
        "filter": (
            f"levenshtein_less_equal(e.surname, {SURNAME_FILTER}, 3) < 4 AND "
            f"levenshtein_less_equal(e.name, {NAME_FILTER}, 3) < 4 AND "
            f"levenshtein_less_equal(e.fathername, {FATHERNAME_FILTER}, 3) < 4"
        ),
    },
    {
        "name": "pg_trgm_no_index_1",
        "filter": f"e.surname % {SURNAME_FILTER}",
        "use_index": False,
    },
    {
        "name": "pg_trgm_no_index_2",
        "filter": (
            f"e.surname % {SURNAME_FILTER} AND "
            f"e.name % {NAME_FILTER}"
        ),
        "use_index": False,
    },
    {
        "name": "pg_trgm_no_index_3",
        "filter": (
            f"e.surname % {SURNAME_FILTER} AND "
            f"e.name % {NAME_FILTER} AND "
            f"e.fathername % {FATHERNAME_FILTER}"
        ),
        "use_index": False,
    },
    {
        "name": "pg_trgm_with_index_1",
        "filter": f"e.surname % {SURNAME_FILTER}",
        "use_index": True,
    },
    {
        "name": "pg_trgm_with_index_2",
        "filter": (
            f"e.surname % {SURNAME_FILTER} AND "
            f"e.name % {NAME_FILTER}"
        ),
        "use_index": True,
    },
    {
        "name": "pg_trgm_with_index_3",
        "filter": (
            f"e.surname % {SURNAME_FILTER} AND "
            f"e.name % {NAME_FILTER} AND "
            f"e.fathername % {FATHERNAME_FILTER}"
        ),
        "use_index": True,
    },
]

GIN_INDEXES: List[str] = [
    "CREATE INDEX gin_surname ON employee USING GIN (surname gin_trgm_ops);",
    "CREATE INDEX gin_name ON employee USING GIN (name gin_trgm_ops);",
    "CREATE INDEX gin_fathername ON employee USING GIN (fathername gin_trgm_ops);",
    "CREATE INDEX gin_number ON document USING GIN (number gin_trgm_ops);",
]

DROP_INDEXES: List[str] = [
    "DROP INDEX IF EXISTS gin_surname;",
    "DROP INDEX IF EXISTS gin_name;",
    "DROP INDEX IF EXISTS gin_fathername;",
    "DROP INDEX IF EXISTS gin_number;",
]

def execute_query(connection: psycopg.Connection, query: str, explain: bool = False) -> List[tuple]:
    """
    Executes a query on the database.

    Args:
        connection (psycopg.Connection): The database connection.
        query (str): The SQL query to execute.
        explain (bool): Whether to include EXPLAIN ANALYZE in the query.

    Returns:
        List[tuple]: The query results as a list of tuples.
    """
    if explain:
        query = f"EXPLAIN (ANALYZE, BUFFERS, TIMING) {query}"
    with connection.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


def benchmark_query(connection: psycopg.Connection, query: str, iterations: int = 15) -> List[tuple]:
    """
    Benchmarks a query using a PostgreSQL stored procedure.

    Args:
        connection (psycopg.Connection): The database connection.
        query (str): The query to benchmark.
        iterations (int): Number of iterations for benchmarking.

    Returns:
        List[tuple]: The benchmark results as a list of tuples.
    """
    query = query.replace("'", "''")
    bench_function = f"SELECT * FROM bench('{query}', {iterations})"
    with connection.cursor() as cursor:
        cursor.execute(bench_function)
        return cursor.fetchall()


def manage_indexes(connection: psycopg.Connection, create: bool = True) -> None:
    """
    Creates or drops GIN indexes based on the 'create' flag.

    Args:
        connection (psycopg.Connection): The database connection.
        create (bool): True to create indexes, False to drop them.
    """
    queries = GIN_INDEXES if create else DROP_INDEXES
    with connection.cursor() as cursor:
        for query in queries:
            cursor.execute(query)
        connection.commit()


def benchmark_method(
    connection: psycopg.Connection,
    method: Dict[str, Union[str, bool]],
    results: List[Dict[str, Union[str, float]]],
) -> None:
    """
    Benchmarks a single method and appends results.

    Args:
        connection (psycopg.Connection): The database connection.
        method (Dict[str, Union[str, bool]]): The method to benchmark.
        results (List[Dict[str, Union[str, float]]]): List to store benchmark results.
    """
    query = (
        f"SELECT * FROM employee e WHERE {method['filter']} "
        f"ORDER BY e.Id OFFSET 0 LIMIT 20;"
    )
    use_index = method.get("use_index", False)

    if use_index:
        manage_indexes(connection, create=True)

    try:
        explain_results = execute_query(connection, query, explain=True)
        avg_explain_time = float(explain_results[-1][0].split(" ")[-2])

        bench_results = benchmark_query(connection, query)
        avg_bench_time = bench_results[0][0]

        results.append({
            "Method": method["name"],
            "Explain (ms)": avg_explain_time,
            "Bench (avg ms)": avg_bench_time,
        })

    finally:
        if use_index:
            manage_indexes(connection, create=False)


def benchmark_all() -> None:
    """
    Benchmarks all methods defined in the METHODS list and saves results to a CSV file.
    """
    results: List[Dict[str, Union[str, float]]] = []
    with psycopg.connect(**DB_CONFIG) as connection:
        for method in METHODS:
            benchmark_method(connection, method, results)

    df = pd.DataFrame(results)
    df.to_csv("benchmark_results.csv", index=False)
    print(df)


if __name__ == "__main__":
    benchmark_all()