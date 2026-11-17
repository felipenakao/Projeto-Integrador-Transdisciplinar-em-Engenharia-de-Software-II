// Service worker mínimo: guarda CSS/JS/ícone para abrir mais rápido e mostra página offline simples.
// Páginas dinâmicas (pedidos, pagamento) NUNCA são servidas do cache.
const CACHE = "cupcakes-v1";
const ESTATICOS = ["/static/css/estilo.css", "/static/js/app.js", "/static/img/icone.svg"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ESTATICOS)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))));
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (url.pathname.startsWith("/static/")) {
    e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
  } else {
    e.respondWith(fetch(e.request).catch(() => new Response(
      "<h1>Sem conexão</h1><p>Conecte-se à internet para fazer pedidos.</p>",
      { headers: { "Content-Type": "text/html; charset=utf-8" }, status: 503 })));
  }
});
