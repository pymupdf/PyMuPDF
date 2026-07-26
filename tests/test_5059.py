import sys
from pathlib import Path
from gentle_compare import rms
import pymupdf

ROTATIONS = (90, 180, 270)


def _add_test_content(page, rotation):
    # Simple frame to make orientation changes visible.
    page.draw_polyline([(20, 20), (400, 20), (400, 300), (20, 300), (20, 20)])
    page.draw_line((20, 160), (400, 160))
    page.insert_text((30, 150), f"PAGE ROT {rotation}", fontsize=10)

    # Geometric annotations.
    rect_a = pymupdf.Rect(30, 30, 90, 80)
    square = page.add_rect_annot(rect_a)
    square.set_colors(stroke=(1, 0, 0))
    square.set_border(width=1)
    square.update()

    rect_b = pymupdf.Rect(110, 30, 170, 80)
    circle = page.add_circle_annot(rect_b)
    circle.set_colors(stroke=(0, 0, 1))
    circle.set_border(width=1)
    circle.update()

    line = page.add_line_annot((190, 30), (260, 80))
    line.set_colors(stroke=(0, 0.5, 0))
    line.set_border(width=1)
    line.update()

    polyline = page.add_polyline_annot([(280, 30), (320, 40), (290, 80), (350, 70)])
    polyline.set_colors(stroke=(1, 0.4, 0))
    polyline.set_border(width=1)
    polyline.update()

    polygon = page.add_polygon_annot([(30, 100), (80, 120), (60, 150), (20, 140)])
    polygon.set_colors(stroke=(0.6, 0, 0.8))
    polygon.set_border(width=1)
    polygon.update()

    ink = page.add_ink_annot(
        [
            [(110, 100), (120, 120), (130, 110), (140, 130)],
            [(150, 100), (160, 120), (170, 110)],
        ]
    )
    ink.set_colors(stroke=(0, 0.7, 0.7))
    ink.set_border(width=1)
    ink.update()

    # FreeText in the historically problematic corner.
    ft_rect = pymupdf.Rect(340, 250, 400, 300)
    ft = page.add_freetext_annot(
        ft_rect,
        f"FT {rotation}",
        text_color=(1, 0, 0),
        rotate=rotation,
    )
    ft.update()

    # Sticky note + stamp.
    text_annot = page.add_text_annot((200, 120), f"Note {rotation}")
    text_annot.update()

    stamp_rect = pymupdf.Rect(280, 100, 380, 145)
    stamp = page.add_stamp_annot(stamp_rect, stamp=13)  # Draft
    stamp.update()

    # Marker annotations based on searched text quads.
    marker_text = "MARK_A MARK_B MARK_C MARK_D"
    page.insert_text((30, 220), marker_text, fontsize=12)

    q1 = page.search_for("MARK_A", quads=True)
    if q1:
        page.add_highlight_annot(q1)

    q2 = page.search_for("MARK_B", quads=True)
    if q2:
        page.add_underline_annot(q2)

    q3 = page.search_for("MARK_C", quads=True)
    if q3:
        page.add_strikeout_annot(q3)

    q4 = page.search_for("MARK_D", quads=True)
    if q4:
        page.add_squiggly_annot(q4)


def _make_input_pdf(rotation):
    doc = pymupdf.open()
    page = doc.new_page(width=420, height=320)
    page.set_rotation(rotation)
    _add_test_content(page, rotation)
    return doc


def test_5059():
    for rot in ROTATIONS:
        src = _make_input_pdf(rot)
        page = src[0]
        pix_orig = page.get_pixmap(colorspace=pymupdf.csGRAY)
        page.remove_rotation()
        pix_rot0 = page.get_pixmap(colorspace=pymupdf.csGRAY)
        rms_val = rms(pix_orig.samples, pix_rot0.samples, verbose=False)
        print(f"RMS diff for rotation {rot}: {rms_val}")
        assert rms_val < 2, f"RMS diff for rotation {rot}: {rms_val}"


if __name__ == "__main__":
    test_5059()
