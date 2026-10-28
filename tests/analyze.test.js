// Regressionstest för allergenmatchningen. Kör: node tests/analyze.test.js
const fs = require("fs");
const html = fs.readFileSync(__dirname + "/../src/kan-jag-ata-det.html", "utf8");
let js = html.split("<script>")[1].split("/* ---------- Extra säkerhetskontroller")[0];
js = js.replace(/let profile = [^\n]+/, 'let profile={levels:{mjolk:"allergi",gluten:"allergi",agg:"allergi",notter:"allergi",fisk:"allergi",jordnot:"allergi",kokos:"allergi"},custom:[]};')
       .replace(/let history[^\n]+/, "")
       .replace("const store = {", "const localStorage={getItem(){return null},setItem(){}};const store = {");
const analyze = new Function(js + "; return analyze;")();

// [text, språkkod från databasen, förväntat språk, allergener som MÅSTE hittas, allergener som INTE får hittas]
const cases = [
  ["Vetemjöl, socker, smör, ägg, hasselnötter, kokosmjölk. Kan innehålla spår av fisk.", "", "sv", ["Gluten","Ägg","Mjölk","Nötter","Kokos","Fisk"], []],
  ["Havredryck: vatten, havre, rapsolja, kakaosmör, mjölksyra.", "", "sv", [], ["Mjölk"]],
  ["Sokeri, kaakaovoi, täysmaitojauhe, kerma, emulgointiaine.", "en", "fi", ["Mjölk"], []],
  ["Sokeri/socker, vehnäjauho/vetemjöl, voi/smör, suola/salt.", "", "fi", ["Gluten","Mjölk"], []],
  ["Sokeri, mustekala, kookosmaito, tattari, vesi, suola. Voi sisältää kalaa.", "", "fi", ["Kokos","Fisk"], ["Mjölk"]],
  ["Weizenmehl, Zucker, Butter, Vollei, Haselnüsse, Kokosmilch, Salz. Kann Spuren von Erdnüssen enthalten.", "", "de", ["Gluten","Ägg","Mjölk","Nötter","Kokos","Jordnötter"], []],
  ["Wasser, Zucker, Buchweizen, Tintenfisch, Kokosnuss, Salz, Ei.", "", "de", ["Ägg","Kokos"], ["Gluten","Fisk","Nötter"]],
  ["Water, wheat flour, sugar, butter (milk), whole egg, hazelnuts, coconut milk, peanut butter, nutmeg.", "", "en", ["Gluten","Mjölk","Ägg","Nötter","Kokos","Jordnötter"], []],
  ["Coconut milk, water, sugar, salt, nutmeg.", "", "en", ["Kokos"], ["Mjölk","Nötter"]],
  ["Hvetemel, sukker, smør, egg, hasselnøtter, salt, pålegg. Kan inneholde spor av fisk.", "", "dano", ["Gluten","Ägg","Mjölk","Nötter","Fisk"], []],
  ["Hvedemel, sukker, æg, frugt, salt.", "", "dano", ["Gluten","Ägg"], ["Mjölk"]],
  ["Farine de blé, sucre, beurre, œufs, noisettes, lait de coco, sel.", "", "fr", ["Gluten","Mjölk","Ägg","Nötter","Kokos"], []],
  ["Eau, sucre, lait de coco, noix de coco, sel, maltodextrine.", "", "fr", ["Kokos"], ["Mjölk","Gluten","Nötter"]],
  ["Tarwebloem, suiker, boter, eieren, zout.", "", "nl", [], []],
];
let fail = 0;
for (const [text, hint, lang, must, mustNot] of cases) {
  const r = analyze(text, hint);
  const found = new Set(r.findings.filter(f => f.kind !== "info").map(f => f.a.name));
  const errs = [];
  if (r.lang !== lang) errs.push(`språk ${r.lang}, väntade ${lang}`);
  for (const m of must) if (!found.has(m)) errs.push(`missade ${m}`);
  for (const m of mustNot) if (found.has(m)) errs.push(`felaktig träff ${m}`);
  if (errs.length) { fail++; console.log("FEL:", text.slice(0, 50), "→", errs.join("; ")); }
}
console.log(fail ? `${fail} av ${cases.length} fall misslyckades` : `Alla ${cases.length} fall godkända`);
process.exit(fail ? 1 : 0);
