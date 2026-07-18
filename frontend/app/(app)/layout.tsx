"use client";

import { AppSidebar, useRequireAuth } from "@/components/AppShell";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useRequireAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted">
        Loading workspace…
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <AppSidebar user={user} />
      <main className="flex-1 bg-background px-5 py-6 md:px-8 md:py-8">
        {children}
      </main>
    </div>
  );
}
