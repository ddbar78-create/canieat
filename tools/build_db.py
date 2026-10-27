#!/usr/bin/env python3
"""Bygger en svensk varudatabas för appen från Open Food Facts CSV-export.

Körs varje vecka av GitHub Actions (.github/workflows/se-db.yml).
Laddar ner exporten som en ström (ca 1 GB komprimerat), plockar ut varor som
säljs i Sverige och skriver:

  <ut>/se-index.json   sökindex: [streckkod, namn, märke, har_ingredienser]
  <ut>/p/NN.json       detaljer, uppdelade efter streckkodens två sista siffror
  <ut>/status.json     när det kördes, antal varor och eventuellt fel

Användning:
  python3 tools/build_db.py public/data            # hämtar exporten
  python3 tools/build_db.py public/data fil.csv.gz # läser en lokal fil (test)

Data från Open Food Facts, licens ODbL: https://world.openfoodfacts.org
"""
import csv, gzip, io, json, os, sys, time, urllib.request
from datetime import datetime, timezone

URL = "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz"
UA = "KanJagAtaDet/1.0 (https://github.com/ddbar78-create/canieat)"
COUNTRY = "en:sweden"
MAX_NAME = 90
MAX_INGR = 1500


def first_col(header, *names):
    for n in names:
        if n in header:
            return header.index(n)
    return None


def tags(value):
    out = []
    for t in (value or "").split(","):
        t = t.strip()
        if t and t not in out:
            out.append(t)
    return out


def open_source(path):
    if path:
        raw = open(path, "rb")
    else:
        req = urllib.request.Request(URL, headers={"User-Agent": UA})
        raw = urllib.request.urlopen(req, timeout=120)
    return io.TextIOWrapper(gzip.GzipFile(fileobj=raw), encoding="utf-8", errors="replace", newline="")


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "public/data"
    src = sys.argv[2] if len(sys.argv) > 2 else None
    started = time.time()
    status = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "ok": False}
    try:
        csv.field_size_limit(sys.maxsize)
        reader = csv.reader(open_source(src), delimiter="\t", quoting=csv.QUOTE_NONE)
        header = next(reader)
        c_code = first_col(header, "code")
        c_name = first_col(header, "product_name_sv", "product_name")
        c_brand = first_col(header, "brands")
        c_country = first_col(header, "countries_tags", "countries_en", "countries")
        c_ingr = first_col(header, "ingredients_text_sv", "ingredients_text")
        c_all = first_col(header, "allergens_tags", "allergens", "allergens_en")
        c_tr = first_col(header, "traces_tags", "traces", "traces_en")
        status["columns"] = {k: (header[v] if v is not None else None) for k, v in
                             dict(code=c_code, name=c_name, brand=c_brand, country=c_country,
                                  ingredients=c_ingr, allergens=c_all, traces=c_tr).items()}
        if None in (c_code, c_name, c_country):
            raise RuntimeError("Saknar nödvändiga kolumner i exporten")

        index, shards, rows = [], {}, 0
        for row in reader:
            rows += 1
            if len(row) <= max(c_code, c_name, c_country):
                continue
            countries = row[c_country].lower()
            if COUNTRY not in countries and "sweden" not in countries and "sverige" not in countries:
                continue
            code = row[c_code].strip()
            name = " ".join(row[c_name].split())[:MAX_NAME]
            if not code.isdigit() or len(code) < 8 or not name:
                continue
            brand = " ".join(row[c_brand].split())[:60] if c_brand is not None and c_brand < len(row) else ""
            ingr = " ".join(row[c_ingr].split())[:MAX_INGR] if c_ingr is not None and c_ingr < len(row) else ""
            al = tags(row[c_all]) if c_all is not None and c_all < len(row) else []
            tr = tags(row[c_tr]) if c_tr is not None and c_tr < len(row) else []
            index.append([code, name, brand, 1 if (ingr or al) else 0])
            shards.setdefault(code[-2:].zfill(2), {})[code] = [name, brand, ingr, al, tr]

        if len(index) < 100:
            raise RuntimeError(f"För få svenska varor hittades ({len(index)} av {rows} rader)")

        index.sort(key=lambda r: (-r[3], r[1].lower()))
        for nn, data in shards.items():
            write_json(os.path.join(out, "p", nn + ".json"), data)
        write_json(os.path.join(out, "se-index.json"),
                   {"v": 1, "updated": status["updated"], "n": len(index), "items": index})
        status.update(ok=True, products=len(index),
                      with_ingredients=sum(r[3] for r in index), rows_scanned=rows)
    except Exception as e:  # skriv alltid status så att felet syns i repot
        status["error"] = f"{type(e).__name__}: {e}"
    status["seconds"] = round(time.time() - started)
    write_json(os.path.join(out, "status.json"), status)
    print(json.dumps(status, ensure_ascii=False, indent=1))
    return 0 if status["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
