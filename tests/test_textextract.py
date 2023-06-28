"""
Exract page text in various formats.
No checks performed - just contribute to code coverage.
"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "symbol-list.pdf")


def test_extract1():
    doc = fitz.open(filename)
    page = doc[0]
    text = page.get_text("text")
    blocks = page.get_text("blocks")
    words = page.get_text("words")
    d1 = page.get_text("dict")
    d2 = page.get_text("json")
    d3 = page.get_text("rawdict")
    d3 = page.get_text("rawjson")
    text = page.get_text("html")
    text = page.get_text("xhtml")
    text = page.get_text("xml")
    rects = fitz.get_highlight_selection(page, start=page.rect.tl, stop=page.rect.br)
    text = fitz.ConversionHeader("xml")
    text = fitz.ConversionTrailer("xml")

def _test_extract2():
    import sys
    import time
    path = f'{scriptdir}/../../PyMuPDF-performance/adobe.pdf'
    if not os.path.exists(path):
        print(f'test_extract2(): not running becase does not exist: {path}')
        return
    doc = fitz.open( path)
    for opt in (
            'dict',
            'dict2',
            'text',
            'blocks',
            'words',
            'html',
            'xhtml',
            'xml',
            'json',
            'rawdict',
            'rawjson',
            ):
        for flags in None, fitz.TEXTFLAGS_TEXT:
            t0 = time.time()
            for page in doc:
                page.get_text(opt, flags=flags)
            t = time.time() - t0
            print(f't={t:.02f}: opt={opt} flags={flags}')
            sys.stdout.flush()

def _test_extract3():
    import sys
    import time
    path = f'{scriptdir}/../../PyMuPDF-performance/adobe.pdf'
    if not os.path.exists(path):
        print(f'test_extract3(): not running becase does not exist: {path}')
        return
    doc = fitz.open( path)
    t0 = time.time()
    for page in doc:
        page.get_text('json')
    t = time.time() - t0
    print(f't={t}')
    sys.stdout.flush()

