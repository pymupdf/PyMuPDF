import pymupdf
import pathlib
from pymupdf import Point


def test_5044():
    file_in = (
        pathlib.Path(__file__).resolve().parent.parent
        / "tests"
        / "resources"
        / "test_5044.pdf"
    )
    doc = pymupdf.open(file_in)
    toc = doc.get_toc(False)
    link = toc[0][-1]
    expect_link = {
        "kind": 1,
        "xref": 11,
        "page": 0,
        "to": Point(0.0, 0.89001467),
        "zoom": 0.0,
        "color": (0.0, 0.0, 0.0),
    }
    assert link == expect_link
