import pymupdf

def test_5214_read():
    """Test reading non-ASCII page labels."""
    doc = pymupdf.open()
    for _ in range(4):
        doc.new_page()
    nums = (
        "[0<</S/D/P(Part 1/2-)>> 1<</S/D/P(Sec \\(1\\)-)>>"
        " 2<</S/r/P(Anh\\344-)>> 3<</S/D/P<FEFF03A9002D>>>]"
    )
    doc.xref_set_key(doc.pdf_catalog(), "PageLabels", f"<</Nums{nums}>>")
    doc = pymupdf.open("pdf", doc.tobytes())
    expected = ["Part 1/2-1", "Sec (1)-1", "Anhä-i", "Ω-1"]
    got = [doc[i].get_label() for i in range(4)]
    prefixes = [d["prefix"] for d in doc.get_page_labels()]
    ok = got == expected and prefixes == [e.rsplit("-", 1)[0] + "-" for e in expected]
    assert ok

def test_5214_write():
    """Test writing non-ASCII page labels."""
    doc = pymupdf.open()
    for _ in range(2):
        doc.new_page()
    doc.set_page_labels(
        [
            {"startpage": 0, "prefix": "A/B-", "style": "D"},
            {"startpage": 1, "prefix": "Anh. ä-", "style": "D"},
        ]
    )
    doc = pymupdf.open("pdf", doc.tobytes())
    assert [doc[i].get_label() for i in range(2)] == ["A/B-1", "Anh. ä-1"]

