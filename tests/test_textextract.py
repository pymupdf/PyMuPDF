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

def test_2954():
    '''
    Check handling of unknow unicode characters, issue #2954, fixed in
    mupdf-1.23.9 with addition of FZ_STEXT_USE_CID_FOR_UNKNOWN_UNICODE.
    '''
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_2954.pdf')
    flags0 = (0
            | fitz.TEXT_PRESERVE_WHITESPACE
            | fitz.TEXT_PRESERVE_LIGATURES
            | fitz.TEXT_MEDIABOX_CLIP
            )
    
    document = fitz.Document(path)
    
    expected_good = (
            "IT-204-IP (2021) Page 3 of 5\nNYPA2514    12/06/21\nPartner's share of \n"
            " modifications (see instructions)\n20\n State additions\nNumber\n"
            "A ' Total amount\nB '\n State allocated amount\n"
            "EA '\n20a\nEA '\n20b\nEA '\n20c\nEA '\n20d\nEA '\n20e\nEA '\n20f\n"
            "Total addition modifications (total of column A, lines 20a through 20f)\n"
            ". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . \n"
            "21\n21\n22\n State subtractions\n"
            "Number\nA ' Total amount\nB '\n State allocated amount\n"
            "ES '\n22a\nES '\n22b\nES '\n22c\nES '\n22d\nES '\n22e\nES '\n22f\n23\n23\n"
            "Total subtraction modifications (total of column A, lines 22a through 22f). . . . . . . . . . . . . . . . . . . . . . . . . . . . \n"
            "Additions to itemized deductions\n24\nAmount\n"
            "Letter\n"
            "24a\n24b\n24c\n24d\n24e\n24f\n"
            "Total additions to itemized deductions (add lines 24a through 24f)\n"
            ". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . \n"
            "25\n25\n"
            "Subtractions from itemized deductions\n"
            "26\nLetter\nAmount\n26a\n26b\n26c\n26d\n26e\n26f\n"
            "Total subtractions from itemized deductions (add lines 26a through 26f) . . . . . . . . . . . . . . . . . . . . . . . . . . . . \n"
            "27\n27\n"
            "This line intentionally left blank. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . \n"
            "28\n28\n118003213032\n"
            )
    
    def check_good(text):
        '''
        Returns true if `text` is approximately the same as `expected_good`.

        2024-01-09: MuPDF master and 1.23.x give slightly different 'good'
        output, differing in a missing newline. So we compare without newlines.
        '''
        return text.replace('\n', '') == expected_good.replace('\n', '')
    
    n_fffd_good = 0
    n_fffd_bad = 749
    
    def get(flags=None):
        text = [page.get_text(flags=flags) for page in document]
        assert len(text) == 1
        text = text[0]
        n_fffd = text.count(chr(0xfffd))
        if 0:
            # This print() fails on Windows with UnicodeEncodeError.
            print(f'{flags=} {n_fffd=} {text=}')
        return text, n_fffd
    
    text_none, n_fffd_none = get()
    text_0, n_fffd_0 = get(flags0)
    
    if fitz.mupdf_version_tuple >= (1, 23, 9):
        text_1, n_fffd_1 = get(flags0 | fitz.TEXT_CID_FOR_UNKNOWN_UNICODE)
        
        assert n_fffd_none == n_fffd_good
        assert n_fffd_0 == n_fffd_bad
        assert n_fffd_1 == n_fffd_good
        
        assert check_good(text_none)
        assert not check_good(text_0)
        assert check_good(text_1)
    else:
        assert n_fffd_none == n_fffd_bad
        assert n_fffd_0 == n_fffd_bad
        
        assert not check_good(text_none)
        assert not check_good(text_0)


def test_3027():
    path = path = f'{pymupdfdir}/tests/resources/2.pdf'
    doc = fitz.open(path)
    page = doc[0]
    textpage = page.get_textpage()
    fitz.utils.get_text(page=page, option="dict", textpage=textpage)["blocks"]
