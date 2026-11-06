# Receptbanken skrivs här och sparas som src/recipes.json.
# Rad: t = text, a = allergener raden innehåller, kolla = kan innehålla (läs förpackningen),
#      byt = alternativ [{t, a}] i turordning; {"t": "...", "utan": True} betyder hoppa över.
import json, sys

def L(t, a=(), kolla=(), byt=()):
    d = {"t": t}
    if a: d["a"] = list(a)
    if kolla: d["kolla"] = list(kolla)
    if byt: d["byt"] = [x if isinstance(x, dict) else {"t": x[0], "a": list(x[1])} for x in byt]
    return d
U = lambda t: {"t": t, "utan": True}
MJOLK = [("havredryck", ["gluten"]), ("sojadryck", ["soja"]), ("risdryck", [])]
GRADDE = [("havregrädde", ["gluten"]), ("sojagrädde", ["soja"]), ("kokosgrädde", ["kokos"])]
SMOR = [("mjölkfritt margarin", []), ("rapsolja", [])]
CREME = [("havrefraiche", ["gluten"]), ("sojafraiche", ["soja"])]
def m(q): return [(f"{q} {x}", a) for x, a in MJOLK]
def g(q): return [(f"{q} {x}", a) for x, a in GRADDE]
def s(q): return [(f"{q} {x}", a) for x, a in SMOR]
def c(q): return [(f"{q} {x}", a) for x, a in CREME]
BULJONG = ("selleri", "gluten")

