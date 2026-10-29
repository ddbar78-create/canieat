const C="kjad-v11", DATA="kjad-data";
self.addEventListener("install",e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(["./","./index.html","./manifest.webmanifest","./icon-192.png","./vendor/zxing-0.21.3.min.js","./vendor/qrcode-1.4.4.js"])));self.skipWaiting()});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C&&k!==DATA).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
const put=(name,req,res)=>{if(res&&res.ok){const cp=res.clone();caches.open(name).then(c=>c.put(req,cp))}return res};
const timeout=(p,ms)=>Promise.race([p,new Promise((_,rej)=>setTimeout(()=>rej(new Error("timeout")),ms))]);
self.addEventListener("fetch",e=>{
  const r=e.request,u=new URL(r.url);
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
