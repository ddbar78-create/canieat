#!/usr/bin/env python3
"""Bygger en svensk varudatabas för appen från Open Food Facts.

Körs varje vecka av GitHub Actions (.github/workflows/se-db.yml).

Källa 1 (förstahand): Parquet-exporten på Hugging Face. Den innehåller varje
vara på alla språk den finns på, så vi kan välja svenskt namn och svensk
ingredienslista när de finns. Läses med DuckDB.
Källa 2 (reserv): CSV-exporten, som bara har varans huvudspråk.

Varor som säljs i Sverige skrivs till:
  <ut>/se-index.json   sökindex: [streckkod, namn, märke, har_ingredienser]
  <ut>/p/NN.json       {streckkod: [namn, märke, ingredienser, allergener, spår, språk]}
                       uppdelat efter streckkodens två sista siffror
  <ut>/status.json     när det kördes, källa, antal varor, språk och eventuellt fel
  <ut>/changes.json    varor vars ingredienslista ändrats de senaste 60 dagarna,
                       med den gamla listan: {updated, items:{streckkod:{date, prev}}}

Användning:
  python3 tools/build_db.py public/data                      # hämtar exporten
  python3 tools/build_db.py public/data --parquet fil.parquet  # lokal test
  python3 tools/build_db.py public/data --csv fil.csv.gz       # lokal test

Data från Open Food Facts, licens ODbL: https://world.openfoodfacts.org
"""
import csv, gzip, html, io, json, os, re, shutil, sys, tempfile, time, urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone

PARQUET_URL = "https://huggingface.co/datasets/openfoodfacts/product-database/resolve/main/food.parquet"
CSV_URL = "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz"
UA = "KanJagAtaDet/1.0 (https://github.com/ddbar78-create/canieat)"
COUNTRY = "en:sweden"
MAX_NAME = 90
MAX_INGR = 1500
MIN_PRODUCTS = int(os.environ.get("MIN_PRODUCTS", "100"))
CHANGE_DAYS = 60          # hur länge en ändring visas i appen
CHANGE_MAX_SHARE = 0.15   # ändras fler än så på en gång är det troligen ett formatbyte, inte nya recept


def clean(s, n):
    """Tar bort HTML-taggar (Open Food Facts markerar allergener med <span class="allergen">)
    och understreck runt ord (_mjölk_), avkodar &amp; och liknande, och slår ihop blanksteg."""
    t = html.unescape(re.sub(r"<[^>]*>", "", str(s or "")))
    t = re.sub(r"(?<![\w])_+([^_]+?)_+(?![\w])", r"\1", t)
    return " ".join(t.split())[:n]


def tags(value):
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = str(value or "").split(",")
    out = []
    for t in items:
        t = str(t or "").strip()
        if t and t not in out:
            out.append(t)
    return out


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f, 1 << 22)
    return dest


# ---------- Källa 1: Parquet (alla språk) ----------

