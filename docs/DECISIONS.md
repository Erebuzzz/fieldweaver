# FieldWeaver Decisions

## D001: Monorepo with an isolated simulation core

Decision: use `backend/` (Python) and `frontend/` (Next.js) with the simulator,
controller, safety, and evaluation written as plain Python modules.

Reason: the core must be unit-testable without HTTP, browser, or model credentials.
FastAPI only adapts the core to HTTP. This also keeps the hidden-truth boundary clear.

## D002: Holonomic point robots for the MVP

Decision: 3 to 8 holonomic point robots, explicit Euler at 0.1 s, speed-limited
velocity commands, heading derived from velocity.

Reason: the hackathon thesis is mission compilation, source localization, formation,
and independent safety. A unicycle model adds controller tuning without improving the
evidence. The dynamics are documented and testable. A unicycle model remains future work.

## D003: Quadratic least-squares estimator, not a claimed paper reproduction

Decision: estimate the source from scalar measurements by fitting the known isotropic
quadratic field shape with regularized least squares. Reject ill-conditioned or
negative-curvature fits and retain the previous estimate.

Reason: it is transparent, gradient-free, deterministic, and directly testable. No
published algorithm is claimed as faithfully reproduced. The prior-risk-aware and
source-localization repositories are background context only.

## D004: Baseline uses the same formation and safety, weaker estimator

Decision: the baseline shares dynamics, ring objective, and safety filter, but replaces
the quadratic estimator with an inverse-measurement weighted centroid and uses no agent
replans.

Reason: comparing estimators isolates the contribution of the proposed localization
method. It also makes the comparison honest: the baseline is not deliberately sabotaged
by removing safety.

## D005: Safety filter is independent and has final authority

Decision: the controller never writes robot state directly. Every proposed command passes
through a safety filter and post-step validator. If the filter cannot find a safe
transition, it reverts to the previous safe state and records an intervention.

Reason: model output and controller behavior are untrusted. Metrics must be computed from
actual safe trajectories, and unsafe runs must never be reported as successful.

## D006: Detours use a deterministic route per robot and ring slot

Decision: `switch_search_pattern` maps to deterministic ring-slot assignment followed
by an independent A* grid route from each robot to its assigned slot. The follower
combines per-robot route lookahead with obstacle and inter-robot separation repulsion.
Every route must end at its assigned slot. If any route cannot be planned or validated,
the application terminates with `route_infeasible` rather than moving that target to a
nearby free cell. The model chooses only the action enum.

Reason: the model must not produce executable plans or touch controller gains. A tested
deterministic action is auditable and can be rejected when no safe route exists. A
shared column target produced crossing paths around the enclosure in seeded trials and
was removed. Reusing the ring controller's separation repulsion prevents the detour
team from bunching at the wall.

## D007: Offline mock is explicit, not a silent fallback

Decision: when `BASETEN_API_KEY` is absent, the default provider mode is a deterministic
mock compiler and decision provider, labelled `mock` in every response and in the UI.
Forcing `live` without a key returns an error instead of silently using the mock.

Reason: the project must remain fully usable offline without falsely claiming live model
usage. Live provider metadata is recorded only when a real HTTP request succeeds.

## D008: HTTP calls via httpx instead of the OpenAI SDK

Decision: call the documented OpenAI-compatible `/v1/chat/completions` endpoint with
`httpx.AsyncClient`, injecting a transport in tests. The official OpenAI SDK remains a
valid alternative, but is not required by the endpoint contract.

Reason: one fewer dependency, explicit timeout/error mapping, and straightforward
`MockTransport` tests for 401, 429, timeout, and malformed responses. The request shape
matches the official Baseten Chat Completions contract checked on 2026-10-29.

## D009: No JSON-schema response format by default

Decision: instruct the model to return JSON, parse the content explicitly, and validate
with the application schema. Do not depend on `response_format` structured output by
default, because model-specific support for the exact hackathon slug is not verified
without a live key.

Reason: the build plan explicitly requires application-side validation regardless of
server-side constrained output. A configurable flag can be added only after a live check.

## D010: Persist evaluation evidence as a small JSON report

