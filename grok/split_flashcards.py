import fitz
from PIL import Image
import os
import io

pdf_path = "flashcardsv2.0.pdf"
output_dir = "flashcards"
os.makedirs(output_dir, exist_ok=True)

doc = fitz.open(pdf_path)
card_index = 1

# ================== EXACTE WAARDEN VOOR JOUW PDF ==================
left_x      = 22      # linkerkant voorzijde
front_width = 278     # breedte voorzijde (smaller dan de helft)
back_x      = 305     # start achterzijde (net na de scheidingslijn)
back_width  = 257     # breedte achterzijde (ID-code moet volledig zichtbaar zijn)

card_height = 160     # hoogte van 1 flashcard
gap         = 9       # verticale ruimte tussen kaarten
top_margin  = 42      # vanaf bovenkant van de pagina
# =================================================================

for page_num in range(len(doc)):
    page = doc[page_num]
    current_y = page.rect.height - top_margin
    
    for card in range(5):
        y_top = current_y
        y_bottom = current_y - card_height
        
        # Voorzijde (links)
        front_rect = fitz.Rect(left_x, y_bottom, left_x + front_width, y_top)
        pix_front = page.get_pixmap(clip=front_rect, dpi=300)
        Image.frombytes("RGB", [pix_front.width, pix_front.height], pix_front.samples).save(
            f"{output_dir}/front_{str(card_index).zfill(3)}.png"
        )
        
        # Achterzijde (rechts) - met ID-code rechtsonder
        back_rect = fitz.Rect(back_x, y_bottom, back_x + back_width, y_top)
        pix_back = page.get_pixmap(clip=back_rect, dpi=300)
        Image.frombytes("RGB", [pix_back.width, pix_back.height], pix_back.samples).save(
            f"{output_dir}/back_{str(card_index).zfill(3)}.png"
        )
        
        card_index += 1
        current_y = y_bottom - gap

print(f"✅ Klaar! {card_index-1} flashcards gesplitst in map '{output_dir}'")
print("Controleer front_001.png en back_001.png (en eventueel front_005.png / back_005.png)")