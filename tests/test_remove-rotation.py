import json
import os
import sys
import textwrap
import time

import pymupdf

import gentle_compare


scriptdir = os.path.dirname(__file__)
ROTATIONS = (90, 180, 270)


def test_remove_rotation():
    """Remove rotation verifying identical appearance and text."""
    filename = os.path.join(scriptdir, "resources", "test-2812.pdf")
    doc = pymupdf.open(filename)

    # We always create fresh pages to avoid false positives from cache content.
    # Text on these pages consists of pairwise different strings, sorting by
    # these strings must therefore yield identical bounding boxes.
    for i in range(1, doc.page_count):
        assert doc[i].rotation  # must be a rotated page
        pix0 = doc[i].get_pixmap()  # make image
        words0 = []
        for w in doc[i].get_text("words"):
            words0.append(list(pymupdf.Rect(w[:4]) * doc[i].rotation_matrix) + [w[4]])
        words0.sort(key=lambda w: w[4])  # sort by word strings
        # derotate page and confirm nothing else has changed
        doc[i].remove_rotation()
        assert doc[i].rotation == 0
        pix1 = doc[i].get_pixmap()
        words1 = doc[i].get_text("words")
        words1.sort(key=lambda w: w[4])  # sort by word strings
        assert pix1.digest == pix0.digest, f"{pix1.digest}/{pix0.digest}"
        assert gentle_compare.gentle_compare(words0, words1)


def test_5077():
    """Confirm performance improvement for many links."""
    if os.environ.get('PYMUPDF_RUNNING_ON_VALGRIND') == '1':
        print('test_5077(): not running on valgrind because slowness triggers failure.')
        return
    filename = os.path.join(scriptdir, "resources", "test-4000-links.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    print(f"{page.rotation=}, link count={len(page.get_links())}")
    t0 = time.time()
    page.remove_rotation()
    t1 = time.time()
    assert t1 - t0 < 10, f"de-rotation time {t1-t0:.3f} seconds is too long."


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
        
        path = os.path.relpath(os.path.normpath(f'{__file__}/../../tests/test_5059'))
        pix_orig.save(f'{path}_orig.png')
        pix_rot0.save(f'{path}_rot0.png')
        pix_diff = gentle_compare.pixmaps_diff(pix_orig, pix_rot0)
        pix_diff.save(f'{path}_diff.png')
        
        rms_val = gentle_compare.rms(pix_orig.samples, pix_rot0.samples, verbose=False)
        assert rms_val < 0.05, f"RMS diff for rotation {rot}: {rms_val}"


def _test_4394_internal(angle, cropped):
    with pymupdf.open() as doc:
        page = doc.new_page(width=400, height=300)
        page.insert_text((80, 90), "SYNTHETIC CROP TEST")
        if cropped:
            page.set_cropbox(pymupdf.Rect(50, 30, 350, 250))
        page.set_rotation(angle)
        before = page.get_pixmap(colorspace=pymupdf.csGRAY)
        text_before = page.get_text().strip()
        page.remove_rotation()
        with pymupdf.open(stream=doc.tobytes(), filetype="pdf") as saved:
            after = saved[0].get_pixmap(colorspace=pymupdf.csGRAY)
            path = os.path.normpath(f'{__file__}/../../tests/test_4394_out_{angle}_{cropped}.pdf')
            path = os.path.relpath(path)
            ret = {
                "rotation": angle,
                "cropped": cropped,
                "size_before": [before.width, before.height],
                "size_after": [after.width, after.height],
                "text_before": text_before,
                "text_after": saved[0].get_text().strip(),
                "dark_pixels_before": sum(value < 240 for value in before.samples),
                "dark_pixels_after": sum(value < 240 for value in after.samples),
                "pixels_identical": before.samples == after.samples,
                "path": path,
            }
            saved.save(path)
    #print(f'{angle=} {cropped=}:')
    #t = json.dumps(ret, indent='    ')
    #t = textwrap.indent(t, '    ')
    #print(t)
    return ret


def test_4394():
    print()
    info = dict()
    for angle in (0, 90, 180, 270):
        for cropped in False, True:
            ret = _test_4394_internal(angle, cropped)
            info.setdefault(angle, dict())[cropped] = ret
    for angle in sorted(info.keys()):
        for cropped in sorted(info[angle]):
            ret = info[angle][cropped]
            items = list()
            items.append(f'{angle=}')
            items.append(f'{cropped=}')
            items.append(f'visible: {ret["size_before"]} => {ret["size_after"]}')
            items.append(f'text-after: {"present" if ret["text_after"] else "empty"}')
            items.append(f'dark-pixels: {ret["dark_pixels_before"]} => {ret["dark_pixels_after"]}')
            items.append(f'pixels-identical: {ret["pixels_identical"]}')
            items.append(f'  {ret["path"]}')
            widths = 12, 16, 36, 24, 28, 28, None
            assert len(widths) == len(items), f'{len(widths)=} {len(items)=}'
            for item, width in zip(items, widths):
                if width:
                    item = item.rjust(width)
                sys.stdout.write(f' {item}')
            sys.stdout.write('\n')

