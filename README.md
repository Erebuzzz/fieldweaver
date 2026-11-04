# FieldWeaver

FieldWeaver turns a short operator mission into a validated specification, then runs a
seeded 2D multi-robot source-localization simulation. The simulator keeps the source
coordinate out of mission compilation, controller observations, and agent observations.
An independent safety filter checks every proposed motion.

The project uses Baseten's OpenAI-compatible Chat Completions endpoint with
`meta-models/muse-spark-open-1026` when a server-side `BASETEN_API_KEY` is configured.
Without a key, the application uses an explicitly labelled deterministic mock.
A live mission compilation and a separate live obstacle-response trial succeeded on
November 4, 2026. These are individual checks, not a statistical model evaluation.

## What is implemented

- FastAPI contracts for public scenario metadata, mission compilation, simulation runs,
  and the latest in-process run evaluation.
- Strict, versioned Pydantic mission and agent-decision schemas. Unsupported mission
  requests return review notes and a clarification prompt.
- A deterministic 10 by 10 metre arena, seeded scalar-field noise, holonomic robot
  dynamics, a quadratic least-squares estimator, and a weighted-centroid baseline.
- Ring formation control, per-robot deterministic A* detours ending at assigned ring
  slots, inter-robot separation repulsion, and independent geometric safety checks.
- A bounded event-driven agent loop. It calls the provider only after monitored events,
  applies only known actions, and records a trace. The default caps are two model calls
  and two replans per run.
- A responsive Next.js workbench with mission review and approval, a Three.js 3D arena,
  an SVG 2D fallback, trajectory metrics, provider status, agent trace, and safety log.
  The web app also includes dedicated `/docs` and `/evaluation` pages, `/privacy` and
  `/security` policies, a `/license` page, and a themed custom 404 route.
- A seven-scenario evaluation suite comparing the proposed controller and baseline on
  ten shared seeds. It records 140 runs and publishes the exact JSON snapshot used by
  the evaluation page at `frontend/public/evaluation-report.json`.

This is simulation software. It does not control physical robots and does not claim a
formal safety proof. Multiple-source missions and SAM 3.1 scene segmentation are not
implemented. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and
[docs/API_SETUP.md](docs/API_SETUP.md) for design boundaries and integration details.
The web app's `/docs` Field Guide explains the workflow and API. Read the
[Privacy Policy](docs/PRIVACY.md), [Security Policy](docs/SECURITY.md), and
[MIT License](LICENSE) before using or sharing an instance.

## Architecture

```mermaid
flowchart LR
    Operator -->|mission text| UI[Next.js control room]
    UI -->|compile, review, approve| API[FastAPI routes]
    API --> Compiler[Provider-independent compiler]
    Compiler -->|configured live mode| Baseten[Baseten Chat Completions]
    Compiler -->|offline mode| Mock[Deterministic mock]
    Compiler --> Schema[Strict MissionSpec validation]
    Schema --> UI
    UI -->|approved spec, scenario, seed| API
    API --> Runner[Run service and bounded orchestrator]
    Runner --> Sim[Deterministic simulation core]
    Sim --> Controller[Estimator, ring controller, A* planner]
    Controller --> Safety[Independent safety filter]
    Safety --> Sim
    Runner -->|event checkpoints only| Agent[Bounded AgentDecision provider]
    Agent -->|live or offline mock| Baseten
    Agent --> Schema
    Sim --> Evaluator[Trajectory metrics and hidden truth]
    Evaluator --> UI
    Runner --> Trace[Machine-readable agent and safety trace]
    Trace --> UI
```

The model cannot produce executable code, controller gains, routes, actuator commands,
or changes to safety limits. The application maps validated action enums to deterministic
behaviours and checks proposed motion independently. Model calls do not occur in the
per-tick controller loop.

The 3D scene renders simulation output in the browser. It does not run a second physics
engine or change robot state. Users can switch to the SVG view; WebGL failure or context
loss also falls back to that view. Blender, MuJoCo, and Isaac Sim are not part of the
current runtime. Blender could be used later to author optional browser assets; MuJoCo
or Isaac Sim would need a separate dynamics or sensor-validation goal.

## Run locally

Requirements: Python 3.11 or newer, Node.js 20.9 or newer, and npm. From PowerShell at
the repository root:

```powershell
py -3 -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -e "backend[dev]"
npm ci --prefix frontend
Copy-Item .env.example .env
```

The copied `.env` has a blank key and runs offline. Keep any real key in this backend
environment file or in the backend process environment. Never place it in frontend
configuration. The browser API defaults to `http://127.0.0.1:8000`; the optional
`NEXT_PUBLIC_API_BASE_URL` variable must be supplied to the frontend process if that
origin is changed.

