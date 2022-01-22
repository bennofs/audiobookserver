#!/usr/bin/env python3
import os
import os.path
import re
from urllib.parse import quote

import zipstream
from flask import Flask, Response, url_for, send_file, safe_join, render_template

MEDIA_ROOT = os.path.abspath(os.getenv("MEDIA_ROOT", "/tmp/audiobooks"))
NAME_RE = re.compile(r'^[a-zA-ZäöüÄÖÜ:\- 0-9]*$')
VALID_BOOK_CACHE = set()
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


def load_books():
    for book in os.listdir(MEDIA_ROOT):
        if not NAME_RE.match(book):
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

@app.route('/<name>.zip')
def get_zip(name):
    if not NAME_RE.match(name):
        return "invalid name", 404
    z = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_STORED)
    root = safe_join(MEDIA_ROOT, name)
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            fpath = safe_join(dirpath, filename)
            z.write(fpath, arcname=os.path.relpath(fpath, MEDIA_ROOT))

    response = Response(z, mimetype='application/zip')
    response.headers['Content-Disposition'] = 'attachment; filename=' + quote(name) + ".zip"
    return response


@app.route("/<name>.jpg")
def cover(name):
    if not NAME_RE.match(name):
        return "invalid name", 404

    return send_file(safe_join(MEDIA_ROOT, name, "cover.jpg"))

if __name__ == '__main__':
    app.run()
