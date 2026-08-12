"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  ApiError,
  Dataset,
  DatasetProfile,
  datasetsApi,
} from "@/lib/api";
import { Section, SeverityBadge } from "@/components/evidence";

export default function DatasetDetailPage() {
  const params = useParams<{ id: string; datasetId: string }>();
  const projectId = params.id;
  const datasetId = params.datasetId;

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [target, setTarget] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [profiling, setProfiling] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const d = await datasetsApi.get(projectId, datasetId);
        setDataset(d);
        try {
          setProfile(await datasetsApi.getProfile(projectId, datasetId));
        } catch (err) {
          if (!(err instanceof ApiError && err.status === 404)) throw err;
          setProfile(null);
        }
      } catch (err) {
        setError(err instanceof ApiError ? err.detail : "Failed to load dataset");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [projectId, datasetId]);

  async function onProfile(event: FormEvent) {
    event.preventDefault();
    setProfiling(true);
    setError(null);
    try {
      const result = await datasetsApi.profile(
        projectId,
        datasetId,
        target || undefined,
      );
      setProfile(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Profiling failed");
    } finally {
      setProfiling(false);
    }
  }

  if (loading) {
    return <p className="text-sm text-muted">Loading dataset intelligence…</p>;
  }

  const report = profile?.report;
  const warnings = report?.warnings || [];

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
          Dataset intelligence
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">
          {dataset?.name || "Dataset"}
        </h1>
        <p className="mt-1 text-sm text-muted">
          {dataset?.original_filename} · {dataset?.row_count} rows ·{" "}
          {dataset?.column_count} columns
        </p>
      </div>

      {error ? <p className="mb-4 text-sm text-danger">{error}</p> : null}

      <Section eyebrow="01" title="Generate Atlas Report">
        <form
          onSubmit={onProfile}
          className="flex flex-col gap-3 rounded-2xl border border-border bg-surface p-5 sm:flex-row sm:items-end"
        >
          <label className="block flex-1 text-sm">
            <span className="mb-1.5 block text-muted">
              Target column (optional — enables imbalance analysis)
            </span>
            <select
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="w-full rounded-xl border border-border bg-background px-3 py-2.5 outline-none focus:border-accent/60"
            >
              <option value="">No target</option>
              {(dataset?.column_schema || []).map((col) => (
                <option key={col.name} value={col.name}>
                  {col.name} ({col.dtype})
                </option>
              ))}
            </select>
          </label>
          <button
            type="submit"
            disabled={profiling}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-border-strong bg-surface-2 px-4 py-2.5 text-sm font-medium disabled:opacity-60"
          >
            <span className="accent-dot" />
            {profiling ? "Profiling…" : profile ? "Regenerate report" : "Run profiling"}
          </button>
        </form>
        <p className="mt-3 text-xs text-muted">
          Evidence first: Atlas surfaces missingness, correlations, and leakage
          risks before you train — not after.
        </p>
      </Section>

      {!profile ? (
        <p className="rounded-2xl border border-dashed border-border px-5 py-10 text-center text-sm text-muted">
          No report yet. Generate one to inspect data quality before experimenting.
        </p>
      ) : (
        <>
          <Section eyebrow="02" title="Summary">
            <div className="grid gap-3 sm:grid-cols-4">
              {[
                ["Rows", report?.summary?.row_count],
                ["Columns", report?.summary?.column_count],
                ["Duplicates", report?.summary?.duplicate_row_count],
                [
                  "Dup %",
                  report?.summary?.duplicate_row_pct != null
                    ? `${(report.summary.duplicate_row_pct * 100).toFixed(1)}%`
                    : "—",
                ],
              ].map(([label, value]) => (
                <div
                  key={String(label)}
                  className="rounded-xl border border-border bg-surface px-4 py-3"
                >
                  <p className="text-xs text-muted">{label}</p>
                  <p className="mt-1 font-mono text-lg tabular-nums">{value ?? "—"}</p>
                </div>
              ))}
            </div>
          </Section>

          <Section eyebrow="03" title="Warnings (with why)">
            {warnings.length === 0 ? (
              <p className="text-sm text-muted">No major warnings on this pass.</p>
            ) : (
              <ul className="space-y-2">
                {warnings.map((w, idx) => (
                  <li
                    key={`${w.code}-${w.column}-${idx}`}
                    className="rounded-xl border border-border bg-surface px-4 py-3"
                  >
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <SeverityBadge severity={w.severity} />
                      <span className="font-mono text-xs text-muted">{w.code}</span>
                      {w.column ? (
                        <span className="text-xs text-foreground">{w.column}</span>
                      ) : null}
                    </div>
                    <p className="text-sm leading-relaxed text-muted">{w.message}</p>
                  </li>
                ))}
              </ul>
            )}
          </Section>

          {report?.target_analysis ? (
            <Section eyebrow="04" title="Target analysis">
              <div className="rounded-2xl border border-border bg-surface p-5">
                <p className="text-sm">
                  Column{" "}
                  <span className="font-mono text-accent">
                    {report.target_analysis.column}
                  </span>{" "}
                  · {report.target_analysis.n_classes} classes
                  {report.target_analysis.imbalance_ratio != null
                    ? ` · imbalance ratio ${report.target_analysis.imbalance_ratio}`
                    : ""}
                </p>
                {report.target_analysis.warning ? (
                  <p className="mt-3 text-sm text-muted">
                    {report.target_analysis.warning}
                  </p>
                ) : null}
                <ul className="mt-4 grid gap-2 sm:grid-cols-3">
                  {report.target_analysis.class_counts.map((c) => (
                    <li
                      key={c.value}
                      className="rounded-lg border border-border bg-background/50 px-3 py-2 font-mono text-xs"
                    >
                      {c.value}: {c.count}
                    </li>
                  ))}
                </ul>
              </div>
            </Section>
          ) : null}

          <Section eyebrow="05" title="Columns">
            <div className="overflow-x-auto rounded-2xl border border-border">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-surface text-xs text-muted">
                  <tr>
                    <th className="px-4 py-3 font-medium">Name</th>
                    <th className="px-4 py-3 font-medium">Inferred</th>
                    <th className="px-4 py-3 font-medium">Missing %</th>
                    <th className="px-4 py-3 font-medium">Unique</th>
                  </tr>
                </thead>
                <tbody>
                  {(report?.columns || []).map((col) => (
                    <tr key={col.name} className="border-t border-border">
                      <td className="px-4 py-3 font-mono text-xs">{col.name}</td>
                      <td className="px-4 py-3 text-muted">{col.inferred_type}</td>
                      <td className="px-4 py-3 font-mono text-xs">
                        {(col.missing_pct * 100).toFixed(1)}%
                      </td>
                      <td className="px-4 py-3 font-mono text-xs">
                        {col.unique_count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>

          {(report?.correlations?.pairs?.length || 0) > 0 ? (
            <Section eyebrow="06" title="Strong correlations">
              <ul className="space-y-2">
                {report!.correlations!.pairs.map((pair) => (
                  <li
                    key={`${pair.column_a}-${pair.column_b}`}
                    className="rounded-xl border border-border bg-surface px-4 py-3 text-sm"
                  >
                    <p className="font-mono text-xs text-accent">
                      {pair.column_a} ↔ {pair.column_b} · r={pair.coefficient}
                    </p>
                    <p className="mt-2 text-muted">{pair.note}</p>
                  </li>
                ))}
              </ul>
            </Section>
          ) : null}

          <div className="rounded-2xl border border-border bg-surface p-5">
            <p className="text-sm text-muted">
              Next engineering step: run a comparable experiment on this dataset.
            </p>
            <Link
              href={`/projects/${projectId}`}
              className="mt-3 inline-flex text-sm text-accent hover:underline"
            >
              Back to project → run experiment
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
