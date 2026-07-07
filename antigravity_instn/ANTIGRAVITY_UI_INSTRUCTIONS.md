# Antigravity Instructions: QuerySage Streamlit UI Redesign

Copy each section as a separate prompt to Antigravity. Do them in order.
**Start with Prompt 0A through 0D (backend changes), then proceed to Prompts 1-7 (UI changes).**

---

## Prompt 0A: Add follow_up_suggestions and insight_data to FastAPI Response

```
In app/fast_api_app.py, make these changes:

1. Add two new optional fields to the ChatResponse model:
   - follow_up_suggestions: list[str] | None = None
   - insight_data: dict[str, Any] | None = None

2. In the chat() endpoint, after extracting executor_output from the session state (around line 276), also extract insight_output:

   insight_output = updated_session.state.get("insight_output", {})
   if isinstance(insight_output, dict):
       follow_up_suggestions = insight_output.get("follow_up_questions", [])
       insight_data = {"insights": insight_output.get("insights", ""), "follow_up_questions": follow_up_suggestions}

3. Pass these to the ChatResponse return at the bottom:
   follow_up_suggestions=follow_up_suggestions,
   insight_data=insight_data,

This ensures the Streamlit UI can access the insight_discovery agent's structured output (insights text + follow-up questions) for the suggestion chips and insight cards.
```

---

## Prompt 0B: Add Schema Verification Node to Agent Workflow

```
In app/agent.py, add a new schema verification node that checks if the user's natural language query references valid database concepts. Insert it between validate_query and generate_sql.

1. Add a new Pydantic model:

class SchemaVerification(BaseModel):
    is_ambiguous: bool = False
    original_query: str = ""
    corrected_query: str | None = None
    explanation: str | None = None
    alternatives: list[str] | None = None

2. Add a new LlmAgent called schema_verifier:

schema_verifier = LlmAgent(
    name="schema_verifier",
    model="gemini-2.5-flash",
    instruction=(
        "You are a database schema expert. The user asked a business question in natural language. "
        "Your job is to verify whether the user's question maps correctly to the database schema. "
        "The database is a Neon Postgres e-commerce database with tables: orders, products, customers, order_items, categories. "
        "Key columns include: order_id, customer_id, product_id, order_date, total_amount, quantity, unit_price, product_name, category_name, customer_name, email, city, country. "
        "\n\nCheck for:\n"
        "- Typos in table/column names (e.g., 'revenu' should be 'total_amount' or 'revenue')\n"
        "- Ambiguous terms that could map to multiple columns (e.g., 'sales' could mean total_amount or quantity)\n"
        "- References to tables/columns that don't exist\n"
        "\nIf the query is clear and maps well to the schema, set is_ambiguous=False and corrected_query=None.\n"
        "If the query has issues, set is_ambiguous=True, provide a corrected_query with the improved phrasing, "
        "an explanation of what was ambiguous, and alternatives if applicable.\n"
        "Always set original_query to the input query text."
    ),
    output_schema=SchemaVerification,
    output_key="schema_verification",
)

3. Add a routing node after schema_verifier:

@node
def schema_route(ctx: Context, node_input: dict) -> Event:
    """Routes based on whether the query was ambiguous."""
    is_ambiguous = node_input.get("is_ambiguous", False)
    if is_ambiguous:
        corrected = node_input.get("corrected_query", "")
        if corrected:
            return Event(
                output=corrected,
                actions=EventActions(
                    state_delta={"sanitized_query": corrected, "schema_verification": node_input},
                    route="corrected"
                ),
            )
    return Event(
        output=ctx.state.get("sanitized_query", ""),
        actions=EventActions(
            state_delta={"schema_verification": node_input},
            route="clear"
        ),
    )

4. Update the QuerySageState to add:
   schema_verification: dict[str, Any] | None = None

5. Update the workflow edges. Change the chain from:
   [START, receive_query, validate_query, generate_sql, security_checkpoint]
   to:
   [START, receive_query, validate_query, schema_verifier, schema_route]
   
   Then add:
   (schema_route, {"clear": generate_sql, "corrected": generate_sql}),
   
   Both routes go to generate_sql, but the "corrected" route will have updated the sanitized_query in state so generate_sql uses the corrected version.

6. In fast_api_app.py ChatResponse, add:
   schema_verification: dict[str, Any] | None = None
   
   And extract it from session state alongside executor_output:
   schema_verification = updated_session.state.get("schema_verification")
   
   Pass it in the response:
   schema_verification=schema_verification,

This allows Streamlit to show the Schema Verification card when is_ambiguous is True, displaying the explanation and corrected query.
```

