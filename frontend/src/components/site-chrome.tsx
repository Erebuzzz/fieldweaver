import Link from "next/link";

type ActivePage = "workbench" | "docs" | "evaluation" | "privacy" | "security" | "license" | "not-found";
type BackendState = "connected" | "unavailable" | "connecting";

const navigation = [
  { href: "/", label: "Workbench", page: "workbench" },
  { href: "/docs", label: "Guide", page: "docs" },
  { href: "/evaluation", label: "Results", page: "evaluation" },
] as const;

function NavigationIcon({ page }: { page: ActivePage }) {
  const paths: Partial<Record<ActivePage, string>> = {
    workbench: "M3 12 12 3l9 9-9 9z M7 12h10M12 7v10",
    docs: "M4 5h6l2 2 2-2h6v14h-6l-2 2-2-2H4z M12 7v14",
    evaluation: "M4 19h16M5 16l4-5 4 2 6-8M16 5h3v3",
    privacy: "M5 10h14v10H5z M8 10V7a4 4 0 0 1 8 0v3 M12 14v3",
    security: "M12 3 20 6v5c0 5-3 8-8 10-5-2-8-5-8-10V6z M8 12l3 3 5-6",
  };
  return <svg className="navigation-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d={paths[page]} /></svg>;
}

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
            <path d="M5 11.5 16 5l11 6.5v9L16 27 5 20.5z" />
            <path d="M5 11.5 16 18l11-6.5M5 20.5 16 14l11 6.5M16 5v9m0 4v9" />
            <circle cx="16" cy="16" r="2.2" fill="currentColor" stroke="none" />
          </svg>
        </span>
        <span className="brand-name">FieldWeaver</span>
        <span className="brand-edition">SIMULATION STUDIO</span>
      </Link>

      <nav className="site-nav" aria-label="Main navigation">
        {navigation.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active === item.page ? "page" : undefined}
            className={active === item.page ? "site-nav-link is-active" : "site-nav-link"}
          >
            <NavigationIcon page={item.page} />
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
