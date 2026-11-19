import React from "react";
import { Activity, AppWindow, BookOpen, Bot, Database, ExternalLink, Fingerprint, KeyRound, LayoutDashboard, Lock,
  MessageSquare, Monitor, Network, Server, Shield, Sigma, Sparkles, Users } from "lucide-react";
import { IDENTITIES } from "../api.js";

// Solution architecture of the workshop: one SVG on a fixed grid (viewBox), orthogonal connectors with rounded
// corners, halo labels, and a per-step focus (active nodes in ink, the rest dimmed), after the reference template.
const W = 1160, H = 760;

const ZONES = [
  { x: 12, y: 12, w: 172, h: 736, dbx: false, label: "OUTSIDE · CORPORATE" },
  { x: 200, y: 12, w: 740, h: 736, dbx: true, label: "DATABRICKS · ACCOUNT + WORKSPACE" },
  { x: 956, y: 12, w: 192, h: 736, dbx: false, label: "OUTSIDE · ANY CLIENT" },
];
const GROUPS = [
  { id: "uc", x: 214, y: 192, w: 464, h: 312, label: "UNITY CATALOG · SGW_SHOP", accent: true },
  { id: "surfaces", x: 696, y: 192, w: 232, h: 434, label: "SURFACES", who: true },
  { id: "clients", x: 960, y: 448, w: 184, h: 176 },
];
const CAPTIONS = [
  { x: 228, y: 240, t: "GOLD · OWNERS ONLY", lock: true },
  { x: 488, y: 240, t: "SEMANTIC · FOR CONSUMERS" },
  { x: 708, y: 458, t: "ENDPOINTS FOR ANY CLIENT" },
];

const NODES = {
  idp: { x: 28, y: 64, w: 140, h: 92, stack: true, title: "Corporate IdP", sub: "Entra ID · Okta", icon: KeyRound, tone: "slate" },
  people: { x: 28, y: 300, w: 140, h: 248, people: true, title: "People", icon: Users, tone: "slate" },
  groups: { x: 228, y: 64, w: 176, h: 92, title: "Account groups", sub: "wk_* · via SCIM", icon: Users, tone: "blue", chips: [{ t: "grant to groups", k: "user" }] },
  oauth: { x: 488, y: 64, w: 176, h: 92, title: "Databricks OAuth", sub: "SSO via your IdP", icon: Fingerprint, tone: "blue", chips: [{ t: "1 token per person", k: "entry" }] },
  gold: { x: 228, y: 252, w: 176, h: 88, title: "gold tables", sub: "owner: engineers", icon: Database, tone: "orange", chips: [{ t: "tag pii", k: "val" }, { t: "tag region", k: "val" }] },
  policies: { x: 228, y: 392, w: 176, h: 88, title: "ABAC policies", sub: "row filter · mask", icon: Shield, tone: "red", chips: "who" },
  mv: { x: 488, y: 252, w: 176, h: 88, title: "Metric Views", sub: "19 measures · YAML", icon: Sigma, tone: "orange", chips: [{ t: "SELECT for consumers", k: "user" }] },
  context: { x: 488, y: 392, w: 176, h: 88, title: "Domain · Pages", sub: "certified glossary", icon: BookOpen, tone: "green", chips: [{ t: "✓ certified", k: "exec" }, { t: "domain", k: "neutral" }] },
  dash: { x: 708, y: 228, w: 208, h: 60, title: "AI/BI Dashboard", sub: "viewer credentials", icon: LayoutDashboard, tone: "blue" },
  genie: { x: 708, y: 296, w: 208, h: 60, title: "Genie Agent", sub: "curated · certified", icon: Sparkles, tone: "violet" },
  genieone: { x: 708, y: 364, w: 208, h: 60, title: "Genie One", sub: "finds the domain itself", icon: MessageSquare, tone: "violet" },
  warehouse: { x: 708, y: 470, w: 208, h: 60, title: "SQL warehouse", sub: "JDBC · ODBC · MEASURE()", icon: Server, tone: "slate" },
  gateway: { x: 708, y: 552, w: 208, h: 60, title: "Unity Gateway · MCP", sub: "genie_one · dbsql", icon: Network, tone: "slate" },
  app: { x: 488, y: 540, w: 176, h: 84, title: "Companion app", sub: "Databricks Apps", icon: AppWindow, tone: "orange", chips: [{ t: "acts as MCP client", k: "entry" }] },
  bi: { x: 966, y: 470, w: 174, h: 60, title: "BI tools", sub: "Power BI · Excel", icon: Monitor, tone: "blue" },
  agents: { x: 966, y: 552, w: 174, h: 60, title: "Claude · ChatGPT", sub: "any MCP client", icon: Bot, tone: "violet" },
  ops: { x: 214, y: 652, w: 714, h: 64, wide: true, title: "Operate · system tables", sub: "who queried what · from which surface · blocked attempts · lineage · cost", icon: Activity, tone: "green" },
};

