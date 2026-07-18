"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  ApiError,
  Dataset,
  ExperimentSummary,
  Project,
  datasetsApi,
  experimentsApi,
  projectsApi,
} from "@/lib/api";

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;

  const [project, setProject] = useState<Project | null>(null);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [p, d, e] = await Promise.all([
          projectsApi.get(projectId),
          datasetsApi.list(projectId),
          experimentsApi.list(projectId),
        ]);
        setProject(p);
        setDatasets(d);
        setExperiments(e);
      } catch (err) {
        setError(err instanceof ApiError ? err.detail : "Failed to load project");
      }
    }
    void load();
  }, [projectId]);

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
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load project");
    }
  }

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
      </div>

      {error ? <p className="mb-4 text-sm text-danger">{error}</p> : null}

      <section className="mb-10">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-lg font-medium">Datasets</h2>
        </div>
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
              <li
                key={dataset.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border bg-surface px-4 py-3 text-sm"
              >
                <div>
                  <p className="font-medium">{dataset.name}</p>
                  <p className="text-xs text-muted">
                    {dataset.original_filename} · {dataset.row_count} rows ·{" "}
                    {dataset.column_count} cols
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="mb-4 text-lg font-medium">Experiments</h2>
        {experiments.length === 0 ? (
          <p className="text-sm text-muted">
            No experiments yet. Use the API or upcoming UI to run model
            comparisons.
          </p>
        ) : (
          <ul className="space-y-2">
            {experiments.map((experiment) => (
              <li
                key={experiment.id}
                className="rounded-xl border border-border bg-surface px-4 py-3 text-sm"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-medium">{experiment.name}</p>
                  <span className="font-mono text-xs text-accent">
                    {experiment.status}
                  </span>
                </div>
                <p className="mt-1 text-xs text-muted">
                  {experiment.task_type} · target: {experiment.target_column}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
