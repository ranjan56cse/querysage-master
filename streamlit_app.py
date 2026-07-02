import re
import uuid

import httpx
import pandas as pd
import plotly.express as px
import streamlit as st

# Set page config for a widescreen BI experience
st.set_page_config(
    page_title="QuerySage Canvas", layout="wide", initial_sidebar_state="expanded"
)

# Light Soothing CSS Theme Customization
st.markdown(
    """
<style>
    /* Global Background and Typography */
    .stApp {
        background-color: #f8fafc; /* Slate 50 (Light Gray-Blue) */
        color: #0f172a; /* Slate 900 */
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* Top White Banner Panel */
    .top-banner {
        background-color: #ffffff;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }

    .main-title {
        font-size: 2rem !important;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
    }

    .subtitle {
        font-size: 0.95rem;
        color: #64748b;
        margin-top: 0.25rem;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    .sidebar-title {
        font-weight: 700;
        font-size: 1.2rem;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }

    /* Panel Cards */
    .bi-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
    }

    .panel-section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.75rem;
    }

    /* Adjusted input wrappers */
    div.stTextArea textarea {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }

    /* Alert cards custom theme overrides */
    div[data-testid="stNotification"] {
        border-radius: 8px;
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


# Clean markdown table structures from insights text for display purposes
def clean_markdown_tables(text: str) -> str:
    # Pattern matching markdown grid table structures
    pattern = r"\|.*\|(\r?\n\|[-:| ]+\|)+(\r?\n\|.*\|)*"
    cleaned = re.sub(pattern, "", text)
    # Strip residual double separators
    cleaned = re.sub(r"SQL Results\s*$", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


# Sidebar: Controls and Status Indicators
with st.sidebar:
    st.markdown(
        '<div class="sidebar-title">QuerySage Control</div>', unsafe_allow_html=True
    )
    st.markdown("Automated Postgres insights translation and security validations.")

    st.divider()

    # Left panel: Database selection
    st.markdown("### Database Connection")
    db_selection = st.selectbox("Database", ["analytics_db1 (Neon Postgres)"])

    st.divider()

    st.markdown("### Session Controls")
    st.text_input("User ID", value=st.session_state.user_id, key="user_id")
    st.text_input(
        "Session ID",
        value=st.session_state.session_id,
        key="session_id_input",
        disabled=True,
    )

    if st.button("New Session", width="stretch"):
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

    st.markdown("### Services Status")
    services_list = {
        "Orchestrator": "http://localhost:8000/health",
        "Gatekeeper": "http://localhost:9000/health",
        "SQL Engine": "http://localhost:9001/health",
    }

    for name, url in services_list.items():
        try:
            resp = httpx.get(url, timeout=2.0)
            if resp.status_code == 200:
                st.success(f"{name} online")
            else:
                st.warning(f"{name} online (status {resp.status_code})")
        except Exception:
            st.error(f"{name} offline")

# Top White Panel Banner
st.markdown(
    """
<div class="top-banner">
    <div class="main-title">QuerySage Canvas</div>
    <div class="subtitle">Enter your natural language business queries below to analyze data and build visual reports.</div>
</div>
""",
    unsafe_allow_html=True,
)


# Submit query runner
def submit_query(query_text: str):
    st.session_state.messages.append({"role": "user", "content": query_text})

    with st.spinner("Processing analysis workflow..."):
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
                    st.session_state.current_insights = clean_markdown_tables(output)

                    # Extract SQL
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
                            "content": st.session_state.current_insights,
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

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": f"Neon SQL execution confirmation required:\n\n```sql\n{st.session_state.interrupted_sql}\n```",
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
                st.error(f"Endpoint Error: {resp.status_code} - {resp.text}")
        except Exception as e:
            st.error(f"Failed to connect to Orchestrator: {e}")


# Full-Width Horizon Canvas (NL Query Input)
with st.container():
    st.markdown(
        '<div class="panel-section-title">Query Canvas</div>', unsafe_allow_html=True
    )

    if st.session_state.awaiting_approval:
        st.warning(
            "Review required: Neon SQL Execution request. Do you approve execution?"
        )
        st.code(st.session_state.interrupted_sql, language="sql")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes, Approve Execution", width="stretch", type="primary"):
                st.session_state.awaiting_approval = False
                submit_query("yes")
                st.rerun()
        with c2:
            if st.button("No, Reject Query", width="stretch"):
                st.session_state.awaiting_approval = False
                submit_query("no")
                st.rerun()
    else:
        user_query = st.text_area(
            "Natural Language Question",
            value="",
            placeholder="Type your e-commerce analysis question here...",
            label_visibility="collapsed",
            height=80,
        )

        # Horizontal action buttons below the Canvas input
        btn_col1, btn_col2, _ = st.columns([1, 1, 4])

        with btn_col1:
            submit_click = st.button("Show Result", width="stretch")

        with btn_col2:
            # Determine if Chart visualization is enabled dynamically based on the current results
            chart_enabled = False
            df_temp = None
            if st.session_state.current_results:
                try:
                    df_temp = pd.DataFrame(st.session_state.current_results)
                    if df_temp is not None and not df_temp.empty:
                        num_cols = df_temp.select_dtypes(
                            include=["number"]
                        ).columns.tolist()
                        if len(num_cols) >= 1 and len(df_temp.columns) >= 2:
                            chart_enabled = True
                except Exception:
                    pass

            # Show Charts button enabled or disabled based on result criteria
            charts_click = st.button(
                "Show Charts", width="stretch", disabled=not chart_enabled
            )

        if submit_click and user_query.strip():
            submit_query(user_query)
            st.rerun()

        if charts_click and chart_enabled:
            # If they click Show Charts, automatically activate or scroll to chart tab view
            pass

st.divider()

# Tab workspace display for ResultSet and Chart tabs
if st.session_state.current_results is not None:
    tab_results, tab_chart = st.tabs(["Resultset", "Chart"])

    try:
        df_display = pd.DataFrame(st.session_state.current_results)
    except Exception:
        df_display = None

    with tab_results:
        if df_display is not None and not df_display.empty:
            # Renders adjustable, scrollable table like Hugging Face Data Studio
            st.dataframe(df_display, use_container_width=True, height=400)
        else:
            st.info(
                "Query executed successfully, but no results were returned from the database."
            )

        # Display SQL statement and analyst comments below the table
        if st.session_state.current_sql:
            st.markdown("### SQL Statement")
            st.code(st.session_state.current_sql, language="sql")

        if st.session_state.current_insights:
            st.markdown("### Analyst Insights")
            st.markdown(st.session_state.current_insights)

    with tab_chart:
        if df_display is not None and not df_display.empty and chart_enabled:
            chart_type = st.session_state.current_chart_type
            numeric_cols = df_display.select_dtypes(include=["number"]).columns.tolist()
            categorical_cols = df_display.select_dtypes(
                exclude=["number"]
            ).columns.tolist()

            if (
                chart_type == "bar"
                and len(categorical_cols) >= 1
                and len(numeric_cols) >= 1
            ):
                fig = px.bar(
                    df_display,
                    x=categorical_cols[0],
                    y=numeric_cols[0],
                    color=categorical_cols[0],
                    title="Distribution View",
                    template="plotly_white",
                )
                st.plotly_chart(fig, use_container_width=True)

            elif (
                chart_type == "line"
                and len(categorical_cols) >= 1
                and len(numeric_cols) >= 1
            ):
                fig = px.line(
                    df_display,
                    x=categorical_cols[0],
                    y=numeric_cols[0],
                    markers=True,
                    title="Trend View",
                    template="plotly_white",
                )
                st.plotly_chart(fig, use_container_width=True)

            elif (
                chart_type == "pie"
                and len(categorical_cols) >= 1
                and len(numeric_cols) >= 1
            ):
                fig = px.pie(
                    df_display,
                    names=categorical_cols[0],
                    values=numeric_cols[0],
                    title="Proportion View",
                    template="plotly_white",
                )
                st.plotly_chart(fig, use_container_width=True)

            else:
                if len(numeric_cols) >= 2:
                    fig = px.scatter(
                        df_display,
                        x=numeric_cols[0],
                        y=numeric_cols[1],
                        title="Scatter Analysis",
                        template="plotly_white",
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    fig = px.bar(
                        df_display,
                        x=df_display.columns[0],
                        y=df_display.columns[1],
                        template="plotly_white",
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(
                "Chart view is disabled: the query results do not contain enough dimensions (requires at least 1 numeric column and 2 columns total) to display a graphic chart."
            )
else:
    # Default State
    st.markdown(
        '<div style="background-color: #ffffff; border: 1px dashed #cbd5e1; padding: 4rem; text-align: center; border-radius: 12px;">',
        unsafe_allow_html=True,
    )
    st.markdown("### No Query Executed")
    st.markdown(
        "Type a natural language question in the canvas above and click **Show Result** to analyze e-commerce datasets."
    )
    st.markdown("</div>", unsafe_allow_html=True)
