import { useAuth } from "../context/AuthContext";
import { todayStr } from "../lib/format";

interface Props {
  onOpenSettings: () => void;
}

export function Masthead({ onOpenSettings }: Props) {
  const { user, signOut } = useAuth();
  return (
    <header className="mast">
      <div className="mast-title display">
        Open Food Ledger<em>,</em>
        <br />a food log.
      </div>
      <div className="mast-meta">
        <div>
          Vol. I &middot; <b>{todayStr()}</b>
        </div>
        <div>
          <b>{user?.email ?? "—"}</b>
          <span className="sep">·</span>
          <a onClick={onOpenSettings}>settings</a>
          <span className="sep">·</span>
          <a onClick={signOut}>sign out</a>
        </div>
      </div>
    </header>
  );
}
