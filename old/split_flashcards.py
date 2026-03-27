import fitz  # PyMuPDF
from PIL import Image
import os

pdf_path = "flashcardsv2.0.pdf"          # Naam van je correcte PDF
output_dir = "flashcards"
os.makedirs(output_dir, exist_ok=True)

doc = fitz.open(pdf_path)
card_index = 1

# ================== NIEUWE WAARDEN (afgestemd op jouw PDF + voorbeeld-PNG) ==================
left_margin = 22
front_width = 272
back_x_start = 302
right_margin = 518      # strakker → ID-nummers blijven, lege cel rechts is weg
card_height = 162
gap_between_cards = 9
top_margin = 38
# =========================================================================================

for page_num in range(len(doc)):
    page = doc[page_num]
    page_rect = page.rect
    
    current_y = page_rect.height - top_margin
    
    for card in range(5):
        y_top = current_y
        y_bottom = current_y - card_height
        
        # Front (linkerzijde - visuele situatie)
        front_rect = fitz.Rect(left_margin, y_bottom, left_margin + front_width, y_top)
        pix_front = page.get_pixmap(clip=front_rect, dpi=300)
        img_front = Image.frombytes("RGB", [pix_front.width, pix_front.height], pix_front.samples)
        img_front.save(f"{output_dir}/front_{str(card_index).zfill(3)}.png")
        
        # Back (rechterzijde - tekst + ID-nummers)
        back_rect = fitz.Rect(back_x_start, y_bottom, right_margin, y_top)
        pix_back = page.get_pixmap(clip=back_rect, dpi=300)
        img_back = Image.frombytes("RGB", [pix_back.width, pix_back.height], pix_back.samples)
        img_back.save(f"{output_dir}/back_{str(card_index).zfill(3)}.png")
        
        card_index += 1
        current_y = y_bottom - gap_between_cards

print(f"Klaar! {card_index-1} flashcards gesplitst in map '{output_dir}'")
print("Voor- en achterzijden zijn nu exact zoals je ze geprint zou hebben (met ID-nummers zichtbaar).")