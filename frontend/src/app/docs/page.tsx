import type { Metadata } from "next";

import { DocumentFrame } from "@/components/site-chrome";

export const metadata: Metadata = {
  title: "Field Guide",
  description: "A practical guide to FieldWeaver's mission compiler, simulator, safety layer, and API.",
};

const sections = [
  ["overview", "Overview"],
  ["workflow", "Run workflow"],
  ["safety", "Safety boundaries"],
  ["simulation", "Simulation model"],
  ["providers", "Provider modes"],
  ["api", "API reference"],
  ["evaluation", "Evaluation"],
  ["setup", "Local setup"],
  ["limits", "Known limits"],
] as const;

const diagram = [
  "flowchart LR",
  "  Operator -->|mission text| UI[Next.js workbench]",
  "  UI -->|compile request| API[FastAPI]",
  "  API --> Compiler[Mission compiler]",
  "  Compiler --> Schema[Strict MissionSpec validation]",
  "  Schema -->|operator review| UI",
  "  UI -->|approved spec and seed| API",
  "  API --> Runner[Bounded run service]",
  "  Runner --> Sim[Deterministic simulator]",
  "  Sim --> Safety[Independent safety filter]",
  "  Safety --> Sim",
  "  Runner -->|event checkpoint only| Agent[Bounded agent decision]",
  "  Sim --> Eval[Evaluator with hidden truth]",
  "  Eval --> UI",
].join("\n");

const powershellSetup = [
  "py -3 -m venv backend/.venv",
  '.\\backend\\.venv\\Scripts\\python.exe -m pip install -e "backend[dev]"',
  "npm ci --prefix frontend",
  "Copy-Item .env.example .env",
].join("\n");

const powershellStart = [
  ".\\backend\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000",
  "npm --prefix frontend run dev -- --hostname 127.0.0.1",
].join("\n");

