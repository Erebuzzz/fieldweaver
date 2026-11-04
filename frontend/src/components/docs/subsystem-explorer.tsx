"use client";

import { useState } from "react";

export interface ArchitectureNode {
  id: string;
  name: string;
  category: "interface" | "compiler" | "simulation" | "safety" | "evaluation";
  summary: string;
  invariants: string[];
  inputs: string[];
  outputs: string[];
  sourcePath: string;
  status: "deterministic" | "quarantined" | "bounded" | "untrusted";
  connectedIds: string[];
}

export const ARCHITECTURE_NODES: ArchitectureNode[] = [
  {
    id: "operator_ui",
    name: "Operator Workbench",
    category: "interface",
    summary: "Next.js tactical mission control interface providing natural language input, parameter overrides, and live 3D/2D playback.",
    invariants: [
      "Zero provider API keys exposed to browser",
      "Manual operator approval required before run authorization",
      "Strict schema display with error highlighting"
    ],
    inputs: ["Operator text prompt", "Arena selection", "Controller choice (quadratic vs baseline)", "RNG seed"],
    outputs: ["Compile request payload", "Approved run execution dispatch"],
    sourcePath: "frontend/src/app/page.tsx",
    status: "deterministic",
    connectedIds: ["mission_compiler", "schema_validator", "simulation_core"]
  },
  {
    id: "mission_compiler",
    name: "Mission Compiler",
    category: "compiler",
    summary: "Translates natural language mission requests into structured, versioned MissionSpec objects using Baseten Muse Spark Open or offline deterministic rules.",
    invariants: [
      "Model output treated strictly as untrusted data",
      "Prompt contains zero ground-truth source coordinates",
      "Falls back to deterministic rule-based mock when provider key is absent"
    ],
    inputs: ["Mission text prompt", "Public scenario metadata", "Provider mode setting"],
    outputs: ["Candidate MissionSpec v1.0", "Compiler assumptions", "Clarifying operator questions"],
    sourcePath: "backend/app/services/compiler.py",
    status: "bounded",
    connectedIds: ["operator_ui", "schema_validator"]
  },
  {
    id: "schema_validator",
    name: "Strict Schema Validator",
    category: "safety",
    summary: "Enforces strict Pydantic model validation on all model proposals with extra='forbid' and geometric ring feasibility checks.",
    invariants: [
      "Slot arc clearance check: minimum_robot_separation <= 2*R*sin(pi/N)*0.95",
      "Rejects unknown fields, out-of-range gains, and negative bounds",
      "Locks validated specification hash for audit trail"
    ],
    inputs: ["Raw compiler JSON proposal"],
    outputs: ["Validated MissionSpec v1.0", "Validation error diagnostic trace"],
    sourcePath: "backend/app/schemas.py",
    status: "deterministic",
    connectedIds: ["mission_compiler", "operator_ui", "simulation_core"]
  },
  {
    id: "simulation_core",
    name: "Deterministic Simulation Core",
    category: "simulation",
    summary: "10 Hz discrete-time physics engine using explicit Euler kinematics (dt=0.1s) and quadratic scalar plume dispersion.",
    invariants: [
      "Seeded reproducibility across identical inputs",
      "Strict separation of physics calculation from network and UI",
      "Point-robot kinematic integration: x += v * dt"
    ],
    inputs: ["Validated MissionSpec", "Scenario static obstacles", "RNG seed integer"],
    outputs: ["High-resolution trajectory frames (x, y, heading, scalar reading)", "Final state metrics"],
    sourcePath: "backend/app/simulation/engine.py",
    status: "deterministic",
    connectedIds: ["safety_filter", "replan_agent", "telemetry_quarantine", "post_run_evaluator"]
  },
  {
    id: "safety_filter",
    name: "Independent Safety Filter",
    category: "safety",
    summary: "Independent motion checks can scale or reject unsafe transitions before and after each simulation step.",
    invariants: [
      "Progressive velocity scaling: 1.0 -> 0.6 -> 0.3 -> 0.0 m/s",
      "Pairwise robot separation >= 0.35 m",
      "Obstacle clearance margin >= 0.20 m",
      "Arena boundary margin >= 0.12 m inside 10.0 x 10.0 m box"
    ],
    inputs: ["Current robot states", "Proposed controller velocity vectors"],
    outputs: ["Safe scaled velocity vectors", "Intervention event records"],
    sourcePath: "backend/app/safety/validator.py",
    status: "deterministic",
    connectedIds: ["simulation_core"]
  },
  {
    id: "telemetry_quarantine",
    name: "Telemetry Quarantine Boundary",
    category: "evaluation",
    summary: "Strict security filter that redacts true plume source coordinates (x, y), peak intensity, and dispersion coefficients from all runtime frames.",
    invariants: [
      "Ground truth quarantined until run termination",
      "Agent decisions receive only estimated coordinates and team centroid",
      "Frames sent to UI contain scalar sensor readings only"
    ],
    inputs: ["Raw simulation engine state", "Hidden plume truth coordinates"],
    outputs: ["Sanitized public telemetry frames", "Runtime sensor readings"],
    sourcePath: "backend/app/services/runner.py",
    status: "quarantined",
    connectedIds: ["simulation_core", "operator_ui"]
  },
  {
    id: "replan_agent",
    name: "Bounded Event-Driven Agent",
    category: "compiler",
    summary: "Intermittent decision agent triggered only at discrete checkpoints (obstacle pop-in, repeated safety interventions, or stalls).",
    invariants: [
      "Hard budget ceiling: max 2 replans, max 4 model calls per run",
      "No LLM calls in per-tick 10 Hz simulation loop",
      "Discrete action enum choices only (no arbitrary actuator commands)"
    ],
    inputs: ["Event checkpoint observation", "Bounded action enum candidates"],
    outputs: ["AgentDecision with bounded ReasonCode and ActionEnum"],
    sourcePath: "backend/app/services/agent.py",
    status: "bounded",
    connectedIds: ["simulation_core", "safety_filter"]
  },
  {
    id: "post_run_evaluator",
    name: "Post-Run Evaluator",
    category: "evaluation",
    summary: "Independent assessment module calculating trajectory metrics, convergence times, localization errors, and safety counts from recorded data.",
    invariants: [
      "Ground truth revealed only in post-run payload upon completion",
      "Metrics calculated strictly from actual recorded paths",
      "Unbiased recording of both successes and failures"
    ],
    inputs: ["Recorded frame history", "True source beacon coordinates"],
    outputs: ["Evaluation report JSON with pass/fail gates and benchmark KPIs"],
    sourcePath: "backend/app/evaluation/evaluator.py",
    status: "deterministic",
    connectedIds: ["simulation_core", "operator_ui"]
  }
];

