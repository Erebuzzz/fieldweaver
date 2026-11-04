"use client";

import { useState } from "react";

export type ApiLang = "curl" | "python" | "typescript";
export type ApiEndpointId = "compile" | "run" | "scenarios" | "health";

interface EndpointDoc {
  id: ApiEndpointId;
  method: "GET" | "POST";
  path: string;
  summary: string;
  description: string;
  code: Record<ApiLang, string>;
  responsePayload: string;
}

export const ENDPOINT_DOCS: EndpointDoc[] = [
  {
    id: "compile",
    method: "POST",
    path: "/api/missions/compile",
    summary: "Compile natural language mission text into validated MissionSpec v1.0",
    description: "Accepts operator instructions, calls Baseten Muse Spark Open or offline rule mock, and validates against Pydantic schema.",
    code: {
      curl: `curl -X POST http://127.0.0.1:8000/api/missions/compile \\
  -H "Content-Type: application/json" \\
  -d '{
    "mission_text": "Locate chemical source and encircle with 6 rovers in 1.5m ring formation.",
    "scenario_id": "open_field",
    "mode": "auto"
  }'`,
      python: `import httpx

payload = {
    "mission_text": "Locate chemical source and encircle with 6 rovers in 1.5m ring formation.",
    "scenario_id": "open_field",
    "mode": "auto"
}

response = httpx.post("http://127.0.0.1:8000/api/missions/compile", json=payload, timeout=30.0)
data = response.json()
print("Validated Spec:", data["spec"]["goal"])
print("Robot Count:", data["spec"]["robot_count"])`,
      typescript: `const response = await fetch("http://127.0.0.1:8000/api/missions/compile", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    mission_text: "Locate chemical source and encircle with 6 rovers in 1.5m ring formation.",
    scenario_id: "open_field",
    mode: "auto"
  })
});

const data = await response.json();
console.log("Validated spec:", data.spec);`
    },
    responsePayload: `{
  "status": "valid",
  "provider_used": "mock",
  "spec": {
    "version": "1.0",
    "goal": "source_localization_and_encirclement",
    "robot_count": 6,
    "scenario_id": "open_field",
    "safety_limits": {
      "maximum_speed": 0.50,
      "minimum_robot_separation": 0.35,
      "minimum_obstacle_clearance": 0.20,
      "boundary_margin": 0.12,
      "max_duration_seconds": 180.0
    },
    "formation": {
      "shape": "regular_ring",
      "target_radius_m": 1.50,
      "dwell_time_seconds": 2.0
    }
  },
  "compiler_assumptions": [
    "Formation radius set to 1.5m for optimal 6-robot arc separation",
    "Controller mode set to quadratic least-squares estimator"
  ],
  "clarifying_questions": []
}`
  },
  {
    id: "run",
    method: "POST",
    path: "/api/simulations/run",
    summary: "Execute deterministic simulation run from approved specification and seed",
    description: "Runs 10 Hz discrete Euler physics loop with independent safety filter enforcement and generates trajectory frames.",
    code: {
      curl: `curl -X POST http://127.0.0.1:8000/api/simulations/run \\
  -H "Content-Type: application/json" \\
  -d '{
    "spec": {
      "version": "1.0",
      "goal": "source_localization_and_encirclement",
      "robot_count": 6,
      "scenario_id": "open_field",
      "safety_limits": {
        "maximum_speed": 0.50,
        "minimum_robot_separation": 0.35,
        "minimum_obstacle_clearance": 0.20,
        "boundary_margin": 0.12,
        "max_duration_seconds": 180.0
      },
      "formation": {
        "shape": "regular_ring",
        "target_radius_m": 1.50,
        "dwell_time_seconds": 2.0
      }
    },
    "seed": 42,
    "controller": "quadratic"
  }'`,
      python: `import httpx

payload = {
    "spec": validated_spec,
    "seed": 42,
    "controller": "quadratic"
}

response = httpx.post("http://127.0.0.1:8000/api/simulations/run", json=payload, timeout=60.0)
run_data = response.json()
print("Run Status:", run_data["termination_reason"])
print("Frames Recorded:", len(run_data["frames"]))`,
      typescript: `const response = await fetch("http://127.0.0.1:8000/api/simulations/run", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    spec: validatedSpec,
    seed: 42,
    controller: "quadratic"
  })
});

const runData = await response.json();
console.log("Trajectory frames:", runData.frames.length);`
    },
    responsePayload: `{
  "simulation_id": "sim_7f3b89a0",
  "seed": 42,
  "controller": "quadratic",
  "success": true,
  "termination_reason": "nominal_convergence",
  "duration_seconds": 18.4,
  "frame_count": 184,
  "metrics": {
    "localization_error_m": 0.0042,
    "formation_error_m": 0.081,
    "minimum_robot_separation_m": 0.412,
    "minimum_obstacle_clearance_m": 0.350,
    "safety_interventions_count": 2,
    "robot_collisions_count": 0
  },
  "ground_truth_source": {
    "revealed_post_run": true,
    "x": 6.42,
    "y": 5.18,
    "peak_intensity": 100.0
  }
}`
  },
  {
    id: "scenarios",
    method: "GET",
    path: "/api/scenarios",
    summary: "Retrieve public arena scenarios and boundary geometries",
    description: "Returns public arena dimensions, static obstacle polygons, and initial docking coordinates without exposing hidden source positions.",
    code: {
      curl: `curl http://127.0.0.1:8000/api/scenarios`,
      python: `import httpx

response = httpx.get("http://127.0.0.1:8000/api/scenarios")
scenarios = response.json()["scenarios"]
for s in scenarios:
    print(f"Scenario: {s['name']} (ID: {s['id']})")`,
      typescript: `const response = await fetch("http://127.0.0.1:8000/api/scenarios");
const data = await response.json();
console.log("Available scenarios:", data.scenarios);`
    },
    responsePayload: `{
  "scenarios": [
    {
      "id": "open_field",
      "name": "Open Field",
      "description": "Unobstructed 10x10m arena for baseline plume seeking.",
      "arena_size": [10.0, 10.0],
      "obstacle_count": 0,
      "recommended_robots": 6
    },
    {
      "id": "restricted_corridor",
      "name": "Restricted Corridor",
      "description": "Central pillar obstacles requiring swarm detour routing.",
      "arena_size": [10.0, 10.0],
      "obstacle_count": 2,
      "recommended_robots": 5
    },
    {
      "id": "disturbed_corridor",
      "name": "Disturbed Corridor",
      "description": "Dynamic obstacle pop-in checkpoint triggering event replanning.",
      "arena_size": [10.0, 10.0],
      "obstacle_count": 3,
      "recommended_robots": 5
    }
  ]
}`
  },
  {
    id: "health",
    method: "GET",
    path: "/api/health",
    summary: "Inspect backend health, provider configuration, and active safety envelope",
    description: "Returns service uptime, model provider connection status (Baseten live vs offline mock), and enforced safety envelope limits.",
    code: {
      curl: `curl http://127.0.0.1:8000/api/health`,
      python: `import httpx

response = httpx.get("http://127.0.0.1:8000/api/health")
health = response.json()
print("Status:", health["status"])
print("Provider:", health["provider_status"])`,
      typescript: `const response = await fetch("http://127.0.0.1:8000/api/health");
const health = await response.json();
console.log("Backend status:", health.status);`
    },
    responsePayload: `{
  "status": "healthy",
  "version": "0.1.0",
  "provider_status": "offline_mock",
  "baseten_model": "meta-models/muse-spark-open-1026",
  "safety_envelope": {
    "speed_ceiling_mps": 0.50,
    "separation_floor_m": 0.35,
    "obstacle_clearance_m": 0.20,
    "boundary_margin_m": 0.12,
    "max_replans": 2,
    "max_model_calls": 4
  }
}`
  }
];

