/** Shared evidence-first UI primitives for Atlas engineering workflows. */

export function SeverityBadge({ severity }: { severity: string }) {
  const tone =
    severity === "high"
      ? "border-danger/40 text-danger"
      : severity === "medium"
        ? "border-accent/40 text-accent"
        : "border-border-strong text-muted";
  return (
    <span
      className={`rounded-md border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide ${tone}`}
    >
      {severity}
    </span>
  );
}

export function Section({
  eyebrow,
  title,
  children,
}: {
  eyebrow?: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mb-10">
      {eyebrow ? (
        <p className="mb-1 font-mono text-[11px] uppercase tracking-[0.14em] text-accent">
          {eyebrow}
        </p>
      ) : null}
      <h2 className="mb-4 text-lg font-medium tracking-tight">{title}</h2>
      {children}
    </section>
  );
}

export function ShapBar({
  label,
  value,
  max,
}: {
  label: string;
  value: number;
  max: number;
}) {
  const width = max > 0 ? Math.max(4, (Math.abs(value) / max) * 100) : 0;
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_120px] items-center gap-3 text-sm">
      <div className="min-w-0">
        <p className="truncate font-mono text-xs text-muted">{label}</p>
        <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-surface-2">
          <div
            className="h-full rounded-full bg-accent"
            style={{ width: `${width}%` }}
          />
        </div>
      </div>
      <p className="text-right font-mono text-xs tabular-nums">
        {value.toFixed(4)}
      </p>
    </div>
  );
}

export function formatMetric(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  return value.toFixed(4);
}
