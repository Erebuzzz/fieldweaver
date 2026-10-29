from __future__ import annotations

import json
import math

import pytest

from app.schemas import default_mission_spec
from app.simulation.estimator import QuadraticSourceEstimator, WeightedCentroidEstimator
from app.simulation.field import FieldTruth
from app.simulation.geometry import Vec2
from app.simulation.scenario import OPEN_FIELD
from app.simulation.types import RobotObservation, TeamObservation


def _team_observation(points: list[tuple[float, float]], field: FieldTruth) -> TeamObservation:
    robots = tuple(
        RobotObservation(
            robot_id=index,
            step=0,
            time_s=0.0,
            x=x,
            y=y,
            heading=0.0,
            measurement=field.value(Vec2(x, y)),
        )
        for index, (x, y) in enumerate(points)
    )
    return TeamObservation(step=0, time_s=0.0, robots=robots)


def test_quadratic_estimator_recovers_source_from_spread_samples() -> None:
    field = FieldTruth(source=Vec2(7.1, 4.3), baseline=1.0, kappa=1.0)
    points = [
        (1.0, 1.0),
        (2.5, 1.0),
        (4.5, 1.5),
        (1.0, 3.0),
        (3.0, 3.5),
        (5.5, 3.0),
        (2.0, 5.0),
        (4.0, 5.5),
        (6.0, 5.0),
        (1.5, 7.0),
        (3.5, 7.5),
        (5.0, 7.0),
    ]
    estimator = QuadraticSourceEstimator(10.0, 10.0)
    for chunk in range(0, len(points), 3):
        estimator.add_observations(_team_observation(points[chunk : chunk + 3], field))
    estimate = estimator.estimate()
    assert estimate.valid
    assert estimate.x == pytest.approx(7.1, abs=1e-4)
    assert estimate.y == pytest.approx(4.3, abs=1e-4)
    assert estimate.confidence > 0.3


def test_quadratic_estimator_rejects_collinear_samples() -> None:
    field = FieldTruth(source=Vec2(7.0, 5.0), baseline=1.0, kappa=1.0)
    points = [(x, 2.0) for x in (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0)]
    estimator = QuadraticSourceEstimator(10.0, 10.0)
    estimator.add_observations(_team_observation(points, field))
    estimate = estimator.estimate()
    assert not estimate.valid
    assert estimate.note.startswith("arena centre prior")


def test_quadratic_estimator_holds_previous_fit_on_degeneracy() -> None:
    field = FieldTruth(source=Vec2(7.0, 5.0), baseline=1.0, kappa=1.0)
    spread = [
        (1.0, 1.0),
        (3.0, 1.0),
        (5.0, 2.0),
        (2.0, 4.0),
        (4.0, 5.0),
        (6.0, 4.0),
        (1.5, 6.0),
        (3.5, 7.0),
        (5.5, 6.5),
    ]
    estimator = QuadraticSourceEstimator(10.0, 10.0, window=9)
    estimator.add_observations(_team_observation(spread, field))
    first = estimator.estimate()
    assert first.valid

    estimator.add_observations(_team_observation([(x, 2.0) for x in (1.0, 2.0, 3.0)] * 3, field))
    estimate = estimator.estimate()
    assert estimate.note.startswith("held previous fit")
    assert math.isclose(estimate.x, first.x, abs_tol=0.05)


def test_weighted_centroid_baseline_returns_finite_estimate() -> None:
    field = FieldTruth(source=Vec2(7.0, 5.0), baseline=1.0, kappa=1.0)
    estimator = WeightedCentroidEstimator(10.0, 10.0)
    points = [
        (1.0, 1.0),
        (2.0, 3.0),
        (4.0, 5.0),
        (3.0, 7.0),
        (6.0, 2.0),
        (5.5, 5.5),
        (7.0, 6.0),
        (2.5, 5.5),
        (6.5, 3.0),
    ]
    estimator.add_observations(_team_observation(points, field))
    estimate = estimator.estimate()
    assert estimate.valid
    assert 0.0 <= estimate.x <= 10.0
    assert 0.0 <= estimate.y <= 10.0
    assert estimate.note == "weighted centroid baseline"


def test_estimators_accept_only_public_scenario_metadata() -> None:
    public = OPEN_FIELD.to_public()
    serialized = json.dumps(public)
    assert "source_revealed" in public
    assert public["source_revealed"] is False
    assert "7.0" not in serialized
    assert default_mission_spec().robot_count == OPEN_FIELD.default_robot_count
