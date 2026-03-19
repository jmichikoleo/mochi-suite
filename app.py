import os
from flask import Flask, render_template, request
from services.pdf_processor import extract_slides
from services.summarizer import process_slide

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]

        if file.filename == "":
            return "No file selected"

        path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(path)

        slides = extract_slides(path)

        results = []
        for slide in slides:
            if slide["content"].strip() == "":
                continue

            output = process_slide(slide["content"])

            summary = ""
            explanation = ""

            if "EXPLANATION:" in output:
                parts = output.split("EXPLANATION:")
                summary = parts[0].replace("SUMMARY:", "").strip()
                explanation = parts[1].strip()
            else:
                summary = output

            results.append({
                "slide": slide["slide"],
                "content": slide["content"],
                "summary": summary,
                "explanation": explanation
            })

        return render_template("result.html", results=results)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)