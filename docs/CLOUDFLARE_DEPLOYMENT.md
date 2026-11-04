# Cloudflare deployment preparation

Target hostname: `fieldweaver.erebuzzz.tech`. The hostname was not assigned at the time of inspection. No deployment or DNS changes have been made.

The frontend builds as a Next.js application. The Python backend can be packaged with `backend/Dockerfile`, and the image built successfully after starting Docker Desktop. A local offline smoke test passed for health, scenarios, compilation and simulation. Cloudflare rejected a read of Containers applications with a message that the Workers Paid plan is required. The Cloudflare connector does not have billing-read permissions, so the current subscription could not be independently inspected.

Before public deployment, protect the API from unauthorized inference and excessive simulation requests. In particular, do not configure a shared server Baseten key on an unauthenticated public API. The current `/api/evaluations/latest` uses shared in-process state and is not isolated per user. Choose and test an access and isolation design before exposing it. HTTPS alone does not solve these issues. The local browser BYOK feature is not evidence of a secure hosted multi-user system.

Cloudflare Containers charge for active compute, provisioned memory and disk, and potentially network egress. A continuously running container can exceed the monthly included allocation. An idle-sleep configuration reduces idle cost but may cause cold starts; neither configuration guarantees uninterrupted availability. Verify current pricing and the account plan before deployment: https://developers.cloudflare.com/containers/platform/pricing/.

After access and security are addressed: build and locally test the image, create a Cloudflare-compatible deployment, configure the frontend API URL and backend CORS for the actual public hostnames, attach the custom domain, then verify HTTPS, offline simulation, credential handling and all guide links against the deployed services. Update user-facing documentation only after URLs are live and verified.
