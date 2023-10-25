"""
Tests for the Font class.
"""
import fitz
import os

def test_font1():
    text = "PyMuPDF"
    font = fitz.Font("helv")
    assert font.name == "Helvetica"
    tl = font.text_length(text, fontsize=20)
    cl = font.char_lengths(text, fontsize=20)
    assert len(text) == len(cl)
    assert abs(sum(cl) - tl) < fitz.EPSILON
    for i in range(len(cl)):
        assert cl[i] == font.glyph_advance(ord(text[i])) * 20
    font2 = fitz.Font(fontbuffer=font.buffer)
    assert font2.valid_codepoints() == font.valid_codepoints()


def test_font2():
    """Old and new length computation must be the same."""
    font = fitz.Font("helv")
    text = "PyMuPDF"
    assert font.text_length(text) == fitz.get_text_length(text)


def test_fontname():
    """Assert a valid PDF fontname."""
    doc = fitz.open()
    page = doc.new_page()
    assert page.insert_font()  # assert: a valid fontname works!
    detected = False  # preset indicator
    try:  # fontname check will fail first - don't need a font at all here
        page.insert_font(fontname="illegal/char", fontfile="unimportant")
    except ValueError as e:
        if str(e).startswith("bad fontname chars"):
            detected = True  # illegal fontname detected
    assert detected

def test_2608():
    if fitz.mupdf_version_tuple <= (1, 23, 4):
        print( f'Not running test_2608 because mupdf too old: {fitz.mupdf_version_tuple=}')
        return
    flags = (fitz.TEXT_DEHYPHENATE | fitz.TEXT_MEDIABOX_CLIP)
    with fitz.open(os.path.abspath(f'{__file__}/../resources/2201.00069.pdf')) as doc:
        page = doc[4]
        blocks = page.get_text_blocks(flags=flags)
        text = blocks[10][4]
        with open(os.path.abspath(f'{__file__}/../test_2608_out'), 'wb') as f:
            f.write(text.encode('utf8'))
        with open(os.path.abspath(f'{__file__}/../resources/test_2608_expected'), 'rb') as f:
            expected = f.read().decode('utf8')
        # Github windows x32 seems to insert \r characters; maybe something to
        # do with the Python installation's line endings settings.
        expected = expected.replace('\r', '')
        print(f'test_2608(): {text.encode("utf8")=}')
        print(f'test_2608(): {expected.encode("utf8")=}')
        assert text == expected
