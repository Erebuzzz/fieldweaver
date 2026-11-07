# FieldWeaver build state

Updated November 4, 2026. This file records observed implementation and verification
status for the current checkout.

## Objective

Compile operator text into a strict mission, run a deterministic multi-robot source
localization simulation, enforce motion checks independently, and report metrics from
recorded trajectories. The live provider is Baseten Chat Completions with model
meta-models/muse-spark-open-1026 and a backend-only BASETEN_API_KEY.

## Current phase status

| Phase | Status | Evidence and remaining gate |
| --- | --- | --- |
| 0. Workspace and boundaries | Passed | Architecture, prior-work boundary, secret policy, and ignored local paths are documented. |
| 1. Runnable skeleton and contracts | Passed locally | FastAPI and Next.js start. Strict schemas, request IDs, API tests, and smoke flow pass. |
| 2. Deterministic world | Passed locally | Seeded scenarios, reproducible observations, public telemetry, and hidden-source tests pass. |
| 3. Controller and safety | Passed for tested acceptance cases | Ring-slot detours terminate at their assigned targets; separation repulsion and independent safety checks are tested. |
| 4. Baseten compiler | Passed for exercised live and mock cases | Live API compilation and browser compilation passed strict validation with Muse Spark Open. |
| 4B. Bounded agent loop | Passed for exercised live and mock cases | A live obstacle event requested a validated detour and converged; mock recovery passed 10 seeds. |
| 5. SAM 3.1 | Out of scope | Excluded by the user; no integration is planned. |
| 6. Evaluation | Passed for fixed protocol | 40/70 task successes, 30 retained expected-failure trials, and 10/10 mock disturbance recoveries; a separate 40-run held-out nominal sample passed. |
| 7. Product integration | Passed locally for tested paths | Offline compile and run, responsive pages, Three.js render, camera modes, SVG fallback, WebGL context-loss fallback, and custom 404 are browser-checked. A fresh source snapshot with current uncommitted changes passed install and checks. |
| 8. Demo and submission | Partial | The three-minute storyboard exists, but no timed spoken rehearsal was recorded. Participant-portal rules were not reviewed, and no submission occurred. |

The simulator, live Baseten compiler, and live agent have passed the exercised paths.
The clean source snapshot passed installation and smoke checks. Recording and timed
rehearsal remain; live reliability and physical-device accessibility remain limited.

## Implemented behavior

- FastAPI health, public scenario, compile, run, and latest in-process evaluation routes.
- Strict Pydantic mission and agent-decision schemas with unknown-field rejection,
  numeric limits, unsupported-request clarification, and provider error mapping.
- Baseten adapter with documented Chat Completions path, timeouts, transient-error
  handling, and injected HTTP transport tests.
- Deterministic mock compiler and decision provider. The browser labels provider mode.
- Seeded scalar field, hidden source state, holonomic robot dynamics, quadratic
  estimator, and weighted-centroid baseline.
- Order-preserving ring assignment and a deterministic A* route for each assigned ring
  slot. Missing routes terminate as route_infeasible. Targets are not shifted to nearby
  cells. The detour follower includes inter-robot separation repulsion.
- Independent pre-step and post-step checks for separation, obstacles, boundaries,
  speed, and finite state, with recorded interventions.
- Bounded event-driven orchestration. Default limits are two model calls and two
  replans per run. No model call is made in the per-tick controller loop.
- Responsive Next.js workbench, mission review and approval, run metrics, agent trace,
  safety events, dedicated guide and policy pages, MIT license page, and custom 404.
- Browser-side Three.js presentation using the existing run data, perspective,
  top-down, and follow camera modes, and an SVG 2D fallback.
- Ten-seed evaluation generator and public report at
  frontend/public/evaluation-report.json.

## Evaluation evidence

The checked-in snapshot records 140 runs: two controllers, seven scenarios, and seeds
42 through 51.

- Quadratic estimator: 40/70 successes, 20 route_infeasible terminations, 10 timeouts.
- Weighted-centroid baseline: 0/70 successes; all 70 runs timed out.
- Disturbed-corridor deterministic mock recovery: 10/10 trials.
- Robot collisions: zero in both controller samples.
- The evaluation report uses mock inference; live inference has individual smoke checks only.

