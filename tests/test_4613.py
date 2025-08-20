import pymupdf
import string


def test_4613():
    text = " ".join([string.ascii_lowercase + " " + string.ascii_uppercase] * 3)
    story = pymupdf.Story(text)
    doc = pymupdf.open()
    page = doc.new_page()
    rect = pymupdf.Rect(10, 10, 100, 100)
    rc1 = page.insert_htmlbox(rect, story)

    new_text = page.get_text("text", clip=rect).replace("\n", " ")
    assert text.strip() == new_text.strip()
