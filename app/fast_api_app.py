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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Google Cloud auth for Agent Runtime inter-service calls
_auth_token_cache: dict = {}


async def _get_auth_headers() -> dict:
    """Get Google Cloud auth headers for Agent Runtime API calls."""
    try:
        import google.auth
        import google.auth.transport.requests

        credentials, _ = google.auth.default()
        credentials.refresh(google.auth.transport.requests.Request())
        return {"Authorization": f"Bearer {credentials.token}"}
    except Exception:
        return {}


def _needs_auth(url: str) -> bool:
    """Check if the URL is an Agent Runtime endpoint needing auth."""
    return "aiplatform.googleapis.com" in (url or "")
from google.adk.runners import Runner
from google.genai import types
from pydantic import BaseModel

from app.agent import app as adk_app
from app.agent import memory_service, session_service

# Configure logging
logging.basicConfig(level=logging.INFO)

# ADK 2.0 HITL function call name used by RequestInput
REQUEST_INPUT_FC_NAME = "adk_request_input"

# Initialize FastAPI App
app = FastAPI(title="QuerySage API Server")

# Add CORS Middleware to support Streamlit cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    user_query: str


class ChatResponse(BaseModel):
    status: str
    output: str | None = None
    interrupted: bool = False
    interrupt_id: str | None = None
    message: str | None = None
    session_id: str
    sql_results: list[dict[str, Any]] | None = None
    chart_type: str | None = None


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "querysage-master"}


def _find_pending_interrupt(session) -> str | None:
    """Find an unresolved adk_request_input function call in session events."""
    if not session or not session.events:
        return None

    fc_ids: set[str] = set()
    fr_ids: set[str] = set()
    for event in session.events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if (
                    part.function_call
                    and part.function_call.name == REQUEST_INPUT_FC_NAME
                ):
                    fc_ids.add(part.function_call.id)
                if part.function_response and part.function_response.id:
                    fr_ids.add(part.function_response.id)

    pending = fc_ids - fr_ids
    return next(iter(pending)) if pending else None


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Processes natural language questions, executing the QuerySage ADK workflow."""

    # 1. Ensure session exists
    try:
        session = await session_service.get_session(
            app_name="app", user_id=req.user_id, session_id=req.session_id
        )
    except Exception:
        session = None

    if session is None:
        session = await session_service.create_session(
            app_name="app", user_id=req.user_id, session_id=req.session_id
        )
        logging.info(f"Created new session: {req.session_id}")

    # 2. Check if this is a resume (session has a pending HITL interrupt)
    pending_interrupt_id = _find_pending_interrupt(session)

    state_delta = None
    if pending_interrupt_id:
        # Resume: send a FunctionResponse matching the pending FC
        logging.info(
            f"Resuming HITL interrupt_id={pending_interrupt_id}, "
            f"user response={req.user_query}"
        )
        new_message = types.Content(
            role="user",
            parts=[
                types.Part(
                    function_response=types.FunctionResponse(
                        id=pending_interrupt_id,
                        name=REQUEST_INPUT_FC_NAME,
                        response={"result": req.user_query},
                    )
                )
            ],
        )
    else:
        # New query: pre-call Gatekeeper and SQL Engine
        gatekeeper_url = os.environ.get("GATEKEEPER_SERVICE_URL")
        sql_engine_url = os.environ.get("SQL_ENGINE_SERVICE_URL")

        # Call Gatekeeper
        sanitized_query = req.user_query
        gatekeeper_blocked = False
        gatekeeper_reason = None
        if gatekeeper_url and "YOUR_GATEKEEPER_SERVICE_URL" not in gatekeeper_url:
            try:
                headers = await _get_auth_headers() if _needs_auth(gatekeeper_url) else {}
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        gatekeeper_url, json={"query": req.user_query},
                        headers=headers, timeout=10.0,
                    )
                    if resp.status_code == 200:
                        gk_data = resp.json()
                        if gk_data.get("status") == "blocked":
                            gatekeeper_blocked = True
                            gatekeeper_reason = gk_data.get(
                                "reason", "Query blocked by security policy."
                            )
                        else:
                            sanitized_query = gk_data.get(
                                "sanitized_query", req.user_query
                            )
            except Exception as e:
                logging.warning(
                    f"Gatekeeper call failed: {e}. Falling back to raw query."
                )

        # If gatekeeper blocked the query, return immediately
        if gatekeeper_blocked:
            return ChatResponse(
                status="blocked",
                output=f"Query blocked: {gatekeeper_reason}",
                session_id=req.session_id,
            )

        # Call SQL Engine
        sql_query = "SELECT * FROM orders LIMIT 5;"
        if sql_engine_url and "YOUR_SQL_ENGINE_SERVICE_URL" not in sql_engine_url:
            try:
                headers = await _get_auth_headers() if _needs_auth(sql_engine_url) else {}
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        sql_engine_url, json={"query": sanitized_query},
                        headers=headers, timeout=60.0,
                    )
                    if resp.status_code == 200:
                        sql_query = resp.json().get("sql_query", sql_query)
            except Exception as e:
                logging.warning(
                    f"SQL Engine call failed: {e}. Falling back to default query."
                )

        state_delta = {
            "user_query": req.user_query,
            "sanitized_query": sanitized_query,
            "sql_query": sql_query,
        }
        new_message = types.Content(
            role="user", parts=[types.Part.from_text(text=req.user_query)]
        )

    # 3. Drive the ADK workflow via the Runner
    runner = Runner(
        app=adk_app,
        session_service=session_service,
        memory_service=memory_service,
    )

    events = []
    try:
        async for event in runner.run_async(
            user_id=req.user_id,
            session_id=req.session_id,
            new_message=new_message,
            state_delta=state_delta,
        ):
            events.append(event)
    except Exception as e:
        logging.error(f"Error during ADK workflow execution: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

    # 4. Check for HITL interrupts (adk_request_input FCs) or final outputs
    final_output = ""
    interrupted = False
    interrupt_id = None
    interrupt_msg = None

    for event in events:
        # Detect adk_request_input function calls — the ADK 2.0 HITL mechanism
        if event.content and event.content.parts:
            for part in event.content.parts:
                if (
                    part.function_call
                    and part.function_call.name == REQUEST_INPUT_FC_NAME
                ):
                    interrupted = True
                    interrupt_id = part.function_call.id
                    args = part.function_call.args or {}
                    interrupt_msg = args.get(
                        "message", "Approval required. Do you approve? (yes/no)"
                    )

        if event.output is not None:
            final_output = str(event.output)

    if interrupted:
        return ChatResponse(
            status="interrupted",
            interrupted=True,
            interrupt_id=interrupt_id,
            message=interrupt_msg,
            session_id=req.session_id,
        )

    # 5. Extract structured results from session state for charts
    sql_results = None
    chart_type = None
    try:
        updated_session = await session_service.get_session(
            app_name="app", user_id=req.user_id, session_id=req.session_id
        )
        if updated_session and updated_session.state:
            executor_output = updated_session.state.get("executor_output", {})
            if isinstance(executor_output, dict):
                sql_results = executor_output.get("sql_results")
                chart_type = executor_output.get("chart_type", "table")
    except Exception as e:
        logging.warning(f"Could not extract structured results: {e}")

    return ChatResponse(
        status="success",
        output=final_output,
        session_id=req.session_id,
        sql_results=sql_results,
        chart_type=chart_type,
    )
