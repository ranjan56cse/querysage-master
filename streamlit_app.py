import uuid

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Set page config
st.set_page_config(
    page_title="QuerySage | E-Commerce NL-to-SQL Analytics",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium Gradient Header and Styling
st.markdown(
    """
<style>
    /* Styling */
    .stApp {
        background-color: #0f111a;
        color: #e6e8f0;
    }
    .main-title {
        font-size: 3rem !important;
        font-weight: 800;
        background: linear-gradient(135deg, #4f46e5 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #9ca3af;
        margin-bottom: 2rem;
    }
    .sidebar-title {
        font-weight: 700;
        font-size: 1.5rem;
        color: #a855f7;
        margin-bottom: 1rem;
    }
    /* Chat bubbles styling */
    .user-msg {
        background-color: #1e1b4b;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border-left: 4px solid #4f46e5;
    }
    .warning-msg {
        background-color: #450a0a;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid #f87171;
    }
    .approval-card {
        background-color: #1e293b;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px dashed #f59e0b;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize Session State Variables
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

# Sidebar Layout
with st.sidebar:
    st.markdown(
        '<div class="sidebar-title">🔮 QuerySage Control</div>', unsafe_allow_html=True
    )
    st.markdown(
        "QuerySage uses Google ADK 2.0 graph workflow orchestration to secure, "
        "translate, and analyze e-commerce analytics queries."
    )

    st.divider()

    st.markdown("### 🔑 Session Metadata")
    st.text_input("User ID", value=st.session_state.user_id, key="user_id")
    st.text_input(
        "Session ID",
        value=st.session_state.session_id,
        key="session_id_input",
        disabled=True,
    )

    # New Session Button
    if st.button("🔄 New Session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.awaiting_approval = False
        st.session_state.interrupted_sql = ""
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

# Main Title Area
st.markdown(
    '<div class="main-title">🔮 QuerySage E-Commerce Analytics</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">Secure natural-language to PostgreSQL translator with '
    "human-in-the-loop validation and visual insights.</div>",
    unsafe_allow_html=True,
)


def render_chart(sql_results: list[dict], chart_type: str):
    """Render a Plotly chart from structured SQL results."""
    if not sql_results:
        return
    df = pd.DataFrame(sql_results)
    if df.empty:
        return

    cols = list(df.columns)
    x_col = cols[0]
    y_col = cols[1] if len(cols) > 1 else None

    ct = chart_type.lower().strip() if chart_type else "table"

    if ct == "bar" and y_col:
        fig = px.bar(
            df,
            x=x_col,
            y=y_col,
            title=f"{x_col.replace('_', ' ').title()} vs {y_col.replace('_', ' ').title()}",
            template="plotly_dark",
        )
        st.plotly_chart(fig, use_container_width=True)
    elif ct == "line" and y_col:
        fig = px.line(
            df,
            x=x_col,
            y=y_col,
            title=f"{x_col.replace('_', ' ').title()} Trend",
            template="plotly_dark",
        )
        st.plotly_chart(fig, use_container_width=True)
    elif ct == "pie" and y_col:
        fig = px.pie(
            df,
            names=x_col,
            values=y_col,
            title=f"{x_col.replace('_', ' ').title()} Distribution",
            template="plotly_dark",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Table display
        fig = go.Figure(
            data=[
                go.Table(
                    header={
                        "values": cols,
                        "fill_color": "#312e81",
                        "font": {"color": "white"},
                        "align": "left",
                    },
                    cells={
                        "values": [df[c].tolist() for c in cols],
                        "fill_color": "#1e1b4b",
                        "font": {"color": "#e6e8f0"},
                        "align": "left",
                    },
                )
            ]
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)


# Render Chat History
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(
            f'<div class="user-msg"><b>🧑 User:</b><br>{message["content"]}</div>',
            unsafe_allow_html=True,
        )
    elif message["role"] == "assistant":
        if message.get("status") == "blocked":
            st.markdown(
                f'<div class="warning-msg"><b>⚠️ Security Block:</b><br>'
                f'{message["content"]}</div>',
                unsafe_allow_html=True,
            )
        elif message.get("status") == "interrupted":
            st.warning(f"⏸️ **HITL Approval Requested**\n\n{message['content']}")
        else:
            # Render markdown output (tables, insights, etc.)
            st.markdown(message["content"])

            # Render chart if structured data is present
            if message.get("sql_results"):
                render_chart(message["sql_results"], message.get("chart_type", "table"))


# Helper function to submit query
def submit_query(query_text: str):
    """Send query to master orchestrator and handle the response."""
    st.session_state.messages.append({"role": "user", "content": query_text})

    with st.spinner("Executing ADK orchestrator workflow..."):
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
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": data.get(
                                "output", "No response content returned."
                            ),
                            "status": "success",
                            "sql_results": data.get("sql_results"),
                            "chart_type": data.get("chart_type"),
                        }
                    )
                    st.session_state.awaiting_approval = False
                    st.session_state.interrupted_sql = ""

                elif status == "interrupted":
                    st.session_state.awaiting_approval = True
                    st.session_state.interrupted_sql = data.get(
                        "message", "Approval required"
                    )
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": st.session_state.interrupted_sql,
                            "status": "interrupted",
                        }
                    )

                elif status == "blocked":
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": data.get("output", "Blocked by safety checks."),
                            "status": "blocked",
                        }
                    )
                    st.session_state.awaiting_approval = False
                    st.session_state.interrupted_sql = ""
            else:
                st.error(
                    f"Error calling orchestrator: {resp.status_code} - {resp.text}"
                )
        except Exception as e:
            st.error(f"Failed to connect to Orchestrator service: {e}")


# Handle Awaiting Human Approval flow
if st.session_state.awaiting_approval:
    st.markdown('<div class="approval-card">', unsafe_allow_html=True)
    st.warning(
        "🚨 A SQL query is waiting for your explicit approval before execution. "
        "Review the query above and decide."
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "✅ Yes, Approve and Execute", use_container_width=True, type="primary"
        ):
            st.session_state.awaiting_approval = False
            submit_query("yes")
            st.rerun()

    with col2:
        if st.button("❌ No, Reject", use_container_width=True):
            st.session_state.awaiting_approval = False
            submit_query("no")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
else:
    # Standard Chat Input
    user_query = st.chat_input(
        "Ask a business question (e.g. 'Show me top 5 selling products by profit margin')..."
    )
    if user_query:
        submit_query(user_query)
        st.rerun()
