# ruff: noqa: E402
import logging
import os

from dotenv import load_dotenv

load_dotenv(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
)
load_dotenv()

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.adk.runners import Runner
from google.genai import types
from pydantic import BaseModel

from app.agent import app as adk_app
from app.agent import memory_service, session_service

# Configure logging
logging.basicConfig(level=logging.INFO)

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


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "querysage-master"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Processes natural language questions, executing the QuerySage ADK workflow."""

    # 1. Ensure session exists, then check if suspended for resume
    invocation_id = None
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

    if session and session.events:
        last_event = session.events[-1]
        if last_event.interrupted:
            invocation_id = last_event.invocation_id
            logging.info(
                f"Resuming suspended workflow for session {req.session_id} with invocation {invocation_id}"
            )

    # 2. If it's a new turn, pre-run Gatekeeper and SQL Engine
    state_delta = None
    if not invocation_id:
        gatekeeper_url = os.environ.get("GATEKEEPER_SERVICE_URL")
        sql_engine_url = os.environ.get("SQL_ENGINE_SERVICE_URL")

        # Call Gatekeeper
        sanitized_query = req.user_query
        gatekeeper_blocked = False
        gatekeeper_reason = None
        if gatekeeper_url and "YOUR_GATEKEEPER_SERVICE_URL" not in gatekeeper_url:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        gatekeeper_url, json={"query": req.user_query}, timeout=10.0
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
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        sql_engine_url, json={"query": sanitized_query}, timeout=60.0
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

    # 3. Drive the ADK workflow via the Runner
    runner = Runner(
        app=adk_app,
        session_service=session_service,
        memory_service=memory_service,
    )

    new_message = types.Content(
        role="user", parts=[types.Part.from_text(text=req.user_query)]
    )

    events = []
    try:
        async for event in runner.run_async(
            user_id=req.user_id,
            session_id=req.session_id,
            invocation_id=invocation_id,
            new_message=new_message,
            state_delta=state_delta,
        ):
            events.append(event)
    except Exception as e:
        logging.error(f"Error during ADK workflow execution: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

    # 4. Check for interrupts or final outputs
    final_output = ""
    interrupted = False
    interrupt_id = None
    interrupt_msg = None

    for event in events:
        if event.interrupted:
            interrupted = True
            # Find RequestInput details
            if event.content and event.content.parts:
                interrupt_msg = "".join(p.text for p in event.content.parts if p.text)
            # Find RequestInput details from custom_metadata or actions
            if event.actions and event.actions.render_ui_widgets:
                for widget in event.actions.render_ui_widgets:
                    if hasattr(widget, "interrupt_id"):
                        interrupt_id = widget.interrupt_id
            # Fallback values
            if not interrupt_id:
                interrupt_id = "approved"
            if not interrupt_msg:
                interrupt_msg = (
                    "Neon SQL Execution request. Do you approve execution? (yes/no)"
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

    return ChatResponse(
        status="success", output=final_output, session_id=req.session_id
    )
