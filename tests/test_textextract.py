"""
Exract page text in various formats.
No checks performed - just contribute to code coverage.
"""
import os

import fitz

pymupdfdir = os.path.abspath(f'{__file__}/../..')
scriptdir = f'{pymupdfdir}/tests'
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
    
def test_extract4():
    '''
    Rebased-specific.
    '''
    if not hasattr(fitz, 'mupdf'):
        return
    path = f'{pymupdfdir}/tests/resources/2.pdf'
    document = fitz.open(path)
    page = document[4]
    
    out = 'test_stext.html'
    text = page.get_text('html')
    with open(out, 'w') as f:
        f.write(text)
    print(f'Have written to: {out}')
    
    out = 'test_extract.html'
    writer = fitz.mupdf.FzDocumentWriter(
            out,
            'html',
            fitz.mupdf.FzDocumentWriter.OutputType_DOCX,
            )
    device = fitz.mupdf.fz_begin_page(writer, fitz.mupdf.fz_bound_page(page))
    fitz.mupdf.fz_run_page(page, device, fitz.mupdf.FzMatrix(), fitz.mupdf.FzCookie())
    fitz.mupdf.fz_end_page(writer)
    fitz.mupdf.fz_close_document_writer(writer)
    print(f'Have written to: {out}')
    
    if fitz.mupdf_version_tuple >= (1, 23, 4):
        def get_text(page, space_guess):
            buffer_ = fitz.mupdf.FzBuffer( 10)
            out = fitz.mupdf.FzOutput( buffer_)
            writer = fitz.mupdf.FzDocumentWriter(
                    out,
                    'text,space-guess={space_guess}',
                    fitz.mupdf.FzDocumentWriter.OutputType_DOCX,
                    )
            device = fitz.mupdf.fz_begin_page(writer, fitz.mupdf.fz_bound_page(page))
            fitz.mupdf.fz_run_page(page, device, fitz.mupdf.FzMatrix(), fitz.mupdf.FzCookie())
            fitz.mupdf.fz_end_page(writer)
            fitz.mupdf.fz_close_document_writer(writer)
            text = buffer_.fz_buffer_extract()
            text = text.decode('utf8')
            n = text.count(' ')
            print(f'{space_guess=}: {n=}')
            return text, n
        page = document[4]
        text0, n0 = get_text(page, 0)
        text1, n1 = get_text(page, 0.5)
        text2, n2 = get_text(page, 0.001)
        text2, n2 = get_text(page, 0.1)
        text2, n2 = get_text(page, 0.3)
        text2, n2 = get_text(page, 0.9)
        text2, n2 = get_text(page, 5.9)
        assert text1 == text0
