import logging
import os
from typing import Any

import sqlparse
from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.apps import App
from google.adk.events import EventActions
from google.adk.events.event import Event
from google.adk.tools import FunctionTool
from google.adk.workflow import START, Edge, Workflow, node
from google.genai import types
from pydantic import BaseModel

from tools.neon_schema_tools import describe_columns, list_tables

# Configure logging
logging.basicConfig(level=logging.INFO)


# Edge.chain helper definition
def _edge_chain(nodes_list):
    edges_list = []
    for i in range(len(nodes_list) - 1):
        edges_list.append((nodes_list[i], nodes_list[i + 1]))
    return edges_list


Edge.chain = staticmethod(_edge_chain)

# Read configurations
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ontology_path = os.path.join(base_dir, "config", "ontology.yaml")
few_shot_path = os.path.join(base_dir, "config", "few_shot_examples.yaml")

ontology_rules = ""
if os.path.exists(ontology_path):
    try:
        with open(ontology_path) as f:
            ontology_rules = f.read()
    except Exception as e:
        logging.warning(f"Could not read ontology rules: {e}")

few_shot_examples = ""
if os.path.exists(few_shot_path):
    try:
        with open(few_shot_path) as f:
            few_shot_examples = f.read()
    except Exception as e:
        logging.warning(f"Could not read few shot examples: {e}")


# Define state and schemas
class SqlEngineState(BaseModel):
    user_query: str | None = None
    schema_hint: str | None = None
    enriched_context: str | None = None
    tables_used: list[str] | None = None
    generated_sql: str | None = None
    retry_count: int = 0
    correction_message: str | None = None


class SchemaContextOutput(BaseModel):
    enriched_context: str
    tables_used: list[str]


class SqlGeneratorOutput(BaseModel):
    generated_sql: str


class SqlEngineResponse(BaseModel):
    generated_sql: str
    enriched_context: str
    tables_used: list[str]


# Define nodes
@node
def receive_request(ctx: Context, node_input: types.Content) -> Event:
    """Extracts user query and schema hints from request."""
    query_text = ""
    if node_input and node_input.parts:
        query_text = "".join(part.text for part in node_input.parts if part.text)

    # Check if hints were provided in the state or request custom_metadata
    schema_hint = ctx.state.get("schema_hint", "")
    return Event(
        output=query_text,
        actions=EventActions(
            state_delta={"user_query": query_text, "schema_hint": schema_hint}
        ),
    )


# Llm Agents
schema_context = LlmAgent(
    name="schema_context",
    model="gemini-2.5-flash",
    instruction=(
        "You are an expert database schema analyst. Your task is to select and describe the relevant "
        "database schemas needed to answer the user query.\n\n"
        "Follow these steps:\n"
        "1. List all available tables in the database using the `list_tables` tool.\n"
        "2. Identify the relevant tables for the user query, and describe their columns using `describe_columns`.\n"
        "3. Incorporate the following business ontology rules into the context: \n"
        f"{ontology_rules}\n"
        "4. Output an enriched database context containing only these relevant table definitions and the ontology rules. "
        "Select and prioritize schemas carefully, enforcing a strict 8000-token budget for the overall prompt content.\n"
        "5. Populate the output schema with the final `enriched_context` and a list of `tables_used`."
    ),
    tools=[
        FunctionTool(list_tables, require_confirmation=False),
        FunctionTool(describe_columns, require_confirmation=False),
    ],
    output_schema=SchemaContextOutput,
    output_key="schema_context_output",
)

sql_generator = LlmAgent(
    name="sql_generator",
    model="gemini-2.5-flash",
    instruction=(
        "You are an expert SQL generator. Your task is to convert the user's natural language question "
        "into a valid, read-only PostgreSQL SELECT query.\n\n"
        "Requirements:\n"
        "- Generate ONLY a SELECT query. Never include mutations (DELETE, DROP, UPDATE, INSERT, ALTER, TRUNCATE).\n"
        "- Always use table aliases for clarity.\n"
        "- Enforce a result limit of 1000 rows unless specified otherwise.\n"
        "- Base your query on the enriched database context provided in the conversation history.\n\n"
        "Use the following few-shot examples for guidance on style, metrics, and active filter rules:\n"
        f"{few_shot_examples}\n\n"
        "If a previous query attempt failed with a syntax check error, analyze the error message provided "
        "in the conversation history and correct the query accordingly."
    ),
    output_schema=SqlGeneratorOutput,
    output_key="sql_generator_output",
)


@node
def self_correct(ctx: Context, node_input: dict) -> Event:
    """Checks the generated SQL query for syntax issues and self-corrects up to 3 times."""
    sql = node_input.get("generated_sql", "").strip()

    # Quick syntax parsing check using sqlparse
    errors = []
    if not sql:
        errors.append("SQL query is empty.")
    else:
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                errors.append("Failed to parse SQL query.")
            else:
                stmt = parsed[0]
                if stmt.get_type() != "SELECT":
                    errors.append(
                        f"Restricted query type: Only SELECT queries allowed. Got: {stmt.get_type()}"
                    )
        except Exception as e:
            errors.append(f"SQL Syntax Exception: {e}")

    retry_count = ctx.state.get("retry_count", 0)
    if errors and retry_count < 3:
        logging.warning(
            f"SQL check failed: {errors}. Retrying ({retry_count + 1}/3)..."
        )
        return Event(
            output=sql,
            actions=EventActions(
                route="retry",
                state_delta={
                    "retry_count": retry_count + 1,
                    "correction_message": f"Syntax error(s) found: {', '.join(errors)}. Please correct this SQL query.",
                },
            ),
        )

    # Route to output if valid or retries exhausted
    return Event(output=node_input, actions=EventActions(route="output"))


@node
def output_node(ctx: Context, node_input: Any) -> Event:
    """Assembles final generated SQL, enriched context, and tables used."""
    schema_data = ctx.state.get("schema_context_output", {})
    sql_data = ctx.state.get("sql_generator_output", {})

    result = {
        "generated_sql": sql_data.get("generated_sql", ""),
        "enriched_context": schema_data.get("enriched_context", ""),
        "tables_used": schema_data.get("tables_used", []),
    }
    return Event(output=result, actions=EventActions(state_delta=result))


# Define Graph Workflow using Edge.chain & manually wiring branches
root_agent = Workflow(
    name="sql_engine",
    state_schema=SqlEngineState,
    edges=[
        *Edge.chain(
            [START, receive_request, schema_context, sql_generator, self_correct]
        ),
        (self_correct, {"retry": sql_generator, "output": output_node}),
    ],
)

app = App(root_agent=root_agent, name="app")
