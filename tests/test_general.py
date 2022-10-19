# encoding utf-8
"""
* Confirm sample doc has no links and no annots.
* Confirm proper release of file handles via Document.close()
* Confirm properly raising exceptions in document creation
"""
import io
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "001003ED.pdf")


def test_haslinks():
    doc = fitz.open(filename)
    assert doc.has_links() == False


def test_hasannots():
    doc = fitz.open(filename)
    assert doc.has_annots() == False


def test_haswidgets():
    doc = fitz.open(filename)
    assert doc.is_form_pdf == False


def test_isrepaired():
    doc = fitz.open(filename)
    assert doc.is_repaired == False
    fitz.TOOLS.mupdf_warnings()


def test_isdirty():
    doc = fitz.open(filename)
    assert doc.is_dirty == False


def test_cansaveincrementally():
    doc = fitz.open(filename)
    assert doc.can_save_incrementally() == True


def test_iswrapped():
    doc = fitz.open(filename)
    page = doc[0]
    assert page.is_wrapped


def test_wrapcontents():
    doc = fitz.open(filename)
    page = doc[0]
    page.wrap_contents()
    xref = page.get_contents()[0]
    cont = page.read_contents()
    doc.update_stream(xref, cont)
    page.set_contents(xref)
    assert len(page.get_contents()) == 1
    page.clean_contents()


def test_config():
    assert fitz.TOOLS.fitz_config["py-memory"] in (True, False)


def test_glyphnames():
    name = "infinity"
    infinity = fitz.glyph_name_to_unicode(name)
    assert fitz.unicode_to_glyph_name(infinity) == name


def test_rgbcodes():
    sRGB = 0xFFFFFF
    assert fitz.sRGB_to_pdf(sRGB) == (1, 1, 1)
    assert fitz.sRGB_to_rgb(sRGB) == (255, 255, 255)


def test_pdfstring():
    fitz.get_pdf_now()
    fitz.get_pdf_str("Beijing, chinesisch 北京")
    fitz.get_text_length("Beijing, chinesisch 北京", fontname="china-s")
    fitz.get_pdf_str("Latin characters êßöäü")


def test_open_exceptions():
    try:
        doc = fitz.open(filename, filetype="xps")
    except RuntimeError as e:
        assert repr(e).startswith("FileDataError")

    try:
        doc = fitz.open(filename, filetype="xxx")
    except Exception as e:
        assert repr(e).startswith("ValueError")

    try:
        doc = fitz.open("x.y")
    except Exception as e:
        assert repr(e).startswith("FileNotFoundError")

    try:
        doc = fitz.open("pdf", b"")
    except RuntimeError as e:
        assert repr(e).startswith("EmptyFileError")


def test_bug1945():
    pdf = fitz.open(f'{scriptdir}/resources/bug1945.pdf')
    buffer_ = io.BytesIO()
    pdf.save(buffer_, clean=True)


def test_bug1971():
    for _ in range(2):
        doc = fitz.Document(f'{scriptdir}/resources/bug1971.pdf')
        page = next(doc.pages())
        page.get_drawings()
        doc.close()

