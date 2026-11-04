# FieldWeaver status snapshot

Last updated: November 4, 2026.

- **Implemented:** Local mission-to-simulation flow, strict validation, deterministic
  controller and baseline, independent simulation safety checks, bounded event-driven
  mock agent, exact ring-slot A* detours with separation repulsion, evaluation report,
  dedicated guide and policy pages, MIT license page, and custom 404.
- **Visual presentation:** Browser Three.js scene renders run data with perspective,
  top-down, and follow controls. SVG 2D fallback works by manual switch and forced
  WebGL context loss. This is presentation only; no additional physics engine is used.
- **Phase status:** Phases 0-4B pass locally or with mocked providers. Phase 5 SAM is
  deferred. Phase 6 has a ten-seed, seven-scenario, 140-run snapshot. Phase 7 passes
  the exercised production browser flows. Phase 8 still needs a timed spoken rehearsal
  and participant-portal review.
- **Live provider:** Baseten Muse Spark Open compiled one generic API mission that
  converged with the agent disabled. One live dynamic-barrier trial converged after a
  validated detour; an earlier constrained trial exhausted its decision budget.
- **Evaluation:** Quadratic controller 40/70 successes; baseline 0/70; seeded
  disturbed-corridor mock recovery 10/10. Expected failures remain in the denominator.
- **Verification:** 99 backend tests passed; Ruff, frontend typecheck/lint/build, API
  smoke, release-artifact checks, and empirical frame serialization checks passed.
  The browser completed an offline compile and run at seed 42, exercised 3D controls
  and the 2D fallback, and forced a WebGL context-loss fallback.
- **Dependencies:** npm audit reported zero production vulnerabilities and 16 moderate
  development dependency vulnerabilities, primarily in lint tooling. No major upgrade
  was applied automatically.
- **Privacy and security:** The policy discloses local storage of the audio mute
  preference. The API remains local-development software with no authentication or
  rate limiting. Do not expose it to untrusted networks.
- **Known gaps:** A clean-checkout install, the
  spoken demo rehearsal, and portal rule review remain outstanding. SAM is out of scope.
  The exact commands and limitations are in docs/BUILD_STATE.md.
- **External actions:** No deploy or hackathon submission occurred. The key value is
  not recorded in project documentation.
