// Regressionstest för allergenmatchningen. Kör: node tests/analyze.test.js
const fs = require("fs");
const html = fs.readFileSync(__dirname + "/../src/kan-jag-ata-det.html", "utf8");
const src = html.split("<script>")[1].split("/* ---------- Extra säkerhetskontroller")[0];
const makeAnalyze = prof => new Function(src.replace(/let profile = [^\n]+/, "let profile=" + JSON.stringify(prof) + ";")
       .replace(/let history[^\n]+/, "")
       .replace("const store = {", "const localStorage={getItem(){return null},setItem(){}};const store = {") + "; return analyze;")();
const analyze = makeAnalyze({levels:{mjolk:"allergi",gluten:"allergi",agg:"allergi",notter:"allergi",fisk:"allergi",jordnot:"allergi",kokos:"allergi"},custom:[]});

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
  ["Nötfärs, lök, salt, peppar och nötbuljong.", "", "sv", [], ["Nötter"]],
  ["Havregrädde, kokosgrädde, sojayoghurt och vatten.", "", "sv", ["Kokos"], ["Mjölk"]],
  ["Gräddfil, gurka, vitlök och salt.", "", "sv", ["Mjölk"], []],
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
// Sorter: bara cashew och pistage bland nötterna, bara räkor bland kräftdjuren
const sortAnalyze = makeAnalyze({levels:{notter:"allergi",krafdjur:"allergi"},types:{notter:["cashew","pistage"],krafdjur:["rakor"]},custom:[]});
const sortCases = [
  // [text, förväntat besked, beskrivning]
  ["Socker, hasselnötter, kakao.", "green", "hasselnöt när bara cashew och pistage är valda"],
  ["Ris, cashewnötter, salt.", "red", "cashew"],
  ["Choklad med pistage och mandel.", "red", "pistage bland andra nötter"],
  ["Socker, nötter, kakao.", "amber", "bara 'nötter' utan sort"],
  ["Socker, nötter (hasselnöt), kakao.", "green", "nötter med sorten utskriven"],
  ["Socker, kakao. Kan innehålla spår av nötter.", "amber", "spår av nötter utan sort"],
  ["Socker, kakao. Kan innehålla spår av mandel.", "green", "spår av en annan sort"],
  ["Pasta med krabba och hummer.", "green", "kräftdjur som inte är räkor"],
  ["Räksallad med majonnäs.", "red", "räkor"],
  ["Shrimp, rice, soy sauce.", "red", "räkor på engelska"],
  ["Marsipan, socker.", "green", "marsipan räknas som mandel"],
];
// Gluten: bara vete (veteallergi), och bara havre
const wheat = makeAnalyze({levels:{gluten:"allergi"},types:{gluten:["vete"]},custom:[]});
const oats = makeAnalyze({levels:{gluten:"allergi"},types:{gluten:["havre"]},custom:[]});
const celiac = makeAnalyze({levels:{gluten:"allergi"},custom:[]});
for (const c of [
  [wheat, "Rågmjöl, vatten, salt.", "green", "råg vid veteallergi"],
  [wheat, "Vetemjöl, vatten, salt.", "red", "vete vid veteallergi"],
  [wheat, "Dinkelmjöl, honung.", "red", "dinkel är vete"],
  [wheat, "Havregryn, russin.", "amber", "havre kan vara förorenad med vete"],
  [wheat, "Socker, gluten, salt.", "amber", "bara 'gluten' utan sädesslag"],
  [wheat, "Rye flour, water, salt.", "green", "råg på engelska"],
  [oats, "Havregryn, russin.", "red", "havre vid havreallergi"],
  [oats, "Glutenfri havre, russin.", "red", "glutenfri havre är ändå havre"],
  [oats, "Vetemjöl, vatten.", "green", "vete vid bara havreallergi"],
  [celiac, "Havregryn, russin.", "amber", "celiaki: havre som förut"],
  [celiac, "Rågmjöl, vatten.", "red", "celiaki: råg som förut"],
]) sortCases.push([c[1], c[2], c[3], c[0]]);
let sfail = 0;
for (const [text, want, what, fn] of sortCases) {
  const r = (fn || sortAnalyze)(text, "");
  if (r.status !== want) { sfail++; console.log("FEL sort:", what, "→", r.status, "väntade", want); }
}
fail += sfail;
console.log(sfail ? `${sfail} sortfall misslyckades` : `Alla ${sortCases.length} sortfall godkända`);
console.log(fail ? `${fail} av ${cases.length} fall misslyckades` : `Alla ${cases.length} fall godkända`);
process.exit(fail ? 1 : 0);
