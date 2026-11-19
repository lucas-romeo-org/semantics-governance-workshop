import React, { useState } from "react";
import { Bot, ExternalLink, Loader, Play, Sparkles, X } from "lucide-react";
import { api, eur, IDENTITIES } from "../api.js";

// Ask once, answer twice: Genie One MCP (ontology-grounded) vs "your agent" (an LLM that writes SQL
// against the certified Metric Views and runs it through DBSQL MCP). Data is always read as the selected identity.
const PRESETS = [
  "What were net sales by region in 2026-Q3 versus budget?",
  "Who are the top 5 customers by net sales in 2026?",
  "How did net sales grow year over year in 2026, month by month?",
  "Show me raw rows from gold.fact_sales",
];

const clean = (t) => (t || "").replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/^#+\s*/gm, "").replace(/\*\*/g, "")
  .split("\n").filter((l) => l.trim() && !l.trim().startsWith("|")).join("\n");

function Clamp({ text }) {
  const [more, setMore] = useState(false);
  return (<>
    <div className={`answer-md ${more ? "" : "clamp"}`}>{clean(text)}</div>
    {clean(text).length > 220 && <button className="link-btn" onClick={() => setMore(!more)}>{more ? "show less" : "show more"}</button>}
  </>);
}

function Cell({ v, last }) {
  if (v === "****") return <span className="masked">•••• masked</span>;
  if (last && v !== null && v !== "" && !isNaN(Number(v)) && Math.abs(Number(v)) > 50) return eur(v);
  return v;
}

function Rows({ columns, rows }) {
  if (!rows?.length) return null;
  return (
    <table className="mini"><thead><tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
      <tbody>{rows.slice(0, 8).map((r, i) => <tr key={i}>{r.map((v, j) => <td key={j} className={j === r.length - 1 ? "num" : ""}><Cell v={v} last={j === r.length - 1} /></td>)}</tr>)}</tbody></table>
  );
}

function GenieLane({ res }) {
  if (!res) return <div className="lane-empty">Genie reasons over the ontology: Metric Views, Pages, certification.</div>;
  if (res.loading) return <div className="proof-loading"><Loader size={16} className="spin" /> Genie is reasoning (≈30–40 s)…</div>;
  if (!res.ok) return <div className="proof-error"><X size={14} /> {res.error}</div>;
  return (
    <div className="answer"><Clamp text={res.answer} />
      <div className="answer-meta"><span>⏱ {res.seconds}s</span>{res.deep_link && <a href={res.deep_link} target="_blank" rel="noreferrer">open in Genie One <ExternalLink size={11} /></a>}</div>
    </div>
  );
}

function AgentLane({ res }) {
  if (!res) return <div className="lane-empty">An LLM writes SQL on the certified Metric Views; DBSQL MCP runs it as you.</div>;
  if (res.loading) return <div className="proof-loading"><Loader size={16} className="spin" /> the agent is writing and running SQL…</div>;
  if (!res.ok) return <div className="proof-error"><X size={14} /> {res.error}</div>;
  const last = [...(res.calls || [])].reverse().find((c) => c.rows?.length) || res.calls?.[res.calls.length - 1];
  return (
    <div className="answer">
      <Clamp text={res.answer} />
      {res.calls?.map((c, i) => (
        <div key={i} className={`call ${c.state === "SUCCEEDED" ? "" : "bad"}`}>
          <span className="eyebrow">tool call {i + 1} · execute_sql · {c.state === "SUCCEEDED" ? "ok" : "rejected"}</span>
          <pre className="code tiny">{c.sql}</pre>
          {c.error && <div className="proof-error"><X size={13} /> {c.error.split("\n")[0].slice(0, 160)}</div>}
        </div>
      ))}
      {last && <Rows columns={last.columns} rows={last.rows} />}
      <div className="answer-meta"><span>⏱ {res.seconds}s</span><span className="mono">LLM {res.model} as app · SQL as user</span></div>
    </div>
  );
}

export default function AgentConsole({ who }) {
  const [q, setQ] = useState(PRESETS[0]);
  const [genie, setGenie] = useState(null);
  const [agentRes, setAgentRes] = useState(null);
  const ident = IDENTITIES.find((i) => i.id === who);

  const run = () => {
    setGenie({ loading: true }); setAgentRes({ loading: true });
    api.agent(q, who).then(setAgentRes).catch((e) => setAgentRes({ ok: false, error: String(e) }));
    api.ask("genie_one", q, who).then(setGenie).catch((e) => setGenie({ ok: false, error: String(e) }));
  };

  return (
    <div className="proof console">
      <div className="proof-head"><span className="eyebrow">Agent console · ask once, answer twice</span>
        <span className="who-badge" style={{ "--c": ident.color }}><span className="avatar sm">{ident.label[0]}</span>as {ident.label}</span></div>
      <div className="ask">
        <input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && run()} aria-label="Question" />
        <button className="primary" onClick={run}><Play size={14} /> Ask</button>
      </div>
      <div className="presets">{PRESETS.map((x) => <button key={x} className={`preset ${x === q ? "on" : ""}`} onClick={() => setQ(x)}>{x}</button>)}</div>
      <div className="duo">
        <div className="lane"><div className="lane-head"><Sparkles size={15} /> Genie One MCP <small>system.ai.genie_one_mcp</small></div><GenieLane res={genie} /></div>
        <div className="lane"><div className="lane-head"><Bot size={15} /> Your agent · DBSQL MCP <small>system.ai.dbsql</small></div><AgentLane res={agentRes} /></div>
      </div>
      <div className="console-foot">Same per-user OAuth · same certified semantics · same row and column security · audited in step 8</div>
    </div>
  );
}
