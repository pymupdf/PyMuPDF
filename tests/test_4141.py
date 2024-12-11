import pymupdf

import os.path


def test_4141():
    """survive missing /Resources object in a number of cases."""
    path = os.path.abspath(f"{__file__}/../../tests/resources/test_4141.pdf")
    doc = pymupdf.open(path)
    page = doc[0]
    # make sure the right test file
    assert doc.xref_get_key(page.xref, "Resources") == ("null", "null")
    page.insert_htmlbox((100, 100, 200, 200), "Hallo")  # will fail without the fix
    doc.close()
    doc = pymupdf.open(doc.name)
    page = doc[0]
    tw = pymupdf.TextWriter(page.rect)
    tw.append((100, 100), "Hallo")
    tw.write_text(page)  # will fail without the fix
