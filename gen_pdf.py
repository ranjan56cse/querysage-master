"""Generate QuerySage Architecture PDF with embedded diagrams."""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)
from reportlab.graphics.shapes import (
    Drawing,
    Rect,
    String,
    Line,
    Polygon,
    Group,
    Circle,
)
from reportlab.graphics import renderPDF
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

WIDTH, HEIGHT = A4
MARGIN = 50

# ─── Color palette ───
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
C_DARKBG = colors.HexColor("#1e293b")
C_WHITE = colors.white
C_GRAY = colors.HexColor("#64748b")

styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    "CustomTitle",
    parent=styles["Title"],
    fontSize=24,
    textColor=C_PRIMARY,
    spaceAfter=6,
    alignment=TA_CENTER,
)
subtitle_style = ParagraphStyle(
    "Subtitle",
    parent=styles["Normal"],
    fontSize=11,
    textColor=C_GRAY,
    alignment=TA_CENTER,
    spaceAfter=20,
)
h1 = ParagraphStyle(
    "H1",
    parent=styles["Heading1"],
    fontSize=18,
    textColor=C_PRIMARY,
    spaceBefore=16,
    spaceAfter=8,
)
h2 = ParagraphStyle(
    "H2",
    parent=styles["Heading2"],
    fontSize=14,
    textColor=C_ACCENT,
    spaceBefore=12,
    spaceAfter=6,
)
body = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontSize=10,
    leading=14,
    textColor=colors.HexColor("#334155"),
    alignment=TA_JUSTIFY,
    spaceAfter=6,
)
caption_style = ParagraphStyle(
    "Caption",
    parent=styles["Normal"],
    fontSize=9,
    textColor=C_GRAY,
    alignment=TA_CENTER,
    spaceBefore=4,
    spaceAfter=12,
)

# ─── Helper: rounded rect with text ───
def _box(g, x, y, w, h, fill, label, font_size=8, text_color=C_WHITE):
    g.add(Rect(x, y, w, h, fillColor=fill, strokeColor=None, rx=6, ry=6))
    lines = label.split("\n")
    line_h = font_size + 2
    start_y = y + h / 2 + (len(lines) - 1) * line_h / 2
    for i, line in enumerate(lines):
        g.add(
            String(
                x + w / 2,
                start_y - i * line_h - font_size * 0.35,
                line,
                fontSize=font_size,
                fillColor=text_color,
                textAnchor="middle",
                fontName="Helvetica-Bold" if font_size >= 9 else "Helvetica",
            )
        )

def _arrow_down(g, x, y1, y2, color=C_GRAY):
    g.add(Line(x, y1, x, y2 + 6, strokeColor=color, strokeWidth=1.5))
    g.add(Polygon(points=[x - 4, y2 + 6, x + 4, y2 + 6, x, y2], fillColor=color, strokeColor=None))

def _arrow_right(g, x1, x2, y, color=C_GRAY):
    g.add(Line(x1, y, x2 - 6, y, strokeColor=color, strokeWidth=1.5))
    g.add(Polygon(points=[x2 - 6, y - 4, x2 - 6, y + 4, x2, y], fillColor=color, strokeColor=None))

def _arrow_left(g, x1, x2, y, color=C_GRAY):
    """Arrow from x1 going left to x2 (x2 < x1)."""
    g.add(Line(x1, y, x2 + 6, y, strokeColor=color, strokeWidth=1.5))
    g.add(Polygon(points=[x2 + 6, y - 4, x2 + 6, y + 4, x2, y], fillColor=color, strokeColor=None))


