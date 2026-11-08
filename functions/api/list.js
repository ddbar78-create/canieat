// Delad inköpslista. Sparas i samma Cloudflare KV som feedbacken (bindning FEEDBACK), med prefixet "list:".
//
// Den som har listans id kan läsa och ändra den. Id:t är 22 slumpmässiga tecken (ca 130 bitar),
// så det går inte att gissa. Inga allergiprofiler sparas här, bara raderna och valda varor.
//
// Skydd:
// - Bara anrop från appens egen webbplats (Origin/Sec-Fetch-Site)
// - Storleksgränser på allt; listan raderas automatiskt efter 120 dagar utan ändringar
// - Högst 300 rader per lista
const ID = /^[A-Za-z0-9_-]{22}$/;
const MAX_ITEMS = 300, MAX_BODY = 200000, TTL = 60 * 60 * 24 * 120, TOMBSTONE_DAYS = 30;

const json = (d, status = 200) => new Response(JSON.stringify(d), {
  status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", "x-content-type-options": "nosniff" }
});
const str = (v, n) => String(v ?? "").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, "").slice(0, n);
const tags = v => Array.isArray(v) ? v.slice(0, 40).map(x => str(x, 60)) : [];

function sameSite(request) {
  const site = request.headers.get("sec-fetch-site");
  if (site && site !== "same-origin") return false;
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin) return false;
  return true;
}

function cleanItem(x) {
  if (!x || typeof x !== "object" || !/^[a-z0-9]{4,12}$/.test(String(x.id || ""))) return null;
  const u = Math.min(Number(x.u) || 0, Date.now() + 86400000);
  if (x.d) return { id: x.id, d: 1, u };
  const it = { id: x.id, t: str(x.t, 80), done: !!x.done, u };
  if (x.changed) it.changed = true;
  if (x.p && typeof x.p === "object") it.p = {
    code: str(x.p.code, 14).replace(/\D/g, ""), product_name: str(x.p.product_name, 200), brands: str(x.p.brands, 200),
    ingredients_text: str(x.p.ingredients_text, 3000), allergens_tags: tags(x.p.allergens_tags), traces_tags: tags(x.p.traces_tags), _lang: str(x.p._lang, 5)
  };
  return it.t ? it : null;
}

// Senaste ändringen per rad vinner. Borttagna rader sparas en tid så att borttagningen når alla telefoner.
function merge(a, b) {
  const m = new Map();
  for (const x of [...a, ...b]) { const o = m.get(x.id); if (!o || (x.u || 0) > (o.u || 0)) m.set(x.id, x); }
  const old = Date.now() - TOMBSTONE_DAYS * 86400000;
  return [...m.values()].filter(x => !(x.d && x.u < old)).slice(-MAX_ITEMS);
}

async function load(env, id) {
  try { return JSON.parse(await env.FEEDBACK.get("list:" + id) || "null"); } catch { return null; }
}

export async function onRequestGet({ request, env }) {
  if (!env.FEEDBACK) return json({ ok: false, error: "no_storage" }, 503);
  if (!sameSite(request)) return json({ ok: false, error: "forbidden" }, 403);
  const id = new URL(request.url).searchParams.get("id") || "";
  if (!ID.test(id)) return json({ ok: false, error: "bad_id" }, 400);
  const d = await load(env, id);
  return json({ ok: true, items: d ? d.items : [] });
}

export async function onRequestPut({ request, env }) {
  if (!env.FEEDBACK) return json({ ok: false, error: "no_storage" }, 503);
  if (!sameSite(request)) return json({ ok: false, error: "forbidden" }, 403);
  if (!(request.headers.get("content-type") || "").includes("application/json")) return json({ ok: false, error: "bad_type" }, 415);
  const id = new URL(request.url).searchParams.get("id") || "";
  if (!ID.test(id)) return json({ ok: false, error: "bad_id" }, 400);
  let raw;
  try { raw = await request.text(); } catch { return json({ ok: false, error: "bad_body" }, 400); }
  if (raw.length > MAX_BODY) return json({ ok: false, error: "too_large" }, 413);
  let b;
  try { b = JSON.parse(raw); } catch { return json({ ok: false, error: "bad_json" }, 400); }
  const incoming = (Array.isArray(b && b.items) ? b.items : []).slice(0, MAX_ITEMS * 2).map(cleanItem).filter(Boolean);
  const cur = await load(env, id);
  const items = merge(cur ? cur.items : [], incoming);
  const before = JSON.stringify(cur ? cur.items : []);
  // Skriv bara om något faktiskt ändrats (KV:s gratisnivå tål 1 000 skrivningar per dygn)
  if (JSON.stringify(items) !== before) await env.FEEDBACK.put("list:" + id, JSON.stringify({ items, at: Date.now() }), { expirationTtl: TTL });
  return json({ ok: true, items });
}

export async function onRequest() {
  return json({ ok: false, error: "method_not_allowed" }, 405);
}
