import axios from "axios";

const api = axios.create({
  baseURL: "https://ga4-mcp-backend-550184459078.us-central1.run.app",
  headers: { "Content-Type": "application/json" },
});

// ✅ attach session_id automatically to every request
api.interceptors.request.use((config) => {
  const sessionId =
    localStorage.getItem("pending_session") ||
    JSON.parse(localStorage.getItem("app_session") || "{}")?.sessionId;

  if (sessionId) {
    config.headers["session_id"] = sessionId;
  }

  return config;
});

export const getAuthUrl = () =>
  api.get("/auth/url").then((r) => r.data);

export const getProperties = (session_id: string) =>
  api.post("/auth/properties", { session_id }).then((r) => r.data);

export const sendChat = (
  message: string,
  history: { role: string; content: string }[],
  property_id: string,
  session_id: string
) =>
  api
    .post("/chat", { message, history, property_id, session_id })
    .then((r) => r.data);