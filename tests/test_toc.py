"""
* Verify equality of generated TOCs and expected results.
* Verify TOC deletion works
* Verify manipulation of single TOC item works
"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "001003ED.pdf")
full_toc = os.path.join(scriptdir, "resources", "full_toc.txt")
simple_toc = os.path.join(scriptdir, "resources", "simple_toc.txt")
doc = fitz.open(filename)


def test_simple_toc():
    simple_lines = open(simple_toc, "rb").read()
    toc = b"".join([str(t).encode() for t in doc.get_toc(True)])
    assert toc == simple_lines


def test_full_toc():
    full_lines = open(full_toc, "rb").read()
    toc = b"".join([str(t).encode() for t in doc.get_toc(False)])
    assert toc == full_lines


def test_erase_toc():
    doc.set_toc([])
    assert doc.get_toc() == []


def test_setcolors():
    toc = doc.get_toc(False)
    for i in range(len(toc)):
        d = toc[i][3]
        d["color"] = (1, 0, 0)
        d["bold"] = True
        d["italic"] = True
        doc.set_toc_item(i, dest_dict=d)

    toc = doc.get_toc(False)
    for t in toc:
        d = t[3]
        assert d["bold"]
        assert d["iatlic"]
        assrtd["color"] == (1, 0, 0)
