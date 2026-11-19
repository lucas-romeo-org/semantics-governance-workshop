import React from "react";
import { ChevronLeft, ChevronRight, Code, ExternalLink, FileCode, Loader, Play } from "lucide-react";
import Proof from "./Proof.jsx";
import OboTrace from "./OboTrace.jsx";

export default function StepPanel({ step, who, info, deep, setDeep, onPrev, onNext, onJump, isLast, built = null }) {
  const consoleStep = step.proof === "agent_console";
  return (
    <aside className="panel">
      <div className="eyebrow accent">{step.eyebrow}</div>
      <h2>{step.title}</h2>
      <p className="line">{step.line}</p>
      {!consoleStep && <ul className="points">{step.points.map((p) => <li key={p}>{p}</li>)}</ul>}

      {consoleStep ? <OboTrace who={who} info={info} onJump={() => onJump(8)} /> : <Proof step={step} who={who} />}

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

      {built && <BuiltWith built={built} />}

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

// Builder view only: the notebooks, scripts and bundle files that deployed this step.
function BuiltWith({ built }) {
  if (built === "loading") return <div className="built"><div className="eyebrow">Built with</div><div className="proof-loading"><Loader size={14} className="spin" /> resolving sources…</div></div>;
  return (
    <div className="built">
      <div className="built-head"><span className="eyebrow">Built with · code behind this step</span>
        {built.job && <a className="chip sm" href={built.job.url} target="_blank" rel="noreferrer"><Play size={11} /> job {built.job.key}<ExternalLink size={11} /></a>}</div>
      <div className="built-list">
        {built.items.map((it) => (
          <div key={it.path} className="src-row">
            <FileCode size={14} className="src-ico" />
            <span className="src-name"><b title={it.path}>{it.path}</b><small>{it.kind}</small></span>
            {it.workspace && <a href={it.workspace} target="_blank" rel="noreferrer" className="src-link">workspace <ExternalLink size={10} /></a>}
            <a href={it.github} target="_blank" rel="noreferrer" className="src-link">GitHub <ExternalLink size={10} /></a>
          </div>
        ))}
      </div>
    </div>
  );
}
