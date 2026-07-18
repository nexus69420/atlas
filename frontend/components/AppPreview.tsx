export function AppPreview() {
  const nav = [
    { label: "Projects", active: true },
    { label: "Datasets", active: false },
    { label: "Experiments", active: false },
    { label: "Explain", active: false },
    { label: "Deployments", active: false },
  ];

  const projects = [
    {
      name: "Customer churn baseline",
      meta: "3 datasets · 2 experiments",
      status: "Ready",
    },
    {
      name: "Fraud detection v2",
      meta: "1 dataset · profiling done",
      status: "Active",
    },
    {
      name: "Demand forecast",
      meta: "Waiting on upload",
      status: "Draft",
    },
  ];

  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-[0_0_0_1px_rgba(255,255,255,0.03),0_40px_80px_rgba(0,0,0,0.55)]">
      <div className="flex items-center gap-2 border-b border-border px-4 py-3">
        <span className="h-2.5 w-2.5 rounded-full bg-border-strong" />
        <span className="h-2.5 w-2.5 rounded-full bg-border-strong" />
        <span className="h-2.5 w-2.5 rounded-full bg-border-strong" />
        <span className="ml-3 font-mono text-xs text-muted">
          app.atlas.local / projects
        </span>
      </div>
      <div className="grid min-h-[420px] grid-cols-1 md:grid-cols-[220px_1fr]">
        <aside className="border-b border-border p-4 md:border-b-0 md:border-r">
          <div className="mb-4 flex items-center gap-2 px-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-md border border-border text-[10px] text-accent">
              A
            </span>
            <span className="text-sm font-medium">Atlas</span>
          </div>
          <p className="mb-2 px-2 text-[11px] uppercase tracking-[0.14em] text-muted">
            Workspace
          </p>
          <ul className="space-y-1">
            {nav.map((item) => (
              <li key={item.label}>
                <div
                  className={`rounded-lg px-3 py-2 text-sm ${
                    item.active
                      ? "bg-surface-2 text-foreground"
                      : "text-muted"
                  }`}
                >
                  {item.label}
                </div>
              </li>
            ))}
          </ul>
        </aside>
        <section className="p-5">
          <div className="mb-5 flex items-end justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold tracking-tight">Projects</h3>
              <p className="mt-1 text-sm text-muted">
                Containers for datasets, experiments, and deployments.
              </p>
            </div>
            <button
              type="button"
              className="rounded-xl border border-border-strong bg-surface-2 px-3 py-2 text-xs font-medium"
            >
              New project
            </button>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <article
                key={project.name}
                className="rounded-xl border border-border bg-background/60 p-4 transition-colors hover:border-border-strong"
              >
                <div className="mb-3 flex items-center justify-between gap-2">
                  <span className="text-xs text-muted">{project.status}</span>
                  <span className="accent-dot !h-1.5 !w-1.5" />
                </div>
                <h4 className="text-sm font-medium leading-snug">
                  {project.name}
                </h4>
                <p className="mt-2 text-xs leading-relaxed text-muted">
                  {project.meta}
                </p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
