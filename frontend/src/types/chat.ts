export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  data?: Record<string, string>[];
  tool_used?: string;
  error?: boolean;
}