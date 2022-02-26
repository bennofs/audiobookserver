#!/usr/bin/env python3
import re
import zipstream
import os
import os.path
from flask import Flask, Response, url_for, send_file, safe_join, render_template
from urllib.parse import quote

MEDIA_ROOT = os.path.abspath(os.getenv("MEDIA_ROOT", "/tmp/audiobooks"))
NAME_RE = re.compile(r'^[a-zA-ZäöüÄÖÜ:\- 0-9.]*$')
VALID_BOOK_CACHE = set()
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


def load_books():
    for book in os.listdir(MEDIA_ROOT):
        if not NAME_RE.match(book):
            continue

        if book.endswith(".zip") or book.endswith(".m4b"):
            continue

        if book in VALID_BOOK_CACHE:
            yield book
            continue

        if not os.path.exists(os.path.join(MEDIA_ROOT, book, 'cover.jpg')):
            continue

        VALID_BOOK_CACHE.add(book)
        yield book

@app.route('/')
def index():
    books = [
        { "name": name, "download": url_for('get_zip', name=name), "cover": url_for('cover', name=name) }
        for name in sorted(load_books())
    ]
    return render_template('index.html', books=books)

@app.route('/<name>')
def get_zip(name):
    if not NAME_RE.match(name):
        return "invalid name", 404

    zip_name = safe_join(MEDIA_ROOT, name + ".zip")
    if os.path.exists(zip_name):
        return send_file(zip_name, as_attachment=True, attachment_filename=os.path.basename(zip_name))

    m4b_name = safe_join(MEDIA_ROOT, name + ".m4b")
    if os.path.exists(m4b_name):
        return send_file(m4b_name, as_attachment=True, attachment_filename=os.path.basename(m4b_name))

    return 'missing file', 500

@app.route("/<name>.jpg")
def cover(name):
    if not NAME_RE.match(name):
        return "invalid name", 404

    return send_file(safe_join(MEDIA_ROOT, name, "cover.jpg"))

if __name__ == '__main__':
    app.run()
