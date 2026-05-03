import { useMemo } from "react";
import { pushToast } from "../../hooks/useToast";
import { ApiError } from "../../lib/api";
import type { Entry } from "../../types/api";
import { DateFilter } from "./DateFilter";
import { EntryRow } from "./EntryRow";

interface Props {
  entries: Entry[];
  filterDate: string;
  onFilterDateChange: (date: string) => void;
  onRefresh: () => void;
  onEdit: (entry: Entry) => void;
  onDelete: (id: string) => Promise<void>;
}

export function EntryList({
  entries,
  filterDate,
  onFilterDateChange,
  onRefresh,
  onEdit,
  onDelete,
}: Props) {
  const dayEntries = useMemo(
    () =>
      entries
        .filter((e) => e.entry_date === filterDate)
        .sort((a, b) => (a.entry_time || "").localeCompare(b.entry_time || "")),
    [entries, filterDate],
  );

  async function handleDelete(entry: Entry) {
    if (!confirm(`Delete "${entry.food_name}"?`)) return;
    try {
      await onDelete(entry.id);
      pushToast("Deleted.");
    } catch (e) {
      pushToast(e instanceof ApiError ? e.detail : (e as Error).message, true);
    }
  }

  return (
    <section>
      <h2 className="sec">
        The log
        <DateFilter
          value={filterDate}
          onChange={onFilterDateChange}
          onRefresh={onRefresh}
        />
      </h2>
      <div className="entries">
        {dayEntries.length === 0 ? (
          <div className="empty">No entries on this day. Yet.</div>
        ) : (
          dayEntries.map((e) => (
            <EntryRow
              key={e.id}
              entry={e}
              onEdit={onEdit}
              onDelete={handleDelete}
            />
          ))
        )}
      </div>
    </section>
  );
}
