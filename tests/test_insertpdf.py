"""
* Join multiple PDFs into a new one.
* Compare with stored earlier result:
    - must have identical object definitions
    - must have different trailers
"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
resources = os.path.join(scriptdir, "resources")
oldfile = os.path.join(resources, "joined.pdf")


def test_joining():
    """Join 4 files and compare result with previously stored one."""
    flist = ("1.pdf", "2.pdf", "3.pdf", "4.pdf")
    doc = fitz.open()
    for f in flist:
        fname = os.path.join(resources, f)
        x = fitz.open(fname)
        doc.insert_pdf(x, links=True, annots=True)
        x.close()

    tobytes = doc.tobytes(deflate=True, garbage=4)
    new_output = fitz.open("pdf", tobytes)
    old_output = fitz.open(oldfile)
    # result must have same objects, because MuPDF garbage
    # collection is a predictable process.
    assert old_output.xref_length() == new_output.xref_length()
    for xref in range(1, old_output.xref_length()):
        assert old_output.xref_object(xref, compressed=True) == new_output.xref_object(
            xref, compressed=True
        )
    assert old_output.xref_get_keys(-1) == new_output.xref_get_keys(-1)
    assert old_output.xref_get_key(-1, "ID") != new_output.xref_get_key(-1, "ID")
