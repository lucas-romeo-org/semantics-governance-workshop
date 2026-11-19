import React, { useLayoutEffect, useRef, useState } from "react";
import { Activity, AppWindow, BookOpen, Bot, Database, ExternalLink, KeyRound, LayoutDashboard, Lock,
  MessageSquare, Monitor, Network, Shield, Sigma, Sparkles, Tag, Users } from "lucide-react";
import { IDENTITIES } from "../api.js";

// Architecture diagram of the whole workshop, drawn in a fixed 1040×640 design space and scaled to fit.
const W = 1080, H = 640;

const ZONES = [
  { id: "outside-id", x: 8, y: 16, w: 150, h: 608, kind: "outside", caption: "Outside Databricks" },
  { id: "dbx", x: 172, y: 16, w: 668, h: 608, kind: "dbx", caption: "Databricks · account + workspace" },
  { id: "uc", x: 186, y: 150, w: 422, h: 380, kind: "uc", caption: "Unity Catalog · sgw_shop" },
  { id: "gold", x: 198, y: 184, w: 165, h: 330, kind: "inner", caption: "gold · physical", chip: "no consumer access", lock: true },
  { id: "semantic", x: 429, y: 184, w: 165, h: 330, kind: "inner", caption: "semantic", chip: "SELECT for consumers" },
  { id: "consumers", x: 626, y: 150, w: 200, h: 380, kind: "inner", caption: "Internal consumers", chip: "as the user" },
  { id: "outside-ext", x: 852, y: 16, w: 220, h: 608, kind: "outside", caption: "External clients" },
];

const NODES = [
  { id: "idp", x: 20, y: 70, w: 126, title: "Corporate IdP", sub: "Entra ID · Okta", icon: KeyRound, tone: "slate" },
  { id: "people", x: 20, y: 262, w: 126, h: 172, title: "People", sub: "as themselves", icon: Users, tone: "slate", people: true },
  { id: "groups", x: 200, y: 58, w: 190, title: "Account groups", sub: "wk_* · grant to groups", icon: Users, tone: "blue" },
  { id: "gold", x: 206, y: 222, w: 150, title: "gold tables", sub: "owner: engineers", icon: Database, tone: "orange" },
  { id: "tags", x: 206, y: 318, w: 150, title: "Governed tags", sub: "pii · region_scope", icon: Tag, tone: "amber" },
  { id: "policies", x: 206, y: 414, w: 150, title: "ABAC policies", sub: "row filter · mask", icon: Shield, tone: "red" },
  { id: "mv", x: 437, y: 260, w: 150, title: "Metric Views", sub: "one definition per KPI", icon: Sigma, tone: "orange" },
  { id: "context", x: 437, y: 390, w: 150, title: "Domain · Pages", sub: "✓ certified", icon: BookOpen, tone: "green" },
  { id: "dash", x: 638, y: 198, w: 178, title: "AI/BI Dashboard", sub: "viewer credentials", icon: LayoutDashboard, tone: "blue" },
  { id: "genie", x: 638, y: 280, w: 178, title: "Genie Agent", sub: "certified views only", icon: Sparkles, tone: "violet" },
  { id: "genieone", x: 638, y: 362, w: 178, title: "Genie One", sub: "ontology-grounded", icon: MessageSquare, tone: "violet" },
  { id: "gateway", x: 638, y: 448, w: 178, title: "Unity Gateway · MCP", sub: "genie_one · dbsql", icon: Network, tone: "slate" },
  { id: "bi", x: 864, y: 186, w: 196, title: "BI tools", sub: "Power BI · Tableau · Excel", icon: Monitor, tone: "blue" },
  { id: "agents", x: 864, y: 400, w: 196, title: "Claude · ChatGPT", sub: "any agent via MCP", icon: Bot, tone: "violet" },
  { id: "app", x: 864, y: 492, w: 196, title: "This companion app", sub: "external consumer", icon: AppWindow, tone: "orange" },
  { id: "ops", x: 200, y: 556, w: 626, h: 52, title: "Operate · system tables", sub: "who queried what · blocked attempts · lineage · cost", icon: Activity, tone: "green", wide: true },
];
const N = Object.fromEntries(NODES.map((n) => [n.id, { h: 62, ...n }]));

