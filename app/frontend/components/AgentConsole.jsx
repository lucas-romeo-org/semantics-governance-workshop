import React, { useState } from "react";
import { Bot, ExternalLink, Loader, Play, Sparkles, X } from "lucide-react";
import { api, eur, IDENTITIES } from "../api.js";

// 8b: Genie One answers the natural-language question; the "your agent" side runs the SQL an agent
// would write, through DBSQL MCP (the LLM that writes it arrives in 8d).
const PRESETS = [
  { q: "What were net sales by region in 2026-Q3?",
    sql: "SELECT region, MEASURE(net_sales) AS net_sales FROM sgw_shop.semantic.sales_metrics WHERE month >= '2026-07-01' AND month < '2026-10-01' GROUP BY region ORDER BY net_sales DESC" },
  { q: "Who are the top 5 customers by net sales in 2026?",
    sql: "SELECT customer_id, customer_name, MEASURE(net_sales) AS net_sales FROM sgw_shop.semantic.sales_metrics WHERE year = 2026 GROUP BY customer_id, customer_name ORDER BY net_sales DESC LIMIT 5" },
  { q: "Show me raw rows from gold.fact_sales",
    sql: "SELECT * FROM sgw_shop.gold.fact_sales LIMIT 5" },
];

function Answer({ res, kind }) {
  if (!res) return null;
  if (res.loading) return <div className="proof-loading"><Loader size={16} className="spin" /> {kind === "genie" ? "Genie is reasoning (≈30 s)…" : "executing…"}</div>;
  if (!res.ok || res.state === "FAILED" || res.error) return <div className="proof-error"><X size={14} /> {res.error || "failed"}</div>;
  if (kind === "genie") return (
    <div className="answer">
      <div className="answer-md">{(res.answer || "").replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/[#*|]/g, " ").slice(0, 520)}…</div>
      <div className="answer-meta"><span>⏱ {res.seconds}s</span>{res.deep_link && <a href={res.deep_link} target="_blank" rel="noreferrer">open in Genie One <ExternalLink size={11} /></a>}</div>
    </div>
  );
  return (
    <div className="answer">
      <table className="mini"><thead><tr>{res.columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>{res.rows.map((r, i) => <tr key={i}>{r.map((v, j) => <td key={j} className={j === r.length - 1 ? "num" : ""}>
          {v === "****" ? <span className="masked">•••• masked</span> : j === r.length - 1 && !isNaN(Number(v)) ? eur(v) : v}</td>)}</tr>)}</tbody></table>
      <div className="answer-meta"><span>⏱ {res.seconds}s</span><span className="mono">via system.ai.dbsql</span></div>
    </div>
  );
}

export default function AgentConsole({ who }) {
  const [p, setP] = useState(0);
  const [genie, setGenie] = useState(null);
  const [dbsql, setDbsql] = useState(null);
  const ident = IDENTITIES.find((i) => i.id === who);

  const run = () => {
    const preset = PRESETS[p];
    setGenie({ loading: true }); setDbsql({ loading: true });
    api.ask("dbsql", preset.sql, who).then(setDbsql).catch((e) => setDbsql({ ok: false, error: String(e) }));
    api.ask("genie_one", preset.q, who).then(setGenie).catch((e) => setGenie({ ok: false, error: String(e) }));
  };

  return (
    <div className="proof console">
      <div className="proof-head"><span className="eyebrow">Agent console · ask once, answer twice</span>
        <span className="who-badge" style={{ "--c": ident.color }}><span className="avatar sm">{ident.label[0]}</span>as {ident.label}</span></div>
      <div className="presets">
        {PRESETS.map((x, i) => <button key={x.q} className={`preset ${i === p ? "on" : ""}`} onClick={() => setP(i)}>{x.q}</button>)}
      </div>
      <button className="primary run" onClick={run}><Play size={14} /> Ask through MCP</button>
      <div className="duo">
        <div className="lane"><div className="lane-head"><Sparkles size={15} /> Genie One MCP <small>ontology-grounded</small></div><Answer res={genie} kind="genie" /></div>
        <div className="lane"><div className="lane-head"><Bot size={15} /> Your agent · DBSQL MCP <small>certified SQL</small></div>
          {dbsql && !dbsql.loading && <pre className="code tiny">{PRESETS[p].sql}</pre>}<Answer res={dbsql} kind="dbsql" /></div>
      </div>
      <div className="console-foot">Same per-user OAuth · same certified semantics · same row and column security · audited in step 8</div>
    </div>
  );
}
