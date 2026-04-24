import { useRef, useEffect, useState, KeyboardEvent } from "react";
import { useChat } from "../hooks/useChat";
import { ChatMessage } from "../types/chat";
import { AppSession } from "../types/auth";

const ALL_SUGGESTIONS = [
  "Active users today",
  "Top referral channels this month",
  "Bounce rate this month",
  "Sessions by country last 30 days",
  "New users this week",
  "Top 5 pages by views last 30 days",
  "Sessions by device this month",
  "Daily active users last 14 days",
  "Top cities by sessions last 90 days",
  "Engagement rate by country last 30 days",
  "Sessions from organic search this month",
  "Bounce rate by landing page last 30 days",
  "Top campaigns by sessions this month",
  "Sessions by browser last 30 days",
  "Active users by source last 7 days",
];

const getRandomChips = () =>
  [...ALL_SUGGESTIONS].sort(() => Math.random() - 0.5).slice(0, 4);

interface Props {
  session: AppSession;
  onLogout: () => void;
}

function DataTable({ rows }: { rows: Record<string, string>[] }) {
  if (!rows?.length) return null;
  const cols = Object.keys(rows[0]);
  return (
    <div style={{ overflowX: "auto", marginTop: 14, borderRadius: 10, overflow: "hidden", border: "1px solid rgba(255,255,255,0.06)" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
        <thead>
          <tr style={{ background: "rgba(255,255,255,0.04)" }}>
            {cols.map((c) => (
              <th key={c} style={{ textAlign: "left", padding: "8px 12px", color: "rgba(255,255,255,0.4)", fontWeight: 600, fontSize: 11, letterSpacing: "0.06em", textTransform: "uppercase" as const, borderBottom: "1px solid rgba(255,255,255,0.06)", fontFamily: "'Inter', sans-serif" }}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} style={{ background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.02)" }}>
              {cols.map((c) => (
                <td key={c} style={{ padding: "8px 12px", color: "rgba(255,255,255,0.75)", borderBottom: "1px solid rgba(255,255,255,0.04)", fontSize: 12, fontFamily: "'JetBrains Mono', monospace" }}>{row[c]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AssistantBubble({ msg }: { msg: ChatMessage }) {
  const formatted = msg.content
    .replace(
      /\*\*(.*?)\*\*/g,
      '<strong style="color:#4ade80;font-weight:700;font-family:\'Raleway\',sans-serif">$1</strong>'
    )
    .replace(
      /(\d+\.?\d*%)/g,
      '<span style="color:#4ade80;font-weight:600;font-family:\'JetBrains Mono\',monospace;font-size:13px">$1</span>'
    )
    .replace(
      /(`[^`]+`)/g,
      '<code style="font-family:\'JetBrains Mono\',monospace;font-size:12px;background:rgba(74,222,128,0.08);padding:2px 6px;border-radius:4px;color:#4ade80">$1</code>'
    );

  return (
    <div style={{ display: "flex", gap: 12, marginBottom: 24, alignItems: "flex-start" }}>
      <div style={{
        width: 34, height: 34, borderRadius: "50%", flexShrink: 0,
        background: "linear-gradient(135deg, #1a3a2a 0%, #0d2018 100%)",
        border: "1px solid rgba(74,222,128,0.3)",
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="#4ade80" />
        </svg>
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: "#4ade80", letterSpacing: "0.12em", marginBottom: 8, textTransform: "uppercase" as const, fontFamily: "'Raleway', sans-serif" }}>
          Aura Intelligence
        </div>
        <div style={{
          background: "linear-gradient(135deg, rgba(255,255,255,0.07) 0%, rgba(255,255,255,0.03) 100%)",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: "4px 16px 16px 16px",
          padding: "14px 18px",
          color: msg.error ? "#fca5a5" : "rgba(255,255,255,0.88)",
          fontSize: 14,
          lineHeight: 1.8,
          fontFamily: "'Raleway', sans-serif",
          fontWeight: 500,
        }}>
          <div style={{ whiteSpace: "pre-wrap" }} dangerouslySetInnerHTML={{ __html: formatted }} />
          {msg.tool_used && (
            <div style={{ marginTop: 12, display: "inline-flex", alignItems: "center", gap: 6, background: "rgba(74,222,128,0.08)", border: "1px solid rgba(74,222,128,0.2)", borderRadius: 20, padding: "3px 10px", fontSize: 11, color: "#4ade80", fontFamily: "'JetBrains Mono', monospace" }}>
              <div style={{ width: 5, height: 5, borderRadius: "50%", background: "#4ade80" }} />
              {msg.tool_used}
            </div>
          )}
          {msg.data && msg.data.length > 0 && <DataTable rows={msg.data} />}
        </div>
      </div>
    </div>
  );
}

function UserBubble({ msg }: { msg: ChatMessage }) {
  return (
    <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 24 }}>
      <div style={{
        maxWidth: "68%",
        background: "linear-gradient(135deg, rgba(74,222,128,0.15) 0%, rgba(74,222,128,0.08) 100%)",
        border: "1px solid rgba(74,222,128,0.2)",
        borderRadius: "16px 4px 16px 16px",
        padding: "12px 16px",
        color: "rgba(255,255,255,0.88)",
        fontSize: 14,
        lineHeight: 1.7,
        fontFamily: "'Raleway', sans-serif",
        fontWeight: 500,
      }}>
        {msg.content}
      </div>
    </div>
  );
}

function Bubble({ msg }: { msg: ChatMessage }) {
  return msg.role === "user" ? <UserBubble msg={msg} /> : <AssistantBubble msg={msg} />;
}

function TypingIndicator() {
  return (
    <div style={{ display: "flex", gap: 12, marginBottom: 24, alignItems: "flex-start" }}>
      <div style={{ width: 34, height: 34, borderRadius: "50%", flexShrink: 0, background: "linear-gradient(135deg, #1a3a2a 0%, #0d2018 100%)", border: "1px solid rgba(74,222,128,0.3)", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="#4ade80" /></svg>
      </div>
      <div style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "4px 16px 16px 16px", padding: "16px 20px", display: "flex", gap: 6, alignItems: "center" }}>
        {[0, 1, 2].map((i) => (
          <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: "#4ade80", opacity: 0.5, animation: `blink 1.4s ease-in-out ${i * 0.2}s infinite` }} />
        ))}
      </div>
    </div>
  );
}

export default function Chat({ session, onLogout }: Props) {
  const { messages, loading, send, reset } = useChat(session.propertyId, session.sessionId);
  const [input, setInput] = useState("");
  const [currentChips, setCurrentChips] = useState(() => getRandomChips());
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (messages.length > 0 && messages[messages.length - 1].role === "assistant") {
      setCurrentChips(getRandomChips());
    }
  }, [messages]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    send(text);
  };

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <div style={{
      height: "100vh",
      background: "#0d1117",
      color: "rgba(255,255,255,0.88)",
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
    }}>

      {/* ── Fixed Header ── */}
      <div style={{
        padding: "14px 20px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        background: "#0d1117",
        flexShrink: 0,
        zIndex: 100,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: "linear-gradient(135deg, #1a3a2a, #0d2018)", border: "1px solid rgba(74,222,128,0.3)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="#4ade80" /></svg>
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#4ade80", letterSpacing: "0.08em", fontFamily: "'Raleway', sans-serif" }}>
              {session.propertyName.toUpperCase()}
            </div>
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.25)", marginTop: 1, fontFamily: "'Inter', sans-serif" }}>
              {session.accountName} · GA4 MCP
            </div>
          </div>
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button onClick={reset} style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 20, padding: "7px 14px", color: "rgba(255,255,255,0.5)", fontSize: 12, cursor: "pointer", fontFamily: "'Inter', sans-serif", display: "flex", alignItems: "center", gap: 6, transition: "all 0.15s" }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(74,222,128,0.4)"; (e.currentTarget as HTMLElement).style.color = "#4ade80"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.1)"; (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.5)"; }}
          >
            + New Chat
          </button>
          <button onClick={onLogout} title="Sign out"
            style={{ width: 34, height: 34, borderRadius: "50%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", transition: "all 0.15s" }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(248,113,113,0.4)"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.1)"; }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" stroke="rgba(255,255,255,0.4)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </div>

      {/* ── Scrollable Messages ── */}
      <div style={{ flex: 1, overflowY: "auto", padding: "0 16px" }}>
        <div style={{ maxWidth: 680, margin: "0 auto" }}>
          {messages.length === 0 ? (
            <>
              <div style={{ padding: "52px 8px 40px" }}>
                <h1 style={{
                  fontSize: "clamp(26px, 5vw, 40px)",
                  fontWeight: 800,
                  lineHeight: 1.15,
                  margin: "0 0 14px",
                  color: "#fff",
                  letterSpacing: "-0.02em",
                  fontFamily: "'Poppins', sans-serif",
                }}>
                  Visualizing your{" "}
                  <span style={{ background: "linear-gradient(135deg, #4ade80 0%, #22c55e 50%, #16a34a 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                    neural data.
                  </span>
                </h1>
                <p style={{
                  fontSize: 14,
                  color: "rgba(255,255,255,0.35)",
                  lineHeight: 1.7,
                  maxWidth: 400,
                  margin: 0,
                  fontFamily: "'Inter', sans-serif",
                }}>
                  Query <strong style={{ color: "rgba(255,255,255,0.5)" }}>{session.propertyName}</strong> with natural language. Filters, trends, comparisons — all in plain English.
                </p>
              </div>
              <AssistantBubble msg={{
                role: "assistant",
                content: `I'm connected to **${session.propertyName}**. Ask me anything about your GA4 data — sessions, bounce rates, top pages, country breakdowns, or filtered queries.`,
              }} />
            </>
          ) : (
            <div style={{ paddingTop: 24 }}>
              {messages.map((m, i) => <Bubble key={i} msg={m} />)}
            </div>
          )}
          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* ── Fixed Bottom ── */}
      <div style={{ padding: "0 16px 24px", flexShrink: 0, background: "#0d1117" }}>
        <div style={{ maxWidth: 680, margin: "0 auto" }}>

          {!loading && (
            <div style={{ display: "flex", gap: 8, overflowX: "auto", paddingBottom: 12, scrollbarWidth: "none" as const }}>
              {currentChips.map((s) => (
                <button key={s} onClick={() => send(s)} style={{
                  flexShrink: 0, background: "rgba(255,255,255,0.05)",
                  border: "1px solid rgba(255,255,255,0.1)", borderRadius: 20,
                  padding: "8px 16px", color: "rgba(255,255,255,0.55)",
                  fontSize: 13, cursor: "pointer",
                  fontFamily: "'Raleway', sans-serif",
                  fontWeight: 600,
                  whiteSpace: "nowrap" as const, transition: "all 0.15s",
                }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(74,222,128,0.4)"; (e.currentTarget as HTMLElement).style.color = "#4ade80"; (e.currentTarget as HTMLElement).style.background = "rgba(74,222,128,0.06)"; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.1)"; (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.55)"; (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
                >{s}</button>
              ))}
            </div>
          )}

          <div style={{ display: "flex", alignItems: "center", gap: 10, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 24, padding: "6px 6px 6px 16px", transition: "border-color 0.15s" }}
            onFocusCapture={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(74,222,128,0.4)"; }}
            onBlurCapture={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.1)"; }}
          >
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask Aura about your GA4 data..."
              rows={1}
              style={{
                flex: 1, background: "transparent", border: "none",
                color: "rgba(255,255,255,0.88)", fontSize: 14,
                resize: "none", outline: "none",
                fontFamily: "'Raleway', sans-serif",
                fontWeight: 500,
                lineHeight: 1.5, padding: "6px 0",
                maxHeight: 120, overflowY: "auto" as const,
              }}
              onInput={(e) => {
                const t = e.target as HTMLTextAreaElement;
                t.style.height = "auto";
                t.style.height = Math.min(t.scrollHeight, 120) + "px";
              }}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              style={{ width: 38, height: 38, borderRadius: "50%", flexShrink: 0, background: loading || !input.trim() ? "rgba(255,255,255,0.06)" : "linear-gradient(135deg, #4ade80 0%, #16a34a 100%)", border: "none", cursor: loading || !input.trim() ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", transition: "all 0.15s" }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M5 12h14M12 5l7 7-7 7" stroke={loading || !input.trim() ? "rgba(255,255,255,0.2)" : "#fff"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>

          <div style={{ textAlign: "center", marginTop: 10, fontSize: 10, letterSpacing: "0.12em", color: "rgba(255,255,255,0.12)", textTransform: "uppercase" as const, fontFamily: "'Inter', sans-serif" }}>
            End-to-end encrypted · Neural processing active
          </div>
        </div>
      </div>

      <style>{`
        @keyframes blink { 0%,80%,100%{opacity:0.3;transform:scale(0.8)} 40%{opacity:1;transform:scale(1)} }
        *{box-sizing:border-box;}
        ::-webkit-scrollbar{width:0;height:0;}
        textarea::placeholder{color:rgba(255,255,255,0.2);font-family:'Raleway',sans-serif;}
      `}</style>
    </div>
  );
}