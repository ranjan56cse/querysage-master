# ruff: noqa: E402
import logging
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
)
load_dotenv()

import httpx
import sqlparse
from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.apps import App, ResumabilityConfig
from google.adk.apps.app import EventsCompactionConfig
from google.adk.apps.llm_event_summarizer import LlmEventSummarizer
from google.adk.events import EventActions
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.memory import InMemoryMemoryService
from google.adk.models import Gemini
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.adk.workflow import START, Edge, Workflow, node
from google.genai import types
from pydantic import BaseModel

from context.context_engine import ContextEngine

# Import tools and Context Engine
from tools.neon_tools import generate_chart, neon_execute_sql

# Configure logging
logging.basicConfig(level=logging.INFO)

# Expose process-wide service instances
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()
context_engine = ContextEngine(max_tokens=8000)


# Edge.chain helper definition
def _edge_chain(nodes_list):
    edges_list = []
    for i in range(len(nodes_list) - 1):
        edges_list.append((nodes_list[i], nodes_list[i + 1]))
    return edges_list


Edge.chain = staticmethod(_edge_chain)


# Define state and schemas
class QuerySageState(BaseModel):
    user_query: str | None = None
    sanitized_query: str | None = None
    sql_query: str | None = None
    sql_results: list[dict[str, Any]] | None = None
    visualization: str | None = None
    insights: str | None = None
    executor_output: dict[str, Any] | None = None
    insight_output: dict[str, Any] | None = None


class ExecutorOutput(BaseModel):
    sql_results: list[dict[str, Any]]
    chart_type: str
    message: str


class InsightOutput(BaseModel):
    insights: str
    follow_up_questions: list[str]


# Define nodes


@node
def receive_query(ctx: Context, node_input: types.Content) -> Event:
    """Extracts the query text from the input content and stores it in the state."""
    query_text = ""
    if node_input and node_input.parts:
        query_text = "".join(part.text for part in node_input.parts if part.text)

    return Event(
        output=query_text,
        actions=EventActions(
            state_delta={"user_query": query_text, "sanitized_query": query_text}
        ),
    )