export function SubsystemExplorer() {
  const [selectedId, setSelectedId] = useState<string>("simulation_core");

  const activeNode = ARCHITECTURE_NODES.find((node) => node.id === selectedId) ?? ARCHITECTURE_NODES[0];

  return (
    <div className="subsystem-explorer">
      <div className="subsystem-graph-header">
        <div className="subsystem-title-row">
          <span className="subsystem-tag">TOPOLOGY VISUALIZER</span>
          <span className="subsystem-status-indicator">
            <i aria-hidden="true" />8 SUBSYSTEM NODES ACTIVE
          </span>
        </div>
        <p className="subsystem-lead">
          Select any node to inspect subsystem contracts, deterministic invariants, I/O schemas, and backend source files.
        </p>
      </div>

      <div className="subsystem-grid">
        <div className="subsystem-nodes-panel" role="tablist" aria-label="Subsystem node selector">
          {ARCHITECTURE_NODES.map((node, index) => {
            const isSelected = node.id === selectedId;
            return (
              <button
                key={node.id}
                role="tab"
                aria-selected={isSelected}
                aria-controls={`subsystem-inspector-${node.id}`}
                id={`subsystem-tab-${node.id}`}
                onClick={() => setSelectedId(node.id)}
                className={`subsystem-node-card ${isSelected ? "is-selected" : ""} cat-${node.category}`}
              >
                <div className="node-card-top">
                  <span className="node-index">{String(index + 1).padStart(2, "0")}</span>
                  <span className={`node-badge status-${node.status}`}>{node.status}</span>
                </div>
                <div className="node-name">{node.name}</div>
                <div className="node-category">{node.category}</div>
              </button>
            );
          })}
        </div>

        <div
          className="subsystem-inspector-card"
          id={`subsystem-inspector-${activeNode.id}`}
          role="tabpanel"
          aria-labelledby={`subsystem-tab-${activeNode.id}`}
        >
          <div className="inspector-card-header">
            <div>
              <span className="inspector-eyebrow">SUBSYSTEM CONTRACT</span>
              <h3 className="inspector-title">{activeNode.name}</h3>
            </div>
            <div className="inspector-badges">
              <span className={`inspector-status-badge status-${activeNode.status}`}>
                {activeNode.status}
              </span>
              <span className="inspector-category-badge">
                {activeNode.category}
              </span>
            </div>
          </div>

          <p className="inspector-summary">{activeNode.summary}</p>

          <div className="inspector-section">
            <span className="inspector-section-label">Deterministic Invariants:</span>
            <ul className="inspector-invariants-list">
              {activeNode.invariants.map((invariant) => (
                <li key={invariant}>
                  <span className="invariant-bullet" aria-hidden="true" />
                  <span>{invariant}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="inspector-io-grid">
            <div className="inspector-io-column">
              <span className="inspector-section-label">Input Contracts:</span>
              <ul className="inspector-io-list">
                {activeNode.inputs.map((input) => (
                  <li key={input}>{input}</li>
                ))}
              </ul>
            </div>
            <div className="inspector-io-column">
              <span className="inspector-section-label">Output Contracts:</span>
              <ul className="inspector-io-list">
                {activeNode.outputs.map((output) => (
                  <li key={output}>{output}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="inspector-footer">
            <div className="inspector-source-box">
              <span className="source-label">Source Implementation:</span>
              <code className="source-path">{activeNode.sourcePath}</code>
            </div>

            <div className="inspector-connections">
              <span className="connected-label">Connected Subsystems:</span>
              <div className="connected-pill-list">
                {activeNode.connectedIds.map((connId) => {
                  const target = ARCHITECTURE_NODES.find((n) => n.id === connId);
                  if (!target) return null;
                  return (
                    <button
                      key={connId}
                      type="button"
                      className="connected-pill"
                      onClick={() => setSelectedId(connId)}
                      title={`Jump to ${target.name}`}
                    >
                      {target.name} <span aria-hidden="true">→</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
