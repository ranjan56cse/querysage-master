import os
import re
import uuid

import httpx
import pandas as pd
import plotly.express as px
import streamlit as st

# ── Service URLs ───────────────────────────────────────────────────────────────
MASTER_URL     = os.environ.get("MASTER_URL",      "http://localhost:8000")
GATEKEEPER_URL = os.environ.get("GATEKEEPER_URL",  "http://localhost:9000")
SQL_ENGINE_URL = os.environ.get("SQL_ENGINE_URL",  "http://localhost:9001")


def _get_auth_headers(url: str) -> dict:
    if "aiplatform.googleapis.com" not in url:
        return {}
    try:
        import google.auth
        import google.auth.transport.requests
        creds, _ = google.auth.default()
        creds.refresh(google.auth.transport.requests.Request())
        return {"Authorization": f"Bearer {creds.token}"}
    except Exception:
        return {}


def _clean_sql_text(raw: str) -> str:
    s = raw
    s = re.sub(r"(?i)^neon sql execution request:\s*", "", s)
    s = re.sub(r"```sql\s*", "", s)
    s = re.sub(r"```\s*", "", s)
    s = re.sub(r"(?i)do you approve execution\?\s*\(yes/no\)\s*", "", s)
    return s.strip()


# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QuerySage", page_icon="❖",
    layout="wide", initial_sidebar_state="collapsed",
)

# ── Health check ──────────────────────────────────────────────────────────────
try:
    _r = httpx.get(f"{MASTER_URL}/health", headers=_get_auth_headers(MASTER_URL), timeout=2.0)
    _service_ok = _r.status_code == 200
except Exception:
    _service_ok = False

