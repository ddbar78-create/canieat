"""Bygger public/ från src/.

  public/index.html        startsidan (src/landing.html)
  public/app/              appen (src/kan-jag-ata-det.html) med manifest, service worker och ikoner
  public/data/             varudatabas och återkallelser – skrivs av GitHub Actions, rörs inte här

Kör: python3 tools/build.py   (kräver Pillow)
"""
import os, json, shutil
from PIL import Image, ImageDraw

ROOT = "public"
APP = os.path.join(ROOT, "app")
VERSION = "kjad-v12"
os.makedirs(APP, exist_ok=True)

# ---------- Appen ----------
src = open("src/kan-jag-ata-det.html", encoding="utf8").read()
head = '''<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#E7EFE9">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Kan jag äta?">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon-192.png">
<link rel="apple-touch-icon" href="icon-180.png">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}</style>
</head>
<body>
'''
open(f"{APP}/index.html", "w", encoding="utf8").write(head + src + "\n</body>\n</html>\n")

def manifest(start, scope, path):
    json.dump({"name": "Kan jag äta det?", "short_name": "Kan jag äta?", "lang": "sv",
               "start_url": start, "scope": scope, "display": "standalone",
               "background_color": "#E7EFE9", "theme_color": "#E7EFE9",
               "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                         {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
                         {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]},
              open(path, "w", encoding="utf8"), ensure_ascii=False, indent=1)

manifest("./", "./", f"{APP}/manifest.webmanifest")
# Äldre installationer pekar på /manifest.webmanifest – skicka dem till appen
manifest("app/", "./", f"{ROOT}/manifest.webmanifest")

# Service worker:
#  - appens filer: nätverket först, men högst 3,5 s innan sparad version används (dålig täckning i butik)
#  - /data/: sparad version direkt och uppdatering i bakgrunden; cache:"reload" hämtar alltid nytt
#  - /api/: aldrig sparad
SW = '''const C="%s", DATA="kjad-data", FONTS="kjad-fonts";
self.addEventListener("install",e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(%s)));self.skipWaiting()});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C&&k!==DATA&&k!==FONTS).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
const put=(name,req,res)=>{if(res&&res.ok){const cp=res.clone();caches.open(name).then(c=>c.put(req,cp))}return res};
const timeout=(p,ms)=>Promise.race([p,new Promise((_,rej)=>setTimeout(()=>rej(new Error("timeout")),ms))]);
self.addEventListener("fetch",e=>{
  const r=e.request,u=new URL(r.url);
  if(r.method==="GET"&&(u.hostname==="fonts.googleapis.com"||u.hostname==="fonts.gstatic.com")){
    e.respondWith(caches.match(r).then(hit=>hit||fetch(r).then(res=>{if(res&&(res.ok||res.type==="opaque")){const cp=res.clone();caches.open(FONTS).then(c=>c.put(r,cp))}return res})));return}
  if(r.method!=="GET"||u.origin!==location.origin||u.pathname.startsWith("/api/"))return;
  if(u.pathname.startsWith("/data/")){
    const key=u.origin+u.pathname;
    if(r.cache==="reload"){e.respondWith(fetch(key).then(res=>put(DATA,key,res)).catch(()=>caches.match(key)));return}
    e.respondWith(caches.match(key).then(hit=>{const net=fetch(key).then(res=>put(DATA,key,res)).catch(()=>hit);return hit||net}));
    return;
  }
  const net=fetch(r).then(res=>put(C,r,res));
  e.respondWith(timeout(net,3500).catch(()=>caches.match(r,{ignoreSearch:true}).then(hit=>hit||net)));
});
'''
open(f"{APP}/sw.js", "w").write(SW % (VERSION, '["./","./index.html","./manifest.webmanifest","./icon-192.png","./vendor/zxing-0.21.3.min.js","./vendor/qrcode-1.4.4.js"]'))
# Bibliotek för skanning och QR-koder ligger i appen så att de fungerar offline
os.makedirs(f"{APP}/vendor", exist_ok=True)
for f in os.listdir("src/vendor"):
    shutil.copy(f"src/vendor/{f}", f"{APP}/vendor/{f}")
# Service worker på roten finns kvar för äldre installationer (nätverk först)
open(f"{ROOT}/sw.js", "w").write(SW % (VERSION + "-root", '["./"]'))

# ---------- Ikoner: trafikljus på skogsgrönt ----------
def icon(n):
    S = n * 4
    im = Image.new("RGB", (S, S), (44, 58, 52)); d = ImageDraw.Draw(im)
    pad = int(S * .2); d.rounded_rectangle([pad, int(S * .33), S - pad, int(S * .67)], radius=int(S * .17), fill=(231, 239, 233))
    r = int(S * .075); cy = S // 2
    for i, col in enumerate([(178, 58, 46), (209, 138, 0), (46, 122, 79)]):
        cx = int(S * (.33 + .17 * i)); d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    return im.resize((n, n), Image.LANCZOS)
for n in (180, 192, 512):
    im = icon(n); im.save(f"{APP}/icon-{n}.png"); im.save(f"{ROOT}/icon-{n}.png")

# ---------- Startsidan ----------
shutil.copy("src/landing.html", f"{ROOT}/index.html")
shutil.copy("src/feedback-admin.html", f"{ROOT}/feedback-admin.html")
shutil.copy("src/assets/app-resultat.png", f"{ROOT}/app-resultat.png")
print(sorted(os.listdir(ROOT)), sorted(os.listdir(APP)))
