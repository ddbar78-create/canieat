# Kan jag äta det?

En webbapp (PWA) som kollar matvaror mot en personlig allergiprofil. Den fungerar på iPhone, Android och dator.

- Allergiprofil med EU:s 14 allergener plus laktos, som allergi eller intolerans
- Streckkodsskanning och sökning i Open Food Facts
- Trafikljus (rött, gult, grönt) med markerade ingredienser
- Valfria AI-funktioner via Claude: fotoläsning av ingredienslistor, dubbelkoll och frågor
- Profil och nyckel sparas bara på enheten och kan flyttas med QR-kod

## Struktur

| Sökväg | Innehåll |
| --- | --- |
| `src/kan-jag-ata-det.html` | Appens källkod (en fil). Samma fil körs också som sida i Claude. |
| `tools/build.py` | Bygger `public/` från källan: lägger till manifest, ikoner och service worker. |
| `public/` | Det som Netlify publicerar. |

## Ändra appen

1. Redigera `src/kan-jag-ata-det.html`.
2. Kör `python3 tools/build.py` (kräver Pillow).
3. Committa och pusha. Netlify publicerar automatiskt.

Appen ersätter inte förpackningens märkning eller råd från läkare eller dietist.
