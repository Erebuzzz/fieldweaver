"""Explicit robot dynamics shared by the simulator and independent filter."""

from __future__ import annotations

import math

from app.simulation.types import RobotCommand, RobotState


def clamp_command(command: RobotCommand, speed_limit: float) -> RobotCommand:
    speed = command.speed()
    if speed <= speed_limit or speed <= 1e-12:
        return command
    scale = speed_limit / speed
    return RobotCommand(vx=command.vx * scale, vy=command.vy * scale)


def integrate_state(state: RobotState, command: RobotCommand, dt: float) -> RobotState:
    if dt <= 0 or not math.isfinite(dt):
        raise ValueError("dt must be positive and finite")
    x = state.x + command.vx * dt
    y = state.y + command.vy * dt
    speed = command.speed()
    heading = state.heading if speed <= 1e-9 else math.atan2(command.vy, command.vx)
    return RobotState(robot_id=state.robot_id, x=x, y=y, heading=heading)
