"""
* Join multiple PDFs into a new one.
* Compare to stored earlier result:
    - must be same length
    - must differ b/o different ID fields
"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
resources = os.path.join(scriptdir, "resources")
oldfile = os.path.join(resources, "joined.pdf")


def test_joining():
    flist = ("1.pdf", "2.pdf", "3.pdf", "4.pdf")
    doc = fitz.open()
    for f in flist:
        fname = os.path.join(resources, f)
        x = fitz.open(fname)
        doc.insert_pdf(x, links=True, annots=True)
        x.close()

    output = doc.tobytes(deflate=True, garbage=4)
    old_output = open(oldfile, "rb").read()
    assert len(output) == len(old_output)
    assert output != old_output
