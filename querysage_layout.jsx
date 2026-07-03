import React, { useState, useRef, useEffect } from "react";
import {
  BarChart, Bar, LineChart, Line, ScatterChart, Scatter, PieChart, Pie, Cell,
  CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts";
import {
  Sparkles, Database, Search, ChevronDown, ChevronRight, Terminal,
  CheckCircle2, AlertTriangle, TrendingUp, GitCompareArrows, Table2,
  BarChart3, Lightbulb, ArrowRight, Wand2, ShieldCheck,
} from "lucide-react";

const C = {
  bg: "#FBF9F4",
  panel: "#FFFFFF",
  panel2: "#F4F1E8",
  border: "#E6E1D3",
  borderSoft: "#EEEAE0",
  text: "#241F1A",
  textSoft: "#6B6252",
  textMute: "#A69E8C",
  orange: "#E4572E",
  orangeSoft: "#FBEAE4",
  sky: "#0EA5E9",
  skySoft: "#E4F4FC",
  neon: "#CFFF3D",
  neonDeep: "#8FCC00",
};
const DISPLAY = "'Space Grotesk', sans-serif";
const BODY = "'Inter', sans-serif";
const MONO = "'JetBrains Mono', monospace";

const SQL = `SELECT p.product_name, SUM(o.line_total) AS total_sales
FROM order_items o
JOIN products p ON p.product_id = o.product_id
WHERE o.order_date >= date_trunc('year', now())
GROUP BY p.product_name
ORDER BY total_sales DESC
LIMIT 5;`;

const ROWS = [
  { name: "Aria Desk Lamp", value: 184200 },
  { name: "Nimbus Chair", value: 162800 },
  { name: "Cobalt Monitor Arm", value: 141500 },
  { name: "Slate Keyboard", value: 118700 },
  { name: "Ridge Backpack", value: 97300 },
];

const PIE_COLORS = [C.orange, C.sky, C.neonDeep, "#B18CFF", "#F2A65A"];

function TopBar({ db, setDb }) {
  const [open, setOpen] = useState(false);
  const dbs = ["Neon Postgres — Production", "Neon Postgres — Staging", "QuerySage Sandbox"];
  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "14px 28px", borderBottom: `1px solid ${C.border}`, background: C.panel,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
        <div style={{ width: 28, height: 28, borderRadius: 8, background: C.neon, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Sparkles size={15} color={C.text} />
        </div>
        <span style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: 19, letterSpacing: -0.3, color: C.orange }}>QuerySage</span>
      </div>
      <div style={{ position: "relative" }}>
        <button
          onClick={() => setOpen(!open)}
          style={{
            display: "flex", alignItems: "center", gap: 8,
            background: C.panel2, border: `1px solid ${C.border}`, borderRadius: 999, padding: "7px 14px 7px 12px",
            cursor: "pointer", fontFamily: BODY, fontSize: 12.5, color: C.textSoft,
          }}
        >
          <Database size={13} color={C.sky} />
          <span style={{ color: C.text, fontWeight: 500 }}>{db}</span>
          <ChevronDown size={13} color={C.textMute} />
        </button>
        {open && (
          <div style={{ position: "absolute", top: "115%", right: 0, width: 260, background: C.panel, border: `1px solid ${C.border}`, borderRadius: 12, zIndex: 20, overflow: "hidden", boxShadow: "0 12px 32px rgba(36,31,26,0.12)" }}>
            {dbs.map((d) => (
              <div key={d} onClick={() => { setDb(d); setOpen(false); }}
                style={{ padding: "10px 14px", fontFamily: BODY, fontSize: 12.5, color: d === db ? C.orange : C.textSoft, cursor: "pointer", fontWeight: d === db ? 600 : 400 }}>
                {d}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function QueryBar({ value, setValue, onSubmit, disabled }) {
  return (
    <div style={{ padding: "22px 28px 8px" }}>
      <div style={{
        maxWidth: 980, margin: "0 auto",
        display: "flex", alignItems: "center", gap: 12,
        background: C.panel, border: `1.5px solid ${C.border}`, borderRadius: 999,
        padding: "8px 8px 8px 20px", boxShadow: "0 1px 2px rgba(36,31,26,0.04)",
      }}>
        <Search size={17} color={C.textMute} />
        <input
          value={value}
          disabled={disabled}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !disabled && onSubmit()}
          placeholder="Ask a business question in plain English…"
          style={{
            flex: 1, background: "transparent", border: "none", outline: "none",
            color: C.text, fontFamily: BODY, fontSize: 15, padding: "8px 0",
          }}
        />
        <button
          onClick={onSubmit}
          disabled={disabled}
          style={{
            display: "flex", alignItems: "center", gap: 6,
            background: C.neon, color: C.text, border: "none", borderRadius: 999,
            padding: "11px 20px", fontFamily: DISPLAY, fontWeight: 700, fontSize: 13.5,
            cursor: disabled ? "default" : "pointer", opacity: disabled ? 0.5 : 1,
          }}
        >
          Run <ArrowRight size={14} />
        </button>
      </div>
      <div style={{ maxWidth: 980, margin: "10px auto 0", display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "center" }}>
        {["Top 5 products by sales this year", "QoQ revenue for Aria Desk Lamp", "Marketing spend vs revenue"].map((ex) => (
          <button key={ex} onClick={() => setValue(ex)} style={{
            background: "transparent", border: `1px solid ${C.border}`, borderRadius: 999,
            padding: "6px 12px", fontFamily: BODY, fontSize: 12, color: C.textSoft, cursor: "pointer",
          }}>{ex}</button>
        ))}
      </div>
    </div>
  );
}

function VerificationCard({ stage, onResolve }) {
  const [picked, setPicked] = useState(null);
  if (stage === "idle") return null;

  const resolved = stage === "confirmed" || stage === "sql" || stage === "results";

  return (
    <div style={{ maxWidth: 980, margin: "18px auto 0", padding: "0 28px" }}>
      <div style={{
        background: C.skySoft, border: `1px solid ${C.sky}44`, borderRadius: 16,
        padding: "16px 20px", display: "flex", gap: 14,
      }}>
        <div style={{
          width: 32, height: 32, minWidth: 32, borderRadius: 10, background: C.panel,
          display: "flex", alignItems: "center", justifyContent: "center", border: `1px solid ${C.sky}55`,
        }}>
          <ShieldCheck size={16} color={C.sky} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: DISPLAY, fontSize: 10.5, letterSpacing: 0.6, textTransform: "uppercase", color: C.sky, marginBottom: 5 }}>
            Schema verification
          </div>

          {!resolved ? (
            <>
              <div style={{ fontFamily: BODY, fontSize: 13.5, color: C.text, marginBottom: 10, lineHeight: 1.5 }}>
                I found a <b>products</b> and <b>order_items</b> table that match your question, but "top" is ambiguous —
                did you mean by <b>revenue</b> or by <b>units sold</b>?
              </div>
              <div style={{
                background: C.panel, border: `1px dashed ${C.sky}66`, borderRadius: 10, padding: "9px 12px",
                fontFamily: MONO, fontSize: 12, color: C.textSoft, marginBottom: 12,
              }}>
                Suggested phrasing: <span style={{ color: C.orange }}>"Top 5 products by total revenue this year"</span>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                {["Revenue", "Units sold"].map((opt) => (
                  <button key={opt} onClick={() => setPicked(opt)} style={{
                    background: picked === opt ? C.sky : "transparent",
                    color: picked === opt ? "#fff" : C.sky,
                    border: `1.5px solid ${C.sky}`, borderRadius: 999, padding: "6px 14px",
                    fontFamily: BODY, fontSize: 12.5, fontWeight: 600, cursor: "pointer",
                  }}>{opt}</button>
                ))}
                <button
                  onClick={() => picked && onResolve()}
                  disabled={!picked}
                  style={{
                    marginLeft: "auto", display: "flex", alignItems: "center", gap: 6,
                    background: picked ? C.neon : C.borderSoft, color: C.text, border: "none",
                    borderRadius: 999, padding: "6px 16px", fontFamily: DISPLAY, fontWeight: 700,
                    fontSize: 12.5, cursor: picked ? "pointer" : "default", opacity: picked ? 1 : 0.6,
                  }}
                >
                  Confirm & run <CheckCircle2 size={14} />
                </button>
              </div>
            </>
          ) : (
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontFamily: BODY, fontSize: 13, color: C.text }}>
              <CheckCircle2 size={15} color={C.sky} />
              Confirmed: <b>Top 5 products by total revenue this year</b>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SqlCollapsible({ stage }) {
  const [open, setOpen] = useState(true);
  if (stage === "idle" || stage === "verifying") return null;
  const generating = stage === "confirmed";

  return (
    <div style={{ maxWidth: 980, margin: "16px auto 0", padding: "0 28px" }}>
      <div style={{ background: C.panel, border: `1px solid ${C.borderSoft}`, borderRadius: 16, overflow: "hidden" }}>
        <button
          onClick={() => setOpen(!open)}
          style={{
            width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
            background: "transparent", border: "none", padding: "13px 18px", cursor: "pointer",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Terminal size={14} color={C.textMute} />
            <span style={{ fontFamily: DISPLAY, fontSize: 11.5, letterSpacing: 0.6, textTransform: "uppercase", color: C.textMute }}>
              Generated SQL
            </span>
            {!generating && (
              <span style={{
                display: "flex", alignItems: "center", gap: 4, background: C.orangeSoft, color: C.orange,
                borderRadius: 999, padding: "2px 9px", fontFamily: BODY, fontSize: 11, fontWeight: 600, marginLeft: 4,
              }}>
                <CheckCircle2 size={11} /> Verified
              </span>
            )}
          </div>
          <ChevronRight size={16} color={C.textMute} style={{ transform: open ? "rotate(90deg)" : "none", transition: "transform 0.15s" }} />
        </button>
        {open && (
          <div style={{ borderTop: `1px solid ${C.borderSoft}`, padding: "14px 18px" }}>
            {generating ? (
              <div style={{ display: "flex", alignItems: "center", gap: 8, fontFamily: BODY, fontSize: 13, color: C.textSoft }}>
                <Wand2 size={14} color={C.orange} className="spin" /> Writing query against verified schema…
              </div>
            ) : (
              <pre style={{ margin: 0, fontFamily: MONO, fontSize: 12.5, lineHeight: 1.7, color: C.orange, overflowX: "auto" }}>
                {SQL}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function TabsBar({ tab, setTab, disabled }) {
  const tabs = [
    { id: "result", label: "ResultSet", icon: Table2 },
    { id: "graph", label: "Graph", icon: BarChart3 },
    { id: "insight", label: "Insight", icon: Lightbulb },
  ];
  return (
    <div style={{ display: "flex", gap: 4, marginTop: 22, borderBottom: `1px solid ${C.border}` }}>
      {tabs.map((t) => {
        const Icon = t.icon;
        const active = tab === t.id;
        return (
          <button
            key={t.id}
            onClick={() => !disabled && setTab(t.id)}
            style={{
              display: "flex", alignItems: "center", gap: 7, padding: "10px 6px", marginRight: 22,
              background: "transparent", border: "none", cursor: disabled ? "default" : "pointer",
              borderBottom: `2.5px solid ${active ? C.neonDeep : "transparent"}`,
              color: active ? C.text : C.textMute, fontFamily: DISPLAY, fontSize: 13, fontWeight: 600,
              opacity: disabled ? 0.4 : 1,
            }}
          >
            <Icon size={14} color={active ? C.orange : C.textMute} /> {t.label}
          </button>
        );
      })}
    </div>
  );
}

function ResultTab() {
  return (
    <div style={{ border: `1px solid ${C.borderSoft}`, borderRadius: 12, overflow: "hidden" }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", background: C.panel2, padding: "10px 16px", fontFamily: DISPLAY, fontSize: 11, color: C.textMute, textTransform: "uppercase", letterSpacing: 0.5 }}>
        <span>Product</span><span style={{ textAlign: "right" }}>Total sales</span>
      </div>
      {ROWS.map((r, i) => (
        <div key={r.name} style={{ display: "grid", gridTemplateColumns: "1fr 1fr", padding: "11px 16px", borderTop: `1px solid ${C.borderSoft}`, fontFamily: BODY, fontSize: 13.5, color: C.textSoft, background: i % 2 ? "transparent" : C.panel2 + "80" }}>
          <span style={{ color: C.text, fontWeight: 500 }}>{r.name}</span>
          <span style={{ textAlign: "right", fontFamily: MONO }}>${r.value.toLocaleString()}</span>
        </div>
      ))}
    </div>
  );
}

function GraphTab() {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
      <div style={{ background: C.panel, border: `1px solid ${C.borderSoft}`, borderRadius: 14, padding: "16px 18px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
          <span style={{ fontFamily: DISPLAY, fontSize: 11, letterSpacing: 0.5, textTransform: "uppercase", color: C.textMute }}>Bar chart</span>
          <span style={{ fontFamily: BODY, fontSize: 10.5, color: C.orange, background: C.orangeSoft, borderRadius: 999, padding: "2px 8px" }}>best for ranking</span>
        </div>
        <ResponsiveContainer width="100%" height={230}>
          <BarChart data={ROWS} margin={{ top: 6, right: 6, left: 0, bottom: 0 }}>
            <CartesianGrid stroke={C.borderSoft} vertical={false} />
            <XAxis dataKey="name" tick={{ fill: C.textMute, fontSize: 10, fontFamily: BODY }} axisLine={{ stroke: C.border }} tickLine={false} interval={0} angle={-18} textAnchor="end" height={50} />
            <YAxis tick={{ fill: C.textMute, fontSize: 10, fontFamily: BODY }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: C.panel, border: `1px solid ${C.border}`, borderRadius: 8, fontFamily: BODY, fontSize: 12 }} cursor={{ fill: "rgba(207,255,61,0.15)" }} />
            <Bar dataKey="value" radius={[5, 5, 0, 0]}>
              {ROWS.map((_, i) => <Cell key={i} fill={i === 0 ? C.neonDeep : C.sky} fillOpacity={i === 0 ? 1 : 0.55} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div style={{ background: C.panel, border: `1px solid ${C.borderSoft}`, borderRadius: 14, padding: "16px 18px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
          <span style={{ fontFamily: DISPLAY, fontSize: 11, letterSpacing: 0.5, textTransform: "uppercase", color: C.textMute }}>Share of total</span>
          <span style={{ fontFamily: BODY, fontSize: 10.5, color: C.sky, background: C.skySoft, borderRadius: 999, padding: "2px 8px" }}>best for proportion</span>
        </div>
        <ResponsiveContainer width="100%" height={230}>
          <PieChart>
            <Pie data={ROWS} dataKey="value" nameKey="name" innerRadius={52} outerRadius={82} paddingAngle={2}>
              {ROWS.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
            </Pie>
            <Tooltip contentStyle={{ background: C.panel, border: `1px solid ${C.border}`, borderRadius: 8, fontFamily: BODY, fontSize: 12 }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function InsightCard({ icon: Icon, label, accent, children }) {
  return (
    <div style={{ background: C.panel, border: `1px solid ${C.borderSoft}`, borderRadius: 14, padding: "14px 16px", display: "flex", gap: 12 }}>
      <div style={{ width: 30, height: 30, minWidth: 30, borderRadius: 9, background: `${accent}1A`, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Icon size={15} color={accent} />
      </div>
      <div>
        <div style={{ fontFamily: DISPLAY, fontSize: 11, letterSpacing: 0.5, textTransform: "uppercase", color: accent, marginBottom: 4 }}>{label}</div>
        <div style={{ fontFamily: BODY, fontSize: 13, lineHeight: 1.55, color: C.textSoft }}>{children}</div>
      </div>
    </div>
  );
}

function InsightTab() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <InsightCard icon={AlertTriangle} label="Anomaly" accent={C.orange}>
        Cobalt Monitor Arm sales jumped 38% in the last two weeks — well outside its usual weekly range.
      </InsightCard>
      <InsightCard icon={TrendingUp} label="Trend" accent={C.sky}>
        Aria Desk Lamp has held the #1 spot for six consecutive months, growing 12% quarter over quarter.
      </InsightCard>
      <InsightCard icon={GitCompareArrows} label="Correlation" accent={C.neonDeep}>
        Products bundled with a desk mat see a 22% higher attach rate on average.
      </InsightCard>
    </div>
  );
}

export default function QuerySageLayout() {
  const [db, setDb] = useState("Neon Postgres — Production");
  const [query, setQuery] = useState("");
  const [stage, setStage] = useState("idle"); // idle -> verifying -> confirmed -> sql -> results
  const [tab, setTab] = useState("result");
  const timers = useRef([]);

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const submit = () => {
    if (!query.trim() || stage !== "idle") return;
    setStage("verifying");
  };

  const resolveVerification = () => {
    setStage("confirmed");
    timers.current.push(setTimeout(() => setStage("sql"), 900));
    timers.current.push(setTimeout(() => setStage("results"), 1500));
  };

  const resultsReady = stage === "results";

  return (
    <div style={{ background: C.bg, minHeight: 780, fontFamily: BODY, borderRadius: 12, overflow: "hidden" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
        * { box-sizing: border-box; }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg);} to { transform: rotate(360deg);} }
        ::placeholder { color: ${C.textMute}; }
      `}</style>

      <TopBar db={db} setDb={setDb} />
      <QueryBar value={query} setValue={setQuery} onSubmit={submit} disabled={stage !== "idle"} />
      <VerificationCard stage={stage} onResolve={resolveVerification} />
      <SqlCollapsible stage={stage} />

      {(stage === "sql" || stage === "results") && (
        <div style={{ maxWidth: 980, margin: "0 auto", padding: "0 28px 32px" }}>
          <TabsBar tab={tab} setTab={setTab} disabled={!resultsReady} />
          <div style={{ paddingTop: 18 }}>
            {!resultsReady ? (
              <div style={{ display: "flex", alignItems: "center", gap: 8, fontFamily: BODY, fontSize: 13, color: C.textSoft, padding: "24px 0" }}>
                <Wand2 size={14} color={C.orange} className="spin" /> Executing against Neon Postgres…
              </div>
            ) : (
              <>
                {tab === "result" && <ResultTab />}
                {tab === "graph" && <GraphTab />}
                {tab === "insight" && <InsightTab />}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
