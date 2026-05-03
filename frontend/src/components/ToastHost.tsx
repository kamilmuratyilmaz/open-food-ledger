import { useToasts } from "../hooks/useToast";

export function ToastHost() {
  const toasts = useToasts();
  return (
    <div>
      {toasts.map((t) => (
        <div key={t.id} className={"toast" + (t.err ? " err" : "")}>
          {t.msg}
        </div>
      ))}
    </div>
  );
}
