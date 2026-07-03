# QuerySage — Deploy to Agent Runtime (Day 5 Codelab)

This guide follows the **Kaggle 5-Day AI Agents** Day 5 deployment workflow using `agents-cli` and **Agent Runtime** on Google Cloud.

## Architecture Note

QuerySage has 3 services + 1 frontend:

| Component | Deployment Target | Why |
|-----------|------------------|-----|
| **Master Orchestrator** (ADK 2.0 workflow) | **Agent Runtime** | This is the ADK agent — deploys via `agents-cli deploy` |
| **Gatekeeper** (regex validator) | **Agent Runtime** | Also an ADK agent — has its own `agents-cli-manifest.yaml` |
| **SQL Engine** (Gemini NL→SQL) | **Agent Runtime** | Also an ADK agent — has its own `agents-cli-manifest.yaml` |
| **Streamlit UI** (frontend) | **Cloud Run** | Frontend — covered in Day 5 Codelab #2 |

All three services were scaffolded with `agents-cli` and have ADK `app/agent.py` + `app/fast_api_app.py`. Each gets deployed to Agent Runtime independently, then the master's env vars are updated to point to the deployed Gatekeeper and SQL Engine endpoints.

---

## Step 1: Set Up Google Cloud Environment

Open **Google Antigravity** and prompt:

```
Help me set up my Google Cloud environment. Connect to my project
querysage-capstone in the global region, authenticate, and enable the necessary
generative platform APIs (aiplatform.googleapis.com, cloudtrace.googleapis.com,
cloudbuild.googleapis.com, agentregistry.googleapis.com).
```

This will:
- Run `gcloud auth login` (follow the browser link to authenticate)
- Set your project: `gcloud config set project querysage-capstone`
- Enable all required APIs

> **Note**: If this is a new project, you may need to enable the Service Usage API first via the Cloud Console link shown in terminal.

---

## Step 2: Install Agents CLI & ADK Skills

Prompt **Antigravity**:

```
Install the agents-cli toolchain and its ADK skills so you can help me build
an ADK agent. Run "uvx google-agents-cli setup", then confirm with
"agents-cli info" and tell me which skills are now available.
```

This installs:
- `agents-cli` command-line tool
- ADK companion skills (`google-agents-cli-deploy`, `google-agents-cli-workflow`, etc.)

---

## Step 3: Skip Scaffolding (Project Already Exists)

QuerySage is already built. All three services have `agents-cli-manifest.yaml` files. Skip the "Create your agent project" step from the codelab.

---

## Step 4: Deploy Gatekeeper to Agent Runtime

The Gatekeeper must be deployed first since the Master depends on its URL.

```bash
cd services/gatekeeper
```

### 4a. Scaffold production files

Prompt **Antigravity** (while in `services/gatekeeper` directory):

```
Scaffold the production deployment files for Agent Runtime.
```

This runs: `agents-cli scaffold enhance --deployment-target agent_runtime --yes`

It generates:
- `app/agent_runtime_app.py` — production wrapper
- `deployment_metadata.json` — layout schema for Agent Runtime

### 4b. Lock dependencies & dry-run

Prompt **Antigravity**:

```
Lock my python dependencies and run a dry-run deployment to check for any
configuration or dependency issues.
```

This runs:
- `uv lock` — creates deterministic lockfile
- `agents-cli deploy --dry-run` — validates config without deploying

### 4c. Deploy

Prompt **Antigravity**:

```
Deploy this agent to Agent Runtime.
```

This runs: `agents-cli deploy --project querysage-capstone --region asia-southeast1`

> **Wait 5–10 minutes**. Once done, note the **live endpoint URL** displayed.
>
> Example: `https://gatekeeper-XXXXX.asia-southeast1.run.app`

---

## Step 5: Deploy SQL Engine to Agent Runtime

```bash
cd services/sql-engine
```

### 5a. Scaffold production files

Prompt **Antigravity** (while in `services/sql-engine` directory):

```
Scaffold the production deployment files for Agent Runtime.
```

### 5b. Lock & dry-run

```
Lock my python dependencies and run a dry-run deployment to check for any
configuration or dependency issues.
```

### 5c. Set environment variable

The SQL Engine needs the Gemini API key. Update `services/sql-engine/.env`:

```
GOOGLE_API_KEY=your_google_api_key_here
```

