import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image, ImageFilter
import openai

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/ascii"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Clé OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY") or "sk-..."

# ASCII personnalisée
ASCII_CHARS = "@§#×  ○ ⋅ "

def resize_image(image, new_width=150):
    width, height = image.size
    ratio = height / width / 1.8
    new_height = int(new_width * ratio)
    return image.resize((new_width, new_height))

def grayify(image):
    return image.convert("L")

def sharpen_image(image):
    return image.filter(ImageFilter.SHARPEN)

def pixels_to_ascii(image):
    pixels = image.getdata()
    interval = 255 / (len(ASCII_CHARS) - 1)
    chars = "".join(ASCII_CHARS[int(pixel / interval)] for pixel in pixels)
    return chars

def image_to_ascii(image, width):
    image = resize_image(image, width)
    image = sharpen_image(image)
    image = grayify(image)
    ascii_str = pixels_to_ascii(image)
    ascii_img = "\n".join(ascii_str[i:i+width] for i in range(0, len(ascii_str), width))
    return ascii_img

@app.route("/", methods=["GET", "POST"])
def index():
    ascii_art = None
    error = None
    width = 100
    ascii_filename = None

    if request.method == "POST":
        try:
            width = int(request.form.get("width", 100))
            file = request.files.get("image")
            if not file:
                error = "Aucun fichier uploadé."
            else:
                image = Image.open(file.stream)
                ascii_art = image_to_ascii(image, width)

                # Sauvegarde ASCII dans fichier
                filename = f"ascii_{uuid.uuid4().hex[:8]}.txt"
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(ascii_art)
                ascii_filename = filename

        except Exception as e:
            error = f"Erreur lors de la conversion : {e}"

    return render_template("index.html", ascii_art=ascii_art, width=width, error=error, ascii_filename=ascii_filename)

@app.route("/stylize_ascii", methods=["POST"])
def stylize_ascii():
    data = request.get_json(force=True)
    ascii_text = data.get("ascii_text", "")
    color = data.get("color", "#39ff14")

    if not ascii_text:
        return jsonify({"error": "Aucun ASCII reçu"}), 400

    prompt = (
        "Améliore cet art ASCII pour adapter au mieu les caracteres utilisés afin de rendre le motif le plus lisible et reconnaissable possible. "
        f"La couleur dominante choisie est : {color}. "
        "Ajoute des effets visuels textuels (comme des encadrements, titres stylisés), reste en ASCII pur. "
        "Ne modifie pas l'alignement de base :\n\n"
        f"{ascii_text}"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.8,
        )
        styled_ascii = response.choices[0].message.content.strip()

        # Sauvegarde du résultat stylisé
        styled_filename = f"styled_{uuid.uuid4().hex[:8]}.txt"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], styled_filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(styled_ascii)

        return jsonify({
            "styled_ascii": styled_ascii,
            "download_url": f"/download_ascii/{styled_filename}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download_ascii/<filename>")
def download_ascii(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
