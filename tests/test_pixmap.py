"""
Pixmap tests
* make pixmap of a page and assert bbox size
* make pixmap from a PDF xref and compare with extracted image
* pixmap from file and from binary image and compare
"""

import pymupdf
import gentle_compare

import os
import platform
import subprocess
import sys
import tempfile
import pytest
import textwrap
import time


scriptdir = os.path.abspath(os.path.dirname(__file__))
epub = os.path.join(scriptdir, "resources", "Bezier.epub")
pdf = os.path.join(scriptdir, "resources", "001003ED.pdf")
imgfile = os.path.join(scriptdir, "resources", "nur-ruhig.jpg")


def test_pagepixmap():
    # pixmap from an EPUB page
    doc = pymupdf.open(epub)
    page = doc[0]
    pix = page.get_pixmap()
    assert pix.irect == page.rect.irect
    pix = page.get_pixmap(alpha=True)
    assert pix.alpha
    assert pix.n == pix.colorspace.n + pix.alpha


def test_pdfpixmap():
    # pixmap from xref in a PDF
    doc = pymupdf.open(pdf)
    # take first image item of first page
    img = doc.get_page_images(0)[0]
    # make pixmap of it
    pix = pymupdf.Pixmap(doc, img[0])
    # assert pixmap properties
    assert pix.width == img[2]
    assert pix.height == img[3]
    # extract image and compare metadata
    extractimg = doc.extract_image(img[0])
    assert extractimg["width"] == pix.width
    assert extractimg["height"] == pix.height


def test_filepixmap():
    # pixmaps from file and from stream
    # should lead to same result
    pix1 = pymupdf.Pixmap(imgfile)
    stream = open(imgfile, "rb").read()
    pix2 = pymupdf.Pixmap(stream)
    assert repr(pix1) == repr(pix2)
    assert pix1.digest == pix2.digest


def test_pilsave():
    # pixmaps from file then save to pillow image
    # make pixmap from this and confirm equality
    try:
        pix1 = pymupdf.Pixmap(imgfile)
        stream = pix1.pil_tobytes("JPEG")
        pix2 = pymupdf.Pixmap(stream)
        assert repr(pix1) == repr(pix2)
    except ModuleNotFoundError:
        assert platform.system() == 'Windows' and sys.maxsize == 2**31 - 1


def test_save(tmpdir):
    # pixmaps from file then save to image
    # make pixmap from this and confirm equality
    pix1 = pymupdf.Pixmap(imgfile)
    outfile = os.path.join(tmpdir, "foo.png")
    pix1.save(outfile, output="png")
    # read it back
    pix2 = pymupdf.Pixmap(outfile)
    assert repr(pix1) == repr(pix2)


def test_setalpha():
    # pixmap from JPEG file, then add an alpha channel
    # with 30% transparency
    pix1 = pymupdf.Pixmap(imgfile)
    opa = int(255 * 0.3)  # corresponding to 30% transparency
    alphas = [opa] * (pix1.width * pix1.height)
    alphas = bytearray(alphas)
    pix2 = pymupdf.Pixmap(pix1, 1)  # add alpha channel
    pix2.set_alpha(alphas)  # make image 30% transparent
    samples = pix2.samples  # copy of samples
    # confirm correct the alpha bytes
    t = bytearray([samples[i] for i in range(3, len(samples), 4)])
    assert t == alphas

def test_color_count():
    '''
    This is known to fail if MuPDF is built without PyMuPDF's custom config.h,
    e.g. in Linux system installs.
    '''
    pm = pymupdf.Pixmap(imgfile)
    assert pm.color_count() == 40624

def test_memoryview():
    pm = pymupdf.Pixmap(imgfile)
    samples = pm.samples_mv
    assert isinstance( samples, memoryview)
    print( f'samples={samples} samples.itemsize={samples.itemsize} samples.nbytes={samples.nbytes} samples.ndim={samples.ndim} samples.shape={samples.shape} samples.strides={samples.strides}')
    assert samples.itemsize == 1
    assert samples.nbytes == 659817
    assert samples.ndim == 1
    assert samples.shape == (659817,)
    assert samples.strides == (1,)
    
    color = pm.pixel( 100, 100)
    print( f'color={color}')
    assert color == (83, 66, 40)

