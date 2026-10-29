"use client";

import { useEffect, useMemo, useState } from "react";

import { ArenaCanvas } from "@/components/arena-canvas";
import { SiteFooter, SiteHeader } from "@/components/site-chrome";
import { apiRequest } from "@/lib/api";
import type {
  CompileResponse,
  Health,
  RunResult,
  Scenario,
  ScenarioListResponse,
} from "@/lib/types";

const EXAMPLE_MISSION =
  "Search for the signal source, maintain a ring formation, and avoid restricted regions.";

type ProviderMode = "auto" | "mock" | "live";
type AgentMode = "auto" | "off" | "mock" | "live";
type Controller = "quadratic" | "baseline";
type CompiledMission = {
  result: CompileResponse;
  scenarioId: string;
  missionText: string;
};

function number(value: number | null | undefined, digits = 2): string {
  return value === null || value === undefined || !Number.isFinite(value)
    ? "Unavailable"
    : value.toFixed(digits);
}

function metricLabel(value: number | null | undefined, suffix = "", digits = 2): string {
  return value === null || value === undefined ? "Unavailable" : `${number(value, digits)}${suffix}`;
}

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [seedDefault, setSeedDefault] = useState(42);
  const [scenarioId, setScenarioId] = useState("open_field");
  const [missionText, setMissionText] = useState(EXAMPLE_MISSION);
  const [providerMode, setProviderMode] = useState<ProviderMode>("auto");
  const [agentMode, setAgentMode] = useState<AgentMode>("auto");
  const [controller, setController] = useState<Controller>("quadratic");
  const [seed, setSeed] = useState("42");
  const [compiled, setCompiled] = useState<CompiledMission | null>(null);
  const [approved, setApproved] = useState(false);
  const [result, setResult] = useState<RunResult | null>(null);
  const [frameIndex, setFrameIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [busy, setBusy] = useState<"compile" | "run" | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([
      apiRequest<Health>("/api/health"),
      apiRequest<ScenarioListResponse>("/api/scenarios"),
    ])
      .then(([healthResponse, scenarioResponse]) => {
        if (!active) return;
        setHealth(healthResponse);
        setScenarios(scenarioResponse.scenarios);
        setSeedDefault(scenarioResponse.seed.default);
        setSeed(String(scenarioResponse.seed.default));
      })
      .catch((reason: unknown) => {
        if (!active) return;
        setApiError(reason instanceof Error ? reason.message : "The backend could not be reached.");
      });
    return () => {
      active = false;
    };
  }, []);

  const selectedScenario = scenarios.find((scenario) => scenario.id === scenarioId) ?? null;
  const activeCompile =
    compiled?.scenarioId === scenarioId && compiled.missionText === missionText
      ? compiled.result
      : null;
  const mission = activeCompile?.spec ?? result?.mission ?? null;
  const currentFrame = result?.frames[frameIndex] ?? null;
  const lastFrameIndex = Math.max(0, (result?.frames.length ?? 1) - 1);
  const missionReady = Boolean(activeCompile && approved);
  const metrics = result?.evaluation.metrics;
  const finalStatus = result?.evaluation.success ? "Converged" : "Stopped safely";
  const workflowStep = result ? 4 : activeCompile ? (approved ? 3 : 2) : 1;

  const agentEvents = useMemo(() => result?.agent.trace ?? [], [result]);
  const safetyEvents = useMemo(
    () => result?.safety.interventions.slice(-8).reverse() ?? [],
    [result],
  );

  useEffect(() => {
    if (!playing || !result) return;
    if (frameIndex >= lastFrameIndex) return;
    const nextFrame = frameIndex + 1;
    const timer = window.setTimeout(
      () => {
        setFrameIndex(nextFrame);
        if (nextFrame >= lastFrameIndex) setPlaying(false);
      },
      Math.max(40, 120 / speed),
    );
    return () => window.clearTimeout(timer);
  }, [playing, result, frameIndex, lastFrameIndex, speed]);

  function invalidateMission() {
    setCompiled(null);
    setApproved(false);
    setResult(null);
    setFrameIndex(0);
    setPlaying(false);
    setActionError(null);
  }

  async function compileMission() {
    if (!missionText.trim()) {
      setActionError("Enter a mission before compiling it.");
      return;
    }
    setBusy("compile");
    setActionError(null);
    setResult(null);
    setPlaying(false);
    try {
      const response = await apiRequest<CompileResponse>("/api/missions/compile", {
        mission_text: missionText,
        scenario_id: scenarioId,
        mode: providerMode,
      });
      setCompiled({ result: response, scenarioId, missionText });
      setApproved(false);
    } catch (reason) {
      setCompiled(null);
      setApproved(false);
      setActionError(reason instanceof Error ? reason.message : "Mission compilation failed.");
    } finally {
      setBusy(null);
    }
  }

  async function runSimulation() {
    if (!activeCompile || !approved) return;
    const parsedSeed = Number(seed);
    if (!Number.isInteger(parsedSeed) || parsedSeed < 0 || parsedSeed > 2_147_483_647) {
      setActionError("Seed must be a whole number between 0 and 2,147,483,647.");
      return;
    }
    setBusy("run");
    setActionError(null);
    setResult(null);
    setFrameIndex(0);
    setPlaying(false);
    try {
      const response = await apiRequest<RunResult>("/api/simulations/run", {
        mission: activeCompile.spec,
        scenario_id: scenarioId,
        seed: parsedSeed,
        controller,
        agent_mode: agentMode,
      });
      setResult(response);
      setFrameIndex(0);
      setPlaying(response.frames.length > 1);
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : "Simulation could not be started.");
    } finally {
      setBusy(null);
    }
  }

  function selectScenario(nextId: string) {
    setScenarioId(nextId);
    invalidateMission();
  }

  function editMission(nextText: string) {
    setMissionText(nextText);
    invalidateMission();
  }

  return (
    <div className="app-shell">
      <SiteHeader
        active="workbench"
        backend={health ? "connected" : apiError ? "unavailable" : "connecting"}
        provider={health ? (health.provider.configured ? "live" : "offline") : null}
      />

      <main className="workspace-main" id="workspace">
      <div className="workspace-heading">
        <div>
          <p className="eyebrow"><span className="eyebrow-mark" aria-hidden="true" />Swarm localization / 2D arena</p>
          <h1>Mission workspace</h1>
          <p className="workspace-description">
            Compile operator intent, review the bounded plan, then inspect a seeded run.
          </p>
        </div>
        <div className="run-state" aria-live="polite">
          <span className={`state-dot ${result ? (result.evaluation.success ? "state-success" : "state-stop") : ""}`} />
          <span>{busy === "compile" ? "Compiling mission" : busy === "run" ? "Running simulation" : result ? finalStatus : activeCompile ? (approved ? "Approved to run" : "Review required") : "Draft mission"}</span>
        </div>
      </div>

      <nav className="workflow-rail" aria-label="Mission workflow">
        <span className="workflow-label">WORKFLOW</span>
        {[
          [1, "Describe"],
          [2, "Review spec"],
          [3, "Approve run"],
          [4, "Evaluate"],
        ].map(([step, label]) => (
          <span className={`workflow-step ${workflowStep >= Number(step) ? "is-reached" : ""} ${workflowStep === Number(step) ? "is-current" : ""}`} key={step}>
            <i>{String(step).padStart(2, "0")}</i>{label}
          </span>
        ))}
      </nav>

      {apiError ? (
        <div className="alert alert-error" role="alert">
          <strong>Backend unavailable</strong>
          <span>{apiError}</span>
          <button className="text-button" onClick={() => window.location.reload()} type="button">
            Retry connection
          </button>
        </div>
      ) : null}
      {actionError ? (
        <div className="alert alert-error" role="alert">
          <strong>Request not completed</strong>
          <span>{actionError}</span>
          <button className="alert-dismiss" onClick={() => setActionError(null)} type="button" aria-label="Dismiss error">
            ×
          </button>
        </div>
      ) : null}

      <section className="workspace-grid" aria-label="Mission and simulation workspace">
        <aside className="mission-column">
          <div className="section-heading">
            <span className="section-index">01</span>
            <div>
              <h2>Mission</h2>
              <p>Describe the task and choose a known arena.</p>
            </div>
          </div>

          <label className="field-label" htmlFor="mission-text">Mission objective</label>
          <textarea
            id="mission-text"
            className="mission-input"
            value={missionText}
            onChange={(event) => editMission(event.target.value)}
            maxLength={2_000}
            placeholder="Describe what the swarm should do..."
            rows={5}
          />
          <button className="example-link" type="button" onClick={() => editMission(EXAMPLE_MISSION)}>
            Use example mission
          </button>

          <div className="field-row">
            <label className="field-group" htmlFor="scenario-select">
              <span className="field-label">Arena</span>
              <select
                id="scenario-select"
                value={scenarioId}
                onChange={(event) => selectScenario(event.target.value)}
                disabled={!scenarios.length || busy !== null}
              >
                {scenarios.map((scenario) => (
                  <option key={scenario.id} value={scenario.id}>{scenario.name}</option>
                ))}
              </select>
            </label>
            <label className="field-group seed-group" htmlFor="seed-input">
              <span className="field-label">Seed</span>
              <input
                id="seed-input"
                type="number"
                min={0}
                max={2_147_483_647}
                step={1}
                value={seed}
                onChange={(event) => setSeed(event.target.value)}
              />
            </label>
          </div>
          <p className="scenario-description">
            {selectedScenario?.description ?? "Loading arena descriptions..."}
          </p>

          <div className="field-row field-row-small">
            <label className="field-group" htmlFor="compiler-mode">
              <span className="field-label">Mission compiler</span>
              <select id="compiler-mode" value={providerMode} onChange={(event) => setProviderMode(event.target.value as ProviderMode)}>
                <option value="auto">Automatic</option>
                <option value="mock">Offline mock</option>
                <option value="live">Baseten live</option>
              </select>
            </label>
            <label className="field-group" htmlFor="agent-mode">
              <span className="field-label">Agent decisions</span>
              <select id="agent-mode" value={agentMode} onChange={(event) => setAgentMode(event.target.value as AgentMode)}>
                <option value="auto">Automatic</option>
                <option value="off">Off</option>
                <option value="mock">Offline mock</option>
                <option value="live">Baseten live</option>
              </select>
            </label>
          </div>
          <div className="field-row field-row-small">
            <label className="field-group" htmlFor="controller-select">
              <span className="field-label">Controller</span>
              <select id="controller-select" value={controller} onChange={(event) => setController(event.target.value as Controller)}>
                <option value="quadratic">Quadratic estimator</option>
                <option value="baseline">Weighted-centroid baseline</option>
              </select>
            </label>
          </div>

          <button
            className="primary-button compile-button"
            type="button"
            onClick={compileMission}
            disabled={busy !== null || !health || !missionText.trim()}
          >
            {busy === "compile" ? <span className="button-spinner" /> : <span className="compile-glyph">↳</span>}
            {busy === "compile" ? "Compiling" : "Compile mission"}
          </button>

          {activeCompile ? (
            <div className="compile-result" aria-live="polite">
              <div className="compile-result-heading">
                <span className="check-mark">✓</span>
                <div>
                  <strong>Validated specification</strong>
                  <span className={`provider-detail ${activeCompile.provider.mode}`}>
                    {activeCompile.provider.mode === "live" ? "Baseten live" : "Offline mock"}
                    <span> / </span>{activeCompile.provider.model}
                  </span>
                </div>
              </div>
              <dl className="mission-summary">
                <div><dt>Robots</dt><dd>{activeCompile.spec.robot_count}</dd></div>
                <div><dt>Ring radius</dt><dd>{number(activeCompile.spec.formation.radius)} m</dd></div>
                <div><dt>Run limit</dt><dd>{number(activeCompile.spec.search.max_duration_s, 0)} s</dd></div>
                <div><dt>Speed cap</dt><dd>{number(activeCompile.spec.constraints.maximum_speed)} m/s</dd></div>
              </dl>
              {activeCompile.spec.assumptions.length ? (
                <div className="review-note">
                  <span className="field-label">Assumptions</span>
                  <ul>{activeCompile.spec.assumptions.map((item) => <li key={item}>{item}</li>)}</ul>
                </div>
              ) : null}
              {activeCompile.spec.unsupported_requirements.length || activeCompile.warnings.length ? (
                <div className="review-warning">
                  <span className="field-label">Review notes</span>
                  <ul>
                    {[...activeCompile.spec.unsupported_requirements, ...activeCompile.warnings].map((item, index) => (
                      <li key={`${index}-${item}`}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {activeCompile.spec.clarifying_questions.length ? (
                <div className="review-warning">
                  <span className="field-label">Clarification needed</span>
                  <ul>{activeCompile.spec.clarifying_questions.map((item) => <li key={item}>{item}</li>)}</ul>
                </div>
              ) : null}
              <label className="approval-control">
                <input
                  type="checkbox"
                  checked={approved}
                  onChange={(event) => setApproved(event.target.checked)}
                  disabled={busy !== null || activeCompile.spec.clarifying_questions.length > 0}
                />
                <span>I reviewed this specification and approve the run.</span>
              </label>
              <button
                className="run-button"
                type="button"
                onClick={runSimulation}
                disabled={!missionReady || busy !== null || !selectedScenario}
              >
                {busy === "run" ? <span className="button-spinner" /> : <span className="run-glyph">▶</span>}
                {busy === "run" ? "Running simulation" : "Run approved mission"}
              </button>
            </div>
          ) : (
            <div className="review-empty">
              <span className="empty-step">02</span>
              <p>Compile to review the validated mission, assumptions, and safety limits.</p>
            </div>
          )}
        </aside>

        <section className="arena-column" aria-label="Simulation arena">
          <div className="section-heading arena-heading">
            <span className="section-index">02</span>
            <div className="arena-title">
              <div>
                <h2>Arena</h2>
                <p>{selectedScenario?.name ?? "No arena selected"} · {selectedScenario?.arena.width_m ?? 10} × {selectedScenario?.arena.height_m ?? 10} m</p>
              </div>
              {result ? (
                <span className={`result-badge ${result.evaluation.success ? "success" : "failure"}`}>
                  {result.evaluation.success ? "SUCCESS" : result.evaluation.failure_reason?.replaceAll("_", " ").toUpperCase() ?? "STOPPED"}
                </span>
              ) : <span className="arena-idle">READY</span>}
            </div>
          </div>

          <ArenaCanvas
            scenario={selectedScenario}
            mission={mission}
            result={result}
            frame={currentFrame}
            frameIndex={frameIndex}
          />

          <div className="playback-bar">
            <div className="playback-buttons">
              <button
                className="play-button"
                type="button"
                onClick={() => setPlaying((value) => !value)}
                disabled={!result || busy !== null}
                aria-label={playing ? "Pause playback" : "Play playback"}
              >
                {playing ? "Ⅱ" : "▶"}
              </button>
              <button
                className="reset-button"
                type="button"
                onClick={() => { setPlaying(false); setFrameIndex(0); }}
                disabled={!result}
              >
                Reset
              </button>
            </div>
            <input
              className="timeline-slider"
              aria-label="Simulation playback position"
              type="range"
              min={0}
              max={lastFrameIndex}
              value={Math.min(frameIndex, lastFrameIndex)}
              onChange={(event) => { setPlaying(false); setFrameIndex(Number(event.target.value)); }}
              disabled={!result}
            />
            <span className="playback-time">
              {number(currentFrame?.t ?? 0, 1)} <span>/</span> {number(result?.duration_s ?? 0, 1)} s
            </span>
            <label className="speed-control">
              <span className="sr-only">Playback speed</span>
              <select value={speed} onChange={(event) => setSpeed(Number(event.target.value))} disabled={!result}>
                <option value={0.5}>0.5×</option>
                <option value={1}>1×</option>
                <option value={2}>2×</option>
              </select>
            </label>
          </div>

          {result ? (
            <div className="arena-caption">
              <span>Seed {result.seed}</span>
              <span>Frame {frameIndex + 1} / {result.frames.length}</span>
              <span>{result.agent.mode === "live" && result.agent.live_verified ? "Live agent call verified" : `Agent ${result.agent.mode}`}</span>
            </div>
          ) : (
            <div className="arena-caption">
              <span>Choose a scenario and compile a mission to begin.</span>
              <span>Ground truth stays in the evaluator until a run ends.</span>
            </div>
          )}
        </section>

        <aside className="inspector-column">
          <div className="section-heading">
            <span className="section-index">03</span>
            <div>
              <h2>Evaluation</h2>
              <p>Metrics from the recorded trajectory.</p>
            </div>
          </div>

          {result ? (
            <>
              <div className={`evaluation-status ${result.evaluation.success ? "success" : "failure"}`}>
                <span className="evaluation-mark">{result.evaluation.success ? "✓" : "!"}</span>
                <div>
                  <strong>{result.evaluation.success ? "Mission converged" : "Mission stopped safely"}</strong>
                  <span>{result.evaluation.failure_reason?.replaceAll("_", " ") ?? "All acceptance checks passed"}</span>
                </div>
              </div>
              <div className="metrics-list">
                <Metric label="Localization error" value={metricLabel(metrics?.localization_error_m, " m")} />
                <Metric label="Formation error" value={metricLabel(metrics?.formation_error_m, " m")} />
                <Metric label="Minimum separation" value={metricLabel(metrics?.minimum_robot_separation_m, " m")} />
                <Metric label="Obstacle clearance" value={metricLabel(metrics?.minimum_obstacle_clearance_m, " m")} />
                <Metric label="Total path length" value={metricLabel(metrics?.path_length_total_m, " m")} />
                <Metric label="Simulation time" value={metricLabel(metrics?.simulation_duration_s, " s", 1)} />
                <Metric label="Safety interventions" value={String(metrics?.safety_intervention_count ?? "Unavailable")} />
                <Metric label="Robot collisions" value={String(metrics?.robot_collision_count ?? "Unavailable")} />
              </div>
              <div className="check-list">
                <h3>Acceptance checks</h3>
                {result.evaluation.checks.map((check) => (
                  <div className="check-row" key={check.name}>
                    <span className={`check-dot ${check.passed ? "passed" : "failed"}`} />
                    <div><strong>{check.name.replaceAll("_", " ")}</strong><span>{check.detail}</span></div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="inspector-empty">
              <span className="empty-ring" />
              <strong>No evaluation yet</strong>
              <p>Run a reviewed mission to see measured localization, formation, safety, and path metrics.</p>
            </div>
          )}

          {result?.warnings.length ? (
            <div className="result-warnings">
              <h3>Run notes</h3>
              <ul>{result.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
            </div>
          ) : null}
        </aside>
      </section>

      <section className="trace-section" aria-label="Agent and safety trace">
        <div className="trace-heading">
          <div className="section-heading">
            <span className="section-index">04</span>
            <div>
              <h2>Run trace</h2>
              <p>Event-driven decisions and independent safety interventions.</p>
            </div>
          </div>
          {result ? (
            <div className="trace-meta">
              <span>{result.agent.decision_calls} decision calls</span>
              <span>{result.agent.replans} replans</span>
              <span>{result.agent.live_verified ? "Live verified" : result.agent.mode === "off" ? "Agent disabled" : "Mock or no live call"}</span>
            </div>
          ) : null}
        </div>

        {result ? (
          <div className="trace-columns">
            <div className="trace-list">
              <h3>Agent events</h3>
              {agentEvents.length ? (
                <ol>
                  {agentEvents.map((entry, index) => (
                    <li className="trace-row" key={`${entry.seq ?? index}-${entry.phase ?? "event"}`}>
                      <span className="trace-time">{number(typeof entry.t === "number" ? entry.t : 0, 1)} s</span>
                      <span className={`trace-phase phase-${entry.phase ?? "event"}`}>{entry.phase ?? "event"}</span>
                      <div>
                        <strong>{entry.reason_code?.replaceAll("_", " ") ?? entry.decision?.replaceAll("_", " ") ?? "System"}</strong>
                        <p>{entry.detail ?? entry.rationale ?? "No additional detail recorded."}</p>
                      </div>
                    </li>
                  ))}
                </ol>
              ) : <p className="trace-empty">No replan events occurred during this run.</p>}
            </div>
            <div className="safety-list">
              <h3>Safety interventions <span>{result.safety.total}</span></h3>
              {safetyEvents.length ? (
                <ol>
                  {safetyEvents.map((event, index) => (
                    <li className="safety-row" key={`${event.step}-${event.kind}-${index}`}>
                      <span className="safety-kind">{event.kind.replaceAll("_", " ")}</span>
                      <span className="trace-time">{number(event.t, 1)} s</span>
                      <p>{event.detail}</p>
                    </li>
                  ))}
                </ol>
              ) : <p className="trace-empty">No safety interventions recorded.</p>}
              {result.safety.truncated ? <p className="truncation-note">Only a recent sample is shown.</p> : null}
            </div>
          </div>
        ) : (
          <div className="trace-placeholder">Trace details appear after a simulation run.</div>
        )}
      </section>

      <div className="app-meta">
        <span>FieldWeaver / deterministic simulation</span>
        <span>{health?.provider.model ?? "Provider status unavailable"}</span>
        <span>dt {health ? number(health.simulation.dt_s, 1) : "n/a"} s / seed default {seedDefault}</span>
      </div>
      </main>
      <SiteFooter />
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
