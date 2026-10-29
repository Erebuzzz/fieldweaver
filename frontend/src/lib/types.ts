export type PublicRegion = {
  id: string;
  kind: "obstacle" | "restricted";
  label: string;
  shape: "rect" | "circle";
  active_from_s: number;
  x_min?: number;
  y_min?: number;
  x_max?: number;
  y_max?: number;
  cx?: number;
  cy?: number;
  radius?: number;
};

export type Scenario = {
  id: string;
  name: string;
  description: string;
  arena: { width_m: number; height_m: number };
  sensor: Record<string, unknown>;
  initial_regions: PublicRegion[];
  scheduled_event_count: number;
  default_robot_count: number;
  recommended_mission: string;
  tags: string[];
  source_revealed: false;
};

export type MissionSpec = {
  schema_version: "1.0";
  goal: "locate_and_encircle_source";
  robot_count: number;
  formation: { type: "ring"; radius: number };
  search: {
    strategy: "scalar_field_source_seeking";
    max_duration_s: number;
    target_source_count: 1;
  };
  constraints: {
    minimum_robot_separation: number;
    minimum_obstacle_clearance: number;
    maximum_speed: number;
    avoid_restricted_regions: true;
  };
  termination: { localization_tolerance: number; formation_tolerance: number };
  assumptions: string[];
  clarifying_questions: string[];
  unsupported_requirements: string[];
};

export type ProviderMetadata = {
  mode: "mock" | "live";
  name: "mock" | "baseten";
  model: string;
  latency_ms: number;
  live_verified: boolean;
  usage: Record<string, number>;
};

export type Health = {
  status: "ok";
  mode: "offline_mock" | "live_configured";
  provider: {
    name: "baseten" | "mock";
    model: string;
    configured: boolean;
    mode: "live" | "mock";
  };
  simulation: { dt_s: number; arena_width_m: number; arena_height_m: number };
};

export type CompileResponse = {
  spec: MissionSpec;
  provider: ProviderMetadata;
  warnings: string[];
  request_id: string;
};

export type FrameRobot = {
  id: number;
  x: number;
  y: number;
  heading: number;
  measurement: number;
};

export type Frame = {
  step: number;
  t: number;
  robots: FrameRobot[];
  estimate: { x: number; y: number; confidence: number; valid: boolean; samples: number };
  formation_error_estimate: number;
  obstacle_version: number;
  active_region_ids: string[];
};

export type AgentTraceEntry = {
  seq?: number;
  t?: number;
  phase?: string;
  detail?: string;
  reason_code?: string;
  decision?: string;
  rationale?: string;
  [key: string]: unknown;
};

export type Evaluation = {
  success: boolean;
  failure_reason: string | null;
  metrics: {
    localization_error_m: number;
    formation_error_m: number;
    robot_collision_count: number;
    minimum_robot_separation_m: number;
    minimum_obstacle_clearance_m: number | null;
    path_length_total_m: number;
    simulation_duration_s: number;
    wall_clock_ms: number;
    safety_intervention_count: number;
    controller_iteration_count: number;
    termination_reason: string;
    obstacle_event_count: number;
    [key: string]: number | boolean | string | null;
  };
  checks: { name: string; passed: boolean; detail: string }[];
  ground_truth: { x: number; y: number; revealed: "after_run_only" };
  final_estimate: {
    x: number;
    y: number;
    confidence: number;
    samples: number;
    valid: boolean;
    residual: number;
    curvature: number;
    note: string;
  };
};

export type RunResult = {
  run_id: string;
  scenario: Scenario;
  mission: MissionSpec;
  seed: number;
  controller: "quadratic" | "baseline";
  agent: {
    mode: "off" | "mock" | "live";
    model: string;
    decision_calls: number;
    replans: number;
    live_calls: number;
    live_verified: boolean;
    max_decisions: number;
    max_replans: number;
    termination_detail: string | null;
    trace: AgentTraceEntry[];
  };
  frames: Frame[];
  world_events: { t: number; type: string; regions: PublicRegion[]; detail: string }[];
  safety: {
    total: number;
    counts_by_kind: Record<string, number>;
    interventions: { step: number; t: number; kind: string; robot_id: number | null; detail: string }[];
    truncated: boolean;
  };
  evaluation: Evaluation;
  duration_s: number;
  wall_clock_ms: number;
  warnings: string[];
  request_id: string;
};

export type ScenarioListResponse = {
  scenarios: Scenario[];
  seed: { min: number; max: number; default: number };
  limits: Record<string, number>;
  request_id: string;
};

export type ApiErrorBody = {
  error?: { code?: string; message?: string; request_id?: string };
};
