import React, { useState } from "react";
import { MessagesSquare, Workflow } from "lucide-react";
import AgentChat from "./AgentChat.jsx";
import Diagram from "./Diagram.jsx";

// Step 7: the stage becomes a real agent chat (the app playing an external MCP client); the map stays one click away.
export default function ExternalStage({ step, nodes, who, sources }) {
  const [view, setView] = useState("chat");
  return (
    <div className="ext-stage">
      <div className="seg" role="tablist" aria-label="Stage view">
        <button role="tab" aria-selected={view === "chat"} className={view === "chat" ? "on" : ""} onClick={() => setView("chat")}><MessagesSquare size={14} /> Agent chat</button>
        <button role="tab" aria-selected={view === "map"} className={view === "map" ? "on" : ""} onClick={() => setView("map")}><Workflow size={14} /> Architecture</button>
      </div>
      {/* keep the chat mounted so the conversation survives a look at the map */}
      <div className={`ext-pane ${view === "chat" ? "" : "hidden"}`}><AgentChat who={who} /></div>
      {view === "map" && <div className="ext-pane"><Diagram step={step} nodes={nodes} who={who} sources={sources} /></div>}
    </div>
  );
}