# ═══════════════════════════════════════════════════
# DIAGRAM 1: System Architecture (3 services + UI)
# ═══════════════════════════════════════════════════
def build_system_arch_diagram():
    d = Drawing(480, 340)
    # Background
    d.add(Rect(0, 0, 480, 340, fillColor=colors.HexColor("#f8fafc"), strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.5, rx=8, ry=8))
    # Title
    d.add(String(240, 318, "QuerySage — System Architecture", fontSize=12, fillColor=C_PRIMARY, textAnchor="middle", fontName="Helvetica-Bold"))

    # --- User / Streamlit ---
    _box(d, 20, 250, 100, 40, C_PURPLE, "Streamlit UI\nPort 8501", 8)

    # Arrow: Streamlit -> Master
    _arrow_right(d, 120, 175, 270, C_ACCENT)
    d.add(String(148, 276, "REST", fontSize=7, fillColor=C_ACCENT, textAnchor="middle"))

    # --- Master Orchestrator ---
    _box(d, 175, 240, 130, 60, C_PRIMARY, "Master Orchestrator\n(ADK 2.0 Workflow)\nPort 8000", 8)

    # Arrow: Master -> Gatekeeper
    _arrow_down(d, 220, 240, 190, C_GREEN)
    d.add(String(230, 210, "validate", fontSize=7, fillColor=C_GREEN, textAnchor="start"))

    # Arrow: Master -> SQL Engine
    _arrow_down(d, 260, 240, 190, C_ORANGE)
    d.add(String(268, 210, "generate", fontSize=7, fillColor=C_ORANGE, textAnchor="start"))

    # --- Gatekeeper ---
    _box(d, 140, 140, 110, 45, C_GREEN, "Gatekeeper Service\nRegex + Blocklists\nPort 9000", 8)

    # --- SQL Engine ---
    _box(d, 275, 140, 110, 45, C_ORANGE, "SQL Engine Service\nGemini LLM\nPort 9001", 8)

    # Arrow: Master -> Neon DB (down from master)
    _arrow_down(d, 240, 240, 80, C_TEAL)
    d.add(String(248, 100, "execute SQL", fontSize=7, fillColor=C_TEAL, textAnchor="start"))

    # --- Neon Postgres ---
    _box(d, 185, 30, 110, 45, C_TEAL, "Neon Postgres\n(Cloud DB)\nPgBouncer", 8)

    # --- HITL box ---
    _box(d, 350, 250, 110, 40, C_RED, "HITL Approval\n(RequestInput)", 8)
    # Arrow: Master -> HITL
    _arrow_right(d, 305, 350, 270, C_RED)

    # --- Memory ---
    _box(d, 350, 30, 110, 40, C_AMBER, "InMemory\nSession + Memory", 8)
    # Arrow: Master -> Memory
    d.add(Line(305, 265, 405, 75, strokeColor=C_AMBER, strokeWidth=1, strokeDashArray=[3, 3]))

    # --- Google AI ---
    _box(d, 20, 140, 100, 45, C_PINK, "Google AI Studio\nGemini Model\nAPI Key", 8)
    # Dashed line to SQL Engine
    d.add(Line(120, 162, 275, 162, strokeColor=C_PINK, strokeWidth=1, strokeDashArray=[3, 3]))

    return d


