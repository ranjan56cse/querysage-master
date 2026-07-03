"""Generate QuerySage Deployment Journey PDF — self-learning guide with diagrams."""

import math
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.graphics.shapes import (
    Drawing, Rect, String, Line, Polygon, Circle, Ellipse,
)

WIDTH, HEIGHT = A4
MARGIN = 45

# ─── Colors ───
C_PRIMARY = colors.HexColor("#1e3a5f")
C_ACCENT = colors.HexColor("#2563eb")
C_GREEN = colors.HexColor("#16a34a")
C_ORANGE = colors.HexColor("#ea580c")
C_RED = colors.HexColor("#dc2626")
C_PURPLE = colors.HexColor("#7c3aed")
C_TEAL = colors.HexColor("#0d9488")
C_PINK = colors.HexColor("#db2777")
C_AMBER = colors.HexColor("#d97706")
C_LIGHTBG = colors.HexColor("#f1f5f9")
C_WHITE = colors.white
C_GRAY = colors.HexColor("#64748b")
C_DARKTEXT = colors.HexColor("#334155")
C_LIGHTRED = colors.HexColor("#fef2f2")
C_LIGHTGREEN = colors.HexColor("#f0fdf4")
C_LIGHTBLUE = colors.HexColor("#eff6ff")
C_LIGHTYELLOW = colors.HexColor("#fffbeb")

styles = getSampleStyleSheet()

title_style = ParagraphStyle("T", parent=styles["Title"], fontSize=26, textColor=C_PRIMARY, spaceAfter=4, alignment=TA_CENTER)
subtitle_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=11, textColor=C_GRAY, alignment=TA_CENTER, spaceAfter=18)
h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=18, textColor=C_PRIMARY, spaceBefore=16, spaceAfter=8)
h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, textColor=C_ACCENT, spaceBefore=12, spaceAfter=6)
body = ParagraphStyle("B", parent=styles["Normal"], fontSize=10, leading=14, textColor=C_DARKTEXT, alignment=TA_JUSTIFY, spaceAfter=6)
code_style = ParagraphStyle("Code", parent=styles["Normal"], fontSize=9, fontName="Courier", textColor=colors.HexColor("#1e293b"), backColor=C_LIGHTBG, leading=12, spaceAfter=6, leftIndent=12, rightIndent=12, spaceBefore=4)
caption_style = ParagraphStyle("Cap", parent=styles["Normal"], fontSize=9, textColor=C_GRAY, alignment=TA_CENTER, spaceBefore=4, spaceAfter=12)
issue_style = ParagraphStyle("Issue", parent=styles["Normal"], fontSize=10, leading=13, textColor=C_RED, spaceAfter=2, leftIndent=8)
fix_style = ParagraphStyle("Fix", parent=styles["Normal"], fontSize=10, leading=13, textColor=C_GREEN, spaceAfter=6, leftIndent=8)
concept_style = ParagraphStyle("Concept", parent=styles["Normal"], fontSize=10, leading=14, textColor=C_DARKTEXT, spaceAfter=6, leftIndent=12, borderColor=C_ACCENT, borderWidth=1, borderPadding=6)


# ─── Drawing helpers ───
def _box(g, x, y, w, h, fill, label, fs=8, tc=C_WHITE):
    g.add(Rect(x, y, w, h, fillColor=fill, strokeColor=None, rx=6, ry=6))
    lines = label.split("\n")
    lh = fs + 2
    sy = y + h / 2 + (len(lines) - 1) * lh / 2
    for i, ln in enumerate(lines):
        g.add(String(x + w / 2, sy - i * lh - fs * 0.35, ln, fontSize=fs, fillColor=tc, textAnchor="middle", fontName="Helvetica-Bold" if fs >= 9 else "Helvetica"))

def _arrow_down(g, x, y1, y2, clr=C_GRAY):
    g.add(Line(x, y1, x, y2 + 6, strokeColor=clr, strokeWidth=1.5))
    g.add(Polygon(points=[x - 4, y2 + 6, x + 4, y2 + 6, x, y2], fillColor=clr, strokeColor=None))

def _arrow_right(g, x1, x2, y, clr=C_GRAY):
    g.add(Line(x1, y, x2 - 6, y, strokeColor=clr, strokeWidth=1.5))
    g.add(Polygon(points=[x2 - 6, y - 4, x2 - 6, y + 4, x2, y], fillColor=clr, strokeColor=None))

def _arrow_left(g, x1, x2, y, clr=C_GRAY):
    g.add(Line(x1, y, x2 + 6, y, strokeColor=clr, strokeWidth=1.5))
    g.add(Polygon(points=[x2 + 6, y - 4, x2 + 6, y + 4, x2, y], fillColor=clr, strokeColor=None))