Start the backend in one terminal:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Start the frontend in a second terminal:

```powershell
npm --prefix frontend run dev -- --hostname 127.0.0.1
```

Open `http://127.0.0.1:3000`. API health and interactive OpenAPI documentation are at
`http://127.0.0.1:8000/api/health` and `http://127.0.0.1:8000/docs`.

For Bash or another POSIX shell, replace the virtual-environment setup with:

```sh
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -e 'backend[dev]'
npm ci --prefix frontend
cp .env.example .env
```

Then run `backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`
and `npm --prefix frontend run dev -- --hostname 127.0.0.1` in separate terminals.

## Baseten configuration

The server reads `BASETEN_API_KEY` from the environment or the root `.env` file. The
configured defaults are `https://inference.baseten.co/v1` and
`meta-models/muse-spark-open-1026`. The browser never receives the API key. Selecting
`Baseten live` without a key returns an explicit provider error. `Automatic` uses live
only when the backend has a key; otherwise it uses the labelled offline mock.

The deterministic test suite uses mocked HTTP. On November 4, 2026, a live API
compilation returned a strictly validated specification and the resulting open-field
run converged with the agent disabled. A separate live agent requested a validated
detour in one dynamic-barrier trial, which converged. An earlier one-decision trial
selected a cautious profile and exhausted its decision budget. These limited checks do
not establish live-agent reliability. Mission and agent completions use a 4096-token
cap. See [docs/API_SETUP.md](docs/API_SETUP.md) for setup and test details.

## API routes

| Method and route | Purpose |
| --- | --- |
| `GET /` | Service identity and OpenAPI path |
| `GET /api/health` | Secret-free provider configuration, simulation limits, and safety envelope |
| `GET /api/scenarios` | Public scenario geometry and seed bounds, without source coordinates |
| `POST /api/missions/compile` | Compile text to a strict mission specification |
| `POST /api/simulations/run` | Run a seeded simulation and return frames, metrics, and traces |
| `GET /api/evaluations/latest` | Latest run evaluation held in the current backend process |
| `POST /api/scenes/segment` | Returns `503`; SAM is out of scope |

All API errors use a request-ID error envelope. The latest evaluation endpoint is
process-local and is not the aggregate report. The `/evaluation` page displays the
checked-in `frontend/public/evaluation-report.json`; the evaluation script writes the
same data to that public snapshot and the ignored `artifacts/evaluation_report.json`.

## Verification commands

Run backend commands from `backend/`:

```powershell
.venv\Scripts\python.exe -m pytest -v
.venv\Scripts\python.exe -m ruff check app tests ..\scripts
```

Run frontend checks from `frontend/`:

```powershell
npm run typecheck
npm run lint
npm run build
```

From the repository root, run the API smoke path and paired evaluation:

```powershell
.\backend\.venv\Scripts\python.exe scripts\smoke_test.py
.\backend\.venv\Scripts\python.exe scripts\run_evaluation.py
```

The smoke check covers health, public scenarios, mock mission compilation, a seeded
simulation, and the latest evaluation route. The evaluation run uses deterministic
seeds; local wall-clock timings naturally vary between executions.

## Evaluation snapshot

In the checked-in ten-seed suite, the quadratic controller succeeded in 40 of 70 runs
and the weighted-centroid baseline succeeded in 0 of 70. The proposed controller
terminated with `route_infeasible` in 20 runs and timed out in 10. All 70 baseline runs
timed out. The seeded `disturbed_corridor` case recovered in 10 of 10 trials with the
offline mock agent. These results are limited to the listed scenarios and seeds. They do
not establish general superiority or live-agent performance. Full metrics, variation,
and failure counts are in [docs/EVALUATION_RESULTS.md](docs/EVALUATION_RESULTS.md) and
the [raw evaluation JSON](frontend/public/evaluation-report.json), also shown at
`/evaluation`.

## Known limits

- The source-localization task supports one hidden source and 3 to 8 point robots.
- The safety filter is a geometric validator for this simulation, not a formal proof.
- The latest-run API state is process-local; it resets when the backend restarts.
- The evaluation sample contains ten seeds for each of seven scenarios. Broader
  robustness and cross-platform determinism have not been established.
- Live compiler and agent checks have passed individual trials, but live-agent
  reliability and latency distributions have not been evaluated.
- SAM 3.1 is not planned for this build. Physical hardware, persistent storage, and
  multi-source missions are outside the implemented scope.

The reproduction steps for the seeded disturbance demo are in
[docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md). Remaining limitations are summarized above
and in [docs/EVALUATION_RESULTS.md](docs/EVALUATION_RESULTS.md).
