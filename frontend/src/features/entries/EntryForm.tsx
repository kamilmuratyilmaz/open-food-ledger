import { useEffect, useState, type FormEvent } from "react";
import { pushToast } from "../../hooks/useToast";
import { ApiError } from "../../lib/api";
import { nowTime } from "../../lib/format";
import type { Entry, EntryIn, MealType } from "../../types/api";

interface Props {
  filterDate: string;
  editing: Entry | null;
  onCancelEdit: () => void;
  onCreate: (payload: EntryIn) => Promise<unknown>;
  onUpdate: (id: string, payload: Partial<EntryIn>) => Promise<unknown>;
}

interface FormValues {
  food_name: string;
  weight_g: string;
  meal_type: MealType;
  calories: string;
  protein_g: string;
  carbs_g: string;
  fat_g: string;
  fiber_g: string;
  sugar_g: string;
  sodium_mg: string;
  notes: string;
  entry_time: string;
}

const empty: FormValues = {
  food_name: "",
  weight_g: "",
  meal_type: "breakfast",
  calories: "",
  protein_g: "",
  carbs_g: "",
  fat_g: "",
  fiber_g: "",
  sugar_g: "",
  sodium_mg: "",
  notes: "",
  entry_time: "",
};

function fromEntry(e: Entry): FormValues {
  const num = (n: number) => (n ? String(n) : "");
  return {
    food_name: e.food_name,
    weight_g: num(e.weight_g),
    meal_type: e.meal_type,
    calories: num(e.calories),
    protein_g: num(e.protein_g),
    carbs_g: num(e.carbs_g),
    fat_g: num(e.fat_g),
    fiber_g: num(e.fiber_g),
    sugar_g: num(e.sugar_g),
    sodium_mg: num(e.sodium_mg),
    notes: e.notes ?? "",
    entry_time: e.entry_time ?? "",
  };
}

export function EntryForm({ filterDate, editing, onCancelEdit, onCreate, onUpdate }: Props) {
  const [v, setV] = useState<FormValues>(empty);
  const [microsOpen, setMicrosOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (editing) {
      setV(fromEntry(editing));
      setMicrosOpen(true);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [editing]);

  function set<K extends keyof FormValues>(key: K, val: FormValues[K]) {
    setV((prev) => ({ ...prev, [key]: val }));
  }

  function clear() {
    setV(empty);
    onCancelEdit();
  }

  async function onSubmit(ev: FormEvent) {
    ev.preventDefault();
    if (!v.food_name.trim() || !parseFloat(v.weight_g)) {
      pushToast("Need a food name and a weight", true);
      return;
    }
    const numOr0 = (s: string) => parseFloat(s) || 0;
    const payload: EntryIn = {
      food_name: v.food_name.trim(),
      weight_g: numOr0(v.weight_g),
      meal_type: v.meal_type,
      calories: numOr0(v.calories),
      protein_g: numOr0(v.protein_g),
      carbs_g: numOr0(v.carbs_g),
      fat_g: numOr0(v.fat_g),
      fiber_g: numOr0(v.fiber_g),
      sugar_g: numOr0(v.sugar_g),
      sodium_mg: numOr0(v.sodium_mg),
      notes: v.notes.trim() || null,
      entry_time: v.entry_time || nowTime(),
    };
    setSubmitting(true);
    try {
      if (editing) {
        await onUpdate(editing.id, payload);
        pushToast("Updated.");
      } else {
        await onCreate({ ...payload, entry_date: filterDate });
        pushToast("Logged.");
      }
      setV(empty);
      onCancelEdit();
    } catch (e) {
      pushToast(e instanceof ApiError ? e.detail : (e as Error).message, true);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section>
      <h2 className="sec">
        {editing ? "Edit entry" : "New entry"} <span className="pill">+</span>
      </h2>
      <form className="entry" onSubmit={onSubmit}>
        <div className="full">
          <label>Food</label>
          <input
            placeholder="grilled chicken, oats with banana, ..."
            required
            value={v.food_name}
            onChange={(e) => set("food_name", e.target.value)}
          />
        </div>
        <div>
          <label>Weight (g)</label>
          <input
            type="number"
            step="1"
            min="0"
            className="num"
            required
            value={v.weight_g}
            onChange={(e) => set("weight_g", e.target.value)}
          />
        </div>
        <div>
          <label>Meal</label>
          <select value={v.meal_type} onChange={(e) => set("meal_type", e.target.value as MealType)}>
            <option value="breakfast">breakfast</option>
            <option value="lunch">lunch</option>
            <option value="dinner">dinner</option>
            <option value="snack">snack</option>
          </select>
        </div>
        <div>
          <label>Calories (kcal)</label>
          <input
            type="number" step="0.1" min="0" className="num"
            value={v.calories}
            onChange={(e) => set("calories", e.target.value)}
          />
        </div>
        <div>
          <label>Protein (g)</label>
          <input
            type="number" step="0.1" min="0" className="num"
            value={v.protein_g}
            onChange={(e) => set("protein_g", e.target.value)}
          />
        </div>
        <div>
          <label>Carbs (g)</label>
          <input
            type="number" step="0.1" min="0" className="num"
            value={v.carbs_g}
            onChange={(e) => set("carbs_g", e.target.value)}
          />
        </div>
        <div>
          <label>Fat (g)</label>
          <input
            type="number" step="0.1" min="0" className="num"
            value={v.fat_g}
            onChange={(e) => set("fat_g", e.target.value)}
          />
        </div>

        <button
          type="button"
          className="micros-toggle"
          onClick={() => setMicrosOpen((o) => !o)}
        >
          {microsOpen ? "− hide micros & notes" : "+ add micros & notes"}
        </button>

        <div className={"micros-fields" + (microsOpen ? "" : " hidden")}>
          <div>
            <label>Fiber (g)</label>
            <input
              type="number" step="0.1" min="0" className="num"
              value={v.fiber_g}
              onChange={(e) => set("fiber_g", e.target.value)}
            />
          </div>
          <div>
            <label>Sugar (g)</label>
            <input
              type="number" step="0.1" min="0" className="num"
              value={v.sugar_g}
              onChange={(e) => set("sugar_g", e.target.value)}
            />
          </div>
          <div>
            <label>Sodium (mg)</label>
            <input
              type="number" step="1" min="0" className="num"
              value={v.sodium_mg}
              onChange={(e) => set("sodium_mg", e.target.value)}
            />
          </div>
          <div>
            <label>Time</label>
            <input
              type="time" className="num"
              value={v.entry_time}
              onChange={(e) => set("entry_time", e.target.value)}
            />
          </div>
          <div className="full">
            <label>Notes</label>
            <textarea
              rows={1}
              placeholder="optional"
              value={v.notes}
              onChange={(e) => set("notes", e.target.value)}
            />
          </div>
        </div>

        <div className="submit-row">
          <button type="button" className="ghost" onClick={clear}>
            Clear
          </button>
          <button type="submit" disabled={submitting}>
            {editing ? "Update entry" : "Save entry"}
          </button>
        </div>
      </form>
    </section>
  );
}
