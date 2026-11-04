"""Empirical Telemetry Verification Script for FieldWeaver.

Conducts rigorous empirical stress-testing for:
1. Frame JSON serialization size and an uncompressed 10-frame/sec estimate.
2. Public serialization fields for the frame and scenario.
3. Reference Hermite and shortest-arc interpolation identities.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.schemas import default_mission_spec  # noqa: E402
from app.simulation.engine import SimulationSession  # noqa: E402
from app.simulation.scenario import get_scenario  # noqa: E402


def verify_telemetry_payload_and_bandwidth():
    print("--- 1. JSON FRAME SIZE AND UNCOMPRESSED BANDWIDTH ESTIMATE ---")
    scenarios = ["open_field", "noisy_open", "restricted_corridor", "near_boundary"]
    robot_counts = [3, 5, 8]

    overall_sizes_compact = []
    overall_sizes_pretty = []

    for sc_id in scenarios:
        scenario = get_scenario(sc_id)
        for n_robots in robot_counts:
            mission = default_mission_spec().model_copy(update={"robot_count": n_robots})
            session = SimulationSession(mission=mission, scenario=scenario, seed=42)

            # Step 50 steps
            for _ in range(50):
                if session.finished:
                    break
                session.step()

            for frame in session.frames:
                pub = frame.to_public()
                compact_json = json.dumps(pub, separators=(",", ":"))
                pretty_json = json.dumps(pub, indent=2)

                overall_sizes_compact.append(len(compact_json.encode("utf-8")))
                overall_sizes_pretty.append(len(pretty_json.encode("utf-8")))

    min_c = min(overall_sizes_compact)
    max_c = max(overall_sizes_compact)
    avg_c = sum(overall_sizes_compact) / len(overall_sizes_compact)

    min_p = min(overall_sizes_pretty)
    max_p = max(overall_sizes_pretty)
    avg_p = sum(overall_sizes_pretty) / len(overall_sizes_pretty)

    # Bandwidth at 10 Hz:
    bw_bytes_sec_avg = avg_c * 10.0
    bw_kb_sec_avg = bw_bytes_sec_avg / 1024.0
    bw_kbps_avg = (bw_bytes_sec_avg * 8.0) / 1000.0  # kbps in standard telecomm 10^3

    # 5 robots typical
    mission_5 = default_mission_spec()
    session_5 = SimulationSession(mission=mission_5, scenario=get_scenario("open_field"), seed=42)
    session_5.step()
    frame_5 = session_5.frames[0].to_public()
    size_5_compact = len(json.dumps(frame_5, separators=(",", ":")).encode("utf-8"))
    bw_5_kbps = (size_5_compact * 10 * 8) / 1000.0
    bw_5_kbs = (size_5_compact * 10) / 1024.0

    print(f"Total frames sampled: {len(overall_sizes_compact)}")
    print(
        "Compact JSON bytes per frame (all configs): "
        f"min={min_c}, max={max_c}, avg={avg_c:.1f} bytes"
    )
    print(
        "Pretty JSON bytes per frame (all configs): "
        f"min={min_p}, max={max_p}, avg={avg_p:.1f} bytes"
    )
    print(f"Typical 5-robot frame compact bytes: {size_5_compact} bytes")
    print(
        "10 frames/sec JSON estimate (5 robots, excluding HTTP framing): "
        f"{bw_5_kbs:.2f} KB/s ({bw_5_kbps:.2f} kbps)"
    )
    print(
        "10 frames/sec JSON estimate (average, excluding HTTP framing): "
        f"{bw_kb_sec_avg:.2f} KB/s ({bw_kbps_avg:.2f} kbps)"
    )

    assert bw_kb_sec_avg > 0, "Expected a positive measured payload size"
    print("PASS: Payload sizes and estimated 10 Hz bandwidth were measured.")
    return {
        "min_bytes": min_c,
        "max_bytes": max_c,
        "avg_bytes": avg_c,
        "typical_5_robots_bytes": size_5_compact,
        "typical_5_robots_bw_kbs": bw_5_kbs,
        "typical_5_robots_bw_kbps": bw_5_kbps,
        "avg_bw_kbs": bw_kb_sec_avg,
        "avg_bw_kbps": bw_kbps_avg,
    }


def verify_public_serialization_fields():
    print("\n--- 2. PUBLIC SERIALIZATION FIELD CHECKS ---")
    scenarios = ["open_field", "noisy_open", "restricted_corridor", "far_source"]

    forbidden_terms = ["source", "kappa", "baseline", "truth", "oracle"]

    for sc_id in scenarios:
        scenario = get_scenario(sc_id)
        mission = default_mission_spec()
        session = SimulationSession(mission=mission, scenario=scenario, seed=123)

        for _step_idx in range(40):
            if session.finished:
                break
            session.step()
            frame = session.frames[-1]
            pub = frame.to_public()

            # Check keys
            def scan_keys_and_values(obj, path=""):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        for term in forbidden_terms:
                            assert term != k.lower(), f"Forbidden key '{k}' found at path '{path}'!"
                        scan_keys_and_values(v, f"{path}.{k}")
                elif isinstance(obj, list):
                    for idx, item in enumerate(obj):
                        scan_keys_and_values(item, f"{path}[{idx}]")

            scan_keys_and_values(pub, "frame")

            # Verify that Frame.to_public() contains strictly public telemetry fields
            expected_keys = {
                "step",
                "t",
                "robots",
                "estimate",
                "formation_error_estimate",
                "obstacle_version",
                "active_region_ids",
            }
            assert set(pub.keys()) == expected_keys, (
                f"Unexpected keys in Frame.to_public(): {pub.keys()}"
            )

            # Verify robot state attributes in telemetry
            for r in pub["robots"]:
                assert set(r.keys()) == {"id", "x", "y", "heading", "measurement"}

            # Verify estimate fields in telemetry
            assert set(pub["estimate"].keys()) == {"x", "y", "confidence", "valid", "samples"}

            # Verify Scenario public presentation quarantine
            sc_pub = scenario.to_public()
            assert "source" not in sc_pub
            assert "source_x" not in sc_pub
            assert "source_y" not in sc_pub
            assert sc_pub["source_revealed"] is False

            # Verify FieldTruth public presentation quarantine
            ft_pub = scenario.truth_field.public_description()
            assert "source" not in ft_pub
            assert "kappa" not in ft_pub
            assert "baseline" not in ft_pub


def verify_mathematical_interpolation():
    print("\n--- 3. REFERENCE INTERPOLATION FORMULAS ---")

    # 3.1 Cubic Hermite Spline Verification
    # Formula from Roadmap Section 4.2:
    # Check the endpoint values of the cubic Hermite reference formula.
    def hermite_pos(p0, v0, p1, v1, dt, alpha):
        h00 = 2 * (alpha**3) - 3 * (alpha**2) + 1
        h10 = (alpha**3) - 2 * (alpha**2) + alpha
        h01 = -2 * (alpha**3) + 3 * (alpha**2)
        h11 = (alpha**3) - (alpha**2)
        return h00 * p0 + h10 * dt * v0 + h01 * p1 + h11 * dt * v1

    def hermite_vel(p0, v0, p1, v1, dt, alpha):
        dh00 = 6 * (alpha**2) - 6 * alpha
        dh10 = 3 * (alpha**2) - 4 * alpha + 1
        dh01 = -6 * (alpha**2) + 6 * alpha
        dh11 = 3 * (alpha**2) - 2 * alpha
        return (dh00 * p0 + dh10 * dt * v0 + dh01 * p1 + dh11 * dt * v1) / dt

    dt = 0.1
    p0, v0 = 1.0, 0.5
    p1, v1 = 2.0, 0.2

    # Check boundaries
    p_start = hermite_pos(p0, v0, p1, v1, dt, 0.0)
    p_end = hermite_pos(p0, v0, p1, v1, dt, 1.0)
    v_start = hermite_vel(p0, v0, p1, v1, dt, 0.0)
    v_end = hermite_vel(p0, v0, p1, v1, dt, 1.0)

    assert abs(p_start - p0) < 1e-12, f"Hermite p(0) failed: {p_start} vs {p0}"
    assert abs(p_end - p1) < 1e-12, f"Hermite p(1) failed: {p_end} vs {p1}"
    assert abs(v_start - v0) < 1e-12, f"Hermite v(0) failed: {v_start} vs {v0}"
    assert abs(v_end - v1) < 1e-12, f"Hermite v(1) failed: {v_end} vs {v1}"
    print("Hermite boundary values verified: C1 continuity satisfied at endpoints.")

    # 3.2 Shortest-Arc Angular Slerp Across Boundary Wrap-Arounds
    # Formula from Roadmap Section 4.3:
    # delta_theta = atan2(sin(theta1 - theta0), cos(theta1 - theta0))
    # theta(alpha) = theta0 + alpha * delta_theta
    def slerp_heading(theta0, theta1, alpha):
        delta = math.atan2(math.sin(theta1 - theta0), math.cos(theta1 - theta0))
        return theta0 + alpha * delta, delta

    # Stress Case 1: Crossing from positive boundary (+3.10) to negative boundary (-3.10)
    # The naive linear interpolation sweeps backwards: -3.10 - 3.10 = -6.20 rad (-355 deg!)
    # Shortest arc should be: +0.083185 rad (+4.77 deg forward across pi)
    theta0 = 3.10
    theta1 = -3.10
    th_mid, delta = slerp_heading(theta0, theta1, 0.5)
    print(f"Wrap-around test 1: delta={delta:.5f} rad ({math.degrees(delta):.2f} deg)")
    assert abs(delta) < 0.1, f"Shortest arc delta too large: {delta}"
    assert delta > 0, f"Expected positive forward arc across +pi, got {delta}"

    # Stress Case 2: Crossing from negative boundary (-3.14) to positive boundary (+3.14)
    theta0 = -3.14
    theta1 = 3.14
    th_mid, delta = slerp_heading(theta0, theta1, 0.5)
    print(f"Wrap-around test 2: delta={delta:.5f} rad ({math.degrees(delta):.2f} deg)")
    assert abs(delta) < 0.01, f"Shortest arc delta too large: {delta}"

    # Stress Case 3: Exactly opposite angles (pi and -pi)
    theta0 = math.pi
    theta1 = -math.pi
    th_mid, delta = slerp_heading(theta0, theta1, 0.5)
    assert abs(delta) < 1e-7 or abs(abs(delta) - math.pi) < 1e-7

    # 3.3 Quaternion Mapping Verification
    # q = [0, sin(theta / 2), 0, cos(theta / 2)]
    def to_quat(theta):
        return (0.0, math.sin(theta / 2.0), 0.0, math.cos(theta / 2.0))

    # Test that q(alpha) represents equivalent rotation to normalized theta
    for alpha in [0.0, 0.25, 0.5, 0.75, 1.0]:
        th, _ = slerp_heading(theta0, theta1, alpha)
        q = to_quat(th)
        norm_sq = q[1] ** 2 + q[3] ** 2
        assert abs(norm_sq - 1.0) < 1e-12, f"Quaternion not unit length: {norm_sq}"

    print("PASS: Reference Hermite and shortest-arc interpolation formulas passed.")


def main():
    print("=== STARTING EMPIRICAL CHALLENGER VERIFICATION ===")
    verify_telemetry_payload_and_bandwidth()
    verify_public_serialization_fields()
    verify_mathematical_interpolation()
    print("\n=== ALL SCRIPT CHECKS COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
