import pymupdf
import os
import util


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


def test_4918():
    '''
    By default this test does nothing, because it requires a rather large input document from:
        https://drive.google.com/file/d/1OkIq3XJuKiFfKDWBIcAk8_fLLjpNkuHQ/view?usp=sharing
    
    It's non-trivial to download from this url, so we only do anything if
    environment variable PYMUPDF_TEST_4918_PATH is set to local path of the
    input document.
    
    As of 2026-06-04 this passes with mupdf master, but segvs with current
    pymupdf release 1.27.2.3.
    '''
    PYMUPDF_TEST_4918_PATH = os.environ.get('PYMUPDF_TEST_4918_PATH')
    if not PYMUPDF_TEST_4918_PATH :
        print(f'test_4918(): Doing nothing because {PYMUPDF_TEST_4918_PATH=}.')
        return
    path = PYMUPDF_TEST_4918_PATH
    print(f'{path=}')
    with pymupdf.open(path) as document:
        document.rewrite_images(dpi_threshold=150, dpi_target=100, quality=50)
