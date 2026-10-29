"""Internal simulation data structures.

None of the observation structures contain ground-truth source coordinates.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RobotState:
    robot_id: int
    x: float
    y: float
    heading: float = 0.0

    def __post_init__(self) -> None:
        if not all(math.isfinite(value) for value in (self.x, self.y, self.heading)):
            raise ValueError("robot state must be finite")

    def position(self) -> tuple[float, float]:
        return (self.x, self.y)


@dataclass(frozen=True)
class RobotCommand:
    vx: float
    vy: float

    def __post_init__(self) -> None:
        if not all(math.isfinite(value) for value in (self.vx, self.vy)):
            raise ValueError("robot command must be finite")

    def speed(self) -> float:
        return math.hypot(self.vx, self.vy)


@dataclass(frozen=True)
class RobotObservation:
    """The complete observation interface available to the controller.

    Deliberately contains no source position, field kappa, baseline, or oracle value.
    """

    robot_id: int
    step: int
    time_s: float
    x: float
    y: float
    heading: float
    measurement: float


@dataclass(frozen=True)
class TeamObservation:
    step: int
    time_s: float
    robots: tuple[RobotObservation, ...]


@dataclass(frozen=True)
class SourceEstimate:
    x: float
    y: float
    confidence: float
    samples: int
    valid: bool
    residual: float = 0.0
    curvature: float = 0.0
    note: str = ""

    def __post_init__(self) -> None:
        if not all(
            math.isfinite(value)
            for value in (self.x, self.y, self.confidence, self.residual, self.curvature)
        ):
            raise ValueError("source estimate must be finite")

    def distance_to(self, other_x: float, other_y: float) -> float:
        return math.hypot(self.x - other_x, self.y - other_y)


@dataclass(frozen=True)
class FrameRobot:
    robot_id: int
    x: float
    y: float
    heading: float
    measurement: float


@dataclass(frozen=True)
class Frame:
    step: int
    time_s: float
    robots: tuple[FrameRobot, ...]
    estimate: SourceEstimate
    formation_error_estimate: float
    obstacle_version: int
    active_region_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_public(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "t": round(self.time_s, 4),
            "robots": [
                {
                    "id": robot.robot_id,
                    "x": round(robot.x, 5),
                    "y": round(robot.y, 5),
                    "heading": round(robot.heading, 5),
                    "measurement": round(robot.measurement, 5),
                }
                for robot in self.robots
            ],
            "estimate": {
                "x": round(self.estimate.x, 5),
                "y": round(self.estimate.y, 5),
                "confidence": round(self.estimate.confidence, 4),
                "valid": self.estimate.valid,
                "samples": self.estimate.samples,
            },
            "formation_error_estimate": round(self.formation_error_estimate, 5),
            "obstacle_version": self.obstacle_version,
            "active_region_ids": list(self.active_region_ids),
        }


@dataclass(frozen=True)
class SafetyIntervention:
    step: int
    time_s: float
    kind: str
    robot_id: int | None
    detail: str

    def to_public(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "t": round(self.time_s, 4),
            "kind": self.kind,
            "robot_id": self.robot_id,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class WorldEvent:
    time_s: float
    event_type: str
    regions: tuple[Any, ...]
    detail: str

    def to_public(self) -> dict[str, Any]:
        return {
            "t": round(self.time_s, 4),
            "type": self.event_type,
            "regions": [region_to_public(region) for region in self.regions],
            "detail": self.detail,
        }


def region_to_public(region: Any) -> dict[str, Any]:
    from app.simulation.geometry import CircleRegion, RectRegion

    base = {
        "id": region.id,
        "kind": region.kind.value,
        "label": region.label,
        "active_from_s": region.active_from_s,
    }
    if isinstance(region, RectRegion):
        base.update(
            {
                "shape": "rect",
                "x_min": region.x_min,
                "y_min": region.y_min,
                "x_max": region.x_max,
                "y_max": region.y_max,
            }
        )
    elif isinstance(region, CircleRegion):
        base.update(
            {
                "shape": "circle",
                "cx": region.center.x,
                "cy": region.center.y,
                "radius": region.radius,
            }
        )
    else:
        raise TypeError(f"unsupported region type: {type(region)!r}")
    return base