---

## Prompt 0C: Fix Insight Agent with Structured Output for Anomaly/Trend/Correlation Cards

```
In app/agent.py, update the insight_discovery agent to produce structured output instead of a single string.

1. Replace the InsightOutput schema with:

class InsightCard(BaseModel):
    category: str  # "anomaly", "trend", or "correlation"
    title: str
    description: str

class InsightOutput(BaseModel):
    anomaly: str = ""
    trend: str = ""
    correlation: str = ""
    follow_up_questions: list[str] = []

2. Update the insight_discovery agent instruction to:

insight_discovery = LlmAgent(
    name="insight_discovery",
    model="gemini-2.5-flash",
    instruction=(
        "You are a senior business intelligence analyst. "
        "Review the SQL query results stored in the workflow state (`executor_output`). "
        "You have access to the `neon_execute_sql` tool to perform additional SELECT queries "
        "if you want to dive deeper into the database to find anomalies, trends, or correlations. "
        "\n\nAnalyze the data BEYOND the user's original question and produce THREE structured sections:\n"
        "- anomaly: Describe any values that deviate significantly from expected norms. "
        "Example: 'Product X revenue is 3x higher than category average, suggesting a pricing anomaly or bulk order.'\n"
        "- trend: Describe any patterns over time or sequential dimensions. "
        "Example: 'Revenue has grown 15% month-over-month for the last 3 months.'\n"
        "- correlation: Describe relationships between different data columns or metrics. "
        "Example: 'Higher-priced products correlate with lower quantity but higher total revenue.'\n"
        "\nIf you cannot find a meaningful insight for a category, set it to an empty string.\n"
        "\nAlso generate exactly 3 follow-up natural language questions the user should ask next. "
        "These should be specific to the data returned, referencing actual product names, categories, or metrics from the results. "
        "Example: 'What is the quarterly revenue trend for Aria Desk Lamp?' or 'How does Nimbus Chair compare to other furniture items?'\n"
        "Do NOT generate generic questions. Make them data-driven and specific to the current results."
    ),
    tools=[FunctionTool(neon_execute_sql, require_confirmation=False)],
    output_schema=InsightOutput,
    output_key="insight_output",
)

3. Update the present_results node to handle the new structure. Where it currently checks for node_input.get("insights"), change it to handle the three fields:

    if isinstance(node_input, dict):
        anomaly = node_input.get("anomaly", "")
        trend = node_input.get("trend", "")
        correlation = node_input.get("correlation", "")
        questions = node_input.get("follow_up_questions", [])
        
        if anomaly:
            md_response += f"### Anomaly Detection\n{anomaly}\n\n"
        if trend:
            md_response += f"### Trend Analysis\n{trend}\n\n"
        if correlation:
            md_response += f"### Correlation Discovery\n{correlation}\n\n"
        if questions:
            md_response += "### Suggested Follow-up Questions\n"
            md_response += "\n".join(f"- {q}" for q in questions) + "\n"

4. Update Prompt 0A accordingly — the insight_data extracted from session state in fast_api_app.py should now include the structured fields:

   insight_output = updated_session.state.get("insight_output", {})
   if isinstance(insight_output, dict):
       follow_up_suggestions = insight_output.get("follow_up_questions", [])
       insight_data = {
           "anomaly": insight_output.get("anomaly", ""),
           "trend": insight_output.get("trend", ""),
           "correlation": insight_output.get("correlation", ""),
           "follow_up_questions": follow_up_suggestions,
       }
```

