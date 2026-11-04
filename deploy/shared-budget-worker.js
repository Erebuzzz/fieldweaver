const DAILY_LIMIT = 250;

function matchesToken(actual, expected) {
  if (!actual || !expected || actual.length !== expected.length) return false;
  let difference = 0;
  for (let i = 0; i < actual.length; i++) difference |= actual.charCodeAt(i) ^ expected.charCodeAt(i);
  return difference === 0;
}

export default {
  async fetch(request, env) {
    if (!env.BUDGET_TOKEN) return new Response(null, { status: 503 });
    if (request.method !== "POST" || !matchesToken(request.headers.get("Authorization"), `Bearer ${env.BUDGET_TOKEN}`)) {
      return new Response(null, { status: 403 });
    }
    const day = new Date().toISOString().slice(0, 10);
    try {
      const result = await env.DB.prepare(
        "INSERT INTO usage (day, requests) VALUES (?, 1) ON CONFLICT(day) DO UPDATE SET requests = requests + 1 WHERE requests < ? RETURNING requests"
      ).bind(day, DAILY_LIMIT).first();
      return new Response(null, { status: result ? 200 : 429, headers: { "Cache-Control": "no-store" } });
    } catch {
      return new Response(null, { status: 503 });
    }
  },
};
