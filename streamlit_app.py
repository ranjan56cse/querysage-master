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
        import google.auth, google.auth.transport.requests
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


st.set_page_config(page_title="QuerySage", page_icon="❖", layout="wide", initial_sidebar_state="collapsed")

try:
    _r = httpx.get(f"{MASTER_URL}/health", headers=_get_auth_headers(MASTER_URL), timeout=2.0)
    _service_ok = _r.status_code == 200
except Exception:
    _service_ok = False

# ══════════════════════════════════════════════════════════════════════════════
# ── CSS — Professional Design System ─────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ═══ Design Tokens ══════════════════════════════════════════════════ */
:root {
    --bg:       #F7F5F0;
    --surface:  #FFFFFF;
    --surface2: #F4F1EA;
    --border:   #E8E3D8;
    --border2:  #DDD7CA;
    --text:     #1A1714;
    --text2:    #5C5549;
    --text3:    #9C9488;
    --accent:   #E4572E;
    --accent2:  #D14820;
    --neon:     #CFFF3D;
    --neon2:    #B8E635;
    --sky:      #0EA5E9;
    --green:    #16A34A;
    --radius:   16px;
    --radius-sm: 10px;
    --radius-pill: 9999px;
    --shadow-sm:  0 1px 3px rgba(26,23,20,0.04), 0 1px 2px rgba(26,23,20,0.03);
    --shadow-md:  0 4px 16px rgba(26,23,20,0.06), 0 1px 4px rgba(26,23,20,0.04);
    --shadow-lg:  0 8px 32px rgba(26,23,20,0.08), 0 2px 8px rgba(26,23,20,0.04);
    --shadow-xl:  0 16px 48px rgba(26,23,20,0.10), 0 4px 12px rgba(26,23,20,0.05);
    --transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    --max-w:    1120px;
}

