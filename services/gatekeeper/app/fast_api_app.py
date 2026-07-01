import datetime
import logging
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


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "gatekeeper"}


@app.get("/audit")
def get_audit_log():
    """Audit log endpoint."""
    return audit_log


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
