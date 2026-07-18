import Link from "next/link";

type CtaProps = {
  href: string;
  children: React.ReactNode;
  variant?: "primary" | "ghost";
  className?: string;
};

export function CtaButton({
  href,
  children,
  variant = "primary",
  className = "",
}: CtaProps) {
  const base =
    "inline-flex items-center justify-center gap-2.5 rounded-xl px-5 py-2.5 text-sm font-medium transition-colors";
  const styles =
    variant === "primary"
      ? "border border-border-strong bg-surface-2 text-foreground hover:border-accent/50 hover:bg-surface"
      : "text-muted hover:text-foreground";

  return (
    <Link href={href} className={`${base} ${styles} ${className}`}>
      {variant === "primary" ? <span className="accent-dot" aria-hidden /> : null}
      {children}
    </Link>
  );
}

export function SiteHeader() {
  return (
    <header className="relative z-20 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
      <Link href="/" className="flex items-center gap-2.5">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-border-strong bg-surface text-xs font-semibold text-accent">
          A
        </span>
        <span className="text-[15px] font-semibold tracking-tight">Atlas</span>
      </Link>
      <nav className="hidden items-center gap-8 text-sm text-muted md:flex">
        <a href="#product" className="hover:text-foreground">
          Product
        </a>
        <a href="#workflow" className="hover:text-foreground">
          Workflow
        </a>
        <Link href="/login" className="hover:text-foreground">
          Sign in
        </Link>
      </nav>
      <CtaButton href="/register">Start building</CtaButton>
    </header>
  );
}
