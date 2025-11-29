import pymupdf
from pathlib import Path


def test_4141():
    """Survive missing /Resources object in multiple situations."""

    # Resolve the test file path
    test_pdf = Path(__file__).resolve().parent.parent / "tests" / "resources" / "test_4141.pdf"
    assert test_pdf.exists(), f"Missing test file: {test_pdf}"

    # Case 1: Insert HTML box
    with pymupdf.open(test_pdf) as doc:
        page = doc[0]

        # Ensure we are using the correct test file
        assert doc.xref_get_key(page.xref, "Resources") == ("null", "null")

        # Should not fail after the fix
        page.insert_htmlbox((100, 100, 200, 200), "Hallo")

    # Case 2: TextWriter operations after reopen
    with pymupdf.open(test_pdf) as doc:
        page = doc[0]
        tw = pymupdf.TextWriter(page.rect)
        tw.append((100, 100), "Hallo")
        tw.write_text(page)  # Should also not fail
