"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { ApiError, Project, projectsApi } from "@/lib/api";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  async function load() {
    setLoading(true);
    try {
      setProjects(await projectsApi.list());
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    setCreating(true);
    setError(null);
    try {
      await projectsApi.create({
        name,
        description: description || undefined,
      });
      setName("");
      setDescription("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not create project");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Projects</h1>
          <p className="mt-1 text-sm text-muted">
            Each project owns datasets, experiments, and deployments.
          </p>
        </div>
      </div>

      <form
        onSubmit={onCreate}
        className="mb-8 grid gap-3 rounded-2xl border border-border bg-surface p-5 sm:grid-cols-[1fr_1fr_auto]"
      >
        <input
          required
          placeholder="Project name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="rounded-xl border border-border bg-background px-3 py-2.5 text-sm outline-none focus:border-accent/60"
        />
        <input
          placeholder="Short description (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="rounded-xl border border-border bg-background px-3 py-2.5 text-sm outline-none focus:border-accent/60"
        />
        <button
          type="submit"
          disabled={creating}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-border-strong bg-surface-2 px-4 py-2.5 text-sm font-medium hover:border-accent/40 disabled:opacity-60"
        >
          <span className="accent-dot" />
          {creating ? "Creating…" : "New project"}
        </button>
      </form>

      {error ? <p className="mb-4 text-sm text-danger">{error}</p> : null}

      {loading ? (
        <p className="text-sm text-muted">Loading projects…</p>
      ) : projects.length === 0 ? (
        <p className="rounded-2xl border border-dashed border-border px-5 py-10 text-center text-sm text-muted">
          No projects yet. Create one to upload datasets and run experiments.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Link
              key={project.id}
              href={`/projects/${project.id}`}
              className="rounded-2xl border border-border bg-surface p-5 transition-colors hover:border-border-strong"
            >
              <div className="mb-3 flex items-center justify-between">
                <span className="text-xs text-muted">Project</span>
                <span className="accent-dot !h-1.5 !w-1.5" />
              </div>
              <h2 className="text-base font-medium">{project.name}</h2>
              <p className="mt-2 line-clamp-2 text-sm text-muted">
                {project.description || "No description"}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
