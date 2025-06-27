import os
from io import BytesIO
from PIL import Image
from flask import Flask, request, render_template, send_file, url_for
import openai

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

ASCII_CHARS = "@%#*+=-:. "
def resize_image(image, new_width):
    w, h = image.size
    ratio = h / w / 1.65
    return image.resize((new_width, int(new_width * ratio)))

def image_to_ascii(image, width):
    image = image.convert("L")
    image = resize_image(image, width)
    pixels = image.getdata()
    ascii_str = ''.join([ASCII_CHARS[min(p // 25, len(ASCII_CHARS)-1)] for p in pixels])
    return '\n'.join([ascii_str[i:i+width] for i in range(0, len(ascii_str), width)])

def ascii_to_svg(ascii_art, color="#0ff", shadow=2, font_size=7, letter_spacing=1):
    # SVG basique pour texte monospace, ajout ombre/néon via filter + style
    lines = ascii_art.split('\n')
    svg_lines = []
    y = font_size * 1.2
    for i, line in enumerate(lines):
        # échappe & < > dans le texte
        safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        svg_lines.append(f'<text x="0" y="{y*(i+1)}">{safe_line}</text>')
    svg_content = "\n".join(svg_lines)

    svg_template = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
    width="100%" height="{y * len(lines)}" 
    style="background:#111; font-family: monospace; font-size:{font_size}px; fill:{color}; 
           filter: drop-shadow(0 0 {shadow}px #0ffccf) drop-shadow(0 0 {shadow/2}px #0ffccf);"
    >
  {svg_content}
</svg>
'''
    return svg_template

@app.route("/", methods=["GET", "POST"])
def index():
    ascii = ascii_svg = None
    color = "#0ff"
    shadow = 2
    if request.method == "POST":
        file = request.files.get("image")
        if file:
            img = Image.open(file.stream)
            width = int(request.form.get("width", 100))
            color = request.form.get("color", "#0ff")
            shadow = int(request.form.get("shadow", 2))
            ascii = image_to_ascii(img, width)
            ascii_svg = ascii_to_svg(ascii, color=color, shadow=shadow)
    return render_template("index.html", ascii=ascii, ascii_svg=ascii_svg, color=color, shadow=shadow)

@app.route("/download/txt")
def download_txt():
    ascii = request.args.get("ascii", "")
    buf = BytesIO(ascii.encode('utf-8'))
    return send_file(buf, as_attachment=True, download_name="ascii_output.txt")

@app.route("/download/svg")
def download_svg():
    svg = request.args.get("svg", "")
    buf = BytesIO(svg.encode('utf-8'))
    return send_file(buf, as_attachment=True, download_name="ascii_output.svg")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)
