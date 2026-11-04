"use client";

import { useState } from "react";

export interface LifecycleState {
  state: "IDLE" | "COMPILING" | "AWAITING_APPROVAL" | "RUNNING" | "REPLANNING" | "COMPLETE" | "ABORTED";
  label: string;
  trigger: string;
  guardConditions: string[];
  systemBehavior: string;
  nextStates: Array<LifecycleState["state"]>;
  safetyInvariants: string[];
}

export const LIFECYCLE_STATES: LifecycleState[] = [
  {
    state: "IDLE",
    label: "Idle (Docked)",
    trigger: "Initial page load or workbench reset event",
    guardConditions: [
      "No active simulation loop running",
      "Swarm docked at assigned starting coordinates"
    ],
    systemBehavior: "Workbench accepts operator mission prompt, scenario selection, and controller overrides.",
    nextStates: ["COMPILING"],
    safetyInvariants: ["Zero actuator movement while idle", "Deterministic RNG seed initialized"]
  },
  {
    state: "COMPILING",
    label: "Compiling Specification",
    trigger: "Operator dispatches 'Compile mission' action",
    guardConditions: [
      "Mission text prompt is non-empty",
      "Provider configured or offline deterministic mock available"
    ],
    systemBehavior: "Backend prompts Muse Spark Open or offline mock, then parses candidate JSON into Pydantic schema.",
    nextStates: ["AWAITING_APPROVAL", "IDLE"],
    safetyInvariants: [
      "Model output is strictly untrusted",
      "No ground-truth coordinates exposed in prompt context"
    ]
  },
  {
    state: "AWAITING_APPROVAL",
    label: "Awaiting Operator Approval",
    trigger: "Compiler returns validated MissionSpec v1.0",
    guardConditions: [
      "Schema validation passed with extra='forbid'",
      "Geometric ring feasibility check satisfied: separation <= 2*R*sin(pi/N)*0.95"
    ],
    systemBehavior: "UI displays formatted spec parameters, assumptions, and constraints. Simulation run is locked until explicit operator confirmation.",
    nextStates: ["RUNNING", "IDLE"],
    safetyInvariants: [
      "Manual human gate required before execution",
      "Immutable specification hash locked"
    ]
  },
  {
    state: "RUNNING",
    label: "Autonomous Execution (10 Hz)",
    trigger: "Operator approves mission and clicks 'Run simulation'",
    guardConditions: [
      "Approved specification locked",
      "RNG seed initialized and scenario geometry loaded"
    ],
    systemBehavior: "SimulationSession advances in 0.1s steps. Safety filter checks every velocity command before Euler integration.",
    nextStates: ["REPLANNING", "COMPLETE", "ABORTED"],
    safetyInvariants: [
      "Pre-step velocity scaling: 1.0 -> 0.6 -> 0.3 -> 0.0 m/s",
      "Pairwise separation >= 0.35m, obstacle clearance >= 0.20m",
      "Arena boundary margin >= 0.12m",
      "Zero LLM calls in per-tick controller loop"
    ]
  },
  {
    state: "REPLANNING",
    label: "Event Replan Checkpoint",
    trigger: "Obstacle pop-in event, repeated safety interventions, or progress blocked",
    guardConditions: [
      "Agent call budget remaining (calls < 4, replans < 2)",
      "Agent mode set to auto or live"
    ],
    systemBehavior: "Simulation pauses briefly. Bounded observation sent to agent. Model selects discrete DecisionAction enum.",
    nextStates: ["RUNNING", "ABORTED"],
    safetyInvariants: [
      "Hard ceiling of 2 replans per run",
      "Only discrete approved action enums accepted",
      "Hidden plume coordinates remain redacted"
    ]
  },
  {
    state: "COMPLETE",
    label: "Nominal Convergence",
    trigger: "Swarm encircles plume source within tolerance criteria",
    guardConditions: [
      "Localization error <= 0.25 m",
      "Formation error <= 0.25 m",
      "Dwell time >= 2.0 s"
    ],
    systemBehavior: "Simulation halts. Ground-truth source beacon revealed in post-run payload. Final trajectory metrics calculated.",
    nextStates: ["IDLE"],
    safetyInvariants: [
      "Ground truth unquarantined only post-termination",
      "Metrics calculated from actual recorded trajectory"
    ]
  },
  {
    state: "ABORTED",
    label: "Terminated (Infeasible)",
    trigger: "Max duration exceeded (180s), route infeasible, or safety veto ceiling reached",
    guardConditions: [
      "Termination boundary condition met"
    ],
    systemBehavior: "Simulation halts safely. Recorded trajectory frames preserved. Exact termination reason flagged in evaluation report.",
    nextStates: ["IDLE"],
    safetyInvariants: [
      "Robots brought to safe zero-velocity halt",
      "Failure diagnostics recorded for audit without score inflation"
    ]
  }
];

