from __future__ import annotations

import math

from app.simulation.field import FieldTruth
from app.simulation.geometry import Vec2
from app.simulation.planner import plan_detour_path, validate_path
from app.simulation.scenario import INFEASIBLE_ENCLOSURE, RESTRICTED_CORRIDOR


def test_planner_routes_around_static_wall() -> None:
    wall = RESTRICTED_CORRIDOR.regions[0]
    start = Vec2(2.0, 5.0)
    goal = Vec2(8.0, 5.0)
    result = plan_detour_path(
        start=start,
        goal=goal,
        width=10.0,
        height=10.0,
        regions=(wall,),
        clearance=0.2,
    )
    assert result.reason == "ok"
    assert len(result.path) >= 2
    assert result.path[0] == start
    assert result.path[-1] == goal
    assert any(point.y > 6.3 for point in result.path)
    assert validate_path(result.path, 10.0, 10.0, (wall,), 0.2) is None


def test_planner_refuses_sealed_enclosure() -> None:
    result = plan_detour_path(
        start=Vec2(2.0, 2.0),
        goal=Vec2(7.3, 5.0),
        width=10.0,
        height=10.0,
        regions=INFEASIBLE_ENCLOSURE.regions,
        clearance=0.2,
    )
    assert result.path == ()
    assert "no route" in result.reason


def test_validate_path_rejects_clearance_violation() -> None:
    wall = RESTRICTED_CORRIDOR.regions[0]
    path = (Vec2(2.0, 3.0), Vec2(8.0, 3.0))
    reason = validate_path(path, 10.0, 10.0, (wall,), 0.2)
    assert reason == "path segment violates clearance"


def test_truth_field_matches_scenario_source() -> None:
    assert RESTRICTED_CORRIDOR.source == RESTRICTED_CORRIDOR.truth_field.source
    field = FieldTruth(source=RESTRICTED_CORRIDOR.source, baseline=1.0, kappa=1.0)
    assert field.value(RESTRICTED_CORRIDOR.source) == 1.0
    assert math.isfinite(field.value(Vec2(0.0, 0.0)))