def _dashed_line(g, x1, y1, x2, y2, clr=C_GRAY):
    g.add(Line(x1, y1, x2, y2, strokeColor=clr, strokeWidth=1, strokeDashArray=[4, 2]))


# ═══════════════════════════════════════════
# DIAGRAM 1: Deployment Pipeline Flow
# ═══════════════════════════════════════════
def build_deploy_pipeline():
    d = Drawing(500, 200)
    d.add(Rect(0, 0, 500, 200, fillColor=C_LIGHTBG, strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.5, rx=8, ry=8))
    d.add(String(250, 182, "Agent Deployment Pipeline", fontSize=12, fillColor=C_PRIMARY, textAnchor="middle", fontName="Helvetica-Bold"))

    # Row 1: Dev flow
    _box(d, 10, 130, 75, 35, C_PURPLE, "Local Dev\nAntigravity", 7)
    _arrow_right(d, 85, 105, 147, C_GRAY)
    _box(d, 105, 130, 75, 35, C_ACCENT, "agents-cli\nsetup", 7)
    _arrow_right(d, 180, 200, 147, C_GRAY)
    _box(d, 200, 130, 80, 35, C_ORANGE, "scaffold\nenhance", 7)
    _arrow_right(d, 280, 300, 147, C_GRAY)
    _box(d, 300, 130, 75, 35, C_AMBER, "uv lock\n+ dry-run", 7)
    _arrow_right(d, 375, 395, 147, C_GRAY)
    _box(d, 395, 130, 90, 35, C_GREEN, "agents-cli\ndeploy", 7)

    # Row 2: What each step produces
    _arrow_down(d, 47, 130, 95, C_PURPLE)
    d.add(String(47, 82, "agent.py", fontSize=7, fillColor=C_GRAY, textAnchor="middle"))
    d.add(String(47, 72, "fast_api_app.py", fontSize=7, fillColor=C_GRAY, textAnchor="middle"))

    _arrow_down(d, 142, 130, 95, C_ACCENT)
    d.add(String(142, 82, "ADK skills", fontSize=7, fillColor=C_GRAY, textAnchor="middle"))
    d.add(String(142, 72, "installed", fontSize=7, fillColor=C_GRAY, textAnchor="middle"))

    _arrow_down(d, 240, 130, 95, C_ORANGE)
    d.add(String(240, 82, "agent_runtime", fontSize=7, fillColor=C_GRAY, textAnchor="middle"))
    d.add(String(240, 72, "_app.py", fontSize=7, fillColor=C_GRAY, textAnchor="middle"))
    d.add(String(240, 62, "deployment_", fontSize=7, fillColor=C_GRAY, textAnchor="middle"))
    d.add(String(240, 52, "metadata.json", fontSize=7, fillColor=C_GRAY, textAnchor="middle"))

    _arrow_down(d, 337, 130, 95, C_AMBER)
    d.add(String(337, 82, "uv.lock", fontSize=7, fillColor=C_GRAY, textAnchor="middle"))
    d.add(String(337, 72, "config validated", fontSize=7, fillColor=C_GRAY, textAnchor="middle"))

    _arrow_down(d, 440, 130, 95, C_GREEN)
    d.add(String(440, 82, "Reasoning", fontSize=7, fillColor=C_GRAY, textAnchor="middle"))
    d.add(String(440, 72, "Engine on", fontSize=7, fillColor=C_GRAY, textAnchor="middle"))
    d.add(String(440, 62, "Vertex AI", fontSize=7, fillColor=C_GRAY, textAnchor="middle"))

    # Bottom label
    d.add(String(250, 15, "Each step done via Antigravity prompts — no manual Docker/gcloud needed", fontSize=8, fillColor=C_GRAY, textAnchor="middle"))

    return d


