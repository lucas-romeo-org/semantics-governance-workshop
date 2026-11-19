import React, { memo, useEffect, useMemo, useRef, useState } from "react";
import { AssistantRuntimeProvider, ComposerPrimitive, MessagePrimitive, ThreadPrimitive, useLocalRuntime } from "@assistant-ui/react";
import { MarkdownTextPrimitive } from "@assistant-ui/react-markdown";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ArrowDown, ArrowUp, Bot, Check, ChevronDown, Database, ExternalLink, Loader, Lock, MessageSquare, Network,
  RotateCcw, Sparkles, Square, X } from "lucide-react";
import { IDENTITIES, api, eur } from "../api.js";
import { readSSE, trace, useTrace } from "../trace.js";

const SERVERS = [
  { id: "genie_one", label: "Genie One MCP", service: "system.ai.genie_one_mcp", icon: Sparkles, hint: "answers grounded on the ontology" },
  { id: "dbsql", label: "DBSQL MCP", service: "system.ai.dbsql", icon: Database, hint: "your agent writes the SQL" },
];
const SUGGESTIONS = [
  { title: "Net sales by region", sub: "last quarter, vs budget", prompt: "What were net sales by region in 2026-Q3 versus budget?" },
  { title: "Top 5 customers", sub: "PII decided by policy", prompt: "Who are the top 5 customers by net sales in 2026?" },
  { title: "Year over year", sub: "window measure", prompt: "How did net sales grow year over year in 2026, month by month?" },
  { title: "Try to read gold", sub: "the trap", prompt: "Show me raw rows from gold.fact_sales", trap: true },
];
const isMask = (ch) => (Array.isArray(ch) ? ch.join("") : String(ch ?? "")).trim() === "****";
const links = {
  a: ({ node, ...p }) => <a {...p} target="_blank" rel="noreferrer" />,
  td: ({ node, children, ...p }) => <td {...p}>{isMask(children) ? <span className="masked"><Lock size={10} /> masked</span> : children}</td>,
};

const MarkdownText = memo(() => <MarkdownTextPrimitive remarkPlugins={[remarkGfm]} className="md" components={links} />);

// ── adapter: the assistant-ui runtime talks to /api/chat (server-sent events) ─────────────────────────────
function makeAdapter(ctx) {
  return {
    async *run({ messages, abortSignal }) {
      const { who, servers } = ctx.current;
      const history = messages.map((m) => ({
        role: m.role,
        content: (m.content || []).filter((p) => p.type === "text").map((p) => p.text).join("\n"),
      })).filter((m) => m.content);
      trace.start();
      const res = await fetch("/api/chat", {
        method: "POST", signal: abortSignal, headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ who, servers, history, genie_conversation_id: ctx.current.genieConv }),
      });
      if (!res.ok) { const msg = `${res.status} · ${(await res.text()).slice(0, 200)}`; trace.fail(msg); throw new Error(msg); }
      const parts = [];
      const snapshot = () => ({ content: parts.map((p) => ({ ...p })) });
      for await (const ev of readSSE(res.body)) {
        if (ev.t === "identity") trace.identity(ev);
        else if (ev.t === "text" && ev.text) { trace.text(); parts.push({ type: "text", text: ev.text }); yield snapshot(); }
        else if (ev.t === "tool_start") {
          trace.toolStart(ev);
          parts.push({ type: "tool-call", toolCallId: ev.id, toolName: ev.tool, args: ev.args, argsText: JSON.stringify(ev.args) });
          yield snapshot();
        } else if (ev.t === "tool_progress") trace.toolProgress(ev);
        else if (ev.t === "tool_end") {
          trace.toolEnd(ev);
          const p = parts.find((x) => x.toolCallId === ev.id);
          if (p) p.result = { ok: ev.ok, state: ev.state || ev.status };
          yield snapshot();
        } else if (ev.t === "error") { parts.push({ type: "text", text: `**Error** · ${ev.message}` }); trace.fail(ev.message); yield snapshot(); }
        else if (ev.t === "done") { if (ev.genie_conversation_id) ctx.current.genieConv = ev.genie_conversation_id; trace.finish(ev); }
      }
      if (!parts.length) { parts.push({ type: "text", text: "_(no answer)_" }); yield snapshot(); }
    },
  };
}

// ── tool call card: what the MCP client sent, as whom, and what Unity Catalog returned ─────────────────────
function Cell({ v }) {
  if (v === "****") return <span className="masked"><Lock size={10} /> masked</span>;
  if (v !== null && v !== "" && !isNaN(Number(v)) && Math.abs(Number(v)) >= 1000) return <span className="num">{eur(v)}</span>;
  if (v !== null && v !== "" && !isNaN(Number(v)) && String(v).includes(".")) return <span className="num">{Number(v).toFixed(3)}</span>;
  return v ?? "–";
}