// Connectors point in the direction of the request. label: [text, x, y, anchor]
const EDGES = [
  { id: "sso", pts: [[98, 300], [98, 156]], label: ["SSO", 106, 232, "start"] },
  { id: "scim", pts: [[168, 110], [228, 110]], label: ["SCIM", 198, 102, "middle"] },
  { id: "grants", pts: [[316, 156], [316, 192]], label: ["grants", 324, 178, "start"] },
  { id: "deny", pts: [[168, 424], [192, 424], [192, 296], [222, 296]], deny: true, label: ["✕ no grants", 198, 368, "start"] },
  { id: "owner", pts: [[488, 296], [404, 296]], label: ["owner rights", 446, 288, "middle"] },
  { id: "pol", pts: [[316, 392], [316, 340]], label: ["filter · mask", 324, 370, "start"] },
  { id: "desc", pts: [[576, 392], [576, 340]], label: ["describes", 584, 370, "start"] },
  { id: "s-dash", pts: [[708, 258], [684, 258], [684, 296], [664, 296]] },
  { id: "s-genie", pts: [[708, 326], [684, 326], [684, 296], [664, 296]] },
  { id: "s-one", pts: [[708, 394], [684, 394], [684, 296], [664, 296]] },
  { id: "s-wh", pts: [[708, 500], [684, 500], [684, 296], [664, 296]] },
  { id: "gw-wh", pts: [[812, 552], [812, 530]], label: ["SQL", 820, 545, "start"] },
  { id: "app-gw", pts: [[664, 582], [708, 582]], label: ["MCP", 686, 574, "middle"] },
  { id: "bi-wh", pts: [[966, 500], [916, 500]], label: ["JDBC", 942, 492, "middle"] },
  { id: "ag-gw", pts: [[966, 582], [916, 582]], label: ["MCP", 942, 574, "middle"] },
  { id: "signin", pts: [[1053, 448], [1053, 110], [664, 110]], dashed: true, label: ["OAuth sign-in · as the person", 858, 102, "middle"] },
  { id: "audit", pts: [[812, 626], [812, 652]], dashed: true, label: ["audit", 820, 643, "start"] },
];

const STEP = {
  0: { nodes: "*", edges: [] },
  1: { nodes: ["idp", "people", "groups", "oauth"], edges: ["sso", "scim", "grants"] },
  2: { nodes: ["gold", "groups", "people"], edges: ["grants", "deny"] },
  3: { nodes: ["policies", "gold"], edges: ["pol"] },
  4: { nodes: ["mv", "gold"], edges: ["owner"] },
  5: { nodes: ["context", "mv"], edges: ["desc"] },
  6: { nodes: ["dash", "genie", "genieone", "mv", "gold", "policies"], edges: ["s-dash", "s-genie", "s-one", "owner", "pol"] },
  7: { nodes: ["agents", "bi", "oauth", "gateway", "warehouse", "app", "mv"], edges: ["signin", "ag-gw", "app-gw", "gw-wh", "bi-wh", "s-wh"] },
  8: { nodes: ["ops", "dash", "genie", "genieone", "warehouse", "gateway"], edges: ["audit"] },
};

