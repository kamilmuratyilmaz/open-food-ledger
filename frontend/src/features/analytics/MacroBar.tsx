import { fmt } from "../../lib/format";

interface Props {
  proteinPct: number;
  carbsPct: number;
  fatPct: number;
}

export function MacroBar({ proteinPct, carbsPct, fatPct }: Props) {
  return (
    <>
      <div className="macro-bar">
        <div className="protein" style={{ width: `${proteinPct}%` }} />
        <div className="carbs" style={{ width: `${carbsPct}%` }} />
        <div className="fat" style={{ width: `${fatPct}%` }} />
      </div>
      <div className="macro-legend">
        <span>
          <span className="dot" style={{ background: "var(--accent)" }} />
          <span>P {fmt(proteinPct)}%</span>
        </span>
        <span>
          <span className="dot" style={{ background: "var(--warn)" }} />
          <span>C {fmt(carbsPct)}%</span>
        </span>
        <span>
          <span className="dot" style={{ background: "var(--good)" }} />
          <span>F {fmt(fatPct)}%</span>
        </span>
      </div>
    </>
  );
}
