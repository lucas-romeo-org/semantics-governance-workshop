import React from "react";
import { Activity, BookOpen, Bot, Database, ExternalLink, LayoutDashboard, Lock, Monitor, Shield, Sigma, Sparkles, Tag, User, Users } from "lucide-react";

// The one map of the workshop. Every node opens the real artifact.
const ZONES = [
  { id: "identity", caption: "Identity", nodes: [
    { id: "groups", icon: Users, title: "Account groups", sub: "wk_* · unit of governance" },
    { id: "personas", icon: User, title: "Ana · Pedro · Marta", sub: "persona identities" },
  ]},
  { id: "gold", caption: "Gold · physical", chip: { icon: Lock, text: "no consumer access" }, nodes: [
    { id: "gold", icon: Database, title: "gold tables", sub: "owned by data engineering" },
    { id: "tags", icon: Tag, title: "Governed tags", sub: "pii · region_scope" },
    { id: "policies", icon: Shield, title: "ABAC policies", sub: "row filter · column mask" },
  ]},
  { id: "semantic", caption: "Semantic layer", chip: { text: "SELECT for consumers" }, nodes: [
    { id: "mv", icon: Sigma, title: "Metric Views", sub: "one definition per KPI" },
    { id: "context", icon: BookOpen, title: "Domain · Pages · ✓", sub: "findable and certified" },
  ]},
  { id: "consumers", caption: "Consumers · as the user", nodes: [
    { id: "dash", icon: LayoutDashboard, title: "AI/BI Dashboard", sub: "viewer credentials" },
    { id: "genie", icon: Sparkles, title: "Genie Agent", sub: "certified views only" },
    { id: "mcp", icon: Bot, title: "Agents via MCP", sub: "Genie One · DBSQL" },
    { id: "bi", icon: Monitor, title: "BI tools", sub: "Power BI · Tableau · Excel" },
  ]},
];
const LINKS = ["grants · OAuth", "owner rights", "SELECT · as you"];

function Node({ n, active, url }) {
  const Icon = n.icon;
  const body = (
    <>
      <span className="node-icon"><Icon size={18} strokeWidth={1.75} /></span>
      <span className="node-text"><b>{n.title}</b><small>{n.sub}</small></span>
      {url && <ExternalLink className="node-open" size={13} />}
    </>
  );
  return url
    ? <a className={`node ${active ? "on" : ""}`} href={url} target="_blank" rel="noreferrer" title="Open the real artifact">{body}</a>
    : <div className={`node ${active ? "on" : ""}`}>{body}</div>;
}

export default function JourneyMap({ step, nodes }) {
  const active = new Set(step.nodes || []);
  const all = step.id === 0;
  return (
    <section className={`map ${all ? "all" : ""}`} aria-label="Journey map">
      <div className="map-flow">
        {ZONES.map((z, i) => {
          const zoneOn = z.nodes.some((n) => active.has(n.id));
          return (
            <React.Fragment key={z.id}>
              <div className={`zone zone-${z.id} ${zoneOn ? "on" : ""}`}>
                <div className="zone-head">
                  <span className="eyebrow">{z.caption}</span>
                  {z.chip && <span className="zone-chip">{z.chip.icon && <z.chip.icon size={11} />}{z.chip.text}</span>}
                </div>
                {z.nodes.map((n) => <Node key={n.id} n={n} active={all || active.has(n.id)} url={nodes[n.id]} />)}
              </div>
              {i < ZONES.length - 1 && (
                <div className={`link ${zoneOn || all ? "on" : ""}`}>
                  <span className="link-line" /><span className="link-label">{LINKS[i]}</span>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
      <a className={`ops-band ${all || active.has("ops") ? "on" : ""}`} href={nodes.ops} target="_blank" rel="noreferrer">
        <Activity size={16} strokeWidth={1.75} />
        <b>Operate</b><span>audit · lineage · cost · change control, from system tables</span>
        <ExternalLink size={13} className="node-open" />
      </a>
    </section>
  );
}