---

## Prompt 0D: Fix Graph/Chart Generation in Streamlit

```
The current chart rendering in streamlit_app.py has issues:
1. The "Show Charts" button is separate and often disabled
2. Chart rendering fails when chart_type from the agent doesn't match the data shape
3. The generate_chart() function in tools/neon_tools.py saves a file but Streamlit never uses it

Fix the chart logic in streamlit_app.py (this will be in the Graph tab from Prompt 4):

1. Remove the dependency on chart_type from the agent. Instead, ALWAYS try to generate both a bar chart and a pie chart from the available data:

   - Auto-detect: find the first categorical column (non-numeric) and the first numeric column
   - If both exist: render bar chart (categorical on x, numeric on y) AND pie chart (categorical as names, numeric as values)
   - If only numeric columns exist: render bar chart with index on x-axis
   - If no numeric columns: show a message "Data doesn't contain numeric values for charting"

2. Use plotly with dark theme settings:
   - template="plotly_dark"
   - paper_bgcolor="rgba(0,0,0,0)" (transparent)
   - plot_bgcolor="rgba(0,0,0,0)"
   - Bar chart colors: first bar #2DD4BF (teal), rest #0EA5E9 at 55% opacity
   - Pie chart colors: cycle through ["#E4572E", "#0EA5E9", "#8FCC00", "#B18CFF", "#F2A65A"]

3. Remove the old chart_enabled check and the separate "Show Charts" button — charts are now always attempted in the Graph tab.

4. The generate_chart() function in tools/neon_tools.py can stay as-is (it's used by the agent workflow internally), but Streamlit should NOT depend on it. Streamlit generates its own charts from the sql_results data.
```

---

## Prompt 1: Theme & Layout Overhaul

```
Redesign streamlit_app.py with a dark professional theme and new layout. Here are the exact requirements:

COLOR SCHEME (dark theme):
- Background: #0F172A (deep navy)
- Panel/Card background: #1E293B (dark slate)
- Card borders: #334155 (subtle gray)
- Primary text: #F1F5F9 (near white)
- Secondary text: #94A3B8 (muted slate)
- Accent 1 (brand): #E4572E (burnt orange) — for QuerySage logo text and highlights
- Accent 2 (charts): #2DD4BF (teal) — for primary chart bars and active states
- Accent 3 (CTA button): #CFFF3D (neon green-yellow) — for the "Run" button
- Accent 4 (info): #0EA5E9 (sky blue) — for verification cards and secondary highlights
- SQL text color: #E4572E (orange) in code blocks
- Success: #16A34A
- Warning: #F59E0B
- Error: #DC2626

LAYOUT STRUCTURE:
1. TOP BAR: Left side shows "QuerySage" brand name in orange (#E4572E) with a small sparkle icon. Right side shows a database selector dropdown (pill-shaped, dark bg).

2. QUERY BAR (centered, max-width 900px):
   - A rounded pill-shaped search input with a search icon on the left
   - Placeholder: "Ask a business question in plain English..."
   - A "Run →" button on the RIGHT SIDE inside the pill (neon green #CFFF3D background, dark text, bold)
   - NO separate "Show Result" or "Show Charts" buttons — only the Run button inside the search bar
   - User presses Enter or clicks Run to submit

3. SUGGESTION CHIPS (below query bar, centered):
   - Initially HIDDEN (empty state)
   - Only appear AFTER results come back from the agent
   - Show as follow-up suggestion pills with subtle border
   - Clicking a chip fills the query bar with that suggestion text
   - Suggestions come from the agent response (stored in session state as "follow_up_suggestions")

4. Remove the old two-column layout, the "Query Canvas" label, the text_area, and the separate "Show Result"/"Show Charts" buttons.

Apply all these CSS changes using st.markdown with <style> tags. Keep the existing functionality (submit_query function, HITL approval, session state) intact — only change the visual presentation and layout.
```

