"""Built-in scenario definitions and hidden ground truth."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from app import limits
from app.simulation.field import FieldTruth, NoiseModel
from app.simulation.geometry import CircleRegion, RectRegion, Region, RegionKind, Vec2
from app.simulation.types import RobotState, region_to_public


@dataclass(frozen=True)
class Scenario:
    id: str
    name: str
    description: str
    width: float
    height: float
    source: Vec2
    truth_field: FieldTruth
    regions: tuple[Region, ...] = field(default_factory=tuple)
    default_robot_count: int = limits.DEFAULT_ROBOTS
    recommended_mission: str = (
        "Search for the signal source, maintain a ring formation, and avoid restricted regions."
    )
    tags: tuple[str, ...] = field(default_factory=tuple)
    start_jitter_m: float = 0.07

    def active_regions(self, time_s: float) -> tuple[Region, ...]:
        return tuple(region for region in self.regions if region.active_from_s <= time_s + 1e-9)

    def scheduled_regions(self) -> tuple[Region, ...]:
        return tuple(region for region in self.regions if region.active_from_s > 0)

    def to_public(self) -> dict[str, object]:
        initial = tuple(region for region in self.regions if region.active_from_s <= 0)
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "arena": {"width_m": self.width, "height_m": self.height},
            "sensor": self.truth_field.public_description(),
            "initial_regions": [region_to_public(region) for region in initial],
            "scheduled_event_count": len(self.scheduled_regions()),
            "default_robot_count": self.default_robot_count,
            "recommended_mission": self.recommended_mission,
            "tags": list(self.tags),
            "source_revealed": False,
        }

    def initial_states(
        self,
        robot_count: int,
        minimum_separation: float,
        rng: random.Random,
    ) -> tuple[RobotState, ...]:
        if not (limits.MIN_ROBOTS <= robot_count <= limits.MAX_ROBOTS):
            raise ValueError("robot_count outside supported range")
        rows = math.ceil(robot_count / 2)
        column_spacing = max(1.25, minimum_separation + 0.25)
        row_spacing = max(1.2, minimum_separation + 0.3)
        total_height = (rows - 1) * row_spacing
        start_y = (self.height - total_height) / 2.0
        start_x = 1.0
        states: list[RobotState] = []
        for index in range(robot_count):
            column = index % 2
            row = index // 2
            x = start_x + column * column_spacing
            y = start_y + row * row_spacing
            jitter = self.start_jitter_m
            x += rng.uniform(-jitter, jitter)
            y += rng.uniform(-jitter, jitter)
            x = min(
                max(x, limits.BOUNDARY_MARGIN_M + 0.1),
                self.width - limits.BOUNDARY_MARGIN_M - 0.1,
            )
            y = min(
                max(y, limits.BOUNDARY_MARGIN_M + 0.1),
                self.height - limits.BOUNDARY_MARGIN_M - 0.1,
            )
            states.append(RobotState(robot_id=index, x=x, y=y, heading=0.0))
        return tuple(states)


def _wall(
    region_id: str,
    x_min: float,
    y_min: float,
    x_max: float,
    y_max: float,
    active_from: float = 0.0,
    label: str = "barrier",
) -> RectRegion:
    return RectRegion(
        id=region_id,
        kind=RegionKind.OBSTACLE,
        x_min=x_min,
        y_min=y_min,
        x_max=x_max,
        y_max=y_max,
        active_from_s=active_from,
        label=label,
    )


OPEN_FIELD = Scenario(
    id="open_field",
    name="Open field",
    description="Single hidden source in an unobstructed arena. Baseline reproducibility scenario.",
    width=10.0,
    height=10.0,
    source=Vec2(7.0, 5.0),
    truth_field=FieldTruth(
        source=Vec2(7.0, 5.0),
        baseline=1.0,
        kappa=1.0,
        noise_model=NoiseModel.NONE,
        noise_amplitude=0.0,
    ),
    regions=(),
    tags=("baseline", "no-obstacles"),
)

NOISY_OPEN = Scenario(
    id="noisy_open",
    name="Noisy field",
    description="Single hidden source with seeded Gaussian sensor noise.",
    width=10.0,
    height=10.0,
    source=Vec2(6.7, 4.6),
    truth_field=FieldTruth(
        source=Vec2(6.7, 4.6),
        baseline=1.0,
        kappa=1.0,
        noise_model=NoiseModel.GAUSSIAN,
        noise_amplitude=0.04,
    ),
    regions=(),
    tags=("noise", "robustness"),
)

RESTRICTED_CORRIDOR = Scenario(
    id="restricted_corridor",
    name="Static barrier",
    description=(
        "A wall separates the staging area from the source. The direct ring objective is "
        "blocked until the agent requests a deterministic detour."
    ),
    width=10.0,
    height=10.0,
    source=Vec2(8.0, 5.0),
    truth_field=FieldTruth(
        source=Vec2(8.0, 5.0),
        baseline=1.0,
        kappa=1.0,
        noise_model=NoiseModel.NONE,
        noise_amplitude=0.0,
    ),
    regions=(
        _wall("wall-static", 4.75, 0.0, 5.25, 6.2, label="service wall"),
        CircleRegion(
            id="restricted-static",
            kind=RegionKind.RESTRICTED,
            center=Vec2(3.3, 8.7),
            radius=0.7,
            label="restricted zone",
        ),
    ),
    tags=("obstacle", "agent-replan"),
)

DISTURBED_CORRIDOR = Scenario(
    id="disturbed_corridor",
    name="Dynamic barrier",
    description=(
        "The map is open at launch. At 6 seconds a wall appears across the direct route, "
        "triggering an obstacle-change event and a bounded replan."
    ),
    width=10.0,
    height=10.0,
    source=Vec2(8.0, 5.0),
    truth_field=FieldTruth(
        source=Vec2(8.0, 5.0),
        baseline=1.0,
        kappa=1.0,
        noise_model=NoiseModel.NONE,
        noise_amplitude=0.0,
    ),
    regions=(
        _wall("wall-dynamic", 5.55, 0.0, 6.05, 6.2, active_from=6.0, label="appearing wall"),
    ),
    tags=("obstacle", "dynamic-event", "agent-replan"),
)

NEAR_BOUNDARY = Scenario(
    id="near_boundary",
    name="Source near boundary",
    description=(
        "The hidden source lies close to the arena edge. A full ring at the requested radius "
        "cannot fit, so the run should fail the formation check honestly."
    ),
    width=10.0,
    height=10.0,
    source=Vec2(9.35, 5.2),
    truth_field=FieldTruth(
        source=Vec2(9.35, 5.2),
        baseline=1.0,
        kappa=1.0,
        noise_model=NoiseModel.NONE,
        noise_amplitude=0.0,
    ),
    regions=(),
    tags=("boundary", "expected-failure"),
)

INFEASIBLE_ENCLOSURE = Scenario(
    id="infeasible_enclosure",
    name="Sealed enclosure",
    description=(
        "The source is inside a sealed box. No safe route can encircle it; the system must "
        "stop and report an infeasible mission rather than claiming success."
    ),
    width=10.0,
    height=10.0,
    source=Vec2(7.3, 5.0),
    truth_field=FieldTruth(
        source=Vec2(7.3, 5.0),
        baseline=1.0,
        kappa=1.0,
        noise_model=NoiseModel.NONE,
        noise_amplitude=0.0,
    ),
    regions=(
        _wall("box-left", 5.9, 3.7, 6.1, 6.3, label="enclosure"),
        _wall("box-right", 8.5, 3.7, 8.7, 6.3, label="enclosure"),
        _wall("box-bottom", 5.9, 3.7, 8.7, 3.9, label="enclosure"),
        _wall("box-top", 5.9, 6.1, 8.7, 6.3, label="enclosure"),
    ),
    tags=("infeasible", "expected-failure"),
)

FAR_SOURCE = Scenario(
    id="far_source",
    name="Far source",
    description=(
        "Source in the far corner. Useful for timeout experiments with short "
        "mission budgets."
    ),
    width=10.0,
    height=10.0,
    source=Vec2(9.0, 9.0),
    truth_field=FieldTruth(
        source=Vec2(9.0, 9.0),
        baseline=1.0,
        kappa=1.0,
        noise_model=NoiseModel.NONE,
        noise_amplitude=0.0,
    ),
    regions=(),
    tags=("timeout", "expected-failure"),
)

SCENARIOS: dict[str, Scenario] = {
    scenario.id: scenario
    for scenario in (
        OPEN_FIELD,
        NOISY_OPEN,
        RESTRICTED_CORRIDOR,
        DISTURBED_CORRIDOR,
        NEAR_BOUNDARY,
        INFEASIBLE_ENCLOSURE,
        FAR_SOURCE,
    )
}


def get_scenario(scenario_id: str) -> Scenario:
    try:
        return SCENARIOS[scenario_id]
    except KeyError as exc:
        raise KeyError(f"unknown scenario: {scenario_id}") from exc


def list_public_scenarios() -> list[dict[str, object]]:
    return [scenario.to_public() for scenario in SCENARIOS.values()]
