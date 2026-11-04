import type { Metadata } from "next";
import Link from "next/link";

import evaluationReport from "../../../public/evaluation-report.json";
import ablationReport from "../../../public/agent-off-ablation.json";
import { DocumentFrame } from "@/components/site-chrome";
import { EvaluationControllerView } from "@/components/evaluation-controller-view";

export const metadata: Metadata = {
  title: "Evaluation: Empirical Benchmark",
  description: "Paired, seeded controller results and trajectory metrics for FieldWeaver's simulation suite.",
};

const scenarioNames: Record<string, string> = {
  open_field: "Open field",
  noisy_open: "Noisy open field",
  restricted_corridor: "Restricted corridor",
  disturbed_corridor: "Disturbed corridor",
  near_boundary: "Near boundary",
  infeasible_enclosure: "Infeasible enclosure",
  far_source: "Far source",
};

const metricRows = [
  { key: "localization_error_m", label: "Localization error", unit: "m" },
  { key: "formation_error_m", label: "Formation error", unit: "m" },
  { key: "minimum_robot_separation_m", label: "Minimum separation", unit: "m" },
  { key: "minimum_obstacle_clearance_m", label: "Obstacle clearance", unit: "m" },
  { key: "path_length_total_m", label: "Total path length", unit: "m" },
  { key: "simulation_duration_s", label: "Simulation duration", unit: "s" },
  { key: "safety_intervention_count", label: "Safety interventions", unit: "count" },
  { key: "robot_collision_count", label: "Robot collisions", unit: "count" },
] as const;

type Run = (typeof evaluationReport.runs)[number];

function terminationSummary(rows: Run[]): string {
  const reasons = new Map<string, number>();
  for (const row of rows) {
    if (row.termination_reason === "nominal_convergence") continue;
    reasons.set(row.termination_reason, (reasons.get(row.termination_reason) ?? 0) + 1);
  }
  if (!reasons.size) return "No failures";
  return [...reasons.entries()]
    .map(([reason, count]) => `${count} ${reason.replaceAll("_", " ")}`)
    .join(" · ");
}

