from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route('/')
def index():
    books = os.listdir(UPLOAD_FOLDER)
    return render_template("index.html", books=books)


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']

    if file:
        filename = secure_filename(file.filename)

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

    return redirect(url_for('index'))


@app.route('/read/<path:filename>')
def read(filename):
    return render_template("reader.html", filename=filename)


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == '__main__':
    app.run(debug=True)
