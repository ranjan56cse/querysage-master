# ruff: noqa: E402
import logging
import os

from dotenv import load_dotenv

# Load .env from both service root and app/ directory
load_dotenv(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
)
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.adk.runners import Runner
from google.genai import types
from pydantic import BaseModel

from app.agent import app as adk_app
from app.app_utils import services

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI App
app = FastAPI(title="SQL Engine Service API")

# Add CORS Middleware to support Streamlit cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    query: str
    schema_hint: str | None = None
    session_id: str | None = None
    user_id: str | None = None


class GenerateResponse(BaseModel):
    sql_query: str
    enriched_context: str
    tables_used: list[str]


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "sql_engine"}


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """Processes natural language questions, executing the SQL Engine ADK workflow."""
    session_id = req.session_id or "default-sql-session"
    user_id = req.user_id or "default-user"

    # 1. Ensure session exists
    session_svc = services.get_session_service()
    try:
        session = await session_svc.get_session(
            app_name="app", user_id=user_id, session_id=session_id
        )
    except Exception:
        session = None

    if session is None:
        import uuid

        session_id = f"sql-{uuid.uuid4().hex[:8]}"
        await session_svc.create_session(
            app_name="app", user_id=user_id, session_id=session_id
        )
        logging.info(f"Created new SQL Engine session: {session_id}")

    # 2. Drive the ADK workflow via the Runner
    runner = Runner(
        app=adk_app,
        session_service=session_svc,
        artifact_service=services.get_artifact_service(),
    )

    new_message = types.Content(
        role="user", parts=[types.Part.from_text(text=req.query)]
    )

    # Supply custom inputs in initial state_delta
    state_delta = {
        "user_query": req.query,
        "schema_hint": req.schema_hint or "",
        "retry_count": 0,
    }

    events = []
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message,
            state_delta=state_delta,
        ):
            events.append(event)
    except Exception as e:
        logging.error(f"Error during SQL Engine execution: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

    # 2. Extract output dict
    final_output = None
    for event in events:
        if event.output is not None:
            final_output = event.output

    # Fallback to state check if direct output is not formatted as dictionary
    if not final_output or not isinstance(final_output, dict):
        try:
            session = await services.get_session_service().get_session(
                app_name="app", user_id=user_id, session_id=session_id
            )
            if session and session.state:
                final_output = session.state
        except Exception as e:
            logging.warning(f"Could not retrieve state details: {e}")

    if not final_output or not isinstance(final_output, dict):
        raise HTTPException(
            status_code=500,
            detail="SQL generation workflow failed to yield valid output state.",
        )

    return GenerateResponse(
        sql_query=final_output.get("generated_sql", ""),
        enriched_context=final_output.get("enriched_context", ""),
        tables_used=final_output.get("tables_used", []),
    )


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9001)
