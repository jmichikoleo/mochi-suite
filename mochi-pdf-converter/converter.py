import os
from pdfminer.high_level import extract_text
from ebooklib import epub
from gtts import gTTS


def extract_pdf_text(pdf_path):
    return extract_text(pdf_path)


def detect_chapters(text):

    chapters = []
    current = []

    for line in text.split("\n"):

        if line.isupper() and len(line) < 60:
            if current:
                chapters.append("\n".join(current))
                current = []

        current.append(line)

    if current:
        chapters.append("\n".join(current))

    return chapters


def save_txt(text, path):

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def create_epub(chapters, title, output):

    book = epub.EpubBook()

    book.set_title(title)
    book.set_language("en")

    epub_chapters = []

    for i, chapter in enumerate(chapters):

        c = epub.EpubHtml(
            title=f"Chapter {i+1}",
            file_name=f"chap_{i+1}.xhtml"
        )

        html = "<p>" + chapter.replace("\n", "</p><p>") + "</p>"
        c.content = f"<h1>Chapter {i+1}</h1>{html}"

        book.add_item(c)
        epub_chapters.append(c)

    book.toc = tuple(epub_chapters)

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    book.spine = ["nav"] + epub_chapters

    epub.write_epub(output, book)


def create_audiobook(text, output):

    tts = gTTS(text)
    tts.save(output)