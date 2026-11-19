const get = async (url) => {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
};
export const api = {
  info: () => get("/api/info"),
  steps: () => get("/api/steps"),
  proof: (key, who) => get(`/api/proof/${key}?who=${who}`),
  ask: (surface, q, who) => get(`/api/ask/${surface}?who=${who}&q=${encodeURIComponent(q)}`),
};

export const IDENTITIES = [
  { id: "me", label: "You", sub: "your own login", color: "var(--id-you)" },
  { id: "ana", label: "Ana", sub: "analyst · ES", color: "var(--id-ana)" },
  { id: "pedro", label: "Pedro", sub: "analyst · PT", color: "var(--id-pedro)" },
  { id: "marta", label: "Marta", sub: "lead · all + PII", color: "var(--id-marta)" },
];

export const eur = (v) => {
  const n = Number(v);
  if (!isFinite(n)) return v ?? "–";
  return new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR", notation: "compact", maximumFractionDigits: 2 }).format(n);
};
export const pct = (v) => (isFinite(Number(v)) ? `${(Number(v) * 100).toFixed(1)}%` : "–");
