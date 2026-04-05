// B737NG Flashcard Trainer - Service Worker v4.15
// v4.15: streak sync, keywords merge, debug logs verwijderd
const CACHE = 'b737-trainer-v4.15';
const TOTAL_PAGES = 38;
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
    // Race: netwerk (max 3s) vs cache — bij slecht bereik wint de cache direct
    e.respondWith(
      Promise.race([
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('timeout')), 3000)
        ),
        fetch(e.request).then(res => {
          if (res.ok) caches.open(CACHE).then(c => c.put(e.request, res.clone()));
          return res;
        })
      ]).catch(() =>
        caches.match(e.request).then(cached =>
          cached || new Response('Offline — geen verbinding', { status: 503 })
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
