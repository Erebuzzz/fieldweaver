"""Deterministic grid planner used only by the approved detour action.

The model never produces a route. It selects a supported action enum; the
application computes a path through inflated public obstacle geometry, then the
safety layer validates the resulting waypoints and motion.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass

from app.simulation.geometry import Region, Vec2


@dataclass(frozen=True)
class PlanResult:
    path: tuple[Vec2, ...]
    expanded_nodes: int
    reason: str


def _cell_free(
    point: Vec2,
    width: float,
    height: float,
    margin: float,
    regions: tuple[Region, ...],
    clearance: float,
) -> bool:
    if not (margin <= point.x <= width - margin and margin <= point.y <= height - margin):
        return False
    return all(region.clearance(point) >= clearance for region in regions)


def _nearest_free_cell(
    origin: Vec2,
    width: float,
    height: float,
    margin: float,
    cell_size: float,
    regions: tuple[Region, ...],
    clearance: float,
    max_radius_cells: int = 20,
) -> tuple[int, int] | None:
    origin_ix = round((origin.x - margin) / cell_size)
    origin_iy = round((origin.y - margin) / cell_size)
    max_ix = int(math.floor((width - 2 * margin) / cell_size))
    max_iy = int(math.floor((height - 2 * margin) / cell_size))
    for radius in range(max_radius_cells + 1):
        candidates: list[tuple[float, int, int]] = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if max(abs(dx), abs(dy)) != radius:
                    continue
                ix = origin_ix + dx
                iy = origin_iy + dy
                if ix < 0 or iy < 0 or ix > max_ix or iy > max_iy:
                    continue
                point = Vec2(margin + ix * cell_size, margin + iy * cell_size)
                if _cell_free(point, width, height, margin, regions, clearance):
                    candidates.append((point.distance_to(origin), ix, iy))
        if candidates:
            candidates.sort()
            return candidates[0][1], candidates[0][2]
    return None


def _line_clear(
    start: Vec2,
    end: Vec2,
    regions: tuple[Region, ...],
    clearance: float,
) -> bool:
    return all(region.segment_clearance(start, end) >= clearance for region in regions)


def _simplify(
    path: list[Vec2],
    regions: tuple[Region, ...],
    clearance: float,
) -> list[Vec2]:
    if len(path) <= 2:
        return path
    simplified = [path[0]]
    index = 0
    while index < len(path) - 1:
        next_index = len(path) - 1
        while next_index > index + 1 and not _line_clear(
            path[index], path[next_index], regions, clearance
        ):
            next_index -= 1
        simplified.append(path[next_index])
        index = next_index
    return simplified


def plan_detour_path(
    start: Vec2,
    goal: Vec2,
    width: float,
    height: float,
    regions: tuple[Region, ...],
    clearance: float,
    margin: float = 0.12,
    cell_size: float = 0.25,
) -> PlanResult:
    if not all(math.isfinite(value) for value in (start.x, start.y, goal.x, goal.y)):
        return PlanResult((), 0, "non-finite start or goal")

    active_regions = tuple(region for region in regions if region.active_from_s <= 1e9)
    start_cell = _nearest_free_cell(
        start, width, height, margin, cell_size, active_regions, clearance
    )
    goal_cell = _nearest_free_cell(
        goal, width, height, margin, cell_size, active_regions, clearance
    )
    if start_cell is None:
        return PlanResult((), 0, "no free cell near start")
    if goal_cell is None:
        return PlanResult((), 0, "no free cell near goal")

    max_ix = int(math.floor((width - 2 * margin) / cell_size))
    max_iy = int(math.floor((height - 2 * margin) / cell_size))
    start_node = (start_cell[0], start_cell[1])
    goal_node = (goal_cell[0], goal_cell[1])
    if start_node == goal_node:
        point = Vec2(margin + start_node[0] * cell_size, margin + start_node[1] * cell_size)
        return PlanResult((point,), 0, "already at goal cell")

    open_heap: list[tuple[float, int, tuple[int, int]]] = []
    counter = 0
    heapq.heappush(open_heap, (0.0, counter, start_node))
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    cost_so_far: dict[tuple[int, int], float] = {start_node: 0.0}
    expanded = 0

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        expanded += 1
        if current == goal_node:
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (current[0] + dx, current[1] + dy)
            if neighbor[0] < 0 or neighbor[1] < 0 or neighbor[0] > max_ix or neighbor[1] > max_iy:
                continue
            point = Vec2(
                margin + neighbor[0] * cell_size,
                margin + neighbor[1] * cell_size,
            )
            if not _cell_free(
                point, width, height, margin, active_regions, clearance
            ):
                continue
            new_cost = cost_so_far[current] + 1.0
            if neighbor in cost_so_far and new_cost >= cost_so_far[neighbor]:
                continue
            cost_so_far[neighbor] = new_cost
            heuristic = abs(neighbor[0] - goal_node[0]) + abs(neighbor[1] - goal_node[1])
            counter += 1
            heapq.heappush(open_heap, (new_cost + heuristic, counter, neighbor))
            came_from[neighbor] = current

    if goal_node not in came_from and goal_node != start_node:
        return PlanResult((), expanded, "no route through inflated obstacles")

    nodes = [goal_node]
    while nodes[-1] != start_node:
        nodes.append(came_from[nodes[-1]])
    nodes.reverse()
    points = [
        Vec2(margin + node[0] * cell_size, margin + node[1] * cell_size) for node in nodes
    ]
    if _cell_free(start, width, height, margin, active_regions, clearance):
        points[0] = start
    if _cell_free(goal, width, height, margin, active_regions, clearance):
        points[-1] = goal
    simplified = _simplify(points, active_regions, clearance)
    if not all(
        _line_clear(simplified[index], simplified[index + 1], active_regions, clearance)
        for index in range(len(simplified) - 1)
    ):
        return PlanResult((), expanded, "simplified path failed clearance check")
    return PlanResult(tuple(simplified), expanded, "ok")


def validate_path(
    path: tuple[Vec2, ...],
    width: float,
    height: float,
    regions: tuple[Region, ...],
    clearance: float,
    margin: float = 0.12,
) -> str | None:
    if not path:
        return "empty path"
    for point in path:
        if not (math.isfinite(point.x) and math.isfinite(point.y)):
            return "non-finite path point"
        if not (margin <= point.x <= width - margin and margin <= point.y <= height - margin):
            return "path leaves arena"
        if any(region.clearance(point) < clearance for region in regions):
            return "path point violates clearance"
    for index in range(len(path) - 1):
        if any(
            region.segment_clearance(path[index], path[index + 1]) < clearance
            for region in regions
        ):
            return "path segment violates clearance"
    return None
