# Three-minute FieldWeaver demo

## Preparation

Start the backend and frontend using `API_SETUP.md`, with `BASETEN_API_KEY` available
only to the backend. Select `Dynamic barrier`, seed `42`, the quadratic controller,
and `Baseten live` for both the compiler and agent. The user has authorized Baseten
development usage. Never show or paste the key.

Mission text:

> Search for the signal source, maintain a ring formation, and avoid restricted regions.

On November 4, 2026, this browser flow compiled a live mission, received operator
approval, and converged after one live obstacle-change decision and validated detour.
It reported zero collisions and zero safety interventions. Model output can vary, so
review the specification and report the actual run rather than fixed numbers. The
walkthrough below is a timing target, not a recorded spoken rehearsal.

## Walkthrough

| Target time | Action and narration | Evidence to show |
| --- | --- | --- |
| 0:00-0:20 | Introduce the hidden scalar source and simulation-only scope. | Mission workspace and provider status. |
| 0:20-0:45 | Choose Dynamic barrier and seed 42; select the two live Baseten modes. | Scenario and explicit provider modes. |
| 0:45-1:05 | Compile, review the validated specification and assumptions, and approve it. | Baseten live label and approval gate. |
| 1:05-1:45 | Run the mission; explain that the model is invoked at events, not on each simulation tick. | Arena playback, source estimate, and obstacle event. |
| 1:45-2:10 | Open run results and describe the observed trajectory metrics. | Actual localization, formation, separation, clearance, and collision results. |
| 2:10-2:30 | Expand the run trace. | Decision provider, obstacle event, decision, validator outcome, and interventions. |
| 2:30-2:50 | Open the paired evaluation. | Quadratic 40/70 and baseline 0/70; 30 quadratic cases intentionally test infeasibility or timeout. The fixed suite uses a mock agent. |
| 2:50-3:00 | State limits. | Simulation only; single source; ten fixed seeds do not establish general reliability. |

## Recovery

If the live provider is unavailable or returns a rejected response, show the error and
switch both modes to `Offline mock` for the deterministic demonstration. Label the
fallback and do not present it as live inference. If a trial fails, show its actual
termination and trace. SAM 3.1 is outside this build's scope.
