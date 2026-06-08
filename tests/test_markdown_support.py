import pymupdf
import os


def test_archive_markdown():
    """Test Archive support."""
    if pymupdf.mupdf_version_tuple < (1, 28, 0):
        print("no testing on MuPDF < 1.28.0")
        return

    path = os.path.abspath(f"{__file__}/../../tests/resources")
    md = b"![](nur-ruhig.jpg)\n\n**A referenced image.**"
    md_doc = pymupdf.open(stream=md, filetype="md", archive=path)
    pdfdata = md_doc.convert_to_pdf()
    doc = pymupdf.open(stream=pdfdata)
    page = doc[0]
    images = page.get_image_info()
    assert len(images) == 1

def test_archive_links():
    """Create an internal and an external link and confirm
    that they are correctly converted to PDF links."""
    if pymupdf.mupdf_version_tuple < (1, 28, 0):
        print("no testing on MuPDF < 1.28.0")
        return

    md = """Some text containing an external [link](http://www.google.com) to Google.
    Now an internal link to a header in this document: [Some Header](#some-header). The header is here:

    <h2 id="some-header">Some Header</h2>

    Some text following the header.
    """
    md_doc = pymupdf.open(stream=md.encode(), filetype="md")
    pdfdata = md_doc.convert_to_pdf()
    doc = pymupdf.open(stream=pdfdata)
    page = doc[0]
    links=page.get_links()
    assert len(links) == 2
    assert links[0]["uri"] == "http://www.google.com"
    assert links[0]["kind"] == pymupdf.LINK_URI
    assert links[1]["kind"] == pymupdf.LINK_GOTO
