import os
from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageFilter
import openai

app = Flask(__name__)

# Clé OpenAI : passer par variable d'environnement en prod
openai.api_key = os.getenv("OPENAI_API_KEY") or "sk-..."

# Palette ASCII personnalisée avec caractères spéciaux
ASCII_CHARS = "@§#×  ○ ⋅ "
#ASCII_CHARS = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
#ASCII_CHARS = "@%#◍×✰○⋅ "

def resize_image(image, new_width=150):
    width, height = image.size
    ratio = height / width / 1.8  # Ratio pour rendre plus compact
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

    if request.method == "POST":
        try:
            width = int(request.form.get("width", 100))
            file = request.files.get("image")
            if not file:
                error = "Aucun fichier uploadé."
            else:
                image = Image.open(file.stream)
                ascii_art = image_to_ascii(image, width)
        except Exception as e:
            error = f"Erreur lors de la conversion : {e}"

    return render_template("index.html", ascii_art=ascii_art, width=width, error=error)

@app.route("/stylize_ascii", methods=["POST"])
def stylize_ascii():
    """
    Reçoit le texte ASCII + couleur choisie, et demande à GPT-4 de styliser façon hacker neon.
    """
    data = request.get_json(force=True)
    ascii_text = data.get("ascii_text", "")
    color = data.get("color", "#39ff14")  # Couleur fluo par défaut vert neon

    if not ascii_text:
        return jsonify({"error": "Aucun ASCII reçu"}), 400

    prompt = (
        "Améliore cet art ASCII pour lui donner un style cyberpunk/hacker avec effet fluo. "
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
            temperature=0.7,
        )
        styled_ascii = response.choices[0].message.content.strip()
        return jsonify({"styled_ascii": styled_ascii})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
