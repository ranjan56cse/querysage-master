import os
from datetime import date, datetime
from decimal import Decimal

import plotly.express as px
import plotly.graph_objects as go
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
    # Force everything else to a JSON-safe primitive
    if not isinstance(value, (str, int, float, bool)):
        return str(value)
    return value


def neon_execute_sql(query: str) -> dict:
    """Executes a SELECT-only SQL query against Neon Postgres and returns columns and rows.

    Args:
        query: The SELECT SQL query to execute.

    Returns:
        dict: Containing 'columns' (list of str) and 'rows' (list of lists/tuples).
    """
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Query is empty.")

    # Validation: block mutation keywords
    parsed = sqlparse.parse(cleaned_query)
    if not parsed:
        raise ValueError("Could not parse SQL query.")

    blocked_keywords = {
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "TRUNCATE",
        "GRANT",
        "REVOKE",
    }
    for statement in parsed:
        # Check statement type
        stmt_type = statement.get_type()
        if stmt_type != "SELECT":
            raise ValueError(
                f"Restricted query type: Only SELECT statements are allowed. Got: {stmt_type}"
            )

        # Double check all tokens for mutation keywords (just to be extra safe)
        for token in statement.flatten():
            token_val = token.value.upper()
            if token_val in blocked_keywords:
                raise ValueError(
                    f"Security check failed: Query contains blocked mutation keyword '{token_val}'."
                )

    db_url = os.environ.get("NEON_DATABASE_URL")
    if not db_url or "YOUR_NEON_DATABASE_URL" in db_url:
        # Fallback dummy results for local testing/development
        return [
            {"id": 1, "category": "A", "val": 10},
            {"id": 2, "category": "B", "val": 20},
            {"id": 3, "category": "C", "val": 15},
        ]

    try:
        conn = psycopg2.connect(db_url)
        try:
            with conn.cursor() as cur:
                cur.execute(cleaned_query)
                if cur.description is None:
                    return []
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                return [
                    {
                        col: _make_serializable(val)
                        for col, val in zip(columns, row, strict=False)
                    }
                    for row in rows
                ]
        finally:
            conn.close()
    except Exception as e:
        raise RuntimeError(f"Database execution failed: {e}") from e


def generate_chart(data, chart_type: str) -> str:
    """Creates a Plotly chart (bar, line, pie, table), saves it as HTML, and returns the path.

    Args:
        data: List of dicts (rows) or dict with 'columns'/'rows' keys.
        chart_type: Type of chart to generate ('bar', 'line', 'pie', 'table').

    Returns:
        str: Absolute path to the saved HTML chart file.
    """
    # Handle both list[dict] and {"columns":..., "rows":...} formats
    if isinstance(data, list):
        if not data:
            columns, rows = [], []
        else:
            columns = list(data[0].keys())
            rows = [list(r.values()) for r in data]
    else:
        columns = data.get("columns", [])
        rows = data.get("rows", [])

    if not columns or not rows:
        fig = go.Figure(
            data=[
                go.Table(
                    header={"values": ["No Data"]},
                    cells={"values": [["No records found to visualize"]]},
                )
            ]
        )
    else:
        col_data = {col: [row[i] for row in rows] for i, col in enumerate(columns)}
        x_col = columns[0]
        y_col = columns[1] if len(columns) > 1 else None

        c_type = chart_type.lower().strip()
        if c_type == "bar":
            fig = px.bar(
                x=col_data[x_col],
                y=col_data[y_col] if y_col else None,
                labels={"x": x_col, "y": y_col or ""},
                title=f"{x_col.capitalize()} vs {y_col.capitalize() if y_col else ''}",
            )
        elif c_type == "line":
            fig = px.line(
                x=col_data[x_col],
                y=col_data[y_col] if y_col else None,
                labels={"x": x_col, "y": y_col or ""},
                title=f"{x_col.capitalize()} Trend",
            )
        elif c_type == "pie":
            fig = px.pie(
                names=col_data[x_col],
                values=col_data[y_col] if y_col else None,
                title=f"{x_col.capitalize()} Distribution",
            )
        else:  # "table" or fallback
            fig = go.Figure(
                data=[
                    go.Table(
                        header={
                            "values": columns,
                            "fill_color": "paleturquoise",
                            "align": "left",
                        },
                        cells={
                            "values": [col_data[col] for col in columns],
                            "fill_color": "lavender",
                            "align": "left",
                        },
                    )
                ]
            )

    # Determine save path in the workspace root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(base_dir, "chart.html")

    fig.write_html(output_path)
    return output_path
