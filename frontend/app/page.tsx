import { AppPreview } from "@/components/AppPreview";
import { CtaButton, SiteHeader } from "@/components/marketing";

export default function HomePage() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Atmospheric full-bleed plane — not a card */}
      <div
        aria-hidden
        className="ambient-orb pointer-events-none absolute -left-24 top-[-10%] h-[520px] w-[520px] rounded-full bg-[radial-gradient(circle,rgba(45,212,191,0.18),transparent_68%)] blur-2xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute right-[-10%] top-[20%] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle,rgba(20,184,166,0.1),transparent_70%)] blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_bottom,transparent,rgba(5,5,5,0.35)_40%,#050505_92%)]"
      />

      <SiteHeader />

      <main>
        <section className="relative z-10 mx-auto flex min-h-[78vh] w-full max-w-4xl flex-col items-center justify-center px-6 pb-16 pt-10 text-center">
          <p className="animate-fade-up mb-6 text-sm font-medium tracking-[0.22em] text-accent uppercase">
            Atlas
          </p>
          <h1 className="animate-fade-up-delay max-w-3xl text-4xl font-semibold tracking-tight text-balance sm:text-5xl md:text-6xl">
            Evidence-driven machine learning engineering
          </h1>
          <p className="animate-fade-up-delay-2 mt-5 max-w-xl text-base leading-relaxed text-muted sm:text-lg">
            Profile datasets, run comparable experiments, explain models with
            SHAP, and deploy — with reasoning at every step.
          </p>
          <div className="animate-fade-up-delay-2 mt-9 flex flex-wrap items-center justify-center gap-3">
            <CtaButton href="/register" className="px-6 py-3 text-[15px]">
              Start building
            </CtaButton>
            <CtaButton href="/login" variant="ghost">
              Sign in
            </CtaButton>
          </div>
        </section>

        <section id="product" className="relative z-10 mx-auto max-w-6xl px-6 pb-24">
          <AppPreview />
        </section>

        <section
          id="workflow"
          className="relative z-10 mx-auto max-w-6xl px-6 pb-28"
        >
          <div className="max-w-2xl">
            <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              From dataset to deployment — one engineering spine
            </h2>
            <p className="mt-3 text-muted">
              Atlas is not AutoML theater. Each stage produces measurable
              evidence you can inspect, compare, and ship.
            </p>
          </div>
          <ol className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["01", "Profile", "Missingness, correlations, imbalance warnings."],
              ["02", "Experiment", "Train multiple models. Rank with trade-offs."],
              ["03", "Explain", "SHAP global + local drivers, in plain language."],
              ["04", "Deploy", "Predict live or export a Docker model bundle."],
            ].map(([step, title, body]) => (
              <li
                key={step}
                className="rounded-2xl border border-border bg-surface/70 p-5"
              >
                <p className="font-mono text-xs text-accent">{step}</p>
                <h3 className="mt-3 text-base font-medium">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{body}</p>
              </li>
            ))}
          </ol>
        </section>
      </main>

      <footer className="border-t border-border px-6 py-8 text-center text-sm text-muted">
        Atlas — ML Engineering Platform. Open source, evidence first.
      </footer>
    </div>
  );
}
