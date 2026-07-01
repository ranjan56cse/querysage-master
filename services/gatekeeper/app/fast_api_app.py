import datetime
import html
import logging
import re
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.adk.runners import Runner
from google.genai import types
from pydantic import BaseModel

from app.agent import app as adk_app
from app.app_utils import services

# Configure logging
logging.basicConfig(level=logging.INFO)

# In-memory audit log list
audit_log: list[dict[str, Any]] = []

# Initialize FastAPI App
app = FastAPI(title="Gatekeeper Service API")

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
    sanitized_input: str | None = None
    reason: str | None = None
    session_id: str


class ValidateRequest(BaseModel):
    query: str


class ValidateResponse(BaseModel):
    status: str
    sanitized_query: str | None = None
    reason: str | None = None


# Regular expression and string rules matching the ADK workflow logic
PATTERNS = [
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

BLOCKED_KEYWORDS = {
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "ALTER",
    "TRUNCATE",
    "GRANT",
    "REVOKE",
}


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "gatekeeper"}


@app.get("/audit")
def get_audit_log():
    """Audit log endpoint."""
    return audit_log


@app.post("/validate", response_model=ValidateResponse)
def validate_query(req: ValidateRequest):
    """Directly scans input query for security patterns and SQL mutations without ADK runner."""
    query = req.query
    query_lower = query.lower()

    # 1. Injection detection
    detected_patterns = []
    for pattern in PATTERNS:
        if pattern.lower() in query_lower:
            detected_patterns.append(pattern)

    if detected_patterns:
        reason = f"Prompt injection pattern(s) detected: {', '.join(detected_patterns)}"
        result = {"status": "blocked", "reason": reason}
        audit_log.append(
            {
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                "query": query,
                "result": result,
            }
        )
        return ValidateResponse(status="blocked", reason=reason)

    # 2. SQL keyword scanning
    query_upper = query.upper()
    detected_keywords = []
    for kw in BLOCKED_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", query_upper):
            detected_keywords.append(kw)

    if detected_keywords:
        reason = f"SQL mutation keyword(s) detected: {', '.join(detected_keywords)}"
        result = {"status": "blocked", "reason": reason}
        audit_log.append(
            {
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                "query": query,
                "result": result,
            }
        )
        return ValidateResponse(status="blocked", reason=reason)

    # 3. Escaping HTML/XSS elements
    sanitized = html.escape(query)
    result = {"status": "safe", "sanitized_query": sanitized}
    audit_log.append(
        {
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "query": query,
            "result": result,
        }
    )
    return ValidateResponse(status="safe", sanitized_query=sanitized)


@app.post("/chat")
async def chat(req: ChatRequest):
    """Processes natural language questions, executing the Gatekeeper ADK workflow."""

    # 1. Drive the ADK workflow via the Runner
    runner = Runner(
        app=adk_app,
        session_service=services.get_session_service(),
        artifact_service=services.get_artifact_service(),
    )

    new_message = types.Content(
        role="user", parts=[types.Part.from_text(text=req.user_query)]
    )

    events = []
    try:
        async for event in runner.run_async(
            user_id=req.user_id,
            session_id=req.session_id,
            new_message=new_message,
        ):
            events.append(event)
    except Exception as e:
        logging.error(f"Error during Gatekeeper execution: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

    # 2. Extract output dict
    final_output = None
    for event in events:
        if event.output is not None:
            final_output = event.output

    # Fallback to defaults if output is empty/unset
    if not final_output or not isinstance(final_output, dict):
        final_output = {"status": "blocked", "reason": "No execution results returned"}

    # 3. Add interaction to the in-memory audit log
    audit_log.append(
        {
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "query": req.user_query,
            "result": final_output,
        }
    )

    return ChatResponse(
        status=final_output.get("status", "blocked"),
        sanitized_input=final_output.get("sanitized_input"),
        reason=final_output.get("reason"),
        session_id=req.session_id,
    )


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
