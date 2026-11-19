import React, { useCallback, useEffect, useState } from "react";
import { api, IDENTITIES } from "./api.js";
import TopBar from "./components/TopBar.jsx";
import StepRail from "./components/StepRail.jsx";
import JourneyMap from "./components/JourneyMap.jsx";
import StepPanel from "./components/StepPanel.jsx";

export default function App() {
  const [steps, setSteps] = useState([]);
  const [info, setInfo] = useState(null);
  const [current, setCurrent] = useState(() => Number(new URLSearchParams(location.search).get("step") ?? 0));
  const [who, setWho] = useState("me");
  const [deep, setDeep] = useState(false);
  const [dark, setDark] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.steps(), api.info()]).then(([s, i]) => { setSteps(s); setInfo(i); }).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => { document.documentElement.dataset.theme = dark ? "dark" : "light"; }, [dark]);
  useEffect(() => { history.replaceState(null, "", `?step=${current}`); }, [current]);

  const go = useCallback((n) => setCurrent((c) => Math.max(0, Math.min((steps.length || 9) - 1, n(c)))), [steps.length]);

  useEffect(() => {
    const onKey = (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
      if (e.key === "ArrowRight") go((c) => c + 1);
      else if (e.key === "ArrowLeft") go((c) => c - 1);
      else if (/^[0-8]$/.test(e.key)) setCurrent(Number(e.key));
      else if (e.key.toLowerCase() === "v") setWho((w) => IDENTITIES[(IDENTITIES.findIndex((i) => i.id === w) + 1) % IDENTITIES.length].id);
      else if (e.key.toLowerCase() === "d") setDeep((d) => !d);
      else if (e.key.toLowerCase() === "t") setDark((d) => !d);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go]);

  if (error) return <div className="fatal">Could not load the app: {error}</div>;
  if (!steps.length) return <div className="loading"><span className="spinner" /> Loading the journey…</div>;

  const step = steps[current];
  return (
    <div className="app">
      <TopBar who={who} setWho={setWho} dark={dark} setDark={setDark} user={info?.user} />
      <StepRail steps={steps} current={current} setCurrent={setCurrent} />
      <main className="stage">
        <JourneyMap step={step} nodes={info?.nodes ?? {}} />
        <StepPanel key={`${step.id}-${who}`} step={step} who={who} deep={deep} setDeep={setDeep}
                   onPrev={() => go((c) => c - 1)} onNext={() => go((c) => c + 1)} isLast={current === steps.length - 1} />
      </main>
      <footer className="hints">
        <span><kbd>←</kbd><kbd>→</kbd> steps</span><span><kbd>0</kbd>–<kbd>8</kbd> jump</span>
        <span><kbd>V</kbd> view as</span><span><kbd>D</kbd> deep</span><span><kbd>T</kbd> theme</span>
        <span className="grow" />
        <span className="mono">Every result runs as the selected identity · the app never reads data as itself</span>
      </footer>
    </div>
  );
}
