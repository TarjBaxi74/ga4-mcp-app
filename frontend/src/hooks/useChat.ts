import { useState } from "react";
import { sendChat } from "../api/client";
import { ChatMessage } from "../types/chat";

export function useChat(propertyId: string, sessionId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);

  const send = async (text: string) => {
    const userMsg: ChatMessage = { role: "user", content: text };
    const next = [...messages, userMsg];
    setMessages(next);
    setLoading(true);

    try {
      const history = next.map((m) => ({ role: m.role, content: m.content }));
      const res = await sendChat(text, history, propertyId, sessionId);
      setMessages([
        ...next,
        {
          role: "assistant",
          content: res.reply,
          data: res.data,
          tool_used: res.tool_used,
        },
      ]);
    } catch {
      setMessages([
        ...next,
        {
          role: "assistant",
          content: "Backend error — is your FastAPI server running?",
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setMessages([]);
    setLoading(false);
  };

  return { messages, loading, send, reset };
}