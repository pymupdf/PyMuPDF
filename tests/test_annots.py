# -*- coding: utf-8 -*-
"""
Test PDF annotation insertions.
"""
import fitz
import os

fitz.TOOLS.set_annot_stem("jorj")

red = (1, 0, 0)
blue = (0, 0, 1)
gold = (1, 1, 0)
green = (0, 1, 0)

displ = fitz.Rect(0, 50, 0, 50)
r = fitz.Rect(72, 72, 220, 100)
t1 = u"têxt üsès Lätiñ charß,\nEUR: €, mu: µ, super scripts: ²³!"
rect = fitz.Rect(100, 100, 200, 200)


def test_caret():
    doc = fitz.open()
    page = doc.new_page()
    annot = page.add_caret_annot(rect.tl)
    assert annot.type == (14, "Caret")
    annot.update(rotate=20)
    page.annot_names()
    page.annot_xrefs()


def test_freetext():
    doc = fitz.open()
    page = doc.new_page()
    annot = page.add_freetext_annot(
        rect,
        t1,
        fontsize=10,
        rotate=90,
        text_color=blue,
        fill_color=gold,
        align=fitz.TEXT_ALIGN_CENTER,
    )
    annot.set_border(width=0.3, dashes=[2])
    annot.update(text_color=blue, fill_color=gold)
    assert annot.type == (2, "FreeText")


def test_text():
    doc = fitz.open()
    page = doc.new_page()
    annot = page.add_text_annot(r.tl, t1)
    assert annot.type == (0, "Text")


def test_highlight():
    doc = fitz.open()
    page = doc.new_page()
    annot = page.add_highlight_annot(rect)
    assert annot.type == (8, "Highlight")


def test_underline():
    doc = fitz.open()
    page = doc.new_page()
    annot = page.add_underline_annot(rect)
    assert annot.type == (9, "Underline")


def test_squiggly():
    doc = fitz.open()
    page = doc.new_page()
    annot = page.add_squiggly_annot(rect)
    assert annot.type == (10, "Squiggly")


def test_strikeout():
    doc = fitz.open()
    page = doc.new_page()
    annot = page.add_strikeout_annot(rect)
    assert annot.type == (11, "StrikeOut")
    page.delete_annot(annot)


def test_polyline():
    doc = fitz.open()
    page = doc.new_page()
    rect = page.rect + (100, 36, -100, -36)
    cell = fitz.make_table(rect, rows=10)
    for i in range(10):
        annot = page.add_polyline_annot((cell[i][0].bl, cell[i][0].br))
        annot.set_line_ends(i, i)
        annot.update()
    for i, annot in enumerate(page.annots()):
        assert annot.line_ends == (i, i)
    assert annot.type == (7, "PolyLine")


def test_polygon():
    doc = fitz.open()
    page = doc.new_page()
    annot = page.add_polygon_annot([rect.bl, rect.tr, rect.br, rect.tl])
    assert annot.type == (6, "Polygon")


def test_line():
    doc = fitz.open()
    page = doc.new_page()
    rect = page.rect + (100, 36, -100, -36)
    cell = fitz.make_table(rect, rows=10)
    for i in range(10):
        annot = page.add_line_annot(cell[i][0].bl, cell[i][0].br)
        annot.set_line_ends(i, i)
        annot.update()
    for i, annot in enumerate(page.annots()):
        assert annot.line_ends == (i, i)
    assert annot.type == (3, "Line")


def test_square():
    doc = fitz.open()
    page = doc.new_page()
    annot = page.add_rect_annot(rect)
    assert annot.type == (4, "Square")


def test_circle():
    doc = fitz.open()
    page = doc.new_page()
    annot = page.add_circle_annot(rect)
    assert annot.type == (5, "Circle")


def test_fileattachment():
    doc = fitz.open()
    page = doc.new_page()
    annot = page.add_file_annot(rect.tl, b"just anything for testing", "testdata.txt")
    assert annot.type == (17, "FileAttachment")


def test_stamp():
    doc = fitz.open()
    page = doc.new_page()
    annot = page.add_stamp_annot(r, stamp=10)
    assert annot.type == (13, "Stamp")
    annot_id = annot.info["id"]
    annot_xref = annot.xref
    a1 = page.load_annot(annot_id)
    a2 = page.load_annot(annot_xref)
    page = doc.reload_page(page)


def test_redact():
    doc = fitz.open()
    page = doc.new_page()
    annot = page.add_redact_annot(r, text="Hello")
    annot.update(
        cross_out=True,
        rotate=-1,
    )
    assert annot.type == (12, "Redact")
    x = annot._get_redact_values()
    pix = annot.get_pixmap()
    info = annot.info
    annot.set_info(info)
    assert not annot.has_popup
    annot.set_popup(r)
    s = annot.popup_rect
    assert s == r
    page.apply_redactions()

def test_1645():
    '''
    Test fix for #1645.
    '''
    path_in = os.path.abspath( f'{__file__}/../resources/symbol-list.pdf')
    path_expected = os.path.abspath( f'{__file__}/../resources/test_1645_expected.pdf')
    path_out = os.path.abspath( f'{__file__}/../test_1645_out.pdf')
    doc = fitz.open(path_in)
    page = doc[0]
    page_bounds = page.bound()
    annot_loc = fitz.Rect(page_bounds.x0, page_bounds.y0, page_bounds.x0 + 75, page_bounds.y0 + 15)
    page.add_freetext_annot(annot_loc * page.derotation_matrix, "TEST", fontsize=18,
    fill_color=fitz.utils.getColor("FIREBRICK1"), rotate=page.rotation)
    doc.save(path_out, garbage=1, deflate=True, no_new_id=True)
    print(f'Have created {path_out}. comparing with {path_expected}.')
    with open( path_out, 'rb') as f:
        out = f.read()
    with open( path_expected, 'rb') as f:
        expected = f.read()
    assert out == expected, f'Files differ: {path_out} {path_expected}'

def test_1824():
    '''
    Test for fix for #1824: SegFault when applying redactions overlapping a
    transparent image.
    '''
    path = os.path.abspath( f'{__file__}/../resources/test_1824.pdf')
    doc=fitz.open(path)
    page=doc[0]
    page.apply_redactions()
