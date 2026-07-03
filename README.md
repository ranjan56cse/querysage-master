# QuerySage: AI-Powered Postgres Analytics & BI Canvas

QuerySage is a next-generation conversational business intelligence system that translates natural language questions into secure PostgreSQL queries, executes them against a Neon Database, and provides rich insights and interactive charts.

---

## 🏗️ Architecture Diagram

```
+----------+       +-----------+       +---------------------+       +----------------------+
|          | ----> |           | ----> |                     | ----> |  Gatekeeper Service  |
|  User /  |       | Streamlit |       | Master Orchestrator |       |    (Port 9000)       |
| Browser  | <---- |    UI     | <---- |     (Port 8000)     |       +----------------------+
|          |       |           |       |                     |                 |
+----------+       +-----------+       +---------------------+       +----------------------+
     ^                                            |                  |  SQL Engine Service  |
     |                                            v                  |    (Port 9001)       |
     |                                     +--------------+          +----------------------+
     +------------------------------------ |   Neon DB    | <------------------+
                                           +--------------+
```

---

## 🎓 Demonstrated Course Concepts

QuerySage implements seven key advanced agentic engineering concepts taught in the course:

1. **Multi-Agent ADK 2.0 Graph Workflow**: Structured graph architecture utilizing the ADK `Workflow`, `START`, `Edge`, and `@node` decorators to control flow, route results, and support state transitions.
2. **Agent-to-Agent Communication via REST**: Instead of monolithic orchestration, the Master Orchestrator calls dedicated, isolated micro-agents (Gatekeeper and SQL Engine) via standard REST API endpoints.
3. **Human-in-the-Loop (RequestInput)**: Employs ADK's `RequestInput` and `rerun_on_resume=True` interrupt patterns to pause execution and prompt the user to explicitly approve or reject SQL commands before they hit the database.
4. **Long-Term Memory (InMemoryMemoryService)**: Registers successfully executed sessions in long-term memory via the `memory_service` so the history of past interactions is persisted and accessible.
5. **Events Compaction**: Configures `EventsCompactionConfig` using `LlmEventSummarizer` to compress long history and retain critical context once a session crosses limits, preventing LLM context-window bloating.
6. **Tool Use (Neon MCP / Database Execution)**: Integrates Postgres tool calling (`neon_execute_sql`) and dynamic chart-rendering (`generate_chart`) as structured tools that the agents dynamically call.
7. **Security (Gatekeeper & Security Checkpoint)**: Implements multi-layered security checks including query classification via the Gatekeeper agent and AST parsing inside the `security_checkpoint` node to block SQL mutation words (`DROP`, `DELETE`, `UPDATE`, etc.).

---

## ⚙️ Setup Instructions

### 1. Environment Variables
Create a `.env` file at the project root with the following variables:

```env
# Gemini API Key
GOOGLE_API_KEY=your-gemini-api-key

# Neon Database Configuration
NEON_DATABASE_URL=postgresql://<user>:<password>@<host>/<dbname>?sslmode=require
NEON_API_KEY=your-neon-api-key

# Microservice Endpoints
GATEKEEPER_SERVICE_URL=http://localhost:9000/validate
SQL_ENGINE_SERVICE_URL=http://localhost:9001/generate
```

### 2. Installation
Ensure you have `uv` installed. Run the setup from the root folder:

```bash
# Sync dependencies for all services
uv sync
```

### 3. Run the Services
To fully run the system, open four terminal windows and run the following commands:

* **Service 1: Gatekeeper Service (Port 9000)**
  ```bash
  cd services/gatekeeper
  uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 9000 --reload
  ```

* **Service 2: SQL Engine Service (Port 9001)**
  ```bash
  cd services/sql-engine
  uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 9001 --reload
  ```

* **Service 3: Master Orchestrator (Port 8000)**
  ```bash
  # From project root
  uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 --reload
  ```

* **Service 4: Streamlit Frontend**
  ```bash
  # From project root
  uv run streamlit run streamlit_app.py
  ```

---

## 📊 Example Queries

Once the system is running, type these queries into the Streamlit UI to test execution, visualization, and security boundaries:

### 1. Simple Analysis
> *"Show me a list of categories and their total values."*
* Generates a SELECT query, requests user approval (HITL), runs it, and generates a **Bar Chart**.

### 2. Dynamic Trend
> *"What is the monthly sales trend for the past year?"*
* Generates a SELECT query, gets user approval, and renders a **Line Chart** of the results.

### 3. Security Blocked Query
> *"Drop the users table from the database"*
* Blocked automatically by the `security_checkpoint` parser. Shows a security warning immediately without executing or prompting for approval.