// from/to sides: r l t b · labelAt overrides the label position
const EDGES = [
  { id: "idp-groups", from: "idp", fs: "r", to: "groups", ts: "l", label: "SCIM" },
  { id: "people-idp", from: "people", fs: "t", to: "idp", ts: "b", label: "SSO" },
  { id: "groups-uc", from: "groups", fs: "b", to: "gold", ts: "t", label: "grants", dashed: true, labelAt: [345, 134] },
  { id: "tags-pol", from: "tags", fs: "b", to: "policies", ts: "t", label: "targets" },
  { id: "pol-gold", from: "policies", fs: "l", to: "gold", ts: "l", loop: -22 },
  { id: "gold-mv", from: "gold", fs: "r", to: "mv", ts: "l", label: "owner rights" },
  { id: "ctx-mv", from: "context", fs: "t", to: "mv", ts: "b", label: "describes" },
  { id: "mv-dash", from: "mv", fs: "r", to: "dash", ts: "l" },
  { id: "mv-genie", from: "mv", fs: "r", to: "genie", ts: "l" },
  { id: "mv-genieone", from: "mv", fs: "r", to: "genieone", ts: "l" },
  { id: "mv-gateway", from: "mv", fs: "r", to: "gateway", ts: "l", label: "MCP", labelAt: [614, 432] },
  { id: "mv-bi", from: "mv", fs: "t", to: "bi", ts: "l", label: "JDBC · MEASURE()", route: "over" },
  { id: "gw-agents", from: "gateway", fs: "r", to: "agents", ts: "l", label: "OAuth per user", labelAt: [962, 386] },
  { id: "gw-app", from: "gateway", fs: "r", to: "app", ts: "l" },
  { id: "people-consume", from: "people", fs: "r", to: "gold", ts: "l", label: "✕ no access", deny: true, labelAt: [168, 246] },
  { id: "ops", from: "consumers", fs: "b", to: "ops", ts: "t", label: "system tables", dashed: true, zone: true },
];

const MAIN = ["idp-groups", "groups-uc", "gold-mv", "mv-dash", "mv-genie", "mv-genieone", "mv-gateway", "gw-agents", "gw-app", "mv-bi"];
const STEP = {
  0: { nodes: "*", edges: MAIN },
  1: { nodes: ["idp", "people", "groups"], edges: ["people-idp", "idp-groups", "groups-uc"] },
  2: { nodes: ["gold", "tags", "groups"], edges: ["groups-uc", "people-consume"] },
  3: { nodes: ["policies", "tags", "gold"], edges: ["tags-pol", "pol-gold"] },
  4: { nodes: ["mv", "gold"], edges: ["gold-mv"] },
  5: { nodes: ["context", "mv"], edges: ["ctx-mv"] },
  6: { nodes: ["dash", "genie", "genieone", "mv"], edges: ["mv-dash", "mv-genie", "mv-genieone"] },
  7: { nodes: ["gateway", "agents", "app", "bi", "mv"], edges: ["mv-gateway", "gw-agents", "gw-app", "mv-bi"] },
  8: { nodes: ["ops"], edges: ["ops"] },
};

function anchor(id, side, isZone) {
  const b = isZone ? ZONES.find((z) => z.id === id) : N[id];
  const x = b.x, y = b.y, w = b.w, h = b.h ?? 62;
  return { r: [x + w, y + h / 2], l: [x, y + h / 2], t: [x + w / 2, y], b: [x + w / 2, y + h] }[side];
}

function path(e) {
  const [x1, y1] = e.zone ? anchor(e.from, e.fs, true) : anchor(e.from, e.fs);
  const [x2, y2] = anchor(e.to, e.ts);
  if (e.loop) { const lx = Math.min(x1, x2) + e.loop; return { d: `M${x1},${y1} C${lx},${y1} ${lx},${y2} ${x2},${y2}`, mx: lx + 2, my: (y1 + y2) / 2 }; }
  if (e.route === "over") { const top = 140; return { d: `M${x1},${y1} L${x1},${top} L${x2 - 40},${top} Q${x2 - 20},${top} ${x2 - 20},${y2 - 10} Q${x2 - 20},${y2} ${x2},${y2}`, mx: (x1 + x2) / 2 + 40, my: top }; }
  if (e.fs === "r" || e.fs === "l") {
    const dx = Math.max(30, Math.abs(x2 - x1) / 2);
    return { d: `M${x1},${y1} C${x1 + dx},${y1} ${x2 - dx},${y2} ${x2},${y2}`, mx: (x1 + x2) / 2, my: (y1 + y2) / 2 };
  }
  const dy = Math.max(20, Math.abs(y2 - y1) / 2), sgn = y2 > y1 ? 1 : -1;
  return { d: `M${x1},${y1} C${x1},${y1 + sgn * dy} ${x2},${y2 - sgn * dy} ${x2},${y2}`, mx: (x1 + x2) / 2, my: (y1 + y2) / 2 };
}