# ═══════════════════════════════════════════
# DIAGRAM 2: Cloud Architecture (deployed)
# ═══════════════════════════════════════════
def build_cloud_architecture():
    d = Drawing(500, 340)
    d.add(Rect(0, 0, 500, 340, fillColor=C_LIGHTBG, strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.5, rx=8, ry=8))
    d.add(String(250, 318, "QuerySage Cloud Architecture (Deployed)", fontSize=12, fillColor=C_PRIMARY, textAnchor="middle", fontName="Helvetica-Bold"))

    # GCP boundary box
    d.add(Rect(15, 40, 470, 260, fillColor=None, strokeColor=C_ACCENT, strokeWidth=1, strokeDashArray=[6, 3], rx=8, ry=8))
    d.add(String(250, 285, "Google Cloud Platform", fontSize=9, fillColor=C_ACCENT, textAnchor="middle", fontName="Helvetica-Bold"))

    # Agent Runtime boundary
    d.add(Rect(25, 130, 300, 145, fillColor=colors.HexColor("#eff6ff"), strokeColor=C_ACCENT, strokeWidth=0.5, rx=6, ry=6))
    d.add(String(175, 260, "Agent Runtime (Vertex AI)", fontSize=8, fillColor=C_ACCENT, textAnchor="middle", fontName="Helvetica-Bold"))

    # 3 Reasoning Engines
    _box(d, 35, 210, 90, 35, C_GREEN, "Gatekeeper\nReasoning Engine", 7)
    _box(d, 140, 210, 90, 35, C_ORANGE, "SQL Engine\nReasoning Engine", 7)
    _box(d, 35, 150, 195, 40, C_PRIMARY, "Master Orchestrator\nReasoning Engine (ADK 2.0 Workflow)", 8)

    # Arrows: Master → Gatekeeper, Master → SQL Engine
    _arrow_right(d, 132, 140, 230, C_GREEN)
    d.add(Line(132, 190, 132, 230, strokeColor=C_GREEN, strokeWidth=1))
    d.add(Line(185, 190, 185, 210, strokeColor=C_ORANGE, strokeWidth=1))

    # Cloud Run boundary
    d.add(Rect(340, 195, 140, 65, fillColor=colors.HexColor("#faf5ff"), strokeColor=C_PURPLE, strokeWidth=0.5, rx=6, ry=6))
    d.add(String(410, 248, "Cloud Run", fontSize=8, fillColor=C_PURPLE, textAnchor="middle", fontName="Helvetica-Bold"))
    _box(d, 350, 210, 120, 35, C_PURPLE, "Streamlit UI\nPublic URL", 8)

    # Arrow: Streamlit → Master
    _arrow_left(d, 350, 230, 227, C_ACCENT)
    d.add(String(290, 233, "REST + Auth", fontSize=7, fillColor=C_ACCENT, textAnchor="middle"))

    # Cloud Trace / Logging
    _box(d, 340, 140, 140, 35, C_TEAL, "Cloud Trace +\nCloud Logging", 8)
    _dashed_line(d, 230, 170, 340, 157, C_TEAL)

    # Neon DB (external)
    _box(d, 340, 55, 140, 35, colors.HexColor("#0d9488"), "Neon Postgres\n(External Cloud DB)", 8)
    _arrow_down(d, 132, 150, 100, C_TEAL)
    d.add(Line(132, 100, 132, 72, strokeColor=C_TEAL, strokeWidth=1.5))
    _arrow_right(d, 132, 340, 72, C_TEAL)

    # User
    d.add(Circle(410, 16, 12, fillColor=C_PURPLE, strokeColor=None))
    d.add(String(410, 12, "User", fontSize=7, fillColor=C_WHITE, textAnchor="middle", fontName="Helvetica-Bold"))
    d.add(Line(410, 28, 410, 210, strokeColor=C_PURPLE, strokeWidth=1, strokeDashArray=[4, 3]))

    # Google AI
    _box(d, 35, 55, 120, 35, C_PINK, "Google AI Studio\nGemini API", 8)
    _dashed_line(d, 155, 72, 185, 150, C_PINK)

    return d


# ═══════════════════════════════════════════
# DIAGRAM 3: Auth Flow
# ═══════════════════════════════════════════
def build_auth_flow():
    d = Drawing(500, 130)
    d.add(Rect(0, 0, 500, 130, fillColor=C_LIGHTYELLOW, strokeColor=C_AMBER, strokeWidth=0.5, rx=6, ry=6))
    d.add(String(250, 112, "Google Cloud Authentication Flow", fontSize=11, fillColor=C_AMBER, textAnchor="middle", fontName="Helvetica-Bold"))

    _box(d, 10, 55, 80, 35, C_PURPLE, "gcloud auth\nlogin", 7)
    _arrow_right(d, 90, 115, 72, C_GRAY)
    _box(d, 115, 55, 80, 35, C_ACCENT, "application-\ndefault login", 7)
    _arrow_right(d, 195, 220, 72, C_GRAY)
    _box(d, 220, 55, 80, 35, C_ORANGE, "set-quota-\nproject", 7)
    _arrow_right(d, 300, 325, 72, C_GRAY)
    _box(d, 325, 55, 80, 35, C_GREEN, "Credentials\nSaved!", 7)
    _arrow_right(d, 405, 425, 72, C_GRAY)
    _box(d, 425, 55, 65, 35, C_PRIMARY, "Deploy\nReady", 7)

    # Labels
    d.add(String(50, 43, "Browser OAuth", fontSize=6, fillColor=C_GRAY, textAnchor="middle"))
    d.add(String(155, 43, "ADC for APIs", fontSize=6, fillColor=C_GRAY, textAnchor="middle"))
    d.add(String(260, 43, "Link billing", fontSize=6, fillColor=C_GRAY, textAnchor="middle"))
    d.add(String(365, 43, ".json file", fontSize=6, fillColor=C_GRAY, textAnchor="middle"))

    # Error path
    d.add(Rect(100, 8, 300, 22, fillColor=C_LIGHTRED, strokeColor=C_RED, strokeWidth=0.5, rx=4, ry=4))
    d.add(String(250, 14, "If errors: use --no-launch-browser flag, copy auth code manually", fontSize=7, fillColor=C_RED, textAnchor="middle"))

    return d