# ═══════════════════════════════════════════════════
# DIAGRAM 2: Agent Workflow (9 nodes)
# ═══════════════════════════════════════════════════
def build_workflow_diagram():
    d = Drawing(480, 420)
    d.add(Rect(0, 0, 480, 420, fillColor=colors.HexColor("#f8fafc"), strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.5, rx=8, ry=8))
    d.add(String(240, 398, "ADK 2.0 Graph Workflow — 9 Nodes", fontSize=12, fillColor=C_PRIMARY, textAnchor="middle", fontName="Helvetica-Bold"))

    # Node positions (x, y, w, h, color, label)
    nodes = [
        (190, 355, 100, 30, C_ACCENT,  "1. receive_query"),
        (190, 305, 100, 30, C_GREEN,   "2. validate_query"),
        (190, 255, 100, 30, C_ORANGE,  "3. generate_sql"),
        (190, 205, 100, 30, C_RED,     "4. security_check"),
        (190, 155, 100, 30, colors.HexColor("#b91c1c"), "5. approve_sql"),
        (190, 105, 100, 30, C_TEAL,    "6. executor"),
        (190, 55,  100, 30, C_PURPLE,  "7. insight_router"),
        (60,  10,  100, 30, C_PINK,    "8. insight_disc."),
        (320, 10,  100, 30, C_AMBER,   "9. present_results"),
    ]

    for x, y, w, h, c, label in nodes:
        _box(d, x, y, w, h, c, label, 8)

    # Vertical arrows between sequential nodes (1->2->3->4->5->6->7)
    for i in range(6):
        _, y1, _, _, _, _ = nodes[i]
        _, y2, _, h2, _, _ = nodes[i + 1]
        _arrow_down(d, 240, y1, y2 + h2, C_GRAY)

    # 7 -> 8 (left branch)
    d.add(Line(190, 70, 160, 40, strokeColor=C_GRAY, strokeWidth=1.5))
    _arrow_left(d, 160, 110 + 50, 40, C_GRAY)

    # 7 -> 9 (right branch)
    d.add(Line(290, 70, 320, 40, strokeColor=C_GRAY, strokeWidth=1.5))

    # 8 -> 9 arrow
    _arrow_right(d, 160, 320, 25, C_GRAY)

    # Reject branch from security_check
    _box(d, 360, 205, 90, 30, colors.HexColor("#991b1b"), "reject_query", 8)
    _arrow_right(d, 290, 360, 220, C_RED)
    d.add(String(325, 226, "blocked", fontSize=7, fillColor=C_RED, textAnchor="middle"))

    # HITL annotation on approve_sql
    d.add(Rect(330, 155, 130, 30, fillColor=colors.HexColor("#fef2f2"), strokeColor=C_RED, strokeWidth=0.8, rx=4, ry=4))
    d.add(String(395, 167, "Human-in-the-Loop", fontSize=8, fillColor=C_RED, textAnchor="middle", fontName="Helvetica-Bold"))
    d.add(String(395, 158, "yield RequestInput", fontSize=7, fillColor=C_GRAY, textAnchor="middle"))
    _arrow_right(d, 290, 330, 170, C_RED)

    # Legend
    d.add(Rect(10, 355, 12, 12, fillColor=C_GREEN, strokeColor=None))
    d.add(String(26, 358, "Validation", fontSize=7, fillColor=C_GRAY))
    d.add(Rect(10, 338, 12, 12, fillColor=C_RED, strokeColor=None))
    d.add(String(26, 341, "Security", fontSize=7, fillColor=C_GRAY))
    d.add(Rect(10, 321, 12, 12, fillColor=C_TEAL, strokeColor=None))
    d.add(String(26, 324, "Execution", fontSize=7, fillColor=C_GRAY))
    d.add(Rect(10, 304, 12, 12, fillColor=C_PURPLE, strokeColor=None))
    d.add(String(26, 307, "Analysis", fontSize=7, fillColor=C_GRAY))

    return d


# ═══════════════════════════════════════════════════
# DIAGRAM 3: 7 Course Concepts
# ═══════════════════════════════════════════════════
def build_concepts_diagram():
    d = Drawing(480, 320)
    d.add(Rect(0, 0, 480, 320, fillColor=colors.HexColor("#f8fafc"), strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.5, rx=8, ry=8))
    d.add(String(240, 298, "7 Kaggle Course Concepts in QuerySage", fontSize=12, fillColor=C_PRIMARY, textAnchor="middle", fontName="Helvetica-Bold"))

    # Central hub
    cx, cy, cr = 240, 155, 35
    d.add(Circle(cx, cy, cr, fillColor=C_PRIMARY, strokeColor=None))
    d.add(String(cx, 160, "QuerySage", fontSize=9, fillColor=C_WHITE, textAnchor="middle", fontName="Helvetica-Bold"))
    d.add(String(cx, 149, "Hub", fontSize=8, fillColor=C_WHITE, textAnchor="middle"))

    # 7 concepts around the hub
    import math
    concepts = [
        ("Graph\nWorkflow", C_ACCENT),
        ("Multi-Agent\nServices", C_GREEN),
        ("HITL\nApproval", C_RED),
        ("Tool Use\n(Neon SQL)", C_TEAL),
        ("Safety\nGuardrails", C_ORANGE),
        ("Memory\n(Sessions)", C_AMBER),
        ("Context\nEngine", C_PURPLE),
    ]

    radius = 115
    for i, (label, clr) in enumerate(concepts):
        angle = math.pi / 2 + 2 * math.pi * i / 7
        bx = cx + radius * math.cos(angle) - 45
        by = cy + radius * math.sin(angle) - 18
        bw, bh = 90, 36

        # Line from center to box
        ex = bx + bw / 2
        ey = by + bh / 2
        d.add(Line(cx, cy, ex, ey, strokeColor=clr, strokeWidth=1.2, strokeDashArray=[4, 2]))

        _box(d, bx, by, bw, bh, clr, label, 8)

    return d


