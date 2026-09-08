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
    for i, (label, clip) in enumerate([
            ('whole page                            ', pymupdf.Rect(0, 0, 400, 400)),
            ('right half (holds shading)            ', pymupdf.Rect(200, 0, 400, 400)),
            ('page inset by 1pt                     ', pymupdf.Rect(1, 1, 399, 399)),
            ('1x1 at PDF origin, no shading in it   ', pymupdf.Rect(0, 399, 1, 400)),
            ('                                      ', pymupdf.Rect(0, 0, 10, 10)),
            ('                                      ', pymupdf.Rect(0, 2, 10, 7)),
            ]):
        content = clipped_content(i, clip)
        sh_kept = str(b'sh' in content)
        print(f'    {label} -> {sh_kept=:5s} {content!r}')    


        
    
