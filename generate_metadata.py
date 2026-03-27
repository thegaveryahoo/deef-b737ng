#!/usr/bin/env python3
"""
B737NG Flashcard Trainer — Naslag Metadata Generator
Extraheert tekst uit de originele PDF en slaat op als flashcards/metadata.json.
Dit bestand wordt door de app gebruikt voor de Naslag-zoekfunctie.

Gebruik:   python generate_metadata.py [pdf_bestand]
Standaard: python generate_metadata.py flashcardsv2.0.pdf

Vereisten: pip install pymupdf pillow numpy  (zelfde als app.py)
"""
import sys, json, io
from pathlib import Path

try:
    import fitz
    from PIL import Image
    import numpy as np
except ImportError:
    print("Installeer eerst: pip install pymupdf pillow numpy")
    sys.exit(1)

PDF_FILE      = sys.argv[1] if len(sys.argv) > 1 else "flashcardsv2.0.pdf"
OUT_DIR       = Path("flashcards")
CARDS_PER_PAGE = 5
DPI            = 150


def find_split(img):
    """Detecteert de oranje splitslijn tussen voor- en achterzijde."""
    w, h = img.size
    arr = np.array(img.convert("RGB"))
    for col in range(int(w * 0.38), int(w * 0.62)):
        col_data = arr[:, col, :]
        r = int(col_data[:, 0].mean())
        g = int(col_data[:, 1].mean())
        b = int(col_data[:, 2].mean())
        if r > 120 and 40 < g < 160 and b < 100:
            return max(col + 4, int(w * 0.38))
    return int(w * 0.45)


def generate(pdf_path):
    if not Path(pdf_path).exists():
        print(f"FOUT: PDF niet gevonden: {pdf_path}")
        print("Gebruik: python generate_metadata.py <pdf_bestand>")
        sys.exit(1)

    OUT_DIR.mkdir(exist_ok=True)
    doc  = fitz.open(pdf_path)
    meta = {}

    print(f"Verwerken: {pdf_path}  ({len(doc)} pagina's, {len(doc) * CARDS_PER_PAGE} kaarten)")

    for page_num in range(len(doc)):
        page      = doc[page_num]
        page_idx  = page_num + 1

        # Render pagina om splitspunt te detecteren
        mat = fitz.Matrix(DPI / 72, DPI / 72)
        img = Image.open(io.BytesIO(page.get_pixmap(matrix=mat).tobytes("png")))
        w, h       = img.size
        split_x    = find_split(img)
        card_h     = h // CARDS_PER_PAGE
        scale      = 72.0 / DPI
        split_x_pdf = split_x * scale

        text_blocks = page.get_text("blocks")  # (x0,y0,x1,y1,text,bn,type)

        for card_idx in range(CARDS_PER_PAGE):
            card_num = card_idx + 1
            meta_id  = f"{page_idx:02d}-{card_num}"

            y_top = (card_idx * card_h) * scale
            y_bot = y_top + card_h * scale

            front_b, back_b = [], []

            for blk in text_blocks:
                x0, y0, x1, y1, text, _bn, btype = blk
                if btype != 0 or not text.strip():
                    continue
                mid_y = (y0 + y1) / 2
                if not (y_top <= mid_y <= y_bot):
                    continue
                clean = ' '.join(text.split()).upper()
                if (x0 + x1) / 2 < split_x_pdf:
                    front_b.append((y0, clean))
                else:
                    back_b.append((y0, clean))

            front_b.sort(key=lambda b: b[0])
            back_b.sort(key=lambda b: b[0])
            meta[meta_id] = {
                "f": [t for _, t in front_b],
                "b": [t for _, t in back_b],
            }

        print(f"  Pagina {page_idx}/{len(doc)} verwerkt", end="\r")

    doc.close()

    out_path = OUT_DIR / "metadata.json"
    out_path.write_text(json.dumps(meta, ensure_ascii=False, separators=(',', ':')))
    total_words = sum(
        len(' '.join(v['f'] + v['b']).split())
        for v in meta.values()
    )
    print(f"\nKlaar!  {len(meta)} kaarten geïndexeerd · ~{total_words} woorden")
    print(f"Opgeslagen: {out_path}")
    print("Herstart de app (of druk Ctrl+Shift+R) om de zoekindex te activeren.")


if __name__ == '__main__':
    generate(PDF_FILE)
