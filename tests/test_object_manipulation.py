"""
Check some low-level PDF object manipulations:
1. Set page rotation and compare with string in object definition.
2. Set page rotation via string manipulation and compare with result of
   proper page property.
3. Read the PDF trailer and verify it has the keys "/Root", "/ID", etc.
"""
import fitz
import os

scriptdir = os.path.abspath(os.path.dirname(__file__))
resources = os.path.join(scriptdir, "resources")
filename = os.path.join(resources, "001003ED.pdf")


def test_rotation1():
    doc = fitz.open()
    page = doc.new_page()
    page.set_rotation(270)
    assert doc.xref_get_key(page.xref, "Rotate") == ("int", "270")


def test_rotation2():
    doc = fitz.open()
    page = doc.new_page()
    doc.xref_set_key(page.xref, "Rotate", "270")
    assert page.rotation == 270


def test_trailer():
    """Access PDF trailer information."""
    doc = fitz.open(filename)
    xreflen = doc.xref_length()
    _, xreflen_str = doc.xref_get_key(-1, "Size")
    assert xreflen == int(xreflen_str)
    trailer_keys = doc.xref_get_keys(-1)
    assert "ID" in trailer_keys
    assert "Root" in trailer_keys
