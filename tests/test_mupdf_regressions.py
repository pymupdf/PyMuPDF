import pymupdf
import os
from gentle_compare import gentle_compare

scriptdir = os.path.abspath(os.path.dirname(__file__))


def test_707448():
    """Confirm page content cleaning does not destroy page appearance."""
    filename = os.path.join(scriptdir, "resources", "test-707448.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    words0 = page.get_text("words")
    page.clean_contents(sanitize=True)
    words1 = page.get_text("words")
    assert gentle_compare(words0, words1)


def test_707673():
    """Confirm page content cleaning does not destroy page appearance.

    Fails starting with MuPDF v1.23.9.

    Fixed in:
    commit 779b8234529cb82aa1e92826854c7bb98b19e44b (golden/master)
    """
    filename = os.path.join(scriptdir, "resources", "test-707673.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    words0 = page.get_text("words")
    page.clean_contents(sanitize=True)
    words1 = page.get_text("words")
    ok = gentle_compare(words0, words1)
    if pymupdf.mupdf_version_tuple >= (1, 24, 1):
        assert ok
    else:
        assert not ok


def test_707727():
    """Confirm page content cleaning does not destroy page appearance.

    MuPDF issue: https://bugs.ghostscript.com/show_bug.cgi?id=707727
    """
    filename = os.path.join(scriptdir, "resources", "test_3362.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    pix0 = page.get_pixmap()
    page.clean_contents(sanitize=True)
    page = doc.reload_page(page)  # required to prevent re-use
    pix1 = page.get_pixmap()
    ok = pix0.samples == pix1.samples
    if pymupdf.mupdf_version_tuple > (1, 24, 1):
        assert ok
    else:
        assert not ok
    if pymupdf.mupdf_version_tuple <= (1, 24, 1):
        # We expect warnings.
        wt = pymupdf.TOOLS.mupdf_warnings()
        print(f"{wt=}")
        assert wt


def test_707721():
    """Confirm text extraction works for nested MCID with Type 3 fonts.
    PyMuPDF issue https://github.com/pymupdf/PyMuPDF/issues/3357
    MuPDF issue: https://bugs.ghostscript.com/show_bug.cgi?id=707721
    """
    if pymupdf.mupdf_version_tuple < (1, 24, 2):
        print(
            "test_707721(): not running because MuPDF-{pymupdf.mupdf_version} known to hang."
        )
        return
    filename = os.path.join(scriptdir, "resources", "test_3357.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    ok = page.get_text()
    assert ok


def test_3376():
    """Check fix of MuPDF bug 707733.

    https://bugs.ghostscript.com/show_bug.cgi?id=707733
    PyMuPDF issue https://github.com/pymupdf/PyMuPDF/issues/3376

    Test file contains a redaction for the first 3 words: "Table of Contents".
    Test strategy:
    - extract all words (sorted)
    - apply redactions
    - extract words again
    - confirm: we now have 3 words less and remaining words are equal.
    """
    filename = os.path.join(scriptdir, "resources", "test_3376.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    words0 = page.get_text("words", sort=True)
    words0_s = words0[:3]  # first 3 words
    words0_e = words0[3:]  # remaining words
    assert " ".join([w[4] for w in words0_s]) == "Table of Contents"

    page.apply_redactions()

    words1 = page.get_text("words", sort=True)

    ok = gentle_compare(words0_e, words1)
    if pymupdf.mupdf_version_tuple >= (1, 24, 2):
        assert ok
    else:
        assert not ok