# ═══════════════════════════════════════════
# DIAGRAM 4: Deployment Order
# ═══════════════════════════════════════════
def build_deploy_order():
    d = Drawing(500, 180)
    d.add(Rect(0, 0, 500, 180, fillColor=C_LIGHTBG, strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.5, rx=8, ry=8))
    d.add(String(250, 162, "Deployment Order — Why Sequence Matters", fontSize=11, fillColor=C_PRIMARY, textAnchor="middle", fontName="Helvetica-Bold"))

    # Step boxes with numbers
    _box(d, 15, 100, 100, 40, C_GREEN, "1. Gatekeeper\n(no deps)", 8)
    _arrow_right(d, 115, 140, 120, C_GRAY)
    _box(d, 140, 100, 100, 40, C_ORANGE, "2. SQL Engine\n(no deps)", 8)
    _arrow_right(d, 240, 265, 120, C_GRAY)
    _box(d, 265, 100, 110, 40, C_PRIMARY, "3. Master\n(needs 1 & 2 URLs)", 8)
    _arrow_right(d, 375, 400, 120, C_GRAY)
    _box(d, 400, 100, 85, 40, C_PURPLE, "4. Streamlit\n(needs 3 URL)", 8)

    # Dependency arrows
    d.add(Line(65, 100, 320, 100, strokeColor=C_RED, strokeWidth=1, strokeDashArray=[3, 2]))
    d.add(Line(320, 100, 320, 95, strokeColor=C_RED, strokeWidth=1))
    d.add(String(195, 90, "URLs flow into Master's .env", fontSize=7, fillColor=C_RED, textAnchor="middle"))

    d.add(Line(440, 100, 440, 70, strokeColor=C_RED, strokeWidth=1, strokeDashArray=[3, 2]))
    d.add(Line(320, 70, 440, 70, strokeColor=C_RED, strokeWidth=1, strokeDashArray=[3, 2]))
    d.add(String(380, 60, "Master URL → Streamlit env", fontSize=7, fillColor=C_RED, textAnchor="middle"))

    # Time estimate
    d.add(Rect(130, 15, 240, 25, fillColor=C_LIGHTGREEN, strokeColor=C_GREEN, strokeWidth=0.5, rx=4, ry=4))
    d.add(String(250, 23, "Total: ~30 min (3 x 5-10 min deploys + Streamlit)", fontSize=8, fillColor=C_GREEN, textAnchor="middle", fontName="Helvetica-Bold"))

    return d


# ═══════════════════════════════════════════
# DIAGRAM 5: Agent Runtime Concepts
# ═══════════════════════════════════════════
def build_concepts_map():
    d = Drawing(500, 300)
    d.add(Rect(0, 0, 500, 300, fillColor=C_LIGHTBG, strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.5, rx=8, ry=8))
    d.add(String(250, 278, "Agent Runtime — Key Concepts", fontSize=12, fillColor=C_PRIMARY, textAnchor="middle", fontName="Helvetica-Bold"))

    # Center
    cx, cy = 250, 140
    d.add(Circle(cx, cy, 30, fillColor=C_PRIMARY, strokeColor=None))
    d.add(String(cx, 145, "Agent", fontSize=9, fillColor=C_WHITE, textAnchor="middle", fontName="Helvetica-Bold"))
    d.add(String(cx, 134, "Runtime", fontSize=8, fillColor=C_WHITE, textAnchor="middle"))

    concepts = [
        ("Reasoning\nEngine", C_ACCENT, "Your ADK agent\nas a managed service"),
        ("agents-cli", C_ORANGE, "CLI tool for\nscaffold + deploy"),
        ("Cloud Build", C_TEAL, "Packages Docker\nimage automatically"),
        ("Cloud Trace", C_PURPLE, "Execution traces\n+ latency monitoring"),
        ("Session\nManagement", C_PINK, "Built-in stateful\nconversation memory"),
        ("Artifact\nRegistry", C_AMBER, "Stores your\nDocker images"),
    ]

    radius = 105
    for i, (label, clr, desc) in enumerate(concepts):
        angle = math.pi / 2 + 2 * math.pi * i / 6
        bx = cx + radius * math.cos(angle) - 42
        by = cy + radius * math.sin(angle) - 16
        bw, bh = 84, 32

        ex = bx + bw / 2
        ey = by + bh / 2
        _dashed_line(d, cx, cy, ex, ey, clr)
        _box(d, bx, by, bw, bh, clr, label, 7)

        # Description text near each box
        dx = bx + bw / 2
        dy = by - 10
        if by > cy:
            dy = by + bh + 8
        for j, dline in enumerate(desc.split("\n")):
            d.add(String(dx, dy - j * 8, dline, fontSize=6, fillColor=C_GRAY, textAnchor="middle"))

    return d


