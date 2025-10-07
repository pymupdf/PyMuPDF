import pymupdf
import os

def test_4716():
    """Confirm that ZERO WIDTH JOINER will never start a word."""
    script_dir = os.path.dirname(__file__)
    filename = os.path.join(script_dir, "resources", "test_4716.pdf")
    doc = pymupdf.open(filename)
    expected = set(["+25.00", "Любимый", "-10.00"])
    word_text = set()
    for page in doc:
        words = page.get_text("words")
        for w in words:
            word_text.add(w[4])
    assert word_text == expected
