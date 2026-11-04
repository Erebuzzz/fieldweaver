# Privacy Policy

Last reviewed: November 4, 2026

## Scope

FieldWeaver is self-hosted software. The project maintainers do not operate a hosted
FieldWeaver service or receive mission data. This notice describes the current source
code when an operator runs it locally. If another party hosts an instance, that
operator's practices also apply.

The application is simulation software and is not designed for personal, confidential,
or safety-critical information.

## Data handled by a local instance

- The browser sends mission text, scenario selection, provider and controller choices,
  and the run seed to the configured FieldWeaver API.
- The API returns a validated mission specification, simulation frames, metrics, and
  event trace to the browser.
- The latest run is held in the API process memory for `GET /api/evaluations/latest`.
  It is not stored in a database and is cleared when the process restarts.
- The evaluation script can write a JSON report to the local ignored `artifacts/`
  directory.
- Normal request logs contain method, route path, status, duration, and request ID.
  Unexpected exceptions also write a stack trace. Operators should protect logs and
  generated evaluation reports.

The frontend stores one preference in browser local storage: whether tactical audio
is muted. It does not set application cookies or load an analytics tracker. The browser
and hosting platform may still create technical logs outside this project.

## Live inference

When the compiler or agent is set to `live`, or to `auto` while the backend key is
configured, the backend calls Baseten's Chat Completions endpoint. Mission compilation
sends the mission text and a public summary of the selected scenario. Event-driven
agent calls send a bounded observation summary, including the current estimate, team
centroid, safety state, and allowed actions. The backend key is not sent to the browser.

Ground-truth source coordinates are excluded from compiler requests and agent
observations. Evaluation data can be returned to the browser after the run ends.

Baseten's published Security Practices currently describe Zero Data Retention for its
Model APIs inputs and outputs. The actual service, configuration, account agreement,
and current provider terms govern a live request. FieldWeaver does not configure or
guarantee provider retention on an operator's behalf. See the [Baseten Security
Practices](https://www.baseten.co/security-practices/), [Privacy
Policy](https://www.baseten.co/privacy-policy/), and [Data Request
Policy](https://www.baseten.co/data-request-policy/).

## Operator choices

- Use Offline mock mode to avoid sending mission and event content to a model provider.
- Do not enter credentials, personal information, or confidential material into mission
  text.
- Keep the API on loopback unless the deployment has been secured.
- Review and remove local logs and evaluation artifacts according to local retention
  requirements.
- For a locally operated installation, direct access or deletion requests to that
  instance's operator. The project has no central user account or data store.

This notice applies to the source reviewed on November 4, 2026. Revisit it if storage,
telemetry, hosting, or provider integrations change.
