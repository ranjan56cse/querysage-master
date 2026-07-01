# QuerySage Project Context & Secure Coding Standards

## Core Rules
1. All SQL execution must be read-only (SELECT only). Never allow mutations.
2. All user input must pass through the Gatekeeper before reaching any LLM.
3. Use Pydantic models for all tool input validation.
4. Never log or expose database credentials, connection strings, or API keys.
5. Use state dict for passing data between workflow nodes — no global variables.
6. All agents use gemini-2.5-flash model.
7. Human-in-the-Loop required before any SQL execution.

## ADK 2.0 Conventions
- Use graph Workflow API (Workflow, Edge, @node, App)
- Use RequestInput for HITL pauses
- Use InMemorySessionService for session management
- Use InMemoryMemoryService for long-term memory
