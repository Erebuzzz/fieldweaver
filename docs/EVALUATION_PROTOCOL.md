# Evaluation protocol

## Fixed run matrix

Run the suite from the repository root:

```powershell
.\backend\.venv\Scripts\python.exe scripts\run_evaluation.py
```

The current matrix contains seven scenarios and ten paired seeds: 42 through 51.
Each scenario and seed is run once with the quadratic estimator and deterministic
offline agent, then once with the weighted-centroid baseline and agent disabled. This
produces 70 observations per controller and 140 runs total. The controller pair shares
scenario, seed, mission, and duration limits.

Scenarios cover open field, noisy field, a restricted corridor, a seeded dynamic
obstacle change, a near-boundary source, an infeasible enclosure, and a far-source
timeout. The far-source mission duration is explicitly capped at 20 seconds. Other
trials use the mission default of 90 seconds. Simulation step size is 0.1 seconds.

The script computes success counts, termination reasons, and per-metric mean, median,
sample standard deviation, and non-null sample count from each run's evaluator output.
Obstacle-clearance metrics are null for scenes without obstacles, so their contributing
sample count is lower. No success-only filter is applied. The JSON report includes all
140 runs and the configuration details.

The raw report is written to `artifacts/evaluation_report.json`; `.gitignore` excludes
that generated output. The same report is copied to
`frontend/public/evaluation-report.json`, which is the checked-in data source for the
`/evaluation` page and its downloadable JSON. Regenerate this snapshot whenever the
scenario matrix or simulator behavior changes. The measured values and limitations
are summarized in `EVALUATION_RESULTS.md`.

## Agent evidence

The `disturbed_corridor` scenario activates a dynamic obstacle at a scheduled simulation
time. Recovery counts only when the quadratic run succeeds and records at least one
replan. The report includes disturbance trials and recovery rate, decision and replan
counts, provider mode, and live-call flags. Invalid or unsafe model output is covered
by backend unit tests, not counted as a simulated recovery trial.

Live inference latency remains null with a sample count of zero when the suite uses the
offline mock. Local `wall_clock_ms` is recorded for each complete simulation run, but
it is not reported as model inference latency. When live credentials are available, a
separate live check is required before making live latency or model-performance claims.

## Interpretation limits

- Ten seeds provide a larger deterministic sample, not broad robustness evidence.
- The baseline deliberately uses a weaker weighted-centroid estimator but shares the
  same formation objective and safety layer. It is not a general navigation benchmark.
- Scenario geometry and the timeout cap are fixed. Results do not establish performance
  on arbitrary arenas or source distributions.
- Wall-clock timings vary with host load and are not part of trajectory determinism.
- Offline agent outcomes do not establish live model decision quality or latency.
- A safe `route_infeasible` or timeout remains a failed task and stays in the report.

The tests in `backend/tests/test_evaluator.py` use hand-checkable fixture runs to verify
metric calculations and preserve specific termination causes.

## Held-out nominal scenarios

A separate evaluation uses seeds 52 through 61 for each of `open_field`, `noisy_open`,
`restricted_corridor`, and `disturbed_corridor`. These seeds are disjoint from the fixed
paired report. It uses the quadratic controller and deterministic mock agent; it is not
a paired baseline comparison and makes no live inference calls.

```powershell
.\backend\.venv\Scripts\python.exe scripts\run_heldout_evaluation.py
```

The generated `artifacts/heldout_evaluation_report.json` records each trial and is
ignored by Git. The held-out sample is a limited test, not a general safety guarantee.
