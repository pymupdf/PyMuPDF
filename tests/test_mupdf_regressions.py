import fitz
import os

scriptdir = os.path.abspath(os.path.dirname(__file__))


def gentle_compare(w0, w1):
    """Check lists of "words" extractions for approximate equality.

    * both lists must have same length
    * word items must contain same word strings
    * word rectangles must be approximately equal
    """
    tolerance = 1e-3  # maximum (Euclidean) norm of difference rectangle
    word_count = len(w0)  # number of words
    if word_count != len(w1):
        print(f"different number of words: {word_count}/{len(w1)}")
        return False
    for i in range(word_count):
        if w0[i][4] != w1[i][4]:  # word strings must be the same
            print(f"word {i} mismatch")
            return False
        r0 = fitz.Rect(w0[i][:4])  # rect of first word
        r1 = fitz.Rect(w1[i][:4])  # rect of second word
        delta = (r1 - r0).norm()  # norm of difference rectangle
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
    if fitz.mupdf_version_tuple <= (1, 24, 1):
        # We expect warnings.
        wt = fitz.TOOLS.mupdf_warnings()
        print(f'{wt=}')
        assert wt


def test_707721():
    """Confirm text extraction works for nested MCID with Type 3 fonts.
    PyMuPDF issue https://github.com/pymupdf/PyMuPDF/issues/3357
    MuPDF issue: https://bugs.ghostscript.com/show_bug.cgi?id=707721
    """
    if fitz.mupdf_version_tuple < (1, 24, 2):
        print('test_707721(): not running because MuPDF-{fitz.mupdf_version} known to hang.')
        return
    filename = os.path.join(scriptdir, "resources", "test_3357.pdf")
    doc = fitz.open(filename)
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
    doc = fitz.open(filename)
    page = doc[0]
    words0 = page.get_text("words", sort=True)
    words0_s = words0[:3]  # first 3 words
    words0_e = words0[3:]  # remaining words
    assert " ".join([w[4] for w in words0_s]) == "Table of Contents"

    page.apply_redactions()

    words1 = page.get_text("words", sort=True)

    ok = gentle_compare(words0_e, words1)
    if fitz.mupdf_version_tuple >= (1, 24, 2):
        assert ok
    else:
        assert not ok
