import { todayStr } from "../../lib/format";

interface Props {
  value: string;
  onChange: (date: string) => void;
  onRefresh: () => void;
}

export function DateFilter({ value, onChange, onRefresh }: Props) {
  return (
    <span style={{ display: "flex", gap: 8, alignItems: "center" }} className="toolbar">
      <input
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      <button className="tiny" onClick={() => onChange(todayStr())}>today</button>
      <button className="tiny" onClick={onRefresh}>refresh</button>
    </span>
  );
}
