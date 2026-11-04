# Evaluation results

Generated on 2026-10-30. Configuration: seeds 42 through 51; seven scenarios; 70
paired runs per controller; 140 total runs; `dt = 0.1 s`. The proposed controller used
the deterministic offline agent. The baseline used the same formation objective and
safety filter with a weighted-centroid estimator and no agent. The evaluation made no
live inference requests.

## Task outcomes

| Controller | Success | Termination counts |
| --- | ---: | --- |
| Quadratic estimator | 31 / 70 (44.3%) | 31 nominal convergence, 21 route infeasible, 18 timeout |
| Weighted-centroid baseline | 0 / 70 (0%) | 70 timeout |

Every run is retained, including safe failures and expected infeasible or timeout
scenarios. The results describe this fixed matrix only. They do not establish general
controller superiority.

## Scenario outcomes

| Scenario | Quadratic successes | Quadratic failures | Baseline successes |
| --- | ---: | ---: | ---: |
| Open field | 9 / 10 | 1 timeout | 0 / 10 |
| Noisy open field | 2 / 10 | 1 route infeasible, 7 timeout | 0 / 10 |
| Restricted corridor | 10 / 10 | 0 | 0 / 10 |
| Disturbed corridor | 10 / 10 | 0 | 0 / 10 |
| Near boundary | 0 / 10 | 10 route infeasible | 0 / 10 |
| Infeasible enclosure | 0 / 10 | 10 route infeasible | 0 / 10 |
| Far source | 0 / 10 | 10 timeout | 0 / 10 |

## Trajectory metrics

Values are mean / median / sample standard deviation. Units are metres except for
simulation duration in seconds and safety interventions, which are counts. Obstacle
clearance has 30 samples per controller because it is unavailable in scenes without
obstacles.

| Metric | Quadratic, n=70 (or n=30) | Baseline, n=70 (or n=30) |
| --- | ---: | ---: |
| Localization error | 0.000607 / 0.000008 / 0.001696 | 1.339563 / 0.466182 / 1.306191 |
| Formation error | 0.258352 / 0.227253 / 0.215368 | 0.969127 / 0.415839 / 0.970807 |
| Minimum robot separation | 0.424600 / 0.403846 / 0.084447 | 0.937682 / 0.884533 / 0.127562 |
| Minimum obstacle clearance, n=30 | 0.225679 / 0.202864 / 0.036685 | 0.203286 / 0.203208 / 0.002627 |
| Total path length | 43.206386 / 46.833804 / 13.643553 | 71.437437 / 46.490877 / 66.091320 |
| Simulation duration | 37.654286 / 28.400000 / 24.099647 | 80.000000 / 90.000000 / 24.671759 |
| Safety intervention count | 174.214286 / 4 / 264.700809 | 390.571429 / 1 / 417.425775 |
| Robot collision count | 0 / 0 / 0 | 0 / 0 / 0 |

The large differences between means and medians for path length and safety interventions
show that a mean alone would obscure variation across runs.

## Disturbance and agent outcomes

- `disturbed_corridor` recovered in 10 of 10 fixed-seed trials. Each trial recorded one
  bounded replan after the scheduled obstacle change.
- Across the 70 quadratic runs, the offline agent made 63 decision calls and 41 replans:
  0.90 calls and 0.59 replans per run on average.
- Live inference latency is unavailable. The suite made zero live requests and records
  a null latency with a sample count of zero.
- Invalid decision and unsafe-field rejection are tested with mocked provider responses;
  those tests are separate from the evaluation runs.

The checked-in [JSON report](../frontend/public/evaluation-report.json) is the source for
the `/evaluation` page. The script also writes the same report to the ignored
`artifacts/evaluation_report.json` path. Local wall-clock values vary by host and run.

## Limitations

Ten fixed seeds per scenario provide more variation evidence than the initial three-seed
sample, but still do not establish broad robustness. The quadratic controller succeeded
in 31 of 70 runs; all failures remain visible. The baseline timed out in every trial
under these settings. The near-boundary and infeasible-enclosure scenarios intentionally
exercise safe route rejection, while the far-source scenario is capped at 20 seconds.
The noisy-open results show limited success under the current seeded noise model. The
disturbance recovery sample uses a deterministic mock provider and does not establish
live model decision quality or latency.
