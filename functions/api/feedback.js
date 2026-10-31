// Feedback från appen. Sparas i Cloudflare KV (bindning FEEDBACK).
// Läs rapporterna på /feedback-admin.html med nyckeln i miljövariabeln FEEDBACK_KEY.
//
// Skydd:
// - Bara anrop från appens egen webbplats tas emot (Origin/Sec-Fetch-Site)
// - Honungsfälla: ett dolt fält som bara robotar fyller i
// - Högst 5 rapporter per IP-adress och 10 minuter, och högst 200 per dygn totalt (KV:s gratisnivå tål 1 000 skrivningar per dygn)
// - Läsning och borttagning kräver nyckeln; nyckeln jämförs i konstant tid
//   och efter 10 fel försök på 15 minuter spärras IP-adressen en stund
// - Storleksgränser på alla fält
const KINDS = ["fel_besked", "data", "ide", "annat"];
const PER_IP = 5, IP_WINDOW = 600, DAILY_MAX = 200, AUTH_FAILS = 10, AUTH_WINDOW = 900;

const json = (d, status = 200) => new Response(JSON.stringify(d), {
  status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", "x-content-type-options": "nosniff" }
});
const str = (v, n) => String(v ?? "").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, "").slice(0, n);
const ip = request => request.headers.get("cf-connecting-ip") || "okänd";

// Samma webbplats? Webbläsare skickar Origin vid POST/DELETE och Sec-Fetch-Site vid alla anrop.
function sameSite(request) {
  const site = request.headers.get("sec-fetch-site");
  if (site && site !== "same-origin") return false;
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin) return false;
  return true;
}

function safeEqual(a, b) {
  const x = new TextEncoder().encode(String(a)), y = new TextEncoder().encode(String(b));
  let diff = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) diff |= (x[i] || 0) ^ (y[i] || 0);
  return diff === 0;
}

// Enkel räknare i KV. Inte exakt vid samtidiga anrop, men räcker för att stoppa spam.
async function bump(env, key, ttl) {
  const n = Number(await env.FEEDBACK.get(key)) || 0;
  await env.FEEDBACK.put(key, String(n + 1), { expirationTtl: Math.max(60, ttl) });
  return n + 1;
}
async function count(env, key) { return Number(await env.FEEDBACK.get(key)) || 0; }

async function authorized(request, env) {
  if (!env.FEEDBACK_KEY || String(env.FEEDBACK_KEY).length < 8) return { ok: false, status: 503, error: "no_key" };
  const lockKey = "rl:auth:" + ip(request);
  if (await count(env, lockKey) >= AUTH_FAILS) return { ok: false, status: 429, error: "too_many_attempts" };
  const given = (request.headers.get("authorization") || "").replace(/^Bearer /, "");
  if (given && safeEqual(given, env.FEEDBACK_KEY)) return { ok: true };
  await bump(env, lockKey, AUTH_WINDOW);
  return { ok: false, status: 401, error: "unauthorized" };
}

export async function onRequestPost({ request, env }) {
  if (!env.FEEDBACK) return json({ ok: false, error: "no_storage" }, 503);
  if (!sameSite(request)) return json({ ok: false, error: "forbidden" }, 403);
  if (!(request.headers.get("content-type") || "").includes("application/json")) return json({ ok: false, error: "bad_type" }, 415);
  const len = Number(request.headers.get("content-length") || 0);
  if (len > 12000) return json({ ok: false, error: "too_large" }, 413);
  let raw;
  try { raw = await request.text(); } catch { return json({ ok: false, error: "bad_body" }, 400); }
  if (raw.length > 12000) return json({ ok: false, error: "too_large" }, 413);
  let b;
  try { b = JSON.parse(raw); } catch { return json({ ok: false, error: "bad_json" }, 400); }
  if (!b || typeof b !== "object") return json({ ok: false, error: "bad_json" }, 400);
  // Honungsfälla: fältet "website" är dolt i appen. Låtsas att allt gick bra.
  if (b.website) return json({ ok: true });

  const rec = {
    kind: KINDS.includes(b.kind) ? b.kind : "annat",
    msg: str(b.msg, 2000), product: str(b.product, 200), code: str(b.code, 20).replace(/\D/g, ""),
    verdict: ["red", "amber", "green"].includes(b.verdict) ? b.verdict : "",
    ingredients: str(b.ingredients, 2000), allergens: str(b.allergens, 400),
    app: str(b.app, 40), at: new Date().toISOString()
  };
  if (!rec.msg && !rec.product) return json({ ok: false, error: "empty" }, 400);

  const day = rec.at.slice(0, 10);
  if (await count(env, "rl:day:" + day) >= DAILY_MAX) return json({ ok: false, error: "daily_limit" }, 429);
  if (await bump(env, "rl:ip:" + ip(request), IP_WINDOW) > PER_IP) return json({ ok: false, error: "rate_limited" }, 429);
  await bump(env, "rl:day:" + day, 86400 * 2);

  const id = rec.at.replace(/[:.]/g, "-") + "-" + crypto.randomUUID().slice(0, 8);
  await env.FEEDBACK.put("fb:" + id, JSON.stringify(rec), { expirationTtl: 60 * 60 * 24 * 365 });
  return json({ ok: true });
}

export async function onRequestGet({ request, env }) {
  if (!env.FEEDBACK) return json({ ok: false, error: "no_storage" }, 503);
  if (!sameSite(request)) return json({ ok: false, error: "forbidden" }, 403);
  const a = await authorized(request, env);
  if (!a.ok) return json({ ok: false, error: a.error }, a.status);
  const list = await env.FEEDBACK.list({ prefix: "fb:", limit: 500 });
  const items = await Promise.all(list.keys.map(async k => {
    try { return { id: k.name, ...JSON.parse(await env.FEEDBACK.get(k.name) || "{}") }; } catch { return { id: k.name }; }
  }));
  return json({ ok: true, items: items.reverse() });
}

export async function onRequestDelete({ request, env }) {
  if (!env.FEEDBACK) return json({ ok: false, error: "no_storage" }, 503);
  if (!sameSite(request)) return json({ ok: false, error: "forbidden" }, 403);
  const a = await authorized(request, env);
  if (!a.ok) return json({ ok: false, error: a.error }, a.status);
  const id = new URL(request.url).searchParams.get("id") || "";
  if (!/^fb:[0-9A-Za-z-]{10,80}$/.test(id)) return json({ ok: false, error: "bad_id" }, 400);
  await env.FEEDBACK.delete(id);
  return json({ ok: true });
}

// Andra metoder avvisas
export async function onRequest({ request }) {
  return json({ ok: false, error: "method_not_allowed" }, 405);
}
