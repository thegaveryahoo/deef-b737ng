#!/usr/bin/env python3
"""
B737NG-800 Flashcard Trainer - PDF Splitter + App Generator
Gebruik: python maak_app.py [pdf_bestand]
Vereisten: pip install pymupdf pillow
"""
import sys, os, json, base64, re
from pathlib import Path

try:
    import fitz  # pymupdf
    from PIL import Image
    import io
except ImportError:
    print("Installeer eerst: pip install pymupdf pillow")
    sys.exit(1)

PDF_FILE = sys.argv[1] if len(sys.argv) > 1 else "flashcardsv2.0.pdf"
OUT_DIR = Path("flashcards")
APP_FILE = "flashcard_trainer.html"
CARDS_PER_PAGE = 5
DPI = 150

def split_pdf_to_cards(pdf_path):
    """Splits elke pagina in 5 voor+achterzijdes en extraheert tekst voor zoekindex."""
    OUT_DIR.mkdir(exist_ok=True)
    doc = fitz.open(pdf_path)
    cards = []
    metadata = {}  # card_id -> {"f": [...], "b": [...]}

    print(f"PDF heeft {len(doc)} pagina's, verwacht {len(doc) * CARDS_PER_PAGE} flashcards")

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_idx = page_num + 1  # 1-based

        # Render pagina op hoge resolutie
        mat = fitz.Matrix(DPI/72, DPI/72)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        w, h = img.size
        split_x = find_split(img)  # detecteer exacte splitslijn
        card_height = h // CARDS_PER_PAGE

        # Schaal: pixel → PDF-punten
        scale = 72.0 / DPI
        split_x_pdf = split_x * scale

        # Haal alle tekst-blokken van de pagina op
        text_blocks = page.get_text("blocks")  # (x0,y0,x1,y1,text,block_no,block_type)

        for card_idx in range(CARDS_PER_PAGE):
            card_num = card_idx + 1  # 1-based
            card_id = f"{page_idx}-{card_num}"
            meta_id = f"{page_idx:02d}-{card_num}"  # ID-formaat zoals de app gebruikt

            y_top = card_idx * card_height
            y_bot = y_top + card_height

            # Voorzijde = links t/m de split (inclusief eigen border), GEEN rechts-trim
            front = img.crop((0, y_top, split_x, y_bot))
            # Achterzijde = vanaf net na de split, rechts bijgesneden
            back_raw = img.crop((split_x, y_top, w, y_bot))
            back = trim_right_whitespace(back_raw)

            front_path = OUT_DIR / f"front_{page_idx:02d}_{card_num}.png"
            back_path  = OUT_DIR / f"back_{page_idx:02d}_{card_num}.png"

            front.save(front_path, "PNG", optimize=True)
            back.save(back_path, "PNG", optimize=True)

            cards.append({
                "id": card_id,
                "page": page_idx,
                "card": card_num,
                "front_file": str(front_path),
                "back_file": str(back_path),
                "front_b64": img_to_b64(front),
                "back_b64": img_to_b64(back),
            })

            # ── Tekst extraheren voor zoekindex ──────────────────────────
            y_top_pdf = y_top * scale
            y_bot_pdf = y_bot * scale
            front_blocks_text = []
            back_blocks_text  = []

            for block in text_blocks:
                x0, y0, x1, y1, text, _block_no, block_type = block
                if block_type != 0 or not text.strip():
                    continue
                block_mid_y = (y0 + y1) / 2
                if not (y_top_pdf <= block_mid_y <= y_bot_pdf):
                    continue
                clean = ' '.join(text.split()).upper()
                block_mid_x = (x0 + x1) / 2
                if block_mid_x < split_x_pdf:
                    front_blocks_text.append((y0, clean))
                else:
                    back_blocks_text.append((y0, clean))

            front_blocks_text.sort(key=lambda b: b[0])
            back_blocks_text.sort(key=lambda b: b[0])
            metadata[meta_id] = {
                "f": [t for _, t in front_blocks_text],
                "b": [t for _, t in back_blocks_text],
            }

            print(f"  Kaart {card_id} opgeslagen")

    doc.close()

    # Sla zoekindex op
    meta_path = OUT_DIR / "metadata.json"
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, separators=(',', ':')))
    print(f"Zoekindex opgeslagen: {meta_path} ({len(metadata)} kaarten)")
    print(f"\nKlaar: {len(cards)} flashcards verwerkt")
    return cards

def find_split(img):
    """Detecteert de exacte splitslijn tussen voorzijde en achterzijde.
    Zoekt de linker oranje kaderrand van de achterzijde in het middengebied.
    Fallback: iets links van het midden (45%).
    """
    import numpy as np
    w, h = img.size
    arr = np.array(img.convert("RGB"))

    # Zoek de eerste oranje kolom in het middengebied (38%–62%)
    search_start = int(w * 0.38)
    search_end   = int(w * 0.62)

    for col in range(search_start, search_end):
        col_data = arr[:, col, :]
        r = int(col_data[:, 0].mean())
        g = int(col_data[:, 1].mean())
        b = int(col_data[:, 2].mean())
        # Oranje = hoge R, middelmatige G, lage B
        if r > 120 and 40 < g < 160 and b < 100:
            # Gevonden: gebruik dit als splitspunt (5px marge vóór de rand)
            # +4px: voorzijde toont eigen bruine rand, achterzijde begint erna
            return max(col + 4, int(w * 0.38))

    # Geen oranje gevonden: gebruik 45% als conservatieve fallback
    return int(w * 0.45)


def trim_right_whitespace(img, threshold=245, min_content_width=50):
    """Snijdt lege witte ruimte aan de rechterkant af."""
    import numpy as np
    arr = np.array(img.convert("RGB"))
    col_max = arr.min(axis=(0, 2))
    last_col = len(col_max) - 1
    for i in range(len(col_max) - 1, min_content_width, -1):
        if col_max[i] < threshold:
            last_col = i + 10
            break
    return img.crop((0, 0, min(last_col, img.width), img.height))

def img_to_b64(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

# Hieronder de rest van Claude's code (build_html_app etc.)
# ... (de rest van de code die je al had)

if __name__ == '__main__':
    if not os.path.exists(PDF_FILE):
        print(f"PDF niet gevonden: {PDF_FILE}")
        sys.exit(1)
    
    cards = split_pdf_to_cards(PDF_FILE)
    # build_html_app(cards)   ← dit deel vervangen we door mijn versie
    print(f"\nPNG's zijn klaar in de map 'flashcards'")