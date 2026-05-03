import { useState } from "react";
import { ToastHost } from "./components/ToastHost";
import { Masthead } from "./components/Masthead";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { useEntries } from "./hooks/useEntries";
import { todayStr } from "./lib/format";
import { AuthScreen } from "./features/auth/AuthScreen";
import { DailyTotals } from "./features/analytics/DailyTotals";
import { EntryForm } from "./features/entries/EntryForm";
import { EntryList } from "./features/entries/EntryList";
import { SettingsPanel } from "./features/settings/SettingsPanel";
import type { Entry } from "./types/api";

function AppShell() {
  const [filterDate, setFilterDate] = useState<string>(() => todayStr());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const { entries, refresh, create, update, remove } = useEntries();

  const editing: Entry | null = editingId
    ? entries.find((e) => e.id === editingId) ?? null
    : null;

  return (
    <>
      <div className="shell">
        <Masthead onOpenSettings={() => setSettingsOpen(true)} />
        <main>
          <div className="grid">
            <EntryForm
              filterDate={filterDate}
              editing={editing}
              onCancelEdit={() => setEditingId(null)}
              onCreate={create}
              onUpdate={update}
            />
            <section>
              <DailyTotals entries={entries} date={filterDate} />
              <EntryList
                entries={entries}
                filterDate={filterDate}
                onFilterDateChange={setFilterDate}
                onRefresh={refresh}
                onEdit={(e) => setEditingId(e.id)}
                onDelete={remove}
              />
            </section>
          </div>
          <div className="footnote">
            PostgreSQL &middot; readable by your MCP &middot; Made with restraint.
          </div>
        </main>
      </div>
      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}

function Root() {
  const { status } = useAuth();
  if (status === "loading") return null;
  if (status === "anon") return <AuthScreen />;
  return <AppShell />;
}

export default function App() {
  return (
    <AuthProvider>
      <Root />
      <ToastHost />
    </AuthProvider>
  );
}
