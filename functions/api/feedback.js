// Feedback från appen. Sparas i Cloudflare KV (bindning FEEDBACK).
// Läs rapporterna på /feedback-admin.html med nyckeln i miljövariabeln FEEDBACK_KEY.
const KINDS = ["fel_besked", "data", "ide", "annat"];
const json = (d, status = 200) => new Response(JSON.stringify(d), {
  status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" }
});
const str = (v, n) => String(v ?? "").slice(0, n);
const authorized = (request, env) =>
  !!env.FEEDBACK_KEY && (request.headers.get("authorization") || "") === "Bearer " + env.FEEDBACK_KEY;

export async function onRequestPost({ request, env }) {
  if (!env.FEEDBACK) return json({ ok: false, error: "no_storage" }, 503);
  const len = Number(request.headers.get("content-length") || 0);
  if (len > 12000) return json({ ok: false, error: "too_large" }, 413);
  let b;
  try { b = await request.json(); } catch { return json({ ok: false, error: "bad_json" }, 400); }
  const rec = {
    kind: KINDS.includes(b.kind) ? b.kind : "annat",
    msg: str(b.msg, 2000), product: str(b.product, 200), code: str(b.code, 20).replace(/\D/g, ""),
    verdict: str(b.verdict, 10), ingredients: str(b.ingredients, 2000), allergens: str(b.allergens, 400),
    app: str(b.app, 40), at: new Date().toISOString()
  };
  if (!rec.msg && !rec.product) return json({ ok: false, error: "empty" }, 400);
  const id = rec.at.replace(/[:.]/g, "-") + "-" + crypto.randomUUID().slice(0, 8);
  await env.FEEDBACK.put("fb:" + id, JSON.stringify(rec), { expirationTtl: 60 * 60 * 24 * 365 });
  return json({ ok: true });
}

export async function onRequestGet({ request, env }) {
  if (!env.FEEDBACK) return json({ ok: false, error: "no_storage" }, 503);
  if (!authorized(request, env)) return json({ ok: false, error: "unauthorized" }, 401);
  const list = await env.FEEDBACK.list({ prefix: "fb:", limit: 500 });
  const items = await Promise.all(list.keys.map(async k => {
    try { return { id: k.name, ...JSON.parse(await env.FEEDBACK.get(k.name) || "{}") }; } catch { return { id: k.name }; }
  }));
  return json({ ok: true, items: items.reverse() });
}

export async function onRequestDelete({ request, env }) {
  if (!env.FEEDBACK) return json({ ok: false, error: "no_storage" }, 503);
  if (!authorized(request, env)) return json({ ok: false, error: "unauthorized" }, 401);
  const id = new URL(request.url).searchParams.get("id") || "";
  if (!id.startsWith("fb:")) return json({ ok: false, error: "bad_id" }, 400);
  await env.FEEDBACK.delete(id);
  return json({ ok: true });
}
