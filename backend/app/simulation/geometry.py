"""2D geometry used by the simulator, planner, and safety validator.

All coordinates are metres in a right-handed x/y plane with the arena origin at
the lower-left corner. Regions are axis-aligned rectangles or circles.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum


class RegionKind(StrEnum):
    OBSTACLE = "obstacle"
    RESTRICTED = "restricted"


@dataclass(frozen=True)
class Vec2:
    x: float
    y: float

    def distance_to(self, other: Vec2) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


@dataclass(frozen=True)
class RectRegion:
    id: str
    kind: RegionKind
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    active_from_s: float = 0.0
    label: str = ""

    def __post_init__(self) -> None:
        values = (self.x_min, self.y_min, self.x_max, self.y_max, self.active_from_s)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("rectangle coordinates must be finite")
        if self.x_max <= self.x_min or self.y_max <= self.y_min:
            raise ValueError("rectangle requires x_max > x_min and y_max > y_min")
        if self.active_from_s < 0:
            raise ValueError("active_from_s must be non-negative")

    def contains(self, point: Vec2, margin: float = 0.0) -> bool:
        return (
            self.x_min - margin <= point.x <= self.x_max + margin
            and self.y_min - margin <= point.y <= self.y_max + margin
        )

    def clearance(self, point: Vec2) -> float:
        dx = max(self.x_min - point.x, 0.0, point.x - self.x_max)
        dy = max(self.y_min - point.y, 0.0, point.y - self.y_max)
        return math.hypot(dx, dy)

    def segment_clearance(self, start: Vec2, end: Vec2) -> float:
        """Approximate minimum clearance along a segment by dense sampling."""

        length = start.distance_to(end)
        samples = max(2, int(math.ceil(length / 0.05)) + 1)
        return min(
            self.clearance(
                Vec2(
                    start.x + (end.x - start.x) * (index / (samples - 1)),
                    start.y + (end.y - start.y) * (index / (samples - 1)),
                )
            )
            for index in range(samples)
        )


@dataclass(frozen=True)
class CircleRegion:
    id: str
    kind: RegionKind
    center: Vec2
    radius: float
    active_from_s: float = 0.0
    label: str = ""

    def __post_init__(self) -> None:
        if not all(
            math.isfinite(value)
            for value in (self.center.x, self.center.y, self.radius, self.active_from_s)
        ):
            raise ValueError("circle geometry must be finite")
        if self.radius <= 0:
            raise ValueError("circle radius must be positive")
        if self.active_from_s < 0:
            raise ValueError("active_from_s must be non-negative")

    def contains(self, point: Vec2, margin: float = 0.0) -> bool:
        return self.center.distance_to(point) <= self.radius + margin

    def clearance(self, point: Vec2) -> float:
        return max(0.0, self.center.distance_to(point) - self.radius)

    def segment_clearance(self, start: Vec2, end: Vec2) -> float:
        length = start.distance_to(end)
        samples = max(2, int(math.ceil(length / 0.05)) + 1)
        return min(
            self.clearance(
                Vec2(
                    start.x + (end.x - start.x) * (index / (samples - 1)),
                    start.y + (end.y - start.y) * (index / (samples - 1)),
                )
            )
            for index in range(samples)
        )


Region = RectRegion | CircleRegion


def region_clearance(region: Region, point: Vec2) -> float:
    return region.clearance(point)


def point_to_segment_distance(point: Vec2, start: Vec2, end: Vec2) -> float:
    dx = end.x - start.x
    dy = end.y - start.y
    if dx == 0.0 and dy == 0.0:
        return point.distance_to(start)
    t = ((point.x - start.x) * dx + (point.y - start.y) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return point.distance_to(Vec2(start.x + t * dx, start.y + t * dy))


def swept_region_clearance(region: Region, start: Vec2, end: Vec2) -> float:
    if isinstance(region, CircleRegion):
        return max(0.0, point_to_segment_distance(region.center, start, end) - region.radius)

    low, high = 0.0, 1.0
    for origin, delta, minimum, maximum in (
        (start.x, end.x - start.x, region.x_min, region.x_max),
        (start.y, end.y - start.y, region.y_min, region.y_max),
    ):
        if delta == 0:
            if origin < minimum or origin > maximum:
                low, high = 1.0, 0.0
                break
        else:
            first, second = (minimum - origin) / delta, (maximum - origin) / delta
            low = max(low, min(first, second))
            high = min(high, max(first, second))
    if low <= high:
        return 0.0
    corners = (
        Vec2(region.x_min, region.y_min),
        Vec2(region.x_min, region.y_max),
        Vec2(region.x_max, region.y_min),
        Vec2(region.x_max, region.y_max),
    )
    return min(
        region.clearance(start),
        region.clearance(end),
        *(point_to_segment_distance(corner, start, end) for corner in corners),
    )