def test_samples_ptr():
    pm = pymupdf.Pixmap(imgfile)
    samples = pm.samples_ptr
    print( f'samples={samples}')
    assert isinstance( samples, int)

def test_2369():

    width, height = 13, 37
    image = pymupdf.Pixmap(pymupdf.csGRAY, width, height, b"\x00" * (width * height), False)

    with pymupdf.Document(stream=image.tobytes(output="pam"), filetype="pam") as doc:
        test_pdf_bytes = doc.convert_to_pdf()
    
    with pymupdf.Document(stream=test_pdf_bytes) as doc:
        page = doc[0]
        img_xref = page.get_images()[0][0]
        img = doc.extract_image(img_xref)
        img_bytes = img["image"]
        pymupdf.Pixmap(img_bytes)

def test_page_idx_int():
    doc = pymupdf.open(pdf)
    with pytest.raises(AssertionError):
        doc["0"]
    assert doc[0]
    assert doc[(0,0)]

def test_fz_write_pixmap_as_jpeg():
    width, height = 13, 37
    image = pymupdf.Pixmap(pymupdf.csGRAY, width, height, b"\x00" * (width * height), False)

    with pymupdf.Document(stream=image.tobytes(output="jpeg"), filetype="jpeg") as doc:
        test_pdf_bytes = doc.convert_to_pdf()

def test_3020():
    pm = pymupdf.Pixmap(imgfile)
    pm2 = pymupdf.Pixmap(pm, 20, 30, None)
    pm3 = pymupdf.Pixmap(pymupdf.csGRAY, pm)
    pm4 = pymupdf.Pixmap(pm, pm3)

def test_3050():
    '''
    This is known to fail if MuPDF is built without it's default third-party
    libraries, e.g. in Linux system installs.
    '''
    path = os.path.normpath(f'{__file__}/../../tests/resources/001003ED.pdf')
    with pymupdf.open(path) as pdf_file:
        page_no = 0
        page = pdf_file[page_no]
        zoom_x = 4.0
        zoom_y = 4.0
        matrix = pymupdf.Matrix(zoom_x, zoom_y)
        pix = page.get_pixmap(matrix=matrix)
        path_out = os.path.normpath(f'{__file__}/../../tests/test_3050_out.png')
        pix.save(path_out)
        print(f'{pix.width=} {pix.height=}')
        def product(x, y):
            for yy in y:
                for xx in x:
                    yield (xx, yy)
        n = 0
        # We use a small subset of the image because non-optimised rebase gets
        # very slow.
        for pos in product(range(100), range(100)):
            if sum(pix.pixel(pos[0], pos[1])) >= 600:
                n += 1
                pix.set_pixel(pos[0], pos[1], (255, 255, 255))
        path_out2 = os.path.normpath(f'{__file__}/../../tests/test_3050_out2.png')
        pix.save(path_out2)
        path_expected = os.path.normpath(f'{__file__}/../../tests/resources/test_3050_expected.png')
        rms = gentle_compare.pixmaps_rms(path_expected, path_out2)
        print(f'{rms=}')
        if pymupdf.mupdf_version_tuple < (1, 26):
            # Slight differences in rendering from fix for mupdf bug 708274.
            assert rms < 0.2
        else:
            assert rms == 0
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == 'PDF stream Length incorrect'

