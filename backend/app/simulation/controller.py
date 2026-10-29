"""Deterministic formation and source-seeking controller.

The controller receives only team poses and scalar measurements. It never sees
ground-truth source coordinates and never calls a model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app import limits
from app.schemas import MissionSpec
from app.simulation.estimator import QuadraticSourceEstimator, WeightedCentroidEstimator
from app.simulation.geometry import RectRegion, Region, Vec2
from app.simulation.types import (
    RobotCommand,
    RobotObservation,
    SourceEstimate,
    TeamObservation,
)


@dataclass
class DetourState:
    routes: dict[int, tuple[Vec2, ...]]
    cumulative: dict[int, tuple[float, ...]]
    lengths: dict[int, float]
    progress: dict[int, float]
    start_time_s: float
    end_time_s: float
    lead: float = 0.4
    settle_tolerance: float = 0.35
    active: bool = True


class FormationController:
    def __init__(
        self,
        mission: MissionSpec,
        arena_width: float,
        arena_height: float,
        estimator_kind: str = "quadratic",
        dt: float = limits.DT_S,
    ) -> None:
        if estimator_kind not in {"quadratic", "weighted_centroid"}:
            raise ValueError(f"unsupported estimator: {estimator_kind}")
        self.mission = mission
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.dt = dt
        self.estimator_kind = estimator_kind
        if estimator_kind == "quadratic":
            self.estimator = QuadraticSourceEstimator(arena_width, arena_height)
        else:
            self.estimator = WeightedCentroidEstimator(arena_width, arena_height)
        self.estimate: SourceEstimate = self.estimator.prior
        self.formation_error_estimate = math.inf
        self.cautious = False
        self.detour: DetourState | None = None
        self.last_commands: tuple[RobotCommand, ...] = ()
        self._estimate_history: list[tuple[float, SourceEstimate]] = []
        self._formation_history: list[tuple[float, float]] = []
        self._slot_ranks: dict[int, int] | None = None
        self._slot_base_angle = math.pi

    @property
    def name(self) -> str:
        if self.estimator_kind == "weighted_centroid":
            return "baseline_weighted_centroid"
        return "fieldweaver_quadratic_ring"

    def update(self, observation: TeamObservation) -> None:
        self.estimator.add_observations(observation)
        self.estimate = self.estimator.estimate()
        self.formation_error_estimate = self._formation_error(observation)
        self._estimate_history.append((observation.time_s, self.estimate))
        self._formation_history.append((observation.time_s, self.formation_error_estimate))
        if len(self._estimate_history) > 400:
            self._estimate_history = self._estimate_history[-400:]
        if len(self._formation_history) > 400:
            self._formation_history = self._formation_history[-400:]

    def _formation_error(self, observation: TeamObservation) -> float:
        radius = self.mission.formation.radius
        if not self.estimate.valid:
            return math.inf
        squared = [
            (math.hypot(robot.x - self.estimate.x, robot.y - self.estimate.y) - radius) ** 2
            for robot in observation.robots
        ]
        return math.sqrt(sum(squared) / len(squared))

    def estimate_stable(self, window_s: float) -> bool:
        if not self.estimate.valid or not self._estimate_history:
            return False
        cutoff = self._estimate_history[-1][0] - window_s
        recent = [item for item in self._estimate_history if item[0] >= cutoff]
        if len(recent) < 2:
            return False
        first = recent[0][1]
        return all(
            math.hypot(item[1].x - first.x, item[1].y - first.y) <= limits.ESTIMATE_STABILITY_EPS_M
            for item in recent
        )

    def formation_settled(self, window_s: float, threshold: float) -> bool:
        if not self._formation_history:
            return False
        cutoff = self._formation_history[-1][0] - window_s
        recent = [item for item in self._formation_history if item[0] >= cutoff]
        return len(recent) >= 2 and all(
            error <= threshold for _, error in recent
        )

    def set_cautious(self) -> None:
        self.cautious = True

    def set_detour(
        self,
        routes: dict[int, tuple[Vec2, ...]],
        now_s: float,
        max_duration_s: float = 45.0,
    ) -> None:
        if not routes:
            raise ValueError("detour requires at least one route")
        cumulative: dict[int, tuple[float, ...]] = {}
        lengths: dict[int, float] = {}
        for robot_id, route in routes.items():
            if len(route) < 2:
                raise ValueError(f"detour route for robot {robot_id} needs two points")
            values = [0.0]
            for index in range(1, len(route)):
                values.append(values[-1] + route[index - 1].distance_to(route[index]))
            if values[-1] <= 1e-6:
                raise ValueError(f"detour route for robot {robot_id} has zero length")
            cumulative[robot_id] = tuple(values)
            lengths[robot_id] = values[-1]
        self.detour = DetourState(
            routes=dict(routes),
            cumulative=cumulative,
            lengths=lengths,
            progress={robot_id: 0.0 for robot_id in routes},
            start_time_s=now_s,
            end_time_s=now_s + max_duration_s,
            active=True,
        )

    def cancel_detour(self) -> None:
        self.detour = None

    def ring_slot_targets(
        self,
        positions: dict[int, Vec2],
        center_x: float,
        center_y: float,
        radius: float | None = None,
    ) -> dict[int, Vec2]:
        """Deterministic ring slots shared by ring control and detour planning."""

        if not positions:
            return {}
        if radius is None:
            radius = self.mission.formation.radius
        ordered = sorted(
            positions.items(),
            key=lambda item: (
                math.atan2(item[1].y - center_y, item[1].x - center_x),
                item[0],
            ),
        )
        if self.estimate.valid and self._slot_ranks is None:
            self._slot_ranks = {
                robot_id: rank for rank, (robot_id, _) in enumerate(ordered)
            }
            self._slot_base_angle = math.atan2(
                ordered[0][1].y - center_y,
                ordered[0][1].x - center_x,
            )
        count = max(1, len(ordered))
        targets: dict[int, Vec2] = {}
        for fallback_rank, (robot_id, _) in enumerate(ordered):
            rank = (
                self._slot_ranks.get(robot_id, fallback_rank)
                if self._slot_ranks is not None
                else fallback_rank
            )
            angle = self._slot_base_angle + 2.0 * math.pi * rank / count
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            x = min(max(x, limits.BOUNDARY_MARGIN_M), self.arena_width - limits.BOUNDARY_MARGIN_M)
            y = min(max(y, limits.BOUNDARY_MARGIN_M), self.arena_height - limits.BOUNDARY_MARGIN_M)
            targets[robot_id] = Vec2(x, y)
        return targets

    @staticmethod
    def _point_at_route(
        route: tuple[Vec2, ...],
        cumulative: tuple[float, ...],
        distance: float,
    ) -> Vec2:
        if distance <= 0.0:
            return route[0]
        if distance >= cumulative[-1]:
            return route[-1]
        for index in range(1, len(cumulative)):
            if cumulative[index] >= distance:
                segment_start = cumulative[index - 1]
                segment_length = cumulative[index] - segment_start
                ratio = 0.0 if segment_length <= 0 else (distance - segment_start) / segment_length
                start = route[index - 1]
                end = route[index]
                return Vec2(
                    start.x + (end.x - start.x) * ratio,
                    start.y + (end.y - start.y) * ratio,
                )
        return route[-1]

    def _speed_limit(self) -> float:
        speed = self.mission.constraints.maximum_speed
        return speed * 0.6 if self.cautious else speed

    def propose(
        self,
        observation: TeamObservation,
        active_regions: tuple[Region, ...],
        time_s: float,
    ) -> tuple[RobotCommand, ...]:
        speed_limit = self._speed_limit()
        if self.detour is not None and self.detour.active:
            commands = self._propose_detour(observation, active_regions, time_s, speed_limit)
            self.last_commands = commands
            return commands
        commands = self._propose_ring(observation, speed_limit)
        self.last_commands = commands
        return commands

    def _obstacle_repulsion(
        self,
        robot: RobotObservation,
        regions: tuple[Region, ...],
    ) -> tuple[float, float]:
        threshold = self.mission.constraints.minimum_obstacle_clearance + 0.4
        push_x = 0.0
        push_y = 0.0
        for region in regions:
            if isinstance(region, RectRegion):
                nearest_x = min(max(robot.x, region.x_min), region.x_max)
                nearest_y = min(max(robot.y, region.y_min), region.y_max)
            else:
                center_distance = math.hypot(robot.x - region.center.x, robot.y - region.center.y)
                if center_distance <= 1e-9:
                    nearest_x = region.center.x + region.radius
                    nearest_y = region.center.y
                else:
                    scale = region.radius / center_distance
                    nearest_x = region.center.x + (robot.x - region.center.x) * scale
                    nearest_y = region.center.y + (robot.y - region.center.y) * scale
            offset_x = robot.x - nearest_x
            offset_y = robot.y - nearest_y
            distance = math.hypot(offset_x, offset_y)
            clearance = region.clearance(Vec2(robot.x, robot.y))
            if clearance >= threshold:
                continue
            strength = (threshold - clearance) * 2.0
            if distance <= 1e-9:
                push_x += strength
                continue
            push_x += strength * offset_x / distance
            push_y += strength * offset_y / distance
        return push_x, push_y

    def _segment_is_clear(
        self,
        start: Vec2,
        end: Vec2,
        regions: tuple[Region, ...],
        clearance: float,
    ) -> bool:
        return all(
            region.segment_clearance(start, end) >= clearance - 1e-9 for region in regions
        )

    def _visible_target(
        self,
        route: tuple[Vec2, ...],
        robot: RobotObservation,
        preferred: Vec2,
        regions: tuple[Region, ...],
    ) -> Vec2:
        start = Vec2(robot.x, robot.y)
        clearance = self.mission.constraints.minimum_obstacle_clearance + 0.03
        if self._segment_is_clear(start, preferred, regions, clearance):
            return preferred
        for vertex in sorted(route, key=lambda point: point.distance_to(start)):
            if self._segment_is_clear(start, vertex, regions, clearance):
                return vertex
        return preferred

    @staticmethod
    def _advance_route_progress(
        route: tuple[Vec2, ...],
        cumulative: tuple[float, ...],
        point: Vec2,
        progress: float,
        window: float = 1.5,
    ) -> float:
        best = progress
        best_distance = math.inf
        limit = progress + window
        for index in range(1, len(cumulative)):
            segment_start = cumulative[index - 1]
            segment_end = cumulative[index]
            if segment_end < progress:
                continue
            if segment_start > limit:
                break
            start = route[index - 1]
            end = route[index]
            segment_x = end.x - start.x
            segment_y = end.y - start.y
            length_sq = segment_x * segment_x + segment_y * segment_y
            if length_sq <= 1e-12:
                continue
            ratio = (
                (point.x - start.x) * segment_x + (point.y - start.y) * segment_y
            ) / length_sq
            ratio = min(1.0, max(0.0, ratio))
            closest = Vec2(start.x + segment_x * ratio, start.y + segment_y * ratio)
            distance = point.distance_to(closest)
            candidate = segment_start + ratio * (segment_end - segment_start)
            candidate = max(progress, candidate)
            if candidate > limit:
                continue
            if distance < best_distance - 1e-9:
                best_distance = distance
                best = candidate
        return best

    def _propose_detour(
        self,
        observation: TeamObservation,
        active_regions: tuple[Region, ...],
        time_s: float,
        speed_limit: float,
    ) -> tuple[RobotCommand, ...]:
        assert self.detour is not None
        detour = self.detour
        if time_s >= detour.end_time_s:
            detour.active = False
            self.detour = None
            return self._propose_ring(observation, speed_limit)

        commands: list[RobotCommand] = []
        settled = True
        separation = self.mission.constraints.minimum_robot_separation
        repulsion_margin = separation + (0.65 if self.cautious else 0.55)
        for robot in observation.robots:
            route = detour.routes.get(robot.robot_id)
            if route is None:
                settled = False
                commands.append(_clamp_command(0.0, 0.0, speed_limit))
                continue
            cumulative = detour.cumulative[robot.robot_id]
            length = detour.lengths[robot.robot_id]
            position = Vec2(robot.x, robot.y)
            progress = self._advance_route_progress(
                route,
                cumulative,
                position,
                detour.progress.get(robot.robot_id, 0.0),
            )
            detour.progress[robot.robot_id] = progress
            target_distance = min(length, progress + detour.lead)
            preferred = self._point_at_route(route, cumulative, target_distance)
            target = self._visible_target(route, robot, preferred, active_regions)
            dx = target.x - robot.x
            dy = target.y - robot.y
            if (
                math.hypot(dx, dy) > detour.settle_tolerance
                or progress < length - detour.settle_tolerance
            ):
                settled = False
            vx = limits.FORMATION_GAIN * dx
            vy = limits.FORMATION_GAIN * dy
            for other in observation.robots:
                if other.robot_id == robot.robot_id:
                    continue
                offset_x = robot.x - other.x
                offset_y = robot.y - other.y
                distance = math.hypot(offset_x, offset_y)
                if 1e-9 < distance < repulsion_margin:
                    strength = (repulsion_margin - distance) * 1.8
                    vx += strength * offset_x / distance
                    vy += strength * offset_y / distance
                    vx += 0.5 * strength * (-offset_y / distance)
                    vy += 0.5 * strength * (offset_x / distance)
            push_x, push_y = self._obstacle_repulsion(robot, active_regions)
            commands.append(_clamp_command(vx + push_x, vy + push_y, speed_limit))
        if settled:
            detour.active = False
            self.detour = None
        return tuple(commands)

    def _propose_ring(
        self,
        observation: TeamObservation,
        speed_limit: float,
    ) -> tuple[RobotCommand, ...]:
        radius = self.mission.formation.radius
        if self.estimate.valid:
            center_x = self.estimate.x
            center_y = self.estimate.y
        else:
            center_x = self.arena_width / 2.0
            center_y = self.arena_height / 2.0

        centroid_x = sum(robot.x for robot in observation.robots) / len(observation.robots)
        centroid_y = sum(robot.y for robot in observation.robots) / len(observation.robots)
        distance_to_center = math.hypot(centroid_x - center_x, centroid_y - center_y)

        if self.estimate.valid and distance_to_center > radius + 1.1:
            desired_points = self._travel_targets(
                observation, center_x, center_y, distance_to_center
            )
        else:
            desired_points = self._ring_targets(observation, center_x, center_y, radius)

        separation = self.mission.constraints.minimum_robot_separation
        repulsion_margin = separation + (0.65 if self.cautious else 0.55)
        commands: list[RobotCommand] = []
        for robot in observation.robots:
            desired_x, desired_y = desired_points[robot.robot_id]
            vx = limits.FORMATION_GAIN * (desired_x - robot.x)
            vy = limits.FORMATION_GAIN * (desired_y - robot.y)
            for other in observation.robots:
                if other.robot_id == robot.robot_id:
                    continue
                dx = robot.x - other.x
                dy = robot.y - other.y
                distance = math.hypot(dx, dy)
                if 1e-9 < distance < repulsion_margin:
                    strength = (repulsion_margin - distance) * 1.8
                    vx += strength * dx / distance
                    vy += strength * dy / distance
                    vx += 0.9 * strength * (-dy / distance)
                    vy += 0.9 * strength * (dx / distance)
            if math.hypot(vx, vy) < 1e-3:
                vx = 0.0
                vy = 0.0
            commands.append(_clamp_command(vx, vy, speed_limit))
        return tuple(commands)

    def _travel_targets(
        self,
        observation: TeamObservation,
        center_x: float,
        center_y: float,
        distance_to_center: float,
    ) -> dict[int, tuple[float, float]]:
        count = self.mission.robot_count
        rows = math.ceil(count / 2)
        separation = self.mission.constraints.minimum_robot_separation
        column_spacing = max(0.9, separation + 0.4)
        row_spacing = max(1.0, separation + 0.5)
        centroid_x = sum(robot.x for robot in observation.robots) / len(observation.robots)
        centroid_y = sum(robot.y for robot in observation.robots) / len(observation.robots)
        unit_x = (center_x - centroid_x) / distance_to_center
        unit_y = (center_y - centroid_y) / distance_to_center
        staging_distance = self.mission.formation.radius + 0.8
        group_x = center_x - unit_x * staging_distance
        group_y = center_y - unit_y * staging_distance
        perpendicular_x = -unit_y
        perpendicular_y = unit_x
        targets: dict[int, tuple[float, float]] = {}
        for robot in observation.robots:
            column = robot.robot_id % 2
            row = robot.robot_id // 2
            forward_offset = (column - 0.5) * column_spacing
            lateral_offset = (row - (rows - 1) / 2.0) * row_spacing
            x = group_x + unit_x * forward_offset + perpendicular_x * lateral_offset
            y = group_y + unit_y * forward_offset + perpendicular_y * lateral_offset
            x = min(max(x, limits.BOUNDARY_MARGIN_M), self.arena_width - limits.BOUNDARY_MARGIN_M)
            y = min(max(y, limits.BOUNDARY_MARGIN_M), self.arena_height - limits.BOUNDARY_MARGIN_M)
            targets[robot.robot_id] = (x, y)
        return targets

    def _ring_targets(
        self,
        observation: TeamObservation,
        center_x: float,
        center_y: float,
        radius: float,
    ) -> dict[int, tuple[float, float]]:
        positions = {
            robot.robot_id: Vec2(robot.x, robot.y) for robot in observation.robots
        }
        goals = self.ring_slot_targets(positions, center_x, center_y, radius)
        return {robot_id: (point.x, point.y) for robot_id, point in goals.items()}


def _clamp_command(vx: float, vy: float, speed_limit: float) -> RobotCommand:
    speed = math.hypot(vx, vy)
    if speed <= speed_limit or speed <= 1e-12:
        return RobotCommand(vx=vx, vy=vy)
    scale = speed_limit / speed
    return RobotCommand(vx=vx * scale, vy=vy * scale)


def observation_from_states(
    states: tuple[RobotObservation, ...] | list[RobotObservation],
    step: int,
    time_s: float,
) -> TeamObservation:
    return TeamObservation(step=step, time_s=time_s, robots=tuple(states))