export function ApiConsole() {
  const [selectedEndpoint, setSelectedEndpoint] = useState<ApiEndpointId>("compile");
  const [selectedLang, setSelectedLang] = useState<ApiLang>("curl");
  const [copiedCode, setCopiedCode] = useState(false);
  const [copiedPayload, setCopiedPayload] = useState(false);
  const [showPayload, setShowPayload] = useState(true);

  const activeDoc = ENDPOINT_DOCS.find((d) => d.id === selectedEndpoint) ?? ENDPOINT_DOCS[0];

  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(activeDoc.code[selectedLang]);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    } catch {
      // Clipboard fallback
    }
  };

  const handleCopyPayload = async () => {
    try {
      await navigator.clipboard.writeText(activeDoc.responsePayload);
      setCopiedPayload(true);
      setTimeout(() => setCopiedPayload(false), 2000);
    } catch {
      // Clipboard fallback
    }
  };

  return (
    <div className="api-console">
      <div className="api-console-header">
        <div className="api-title-row">
          <span className="api-tag">INTERACTIVE API EXPLORER</span>
          <span className="api-origin-pill">BASE URL: http://127.0.0.1:8000</span>
        </div>
        <p className="api-lead">
          Inspect production request snippets, language clients, and realistic JSON schemas for all core endpoints.
        </p>
      </div>

      <div className="api-endpoint-selector" role="tablist" aria-label="API endpoint tabs">
        {ENDPOINT_DOCS.map((doc) => {
          const isSelected = doc.id === selectedEndpoint;
          return (
            <button
              key={doc.id}
              role="tab"
              aria-selected={isSelected}
              onClick={() => setSelectedEndpoint(doc.id)}
              className={`endpoint-tab-btn ${isSelected ? "is-selected" : ""}`}
            >
              <span className={`method-badge method-${doc.method.toLowerCase()}`}>{doc.method}</span>
              <span className="path-text">{doc.path}</span>
            </button>
          );
        })}
      </div>

      <div className="api-display-card">
        <div className="api-doc-summary">
          <div>
            <div className="api-route-title">
              <span className={`method-badge large method-${activeDoc.method.toLowerCase()}`}>
                {activeDoc.method}
              </span>
              <code className="route-path-code">{activeDoc.path}</code>
            </div>
            <p className="route-desc">{activeDoc.summary}</p>
          </div>
          <span className="subtle-note">{activeDoc.description}</span>
        </div>

        <div className="code-viewer-container">
          <div className="code-viewer-bar">
            <div className="lang-tabs" role="tablist" aria-label="Snippet language options">
              {(["curl", "python", "typescript"] as ApiLang[]).map((lang) => (
                <button
                  key={lang}
                  role="tab"
                  aria-selected={selectedLang === lang}
                  onClick={() => setSelectedLang(lang)}
                  className={`lang-tab ${selectedLang === lang ? "is-active" : ""}`}
                >
                  {lang === "curl" ? "cURL" : lang === "python" ? "Python (httpx)" : "TypeScript (fetch)"}
                </button>
              ))}
            </div>

            <button
              type="button"
              onClick={handleCopyCode}
              className="copy-btn"
              aria-label="Copy code snippet to clipboard"
            >
              {copiedCode ? "COPIED" : "COPY SNIPPET"}
            </button>
          </div>

          <pre className="code-block api-code-pre">
            <code>{activeDoc.code[selectedLang]}</code>
          </pre>
        </div>

        <div className="payload-viewer-container">
          <div className="payload-bar">
            <button
              type="button"
              className="payload-toggle-btn"
              onClick={() => setShowPayload(!showPayload)}
              aria-expanded={showPayload}
            >
              <span className="toggle-icon">{showPayload ? "▼" : "▶"}</span>
              <span>Sample Response Payload (200 OK)</span>
            </button>

            {showPayload && (
              <button
                type="button"
                onClick={handleCopyPayload}
                className="copy-btn mini"
                aria-label="Copy response JSON payload"
              >
                {copiedPayload ? "COPIED" : "COPY JSON"}
              </button>
            )}
          </div>

          {showPayload && (
            <pre className="code-block payload-pre">
              <code>{activeDoc.responsePayload}</code>
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