def test_3058():
    doc = pymupdf.Document(os.path.abspath(f'{__file__}/../../tests/resources/test_3058.pdf'))
    images = doc[0].get_images(full=True)
    pix = pymupdf.Pixmap(doc, 17)
    
    # First bug was that `pix.colorspace` was DeviceRGB.
    assert str(pix.colorspace) == 'Colorspace(CS_CMYK) - DeviceCMYK'
    
    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    assert str(pix.colorspace) == 'Colorspace(CS_RGB) - DeviceRGB'
    
    # Second bug was that the image was converted to RGB via greyscale proofing
    # color space, so image contained only shades of grey. This compressed
    # easily to a .png file, so we crudely check the bug is fixed by looking at
    # size of .png file.
    path = os.path.abspath(f'{__file__}/../../tests/test_3058_out.png')
    pix.save(path)
    s = os.path.getsize(path)
    assert 1800000 < s < 2600000, f'Unexpected size of {path}: {s}'

def test_3072():
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_3072.pdf')
    out = os.path.abspath(f'{__file__}/../../tests')
    
    doc = pymupdf.open(path)
    page_48 = doc[0]
    bbox = [147, 300, 447, 699]
    rect = pymupdf.Rect(*bbox)
    zoom = pymupdf.Matrix(3, 3)
    pix = page_48.get_pixmap(clip=rect, matrix=zoom)
    image_save_path = f'{out}/1.jpg'
    pix.save(image_save_path, jpg_quality=95)
    
    doc = pymupdf.open(path)
    page_49 = doc[1]
    bbox = [147, 543, 447, 768]
    rect = pymupdf.Rect(*bbox)
    zoom = pymupdf.Matrix(3, 3)
    pix = page_49.get_pixmap(clip=rect, matrix=zoom)
    image_save_path = f'{out}/2.jpg'
    pix.save(image_save_path, jpg_quality=95)
    rebase = hasattr(pymupdf, 'mupdf')
    if rebase:
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == (
                "syntax error: cannot find ExtGState resource 'BlendMode0'\n"
                "encountered syntax errors; page may not be correct\n"
                "syntax error: cannot find ExtGState resource 'BlendMode0'\n"
                "encountered syntax errors; page may not be correct"
                )

def test_3134():
    doc = pymupdf.Document()
    page = doc.new_page()
    page.get_pixmap(clip=pymupdf.Rect(0, 0, 100, 100)).save("test_3134_rect.jpg")
    page.get_pixmap(clip=pymupdf.IRect(0, 0, 100, 100)).save("test_3134_irect.jpg")
    stat_rect = os.stat('test_3134_rect.jpg')
    stat_irect = os.stat('test_3134_irect.jpg')
    print(f' {stat_rect=}')
    print(f'{stat_irect=}')
    assert stat_rect.st_size == stat_irect.st_size
    
def test_3177():
    path = os.path.abspath(f'{__file__}/../../tests/resources/img-transparent.png')
    pixmap = pymupdf.Pixmap(path)
    pixmap2 = pymupdf.Pixmap(None, pixmap)


