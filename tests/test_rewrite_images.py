import pymupdf
import os

scriptdir = os.path.dirname(__file__)


def test_rewrite_images():
    """Example for decreasing file size by more than 30%."""
    filename = os.path.join(scriptdir, "resources", "test-rewrite-images.pdf")
    doc = pymupdf.open(filename)
    size0 = os.path.getsize(doc.name)
    doc.rewrite_images(dpi_threshold=100, dpi_target=72, quality=33)
    data = doc.tobytes(garbage=3, deflate=True)
    size1 = len(data)
    assert (1 - (size1 / size0)) > 0.3
