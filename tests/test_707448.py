import fitz
import os


def gentle_compare(w0, w1):
    """Compare lists of "words" extractions for approximate equality.

    * both lists must have same length
    * word items must contain same word strings
    * word rectangle coordinates must be approximately equal.

    The test strategy is based on extracting text before and after executing
    page cleaning. Cleaning must not influence the text extraction
    result - beyond some tolerance: rounding the coordinates to 4 decimal
    places must deliver equality.
    """
    round4 = lambda x: round(x, 4)
    word_count = len(w0)  # number of words
    assert word_count == len(w1)
    for i in range(word_count):
        if w0[i][4] != w1[i][4]:  # word strings must be the same
            print(f"word {i} mismatch")
            return False
        # compute rounded word rectangles
        r0 = tuple(map(round4, w0[i][:4]))
        r1 = tuple(map(round4, w1[i][:4]))
        if r0 != r1:
            print(f"rect {i} mismatch")
            print(r0)
            print(r1)
            return False
    return True


def test_707448():
    """Confirm page content cleaning does not destroy page appearance."""
    scriptdir = os.path.abspath(os.path.dirname(__file__))
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
    scriptdir = os.path.abspath(os.path.dirname(__file__))
    filename = os.path.join(scriptdir, "resources", "test-707673.pdf")
    doc = fitz.open(filename)
    page = doc[0]
    words0 = page.get_text("words")
    page.clean_contents(sanitize=True)
    words1 = page.get_text("words")
    ok = gentle_compare(words0, words1)
    if fitz.mupdf_version_tuple >= (1, 25):
        assert ok
    else:
        assert not ok