# ═══════════════════════════════════════════════════
# BUILD PDF
# ═══════════════════════════════════════════════════
def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )
    story = []

    # ── Page 1: Title + Executive Summary + System Architecture ──
    story.append(Paragraph("QuerySage Architecture", title_style))
    story.append(Paragraph("Capstone Project — Kaggle 5-Day AI Agents Vibe Coding Course", subtitle_style))
    story.append(HRFlowable(width="100%", color=C_ACCENT, thickness=2))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Executive Summary", h1))
    story.append(Paragraph(
        "QuerySage is a natural-language-to-SQL analytics platform built with Google ADK 2.0. "
        "Users type business questions in plain English; the system validates, translates to SQL, "
        "executes against a Neon Postgres cloud database, and returns results with Plotly charts — "
        "all with human-in-the-loop approval before any query touches the database.",
        body,
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("System Architecture", h1))
    story.append(Paragraph(
        "The platform is composed of three FastAPI micro-services plus a Streamlit front-end. "
        "The <b>Master Orchestrator</b> (port 8000) runs the ADK 2.0 graph workflow and coordinates "
        "calls to the <b>Gatekeeper</b> (port 9000) for regex-based input sanitisation and to the "
        "<b>SQL Engine</b> (port 9001) for Gemini-powered SQL generation. The Streamlit UI (port 8501) "
        "provides the chat interface with HITL approval buttons and Plotly visualisations.",
        body,
    ))
    story.append(Spacer(1, 6))
    story.append(build_system_arch_diagram())
    story.append(Paragraph("Figure 1 — System architecture showing service interactions, ports, and data flow.", caption_style))

    # Service detail table
    svc_data = [
        ["Service", "Port", "Technology", "Role"],
        ["Master Orchestrator", "8000", "FastAPI + ADK 2.0", "Graph workflow engine, HITL, session mgmt"],
        ["Gatekeeper", "9000", "FastAPI + Regex", "Input validation, SQL-injection blocking"],
        ["SQL Engine", "9001", "FastAPI + Gemini", "NL-to-SQL translation via LLM"],
        ["Streamlit UI", "8501", "Streamlit + Plotly", "Chat interface, charts, approval buttons"],
        ["Neon Postgres", "Cloud", "PgBouncer + SSL", "Analytics database (e-commerce data)"],
    ]
    t = Table(svc_data, colWidths=[100, 45, 100, 230])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHTBG]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # ── Page 2: Workflow Diagram ──
    story.append(PageBreak())
    story.append(Paragraph("ADK 2.0 Graph Workflow", h1))
    story.append(Paragraph(
        "The master orchestrator runs a 9-node directed graph built with Google ADK 2.0's "
        "<b>GraphFlow</b> API. Each node is a Python function that reads/writes shared state. "
        "The workflow enforces a strict pipeline: receive → validate → generate → security-check → "
        "approve (HITL) → execute → analyse → present.",
        body,
    ))
    story.append(Spacer(1, 6))
    story.append(build_workflow_diagram())
    story.append(Paragraph("Figure 2 — The 9-node ADK 2.0 graph workflow with HITL approval gate.", caption_style))

    # Node descriptions
    node_data = [
        ["#", "Node", "Description"],
        ["1", "receive_query", "Accepts the NL question from the user and stores it in state"],
        ["2", "validate_query", "Calls Gatekeeper service for regex/blocklist validation"],
        ["3", "generate_sql", "Calls SQL Engine (Gemini LLM) to translate NL to SQL"],
        ["4", "security_checkpoint", "Final safety check — blocks DROP/DELETE/UPDATE mutations"],
        ["5", "approve_sql", "HITL gate — yields RequestInput, waits for user yes/no"],
        ["6", "executor", "Runs the approved SQL against Neon Postgres via neon_tools"],
        ["7", "insight_router", "Routes to insight discovery or directly to presentation"],
        ["8", "insight_discovery", "Uses Gemini to generate analytical insights from results"],
        ["9", "present_results", "Formats the final response with data + insights"],
    ]
    t2 = Table(node_data, colWidths=[20, 100, 355])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHTBG]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t2)

    # ── Page 3: 7 Course Concepts + HITL Detail ──
    story.append(PageBreak())
    story.append(Paragraph("7 Kaggle Course Concepts", h1))
    story.append(Paragraph(
        "QuerySage demonstrates all seven concepts taught in the Kaggle 5-Day AI Agents "
        "Vibe Coding Course. The diagram below shows how each concept connects to the "
        "central QuerySage platform.",
        body,
    ))
    story.append(Spacer(1, 6))
    story.append(build_concepts_diagram())
    story.append(Paragraph("Figure 3 — The 7 course concepts and how QuerySage implements each.", caption_style))

    concepts_table = [
        ["#", "Concept", "Implementation"],
        ["1", "Graph Workflow", "ADK 2.0 GraphFlow with 9 sequential + branching nodes"],
        ["2", "Multi-Agent", "3 independent FastAPI services communicating via REST"],
        ["3", "HITL (Human-in-the-Loop)", "RequestInput at approve_sql node; FunctionResponse resume"],
        ["4", "Tool Use", "neon_execute_sql() and generate_chart() registered as ADK tools"],
        ["5", "Safety Guardrails", "Regex blocklists, sqlparse validation, SELECT-only enforcement"],
        ["6", "Memory", "InMemoryMemoryService persists context across conversation turns"],
        ["7", "Context Engine", "EventsCompactionConfig + ResumabilityConfig for state management"],
    ]
    t3 = Table(concepts_table, colWidths=[20, 120, 335])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHTBG]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t3)

    # ── Page 4: HITL Deep Dive + Security ──
    story.append(PageBreak())
    story.append(Paragraph("Human-in-the-Loop (HITL) — Deep Dive", h1))
    story.append(Paragraph(
        "The HITL mechanism is the most critical safety feature. When the workflow reaches the "
        "<b>approve_sql</b> node, it yields a <b>RequestInput</b> object. ADK 2.0 converts this "
        "into an Event containing a <b>FunctionCall</b> with name <font face='Courier'>adk_request_input</font> "
        "and the interrupt_id <font face='Courier'>\"approved\"</font>.",
        body,
    ))
    story.append(Paragraph(
        "The master's FastAPI endpoint detects this by scanning event content parts for "
        "<font face='Courier'>part.function_call.name == \"adk_request_input\"</font>. "
        "It returns <font face='Courier'>status: \"interrupted\"</font> to the Streamlit UI, "
        "which shows Approve/Reject buttons. When the user clicks Approve, the UI sends "
        "<font face='Courier'>\"yes\"</font> back, and the master resumes the workflow by sending a "
        "<b>FunctionResponse</b> with the matching interrupt_id.",
        body,
    ))

    # HITL flow mini-diagram
    hitl_d = Drawing(480, 120)
    hitl_d.add(Rect(0, 0, 480, 120, fillColor=colors.HexColor("#fef2f2"), strokeColor=C_RED, strokeWidth=0.5, rx=6, ry=6))
    hitl_d.add(String(240, 104, "HITL Approval Flow", fontSize=10, fillColor=C_RED, textAnchor="middle", fontName="Helvetica-Bold"))

    _box(hitl_d, 10, 50, 80, 35, C_PURPLE, "approve_sql\nyield RI", 7)
    _arrow_right(hitl_d, 90, 130, 67, C_RED)
    _box(hitl_d, 130, 50, 80, 35, C_PRIMARY, "Master API\ndetect FC", 7)
    _arrow_right(hitl_d, 210, 250, 67, C_RED)
    _box(hitl_d, 250, 50, 80, 35, colors.HexColor("#7c3aed"), "Streamlit\nApprove?", 7)
    _arrow_right(hitl_d, 330, 370, 67, C_GREEN)
    _box(hitl_d, 370, 50, 95, 35, C_GREEN, "Resume with\nFuncResponse", 7)

    # Labels below
    hitl_d.add(String(50, 38, "RequestInput", fontSize=6, fillColor=C_GRAY, textAnchor="middle"))
    hitl_d.add(String(170, 38, "adk_request_input", fontSize=6, fillColor=C_GRAY, textAnchor="middle"))
    hitl_d.add(String(290, 38, "User clicks Yes", fontSize=6, fillColor=C_GRAY, textAnchor="middle"))
    hitl_d.add(String(417, 38, "id + {result: yes}", fontSize=6, fillColor=C_GRAY, textAnchor="middle"))

    story.append(hitl_d)
    story.append(Paragraph("Figure 4 — HITL approval flow from node to UI and back.", caption_style))

    story.append(Paragraph("Security Layers", h1))
    story.append(Paragraph(
        "QuerySage implements defence-in-depth with multiple security layers:",
        body,
    ))

    sec_data = [
        ["Layer", "Component", "Mechanism"],
        ["1 — Input", "Gatekeeper (port 9000)", "Regex patterns block SQL injection, XSS, system commands"],
        ["2 — Generation", "SQL Engine (port 9001)", "Gemini prompt instructs SELECT-only generation"],
        ["3 — Validation", "security_checkpoint node", "sqlparse tokenisation rejects non-SELECT statements"],
        ["4 — Approval", "approve_sql node", "Human reviews exact SQL before execution"],
        ["5 — Execution", "neon_tools.py", "Blocked keyword set (DROP, DELETE, UPDATE, etc.)"],
        ["6 — Database", "Neon Postgres", "Read-only connection role, SSL + channel_binding"],
    ]
    t4 = Table(sec_data, colWidths=[60, 120, 295])
    t4.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_RED),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, colors.HexColor("#fef2f2")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#fca5a5")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t4)

    # ── Page 5: Setup + Tech Stack ──
    story.append(PageBreak())
    story.append(Paragraph("Technology Stack", h1))
    tech_data = [
        ["Category", "Technology", "Details"],
        ["AI Framework", "Google ADK 2.0", "GraphFlow, RequestInput, Runner, Events"],
        ["LLM", "Google Gemini", "gemini-2.0-flash via Google AI Studio API key"],
        ["Backend", "FastAPI + Uvicorn", "3 async micro-services"],
        ["Frontend", "Streamlit + Plotly", "Interactive chat UI with charts"],
        ["Database", "Neon Postgres", "Serverless, auto-suspend, PgBouncer pooling"],
        ["SQL Parsing", "sqlparse", "Token-level SQL validation"],
        ["HTTP Client", "httpx", "Async inter-service communication"],
        ["Environment", "python-dotenv", ".env-based configuration"],
    ]
    t5 = Table(tech_data, colWidths=[80, 110, 285])
    t5.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHTBG]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t5)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Quick Start", h1))
    story.append(Paragraph(
        "<b>1.</b> Clone the repo and install dependencies: "
        "<font face='Courier'>pip install -r requirements.txt</font>",
        body,
    ))
    story.append(Paragraph(
        "<b>2.</b> Copy <font face='Courier'>.env.example</font> to <font face='Courier'>.env</font> "
        "and fill in GOOGLE_API_KEY and NEON_DATABASE_URL.",
        body,
    ))
    story.append(Paragraph(
        "<b>3.</b> Start the three services:",
        body,
    ))
    story.append(Paragraph(
        "<font face='Courier' size='9'>uvicorn app.fast_api_app:app --port 8000</font><br/>"
        "<font face='Courier' size='9'>uvicorn services.gatekeeper.gatekeeper_app:app --port 9000</font><br/>"
        "<font face='Courier' size='9'>uvicorn services.sql_engine.sql_engine_app:app --port 9001</font>",
        body,
    ))
    story.append(Paragraph(
        "<b>4.</b> Launch the Streamlit UI: "
        "<font face='Courier'>streamlit run streamlit_app.py</font>",
        body,
    ))
    story.append(Paragraph(
        "<b>5.</b> Open <font face='Courier'>http://localhost:8501</font>, type a question, "
        "approve the SQL, and see results with charts.",
        body,
    ))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", color=C_ACCENT, thickness=1))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "QuerySage — Built for the Kaggle 5-Day AI Agents Vibe Coding Course with Google ADK 2.0",
        ParagraphStyle("Footer", parent=body, alignment=TA_CENTER, textColor=C_GRAY, fontSize=9),
    ))

    doc.build(story)
    return output_path


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "/sessions/friendly-sharp-davinci/mnt/querysage-master/QuerySage_Architecture.pdf"
    build_pdf(out)
    print(f"PDF written to {out}")