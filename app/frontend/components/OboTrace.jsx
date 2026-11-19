import React, { useState } from "react";
import { Activity, AppWindow, Bot, Check, Copy, Fingerprint, Network, ShieldCheck, User, X } from "lucide-react";
import { IDENTITIES } from "../api.js";
import { useTrace } from "../trace.js";

// "On behalf of the user", live: the path every MCP call takes, lit by the chat's events.
export default function OboTrace({ who, info, onJump }) {
  const t = useTrace();
  const ident = IDENTITIES.find((i) => i.id === who);
  const calls = t.order.map((id) => t.calls[id]);
  const last = t.calls[t.last];
  const anyFail = calls.some((c) => c.status === "fail");
  const started = t.phase !== "idle";
  const simulated = who !== "me";
  const principal = t.identity?.principal || (simulated ? `sgw-persona-${who}` : info?.user || "you");

  // stage state: idle · live · ok · fail
  const reach = (n) => {
    if (!started) return "idle";
    if (!last) return n <= 3 ? "live" : "idle";
    if (last.status === "running") return n <= 3 ? "ok" : n === 4 ? "live" : "idle";
    if (last.status === "fail") return n === 5 ? "fail" : "ok";      // blocked attempts are audited too
    return "ok";
  };

  const stages = [
    { icon: User, title: `${ident.label} signs in`, sub: simulated ? "persona · same groups as the person" : "SSO through the corporate IdP",
      chips: [{ t: principal, k: "user" }] },
    { icon: AppWindow, title: "The client", sub: "this app, inside Databricks Apps, plays the MCP client",
      chips: [{ t: "same role as Claude · ChatGPT", k: "neutral" }] },
    { icon: Fingerprint, title: "A token for that person", sub: simulated ? "OAuth M2M of the persona (simulation)" : "OBO · your OAuth token, never a shared account",
      chips: simulated ? [{ t: "oauth-m2m", k: "entry" }] : [{ t: "sql", k: "entry" }, { t: "ai-gateway", k: "entry" }, { t: "dashboards.genie", k: "entry" }] },
    { icon: Network, title: "Unity Gateway · MCP", sub: last ? `${last.server} → ${last.tool}` : "genie_one_mcp · dbsql",
      chips: calls.length ? [{ t: `${calls.length} tool call${calls.length > 1 ? "s" : ""}`, k: "neutral" }] : [] },
    { icon: ShieldCheck, title: `Unity Catalog decides as ${ident.label}`, sub: last?.status === "fail" ? (last.error || "").split(":")[0].slice(0, 60) : "grants · row filters · column masks",
      chips: who === "me" ? [{ t: "your grants", k: "exec" }] : [{ t: `rows ${ident.rows}`, k: "exec" }, { t: `PII ${ident.pii}`, k: "exec" }] },
    { icon: Activity, title: "Audited under that name", sub: "system.query.history · allowed and blocked", chips: [{ t: `executed_by ${principal}`, k: "neutral" }], jump: true },
  ];

  return (
    <div className="obo">
      <div className="obo-head"><span className="eyebrow">On behalf of the user · live</span>
        {t.phase === "running" && <span className="pill run sm">call in flight</span>}
        {t.phase === "done" && !anyFail && calls.length > 0 && <span className="pill ok sm"><Check size={11} /> allowed</span>}
        {t.phase === "done" && anyFail && <span className="pill bad sm"><X size={11} /> blocked</span>}
      </div>
      <ol className="obo-steps">
        {stages.map((s, i) => {
          const st = reach(i + 1);
          return (
            <li key={s.title} className={`obo-step s-${st}`} style={{ "--c": ident.color }}>
              <span className="obo-dot"><s.icon size={14} /></span>
              <div className="obo-txt">
                <b>{s.title}</b><small>{s.sub}</small>
                {(s.chips.length > 0 || s.jump) && (
                  <div className="obo-chips">
                    {s.chips.map((c) => <span key={c.t} className={`tchip k-${c.k}`}>{c.t}</span>)}
                    {s.jump && <button className="link-btn" onClick={onJump}>see it in step 8 →</button>}
                  </div>
                )}
              </div>
            </li>
          );
        })}
      </ol>
      <div className="obo-note"><Bot size={14} /> <span>The LLM reasons as the <b>app's service principal</b> and never reads data. Only the tool calls reach Unity Catalog, as {ident.label}.</span></div>
      <Connect info={info} />
    </div>
  );
}

function Connect({ info }) {
  const [copied, setCopied] = useState(null);
  const urls = info?.mcp || {};
  const copy = (k) => { navigator.clipboard?.writeText(urls[k]); setCopied(k); setTimeout(() => setCopied(null), 1200); };
  return (
    <div className="connect">
      <span className="eyebrow">Connect any client · same URLs, own sign-in</span>
      {[["genie_one", "Genie One"], ["dbsql", "DBSQL"]].map(([k, l]) => urls[k] && (
        <div key={k} className="url-row"><b>{l}</b><code title={urls[k]}>{urls[k].replace(/^https:\/\/[^/]+/, "…")}</code>
          <button className="icon-btn xs" onClick={() => copy(k)} aria-label={`Copy ${l} MCP URL`}>{copied === k ? <Check size={12} /> : <Copy size={12} />}</button></div>
      ))}
    </div>
  );
}
