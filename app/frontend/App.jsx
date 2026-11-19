import React, { useCallback, useEffect, useState } from "react";
import { api, IDENTITIES } from "./api.js";
import TopBar from "./components/TopBar.jsx";
import StepRail from "./components/StepRail.jsx";
import Diagram from "./components/Diagram.jsx";
import StepPanel from "./components/StepPanel.jsx";
import ExternalStage from "./components/ExternalStage.jsx";
import ErrorBoundary from "./components/ErrorBoundary.jsx";

export default function App() {
  const [steps, setSteps] = useState([]);
  const [info, setInfo] = useState(null);
  const [current, setCurrent] = useState(() => Number(new URLSearchParams(location.search).get("step") ?? 0));
  const [who, setWho] = useState("me");
  const [deep, setDeep] = useState(false);
  const [dark, setDark] = useState(false);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState({});
  // Builder view: complementary links to the notebooks, scripts and bundle files. Off by default.
  const [builder, setBuilder] = useState(() => localStorage.getItem("sgw-builder") === "1");
  const [sources, setSources] = useState(null);
  const [present, setPresent] = useState(false);

  useEffect(() => {
    Promise.all([api.steps(), api.info()]).then(([s, i]) => { setSteps(s); setInfo(i); }).catch((e) => setError(String(e)));
    api.status().then(setStatus).catch(() => {});
  }, []);

  useEffect(() => { document.documentElement.dataset.theme = dark ? "dark" : "light"; }, [dark]);
  useEffect(() => {
    localStorage.setItem("sgw-builder", builder ? "1" : "0");
    if (builder && !sources) api.sources().then(setSources).catch(() => setSources({ nodes: {}, steps: {} }));
  }, [builder, sources]);
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
      else if (e.key.toLowerCase() === "b") setBuilder((b) => !b);
      else if (e.key.toLowerCase() === "p") {
        setPresent((p) => {
          if (!p) document.documentElement.requestFullscreen?.().catch(() => {});
          else if (document.fullscreenElement) document.exitFullscreen?.();
          return !p;
        });
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go]);

  if (error) return <div className="fatal">Could not load the app: {error}</div>;
  if (!steps.length) return <div className="loading"><span className="spinner" /> Loading the journey…</div>;

  const step = steps[current];
  return (
    <div className={`app ${present ? "present" : ""}`}>
      <TopBar who={who} setWho={setWho} dark={dark} setDark={setDark} user={info?.user} builder={builder} setBuilder={setBuilder} />
      <StepRail steps={steps} current={current} setCurrent={setCurrent} status={status} />
      <main className="stage">
        <ErrorBoundary resetKey={`${current}-${who}`}>
        {step.proof === "agent_console"
          ? <ExternalStage step={step} nodes={info?.nodes ?? {}} who={who} sources={builder ? sources?.nodes : null} />
          : <Diagram step={step} nodes={info?.nodes ?? {}} who={who} sources={builder ? sources?.nodes : null} />}
        </ErrorBoundary>
        <ErrorBoundary resetKey={`${current}-${who}`}>
        <StepPanel key={`${step.id}-${who}`} step={step} who={who} info={info} deep={deep} setDeep={setDeep} onJump={setCurrent}
                   built={builder ? (sources?.steps?.[step.id] ?? "loading") : null}
                   onPrev={() => go((c) => c - 1)} onNext={() => go((c) => c + 1)} isLast={current === steps.length - 1} />
        </ErrorBoundary>
      </main>
      <footer className="hints">
        <span><kbd>←</kbd><kbd>→</kbd> steps</span><span><kbd>0</kbd>–<kbd>8</kbd> jump</span>
        <span><kbd>V</kbd> view as</span><span><kbd>D</kbd> deep</span><span><kbd>T</kbd> theme</span><span><kbd>B</kbd> builder view</span><span><kbd>P</kbd> present</span>
        <span className="grow" />
        <span className="mono">Every result runs as the selected identity · the app never reads data as itself</span>
      </footer>
    </div>
  );
}
