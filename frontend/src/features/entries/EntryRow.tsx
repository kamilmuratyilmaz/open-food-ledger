import { fmt } from "../../lib/format";
import type { Entry } from "../../types/api";

interface Props {
  entry: Entry;
  onEdit: (entry: Entry) => void;
  onDelete: (entry: Entry) => void;
}

export function EntryRow({ entry, onEdit, onDelete }: Props) {
  return (
    <div className="entry-row">
      <div className="entry-time num">{entry.entry_time || "—"}</div>
      <div>
        <span className="entry-meal">{entry.meal_type}</span>
        <div className="entry-name">{entry.food_name}</div>
        <div className="entry-meta">
          <span className="accent">{fmt(entry.calories)} kcal</span>
          <span className="sep">·</span>
          <span>{fmt(entry.weight_g)}g</span>
          <span className="sep">·</span>
          <span>P {fmt(entry.protein_g, 1)}</span>
          <span className="sep">·</span>
          <span>C {fmt(entry.carbs_g, 1)}</span>
          <span className="sep">·</span>
          <span>F {fmt(entry.fat_g, 1)}</span>
        </div>
        {entry.notes && <div className="entry-notes">"{entry.notes}"</div>}
      </div>
      <div className="entry-actions">
        <button className="tiny" onClick={() => onEdit(entry)}>edit</button>
        <button className="tiny danger" onClick={() => onDelete(entry)}>×</button>
      </div>
    </div>
  );
}
