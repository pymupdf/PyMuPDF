import pymupdf


def test_4520():
    """Accept source pages without /Contents object in show_pdf_page."""
    vsn_tuple = tuple(map(int, pymupdf.__version__.split(".")))
    tar = pymupdf.open()
    src = pymupdf.open()
    src.new_page()
    page = tar.new_page()
    try:
        assert page.show_pdf_page(page.rect, src, 0)
        rc = True
    except Exception as e:
        rc = False
    if vsn_tuple < (1, 26, 0):
        assert rc is False
    else:
        assert rc is True
