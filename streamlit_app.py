import uuid

import httpx
import pandas as pd
import plotly.express as px
import streamlit as st

# Set page config for a widescreen BI experience
st.set_page_config(
    page_title="QuerySage Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom premium styling for BI dashboard
st.markdown(
    """
<style>
    /* Global Background and Typography */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* Header Gradient Banner */
    .header-banner {
        background: linear-gradient(90deg, #1e1b4b 0%, #311042 50%, #0b0f19 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        border: 1px solid #312e81;
    }

    .main-title {
        font-size: 2.5rem !important;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1 0%, #d946ef 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .subtitle {
        font-size: 1rem;
        color: #94a3b8;
        margin-top: 0.5rem;
    }

    /* Sidebar controls styling */
    .sidebar-title {
        font-weight: 800;
        font-size: 1.4rem;
        color: #818cf8;
        margin-bottom: 1rem;
    }

    /* Panel Cards */
    .bi-card {
        background-color: #111827;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #1f2937;
        margin-bottom: 1.5rem;
    }

    .bi-card-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #c084fc;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Table headers customization */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Custom button styling */
    div.stButton > button:first-child {
        background-color: #4f46e5;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: all 0.3s;
    }

    div.stButton > button:first-child:hover {
        background-color: #4338ca;
        box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "user_id" not in st.session_state:
    st.session_state.user_id = "streamlit_user"
if "awaiting_approval" not in st.session_state:
    st.session_state.awaiting_approval = False
if "interrupted_sql" not in st.session_state:
    st.session_state.interrupted_sql = ""
if "current_results" not in st.session_state:
    st.session_state.current_results = None
if "current_chart_type" not in st.session_state:
    st.session_state.current_chart_type = "table"
if "current_sql" not in st.session_state:
    st.session_state.current_sql = ""
if "current_insights" not in st.session_state:
    st.session_state.current_insights = ""

# Sidebar controls & Metadata
with st.sidebar:
    st.markdown(
        '<div class="sidebar-title">🔮 QuerySage Control</div>', unsafe_allow_html=True
    )
    st.markdown(
        "Automated PostgreSQL analytics generation with active safety guardrails and human review."
    )

    st.divider()

    st.markdown("### 🔑 Active Session")
    st.text_input("User ID", value=st.session_state.user_id, key="user_id")
    st.text_input(
        "Session ID",
        value=st.session_state.session_id,
        key="session_id_input",
        disabled=True,
    )

    if st.button("🔄 New Session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.awaiting_approval = False
        st.session_state.interrupted_sql = ""
        st.session_state.current_results = None
        st.session_state.current_chart_type = "table"
        st.session_state.current_sql = ""
        st.session_state.current_insights = ""
        st.rerun()

    st.divider()

    st.markdown("### 🔌 Connected Services")
    services_list = {
        "Orchestrator (Port 8000)": "http://localhost:8000/health",
        "Gatekeeper (Port 9000)": "http://localhost:9000/health",
        "SQL Engine (Port 9001)": "http://localhost:9001/health",
    }

    for name, url in services_list.items():
        try:
            resp = httpx.get(url, timeout=2.0)
            if resp.status_code == 200:
                st.success(f"🟢 {name} online")
            else:
                st.warning(f"🟡 {name} status: {resp.status_code}")
        except Exception:
            st.error(f"🔴 {name} offline")

# Header Banner
st.markdown(
    """
<div class="header-banner">
    <div class="main-title">🔮 QuerySage Analytics Dashboard</div>
    <div class="subtitle">Enter natural language queries to retrieve raw transactional views and dynamic graphical reports.</div>
</div>
""",
    unsafe_allow_html=True,
)

# Main Dashboard Layout
# Column 1: NL Query Canvas (Input) & Chat History
# Column 2: BI Data View & Chart Visualization Panels
col_input, col_display = st.columns([1, 2])


# API Submission function
def submit_query(query_text: str):
    # Log user query in chat list
    st.session_state.messages.append({"role": "user", "content": query_text})

    with st.spinner("Analyzing question, generating SQL and building report..."):
        try:
            payload = {
                "session_id": st.session_state.session_id,
                "user_id": st.session_state.user_id,
                "user_query": query_text,
            }
            resp = httpx.post("http://localhost:8000/chat", json=payload, timeout=90.0)

            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status")

                if status == "success":
                    output = data.get("output", "")
                    sql_results = data.get("sql_results")
                    chart_type = data.get("chart_type", "table")

                    st.session_state.current_results = sql_results
                    st.session_state.current_chart_type = chart_type
                    st.session_state.current_insights = output

                    # Extract generated SQL from output markdown if present
                    st.session_state.current_sql = ""
                    if "```sql" in output:
                        try:
                            parts = output.split("```sql")
                            st.session_state.current_sql = (
                                parts[1].split("```")[0].strip()
                            )
                        except Exception:
                            pass

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": output,
                            "status": "success",
                            "sql_results": sql_results,
                            "chart_type": chart_type,
                        }
                    )
                    st.session_state.awaiting_approval = False
                    st.session_state.interrupted_sql = ""

                elif status == "interrupted":
                    st.session_state.awaiting_approval = True
                    st.session_state.interrupted_sql = data.get(
                        "message", "RequestInput Approval Required"
                    )

                    # Store interrupted event in history
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": f"Review execution statement for Neon SQL execution:\n\n```sql\n{st.session_state.interrupted_sql}\n```",
                            "status": "interrupted",
                        }
                    )

                elif status == "blocked":
                    output = data.get("output", "Blocked by safety checks.")
                    st.session_state.messages.append(
                        {"role": "assistant", "content": output, "status": "blocked"}
                    )
                    st.session_state.awaiting_approval = False
                    st.session_state.interrupted_sql = ""
                    st.session_state.current_insights = output
                    st.session_state.current_results = None
            else:
                st.error(
                    f"Error calling orchestrator: {resp.status_code} - {resp.text}"
                )
        except Exception as e:
            st.error(f"Failed to connect to Orchestrator service: {e}")


# Left Canvas: Query Panel
with col_input:
    st.markdown(
        '<div class="bi-card-title">✍️ Query Canvas</div>', unsafe_allow_html=True
    )

    # Handle Awaiting Human Approval flow
    if st.session_state.awaiting_approval:
        st.warning("🚨 Execution paused. Do you approve executing the SQL statement?")
        st.code(st.session_state.interrupted_sql, language="sql")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Yes, Execute", use_container_width=True, type="primary"):
                st.session_state.awaiting_approval = False
                submit_query("yes")
                st.rerun()
        with c2:
            if st.button("❌ No, Decline", use_container_width=True):
                st.session_state.awaiting_approval = False
                submit_query("no")
                st.rerun()
    else:
        # Standard NL search bar
        user_query = st.text_area(
            "Natural Language Question",
            placeholder="e.g., Show me monthly profit margins for fiscal year 2026...",
            height=100,
        )
        if st.button("🚀 Analyze Query", use_container_width=True):
            if user_query.strip():
                submit_query(user_query)
                st.rerun()

    st.divider()

    # Simple Chat/Interaction log view
    st.markdown(
        '<div class="bi-card-title">💬 Conversation Logs</div>', unsafe_allow_html=True
    )
    for msg in st.session_state.messages:
        role_label = "🧑 User" if msg["role"] == "user" else "🤖 Assistant"
        if msg.get("status") == "blocked":
            st.markdown(f"**🔴 {role_label}**: Blocked by safety policy.")
        elif msg.get("status") == "interrupted":
            st.markdown(f"**🟡 {role_label}**: Interrupted (HITL Approval Required).")
        else:
            # truncate display text in logs for compact canvas
            text = msg["content"]
            if len(text) > 100:
                text = text[:100] + "..."
            st.markdown(f"**{role_label}**: {text}")

# Right Canvas: Data View & Interactive Visualizations
with col_display:
    if st.session_state.current_results is not None:
        # Convert results to DataFrame
        try:
            df = pd.DataFrame(st.session_state.current_results)
        except Exception:
            df = None

        # Tabs for tabular details vs visual charts
        tab_table, tab_chart, tab_insights = st.tabs(
            ["📊 Tabular Dataset", "📈 Graphical Report", "💡 AI Storytelling & SQL"]
        )

        with tab_table:
            st.markdown(
                '<div class="bi-card-title">📁 Query Results View</div>',
                unsafe_allow_html=True,
            )
            if df is not None and not df.empty:
                st.markdown(
                    f"Total Rows Returned: `{len(df)}` | Columns: `{', '.join(df.columns)}`"
                )
                st.dataframe(df, use_container_width=True, height=450)
            else:
                st.info(
                    "Query executed successfully, but no rows were returned from the database."
                )

        with tab_chart:
            st.markdown(
                '<div class="bi-card-title">🎨 Interactive Visualization</div>',
                unsafe_allow_html=True,
            )
            if df is not None and not df.empty:
                chart_type = st.session_state.current_chart_type

                # Dynamic Plotly Visualization based on Columns and Types
                numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
                categorical_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

                st.caption(f"Suggested visualization type: `{chart_type}`")

                if (
                    chart_type == "bar"
                    and len(categorical_cols) >= 1
                    and len(numeric_cols) >= 1
                ):
                    fig = px.bar(
                        df,
                        x=categorical_cols[0],
                        y=numeric_cols[0],
                        color=categorical_cols[0],
                        title="Results Bar Chart",
                        template="plotly_dark",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                elif (
                    chart_type == "line"
                    and len(categorical_cols) >= 1
                    and len(numeric_cols) >= 1
                ):
                    fig = px.line(
                        df,
                        x=categorical_cols[0],
                        y=numeric_cols[0],
                        markers=True,
                        title="Results Line Chart",
                        template="plotly_dark",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                elif (
                    chart_type == "pie"
                    and len(categorical_cols) >= 1
                    and len(numeric_cols) >= 1
                ):
                    fig = px.pie(
                        df,
                        names=categorical_cols[0],
                        values=numeric_cols[0],
                        title="Results Pie Distribution",
                        template="plotly_dark",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                else:
                    # Fallback to scatter, line or auto bar depending on columns
                    if len(numeric_cols) >= 2:
                        fig = px.scatter(
                            df,
                            x=numeric_cols[0],
                            y=numeric_cols[1],
                            title="Scatter Correlation View",
                            template="plotly_dark",
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    elif len(df.columns) >= 2:
                        # Fallback simple bar
                        fig = px.bar(
                            df, x=df.columns[0], y=df.columns[1], template="plotly_dark"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info(
                            "Not enough numeric dimensions to render a graphical representation."
                        )
            else:
                st.info("No data dimensions available to plot visual graphics.")

        with tab_insights:
            st.markdown(
                '<div class="bi-card-title">🔮 Executive Insights</div>',
                unsafe_allow_html=True,
            )
            if st.session_state.current_sql:
                st.markdown("#### Generated PostgreSQL statement:")
                st.code(st.session_state.current_sql, language="sql")

            st.markdown("#### Senior Analyst Findings:")
            st.markdown(st.session_state.current_insights)
    else:
        # Default Welcome State / No active result
        st.markdown(
            '<div class="bi-card" style="text-align: center; padding: 4rem 2rem;">',
            unsafe_allow_html=True,
        )
        st.markdown("### 📊 No Query Executed Yet")
        st.markdown(
            "Submit a natural language question in the left panel to query the Neon database, execute safety checks, and view results."
        )
        st.markdown("</div>", unsafe_allow_html=True)
