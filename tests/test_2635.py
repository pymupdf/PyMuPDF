def test_2635():
    """Rendering a page before and after cleaning it should yield the same pixmap."""
    doc = fitz.open(f"{scriptdir}/resources/test_2635.pdf")
    page = doc[0]
    pix1 = page.get_pixmap()  # pixmap before cleaning

    page.clean_contents()  # clean page
    pix2 = page.get_pixmap()  # pixmap after cleaning
    assert pix1.samples == pix2.samples  # assert equality
