import React from "react";
import { ChevronLeft, ChevronRight, Code, ExternalLink } from "lucide-react";
import Proof from "./Proof.jsx";

export default function StepPanel({ step, who, deep, setDeep, onPrev, onNext, isLast }) {
  return (
    <aside className="panel">
      <div className="eyebrow accent">{step.eyebrow}</div>
      <h2>{step.title}</h2>
      <p className="line">{step.line}</p>
      <ul className="points">{step.points.map((p) => <li key={p}>{p}</li>)}</ul>

      <Proof step={step} who={who} />

      {step.artifacts?.length > 0 && (
        <div className="artifacts">
          <div className="eyebrow">Open the real thing</div>
          <div className="chips">
            {step.artifacts.map((a) => a.url
              ? <a key={a.label} className="chip" href={a.url} target="_blank" rel="noreferrer">{a.label}<ExternalLink size={12} /></a>
              : <span key={a.label} className="chip muted">{a.label}</span>)}
          </div>
        </div>
      )}

      {step.deep && (
        <div className="deep">
          <button className="link-btn" onClick={() => setDeep(!deep)}><Code size={14} /> {deep ? "Hide" : "Show"} how it's built</button>
          {deep && (<><div className="eyebrow">{step.deep.title}</div><pre className="code">{step.deep.code}</pre></>)}
        </div>
      )}

      <div className="pager">
        <button className="ghost" onClick={onPrev} disabled={step.id === 0}><ChevronLeft size={16} /> Back</button>
        <button className="primary" onClick={onNext} disabled={isLast}>{step.id === 0 ? "Start the journey" : "Next step"} <ChevronRight size={16} /></button>
      </div>
    </aside>
  );
}
