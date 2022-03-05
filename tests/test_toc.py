"""
* Verify equality of generated TOCs and expected results.
* Verify TOC deletion works
* Verify manipulation of single TOC item works
* Verify stability against circular TOC items
"""
import os
import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "001003ED.pdf")
filename2 = os.path.join(scriptdir, "resources", "2.pdf")
circular = os.path.join(scriptdir, "resources", "circular-toc.pdf")
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


def test_replace_toc():
    toc = doc.get_toc(False)
    doc.set_toc(toc)


def test_setcolors():
    doc = fitz.open(filename2)
    toc = doc.get_toc(False)
    for i in range(len(toc)):
        d = toc[i][3]
        d["color"] = (1, 0, 0)
        d["bold"] = True
        d["italic"] = True
        doc.set_toc_item(i, dest_dict=d)

    toc2 = doc.get_toc(False)
    assert len(toc2) == len(toc)

    for t in toc2:
        d = t[3]
        assert d["bold"]
        assert d["italic"]
        assert d["color"] == (1, 0, 0)


def test_circular():
    """The test file contains circular bookmarks."""
    doc = fitz.open(circular)
    toc = doc.get_toc(False)  # this must not loop
