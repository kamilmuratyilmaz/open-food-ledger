import { useAuth } from "../../context/AuthContext";
import { ExportButton } from "./ExportButton";
import { TokenManager } from "./TokenManager";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function SettingsPanel({ open, onClose }: Props) {
  const { user, signOut } = useAuth();

  return (
    <>
      <div className={"panel-overlay" + (open ? " open" : "")} onClick={onClose} />
      <aside className={"panel" + (open ? " open" : "")}>
        <button className="panel-close" onClick={onClose} aria-label="close">
          ×
        </button>
        <h3>Settings</h3>

        <div className="sub-head">Account</div>
        <div className="help">
          Signed in as <b>{user?.email ?? "—"}</b>
        </div>

        <ExportButton />
        <TokenManager />

        <div className="sub-head">Danger zone</div>
        <button
          className="ghost"
          onClick={() => {
            onClose();
            signOut();
          }}
        >
          Sign out
        </button>
      </aside>
    </>
  );
}
