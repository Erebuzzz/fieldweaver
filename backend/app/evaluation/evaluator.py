"""Metrics computed from recorded trajectories and evaluator-only ground truth."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from app import limits
from app.schemas import MissionSpec
from app.simulation.scenario import Scenario
from app.simulation.types import Frame, SafetyIntervention, WorldEvent


@dataclass(frozen=True)
class EvaluationResult:
    success: bool
    failure_reason: str | None
    metrics: dict[str, Any]
    checks: list[dict[str, Any]]
    ground_truth: dict[str, Any]
    final_estimate: dict[str, Any]

    def to_public(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "failure_reason": self.failure_reason,
            "metrics": self.metrics,
            "checks": self.checks,
            "ground_truth": self.ground_truth,
            "final_estimate": self.final_estimate,
        }


def evaluate_run(
    scenario: Scenario,
    mission: MissionSpec,
    frames: list[Frame],
    interventions: list[SafetyIntervention],
    world_events: list[WorldEvent],
    termination_reason: str,
    wall_clock_ms: float,
    seed: int,
    controller_name: str,
) -> EvaluationResult:
    if not frames:
        raise ValueError("cannot evaluate an empty trajectory")
    final_frame = frames[-1]
    final_estimate = final_frame.estimate
    truth_x = scenario.source.x
    truth_y = scenario.source.y
    radius = mission.formation.radius
    separation_limit = mission.constraints.minimum_robot_separation
    clearance_limit = mission.constraints.minimum_obstacle_clearance
    boundary_margin = limits.BOUNDARY_MARGIN_M

    localization_error = math.hypot(final_estimate.x - truth_x, final_estimate.y - truth_y)
    radial_errors = [
        math.hypot(robot.x - truth_x, robot.y - truth_y) - radius for robot in final_frame.robots
    ]
    formation_error = math.sqrt(sum(error * error for error in radial_errors) / len(radial_errors))

    min_separation = math.inf
    collision_count = 0
    boundary_violations = 0
    numeric_invalid = 0
    min_clearance: float | None = None
    path_length = 0.0
    previous_positions: dict[int, tuple[float, float]] = {}

    for frame in frames:
        for robot in frame.robots:
            if not all(math.isfinite(value) for value in (robot.x, robot.y, robot.heading)):
                numeric_invalid += 1
            if not (
                boundary_margin <= robot.x <= scenario.width - boundary_margin
                and boundary_margin <= robot.y <= scenario.height - boundary_margin
            ):
                boundary_violations += 1
            if robot.robot_id in previous_positions:
                previous_x, previous_y = previous_positions[robot.robot_id]
                path_length += math.hypot(robot.x - previous_x, robot.y - previous_y)
            previous_positions[robot.robot_id] = (robot.x, robot.y)

        robots = frame.robots
        for left_index, left in enumerate(robots):
            for right in robots[left_index + 1 :]:
                distance = math.hypot(left.x - right.x, left.y - right.y)
                min_separation = min(min_separation, distance)
                if distance < separation_limit - limits.NUMERIC_EPSILON:
                    collision_count += 1

        active_regions = scenario.active_regions(frame.time_s)
        for region in active_regions:
            for robot in robots:
                from app.simulation.geometry import Vec2

                clearance = region.clearance(Vec2(robot.x, robot.y))
                min_clearance = (
                    clearance
                    if min_clearance is None
                    else min(min_clearance, clearance)
                )

    if min_separation is math.inf:
        min_separation = 0.0
    if not math.isfinite(localization_error) or not math.isfinite(formation_error):
        numeric_invalid += 1

    runtime_nominal = termination_reason == "nominal_convergence"
    checks = [
        {
            "name": "nominal_convergence",
            "passed": runtime_nominal,
            "detail": f"runtime termination was {termination_reason}",
        },
        {
            "name": "localization_tolerance",
            "passed": localization_error <= mission.termination.localization_tolerance,
            "detail": (
                f"final estimate error {localization_error:.3f} m vs "
                f"{mission.termination.localization_tolerance:.3f} m tolerance"
            ),
        },
        {
            "name": "formation_tolerance",
            "passed": formation_error <= mission.termination.formation_tolerance,
            "detail": (
                f"radial RMS {formation_error:.3f} m vs "
                f"{mission.termination.formation_tolerance:.3f} m tolerance"
            ),
        },
        {
            "name": "robot_separation",
            "passed": min_separation >= separation_limit - limits.NUMERIC_EPSILON,
            "detail": f"minimum separation {min_separation:.3f} m vs {separation_limit:.3f} m",
        },
        {
            "name": "obstacle_clearance",
            "passed": (
                min_clearance is None
                or min_clearance >= clearance_limit - limits.NUMERIC_EPSILON
            ),
            "detail": (
                "no active obstacles"
                if min_clearance is None
                else f"minimum clearance {min_clearance:.3f} m vs {clearance_limit:.3f} m"
            ),
        },
        {
            "name": "arena_boundaries",
            "passed": boundary_violations == 0,
            "detail": f"{boundary_violations} robot-frame boundary violations",
        },
        {
            "name": "numeric_validity",
            "passed": numeric_invalid == 0,
            "detail": f"{numeric_invalid} invalid numeric states",
        },
        {
            "name": "no_safety_failure",
            "passed": termination_reason != "safety_abort",
            "detail": f"{len(interventions)} safety interventions recorded",
        },
    ]
    success = all(check["passed"] for check in checks)

    if success:
        failure_reason = None
    elif termination_reason == "safety_abort":
        failure_reason = "safety_abort"
    elif termination_reason == "user_abort":
        failure_reason = "user_abort"
    elif termination_reason == "user_clarification_required":
        failure_reason = "user_clarification_required"
    elif termination_reason == "provider_failure":
        failure_reason = "provider_failure"
    elif termination_reason == "replan_budget_exhausted":
        failure_reason = "replan_budget_exhausted"
    elif termination_reason in {"route_infeasible", "invalid_decision"}:
        failure_reason = termination_reason
    elif not runtime_nominal:
        failure_reason = "timeout_before_convergence"
    elif localization_error > mission.termination.localization_tolerance:
        failure_reason = "localization_tolerance_not_met"
    elif formation_error > mission.termination.formation_tolerance:
        failure_reason = "formation_tolerance_not_met"
    elif collision_count > 0:
        failure_reason = "robot_separation_violation"
    elif min_clearance is not None and min_clearance < clearance_limit:
        failure_reason = "obstacle_clearance_violation"
    else:
        failure_reason = "acceptance_check_failed"

    metrics = {
        "success": success,
        "localization_error_m": localization_error,
        "formation_error_m": formation_error,
        "robot_collision_count": collision_count,
        "minimum_robot_separation_m": min_separation,
        "minimum_obstacle_clearance_m": min_clearance,
        "path_length_total_m": path_length,
        "simulation_duration_s": final_frame.time_s,
        "wall_clock_ms": wall_clock_ms,
        "safety_intervention_count": len(interventions),
        "controller_iteration_count": max(0, len(frames) - 1),
        "termination_reason": termination_reason,
        "obstacle_event_count": len(world_events),
        "final_estimate_confidence": final_estimate.confidence,
        "final_estimate_valid": final_estimate.valid,
    }

    return EvaluationResult(
        success=success,
        failure_reason=failure_reason,
        metrics=metrics,
        checks=checks,
        ground_truth={
            "x": truth_x,
            "y": truth_y,
            "revealed": "after_run_only",
        },
        final_estimate={
            "x": final_estimate.x,
            "y": final_estimate.y,
            "confidence": final_estimate.confidence,
            "samples": final_estimate.samples,
            "valid": final_estimate.valid,
            "residual": final_estimate.residual,
            "curvature": final_estimate.curvature,
            "note": final_estimate.note,
        },
    )
