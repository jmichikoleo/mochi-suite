import os
from flask import Flask, render_template, request, send_file
from converter import *

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    file = request.files["file"]

    pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(pdf_path)

    text = extract_pdf_text(pdf_path)

    chapters = detect_chapters(text)

    base = file.filename.replace(".pdf", "")

    txt_path = os.path.join(OUTPUT_FOLDER, base + ".txt")
    epub_path = os.path.join(OUTPUT_FOLDER, base + ".epub")
    audio_path = os.path.join(OUTPUT_FOLDER, base + ".mp3")

    save_txt(text, txt_path)

    create_epub(chapters, base, epub_path)

    create_audiobook(text[:5000], audio_path)

    return {
        "txt": txt_path,
        "epub": epub_path,
        "audio": audio_path
    }


@app.route("/download")
def download():

    file = request.args.get("file")

    return send_file(file, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)