@node
def validate_query(ctx: Context, node_input: str) -> Event:
    """Validates the input query with the external Gatekeeper service or falls back."""
    cached = ctx.state.get("sanitized_query")
    if cached:
        return Event(output=cached)
    url = os.environ.get("GATEKEEPER_SERVICE_URL")
    if not url or "YOUR_GATEKEEPER_SERVICE_URL" in url:
        logging.warning(
            "Gatekeeper URL not configured or placeholder. Passing query through unchanged."
        )
        return Event(output=node_input)
    try:
        resp = httpx.post(url, json={"query": node_input}, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        sanitized = data.get("sanitized_query", node_input)
        return Event(
            output=sanitized,
            actions=EventActions(state_delta={"sanitized_query": sanitized}),
        )
    except Exception as e:
        logging.warning(
            f"Failed to call Gatekeeper service: {e}. Passing query through unchanged."
        )
        return Event(output=node_input)


@node
def generate_sql(ctx: Context, node_input: str) -> Event:
    """Generates SQL using the external SQL Engine service or falls back to a placeholder."""
    cached = ctx.state.get("sql_query")
    if cached:
        return Event(output=cached)
    url = os.environ.get("SQL_ENGINE_SERVICE_URL")
    if not url or "YOUR_SQL_ENGINE_SERVICE_URL" in url:
        logging.warning(
            "SQL Engine URL not configured or placeholder. Returning placeholder SQL query."
        )
        placeholder = "SELECT * FROM orders LIMIT 5;"
        return Event(
            output=placeholder,
            actions=EventActions(state_delta={"sql_query": placeholder}),
        )
    try:
        resp = httpx.post(url, json={"query": node_input}, timeout=60.0)
        resp.raise_for_status()
        data = resp.json()
        sql = data.get("sql_query", "SELECT * FROM orders LIMIT 5;")
        return Event(output=sql, actions=EventActions(state_delta={"sql_query": sql}))
    except Exception as e:
        logging.warning(
            f"Failed to call SQL Engine service: {e}. Returning placeholder SQL query."
        )
        placeholder = "SELECT * FROM orders LIMIT 5;"
        return Event(
            output=placeholder,
            actions=EventActions(state_delta={"sql_query": placeholder}),
        )


@node
def security_checkpoint(ctx: Context, node_input: str) -> Event:
    """Checks the generated SQL query for mutation keywords and routes accordingly."""
    cleaned = node_input.strip()
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
    try:
        parsed = sqlparse.parse(cleaned)
        if not parsed:
            return Event(output=node_input, actions=EventActions(route="invalid"))
        for stmt in parsed:
            if stmt.get_type() != "SELECT":
                return Event(output=node_input, actions=EventActions(route="invalid"))
            for token in stmt.flatten():
                if token.value.upper() in blocked_keywords:
                    return Event(
                        output=node_input, actions=EventActions(route="invalid")
                    )
        return Event(output=node_input, actions=EventActions(route="valid"))
    except Exception:
        return Event(output=node_input, actions=EventActions(route="invalid"))


@node(rerun_on_resume=True)
async def approve_sql(ctx: Context, node_input: str):
    """Requests user confirmation before executing the SQL statement."""
    if not ctx.resume_inputs or "approved" not in ctx.resume_inputs:
        yield RequestInput(
            interrupt_id="approved",
            message=f"Neon SQL Execution request:\n```sql\n{node_input}\n```\nDo you approve execution? (yes/no)",
        )
        return

    user_response = ctx.resume_inputs["approved"].strip().lower()
    if user_response in ("yes", "y", "approve", "approved"):
        yield Event(output=node_input, actions=EventActions(route="approved"))
    else:
        yield Event(output=node_input, actions=EventActions(route="rejected"))


@node
def reject_query(ctx: Context, node_input: str) -> Event:
    """Handles query rejection and outputs mutation warning messages."""
    msg = f"Security / User Checkpoint Blocked or Rejected Query execution: '{node_input}'"
    return Event(
        output=msg,
        actions=EventActions(
            state_delta={
                "executor_output": {
                    "sql_results": [],
                    "chart_type": "table",
                    "message": msg,
                }
            }
        ),
    )


# LLM Agents
executor = LlmAgent(
    name="executor",
    model="gemini-2.5-flash",
    instruction=(
        "You are an expert database administrator. You have access to a Neon Postgres database. "
        "Your predecessor has generated a SQL query to answer the user's question. "
        "You MUST run this SQL query using the `neon_execute_sql` tool to retrieve the results. "
        'Note that `neon_execute_sql` returns a dictionary in the format `{"columns": [...], "rows": [...]}`. '
        "You MUST transform this result into a list of dictionaries where each dictionary maps column names to values "
        '(e.g., `[{"col1": val1, "col2": val2}, ...]`) and store this transformed list in `sql_results` in the output schema. '
        "Analyze the results and determine the best visualization chart type ('bar', 'line', 'pie', 'table'). "
        "Populate the final schema including `sql_results`, `chart_type`, and a summary `message`."
    ),
    tools=[
        FunctionTool(neon_execute_sql, require_confirmation=False)
    ],  # confirmation handled at graph checkpoint
    output_schema=ExecutorOutput,
    output_key="executor_output",
)


@node
def insight_router(ctx: Context, node_input: dict) -> Event:
    """Conditionally routes to insight discovery if query results exist in the output."""
    sql_results = node_input.get("sql_results", [])
    if sql_results:
        return Event(output=node_input, actions=EventActions(route="explore"))
    return Event(output=node_input, actions=EventActions(route="skip"))


insight_discovery = LlmAgent(
    name="insight_discovery",
    model="gemini-2.5-flash",
    instruction=(
        "You are a senior business intelligence analyst. "
        "Review the SQL query results stored in the workflow state (`executor_output`). "
        "You have access to the `neon_execute_sql` tool to perform additional SELECT queries "
        "if you want to dive deeper into the database to find anomalies, trends, or correlations. "
        "Analyze the data BEYOND the user's original question. Look for: "
        "- Anomalies — values deviating significantly from norms\n"
        "- Trends — patterns over time dimensions\n"
        "- Correlations — relationships between columns\n"
        "Generate 2-3 follow-up natural language questions the user should ask next. "
        "If no interesting patterns are found, pass through with a brief note stating that."
    ),
    tools=[FunctionTool(neon_execute_sql, require_confirmation=False)],
    output_schema=InsightOutput,
    output_key="insight_output",
)


@node
async def present_results(ctx: Context, node_input: Any) -> Event:
    """Assembles the final output structure containing the SQL results table, plotly chart, and insights."""
    # Check if we got a simple rejection message or structured insight dict
    is_rejected = isinstance(node_input, str)

    executor_data = ctx.state.get("executor_output", {})
    sql_results = executor_data.get("sql_results", [])
    chart_type = executor_data.get("chart_type", "table")
    message = executor_data.get("message", "")

    # Compile markdown response
    md_response = "## QuerySage Analysis Results\n\n"

    if is_rejected:
        md_response += f"⚠️ **Execution Blocked**\n{node_input}\n"
        yield Event(
            content=types.Content(
                role="model", parts=[types.Part.from_text(text=md_response)]
            )
        )
        yield Event(output=md_response)
        return

    # Success Flow Chart Generation
    chart_path = ""
    if sql_results:
        columns = list(sql_results[0].keys())
        rows = [list(r.values()) for r in sql_results]
        data = {"columns": columns, "rows": rows}
        try:
            chart_path = generate_chart(data, chart_type)
        except Exception as e:
            logging.error(f"Failed to generate chart: {e}")

    if sql_results:
        md_response += "### SQL Results\n"
        headers = list(sql_results[0].keys())
        md_response += "| " + " | ".join(headers) + " |\n"
        md_response += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        for row in sql_results[:10]:
            md_response += (
                "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |\n"
            )
        if len(sql_results) > 10:
            md_response += f"\n*(Showing top 10 of {len(sql_results)} rows)*\n"
        md_response += "\n"
    else:
        md_response += (
            f"*No results returned from query execution. Details: {message}*\n\n"
        )

    if chart_path:
        md_response += "### Visualization\n"
        md_response += f"Chart saved to: [chart.html](file:///{chart_path.replace(os.sep, '/')})\n\n"

    # Handle insights section depending on if the optional branch was run
    if isinstance(node_input, dict) and "insights" in node_input:
        insights = node_input.get("insights", "")
        questions = node_input.get("follow_up_questions", [])
        md_response += f"### Insights\n{insights}\n\n"
        if questions:
            md_response += "### Suggested Follow-up Questions\n"
            md_response += "\n".join(f"- {q}" for q in questions) + "\n"
    else:
        md_response += "### Insights\n*No additional insights generated as query results exploration was skipped or empty.*\n\n"

    # Long-term Memory registration for successful queries
    try:
        await memory_service.add_session_to_memory(ctx.session)
        logging.info("Interaction recorded in long-term memory successfully.")
    except Exception as e:
        logging.error(f"Failed to write to long-term memory: {e}")

    # Emit Content Event for Web UI
    yield Event(
        content=types.Content(
            role="model", parts=[types.Part.from_text(text=md_response)]
        )
    )
    yield Event(output=md_response)


# Define Graph Workflow using Edge.chain & manually wiring branches
root_agent = Workflow(
    name="querysage",
    state_schema=QuerySageState,
    edges=[
        *Edge.chain(
            [START, receive_query, validate_query, generate_sql, security_checkpoint]
        ),
        (security_checkpoint, {"valid": approve_sql, "invalid": reject_query}),
        (approve_sql, {"approved": executor, "rejected": reject_query}),
        (executor, insight_router),
        (insight_router, {"explore": insight_discovery, "skip": present_results}),
        (insight_discovery, present_results),
        (reject_query, present_results),
    ],
)

# App wrapping with Resumability enabled for Human-in-the-Loop,
# along with EventsCompactionConfig.
app = App(
    root_agent=root_agent,
    name="app",
    resumability_config=ResumabilityConfig(is_resumable=True),
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=10,
        event_retention_size=5,
        token_threshold=1000,
        overlap_size=2,
        summarizer=LlmEventSummarizer(llm=Gemini(model="gemini-2.5-flash")),
    ),
)
