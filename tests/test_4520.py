import pymupdf


def test_4520():
    """Accept source pages without /Contents object in show_pdf_page."""
    tar = pymupdf.open()
    src = pymupdf.open()
    src.new_page()
    page = tar.new_page()
    xref = page.show_pdf_page(page.rect, src, 0)
    assert xref
