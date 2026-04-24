import { useState, useEffect } from "react";
import { BrowserRouter, useSearchParams } from "react-router-dom";
import Landing from "../src/pages/Landing";
import Chat from "./pages/Chat";
import { AppSession } from "./types/auth";

function AppInner() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [session, setSession] = useState<AppSession | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Step 1 — check if returning from Google OAuth
    const sidFromUrl = searchParams.get("session_id"); // ✅ correct param name
    if (sidFromUrl) {
      localStorage.setItem("pending_session", sidFromUrl);
      setSearchParams({});
      setReady(true);
      return;
    }

    // Step 2 — check if already have a saved session
    const saved = localStorage.getItem("app_session");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        fetch("https://ga4-mcp-backend-550184459078.us-central1.run.app/auth/properties", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: parsed.sessionId }),
        })
          .then((r) => r.json())
          .then((res) => {
            if (res.error) {
              localStorage.clear();
              setSession(null);
            } else {
              setSession(parsed);
            }
            setReady(true);
          })
          .catch(() => {
            localStorage.clear();
            setSession(null);
            setReady(true);
          });
        return;
      } catch {
        localStorage.removeItem("app_session");
      }
    }

    setReady(true);
  }, []);

  const handleSessionReady = (s: AppSession) => {
    localStorage.setItem("app_session", JSON.stringify(s));
    localStorage.removeItem("pending_session");
    setSession(s);
  };

  const handleLogout = () => {
    localStorage.clear();
    setSession(null);
  };

  if (!ready) return null; // avoid flash of Landing while validating

  return session
    ? <Chat session={session} onLogout={handleLogout} />
    : <Landing onSessionReady={handleSessionReady} />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AppInner />
    </BrowserRouter>
  );
}