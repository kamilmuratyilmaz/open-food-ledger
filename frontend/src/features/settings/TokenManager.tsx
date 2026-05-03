import { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { pushToast } from "../../hooks/useToast";
import { ApiError } from "../../lib/api";

const MASK = "••••••••••••••••••••••••";

export function TokenManager() {
  const { user, rotateToken } = useAuth();
  const [revealed, setRevealed] = useState(false);

  if (!user) return null;

  async function copy() {
    try {
      await navigator.clipboard.writeText(user!.api_token);
      pushToast("Token copied.");
    } catch {
      pushToast("Copy failed.", true);
    }
  }

  async function rotate() {
    if (!confirm("Rotating breaks any MCP servers using the old token. Continue?")) return;
    try {
      await rotateToken();
      pushToast("Token rotated.");
    } catch (e) {
      pushToast(e instanceof ApiError ? e.detail : (e as Error).message, true);
    }
  }

  return (
    <>
      <div className="sub-head">MCP token</div>
      <div className="help">
        Use this token in your Claude Desktop config so Claude can read &amp; write your log via the MCP server.
      </div>
      <div className={"token-display" + (revealed ? " revealed" : "")}>
        {revealed ? user.api_token : MASK}
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <button className="ghost tiny" onClick={() => setRevealed((r) => !r)}>
          {revealed ? "Hide" : "Reveal"}
        </button>
        <button className="ghost tiny" onClick={copy}>Copy</button>
        <button className="ghost tiny danger" onClick={rotate}>Rotate</button>
      </div>
      <div className="help" style={{ marginTop: 14 }}>
        API base URL: <code>{window.location.origin}</code>
      </div>
    </>
  );
}
