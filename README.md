# Kan jag äta det?

En webbapp (PWA) som kollar matvaror mot en personlig allergiprofil. Den fungerar på iPhone, Android och dator.

- Allergiprofil med EU:s 14 allergener plus laktos, som allergi eller intolerans
- Streckkodsskanning och sökning i Open Food Facts
- Trafikljus (rött, gult, grönt) med markerade ingredienser
- Valfria AI-funktioner via Claude: fotoläsning av ingredienslistor, dubbelkoll och frågor
- Profil och nyckel sparas bara på enheten och kan flyttas med QR-kod
- Allergikort på sex språk, val att undvika även spår, fler vanliga allergener (ärtor, linser m.fl.)
- Info om allergisk reaktion (enligt 1177), allergener, E-nummer och märkning
- Varning för återkallade varor från Livsmedelsverket, samt listor med säkra varor och varor att undvika

## Publicering

Appen publiceras från mappen `public/` utan byggsteg. Den fungerar på Cloudflare Pages (byggkommando tomt, output-mapp `public`) och Netlify (`netlify.toml`). `public/_headers` styr cache-inställningar på Cloudflare.

## Struktur

| Sökväg | Innehåll |
| --- | --- |
| `src/kan-jag-ata-det.html` | Appens källkod (en fil). Samma fil körs också som sida i Claude. |
| `tools/build.py` | Bygger `public/` från källan: lägger till manifest, ikoner och service worker. |
| `public/` | Det som Netlify publicerar. |
| `tools/build_db.py` | Bygger den svenska varudatabasen från Open Food Facts export. |
| `public/data/` | Varudatabasen: sökindex, varor uppdelade på streckkod och status. Skrivs av GitHub Actions. |
| `.github/workflows/se-db.yml` | Kör `build_db.py` varje måndag och sparar resultatet i repot. |
| `tools/fetch_recalls.py` | Hämtar Livsmedelsverkets återkallelser och plockar ut streckkoder. |
| `.github/workflows/recalls.yml` | Kör `fetch_recalls.py` varje morgon och sparar `public/data/recalls.json`. |

## Varudatabasen

Varje måndag hämtar GitHub Actions Open Food Facts CSV-export och plockar ut varor som säljs i Sverige.
Appen söker först där och går bara ut till Open Food Facts API när en vara saknas.
Det tar bort API:ets gräns på 10 sökningar per minut och gör sökningen snabb.
Se `public/data/status.json` för senaste körning.

Data från [Open Food Facts](https://world.openfoodfacts.org), licens [ODbL](https://opendatacommons.org/licenses/odbl/1-0/).

## Ändra appen

1. Redigera `src/kan-jag-ata-det.html`.
2. Kör `node tests/analyze.test.js` och kontrollera att alla fall är godkända.
3. Kör `python3 tools/build.py` (kräver Pillow).
4. Committa och pusha. Netlify publicerar automatiskt.

Appen ersätter inte förpackningens märkning eller råd från läkare eller dietist.
