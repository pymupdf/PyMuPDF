import pymupdf

import os.path


def test_linebreaks():
    """Test avoidance of linebreaks."""
    path = os.path.abspath(f"{__file__}/../../tests/resources/test-linebreaks.pdf")
    doc = pymupdf.open(path)
    page = doc[0]
    tp = page.get_textpage(flags=pymupdf.TEXTFLAGS_WORDS)
    word_count = len(page.get_text("words", textpage=tp))
    line_count1 = len(page.get_text(textpage=tp).splitlines())
    line_count2 = len(page.get_text(sort=True, textpage=tp).splitlines())
    assert word_count == line_count1
    assert line_count2 < line_count1 / 2
