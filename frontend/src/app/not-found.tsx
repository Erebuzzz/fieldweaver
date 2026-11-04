import Link from "next/link";
import { SiteFooter, SiteHeader } from "@/components/site-chrome";

export const metadata = {
  title: "Route not found",
  description: "The requested FieldWeaver route could not be resolved.",
};

export default function NotFound() {
  return (
    <div className="document-shell">
      <SiteHeader active="not-found" />
      <main className="not-found-main" id="main-content">
        <section className="not-found-panel" aria-labelledby="not-found-title">
          <div className="not-found-copy">
            <p className="doc-kicker">
              <span className="eyebrow-mark" aria-hidden="true" />
              FIELDWEAVER: ROUTE RECOVERY
            </p>
            <div className="not-found-code-row">
              <span className="not-found-code">404</span>
              <span className="not-found-code-label">ROUTE<br />NOT FOUND</span>
            </div>
            <h1 id="not-found-title">This vector is outside the field map.</h1>
            <p className="not-found-description">
              The requested page is not in FieldWeaver’s map. Return to the workbench or open the
              field guide to find your way around.
            </p>

            <div className="telemetry-diagnostics-card" aria-label="Recovery guidance">
              <div className="diag-header">
                <span className="diag-title">RECOVERY GUIDE</span>
                <span className="diag-status-pill">HTTP 404</span>
              </div>
              <div className="diag-grid">
                <div><span>REQUEST</span><strong>Page unavailable</strong></div>
                <div><span>RETURN</span><strong>Mission workbench</strong></div>
                <div><span>REFERENCE</span><strong>Field guide</strong></div>
              </div>
            </div>

            <nav className="not-found-actions" aria-label="Route recovery actions">
              <Link className="not-found-primary" href="/">
                Return to Mission Control
                <span aria-hidden="true">→</span>
              </Link>
              <Link className="not-found-secondary" href="/docs">
                Architecture Docs
              </Link>
              <Link className="not-found-secondary" href="/evaluation">
                Evaluation Benchmark
              </Link>
            </nav>

            <div className="not-found-meta" aria-label="Page context">
              <span><i aria-hidden="true" />SIMULATION ONLY</span>
              <span>PAGE STATUS: 404</span>
            </div>
          </div>

          <div className="not-found-visual" aria-hidden="true">
            <div className="not-found-visual-header">
              <span>ILLUSTRATIVE ROUTE MAP</span>
              <span>NOT A LIVE SIMULATION</span>
            </div>

            <svg
              className="not-found-map"
              viewBox="0 0 520 340"
              fill="none"
              aria-hidden="true"
              focusable="false"
            >
              <defs>
                <pattern id="radar-grid" width="26" height="26" patternUnits="userSpaceOnUse">
                  <path d="M26 0H0V26" stroke="#38bdf8" strokeOpacity="0.08" />
                </pattern>
                <radialGradient id="radar-sweep" cx="100" cy="230" r="320" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#38bdf8" stopOpacity="0.16" />
                  <stop offset="0.6" stopColor="#38bdf8" stopOpacity="0.04" />
                  <stop offset="1" stopColor="#0b0f17" stopOpacity="0" />
                </radialGradient>
                <linearGradient id="return-vector-grad" x1="390" y1="110" x2="100" y2="230" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#f87171" stopOpacity="0.8" />
                  <stop offset="0.5" stopColor="#fbbf24" stopOpacity="0.7" />
                  <stop offset="1" stopColor="#38bdf8" stopOpacity="0.9" />
                </linearGradient>
              </defs>

              {/* Grid Background */}
              <rect x="10" y="10" width="500" height="320" rx="4" fill="#070c14" />
              <rect x="10" y="10" width="500" height="320" rx="4" fill="url(#radar-grid)" />
              <rect x="10" y="10" width="500" height="320" rx="4" fill="url(#radar-sweep)" />
              <rect x="10" y="10" width="500" height="320" rx="4" stroke="#1e293b" strokeWidth="1" />

              {/* Concentric Radar Range Rings radiating from home workbench */}
              <circle cx="100" cy="230" r="70" stroke="#38bdf8" strokeOpacity="0.22" strokeDasharray="3 4" />
              <circle cx="100" cy="230" r="140" stroke="#38bdf8" strokeOpacity="0.18" strokeDasharray="3 4" />
              <circle cx="100" cy="230" r="220" stroke="#38bdf8" strokeOpacity="0.14" strokeDasharray="4 6" />
              <circle cx="100" cy="230" r="310" stroke="#38bdf8" strokeOpacity="0.10" strokeDasharray="4 6" />

              {/* Axes Crosshair lines */}
              <line x1="10" y1="230" x2="510" y2="230" stroke="#38bdf8" strokeOpacity="0.12" />
              <line x1="100" y1="10" x2="100" y2="330" stroke="#38bdf8" strokeOpacity="0.12" />

              {/* Recovery Vector Path */}
              <path
                d="M390 110 Q260 140 100 230"
                stroke="url(#return-vector-grad)"
                strokeWidth="2"
                strokeDasharray="5 5"
              />

              {/* Lost Route Beacon at (390, 110) */}
              <circle cx="390" cy="110" r="22" stroke="#f87171" strokeOpacity="0.3" strokeWidth="1">
                <animate attributeName="r" values="14;28;14" dur="2.4s" repeatCount="indefinite" />
                <animate attributeName="stroke-opacity" values="0.6;0.1;0.6" dur="2.4s" repeatCount="indefinite" />
              </circle>
              <circle cx="390" cy="110" r="14" fill="#0b0f17" stroke="#f87171" strokeWidth="1.5" />
              <path d="M382 102l16 16m0-16-16 16" stroke="#f87171" strokeWidth="2" strokeLinecap="round" />
              <text x="340" y="80" fill="#f87171" fontSize="8" fontWeight="600" fontFamily="var(--mono)">
                404: ROUTE_UNMAPPED
              </text>
              <text x="360" y="93" fill="#94a3b8" fontSize="7" fontFamily="var(--mono)">
                VECTOR LOST
              </text>

              {/* Workbench destination marker */}
              <circle cx="100" cy="230" r="18" fill="#0b0f17" stroke="#38bdf8" strokeWidth="1.5" />
              <circle cx="100" cy="230" r="6" fill="#38bdf8" />
              <path d="M85 230h30m-15-15v30" stroke="#38bdf8" strokeWidth="1.5" strokeLinecap="round" />
              <text x="70" y="268" fill="#38bdf8" fontSize="8" fontWeight="600" fontFamily="var(--mono)">
                MISSION_WORKBENCH
              </text>

              {/* Illustration labels */}
              <text x="25" y="32" fill="#64748b" fontSize="8" fontFamily="var(--mono)">
                NOT TO SCALE
              </text>
              <text x="430" y="32" fill="#64748b" fontSize="8" fontFamily="var(--mono)">
                ROUTE RETURN
              </text>
            </svg>

            <div className="not-found-visual-footer">
              <span><i className="map-legend-known" />WORKBENCH</span>
              <span><i className="map-legend-missing" />MISSING ROUTE</span>
              <span><i style={{ background: "#fbbf24" }} />RETURN LINK</span>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
