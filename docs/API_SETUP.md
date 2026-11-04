# Local setup and API guide

## Prerequisites

- Python 3.11 or newer
- Node.js 20.9 or newer and npm
- The repository checkout with `backend/` and `frontend/`

No API key is required to use the local simulator. The offline mock is explicit in API
responses and in the browser.

## Install

From the repository root in PowerShell:

```powershell
py -3 -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -e "backend[dev]"
npm ci --prefix frontend
Copy-Item .env.example .env
```

From Bash:

```sh
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -e 'backend[dev]'
npm ci --prefix frontend
cp .env.example .env
```

Edit `.env` locally only if needed. Keep `BASETEN_API_KEY` blank to stay on the mock
path. The root `.env` is read by the backend. The frontend uses
`http://127.0.0.1:8000` by default; to change it, set `NEXT_PUBLIC_API_BASE_URL` in the
frontend process environment before starting Next.js. Never put a secret in a
`NEXT_PUBLIC_*` variable.

## Start the services

Run each command in a separate terminal from the repository root.

PowerShell backend:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

PowerShell frontend:

```powershell
npm --prefix frontend run dev -- --hostname 127.0.0.1
```

Bash backend:

```sh
backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Bash frontend:

```sh
npm --prefix frontend run dev -- --hostname 127.0.0.1
```

Open `http://127.0.0.1:3000`. The API is at `http://127.0.0.1:8000`; OpenAPI docs
are available at `/docs`.

## Provider behavior

The only supported live provider is Baseten Chat Completions:

- Base URL: `https://inference.baseten.co/v1`
- Model: `meta-models/muse-spark-open-1026`
- Secret: `BASETEN_API_KEY`, read only by the backend
- Request path: `/chat/completions`

`mode="auto"` selects live when the backend has a key and selects the offline mock
otherwise. `mode="mock"` always uses the deterministic mock. `mode="live"` without a
key returns `503 provider_not_configured`; it does not silently switch to mock. The
same policy applies to agent decisions. A configured key is not proof of a successful
live call. Public metadata marks `live_verified` only after a successful response.

The implementation uses `httpx` against the [Baseten Chat Completions
contract](https://docs.baseten.co/reference/inference-api/chat-completions). Request
timeouts, authentication errors, rate limits, unreachable responses, malformed
completion shapes, and invalid model output are mapped to explicit errors. Provider
tests use an injected `httpx.MockTransport`; they do not make network calls.

The mission compiler and agent decision provider explicitly set a 4096-token output
cap. Reasoning tokens may consume part of this budget. The adapter reads the final
answer from `message.content`; it does not treat `reasoning_content` as a mission
result. On November 4, 2026, one bounded live compilation passed strict validation and
an actual API route compiled a generic mission that subsequently converged with the
agent off. A live dynamic-barrier trial also requested a validated detour and converged.
An earlier one-decision live trial selected a cautious profile and exhausted its budget.
These individual trials do not establish reliability or a latency distribution.

## HTTP routes

| Route | Contract |
| --- | --- |
| `GET /` | Name, app version, and docs path |
| `GET /api/health` | Versioned health, public provider settings, limits, secret-free safety envelope |
| `GET /api/scenarios` | Scenario descriptions and public geometry; no hidden source coordinate |
| `POST /api/missions/compile` | `mission_text`, optional `scenario_id`, optional provider `mode`; returns validated `MissionSpec`, provider metadata, and warnings |
| `POST /api/simulations/run` | Validated mission, `scenario_id`, seed, controller, and agent mode; returns recorded frames, computed evaluation, safety summary, and agent trace |
| `GET /api/evaluations/latest` | Latest run evaluation in this backend process; `404` before the first run |
| `POST /api/scenes/segment` | `503 perception_disabled`; SAM is out of scope for this build |

Every response includes a request ID field and `X-Request-ID` header. Errors follow
this shape:

```json
{
  "error": {
    "code": "provider_not_configured",
    "message": "Live inference requires BASETEN_API_KEY on the server.",
    "details": null,
    "request_id": "..."
  }
}
```

The compile response is review-only. The UI requires explicit operator approval before
the simulation request can start. Unsupported requested capabilities produce warning
text and a clarification prompt. The browser disables approval until the operator
removes that unsupported request and recompiles.

The run response reveals evaluation ground truth only after the run has ended, with an
explicit `after_run_only` marker. Public scenario and agent-observation schemas omit
source fields. Mission compilation, controller inputs, and model decision summaries
never receive the hidden coordinate.

## Operational limits

The default server limits are two model calls and two replans per simulation. Values
are read from `FIELDWEAVER_MAX_MODEL_CALLS` and `FIELDWEAVER_MAX_REPLANS`, bounded by
backend constants, and cannot be changed by model output. Calls occur only at
event-monitor checkpoints. The safety filter retains final authority over proposed
motion.

`GET /api/evaluations/latest` keeps the most recent run in process memory. It is not
the aggregate evaluation suite and it is cleared on server restart. The reproducible
suite writes `artifacts/evaluation_report.json` for local inspection and the same
checked-in snapshot to `frontend/public/evaluation-report.json`. The `/evaluation` page
renders that snapshot and links to the raw JSON. The script also refreshes the snapshot
when the scenario matrix is regenerated.

## Verify

From the repository root:

```powershell
.\backend\.venv\Scripts\python.exe scripts\smoke_test.py
```

From `backend/`, run the backend tests with:

```powershell
.venv\Scripts\python.exe -m pytest -v
```

## Browser-entered provider keys

The advanced workspace accepts a Baseten, Meta Model API, or Fireworks key and a model ID. A provided key is held in page memory and sent to the backend with each live compile or live agent run; mock and agent-off requests omit it. Closing the page or clearing the field removes it from the UI. The backend uses fixed provider URLs and request-scoped settings, and does not return the key. The configured server Baseten key remains the default when no browser key is provided.

Use this feature locally or behind HTTPS. This local application has no user authentication or multi-user session isolation and is not ready to be exposed directly to untrusted networks. TLS does not protect against a compromised browser, server, or logging proxy. Provider account permissions, billing, model availability, and content policies still apply. Enter only text-generation model IDs. Meta and Fireworks live calls have not been verified because keys are unavailable.

Meta: https://dev.meta.ai/docs/protocols and https://dev.meta.ai/docs/models. Fireworks: https://docs.fireworks.ai/.
