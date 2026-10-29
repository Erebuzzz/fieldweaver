"""Gradient-free source estimators built only from team poses and scalar readings."""

from __future__ import annotations

import math
from collections import deque
from dataclasses import replace

from app import limits
from app.simulation.field import FieldTruth
from app.simulation.types import SourceEstimate, TeamObservation


def _solve_4x4(matrix: list[list[float]], rhs: list[float]) -> list[float] | None:
    """Gaussian elimination with partial pivoting for a 4x4 system."""

    size = 4
    augmented = [row[:] + [rhs[index]] for index, row in enumerate(matrix)]
    max_coefficient = max(abs(value) for row in matrix for value in row) or 1.0
    threshold = 1e-10 * max_coefficient
    for column in range(size):
        pivot_row = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot_row][column]) < threshold:
            return None
        if pivot_row != column:
            augmented[column], augmented[pivot_row] = augmented[pivot_row], augmented[column]
        pivot = augmented[column][column]
        for row in range(column + 1, size):
            factor = augmented[row][column] / pivot
            if factor == 0.0:
                continue
            for index in range(column, size + 1):
                augmented[row][index] -= factor * augmented[column][index]
    solution = [0.0] * size
    for row in range(size - 1, -1, -1):
        value = augmented[row][size] - sum(
            augmented[row][column] * solution[column] for column in range(row + 1, size)
        )
        solution[row] = value / augmented[row][row]
    if not all(math.isfinite(value) for value in solution):
        return None
    return solution


class QuadraticSourceEstimator:
    """Regularized least-squares fit of f = a + b u + c v + d (u^2 + v^2).

    Coordinates are centered and scaled by arena half-size for conditioning.
    Ill-conditioned, flat, or negative-curvature fits are rejected. The last
    accepted estimate is retained with reduced confidence; a raw arena-centre
    prior is used until the first accepted fit.
    """

    def __init__(
        self,
        arena_width: float,
        arena_height: float,
        window: int = limits.ESTIMATOR_WINDOW_SAMPLES,
    ) -> None:
        self._arena_width = arena_width
        self._arena_height = arena_height
        self._history: deque[tuple[float, float, float]] = deque(maxlen=window)
        self._prior = SourceEstimate(
            x=arena_width / 2.0,
            y=arena_height / 2.0,
            confidence=0.0,
            samples=0,
            valid=False,
            note="arena centre prior",
        )
        self._last_valid: SourceEstimate | None = None

    @property
    def prior(self) -> SourceEstimate:
        return self._prior

    def add_observations(self, observation: TeamObservation) -> None:
        for robot in observation.robots:
            self._history.append((robot.x, robot.y, robot.measurement))

    def estimate(self) -> SourceEstimate:
        sample_count = len(self._history)
        if sample_count < limits.ESTIMATOR_MIN_SAMPLES:
            return replace(self._prior, samples=sample_count)

        center_x = self._arena_width / 2.0
        center_y = self._arena_height / 2.0
        scale = max(self._arena_width, self._arena_height) / 2.0

        mean_x = sum(item[0] for item in self._history) / sample_count
        mean_y = sum(item[1] for item in self._history) / sample_count
        var_x = sum((item[0] - mean_x) ** 2 for item in self._history) / sample_count
        var_y = sum((item[1] - mean_y) ** 2 for item in self._history) / sample_count
        cov_xy = (
            sum((item[0] - mean_x) * (item[1] - mean_y) for item in self._history)
            / sample_count
        )
        half_trace = (var_x + var_y) / 2.0
        discriminant = max(half_trace * half_trace - (var_x * var_y - cov_xy * cov_xy), 0.0)
        min_variance = half_trace - math.sqrt(discriminant)
        if min_variance < limits.ESTIMATOR_MIN_POSITION_STD_M**2:
            return self._fallback("sample positions are nearly collinear or clustered")

        normal = [[0.0] * 4 for _ in range(4)]
        rhs = [0.0] * 4
        values: list[float] = []
        for x, y, measurement in self._history:
            u = (x - center_x) / scale
            v = (y - center_y) / scale
            features = (1.0, u, v, u * u + v * v)
            values.append(measurement)
            for row in range(4):
                for column in range(4):
                    normal[row][column] += features[row] * features[column]
                rhs[row] += features[row] * measurement

        ridge = limits.ESTIMATOR_REGULARIZATION
        for index in range(4):
            normal[index][index] += ridge

        solution = _solve_4x4(normal, rhs)
        if solution is None:
            return self._fallback("degenerate sample geometry")

        intercept, b, c, curvature = solution
        if curvature <= limits.ESTIMATOR_MIN_CURVATURE:
            return self._fallback("non-positive field curvature")

        raw_x = center_x + (-b / (2.0 * curvature)) * scale
        raw_y = center_y + (-c / (2.0 * curvature)) * scale
        if not math.isfinite(raw_x) or not math.isfinite(raw_y):
            return self._fallback("non-finite estimate")

        outside_limit = 2.0
        if (
            raw_x < -outside_limit
            or raw_x > self._arena_width + outside_limit
            or raw_y < -outside_limit
            or raw_y > self._arena_height + outside_limit
        ):
            return self._fallback("estimate far outside arena")

        clamped_x = min(max(raw_x, 0.0), self._arena_width)
        clamped_y = min(max(raw_y, 0.0), self._arena_height)

        predicted = [
            intercept
            + b * ((x - center_x) / scale)
            + c * ((y - center_y) / scale)
            + curvature * (((x - center_x) / scale) ** 2 + ((y - center_y) / scale) ** 2)
            for x, y, _ in self._history
        ]
        mean_value = sum(values) / len(values)
        variance = sum((value - mean_value) ** 2 for value in values) / len(values)
        spread = math.sqrt(max(variance, 0.0))
        residual = math.sqrt(
            sum((actual - fit) ** 2 for actual, fit in zip(values, predicted, strict=True))
            / len(values)
        )
        sample_factor = min(1.0, sample_count / 36.0)
        residual_factor = 1.0 if spread < 1e-9 else max(0.0, 1.0 - residual / (spread + 1e-9))
        confidence = max(0.0, min(1.0, sample_factor * residual_factor))

        estimate = SourceEstimate(
            x=clamped_x,
            y=clamped_y,
            confidence=confidence,
            samples=sample_count,
            valid=True,
            residual=residual,
            curvature=curvature,
            note="quadratic least-squares fit",
        )
        self._last_valid = estimate
        return estimate

    def _fallback(self, reason: str) -> SourceEstimate:
        if self._last_valid is not None:
            return replace(
                self._last_valid,
                confidence=self._last_valid.confidence * 0.9,
                samples=len(self._history),
                note=f"held previous fit: {reason}",
            )
        return replace(
            self._prior,
            samples=len(self._history),
            note=f"arena centre prior: {reason}",
        )


