// Tiny external store shared by the chat (writer) and the OBO trace panel (reader).
import { useSyncExternalStore } from "react";

let state = { phase: "idle", waiting: false, identity: null, calls: {}, order: [], last: null, done: null };
const subs = new Set();
const set = (patch) => { state = { ...state, ...patch }; subs.forEach((f) => f()); };

export const trace = {
  reset: () => set({ phase: "idle", waiting: false, identity: null, calls: {}, order: [], last: null, done: null }),
  start: () => set({ phase: "running", waiting: true, done: null }),
  identity: (ev) => set({ identity: ev }),
  text: () => set({ waiting: false }),
  toolStart: (ev) => set({ waiting: false, last: ev.id, order: [...state.order, ev.id],
    calls: { ...state.calls, [ev.id]: { ...ev, status: "running", t0: Date.now() } } }),
  toolProgress: (ev) => set({ calls: { ...state.calls, [ev.id]: { ...state.calls[ev.id], progress: ev } } }),
  toolEnd: (ev) => set({ waiting: true, calls: { ...state.calls, [ev.id]: { ...state.calls[ev.id], ...ev, status: ev.ok ? "ok" : "fail" } } }),
  finish: (ev) => set({ phase: "done", waiting: false, done: ev || {} }),
  fail: (message) => set({ phase: "done", waiting: false, done: { error: message } }),
};

export const useTrace = () => useSyncExternalStore((f) => { subs.add(f); return () => subs.delete(f); }, () => state);

// Parse a fetch() body of server-sent events ("data: {...}\n\n").
export async function* readSSE(body) {
  const reader = body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i;
    while ((i = buf.indexOf("\n\n")) >= 0) {
      const chunk = buf.slice(0, i); buf = buf.slice(i + 2);
      const line = chunk.split("\n").find((l) => l.startsWith("data:"));
      if (line) { try { yield JSON.parse(line.slice(5)); } catch { /* ignore keep-alives */ } }
    }
  }
}
