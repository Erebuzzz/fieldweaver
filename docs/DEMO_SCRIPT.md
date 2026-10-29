# Three-minute FieldWeaver demo

## Preparation

Start the backend and frontend using `API_SETUP.md`. Keep the provider in `Automatic`
with the current blank-key setup so the UI truthfully displays `Offline mock`. The
mission compiler and agent remain usable without network calls. Use the `Dynamic
barrier` scenario, seed `42`, and the quadratic controller.

Exact mission text:

> Search for the signal source, maintain a ring formation, and avoid restricted regions.

The primary browser flow was exercised against the local UI and API in Playwright. It
was not rehearsed as a timed recording, so the timestamps below are a presentation
target. The three-seed summary in `EVALUATION_RESULTS.md` is the recorded comparison,
not a live inference result.

## Walkthrough

| Target time | Action and narration | Expected evidence |
| --- | --- | --- |
| 0:00-0:20 | Explain that the robots must locate a hidden scalar-field source without receiving its coordinate. | Mission control shows `Simulation only` and `Offline mock`. |
| 0:20-0:40 | Enter the exact mission text. Select `Dynamic barrier`, seed `42`, `Automatic` compiler and agent, and `Quadratic estimator`. | The scenario is described as a seeded obstacle-change run. |
| 0:40-1:00 | Select **Compile mission** and review the validated specification, assumptions, and safety limits. Check the approval box. | Provider label says `Offline mock`; mission review is visible before execution. |
| 1:00-1:45 | Select **Run approved mission**. While it runs, explain that the dynamic obstacle activates at simulation time 6 seconds and decisions occur only at event checkpoints. | The arena animates robot paths and estimate. The run should finish successfully at about 29.7 simulated seconds for this seed. |
| 1:45-2:10 | Pause or scrub the playback and inspect the evaluation panel. | Seed 42 previously measured 0.000 m localization error, 0.025 m formation error, 0.595 m minimum separation, 0.245 m obstacle clearance, 56.80 m total path, and zero collisions. Values are trajectory-derived. |
| 2:10-2:30 | Expand the agent and safety trace. | Trace shows the obstacle-change event, one offline mock decision, a validated per-robot detour, and one replan. No safety intervention was recorded in this run. |
| 2:30-2:50 | Show `EVALUATION_RESULTS.md` and describe the paired 21-run results for each controller. | State the measured results honestly: quadratic 10/21 successes and baseline 0/21; all failures are retained. The disturbed scenario recovered in 3/3 seeds. |
| 2:50-3:00 | Close with limits. | Say live Baseten inference was not tested, the source-localization task has one source, and the three-seed evaluation is small. |

## Recovery path

- If the backend is unavailable, check `GET /api/health` at `127.0.0.1:8000` and
  restart the local services from `API_SETUP.md`.
- If a run fails for a different seed or local code change, show the recorded
  termination and safety trace. Do not present a failed run as a success or change its
  acceptance criteria.
- If asked to demonstrate unsupported multi-source intent, enter “Find two sources
  with a ring formation and avoid restricted areas.” The offline compiler should return
  a clarification prompt and disable approval and run until the mission is corrected.
- Do not select `Baseten live` unless a key has been configured server-side and a
  successful request has actually been verified. Never show or paste the key.

The browser flow and unsupported-request guard were manually exercised. The full
three-minute spoken presentation has not been timed or recorded.
