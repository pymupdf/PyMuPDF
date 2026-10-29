"""
Tests for Document.convert_to_pdf() with page subsets.
"""

import io
import os
import platform
import sys

import pymupdf


def _sized_pdf():
    """Return a 4-page PDF whose page widths are 100, 200, 300 and 400."""
    doc = pymupdf.open()
    for i in range(4):
        doc.new_page(width=100 * (i + 1), height=500)
    return doc


def _widths(pdfbytes):
    with pymupdf.open("pdf", pdfbytes) as doc:
        return [page.rect.width for page in doc]


def test_convert_to_pdf_page_subset():
    doc = _sized_pdf()
    assert _widths(doc.convert_to_pdf()) == [100, 200, 300, 400]
    assert _widths(doc.convert_to_pdf(from_page=0, to_page=2)) == [100, 200, 300]
    assert _widths(doc.convert_to_pdf(from_page=1, to_page=1)) == [200]
    assert _widths(doc.convert_to_pdf(from_page=2, to_page=3)) == [300, 400]
    assert _widths(doc.convert_to_pdf(from_page=3, to_page=1)) == [400, 300, 200]


def test_convert_to_pdf_image_frame():
    # Each frame of a multi-frame TIFF can be converted on its own.
    if platform.system() == 'Windows' and int.bit_length(sys.maxsize+1) == 32:
        # module `PIL` not available - see
        # conftest.py:install_required_packages for details.
        return
    if os.environ.get('PYODIDE_ROOT'):
        print('test_convert_to_pdf_image_frame(): not running on Pyodide - No module named \'PIL\'.')
        return
    import PIL.Image

    frames = [PIL.Image.new("L", (24 * (i + 1), 30), 90) for i in range(3)]
    buffer = io.BytesIO()
    frames[0].save(buffer, format="TIFF", save_all=True, append_images=frames[1:])
    with pymupdf.open(stream=buffer.getvalue(), filetype="tiff") as img:
        assert img.page_count == 3
        for pno in range(img.page_count):
            with pymupdf.open("pdf", img.convert_to_pdf(from_page=pno, to_page=pno)) as pdf:
                assert pdf.page_count == 1
                assert pdf[0].rect == img[pno].rect


def test_convert_to_pdf_page_subset_links():
    doc = _sized_pdf()
    # page 1 links to page 3 (converted) and to page 0 (not converted)
    doc[1].insert_link({"kind": pymupdf.LINK_GOTO, "from": pymupdf.Rect(10, 10, 50, 50), "page": 3})
    doc[1].insert_link({"kind": pymupdf.LINK_GOTO, "from": pymupdf.Rect(10, 60, 50, 100), "page": 0})
    doc[2].insert_link({"kind": pymupdf.LINK_URI, "from": pymupdf.Rect(10, 10, 50, 50), "uri": "https://pymupdf.io/"})
    src = pymupdf.open("pdf", doc.tobytes())  # links resolve after a save
    with pymupdf.open("pdf", src.convert_to_pdf(from_page=1, to_page=3)) as pdf:
        links0 = pdf[0].get_links()
        assert [link["kind"] for link in links0] == [pymupdf.LINK_GOTO]
        assert links0[0]["page"] == 2
        links1 = pdf[1].get_links()
        assert [link.get("uri") for link in links1] == ["https://pymupdf.io/"]
        assert pdf[2].get_links() == []
