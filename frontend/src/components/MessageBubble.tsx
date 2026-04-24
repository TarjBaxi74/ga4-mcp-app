import { ChatMessage } from "../types/chat";
import DataTable from "./DataTable";

export default function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
      marginBottom: 16,
    }}>
      <div style={{
        maxWidth: "75%",
        background: isUser ? "#2563eb" : (msg.error ? "#450a0a" : "#111827"),
        border: `1px solid ${isUser ? "#1d4ed8" : (msg.error ? "#7f1d1d" : "#1f2937")}`,
        borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
        padding: "12px 16px",
        color: "#f9fafb",
        fontSize: 14,
        lineHeight: 1.6,
      }}>
        <div style={{ whiteSpace: "pre-wrap" }}>{msg.content}</div>

        {msg.tool_used && (
          <div style={{
            marginTop: 8,
            display: "inline-block",
            background: "#0f172a",
            border: "1px solid #334155",
            borderRadius: 6,
            padding: "2px 8px",
            fontSize: 11,
            color: "#94a3b8",
          }}>
            🔧 {msg.tool_used}
          </div>
        )}

        {msg.data && msg.data.length > 0 && (
          <div style={{
            marginTop: 12,
            background: "#0f172a",
            borderRadius: 8,
            padding: 12,
            border: "1px solid #1e293b",
          }}>
            <DataTable rows={msg.data} />
          </div>
        )}
      </div>
    </div>
  );
}