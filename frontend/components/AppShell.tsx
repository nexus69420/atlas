"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { authApi, User } from "@/lib/api";

const NAV = [
  { href: "/projects", label: "Projects" },
];

export function AppSidebar({ user }: { user: User | null }) {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <aside className="flex w-full flex-col border-b border-border bg-surface md:min-h-screen md:w-60 md:border-b-0 md:border-r">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <Link href="/projects" className="flex items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-border-strong text-xs text-accent">
            A
          </span>
          <span className="text-sm font-semibold">Atlas</span>
        </Link>
      </div>
      <p className="px-5 pb-2 text-[11px] uppercase tracking-[0.14em] text-muted">
        Workspace
      </p>
      <nav className="flex gap-1 px-3 pb-4 md:flex-col">
        {NAV.map((item) => {
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-lg px-3 py-2 text-sm transition-colors ${
                active
                  ? "bg-surface-2 text-foreground"
                  : "text-muted hover:bg-surface-2/60 hover:text-foreground"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto border-t border-border px-5 py-4">
        <p className="truncate text-sm">{user?.full_name || user?.email || "…"}</p>
        <button
          type="button"
          className="mt-2 text-xs text-muted hover:text-foreground"
          onClick={() => {
            authApi.logout();
            router.push("/login");
          }}
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}

export function useRequireAuth() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    authApi
      .me()
      .then((me) => {
        if (!cancelled) setUser(me);
      })
      .catch(() => {
        authApi.logout();
        router.replace("/login");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  return { user, loading };
}
