import os
from io import BytesIO
from PIL import Image
from flask import Flask, request, render_template, send_file
import openai

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

openai.api_key = os.getenv("OPENAI_API_KEY")

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

@app.route("/", methods=["GET", "POST"])
def index():
    ascii = result = None
    if request.method == "POST":
        file = request.files.get("image")
        if file:
            img = Image.open(file.stream)
            width = int(request.form.get("width", 100))
            ascii = image_to_ascii(img, width)
            # GPT-4 Vision example (optional)
            try:
                resp = openai.ChatCompletion.create(
                    model="gpt-4-1106-preview",
                    messages=[
                        {"role":"user","content":[
                            {"type":"text","text":"Donne-moi un titre court pour cet ASCII art :"},
                            {"type":"image_url","image_url":{"url":""}}
                        ]}
                    ],
                    response_format={"type":"json_object"}
                )
                result = resp.choices[0].message.content
            except Exception:
                result = None
    return render_template("index.html", ascii=ascii, analysis=result)

@app.route("/download")
def download():
    ascii = request.args.get("ascii","")
    buf = BytesIO(ascii.encode('utf-8'))
    return send_file(buf, as_attachment=True, download_name="ascii_output.txt")

if __name__ == "__main__":
    app.run()