R = [
 dict(id="kottbullar", namn="Köttbullar med potatismos", kat="middag", tid=45, port=4, ingr=[
   L("500 g nötfärs"),
   L("1 dl ströbröd", ["gluten"], byt=[("1 dl glutenfritt ströbröd", []), ("1 dl majsmjöl", ["majs"])]),
   L("1,5 dl mjölk", ["mjolk", "laktos"], byt=m("1,5 dl")),
   L("1 ägg", ["agg"], byt=[("1 msk potatismjöl rört i 3 msk vatten", [])]),
   L("1 gul lök, finhackad"), L("1 tsk salt och lite svartpeppar"),
   L("smör till stekning", ["mjolk"], byt=[("rapsolja till stekning", [])]),
   L("1 kg mjölig potatis"),
   L("2 dl mjölk till moset", ["mjolk", "laktos"], byt=m("2 dl")),
   L("2 msk smör till moset", ["mjolk"], byt=s("2 msk")),
   L("lingonsylt"),
 ], steg=["Blanda ströbröd och mjölk och låt svälla i 5 minuter.",
          "Blanda i färs, ägg, lök, salt och peppar. Rulla små bullar.",
          "Stek bullarna i flera omgångar tills de är genomstekta.",
          "Koka potatisen mjuk, häll av och mosa med mjölk och smör. Smaka av med salt.",
          "Servera med lingonsylt."]),
 dict(id="kottfarssas", namn="Spaghetti med köttfärssås", kat="middag", tid=40, port=4, ingr=[
   L("500 g nötfärs"), L("1 gul lök"), L("2 vitlöksklyftor"), L("1 morot, riven"),
   L("1 stjälk blekselleri", ["selleri"], byt=[U("Hoppa över blekselleri")]),
   L("2 burkar krossade tomater"), L("2 msk tomatpuré"),
   L("1 tärning köttbuljong", kolla=BULJONG),
   L("1 tsk torkad oregano"), L("400 g spaghetti av durumvete", ["gluten"], byt=[("400 g glutenfri spaghetti", []), ("400 g risnudlar", [])]),
   L("riven parmesan", ["mjolk"], byt=[U("Hoppa över osten")]),
 ], steg=["Fräs lök, vitlök, morot och selleri i lite olja.",
          "Bryn färsen i samma panna.",
          "Tillsätt tomater, tomatpuré, buljong och oregano. Låt puttra i 20 minuter.",
          "Koka spaghettin enligt förpackningen.",
          "Servera med riven ost."]),
 dict(id="lasagne", namn="Lasagne", kat="middag", tid=75, port=6, ingr=[
   L("500 g nötfärs"), L("1 gul lök"), L("2 burkar krossade tomater"), L("1 tärning köttbuljong", kolla=BULJONG),
   L("12 lasagneplattor", ["gluten"], kolla=["agg"], byt=[("12 glutenfria lasagneplattor", []), ("2 zucchini i tunna skivor", [])]),
   L("3 msk smör", ["mjolk"], byt=s("3 msk")),
   L("3 msk vetemjöl", ["gluten"], byt=[("2 msk majsstärkelse", ["majs"]), ("2 msk potatismjöl", [])]),
   L("6 dl mjölk", ["mjolk", "laktos"], byt=m("6 dl")),
   L("2 dl riven ost", ["mjolk"], byt=[("2 dl mjölkfri riven ost", []), U("Hoppa över osten")]),
 ], steg=["Gör en köttfärssås av färs, lök, tomater och buljong. Låt puttra i 15 minuter.",
          "Smält smöret, vispa i mjölet och späd med mjölken under omrörning. Låt sjuda till en tjock sås.",
          "Varva sås, plattor och vit sås i en ugnsform. Toppa med ost.",
          "Grädda i 225 °C i cirka 35 minuter."]),
 dict(id="kycklingcurry", namn="Kycklinggryta med curry och ris", kat="middag", tid=30, port=4, ingr=[
   L("600 g kycklingfilé"), L("1 gul lök"), L("1 röd paprika"),
   L("1 msk currypulver", kolla=["senap", "selleri"]),
   L("4 dl kokosmjölk", ["kokos"], byt=g("4 dl")),
   L("1 dl vatten"), L("1 tärning hönsbuljong", kolla=BULJONG),
   L("3 dl jasminris"), L("färsk koriander"),
 ], steg=["Skär kycklingen i bitar och bryn den i lite olja.",
          "Tillsätt lök, paprika och curry och fräs en minut.",
          "Häll på kokosmjölk, vatten och buljong. Låt puttra i 15 minuter.",
          "Koka riset och servera med koriander."]),
 dict(id="tacos", namn="Tacos", kat="middag", tid=30, port=4, ingr=[
   L("500 g nötfärs"), L("1 påse tacokrydda", kolla=["gluten", "selleri"]),
   L("8 tortillabröd av vete", ["gluten"], byt=[("8 majstortillas", ["majs"]), ("salladsblad att rulla in i", [])]),
   L("1 dl riven ost", ["mjolk"], byt=[U("Hoppa över osten")]),
   L("2 dl gräddfil", ["mjolk", "laktos"], byt=c("2 dl") + [U("Hoppa över gräddfilen")]),
   L("1 burk majs", ["majs"], byt=[U("Hoppa över majsen")]),
   L("tomat, gurka, isbergssallad"), L("tacosås", kolla=["selleri"]),
 ], steg=["Bryn färsen och tillsätt tacokrydda och vatten enligt påsen.",
          "Skär grönsakerna.",
          "Värm bröden och låt alla bygga sina tacos."]),
 dict(id="ugnslax", namn="Lax i ugn med potatis och dillsås", kat="middag", tid=35, port=4, ingr=[
   L("600 g laxfilé", ["fisk"]), L("1 citron"), L("salt och peppar"),
   L("800 g fast potatis"),
   L("2 dl crème fraiche", ["mjolk", "laktos"], byt=c("2 dl")),
   L("1 dl hackad dill"),
 ], steg=["Lägg laxen i en ugnsform, salta och pressa över citron.",
          "Grädda i 175 °C i cirka 20 minuter.",
          "Koka potatisen.",
          "Rör ihop crème fraiche och dill till en kall sås."]),
 dict(id="stroganoff", namn="Korv Stroganoff", kat="middag", tid=25, port=4, ingr=[
   L("600 g falukorv", kolla=["mjolk", "soja", "senap"]),
   L("1 gul lök"), L("2 msk tomatpuré"),
   L("1 msk senap", ["senap"], byt=[U("Hoppa över senapen")]),
   L("2 dl matlagningsgrädde", ["mjolk", "laktos"], byt=g("2 dl")),
   L("3 dl ris"),
 ], steg=["Skär korven i strimlor och bryn den med löken.",
          "Rör ner tomatpuré och senap.",
          "Häll på grädden och låt sjuda i 5 minuter.",
          "Servera med ris."]),
 dict(id="pyttipanna", namn="Pyttipanna med stekt ägg", kat="middag", tid=30, port=4, ingr=[
   L("800 g kokt potatis"), L("400 g kokt eller stekt kött, eller korv"), L("2 gula lökar"),
   L("2 msk smör", ["mjolk"], byt=[("2 msk rapsolja", [])]),
   L("4 ägg", ["agg"], byt=[U("Hoppa över äggen")]),
   L("inlagda rödbetor"),
 ], steg=["Tärna potatis, kött och lök.",
          "Stek allt gyllene i smöret, i omgångar.",
          "Stek äggen och lägg ovanpå.",
          "Servera med rödbetor."]),
 dict(id="kycklingwok", namn="Kycklingwok med nudlar", kat="middag", tid=25, port=4, ingr=[
   L("500 g kycklingfilé"), L("1 påse wokgrönsaker"),
   L("250 g äggnudlar", ["gluten", "agg"], byt=[("250 g risnudlar", [])]),
   L("3 msk kinesisk soja", ["soja", "gluten"], byt=[("3 msk tamari", ["soja"]), ("3 msk kokosaminos", ["kokos"])]),
   L("1 msk sesamolja", ["sesam"], byt=[("1 msk rapsolja", [])]),
   L("1 msk riven ingefära"), L("2 vitlöksklyftor"),
   L("1 dl cashewnötter", ["notter"], byt=[("1 dl rostade solroskärnor", []), U("Hoppa över nötterna")]),
 ], steg=["Koka nudlarna och spola dem i kallt vatten.",
          "Woka kycklingen het, ta upp den.",
          "Woka grönsaker, ingefära och vitlök.",
          "Vänd ner kyckling, nudlar, soja och olja. Toppa med nötter."]),
 dict(id="linsgryta", namn="Linsgryta med kokos", kat="middag", tid=35, port=4, ingr=[
   L("3 dl röda linser", ["linser"], byt=[("2 burkar kikärtor", ["kikartor"])]),
   L("1 gul lök"), L("2 vitlöksklyftor"), L("1 msk riven ingefära"),
   L("1 msk currypulver", kolla=["senap", "selleri"]),
   L("1 burk krossade tomater"),
   L("4 dl kokosmjölk", ["kokos"], byt=g("4 dl")),
   L("3 dl vatten"), L("1 tärning grönsaksbuljong", kolla=BULJONG), L("bladspenat"),
 ], steg=["Fräs lök, vitlök, ingefära och curry.",
          "Tillsätt linser, tomater, kokosmjölk, vatten och buljong.",
          "Låt koka i cirka 20 minuter tills linserna är mjuka.",
          "Rör ner spenaten och servera med ris eller bröd."]),
 dict(id="artsoppa", namn="Ärtsoppa", kat="middag", tid=120, port=4, ingr=[
   L("500 g torkade gula ärtor", ["artor"]),
   L("2 liter vatten"), L("1 gul lök"), L("500 g rimmat fläsk"), L("1 tsk timjan"), L("1 tsk mejram"),
   L("senap till servering", ["senap"], byt=[U("Hoppa över senapen")]),
 ], steg=["Blötlägg ärtorna över natten och häll av vattnet.",
          "Koka ärtorna i nytt vatten med lök, fläsk och kryddor i cirka 1,5 timme.",
          "Ta upp fläsket, skär det i bitar och lägg tillbaka.",
          "Servera med senap."]),
 dict(id="purjosoppa", namn="Potatis- och purjolökssoppa", kat="middag", tid=30, port=4, ingr=[
   L("800 g potatis"), L("2 purjolökar"),
   L("2 msk smör", ["mjolk"], byt=[("2 msk rapsolja", [])]),
   L("1 liter vatten"), L("2 tärningar grönsaksbuljong", kolla=BULJONG),
   L("2 dl matlagningsgrädde", ["mjolk", "laktos"], byt=g("2 dl")),
 ], steg=["Fräs purjolöken mjuk i smöret.",
          "Tillsätt potatis i bitar, vatten och buljong. Koka i 15 minuter.",
          "Mixa soppan slät och rör ner grädden.",
          "Smaka av med salt och peppar."]),
 dict(id="fiskgratang", namn="Fiskgratäng med räkor", kat="middag", tid=50, port=4, ingr=[
   L("600 g torskfilé", ["fisk"]),
   L("150 g skalade räkor", ["krafdjur"], byt=[U("Hoppa över räkorna")]),
   L("1 kg potatis"),
   L("2 dl mjölk", ["mjolk", "laktos"], byt=m("2 dl")),
   L("2 msk smör", ["mjolk"], byt=s("2 msk")),
   L("2 dl crème fraiche", ["mjolk", "laktos"], byt=c("2 dl")),
   L("1 dl riven ost", ["mjolk"], byt=[U("Hoppa över osten")]),
   L("1 citron"), L("dill"),
 ], steg=["Koka potatisen och mosa den med mjölk och smör.",
          "Lägg fisken i en ugnsform och strö över räkorna.",
          "Rör ihop crème fraiche, dill och citron och bred över fisken.",
          "Spritsa eller klicka moset runt kanten, strö över ost och grädda i 200 °C i 25 minuter."]),
 dict(id="ugnskyckling", namn="Kyckling med ugnsrostade rotfrukter", kat="middag", tid=50, port=4, ingr=[
   L("8 kycklingklubbor"), L("4 morötter"), L("2 rödbetor"), L("600 g potatis"),
   L("3 msk olivolja"), L("1 citron"), L("färsk timjan"), L("salt och peppar"),
 ], steg=["Skär rotfrukterna i bitar och lägg dem i en långpanna.",
          "Lägg kycklingen ovanpå och ringla över olja och citronsaft. Krydda.",
          "Rosta i 200 °C i cirka 40 minuter tills kycklingen är genomstekt."]),
 dict(id="chili", namn="Chili med bönor och linser", kat="middag", tid=40, port=4, ingr=[
   L("1 gul lök"), L("2 vitlöksklyftor"), L("1 röd paprika"),
   L("2 burkar kidneybönor"),
   L("1 dl röda linser", ["linser"], byt=[("1 burk svarta bönor", [])]),
   L("2 burkar krossade tomater"), L("1 msk chilipulver"), L("1 tsk spiskummin"), L("1 msk kakao"),
   L("1 dl gräddfil till servering", ["mjolk", "laktos"], byt=c("1 dl") + [U("Hoppa över gräddfilen")]),
 ], steg=["Fräs lök, vitlök och paprika.",
          "Tillsätt kryddor, kakao, linser, bönor och tomater.",
          "Låt puttra i 25 minuter.",
          "Servera med gräddfil och ris."]),
 dict(id="risotto", namn="Svamprisotto", kat="middag", tid=40, port=4, ingr=[
   L("3 dl arborioris"), L("250 g champinjoner"), L("1 schalottenlök"),
   L("1 dl torrt vitt vin", ["sulfit"], byt=[("1 dl buljong extra och 1 msk citronsaft", [])]),
   L("1 liter grönsaksbuljong", kolla=BULJONG),
   L("2 msk smör", ["mjolk"], byt=[("2 msk olivolja", [])]),
   L("1 dl riven parmesan", ["mjolk"], byt=[("2 msk näringsjäst", []), U("Hoppa över osten")]),
 ], steg=["Fräs lök och svamp i hälften av smöret.",
          "Tillsätt riset och fräs tills det blir blankt. Häll på vinet.",
          "Tillsätt varm buljong lite i taget under omrörning, cirka 20 minuter.",
          "Rör ner resten av smöret och osten."]),
 dict(id="havregrot", namn="Havregrynsgröt", kat="frukost", tid=5, port=1, ingr=[
   L("1 dl havregryn", ["gluten"], byt=[("1 dl glutenfria havregryn", []), ("1 dl hirsflingor", [])]),
   L("2 dl vatten"), L("en nypa salt"),
   L("mjölk till servering", ["mjolk", "laktos"], byt=[("havredryck till servering", ["gluten"]), ("sojadryck till servering", ["soja"]), ("risdryck till servering", [])]),
   L("bär eller äppelmos"),
 ], steg=["Koka upp gryn, vatten och salt.", "Låt sjuda i 3 minuter under omrörning.", "Servera med mjölk och bär."]),
 dict(id="omelett", namn="Omelett", kat="frukost", tid=10, port=1, ingr=[
   L("3 ägg", ["agg"], byt=[("1 dl kikärtsmjöl rört med 1,5 dl vatten", ["kikartor"])]),
   L("2 msk mjölk", ["mjolk", "laktos"], byt=[("2 msk vatten", [])]),
   L("smör till stekning", ["mjolk"], byt=[("rapsolja till stekning", [])]),
   L("skinka, tomat eller spenat"), L("salt och peppar"),
 ], steg=["Vispa ägg och mjölk lätt och krydda.", "Häll i en het panna med smör.", "Lägg på fyllningen och vik ihop när ytan stelnat."]),
 dict(id="smoothie", namn="Bärsmoothie", kat="frukost", tid=5, port=2, ingr=[
   L("2 dl frysta blåbär eller hallon"), L("1 banan"),
   L("2 dl naturell yoghurt", ["mjolk", "laktos"], byt=[("2 dl havreyoghurt", ["gluten"]), ("2 dl sojayoghurt", ["soja"]), ("2 dl kokosyoghurt", ["kokos"])]),
   L("1 dl vatten"),
 ], steg=["Mixa allt slätt.", "Späd med mer vatten om den är för tjock."]),
 dict(id="chiapudding", namn="Chiapudding", kat="frukost", tid=5, port=2, ingr=[
   L("4 msk chiafrön"),
   L("3 dl havredryck", ["gluten"], byt=[("3 dl risdryck", []), ("3 dl kokosdryck", ["kokos"])]),
   L("1 tsk honung"), L("färska bär"),
 ], steg=["Rör ihop chiafrön, dryck och honung.", "Låt stå i kylen minst 2 timmar eller över natten.", "Toppa med bär."]),
 dict(id="pannkakor", namn="Pannkakor", kat="fika", tid=30, port=4, ingr=[
   L("2,5 dl vetemjöl", ["gluten"], byt=[("2,5 dl glutenfri mjölmix", [])]),
   L("6 dl mjölk", ["mjolk", "laktos"], byt=m("6 dl")),
   L("3 ägg", ["agg"], byt=[("3 msk potatismjöl och 1 dl extra dryck", [])]),
   L("en nypa salt"),
   L("2 msk smält smör", ["mjolk"], byt=[("2 msk rapsolja", [])]),
   L("sylt"),
 ], steg=["Vispa mjölet med hälften av mjölken till en slät smet.", "Vispa i resten av mjölken, äggen, salt och smör.", "Grädda tunna pannkakor i en het panna.", "Servera med sylt."]),
 dict(id="kladdkaka", namn="Kladdkaka", kat="fika", tid=35, port=8, ingr=[
   L("100 g smör", ["mjolk"], byt=s("100 g")),
   L("2 ägg", ["agg"], byt=[("1 dl äppelmos", [])]),
   L("2,5 dl socker"), L("4 msk kakao"), L("1 tsk vaniljsocker"),
   L("1,5 dl vetemjöl", ["gluten"], byt=[("1,5 dl glutenfri mjölmix", []), ("1 dl mandelmjöl", ["notter"])]),
 ], steg=["Smält smöret.", "Rör ner övriga ingredienser.", "Häll i en smord form och grädda i 175 °C i cirka 20 minuter. Kakan ska vara kladdig i mitten."]),
 dict(id="bananbrod", namn="Bananbröd", kat="fika", tid=70, port=10, ingr=[
   L("3 mogna bananer"),
   L("2 ägg", ["agg"], byt=[("2 msk chiafrön rörda i 6 msk vatten", [])]),
   L("1 dl socker"),
   L("75 g smält smör", ["mjolk"], byt=[("0,75 dl rapsolja", [])]),
   L("3 dl vetemjöl", ["gluten"], byt=[("3 dl glutenfri mjölmix", [])]),
   L("2 tsk bakpulver"), L("1 tsk kanel"),
   L("1 dl hackade valnötter", ["notter"], byt=[U("Hoppa över nötterna")]),
 ], steg=["Mosa bananerna och rör ner ägg, socker och smör.", "Blanda i torra ingredienser och nötter.", "Häll i en smord avlång form och grädda i 175 °C i cirka 50 minuter."]),
 dict(id="chokladbollar", namn="Chokladbollar", kat="fika", tid=20, port=20, ingr=[
   L("100 g smör, rumsvarmt", ["mjolk"], byt=s("100 g")),
   L("1 dl socker"), L("1 tsk vaniljsocker"), L("3 msk kakao"),
   L("3 dl havregryn", ["gluten"], byt=[("3 dl glutenfria havregryn", [])]),
   L("2 msk kallt kaffe"),
   L("kokosflingor att rulla i", ["kokos"], byt=[("pärlsocker att rulla i", [])]),
 ], steg=["Blanda allt utom kokosen till en jämn smet.", "Rulla bollar och rulla dem i kokos.", "Låt stå kallt en stund."]),
 dict(id="smulpaj", namn="Äppelsmulpaj", kat="fika", tid=40, port=6, ingr=[
   L("5 äpplen"), L("1 tsk kanel"),
   L("100 g smör", ["mjolk"], byt=s("100 g")),
   L("1 dl vetemjöl", ["gluten"], byt=[("1 dl glutenfri mjölmix", [])]),
   L("1 dl havregryn", ["gluten"], byt=[("1 dl glutenfria havregryn", [])]),
   L("1 dl socker"),
   L("vaniljsås eller glass", ["mjolk", "laktos"], kolla=["agg"], byt=[("havrebaserad vaniljsås", ["gluten"]), ("sojabaserad vaniljsås", ["soja"])]),
 ], steg=["Skiva äpplena i en ugnsform och strö över kanel.", "Nyp ihop smör, mjöl, havregryn och socker till en smulig deg.", "Strö över äpplena och grädda i 200 °C i cirka 25 minuter."]),
 dict(id="hummus", namn="Hummus med grönsaksstavar", kat="mellanmal", tid=10, port=4, ingr=[
   L("1 burk kikärtor", ["kikartor"], byt=[("1 burk vita bönor", [])]),
   L("2 msk tahini", ["sesam"], byt=[("2 msk olivolja extra", [])]),
   L("1 vitlöksklyfta"), L("1 citron"), L("3 msk olivolja"), L("salt och spiskummin"),
   L("morötter, gurka och paprika i stavar"),
 ], steg=["Häll av kikärtorna men spara lite spad.", "Mixa allt slätt och späd med spadet.", "Servera med grönsaksstavar."]),
 dict(id="guacamole", namn="Guacamole", kat="mellanmal", tid=10, port=4, ingr=[
   L("2 mogna avokador"), L("1 lime"), L("0,5 rödlök"), L("1 tomat"), L("färsk koriander"), L("salt"),
   L("majschips", ["majs"], byt=[("grönsaksstavar", [])]),
 ], steg=["Mosa avokadon med limesaft.", "Rör ner finhackad lök, tomat och koriander.", "Smaka av med salt."]),
 dict(id="potatissallad", namn="Potatissallad", kat="mellanmal", tid=30, port=4, ingr=[
   L("800 g fast potatis"),
   L("1 dl majonnäs", ["agg"], kolla=["senap"], byt=[("1 dl äggfri majonnäs", [])]),
   L("1 dl crème fraiche", ["mjolk", "laktos"], byt=c("1 dl")),
   L("1 rödlök"), L("gräslök"), L("salt och peppar"),
 ], steg=["Koka potatisen, låt svalna och skär i bitar.", "Rör ihop majonnäs, crème fraiche, lök och gräslök.", "Vänd ner potatisen och smaka av."]),
 dict(id="quinoasallad", namn="Quinoasallad med feta", kat="mellanmal", tid=25, port=4, ingr=[
   L("2 dl quinoa"), L("1 gurka"), L("200 g körsbärstomater"), L("1 rödlök"),
   L("150 g fetaost", ["mjolk"], byt=[U("Hoppa över fetaosten")]),
   L("2 msk pumpakärnor"), L("1 citron"), L("3 msk olivolja"),
 ], steg=["Koka quinoan och låt svalna.", "Hacka grönsakerna.", "Blanda allt och smaka av med citron, olja och salt."]),
]
out = sys.argv[1]
json.dump({"v": 1, "recipes": R}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(R), "recept,", sum(len(r["ingr"]) for r in R), "rader")