export function LifecycleVisualizer() {
  const [activeState, setActiveState] = useState<LifecycleState["state"]>("RUNNING");

  const currentState = LIFECYCLE_STATES.find((s) => s.state === activeState) ?? LIFECYCLE_STATES[3];

  return (
    <div className="lifecycle-visualizer">
      <div className="lifecycle-header">
        <div className="lifecycle-title-row">
          <span className="lifecycle-tag">STATE MACHINE VISUALIZER</span>
          <span className="lifecycle-state-badge">
            ACTIVE STATE: {currentState.state}
          </span>
        </div>
        <p className="lifecycle-lead">
          Explore the 7 deterministic lifecycle states governing mission compilation, safety gating, and run execution.
        </p>
      </div>

      <div className="lifecycle-track-container" role="tablist" aria-label="Mission lifecycle state track">
        <div className="lifecycle-track">
          {LIFECYCLE_STATES.map((item, idx) => {
            const isSelected = item.state === activeState;
            return (
              <button
                key={item.state}
                role="tab"
                aria-selected={isSelected}
                aria-controls={`lifecycle-panel-${item.state}`}
                id={`lifecycle-tab-${item.state}`}
                onClick={() => setActiveState(item.state)}
                className={`lifecycle-step-node ${isSelected ? "is-selected" : ""} state-${item.state.toLowerCase()}`}
              >
                <span className="step-num">{String(idx + 1).padStart(2, "0")}</span>
                <span className="step-label">{item.state}</span>
                <span className="step-name">{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div
        className="lifecycle-detail-panel"
        id={`lifecycle-panel-${currentState.state}`}
        role="tabpanel"
        aria-labelledby={`lifecycle-tab-${currentState.state}`}
      >
        <div className="lifecycle-detail-header">
          <div>
            <span className="detail-eyebrow">STATE SPECIFICATION</span>
            <h3 className="detail-title">{currentState.label}</h3>
          </div>
          <span className={`detail-code-pill state-pill-${currentState.state.toLowerCase()}`}>
            {currentState.state}
          </span>
        </div>

        <div className="lifecycle-detail-grid">
          <div className="detail-card">
            <span className="detail-card-label">State Trigger:</span>
            <p className="detail-card-text">{currentState.trigger}</p>
          </div>

          <div className="detail-card">
            <span className="detail-card-label">System Behavior:</span>
            <p className="detail-card-text">{currentState.systemBehavior}</p>
          </div>
        </div>

        <div className="lifecycle-detail-grid">
          <div className="detail-card">
            <span className="detail-card-label">Guard Conditions:</span>
            <ul className="detail-list">
              {currentState.guardConditions.map((cond) => (
                <li key={cond}>{cond}</li>
              ))}
            </ul>
          </div>

          <div className="detail-card">
            <span className="detail-card-label">Deterministic Safety Invariants:</span>
            <ul className="detail-list invariant-list">
              {currentState.safetyInvariants.map((inv) => (
                <li key={inv}>{inv}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="lifecycle-next-states">
          <span className="next-states-label">Valid Next State Transitions:</span>
          <div className="next-states-list">
            {currentState.nextStates.map((next) => {
              const nextObj = LIFECYCLE_STATES.find((s) => s.state === next);
              return (
                <button
                  key={next}
                  type="button"
                  className="next-state-pill"
                  onClick={() => setActiveState(next)}
                >
                  <span>Transition to {nextObj?.label ?? next}</span>
                  <span className="arrow" aria-hidden="true">→</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