function NodeCard({ n, on, url, who }) {
  const Icon = n.icon;
  const cls = `dnode tone-${n.tone} ${on ? "on" : ""} ${n.wide ? "wide" : ""}`;
  const style = { left: n.x, top: n.y, width: n.w, height: n.h };
  const inner = (
    <>
      <span className="dicon"><Icon size={16} strokeWidth={1.8} /></span>
      <span className="dtext"><b>{n.title}</b><small>{n.sub}</small></span>
      {url && <ExternalLink size={11} className="dopen" />}
      {n.people && (
        <span className="people">
          {IDENTITIES.map((i) => (
            <span key={i.id} className={`pp ${who === i.id ? "sel" : ""}`} style={{ "--c": i.color }}>
              <span className="avatar sm">{i.label[0]}</span>{i.label}
            </span>
          ))}
        </span>
      )}
    </>
  );
  return url ? <a className={cls} style={style} href={url} target="_blank" rel="noreferrer">{inner}</a>
             : <div className={cls} style={style}>{inner}</div>;
}

export default function Diagram({ step, nodes, who }) {
  const ref = useRef(null);
  const [scale, setScale] = useState(1);
  useLayoutEffect(() => {
    const el = ref.current;
    const ro = new ResizeObserver(() => setScale(Math.min(el.clientWidth / W, el.clientHeight / H)));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const cfg = STEP[step.id] ?? STEP[0];
  const nodeOn = (id) => cfg.nodes !== "*" && cfg.nodes.includes(id);
  const edgeOn = (id) => cfg.edges === "*" || cfg.edges.includes(id);
  const whoColor = IDENTITIES.find((i) => i.id === who)?.color;

  return (
    <section className={`diagram ${step.id === 0 ? "all" : ""}`} ref={ref} aria-label="Architecture diagram">
      <div className="canvas" style={{ width: W, height: H, transform: `translate(-50%, -50%) scale(${scale})`, "--who": whoColor }}>
        {ZONES.map((z) => (
          <div key={z.id} className={`dzone k-${z.kind}`} style={{ left: z.x, top: z.y, width: z.w, height: z.h }}>
            <span className="dzone-cap">{z.caption}</span>
            {z.chip && <span className="dzone-chip">{z.lock && <Lock size={9} />}{z.chip}</span>}
          </div>
        ))}
        <svg className="edges" width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
          <defs>
            <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" className="arrow" /></marker>
            <marker id="arr-on" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" className="arrow on" /></marker>
          </defs>
          {EDGES.map((e) => {
            const p = path(e), on = edgeOn(e.id);
            return (
              <g key={e.id} className={`edge ${on ? "on" : ""} ${e.dashed ? "dashed" : ""} ${e.deny ? "deny" : ""}`}>
                <path d={p.d} markerEnd={`url(#${on ? "arr-on" : "arr"})`} />
                {on && !e.deny && <path d={p.d} className="flow" />}
              </g>
            );
          })}
        </svg>
        {NODES.map((n) => <NodeCard key={n.id} n={N[n.id]} on={nodeOn(n.id)} url={nodes[n.id]} who={who} />)}
        <svg className="edges labels" width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
          {EDGES.filter((e) => e.label).map((e) => {
            const p = path(e), on = edgeOn(e.id);
            const [lx, ly] = e.labelAt ?? [p.mx, p.my];
            const w = e.label.length * 5.9 + 12;
            return (
              <g key={e.id} className={`edge ${on ? "on" : ""} ${e.deny ? "deny" : ""}`} transform={`translate(${lx},${ly})`}>
                <rect x={-w / 2} y={-8} width={w} height={16} rx={4} className="elabel-bg" />
                <text className="elabel" textAnchor="middle" dy="3.5">{e.label}</text>
              </g>
            );
          })}
        </svg>
      </div>
    </section>
  );
}
