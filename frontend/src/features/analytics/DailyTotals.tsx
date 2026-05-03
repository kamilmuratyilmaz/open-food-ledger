import { useMemo } from "react";
import { fmt, formatDateLong, todayStr } from "../../lib/format";
import type { Entry } from "../../types/api";
import { MacroBar } from "./MacroBar";

interface Props {
  entries: Entry[];
  date: string;
}

export function DailyTotals({ entries, date }: Props) {
  const dayEntries = useMemo(
    () => entries.filter((e) => e.entry_date === date),
    [entries, date],
  );

  const sum = (k: keyof Entry) =>
    dayEntries.reduce((a, e) => a + (Number(e[k]) || 0), 0);
  const cal = sum("calories");
  const p = sum("protein_g");
  const c = sum("carbs_g");
  const f = sum("fat_g");
  const pk = p * 4;
  const ck = c * 4;
  const fk = f * 9;
  const tot = pk + ck + fk || 1;

  const niceDate = formatDateLong(date);
  const heading = date === todayStr() ? `Today, ${niceDate}` : niceDate;

  return (
    <div className="totals">
      <div className="totals-head">
        <div className="date display">{heading}</div>
        <div className="count">
          {dayEntries.length} {dayEntries.length === 1 ? "entry" : "entries"}
        </div>
      </div>
      <div className="totals-grid">
        <div className="stat accent">
          <div className="k">Calories</div>
          <div className="v">
            {fmt(cal)}
            <span className="unit">kcal</span>
          </div>
        </div>
        <div className="stat">
          <div className="k">Protein</div>
          <div className="v">
            {fmt(p, 1)}
            <span className="unit">g</span>
          </div>
        </div>
        <div className="stat">
          <div className="k">Carbs</div>
          <div className="v">
            {fmt(c, 1)}
            <span className="unit">g</span>
          </div>
        </div>
        <div className="stat">
          <div className="k">Fat</div>
          <div className="v">
            {fmt(f, 1)}
            <span className="unit">g</span>
          </div>
        </div>
      </div>
      <MacroBar
        proteinPct={(pk / tot) * 100}
        carbsPct={(ck / tot) * 100}
        fatPct={(fk / tot) * 100}
      />
    </div>
  );
}
