"""
1. Read metadata and compare with stored expected result.
2. Erase metadata and assert object has indeed been deleted.
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
    # Check PDF trailer and assert that there is no more /Info object
    # or is set to "null".
    statement1 = doc.xref_get_key(-1, "Info")[1] == "null"
    statement2 = "Info" not in doc.xref_get_keys(-1)
    assert statement2 or statement1
