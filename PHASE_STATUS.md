# FieldWeaver phase status

Updated November 4, 2026. Detailed evidence is in docs/BUILD_STATE.md.

| Phase | Status | Evidence or remaining gate |
| --- | --- | --- |
| 0. Workspace and boundaries | Passed | Architecture, prior-work boundary, environment template, and ignore rules. |
| 1. Runnable skeleton and contracts | Passed locally | FastAPI, Next.js, schemas, request IDs, API tests, startup smoke. |
| 2. Deterministic world | Passed locally | Seeded scenarios, repeatability, public telemetry, and hidden-source boundary tests. |
| 3. Controller and safety | Passed for tested cases | Shared-seed baseline, trajectory metrics, per-robot exact-slot detours, separation repulsion, and safety tests. |
| 4. Baseten compiler | Passed for exercised cases | Live API and browser compilation passed strict validation. |
| 4B. Bounded agent loop | Passed for exercised cases | Live dynamic-obstacle run requested a validated detour and converged; mock recovery passed 10 seeds. |
| 5. SAM 3.1 | Out of scope | Excluded by the user. |
| 6. Evaluation | Passed for fixed protocol | 40/70 task successes and 30 expected failures; 40/40 additional held-out nominal runs succeeded. |
| 7. Product readiness | Passed for exercised paths | Production build, offline browser flow, responsive policy and guide routes, 3D view and cameras, 2D fallback, forced context-loss fallback, custom 404. Fresh source snapshot install and checks passed. |
| 8. Demo and submission package | Partial | Demo script is present; timed spoken rehearsal and participant-portal review remain outstanding. No submission occurred. |

## Earlier verification

- Backend: 99 collected tests passed. Pytest reported loop-scope and Starlette/httpx
  deprecation warnings.
- Backend lint: Ruff passed for app, tests, and scripts.
- Frontend: typecheck, lint, and production build passed.
- API smoke: health, public scenarios, mock compilation, seeded run, and latest
  evaluation passed. The offline run converged in 14.4 simulated seconds.
- Evaluation: 140 paired runs across ten seeds and seven scenarios. The quadratic
  controller succeeded in 31/70; the baseline succeeded in 0/70. Disturbed-corridor
  mock recovery was 10/10. No collisions occurred in either controller sample.
- Browser: WebGL2 rendered; perspective, top-down, and follow modes worked; the SVG
  fallback rendered. A forced WebGL context loss switched the view to SVG with a notice.
- Responsive routes: workbench, guide, evaluation, privacy, security, license, and
  custom 404 showed no document-level horizontal overflow at 320 px.
- Custom 404: returned HTTP 404 and displayed its recovery links. The page no longer
  shows placeholder coordinates or a local host address.
- Live Baseten: unverified after the adapter change. No new request was made.
- npm audit: zero production dependency vulnerabilities and 16 moderate development
  dependency findings.

The recorded test counts below are historical. Latest live and clean-source checks are
in `docs/BUILD_STATE.md`. Recording, timed rehearsal and participant-portal review remain.
No deploy or submission occurred.

## 2026-11-04 workspace design continuation

- Focused views, larger common text, and offline browser compile/run navigation were verified as recorded in `docs/BUILD_STATE.md`.
- The requested complete frontend refactor and Blender asset work remain in progress. Blender MCP cannot connect to its add-on server on localhost:9876. Existing release gates remain unchanged.

## 2026-11-04 Blender prototype

The community Blender add-on responded and a separate rover GLB prototype was exported. Header and mesh structure were checked. Visual review and application integration remain outstanding; the existing procedural rover remains active. Details are in `docs/BUILD_STATE.md`.

## 2026-11-04 official Blender bridge

The official Blender MCP scene inspection succeeded and the rover prototype was inspected in the Blender viewport. The GLB is still not integrated or tested in the browser; see `docs/BUILD_STATE.md`.

## 2026-11-04 Blender rover integration

