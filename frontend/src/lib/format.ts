export function todayStr(): string {
  return new Date().toISOString().slice(0, 10);
}

export function nowTime(): string {
  return new Date().toTimeString().slice(0, 5);
}

export function fmt(n: number | null | undefined, digits = 0): string {
  if (n == null || isNaN(n)) return "0";
  return Number(n).toFixed(digits).replace(/\.0+$/, "");
}

export function formatDateLong(isoDate: string): string {
  const d = new Date(isoDate + "T00:00:00");
  return d.toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}