---

## Prompt 2: Schema Verification Card

```
Add a Schema Verification Card to streamlit_app.py that appears between the query bar and the results when the agent detects ambiguity or suggests a correction.

BEHAVIOR:
- When the master API returns status "success", check if the response contains a field called "query_suggestion" or "corrected_query" in the output
- If the agent's output contains phrases like "did you mean", "ambiguous", or suggests a rephrasing, show the verification card BEFORE showing results
- The card should have:
  - Sky blue (#0EA5E9) left accent border and icon (shield/check icon)
  - Label: "SCHEMA VERIFICATION" in uppercase sky blue
  - The agent's suggestion text explaining what was ambiguous
  - A "Suggested phrasing" box with the corrected query in orange text on a subtle dark panel
  - Two option buttons if applicable (e.g., "Revenue" / "Units sold") styled as pill buttons with sky blue border
  - A "Confirm & Run" button (neon green) that re-submits with the corrected query
- If no ambiguity detected, skip this card and show results directly

STYLING:
- Background: #0C4A6E (dark blue tint)
- Border: 1px solid rgba(14, 165, 233, 0.3)
- Border-radius: 16px
- Padding: 16px 20px
- The "Confirm & Run" button uses the neon green (#CFFF3D) background

For now, implement the UI structure. The actual query correction logic will come from the agent's response — just check if the response output contains correction/suggestion text and display it in this card format.
```

---

## Prompt 3: SQL Display (Collapsible)

```
Replace the current SQL display in streamlit_app.py with a collapsible SQL section that appears after query execution.

DESIGN:
- A collapsible panel with:
  - Header row: terminal icon + "GENERATED SQL" label (uppercase, muted) + a "Verified" badge (small pill, orange background #E4572E on dark, with a check icon)
  - Chevron arrow on the right that toggles open/close
  - Default state: OPEN (showing the SQL)
- SQL code displayed in monospace font, color #E4572E (orange) on dark background #1E293B
- Use st.expander or custom HTML for the collapsible behavior
- The panel has rounded corners (16px), subtle border (#334155)

Place this section between the verification card (if shown) and the results tabs.
```

---

## Prompt 4: Three-Tab Results Area

```
Replace the current two-tab layout (Resultset/Chart) in streamlit_app.py with a THREE-tab layout:

TABS: "ResultSet" | "Graph" | "Insight"

Tab styling:
- Tabs sit on a horizontal bar with bottom border
- Active tab has a 2.5px bottom border in neon green (#CFFF3D)
- Active tab text is white, inactive is muted gray (#64748B)
- Each tab has a small icon: table icon for ResultSet, bar-chart icon for Graph, lightbulb icon for Insight

TAB 1 — ResultSet:
- Display the dataframe in a styled dark table
- Header row: dark slate background (#334155), uppercase column names, muted text
- Alternating row colors: #1E293B and #1E293B with slight opacity variation
- Numbers in monospace font, right-aligned
- Use st.dataframe with dark theme or custom HTML table

TAB 2 — Graph:
- Show TWO charts side by side (2 columns):
  - Left: Bar chart with label "BAR CHART" and a small pill badge "best for ranking"
  - Right: Pie chart with label "SHARE OF TOTAL" and badge "best for proportion"
- Bar chart colors: first bar teal (#2DD4BF), remaining bars sky blue (#0EA5E9) at 55% opacity
- Pie chart colors: cycle through [#E4572E, #0EA5E9, #8FCC00, #B18CFF, #F2A65A]
- Use plotly with dark template, transparent background
- Charts in cards with rounded corners and subtle borders

TAB 3 — Insight (NEW):
- Display Agent Insights as styled cards, each with:
  - A colored icon on the left (30x30 rounded square with tinted background)
  - A label in uppercase (colored to match the icon)
  - Description text in muted white

Three insight card types:
1. ANOMALY DETECTION — orange icon (#E4572E), warning triangle icon
   Text comes from agent output — look for anomaly-related insights
2. TREND ANALYSIS — sky blue icon (#0EA5E9), trending-up icon
   Text comes from agent output — look for trend-related insights
3. CORRELATION DISCOVERY — teal icon (#2DD4BF), git-compare icon
   Text comes from agent output — look for correlation insights

If the agent doesn't provide structured insights, use the raw insight text from current_insights and display it in a single card.

Also add a "FOLLOW-UP SUGGESTIONS" section at the bottom of the Insight tab:
- Show 2-3 follow-up question suggestions as clickable pills
- These come from the agent's response (parse from output text or a dedicated field)
- Clicking a suggestion fills the query bar and submits automatically
- Store these in st.session_state.follow_up_suggestions
```