def read_parquet(path, status):
    import duckdb  # installeras i arbetsflödet
    con = duckdb.connect()
    src = f"read_parquet('{path}')"
    cols = {r[0]: r[1] for r in con.execute(f"DESCRIBE SELECT * FROM {src}").fetchall()}
    status["parquet_columns"] = {k: cols.get(k) for k in
                                 ("code", "product_name", "ingredients_text", "lang", "brands",
                                  "countries_tags", "allergens_tags", "traces_tags")}

    def multilang(col):
        """Uttryck för (svensk text, text på huvudspråket/första språket, svenska finns?)."""
        t = cols.get(col, "")
        if t.startswith("STRUCT") and t.endswith("[]") and "lang" in t and "text" in t:
            sv = f"list_extract(list_filter({col}, lambda x: x.lang = 'sv' AND length(trim(x.text)) > 0), 1).text"
            main = f"list_extract(list_filter({col}, lambda x: x.lang = 'main' AND length(trim(x.text)) > 0), 1).text"
            mainlang = (f"list_extract(list_filter({col}, lambda x: x.lang = lang AND length(trim(x.text)) > 0), 1).text"
                        if "lang" in cols else "NULL")
            first = f"list_extract(list_filter({col}, lambda x: length(trim(x.text)) > 0), 1).text"
            firstlang = f"list_extract(list_filter({col}, lambda x: x.lang <> 'main' AND length(trim(x.text)) > 0), 1).lang"
            return sv, f"coalesce({main}, {mainlang}, {first})", firstlang
        if t:
            svcol = f"{col}_sv"
            sv = svcol if svcol in cols else "NULL"
            return sv, col, "NULL"
        return "NULL", "NULL", "NULL"

    if "code" not in cols or "countries_tags" not in cols:
        raise RuntimeError("Parquet saknar code eller countries_tags")
    ct = cols["countries_tags"]
    where = "list_contains(countries_tags, 'en:sweden')" if ct.endswith("[]") else "countries_tags LIKE '%en:sweden%'"
    n_sv, n_main, n_lang = multilang("product_name")
    i_sv, i_main, i_lang = multilang("ingredients_text")
    lang = "lang" if "lang" in cols else "NULL"
    brands = cols.get("brands", "")
    brands_x = "array_to_string(brands, ', ')" if brands.endswith("[]") else ("brands" if brands else "''")
    al = "allergens_tags" if "allergens_tags" in cols else "NULL"
    tr = "traces_tags" if "traces_tags" in cols else "NULL"
    sql = f"""
      SELECT CAST(code AS VARCHAR), {n_sv}, {n_main}, {i_sv}, {i_main},
             coalesce({lang}, {i_lang}, {n_lang}), {brands_x}, {al}, {tr}
      FROM {src} WHERE {where}"""
    rows = con.execute(sql).fetchall()
    status["rows_matched"] = len(rows)
    for code, nsv, nmain, isv, imain, lg, brand, a, t in rows:
        name = nsv or nmain
        if isv:
            ingr, ilang = isv, "sv"
        else:
            ingr, ilang = imain, (lg or "")
        yield code, name, brand, ingr, ilang, tags(a), tags(t)


# ---------- Källa 2: CSV (bara huvudspråket) ----------

def read_csv(path, status):
    csv.field_size_limit(sys.maxsize)
    raw = open(path, "rb")
    reader = csv.reader(io.TextIOWrapper(gzip.GzipFile(fileobj=raw), encoding="utf-8", errors="replace", newline=""),
                        delimiter="\t", quoting=csv.QUOTE_NONE)
    header = next(reader)
    def col(*names):
        for n in names:
            if n in header:
                return header.index(n)
        return None
    c = dict(code=col("code"), name=col("product_name_sv", "product_name"), brand=col("brands"),
             country=col("countries_tags", "countries_en", "countries"),
             ingr=col("ingredients_text_sv", "ingredients_text"), lang=col("lang"),
             al=col("allergens_tags", "allergens", "allergens_en"), tr=col("traces_tags", "traces", "traces_en"))
    status["csv_columns"] = {k: (header[v] if v is not None else None) for k, v in c.items()}
    if None in (c["code"], c["name"], c["country"]):
        raise RuntimeError("CSV saknar nödvändiga kolumner")
    need = max(c["code"], c["name"], c["country"])
    get = lambda row, k: row[c[k]] if c[k] is not None and c[k] < len(row) else ""
    n = 0
    for row in reader:
        n += 1
        if len(row) <= need:
            continue
        countries = row[c["country"]].lower()
        if COUNTRY not in countries and "sweden" not in countries:
            continue
        yield (row[c["code"]], get(row, "name"), get(row, "brand"), get(row, "ingr"),
               get(row, "lang"), tags(get(row, "al")), tags(get(row, "tr")))
    status["rows_scanned"] = n


# ---------- Gemensamt ----------

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)


def collect(records):
    index, shards, langs = [], {}, Counter()
    seen = set()
    for code, name, brand, ingr, lang, al, tr in records:
        code = str(code or "").strip()
        name = clean(name, MAX_NAME)
        if not code.isdigit() or len(code) < 8 or not name or code in seen:
            continue
        seen.add(code)
        ingr = clean(ingr, MAX_INGR)
        lang = str(lang or "")[:5] if ingr else ""
        if ingr:
            langs[lang or "?"] += 1
        index.append([code, name, clean(brand, 60), 1 if (ingr or al) else 0])
        shards.setdefault(code[-2:].zfill(2), {})[code] = [name, clean(brand, 60), ingr, al, tr, lang]
    return index, shards, langs


def norm_ingr(s):
    """Jämförbar form: små bokstäver, bara bokstäver och siffror."""
    return re.sub(r"[^0-9a-zåäöæøüéè]+", " ", str(s or "").lower()).strip()


