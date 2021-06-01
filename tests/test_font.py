"""
Tests for the Font class.
"""
import fitz


def test_font1():
    font = fitz.Font("cjk")
    assert font.name == "Droid Sans Fallback Regular"
    text = "PyMuPDF"
    tl = font.text_length(text, fontsize=20)
    cl = font.char_lengths(text, fontsize=20)
    assert len(text) == len(cl)
    assert abs(sum(cl) - tl) < fitz.EPSILON
    for i in range(len(cl)):
        assert cl[i] == font.glyph_advance(ord(text[i])) * 20
    font2 = fitz.Font(fontbuffer=font.buffer)
    assert font2.name == font.name
    assert len(font.valid_codepoints()) > 30000


def test_font2():
    """Old and new length computation must be the same."""
    font = fitz.Font("helv")
    text = "PyMuPDF"
    assert font.text_length(text) == fitz.get_text_length(text)