def test_3493():
    '''
    If python3-gi is installed, we check fix for #3493, where importing gi
    would load an older version of libjpeg than is used in MuPDF, and break
    MuPDF.
    
    This test is excluded by default in sysinstall tests, because running
    commands in a new venv does not seem to pick up pymupdf as expected.
    '''
    if platform.system() != 'Linux':
        print(f'Not running because not Linux: {platform.system()=}')
        return
    
    import subprocess
    
    root = os.path.abspath(f'{__file__}/../..')
    in_path = f'{root}/tests/resources/test_3493.epub'
    
    def run(command, check=1, stdout=None):
        print(f'Running with {check=}: {command}')
        return subprocess.run(command, shell=1, check=check, stdout=stdout, text=1)
    
    def run_code(code, code_path, *, check=True, venv=None, venv_args='', pythonpath=None, stdout=None):
        code = textwrap.dedent(code)
        with open(code_path, 'w') as f:
            f.write(code)
        prefix = f'PYTHONPATH={pythonpath} ' if pythonpath else ''
        if venv:
            # Have seen this fail on Github in a curious way:
            #
            #   Running: /tmp/tmp.fBeKNLJQKk/venv/bin/python -m venv --system-site-packages /project/tests/resources/test_3493_venv
            #   Error: [Errno 2] No such file or directory: '/project/tests/resources/test_3493_venv/bin/python'
            #
            r = run(f'{sys.executable} -m venv {venv_args} {venv}', check=check)
            if r.returncode:
                return r
            r = run(f'. {venv}/bin/activate && {prefix}python {code_path}', check=check, stdout=stdout)
        else:
            r = run(f'{prefix}{sys.executable} {code_path}', check=check, stdout=stdout)
        return r
    
    # Find location of system install of `gi`.
    r = run_code(
            '''
            from gi.repository import GdkPixbuf
            import gi
            print(gi.__file__)
            '''
            ,
            f'{root}/tests/resources/test_3493_gi.py',
            check=0,
            venv=f'{root}/tests/resources/test_3493_venv',
            venv_args='--system-site-packages',
            stdout=subprocess.PIPE,
            )
    if r.returncode:
        print(f'test_3493(): Not running test because --system-site-packages venv cannot import gi.')
        return
    gi = r.stdout.strip()
    gi_pythonpath = os.path.abspath(f'{gi}/../..')
    
    def do(gi):
        # Run code that will import gi and pymupdf in different orders, and
        # return contents of generated .png file as a bytes.
        out = f'{root}/tests/resources/test_3493_{gi}.png'
        run_code(
                f'''
                if {gi}==0:
                    import pymupdf
                elif {gi}==1:
                    from gi.repository import GdkPixbuf
                    import pymupdf
                elif {gi}==2:
                    import pymupdf
                    from gi.repository import GdkPixbuf
                else:
                    assert 0
                document = pymupdf.Document('{in_path}')
                page = document[0]
                print(f'{gi=}: saving to: {out}')
                page.get_pixmap().save('{out}')
                '''
                ,
                os.path.abspath(f'{root}/tests/resources/test_3493_{gi}.py'),
                pythonpath=gi_pythonpath,
                )
        with open(out, 'rb') as f:
            return f.read()
    
    out0 = do(0)
    out1 = do(1)
    out2 = do(2)
    print(f'{len(out0)=} {len(out1)=} {len(out2)=}.')
    if pymupdf.mupdf_version_tuple >= (1, 24, 3):
        assert out1 == out0
    else:
        assert out1 != out0
    assert out2 == out0


def test_3848():
    if os.environ.get('PYMUPDF_RUNNING_ON_VALGRIND') == '1':
        # Takes 40m on Github.
        print(f'test_3848(): not running on valgrind because very slow.', flush=1)
        return
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3848.pdf')
    with pymupdf.open(path) as document:
        for i in range(len(document)):
            page = document.load_page(i)
            print(f'{page=}.')
            for annot in page.get_drawings():
                if page.get_textbox(annot['rect']):
                    rect = annot['rect']
                    pixmap = page.get_pixmap(clip=rect)
                    color_bytes = pixmap.color_topusage()


def test_3994():
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3994.pdf')
    with pymupdf.open(path) as document:
        page = document[0]
        txt_blocks = [blk for blk in page.get_text('dict')['blocks'] if blk['type']==0]
        for blk in txt_blocks:
            pix = page.get_pixmap(clip=pymupdf.Rect([int(v) for v in blk['bbox']]), colorspace=pymupdf.csRGB, alpha=False)
            percent, color = pix.color_topusage()
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == 'premature end of data in flate filter\n... repeated 2 times...'


def test_3448():
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3448.pdf')
    with pymupdf.open(path) as document:
        page = document[0]
        pixmap = page.get_pixmap(alpha=False, dpi=150)
        path_out = f'{path}.png'
        pixmap.save(path_out)
        print(f'Have written to: {path_out}')
    path_expected = os.path.normpath(f'{__file__}/../../tests/resources/test_3448.pdf-expected.png')
    pixmap_expected = pymupdf.Pixmap(path_expected)
    rms = gentle_compare.pixmaps_rms(pixmap, pixmap_expected)
    diff = gentle_compare.pixmaps_diff(pixmap_expected, pixmap)
    path_diff = os.path.normpath(f'{__file__}/../../tests/test_3448-diff.png')
    diff.save(path_diff)
    print(f'{rms=}')
    if pymupdf.mupdf_version_tuple < (1, 24, 11):
        assert 30 <= rms < 45
    elif pymupdf.mupdf_version_tuple < (1, 25, 5):
        # Prior to fix for mupdf bug 708274.
        assert 1 < rms < 2
    else:
        assert rms == 0


