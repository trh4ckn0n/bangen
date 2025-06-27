import os
from flask import Flask, render_template, request, jsonify
from PIL import Image
import openai

app = Flask(__name__)

# Met ta clé API OpenAI en variable d'environnement ou ici directement (pas recommandé en prod)
openai.api_key = os.getenv("OPENAI_API_KEY") or "ta_clef_openai_ici"

ASCII_CHARS = "@%#*+=-:. "

def resize_image(image, new_width=100):
    width, height = image.size
    ratio = height / width / 1.65
    new_height = int(new_width * ratio)
    return image.resize((new_width, new_height))

def grayify(image):
    return image.convert("L")

def pixels_to_ascii(image):
    pixels = image.getdata()
    chars = "".join([ASCII_CHARS[min(pixel // 25, len(ASCII_CHARS) - 1)] for pixel in pixels])
    return chars

def image_to_ascii(image, width):
    image = resize_image(image, width)
    image = grayify(image)
    ascii_str = pixels_to_ascii(image)
    pixel_count = len(ascii_str)
    ascii_img = "\n".join([ascii_str[index:index+width] for index in range(0, pixel_count, width)])
    return ascii_img

@app.route("/", methods=["GET", "POST"])
def index():
    ascii_art = None
    stylized_ascii = None
    width = 100
    error = None

    if request.method == "POST":
        file = request.files.get("image")
        width = int(request.form.get("width", 100))
        if not file:
            error = "Aucun fichier uploadé."
        else:
            try:
                image = Image.open(file.stream)
                ascii_art = image_to_ascii(image, width)
            except Exception as e:
                error = f"Erreur lors de la conversion : {e}"

    return render_template("index.html", ascii_art=ascii_art, stylized_ascii=stylized_ascii, width=width, error=error)

@app.route("/stylize_ascii", methods=["POST"])
def stylize_ascii():
    """
    Reçoit le texte ASCII, demande à OpenAI de le rendre plus "hacker style", renvoie résultat
    """
    data = request.json
    ascii_text = data.get("ascii_text", "")
    color = data.get("color", "#00ffff")

    if not ascii_text:
        return jsonify({"error": "Aucun ASCII reçu"}), 400

    prompt = f"Améliore ce texte ASCII pour lui donner un style hacker, ajoute des effets visuels en texte, reste en ASCII art, ne modifie pas la structure:\n\n{ascii_text}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7,
        )
        styled_ascii = response.choices[0].message.content.strip()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"styled_ascii": styled_ascii})

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