# ═══════════════════════════════════════════
# DIAGRAM 6: Local vs Cloud comparison
# ═══════════════════════════════════════════
def build_local_vs_cloud():
    d = Drawing(500, 160)
    d.add(Rect(0, 0, 500, 160, fillColor=C_LIGHTBG, strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.5, rx=8, ry=8))
    d.add(String(250, 142, "Local Development vs Cloud Deployment", fontSize=11, fillColor=C_PRIMARY, textAnchor="middle", fontName="Helvetica-Bold"))

    # Local side
    d.add(Rect(15, 20, 225, 108, fillColor=C_LIGHTRED, strokeColor=C_RED, strokeWidth=0.5, rx=6, ry=6))
    d.add(String(127, 114, "Local (Development)", fontSize=9, fillColor=C_RED, textAnchor="middle", fontName="Helvetica-Bold"))

    _box(d, 25, 80, 65, 22, C_GREEN, "GK :9000", 7)
    _box(d, 100, 80, 65, 22, C_ORANGE, "SQL :9001", 7)
    _box(d, 60, 50, 80, 22, C_PRIMARY, "Master :8000", 7)
    _box(d, 60, 25, 80, 20, C_PURPLE, "Streamlit :8501", 7)

    d.add(String(127, 105, "localhost — no auth needed", fontSize=6, fillColor=C_GRAY, textAnchor="middle"))

    # Cloud side
    d.add(Rect(260, 20, 225, 108, fillColor=C_LIGHTGREEN, strokeColor=C_GREEN, strokeWidth=0.5, rx=6, ry=6))
    d.add(String(372, 114, "Cloud (Production)", fontSize=9, fillColor=C_GREEN, textAnchor="middle", fontName="Helvetica-Bold"))

    _box(d, 270, 80, 65, 22, C_GREEN, "GK Engine", 7)
    _box(d, 345, 80, 68, 22, C_ORANGE, "SQL Engine", 7)
    _box(d, 305, 50, 80, 22, C_PRIMARY, "Master Engine", 7)
    _box(d, 425, 50, 50, 22, C_PURPLE, "Cloud\nRun", 6)

    d.add(String(372, 105, "Agent Runtime — Bearer token auth", fontSize=6, fillColor=C_GRAY, textAnchor="middle"))

    # Arrow between
    _arrow_right(d, 240, 260, 65, C_ACCENT)
    d.add(String(250, 72, "deploy", fontSize=7, fillColor=C_ACCENT, textAnchor="middle"))

    return d


