import pdfplumber

def extract_slides(pdf_path):
    slides = []

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()

            if text is None:
                text = ""

            slides.append({
                "slide": i + 1,
                "content": text.strip()
            })

    return slides