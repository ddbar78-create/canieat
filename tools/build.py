import os, json, shutil
from PIL import Image, ImageDraw
src=open("src/kan-jag-ata-det.html",encoding="utf8").read()
out="public"
os.makedirs(out,exist_ok=True)  # rör inte public/data, den skrivs av GitHub Actions
head='''<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#1F1C44">
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
open(f"{out}/index.html","w",encoding="utf8").write(head+src+"\n</body>\n</html>\n")
json.dump({"name":"Kan jag äta det?","short_name":"Kan jag äta?","lang":"sv","start_url":"./","scope":"./","display":"standalone",
  "background_color":"#1F1C44","theme_color":"#1F1C44",
  "icons":[{"src":"icon-192.png","sizes":"192x192","type":"image/png"},{"src":"icon-512.png","sizes":"512x512","type":"image/png"},{"src":"icon-512.png","sizes":"512x512","type":"image/png","purpose":"maskable"}]},
  open(f"{out}/manifest.webmanifest","w",encoding="utf8"),ensure_ascii=False,indent=1)
open(f"{out}/sw.js","w").write('''const C="kjad-v9";
self.addEventListener("install",e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(["./","./index.html","./manifest.webmanifest","./icon-192.png"])));self.skipWaiting()});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{const u=new URL(e.request.url);if(e.request.method!=="GET"||u.origin!==location.origin)return;
 e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(C).then(c=>c.put(e.request,cp));return r}).catch(()=>caches.match(e.request)))});
''')
def icon(n):
    S=n*4; im=Image.new("RGB",(S,S),(48,70,166)); d=ImageDraw.Draw(im)
    pad=int(S*.2); d.rounded_rectangle([pad,int(S*.33),S-pad,int(S*.67)],radius=int(S*.17),fill=(255,255,255))
    r=int(S*.075); cy=S//2
    for i,col in enumerate([(188,47,38),(230,150,20),(29,119,69)]):
        cx=int(S*(.33+.17*i)); d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=col)
    return im.resize((n,n),Image.LANCZOS)
for n in (180,192,512): icon(n).save(f"{out}/icon-{n}.png")
print(os.listdir(out))
