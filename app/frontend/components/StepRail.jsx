import React from "react";

export default function StepRail({ steps, current, setCurrent }) {
  return (
    <nav className="rail" aria-label="Workshop steps">
      {steps.map((s) => (
        <button key={s.id} className={`rail-step ${s.id === current ? "on" : ""} ${s.id < current ? "done" : ""}`}
                onClick={() => setCurrent(s.id)}>
          <span className="num">{s.id === 0 ? "★" : s.id}</span>
          <span className="lbl">{s.short}</span>
        </button>
      ))}
    </nav>
  );
}