Decision: the evaluation suite writes the full report to ignored
`artifacts/evaluation_report.json` and the checked-in
`frontend/public/evaluation-report.json` snapshot. The `/evaluation` page renders that
same JSON, while `docs/EVALUATION_RESULTS.md` records the configuration and measured
summary.

Reason: UI values must match saved evaluation JSON, and claims in the README must be
traceable. The checked-in data is generated from actual runs, not hand-entered.

## D011: No SAM integration without verified access

Decision: Phase 5 remains deferred. The UI will state that scene upload is unavailable
and use built-in scenarios. No mock SAM output will be presented as a model result.

Reason: the Baseten hackathon key is for Muse Spark Open only, and no verified SAM 3.1
endpoint or credential is available in this environment.

## D012: The latest-evaluation route is process-local

Decision: `GET /api/evaluations/latest` returns the latest run stored in the current
FastAPI process. It remains separate from the static paired report rendered by the
`/evaluation` page.

Reason: a database or report-serving layer is outside the current vertical slice. The
API documentation must not describe the in-memory latest-run response as a persisted
suite summary.

## D013: Evaluation uses ten shared fixed seeds

Decision: the checked-in suite compares the quadratic controller and weighted-centroid
baseline across seven scenarios with shared seeds 42 through 51. It retains every
failure and reports mean, median, sample standard deviation, and non-null sample count.

Reason: one seed per scenario did not show any cross-seed variation. Ten paired seeds
provide a more useful reproducible spread estimate while keeping the local suite under
one minute on the verified development environment. This sample does not establish
broad robustness.

## D014: Let Baseten apply the documented completion budget (superseded by D016)

Decision: omit `max_tokens` for default Muse Spark requests and preserve an explicit
override only for callers that need one. If the provider reports an empty final answer
with `finish_reason: "length"`, return an output-limit error message without logging
the response body. Continue to parse the final answer from `message.content`.

Reason: Baseten's Chat Completions docs set the default output budget to 4096 tokens.
Its reasoning guide says the unversioned Muse Spark Open model always reasons and that
reasoning tokens count toward the completion budget. Applying that model behavior to
the hackathon slug is an inference; the exact `-1026` variant was not independently
verified. The two approved smoke requests used caps of 8 and 128, and both returned
empty content. This makes budget exhaustion plausible, but the raw responses were not
captured, so the cause is unconfirmed. The API default now leaves space for both
reasoning and the final response. The exact hackathon model ID remains
`meta-models/muse-spark-open-1026`. Checked October 30, 2026:
[Chat Completions](https://docs.baseten.co/reference/inference-api/chat-completions),
[reasoning](https://docs.baseten.co/inference/model-apis/reasoning),
[quickstart](https://docs.baseten.co/quickstart).

## D015: Use the shared shell for the not-found page

Decision: render Next.js's app-wide `not-found.tsx` with the shared FieldWeaver header
and footer, an illustrative route map, and direct links to the workbench and field guide.

Reason: a lost route should preserve the existing graphite, amber, and mint visual
language and provide a clear way back into the product. The map is explicitly an
illustration and exposes no fake coordinates, local host address, or simulation state.

## D016: Keep 3D visualization passive and browser-side

Decision: use Three.js to render the existing run data in the browser, keep the SVG view
available, and fall back to SVG if WebGL initialization or context fails. Do not add
Blender, MuJoCo, or Isaac Sim to the runtime just for visual polish.

Reason: the browser view improves spatial presentation without creating a second
simulation authority. Blender remains an option for authoring exported assets. MuJoCo
and Isaac Sim are better justified by future contact-dynamics or sensor-realism goals,
which require their own implementation and validation. Production browser checks
confirmed WebGL2 rendering, camera controls, the 2D view, and context-loss fallback.

## D016: Bound verified live inference and retain safe failures

Decision: set a 4096-token cap for mission and agent completions. Include the
deterministically computed direct-path obstruction in agent event observations and
leave the safety filter authoritative. Apply a controller-side closing-velocity
projection near neighboring robots without changing the safety envelope or benchmark
success criteria. SAM 3.1 is outside the build scope.

Evidence: November 4 live mission and dynamic-obstacle agent trials each succeeded;
an earlier constrained live-agent trial exhausted its decision budget. The fixed
evaluation achieved 40/70 quadratic task successes, including 30 retained expected
failures. These isolated checks are not a formal safety or model reliability proof.
