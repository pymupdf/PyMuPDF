import os
import pymupdf

def test_5122():
    script_dir = os.path.dirname(__file__)
    filename = os.path.join(script_dir, "resources", "test_5122.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    path=page.get_drawings()[0]
    rect_tl = path["items"][0][1].tl
    line_p1 = path["items"][1][1]
    assert line_p1 == rect_tl
