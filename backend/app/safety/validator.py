"""Independent safety filter and post-step validator.

The controller proposes commands. This module decides whether a transition is
admissible. It has no import from the controller or the model provider.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app import limits
from app.schemas import MissionSpec
from app.simulation.dynamics import integrate_state
from app.simulation.geometry import Region, Vec2, swept_region_clearance
from app.simulation.types import RobotCommand, RobotState, SafetyIntervention


@dataclass(frozen=True)
class ValidationIssue:
    kind: str
    robot_id: int | None
    detail: str
    related_robot_id: int | None = None

    def to_public(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "robot_id": self.robot_id,
            "related_robot_id": self.related_robot_id,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class FilterResult:
    commands: tuple[RobotCommand, ...]
    scale: float
    interventions: tuple[SafetyIntervention, ...]
    issues: tuple[ValidationIssue, ...]


def _active_regions(regions: tuple[Region, ...], time_s: float) -> tuple[Region, ...]:
    return tuple(region for region in regions if region.active_from_s <= time_s + 1e-9)


def validate_state(
    states: tuple[RobotState, ...] | list[RobotState],
    mission: MissionSpec,
    width: float,
    height: float,
    regions: tuple[Region, ...],
    time_s: float,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    margin = limits.BOUNDARY_MARGIN_M
    separation = mission.constraints.minimum_robot_separation
    clearance = mission.constraints.minimum_obstacle_clearance
    active = _active_regions(regions, time_s)

    for state in states:
        if not all(math.isfinite(value) for value in (state.x, state.y, state.heading)):
            issues.append(
                ValidationIssue("non_finite_state", state.robot_id, "state is not finite")
            )
            continue
        if not (margin <= state.x <= width - margin and margin <= state.y <= height - margin):
            issues.append(
                ValidationIssue(
                    "arena_boundary",
                    state.robot_id,
                    f"position ({state.x:.3f}, {state.y:.3f}) is outside the arena margin",
                )
            )
        for region in active:
            gap = region.clearance(Vec2(state.x, state.y))
            if gap < clearance - limits.NUMERIC_EPSILON:
                issues.append(
                    ValidationIssue(
                        "obstacle_clearance",
                        state.robot_id,
                        f"clearance {gap:.3f} m to {region.id} is below {clearance:.3f} m",
                    )
                )

    for left_index, left in enumerate(states):
        for right in states[left_index + 1 :]:
            distance = math.hypot(left.x - right.x, left.y - right.y)
            if distance < separation - limits.NUMERIC_EPSILON:
                issues.append(
                    ValidationIssue(
                        "robot_separation",
                        left.robot_id,
                        f"separation {distance:.3f} m to robot {right.robot_id} is below "
                        f"{separation:.3f} m",
                        related_robot_id=right.robot_id,
                    )
                )
    return issues


def validate_transition(
    previous: tuple[RobotState, ...] | list[RobotState],
    current: tuple[RobotState, ...] | list[RobotState],
    mission: MissionSpec,
    width: float,
    height: float,
    regions: tuple[Region, ...],
    time_s: float,
    dt: float,
) -> list[ValidationIssue]:
    issues = validate_state(current, mission, width, height, regions, time_s)
    if len(previous) != len(current):
        issues.append(
            ValidationIssue("invalid_transition", None, "robot count changed during a step")
        )
        return issues
    max_speed = mission.constraints.maximum_speed
    for before, after in zip(previous, current, strict=True):
        if before.robot_id != after.robot_id:
            issues.append(
                ValidationIssue("invalid_transition", None, "robot identity changed during a step")
            )
            continue
        if not all(
            math.isfinite(value)
            for value in (before.x, before.y, after.x, after.y, before.heading, after.heading)
        ):
            continue
        distance = math.hypot(after.x - before.x, after.y - before.y)
        speed = distance / dt if dt > 0 else math.inf
        if speed > max_speed + limits.SPEED_TOLERANCE_MPS:
            issues.append(
                ValidationIssue(
                    "speed_limit",
                    after.robot_id,
                    f"instantaneous speed {speed:.3f} m/s exceeds {max_speed:.3f} m/s",
                )
            )
        if dt > 0 and math.isfinite(dt):
            for region in _active_regions(regions, time_s):
                fraction = max(0.0, min(1.0, (region.active_from_s - (time_s - dt)) / dt))
                start = Vec2(
                    before.x + fraction * (after.x - before.x),
                    before.y + fraction * (after.y - before.y),
                )
                end = Vec2(after.x, after.y)
                gap = swept_region_clearance(region, start, end)
                clearance = mission.constraints.minimum_obstacle_clearance
                if (
                    gap < clearance - limits.NUMERIC_EPSILON
                    and region.clearance(end) >= clearance - limits.NUMERIC_EPSILON
                ):
                    issues.append(
                        ValidationIssue(
                            "obstacle_clearance",
                            after.robot_id,
                            f"swept clearance {gap:.3f} m to {region.id} "
                            f"is below {clearance:.3f} m",
                        )
                    )
    for index, (left_before, left_after) in enumerate(zip(previous, current, strict=True)):
        for right_before, right_after in zip(
            previous[index + 1 :], current[index + 1 :], strict=True
        ):
            values = (
                left_before.x,
                left_before.y,
                left_after.x,
                left_after.y,
                right_before.x,
                right_before.y,
                right_after.x,
                right_after.y,
            )
            if not all(math.isfinite(value) for value in values):
                continue
            dx = left_before.x - right_before.x
            dy = left_before.y - right_before.y
            vx = (left_after.x - left_before.x) - (right_after.x - right_before.x)
            vy = (left_after.y - left_before.y) - (right_after.y - right_before.y)
            motion_sq = vx * vx + vy * vy
            t = max(0.0, min(1.0, -(dx * vx + dy * vy) / motion_sq)) if motion_sq else 0.0
            distance = math.hypot(dx + t * vx, dy + t * vy)
            end_distance = math.hypot(left_after.x - right_after.x, left_after.y - right_after.y)
            separation = mission.constraints.minimum_robot_separation
            if (
                distance < separation - limits.NUMERIC_EPSILON
                and end_distance >= separation - limits.NUMERIC_EPSILON
            ):
                issues.append(
                    ValidationIssue(
                        "robot_separation",
                        left_after.robot_id,
                        f"swept separation {distance:.3f} m to robot {right_after.robot_id} "
                        f"is below {separation:.3f} m",
                        related_robot_id=right_after.robot_id,
                    )
                )
    return issues


class SafetyFilter:
    def __init__(self) -> None:
        self._next_scale = {1.0: 0.6, 0.6: 0.3, 0.3: 0.0, 0.0: 0.0}

    def apply(
        self,
        states: tuple[RobotState, ...],
        commands: tuple[RobotCommand, ...],
        mission: MissionSpec,
        width: float,
        height: float,
        regions: tuple[Region, ...],
        time_s: float,
        step: int,
        dt: float,
    ) -> FilterResult:
        if len(states) != len(commands):
            raise ValueError("state and command counts must match")
        current_issues = validate_state(states, mission, width, height, regions, time_s)
        if current_issues:
            zero = tuple(RobotCommand(0.0, 0.0) for _ in states)
            interventions = (
                SafetyIntervention(
                    step=step,
                    time_s=time_s,
                    kind="unsafe_current_state",
                    robot_id=None,
                    detail="current state violates constraints; holding position",
                ),
            )
            return FilterResult(zero, 0.0, interventions, tuple(current_issues))

        speed_limit = mission.constraints.maximum_speed
        scales = {state.robot_id: 1.0 for state in states}
        last_issues: tuple[ValidationIssue, ...] = ()
        for _ in range(max(4, len(states) + 2)):
            scaled = tuple(
                _scale_command(command, speed_limit * scales[state.robot_id])
                for state, command in zip(states, commands, strict=True)
            )
            proposed = tuple(
                integrate_state(state, command, dt)
                for state, command in zip(states, scaled, strict=True)
            )
            issues = validate_transition(
                states,
                proposed,
                mission,
                width,
                height,
                regions,
                time_s + dt,
                dt,
            )
            if not issues:
                interventions: tuple[SafetyIntervention, ...] = ()
                affected = sorted(robot_id for robot_id, scale in scales.items() if scale < 1.0)
                if affected:
                    kinds = {scales[robot_id] for robot_id in affected}
                    interventions = (
                        SafetyIntervention(
                            step=step,
                            time_s=time_s,
                            kind="safe_stop" if kinds == {0.0} else "velocity_scaled",
                            robot_id=affected[0] if len(affected) == 1 else None,
                            detail=(
                                "per-robot velocity scaling applied to robots "
                                + ", ".join(str(robot_id) for robot_id in affected)
                            ),
                        ),
                    )
                return FilterResult(
                    scaled,
                    min(scales.values()),
                    interventions,
                    (),
                )
            last_issues = tuple(issues)
            affected_ids: set[int] = set()
            for issue in issues:
                if issue.robot_id is None:
                    affected_ids.update(scales)
                else:
                    affected_ids.add(issue.robot_id)
                if issue.related_robot_id is not None:
                    affected_ids.add(issue.related_robot_id)
            for robot_id in affected_ids:
                scales[robot_id] = self._next_scale[scales[robot_id]]
            if all(scale == 0.0 for scale in scales.values()):
                zero = tuple(RobotCommand(0.0, 0.0) for _ in states)
                return FilterResult(
                    zero,
                    0.0,
                    (
                        SafetyIntervention(
                            step=step,
                            time_s=time_s,
                            kind="safe_stop",
                            robot_id=None,
                            detail="no admissible velocity; conservative stop applied",
                        ),
                    ),
                    last_issues,
                )

        zero = tuple(RobotCommand(0.0, 0.0) for _ in states)
        return FilterResult(
            zero,
            0.0,
            (
                SafetyIntervention(
                    step=step,
                    time_s=time_s,
                    kind="safe_stop",
                    robot_id=None,
                    detail="safety filter iteration limit reached; conservative stop applied",
                ),
            ),
            last_issues,
        )


def _scale_command(command: RobotCommand, limit: float) -> RobotCommand:
    speed = command.speed()
    if speed <= limit or speed <= limits.NUMERIC_EPSILON:
        return command
    factor = limit / speed
    return RobotCommand(vx=command.vx * factor, vy=command.vy * factor)