# ══════════════════════════════════════════════════════════════════════════════
# ── GLOBAL CSS ────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ─── Base ───────────────────────────────────────────────────────── */
html,body,[class*="css"]{font-family:'Inter',-apple-system,sans-serif!important}
.stApp{background-color:#FBF9F4!important;color:#241F1A!important}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding-top:0!important;padding-bottom:40px!important;max-width:100%!important}
section[data-testid="stSidebar"],
button[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"]{display:none!important}

/* ─── Top Bar ────────────────────────────────────────────────────── */
.qs-topbar{display:flex;align-items:center;justify-content:space-between;padding:14px 28px;background:#FFF;border-bottom:1px solid #E6E1D3}
.qs-brand-block{display:flex;align-items:center;gap:10px}
.qs-brand-icon{width:32px;height:32px;border-radius:9px;background:#CFFF3D;display:flex;align-items:center;justify-content:center}
.qs-brand-icon svg{width:16px;height:16px}
.qs-brand-text{display:flex;flex-direction:column}
.qs-brand-name{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:21px;letter-spacing:-0.3px;color:#E4572E;line-height:1.2}
.qs-brand-sub{font-family:'Inter',sans-serif;font-size:11.5px;font-weight:500;color:#A69E8C;margin-top:2px}
.qs-topbar-right{display:flex;align-items:center;gap:16px}
.qs-status-pill{display:flex;align-items:center;gap:7px;font-family:'Inter',sans-serif;font-size:12px;font-weight:500;color:#6B6252}
.qs-status-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.qs-status-dot.green{background:#16A34A;box-shadow:0 0 6px rgba(22,163,74,0.4)}
.qs-status-dot.red{background:#DC2626;box-shadow:0 0 6px rgba(220,38,38,0.4)}
.qs-db-pill{font-family:'Inter',sans-serif;font-size:12.5px;font-weight:500;color:#241F1A;background:#F4F1E8;border:1px solid #E6E1D3;border-radius:9999px;padding:7px 14px}

/* ─── Search Pill ────────────────────────────────────────────────── */
.qs-search-section{max-width:980px;margin:22px auto 0;padding:0 28px}
div[data-testid="stForm"]{background:#FFF!important;border:1.5px solid #E6E1D3!important;border-radius:9999px!important;padding:4px 6px 4px 22px!important;box-shadow:0 1px 2px rgba(36,31,26,0.04)!important}
div[data-testid="stForm"]:focus-within{border-color:#A69E8C!important;box-shadow:0 0 0 3px rgba(166,158,140,0.12),0 1px 2px rgba(36,31,26,0.04)!important}
div[data-testid="stForm"] [data-testid="stHorizontalBlock"]{align-items:center!important;gap:4px!important;flex-wrap:nowrap!important}
div[data-testid="stForm"] [data-testid="column"]{padding:0!important;min-width:0!important}
div[data-testid="stForm"] [data-baseweb="base-input"],
div[data-testid="stForm"] [data-baseweb="input"]{background:transparent!important;border:none!important;box-shadow:none!important}
div[data-testid="stForm"] input[type="text"]{background:transparent!important;border:none!important;box-shadow:none!important;outline:none!important;color:#241F1A!important;font-size:15px!important;font-family:'Inter',sans-serif!important;padding:8px 8px 8px 0!important;caret-color:#E4572E!important}
div[data-testid="stForm"] input[type="text"]::placeholder{color:#A69E8C!important}
div[data-testid="stForm"] label{display:none!important}
div[data-testid="stForm"] [data-testid="stTextInput"]{margin:0!important;padding:0!important}
div[data-testid="stForm"] [data-testid="stTextInput"]>div{margin:0!important}
div[data-testid="stForm"] button{background-color:#CFFF3D!important;color:#241F1A!important;font-weight:700!important;font-size:13.5px!important;font-family:'Space Grotesk',sans-serif!important;border:none!important;border-radius:9999px!important;padding:11px 20px!important;white-space:nowrap!important;cursor:pointer!important}
div[data-testid="stForm"] button:hover{opacity:0.87!important}

/* ─── HITL Card ──────────────────────────────────────────────────── */
.hitl-card{background:#FFF;border:1px solid #EEEAE0;border-radius:16px;padding:0;overflow:hidden;box-shadow:0 2px 12px rgba(36,31,26,0.05)}
.hitl-top{padding:18px 24px;border-bottom:1px solid #EEEAE0}
.hitl-title{font-family:'Space Grotesk',sans-serif;font-size:12px;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;color:#E4572E;margin-bottom:4px}
.hitl-subtitle{font-size:13.5px;color:#6B6252;line-height:1.5}
.hitl-sql-toggle{border:none;border-bottom:1px solid #EEEAE0}
.hitl-sql-toggle summary{padding:12px 24px;cursor:pointer;display:flex;align-items:center;gap:8px;list-style:none;font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:600;letter-spacing:0.5px;text-transform:uppercase;color:#A69E8C;user-select:none}
.hitl-sql-toggle summary:hover{background:#FAFAF7}
.hitl-sql-toggle summary::-webkit-details-marker{display:none}
.hitl-sql-toggle summary::before{content:'';width:0;height:0;border-left:5px solid #A69E8C;border-top:4px solid transparent;border-bottom:4px solid transparent;transition:transform 0.2s}
.hitl-sql-toggle[open] summary::before{transform:rotate(90deg)}
.hitl-sql-block{margin:0 24px 16px;background:#1B2838;border-radius:10px;padding:18px 20px;font-family:'JetBrains Mono',monospace;font-size:13px;color:#7FDBCA;line-height:1.7;white-space:pre-wrap;word-break:break-word;max-height:240px;overflow-y:auto}
.hitl-btn-row{padding:14px 24px;display:flex;align-items:center;gap:10px}
.hitl-btn-approve{display:inline-block;background:#CFFF3D;color:#241F1A;font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:13px;border:none;border-radius:9999px;padding:10px 24px;cursor:pointer;text-decoration:none}
.hitl-btn-approve:hover{opacity:0.87}
.hitl-btn-reject{display:inline-block;background:transparent;color:#DC2626;font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:13px;border:1.5px solid rgba(220,38,38,0.4);border-radius:9999px;padding:10px 24px;cursor:pointer;text-decoration:none}
.hitl-btn-reject:hover{border-color:#DC2626;background:rgba(220,38,38,0.05)}

/* Streamlit buttons styled for HITL */
button[data-testid="stBaseButton-primary"]{background-color:#CFFF3D!important;color:#241F1A!important;font-weight:700!important;font-size:13px!important;font-family:'Space Grotesk',sans-serif!important;border:none!important;border-radius:9999px!important;padding:10px 24px!important}
button[data-testid="stBaseButton-primary"]:hover{opacity:0.87!important}
button[data-testid="stBaseButton-secondary"]{background:transparent!important;color:#DC2626!important;font-weight:600!important;font-size:13px!important;border:1.5px solid rgba(220,38,38,0.4)!important;border-radius:9999px!important;padding:10px 24px!important}
button[data-testid="stBaseButton-secondary"]:hover{border-color:#DC2626!important;background:rgba(220,38,38,0.05)!important}

/* ─── Schema Verified Card ───────────────────────────────────────── */
.sv-confirmed{background:#E4F4FC;border:1px solid rgba(14,165,233,0.25);border-radius:16px;padding:14px 24px;display:flex;align-items:center;gap:12px}
.sv-confirmed-badge{font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;color:#0EA5E9}
.sv-confirmed-text{font-size:13.5px;color:#241F1A;font-weight:500}
.sv-confirmed-check{color:#16A34A;font-weight:700;margin-right:4px}

/* ─── Schema Ambiguity Card ──────────────────────────────────────── */
.sv-card{background:#E4F4FC;border:1px solid rgba(14,165,233,0.25);border-radius:16px;padding:16px 24px}
.sv-badge{font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;color:#0EA5E9;margin-bottom:6px}
.sv-explanation{font-size:13.5px;color:#241F1A;line-height:1.5;margin-bottom:12px}
.sv-suggestion-box{background:#FFF;border:1px dashed rgba(14,165,233,0.4);border-radius:10px;padding:9px 12px;margin-bottom:12px;font-family:'JetBrains Mono',monospace;font-size:12px;color:#E4572E}

/* ─── SQL Panel ──────────────────────────────────────────────────── */
.qs-sql-wrap [data-testid="stExpander"]{background:#FFF!important;border:1px solid #EEEAE0!important;border-radius:16px!important;overflow:hidden}
.qs-sql-wrap [data-testid="stExpander"] summary,
.qs-sql-wrap details summary{background:#FFF!important;padding:13px 18px!important;cursor:pointer!important;list-style:none!important;border-radius:16px!important}
.qs-sql-wrap [data-testid="stExpander"] svg{color:#A69E8C!important;stroke:#A69E8C!important}
.qs-sql-wrap [data-testid="stExpanderDetails"]{background:#FFF!important;padding:0 18px 14px!important;border-top:1px solid #EEEAE0!important}
.qs-sql-wrap .stCodeBlock,.qs-sql-wrap .stCodeBlock pre{background:#1B2838!important;border:none!important;border-radius:10px!important;margin-top:4px!important}
.qs-sql-wrap .stCodeBlock code{color:#7FDBCA!important;font-family:'JetBrains Mono',monospace!important;font-size:13px!important;line-height:1.7!important}
.sql-panel-label{font-family:'Space Grotesk',sans-serif;font-size:11.5px;font-weight:600;letter-spacing:0.6px;text-transform:uppercase;color:#A69E8C;vertical-align:middle}
.sql-verified-badge{font-size:11px;font-weight:600;color:#16A34A;background:rgba(22,163,74,0.08);border:1px solid rgba(22,163,74,0.2);border-radius:9999px;padding:2px 10px;font-family:'Inter',sans-serif;margin-left:10px;vertical-align:middle}

/* ─── Two-Tab Layout ─────────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"]{background:transparent!important;border-bottom:1px solid #E6E1D3!important;gap:4px!important}
[data-testid="stTabs"] button[data-baseweb="tab"]{background:transparent!important;color:#A69E8C!important;font-family:'Space Grotesk',sans-serif!important;font-weight:600!important;font-size:13px!important;border-radius:0!important;padding:10px 6px!important;margin-right:22px!important}
[data-testid="stTabs"] button[data-baseweb="tab"]:hover{color:#6B6252!important;background:transparent!important}
[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"]{color:#241F1A!important;border-bottom:2.5px solid #8FCC00!important}
[data-testid="stTabPanel"]{background:transparent!important;border:none!important;padding:18px 0!important}

/* ─── ResultSet Table ────────────────────────────────────────────── */
.qs-result-table{width:100%;border-collapse:collapse;border:1px solid #EEEAE0;border-radius:12px;overflow:hidden;font-family:'Inter',sans-serif}
.qs-result-table thead tr{background:#F4F1E8}
.qs-result-table th{font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:600;letter-spacing:0.5px;text-transform:uppercase;color:#A69E8C;padding:10px 16px;text-align:left;white-space:nowrap}
.qs-result-table th.num-col{text-align:right}
.qs-result-table td{font-size:13.5px;color:#6B6252;padding:11px 16px;border-top:1px solid #EEEAE0;white-space:nowrap}
.qs-result-table td.name-col{color:#241F1A;font-weight:500}
.qs-result-table td.num-col{text-align:right;font-family:'JetBrains Mono',monospace;font-size:13px}
.qs-result-table tbody tr:nth-child(odd){background:rgba(244,241,232,0.5)}
.qs-result-table tbody tr:nth-child(even){background:transparent}

/* ─── Chart Cards ────────────────────────────────────────────────── */
.chart-card{background:#FFF;border:1px solid #EEEAE0;border-radius:14px;padding:16px 18px;margin-bottom:8px}
.chart-card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
.chart-card-label{font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:600;letter-spacing:0.5px;text-transform:uppercase;color:#A69E8C}
.chart-card-badge{font-size:10.5px;font-weight:600;padding:2px 8px;border-radius:9999px;font-family:'Inter',sans-serif}
.chart-card-badge.ranking{color:#E4572E;background:#FBEAE4}
.chart-card-badge.proportion{color:#0EA5E9;background:#E4F4FC}

/* ─── Insight Cards (light, full-width) ──────────────────────────── */
.insight-card{background:#FFF;border:1px solid #EEEAE0;border-radius:14px;padding:18px 24px;margin-bottom:12px}
.insight-label{font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;margin-bottom:6px}
.insight-text{font-size:13.5px;color:#6B6252;line-height:1.55}

/* ─── Empty State ────────────────────────────────────────────────── */
.qs-empty{text-align:center;padding:80px 24px;max-width:480px;margin:0 auto}
.qs-empty h3{font-family:'Space Grotesk',sans-serif;color:#6B6252;font-weight:600;margin-bottom:8px;font-size:1.1rem}
.qs-empty p{color:#A69E8C;font-size:13.5px;line-height:1.6}
.qs-empty strong{color:#E4572E}

/* ─── Loading ────────────────────────────────────────────────────── */
[data-testid="stSpinner"]>div:first-child{border-top-color:#E4572E!important;border-right-color:#E4572E!important;border-bottom-color:rgba(228,87,46,0.2)!important;border-left-color:rgba(228,87,46,0.2)!important}
[data-testid="stSpinner"] p{color:#6B6252!important;font-size:0.85rem!important;font-weight:500!important}
.qs-loading-bar{max-width:980px;margin:16px auto;padding:14px 24px;background:#FFF;border:1px solid #E6E1D3;border-radius:16px;display:flex;align-items:center;gap:12px;box-shadow:0 1px 4px rgba(36,31,26,0.06)}
.qs-loading-bar .qs-loading-dots{display:flex;gap:5px;align-items:center}
@keyframes qs-pulse{0%,80%,100%{opacity:0.2;transform:scale(0.8)}40%{opacity:1;transform:scale(1)}}
.qs-loading-dot{width:6px;height:6px;border-radius:50%;background:#E4572E;animation:qs-pulse 1.2s infinite ease-in-out}
.qs-loading-dot:nth-child(2){animation-delay:0.2s}
.qs-loading-dot:nth-child(3){animation-delay:0.4s}
.qs-loading-text{font-size:13.5px;color:#6B6252;font-weight:500}

/* ─── Misc ───────────────────────────────────────────────────────── */
.stCodeBlock,.stCodeBlock pre,.stCodeBlock code{background-color:#1B2838!important;border:none!important;border-radius:10px!important}
.stCodeBlock code{color:#7FDBCA!important}
hr{border-color:#E6E1D3!important;margin:16px 0!important}
div[data-testid="stNotification"]{background-color:#FFF!important;border-left-color:#E6E1D3!important;color:#241F1A!important;border-radius:8px!important}
@keyframes qs-fadein{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
[data-testid="stTabs"]{animation:qs-fadein 0.4s cubic-bezier(0.16,1,0.3,1) both}

/* ─── Content sections consistent width ──────────────────────────── */
.qs-section{max-width:980px;margin:16px auto 0;padding:0 28px}
</style>
""", unsafe_allow_html=True)

# ── Session State ──────────────────────────────────────────────────────────────
_defaults = {
    "messages":              [],
    "session_id":            str(uuid.uuid4()),
    "user_id":               "streamlit_user",
    "awaiting_approval":     False,
    "interrupted_sql":       "",
    "current_results":       None,
    "current_chart_type":    "table",
    "current_sql":           "",
    "current_insights":      "",
    "follow_up_suggestions": [],
    "schema_verification":   None,
    "insight_data":          None,
    "last_error":            None,
    "last_query_text":       "",
    "schema_confirmed":      False,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── Helpers ────────────────────────────────────────────────────────────────────
def clean_markdown_tables(text: str) -> str:
    pattern = r"\|.*\|(\r?\n\|[-:| ]+\|)+(\r?\n\|.*\|)*"
    cleaned = re.sub(pattern, "", text)
    cleaned = re.sub(r"SQL Results\s*$", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def submit_query(query_text: str):
    st.session_state.messages.append({"role": "user", "content": query_text})
    st.session_state.current_results = None
    st.session_state.current_sql = ""
    st.session_state.current_insights = ""
    st.session_state.schema_verification = None
    st.session_state.insight_data = None
    st.session_state.schema_confirmed = False

    with st.spinner("Analyzing your question..."):
        p_loader = st.empty()
        result_holder = {}
        _sid = st.session_state.session_id
        _uid = st.session_state.user_id
        _headers = _get_auth_headers(MASTER_URL)

        def make_request():
            try:
                payload = {"session_id": _sid, "user_id": _uid, "user_query": query_text}
                resp = httpx.post(f"{MASTER_URL}/chat", json=payload, headers=_headers, timeout=90.0)
                result_holder["resp"] = resp
            except Exception as e:
                result_holder["error"] = e

        import threading, time
        thread = threading.Thread(target=make_request)
        thread.start()

        _msgs = [
            (0,   "Analyzing your question..."),
            (1.5, "Writing query against verified schema..."),
            (3.2, "Executing against Neon Postgres..."),
        ]
        start_time = time.time()
        while thread.is_alive():
            elapsed = time.time() - start_time
            _label = _msgs[0][1]
            for _t, _m in _msgs:
                if elapsed >= _t:
                    _label = _m
            p_loader.markdown(
                f'<div class="qs-loading-bar">'
                f'<div class="qs-loading-dots">'
                f'<div class="qs-loading-dot"></div>'
                f'<div class="qs-loading-dot"></div>'
                f'<div class="qs-loading-dot"></div></div>'
                f'<span class="qs-loading-text">{_label}</span></div>',
                unsafe_allow_html=True,
            )
            time.sleep(0.1)
        p_loader.empty()

    st.session_state.last_error = None
    if "error" in result_holder:
        st.session_state.last_error = f"Failed to reach Orchestrator: {result_holder['error']}"
    elif "resp" in result_holder:
        resp = result_holder["resp"]
        if resp.status_code == 200:
            data   = resp.json()
            status = data.get("status")

            if status == "success":
                output      = data.get("output", "")
                sql_results = data.get("sql_results")
                chart_type  = data.get("chart_type", "table")

                st.session_state.current_results    = sql_results
                st.session_state.current_chart_type = chart_type
                st.session_state.current_insights   = clean_markdown_tables(output)
                st.session_state.last_query_text     = query_text

                st.session_state.current_sql = ""
                if "```sql" in output:
                    try:
                        st.session_state.current_sql = output.split("```sql")[1].split("```")[0].strip()
                    except Exception:
                        pass

                # Also try to get sql from data directly
                if not st.session_state.current_sql:
                    _dsql = data.get("sql") or data.get("generated_sql") or ""
                    if _dsql:
                        st.session_state.current_sql = _clean_sql_text(_dsql)

                raw_insight = data.get("insight_data") or {}
                if isinstance(raw_insight, dict) and raw_insight:
                    st.session_state.insight_data = {
                        "anomaly":     raw_insight.get("anomaly", ""),
                        "trend":       raw_insight.get("trend", ""),
                        "correlation": raw_insight.get("correlation", ""),
                        "insights":    raw_insight.get("insights", ""),
                    }
                else:
                    st.session_state.insight_data = {
                        "anomaly": "", "trend": "", "correlation": "",
                        "insights": clean_markdown_tables(output),
                    }

                raw_sv = data.get("schema_verification")
                if isinstance(raw_sv, dict) and raw_sv.get("is_ambiguous"):
                    st.session_state.schema_verification = raw_sv
                    st.session_state.schema_confirmed = False
                else:
                    _sv_keywords = ("did you mean", "ambiguous", "corrected query",
                                    "suggested phrasing", "could mean", "clarif")
                    if any(kw in output.lower() for kw in _sv_keywords):
                        st.session_state.schema_verification = {
                            "is_ambiguous": True, "original_query": query_text,
                            "corrected_query": None, "explanation": output[:400],
                            "alternatives": [],
                        }
                        st.session_state.schema_confirmed = False
                    else:
                        st.session_state.schema_verification = None
                        st.session_state.schema_confirmed = True

                st.session_state.messages.append({
                    "role": "assistant", "content": st.session_state.current_insights,
                    "status": "success", "sql_results": sql_results, "chart_type": chart_type,
                })
                st.session_state.awaiting_approval = False
                st.session_state.interrupted_sql   = ""

            elif status == "interrupted":
                st.session_state.awaiting_approval = True
                raw_msg = data.get("message", "")
                st.session_state.interrupted_sql = _clean_sql_text(raw_msg)
                st.session_state.messages.append({
                    "role": "assistant", "status": "interrupted",
                    "content": f"SQL requires approval:\n```sql\n{st.session_state.interrupted_sql}\n```",
                })

            elif status == "blocked":
                output = data.get("output", "Blocked by safety checks.")
                st.session_state.messages.append({"role": "assistant", "content": output, "status": "blocked"})
                st.session_state.awaiting_approval = False
                st.session_state.interrupted_sql = ""
                st.session_state.current_insights = output
                st.session_state.current_results = None
                st.session_state.insight_data = None
        else:
            st.session_state.last_error = f"Endpoint error {resp.status_code}: {resp.text}"


# ══════════════════════════════════════════════════════════════════════════════
# ── LAYOUT ────────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

# ── Top Bar ──────────────────────────────────────────────────────────────────
_status_cls = "green" if _service_ok else "red"
_status_txt = "Connected &amp; Ready" if _service_ok else "Service Unavailable"

st.markdown(f"""
<div class="qs-topbar">
    <div class="qs-brand-block">
        <div class="qs-brand-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="#241F1A" stroke-width="2"
                 stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 3l1.912 5.813a2 2 0 001.272 1.272L21 12l-5.813 1.912a2 2 0 00-1.272 1.272L12 21l-1.912-5.813a2 2 0 00-1.272-1.272L3 12l5.813-1.912a2 2 0 001.275-1.275z"/>
            </svg>
        </div>
        <div class="qs-brand-text">
            <span class="qs-brand-name">QuerySage</span>
            <span class="qs-brand-sub">Natural language analytics for your e-commerce data</span>
        </div>
    </div>
    <div class="qs-topbar-right">
        <div class="qs-status-pill"><span class="qs-status-dot {_status_cls}"></span>{_status_txt}</div>
        <div class="qs-db-pill">Neon Postgres &mdash; Production</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Search Pill (query persists after submit) ────────────────────────────────
st.markdown('<div class="qs-search-section">', unsafe_allow_html=True)
with st.form(key="search_form", clear_on_submit=False):
    _col_q, _col_btn = st.columns([9, 1])
    with _col_q:
        query_input = st.text_input(
            "query",
            placeholder="Ask a business question in plain English…",
            label_visibility="collapsed",
        )
    with _col_btn:
        run_clicked = st.form_submit_button("Run →")
st.markdown("</div>", unsafe_allow_html=True)

active_query = query_input.strip() if run_clicked else ""

# ── HITL Approval ────────────────────────────────────────────────────────────
if st.session_state.awaiting_approval:
    import html as _html
    _safe_sql = _html.escape(st.session_state.interrupted_sql or "")

    st.markdown(f"""
<div class="qs-section">
<div class="hitl-card">
    <div class="hitl-top">
        <div class="hitl-title">SQL Execution Approval Required</div>
        <div class="hitl-subtitle">The following SQL will be executed against
        <strong style="color:#241F1A;">Neon Postgres</strong>. Review carefully before approving.</div>
    </div>
    <details class="hitl-sql-toggle" open>
        <summary>Generated SQL</summary>
        <div class="hitl-sql-block">{_safe_sql}</div>
    </details>
</div>
</div>
""", unsafe_allow_html=True)

    # Buttons — styled via global CSS for primary/secondary
    st.markdown('<div class="qs-section">', unsafe_allow_html=True)
    _b1, _b2, _pad = st.columns([1.2, 0.8, 5])
    with _b1:
        if st.button("Approve & Execute", key="hitl_approve", type="primary"):
            st.session_state.awaiting_approval = False
            submit_query("yes")
            st.rerun()
    with _b2:
        if st.button("Reject", key="hitl_reject", type="secondary"):
            st.session_state.awaiting_approval = False
            submit_query("no")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif active_query:
    submit_query(active_query)
    st.rerun()

# ── Schema Verification — Ambiguous ──────────────────────────────────────────
_sv = st.session_state.get("schema_verification")
if _sv and _sv.get("is_ambiguous"):
    _sv_explanation  = _sv.get("explanation") or ""
    _sv_corrected    = _sv.get("corrected_query")
    _sv_alternatives = _sv.get("alternatives") or []

    st.markdown('<div class="qs-section">', unsafe_allow_html=True)
    st.markdown('<div class="sv-card">', unsafe_allow_html=True)
    st.markdown('<div class="sv-badge">Schema Verification</div>', unsafe_allow_html=True)

    if _sv_explanation:
        _disp = _sv_explanation if len(_sv_explanation) <= 280 else _sv_explanation[:277] + "…"
        st.markdown(f'<div class="sv-explanation">{_disp}</div>', unsafe_allow_html=True)

    if _sv_corrected:
        st.markdown(
            f'<div class="sv-suggestion-box">'
            f'Suggested: <span style="color:#E4572E;">{_sv_corrected}</span></div>',
            unsafe_allow_html=True,
        )
        if st.button(f"Confirm & Run", key="sv_confirm_run", type="primary"):
            st.session_state.schema_verification = None
            submit_query(_sv_corrected)
            st.rerun()

    if st.button("Dismiss", key="sv_dismiss"):
        st.session_state.schema_verification = None
        st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)

# ── Schema Verification — Confirmed ──────────────────────────────────────────
if st.session_state.get("schema_confirmed") and st.session_state.get("last_query_text"):
    import html as _html_esc
    _qtext = _html_esc.escape(st.session_state.last_query_text)
    st.markdown(f"""
<div class="qs-section">
    <div class="sv-confirmed">
        <div>
            <div class="sv-confirmed-badge">Schema Verification</div>
            <div class="sv-confirmed-text">
                <span class="sv-confirmed-check">Confirmed:</span> {_qtext}
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Generated SQL Panel (with Verified badge) ───────────────────────────────
_current_sql = st.session_state.get("current_sql", "")
if _current_sql:
    st.markdown('<div class="qs-section qs-sql-wrap">', unsafe_allow_html=True)
    _badge = '<span class="sql-verified-badge">Verified</span>' if st.session_state.get("schema_confirmed") else ""
    _sql_label = f'<span class="sql-panel-label">Generated SQL</span>{_badge}'
    with st.expander(_sql_label, expanded=False):
        st.code(_current_sql, language="sql")
    st.markdown("</div>", unsafe_allow_html=True)

# ── Results — Three Tabs: ResultSet | Visualization | Insights ───────────────
if st.session_state.current_results is not None:
    try:
        df_display = pd.DataFrame(st.session_state.current_results)
    except Exception:
        df_display = None

    st.markdown('<div class="qs-section">', unsafe_allow_html=True)

    tab_results, tab_viz, tab_insights = st.tabs(["ResultSet", "Visualization", "Insights"])

    # ── TAB 1: ResultSet ─────────────────────────────────────────────────────
    with tab_results:
        if df_display is not None and not df_display.empty:
            import html as _html_mod
            _num_cols = set(df_display.select_dtypes(include=["number"]).columns)

            _thead = "<tr>"
            for c in df_display.columns:
                _cls = ' class="num-col"' if c in _num_cols else ""
                _thead += f"<th{_cls}>{_html_mod.escape(str(c).upper())}</th>"
            _thead += "</tr>"

            _tbody = ""
            for _, row in df_display.iterrows():
                _tbody += "<tr>"
                for c in df_display.columns:
                    val = row[c]
                    if c in _num_cols:
                        try:
                            _fmt = f"${val:,.0f}" if abs(val) >= 100 else f"{val:g}"
                        except Exception:
                            _fmt = str(val)
                        _tbody += f'<td class="num-col">{_html_mod.escape(_fmt)}</td>'
                    else:
                        _tbody += f'<td class="name-col">{_html_mod.escape(str(val))}</td>'
                _tbody += "</tr>"

            st.markdown(
                f'<table class="qs-result-table"><thead>{_thead}</thead><tbody>{_tbody}</tbody></table>',
                unsafe_allow_html=True,
            )
        else:
            st.info("Query ran successfully but returned no rows.")

    # ── TAB 2: Visualization (bar + pie side by side) ────────────────────────
    with tab_viz:
        if df_display is not None and not df_display.empty:
            _num_cols_list = df_display.select_dtypes(include=["number"]).columns.tolist()
            _cat_cols_list = df_display.select_dtypes(exclude=["number"]).columns.tolist()

            _light = dict(
                template="plotly_white", paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#6B6252", family="Inter, sans-serif"),
                title_font=dict(color="#241F1A", size=14, family="Inter, sans-serif"),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#6B6252")),
                margin=dict(l=32, r=32, t=48, b=36),
            )
            _pie_palette = ["#E4572E", "#0EA5E9", "#8FCC00", "#B18CFF", "#F2A65A"]

            if _cat_cols_list and _num_cols_list:
                _cat, _num = _cat_cols_list[0], _num_cols_list[0]
                _n = len(df_display)
                _bar_clrs = ["#8FCC00"] + ["rgba(14,165,233,0.55)"] * max(0, _n - 1)
                _col_bar, _col_pie = st.columns(2, gap="medium")

                with _col_bar:
                    st.markdown(
                        '<div class="chart-card"><div class="chart-card-header">'
                        '<span class="chart-card-label">Bar chart</span>'
                        '<span class="chart-card-badge ranking">best for ranking</span>'
                        '</div>', unsafe_allow_html=True)
                    _fig_bar = px.bar(df_display, x=_cat, y=_num, title=f"{_num} by {_cat}")
                    _fig_bar.update_traces(marker_color=_bar_clrs)
                    _fig_bar.update_layout(**_light)
                    st.plotly_chart(_fig_bar, use_container_width=True, key="tab_bar")
                    st.markdown("</div>", unsafe_allow_html=True)

                with _col_pie:
                    st.markdown(
                        '<div class="chart-card"><div class="chart-card-header">'
                        '<span class="chart-card-label">Share of total</span>'
                        '<span class="chart-card-badge proportion">best for proportion</span>'
                        '</div>', unsafe_allow_html=True)
                    _fig_pie = px.pie(df_display, names=_cat, values=_num,
                                     title=f"Proportion of {_num}",
                                     color_discrete_sequence=_pie_palette, hole=0.38)
                    _fig_pie.update_layout(**_light)
                    st.plotly_chart(_fig_pie, use_container_width=True, key="tab_pie")
                    st.markdown("</div>", unsafe_allow_html=True)

            elif _num_cols_list:
                _num = _num_cols_list[0]
                _n = len(df_display)
                _bar_clrs = ["#8FCC00"] + ["rgba(14,165,233,0.55)"] * max(0, _n - 1)
                st.markdown(
                    '<div class="chart-card"><div class="chart-card-header">'
                    '<span class="chart-card-label">Distribution</span></div>',
                    unsafe_allow_html=True)
                _fig = px.bar(df_display, x=df_display.index, y=_num, title=f"Distribution of {_num}")
                _fig.update_traces(marker_color=_bar_clrs)
                _fig.update_layout(**_light)
                st.plotly_chart(_fig, use_container_width=True, key="tab_dist")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Data doesn't contain numeric values for charting.")
        else:
            st.info("No data to chart yet — run a query first.")

    # ── TAB 3: Insights (full-width cards) ───────────────────────────────────
    with tab_insights:
        _idata       = st.session_state.get("insight_data") or {}
        _anomaly     = _idata.get("anomaly", "").strip()
        _trend       = _idata.get("trend", "").strip()
        _correlation = _idata.get("correlation", "").strip()
        _raw_insight = _idata.get("insights", "").strip()

        def _render_insight_card(label: str, color: str, text: str):
            st.markdown(
                f'<div class="insight-card">'
                f'<div class="insight-label" style="color:{color};">{label}</div>'
                f'<div class="insight-text">{text}</div></div>',
                unsafe_allow_html=True,
            )

        _any = False
        if _anomaly:
            _render_insight_card("Anomaly", "#E4572E", _anomaly); _any = True
        if _trend:
            _render_insight_card("Trend", "#0EA5E9", _trend); _any = True
        if _correlation:
            _render_insight_card("Correlation", "#8FCC00", _correlation); _any = True
        if not _any:
            if _raw_insight:
                _render_insight_card("Insights", "#6B6252", _raw_insight)
            else:
                st.info("Insights will appear here after a query runs with results.")

    st.markdown("</div>", unsafe_allow_html=True)  # qs-section

# ── Error Display ────────────────────────────────────────────────────────────
if st.session_state.get("last_error"):
    st.error(st.session_state.last_error)

# ── Empty State (only when nothing is happening) ─────────────────────────────
_show_empty = (
    st.session_state.current_results is None
    and not st.session_state.get("last_error")
    and not st.session_state.get("awaiting_approval")
)
if _show_empty:
    st.markdown(
        '<div class="qs-empty">'
        '<h3>No Query Executed</h3>'
        '<p>Type a natural language question above and press '
        '<strong>Run →</strong> to analyze your e-commerce dataset.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
