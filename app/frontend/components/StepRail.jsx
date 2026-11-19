import React from "react";
import { Check } from "lucide-react";

export default function StepRail({ steps, current, setCurrent, status = {} }) {
  return (
    <nav className="rail" aria-label="Workshop steps">
      {steps.map((s) => {
        const st = status[s.id]?.result;
        return (
          <button key={s.id} className={`rail-step ${s.id === current ? "on" : ""} ${s.id < current ? "done" : ""}`}
                  onClick={() => setCurrent(s.id)} title={st ? `last verify run: ${st}` : undefined}>
            <span className="num">{s.id === 0 ? "★" : s.id}</span>
            <span className="lbl">{s.short}</span>
            {st === "SUCCESS" && <span className="verified" title="verified in the workspace"><Check size={10} strokeWidth={3} /></span>}
            {st && st !== "SUCCESS" && <span className="verified bad" title={st}>!</span>}
          </button>
        );
      })}
      <span className="rail-legend"><span className="verified"><Check size={10} strokeWidth={3} /></span> verified by its job in the workspace</span>
    </nav>
  );
}
