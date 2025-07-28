# app/utils/image_utils.py
import os
import uuid
from datetime import datetime
from PIL import Image
from flask import current_app, request, url_for, jsonify

def save_image(image_file, folder="uploads/portfolio", output_format="WEBP", max_size=(1200, 1200)):
    """
    ✅ Sparar en uppladdad bild som WEBP (eller annat angivet format).
    - Lägger till tidsstämpel + UUID i filnamnet för att undvika krockar.
    - Skalar ner bilden proportionerligt till max_size.
    - Returnerar det nya filnamnet (utan sökväg).
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())
        filename = f"{timestamp}_{unique_id}.{output_format.lower()}"

        save_path = os.path.join(current_app.static_folder, folder, filename)

        image = Image.open(image_file).convert("RGB")
        image.thumbnail(max_size)
        image.save(save_path, output_format)

        return filename
    except Exception as e:
        current_app.logger.error(f"Misslyckades att spara bild: {e}", exc_info=True)
        raise

def delete_existing_image(filename, folder="uploads/portfolio"):
    """
    ✅ Tar bort en befintlig bild från servern.
    - Loggar både lyckade borttagningar och varningar om filen inte finns.
    """
    try:
        filepath = os.path.join(current_app.static_folder, folder, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            current_app.logger.info(f"Bild raderad: {filepath}")
        else:
            current_app.logger.warning(f"Filen hittades inte för borttagning: {filepath}")
    except Exception as e:
        current_app.logger.error(f"Misslyckades att ta bort bild: {e}", exc_info=True)

def _handle_quill_upload(folder="uploads/blog"):
    """
    ✅ Hanterar bilduppladdning från Quill-editorn.
    - Tar emot bilden via request.files["image"].
    - Konverterar alltid till WEBP, kvalitet 85.
    - Returnerar en JSON med den publika URL:en för bilden.
    """
    file = request.files.get("image")
    if not file:
        return jsonify({'error': 'Ingen bildfil mottagen'}), 400

    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{uuid.uuid4().hex}.webp"

        save_dir = os.path.join(current_app.static_folder, folder)
        os.makedirs(save_dir, exist_ok=True)

        img = Image.open(file).convert("RGB")
        img.save(os.path.join(save_dir, filename), "WEBP", quality=85)

        image_url = url_for('static', filename=f"{folder}/{filename}")
        return jsonify({'url': image_url})
    except Exception as e:
        current_app.logger.error(f"Fel vid bilduppladdning (Quill): {e}", exc_info=True)
        return jsonify({'error': 'Fel vid uppladdning av bild'}), 500