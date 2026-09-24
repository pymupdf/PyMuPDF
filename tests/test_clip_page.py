"""
Test Page method clip_to_rect.
"""

import os
import pymupdf


def test_clip():
    """
    Clip a Page to a rectangle and confirm that no text has survived
    that is completely outside the rectangle..
    """
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    rect = pymupdf.Rect(200, 200, 400, 500)
    filename = os.path.join(scriptdir, "resources", "v110-changes.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    page.clip_to_rect(rect)  # clip the page to the rectangle
    # capture font warning message of MuPDF
    if pymupdf.mupdf_version_tuple < (1, 27):
        assert pymupdf.TOOLS.mupdf_warnings() == "bogus font ascent/descent values (0 / 0)"
    # extract all text characters and assert that each one
    # has a non-empty intersection with the rectangle.
    chars = [
        c
        for b in page.get_text("rawdict")["blocks"]
        for l in b["lines"]
        for s in l["spans"]
        for c in s["chars"]
    ]
    for char in chars:
        bbox = pymupdf.Rect(char["bbox"])
        if bbox.is_empty:
            continue
        assert bbox.intersects(
            rect
        ), f"Character '{char['c']}' at {bbox} is outside of {rect}."


def test_5108():
    print()
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_5108.pdf')
    def clipped_content(i, clip):
        with pymupdf.open(path) as document:
            page = document[0]
            page.clip_to_rect(clip)
            with pymupdf.open(stream=document.tobytes(garbage=3, clean=True)) as document2:
                page = document2[0]
                ret = b''.join(document2.xref_stream(x) for x in page.get_contents())
                page.draw_rect(clip, (1, 0, 0))
                document2.save(f'{path}.out.{i}.pdf')
                return ret
    num_errors = 0
    for i, (sh_kept_expected, label, clip) in enumerate([
            ( True, 'whole page       ', pymupdf.Rect(0, 0, 400, 400)),
            ( True, 'right half       ', pymupdf.Rect(200, 0, 400, 400)),
            ( True, 'page inset by 1pt', pymupdf.Rect(1, 1, 399, 399)),
            (False, '1x1 at PDF origin', pymupdf.Rect(0, 399, 1, 400)),
            (False, '                 ', pymupdf.Rect(0, 0, 10, 10)),
            (False, '                 ', pymupdf.Rect(0, 2, 10, 7)),
            ( True, 'Partial          ', pymupdf.Rect(100, 100, 300, 300)),
            ]):
        content = clipped_content(i, clip)
        sh_kept = (b'sh' in content)
        if sh_kept !=sh_kept_expected:
            num_errors += 1
        print(f'    {label} -> {sh_kept=} {content!r}')
    print(f'{num_errors=}')
    if pymupdf.mupdf_version_tuple >= (1, 28, 5):
        assert num_errors == 0
    else:
        assert num_errors


        
    
