import os
from datetime import date, datetime
from decimal import Decimal

import psycopg2
import sqlparse


def _make_serializable(value):
    """Convert DB values to JSON-serializable types."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if value is None:
        return None
    if not isinstance(value, (str, int, float, bool)):
        return str(value)
    return value


def execute_sql_query(query: str) -> dict:
    """Executes a SELECT-only SQL query against Neon Postgres and returns results.

    Args:
        query: The SELECT SQL query to execute.

    Returns:
        dict: A status dict containing 'status' and either 'results' or 'error'.
    """
    # Trim and validate statement type using sqlparse
    cleaned_query = query.strip()
    if not cleaned_query:
        return {"status": "error", "error": "Query is empty."}

    parsed = sqlparse.parse(cleaned_query)
    if not parsed:
        return {"status": "error", "error": "Could not parse SQL query."}

    for statement in parsed:
        if statement.get_type() != "SELECT":
            return {
                "status": "error",
                "error": f"Invalid query type: Only SELECT statements are allowed. Got: {statement.get_type()}",
            }

    db_url = os.environ.get("NEON_DATABASE_URL")
    if not db_url or "YOUR_NEON_DATABASE_URL" in db_url:
        return {
            "status": "warning",
            "warning": "Neon Database URL not configured. Returning placeholder results.",
            "results": [
                {"id": 1, "category": "A", "val": 10},
                {"id": 2, "category": "B", "val": 20},
                {"id": 3, "category": "C", "val": 15},
            ],
        }

    try:
        conn = psycopg2.connect(db_url)
        try:
            with conn.cursor() as cur:
                cur.execute(cleaned_query)
                if cur.description is None:
                    return {"status": "success", "results": []}
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                results = [
                    dict(
                        zip(columns, [_make_serializable(v) for v in row], strict=False)
                    )
                    for row in rows
                ]
                return {"status": "success", "results": results}
        finally:
            conn.close()
    except Exception as e:
        return {"status": "error", "error": f"Database execution failed: {e}"}
