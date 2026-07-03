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
    """Return Bearer token headers for Vertex AI Agent Runtime calls."""
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


# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QuerySage",
    page_icon="\u2756",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ─── Typography & Base ───────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, sans-serif !important;
}
.stApp {
    background-color: #0F172A !important;
    color: #F1F5F9 !important;
}
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
.block-container {
    padding-top: 0 !important;
    padding-bottom: 40px !important;
    max-width: 100% !important;
}

/* ─── Sidebar ─────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: #0F172A !important;
    border-right: 1px solid #1E293B !important;
}
/* Suppress Streamlit's default text colors inside sidebar */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] small,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #94A3B8 !important; }

/* Input fields */
section[data-testid="stSidebar"] input {
    background-color: #1E293B !important;
    border: 1px solid #334155 !important;
    color: #F1F5F9 !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
}
section[data-testid="stSidebar"] input:focus {
    border-color: #475569 !important;
    box-shadow: none !important;
}
section[data-testid="stSidebar"] input:disabled {
    background-color: #0F172A !important;
    color: #334155 !important;
    border-color: #1E293B !important;
}

/* "New Session" pill button */
section[data-testid="stSidebar"] .stButton > button {
    background-color: transparent !important;
    color: #64748B !important;
    border: 1px solid #334155 !important;
    border-radius: 9999px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    width: 100% !important;
    padding: 8px 16px !important;
    transition: border-color 0.15s, color 0.15s !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #475569 !important;
    color: #94A3B8 !important;
    background-color: rgba(255,255,255,0.03) !important;
}

/* Sidebar brand block */
.sb-brand {
    padding: 20px 0 16px;
    border-bottom: 1px solid #1E293B;
    margin-bottom: 20px;
}
.sb-brand-name {
    font-size: 1.35rem;
    font-weight: 800;
    color: #E4572E !important;
    letter-spacing: -0.3px;
    display: block;
    line-height: 1.2;
}
.sb-brand-sub {
    font-size: 0.78rem;
    font-weight: 500;
    color: #64748B !important;
    display: block;
    margin-top: 6px;
    line-height: 1.4;
}
.sb-brand-version {
    font-size: 0.68rem;
    font-weight: 500;
    color: #334155 !important;
    letter-spacing: 0.06em;
    display: block;
    margin-top: 3px;
}

/* Section labels */
.sb-section-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #334155 !important;
    margin-bottom: 10px;
    display: block;
}

/* Health status pill */
.sb-health-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 5px 0;
}
.sb-health-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
}
.sb-health-name {
    font-size: 0.8rem;
    color: #64748B !important;
}

/* Divider */
.sb-divider {
    border: none;
    border-top: 1px solid #1E293B;
    margin: 16px 0;
}

/* About footer */
.sb-about {
    padding: 14px 0 8px;
    border-top: 1px solid #1E293B;
    margin-top: 20px;
}
.sb-about-text {
    font-size: 0.72rem;
    color: #334155 !important;
    line-height: 1.55;
}
.sb-about-accent {
    color: #E4572E !important;
    font-weight: 600;
}