function Elapsed({ t0 }) {
  const [, tick] = useState(0);
  useEffect(() => { const i = setInterval(() => tick((n) => n + 1), 500); return () => clearInterval(i); }, []);
  return <>{((Date.now() - t0) / 1000).toFixed(0)}s</>;
}

const ToolCard = (props) => {
  const id = props.toolCallId ?? props.part?.toolCallId;
  const { calls, identity } = useTrace();
  const c = calls[id] || { tool: props.toolName, args: props.args || {}, status: props.result ? "ok" : "running" };
  const [open, setOpen] = useState(true);
  const genie = c.tool === "genie_ask";
  const S = genie ? SERVERS[0] : SERVERS[1];
  const who = IDENTITIES.find((i) => i.id === identity?.who) || IDENTITIES[0];
  return (
    <div className={`tool ${c.status}`}>
      <button className="tool-head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className="tool-ico"><S.icon size={14} /></span>
        <span className="tool-name"><span className="mono">{S.service}</span><b>{c.tool}</b></span>
        <span className="tool-as" style={{ "--c": who.color }}><span className="avatar xs">{who.label[0]}</span>as {who.label}</span>
        <span className="grow" />
        {c.status === "running" && <span className="pill run"><Loader size={11} className="spin" />{genie && c.progress ? `polling · ${c.progress.polls}` : "running"} · <Elapsed t0={c.t0 || Date.now()} /></span>}
        {c.status === "ok" && <span className="pill ok"><Check size={11} />{genie ? "answered" : `${c.rows?.length ?? 0} rows`} · {c.seconds}s</span>}
        {c.status === "fail" && <span className="pill bad"><X size={11} />rejected by Unity Catalog</span>}
        <ChevronDown size={14} className={`chev ${open ? "up" : ""}`} />
      </button>
      {open && (
        <div className="tool-body">
          {genie ? <div className="tool-q"><MessageSquare size={12} /> {c.args?.question}</div>
                 : <pre className="sql">{c.args?.query}</pre>}
          {c.status === "fail" && <div className="tool-err"><Lock size={13} /> <span>{(c.error || "").replace(/\s+/g, " ").slice(0, 280)}</span></div>}
          {!genie && c.status === "ok" && c.rows?.length > 0 && (
            <div className="tbl-wrap"><table className="rtable">
              <thead><tr>{c.columns.map((h) => <th key={h}>{h}</th>)}</tr></thead>
              <tbody>{c.rows.slice(0, 8).map((r, i) => <tr key={i}>{r.map((v, j) => <td key={j}><Cell v={v} /></td>)}</tr>)}</tbody>
            </table>{c.rows.length > 8 && <div className="more">+{c.rows.length - 8} more rows</div>}</div>
          )}
          {genie && c.status === "ok" && (<>
            <GenieAnswer text={c.answer || ""} />
            {c.sql && <details className="genie-sql"><summary>SQL Genie ran</summary><pre className="sql">{c.sql}</pre></details>}
            {c.deep_link && <a className="tool-link" href={c.deep_link} target="_blank" rel="noreferrer">Open this answer in Genie One <ExternalLink size={11} /></a>}
          </>)}
        </div>
      )}
    </div>
  );
};

function GenieAnswer({ text }) {
  const [more, setMore] = useState(false);
  const long = text.length > 650;
  return (
    <div className={`md genie-md ${long && !more ? "clamped" : ""}`}>
      <Markdown remarkPlugins={[remarkGfm]} components={links}>{text}</Markdown>
      {long && <button className="more-btn" onClick={() => setMore(!more)}>{more ? "Show less" : "Show Genie's full answer"}</button>}
    </div>
  );
}

// ── thread ───────────────────────────────────────────────────────────────────────────────────────────────
const UserMessage = () => (
  <MessagePrimitive.Root className="msg user"><div className="bubble"><MessagePrimitive.Content /></div></MessagePrimitive.Root>
);
const AssistantMessage = () => (
  <MessagePrimitive.Root className="msg assistant">
    <div className="msg-avatar"><Bot size={15} /></div>
    <div className="msg-body"><MessagePrimitive.Content components={{ Text: MarkdownText, tools: { Fallback: ToolCard } }} /></div>
  </MessagePrimitive.Root>
);

function Thinking() {
  const { phase, waiting } = useTrace();
  if (phase !== "running" || !waiting) return null;
  return <div className="msg assistant thinking"><div className="msg-avatar"><Bot size={15} /></div><div className="dots"><i /><i /><i /></div></div>;
}

