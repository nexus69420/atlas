"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, authApi } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await authApi.register({
        email,
        password,
        full_name: fullName || undefined,
      });
      await authApi.login({ email, password });
      router.push("/projects");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center px-6">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(45,212,191,0.12),transparent_45%)]"
      />
      <div className="relative w-full max-w-md rounded-2xl border border-border bg-surface p-8">
        <Link href="/" className="mb-8 inline-flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-border-strong text-xs text-accent">
            A
          </span>
          <span className="font-semibold">Atlas</span>
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight">Create account</h1>
        <p className="mt-2 text-sm text-muted">
          Start an evidence-driven ML workspace in minutes.
        </p>
        <form onSubmit={onSubmit} className="mt-8 space-y-4">
          <label className="block text-sm">
            <span className="mb-1.5 block text-muted">Full name</span>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full rounded-xl border border-border bg-background px-3 py-2.5 outline-none focus:border-accent/60"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1.5 block text-muted">Email</span>
            <input
              required
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-border bg-background px-3 py-2.5 outline-none focus:border-accent/60"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1.5 block text-muted">Password</span>
            <input
              required
              minLength={8}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-border bg-background px-3 py-2.5 outline-none focus:border-accent/60"
            />
          </label>
          {error ? <p className="text-sm text-danger">{error}</p> : null}
          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-border-strong bg-surface-2 px-4 py-2.5 text-sm font-medium hover:border-accent/40 disabled:opacity-60"
          >
            <span className="accent-dot" />
            {loading ? "Creating…" : "Create account"}
          </button>
        </form>
        <p className="mt-6 text-sm text-muted">
          Already have an account?{" "}
          <Link href="/login" className="text-accent hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
