#!/usr/bin/env python3
"""Hämtar Livsmedelsverkets återkallelser till appen.

Körs dagligen av GitHub Actions (.github/workflows/recalls.yml).
RSS-flödet visar bara de senaste återkallelserna, så skriptet slår ihop dem
med det som redan finns sparat och behåller ett år bakåt.

För varje ny återkallelse läses sidan hos Livsmedelsverket och streckkoder
(EAN) plockas ut, så att appen kan varna när någon skannar en återkallad vara.

Användning:
  python3 tools/fetch_recalls.py public/data/recalls.json
  python3 tools/fetch_recalls.py public/data/recalls.json feed.xml   # lokal test
"""
import email.utils, html, json, os, re, sys, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

FEED = "https://www.livsmedelsverket.se/rss/rss-aterkallanden"
UA = "KanJagAtaDet/1.0 (https://github.com/ddbar78-create/canieat)"
KEEP_DAYS = 365
MAX_ITEMS = 300


def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def ean_ok(code):
    if len(code) not in (8, 12, 13, 14) or not code.isdigit():
        return False
    digits = [int(c) for c in code]
    check = digits.pop()
    total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(digits)))
    return (10 - total % 10) % 10 == check


def page_text(raw):
    t = raw.decode("utf-8", "replace")
    t = re.sub(r"(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t))


def eans_in(text):
    """Streckkoder: 13 siffror (giltig kontrollsiffra), eller 8/12/14 siffror nära ordet EAN/streckkod."""
    found = []
    for m in re.finditer(r"(?<!\d)(\d{8}|\d{12,14})(?!\d)", text.replace(" ", " ")):
        code = m.group(1)
        near = text[max(0, m.start() - 120):m.start()].lower()
        keyword = any(k in near for k in ("ean", "streckkod", "gtin", "artikelnummer"))
        if ean_ok(code) and (len(code) == 13 or keyword) and code not in found:
            found.append(code)
    return found[:50]


def parse_feed(raw):
    root = ET.fromstring(raw)
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        desc = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", it.findtext("description") or ""))).strip()
        pub = it.findtext("pubDate") or ""
        try:
            date = email.utils.parsedate_to_datetime(pub).date().isoformat()
        except Exception:
            date = datetime.now(timezone.utc).date().isoformat()
        if title and link:
            items.append({"title": title, "link": link, "desc": desc[:400], "date": date})
    return items


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "public/data/recalls.json"
    local_feed = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        old = json.load(open(out, encoding="utf-8"))
    except Exception:
        old = {"items": []}
    known = {r["link"]: r for r in old.get("items", [])}
    status = {"ok": False}
    try:
        raw = open(local_feed, "rb").read() if local_feed else get(FEED)
        fresh = parse_feed(raw)
        added = 0
        for r in fresh:
            prev = known.get(r["link"])
            if prev and prev.get("eans_checked"):
                prev.update(title=r["title"], desc=r["desc"] or prev.get("desc", ""))
                continue
            r["eans"] = []
            if not local_feed:
                try:
                    r["eans"] = eans_in(page_text(get(r["link"], timeout=45)))
                    r["eans_checked"] = True
                except Exception as e:
                    r["eans_error"] = type(e).__name__
            known[r["link"]] = r
            added += 0 if prev else 1
        status.update(ok=True, feed_items=len(fresh), added=added)
    except Exception as e:
        status["error"] = f"{type(e).__name__}: {e}"

    cutoff = (datetime.now(timezone.utc) - timedelta(days=KEEP_DAYS)).date().isoformat()
    items = sorted((r for r in known.values() if r.get("date", "") >= cutoff),
                   key=lambda r: r.get("date", ""), reverse=True)[:MAX_ITEMS]
    data = {"v": 1, "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "source": FEED, "status": status, "items": items}
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out + ".tmp", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=0)
    os.replace(out + ".tmp", out)
    print(json.dumps({**status, "total": len(items),
                      "with_eans": sum(1 for r in items if r.get("eans"))}, ensure_ascii=False))
    return 0 if status["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
