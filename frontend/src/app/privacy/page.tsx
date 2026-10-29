import type { Metadata } from "next";

import { DocumentFrame } from "@/components/site-chrome";

export const metadata: Metadata = {
  title: "Privacy",
  description: "What a local FieldWeaver installation processes and when it sends data to Baseten.",
};

export default function PrivacyPage() {
  return (
    <DocumentFrame active="privacy">
      <main className="document-main policy-main">
        <section className="document-hero policy-hero">
          <p className="eyebrow"><span className="eyebrow-mark" aria-hidden="true" />DATA HANDLING / 01</p>
          <h1>Know where mission<br /><em>data goes.</em></h1>
          <p className="document-lede">FieldWeaver is self-hosted software. The operator running your instance controls its API, logs, environment, and any live model account.</p>
          <div className="doc-hero-meta"><span>NO CENTRAL FIELDWEAVER SERVICE</span><span>UPDATED OCT 30, 2026</span></div>
        </section>

        <div className="policy-layout">
          <aside className="policy-summary">
            <p className="doc-kicker">AT A GLANCE</p>
            <div><i>01</i><span>Requests go to the local API by default.</span></div>
            <div><i>02</i><span>Live mode sends prompt or event data to Baseten.</span></div>
            <div><i>03</i><span>The latest run is held in API process memory.</span></div>
            <div><i>04</i><span>There is no account or central FieldWeaver database.</span></div>
          </aside>

          <article className="policy-article">
            <section className="docs-section">
              <p className="doc-kicker">01 / SCOPE</p>
              <h2>A policy for local installations.</h2>
              <p>This notice describes the current FieldWeaver source code when you run it yourself. The project maintainers do not operate a hosted FieldWeaver service or receive your mission data. If someone else hosts an instance for you, that operator&apos;s practices also apply.</p>
              <p>The application is simulation software. It is not designed to receive personal, confidential, or safety-critical information.</p>
            </section>

            <section className="docs-section">
              <p className="doc-kicker">02 / LOCAL PROCESSING</p>
              <h2>What the application handles.</h2>
              <ul className="limit-list">
                <li>The browser sends mission text, selected scenario, mode choices, and run seed to the configured FieldWeaver API.</li>
                <li>The API returns a validated mission specification, simulation frames, metrics, and event trace to the browser.</li>
                <li>The backend keeps the latest run in memory for <code>/api/evaluations/latest</code>. Restarting the API clears that in-process value.</li>
                <li>The evaluation script can write a report under the local ignored <code>artifacts/</code> folder.</li>
                <li>Normal backend request logs include method, route path, status, duration, and request ID. Unexpected exceptions include a stack trace. Protect local logs and generated reports as you would other project data.</li>
              </ul>
            </section>

            <section className="docs-section">
              <p className="doc-kicker">03 / LIVE INFERENCE</p>
              <h2>Live mode sends data to Baseten.</h2>
              <p>When the compiler or agent is set to live, or to automatic mode while a backend key is configured, the backend calls the Baseten Chat Completions endpoint. Mission compilation sends the mission text and a public summary of the selected scenario. Event-driven agent calls send a bounded observation summary, such as the current estimate, team centroid, safety state, and allowed action list. The backend API key is not sent to the browser.</p>
              <div className="doc-callout">
                <span className="callout-mark" aria-hidden="true">!</span>
                <p><strong>Ground truth stays hidden.</strong> The source&apos;s true coordinates are not included in compiler requests or agent observations. Evaluation data may be returned to the browser after a simulation run.</p>
              </div>
              <p>Baseten&apos;s published security practices currently describe Zero Data Retention for its Model APIs inputs and outputs. The applicable service, configuration, account agreement, and current provider terms govern a real request. FieldWeaver does not configure or guarantee provider retention on your behalf.</p>
              <div className="external-policy-links">
                <a href="https://www.baseten.co/security-practices/" target="_blank" rel="noreferrer">Baseten Security Practices <span aria-hidden="true">↗</span></a>
                <a href="https://www.baseten.co/privacy-policy/" target="_blank" rel="noreferrer">Baseten Privacy Policy <span aria-hidden="true">↗</span></a>
                <a href="https://www.baseten.co/data-request-policy/" target="_blank" rel="noreferrer">Baseten Data Request Policy <span aria-hidden="true">↗</span></a>
              </div>
            </section>

            <section className="docs-section">
              <p className="doc-kicker">04 / BROWSER STORAGE</p>
              <h2>No app analytics or saved browser profile.</h2>
              <p>The current frontend source does not set application cookies, use browser local storage, or load an analytics tracker. Browser requests go to the configured API origin. The browser and hosting platform may still create their own technical logs outside this project.</p>
            </section>

            <section className="docs-section">
              <p className="doc-kicker">05 / YOUR CHOICES</p>
              <h2>Keep control of your instance.</h2>
              <ul className="limit-list">
                <li>Use Offline mock mode to avoid sending prompt and observation content to a model provider.</li>
                <li>Do not enter credentials, personal data, or confidential material into mission text.</li>
                <li>Keep the API on loopback unless you have secured the deployment and its network path.</li>
                <li>Review and remove local logs and evaluation artifacts according to your own retention needs.</li>
              </ul>
              <p>For a locally operated instance, direct access or deletion requests to that instance&apos;s operator. The project itself has no central user account or data store to search.</p>
            </section>

            <p className="policy-version">Effective for the source reviewed October 30, 2026. Revisit this policy if storage, telemetry, hosting, or provider integrations change.</p>
          </article>
        </div>
      </main>
    </DocumentFrame>
  );
}
