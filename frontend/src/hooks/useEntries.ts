import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import type { Entry, EntryIn, EntryUpdate } from "../types/api";

interface UseEntriesResult {
  entries: Entry[];
  loading: boolean;
  refresh: () => Promise<void>;
  create: (payload: EntryIn) => Promise<Entry>;
  update: (id: string, payload: EntryUpdate) => Promise<Entry>;
  remove: (id: string) => Promise<void>;
}

export function useEntries(): UseEntriesResult {
  const { token, status } = useAuth();
  const [entries, setEntries] = useState<Entry[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await api<Entry[]>("GET", "/api/entries?limit=2000", undefined, token);
      setEntries(data);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (status === "authed") {
      refresh();
    } else if (status === "anon") {
      setEntries([]);
    }
  }, [status, refresh]);

  const create = useCallback(
    async (payload: EntryIn) => {
      const e = await api<Entry>("POST", "/api/entries", payload, token);
      await refresh();
      return e;
    },
    [token, refresh],
  );

  const update = useCallback(
    async (id: string, payload: EntryUpdate) => {
      const e = await api<Entry>("PATCH", `/api/entries/${id}`, payload, token);
      await refresh();
      return e;
    },
    [token, refresh],
  );

  const remove = useCallback(
    async (id: string) => {
      await api("DELETE", `/api/entries/${id}`, undefined, token);
      await refresh();
    },
    [token, refresh],
  );

  return { entries, loading, refresh, create, update, remove };
}
