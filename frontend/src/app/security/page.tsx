import type { Metadata } from "next";
import Link from "next/link";

import { DocumentFrame } from "@/components/site-chrome";

export const metadata: Metadata = {
  title: "Security Architecture: Boundary Assurance",
  description: "Security boundaries, secret quarantine rules, and vulnerability reporting for FieldWeaver.",
};

const scorecardItems = [
  {
    label: "INTERFACE BINDING",
    value: "127.0.0.1 (Loopback)",
    desc: "FastAPI and Next.js bind to local loopback; no external network ports exposed by default.",
    badge: "BOUND"
  },
  {
    label: "SECRET QUARANTINE",
    value: "Backend Environment",
    desc: "Use a server environment key or enter a provider key for the current page session.",
    badge: "SERVER SIDE"
  },
  {
    label: "PROMPT BOUNDARY",
    value: "Strict Schemas",
    desc: "Mission and agent responses are validated; model output is not executed as code.",
    badge: "VALIDATED"
  },
  {
    label: "SAFETY VALIDATION",
    value: "Independent Checks",
    desc: "The simulator checks separation, clearance, boundaries, speed, and finite state.",
    badge: "SIMULATOR ONLY"
  }
];

export default function SecurityPage() {
  return (
    <DocumentFrame active="security">
      <main className="document-main policy-main">
        <section className="document-hero policy-hero">
          <p className="eyebrow">
            <span className="eyebrow-mark" aria-hidden="true" />
            SECURITY ARCHITECTURE: BOUNDARY ASSURANCE
          </p>
          <h1>
            Keep the control<br />
            <em>surface local.</em>
          </h1>
          <p className="document-lede">
            The current API is built for local development and research simulation.
            Review these boundaries before exposing an instance to another network.
          </p>
          <div className="doc-hero-meta">
            <span>BOUNDARY ASSURANCE V1.0</span>
            <span>LOCAL DEVELOPMENT</span>
            <span>UPDATED NOV 4, 2026</span>
          </div>
        </section>

        {/* Security Posture Scorecard */}
        <section className="security-scorecard-section" aria-label="Security posture scorecard">
          <div className="scorecard-header">
            <span className="scorecard-kicker">POSTURE SCORECARD</span>
            <h2 className="scorecard-title">Enforced Defense-in-Depth Boundaries</h2>
          </div>
          <div className="scorecard-grid">
            {scorecardItems.map((item) => (
              <div key={item.label} className="scorecard-card">
                <div className="scorecard-card-top">
                  <span className="scorecard-label">{item.label}</span>
                  <span className="scorecard-badge">{item.badge}</span>
                </div>
                <div className="scorecard-value">{item.value}</div>
                <p className="scorecard-desc">{item.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <div className="policy-layout">
          <aside className="security-status-card" aria-label="Current security posture summary">
            <span className="status-emblem" aria-hidden="true">+</span>
            <p className="doc-kicker">CURRENT POSTURE</p>
            <strong>Local use only</strong>
            <p>
              The API has no authentication or rate limiting. CORS is an origin boundary,
              not an access control system.
            </p>
          </aside>

          <article className="policy-article">
            <section className="docs-section">
              <p className="doc-kicker">01: SERVICE BOUNDARY</p>
              <h2>Do not expose the development API as-is.</h2>
              <p>
                The documented launch command binds the backend and frontend to loopback.
                The FastAPI service has no user authentication, authorization, or rate limiting.
                Its CORS allowlist helps browsers enforce origin rules, but does not prevent direct
                HTTP clients from reaching a network-accessible API.
              </p>
              <p>
                For any shared or hosted deployment, add an authenticated reverse proxy, TLS,
                network restrictions, request limits, and a reviewed CORS configuration. Keep the
                API unreachable from untrusted networks until those controls are in place.
              </p>
            </section>

            <section className="docs-section">
              <p className="doc-kicker">02: SECRET HYGIENE</p>
              <h2>Handle provider credentials carefully.</h2>
              <ul className="limit-list">
                <li>Store the key in <code>BASETEN_API_KEY</code> in the backend environment or local root <code>.env</code>.</li>
                <li>The root <code>.env</code> is ignored by Git. Keep the placeholder-only <code>.env.example</code> free of real credentials.</li>
                <li>Keys entered in the app are held in page memory and sent to the backend for live requests. Close or clear the page to remove them; use HTTPS except on the local computer.</li>
                <li>Never use <code>NEXT_PUBLIC_*</code> for provider secrets or put real credentials in source, prompts, logs, screenshots, or test fixtures.</li>
                <li>Use a restricted local account for the key, rotate it if it is exposed, and review provider account access.</li>
              </ul>
            </section>

            <section className="docs-section">
              <p className="doc-kicker">03: MODEL AND MOTION BOUNDARIES</p>
              <h2>Generated output is treated as untrusted input.</h2>
              <p>
                Every mission and agent response is parsed and validated server-side. The model cannot
                provide executable code, arbitrary routes, actuator values, or safety-limit changes.
                Deterministic motion proposals pass through an independent validator, which can stop or reject an unsafe transition.
              </p>
              <p>
                These protections apply to the simulator implementation only. They are not a certification
                or guarantee for physical robots, real sensors, actuators, or changed dynamics.
              </p>
            </section>

            <section className="docs-section">
              <p className="doc-kicker">04: REPORT A VULNERABILITY</p>
              <h2>Share details privately.</h2>
              <p>
                Please do not include API keys, private mission data, or exploit details in a public issue.
                Use GitHub&apos;s private vulnerability reporting flow for the repository if it is enabled.
                If it is unavailable, contact the repository maintainers privately before publishing a report.
                No response-time commitment is currently stated.
              </p>
              <a
                className="doc-action"
                href="https://github.com/Erebuzzz/fieldweaver/security/advisories/new"
                target="_blank"
                rel="noreferrer"
              >
                Open private vulnerability report <span aria-hidden="true">↗</span>
              </a>
            </section>

            <section className="docs-section">
              <p className="doc-kicker">05: DEPENDENCIES AND OPERATIONS</p>
              <h2>Keep the local stack current.</h2>
              <p>
                Install from the committed Python and npm lock/configuration files. Review dependency updates
                before deployment. Protect API logs and generated evaluation reports because they may contain
                request context or trajectory data. The latest run is stored in process memory and is cleared
                when the API process restarts.
              </p>
              <div className="docs-policy-links">
                <Link href="/privacy">Privacy policy <span aria-hidden="true">↗</span></Link>
                <Link href="/docs#limits">Known limits <span aria-hidden="true">↗</span></Link>
              </div>
            </section>

            <p className="policy-version">
              Security guidance reviewed November 4, 2026. Reassess before any non-local deployment.
            </p>
          </article>
        </div>
      </main>
    </DocumentFrame>
  );
}
