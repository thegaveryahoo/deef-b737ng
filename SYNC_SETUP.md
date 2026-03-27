# B737NG Flashcard Trainer — Sync instellen via Google

Eénmalige setup van ~10 minuten. Daarna synchroniseert de app automatisch
tussen je iPad, Samsung S24 en PC.

---

## Stap 1 — Open Google Apps Script

1. Ga naar **script.google.com** (log in met je Google-account)
2. Klik op **Nieuw project**
3. Geef het een naam: `B737 Flashcard Sync`
4. Verwijder alle bestaande code in het editor-venster

---

## Stap 2 — Kopieer onderstaande code

Plak de volgende code in het editor-venster:

```javascript
// B737NG Flashcard Sync — Google Apps Script
// Versie 1.0 — Bewaar data in Google Drive als JSON-bestand

const FILE_NAME = "b737_sync_data.json";

function getOrCreateFile() {
  const files = DriveApp.getFilesByName(FILE_NAME);
  if (files.hasNext()) return files.next();
  return DriveApp.createFile(FILE_NAME, JSON.stringify({ cards: [] }), MimeType.PLAIN_TEXT);
}

function doGet(e) {
  const content = getOrCreateFile().getBlob().getDataAsString();
  return ContentService.createTextOutput(content)
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    const incoming = JSON.parse(e.postData.contents);
    const file = getOrCreateFile();

    let stored;
    try { stored = JSON.parse(file.getBlob().getDataAsString()); }
    catch(err) { stored = { cards: [] }; }

    const storedMap = {};
    (stored.cards || []).forEach(c => { storedMap[c.id] = c; });

    // Smart merge: bewaar de versie met de meest recente lastReviewed
    (incoming.cards || []).forEach(c => {
      if (!storedMap[c.id]) {
        storedMap[c.id] = c;
      } else {
        const st = storedMap[c.id].lastReviewed ? new Date(storedMap[c.id].lastReviewed).getTime() : 0;
        const it = c.lastReviewed ? new Date(c.lastReviewed).getTime() : 0;
        if (it > st) storedMap[c.id] = c;
      }
    });

    const result = {
      version: incoming.version || "3.0",
      syncedAt: new Date().toISOString(),
      cards: Object.values(storedMap)
    };

    file.setContent(JSON.stringify(result));

    return ContentService.createTextOutput(
      JSON.stringify({ status: "ok", cards: result.cards.length })
    ).setMimeType(ContentService.MimeType.JSON);

  } catch(err) {
    return ContentService.createTextOutput(
      JSON.stringify({ status: "error", message: err.toString() })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}
```

---

## Stap 3 — Deploy als Web App

1. Klik op **Deploy** (rechtsboven) → **Nieuwe implementatie**
2. Klik op het tandwiel naast "Type" → kies **Web-app**
3. Vul in:
   - **Beschrijving**: `B737 Sync v1`
   - **Uitvoeren als**: `Ik` (jouw Google-account)
   - **Wie heeft toegang**: `Iedereen`
4. Klik **Implementeren**
5. Geef toestemming als daarom gevraagd wordt (klik "Toestaan")
6. **Kopieer de Web-app URL** — ziet eruit als:
   `https://script.google.com/macros/s/AKfy.../exec`

---

## Stap 4 — Plak de URL in de app

1. Open de B737NG Flashcard Trainer
2. Tik op **Instellen** in de sync-balk onderaan het dashboard
3. Plak de gekopieerde URL in het veld
4. Tik **Verbinding testen** — je ziet: ✅ Verbinding geslaagd!
5. Tik **Opslaan**

De app synchroniseert nu automatisch elke keer dat je een kaart beoordeelt
en elke keer dat je terugkeert naar het dashboard.

---

## Stap 5 — Instellen op andere apparaten

Herhaal Stap 4 op je iPad en Samsung — gebruik dezelfde Apps Script URL.
De studieresultaten worden automatisch samengevoegd (per kaart wint de
meest recente beoordeling).

---

## Hoe werkt de sync?

- **Automatisch**: na elke beoordeling wordt de data naar Google gestuurd
- **Smart merge**: per kaart wordt de meest recente beoordeling bewaard
- **Offline**: de app werkt volledig offline; zodra je weer online bent,
  synchroniseert alles automatisch
- **Nieuwe kaarten**: handmatig toegevoegde kaarten worden ook gesynchroniseerd
- **Privacy**: de data staat alleen in jouw Google Drive (`b737_sync_data.json`)

---

## Problemen?

**"Redirect" of authenticatie-fout**
→ Zorg dat "Wie heeft toegang" ingesteld is op **Iedereen** (niet "Iedereen met account")

**Sync mislukt na app-update**
→ Maak een nieuwe implementatie aan (Deploy → Nieuwe implementatie) en update de URL

**Data kwijt na SUPERRESET**
→ De data op de server blijft bewaard. Na de volgende sync worden de tellers
  teruggehaald (van de server). Wil je ook de server resetten? Verwijder dan
  `b737_sync_data.json` uit je Google Drive.
