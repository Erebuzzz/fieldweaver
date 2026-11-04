# Prior Work Boundary

FieldWeaver is a new hackathon implementation built in this repository during the
Meta Global AI Developer Hackathon build window. The developer's existing repositories
are background research context only.

## Prior work (context only, not copied)

1. `https://github.com/Erebuzzz/Risk-Aware-Hybrid-LQR-MPC-Navigation-for-Autonomous-Systems`
   - Background on risk-aware navigation and safety-aware control.
   - No source code, controller implementation, figures, assets, or simulation output
     from that repository was copied into FieldWeaver.
2. `https://github.com/Erebuzzz/SSL_n_F_DSGFA`
   - Background on scalar-field source localization research.
   - No source code, estimator implementation, plots, datasets, or results were copied.

No algorithm in FieldWeaver is presented as a faithful reproduction of a published
method. The implemented estimator is a straightforward regularized least-squares fit of
a documented isotropic quadratic field, selected for transparency and testability. Any
future claim of reproducing a paper requires checking the primary publication and
validating behavior against it.

## New work created during the hackathon window

- Next.js control-room interface with mission editor, mission specification review,
  Canvas arena playback, metrics, results, and agent trace.
- FastAPI service layer, strict Pydantic contracts, error envelopes, request IDs, and
  secret-free health reporting.
- Deterministic 2D arena, obstacles, restricted regions, seeded sensor noise, robot
  dynamics, and reproducible trajectory recording.
- Quadratic scalar-field estimator with conditioning and degeneracy handling.
- Ring-formation source-seeking controller and a separate weighted-centroid baseline.
- Independent geometric safety filter and post-step validator covering separation,
  obstacles, boundaries, speed, and numeric validity.
- Evaluator that recomputes metrics from recorded state and hidden ground truth.
- Baseten mission compiler adapter for `meta-models/muse-spark-open-1026`, strict
  application-side validation, explicit missing-key/offline behavior, and mock tests.
- Bounded event-driven orchestration loop, strict `AgentDecision` schema, per-robot A*
  detours to assigned ring slots, inter-robot separation repulsion, hard replan/call
  budgets, and an auditable event trace.
- Reproducible evaluation suite, scenario matrix, shared-seed baseline comparison, and
  saved machine-readable results.
- Documentation, demo script, and setup instructions.

## Public references

The implementation uses public API documentation for Baseten Chat Completions and the
build playbook in this repository. Technical algorithms are implemented independently
from standard mathematical descriptions. Third-party dependencies retain their own
licenses and notices.

Starting repository inspection found planning and instruction files but no tracked
application implementation. The simulator, service layer, API, UI, tests, and evaluation
scripts described above were added as new project work. The implementation was not
copied from the two research repositories listed above.

Last updated: October 30, 2026.

Additional private research supplied by the developer is also background context only.
Keep its contents and unpublished claims private. Do not copy its source, assets, or
results into FieldWeaver, and do not publish details without explicit authorization.
Research guarantees do not transfer to FieldWeaver without checking their assumptions
against this implementation and independently validating the relevant claims.