function orth(pts, r = 10) {
  let d = `M${pts[0][0]},${pts[0][1]}`;
  for (let i = 1; i < pts.length - 1; i++) {
    const [x0, y0] = pts[i - 1], [x1, y1] = pts[i], [x2, y2] = pts[i + 1];
    const rr = Math.min(r, Math.hypot(x1 - x0, y1 - y0) / 2, Math.hypot(x2 - x1, y2 - y1) / 2);
    d += ` L${x1 - Math.sign(x1 - x0) * rr},${y1 - Math.sign(y1 - y0) * rr} Q${x1},${y1} ${x1 + Math.sign(x2 - x1) * rr},${y1 + Math.sign(y2 - y1) * rr}`;
  }
  const [xn, yn] = pts[pts.length - 1];
  return `${d} L${xn},${yn}`;
}
const len = (pts) => pts.slice(1).reduce((s, p, i) => s + Math.hypot(p[0] - pts[i][0], p[1] - pts[i][1]), 0);
const halo = (x) => (x < 192 || x > 948 ? "h-out" : "h-dbx");

function Chips({ x, y, items }) {
  let cx = x;
  return items.map((it) => {
    const w = Math.round(it.t.length * 6.4 + 12);
    const g = (
      <g key={it.t} className={`schip k-${it.k}`} style={it.c ? { "--c": it.c } : undefined}>
        <rect x={cx} y={y} width={w} height={20} rx={5} />
        <text x={cx + 6} y={y + 14}>{it.t}</text>
      </g>
    );
    cx += w + 5;
    return g;
  });
}

function Tile({ x, y, n }) {
  const Icon = n.icon;
  return (
    <g>
      <rect className={`tile t-${n.tone}`} x={x} y={y} width={30} height={30} rx={8} />
      <Icon x={x + 6} y={y + 6} size={18} strokeWidth={1.9} className="tile-icon" />
    </g>
  );
}

function NodeBody({ id, n, who }) {
  const { x, y, w, h } = n;
  const ident = IDENTITIES.find((i) => i.id === who);
  if (n.people) {
    return (<>
      <Tile x={x + 12} y={y + 12} n={n} />
      <text className="n-title" x={x + 52} y={y + 32}>{n.title}</text>
      {IDENTITIES.map((p, i) => {
        const cy = y + 72 + i * 44;
        const sel = p.id === who;
        return (
          <g key={p.id} className={`person ${sel ? "sel" : ""}`} style={{ "--c": p.color }}>
            {sel && <rect className="person-sel" x={x + 8} y={cy - 19} width={w - 16} height={38} rx={9} />}
            <circle cx={x + 28} cy={cy} r={12} className="person-dot" />
            <text x={x + 28} y={cy + 4} className="person-initial" textAnchor="middle">{p.label[0]}</text>
            <text x={x + 48} y={cy - 2} className="person-name">{p.label}</text>
            <text x={x + 48} y={cy + 12} className="n-sub">{p.sub}</text>
          </g>
        );
      })}
    </>);
  }
  if (n.stack) {
    return (<>
      <Tile x={x + 14} y={y + 14} n={n} />
      <text className="n-title" x={x + 14} y={y + h - 30}>{n.title}</text>
      <text className="n-sub" x={x + 14} y={y + h - 13}>{n.sub}</text>
    </>);
  }
  if (n.wide) {
    return (<>
      <Tile x={x + 16} y={y + (h - 30) / 2} n={n} />
      <text className="n-title" x={x + 58} y={y + 28}>{n.title}</text>
      <text className="n-sub" x={x + 58} y={y + 46}>{n.sub}</text>
    </>);
  }
  const chips = n.chips === "who"
    ? (who === "me" ? [{ t: "as your grants", k: "exec" }] : [{ t: `rows ${ident.rows}`, k: "exec" }, { t: `PII ${ident.pii}`, k: "exec" }])
    : n.chips;
  const small = h <= 60;
  return (<>
    <Tile x={x + 12} y={small ? y + 15 : y + 14} n={n} />
    <text className="n-title" x={x + 52} y={y + (small ? 28 : 27)}>{n.title}</text>
    <text className="n-sub" x={x + 52} y={y + (small ? 45 : 43)}>{n.sub}</text>
    {chips && <Chips x={x + 12} y={y + 56} items={chips} />}
  </>);
}

