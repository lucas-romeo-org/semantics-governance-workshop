const get = async (url) => {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
};
export const api = {
  info: () => get("/api/info"),
  steps: () => get("/api/steps"),
  proof: (key, who) => get(`/api/proof/${key}?who=${who}`),
  mcpTools: (who) => get(`/api/mcp/tools?who=${who}`),
  sources: () => get("/api/sources"),
  status: () => get("/api/status"),
};

export const IDENTITIES = [
  { id: "me", label: "You", sub: "your own login", color: "var(--id-you)", rows: "your grants", pii: "your grants" },
  { id: "ana", label: "Ana", sub: "analyst · ES", color: "var(--id-ana)", rows: "ES", pii: "masked" },
  { id: "pedro", label: "Pedro", sub: "analyst · PT", color: "var(--id-pedro)", rows: "PT", pii: "masked" },
  { id: "marta", label: "Marta", sub: "lead · all + PII", color: "var(--id-marta)", rows: "all", pii: "shown" },
];

export const eur = (v) => {
  const n = Number(v);
  if (!isFinite(n)) return v ?? "–";
  return new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR", notation: "compact", maximumFractionDigits: 2 }).format(n);
};
export const pct = (v) => (isFinite(Number(v)) ? `${(Number(v) * 100).toFixed(1)}%` : "–");

export const cleanMd = (t) => (t || "").replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/^#+\s*/gm, "").replace(/\*\*/g, "")
  .split("\n").filter((l) => l.trim() && !l.trim().startsWith("|")).join("\n");
export const shortName = (p) => (p || "").startsWith("sgw-persona-") ? p.replace("sgw-persona-", "").replace(/^./, (c) => c.toUpperCase()) : (p || "").split(" ")[0];
