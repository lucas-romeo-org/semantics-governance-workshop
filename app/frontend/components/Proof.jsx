import React, { useEffect, useState } from "react";
import { Check, ExternalLink, Loader, Lock, X } from "lucide-react";
import { api, eur, IDENTITIES, pct } from "../api.js";
import AgentConsole from "./AgentConsole.jsx";

const Who = ({ who }) => {
  const i = IDENTITIES.find((x) => x.id === who);
  return <span className="who-badge" style={{ "--c": i.color }}><span className="avatar sm">{i.label[0]}</span>as {i.label}{who !== "me" && <em> · simulated persona</em>}</span>;
};

function Bars({ rows, label = (r) => r[0], value = (r) => Number(r[1]), fmt = eur, extra }) {
  const max = Math.max(...rows.map(value), 1);
  return (
    <div className="bars">
      {rows.map((r) => (
        <div className="bar-row" key={label(r)}>
          <span className="bar-label">{label(r)}</span>
          <span className="bar-track"><span className="bar-fill" style={{ width: `${(value(r) / max) * 100}%` }} /></span>
          <span className="bar-value">{fmt(value(r))}</span>
          {extra && <span className="bar-extra">{extra(r)}</span>}
        </div>
      ))}
    </div>
  );
}

function Body({ k, data, who }) {
  if (!data.ok && k !== "gold_access") return <div className="proof-error"><X size={14} /> {data.error}</div>;
  switch (k) {
    case "whoami":
      return <div className="big-fact"><Check size={18} /> Databricks sees <b>{data.rows[0][0]}</b></div>;
    case "gold_access":
      return data.ok
        ? <div className="big-fact warn"><Lock size={18} /> gold is readable: {Number(data.rows[0][0]).toLocaleString()} lines <small>(builders only)</small></div>
        : <div className="big-fact denied"><X size={18} /> <span><b>Denied.</b> Consumers can't read gold.<small className="mono">{data.error}</small></span></div>;
    case "net_sales":
      return <Bars rows={data.rows} extra={(r) => <span className="mono">margin {pct(r[2])} · share {pct(r[3])}</span>} />;
    case "top_customers":
      return (
        <table className="mini">
          <thead><tr><th>Customer</th><th>Name</th><th className="num">Net sales 2026</th></tr></thead>
          <tbody>{data.rows.map((r) => (
            <tr key={r[0]}><td className="mono">#{r[0]}</td><td>{r[1] === "****" ? <span className="masked">•••• masked</span> : r[1]}</td><td className="num">{eur(r[2])}</td></tr>
          ))}</tbody>
        </table>
      );
    case "legacy": {
      const [leg, gov] = data.rows.map((r) => Number(r[1]));
      if (!leg || !gov) return <div className="big-fact">Spain is not visible for this identity: the legacy view returns nothing.</div>;
      return (<>
        <Bars rows={data.rows} />
        <div className="delta">Same KPI, two numbers: the legacy view overstates Spain by <b>{eur(leg - gov)}</b> ({pct((leg - gov) / gov)}) because it ignores discounts.</div>
      </>);
    }
    case "certification":
      return (
        <div className="cert-list">{data.rows.map((r) => (
          <span key={r[0]} className={`cert ${r[1]}`}>{r[1] === "certified" ? <Check size={13} /> : <X size={13} />}{r[0]}<em>{r[1]}</em></span>
        ))}</div>
      );
    default:
      return null;
  }
}

const TITLES = {
  whoami: "Who Databricks sees", gold_access: "Try to read gold", net_sales: "Net sales by region (certified Metric View)",
  top_customers: "Top 5 customers 2026: PII as the policy decides", legacy: "The problem in one number · ES Sep-2026",
  certification: "What is official", activity: "Every query, attributed",
};

export default function Proof({ step, who }) {
  const k = step.proof;
  const [data, setData] = useState(null);
  const live = k && !["none", "agent_console", "activity"].includes(k);

  useEffect(() => {
    if (!live) return;
    let alive = true;
    setData(null);
    api.proof(k, who).then((d) => alive && setData(d)).catch((e) => alive && setData({ ok: false, error: String(e) }));
    return () => { alive = false; };
  }, [k, who, live]);

  if (k === "agent_console") return <AgentConsole who={who} />;
  if (k === "none") return null;
  if (k === "activity") return (
    <div className="proof"><div className="proof-head"><span className="eyebrow">{TITLES.activity}</span></div>
      <p className="muted-line">Questions asked in this app show up in <b>Governance in action</b>, attributed to the real person and surface.</p></div>
  );
  return (
    <div className="proof">
      <div className="proof-head"><span className="eyebrow">Live · {TITLES[k]}</span><Who who={who} /></div>
      {data ? <Body k={k} data={data} who={who} /> : <div className="proof-loading"><Loader size={16} className="spin" /> querying…</div>}
    </div>
  );
}