class WeightedCentroidEstimator:
    """Deliberately simple baseline estimator.

    Uses exponential inverse-measurement weights over recent team positions.
    It is not a quadratic field fit and is expected to localize less accurately.
    """

    def __init__(
        self,
        arena_width: float,
        arena_height: float,
        window: int = 120,
    ) -> None:
        self._history: deque[tuple[float, float, float]] = deque(maxlen=window)
        self._prior = SourceEstimate(
            x=arena_width / 2.0,
            y=arena_height / 2.0,
            confidence=0.0,
            samples=0,
            valid=False,
            note="arena centre prior",
        )
        self._last_valid: SourceEstimate | None = None

    @property
    def prior(self) -> SourceEstimate:
        return self._prior

    def add_observations(self, observation: TeamObservation) -> None:
        for robot in observation.robots:
            self._history.append((robot.x, robot.y, robot.measurement))

    def estimate(self) -> SourceEstimate:
        sample_count = len(self._history)
        if sample_count < limits.ESTIMATOR_MIN_SAMPLES:
            return replace(self._prior, samples=sample_count)
        values = [item[2] for item in self._history]
        minimum = min(values)
        mean = sum(values) / len(values)
        spread = math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))
        scale = max(spread, 0.05)
        weights = [math.exp(-(value - minimum) / scale) for value in values]
        total = sum(weights)
        if total <= 0 or not math.isfinite(total):
            return self._fallback("degenerate weights")
        x = (
            sum(
                weight * item[0]
                for weight, item in zip(weights, self._history, strict=True)
            )
            / total
        )
        y = (
            sum(
                weight * item[1]
                for weight, item in zip(weights, self._history, strict=True)
            )
            / total
        )
        confidence = max(0.0, min(1.0, (sample_count / 36.0) * (spread / (spread + 0.05))))
        estimate = SourceEstimate(
            x=x,
            y=y,
            confidence=confidence,
            samples=sample_count,
            valid=True,
            residual=spread,
            note="weighted centroid baseline",
        )
        self._last_valid = estimate
        return estimate

    def _fallback(self, reason: str) -> SourceEstimate:
        if self._last_valid is not None:
            return replace(self._last_valid, samples=len(self._history), note=reason)
        return replace(self._prior, samples=len(self._history), note=reason)


def true_field_value(field: FieldTruth, x: float, y: float) -> float:
    from app.simulation.geometry import Vec2

    return field.value(Vec2(x, y))
