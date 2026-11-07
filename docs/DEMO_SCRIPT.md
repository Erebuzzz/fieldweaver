# FieldWeaver three-minute demo script

## Before recording

- Open https://fieldweaver.erebuzzz.tech and wait until the API shows connected. Render's free backend may take about a minute to wake.
- Select **Dynamic barrier**, seed **42**, and the **Quadratic estimator**. In Advanced settings, choose **Baseten live** for the compiler and agent. The controls may say **Selected provider live**. The shared Baseten key stays on the server; do not display or paste any key.
- Use the mission below. Run through it once before recording. Live model outputs and recovery decisions can vary. If a run fails, show the actual failure and trace, or use the offline fallback described below. Never narrate an unobserved event as though it occurred.
- Keep the evaluation page open in another tab. The fixed evaluation uses a mock agent, not live Baseten.

**Mission text:**

> Search for the signal source, maintain a ring formation, and avoid restricted regions.

## Spoken script and screen directions

### 0:00–0:20 | The problem

**On screen:** Mission workspace, with the 3D arena visible.

**Say:**

“Imagine a team of robots searching an unfamiliar area for a signal source. They can measure the signal locally, but they don't know where the source is. The challenge is to find it together while maintaining a safe formation and reacting to changes in the environment.”

### 0:20–0:37 | Introduce FieldWeaver

**On screen:** Point to the mission editor and the Dynamic barrier arena.

**Say:**

“FieldWeaver is a simulation-first mission studio for that problem. It turns an operator's natural-language objective into a structured mission, then runs a seeded multi-robot simulation. This is a research simulation, not a physical robot controller.”

### 0:37–1:02 | Compile and review

**On screen:** Show the mission text, Dynamic barrier, and seed 42. Open Advanced settings briefly to show the live provider selections, then select **Compile mission**. Once the result appears, point to the provider label and mission summary.

**Say:**

“Here I've asked the team to locate one signal source, form a ring, and avoid restricted regions. FieldWeaver sends the mission to Meta's Muse Spark Open model through Baseten. The backend validates the returned mission against a strict schema. I can review the robot count, formation, limits, and assumptions before approving the run.”

**On screen:** Review the actual response, select the approval checkbox, and start the run. If clarification is required, address it before approval.

### 1:02–1:34 | Show the simulation

**On screen:** Play the 3D arena. Point to the robots, paths, estimate, and the appearing barrier. Change to the top-down view if it makes the event easier to see.

**Say:**

“The robots search using simulated scalar measurements and an estimate of the source. The controller doesn't receive the hidden ground-truth location. In this arena, a barrier appears during the run. The simulation can trigger a bounded agent decision at that event; the model is not called on every simulation tick.”

### 1:34–1:57 | Explain safety and the trace

**On screen:** Open the run trace and safety information. Point to the actual event and decision, if one occurred.

**Say:**

“Any proposed decision must be one of the actions the application supports. An independent safety layer checks robot separation, obstacle clearance, speed, and arena boundaries. If a proposed movement violates a constraint, the safety layer can scale or stop it. The trace lets us inspect what actually happened.”

**If the live run records a validated replan**, add: “Here we can see the obstacle event and the validated replan.” Otherwise, describe the actual trace and outcome without claiming a replan.

### 1:57–2:20 | Show actual results

**On screen:** Open **Run results**. Point to the displayed outcome and the actual localization, formation, and collision metrics.

**Say:**

“After the run, FieldWeaver calculates results from the trajectory. Here are the actual outcome, localization and formation errors, and recorded collision metrics for this seed. If a mission times out or cannot find a safe route, that failure remains visible rather than being counted as a success.”

**On screen:** Read the displayed values only if you want to quote numbers. Do not reuse numbers from an earlier run.

### 2:20–2:48 | Show evaluation and limits

**On screen:** Open **Results** or the evaluation page. Show overall outcomes, the scenario breakdown, and the agent-off comparison.

**Say:**

“In our fixed evaluation, the quadratic policy converged in 40 of 70 trials. The total includes difficult boundary, enclosure, and short-time-budget cases. In a separate matched comparison with the agent off for both controllers, the quadratic policy succeeded in 20 of 40 nominal trials, while the weighted-centroid baseline succeeded in none. That baseline is limited, and these seeded simulations don't establish general reliability. The evaluation uses a deterministic mock agent.”

### 2:48–3:00 | Close

**On screen:** Return to the arena or the mission workspace.

**Say:**

“FieldWeaver connects language-based mission planning with deterministic control and measurable safety checks. It makes the mission, the decisions, and the results visible so an operator can inspect both success and failure.”

## If live inference is unavailable

Show the error briefly, then select **Offline mock** for both compiler and agent. Say: “The live provider is unavailable, so I'm switching to the clearly labeled offline mock. The simulator and safety checks still run locally on the backend.” Compile and run again. Do not call the fallback a live model response.

## Recording notes

The timestamps are targets, not a measured rehearsal. Allow extra time for provider latency or edit around waiting time without hiding a failed run. The previous live Dynamic barrier demonstration converged after one validated detour, but that result does not guarantee the next live run will do the same.
