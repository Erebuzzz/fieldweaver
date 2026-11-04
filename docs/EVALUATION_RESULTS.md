# Evaluation results

Generated from the checked-in [evaluation report](../frontend/public/evaluation-report.json) at 2026-11-04T16:55:33+00:00. The fixed matrix uses seven scenarios, seeds 42 through 51, two controllers, and 140 runs. The quadratic controller uses the deterministic mock agent; the baseline uses the same formation objective and safety filter with the agent off. The suite made no live inference requests.

## Task outcomes

| Controller | Success | Termination counts |
| --- | ---: | --- |
| Quadratic estimator | 40 / 70 (57.1%) | 40 nominal convergence, 20 route infeasible, 10 timeout |
| Weighted-centroid baseline | 0 / 70 (0.0%) | 70 timeout |

All runs remain in the denominator, including scenarios designed to produce safe failure. These results describe this fixed matrix, not general controller superiority.

## Scenario outcomes

| Scenario | Quadratic success | Quadratic termination counts | Baseline success |
| --- | ---: | --- | ---: |
| Open field | 10 / 10 | 10 nominal convergence | 0 / 10 |
| Noisy open field | 10 / 10 | 10 nominal convergence | 0 / 10 |
| Restricted corridor | 10 / 10 | 10 nominal convergence | 0 / 10 |
| Disturbed corridor | 10 / 10 | 10 nominal convergence | 0 / 10 |
| Near boundary | 0 / 10 | 10 route infeasible | 0 / 10 |
| Infeasible enclosure | 0 / 10 | 10 route infeasible | 0 / 10 |
| Far source | 0 / 10 | 10 timeout | 0 / 10 |

## Trajectory metrics

Mean / median / sample standard deviation. Missing obstacle-clearance values are excluded only from that metric.

| Metric | Quadratic | Baseline |
| --- | --- | --- |
| Localization error (m) | 0.0002 / 0.0000 / 0.0007 (n=70) | 1.3396 / 0.4662 / 1.3062 (n=70) |
| Formation error (m) | 0.2247 / 0.0457 / 0.2351 (n=70) | 0.9691 / 0.4158 / 0.9708 (n=70) |
| Minimum separation (m) | 0.4357 / 0.4134 / 0.0775 (n=70) | 0.9377 / 0.8845 / 0.1276 (n=70) |
| Obstacle clearance (m) | 0.2257 / 0.2029 / 0.0367 (n=30) | 0.2033 / 0.2032 / 0.0026 (n=30) |
| Total path length (m) | 44.2376 / 46.8314 / 12.5497 (n=70) | 71.4374 / 46.4909 / 66.0913 (n=70) |
| Simulation duration (s) | 28.4900 / 27.2000 / 15.0184 (n=70) | 80.0000 / 90.0000 / 24.6718 (n=70) |
| Safety interventions | 65.0143 / 0.0000 / 102.5746 (n=70) | 390.5714 / 1.0000 / 417.4258 (n=70) |
| Robot collisions | 0.0000 / 0.0000 / 0.0000 (n=70) | 0.0000 / 0.0000 / 0.0000 (n=70) |

## Agent evidence and limits

The disturbed corridor recovered in 10 of 10 deterministic mock trials, each requiring a recorded replan. Live agent quality and latency are not measured by this report. The near-boundary and sealed-enclosure cases intentionally test infeasibility; the far-source case has a fixed 20-second cap. Ten seeds per scenario do not establish broad robustness.

A separate held-out check used seeds 52 through 61 for each of the four nominal scenarios. The quadratic controller succeeded in 40 of 40 runs with zero reported robot collisions; this check is separate from the fixed paired report and does not establish a general safety guarantee.

## Agent-off comparison

A matched four-scenario, ten-seed ablation with agent decisions off for both controllers produced 20/40 quadratic successes and 0/40 weighted-centroid successes. Open field and noisy open field each produced 10/10 quadratic successes; both corridor scenarios produced 0/10. Both policies reported zero robot collisions. The agent-enabled fixed suite and this agent-off comparison answer different questions; neither establishes general reliability.
