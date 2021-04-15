"""
Check low-level PDF object manipulation:
1. Set page rotation and compare with string in object definition.
2. Set page rotation via string manipulation and compare with result of
   proper page.property.
"""
import fitz


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