/* ═══ Base ═══════════════════════════════════════════════════════════ */
html,body,[class*="css"]{font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif!important}
.stApp{background:var(--bg)!important;color:var(--text)!important}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding:0!important;max-width:100%!important}
section[data-testid="stSidebar"],button[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"]{display:none!important}

/* ═══ Top Bar ════════════════════════════════════════════════════════ */
.qs-topbar{
    background:var(--surface);border-bottom:1px solid var(--border);
    padding:0 40px;height:60px;display:flex;align-items:center;justify-content:space-between;
    position:sticky;top:0;z-index:100;backdrop-filter:blur(12px);
    background:rgba(255,255,255,0.92);
}
.qs-brand{display:flex;align-items:center;gap:12px}
.qs-brand-mark{
    width:36px;height:36px;border-radius:11px;background:linear-gradient(135deg,#CFFF3D 0%,#A8E020 100%);
    display:flex;align-items:center;justify-content:center;
    box-shadow:0 2px 8px rgba(207,255,61,0.3);
}
.qs-brand-mark svg{width:18px;height:18px}
.qs-brand-name{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:20px;color:var(--accent);letter-spacing:-0.4px}
.qs-brand-sep{width:1px;height:24px;background:var(--border);margin:0 4px}
.qs-brand-sub{font-size:13px;font-weight:400;color:var(--text3);letter-spacing:0.2px}
.qs-top-right{display:flex;align-items:center;gap:14px}
.qs-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.qs-dot.on{background:#16A34A;box-shadow:0 0 8px rgba(22,163,74,0.45)}
.qs-dot.off{background:#DC2626;box-shadow:0 0 8px rgba(220,38,38,0.4)}
.qs-status{font-size:12.5px;font-weight:500;color:var(--text2);display:flex;align-items:center;gap:7px}
.qs-db-badge{font-size:12px;font-weight:500;color:var(--text2);background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius-pill);padding:6px 14px}

/* ═══ Hero Search ════════════════════════════════════════════════════ */
.qs-hero{max-width:var(--max-w);margin:0 auto;padding:32px 40px 0}
div[data-testid="stForm"]{
    background:var(--surface)!important;
    border:1.5px solid var(--border)!important;
    border-radius:var(--radius)!important;
    padding:8px 8px 8px 24px!important;
    box-shadow:var(--shadow-md)!important;
    transition:border-color var(--transition),box-shadow var(--transition)!important;
}
div[data-testid="stForm"]:focus-within{
    border-color:var(--accent)!important;
    box-shadow:0 0 0 4px rgba(228,87,46,0.08),var(--shadow-md)!important;
}
div[data-testid="stForm"] [data-testid="stHorizontalBlock"]{align-items:center!important;gap:8px!important;flex-wrap:nowrap!important}
div[data-testid="stForm"] [data-testid="column"]{padding:0!important;min-width:0!important}
div[data-testid="stForm"] [data-baseweb="base-input"],
div[data-testid="stForm"] [data-baseweb="input"]{background:transparent!important;border:none!important;box-shadow:none!important}
div[data-testid="stForm"] input[type="text"]{
    background:transparent!important;border:none!important;box-shadow:none!important;outline:none!important;
    color:var(--text)!important;font-size:16px!important;font-weight:400!important;
    font-family:'Inter',sans-serif!important;padding:12px 8px 12px 0!important;
    caret-color:var(--accent)!important;letter-spacing:-0.1px!important;
}
div[data-testid="stForm"] input[type="text"]::placeholder{color:var(--text3)!important;font-weight:400!important}
div[data-testid="stForm"] label{display:none!important}
div[data-testid="stForm"] [data-testid="stTextInput"]{margin:0!important;padding:0!important}
div[data-testid="stForm"] [data-testid="stTextInput"]>div{margin:0!important}
div[data-testid="stForm"] button[kind="formSubmit"]{
    background:linear-gradient(135deg,#CFFF3D 0%,#B8E635 100%)!important;
    color:var(--text)!important;font-weight:700!important;font-size:14px!important;
    font-family:'Space Grotesk',sans-serif!important;border:none!important;
    border-radius:12px!important;padding:14px 28px!important;
    white-space:nowrap!important;cursor:pointer!important;letter-spacing:0.2px!important;
    box-shadow:0 2px 8px rgba(207,255,61,0.25)!important;
    transition:all var(--transition)!important;
}
div[data-testid="stForm"] button[kind="formSubmit"]:hover{
    transform:translateY(-1px)!important;
    box-shadow:0 4px 16px rgba(207,255,61,0.35)!important;
}

/* ═══ Content Area ═══════════════════════════════════════════════════ */
.qs-content{max-width:var(--max-w);margin:0 auto;padding:0 40px}

/* ═══ HITL Card ══════════════════════════════════════════════════════ */
.hitl-card{
    background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
    overflow:hidden;box-shadow:var(--shadow-md);margin-top:24px;
}
.hitl-header{
    padding:20px 28px;border-bottom:1px solid var(--border);
    background:linear-gradient(135deg,rgba(228,87,46,0.03) 0%,rgba(228,87,46,0.01) 100%);
}
.hitl-badge{
    display:inline-block;font-family:'Space Grotesk',sans-serif;font-size:10.5px;font-weight:700;
    letter-spacing:0.8px;text-transform:uppercase;color:var(--surface);
    background:var(--accent);border-radius:var(--radius-pill);padding:4px 12px;margin-bottom:10px;
}
.hitl-desc{font-size:14px;color:var(--text2);line-height:1.6}
.hitl-desc strong{color:var(--text);font-weight:600}
.hitl-sql-section{border-bottom:1px solid var(--border)}
.hitl-sql-header{
    padding:14px 28px;cursor:pointer;display:flex;align-items:center;gap:8px;
    font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:600;
    letter-spacing:0.6px;text-transform:uppercase;color:var(--text3);user-select:none;
    list-style:none;transition:background var(--transition);
}
.hitl-sql-header:hover{background:rgba(0,0,0,0.015)}
details.hitl-toggle{border:none;margin:0}
details.hitl-toggle summary{list-style:none}
details.hitl-toggle summary::-webkit-details-marker{display:none}
details.hitl-toggle summary::before{
    content:'';display:inline-block;width:0;height:0;
    border-left:5px solid var(--text3);border-top:4px solid transparent;border-bottom:4px solid transparent;
    transition:transform 0.25s ease;margin-right:8px;
}
details.hitl-toggle[open] summary::before{transform:rotate(90deg)}
.hitl-sql-code{
    margin:0 28px 20px;background:#0F172A;border-radius:var(--radius-sm);padding:20px 24px;
    font-family:'JetBrains Mono',monospace;font-size:13.5px;color:#7DD3FC;
    line-height:1.8;white-space:pre-wrap;word-break:break-word;
    max-height:260px;overflow-y:auto;
    box-shadow:inset 0 1px 4px rgba(0,0,0,0.2);
}
.hitl-actions{padding:16px 28px;display:flex;align-items:center;gap:12px;background:var(--surface2)}
/* HITL buttons via Streamlit */
button[data-testid="stBaseButton-primary"]{
    background:linear-gradient(135deg,#CFFF3D 0%,#B8E635 100%)!important;
    color:var(--text)!important;font-weight:700!important;font-size:13.5px!important;
    font-family:'Space Grotesk',sans-serif!important;border:none!important;
    border-radius:var(--radius-sm)!important;padding:12px 28px!important;
    box-shadow:0 2px 8px rgba(207,255,61,0.2)!important;transition:all var(--transition)!important;
}
button[data-testid="stBaseButton-primary"]:hover{transform:translateY(-1px)!important;box-shadow:0 4px 16px rgba(207,255,61,0.3)!important}
button[data-testid="stBaseButton-secondary"]{
    background:var(--surface)!important;color:#DC2626!important;font-weight:600!important;font-size:13px!important;
    border:1.5px solid rgba(220,38,38,0.3)!important;border-radius:var(--radius-sm)!important;
    padding:11px 24px!important;transition:all var(--transition)!important;
}
button[data-testid="stBaseButton-secondary"]:hover{border-color:#DC2626!important;background:rgba(220,38,38,0.04)!important}

/* ═══ Schema Confirmed ═══════════════════════════════════════════════ */
.sv-confirmed{
    background:linear-gradient(135deg,#EFF8FF 0%,#E0F2FE 100%);
    border:1px solid rgba(14,165,233,0.2);border-radius:var(--radius);
    padding:16px 24px;display:flex;align-items:center;gap:14px;margin-top:24px;
}
.sv-check{
    width:32px;height:32px;border-radius:10px;background:rgba(14,165,233,0.1);
    display:flex;align-items:center;justify-content:center;flex-shrink:0;
    font-size:16px;color:var(--sky);
}
.sv-confirmed-label{font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:700;letter-spacing:0.6px;text-transform:uppercase;color:var(--sky)}
.sv-confirmed-text{font-size:14px;color:var(--text);font-weight:500;margin-top:2px}

/* ═══ SQL Expander ═══════════════════════════════════════════════════ */
.qs-sql-section{margin-top:16px}
.qs-sql-section [data-testid="stExpander"]{
    background:var(--surface)!important;border:1px solid var(--border)!important;
    border-radius:var(--radius)!important;overflow:hidden;box-shadow:var(--shadow-sm)!important;
}
.qs-sql-section [data-testid="stExpander"] summary{
    background:var(--surface)!important;padding:14px 20px!important;
    border-radius:var(--radius)!important;
}
.qs-sql-section [data-testid="stExpander"] svg{color:var(--text3)!important;stroke:var(--text3)!important}
.qs-sql-section [data-testid="stExpanderDetails"]{
    background:var(--surface)!important;padding:0 20px 16px!important;
    border-top:1px solid var(--border)!important;
}
.qs-sql-section .stCodeBlock,.qs-sql-section .stCodeBlock pre{
    background:#0F172A!important;border:none!important;border-radius:var(--radius-sm)!important;margin-top:4px!important;
}
.qs-sql-section .stCodeBlock code{
    color:#7DD3FC!important;font-family:'JetBrains Mono',monospace!important;font-size:13px!important;line-height:1.8!important;
}
.sql-label{font-family:'Space Grotesk',sans-serif;font-size:12px;font-weight:600;letter-spacing:0.5px;text-transform:uppercase;color:var(--text3);vertical-align:middle}
.sql-badge{
    font-size:11px;font-weight:600;color:var(--green);
    background:rgba(22,163,74,0.06);border:1px solid rgba(22,163,74,0.18);
    border-radius:var(--radius-pill);padding:3px 12px;
    font-family:'Inter',sans-serif;margin-left:12px;vertical-align:middle;
}

/* ═══ Tabs ═══════════════════════════════════════════════════════════ */
.qs-results{margin-top:28px}
[data-testid="stTabs"] [data-baseweb="tab-list"]{
    background:transparent!important;border-bottom:2px solid var(--border)!important;gap:0!important;
}
[data-testid="stTabs"] button[data-baseweb="tab"]{
    background:transparent!important;color:var(--text3)!important;
    font-family:'Space Grotesk',sans-serif!important;font-weight:600!important;
    font-size:14px!important;border-radius:0!important;
    padding:14px 4px!important;margin-right:32px!important;
    border-bottom:2px solid transparent!important;
    margin-bottom:-2px!important;transition:all var(--transition)!important;
}
[data-testid="stTabs"] button[data-baseweb="tab"]:hover{color:var(--text2)!important}
[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"]{
    color:var(--text)!important;border-bottom:2px solid var(--accent)!important;
}
[data-testid="stTabPanel"]{background:transparent!important;border:none!important;padding:24px 0!important}

/* ═══ ResultSet Table ════════════════════════════════════════════════ */
.qs-table-wrap{
    background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
    overflow:hidden;box-shadow:var(--shadow-sm);
}
.qs-result-table{width:100%;border-collapse:collapse;font-family:'Inter',sans-serif}
.qs-result-table thead tr{background:var(--surface2);border-bottom:2px solid var(--border)}
.qs-result-table th{
    font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:600;
    letter-spacing:0.6px;text-transform:uppercase;color:var(--text3);
    padding:14px 20px;text-align:left;white-space:nowrap;
}
.qs-result-table th.num-col{text-align:right}
.qs-result-table td{
    font-size:14px;color:var(--text2);padding:14px 20px;
    border-top:1px solid var(--border);white-space:nowrap;
    transition:background var(--transition);
}
.qs-result-table td.name-col{color:var(--text);font-weight:500}
.qs-result-table td.num-col{text-align:right;font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:500}
.qs-result-table tbody tr:hover{background:rgba(228,87,46,0.02)}

/* ═══ Chart Cards ════════════════════════════════════════════════════ */
.chart-card{
    background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
    padding:20px 24px;box-shadow:var(--shadow-sm);
    transition:box-shadow var(--transition);
}
.chart-card:hover{box-shadow:var(--shadow-md)}
.chart-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.chart-label{font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:600;letter-spacing:0.6px;text-transform:uppercase;color:var(--text3)}
.chart-badge{font-size:10.5px;font-weight:600;padding:3px 10px;border-radius:var(--radius-pill);font-family:'Inter',sans-serif}
.chart-badge.rank{color:var(--accent);background:rgba(228,87,46,0.06);border:1px solid rgba(228,87,46,0.12)}
.chart-badge.share{color:var(--sky);background:rgba(14,165,233,0.06);border:1px solid rgba(14,165,233,0.12)}

/* ═══ Insight Cards ══════════════════════════════════════════════════ */
.insight-card{
    background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
    padding:20px 24px;margin-bottom:14px;
    border-left:4px solid var(--border);
    box-shadow:var(--shadow-sm);transition:all var(--transition);
}
.insight-card:hover{box-shadow:var(--shadow-md);transform:translateY(-1px)}
.insight-card.anomaly{border-left-color:#E4572E}
.insight-card.trend{border-left-color:#0EA5E9}
.insight-card.correlation{border-left-color:#16A34A}
.insight-card.generic{border-left-color:var(--text3)}
.insight-label{font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:700;letter-spacing:0.6px;text-transform:uppercase;margin-bottom:8px}
.insight-text{font-size:14px;color:var(--text2);line-height:1.65}

/* ═══ Schema Ambiguity ═══════════════════════════════════════════════ */
.sv-card{
    background:linear-gradient(135deg,#EFF8FF 0%,#E0F2FE 100%);
    border:1px solid rgba(14,165,233,0.2);border-radius:var(--radius);
    padding:20px 28px;margin-top:24px;
}

/* ═══ Empty State ════════════════════════════════════════════════════ */
.qs-empty{
    text-align:center;padding:100px 24px 80px;max-width:440px;margin:0 auto;
}
.qs-empty-icon{
    width:64px;height:64px;border-radius:20px;
    background:linear-gradient(135deg,#CFFF3D 0%,#B8E635 100%);
    display:flex;align-items:center;justify-content:center;margin:0 auto 20px;
    box-shadow:0 4px 16px rgba(207,255,61,0.25);
}
.qs-empty-icon svg{width:28px;height:28px}
.qs-empty h3{font-family:'Space Grotesk',sans-serif;color:var(--text);font-weight:600;font-size:18px;margin-bottom:8px}
.qs-empty p{color:var(--text3);font-size:14px;line-height:1.65}
.qs-empty strong{color:var(--accent);font-weight:600}

/* ═══ Loading ════════════════════════════════════════════════════════ */
[data-testid="stSpinner"]>div:first-child{border-top-color:var(--accent)!important;border-right-color:var(--accent)!important;border-bottom-color:rgba(228,87,46,0.15)!important;border-left-color:rgba(228,87,46,0.15)!important}
[data-testid="stSpinner"] p{color:var(--text2)!important;font-size:0.9rem!important;font-weight:500!important}
.qs-loader{
    max-width:var(--max-w);margin:20px auto;padding:18px 28px;
    background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
    display:flex;align-items:center;gap:14px;box-shadow:var(--shadow-sm);
}
@keyframes qs-pulse{0%,80%,100%{opacity:0.15;transform:scale(0.7)}40%{opacity:1;transform:scale(1)}}
.qs-dots{display:flex;gap:5px;align-items:center}
.qs-dot-anim{width:7px;height:7px;border-radius:50%;background:var(--accent);animation:qs-pulse 1.3s infinite ease-in-out}
.qs-dot-anim:nth-child(2){animation-delay:0.15s}
.qs-dot-anim:nth-child(3){animation-delay:0.3s}
.qs-loader-text{font-size:14px;color:var(--text2);font-weight:500}

/* ═══ Global Code Blocks ═════════════════════════════════════════════ */
.stCodeBlock,.stCodeBlock pre,.stCodeBlock code{background-color:#0F172A!important;border:none!important;border-radius:var(--radius-sm)!important}
.stCodeBlock code{color:#7DD3FC!important}
hr{border-color:var(--border)!important;margin:20px 0!important}
div[data-testid="stNotification"]{background:var(--surface)!important;border-left-color:var(--border)!important;color:var(--text)!important;border-radius:var(--radius-sm)!important}

/* ═══ Animations ═════════════════════════════════════════════════════ */
@keyframes qs-rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
[data-testid="stTabs"]{animation:qs-rise 0.45s cubic-bezier(0.16,1,0.3,1) both}
.hitl-card{animation:qs-rise 0.35s cubic-bezier(0.16,1,0.3,1) both}
.sv-confirmed{animation:qs-rise 0.35s 0.05s cubic-bezier(0.16,1,0.3,1) both}
</style>
""", unsafe_allow_html=True)

# ── Session State ──────────────────────────────────────────────────────────────
_defaults = {
    "messages": [], "session_id": str(uuid.uuid4()), "user_id": "streamlit_user",
    "awaiting_approval": False, "interrupted_sql": "", "current_results": None,
    "current_chart_type": "table", "current_sql": "", "current_insights": "",
    "follow_up_suggestions": [], "schema_verification": None, "insight_data": None,
    "last_error": None, "last_query_text": "", "schema_confirmed": False,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


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

    with st.spinner("Analyzing…"):
        p_loader = st.empty()
        result_holder = {}
        _sid, _uid = st.session_state.session_id, st.session_state.user_id
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
        _msgs = [(0, "Analyzing your question…"), (1.5, "Building query against schema…"), (3.2, "Executing on Neon Postgres…")]
        t0 = time.time()
        while thread.is_alive():
            elapsed = time.time() - t0
            _label = _msgs[0][1]
            for _t, _m in _msgs:
                if elapsed >= _t: _label = _m
            p_loader.markdown(
                f'<div class="qs-loader"><div class="qs-dots">'
                f'<div class="qs-dot-anim"></div><div class="qs-dot-anim"></div><div class="qs-dot-anim"></div></div>'
                f'<span class="qs-loader-text">{_label}</span></div>', unsafe_allow_html=True)
            time.sleep(0.1)
        p_loader.empty()

    st.session_state.last_error = None
    if "error" in result_holder:
        st.session_state.last_error = f"Failed to reach Orchestrator: {result_holder['error']}"
    elif "resp" in result_holder:
        resp = result_holder["resp"]
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
                st.session_state.last_query_text = query_text
                st.session_state.current_sql = ""
                if "```sql" in output:
                    try: st.session_state.current_sql = output.split("```sql")[1].split("```")[0].strip()
                    except Exception: pass
                if not st.session_state.current_sql:
                    _dsql = data.get("sql") or data.get("generated_sql") or ""
                    if _dsql: st.session_state.current_sql = _clean_sql_text(_dsql)
                raw_insight = data.get("insight_data") or {}
                if isinstance(raw_insight, dict) and raw_insight:
                    st.session_state.insight_data = {
                        "anomaly": raw_insight.get("anomaly", ""), "trend": raw_insight.get("trend", ""),
                        "correlation": raw_insight.get("correlation", ""), "insights": raw_insight.get("insights", ""),
                    }
                else:
                    st.session_state.insight_data = {"anomaly": "", "trend": "", "correlation": "", "insights": clean_markdown_tables(output)}
                raw_sv = data.get("schema_verification")
                if isinstance(raw_sv, dict) and raw_sv.get("is_ambiguous"):
                    st.session_state.schema_verification = raw_sv
                    st.session_state.schema_confirmed = False
                else:
                    _sv_kw = ("did you mean", "ambiguous", "corrected query", "suggested phrasing", "could mean", "clarif")
                    if any(kw in output.lower() for kw in _sv_kw):
                        st.session_state.schema_verification = {"is_ambiguous": True, "original_query": query_text, "corrected_query": None, "explanation": output[:400], "alternatives": []}
                        st.session_state.schema_confirmed = False
                    else:
                        st.session_state.schema_verification = None
                        st.session_state.schema_confirmed = True
                st.session_state.messages.append({"role": "assistant", "content": st.session_state.current_insights, "status": "success", "sql_results": sql_results, "chart_type": chart_type})
                st.session_state.awaiting_approval = False
                st.session_state.interrupted_sql = ""
            elif status == "interrupted":
                st.session_state.awaiting_approval = True
                raw_msg = data.get("message", "")
                st.session_state.interrupted_sql = _clean_sql_text(raw_msg)
                st.session_state.messages.append({"role": "assistant", "status": "interrupted", "content": f"SQL requires approval:\n```sql\n{st.session_state.interrupted_sql}\n```"})
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

_status_cls = "on" if _service_ok else "off"
_status_txt = "Connected" if _service_ok else "Offline"
st.markdown(f"""
<div class="qs-topbar">
    <div class="qs-brand">
        <div class="qs-brand-mark">
            <svg viewBox="0 0 24 24" fill="none" stroke="#1A1714" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 3l1.912 5.813a2 2 0 001.272 1.272L21 12l-5.813 1.912a2 2 0 00-1.272 1.272L12 21l-1.912-5.813a2 2 0 00-1.272-1.272L3 12l5.813-1.912a2 2 0 001.275-1.275z"/>
            </svg>
        </div>
        <span class="qs-brand-name">QuerySage</span>
        <span class="qs-brand-sep"></span>
        <span class="qs-brand-sub">Agentic Analytics</span>
    </div>
    <div class="qs-top-right">
        <div class="qs-status"><span class="qs-dot {_status_cls}"></span>{_status_txt}</div>
        <div class="qs-db-badge">Neon Postgres</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Search ───────────────────────────────────────────────────────────────────
st.markdown('<div class="qs-hero">', unsafe_allow_html=True)
with st.form(key="search_form", clear_on_submit=False):
    _cq, _cb = st.columns([9, 1])
    with _cq:
        query_input = st.text_input("query", placeholder="Ask a question about your data in plain English…", label_visibility="collapsed")
    with _cb:
        run_clicked = st.form_submit_button("Run →")
st.markdown("</div>", unsafe_allow_html=True)

active_query = query_input.strip() if run_clicked else ""

# ── HITL ─────────────────────────────────────────────────────────────────────
if st.session_state.awaiting_approval:
    import html as _html
    _safe_sql = _html.escape(st.session_state.interrupted_sql or "")

    st.markdown(f"""
<div class="qs-content">
<div class="hitl-card">
    <div class="hitl-header">
        <div class="hitl-badge">Approval Required</div>
        <div class="hitl-desc">The following SQL query will be executed against
        <strong>Neon Postgres — Production</strong>. Please review before approving.</div>
    </div>
    <details class="hitl-toggle" open>
        <summary class="hitl-sql-header">Review Generated SQL</summary>
        <div class="hitl-sql-code">{_safe_sql}</div>
    </details>
</div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="qs-content">', unsafe_allow_html=True)
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

# ── Schema Ambiguity ─────────────────────────────────────────────────────────
_sv = st.session_state.get("schema_verification")
if _sv and _sv.get("is_ambiguous"):
    _sv_explanation = _sv.get("explanation") or ""
    _sv_corrected = _sv.get("corrected_query")

    st.markdown('<div class="qs-content">', unsafe_allow_html=True)
    st.markdown('<div class="sv-card">', unsafe_allow_html=True)
    st.markdown('<div class="sv-confirmed-label">Schema Verification — Ambiguity Detected</div>', unsafe_allow_html=True)
    if _sv_explanation:
        _disp = _sv_explanation if len(_sv_explanation) <= 280 else _sv_explanation[:277] + "…"
        st.markdown(f'<div style="font-size:14px;color:var(--text2);line-height:1.6;margin:8px 0 14px">{_disp}</div>', unsafe_allow_html=True)
    if _sv_corrected:
        if st.button(f"Confirm & Run", key="sv_confirm_run", type="primary"):
            st.session_state.schema_verification = None
            submit_query(_sv_corrected)
            st.rerun()
    if st.button("Dismiss", key="sv_dismiss"):
        st.session_state.schema_verification = None
        st.rerun()
    st.markdown("</div></div>", unsafe_allow_html=True)

# ── Schema Confirmed + SQL ───────────────────────────────────────────────────
if st.session_state.get("schema_confirmed") and st.session_state.get("last_query_text"):
    import html as _html_esc
    _qtext = _html_esc.escape(st.session_state.last_query_text)
    st.markdown(f"""
<div class="qs-content">
    <div class="sv-confirmed">
        <div class="sv-check">✓</div>
        <div>
            <div class="sv-confirmed-label">Schema Verified</div>
            <div class="sv-confirmed-text">{_qtext}</div>
        </div>
    </div>
</div>""", unsafe_allow_html=True)

_current_sql = st.session_state.get("current_sql", "")
if _current_sql:
    st.markdown('<div class="qs-content qs-sql-section">', unsafe_allow_html=True)
    _badge = '<span class="sql-badge">Verified</span>' if st.session_state.get("schema_confirmed") else ""
    with st.expander(f'<span class="sql-label">Generated SQL</span>{_badge}', expanded=False):
        st.code(_current_sql, language="sql")
    st.markdown("</div>", unsafe_allow_html=True)

# ── Results Tabs ─────────────────────────────────────────────────────────────
if st.session_state.current_results is not None:
    try:
        df_display = pd.DataFrame(st.session_state.current_results)
    except Exception:
        df_display = None

    st.markdown('<div class="qs-content qs-results">', unsafe_allow_html=True)
    tab_results, tab_viz, tab_insights = st.tabs(["ResultSet", "Visualization", "Insights"])

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
                        try: _fmt = f"${val:,.0f}" if abs(val) >= 100 else f"{val:g}"
                        except Exception: _fmt = str(val)
                        _tbody += f'<td class="num-col">{_html_mod.escape(_fmt)}</td>'
                    else:
                        _tbody += f'<td class="name-col">{_html_mod.escape(str(val))}</td>'
                _tbody += "</tr>"
            st.markdown(f'<div class="qs-table-wrap"><table class="qs-result-table"><thead>{_thead}</thead><tbody>{_tbody}</tbody></table></div>', unsafe_allow_html=True)
        else:
            st.info("Query ran successfully but returned no rows.")

    with tab_viz:
        if df_display is not None and not df_display.empty:
            _num_cols_list = df_display.select_dtypes(include=["number"]).columns.tolist()
            _cat_cols_list = df_display.select_dtypes(exclude=["number"]).columns.tolist()
            _light = dict(
                template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#5C5549", family="Inter, sans-serif", size=12),
                title_font=dict(color="#1A1714", size=15, family="Inter, sans-serif"),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#5C5549")),
                margin=dict(l=40, r=40, t=52, b=40),
            )
            _pie_palette = ["#E4572E", "#0EA5E9", "#8FCC00", "#B18CFF", "#F2A65A", "#14B8A6"]
            if _cat_cols_list and _num_cols_list:
                _cat, _num = _cat_cols_list[0], _num_cols_list[0]
                _n = len(df_display)
                _bar_clrs = ["#8FCC00"] + ["rgba(14,165,233,0.5)"] * max(0, _n - 1)
                _c1, _c2 = st.columns(2, gap="medium")
                with _c1:
                    st.markdown('<div class="chart-card"><div class="chart-header"><span class="chart-label">Bar Chart</span><span class="chart-badge rank">ranking</span></div>', unsafe_allow_html=True)
                    fig = px.bar(df_display, x=_cat, y=_num, title=f"{_num} by {_cat}")
                    fig.update_traces(marker_color=_bar_clrs)
                    fig.update_layout(**_light)
                    st.plotly_chart(fig, use_container_width=True, key="bar")
                    st.markdown("</div>", unsafe_allow_html=True)
                with _c2:
                    st.markdown('<div class="chart-card"><div class="chart-header"><span class="chart-label">Share of Total</span><span class="chart-badge share">proportion</span></div>', unsafe_allow_html=True)
                    fig2 = px.pie(df_display, names=_cat, values=_num, title=f"Proportion of {_num}", color_discrete_sequence=_pie_palette, hole=0.4)
                    fig2.update_layout(**_light)
                    st.plotly_chart(fig2, use_container_width=True, key="pie")
                    st.markdown("</div>", unsafe_allow_html=True)
            elif _num_cols_list:
                _num = _num_cols_list[0]
                _n = len(df_display)
                _bar_clrs = ["#8FCC00"] + ["rgba(14,165,233,0.5)"] * max(0, _n - 1)
                st.markdown('<div class="chart-card"><div class="chart-header"><span class="chart-label">Distribution</span></div>', unsafe_allow_html=True)
                fig = px.bar(df_display, x=df_display.index, y=_num, title=f"Distribution of {_num}")
                fig.update_traces(marker_color=_bar_clrs)
                fig.update_layout(**_light)
                st.plotly_chart(fig, use_container_width=True, key="dist")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Data doesn't contain numeric values for charting.")
        else:
            st.info("No data to chart yet — run a query first.")

    with tab_insights:
        _idata = st.session_state.get("insight_data") or {}
        _anomaly = _idata.get("anomaly", "").strip()
        _trend = _idata.get("trend", "").strip()
        _correlation = _idata.get("correlation", "").strip()
        _raw_insight = _idata.get("insights", "").strip()
        _any = False
        if _anomaly:
            st.markdown(f'<div class="insight-card anomaly"><div class="insight-label" style="color:#E4572E">Anomaly</div><div class="insight-text">{_anomaly}</div></div>', unsafe_allow_html=True)
            _any = True
        if _trend:
            st.markdown(f'<div class="insight-card trend"><div class="insight-label" style="color:#0EA5E9">Trend</div><div class="insight-text">{_trend}</div></div>', unsafe_allow_html=True)
            _any = True
        if _correlation:
            st.markdown(f'<div class="insight-card correlation"><div class="insight-label" style="color:#16A34A">Correlation</div><div class="insight-text">{_correlation}</div></div>', unsafe_allow_html=True)
            _any = True
        if not _any:
            if _raw_insight:
                st.markdown(f'<div class="insight-card generic"><div class="insight-label" style="color:var(--text3)">Insights</div><div class="insight-text">{_raw_insight}</div></div>', unsafe_allow_html=True)
            else:
                st.info("Insights will appear here after a query runs with results.")

    st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.get("last_error"):
    st.error(st.session_state.last_error)

_show_empty = (
    st.session_state.current_results is None
    and not st.session_state.get("last_error")
    and not st.session_state.get("awaiting_approval")
)
if _show_empty:
    st.markdown("""
<div class="qs-empty">
    <div class="qs-empty-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="#1A1714" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 3l1.912 5.813a2 2 0 001.272 1.272L21 12l-5.813 1.912a2 2 0 00-1.272 1.272L12 21l-1.912-5.813a2 2 0 00-1.272-1.272L3 12l5.813-1.912a2 2 0 001.275-1.275z"/>
        </svg>
    </div>
    <h3>Ask anything about your data</h3>
    <p>Type a natural language question above and press <strong>Run →</strong> to get instant SQL-powered answers with visualizations and insights.</p>
</div>
""", unsafe_allow_html=True)