export default function Diagram({ step, nodes = {}, who, compact = false }) {
  const cfg = STEP[step.id] ?? STEP[0];
  const all = cfg.nodes === "*";
  const nodeState = (id) => (all ? "" : cfg.nodes.includes(id) ? "on" : "dim");
  const edgeOn = (id) => cfg.edges.includes(id);
  const ident = IDENTITIES.find((i) => i.id === who);

  return (
    <section className={`diagram ${compact ? "compact" : ""}`} aria-label="Solution architecture" style={{ "--who": ident.color }}>
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet" role="img">
        <defs>
          <marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" className="ah" /></marker>
          <marker id="ah-on" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" className="ah on" /></marker>
        </defs>

        {ZONES.map((z) => (
          <g key={z.label}>
            <rect className={`zone ${z.dbx ? "dbx" : ""}`} x={z.x} y={z.y} width={z.w} height={z.h} rx={14} />
            <text className="zone-label" x={z.x + 16} y={z.y + 26}>{z.label}</text>
          </g>
        ))}
        {GROUPS.map((g) => (
          <g key={g.id}>
            <rect className={`group ${g.accent ? "accent" : ""}`} x={g.x} y={g.y} width={g.w} height={g.h} rx={12} />
            {g.label && <text className={`group-label ${g.accent ? "accent" : ""}`} x={g.x + 14} y={g.y + 22}>{g.label}</text>}
            {g.who && <Chips x={g.x + g.w - 14 - Math.round(`as ${ident.label}`.length * 6.4 + 12)} y={g.y + 8} items={[{ t: `as ${ident.label}`, k: "who", c: ident.color }]} />}
          </g>
        ))}
        {CAPTIONS.map((c) => (
          <g key={c.t} className="caption">
            {c.lock && <Lock x={c.x} y={c.y - 9} size={11} strokeWidth={2} />}
            <text x={c.x + (c.lock ? 15 : 0)} y={c.y}>{c.t}</text>
          </g>
        ))}

        {/* connectors */}
        {EDGES.map((e) => {
          const on = edgeOn(e.id);
          if (e.deny && !on) return null;
          const d = orth(e.pts);
          return (
            <g key={e.id} className={`edge ${on ? "on" : all ? "" : "off"} ${e.dashed ? "dashed" : ""} ${e.deny ? "deny" : ""}`}>
              <path d={d} markerEnd={e.deny ? undefined : `url(#${on ? "ah-on" : "ah"})`} />
              {on && !e.deny && (
                <circle r={4.2} className="packet">
                  <animateMotion dur={`${Math.max(1.2, len(e.pts) / 160)}s`} repeatCount="indefinite" path={d} />
                </circle>
              )}
              {e.deny && (() => { const [x, y] = e.pts[e.pts.length - 1]; return (
                <g className="fail-x"><circle cx={x} cy={y} r={8} /><line x1={x - 3.5} y1={y - 3.5} x2={x + 3.5} y2={y + 3.5} /><line x1={x + 3.5} y1={y - 3.5} x2={x - 3.5} y2={y + 3.5} /></g>
              ); })()}
            </g>
          );
        })}

        {/* nodes */}
        {Object.entries(NODES).map(([id, n]) => {
          const url = nodes[id];
          const body = (
            <g className={`node ${nodeState(id)}`}>
              <rect className="node-box" x={n.x} y={n.y} width={n.w} height={n.h} rx={10} />
              <NodeBody id={id} n={n} who={who} />
              {url && <ExternalLink x={n.x + n.w - 18} y={n.y + n.h - 18} size={11} className="n-open" />}
            </g>
          );
          return url ? <a key={id} href={url} target="_blank" rel="noreferrer" aria-label={`${n.title}: open in Databricks`}>{body}</a>
                     : <g key={id}>{body}</g>;
        })}

        {/* labels above everything */}
        {EDGES.filter((e) => e.label).map((e) => {
          const on = edgeOn(e.id);
          if (e.deny && !on) return null;
          const [t, x, y, a] = e.label;
          return <text key={e.id} className={`edge-label ${halo(x)} ${on ? "on" : all ? "" : "off"} ${e.deny ? "deny" : ""}`} x={x} y={y} textAnchor={a}>{t}</text>;
        })}
      </svg>
      {!compact && (
        <div className="legend">
          <span><i className="lg-line" /> request</span>
          <span><i className="lg-line dashed" /> sign-in · audit</span>
          <span><i className="lg-dot" /> live, as {ident.label}</span>
          <span><i className="lg-x">✕</i> blocked by Unity Catalog</span>
          <span className="grow" />
          <span className="muted">Click any block to open the real object</span>
        </div>
      )}
    </section>
  );
}
