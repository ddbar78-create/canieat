# Säkerhet – Kan jag äta det?

Appen ger besked om mat för personer med allergier. Fel besked kan vara farligt, så både koden och datan skyddas mot att förstöras eller manipuleras.

## Skydd i appen

| Hot | Skydd |
| --- | --- |
| Inskjuten kod (XSS) via varudata, återkallelser, delade profiler eller AI-svar | All extern text escapas innan den visas. Content Security Policy tillåter bara appens egna skript, med exakt hash för de inbäddade skripten. |
| Sidan byggs in i en annan webbplats (clickjacking) | `frame-ancestors 'none'` och `X-Frame-Options: DENY` |
| Länkar till falska sidor via återkallelsedata | Länkar från återkallelser får bara gå till livsmedelsverket.se |
| Manipulerad QR-kod eller delningslänk som tar bort allergier | Appen visar alltid vad som tas emot och varnar i rött om allergier försvinner eller nyckeln byts |
| Klåfingrig data i Open Food Facts (borttagna allergener) | Produktnamnet kontrolleras, osäker data blir aldrig grönt, och ändrade ingredienslistor visas med det tidigare beskedet |
| Främmande skript och bibliotek | Skanner- och QR-bibliotek ligger i repot (`src/vendor/`), inget skript hämtas från andra webbplatser |
| API-nyckel och profil | Sparas bara på användarens enhet, skickas aldrig till vår server |

## Skydd i feedbackfunktionen (`functions/api/feedback.js`)

- Tar bara emot anrop från appens egen webbplats
- Honungsfälla mot robotar
- Högst 5 rapporter per IP-adress och 10 minuter, högst 200 per dygn
- Läsning och borttagning kräver `FEEDBACK_KEY` (minst 8 tecken), jämförs i konstant tid
- Efter 10 fel försök på 15 minuter spärras IP-adressen
- Storleksgränser på alla fält

## Skydd i GitHub

- GitHub Actions är låsta till exakta versioner (commit-hash) och har bara de behörigheter de behöver
- Dependabot påminner när de får säkerhetsuppdateringar
- Databasjobbet ersätter aldrig databasen med en som är mer än 20 % mindre, och hoppar över ändringslistan om fler än 15 % av varorna ändrats på en gång

## Inställningar som ägaren gör

1. Tvåstegsverifiering på GitHub, Cloudflare, Anthropic och e-postkontot
2. GitHub: regel för grenen `main` som spärrar force push och borttagning
3. GitHub: Claude-appen bara med tillgång till `canieat`
4. Cloudflare: `FEEDBACK_KEY` som lång, slumpmässig hemlighet
5. Anthropic: månadsgräns och en nyckel per enhet; ta bort nycklar som inte används
6. Ta bort gamla Netlify-projektet

## Rapportera ett säkerhetsproblem

Använd **Tyck till** i appen, välj **Annat** och skriv "Säkerhet" först i meddelandet. Skriv inte detaljer om sårbarheten i en publik GitHub-issue.
