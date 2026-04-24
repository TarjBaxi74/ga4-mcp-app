import { useEffect, useState } from "react";
import { getAuthUrl, getProperties } from "../api/client";
import { GA4Account, GA4Property, AppSession } from "../types/auth";

interface Props {
  onSessionReady: (session: AppSession) => void;
}

type Stage = "landing" | "loading" | "pick";

export default function Landing({ onSessionReady }: Props) {
  const [stage, setStage] = useState<Stage>("landing");
  const [accounts, setAccounts] = useState<GA4Account[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [error, setError] = useState("");
  const [expandedAccount, setExpandedAccount] = useState<string | null>(null);
  const [selectedProp, setSelectedProp] = useState<string | null>(null);

  useEffect(() => {
    const sid = localStorage.getItem("pending_session");
    if (sid) {
      setSessionId(sid);
      setStage("loading");
      getProperties(sid)
        .then((res) => {
          if (res.error) {
            setError(res.error);
            localStorage.removeItem("pending_session");
            setStage("landing");
            return;
          }
          localStorage.removeItem("pending_session");
          setAccounts(res.accounts || []);
          if (res.accounts?.length > 0) {
            setExpandedAccount(res.accounts[0].id);
          }
          setStage("pick");
        })
        .catch(() => {
          setError("Failed to fetch properties. Please try again.");
          localStorage.removeItem("pending_session");
          setStage("landing");
        });
    }
  }, []);

  const handleGoogleLogin = async () => {
    try {
      setStage("loading");
      const res = await getAuthUrl();
      window.location.href = res.url;
    } catch {
      setError("Failed to start login. Is the backend running?");
      setStage("landing");
    }
  };

  const handleSelectProperty = (account: GA4Account, prop: GA4Property) => {
    setSelectedProp(prop.id);
    setTimeout(() => {
      onSessionReady({
        sessionId,
        propertyId: prop.id,
        propertyName: prop.name,
        accountName: account.name,
      });
    }, 300);
  };

  const base = {
    root: {
      minHeight: "100vh",
      background: "#0d1117",
      color: "rgba(255,255,255,0.88)",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif",
      display: "flex" as const,
      flexDirection: "column" as const,
      alignItems: "center" as const,
      justifyContent: "center" as const,
      padding: 24,
    },
    card: {
      width: "100%",
      maxWidth: 480,
      background: "rgba(255,255,255,0.03)",
      border: "1px solid rgba(255,255,255,0.08)",
      borderRadius: 20,
      padding: 40,
    },
  };

  if (stage === "loading") {
    return (
      <div style={base.root}>
        <div style={base.card}>
          <div style={{ textAlign: "center", padding: "20px 0" }}>
            <div style={{ fontSize: 32, color: "#4ade80", marginBottom: 16 }}>◈</div>
            <div style={{ color: "#4ade80", fontSize: 14, fontWeight: 600, marginBottom: 6 }}>
              Connecting to GA4
            </div>
            <div style={{ color: "rgba(255,255,255,0.25)", fontSize: 12 }}>
              Fetching your analytics properties...
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (stage === "pick") {
    return (
      <div style={base.root}>
        <div style={{ ...base.card, maxWidth: 520 }}>
          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: "#fff", marginBottom: 4 }}>
              Select a Property
            </div>
            <div style={{ fontSize: 13, color: "rgba(255,255,255,0.3)" }}>
              Choose which GA4 property to connect to the MCP server
            </div>
          </div>

          <div style={{ maxHeight: 400, overflowY: "auto" as const, marginBottom: 16 }}>
            {accounts.map((account) => (
              <div key={account.id} style={{
                background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.06)",
                borderRadius: 12,
                marginBottom: 10,
                overflow: "hidden",
              }}>
                <div
                  style={{
                    padding: "12px 16px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    cursor: "pointer",
                  }}
                  onClick={() =>
                    setExpandedAccount(expandedAccount === account.id ? null : account.id)
                  }
                >
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.75)" }}>
                      {account.name}
                    </div>
                    <div style={{ fontSize: 11, color: "rgba(255,255,255,0.25)", marginTop: 2 }}>
                      {account.properties.length} propert{account.properties.length === 1 ? "y" : "ies"} · Account ID: {account.id}
                    </div>
                  </div>
                  <div style={{
                    fontSize: 11,
                    color: "rgba(255,255,255,0.25)",
                    transform: expandedAccount === account.id ? "rotate(180deg)" : "rotate(0deg)",
                    transition: "transform 0.15s",
                  }}>▾</div>
                </div>

                {expandedAccount === account.id && account.properties.map((prop) => (
                  <div
                    key={prop.id}
                    onClick={() => handleSelectProperty(account, prop)}
                    style={{
                      padding: "10px 16px 10px 32px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      borderTop: "1px solid rgba(255,255,255,0.04)",
                      cursor: "pointer",
                      background: selectedProp === prop.id
                        ? "rgba(74,222,128,0.08)"
                        : "transparent",
                      transition: "background 0.15s",
                    }}
                    onMouseEnter={(e) => {
                      if (selectedProp !== prop.id)
                        (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)";
                    }}
                    onMouseLeave={(e) => {
                      if (selectedProp !== prop.id)
                        (e.currentTarget as HTMLElement).style.background = "transparent";
                    }}
                  >
                    <div>
                      <div style={{
                        fontSize: 13,
                        color: selectedProp === prop.id ? "#4ade80" : "rgba(255,255,255,0.6)",
                        fontWeight: selectedProp === prop.id ? 600 : 400,
                      }}>
                        {prop.name}
                      </div>
                      <div style={{ fontSize: 11, color: "rgba(255,255,255,0.2)", fontFamily: "monospace", marginTop: 2 }}>
                        Property ID: {prop.id}
                      </div>
                    </div>
                    {selectedProp === prop.id && (
                      <div style={{ color: "#4ade80", fontSize: 16 }}>✓</div>
                    )}
                  </div>
                ))}
              </div>
            ))}
          </div>

          {error && (
            <div style={{ color: "#f87171", fontSize: 12, padding: "8px 12px", background: "rgba(248,113,113,0.08)", borderRadius: 8, border: "1px solid rgba(248,113,113,0.2)", marginBottom: 16 }}>
              {error}
            </div>
          )}

          <button
            onClick={() => { localStorage.removeItem("pending_session"); setStage("landing"); }}
            style={{ background: "transparent", border: "none", color: "rgba(255,255,255,0.25)", fontSize: 12, cursor: "pointer", fontFamily: "inherit", padding: 0 }}
          >
            ← Sign in with a different account
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={base.root}>
      <div style={base.card}>
        <div style={{
          width: 48, height: 48, borderRadius: 14,
          background: "linear-gradient(135deg, #1a3a2a, #0d2018)",
          border: "1px solid rgba(74,222,128,0.3)",
          display: "flex", alignItems: "center", justifyContent: "center",
          marginBottom: 20,
        }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="#4ade80" />
          </svg>
        </div>

        <div style={{ fontSize: 22, fontWeight: 700, color: "#fff", marginBottom: 6, letterSpacing: "-0.02em" }}>
          GA4 Analytics MCP
        </div>
        <div style={{ fontSize: 13, color: "rgba(255,255,255,0.35)", marginBottom: 32, lineHeight: 1.6 }}>
          Connect your Google Analytics account and query any property using natural language.
        </div>

        <button
          onClick={handleGoogleLogin}
          style={{
            width: "100%",
            background: "rgba(74,222,128,0.1)",
            border: "1px solid rgba(74,222,128,0.3)",
            borderRadius: 12, padding: "13px 0",
            color: "#4ade80", fontSize: 14, fontWeight: 600,
            cursor: "pointer", fontFamily: "inherit",
            display: "flex", alignItems: "center", justifyContent: "center", gap: 10,
            transition: "all 0.15s",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.background = "rgba(74,222,128,0.18)";
            (e.currentTarget as HTMLElement).style.borderColor = "rgba(74,222,128,0.5)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.background = "rgba(74,222,128,0.1)";
            (e.currentTarget as HTMLElement).style.borderColor = "rgba(74,222,128,0.3)";
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4ade80" />
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#22c55e" />
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#16a34a" />
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#4ade80" />
          </svg>
          Continue with Google
        </button>

        {error && (
          <div style={{ color: "#f87171", fontSize: 12, textAlign: "center", marginTop: 14, padding: "8px 12px", background: "rgba(248,113,113,0.08)", borderRadius: 8, border: "1px solid rgba(248,113,113,0.2)" }}>
            {error}
          </div>
        )}

        <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", margin: "28px 0" }} />

        {[
          "Works with any GA4 account and all its properties",
          "Natural language — no SQL or dashboards needed",
          "Filters, comparisons, trends, funnels and more",
          "Your data stays in your session only",
        ].map((f) => (
          <div key={f} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13, color: "rgba(255,255,255,0.3)", marginBottom: 10 }}>
            <div style={{ width: 5, height: 5, borderRadius: "50%", background: "#4ade80", opacity: 0.6, flexShrink: 0 }} />
            {f}
          </div>
        ))}
      </div>

      <div style={{ marginTop: 20, fontSize: 11, color: "rgba(255,255,255,0.12)", letterSpacing: "0.06em" }}>
        OAUTH SECURED · SESSION ONLY · NO DATA STORED
      </div>
    </div>
  );
}