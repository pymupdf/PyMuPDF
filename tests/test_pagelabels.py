"""
Define some page labels in a PDF.
Check success in various aspects.
"""

import pymupdf


def make_doc():
    """Makes a PDF with 10 pages."""
    doc = pymupdf.open()
    for i in range(10):
        page = doc.new_page()
    return doc


def make_labels():
    """Return page label range rules.
    - Rule 1: labels like "A-n", page 0 is first and has "A-1".
    - Rule 2: labels as capital Roman numbers, page 4 is first and has "I".
    """
    return [
        {"startpage": 0, "prefix": "A-", "style": "D", "firstpagenum": 1},
        {"startpage": 4, "prefix": "", "style": "R", "firstpagenum": 1},
    ]


def test_setlabels():
    """Check setting and inquiring page labels.
    - Make a PDF with 10 pages
    - Label pages
    - Inquire labels of pages
    - Get list of page numbers for a given label.
    """
    doc = make_doc()
    doc.set_page_labels(make_labels())
    page_labels = [p.get_label() for p in doc]
    answer = ["A-1", "A-2", "A-3", "A-4", "I", "II", "III", "IV", "V", "VI"]
    assert page_labels == answer, f"page_labels={page_labels}"
    assert doc.get_page_numbers("V") == [8]
    assert doc.get_page_labels() == make_labels()


def test_labels_styleA():
    """Test correct indexing for styles "a", "A"."""
    doc = make_doc()
    labels = [
        {"startpage": 0, "prefix": "", "style": "a", "firstpagenum": 1},
        {"startpage": 5, "prefix": "", "style": "A", "firstpagenum": 1},
    ]
    doc.set_page_labels(labels)
    pdfdata = doc.tobytes()
    doc.close()
    doc = pymupdf.open("pdf", pdfdata)
    answer = ["a", "b", "c", "d", "e", "A", "B", "C", "D", "E"]
    page_labels = [page.get_label() for page in doc]
    assert page_labels == answer
    assert doc.get_page_labels() == labels
