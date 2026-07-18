import pymupdf
import pathlib


def test_4670():
    """Remove hidden text using redaction annotations.

    The page only contains hidden text, which should be removed
    entirely after scrubbing the document.
    """
    filename = (
        pathlib.Path(__file__).resolve().parent.parent
        / "tests"
        / "resources"
        / "test_4670.pdf"
    )
    doc = pymupdf.open(filename)
    page = doc[0]
    old_text = page.get_text()
    assert old_text
    doc.scrub(hidden_text=True)
    new_text = page.get_text()
    assert not new_text
