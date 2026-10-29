from __future__ import annotations

import math
from dataclasses import replace

import app.services.agent as agent_module
from app.schemas import default_mission_spec
from app.services.agent import BoundedOrchestrator, MockDecisionProvider
from app.simulation.controller import FormationController
from app.simulation.engine import SimulationSession
from app.simulation.geometry import CircleRegion, RegionKind, Vec2
from app.simulation.planner import PlanResult
from app.simulation.scenario import OPEN_FIELD
from app.simulation.types import RobotObservation, SourceEstimate, TeamObservation


def test_detour_routes_end_at_each_assigned_ring_slot() -> None:
    mission = default_mission_spec()
    session = SimulationSession(mission, OPEN_FIELD, seed=42)
    controller = session.controller
    controller.estimate = SourceEstimate(
        x=5.0,
        y=5.0,
        confidence=1.0,
        samples=6,
        valid=True,
    )
    positions = {
        robot.robot_id: Vec2(robot.x, robot.y) for robot in session.states
    }
    expected_targets = controller.ring_slot_targets(positions, 5.0, 5.0)
    orchestrator = BoundedOrchestrator(
        session, OPEN_FIELD, MockDecisionProvider(), max_decisions=2, max_replans=2
    )

    orchestrator._apply_detour()

    assert controller.detour is not None
    assert set(controller.detour.routes) == set(expected_targets)
    for robot_id, target in expected_targets.items():
        route = controller.detour.routes[robot_id]
        assert route[0] == positions[robot_id]
        assert route[-1].distance_to(target) <= 1e-9


def test_detour_commands_repel_robots_from_a_close_pair() -> None:
    mission = default_mission_spec()
    controller = FormationController(mission, arena_width=10.0, arena_height=10.0)
    first = Vec2(3.0, 5.0)
    second = Vec2(3.2, 5.0)
    controller.set_detour(
        {
            0: (first, Vec2(5.0, 5.0)),
            1: (second, Vec2(5.2, 5.0)),
        },
        now_s=0.0,
        max_duration_s=10.0,
    )
    observation = TeamObservation(
        step=1,
        time_s=0.1,
        robots=(
            RobotObservation(0, 1, 0.1, first.x, first.y, 0.0, 1.0),
            RobotObservation(1, 1, 0.1, second.x, second.y, 0.0, 1.0),
        ),
    )

    commands = controller.propose(observation, active_regions=(), time_s=0.1)

    assert commands[0].vx < 0.0
    assert commands[1].vx > 0.0
    assert all(
        math.hypot(command.vx, command.vy) <= mission.constraints.maximum_speed + 1e-9
        for command in commands
    )


def test_detour_fails_when_a_ring_slot_is_blocked_instead_of_shifting_it() -> None:
    mission = default_mission_spec()
    reference = SimulationSession(mission, OPEN_FIELD, seed=42)
    reference.controller.estimate = SourceEstimate(
        x=5.0,
        y=5.0,
        confidence=1.0,
        samples=6,
        valid=True,
    )
    positions = {
        robot.robot_id: Vec2(robot.x, robot.y) for robot in reference.states
    }
    targets = reference.controller.ring_slot_targets(positions, 5.0, 5.0)
    blocked_target = targets[0]
    blocker = CircleRegion(
        id="blocked-ring-slot",
        kind=RegionKind.OBSTACLE,
        center=blocked_target,
        radius=0.05,
    )
    scenario = replace(OPEN_FIELD, id="blocked-ring-slot", regions=(blocker,))
    session = SimulationSession(mission, scenario, seed=42)
    session.controller.estimate = SourceEstimate(
        x=5.0,
        y=5.0,
        confidence=1.0,
        samples=6,
        valid=True,
    )
    orchestrator = BoundedOrchestrator(
        session, scenario, MockDecisionProvider(), max_decisions=2, max_replans=2
    )

    orchestrator._apply_detour()

    assert session.termination_reason == "route_infeasible"
    assert session.controller.detour is None
    assert orchestrator.result.trace[-1]["phase"] == "terminated"


def test_detour_rejects_a_route_endpoint_shift_under_ten_centimeters(
    monkeypatch,
) -> None:
    mission = default_mission_spec()
    session = SimulationSession(mission, OPEN_FIELD, seed=42)
    session.controller.estimate = SourceEstimate(
        x=5.0,
        y=5.0,
        confidence=1.0,
        samples=6,
        valid=True,
    )
    original_planner = agent_module.plan_detour_path

    def shifted_planner(**kwargs: object) -> PlanResult:
        result = original_planner(**kwargs)
        if not result.path:
            return result
        shifted = list(result.path)
        endpoint = shifted[-1]
        shifted[-1] = Vec2(endpoint.x + 0.05, endpoint.y)
        return PlanResult(tuple(shifted), result.expanded_nodes, result.reason)

    monkeypatch.setattr(agent_module, "plan_detour_path", shifted_planner)
    orchestrator = BoundedOrchestrator(
        session, OPEN_FIELD, MockDecisionProvider(), max_decisions=2, max_replans=2
    )

    orchestrator._apply_detour()

    assert session.termination_reason == "route_infeasible"
    assert session.controller.detour is None