def test_3854():
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3854.pdf')
    with pymupdf.open(path) as document:
        page = document[0]
        pixmap = page.get_pixmap()
    pixmap.save(os.path.normpath(f'{__file__}/../../tests/test_3854_out.png'))
    
    # 2024-11-29: this is the incorrect expected output.
    path_expected_png = os.path.normpath(f'{__file__}/../../tests/resources/test_3854_expected.png')
    pixmap_expected = pymupdf.Pixmap(path_expected_png)
    pixmap_diff = gentle_compare.pixmaps_diff(pixmap_expected, pixmap)
    path_diff = os.path.normpath(f'{__file__}/../../tests/resources/test_3854_diff.png')
    pixmap_diff.save(path_diff)
    rms = gentle_compare.pixmaps_rms(pixmap, pixmap_expected)
    print(f'{rms=}.')
    if os.environ.get('PYMUPDF_SYSINSTALL_TEST') == '1':
        # MuPDF using external third-party libs gives slightly different
        # behaviour.
        assert rms < 2
    elif pymupdf.mupdf_version_tuple < (1, 25, 5):
        # # Prior to fix for mupdf bug 708274.
        assert 0.5 < rms < 2
    else:
        assert rms == 0


def test_4155():
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3854.pdf')
    with pymupdf.open(path) as document:
        page = document[0]
        pixmap = page.get_pixmap()
        mv = pixmap.samples_mv
        mvb1 = mv.tobytes()
    del page
    del pixmap
    try:
        mvb2 = mv.tobytes()
    except ValueError as e:
        print(f'Received exception: {e}')
        assert 'operation forbidden on released memoryview object' in str(e)
    else:
        assert 0, f'Did not receive expected exception when using defunct memoryview.'


def test_4336():
    if 0:
        # Compare with last classic release.
        import pickle
        path_out = os.path.normpath(f'{__file__}/../../tests/resources/test_4336_cc')
        code = textwrap.dedent(f'''
                import fitz
                import os
                import time
                import pickle
                
                path = os.path.normpath(f'{__file__}/../../tests/resources/nur-ruhig.jpg')
                pixmap = fitz.Pixmap(path)
                t = time.time()
                for i in range(10):
                    cc = pixmap.color_count()
                t = time.time() - t
                print(f'test_4336(): {{t=}}')
                with open({path_out!r}, 'wb') as f:
                    pickle.dump(cc, f)
                ''')
        path_code = os.path.normpath(f'{__file__}/../../tests/resources/test_4336.py')
        with open(path_code, 'w') as f:
            f.write(code)
        venv = os.path.normpath(f'{__file__}/../../tests/resources/test_4336_venv')
        command = f'{sys.executable} -m venv {venv}'
        command += f' && . {venv}/bin/activate'
        command += f' && pip install --force-reinstall pymupdf==1.23.8'
        command += f' && python {path_code}'
        print(f'Running: {command}', flush=1)
        subprocess.run(command, shell=1, check=1)
        with open(path_out, 'rb') as f:
            cc_old = pickle.load(f)
    else:
        cc_old = None
    path = os.path.normpath(f'{__file__}/../../tests/resources/nur-ruhig.jpg')
    pixmap = pymupdf.Pixmap(path)
    t = time.time()
    for i in range(10):
        cc = pixmap.color_count()
    t = time.time() - t
    print(f'test_4336(): {t=}')
    
    if cc_old:
        assert cc == cc_old
