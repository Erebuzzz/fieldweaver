import Link from "next/link";
import { SiteFooter, SiteHeader } from "@/components/site-chrome";

export const metadata = {
  title: "Route not found",
  description: "The requested FieldWeaver page could not be found.",
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
              FIELDWEAVER / ROUTE RECOVERY
            </p>
            <div className="not-found-code-row">
              <span className="not-found-code">404</span>
              <span className="not-found-code-label">ROUTE<br />NOT FOUND</span>
            </div>
            <h1 id="not-found-title">This path is outside the field map.</h1>
            <p className="not-found-description">
              FieldWeaver could not resolve this address. Return to the workbench to
              plan a mission, or open the field guide for project documentation.
            </p>
            <nav className="not-found-actions" aria-label="Suggested pages">
              <Link className="not-found-primary" href="/">
                Open workbench
                <span aria-hidden="true">→</span>
              </Link>
              <Link className="not-found-secondary" href="/docs">
                Read the field guide
              </Link>
            </nav>
            <div className="not-found-meta" aria-label="Application information">
              <span><i aria-hidden="true" />SIMULATION ONLY</span>
              <span>PAGE ROUTE / UNMAPPED</span>
            </div>
          </div>

          <div className="not-found-visual" aria-hidden="true">
            <div className="not-found-visual-header">
              <span>ARENA / ROUTE TRACE</span>
              <span>INDEX 00</span>
            </div>
            <svg
              className="not-found-map"
              viewBox="0 0 520 360"
              fill="none"
              aria-hidden="true"
              focusable="false"
            >
              <defs>
                <pattern id="field-grid" width="28" height="28" patternUnits="userSpaceOnUse">
                  <path d="M28 0H0V28" stroke="currentColor" strokeOpacity="0.11" />
                </pattern>
                <linearGradient id="route-gradient" x1="76" y1="273" x2="418" y2="119" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#9ED9A8" stopOpacity="0.8" />
                  <stop offset="1" stopColor="#E9A94F" stopOpacity="0.8" />
                </linearGradient>
              </defs>
              <rect x="10" y="10" width="500" height="340" rx="3" fill="url(#field-grid)" />
              <path d="M10 10H510V350H10z" stroke="currentColor" strokeOpacity="0.24" />
              <path d="M190 217c-4-59 45-105 103-105s104 46 104 103-46 104-104 104c-46 0-84-26-97-64" stroke="currentColor" strokeOpacity="0.23" strokeDasharray="3 8" />
              <path d="M76 273c43-18 65-45 109-56 46-12 63 24 111-11 39-29 66-30 122-87" stroke="url(#route-gradient)" strokeWidth="2" strokeDasharray="6 7" />
              <circle cx="190" cy="217" r="15" fill="#101819" stroke="#9ED9A8" strokeWidth="1.5" />
              <circle cx="190" cy="217" r="4" fill="#9ED9A8" />
              <circle cx="293" cy="215" r="4" fill="#E9A94F" />
              <circle cx="396" cy="215" r="4" fill="#E9A94F" />
              <circle cx="293" cy="112" r="4" fill="#E9A94F" />
              <circle cx="396" cy="112" r="4" fill="#E9A94F" />
              <path d="M407 108l18 18m0-18-18 18" stroke="#F18778" strokeWidth="2" strokeLinecap="round" />
              <circle cx="416" cy="117" r="16" stroke="#F18778" strokeOpacity="0.45" />
              <path d="M61 273h30m-15-15v30" stroke="#9ED9A8" strokeWidth="1.5" strokeLinecap="round" />
              <text x="52" y="311" fill="#A5B0AA">HOME</text>
              <text x="383" y="83" fill="#F18778">404 / NO ROUTE</text>
              <text x="30" y="39" fill="#76837E">NORTH / 01</text>
              <text x="419" y="330" fill="#76837E">10 M</text>
            </svg>
            <div className="not-found-visual-footer">
              <span><i className="map-legend-known" />KNOWN PAGES</span>
              <span><i className="map-legend-missing" />UNMAPPED ROUTE</span>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
