import logging

from google.adk.agents.context import Context
from google.adk.apps import App
from google.adk.events import EventActions
from google.adk.events.event import Event
from google.adk.workflow import START, Edge, Workflow, node
from google.genai import types
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)


# Edge.chain helper definition
def _edge_chain(nodes_list):
    edges_list = []
    for i in range(len(nodes_list) - 1):
        edges_list.append((nodes_list[i], nodes_list[i + 1]))
    return edges_list


Edge.chain = staticmethod(_edge_chain)


# Define State Schema
class GatekeeperState(BaseModel):
    user_query: str | None = None
    sanitized_input: str | None = None
    status: str | None = None
    reason: str | None = None


# Define Nodes
@node
def receive_input(ctx: Context, node_input: types.Content) -> Event:
    """Extracts the query text from the input content and stores it in the state."""
    query_text = ""
    if node_input and node_input.parts:
        query_text = "".join(part.text for part in node_input.parts if part.text)

    return Event(
        output=query_text, actions=EventActions(state_delta={"user_query": query_text})
    )


@node
def injection_detector(ctx: Context, node_input: str) -> Event:
    """Checks for prompt injection patterns inside the query."""
    patterns = [
        "ignore previous",
        "ignore above",
        "disregard",
        "you are now",
        "system prompt",
        "reveal your",
        "-- ",
        "/*",
        "xp_cmdshell",
        "UNION SELECT",
        "OR 1=1",
    ]
    query_lower = node_input.lower()
    detected = []
    for pattern in patterns:
        if pattern in query_lower:
            detected.append(pattern)

    if detected:
        reason = f"Prompt injection pattern(s) detected: {', '.join(detected)}"
        return Event(
            output=reason,
            actions=EventActions(
                route="block", state_delta={"reason": reason, "status": "blocked"}
            ),
        )
    return Event(output=node_input, actions=EventActions(route="pass"))


@node
def sql_keyword_scanner(ctx: Context, node_input: str) -> Event:
    """Blocks if the input contains SQL mutation keywords."""
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
    query_upper = node_input.upper()

    import re

    detected = []
    for kw in blocked_keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", query_upper):
            detected.append(kw)

    if detected:
        reason = f"SQL mutation keyword(s) detected: {', '.join(detected)}"
        return Event(
            output=reason,
            actions=EventActions(
                route="block", state_delta={"reason": reason, "status": "blocked"}
            ),
        )
    return Event(output=node_input, actions=EventActions(route="pass"))


@node
def pass_node(ctx: Context, node_input: str) -> Event:
    """Returns safe output status with sanitized query."""
    return Event(
        output={"status": "safe", "sanitized_input": node_input},
        actions=EventActions(
            state_delta={"status": "safe", "sanitized_input": node_input}
        ),
    )


@node
def block(ctx: Context, node_input: str) -> Event:
    """Returns blocked status with details."""
    reason = ctx.state.get("reason", node_input)
    return Event(
        output={"status": "blocked", "reason": reason},
        actions=EventActions(state_delta={"status": "blocked", "reason": reason}),
    )


# Define Graph Workflow using Edge.chain & manually wiring branches
root_agent = Workflow(
    name="gatekeeper",
    state_schema=GatekeeperState,
    edges=[
        *Edge.chain([START, receive_input, injection_detector]),
        (injection_detector, {"block": block, "pass": sql_keyword_scanner}),
        (sql_keyword_scanner, {"block": block, "pass": pass_node}),
    ],
)

app = App(root_agent=root_agent, name="app")
