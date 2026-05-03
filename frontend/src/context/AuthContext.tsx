import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "../lib/api";
import { clearStoredToken, getStoredToken, setStoredToken } from "../lib/storage";
import type { AuthResponse, User } from "../types/api";

type Status = "loading" | "authed" | "anon";

interface AuthContextValue {
  token: string | null;
  user: User | null;
  status: Status;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  signOut: () => void;
  rotateToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<Status>(() => (getStoredToken() ? "loading" : "anon"));

  const fetchMe = useCallback(async (t: string) => {
    const me = await api<User>("GET", "/api/me", undefined, t);
    setUser(me);
    setStatus("authed");
  }, []);

  // Bootstrap: if a token exists in storage, try to load /api/me
  useEffect(() => {
    if (!token) {
      setStatus("anon");
      return;
    }
    fetchMe(token).catch(() => {
      // 401 already cleared storage in api(); reflect locally
      setToken(null);
      setUser(null);
      setStatus("anon");
    });
  }, [token, fetchMe]);

  // Listen for global 401 events from any api() call
  useEffect(() => {
    function onUnauth() {
      setToken(null);
      setUser(null);
      setStatus("anon");
    }
    window.addEventListener("ft:unauthorized", onUnauth);
    return () => window.removeEventListener("ft:unauthorized", onUnauth);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const data = await api<AuthResponse>("POST", "/api/auth/login", { email, password });
    setStoredToken(data.api_token);
    setToken(data.api_token);
    setStatus("loading");
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const data = await api<AuthResponse>("POST", "/api/auth/register", { email, password });
    setStoredToken(data.api_token);
    setToken(data.api_token);
    setStatus("loading");
  }, []);

  const signOut = useCallback(() => {
    clearStoredToken();
    setToken(null);
    setUser(null);
    setStatus("anon");
  }, []);

  const rotateToken = useCallback(async () => {
    if (!token) throw new Error("not signed in");
    const data = await api<AuthResponse>("POST", "/api/me/rotate-token", undefined, token);
    setStoredToken(data.api_token);
    setToken(data.api_token);
    setUser((u) => (u ? { ...u, api_token: data.api_token } : u));
  }, [token]);

  const value = useMemo<AuthContextValue>(
    () => ({ token, user, status, login, register, signOut, rotateToken }),
    [token, user, status, login, register, signOut, rotateToken],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
