import fitz
import os

scriptdir = os.path.abspath(os.path.dirname(__file__))


def gentle_compare(w0, w1):
    """Compare lists of "words" extractions for approximate equality.

    * both lists must have same length
    * word items must contain same word strings
    * word rectangle coordinates must be approximately equal.

    The test strategy is based on extracting text before and after executing
    page cleaning. Cleaning must not influence the text extraction
    result - beyond some tolerance: the Euclidean norm of the difference
    vector of before and after word boundary boxes must not exceed 1E-3.
    """
    tolerance = 1e-3
    word_count = len(w0)  # number of words
    assert word_count == len(w1)
    for i in range(word_count):
        if w0[i][4] != w1[i][4]:  # word strings must be the same
            print(f"word {i} mismatch")
            return False
        # compute rounded word rectangles
        r0 = fitz.Rect(w0[i][:4])
        r1 = fitz.Rect(w1[i][:4])
        delta = (r1 - r0).norm()  # norm of difference vector
        if delta > tolerance:
            print(f"word {i}: rectangle mismatch {delta}")
            return False
    return True


def test_707448():
    """Confirm page content cleaning does not destroy page appearance."""
    filename = os.path.join(scriptdir, "resources", "test-707448.pdf")
    doc = fitz.open(filename)
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
    doc = fitz.open(filename)
    page = doc[0]
    words0 = page.get_text("words")
    page.clean_contents(sanitize=True)
    words1 = page.get_text("words")
    ok = gentle_compare(words0, words1)
    if fitz.mupdf_version_tuple >= (1, 24, 1):
        assert ok
    else:
        assert not ok


def test_707727():
    """Confirm page content cleaning does not destroy page appearance.

    MuPDF issue: https://bugs.ghostscript.com/show_bug.cgi?id=707727
    """
    filename = os.path.join(scriptdir, "resources", "test_3362.pdf")
    doc = fitz.open(filename)
    page = doc[0]
    words0 = page.get_text("words")
    page.clean_contents(sanitize=True)
    words1 = page.get_text("words")
    ok = gentle_compare(words0, words1)
    if fitz.mupdf_version_tuple >= (1, 24, 1):
        assert ok
    else:
        assert not ok


def test_707721():
    """Confirm text extraction works for nested MCID with Type 3 fonts.
    PyMuPDF issue https://github.com/pymupdf/PyMuPDF/issues/3357
    MuPDF issue: https://bugs.ghostscript.com/show_bug.cgi?id=707721
    """
    filename = os.path.join(scriptdir, "resources", "test_3357.pdf")
    doc = fitz.open(filename)
    page = doc[0]
    ok = page.get_text()
    if fitz.mupdf_version_tuple >= (1, 24, 1):
        assert ok
    else:
        assert not ok
