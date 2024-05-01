import os
import pymupdf
from gentle_compare import gentle_compare

scriptdir = os.path.dirname(__file__)


def test_remove_rotation():
    """Remove rotation verifying identical appearance and text."""
    filename = os.path.join(scriptdir, "resources", "test-2812.pdf")
    doc = pymupdf.open(filename)

    # We always create fresh pages to avoid false positves from cache content.
    # Text on these pages consists of pairwise different strings, sorting by
    # these strings must therefore yield identical bounding boxes.
    for i in range(1, doc.page_count):
        assert doc[i].rotation  # must be a rotated page
        pix0 = doc[i].get_pixmap()  # make image
        words0 = []
        for w in doc[i].get_text("words"):
            words0.append(list(pymupdf.Rect(w[:4]) * doc[i].rotation_matrix) + [w[4]])
        words0.sort(key=lambda w: w[4])  # sort by word strings
        # derotate page and confirm nothing else has changed
        doc[i].remove_rotation()
        assert doc[i].rotation == 0
        pix1 = doc[i].get_pixmap()
        words1 = doc[i].get_text("words")
        words1.sort(key=lambda w: w[4])  # sort by word strings
        assert pix1.digest == pix0.digest, f"{pix1.digest}/{pix0.digest}"
        assert gentle_compare(words0, words1)