/* ─── Top Bar ─────────────────────────────────────────────────────────── */
.qs-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 13px 36px;
    background: #1E293B;
    border-bottom: 1px solid #334155;
    margin-bottom: 0;
}
.qs-brand {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1.55rem;
    font-weight: 800;
    color: #E4572E;
    letter-spacing: -0.5px;
    user-select: none;
}
.qs-brand .qs-brand-rest { color: #F1F5F9; font-weight: 600; }
.qs-db-pill {
    font-size: 0.78rem;
    font-weight: 500;
    color: #94A3B8;
    background: #0F172A;
    border: 1px solid #334155;
    border-radius: 9999px;
    padding: 5px 14px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.qs-db-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #16A34A;
    display: inline-block;
}

/* ─── Search Pill ──────────────────────────────────────────────────────── */
.qs-search-section {
    max-width: 900px;
    margin: 32px auto 0;
    padding: 0 24px;
}
.qs-search-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 10px;
}
div[data-testid="stForm"] {
    background: #1E293B !important;
    border: 1.5px solid #334155 !important;
    border-radius: 9999px !important;
    padding: 4px 6px 4px 22px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3) !important;
}
div[data-testid="stForm"]:focus-within {
    border-color: #2DD4BF !important;
    box-shadow: 0 0 0 3px rgba(45,212,191,0.12), 0 2px 12px rgba(0,0,0,0.3) !important;
}
div[data-testid="stForm"] [data-testid="stHorizontalBlock"] {
    align-items: center !important;
    gap: 4px !important;
    flex-wrap: nowrap !important;
}
div[data-testid="stForm"] [data-testid="column"] { padding: 0 !important; min-width: 0 !important; }
div[data-testid="stForm"] [data-baseweb="base-input"],
div[data-testid="stForm"] [data-baseweb="input"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
div[data-testid="stForm"] input[type="text"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    color: #F1F5F9 !important;
    font-size: 1rem !important;
    font-family: 'Inter', sans-serif !important;
    padding: 12px 8px 12px 0 !important;
    caret-color: #2DD4BF !important;
}
div[data-testid="stForm"] input[type="text"]::placeholder { color: #475569 !important; }
div[data-testid="stForm"] label { display: none !important; }
div[data-testid="stForm"] [data-testid="stTextInput"] { margin: 0 !important; padding: 0 !important; }
div[data-testid="stForm"] [data-testid="stTextInput"] > div { margin: 0 !important; }
div[data-testid="stForm"] button {
    background-color: #CFFF3D !important;
    color: #0F172A !important;
    font-weight: 800 !important;
    font-size: 0.9rem !important;
    font-family: 'Inter', sans-serif !important;
    border: none !important;
    border-radius: 9999px !important;
    padding: 10px 26px !important;
    white-space: nowrap !important;
    cursor: pointer !important;
    transition: opacity 0.15s, transform 0.1s !important;
    letter-spacing: 0.01em !important;
}
div[data-testid="stForm"] button:hover { opacity: 0.87 !important; transform: scale(1.02) !important; }
div[data-testid="stForm"] button:active { transform: scale(0.98) !important; }

/* ─── Suggestion Chips ─────────────────────────────────────────────────── */
.qs-chips-section { max-width: 900px; margin: 14px auto 28px; padding: 0 24px; }
.qs-chips-label {
    font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase;
    color: #334155; margin-bottom: 8px;
}
.qs-chips-row .stButton > button {
    background: transparent !important;
    border: 1px solid #334155 !important;
    color: #94A3B8 !important;
    border-radius: 9999px !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    padding: 5px 14px !important;
    transition: border-color 0.15s, color 0.15s, background 0.15s !important;
    white-space: nowrap !important;
}
.qs-chips-row .stButton > button:hover {
    border-color: #2DD4BF !important;
    color: #2DD4BF !important;
    background: rgba(45,212,191,0.06) !important;
}

/* ─── HITL Approval Card ─────────────────────────────────────────────────── */
.hitl-card {
    background: #1C1917;
    border: 1px solid rgba(220, 38, 38, 0.3);
    border-radius: 16px;
    padding: 22px 26px 20px;
    margin: 24px auto;
    max-width: 900px;
    box-shadow: 0 0 0 1px rgba(220,38,38,0.08), 0 4px 24px rgba(0,0,0,0.5);
}
.hitl-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
}
.hitl-title {
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #DC2626;
}
.hitl-subtitle {
    font-size: 0.82rem;
    color: #94A3B8;
    line-height: 1.55;
    margin-bottom: 16px;
}
.hitl-sql-block {
    background: #0F172A;
    border: 1px solid rgba(220,38,38,0.2);
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 20px;
    font-family: 'JetBrains Mono','Fira Code','Cascadia Code',monospace;
    font-size: 0.86rem;
    color: #E4572E;
    line-height: 1.65;
    white-space: pre-wrap;
    word-break: break-word;
}
/* Approve pill — neon green */
.hitl-approve .stButton > button {
    background-color: #CFFF3D !important;
    color: #0F172A !important;
    font-weight: 800 !important;
    font-size: 0.88rem !important;
    border: none !important;
    border-radius: 9999px !important;
    padding: 10px 24px !important;
    transition: opacity 0.15s, transform 0.1s !important;
    letter-spacing: 0.01em !important;
}
.hitl-approve .stButton > button:hover {
    opacity: 0.87 !important;
    transform: scale(1.02) !important;
}
.hitl-approve .stButton > button:active { transform: scale(0.98) !important; }
/* Reject pill — red outline */
.hitl-reject .stButton > button {
    background: transparent !important;
    color: #DC2626 !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    border: 1.5px solid rgba(220,38,38,0.5) !important;
    border-radius: 9999px !important;
    padding: 10px 24px !important;
    transition: border-color 0.15s, background 0.15s !important;
}
.hitl-reject .stButton > button:hover {
    border-color: #DC2626 !important;
    background: rgba(220,38,38,0.07) !important;
}

/* ─── Schema Verification Card ─────────────────────────────────────────── */
.sv-card {
    background: #0C4A6E;
    border: 1px solid rgba(14,165,233,0.3);
    border-radius: 16px;
    padding: 16px 20px;
    max-width: 900px;
    margin: 0 auto 24px;
}
.sv-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.sv-badge {
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase; color: #0EA5E9;
}
.sv-explanation { font-size: 0.88rem; color: #94A3B8; line-height: 1.55; margin-bottom: 12px; }
.sv-suggestion-box {
    background: #082F49;
    border: 1px solid rgba(14,165,233,0.2);
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 14px;
    font-size: 0.85rem;
    color: #E4572E;
    font-family: 'Inter', monospace;
    font-weight: 500;
}
.sv-alt-label {
    font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase;
    color: #475569; margin-bottom: 8px;
}
.sv-card .stButton > button {
    background: transparent !important;
    border: 1px solid #0EA5E9 !important;
    color: #0EA5E9 !important;
    border-radius: 9999px !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    padding: 5px 16px !important;
    transition: background 0.15s, color 0.15s !important;
}
.sv-card .stButton > button:hover {
    background: rgba(14,165,233,0.12) !important; color: #38BDF8 !important;
}
.sv-confirm .stButton > button {
    background-color: #CFFF3D !important;
    color: #0F172A !important;
    font-weight: 800 !important;
    border: none !important;
    border-radius: 9999px !important;
    padding: 10px 24px !important;
    font-size: 0.9rem !important;
}
.sv-confirm .stButton > button:hover { opacity: 0.88 !important; background-color: #CFFF3D !important; }

/* ─── SQL Panel (expander) ──────────────────────────────────────────────── */
.qs-sql-wrap [data-testid="stExpander"] {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    border-radius: 16px !important;
    max-width: 900px;
    margin: 0 auto 24px;
    overflow: hidden;
}
.qs-sql-wrap [data-testid="stExpander"] summary,
.qs-sql-wrap details summary {
    background: #1E293B !important;
    padding: 12px 18px !important;
    cursor: pointer !important;
    list-style: none !important;
    border-radius: 16px !important;
}
.qs-sql-wrap [data-testid="stExpander"] svg { color: #475569 !important; stroke: #475569 !important; }
.qs-sql-wrap [data-testid="stExpanderDetails"] {
    background: #1E293B !important;
    padding: 0 18px 14px !important;
}
.qs-sql-wrap .stCodeBlock,
.qs-sql-wrap .stCodeBlock pre {
    background: #0F172A !important;
    border: none !important;
    border-radius: 10px !important;
    margin-top: 4px !important;
}
.qs-sql-wrap .stCodeBlock code {
    color: #E4572E !important;
    font-family: 'JetBrains Mono','Fira Code','Cascadia Code',monospace !important;
    font-size: 0.88rem !important;
    line-height: 1.6 !important;
}
.sql-verified-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(228,87,46,0.15);
    border: 1px solid rgba(228,87,46,0.35);
    color: #E4572E;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border-radius: 9999px;
    padding: 2px 8px;
    vertical-align: middle;
    margin-left: 8px;
}
.sql-panel-label {
    font-size: 0.7rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: #64748B; vertical-align: middle;
}

/* ─── Three-Tab Layout ─────────────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #334155 !important;
    gap: 4px !important;
}
[data-testid="stTabs"] button[data-baseweb="tab"] {
    background: transparent !important;
    color: #64748B !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    border-radius: 6px 6px 0 0 !important;
    padding: 10px 18px !important;
    transition: color 0.15s !important;
}
[data-testid="stTabs"] button[data-baseweb="tab"]:hover {
    color: #94A3B8 !important;
    background: rgba(255,255,255,0.04) !important;
}
[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
    color: #ffffff !important;
    border-bottom: 2.5px solid #CFFF3D !important;
}
[data-testid="stTabPanel"] {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    border-top: none !important;
    border-radius: 0 0 12px 12px !important;
    padding: 24px !important;
}

/* ─── DataFrame (HuggingFace-style compact columns) ────────────────────── */
[data-testid="stDataFrame"] {
    background: #0F172A !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}
/* Auto-fit column widths to content */
[data-testid="stDataFrame"] table { table-layout: auto !important; }
[data-testid="stDataFrame"] th {
    white-space: nowrap !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: #64748B !important;
    background: #1E293B !important;
    padding: 10px 14px !important;
    border-bottom: 1px solid #334155 !important;
}
[data-testid="stDataFrame"] td {
    white-space: nowrap !important;
    padding: 8px 14px !important;
    font-size: 0.85rem !important;
    color: #F1F5F9 !important;
    border-bottom: 1px solid #1E293B !important;
}
/* Glide data grid (Streamlit's internal) — fit to content */
[data-testid="stDataFrame"] [data-testid="glideDataEditor"],
[data-testid="stDataFrame"] canvas {
    min-width: 0 !important;
}

/* ─── Code Blocks (global) ─────────────────────────────────────────────── */
.stCodeBlock, .stCodeBlock pre, .stCodeBlock code {
    background-color: #0F172A !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}
.stCodeBlock code { color: #E4572E !important; }
hr { border-color: #1E293B !important; margin: 16px 0 !important; }
div[data-testid="stNotification"] {
    background-color: #1E293B !important;
    border-left-color: #334155 !important;
    color: #F1F5F9 !important;
    border-radius: 8px !important;
}

/* ─── Chart Cards (Graph tab) ──────────────────────────────────────────── */
.chart-card {
    background: #0F172A;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 8px;
}
.chart-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
}
.chart-card-label {
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase; color: #64748B;
}
.chart-card-badge {
    font-size: 0.62rem; font-weight: 600;
    padding: 2px 9px;
    border-radius: 9999px;
    color: #94A3B8;
    border: 1px solid #334155;
    background: #1E293B;
}

/* ─── Insight Cards (Insight tab) ──────────────────────────────────────── */
.insight-card {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    background: #0F172A;
    border: 1px solid #1E293B;
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 12px;
}
.insight-icon-box {
    width: 36px; height: 36px;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
    flex-shrink: 0;
    margin-top: 2px;
}
.insight-content { flex: 1; min-width: 0; }
.insight-label {
    font-size: 0.65rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
    margin-bottom: 5px;
}
.insight-text { font-size: 0.875rem; color: #94A3B8; line-height: 1.6; }
.insight-followup-pills .stButton > button {
    background: transparent !important;
    border: 1px solid #334155 !important;
    color: #94A3B8 !important;
    border-radius: 9999px !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    padding: 5px 14px !important;
    transition: border-color 0.15s, color 0.15s, background 0.15s !important;
    white-space: normal !important;
    text-align: left !important;
}
.insight-followup-pills .stButton > button:hover {
    border-color: #CFFF3D !important;
    color: #CFFF3D !important;
    background: rgba(207,255,61,0.05) !important;
}
.followup-section-label {
    font-size: 0.65rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: #334155;
    margin-bottom: 10px;
    margin-top: 24px;
}

/* ─── Empty State ──────────────────────────────────────────────────────── */
.qs-empty {
    text-align: center; padding: 80px 24px;
    color: #334155; max-width: 480px; margin: 0 auto;
}
.qs-empty-icon { font-size: 3rem; margin-bottom: 16px; opacity: 0.5; }
.qs-empty h3 { color: #475569; font-weight: 600; margin-bottom: 8px; font-size: 1.1rem; }
.qs-empty p { color: #334155; font-size: 0.88rem; line-height: 1.6; }
.qs-empty strong { color: #CFFF3D; }

/* ─── Loading States ────────────────────────────────────────────────────── */

/* Override Streamlit built-in spinner to orange */
[data-testid="stSpinner"] > div:first-child {
    border-top-color:    #E4572E !important;
    border-right-color:  #E4572E !important;
    border-bottom-color: rgba(228,87,46,0.2) !important;
    border-left-color:   rgba(228,87,46,0.2) !important;
}
[data-testid="stSpinner"] p {
    color: #94A3B8 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}

/* Custom wand loading container below query bar */
.wand-loading-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 16px;
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 16px;
    margin: 16px auto;
    max-width: 900px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}
@keyframes spin-wand {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
.wand-icon {
    display: inline-block;
    animation: spin-wand 2s linear infinite;
    font-size: 1.3rem;
}
.wand-text {
    font-size: 0.92rem;
    color: #F1F5F9;
    font-weight: 600;
}

/* Simulated SQL Panel loading block */
.loading-sql-panel {
    background: #1E293B;
    border: 1px dashed rgba(228, 87, 46, 0.4);
    border-radius: 16px;
    max-width: 900px;
    margin: 0 auto 24px;
    padding: 20px;
}
.loading-sql-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
}
.loading-sql-text {
    font-size: 0.88rem;
    color: #94A3B8;
    display: flex;
    align-items: center;
    gap: 10px;
}

/* Simulated Execution Panel loading block */
.loading-execution-panel {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 16px;
    max-width: 900px;
    margin: 0 auto 24px;
    padding: 36px;
    text-align: center;
}

/* st.status() dark-theme overrides */
[data-testid="stStatus"],
[data-testid="stStatusWidget"] {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    border-radius: 12px !important;
    max-width: 900px !important;
    margin: 0 auto 20px !important;
}
[data-testid="stStatus"] summary,
[data-testid="stStatusWidget"] summary {
    background: #1E293B !important;
    color: #94A3B8 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 12px 18px !important;
    border-radius: 12px !important;
    border: none !important;
    list-style: none !important;
}
/* Spinner inside running status */
[data-testid="stStatusWidget"][data-state="running"] svg circle {
    stroke: #E4572E !important;
}
/* Completed tick */
[data-testid="stStatusWidget"][data-state="complete"] summary {
    color: #16A34A !important;
}
[data-testid="stStatusWidget"][data-state="complete"] svg {
    color: #16A34A !important; stroke: #16A34A !important;
}
/* Error state */
[data-testid="stStatusWidget"][data-state="error"] summary {
    color: #DC2626 !important;
}
[data-testid="stStatusWidget"][data-state="error"] svg {
    color: #DC2626 !important; stroke: #DC2626 !important;
}
/* Inner content panel */
[data-testid="stStatus"] [data-testid="stVerticalBlock"],
[data-testid="stStatusWidget"] [data-testid="stVerticalBlock"] {
    background: #1E293B !important;
    padding: 0 18px 14px !important;
}

/* Pulsing animated dot row — shown inside status steps */
@keyframes qs-pulse {
    0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
    40%            { opacity: 1;   transform: scale(1);   }
}
.qs-loading-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    background: #0F172A;
    border: 1px solid #1E293B;
    border-radius: 9px;
    margin: 6px 0;
}
.qs-loading-dots {
    display: flex;
    gap: 5px;
    align-items: center;
    flex-shrink: 0;
}
.qs-loading-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #E4572E;
    animation: qs-pulse 1.2s infinite ease-in-out;
}
.qs-loading-dot:nth-child(2) { animation-delay: 0.2s; }
.qs-loading-dot:nth-child(3) { animation-delay: 0.4s; }
.qs-loading-step {
    font-size: 0.72rem;
    color: #334155;
    margin-left: auto;
    font-variant-numeric: tabular-nums;
    letter-spacing: 0.04em;
}

/* Fade-in reveal for tabs when results arrive */
@keyframes qs-fadein {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0);   }
}
[data-testid="stTabs"] {
    animation: qs-fadein 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
}
</style>
""",
    unsafe_allow_html=True,
)

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
    """Send query_text to the Master Orchestrator and update session state."""
    st.session_state.messages.append({"role": "user", "content": query_text})

    # Clear old results/errors/etc to prevent layout shifts
    st.session_state.current_results = None
    st.session_state.current_sql = ""
    st.session_state.current_insights = ""
    st.session_state.schema_verification = None
    st.session_state.insight_data = None

    # Custom wrapper class wrapper
    st.markdown('<div class="query-processing-wrapper">', unsafe_allow_html=True)
    
    with st.spinner("Analyzing your question..."):
        # Wand animation below query bar
        p_wand = st.empty()
        
        # Spacer
        p_spacer = st.empty()
        
        # SQL Panel Loader
        p_sql = st.empty()
        
        # Execution Loader
        p_results = st.empty()

        # Target response storage
        result_holder = {}

        # Capture values BEFORE spawning the thread (threads can't access st.session_state)
        _sid = st.session_state.session_id
        _uid = st.session_state.user_id
        _headers = _get_auth_headers(MASTER_URL)

        def make_request():
            try:
                payload = {
                    "session_id": _sid,
                    "user_id":    _uid,
                    "user_query": query_text,
                }
                resp = httpx.post(
                    f"{MASTER_URL}/chat",
                    json=payload,
                    headers=_headers,
                    timeout=90.0,
                )
                result_holder["resp"] = resp
            except Exception as e:
                result_holder["error"] = e

        import threading
        import time

        thread = threading.Thread(target=make_request)
        thread.start()

        start_time = time.time()
        while thread.is_alive():
            elapsed = time.time() - start_time

            # 1. Subtle loading animation below query bar (spinning wand)
            p_wand.markdown(
                """
                <div class="wand-loading-container">
                    <span class="wand-icon">🪄</span>
                    <span class="wand-text">Analyzing your question...</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            # 2. SQL collapsible panel placeholder
            if elapsed >= 1.5:
                p_sql.markdown(
                    """
                    <div class="loading-sql-panel">
                        <div class="loading-sql-header">
                            <span style="font-size:1.1rem; color:#E4572E;">⚡</span>
                            <span class="sql-panel-label" style="color:#E4572E; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; font-size:0.7rem;">Generated SQL</span>
                            <span class="sql-verified-badge" style="background-color:rgba(228,87,46,0.1); border-color:rgba(228,87,46,0.3); color:#E4572E; font-size:0.65rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; border-radius:9999px; padding:2px 8px;">⏳ Generating</span>
                        </div>
                        <div class="loading-sql-text">
                            <div class="qs-loading-dots">
                                <div class="qs-loading-dot"></div>
                                <div class="qs-loading-dot"></div>
                                <div class="qs-loading-dot"></div>
                            </div>
                            <span>Writing query against verified schema...</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                p_sql.empty()

            # 3. Execution placeholder in results area
            if elapsed >= 3.2:
                p_results.markdown(
                    """
                    <div class="loading-execution-panel">
                        <div style="display: flex; justify-content: center; align-items: center; gap: 8px; margin-bottom: 16px;">
                            <div class="qs-loading-dot" style="width:8px; height:8px;"></div>
                            <div class="qs-loading-dot" style="width:8px; height:8px; animation-delay:0.2s;"></div>
                            <div class="qs-loading-dot" style="width:8px; height:8px; animation-delay:0.4s;"></div>
                        </div>
                        <div style="font-size: 0.9rem; color: #94A3B8; font-weight: 500;">
                            Executing against Neon Postgres...
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                p_results.empty()

            time.sleep(0.1)

        # Clear loaders
        p_wand.empty()
        p_sql.empty()
        p_results.empty()
        p_spacer.empty()

    st.markdown('</div>', unsafe_allow_html=True)

    # Process response
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

                # Extract SQL from markdown fences
                st.session_state.current_sql = ""
                if "```sql" in output:
                    try:
                        parts = output.split("```sql")
                        st.session_state.current_sql = parts[1].split("```")[0].strip()
                    except Exception:
                        pass

                # Follow-up suggestions
                suggestions = data.get("follow_up_suggestions") or []
                st.session_state.follow_up_suggestions = suggestions[:4]

                # Structured insight_data from the agent's InsightOutput
                raw_insight = data.get("insight_data") or {}
                if isinstance(raw_insight, dict) and raw_insight:
                    st.session_state.insight_data = {
                        "anomaly":             raw_insight.get("anomaly", ""),
                        "trend":               raw_insight.get("trend", ""),
                        "correlation":         raw_insight.get("correlation", ""),
                        "insights":            raw_insight.get("insights", ""),
                        "follow_up_questions": raw_insight.get("follow_up_questions", []) or suggestions,
                    }
                else:
                    st.session_state.insight_data = {
                        "anomaly": "", "trend": "", "correlation": "",
                        "insights": clean_markdown_tables(output),
                        "follow_up_questions": suggestions,
                    }

                # Schema verification node output
                raw_sv = data.get("schema_verification")
                if isinstance(raw_sv, dict) and raw_sv.get("is_ambiguous"):
                    st.session_state.schema_verification = raw_sv
                else:
                    _sv_keywords = (
                        "did you mean", "ambiguous", "corrected query",
                        "suggested phrasing", "could mean", "clarif",
                    )
                    if any(kw in output.lower() for kw in _sv_keywords):
                        st.session_state.schema_verification = {
                            "is_ambiguous":   True,
                            "original_query": query_text,
                            "corrected_query": None,
                            "explanation":    output[:400],
                            "alternatives":   [],
                        }
                    else:
                        st.session_state.schema_verification = None

                st.session_state.messages.append(
                    {
                        "role":        "assistant",
                        "content":     st.session_state.current_insights,
                        "status":      "success",
                        "sql_results": sql_results,
                        "chart_type":  chart_type,
                    }
                )
                st.session_state.awaiting_approval = False
                st.session_state.interrupted_sql   = ""

            elif status == "interrupted":
                st.session_state.awaiting_approval = True
                st.session_state.interrupted_sql   = data.get(
                    "message", "RequestInput Approval Required"
                )
                st.session_state.messages.append(
                    {
                        "role":    "assistant",
                        "content": (
                            "Neon SQL execution confirmation required:\n\n"
                            f"```sql\n{st.session_state.interrupted_sql}\n```"
                        ),
                        "status":  "interrupted",
                    }
                )

            elif status == "blocked":
                output = data.get("output", "Blocked by safety checks.")
                st.session_state.messages.append(
                    {"role": "assistant", "content": output, "status": "blocked"}
                )
                st.session_state.awaiting_approval   = False
                st.session_state.interrupted_sql     = ""
                st.session_state.current_insights    = output
                st.session_state.current_results     = None
                st.session_state.follow_up_suggestions = []
                st.session_state.insight_data        = None

        else:
            st.session_state.last_error = f"Endpoint error {resp.status_code}: {resp.text}"


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:

    # ── Brand block ─────────────────────────────────────────────────
    st.markdown(
        '<div class="sb-brand">'
        '<span class="sb-brand-name">\u2756 QuerySage</span>'
        '<span class="sb-brand-sub">Natural language analytics for your e-commerce data</span>'
        '<span class="sb-brand-version">v1.0 \u00b7 Canvas Edition</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Session Controls ─────────────────────────────────────────────
    st.markdown(
        '<span class="sb-section-label">Session Controls</span>',
        unsafe_allow_html=True,
    )
    st.text_input(
        "User ID",
        key="user_id",
        label_visibility="visible",
    )
    st.text_input(
        "Session ID",
        value=st.session_state.session_id,
        key="session_id_input",
        disabled=True,
        label_visibility="visible",
    )
    if st.button("\u21ba  New Session", use_container_width=True):
        for _k, _v in _defaults.items():
            st.session_state[_k] = _v
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    # ── Services Status ──────────────────────────────────────────────
    st.markdown('<hr class="sb-divider">', unsafe_allow_html=True)
    st.markdown(
        '<span class="sb-section-label">Services Status</span>',
        unsafe_allow_html=True,
    )

    # Only check the main orchestrator \u2014 business users just need green/red
    try:
        _r = httpx.get(
            f"{MASTER_URL}/health",
            headers=_get_auth_headers(MASTER_URL),
            timeout=2.0,
        )
        _all_ok = _r.status_code == 200
    except Exception:
        _all_ok = False

    if _all_ok:
        st.markdown(
            '<div class="sb-health-row" style="gap:10px;">'
            '<span class="sb-health-dot" style="background:#16A34A;'
            'box-shadow:0 0 6px #16A34A66;width:9px;height:9px;"></span>'
            '<span class="sb-health-name" style="color:#94A3B8;font-size:0.85rem;">'
            'Connected &amp; Ready</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="sb-health-row" style="gap:10px;">'
            '<span class="sb-health-dot" style="background:#DC2626;'
            'box-shadow:0 0 6px #DC262666;width:9px;height:9px;"></span>'
            '<span class="sb-health-name" style="color:#94A3B8;font-size:0.85rem;">'
            'Service Unavailable</span></div>',
            unsafe_allow_html=True,
        )

    # ── About footer ─────────────────────────────────────────────────
    st.markdown(
        '<div class="sb-about">'
        '<div class="sb-about-text">'
        'Built for the<br>'
        '<span class="sb-about-accent">Kaggle 5-Day AI Agents Course</span><br>'
        '<span style="color:#1E293B;">\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500</span><br>'
        'Neon Postgres \u00b7 Google ADK \u00b7 Vertex AI'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )



# ── Top Bar ────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="qs-topbar">
    <div class="qs-brand">
        \u2756&nbsp;QuerySage<span class="qs-brand-rest">&nbsp;Canvas</span>
    </div>
    <div class="qs-db-pill">
        <span class="qs-db-dot"></span>
        analytics_db1 &middot; Neon Postgres
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ── Search Pill ────────────────────────────────────────────────────────────────
st.markdown('<div class="qs-search-section">', unsafe_allow_html=True)
st.markdown('<div class="qs-search-label">\U0001f50d &nbsp;Ask a question</div>', unsafe_allow_html=True)

with st.form(key="search_form", clear_on_submit=True):
    _col_q, _col_btn = st.columns([9, 1])
    with _col_q:
        query_input = st.text_input(
            "query", value="",
            placeholder="Ask a business question in plain English\u2026",
            label_visibility="collapsed",
        )
    with _col_btn:
        run_clicked = st.form_submit_button("Run \u2192")

st.markdown("</div>", unsafe_allow_html=True)

active_query = query_input.strip() if run_clicked else ""

# ── HITL Approval ──────────────────────────────────────────────────────────────
if st.session_state.awaiting_approval:
    import html as _html
    _safe_sql = _html.escape(st.session_state.interrupted_sql or "")

    st.markdown('<div class="hitl-card">', unsafe_allow_html=True)

    # Header row: shield icon + uppercase red label
    st.markdown(
        '<div class="hitl-header">'
        '<span style="font-size:1.3rem;">\U0001f6e1\ufe0f</span>'
        '<span class="hitl-title">SQL Execution Approval Required</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Subtitle / explanation
    st.markdown(
        '<div class="hitl-subtitle">'
        'The following SQL will be executed against '
        '<strong style="color:#F1F5F9;">Neon Postgres</strong>. '
        'Review carefully before approving.'
        '</div>',
        unsafe_allow_html=True,
    )

    # SQL displayed in orange monospace on near-black background
    st.markdown(
        f'<div class="hitl-sql-block">{_safe_sql}</div>',
        unsafe_allow_html=True,
    )

    # Action buttons — Approve (neon green) | Reject (red outline)
    _b1, _b2, _pad = st.columns([1.5, 1, 4])
    with _b1:
        st.markdown('<div class="hitl-approve">', unsafe_allow_html=True)
        if st.button("\u26a1  Approve & Execute", use_container_width=True, key="hitl_approve"):
            st.session_state.awaiting_approval = False
            submit_query("yes")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with _b2:
        st.markdown('<div class="hitl-reject">', unsafe_allow_html=True)
        if st.button("\u2715  Reject", use_container_width=True, key="hitl_reject"):
            st.session_state.awaiting_approval = False
            submit_query("no")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # hitl-card

elif active_query:
    submit_query(active_query)
    st.rerun()

# ── Suggestion Chips ───────────────────────────────────────────────────────────
if st.session_state.follow_up_suggestions:
    st.markdown('<div class="qs-chips-section">', unsafe_allow_html=True)
    st.markdown('<div class="qs-chips-label">Suggested follow-ups</div>', unsafe_allow_html=True)
    st.markdown('<div class="qs-chips-row">', unsafe_allow_html=True)
    _suggestions = st.session_state.follow_up_suggestions[:4]
    _chip_cols   = st.columns(len(_suggestions))
    for _i, (_col, _sug) in enumerate(zip(_chip_cols, _suggestions)):
        with _col:
            _label = f"\u2197 {_sug}" if len(_sug) <= 48 else f"\u2197 {_sug[:45]}\u2026"
            if st.button(_label, key=f"chip_{_i}"):
                submit_query(_sug)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── Schema Verification Card ───────────────────────────────────────────────────
_sv = st.session_state.get("schema_verification")
if _sv and _sv.get("is_ambiguous"):
    _sv_explanation  = _sv.get("explanation") or ""
    _sv_corrected    = _sv.get("corrected_query")
    _sv_alternatives = _sv.get("alternatives") or []

    st.markdown('<div class="sv-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="sv-header">'
        '<span style="font-size:1.1rem;">\U0001f6e1\ufe0f</span>'
        '<span class="sv-badge">Schema Verification</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    if _sv_explanation:
        _disp = _sv_explanation if len(_sv_explanation) <= 280 else _sv_explanation[:277] + "\u2026"
        st.markdown(f'<div class="sv-explanation">{_disp}</div>', unsafe_allow_html=True)

    if _sv_corrected:
        st.markdown(
            '<div style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;'
            'text-transform:uppercase;color:#475569;margin-bottom:6px;">'
            'Suggested phrasing</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="sv-suggestion-box">{_sv_corrected}</div>', unsafe_allow_html=True)

    if _sv_alternatives:
        st.markdown('<div class="sv-alt-label">Choose an interpretation</div>', unsafe_allow_html=True)
        _alt_cols = st.columns(min(len(_sv_alternatives), 4))
        for _ai, (_acol, _alt) in enumerate(zip(_alt_cols, _sv_alternatives[:4])):
            with _acol:
                if st.button(_alt, key=f"sv_alt_{_ai}"):
                    st.session_state.schema_verification = None
                    submit_query(_alt)
                    st.rerun()

    if _sv_corrected:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="sv-confirm">', unsafe_allow_html=True)
        _clabel = (
            f"Confirm & Run: '{_sv_corrected[:60]}\u2026'"
            if len(_sv_corrected) > 60
            else f"Confirm & Run: '{_sv_corrected}'"
        )
        if st.button(_clabel, key="sv_confirm_run"):
            st.session_state.schema_verification = None
            submit_query(_sv_corrected)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Dismiss  \u2715", key="sv_dismiss"):
        st.session_state.schema_verification = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── Generated SQL Panel ────────────────────────────────────────────────────────
_current_sql = st.session_state.get("current_sql", "")
if _current_sql:
    st.markdown('<div class="qs-sql-wrap">', unsafe_allow_html=True)
    _sql_label = (
        '\u26a1\ufe0f  '
        '<span class="sql-panel-label">Generated SQL</span>'
        '<span class="sql-verified-badge">\u2713&nbsp;Verified</span>'
    )
    with st.expander(_sql_label, expanded=True):
        st.code(_current_sql, language="sql")
    st.markdown("</div>", unsafe_allow_html=True)

# ── Results Workspace — 3 Tabs ─────────────────────────────────────────────────
if st.session_state.current_results is not None:

    try:
        df_display = pd.DataFrame(st.session_state.current_results)
    except Exception:
        df_display = None

    tab_results, tab_graph, tab_insight = st.tabs(
        ["\U0001f4cb  ResultSet", "\U0001f4ca  Graph", "\U0001f4a1  Insight"]
    )

    # ── TAB 1: ResultSet ──────────────────────────────────────────────────────
    with tab_results:
        if df_display is not None and not df_display.empty:
            # Build column config with widths sized to content
            _col_cfg = {}
            for c in df_display.columns:
                # Estimate width: max of header length and longest value
                _max_len = max(
                    len(str(c)),
                    df_display[c].astype(str).str.len().max() if len(df_display) > 0 else 0,
                )
                _width = max(80, min(400, _max_len * 10 + 40))
                if c in df_display.select_dtypes(include=["number"]).columns:
                    _col_cfg[c] = st.column_config.NumberColumn(
                        format="%g", width=_width,
                    )
                else:
                    _col_cfg[c] = st.column_config.TextColumn(width=_width)

            st.dataframe(
                df_display,
                use_container_width=False,
                height=min(420, 38 + len(df_display) * 36),
                column_config=_col_cfg,
            )
        else:
            st.info("Query ran successfully but returned no rows.")

    # ── TAB 2: Graph ──────────────────────────────────────────────────────────
    with tab_graph:
        if df_display is not None and not df_display.empty:
            _num_cols = df_display.select_dtypes(include=["number"]).columns.tolist()
            _cat_cols = df_display.select_dtypes(exclude=["number"]).columns.tolist()

            _dark = dict(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8", family="Inter, sans-serif"),
                title_font=dict(color="#F1F5F9", size=14, family="Inter, sans-serif"),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8")),
                margin=dict(l=32, r=32, t=48, b=36),
            )
            _pie_palette = ["#E4572E", "#0EA5E9", "#8FCC00", "#B18CFF", "#F2A65A"]

            if _cat_cols and _num_cols:
                _cat, _num = _cat_cols[0], _num_cols[0]
                _n         = len(df_display)
                _bar_clrs  = ["#2DD4BF"] + ["rgba(14,165,233,0.55)"] * max(0, _n - 1)

                _col_bar, _col_pie = st.columns(2, gap="medium")

                with _col_bar:
                    st.markdown(
                        '<div class="chart-card">'
                        '<div class="chart-card-header">'
                        '<span class="chart-card-label">Bar Chart</span>'
                        '<span class="chart-card-badge">best for ranking</span>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    _fig_bar = px.bar(df_display, x=_cat, y=_num, title=f"{_num} by {_cat}")
                    _fig_bar.update_traces(marker_color=_bar_clrs)
                    _fig_bar.update_layout(**_dark)
                    st.plotly_chart(_fig_bar, use_container_width=True, key="tab_bar")
                    st.markdown("</div>", unsafe_allow_html=True)

                with _col_pie:
                    st.markdown(
                        '<div class="chart-card">'
                        '<div class="chart-card-header">'
                        '<span class="chart-card-label">Share of Total</span>'
                        '<span class="chart-card-badge">best for proportion</span>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    _fig_pie = px.pie(
                        df_display, names=_cat, values=_num,
                        title=f"Proportion of {_num}",
                        color_discrete_sequence=_pie_palette,
                        hole=0.38,
                    )
                    _fig_pie.update_layout(**_dark)
                    st.plotly_chart(_fig_pie, use_container_width=True, key="tab_pie")
                    st.markdown("</div>", unsafe_allow_html=True)

            elif _num_cols:
                _num      = _num_cols[0]
                _n        = len(df_display)
                _bar_clrs = ["#2DD4BF"] + ["rgba(14,165,233,0.55)"] * max(0, _n - 1)
                st.markdown(
                    '<div class="chart-card">'
                    '<div class="chart-card-header">'
                    '<span class="chart-card-label">Distribution</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                _fig_dist = px.bar(
                    df_display, x=df_display.index, y=_num,
                    title=f"Distribution of {_num}",
                )
                _fig_dist.update_traces(marker_color=_bar_clrs)
                _fig_dist.update_layout(**_dark)
                st.plotly_chart(_fig_dist, use_container_width=True, key="tab_dist")
                st.markdown("</div>", unsafe_allow_html=True)

            else:
                st.info("Data doesn\u2019t contain numeric values for charting.")
        else:
            st.info("No data to chart yet \u2014 run a query first.")

    # ── TAB 3: Insight ────────────────────────────────────────────────────────
    with tab_insight:
        _idata       = st.session_state.get("insight_data") or {}
        _anomaly     = _idata.get("anomaly", "").strip()
        _trend       = _idata.get("trend", "").strip()
        _correlation = _idata.get("correlation", "").strip()
        _raw_insight = _idata.get("insights", "").strip()
        _followups   = (
            _idata.get("follow_up_questions") or
            st.session_state.get("follow_up_suggestions", [])
        )

        def _render_insight_card(icon: str, label: str, color: str, bg_tint: str, text: str):
            st.markdown(
                f'<div class="insight-card">'
                f'<div class="insight-icon-box" style="background:{bg_tint};">{icon}</div>'
                f'<div class="insight-content">'
                f'<div class="insight-label" style="color:{color};">{label}</div>'
                f'<div class="insight-text">{text}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        _any_shown = False

        if _anomaly:
            _render_insight_card(
                "\u26a0\ufe0f", "Anomaly Detection", "#E4572E",
                "rgba(228,87,46,0.12)", _anomaly,
            )
            _any_shown = True

        if _trend:
            _render_insight_card(
                "\U0001f4c8", "Trend Analysis", "#0EA5E9",
                "rgba(14,165,233,0.12)", _trend,
            )
            _any_shown = True

        if _correlation:
            _render_insight_card(
                "\U0001f517", "Correlation Discovery", "#2DD4BF",
                "rgba(45,212,191,0.12)", _correlation,
            )
            _any_shown = True

        if not _any_shown:
            if _raw_insight:
                _render_insight_card(
                    "\U0001f4a1", "Agent Insights", "#94A3B8",
                    "rgba(148,163,184,0.10)", _raw_insight,
                )
            else:
                st.info("Insights will appear here after a query runs with results.")

        # Follow-up suggestions inside Insight tab
        if _followups:
            st.markdown(
                '<div class="followup-section-label">Suggested follow-ups</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="insight-followup-pills">', unsafe_allow_html=True)
            _fu_list = list(_followups)[:4]
            _fu_cols = st.columns(min(len(_fu_list), 2))
            for _fi, _fq in enumerate(_fu_list):
                with _fu_cols[_fi % 2]:
                    _fu_label = f"\u2197 {_fq}" if len(_fq) <= 55 else f"\u2197 {_fq[:52]}\u2026"
                    if st.button(_fu_label, key=f"insight_fu_{_fi}"):
                        submit_query(_fq)
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# ── Persistent Error Display ──────────────────────────────────────────────────
if st.session_state.get("last_error"):
    st.error(st.session_state.last_error)

if st.session_state.current_results is None and not st.session_state.get("last_error"):
    st.markdown(
        """
<div class="qs-empty">
    <div class="qs-empty-icon">\u2756</div>
    <h3>No Query Executed</h3>
    <p>
        Type a natural language question above and press
        <strong>Run \u2192</strong> to analyze your e-commerce dataset.
    </p>
</div>
""",
        unsafe_allow_html=True,
    )
