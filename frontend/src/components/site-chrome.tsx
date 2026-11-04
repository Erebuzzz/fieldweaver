import Link from "next/link";

type ActivePage = "workbench" | "docs" | "evaluation" | "privacy" | "security" | "license" | "not-found";
type BackendState = "connected" | "unavailable" | "connecting";

const navigation = [
  { href: "/", label: "Workbench", page: "workbench" },
  { href: "/docs", label: "Guide", page: "docs" },
  { href: "/evaluation", label: "Results", page: "evaluation" },
  { href: "/privacy", label: "Privacy", page: "privacy" },
  { href: "/security", label: "Security", page: "security" },
] as const;

export function SiteHeader({
  active,
  backend,
  provider,
}: {
  active: ActivePage;
  backend?: BackendState;
  provider?: "configured" | "offline" | null;
}) {
  const backendLabel =
    backend === "connected"
      ? "API connected"
      : backend === "unavailable"
        ? "API unavailable"
        : "Connecting";

  return (
    <header className="site-header">
      <Link className="brand" href="/" aria-label="FieldWeaver home">
        <span className="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none">
            <circle cx="16" cy="16" r="10.5" />
            <circle cx="16" cy="16" r="2.6" />
            <path d="M16 1.5v6M16 24.5v6M1.5 16h6M24.5 16h6M5.75 5.75l4.4 4.4m11.7 11.7 4.4 4.4m0-20.5-4.4 4.4m-11.7 11.7-4.4 4.4" />
          </svg>
        </span>
        <span className="brand-name">FieldWeaver</span>
        <span className="brand-edition">TACTICAL SIM 01</span>
      </Link>

      <nav className="site-nav" aria-label="Main navigation">
        {navigation.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active === item.page ? "page" : undefined}
            className={active === item.page ? "site-nav-link is-active" : "site-nav-link"}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="site-signals" aria-live="polite">
        {backend ? (
          <span className={`signal-pill api-${backend}`}>
            <i aria-hidden="true" />
            <span>{backendLabel}</span>
          </span>
        ) : (
          <span className="signal-pill local-pill">
            <i aria-hidden="true" />
            <span>Local simulation</span>
          </span>
        )}
        {provider ? (
          <span className={`provider-pill provider-${provider}`}>
            <span>{provider === "configured" ? "Baseten configured" : "Offline mock"}</span>
          </span>
        ) : null}
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="footer-meta">
        <span className="footer-telemetry">FIELDWEAVER · AEROSPACE MISSION CONTROL</span>
        <span className="footer-note">Simulation software only. Independent deterministic safety filter enforced.</span>
      </div>
      <nav className="footer-links" aria-label="Policy and project links">
        <Link href="/docs">Documentation</Link>
        <Link href="/evaluation">Evaluation</Link>
        <Link href="/privacy">Privacy</Link>
        <Link href="/security">Security</Link>
        <Link href="/license">MIT license</Link>
        <a href="https://github.com/Erebuzzz/fieldweaver" target="_blank" rel="noreferrer">
          Source <span aria-hidden="true">↗</span>
        </a>
      </nav>
    </footer>
  );
}

export function DocumentFrame({
  active,
  children,
}: {
  active: ActivePage;
  children: React.ReactNode;
}) {
  return (
    <div className="document-shell">
      <SiteHeader active={active} />
      {children}
      <SiteFooter />
    </div>
  );
}