These results describe only the listed configurations and seeds. They do not establish
general controller superiority or live-agent performance. The evaluation page renders
the same JSON snapshot.

## Earlier commands and observed results

The following historical checks preceded the latest controller and provider changes.

| Command | Result |
| --- | --- |
| From backend: .venv\Scripts\python.exe -m pytest -q | Passed all 99 collected tests. Existing pytest-asyncio and Starlette/httpx deprecation warnings remain. |
| From backend: .venv\Scripts\ruff.exe check app tests ..\scripts | Passed: all checks passed. |
| From frontend: npm ci | Completed: 352 packages installed. npm reported 16 moderate vulnerabilities in development dependencies and none in production dependencies. |
| From frontend: npm run typecheck | Passed: tsc --noEmit. |
| From frontend: npm run lint | Passed: ESLint clean. |
| From frontend: npm run build | Passed: optimized Next.js build with workbench, guide, evaluation, privacy, security, license, icon, and not-found routes. |
| From backend: .venv\Scripts\python.exe ..\scripts\smoke_test.py | Passed health, public scenarios, mock compilation, seeded run, and latest evaluation; success=true at 14.4 simulated seconds. |
| From backend: .venv\Scripts\python.exe ..\scripts\verify_m3_contracts.py | Passed punctuation, client-secret, documentation-route, and public evaluation report checks. |
| From backend: .venv\Scripts\python.exe ..\scripts\verify_empirical_telemetry.py | Passed public serialization field checks and reference interpolation calculations. Sampled 612 frames. |
| npm audit --omit=dev | Zero production dependency vulnerabilities at the time of the check. |

Telemetry measurements are compact JSON serialization sizes, not captured network
traffic. At ten frames per second, one typical five-robot frame estimates to 5.85 KB/s
before HTTP overhead or compression. The reference interpolation script tests its own
formulas, not the Three.js renderer.

## Browser verification

A production build was opened with a local FastAPI backend.

- Offline mock mission compiled into a validated specification, required operator
  approval, and ran with seed 42. The run converged in 14.4 simulated seconds and
  reported zero collisions and zero safety interventions.
- The 3D canvas created a WebGL2 context. Perspective, top-down, and follow controls
  worked. Switching to 2D rendered the SVG view.
- Triggering the browser WebGL_lose_context extension removed the 3D canvas and exposed
  the 2D SVG fallback with a visible notice. The intentional context-loss event logged
  one browser warning and no JavaScript errors.
- At a 320 px viewport, the workbench, guide, evaluation, privacy, security, license,
  and 404 pages had no document-level horizontal overflow.
- A missing route returned HTTP 404 and rendered the custom page. The final page has no
  placeholder NaN coordinates, local host address, or claimed live measurements.
- The earlier React hydration mismatch caused by reading the audio preference during
  initial render was fixed. The preference now loads after hydration. The production
  page loaded with zero JavaScript errors.
- The local API smoke flow uses the deterministic mock. No Baseten request occurred in
  this browser pass.

## Privacy and security review

The privacy copy now discloses the one browser-local value: the tactical-audio mute
preference. The app sets no application cookies or analytics trackers. Live prompt and
event content is sent to Baseten only when the operator selects live mode or automatic
mode with a configured backend key. The backend key is not exposed to the client.
Baseten's current Security Practices describe Zero Data Retention for Model APIs
inputs and outputs, subject to their terms and product configuration:
https://www.baseten.co/security-practices/

The API has no authentication or rate limiting and is documented for loopback local
use. Do not expose it to untrusted networks without additional access controls.

The current npm audit found 16 moderate vulnerabilities in development dependencies,
primarily the ESLint toolchain. The production dependency audit found zero. npm reports
that automatic fixes require major version changes, so no forced dependency upgrade was
applied. Reassess the toolchain before a hosted deployment.

The local .env was not opened or copied into this report. Git ignore rules cover .env
and brain/. The public evaluation artifact was checked for hidden-source field names.