### 5d. Deploy

```
Deploy this agent to Agent Runtime.
```

> Note the **live endpoint URL** for the SQL Engine.

---

## Step 6: Deploy Master Orchestrator to Agent Runtime

```bash
cd querysage-master  # project root
```

### 6a. Update service URLs

Before scaffolding, update the `.env` file with the Cloud URLs from Steps 4 & 5:

```env
# Google AI Studio Configuration
GOOGLE_API_KEY=your_google_api_key

# Neon Database Configuration
NEON_DATABASE_URL=postgresql://neondb_owner:npg_XXXX@ep-XXXX-pooler.XXXX.aws.neon.tech/analytics_db1?sslmode=require&connect_timeout=30

# Update these with your deployed Agent Runtime URLs
GATEKEEPER_SERVICE_URL=https://gatekeeper-XXXXX.asia-southeast1.run.app/validate
SQL_ENGINE_SERVICE_URL=https://sql-engine-XXXXX.asia-southeast1.run.app/generate
```

### 6b. Scaffold production files

Prompt **Antigravity**:

```
Scaffold the production deployment files for Agent Runtime.
```

### 6c. Lock & dry-run

```
Lock my python dependencies and run a dry-run deployment to check for any
configuration or dependency issues.
```

### 6d. Deploy

```
Deploy this agent to Agent Runtime.
```

> Note the **Master endpoint URL** — this is the main entry point for QuerySage.

---

## Step 7: Test Your Deployed Agent

Prompt **Antigravity**:

```
Test my deployed Agent Runtime engine with two test cases: first a simple
query "show top 5 products by revenue" to verify the full pipeline works,
and second a query that should trigger the human-in-the-loop SQL approval
pause.
```

### Manual testing via Cloud Console Playground:

1. Go to **Google Cloud Console** → **Agent Platform** → **Deployments**
2. Select your QuerySage master agent
3. Click **Playground**
4. Type: `show top 5 products by revenue`
5. Verify it triggers HITL approval (RequestInput pause)
6. Approve with `yes`
7. Verify SQL results are returned

### Testing via curl:

```bash
# Replace with your actual master endpoint URL
curl -X POST https://master-XXXXX.asia-southeast1.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-deploy-1",
    "user_id": "demo",
    "user_query": "show top 5 products by revenue"
  }'
```

Expected response: `"status": "interrupted"` with SQL approval message.

---

## Step 8: Monitor with Cloud Trace

- **Traces**: Open [Cloud Trace Console](https://console.cloud.google.com/traces) to see execution spans for each node in the workflow
- **Logs**: Use [Cloud Logging](https://console.cloud.google.com/logs) for real-time stdout and error traces
- **Latency**: Inspect model call latencies, Neon DB connection times, and inter-service call durations

---

## Step 9: Deploy Streamlit Frontend (Day 5 Codelab #2)

The Streamlit UI connects to the Master's Agent Runtime endpoint. This is covered in the second Day 5 codelab ("Vibecode and Deploy a Frontend for an ADK Agent").

The `streamlit_app.py` already supports configurable URLs via environment variables:

```python
MASTER_URL = os.environ.get("MASTER_URL", "http://localhost:8000")
```

When deploying to Cloud Run, set `MASTER_URL` to your Master's Agent Runtime endpoint.

---

## Step 10: Clean Up (After Capstone Grading)

> **Do NOT clean up if you plan to continue to the Frontend codelab.**

Prompt **Antigravity**:

```
Clean up all my deployed cloud resources. Use the Agent Runtime ID from
deployment_metadata.json to delete the engine from Vertex AI, remove the local
deployment_metadata.json file, and delete the container image repository from
Artifact Registry.
```

Run this for each service directory (master, gatekeeper, sql-engine).

---

## Summary: Deployment Order

```
1. gcloud auth + enable APIs
2. Install agents-cli
3. Deploy Gatekeeper → get URL
4. Deploy SQL Engine → get URL
5. Update Master .env with URLs
6. Deploy Master → get URL
7. Test via Playground or curl
8. Deploy Streamlit (Cloud Run) → point to Master URL
```

**Total time**: ~30 minutes (mostly waiting for 3 × 5–10 min deploys)

**Cost**: Free tier covers demo usage (Agent Runtime, Neon DB, Gemini API all have free tiers)
