# encoding utf-8
"""
Confirm sample doc has no links and no annots.
"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "001003ED.pdf")
doc = fitz.open(filename)


def test_haslinks():
    assert doc.has_links() == False


def test_hasannots():
    assert doc.has_annots() == False


def test_haswidgets():
    assert doc.is_form_pdf == False


def test_isrepaired():
    assert doc.is_repaired == False
    fitz.TOOLS.mupdf_warnings()


def test_isdirty():
    assert doc.is_dirty == False


def test_cansaveincrementally():
    assert doc.can_save_incrementally() == True


def test_iswrapped():
    page = doc[0]
    assert page.is_wrapped


def test_wrapcontents():
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