## Remaining gates

1. Live Baseten call after the adapter budget change. The two prior separately approved
   generic calls returned empty content at caps of 8 and 128. A new call can consume
   credits and needs fresh user approval. No mission data was sent in the earlier calls.
2. Clean-checkout reproduction of documented Python and npm install commands. npm ci
   ran against the current worktree, not a clean clone.
3. Timed three-minute demo rehearsal and participant-portal review.
4. SAM 3.1 remains optional and disabled.
5. Review the moderate development-tool dependency advisories and decide whether a
   planned major toolchain upgrade is warranted.

No deploy or hackathon submission occurred.

## 2026-11-04 UI readability pass

- Increased small text across the frontend, widened the arena, placed evaluation beneath the primary workspace, and added collapsible advanced settings and run trace.
- Replaced the header mark and favicon with an original SVG mark and added matching navigation icons.
- `npm run typecheck`, `npm run lint`, and `npm run build` passed. `git diff --check` passed with line-ending warnings only.
- At 390px the workbench, guide, evaluation, privacy, security, license, and 404 pages had no document overflow. A browser run using mock compiler and mock agent converged; the 3D canvas was present. Both disclosure controls opened.
- Pixasso and Blender MCP tools were absent from the current tool list and plugin searches returned no matching plugins. The requested Pixasso-led complete refactor and Blender asset work remain unfinished. The current changes remain uncommitted for continuation.

## 2026-11-04 focused workspace views

- Pixasso fetched the Wensity reference and was used to map the design direction. The existing custom SVG mark and navigation symbols were preserved.
- The mission and arena now share one view; run evaluation and the expandable agent/safety trace have a separate view. A completed run links to its results. Common 12 px and 13 px CSS text sizes were increased to 14 px and 15 px, and the body default is 16 px.
- From frontend: `npm run typecheck`, `npm run lint`, and `npm run build` passed. `git diff --check` passed with line-ending warnings.
- A production browser session used the offline mock compiler and agent, approved a mission, and showed a converged result. Switching to results and back retained a 3D canvas. At a measured 375 px document width, the workbench, guide, evaluation, privacy, security, and license routes had no document-level horizontal overflow. The browser reported no console errors in this check.
- The Blender MCP tools exist, but two scene inspections returned connection errors at localhost:9876. Blender is running, but the add-on server was not listening. No Blender asset was created or verified.
- This is a focused interface pass, not completion of the requested full redesign. Further visual and accessibility review, custom asset refinement, and Blender work remain. No live Baseten request, deployment, or submission occurred.

## 2026-11-04 Blender connection and rover prototype

- The community `ahujasid/mcp-for-blender` add-on responded through its local socket bridge. The available official Blender MCP tool did not complete a scene request against this different add-on protocol.
- Scene inspection found the default cube, camera, and light. A separate `FieldWeaver Rover Prototype` collection was added without deleting those objects. The scene remains open in Blender and has not been saved by this operation.
- Exported `frontend/public/models/fieldweaver-rover-prototype.glb`: GLB version 2, 38,412 bytes, nine mesh nodes and three materials. A Node script checked the GLB header, length, JSON, and presence of meshes.
- The prototype is not integrated into the application and has not been visually reviewed or tested in the arena. It does not yet reproduce the existing animated wheels, per-robot color, sensor response, or trail. Preserve the existing procedural rover until those behaviors and rendering are validated.
- Next: inspect the prototype visually, decide whether it improves the arena, and integrate with a fallback only after animation, disposal, playback, hidden-source, and responsive checks pass.

## 2026-11-04 official Blender bridge check

- The official Blender MCP `get_objects_summary` returned successfully after the community server was stopped. It reported the original camera, cube and light plus the separate nine-object `FieldWeaver Rover Prototype` collection.
- Focused the 3D viewport on `FW chassis` and inspected a Blender viewport screenshot. The prototype is a compact four-wheel chassis with a sensor mast and identification spine. The screenshot is a Blender viewport check, not verification of the exported GLB in the browser.
- The prototype remains unintegrated. Browser rendering, wheel and sensor animation, per-robot colors, disposal, fallback and simulation-boundary checks are still needed before replacement of the existing rover.

