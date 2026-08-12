"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import {
  ApiError,
  Deployment,
  Experiment,
  ExperimentComparison,
  Explanation,
  deploymentsApi,
  experimentsApi,
} from "@/lib/api";
import { Section, ShapBar, formatMetric } from "@/components/evidence";

export default function ExperimentWorkspacePage() {
  const params = useParams<{ id: string; experimentId: string }>();
  const projectId = params.id;
  const experimentId = params.experimentId;

  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [comparison, setComparison] = useState<ExperimentComparison | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [deployment, setDeployment] = useState<Deployment | null>(null);
  const [explainModel, setExplainModel] = useState("");
  const [deployName, setDeployName] = useState("");
  const [predictJson, setPredictJson] = useState('[{"age": 40, "income": 70000}]');
  const [predictResult, setPredictResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const exp = await experimentsApi.get(projectId, experimentId);
      setExperiment(exp);
      if (exp.status === "completed") {
        const cmp = await experimentsApi.comparison(projectId, experimentId);
        setComparison(cmp);
        const defaultModel =
          cmp.winner?.model_key || cmp.models[0]?.model_key || "";
        setExplainModel((prev) => prev || defaultModel);
        setDeployName((prev) => prev || `${exp.name} deploy`);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load experiment");
    }
  }, [projectId, experimentId]);

  useEffect(() => {
    void load();
  }, [load]);

  const topShap = useMemo(() => {
    const feats = explanation?.report.feature_importances?.slice(0, 12) || [];
    const max = Math.max(...feats.map((f) => f.mean_abs_shap), 0.0001);
    return { feats, max };
  }, [explanation]);

  async function onExplain(event: FormEvent) {
    event.preventDefault();
    if (!explainModel) return;
    setBusy("explain");
    setError(null);
    try {
      const result = await experimentsApi.explain(projectId, experimentId, {
        model_key: explainModel,
        max_samples: 48,
        instance_index: 0,
      });
      setExplanation(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "SHAP failed");
    } finally {
      setBusy(null);
    }
  }

  async function onDeploy(event: FormEvent) {
    event.preventDefault();
    setBusy("deploy");
    setError(null);
    try {
      const result = await deploymentsApi.create(projectId, {
        experiment_id: experimentId,
        name: deployName || "Deployment",
        model_key: explainModel || undefined,
      });
      setDeployment(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Deploy failed");
    } finally {
      setBusy(null);
    }
  }

  async function onPredict(event: FormEvent) {
    event.preventDefault();
    if (!deployment) return;
    setBusy("predict");
    setError(null);
    setPredictResult(null);
    try {
      const instances = JSON.parse(predictJson) as Array<Record<string, unknown>>;
      const result = await deploymentsApi.predict(
        projectId,
        deployment.id,
        instances,
      );
      setPredictResult(JSON.stringify(result, null, 2));
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : err instanceof SyntaxError
            ? "Predict JSON is invalid"
            : "Predict failed",
      );
    } finally {
      setBusy(null);
    }
  }

  if (!experiment && !error) {
    return <p className="text-sm text-muted">Loading experiment workspace…</p>;
  }

  return (
    <div className="mx-auto max-w-5xl">
      <Link
        href={`/projects/${projectId}`}
        className="text-sm text-muted hover:text-foreground"
      >
        ← Project
      </Link>

      <div className="mt-4 mb-8">
        <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-accent">
          Experiment workspace
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">
          {experiment?.name || "Experiment"}
        </h1>
        <p className="mt-2 text-sm text-muted">
          {experiment?.task_type} · target{" "}
          <span className="font-mono text-foreground">
            {experiment?.target_column}
          </span>{" "}
          · status{" "}
          <span className="font-mono text-accent">{experiment?.status}</span>
        </p>
      </div>

      {error ? <p className="mb-4 text-sm text-danger">{error}</p> : null}

      {experiment?.status === "failed" ? (
        <div className="mb-8 rounded-2xl border border-danger/40 bg-surface px-5 py-4 text-sm text-danger">
          {experiment.error_message || "Experiment failed"}
        </div>
      ) : null}

      <Section eyebrow="01 · Configuration" title="What was run">
        <div className="rounded-2xl border border-border bg-surface p-5 font-mono text-xs leading-relaxed text-muted">
          <pre className="whitespace-pre-wrap">
            {JSON.stringify(experiment?.config || {}, null, 2)}
          </pre>
        </div>
      </Section>

      {comparison ? (
        <>
          <Section eyebrow="02 · Decision" title="Winner & trade-offs">
            <div className="rounded-2xl border border-border bg-surface p-5">
              {comparison.winner ? (
                <>
                  <p className="text-sm">
                    Recommended{" "}
                    <span className="font-medium text-accent">
                      {comparison.winner.model_name}
                    </span>{" "}
                    on{" "}
                    <span className="font-mono">
                      {comparison.primary_metric}
                    </span>{" "}
                    ({formatMetric(comparison.winner.score)}).
                  </p>
                  <p className="mt-2 text-sm text-muted">
                    {comparison.winner.reason}
                  </p>
                </>
              ) : (
                <p className="text-sm text-muted">No winner available.</p>
              )}
              <ul className="mt-4 space-y-2">
                {comparison.tradeoffs.map((t) => (
                  <li
                    key={t}
                    className="rounded-lg border border-border bg-background/40 px-3 py-2 text-sm text-muted"
                  >
                    {t}
                  </li>
                ))}
              </ul>
            </div>
          </Section>

          <Section eyebrow="03 · Comparison" title="Models side by side">
            <div className="grid gap-3 lg:grid-cols-2">
              {comparison.models.map((card) => (
                <article
                  key={card.model_key}
                  className={`rounded-2xl border p-5 ${
                    card.is_winner
                      ? "border-accent/50 bg-accent-soft/30"
                      : "border-border bg-surface"
                  }`}
                >
                  <div className="mb-3 flex items-center justify-between gap-2">
                    <p className="text-sm font-medium">
                      #{card.rank} {card.model_name}
                    </p>
                    {card.is_winner ? (
                      <span className="font-mono text-[10px] uppercase tracking-wide text-accent">
                        Winner
                      </span>
                    ) : null}
                  </div>
                  <p className="font-mono text-xs text-muted">
                    primary {formatMetric(card.primary_score)} · Δ{" "}
                    {formatMetric(card.delta_vs_winner)} ·{" "}
                    {card.train_time_seconds.toFixed(3)}s
                  </p>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div>
                      <p className="mb-1 text-xs text-accent">Pros</p>
                      <ul className="space-y-1 text-xs text-muted">
                        {card.pros.map((p) => (
                          <li key={p}>• {p}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <p className="mb-1 text-xs text-muted">Cons</p>
                      <ul className="space-y-1 text-xs text-muted">
                        {card.cons.map((c) => (
                          <li key={c}>• {c}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </Section>
        </>
      ) : null}

      {experiment?.status === "completed" ? (
        <>
          <Section eyebrow="04 · Explain" title="SHAP evidence">
            <form
              onSubmit={onExplain}
              className="mb-4 flex flex-col gap-3 rounded-2xl border border-border bg-surface p-5 sm:flex-row sm:items-end"
            >
              <label className="block flex-1 text-sm">
                <span className="mb-1.5 block text-muted">Model to explain</span>
                <select
                  value={explainModel}
                  onChange={(e) => setExplainModel(e.target.value)}
                  className="w-full rounded-xl border border-border bg-background px-3 py-2.5 outline-none focus:border-accent/60"
                >
                  {(comparison?.models || []).map((m) => (
                    <option key={m.model_key} value={m.model_key}>
                      {m.model_name}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="submit"
                disabled={busy === "explain"}
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-border-strong bg-surface-2 px-4 py-2.5 text-sm font-medium disabled:opacity-60"
              >
                <span className="accent-dot" />
                {busy === "explain" ? "Computing SHAP…" : "Explain with SHAP"}
              </button>
            </form>

            {explanation ? (
              <div className="rounded-2xl border border-border bg-surface p-5">
                <p className="text-sm text-muted">
                  {explanation.report.summary}
                </p>
                <div className="mt-5 space-y-3">
                  {topShap.feats.map((f) => (
                    <ShapBar
                      key={f.feature}
                      label={f.feature}
                      value={f.mean_abs_shap}
                      max={topShap.max}
                    />
                  ))}
                </div>
                {explanation.report.instance ? (
                  <div className="mt-6 border-t border-border pt-4">
                    <p className="mb-2 text-xs text-accent">
                      Local contributions (instance{" "}
                      {explanation.report.instance.index})
                    </p>
                    <ul className="space-y-1 font-mono text-xs text-muted">
                      {explanation.report.instance.top_contributions
                        .slice(0, 8)
                        .map((c) => (
                          <li key={c.feature}>
                            {c.feature}: {c.shap_value.toFixed(4)}
                          </li>
                        ))}
                    </ul>
                    {explanation.report.instance.note ? (
                      <p className="mt-3 text-xs text-muted">
                        {explanation.report.instance.note}
                      </p>
                    ) : null}
                  </div>
                ) : null}
              </div>
            ) : (
              <p className="text-sm text-muted">
                Run SHAP to see which features drive the selected model — evidence
                for the recommendation above.
              </p>
            )}
          </Section>

          <Section eyebrow="05 · Deploy" title="Ship the decision">
            <form
              onSubmit={onDeploy}
              className="mb-4 flex flex-col gap-3 rounded-2xl border border-border bg-surface p-5 sm:flex-row sm:items-end"
            >
              <label className="block flex-1 text-sm">
                <span className="mb-1.5 block text-muted">Deployment name</span>
                <input
                  value={deployName}
                  onChange={(e) => setDeployName(e.target.value)}
                  className="w-full rounded-xl border border-border bg-background px-3 py-2.5 outline-none focus:border-accent/60"
                />
              </label>
              <button
                type="submit"
                disabled={busy === "deploy"}
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-border-strong bg-surface-2 px-4 py-2.5 text-sm font-medium disabled:opacity-60"
              >
                <span className="accent-dot" />
                {busy === "deploy"
                  ? "Deploying…"
                  : `Deploy ${explainModel || "winner"}`}
              </button>
            </form>

            {deployment ? (
              <div className="space-y-4">
                <div className="rounded-2xl border border-border bg-surface p-5 text-sm">
                  <p>
                    Active deployment{" "}
                    <span className="font-mono text-accent">{deployment.id}</span>{" "}
                    · model {deployment.model_key} · predictions{" "}
                    {deployment.prediction_count}
                  </p>
                  {deployment.bundle_hint ? (
                    <p className="mt-2 text-xs text-muted">
                      {deployment.bundle_hint}
                    </p>
                  ) : null}
                </div>

                <form onSubmit={onPredict} className="rounded-2xl border border-border bg-surface p-5">
                  <label className="block text-sm">
                    <span className="mb-1.5 block text-muted">
                      Predict instances (JSON array)
                    </span>
                    <textarea
                      value={predictJson}
                      onChange={(e) => setPredictJson(e.target.value)}
                      rows={5}
                      className="w-full rounded-xl border border-border bg-background px-3 py-2.5 font-mono text-xs outline-none focus:border-accent/60"
                    />
                  </label>
                  <button
                    type="submit"
                    disabled={busy === "predict"}
                    className="mt-3 inline-flex items-center justify-center gap-2 rounded-xl border border-border-strong bg-surface-2 px-4 py-2.5 text-sm font-medium disabled:opacity-60"
                  >
                    <span className="accent-dot" />
                    {busy === "predict" ? "Predicting…" : "Run prediction"}
                  </button>
                  {predictResult ? (
                    <pre className="mt-4 overflow-x-auto rounded-xl border border-border bg-background/60 p-3 font-mono text-xs text-muted">
                      {predictResult}
                    </pre>
                  ) : null}
                </form>
              </div>
            ) : (
              <p className="text-sm text-muted">
                Deploy the selected/winning model to get a live predict endpoint and
                a Docker export bundle.
              </p>
            )}
          </Section>
        </>
      ) : null}
    </div>
  );
}
