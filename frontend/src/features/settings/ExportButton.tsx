import { useAuth } from "../../context/AuthContext";
import { pushToast } from "../../hooks/useToast";

export function ExportButton() {
  const { token } = useAuth();

  async function exportXlsx() {
    if (!token) return;
    try {
      const res = await fetch("/api/export/xlsx", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const cd = res.headers.get("Content-Disposition") || "";
      const match = cd.match(/filename="?([^"]+)"?/);
      const fname = match ? match[1] : "food-log.xlsx";
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fname;
      a.click();
      URL.revokeObjectURL(url);
      pushToast("XLSX downloaded.");
    } catch (e) {
      pushToast((e as Error).message, true);
    }
  }

  return (
    <>
      <div className="sub-head">Export</div>
      <div className="help">
        Download your full log as XLSX. Open it directly in Excel, Numbers, or import into Google Sheets via <code>File → Import</code>.
      </div>
      <button onClick={exportXlsx} style={{ marginTop: 6 }}>Download XLSX</button>
    </>
  );
}
