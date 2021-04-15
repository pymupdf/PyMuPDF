"""
1. Read metadata and compare with stored expected result.
2. Erase metadata and ensure object has indeed been emptied.
"""
import json
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "001003ED.pdf")
metafile = os.path.join(scriptdir, "resources", "metadata.txt")
doc = fitz.open(filename)


def test_metadata():
    assert json.dumps(doc.metadata) == open(metafile).read()


def test_erase_meta():
    doc.set_metadata({})
    info_str = doc.xref_get_key(-1, "Info")[1].split()[0]
    info_xref = int(info_str)
    assert doc.xref_object(info_xref, compressed=True) == "<<>>"
