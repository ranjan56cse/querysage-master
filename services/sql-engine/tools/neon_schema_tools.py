import os
from typing import Any

import psycopg2


def list_tables() -> list[str]:
    """Retrieves all public table names in the Neon Postgres database.

    Returns:
        List[str]: List of table names.
    """
    db_url = os.environ.get("NEON_DATABASE_URL")
    if not db_url or "YOUR_NEON_DATABASE_URL" in db_url:
        # Fallback dummy tables for testing/development
        return ["customers", "orders", "order_items", "products"]

    try:
        conn = psycopg2.connect(db_url)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"
                )
                return [row[0] for row in cur.fetchall()]
        finally:
            conn.close()
    except Exception as e:
        raise RuntimeError(f"Failed to list tables: {e}") from e


def describe_columns(table_name: str) -> list[dict[str, Any]]:
    """Describes column names and data types for the specified table in the Neon Postgres database.

    Args:
        table_name: Name of the table to describe.

    Returns:
        List[Dict[str, Any]]: List of columns, each represented as a dictionary.
    """
    db_url = os.environ.get("NEON_DATABASE_URL")
    if not db_url or "YOUR_NEON_DATABASE_URL" in db_url:
        # Fallback dummy schemas
        dummy_schemas = {
            "customers": [
                {"column_name": "customer_id", "data_type": "integer"},
                {"column_name": "first_name", "data_type": "character varying"},
                {"column_name": "last_name", "data_type": "character varying"},
                {"column_name": "email", "data_type": "character varying"},
                {"column_name": "last_order_date", "data_type": "date"},
            ],
            "orders": [
                {"column_name": "order_id", "data_type": "integer"},
                {"column_name": "customer_id", "data_type": "integer"},
                {"column_name": "order_date", "data_type": "date"},
                {"column_name": "gross_sales_amount", "data_type": "numeric"},
                {"column_name": "discount_amount", "data_type": "numeric"},
            ],
            "order_items": [
                {"column_name": "item_id", "data_type": "integer"},
                {"column_name": "order_id", "data_type": "integer"},
                {"column_name": "product_id", "data_type": "integer"},
                {"column_name": "quantity", "data_type": "integer"},
            ],
            "products": [
                {"column_name": "product_id", "data_type": "integer"},
                {"column_name": "product_name", "data_type": "character varying"},
                {"column_name": "category", "data_type": "character varying"},
                {"column_name": "selling_price", "data_type": "numeric"},
                {"column_name": "cost_price", "data_type": "numeric"},
            ],
        }
        return dummy_schemas.get(table_name, [])

    try:
        conn = psycopg2.connect(db_url)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = %s;",
                    (table_name,),
                )
                return [
                    {"column_name": row[0], "data_type": row[1]}
                    for row in cur.fetchall()
                ]
        finally:
            conn.close()
    except Exception as e:
        raise RuntimeError(
            f"Failed to describe columns for table '{table_name}': {e}"
        ) from e
