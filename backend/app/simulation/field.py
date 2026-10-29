"""Hidden scalar field and the observation-only sensor interface.

Ground-truth source coordinates live in this module and are read only by the
simulation/evaluation layer. Observations expose scalar measurements and robot
poses, never the source coordinate.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import StrEnum

from app.simulation.geometry import Vec2


class NoiseModel(StrEnum):
    NONE = "none"
    UNIFORM = "uniform"
    GAUSSIAN = "gaussian"


@dataclass(frozen=True)
class FieldTruth:
    source: Vec2
    baseline: float
    kappa: float
    noise_model: NoiseModel = NoiseModel.NONE
    noise_amplitude: float = 0.0

    def __post_init__(self) -> None:
        if not all(
            math.isfinite(value)
            for value in (
                self.source.x,
                self.source.y,
                self.baseline,
                self.kappa,
                self.noise_amplitude,
            )
        ):
            raise ValueError("field parameters must be finite")
        if self.kappa <= 0:
            raise ValueError("field kappa must be positive")
        if self.noise_amplitude < 0:
            raise ValueError("noise amplitude must be non-negative")

    def value(self, point: Vec2) -> float:
        return self.baseline + self.kappa * (
            (point.x - self.source.x) ** 2 + (point.y - self.source.y) ** 2
        )

    def measure(self, point: Vec2, rng: random.Random) -> float:
        value = self.value(point)
        if self.noise_model is NoiseModel.NONE or self.noise_amplitude == 0.0:
            return value
        if self.noise_model is NoiseModel.UNIFORM:
            return value + rng.uniform(-self.noise_amplitude, self.noise_amplitude)
        if self.noise_model is NoiseModel.GAUSSIAN:
            return value + rng.gauss(0.0, self.noise_amplitude)
        raise ValueError(f"unsupported noise model: {self.noise_model}")

    def public_description(self) -> dict[str, object]:
        """Sensor metadata safe to show in the UI. Never includes source coordinates."""

        return {
            "noise_model": self.noise_model.value,
            "noise_amplitude": self.noise_amplitude,
            "measurement_units": "field units, lower is closer",
        }
