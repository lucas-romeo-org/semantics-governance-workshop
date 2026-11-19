import React, { useEffect, useState } from "react";
import { Check, ExternalLink, Loader, Lock, X } from "lucide-react";
import { api, cleanMd, eur, IDENTITIES, pct, shortName } from "../api.js";

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
  if (!data.ok && k === "activity") return <div className="big-fact denied"><Lock size={18} /> <span><b>Restricted.</b> Operate views are for platform and security admins only.<small className="mono">{data.error}</small></span></div>;
  if (!data.ok && k !== "gold_access") return <div className="proof-error"><X size={14} /> {data.error}</div>;
  switch (k) {
    case "whoami": {
      const [name, groups] = data.rows[0];
      return (<>
        <div className="big-fact"><Check size={18} /> <span>Databricks sees <b>{name}</b></span></div>
        <div className="group-chips">{groups.length ? groups.map((g) => <span key={g} className="gchip">{g}</span>)
          : <span className="muted-line">no wk_* groups (builders and admins get access through ownership)</span>}</div>
      </>);
    }
    case "genie_agent":
      return (<>
        {data.answer && <div className="answer-md small clamp">{cleanMd(data.answer)}</div>}
        {data.rows?.length > 0 && <Bars rows={data.rows.map((r) => [r[0], r[r.length - 1]])} />}
        {data.sql && <pre className="code tiny">{data.sql}</pre>}
      </>);
    case "activity":
      return (
        <div className="feed">{data.rows.map((r, i) => (
          <div key={i} className={`feed-row ${r[5] === "FAILED" ? "bad" : ""}`}>
            <span className="mono">{r[0]}</span><b title={r[1]}>{shortName(r[1])}</b>
            <span className={`surf s-${(r[2] || "").replace(/[^a-z]/gi, "").toLowerCase()}`}>{r[2]}</span>
            <span className="obj"><i className={`layer l-${r[3]}`} />{r[4] || "·"}</span>
            <span className={`st ${r[5] === "FAILED" ? "bad" : "ok"}`}>{r[5] === "FAILED" ? "blocked" : "ok"}</span>
          </div>))}
        </div>
      );
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
  certification: "What is official", activity: "Latest activity on the workshop catalog (ops.semantic_activity)",
  genie_agent: "Genie Agent · “Net sales by region in 2026-Q3?”",
};

export default function Proof({ step, who }) {
  const k = step.proof;
  const [data, setData] = useState(null);
  const live = k && !["none", "agent_console"].includes(k);

  useEffect(() => {
    if (!live) return;
    let alive = true;
    setData(null);
    api.proof(k, who).then((d) => alive && setData(d)).catch((e) => alive && setData({ ok: false, error: String(e) }));
    return () => { alive = false; };
  }, [k, who, live]);

  if (k === "none") return null;
  return (
    <div className="proof">
      <div className="proof-head"><span className="eyebrow">Live · {TITLES[k]}</span><Who who={who} /></div>
      {data ? <Body k={k} data={data} who={who} /> : <div className="proof-loading"><Loader size={16} className="spin" /> {k === "genie_agent" ? "asking the Genie Agent (≈20 s)…" : "querying…"}</div>}
    </div>
  );
}