export default function DocsPage() {
  return (
    <DocumentFrame active="docs">
      <main className="document-main docs-main">
        <section className="document-hero docs-hero">
          <p className="eyebrow"><span className="eyebrow-mark" aria-hidden="true" />FIELD GUIDE / 01</p>
          <h1>From mission text<br /><em>to a measured run.</em></h1>
          <p className="document-lede">
            Learn how FieldWeaver turns operator intent into a bounded specification,
            runs a seeded swarm simulation, and checks every motion independently.
          </p>
          <div className="doc-hero-meta">
            <span>SIMULATION ONLY</span><span>MISSION SPEC / 1.0</span><span>LAST REVIEWED OCT 30, 2026</span>
          </div>
        </section>

        <div className="docs-layout">
          <aside className="docs-sidebar" aria-label="Guide sections">
            <p>IN THIS GUIDE</p>
            <nav>
              {sections.map(([id, label], index) => (
                <a key={id} href={`#${id}`}><i>{String(index + 1).padStart(2, "0")}</i>{label}</a>
              ))}
            </nav>
            <div className="sidebar-policy-card">
              <span className="sidebar-shield" aria-hidden="true">+</span>
              <strong>Before using live mode</strong>
              <p>Review where mission text and event summaries are sent.</p>
              <a href="/privacy">Read privacy notes <span aria-hidden="true">↗</span></a>
            </div>
          </aside>

          <article className="docs-article">
            <section className="docs-section" id="overview">
              <p className="doc-kicker">00 / THE PROJECT</p>
              <h2>A small, inspectable robotics stack.</h2>
              <p>
                FieldWeaver compiles a natural-language request into a strict,
                versioned <code>MissionSpec</code>. You review and approve that spec
                before the backend starts a deterministic 2D simulation. The model
                may propose only bounded mission fields or a known agent action.
                The simulator and safety filter keep final authority over motion.
              </p>
              <div className="doc-callout">
                <span className="callout-mark" aria-hidden="true">i</span>
                <p><strong>Simulation software.</strong> The point-robot model is not
                  a hardware controller, and the geometric safety checks are not a
                  formal proof for real-world dynamics.</p>
              </div>
            </section>

            <section className="docs-section" id="workflow">
              <p className="doc-kicker">01 / RUN WORKFLOW</p>
              <h2>Four steps, with a human review gate.</h2>
              <p>Each transition has a clear input and an observable result.</p>
              <div className="flow-map" aria-label="Mission text flows through compile, approval, simulation, and evaluation">
                <article className="flow-node"><i>01</i><span>OPERATOR</span><strong>Describe</strong><p>Write the search objective and choose a built-in arena.</p></article>
                <span className="flow-arrow" aria-hidden="true">→</span>
                <article className="flow-node"><i>02</i><span>COMPILER</span><strong>Validate</strong><p>Build a bounded spec and show assumptions or questions.</p></article>
                <span className="flow-arrow" aria-hidden="true">→</span>
                <article className="flow-node"><i>03</i><span>OPERATOR</span><strong>Approve</strong><p>Review the spec, then explicitly authorize the run.</p></article>
                <span className="flow-arrow" aria-hidden="true">→</span>
                <article className="flow-node"><i>04</i><span>SIMULATOR</span><strong>Measure</strong><p>Run a seeded trajectory and report calculated metrics.</p></article>
              </div>
              <details className="mermaid-source">
                <summary>View the system diagram source</summary>
                <pre><code>{diagram}</code></pre>
              </details>
            </section>

            <section className="docs-section" id="safety">
              <p className="doc-kicker">02 / SAFETY BOUNDARIES</p>
              <h2>The model suggests. The simulator decides.</h2>
              <div className="principle-grid">
                <article><span>01</span><h3>Strict schema</h3><p>Model output is parsed and checked against versioned Pydantic models. Unknown fields, unsupported actions, and out-of-range values are rejected.</p></article>
                <article><span>02</span><h3>Hard limits</h3><p>Deterministic speed, separation, clearance, boundary, duration, and call budgets cannot be relaxed by model output.</p></article>
                <article><span>03</span><h3>Hidden source</h3><p>Ground-truth source coordinates stay in the evaluator. Compiler prompts and event observations contain no truth coordinate.</p></article>
                <article><span>04</span><h3>Independent filter</h3><p>Every proposed transition is checked before and after integration. Unsafe motion is scaled, stopped, or rejected.</p></article>
              </div>
              <p className="docs-footnote">The live model is not called during the per-tick controller loop. Agent calls happen only at bounded event checkpoints.</p>
            </section>

            <section className="docs-section" id="simulation">
              <p className="doc-kicker">03 / SIMULATION MODEL</p>
              <h2>Seeded motion in a bounded 2D arena.</h2>
              <div className="spec-table">
                <div><span>World</span><strong>10 × 10 metre arena, built-in geometry and events</strong></div>
                <div><span>Robots</span><strong>3 to 8 holonomic point robots</strong></div>
                <div><span>Time step</span><strong>Explicit Euler at 0.1 seconds</strong></div>
                <div><span>Field</span><strong>Seeded scalar quadratic field with optional noise</strong></div>
                <div><span>Estimator</span><strong>Regularized least-squares quadratic fit</strong></div>
                <div><span>Detours</span><strong>Per-robot A* routes to exact assigned ring slots</strong></div>
              </div>
              <p>
                The quadratic controller uses a fitted source estimate. The weighted-centroid
                baseline shares the same formation objective and safety checks, but uses a
                simpler estimator and no agent replans. Both are measured from their recorded
                trajectories.
              </p>
            </section>

            <section className="docs-section" id="providers">
              <p className="doc-kicker">04 / PROVIDER MODES</p>
              <h2>Offline works without a key.</h2>
              <div className="mode-grid">
                <article><span className="mode-dot mode-offline" /><h3>Offline mock</h3><p>Deterministic rules compile the supported subset and provide bounded event decisions. The UI labels these responses as mock.</p></article>
                <article><span className="mode-dot mode-live" /><h3>Baseten live</h3><p>When enabled, the backend sends a Chat Completions request using the configured server key and model. The key is never sent to the browser.</p></article>
              </div>
              <p className="docs-footnote">Automatic mode uses live inference when the backend key is configured. Forcing live mode without a key returns an explicit error instead of switching to mock.</p>
            </section>

            <section className="docs-section" id="api">
              <p className="doc-kicker">05 / API REFERENCE</p>
              <h2>Small HTTP surface, explicit contracts.</h2>
              <div className="api-table" role="table" aria-label="FieldWeaver API routes">
                <div className="api-row api-head" role="row"><span>METHOD</span><span>ROUTE</span><span>BEHAVIOR</span></div>
                <div className="api-row" role="row"><code>GET</code><code>/api/health</code><span>Provider status, version, and safety envelope.</span></div>
                <div className="api-row" role="row"><code>GET</code><code>/api/scenarios</code><span>Public arena metadata without source truth.</span></div>
                <div className="api-row" role="row"><code>POST</code><code>/api/missions/compile</code><span>Mission text to validated spec and review notes.</span></div>
                <div className="api-row" role="row"><code>POST</code><code>/api/simulations/run</code><span>Approved spec, scenario, seed, and controller to trajectory.</span></div>
                <div className="api-row" role="row"><code>GET</code><code>/api/evaluations/latest</code><span>Latest evaluation held in the current API process.</span></div>
                <div className="api-row" role="row"><code>POST</code><code>/api/scenes/segment</code><span>Disabled with 503 until a supported perception endpoint is verified.</span></div>
              </div>
              <p className="docs-footnote">API errors include a stable code and request ID. OpenAPI is served by FastAPI at <code>/docs</code> on the backend host.</p>
            </section>

            <section className="docs-section" id="evaluation">
              <p className="doc-kicker">06 / EVALUATION</p>
              <h2>Keep every result, including failures.</h2>
              <p>The checked-in evaluation compares seven scenarios over shared seeds 42, 43, and 44. It is a small fixed sample, not a broad robustness claim.</p>
              <div className="evaluation-cards">
                <article><span>QUADRATIC ESTIMATOR</span><strong>10 / 21</strong><p>Successful runs</p><small>7 route infeasible · 4 timeout</small></article>
                <article><span>WEIGHTED-CENTROID</span><strong>0 / 21</strong><p>Successful runs</p><small>21 timeout</small></article>
                <article><span>DISTURBANCE RECOVERY</span><strong>3 / 3</strong><p>Seeded mock trials</p><small>One bounded replan per trial</small></article>
              </div>
              <p className="docs-footnote">These results were generated offline. No live inference latency is represented. See <a href="https://github.com/Erebuzzz/fieldweaver/blob/main/docs/EVALUATION_RESULTS.md" target="_blank" rel="noreferrer">the full evaluation record ↗</a>.</p>
            </section>

            <section className="docs-section" id="setup">
              <p className="doc-kicker">07 / LOCAL SETUP</p>
              <h2>Run the workbench on your machine.</h2>
              <p>Python 3.11+, Node.js 20.9+, and npm are required. From PowerShell at the repository root:</p>
              <pre className="code-block"><code>{powershellSetup}</code></pre>
              <p>Start each service in its own terminal:</p>
              <pre className="code-block"><code>{powershellStart}</code></pre>
              <p>The offline simulator runs with an empty <code>BASETEN_API_KEY</code>. Add the key only to the backend environment file if you want live inference. Never add it to a <code>NEXT_PUBLIC_*</code> variable.</p>
              <a className="doc-action" href="https://github.com/Erebuzzz/fieldweaver/blob/main/docs/API_SETUP.md" target="_blank" rel="noreferrer">Full setup and API guide <span aria-hidden="true">↗</span></a>
            </section>

            <section className="docs-section" id="limits">
              <p className="doc-kicker">08 / KNOWN LIMITS</p>
              <h2>What this build does not claim.</h2>
              <ul className="limit-list">
                <li>It does not control hardware or model complex robot dynamics.</li>
                <li>It does not support multiple sources, physical mapping, manipulation, or team splitting.</li>
                <li>Scene segmentation is disabled. Built-in scenarios are the supported path.</li>
                <li>The API has no authentication or rate limiting and is intended for local development.</li>
                <li>Evaluation uses three fixed seeds per scenario and does not establish general reliability.</li>
                <li>No live Baseten request was made for the recorded evaluation results.</li>
              </ul>
              <div className="docs-policy-links">
                <a href="/privacy">Privacy policy <span aria-hidden="true">↗</span></a>
                <a href="/security">Security notes <span aria-hidden="true">↗</span></a>
                <a href="/license">MIT license <span aria-hidden="true">↗</span></a>
              </div>
            </section>
          </article>
        </div>
      </main>
    </DocumentFrame>
  );
}
