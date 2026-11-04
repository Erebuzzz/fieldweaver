import type { Metadata } from "next";
import Link from "next/link";

import { DocumentFrame } from "@/components/site-chrome";
import {
  SubsystemExplorer,
  LifecycleVisualizer,
  ApiConsole,
  SafetyBrowser,
} from "@/components/docs";
import { InteractiveGuide } from "@/components/docs/interactive-guide";

export const metadata: Metadata = {
  title: "Field Guide: System Architecture",
  description: "Interactive architecture hub for FieldWeaver's mission compiler, simulation core, safety filters, and API contracts.",
};

const sections = [
  ["overview", "Overview"],
  ["workflow", "Run workflow"],
  ["topology", "Subsystem topology"],
  ["lifecycle", "State machine"],
  ["safety", "Safety contracts"],
  ["simulation", "Simulation model"],
  ["providers", "Provider modes"],
  ["api", "API console"],
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

export default function DocsPage() {
  return (
    <DocumentFrame active="docs">
      <main className="document-main docs-main">
        <section className="document-hero docs-hero">
          <p className="eyebrow">
            <span className="eyebrow-mark" aria-hidden="true" />
            FIELD GUIDE: SYSTEM ARCHITECTURE
          </p>
          <h1>
            From mission text<br />
            <em>to a measured run.</em>
          </h1>
          <p className="document-lede">
            Learn how FieldWeaver turns operator intent into a bounded specification,
            runs a seeded swarm simulation, and checks every motion independently.
          </p>
          <div className="doc-hero-meta">
            <span>SIMULATION ONLY</span>
            <span>SPECIFICATION V1.0</span>
                <span>LOCAL WORKBENCH</span>
          </div>
        </section>

        <div className="docs-layout">
          <aside className="docs-sidebar" aria-label="Guide sections">
            <p>IN THIS GUIDE</p>
            <nav>
              {sections.map(([id, label], index) => (
                <a key={id} href={`#${id}`}>
                  <i>{String(index).padStart(2, "0")}</i>
                  {label}
                </a>
              ))}
            </nav>
            <div className="sidebar-policy-card">
              <span className="sidebar-shield" aria-hidden="true">+</span>
              <strong>Before using live mode</strong>
              <p>Review where mission text and event summaries are sent.</p>
              <Link href="/privacy">
                Read privacy notes <span aria-hidden="true">↗</span>
              </Link>
            </div>
          </aside>

          <article className="docs-article">
            <section className="docs-section" id="overview">
              <p className="doc-kicker">00: THE PROJECT</p>
              <h2>A small, inspectable robotics stack.</h2>
              <p>
                FieldWeaver compiles a natural language request into a strict,
                versioned <code>MissionSpec</code>. You review and approve that spec
                before the backend starts a deterministic 2D simulation. The model
                may propose only bounded mission fields or a known agent action.
                The simulator and safety filter keep final authority over motion.
              </p>
              <div className="doc-callout">
                <span className="callout-mark" aria-hidden="true">i</span>
                <p>
                  <strong>Simulation software.</strong> The point-robot model is not
                  a hardware controller, and the geometric safety checks are not a
                  formal proof for real-world dynamics.
                </p>
              </div>
            </section>

            <section className="docs-section" id="workflow">
              <p className="doc-kicker">01: RUN WORKFLOW</p>
              <h2>Four steps, with a human review gate.</h2>
              <p>Each transition has a clear input and an observable result.</p>
              <div className="flow-map" aria-label="Mission text flows through compile, approval, simulation, and evaluation">
                <article className="flow-node">
                  <i>01</i>
                  <span>OPERATOR</span>
                  <strong>Describe</strong>
                  <p>Write the search objective and choose a built-in arena.</p>
                </article>
                <span className="flow-arrow" aria-hidden="true">→</span>
                <article className="flow-node">
                  <i>02</i>
                  <span>COMPILER</span>
                  <strong>Validate</strong>
                  <p>Build a bounded spec and show assumptions or questions.</p>
                </article>
                <span className="flow-arrow" aria-hidden="true">→</span>
                <article className="flow-node">
                  <i>03</i>
                  <span>OPERATOR</span>
                  <strong>Approve</strong>
                  <p>Review the spec, then explicitly authorize the run.</p>
                </article>
                <span className="flow-arrow" aria-hidden="true">→</span>
                <article className="flow-node">
                  <i>04</i>
                  <span>SIMULATOR</span>
                  <strong>Measure</strong>
                  <p>Run a seeded trajectory and report calculated metrics.</p>
                </article>
              </div>
              <details className="mermaid-source">
                <summary>View the system diagram source</summary>
                <pre><code>{diagram}</code></pre>
              </details>
            </section>

            <section className="docs-section" id="topology">
              <p className="doc-kicker">02: SUBSYSTEM TOPOLOGY</p>
              <h2>Eight decoupled subsystems, strict boundaries.</h2>
              <p>
                Explore the components of the FieldWeaver architecture below. Click any node
                to inspect its inputs, outputs, deterministic invariants, and backend source files.
              </p>
              <SubsystemExplorer />
            </section>

            <section className="docs-section" id="lifecycle">
              <p className="doc-kicker">03: LIFECYCLE STATE MACHINE</p>
              <h2>Seven lifecycle states with guard transitions.</h2>
              <p>
                FieldWeaver transitions through deterministic lifecycle states from docked idle to nominal
                convergence or bounded abort. Scrub through each state below to inspect its trigger conditions
                and safety invariants.
              </p>
              <LifecycleVisualizer />
            </section>

            <section className="docs-section" id="safety">
              <p className="doc-kicker">04: SAFETY BOUNDARIES & CONTRACTS</p>
              <h2>The model suggests. The simulator decides.</h2>
              <div className="principle-grid">
                <article>
                  <span>01</span>
                  <h3>Strict schema</h3>
                  <p>Model output is parsed and checked against versioned Pydantic models. Unknown fields, unsupported actions, and out-of-range values are rejected.</p>
                </article>
                <article>
                  <span>02</span>
                  <h3>Hard limits</h3>
                  <p>Deterministic speed, separation, clearance, boundary, duration, and call budgets cannot be relaxed by model output.</p>
                </article>
                <article>
                  <span>03</span>
                  <h3>Hidden source</h3>
                  <p>Ground-truth source coordinates stay in the evaluator. Compiler prompts and event observations contain no truth coordinate.</p>
                </article>
                <article>
                  <span>04</span>
                  <h3>Independent filter</h3>
                  <p>Every proposed transition is checked before and after integration. Unsafe motion is scaled, stopped, or rejected.</p>
                </article>
              </div>
              <p className="docs-footnote">
                The live model is not called during the per-tick controller loop. Agent calls happen only at bounded event checkpoints.
              </p>
              <div style={{ marginTop: "24px" }}>
                <SafetyBrowser />
              </div>
            </section>

            <section className="docs-section" id="simulation">
              <p className="doc-kicker">05: SIMULATION MODEL</p>
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
              <p className="doc-kicker">06: PROVIDER MODES</p>
              <h2>Offline works without a key.</h2>
              <div className="mode-grid">
                <article>
                  <span className="mode-dot mode-offline" />
                  <h3>Offline mock</h3>
                  <p>Deterministic rules compile the supported subset and provide bounded event decisions. The UI labels these responses as mock.</p>
                </article>
                <article>
                  <span className="mode-dot mode-live" />
                  <h3>Live provider</h3>
                  <p>Use the server&apos;s Baseten key or enter a key for Baseten, Meta, or Fireworks in the workbench. Browser-entered keys are kept in page memory and sent to the backend for live requests.</p>
                </article>
              </div>
              <p className="docs-footnote">
                Automatic mode uses live inference when the backend key is configured. Forcing live mode without a key returns an explicit error instead of switching to mock.
              </p>
            </section>

            <section className="docs-section" id="api">
              <p className="doc-kicker">07: API CONSOLE & REFERENCE</p>
              <h2>Small HTTP surface, explicit contracts.</h2>
              <p>
                Send a read-only request to the running backend and inspect its actual response.
              </p>
              <ApiConsole />
            </section>

            <section className="docs-section" id="evaluation">
              <p className="doc-kicker">08: EVALUATION</p>
              <h2>Compare paired runs, including failures.</h2>
              <p>
                The reproducible snapshot covers seven scenarios over ten shared seeds. It reports controller
                outcomes, trajectory metrics, and seeded mock recovery without implying live model performance.
              </p>
              <Link className="doc-action" href="/evaluation">
                View the evaluation report <span aria-hidden="true">↗</span>
              </Link>
              <p className="docs-footnote">
                The report page reads the same checked-in JSON used by the evaluation script and offers the raw file for download.
              </p>
            </section>

            <section className="docs-section" id="setup">
              <p className="doc-kicker">09: LOCAL SETUP</p>
              <h2>Run the workbench on your machine.</h2>
              <p>Follow the setup steps and a guided offline run. Commands are for PowerShell on Windows.</p>
              <InteractiveGuide />
              <p>
                The offline simulator runs with an empty <code>BASETEN_API_KEY</code>. Add the key only to the backend
                environment file if you want the Baseten server default, or enter a provider key in the workbench. Never add a key to a <code>NEXT_PUBLIC_*</code> variable.
              </p>
              <a className="doc-action" href="https://github.com/Erebuzzz/fieldweaver/blob/main/docs/API_SETUP.md" target="_blank" rel="noreferrer">
                Full setup and API guide <span aria-hidden="true">↗</span>
              </a>
            </section>

            <section className="docs-section" id="limits">
              <p className="doc-kicker">10: KNOWN LIMITS</p>
              <h2>What this build does not claim.</h2>
              <ul className="limit-list">
                <li>It does not control hardware or model complex robot dynamics.</li>
                <li>It does not support multiple sources, physical mapping, manipulation, or team splitting.</li>
                <li>Scene segmentation is disabled. Built-in scenarios are the supported path.</li>
                <li>The hosted API has no user authentication. Its process-local request limit is not a persistent spending cap.</li>
                <li>Evaluation uses ten fixed seeds per scenario and does not establish general reliability.</li>
                <li>No live Baseten request was made for the recorded evaluation results.</li>
              </ul>
              <div className="docs-policy-links">
                <Link href="/privacy">Privacy policy <span aria-hidden="true">↗</span></Link>
                <Link href="/security">Security notes <span aria-hidden="true">↗</span></Link>
                <Link href="/license">MIT license <span aria-hidden="true">↗</span></Link>
              </div>
            </section>
          </article>
        </div>
      </main>
    </DocumentFrame>
  );
}