---

## Prompt 5: HITL Approval Redesign

```
Redesign the HITL SQL approval flow in streamlit_app.py to match the dark theme.

When status is "interrupted" (awaiting SQL approval):
- Show a prominent card with:
  - Dark red-tinted background: #1C1917 with red border rgba(220, 38, 38, 0.3)
  - Shield icon + "SQL EXECUTION APPROVAL REQUIRED" label in red
  - The SQL query displayed in orange monospace font inside a dark code block
  - A brief explanation: "The following SQL will be executed against Neon Postgres. Review and approve."

- Two buttons side by side:
  - "Approve & Execute" — neon green (#CFFF3D) background, dark text, bold, pill-shaped
  - "Reject" — transparent with red border, red text, pill-shaped

- Remove the old st.warning() and st.code() display
- Style everything with the dark theme colors
```

---

## Prompt 6: Sidebar Redesign

```
Redesign the sidebar in streamlit_app.py:

- Background: #0F172A (same as main bg, seamless)
- Remove the database selector from sidebar (it's now in the top bar)
- Keep "Session Controls" section with User ID and Session ID inputs, styled dark
- Keep "New Session" button — style as pill with subtle border
- Keep "Services Status" section — style the health indicators as small pills:
  - Online: small green dot + service name
  - Offline: small red dot + service name
- Add a "QuerySage" logo/brand section at the top of sidebar with version number
- Add a small "About" section at the bottom: "Built for Kaggle 5-Day AI Agents Course"
- All text in the sidebar should use the muted gray (#94A3B8) color
- Input fields: dark background (#1E293B), subtle border (#334155), light text
```

---

## Prompt 7: Loading States & Animations

```
Add polished loading states to streamlit_app.py:

1. QUERY PROCESSING:
   - When query is submitted, show a subtle loading animation below the query bar
   - Text: "Analyzing your question..." with a spinning wand icon (use st.spinner or custom CSS)
   - Use the orange color (#E4572E) for the spinner

2. SQL GENERATION:
   - After verification, show: "Writing query against verified schema..." with spinner
   - This appears inside the SQL collapsible panel

3. EXECUTION:
   - Show: "Executing against Neon Postgres..." with spinner
   - This appears in the results area

4. TRANSITION:
   - When results load, smoothly reveal the tabs and content
   - No jarring layout shifts

Keep the existing st.spinner for the main processing, but wrap it with custom styled HTML that matches the dark theme instead of the default Streamlit spinner appearance.
```

---

## Notes for All Prompts

- The file to modify is: `streamlit_app.py` in the project root
- Keep all existing backend logic intact: submit_query(), _get_auth_headers(), session state variables, MASTER_URL/GATEKEEPER_URL/SQL_ENGINE_URL env vars
- Keep the HITL approval flow working (awaiting_approval, interrupted_sql state)
- The app must work both locally (localhost) and deployed (Cloud Run with Agent Runtime URLs)
- Use st.markdown() with unsafe_allow_html=True for all custom CSS/HTML styling
- For icons, use Unicode characters or HTML entities (Streamlit doesn't support lucide-react)
- Test that the dark theme doesn't conflict with Streamlit's built-in theming
