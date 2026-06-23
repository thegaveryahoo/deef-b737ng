// B737NG Flashcard Trainer - Service Worker v4.24
// v4.22: 4-thema toggle (donker/blauw/licht/contrast) + swipe beoordeelt niet meer (alleen bladeren)
// v4.23: supercyclus-positie (queue + index) synct nu tussen apparaten
// v4.24: verlies-bestendige positie-sync (verste voortgang wint, geen reset door verse cyclus elders)
// v4.25: prio-kaarten + prio-gate, SIMSESSIES, info-labels, 2 nieuwe kaarten (RA FAIL/EVAC), 29-3 front
// v4.26: supercyclus terug naar origineel algoritme; 2e supercyclus 'Simsessies (prio)' met eigen progressiebalk
// v4.27: prio info-label (sim-sessies + fase) nu ook zichtbaar in NASLAG
// v4.28: 26 prio-kaarten toegevoegd (nu 90); nieuwe sim-sessies incl. sub-sessie #5-2 + 2023-varianten
// v4.29: HTML nu NETWORK-FIRST -> updates direct zichtbaar (geen dubbele refresh meer)
const CACHE = 'b737-trainer-v4.29';
const TOTAL_PAGES = 39;
const CARDS_PER_PAGE = 5;

// Core app-bestanden + CDN-scripts + zoekindex — alle via Promise.allSettled (404 breekt install niet)
const CORE_URLS = [
  './',
  './index.html',
  './manifest.json',
  './flashcards/metadata.json',
  './icons/icon-192.png',
  './icons/icon-bg.webp',
  './tailwind.js',
  'https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js',
];

function getAllImageUrls() {
  const urls = [];
  for (let p = 1; p <= TOTAL_PAGES; p++) {
    for (let c = 1; c <= CARDS_PER_PAGE; c++) {
      const pp = String(p).padStart(2, '0');
      urls.push(`./flashcards/front_${pp}_${c}.png`);
      urls.push(`./flashcards/back_${pp}_${c}.png`);
    }
  }
  return urls;
}

// ── Install: cache core files — Promise.allSettled zodat 404 install niet breekt ──
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(cache =>
      Promise.allSettled(
        CORE_URLS.map(url =>
          fetch(url).then(res => { if (res.ok) cache.put(url, res.clone()); }).catch(() => {})
        )
      )
    )
  );
  self.skipWaiting();
});

// ── Activate: verwijder oude caches, start achtergrond-precache ───────
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
  // Start het cachen van alle afbeeldingen op de achtergrond (blokkeert niks)
  precacheAllImages();
});

async function precacheAllImages() {
  const cache = await caches.open(CACHE);
  const urls  = getAllImageUrls();

  // Sla URLs over die al gecached zijn
  const missing = [];
  for (const url of urls) {
    const hit = await cache.match(url);
    if (!hit) missing.push(url);
  }
  if (missing.length === 0) return;

  // Haal op in batches van 10 zodat de browser niet overbelast raakt
  const BATCH = 10;
  for (let i = 0; i < missing.length; i += BATCH) {
    await Promise.allSettled(
      missing.slice(i, i + BATCH).map(url =>
        fetch(url).then(res => {
          if (res.ok) cache.put(url, res.clone());
        }).catch(() => {})
      )
    );
  }
}

// ── Message: SKIP_WAITING (handmatige update) + REFRESH_IMAGES ────────
self.addEventListener('message', e => {
  if (e.data && e.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
    return;
  }
  if (e.data && e.data.type === 'REFRESH_IMAGES' && Array.isArray(e.data.urls)) {
    caches.open(CACHE).then(cache => {
      e.data.urls.forEach(url => {
        cache.delete(url).then(() => {
          fetch(url).then(res => { if (res.ok) cache.put(url, res.clone()); }).catch(() => {});
        });
      });
    });
  }
});

// ── Fetch: network-first voor HTML, cache-first voor de rest ──────────
// index.html altijd van het netwerk ophalen → updates direct zichtbaar.
// Afbeeldingen, scripts etc.: cache-first voor snelheid + offline.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;

  const url = new URL(e.request.url);

  // Google Apps Script sync-API nooit cachen
  if (url.hostname.includes('script.google.com')) return;

  const isHtml = url.pathname === '/' || url.pathname.endsWith('.html') || url.pathname.endsWith('/');

  if (isHtml) {
    // NETWORK-FIRST voor HTML: altijd de nieuwste versie laden als je online bent, zodat
    // updates DIRECT zichtbaar zijn (geen dubbele refresh meer). Offline → val terug op cache.
    e.respondWith(
      fetch(e.request).then(res => {
        if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
        return res;
      }).catch(() =>
        caches.match(e.request).then(cached =>
          cached || new Response('Offline — open de app eerst met een internetverbinding', { status: 503 })
        )
      )
    );
  } else {
    // Cache-first voor alle andere bestanden (afbeeldingen, scripts, etc.)
    e.respondWith(
      caches.match(e.request).then(cached => {
        if (cached) return cached;
        return fetch(e.request).then(res => {
          if (res.ok) caches.open(CACHE).then(c => c.put(e.request, res.clone()));
          return res;
        }).catch(() => new Response('Offline — geen verbinding', { status: 503 }));
      })
    );
  }
});
