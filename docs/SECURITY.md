# Security Policy

Last reviewed: October 30, 2026

## Deployment status

The documented local commands bind the frontend and backend to loopback. The hosted
demo does not implement user authentication or authorization. It applies a process-local
request limit and a persistent 250-request-per-UTC-day allowance for its shared Baseten
key. That allowance limits request count, not spending. CORS is a browser policy and does
not stop direct HTTP clients from reaching a network-accessible API.

Do not expose the development API to untrusted networks. A shared or hosted deployment
needs an authenticated reverse proxy, TLS, network restrictions, request limits, and
a reviewed CORS configuration before it is made reachable.

## Secret handling

- Store `BASETEN_API_KEY` in the backend process environment or the local root `.env`.
- The root `.env` is ignored by Git. Keep real credentials out of `.env.example`.
- Never use `NEXT_PUBLIC_*` for provider secrets or place credentials in source code,
  prompts, logs, screenshots, or test fixtures.
- A key entered in the workbench is held in page memory and sent to the backend for
  provider requests. Use a trusted instance and HTTPS for remote connections, and clear
  the field or close the page when finished. The server-default key is not returned to
  the browser.
- Restrict access to the local account and rotate a key if it is exposed.

## Model and simulation boundaries

Model output is untrusted input. Mission and agent responses are schema-validated on
the server. The model cannot provide executable code, actuator values, arbitrary
routes, or relaxed safety limits. Deterministic motion is checked by an independent
validator. These controls are for the simulator only and are not a physical safety
certification or proof for real robot dynamics.

Protect API logs and local evaluation reports because they can contain request context
and trajectory data. The latest run is held in process memory and is cleared when the
API process restarts. Public mode disables shared latest-run history.

## Reporting a vulnerability

Please do not publish API keys, private mission data, or exploit details in a public
issue. Use [GitHub's private vulnerability reporting
flow](https://github.com/Erebuzzz/fieldweaver/security/advisories/new) if it is enabled
for the repository. If that flow is unavailable, contact the repository maintainers
privately before publishing details. No response-time commitment is currently stated.

Reassess this guidance before any non-local deployment.
