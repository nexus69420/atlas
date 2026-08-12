"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ApiError,
  Dataset,
  ExperimentSummary,
  Project,
  datasetsApi,
  experimentsApi,
  projectsApi,
} from "@/lib/api";
import { Section } from "@/components/evidence";

const CLASSIFICATION_MODELS = [
  "logistic_regression",
  "random_forest",
  "gradient_boosting",
];

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const projectId = params.id;

  const [project, setProject] = useState<Project | null>(null);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [running, setRunning] = useState(false);

  const [expName, setExpName] = useState("Baseline comparison");
  const [expDatasetId, setExpDatasetId] = useState("");
  const [expTarget, setExpTarget] = useState("");
  const [expTask, setExpTask] = useState<"classification" | "regression">(
    "classification",
  );
  const [expModels, setExpModels] = useState<string[]>([
    "logistic_regression",
    "random_forest",
  ]);

  async function reload() {
    try {
      const [p, d, e] = await Promise.all([
        projectsApi.get(projectId),
        datasetsApi.list(projectId),
        experimentsApi.list(projectId),
      ]);
      setProject(p);
      setDatasets(d);
      setExperiments(e);
      if (!expDatasetId && d[0]) {
        setExpDatasetId(d[0].id);
        const firstCol = d[0].column_schema?.[d[0].column_schema.length - 1]?.name;
        if (firstCol) setExpTarget(firstCol);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load project");
    }
  }

  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const selectedDataset = datasets.find((d) => d.id === expDatasetId);

  async function onUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const fileInput = form.elements.namedItem("file") as HTMLInputElement;
    const file = fileInput.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await datasetsApi.upload(projectId, file);
      form.reset();
      await reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function onRunExperiment(event: FormEvent) {
    event.preventDefault();
    setRunning(true);
    setError(null);
    try {
      const created = await experimentsApi.create(projectId, {
        dataset_id: expDatasetId,
        name: expName,
        target_column: expTarget,
        task_type: expTask,
        models: expModels,
      });
      router.push(`/projects/${projectId}/experiments/${created.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Experiment failed to start");
    } finally {
      setRunning(false);
    }
  }

  function toggleModel(key: string) {
    setExpModels((prev) =>
      prev.includes(key) ? prev.filter((m) => m !== key) : [...prev, key],
    );
  }

  if (!project && !error) {
    return <p className="text-sm text-muted">Loading project…</p>;
  }

  return (
    <div className="mx-auto max-w-5xl">
      <Link href="/projects" className="text-sm text-muted hover:text-foreground">
        ← Projects
      </Link>
      <div className="mt-4 mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">
          {project?.name || "Project"}
        </h1>
        <p className="mt-1 text-sm text-muted">
          {project?.description || "No description"}
        </p>
        <p className="mt-3 text-xs text-muted">
          Workflow: upload → profile → experiment → compare → explain → deploy
        </p>
      </div>

      {error ? <p className="mb-4 text-sm text-danger">{error}</p> : null}

      <Section eyebrow="01" title="Datasets">
        <form
          onSubmit={onUpload}
          className="mb-4 flex flex-col gap-3 rounded-2xl border border-border bg-surface p-4 sm:flex-row sm:items-center"
        >
          <input
            required
            name="file"
            type="file"
            accept=".csv,text/csv"
            className="flex-1 text-sm text-muted file:mr-3 file:rounded-lg file:border-0 file:bg-surface-2 file:px-3 file:py-2 file:text-foreground"
          />
          <button
            type="submit"
            disabled={uploading}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-border-strong bg-surface-2 px-4 py-2.5 text-sm font-medium disabled:opacity-60"
          >
            <span className="accent-dot" />
            {uploading ? "Uploading…" : "Upload CSV"}
          </button>
        </form>
        {datasets.length === 0 ? (
          <p className="text-sm text-muted">No datasets yet.</p>
        ) : (
          <ul className="space-y-2">
            {datasets.map((dataset) => (
              <li key={dataset.id}>
                <Link
                  href={`/projects/${projectId}/datasets/${dataset.id}`}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border bg-surface px-4 py-3 text-sm transition-colors hover:border-border-strong"
                >
                  <div>
                    <p className="font-medium">{dataset.name}</p>
                    <p className="text-xs text-muted">
                      {dataset.original_filename} · {dataset.row_count} rows ·{" "}
                      {dataset.column_count} cols · open Atlas Report →
                    </p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section eyebrow="02" title="Run experiment">
        <form
          onSubmit={onRunExperiment}
          className="space-y-4 rounded-2xl border border-border bg-surface p-5"
        >
          <p className="text-sm text-muted">
            Hypothesis → configuration → training → comparison. Atlas trains
            multiple models and explains the trade-offs — not a single AutoML
            guess.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-sm sm:col-span-2">
              <span className="mb-1.5 block text-muted">Experiment name</span>
              <input
                required
                value={expName}
                onChange={(e) => setExpName(e.target.value)}
                className="w-full rounded-xl border border-border bg-background px-3 py-2.5 outline-none focus:border-accent/60"
              />
            </label>
            <label className="block text-sm">
              <span className="mb-1.5 block text-muted">Dataset</span>
              <select
                required
                value={expDatasetId}
                onChange={(e) => {
                  setExpDatasetId(e.target.value);
                  const ds = datasets.find((d) => d.id === e.target.value);
                  const col =
                    ds?.column_schema?.[ds.column_schema.length - 1]?.name || "";
                  setExpTarget(col);
                }}
                className="w-full rounded-xl border border-border bg-background px-3 py-2.5 outline-none focus:border-accent/60"
              >
                <option value="" disabled>
                  Select dataset
                </option>
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm">
              <span className="mb-1.5 block text-muted">Target column</span>
              <select
                required
                value={expTarget}
                onChange={(e) => setExpTarget(e.target.value)}
                className="w-full rounded-xl border border-border bg-background px-3 py-2.5 outline-none focus:border-accent/60"
              >
                <option value="" disabled>
                  Select target
                </option>
                {(selectedDataset?.column_schema || []).map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm">
              <span className="mb-1.5 block text-muted">Task type</span>
              <select
                value={expTask}
                onChange={(e) =>
                  setExpTask(e.target.value as "classification" | "regression")
                }
                className="w-full rounded-xl border border-border bg-background px-3 py-2.5 outline-none focus:border-accent/60"
              >
                <option value="classification">Classification</option>
                <option value="regression">Regression</option>
              </select>
            </label>
          </div>
          <div>
            <p className="mb-2 text-sm text-muted">Models to compare</p>
            <div className="flex flex-wrap gap-2">
              {CLASSIFICATION_MODELS.map((key) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => toggleModel(key)}
                  className={`rounded-lg border px-3 py-1.5 font-mono text-xs ${
                    expModels.includes(key)
                      ? "border-accent/50 bg-accent-soft text-foreground"
                      : "border-border text-muted"
                  }`}
                >
                  {key}
                </button>
              ))}
            </div>
          </div>
          <button
            type="submit"
            disabled={running || !expDatasetId || expModels.length === 0}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-border-strong bg-surface-2 px-4 py-2.5 text-sm font-medium disabled:opacity-60"
          >
            <span className="accent-dot" />
            {running ? "Running experiment…" : "Run & open workspace"}
          </button>
        </form>
      </Section>

      <Section eyebrow="03" title="Experiment history">
        {experiments.length === 0 ? (
          <p className="text-sm text-muted">
            No experiments yet. Profile a dataset, then run a comparison above.
          </p>
        ) : (
          <ul className="space-y-2">
            {experiments.map((experiment) => (
              <li key={experiment.id}>
                <Link
                  href={`/projects/${projectId}/experiments/${experiment.id}`}
                  className="block rounded-xl border border-border bg-surface px-4 py-3 text-sm transition-colors hover:border-border-strong"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-medium">{experiment.name}</p>
                    <span className="font-mono text-xs text-accent">
                      {experiment.status}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-muted">
                    {experiment.task_type} · target: {experiment.target_column} ·
                    open workspace →
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Section>
    </div>
  );
}
