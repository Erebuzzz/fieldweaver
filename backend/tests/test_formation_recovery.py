from __future__ import annotations

import asyncio

import pytest

from app.schemas import default_mission_spec
from app.services.runner import run_scenario
from app.simulation.controller import _separate_closing_commands
from app.simulation.scenario import get_scenario
from app.simulation.types import RobotCommand, RobotObservation, TeamObservation


def test_nearby_robots_do_not_propose_closing_motion() -> None:
    robots = tuple(
        RobotObservation(robot_id=i, step=0, time_s=0.0, x=x, y=0.0, heading=0.0, measurement=1.0)
        for i, x in enumerate((0.0, 0.4, 3.0))
    )
    observation = TeamObservation(step=0, time_s=0.0, robots=robots)
    commands = [RobotCommand(0.4, 0.1), RobotCommand(-0.4, 0.1), RobotCommand(0.2, 0.0)]

    adjusted = _separate_closing_commands(observation, commands, 0.35, 0.5)

    assert adjusted[0].vx <= adjusted[1].vx
    assert adjusted[2] == commands[2]
    assert all(command.speed() <= 0.5 for command in adjusted)


@pytest.mark.parametrize("seed", [43, 44])
def test_noisy_formation_recovers_without_collisions(seed: int) -> None:
    result = asyncio.run(
        run_scenario(
            scenario=get_scenario("noisy_open"),
            mission=default_mission_spec(),
            seed=seed,
            controller="quadratic",
            agent_mode="mock",
        )
    )

    assert result.evaluation.success
    assert result.evaluation.metrics["robot_collision_count"] == 0
    assert result.evaluation.metrics["minimum_robot_separation_m"] >= 0.35 - 1e-6