def find_changes(out, shards, today, status):
    """Jämför nya ingredienslistor med förra körningens och uppdaterar changes.json."""
    path = os.path.join(out, "changes.json")
    try:
        items = json.load(open(path, encoding="utf-8")).get("items", {})
    except Exception:
        items = {}
    cutoff = (datetime.fromisoformat(today) - timedelta(days=CHANGE_DAYS)).date().isoformat()
    items = {k: v for k, v in items.items() if v.get("date", "") >= cutoff}
    fresh, compared = {}, 0
    for nn, data in shards.items():
        try:
            old = json.load(open(os.path.join(out, "p", nn + ".json"), encoding="utf-8"))
        except Exception:
            continue
        for code, row in data.items():
            o = old.get(code)
            if not o or not o[2] or not row[2]:
                continue
            compared += 1
            # Samma språk krävs, annars är det en översättning och inte ett nytt recept
            if (o[5] or "") != (row[5] or ""):
                continue
            if norm_ingr(o[2]) != norm_ingr(row[2]):
                fresh[code] = {"date": today, "prev": o[2][:800]}
    share = len(fresh) / compared if compared else 0
    status["ingredient_changes"] = {"compared": compared, "changed": len(fresh), "share": round(share, 4)}
    if share > CHANGE_MAX_SHARE:
        status["ingredient_changes"]["skipped"] = "för många ändringar på en gång"
    else:
        items.update(fresh)
    write_json(path, {"v": 1, "updated": today, "items": items})


def main():
    args = sys.argv[1:]
    out = args[0] if args else "public/data"
    local = dict(zip(args[1::2], args[2::2])) if len(args) > 2 else {}
    started = time.time()
    status = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "ok": False}
    tmpdir = tempfile.mkdtemp()
    try:
        index = None
        sources = [("parquet", local.get("--parquet")), ("csv", local.get("--csv"))] if local else \
                  [("parquet", None), ("csv", None)]
        errors = {}
        for kind, path in sources:
            if local and not path:
                continue
            try:
                if kind == "parquet":
                    path = path or download(PARQUET_URL, os.path.join(tmpdir, "food.parquet"))
                    index, shards, langs = collect(read_parquet(path, status))
                else:
                    path = path or download(CSV_URL, os.path.join(tmpdir, "food.csv.gz"))
                    index, shards, langs = collect(read_csv(path, status))
                if len(index) < MIN_PRODUCTS:
                    raise RuntimeError(f"För få svenska varor ({len(index)})")
                status["source"] = kind
                break
            except Exception as e:
                errors[kind] = f"{type(e).__name__}: {e}"[:400]
                index = None
            finally:
                if path and path.startswith(tmpdir) and os.path.exists(path):
                    os.remove(path)
        if errors:
            status["source_errors"] = errors
        if index is None:
            raise RuntimeError("Ingen källa fungerade")

        # Skydd mot ofullständig nedladdning: ersätt aldrig en databas med en som är mycket mindre
        try:
            prev = json.load(open(os.path.join(out, "se-index.json"), encoding="utf-8")).get("n", 0)
        except Exception:
            prev = 0
        if prev and len(index) < prev * 0.8:
            raise RuntimeError(f"Bara {len(index)} varor mot {prev} förra gången. Behåller den gamla databasen.")

        index.sort(key=lambda r: (-r[3], r[1].lower()))
        try:
            find_changes(out, shards, status["updated"], status)
        except Exception as e:  # ändringslistan får aldrig stoppa databasen
            status["ingredient_changes"] = {"error": f"{type(e).__name__}: {e}"[:300]}
        for nn, data in shards.items():
            write_json(os.path.join(out, "p", nn + ".json"), data)
        write_json(os.path.join(out, "se-index.json"),
                   {"v": 2, "updated": status["updated"], "n": len(index), "items": index})
        status.update(ok=True, products=len(index), with_ingredients=sum(r[3] for r in index),
                      ingredient_languages=dict(langs.most_common(12)))
    except Exception as e:  # skriv alltid status så att felet syns i repot
        status["error"] = f"{type(e).__name__}: {e}"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    status["seconds"] = round(time.time() - started)
    write_json(os.path.join(out, "status.json"), status)
    print(json.dumps(status, ensure_ascii=False, indent=1))
    return 0 if status["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