function Welcome({ ident, servers }) {
  return (
    <div className="welcome">
      <div className="welcome-mark"><Network size={22} /></div>
      <h3>Ask as {ident.label}</h3>
      <p>An agent with {servers.length === 2 ? "two MCP servers" : "one MCP server"} connected, exactly like Claude or ChatGPT.
        Every tool call carries {ident.id === "me" ? "your" : `${ident.label}'s`} token.</p>
      <div className="suggest">
        {SUGGESTIONS.map((s) => (
          <ThreadPrimitive.Suggestion key={s.title} prompt={s.prompt} method="replace" autoSend className={`sugg ${s.trap ? "trap" : ""}`}>
            <b>{s.title}</b><small>{s.sub}</small>
          </ThreadPrimitive.Suggestion>
        ))}
      </div>
    </div>
  );
}

function Thread({ ident, servers }) {
  return (
    <ThreadPrimitive.Root className="thread">
      <ThreadPrimitive.Viewport className="viewport">
        <ThreadPrimitive.Empty><Welcome ident={ident} servers={servers} /></ThreadPrimitive.Empty>
        <ThreadPrimitive.Messages components={{ UserMessage, AssistantMessage }} />
        <Thinking />
        <div className="viewport-pad" />
        <ThreadPrimitive.ScrollToBottom className="to-bottom" aria-label="Scroll to bottom"><ArrowDown size={15} /></ThreadPrimitive.ScrollToBottom>
      </ThreadPrimitive.Viewport>
      <ComposerPrimitive.Root className="composer">
        <ComposerPrimitive.Input className="composer-input" placeholder={`Ask a data question as ${ident.label}…`} autoFocus rows={1} />
        <ThreadPrimitive.If running={false}>
          <ComposerPrimitive.Send className="send" aria-label="Send"><ArrowUp size={17} /></ComposerPrimitive.Send>
        </ThreadPrimitive.If>
        <ThreadPrimitive.If running>
          <ComposerPrimitive.Cancel className="send stop" aria-label="Stop"><Square size={13} /></ComposerPrimitive.Cancel>
        </ThreadPrimitive.If>
      </ComposerPrimitive.Root>
    </ThreadPrimitive.Root>
  );
}

function Runtime({ who, servers, ident }) {
  const ctx = useRef({ who, servers, genieConv: null });
  ctx.current.who = who; ctx.current.servers = servers;
  const adapter = useMemo(() => makeAdapter(ctx), []);
  const runtime = useLocalRuntime(adapter);
  useEffect(() => trace.reset(), []);
  return <AssistantRuntimeProvider runtime={runtime}><Thread ident={ident} servers={servers} /></AssistantRuntimeProvider>;
}

// ── chat card: header with the connected MCP servers (tools/list as the user) ────────────────────────────────
export default function AgentChat({ who }) {
  const ident = IDENTITIES.find((i) => i.id === who);
  const [servers, setServers] = useState(["genie_one", "dbsql"]);
  const [tools, setTools] = useState(null);
  const [nonce, setNonce] = useState(0);
  useEffect(() => { setTools(null); api.mcpTools(who).then(setTools).catch(() => setTools({})); }, [who]);
  const toggle = (id) => setServers((s) => (s.includes(id) ? (s.length > 1 ? s.filter((x) => x !== id) : s) : [...s, id]));

  return (
    <section className="chat">
      <header className="chat-head">
        <div className="chat-title"><b>Agent chat</b><span className="who-badge" style={{ "--c": ident.color }}><span className="avatar sm">{ident.label[0]}</span>as {ident.label}</span></div>
        <div className="servers" role="group" aria-label="Connected MCP servers">
          <span className="eyebrow">MCP servers</span>
          {SERVERS.map((s) => {
            const on = servers.includes(s.id), t = tools?.[s.id];
            return (
              <button key={s.id} className={`server ${on ? "on" : ""}`} onClick={() => toggle(s.id)} aria-pressed={on}
                      title={t?.tools?.map((x) => `${x.name}: ${x.description}`).join("\n") || s.service}>
                <span className="sw">{on && <Check size={11} strokeWidth={3} />}</span>
                <s.icon size={14} /><span className="server-txt"><b>{s.label}</b>
                  <small>{t ? (t.ok ? `${t.tools.length} tools discovered` : "not reachable") : "discovering…"}</small></span>
              </button>
            );
          })}
        </div>
        <button className="ghost sm" onClick={() => setNonce((n) => n + 1)} title="New chat"><RotateCcw size={14} /> New chat</button>
      </header>
      <Runtime key={`${who}-${servers.join()}-${nonce}`} who={who} servers={servers} ident={ident} />
    </section>
  );
}
