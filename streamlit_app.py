import uuid

import httpx
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
    .assistant-msg {
        background-color: #111827;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border-left: 4px solid #a855f7;
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
    .metric-badge {
        background-color: #312e81;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.85rem;
        color: #c7d2fe;
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
        "QuerySage uses Google ADK 2.0 graph workflow orchestration to secure, translate, and analyze e-commerce analytics queries."
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
    # Health checks indicator
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
    '<div class="subtitle">Secure natural-language to PostgreSQL translator with human-in-the-loop validation and visual insights.</div>',
    unsafe_allow_html=True,
)

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
                f'<div class="warning-msg"><b>⚠️ Security Block:</b><br>{message["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="assistant-msg"><b>🤖 Assistant:</b><br>{message["content"]}</div>',
                unsafe_allow_html=True,
            )


# Helper function to submit query
def submit_query(query_text: str):
    # Add User message
    st.session_state.messages.append({"role": "user", "content": query_text})

    # Show loading status and call API
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
                        }
                    )
                    st.session_state.awaiting_approval = False
                    st.session_state.interrupted_sql = ""

                elif status == "interrupted":
                    st.session_state.awaiting_approval = True
                    st.session_state.interrupted_sql = data.get(
                        "message", "RequestInput Approval Required"
                    )
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": f"**Execution paused for Human-in-the-Loop review:**\n\n```sql\n{st.session_state.interrupted_sql}\n```",
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
                    f"Error calling orchestrator endpoint: {resp.status_code} - {resp.text}"
                )
        except Exception as e:
            st.error(f"Failed to connect to Orchestrator service: {e}")


# Handle Awaiting Human Approval flow
if st.session_state.awaiting_approval:
    st.markdown('<div class="approval-card">', unsafe_allow_html=True)
    st.warning(
        "🚨 A transaction is waiting for your explicit approval. Do you approve executing the SQL statement above?"
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
