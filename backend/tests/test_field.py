from __future__ import annotations

import json
import math
import random

import pytest

from app.simulation.field import FieldTruth, NoiseModel
from app.simulation.geometry import Vec2


def test_field_value_is_baseline_at_hidden_source() -> None:
    field = FieldTruth(source=Vec2(3.0, 4.0), baseline=2.5, kappa=1.5)
    assert field.value(Vec2(3.0, 4.0)) == pytest.approx(2.5)
    assert field.value(Vec2(3.0, 5.0)) == pytest.approx(4.0)


def test_field_rejects_invalid_parameters() -> None:
    with pytest.raises(ValueError):
        FieldTruth(source=Vec2(1.0, 1.0), baseline=1.0, kappa=0.0)
    with pytest.raises(ValueError):
        FieldTruth(source=Vec2(1.0, 1.0), baseline=1.0, kappa=1.0, noise_amplitude=-1.0)
    with pytest.raises(ValueError):
        FieldTruth(source=Vec2(math.nan, 1.0), baseline=1.0, kappa=1.0)


def test_noisy_measurements_reproduce_with_same_seed() -> None:
    field = FieldTruth(
        source=Vec2(6.0, 5.0),
        baseline=1.0,
        kappa=1.0,
        noise_model=NoiseModel.GAUSSIAN,
        noise_amplitude=0.2,
    )
    first = [field.measure(Vec2(2.0, 2.0), random.Random(7)) for _ in range(1)]
    rng_a = random.Random(7)
    rng_b = random.Random(7)
    rng_c = random.Random(8)
    samples_a = [field.measure(Vec2(2.0, 2.0), rng_a) for _ in range(20)]
    samples_b = [field.measure(Vec2(2.0, 2.0), rng_b) for _ in range(20)]
    samples_c = [field.measure(Vec2(2.0, 2.0), rng_c) for _ in range(20)]
    assert first
    assert samples_a == samples_b
    assert samples_a != samples_c


def test_public_field_description_never_contains_source() -> None:
    field = FieldTruth(source=Vec2(6.0, 5.0), baseline=1.0, kappa=1.0)
    description = field.public_description()
    serialized = json.dumps(description)
    assert "6.0" not in serialized
    assert "5.0" not in serialized
    assert set(description) == {"noise_model", "noise_amplitude", "measurement_units"}