## 2026-11-04 Blender rover integration

- `frontend/src/components/arena-3d/robot-mesh.ts` loads the Blender-authored GLB for each rover and replaces its procedural visual only after checking for the sensor, identification spine, and four wheels. The existing procedural rover remains in place on load or validation failure. The loaded sensor and spine receive the robot's team color; the sensor, wheels, pose, and existing trail continue to use run data. Late loads after disposal are discarded.
- From `frontend`, `npm run typecheck`, `npm run lint`, and `npm run build` passed. `git diff --check` passed with line-ending warnings.
- A Node/Three.js check parsed the actual GLB and exercised the model swap, per-robot color, wheel quaternion update, pose update, and a load completing after rover disposal. An initial assertion incorrectly expected disposed meshes to be removed from their detached group; the corrected check verified that the late-loaded model was not attached. The test emitted a Three.js CommonJS deprecation warning.
- A production browser session explicitly selected the offline mock compiler and agent, compiled and ran a mission, and received HTTP 200 for the GLB. Perspective, top-down, follow, manual 2D fallback, and results navigation were exercised. A second run intentionally blocked the GLB request: the 3D canvas remained available. Forcing WebGL context loss then showed the SVG arena and a fallback notice. The deliberate blocked request caused one console error and the forced context loss caused one warning.
- This confirms the exercised mock workflow and fallback behavior. No live Baseten request occurred. The full frontend redesign and the project's prior release gates remain incomplete.

## 2026-11-04 frontend studio refactor

- Used Pixasso to analyze the Wensity reference and establish a restrained interface direction. Wensity was used as inspiration; no Wensity package or component source was installed or copied. Pixasso reference catalog search returned an internal error; its generated audit was based on a design description, not a substitute for browser testing.
- Refactored the workbench into Mission, Arena, and Run results views. A run opens the arena; the mission review and explicit approval gate remain in place. On narrow screens the mission view omits the arena preview, which remains available through the Arena view.
- Rebuilt the 3D/2D, camera, sound, and fullscreen controls with accessible pressed states, custom SVG controls, larger targets, and responsive wrapping. Fullscreen state follows browser fullscreen changes. Shared header, navigation, typography, surfaces, spacing, and document styles were updated; the existing custom SVG logo and navigation icons were retained.
- From frontend: `npm run typecheck`, `npm run lint`, and `npm run build` passed. `git diff --check` passed with line-ending warnings. No backend code was changed for this refactor.
- Production browser checks: explicitly mocked compiler and agent compiled, reviewed, approved, and ran a mission; running without approval was disabled. The arena opened after the run, the GLB returned HTTP 200, perspective/top-down/follow and 2D controls were exercised, and results were shown. At 320, 390, and 1440 px, the workbench, guide, evaluation, privacy, security, license, and missing route had no document-level horizontal overflow; the missing route returned 404. Forced WebGL context loss at 320 px showed the 2D arena and notice, producing the expected WebGL warning. The tested workflow had no page errors.
- No live Baseten request, paid usage, deployment, or submission occurred. The existing live-provider, clean-checkout, and demo gates remain open. These checks do not constitute a comprehensive accessibility audit or testing on physical mobile devices.

## 2026-11-04 free Wensity component

- Adapted the ring variant of Wensity's free MIT spinner for mission compilation and simulation startup. The local implementation uses the existing CSS system and includes the Wensity MIT license in `frontend/src/components/wensity/LICENSE`; no dependencies or paid assets were added. Source: https://github.com/ksparth12/wensity-shadcn-registry/blob/main/spinner.json.
- From frontend: `npm run typecheck`, `npm run lint`, and `npm run build` passed. In the production browser, deliberately delayed offline mock compile and run requests each exposed the labeled spinner, and the approved run completed. No live Baseten request occurred.

## 2026-11-04 controller, live provider, and clean-source checks

