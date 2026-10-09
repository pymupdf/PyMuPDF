import io
import pymupdf
import os
import re
import util

import PIL.Image


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


def test_5164():

    def colorspace_components(doc, xref):
        kind, value = doc.xref_get_key(xref, "ColorSpace")
        if kind == "name":
            return {"/DeviceGray": 1, "/DeviceRGB": 3, "/DeviceCMYK": 4}[value]
        icc = re.search(r"/ICCBased (\d+) 0 R", value if kind == "array" else doc.xref_object(int(value.split()[0])))
        return int(doc.xref_get_key(int(icc.group(1)), "N")[1])

    num_errors = 0
    for label, kwargs in (("defaults", {}), ("downsampling", {"dpi_threshold": 100, "dpi_target": 72})):
        print(f"\nrewrite_images(quality=75, {', '.join(f'{k}={v}' for k, v in kwargs.items())})")
        for mode, fmt in (("L", "PNG"), ("L", "JPEG"), ("CMYK", "JPEG"), ("RGB", "PNG")):
            buf = io.BytesIO()
            PIL.Image.linear_gradient("L").resize((1240, 1754)).convert(mode).save(buf, format=fmt)

            doc = pymupdf.open()
            page = doc.new_page(width=595, height=842)
            page.insert_image(page.rect, stream=buf.getvalue())
            doc.rewrite_images(quality=75, **kwargs)

            xref = page.get_images(full=True)[0][0]
            jpeg = len(PIL.Image.open(io.BytesIO(doc.xref_stream_raw(xref))).getbands())
            declared = colorspace_components(doc, xref)
            if jpeg == declared:
                verdict = "ok"
            else:
                verdict = "MISMATCH"
                num_errors += 1
            verdict = "ok" if jpeg == declared else "MISMATCH"
            print(f"  {mode:4} {fmt:4}: JPEG has {jpeg} components, /ColorSpace declares {declared}  {verdict}")
            path_out = os.path.normpath(f'{__file__}/../../tests/test_5164_out.pdf')
            doc.save(path_out)
    print(f'{num_errors=}')
    if pymupdf.mupdf_version_tuple >= (1, 28, 6):
        assert not num_errors
    else:
        assert num_errors == 5
