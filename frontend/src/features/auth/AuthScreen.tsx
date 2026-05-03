import { useState, type FormEvent } from "react";
import { useAuth } from "../../context/AuthContext";
import { ApiError } from "../../lib/api";

type Mode = "login" | "register";

export function AuthScreen() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(ev: FormEvent) {
    ev.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "login") await login(email.trim(), password);
      else await register(email.trim(), password);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : (e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  function switchMode(m: Mode) {
    setMode(m);
    setError(null);
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <h1 className="display">
          Ledger<em>,</em>
        </h1>
        <div className="sub">a quiet food log.</div>

        <div className="auth-tabs">
          <button
            type="button"
            className={"auth-tab" + (mode === "login" ? " active" : "")}
            onClick={() => switchMode("login")}
          >
            Sign in
          </button>
          <button
            type="button"
            className={"auth-tab" + (mode === "register" ? " active" : "")}
            onClick={() => switchMode("register")}
          >
            Create account
          </button>
        </div>

        <form onSubmit={onSubmit} autoComplete="on">
          <div className="field">
            <label>Email</label>
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="field">
            <label>Password</label>
            <input
              type="password"
              required
              minLength={8}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <div className="auth-error">{error}</div>}
          <button type="submit" className="full" disabled={submitting}>
            {mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
      </div>
    </div>
  );
}