export default function EvaluationPage() {
  const quadratic = evaluationReport.controller_summary.quadratic;
  const baseline = evaluationReport.controller_summary.baseline;
  const seeds = evaluationReport.configuration.seeds;
  const scenarios = [...new Set(evaluationReport.runs.map((run) => run.scenario_id))];
  const nominal = evaluationReport.runs.filter((run) => run.controller === "quadratic" && ["open_field", "noisy_open", "restricted_corridor", "disturbed_corridor"].includes(run.scenario_id));
  const stress = evaluationReport.runs.filter((run) => run.controller === "quadratic" && ["near_boundary", "infeasible_enclosure", "far_source"].includes(run.scenario_id));
  const agentOffQuadratic = ablationReport.runs.filter((run) => run.controller === "quadratic");
  const agentOffBaseline = ablationReport.runs.filter((run) => run.controller === "baseline");

  return (
    <DocumentFrame active="evaluation">
      <main className="document-main evaluation-main">
        <section className="document-hero evaluation-hero">
          <p className="eyebrow">
            <span className="eyebrow-mark" aria-hidden="true" />
            EMPIRICAL BENCHMARK: PAIRED CONTROLLER RESULTS
          </p>
          <h1>
            Paired controller<br />
            <em>results.</em>
          </h1>
          <p className="document-lede">
            Seed-matched runs from the deterministic simulation suite. Every timeout and
            infeasible route stays in the totals without survivorship bias.
          </p>
          <div className="doc-hero-meta">
            <span>{evaluationReport.configuration.runs_per_controller} RUNS PER CONTROLLER</span>
            <span>{evaluationReport.configuration.scenario_count} SCENARIOS</span>
            <span>SEEDS {seeds[0]} TO {seeds[seeds.length - 1]}</span>
            <span>OFFLINE MOCK, NO LIVE INFERENCE</span>
          </div>
        </section>

        <div className="docs-layout evaluation-layout">
          <aside className="docs-sidebar" aria-label="Evaluation sections">
            <p>REPORT SECTIONS</p>
            <nav>
              <a href="#outcomes"><i>01</i>Task outcomes</a>
              <a href="#scenarios"><i>02</i>By scenario</a>
              <a href="#metrics"><i>03</i>Trajectory metrics</a>
              <a href="#agent"><i>04</i>Agent recovery</a>
              <a href="#limits"><i>05</i>Limits</a>
            </nav>
            <div className="sidebar-policy-card">
              <strong>Reproduce the report</strong>
              <p>Run the paired suite locally with the fixed scenario seeds.</p>
              <Link href="/docs#setup">
                Open setup guide <span aria-hidden="true">↗</span>
              </Link>
            </div>
          </aside>

          <article className="docs-article evaluation-article">
            <section className="docs-section" id="outcomes">
              <p className="doc-kicker">01: TASK OUTCOMES</p>
              <h2>{quadratic.success_count} of {quadratic.sample_count} quadratic runs converged.</h2>
              <p>
                The baseline completed {baseline.success_count} of {baseline.sample_count} runs
                under the same scenarios, seeds, mission limits, and safety filter. The quadratic
                policy uses a mock recovery agent; the baseline runs with the agent off, so this
                compares complete policies rather than isolated estimators.
              </p>
              <p>
                Across the four nominal scenarios, {nominal.filter((run) => run.success).length} of {nominal.length} quadratic trials converged.
                The three stress scenarios contributed {stress.filter((run) => run.success).length} of {stress.length} successes;
                their infeasible routes and short time budget remain failures in the total above.
              </p>
              <p>
                With the agent disabled for both controllers on those same four scenarios,
                the quadratic policy converged in {agentOffQuadratic.filter((run) => run.success).length} of {agentOffQuadratic.length} trials,
                and the weighted-centroid policy in {agentOffBaseline.filter((run) => run.success).length} of {agentOffBaseline.length}.
                This separate ablation helps show the recovery agent&apos;s contribution.
              </p>
              <div className="evaluation-kpis">
                <div>
                  <span>QUADRATIC ESTIMATOR</span>
                  <strong>{(quadratic.success_rate * 100).toFixed(1)}%</strong>
                  <p>{quadratic.success_count} of {quadratic.sample_count} successes</p>
                </div>
                <div>
                  <span>WEIGHTED-CENTROID BASELINE</span>
                  <strong>{(baseline.success_rate * 100).toFixed(1)}%</strong>
                  <p>{baseline.success_count} of {baseline.sample_count} successes</p>
                </div>
                <div>
                  <span>DISTURBANCE RECOVERY</span>
                  <strong>
                    {evaluationReport.agent_summary.disturbance_recoveries} of {evaluationReport.agent_summary.disturbance_trials}
                  </strong>
                  <p>Seeded mock recovery runs</p>
                </div>
              </div>
              <p className="docs-footnote">
                Quadratic terminations: {quadratic.termination_reasons.route_infeasible ?? 0} route
                infeasible, {quadratic.termination_reasons.timeout ?? 0} timeout. Baseline
                terminations: {baseline.termination_reasons.timeout ?? 0} timeout.
              </p>
            </section>

            <section className="docs-section" id="scenarios">
              <p className="doc-kicker">02: BY SCENARIO</p>
              <h2>Failures remain visible by case.</h2>
              <div className="evaluation-table-scroll" role="region" aria-label="Scenario results" tabIndex={0}>
                <table className="evaluation-table">
                  <caption className="sr-only">Paired success counts and termination reasons for each scenario</caption>
                  <thead>
                    <tr>
                      <th scope="col">Scenario</th>
                      <th scope="col">Quadratic Success</th>
                      <th scope="col">Failure Reasons</th>
                      <th scope="col">Baseline Success</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scenarios.map((scenarioId) => {
                      const quadraticRuns = evaluationReport.runs.filter(
                        (run) => run.scenario_id === scenarioId && run.controller === "quadratic",
                      );
                      const baselineRuns = evaluationReport.runs.filter(
                        (run) => run.scenario_id === scenarioId && run.controller === "baseline",
                      );
                      const quadraticSuccesses = quadraticRuns.filter((run) => run.success).length;
                      const baselineSuccesses = baselineRuns.filter((run) => run.success).length;
                      return (
                        <tr key={scenarioId}>
                          <th scope="row">{scenarioNames[scenarioId] ?? scenarioId}</th>
                          <td className="mono-num">{quadraticSuccesses} of {quadraticRuns.length}</td>
                          <td className="reasons-cell">{terminationSummary(quadraticRuns)}</td>
                          <td className="mono-num">{baselineSuccesses} of {baselineRuns.length}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="docs-section" id="metrics">
              <p className="doc-kicker">03: TRAJECTORY METRICS</p>
              <h2>Mean, spread, and median for each controller.</h2>
              <p>Values come from recorded trajectories. Obstacle clearance is unavailable in scenes without obstacles.</p>
              <EvaluationControllerView
                quadratic={quadratic}
                baseline={baseline}
                metricRows={metricRows}
              />
              <p className="docs-footnote">
                Obstacle clearance uses {quadratic.metrics.minimum_obstacle_clearance_m.sample_count} samples per controller.
                Other metrics use {quadratic.sample_count} runs per controller.
              </p>
            </section>

            <section className="docs-section" id="agent">
              <p className="doc-kicker">04: BOUNDED AGENT RECOVERY</p>
              <h2>
                {evaluationReport.agent_summary.disturbance_recoveries} of {evaluationReport.agent_summary.disturbance_trials} seeded corridor disturbances recovered.
              </h2>
              <div className="spec-table">
                <div>
                  <span>Mean decision calls</span>
                  <strong>{evaluationReport.agent_summary.mean_decision_calls_per_run.toFixed(2)} per quadratic run</strong>
                </div>
                <div>
                  <span>Mean replans</span>
                  <strong>{evaluationReport.agent_summary.mean_replans_per_run.toFixed(2)} per quadratic run</strong>
                </div>
                <div>
                  <span>Provider</span>
                  <strong>Deterministic offline mock</strong>
                </div>
                <div>
                  <span>Live latency</span>
                  <strong>Unavailable, no live requests in this suite</strong>
                </div>
              </div>
            </section>

            <section className="docs-section" id="limits">
              <p className="doc-kicker">05: SCOPE AND REPRODUCTION</p>
              <h2>This sample does not establish general reliability.</h2>
              <ul className="limit-list">
                {evaluationReport.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
              <div className="evaluation-actions">
                <a className="doc-action" href="/evaluation-report.json" download="fieldweaver-evaluation-report.json">
                  Download source JSON <span aria-hidden="true">↓</span>
                </a>
                <Link className="doc-action" href="/">
                  Open workbench <span aria-hidden="true">↗</span>
                </Link>
                <Link className="doc-action" href="/docs">
                  Read the field guide <span aria-hidden="true">↗</span>
                </Link>
              </div>
              <p className="docs-footnote">
                Snapshot generated {evaluationReport.generated_at_utc}. Regenerate it with <code>scripts/run_evaluation.py</code>.
              </p>
            </section>
          </article>
        </div>
      </main>
    </DocumentFrame>
  );
}