The Blender GLB is loaded into the 3D arena with a procedural fallback. Typecheck, lint, build, targeted model checks, and mock browser fallback checks passed as detailed in `docs/BUILD_STATE.md`. The wider frontend redesign and existing release gates remain open.

## 2026-11-04 frontend studio refactor

Mission, arena, and results navigation, shared styling, and arena controls were refactored. Production build, lint, typecheck, mock workflow, responsive routes, and forced WebGL fallback checks passed as recorded in `docs/BUILD_STATE.md`. The pre-existing live-provider, clean-checkout, and demo gates remain open. No live inference was run.

## 2026-11-04 Wensity loading indicator

A free MIT-licensed Wensity spinner variant was adapted for compile and run loading states. Frontend typecheck, lint, build, and delayed mock browser checks passed. See `docs/BUILD_STATE.md` for provenance.

## 2026-11-04 live and evaluation completion pass

- Current fixed evaluation: quadratic 40/70 task successes with 30 intentional
  infeasibility/timeout failures retained; baseline 0/70. Four nominal scenarios over
  ten additional held-out seeds each passed with no reported collisions.
- Baseten live browser compile and dynamic-obstacle agent run converged after one
  validated detour. A prior one-decision live trial failed safely, so these observations
  do not establish model reliability.
- A fresh source snapshot plus current uncommitted code passed Python/npm installation,
  backend 108 tests and lint, frontend lint/typecheck/build, and offline API smoke.
  Sixteen moderate development-tool advisories remain; production audit returned zero.
- SAM 3.1 is excluded. The demo script is prepared; the recording, spoken rehearsal,
  and exact participant-portal requirements have not been verified. No submission or
  deployment has occurred.
- Organizer reminder: the demo is three minutes and the GitHub repository must be
  open source. `origin` is public, but current local work is not committed or pushed.
  The submission form requires login. The event deadline listed by the organizer is
  November 4 at 9:00 PM ET, or November 5 at 7:30 AM IST. No submission was made.
- Submission and form review were explicitly deferred by the user. The current local
  changes remain uncommitted and unpushed.

## 2026-11-04 approved expansion in progress

Swept robot separation validation and identity checks added. Backend: 110 tests and Ruff passed. Earlier evaluation results predate this change and need rerunning. BYOK for Baseten, Meta Model API and Fireworks, provider and model selection, arena and swarm presets, remaining safety and evaluation work, and end-to-end verification are not complete. No new live calls were made. See docs/BUILD_STATE.md.

The fixed evaluation was rerun after the swept separation change: quadratic 40/70, baseline 0/70, disturbed-corridor recovery 10/10, all with offline mock agent decisions. See docs/BUILD_STATE.md.

Provider selection and request-scoped browser keys are implemented for Baseten, Meta and Fireworks; Meta and Fireworks remain live-unverified. Three ring mission presets were added. Mock browser compile and simulation passed. See docs/BUILD_STATE.md for checks and remaining work.

Final checks for the provider/preset slice: 114 backend tests, Ruff, frontend build, lint and typecheck passed. Local browser mock run passed; Meta and Fireworks are live-unverified. Evaluation now distinguishes nominal and stress scenarios and notes the baseline agent difference. Wider end-to-end checks, swept obstacle-path safety, demo rehearsal and recording remain. See docs/BUILD_STATE.md.

The guide now includes interactive setup, a first-run walkthrough, and real read-only API checks. Frontend typecheck, lint, build, and local browser checks passed. See docs/BUILD_STATE.md.

Cloudflare deployment is blocked by account Containers access, an unavailable local Docker engine, and unresolved public API isolation. Icon changes and frontend checks passed. See docs/CLOUDFLARE_DEPLOYMENT.md.
Local backend Docker image built and its offline smoke test passed. The Cloudflare Containers plan and public API isolation remain deployment blockers.

Render deployment preparation: free service blueprint, server-side Baseten default plus BYOK, shared latest-run disabled and a process-local request limit. Backend 116 tests and Ruff passed; frontend build, lint, and typecheck passed. Render deployment remains unverified. No scheduled keep-alive is planned.