# ═══════════════════════════════════════════
# BUILD PDF
# ═══════════════════════════════════════════
def build_pdf(path):
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN)
    story = []

    # ── PAGE 1: Title + Overview ──
    story.append(Paragraph("QuerySage Deployment Journey", title_style))
    story.append(Paragraph("From Local Development to Google Cloud — A Self-Learning Guide", subtitle_style))
    story.append(HRFlowable(width="100%", color=C_ACCENT, thickness=2))
    story.append(Spacer(1, 10))

    story.append(Paragraph("What This Document Covers", h1))
    story.append(Paragraph(
        "This document captures the complete journey of deploying QuerySage — a multi-agent "
        "NL-to-SQL platform — from local development to Google Cloud. It includes every issue "
        "encountered, how each was resolved, architecture diagrams, and conceptual explanations "
        "of the deployment technologies. Use it as a self-learning reference for deploying "
        "ADK 2.0 agents to production.",
        body,
    ))
    story.append(Spacer(1, 6))
    story.append(build_deploy_pipeline())
    story.append(Paragraph("Figure 1 — The 5-step deployment pipeline, each driven by an Antigravity prompt.", caption_style))

    story.append(Paragraph("Deployment Architecture", h1))
    story.append(Paragraph(
        "QuerySage deploys as 3 <b>Reasoning Engines</b> on Agent Runtime (Vertex AI) plus "
        "1 <b>Cloud Run</b> service for the Streamlit frontend. Agent Runtime is Google Cloud's "
        "managed hosting for ADK agents — it handles scaling, session management, and observability "
        "automatically. The Streamlit UI is a standard web app deployed to Cloud Run with a "
        "public URL for team access.",
        body,
    ))
    story.append(Spacer(1, 6))
    story.append(build_cloud_architecture())
    story.append(Paragraph("Figure 2 — QuerySage cloud architecture: 3 Reasoning Engines + Cloud Run frontend.", caption_style))

    # ── PAGE 2: Auth Journey + Issues ──
    story.append(PageBreak())
    story.append(Paragraph("Phase 1: Google Cloud Authentication", h1))
    story.append(Paragraph(
        "Before any deployment, you must authenticate with Google Cloud. This involves two "
        "separate auth flows: <b>gcloud auth login</b> (for CLI commands) and "
        "<b>gcloud auth application-default login</b> (for API calls from code/libraries). "
        "The second one is often where issues arise.",
        body,
    ))
    story.append(Spacer(1, 4))
    story.append(build_auth_flow())
    story.append(Paragraph("Figure 3 — Authentication flow with fallback path for browser issues.", caption_style))

    # Issue 1
    story.append(Paragraph("Issue #1: application-default login Browser Failure", h2))
    story.append(Paragraph("<b>Error:</b> <font face='Courier' size='8'>ERROR: There was a problem with web authentication. Try running again with --no-browser. scope is required but not consented.</font>", issue_style))
    story.append(Paragraph("<b>Root Cause:</b> The browser opened but the OAuth consent page wasn't completed — either the page closed too fast, or not all permission scopes were checked.", body))
    story.append(Paragraph("<b>Fix:</b> Used <font face='Courier'>--no-launch-browser</font> flag. This prints a URL to copy-paste into the browser manually, then returns an authorization code to paste back into the terminal.", fix_style))
    story.append(Paragraph("<font face='Courier' size='8'>gcloud auth application-default login --no-launch-browser</font>", code_style))

    # Issue 2
    story.append(Paragraph("Issue #2: Quota Project Permission Denied", h2))
    story.append(Paragraph("<b>Error:</b> <font face='Courier' size='8'>Cannot add the project \"querysage-capstone\" to ADC as the quota project because the account does not have the \"serviceusage.services.use\" permission</font>", issue_style))
    story.append(Paragraph("<b>Root Cause:</b> The Google Cloud project didn't exist yet — the <font face='Courier'>querysage-capstone</font> project ID hadn't been created, so the account had no permissions on it.", body))
    story.append(Paragraph("<b>Fix:</b> Created the project first, then set the quota project:", fix_style))
    story.append(Paragraph("<font face='Courier' size='8'>gcloud projects create querysage-capstone --name=\"QuerySage\"<br/>gcloud config set project querysage-capstone<br/>gcloud auth application-default set-quota-project querysage-capstone</font>", code_style))

    # Issue 3
    story.append(Paragraph("Issue #3: IAM Policy Binding Permission Denied", h2))
    story.append(Paragraph("<b>Error:</b> <font face='Courier' size='8'>does not have permission to access projects instance [querysage-capstone:getIamPolicy]</font>", issue_style))
    story.append(Paragraph("<b>Root Cause:</b> Tried to grant IAM roles before the project existed. The <font face='Courier'>add-iam-policy-binding</font> command requires the project to already exist and the caller to be an Owner.", body))
    story.append(Paragraph("<b>Fix:</b> Create the project first (as shown above). The project creator automatically gets Owner role, then all IAM commands work.", fix_style))

    # Issue 4
    story.append(Paragraph("Issue #4: Billing Not Linked", h2))
    story.append(Paragraph("<b>Error:</b> Agent Runtime deployment fails because billing is not enabled on the project.", issue_style))
    story.append(Paragraph("<b>Fix:</b> Opened the GCP Billing Console, created a billing account (or linked existing), and associated it with the project. Google provides free credits for new accounts.", fix_style))

    # ── PAGE 3: Deployment Flow + Issues ──
    story.append(PageBreak())
    story.append(Paragraph("Phase 2: Deploying the Agents", h1))
    story.append(Paragraph(
        "QuerySage has three independent agents that must be deployed in a specific order. "
        "The Gatekeeper and SQL Engine have no dependencies, but the Master depends on their "
        "deployed URLs. The Streamlit UI depends on the Master's URL.",
        body,
    ))
    story.append(Spacer(1, 4))
    story.append(build_deploy_order())
    story.append(Paragraph("Figure 4 — Deployment order with dependency arrows showing why sequence matters.", caption_style))

    # Per-service deployment steps
    story.append(Paragraph("Deployment Steps Per Service", h2))
    story.append(Paragraph(
        "Each service follows the same 4-step pattern via Antigravity prompts:",
        body,
    ))

    steps_data = [
        ["Step", "Antigravity Prompt", "What It Does"],
        ["1. Scaffold", "\"Scaffold production deployment files\nfor Agent Runtime\"", "Runs agents-cli scaffold enhance\nGenerates agent_runtime_app.py +\ndeployment_metadata.json"],
        ["2. Lock", "\"Lock dependencies and run\na dry-run deployment\"", "Runs uv lock + agents-cli deploy --dry-run\nValidates config without deploying"],
        ["3. Deploy", "\"Deploy this agent to Agent\nRuntime using project X region Y\"", "Runs agents-cli deploy\nPackages + uploads + provisions\n(5-10 min wait)"],
        ["4. Get URL", "\"What is the live endpoint URL\nfor my deployed agent?\"", "Returns the Reasoning Engine\nAPI passthrough URL"],
    ]
    t = Table(steps_data, colWidths=[45, 165, 265])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHTBG]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # Issue 5: Inter-service auth
    story.append(Paragraph("Issue #5: Inter-Service Authentication", h2))
    story.append(Paragraph(
        "<b>Problem:</b> Locally, the Master calls Gatekeeper and SQL Engine via "
        "<font face='Courier'>http://localhost:9000</font> — no auth needed. But Agent Runtime "
        "endpoints require Google Cloud <b>Bearer token authentication</b>.",
        issue_style,
    ))
    story.append(Paragraph(
        "<b>Solution:</b> Updated <font face='Courier'>fast_api_app.py</font> with a "
        "<font face='Courier'>_get_auth_headers()</font> helper that auto-detects Agent Runtime "
        "URLs (containing <font face='Courier'>aiplatform.googleapis.com</font>) and adds "
        "<font face='Courier'>Authorization: Bearer &lt;token&gt;</font> headers. Local "
        "<font face='Courier'>localhost</font> URLs continue working without auth.",
        fix_style,
    ))
    story.append(Paragraph(
        "<font face='Courier' size='8'>async def _get_auth_headers():<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;credentials, _ = google.auth.default()<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;credentials.refresh(google.auth.transport.requests.Request())<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;return {\"Authorization\": f\"Bearer {credentials.token}\"}</font>",
        code_style,
    ))

    # ── PAGE 4: Agent Runtime Concepts ──
    story.append(PageBreak())
    story.append(Paragraph("Key Concepts: Agent Runtime & Deployment", h1))
    story.append(Paragraph(
        "Understanding these concepts is essential for deploying and maintaining ADK agents "
        "in production. Agent Runtime is Google Cloud's managed hosting specifically designed "
        "for AI agents — it's different from generic Cloud Run or Cloud Functions.",
        body,
    ))
    story.append(Spacer(1, 6))
    story.append(build_concepts_map())
    story.append(Paragraph("Figure 5 — Agent Runtime ecosystem: the 6 key services that support your deployed agent.", caption_style))

    concepts_table = [
        ["Concept", "What It Is", "Why It Matters"],
        ["Reasoning Engine", "A managed Vertex AI resource that\nhosts your ADK agent", "Always-on endpoint — doesn't stop\nwhen you close your laptop"],
        ["agents-cli", "CLI tool that scaffolds, validates,\nand deploys ADK agents", "Automates Docker build, push, and\nAgent Runtime provisioning"],
        ["scaffold enhance", "Generates agent_runtime_app.py\nand deployment_metadata.json", "Production wrapper that Agent\nRuntime needs to host your agent"],
        ["dry-run", "Validates config + deps without\nactually deploying", "Catches errors before spending\n5-10 min on a real deploy"],
        ["Cloud Trace", "Distributed tracing for every\nagent interaction", "See execution spans for each\nworkflow node + latencies"],
        ["ADC (Application\nDefault Credentials)", "JSON file with OAuth tokens\nfor API authentication", "Required for inter-service calls\nin the cloud environment"],
    ]
    t2 = Table(concepts_table, colWidths=[85, 165, 225])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHTBLUE]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bfdbfe")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t2)

    # ── PAGE 5: Local vs Cloud + Streamlit ──
    story.append(PageBreak())
    story.append(Paragraph("Local vs Cloud: What Changes", h1))
    story.append(Paragraph(
        "The core agent logic (<font face='Courier'>agent.py</font>) stays identical. "
        "What changes is the hosting wrapper and how services discover each other. "
        "Locally, everything runs on <font face='Courier'>localhost</font> with no auth. "
        "In the cloud, each service gets a Vertex AI URL and requires Bearer token auth.",
        body,
    ))
    story.append(Spacer(1, 4))
    story.append(build_local_vs_cloud())
    story.append(Paragraph("Figure 6 — Side-by-side comparison of local development vs cloud deployment.", caption_style))

    diff_table = [
        ["Aspect", "Local", "Cloud"],
        ["Service discovery", "localhost:PORT", "Reasoning Engine API URL"],
        ["Authentication", "None", "Bearer token (google.auth)"],
        ["Session storage", "InMemorySessionService", "Agent Runtime managed sessions"],
        ["Monitoring", "Console logs", "Cloud Trace + Cloud Logging"],
        ["Availability", "Stops when laptop closes", "Always-on 24/7"],
        ["Scaling", "Single process", "Auto-scales with demand"],
        ["Frontend", "streamlit run (local)", "Cloud Run public URL"],
        ["Cost", "Free", "Free tier (demo usage)"],
    ]
    t3 = Table(diff_table, colWidths=[100, 175, 200])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (1, 1), (1, -1), C_LIGHTRED),
        ("BACKGROUND", (2, 1), (2, -1), C_LIGHTGREEN),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t3)

    story.append(Spacer(1, 12))
    story.append(Paragraph("Streamlit Frontend on Cloud Run", h2))
    story.append(Paragraph(
        "The Streamlit app deploys to <b>Cloud Run</b> (not Agent Runtime) because it's a "
        "frontend web app, not an ADK agent. Cloud Run gives it a <b>public URL</b> "
        "(<font face='Courier'>https://querysage-ui-xxxxx-as.a.run.app</font>) that "
        "anyone can open in their browser. The app uses environment variables "
        "(<font face='Courier'>MASTER_URL</font>) to point to the Master's Agent Runtime "
        "endpoint, and includes <font face='Courier'>google-auth</font> to add Bearer "
        "tokens when calling the cloud-hosted Master.",
        body,
    ))

    # ── PAGE 6: Checklist + Summary ──
    story.append(PageBreak())
    story.append(Paragraph("Complete Deployment Checklist", h1))

    checklist = [
        ["#", "Task", "Command / Action", "Status"],
        ["1", "gcloud auth login", "gcloud auth login", "Done"],
        ["2", "application-default login", "gcloud auth application-default login\n--no-launch-browser", "Done"],
        ["3", "Create GCP project", "gcloud projects create querysage-capstone", "Done"],
        ["4", "Enable billing", "GCP Console > Billing > Link account", "Done"],
        ["5", "Enable APIs", "gcloud services enable\naiplatform.googleapis.com\ncloudbuild.googleapis.com\ncloudtrace.googleapis.com", "Done"],
        ["6", "Install agents-cli", "uvx google-agents-cli setup", "Done"],
        ["7", "Deploy Gatekeeper", "Antigravity: scaffold + deploy", "Done"],
        ["8", "Deploy SQL Engine", "Antigravity: scaffold + deploy", "Done"],
        ["9", "Update Master .env", "Set GATEKEEPER_SERVICE_URL\nand SQL_ENGINE_SERVICE_URL\nto Reasoning Engine URLs", "Done"],
        ["10", "Deploy Master", "Antigravity: scaffold + deploy", "Done"],
        ["11", "Deploy Streamlit", "Antigravity: deploy to Cloud Run\nwith MASTER_URL env var", "Done"],
        ["12", "Test end-to-end", "Open public Streamlit URL,\nsubmit query, approve SQL", "Done"],
        ["13", "Git commit & push", "git add -A && git commit && git push", "Pending"],
    ]
    t4 = Table(checklist, colWidths=[20, 95, 195, 45])
    t4.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHTBG]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        # Green for "Done" rows
        ("TEXTCOLOR", (3, 1), (3, 12), C_GREEN),
        ("FONTNAME", (3, 1), (3, 12), "Helvetica-Bold"),
        ("TEXTCOLOR", (3, 13), (3, 13), C_ORANGE),
        ("FONTNAME", (3, 13), (3, 13), "Helvetica-Bold"),
    ]))
    story.append(t4)

    story.append(Spacer(1, 12))
    story.append(Paragraph("Issues Summary", h1))

    issues_summary = [
        ["#", "Issue", "Root Cause", "Resolution"],
        ["1", "Browser auth failure", "OAuth consent not completed", "Used --no-launch-browser flag"],
        ["2", "Quota project denied", "Project didn't exist yet", "Created project first, then set quota"],
        ["3", "IAM binding denied", "Project didn't exist", "Create project before granting roles"],
        ["4", "Billing not linked", "New project has no billing", "Linked via GCP Billing Console"],
        ["5", "Inter-service auth", "Agent Runtime needs Bearer\ntokens, localhost doesn't", "Added _get_auth_headers() that\nauto-detects cloud URLs"],
    ]
    t5 = Table(issues_summary, colWidths=[20, 95, 130, 230])
    t5.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_RED),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHTRED]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#fca5a5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t5)

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", color=C_ACCENT, thickness=1))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "QuerySage Deployment Journal — Kaggle 5-Day AI Agents Vibe Coding Course with Google",
        ParagraphStyle("Footer", parent=body, alignment=TA_CENTER, textColor=C_GRAY, fontSize=9),
    ))

    doc.build(story)
    return path


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "/sessions/friendly-sharp-davinci/mnt/querysage-master/QuerySage_Deployment_Journey.pdf"
    build_pdf(out)
    print(f"PDF written to {out}")
