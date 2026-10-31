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

Webbplatsen publiceras från mappen `public/` utan byggsteg. Startsidan skickar vidare till appen när den öppnas från hemskärmen eller via en delningslänk. Den fungerar på Cloudflare Pages (byggkommando tomt, output-mapp `public`) och Netlify (`netlify.toml`). `public/_headers` styr cache-inställningar på Cloudflare.

## Struktur

| Sökväg | Innehåll |
| --- | --- |
| `src/kan-jag-ata-det.html` | Appens källkod (en fil). Samma fil körs också som sida i Claude. |
| `src/landing.html` | Startsidan som presenterar appen. |
| `src/assets/` | Bilder till startsidan. |
| `tools/build.py` | Bygger `public/`: startsidan i roten och appen i `public/app/` med manifest, ikoner och service worker. |
| `public/` | Det som Cloudflare Pages publicerar. Startsidan på `/`, appen på `/app/`, data på `/data/`. |
| `tools/build_db.py` | Bygger den svenska varudatabasen från Open Food Facts export. |
| `public/data/` | Varudatabasen: sökindex, varor uppdelade på streckkod och status. Skrivs av GitHub Actions. |
| `.github/workflows/se-db.yml` | Kör `build_db.py` varje måndag och sparar resultatet i repot. |
| `tools/fetch_recalls.py` | Hämtar Livsmedelsverkets återkallelser och plockar ut streckkoder. |
| `.github/workflows/recalls.yml` | Kör `fetch_recalls.py` varje morgon och sparar `public/data/recalls.json`. |

## Varudatabasen

Varje måndag hämtar GitHub Actions Open Food Facts export (Parquet, med CSV som reserv) och plockar ut varor som säljs i Sverige.
Appen söker först där och går bara ut till Open Food Facts API när en vara saknas.
Det tar bort API:ets gräns på 10 sökningar per minut och gör sökningen snabb.
Se `public/data/status.json` för senaste körning.

Data från [Open Food Facts](https://world.openfoodfacts.org), licens [ODbL](https://opendatacommons.org/licenses/odbl/1-0/).

## Offline

Appen sparar sina filer och hela varudatabasen i telefonen första gången den öppnas med uppkoppling
(ungefär 10 MB). Sedan fungerar sök, kontroll, listor och allergikort utan nät. Kameraskanning och
QR-koder använder bibliotek som ligger i `src/vendor/` (ZXing, Apache 2.0, och qrcode-generator, MIT).
Det som kräver nät är Claude-funktionerna och sökning hos Open Food Facts för varor som saknas i databasen.

## Ändrade ingredienslistor

`tools/build_db.py` jämför varje veckas ingredienslistor med förra veckans och skriver
`public/data/changes.json` med den gamla listan i 60 dagar. Appen visar då en rad i resultatet,
och en varning om en sparad säker vara har fått ett nytt recept som inte passar profilen.
Ändras över 15 % av listorna samma vecka räknas det som ett formatbyte och sparas inte.

## Feedback

Knappen "Rapportera" i resultatet och "Tyck till" under Info skickar till `functions/api/feedback.js`
(en Cloudflare Pages Function) som sparar i Cloudflare KV. Inget namn eller nyckel skickas; allergier
bara om användaren kryssar i det. Utan uppkoppling sparas feedbacken i telefonen och skickas senare.

Inställning i Cloudflare (gratisplanen räcker):
1. Storage & Databases → KV → Create namespace, till exempel `canieat-feedback`.
2. Pages-projektet → Settings → Bindings → Add → KV namespace. Namn: `FEEDBACK`, välj namespacet.
3. Settings → Variables and Secrets → Add, typ Secret. Namn: `FEEDBACK_KEY`, ett långt eget lösenord.
4. Gör en ny deploy (Deployments → Retry deployment), eller pusha något.

Läs feedbacken på `/feedback-admin.html` med lösenordet från steg 3.

## Ändra appen

1. Redigera `src/kan-jag-ata-det.html`.
2. Kör `node tests/analyze.test.js` och kontrollera att alla fall är godkända.
3. Kör `python3 tools/build.py` (kräver Pillow).
4. Committa och pusha. Cloudflare Pages publicerar automatiskt.

Appen ersätter inte förpackningens märkning eller råd från läkare eller dietist.

## Säkerhet

Se [SECURITY.md](SECURITY.md) för hur appen, datan och feedbackfunktionen skyddas, och vilka inställningar ägaren gör.