- Research context: a local inspection of the developer's prior work and the paper on
  [prioritized multi-robot planning](https://arxiv.org/abs/1409.2399) informed the
  investigation of coordination deadlock. This controller does not implement or claim
  to reproduce that paper. Existing research code, assets and results were not copied.
- Added a deterministic pairwise closing-velocity adjustment near the separation
  boundary in the ring controller. The independent safety filter and post-step checks
  remain authoritative; the adjustment is not a formal safety guarantee. Regression
  tests exercise the near-pair behavior and two previously failing noisy seeds.
- The original fixed paired matrix was rerun without changing scenarios, seed range,
  mission limits, or success criteria. Quadratic: 40/70 successes, 20 route-infeasible,
  10 timeouts; baseline: 0/70 successes, 70 timeouts. All 30 expected boundary,
  enclosure, and short-budget trials remain task failures. Both controllers reported
  zero robot collisions in this sample. The previous quadratic result was 31/70.
- Independently reran four nominal scenarios over held-out seeds 52 through 61: 40/40
  successes and zero reported collisions. `scripts/run_heldout_evaluation.py` reproduces
  this separate mock-provider check and writes an ignored JSON artifact. The held-out
  sample is not a paired baseline or proof of general reliability.
- Added a deterministic public-map direct-path obstruction flag to agent observations.
  It does not expose source truth and does not establish a safe route for each robot.
  Agent and compiler live calls now use a 4096-token cap; mock transport tests check it.
- Approved live calls used Baseten `meta-models/muse-spark-open-1026`: a bounded direct
  mission compile passed (2048-token cap, no retries, 2480 total tokens); an actual
  API compile returned a valid specification (3047 total tokens) and its agent-off
  open-field run converged with zero collisions. An initial one-decision dynamic run
  chose a cautious profile and ended `replan_budget_exhausted`. After the obstruction
  observation and prompt update, one live dynamic run requested one validated detour
  and converged with zero collisions. These are individual trials, not a reliability
  or latency study.
- The production browser then used live compilation and live agent mode for the dynamic
  barrier at seed 42. It showed Baseten live, required approval, recorded one live
  decision and one replan, and converged with zero recorded safety interventions. Its
  actual evaluated metrics included zero collisions. The initial browser automation
  attempt timed out on an incorrect selector before making an inference request; the
  corrected attempt succeeded.
- Clean source reproduction: created an ignored source snapshot from `git archive HEAD`
  plus current modified tracked files and explicitly selected untracked runtime/test
  files, without copying `.env`. Fresh Python venv and editable install, `npm ci`,
  backend 108 tests, backend Ruff, frontend lint/typecheck/build all passed. The first
  API smoke attempt failed because its server was not running; after starting the
  snapshot's backend, `scripts/smoke_test.py` passed in offline mock mode. This is a
  clean source snapshot with overlaid uncommitted work, not an independently cloned
  published commit.
- Current checkout: backend 108 tests and Ruff passed; frontend production build passed;
  release-artifact and telemetry scripts passed. The recorded Node audit reported zero
  production vulnerabilities and 16 moderate development dependency advisories. npm's
  automatic recommendation proposed major-version downgrades, which were not applied.
  Existing pytest-asyncio and Starlette/httpx deprecation warnings remain.
- User excluded SAM 3.1 from the build. The demo script now targets live Baseten, with
  an explicitly labeled mock fallback. A spoken rehearsal and recording remain undone.
  The public organizer page lists the submission due November 4 at 9 PM ET; the exact
  participant portal fields and requirements were not verified, and no submission,
  deployment, push, or publication occurred.
- Organizer review: the public event page and the organizer's November 3 reminder
  give a November 4, 9:00 PM ET submission deadline (November 5, 7:30 AM IST). The
  reminder asks for a three-minute demo and an open-source GitHub repository. The
  existing `origin` repository is public, but the latest work is uncommitted and has
  not been pushed. The exact submission form redirects to login in the available
  browser, so its fields were not inspected. Publishing or pushing requires explicit
  user approval under project rules.
- The held-out script was also copied into the clean source snapshot and rerun there:
  all four ten-seed nominal scenario groups passed; the snapshot's Ruff check passed.
- The user explicitly deferred submission and form review for now. Keep the finished
  changes local; do not commit or push as a side effect of preparing the demo.

## 2026-11-04 swept robot separation guardrail

- The transition validator now checks closest approach between pairs of robots during each linearly integrated timestep, in addition to endpoint separation. It rejects changed robot identities in a transition. This covers robot-to-robot crossings, not swept obstacle clearance or physical-system safety guarantees.
- `backend\.venv\Scripts\python.exe -m pytest tests/test_safety.py -q`: 14 passed. `backend\.venv\Scripts\python.exe -m pytest -q`: 110 passed. `backend\.venv\Scripts\python.exe -m ruff check app tests`: passed. Existing pytest-asyncio and Starlette warnings remain.
- The previously reported evaluation predates this guardrail and must be rerun before applying its numbers to the changed simulator. Provider BYOK, Meta and Fireworks adapters, model selection, new swarm/arena presets, expanded evaluation and browser verification remain outstanding. No new live inference calls were made.
- Meta Model API documents `https://api.meta.ai/v1` and a bearer token at https://dev.meta.ai/docs/api-reference. Its current model access and live behavior remain unverified for this project.

## 2026-11-04 evaluation after swept separation guardrail

- `.\backend\.venv\Scripts\python.exe scripts/run_evaluation.py --help` ran the evaluation because the script does not parse command-line arguments. It completed successfully in offline mock mode, updated the evaluation artifacts, and made no live provider calls.
- Quadratic: 40/70 successes, with 20 route-infeasible and 10 timeouts. Baseline: 0/70 successes, all timeouts. Disturbed-corridor recovery: 10/10. This reproduces the previous aggregate results with the changed validator; limitations of the fixed cases and weak baseline remain.
- BYOK and model selection, provider adapters, presets, further guardrails, and end-to-end verification remain outstanding.

## 2026-11-04 provider selection and presets

- Added request-scoped selection for fixed Baseten, Meta Model API and Fireworks endpoints. Browser keys are held in page state and passed to the backend for live requests only. Model IDs are operator-provided with documented Meta suggestions. The default server settings remain Baseten. The backend uses the existing strict mission and agent validation. Meta and Fireworks have not been tested live.
- Added compact, balanced and wide ring mission presets. Arena selection uses the existing built-in scenarios. Presets alter mission text; the compiled specification must still be reviewed.
- Corrected browser privacy and security copy to describe browser-entered credentials. HTTPS is required for non-loopback browser and backend URLs. The application has no authentication and is not a secure public multi-user service.
- Backend full suite: 112 tests passed. `python -m ruff check app tests`: passed. Frontend `npm run typecheck`, `npm run lint`, and production `npm run build` passed before the final documentation and model-suggestion changes, which require a fresh build. Browser check against local frontend and a routed local backend: balanced preset compiled in mock mode to six robots and a 1.5 m ring, operator approval and agent-off simulation converged; selecting Meta without a key showed the expected error. No external live calls were made.
- Outstanding: re-run checks after final UI copy changes, inspect live provider behavior with user keys when available, complete broader preset and safety verification and honest evaluation presentation, and final demo rehearsal. Request-scoped mock tests do not prove real-provider compatibility.

## 2026-11-04 provider and evaluation verification

- Final backend `python -m pytest -q`: 114 passed. Final backend `python -m ruff check app tests`: passed. Mock-transport tests verify Meta and Fireworks Chat Completions URL, bearer authentication and model payload; no real credentials or external requests were used. Final frontend `npm run build`, `npm run lint`, and `npm run typecheck` passed.
- Browser checks used a local test proxy to direct the frontend to the current backend. The balanced preset compiled as six robots with a 1.5 m ring, was approved, and the agent-off mock run converged. Selecting Meta without a key displayed the expected validation message.
- Evaluation page now shows the four nominal scenarios and three stress scenarios separately while retaining all 70 runs in the overall total. It clarifies that the quadratic policy uses a mock recovery agent and the baseline does not.
- Remaining verification: live Meta and Fireworks with valid user keys, wider browser coverage of provider and preset interactions, swept obstacle-path safety (current new guardrail checks robot pairs only), demo rehearsal and recording. Do not claim those have passed. Public multi-user hosting is not supported without authentication and session isolation.

## 2026-11-04 interactive setup and walkthrough

- Added a six-step PowerShell setup guide with individual copyable commands, a read-only backend health check, and a five-step offline first-run walkthrough. The guide does not overwrite `.env` or send model requests.
- Replaced the API console's inaccurate hard-coded request and response examples with read-only health and scenario requests that show actual backend responses. Corrected provider and fixed-seed descriptions.
- Frontend `npm run typecheck`, `npm run lint`, and `npm run build` passed. Browser validation navigated both steppers, checked health and scenario responses via a local test proxy, verified the workbench link, and found no document-level horizontal overflow at 320 px. An initial browser check failed because the test proxy was not configured; retry with the proxy passed. No live model calls were made.

## 2026-11-05 Cloudflare inspection and icon alignment

- Replaced the license matrix text glyphs and workbench check/play glyphs with centered SVG icons. Frontend lint, typecheck and build passed. Browser geometry confirmed all three license SVG centers align with their circular frames at 1440px.
- Cloudflare account has an active erebuzzz.tech zone and no existing fieldweaver.erebuzzz.tech DNS record. No resource, DNS or deployment was changed. Cloudflare denied access to Containers, reporting that Workers Paid is required; the connector lacks billing-read permission. Docker is installed but its daemon was unavailable.
- Added a backend Dockerfile and dockerignore for a container deployment; the image has not been built or run. The existing unauthenticated backend, shared server key behavior and global latest-run state need protection before public deployment. See docs/CLOUDFLARE_DEPLOYMENT.md. No public URL or 24/7 availability has been verified.
- Follow-up: started Docker Desktop and built `fieldweaver-backend:local-check` successfully. The image ran without a provider key; `FIELDWEAVER_API_BASE_URL=http://127.0.0.1:18081 python scripts/smoke_test.py` passed in offline mock mode with a converged 14.4 s simulated run. This is a local container check, not a Cloudflare deployment. The public API isolation and Cloudflare Containers access blockers remain.

## 2026-11-05 Render preparation

- User selected Render, declined scheduled keep-alive requests, and requested server-side Baseten as the default with optional BYOK. Added a free Docker Blueprint with `FIELDWEAVER_PUBLIC_MODE=true`, the intended frontend CORS origin, and a `sync: false` placeholder for the server key. The key is not in this file.
- Public mode keeps the default server key server-side, disables shared latest-run storage and access, and applies a process-local limit of 12 compile/run requests per minute. The limit is shared across users, resets on restart, and is not a persistent spending cap or distributed abuse protection. The service still needs appropriate production access controls.
- Frontend retries failed startup connections for a bounded period to help with a sleeping Render service. This is not a scheduled keep-alive.
- Backend full suite: 116 passed; Ruff passed. Frontend typecheck, lint, and build passed. Blueprint YAML parsed locally; it has not been deployed or validated by Render. No Render account connection or public service was verified.

## 2026-11-05 Render and static export progress

- User authorized the public GitHub push. Commits `6f2e770` and `77d5442` were pushed to origin/main after an exact staged secret-value scan found no matches. Agent-private folders and `.env` were excluded.
- The frontend static export build succeeded with a placeholder API URL. It must be rebuilt with the real Render HTTPS URL once that service exists. No domain or frontend deployment has occurred.
- Render Blueprint setup was opened in the signed-in account for `Erebuzzz/fieldweaver`; service creation awaits entry of the Baseten secret in Render. No key was returned in tool output. No scheduled keep-alive is planned.

## 2026-11-05 public deployment

- Render deployed `fieldweaver-api` from the approved public repository. Its HTTPS URL is https://fieldweaver-api.onrender.com. The user configured the Baseten key directly in Render; no key was recorded in this log.
- Cloudflare Workers static assets serves https://fieldweaver.erebuzzz.tech. The static export was built with the live Render URL and uploaded through the dashboard. It is a manual upload and does not automatically update from Git.
- Verified HTTPS 200 for frontend root, guide, evaluation, license, and rover GLB. Render CORS preflight allowed the custom frontend origin. Actual Render API checks passed for health, seven scenarios, mock compile, and a seed-42 agent-off run. Public latest-run returned the expected 404. An actual live Baseten compile returned HTTP 200 using `meta-models/muse-spark-open-1026`.
- A browser run on the public site used the balanced preset, mock compilation and agent-off mode; it converged and displayed a 3D canvas. Meta and Fireworks remain live-unverified. No scheduled keep-alive was configured. Render Free can sleep; the backend is not guaranteed continuously available.
- Updated public guide/security copy and API reference link and redeployed static Worker version `5bad2af1`. Verified the public guide links to the Render API reference and the security page states the public demo limitation. The app has no user authentication; the process-local rate limit is not a persistent spending cap.

## 2026-11-05 swept obstacles and matched agent-off evaluation

- Added exact segment clearance for circle and axis-aligned rectangle regions during straight-line timestep motion. Regions activated during a step are checked only from their activation time. This is a simulation check for point robots and does not prove safety for physical robots or moving obstacles.
- Backend full test suite passed 119 tests and targeted safety tests passed 17; Ruff passed. The fixed suite reproduced 40/70 quadratic and 0/70 baseline, with 10/10 mock disturbance recoveries. The four held-out nominal groups each passed 10/10.
- A new agent-off ablation runs both controllers with identical agent settings: quadratic 20/40, baseline 0/40, zero reported collisions. The quadratic controller succeeded 10/10 in each open scenario and 0/10 in each corridor scenario. It is not a strong external research baseline.
- Live browser checks confirmed all three preset robot counts and the missing-key error for Meta. These checks exercised the previously deployed version, not the new swept-obstacle code. Live Meta and Fireworks remain unverified.

## 2026-11-05 shared-key daily allowance

- User selected a 250-request daily allowance for the public shared Baseten key. Added a Cloudflare D1-backed counter and private authenticated Worker, using atomic SQL updates by UTC date. The backend reserves before each shared-key attempt, including retries, and fails closed when the counter is unavailable or exhausted. BYOK and offline paths do not consume this allowance. This limits request count, not dollars; token cost can vary. The existing per-process short-term request limit remains.
- The worker rejected an unauthenticated request and accepted an authenticated reservation. A separate synthetic date boundary test accepted the 250th reservation and rejected the 251st. Render environment variables were merged without replacing existing secrets. Actual hosted enforcement remains pending backend deployment and end-to-end verification.
- Backend full suite passed 124 tests; Ruff passed. The frontend static build passed. Meta and Fireworks remain live-unverified because keys are not available.

## 2026-11-05 deployment verification for safety and quota

- Render deployed commit `edd68cf` and the public Cloudflare frontend was updated. One actual live Baseten compile returned HTTP 200 and increased the D1 counter from 1 to 2. A deliberately invalid BYOK Baseten request returned `provider_unauthorized`, did not echo the test key, and left the counter at 2. The provider key used in this negative test was not a credential.
- The public browser displayed the 250-request limit and matched agent-off evaluation and completed an offline agent-off run with nominal convergence. Cloudflare D1 boundary testing on a synthetic date accepted request 250 and rejected request 251; an unauthenticated counter request was rejected. UTC day resets do not imply a dollar spend cap. Any successful BYOK model call still requires a valid user key and remains unverified for Meta and Fireworks.
- The backend 124-test suite, Ruff and frontend production build passed. The backend has no user authentication, its rate limiter is process-local, and the daily shared-key counter enforces a request count rather than a spend guarantee. Render Free may sleep after inactivity; no keep-alive was configured.

## 2026-11-05 README setup guidance

- Updated README with hosted walkthrough, local setup, provider keys, troubleshooting, and evaluation caveats; updated security guidance.
- Local backend started with documented uvicorn command. scripts/smoke_test.py initially failed with connection refused when no backend was running, then passed health, scenarios, mock compile, seeded run, and latest evaluation after startup. No live model request was made.
- git diff --check passed for README.md and docs/SECURITY.md. No push or deployment performed. Meta and Fireworks live credentials remain unverified.

