import React from "react";
import { Code, Moon, Sun } from "lucide-react";
import { IDENTITIES } from "../api.js";

export default function TopBar({ who, setWho, dark, setDark, user, builder, setBuilder }) {
  return (
    <header className="topbar">
      <div className="brand">
        <div className="logo-mark" aria-hidden>
          <span /><span /><span />
        </div>
        <div>
          <div className="eyebrow">Databricks · Unity Catalog</div>
          <h1>Semantic Governance Workshop</h1>
        </div>
      </div>
      <div className="viewas" role="radiogroup" aria-label="View as">
        <span className="eyebrow">View as</span>
        {IDENTITIES.map((i) => (
          <button key={i.id} role="radio" aria-checked={who === i.id} className={`who ${who === i.id ? "on" : ""}`}
                  style={{ "--c": i.color }} onClick={() => setWho(i.id)} title={i.id === "me" ? user || "you" : i.sub}>
            <span className="avatar">{i.label[0]}</span>
            <span className="who-text"><b>{i.label}</b><small>{i.id === "me" ? "your login" : i.sub}</small></span>
          </button>
        ))}
      </div>
      <button className={`builder-switch ${builder ? "on" : ""}`} role="switch" aria-checked={builder} onClick={() => setBuilder(!builder)}
              title="Show the notebooks, scripts and bundle files behind every block (B)">
        <Code size={15} /><span>Builder view</span><span className="track"><span className="knob" /></span>
      </button>
      <button className="icon-btn" onClick={() => setDark(!dark)} aria-label="Toggle theme">{dark ? <Sun size={18} /> : <Moon size={18} />}</button>
    </header>
  );
}
