# encoding utf-8
"""
* Confirm sample doc has no links and no annots.
* Confirm proper release of file handles via Document.close()
* Confirm properly raising exceptions in document creation
"""
import io
import os

import pymupdf
import pathlib
import pickle
import platform
import re
import subprocess
import sys
import textwrap
import time

import gentle_compare

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "001003ED.pdf")


def test_haslinks():
    doc = pymupdf.open(filename)
    assert doc.has_links() == False


def test_hasannots():
    doc = pymupdf.open(filename)
    assert doc.has_annots() == False


def test_haswidgets():
    doc = pymupdf.open(filename)
    assert doc.is_form_pdf == False


def test_isrepaired():
    doc = pymupdf.open(filename)
    assert doc.is_repaired == False
    pymupdf.TOOLS.mupdf_warnings()


def test_isdirty():
    doc = pymupdf.open(filename)
    assert doc.is_dirty == False


def test_cansaveincrementally():
    doc = pymupdf.open(filename)
    assert doc.can_save_incrementally() == True


def test_iswrapped():
    doc = pymupdf.open(filename)
    page = doc[0]
    assert page.is_wrapped


def test_wrapcontents():
    doc = pymupdf.open(filename)
    page = doc[0]
    page.wrap_contents()
    xref = page.get_contents()[0]
    cont = page.read_contents()
    doc.update_stream(xref, cont)
    page.set_contents(xref)
    assert len(page.get_contents()) == 1
    page.clean_contents()
    rebased = hasattr(pymupdf, 'mupdf')
    if rebased:
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == 'PDF stream Length incorrect'


def test_page_clean_contents():
    """Assert that page contents cleaning actually is invoked."""
    doc = pymupdf.open()
    page = doc.new_page()

    # draw two rectangles - will lead to two /Contents objects
    page.draw_rect((10, 10, 20, 20))
    page.draw_rect((20, 20, 30, 30))
    assert len(page.get_contents()) == 2
    assert page.read_contents().startswith(b"q") == False

    # clean / consolidate into one /Contents object
    page.clean_contents()
    assert len(page.get_contents()) == 1
    assert page.read_contents().startswith(b"q") == True


def test_annot_clean_contents():
    """Assert that annot contents cleaning actually is invoked."""
    doc = pymupdf.open()
    page = doc.new_page()
    annot = page.add_highlight_annot((10, 10, 20, 20))

    # the annotation appearance will not start with command b"q"


    # invoke appearance stream cleaning and reformatting
    annot.clean_contents()

    # appearance stream should now indeed start with command b"q"
    assert annot._getAP().startswith(b"q") == True


def test_config():
    assert pymupdf.TOOLS.fitz_config["py-memory"] in (True, False)


def test_glyphnames():
    name = "infinity"
    infinity = pymupdf.glyph_name_to_unicode(name)
    assert pymupdf.unicode_to_glyph_name(infinity) == name


def test_rgbcodes():
    sRGB = 0xFFFFFF
    assert pymupdf.sRGB_to_pdf(sRGB) == (1, 1, 1)
    assert pymupdf.sRGB_to_rgb(sRGB) == (255, 255, 255)


def test_pdfstring():
    pymupdf.get_pdf_now()
    pymupdf.get_pdf_str("Beijing, chinesisch 北京")
    pymupdf.get_text_length("Beijing, chinesisch 北京", fontname="china-s")
    pymupdf.get_pdf_str("Latin characters êßöäü")


def test_open_exceptions():
    try:
        doc = pymupdf.open(filename, filetype="xps")
    except RuntimeError as e:
        assert repr(e).startswith("FileDataError")

    try:
        doc = pymupdf.open(filename, filetype="xxx")
    except Exception as e:
        assert repr(e).startswith("ValueError")

    try:
        doc = pymupdf.open("x.y")
    except Exception as e:
        assert repr(e).startswith("FileNotFoundError")

    try:
        doc = pymupdf.open("pdf", b"")
    except RuntimeError as e:
        assert repr(e).startswith("EmptyFileError")


def test_bug1945():
    pdf = pymupdf.open(f'{scriptdir}/resources/bug1945.pdf')
    buffer_ = io.BytesIO()
    pdf.save(buffer_, clean=True)


def test_bug1971():
    for _ in range(2):
        doc = pymupdf.Document(f'{scriptdir}/resources/bug1971.pdf')
        page = next(doc.pages())
        page.get_drawings()
        doc.close()
        assert doc.is_closed

def test_default_font():
    f = pymupdf.Font()
    assert str(f) == "Font('Noto Serif Regular')"
    assert repr(f) == "Font('Noto Serif Regular')"

def test_add_ink_annot():
    import math
    document = pymupdf.Document()
    page = document.new_page()
    line1 = []
    line2 = []
    for a in range( 0, 360*2, 15):
        x = a
        c = 300 + 200 * math.cos( a * math.pi/180)
        s = 300 + 100 * math.sin( a * math.pi/180)
        line1.append( (x, c))
        line2.append( (x, s))
    page.add_ink_annot( [line1, line2])
    page.insert_text((100, 72), 'Hello world')
    page.add_text_annot((200,200), "Some Text")
    page.get_bboxlog()
    path = f'{scriptdir}/resources/test_add_ink_annot.pdf'
    document.save( path)
    print( f'Have saved to: path={path!r}')

def test_techwriter_append():
    print(pymupdf.__doc__)
    doc = pymupdf.open()
    page = doc.new_page()
    tw = pymupdf.TextWriter(page.rect)
    text = "Red rectangle = TextWriter.text_rect, blue circle = .last_point"
    r = tw.append((100, 100), text)
    print(f'r={r!r}')
    tw.write_text(page)
    page.draw_rect(tw.text_rect, color=pymupdf.pdfcolor["red"])
    page.draw_circle(tw.last_point, 2, color=pymupdf.pdfcolor["blue"])
    path = f"{scriptdir}/resources/test_techwriter_append.pdf"
    doc.ez_save(path)
    print( f'Have saved to: {path}')

def test_opacity():
    doc = pymupdf.open()
    page = doc.new_page()

    annot1 = page.add_circle_annot((50, 50, 100, 100))
    annot1.set_colors(fill=(1, 0, 0), stroke=(1, 0, 0))
    annot1.set_opacity(2 / 3)
    annot1.update(blend_mode="Multiply")

    annot2 = page.add_circle_annot((75, 75, 125, 125))
    annot2.set_colors(fill=(0, 0, 1), stroke=(0, 0, 1))
    annot2.set_opacity(1 / 3)
    annot2.update(blend_mode="Multiply")
    outfile = f'{scriptdir}/resources/opacity.pdf'
    doc.save(outfile, expand=True, pretty=True)
    print("saved", outfile)

def test_get_text_dict():
    import json
    doc=pymupdf.open(f'{scriptdir}/resources/v110-changes.pdf')
    page=doc[0]
    blocks=page.get_text("dict")["blocks"]
    # Check no opaque types in `blocks`.
    json.dumps( blocks, indent=4)

def test_font():
    font = pymupdf.Font()
    print(repr(font))
    bbox = font.glyph_bbox( 65)
    print( f'bbox={bbox!r}')

def test_insert_font():
    doc=pymupdf.open(f'{scriptdir}/resources/v110-changes.pdf')
    page = doc[0]
    i = page.insert_font()
    print( f'page.insert_font() => {i}')

def test_2173():
    from pymupdf import IRect, Pixmap, CS_RGB, Colorspace
    for i in range( 100):
        #print( f'i={i!r}')
        image = Pixmap(Colorspace(CS_RGB), IRect(0, 0, 13, 37))
    print( 'test_2173() finished')

def test_texttrace():
    import time
    document = pymupdf.Document( f'{scriptdir}/resources/joined.pdf')
    t = time.time()
    for page in document:
        tt = page.get_texttrace()
    t = time.time() - t
    print( f'test_texttrace(): t={t!r}')

    # Repeat, this time writing data to file.
    import json
    path = f'{scriptdir}/resources/test_texttrace.txt'
    print( f'test_texttrace(): Writing to: {path}')
    with open( path, 'w') as f:
        for i, page in enumerate(document):
            tt = page.get_texttrace()
            print( f'page {i} json:\n{json.dumps(tt, indent="    ")}', file=f)


def test_2533():
    """Assert correct char bbox in page.get_texttrace().

    Search for a unique char on page and confirm that page.get_texttrace()
    returns the same bbox as the search method.
    """
    if hasattr(pymupdf, 'mupdf') and not pymupdf.g_use_extra:
        print('Not running test_2533() because rebased with use_extra=0 known to fail')
        return
    pymupdf.TOOLS.set_small_glyph_heights(True)
    try:
        doc = pymupdf.open(os.path.join(scriptdir, "resources", "test_2533.pdf"))
        page = doc[0]
        NEEDLE = "民"
        ord_NEEDLE = ord(NEEDLE)
        for span in page.get_texttrace():
            for char in span["chars"]:
                if char[0] == ord_NEEDLE:
                    bbox = pymupdf.Rect(char[3])
                    break
        bbox2 = page.search_for(NEEDLE)[0]
        assert bbox2 == bbox, f'{bbox=} {bbox2=} {bbox2-bbox=}.'
    finally:
        pymupdf.TOOLS.set_small_glyph_heights(False)


def test_2645():
    """Assert same font size calculation in corner cases.
    """
    folder = os.path.join(scriptdir, "resources")
    files = ("test_2645_1.pdf", "test_2645_2.pdf", "test_2645_3.pdf")
    for f in files:
        doc = pymupdf.open(os.path.join(folder, f))
        page = doc[0]
        fontsize0 = page.get_texttrace()[0]["size"]
        fontsize1 = page.get_text("dict", flags=pymupdf.TEXTFLAGS_TEXT)["blocks"][0]["lines"][
            0
        ]["spans"][0]["size"]
        assert abs(fontsize0 - fontsize1) < 1e-5


def test_2506():
    """Ensure expected font size across text writing angles."""
    doc = pymupdf.open()
    page = doc.new_page()
    point = pymupdf.Point(100, 300)  # insertion point
    fontsize = 11  # fontsize
    text = "Hello"  # text
    angles = (0, 30, 60, 90, 120)  # some angles

    # write text with different angles
    for angle in angles:
        page.insert_text(
            point, text, fontsize=fontsize, morph=(point, pymupdf.Matrix(angle))
        )

    # ensure correct fontsize for get_texttrace() - forgiving rounding problems
    for span in page.get_texttrace():
        print(span["dir"])
        assert round(span["size"]) == fontsize

    # ensure correct fontsize for get_text() - forgiving rounding problems
    for block in page.get_text("dict")["blocks"]:
        for line in block["lines"]:
            print(line["dir"])
            for span in line["spans"]:
                print(span["size"])
                assert round(span["size"]) == fontsize


def test_2108():
    doc = pymupdf.open(f'{scriptdir}/resources/test_2108.pdf')
    page = doc[0]
    areas = page.search_for("{sig}")
    rect = areas[0]
    page.add_redact_annot(rect)
    page.apply_redactions()
    text = page.get_text()

    text_expected = b'Frau\nClaire Dunphy\nTeststra\xc3\x9fe 5\n12345 Stadt\nVertragsnummer:  12345\nSehr geehrte Frau Dunphy,\nText\nMit freundlichen Gr\xc3\xbc\xc3\x9fen\nTestfirma\nVertrag:\n  12345\nAnsprechpartner:\nJay Pritchet\nTelefon:\n123456\nE-Mail:\ntest@test.de\nDatum:\n07.12.2022\n'.decode('utf8')

    if 1:
        # Verbose info.
        print(f'test_2108(): text is:\n{text}')
        print(f'')
        print(f'test_2108(): repr(text) is:\n{text!r}')
        print(f'')
        print(f'test_2108(): repr(text.encode("utf8")) is:\n{text.encode("utf8")!r}')
        print(f'')
        print(f'test_2108(): text_expected is:\n{text_expected}')
        print(f'')
        print(f'test_2108(): repr(text_expected) is:\n{text_expected!r}')
        print(f'')
        print(f'test_2108(): repr(text_expected.encode("utf8")) is:\n{text_expected.encode("utf8")!r}')

        ok1 = (text == text_expected)
        ok2 = (text.encode("utf8") == text_expected.encode("utf8"))
        ok3 = (repr(text.encode("utf8")) == repr(text_expected.encode("utf8")))

        print(f'')
        print(f'ok1={ok1}')
        print(f'ok2={ok2}')
        print(f'ok3={ok3}')

        print(f'')

    print(f'{pymupdf.mupdf_version_tuple=}')
    if pymupdf.mupdf_version_tuple >= (1, 21, 2):
        print('Asserting text==text_expected')
        assert text == text_expected
    else:
        print('Asserting text!=text_expected')
        assert text != text_expected


def test_2238():
    filepath = f'{scriptdir}/resources/test2238.pdf'
    doc = pymupdf.open(filepath)
    rebased = hasattr(pymupdf, 'mupdf')
    if rebased:
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == (
                'format error: cannot recognize version marker\n'
                'trying to repair broken xref\n'
                'repairing PDF document'
                ), f'{wt=}'
    first_page = doc.load_page(0).get_text('text', pymupdf.INFINITE_RECT())
    last_page = doc.load_page(-1).get_text('text', pymupdf.INFINITE_RECT())

    print(f'first_page={first_page!r}')
    print(f'last_page={last_page!r}')
    assert first_page == 'Hello World\n'
    assert last_page == 'Hello World\n'

    first_page = doc.load_page(0).get_text('text')
    last_page = doc.load_page(-1).get_text('text')

    print(f'first_page={first_page!r}')
    print(f'last_page={last_page!r}')
    assert first_page == 'Hello World\n'
    assert last_page == 'Hello World\n'


def test_2093():
    doc = pymupdf.open(f'{scriptdir}/resources/test2093.pdf')

    def average_color(page):
        pixmap = page.get_pixmap()
        p_average = [0] * pixmap.n
        for y in range(pixmap.height):
            for x in range(pixmap.width):
                p = pixmap.pixel(x, y)
                for i in range(pixmap.n):
                    p_average[i] += p[i]
        for i in range(pixmap.n):
            p_average[i] /= (pixmap.height * pixmap.width)
        return p_average

    page = doc.load_page(0)
    pixel_average_before = average_color(page)

    rx=135.123
    ry=123.56878
    rw=69.8409
    rh=9.46397

    x0 = rx
    y0 = ry
    x1 = rx + rw
    y1 = ry + rh

    rect = pymupdf.Rect(x0, y0, x1, y1)

    font = pymupdf.Font("Helvetica")
    fill_color=(0,0,0)
    page.add_redact_annot(
        quad=rect,
        #text="null",
        fontname=font.name,
        fontsize=12,
        align=pymupdf.TEXT_ALIGN_CENTER,
        fill=fill_color,
        text_color=(1,1,1),
    )

    page.apply_redactions()
    pixel_average_after = average_color(page)

    print(f'pixel_average_before={pixel_average_before!r}')
    print(f'pixel_average_after={pixel_average_after!r}')

    # Before this bug was fixed (MuPDF-1.22):
    #   pixel_average_before=[130.864323120088, 115.23577810900859, 92.9268559996174]
    #   pixel_average_after=[138.68844553555772, 123.05687162237561, 100.74275056194105]
    # After fix:
    #   pixel_average_before=[130.864323120088, 115.23577810900859, 92.9268559996174]
    #   pixel_average_after=[130.8889209934799, 115.25722751837269, 92.94327384463327]
    #
    for i in range(len(pixel_average_before)):
        diff = pixel_average_before[i] - pixel_average_after[i]
        assert abs(diff) < 0.1

    out = f'{scriptdir}/resources/test2093-out.pdf'
    doc.save(out)
    print(f'Have written to: {out}')


def test_2182():
    print(f'test_2182() started')
    doc = pymupdf.open(f'{scriptdir}/resources/test2182.pdf')
    page = doc[0]
    for annot in page.annots():
        print(annot)
    print(f'test_2182() finished')


def test_2246():
    """
    Test / confirm identical text positions generated by
    * page.insert_text()
    versus
    * TextWriter.write_text()

    ... under varying situations as follows:

    1. MediaBox does not start at (0, 0)
    2. CropBox origin is different from that of MediaBox
    3. Check for all 4 possible page rotations

    The test writes the same text at the same positions using `page.insert_text()`,
    respectively `TextWriter.write_text()`.
    Then extracts the text spans and confirms that they all occupy the same bbox.
    This ensures coincidence of text positions of page.of insert_text()
    (which is assumed correct) and TextWriter.write_text().
    """
    def bbox_count(rot):
        """Make a page and insert identical text via different methods.

        Desired page rotation is a parameter. MediaBox and CropBox are chosen
        to be "awkward": MediaBox does not start at (0,0) and CropBox is a
        true subset of MediaBox.
        """
        # bboxes of spans on page: same text positions are represented by ONE bbox
        bboxes = set()
        doc = pymupdf.open()
        # prepare a page with desired MediaBox / CropBox peculiarities
        mediabox = pymupdf.paper_rect("letter")
        page = doc.new_page(width=mediabox.width, height=mediabox.height)
        xref = page.xref
        newmbox = list(map(float, doc.xref_get_key(xref, "MediaBox")[1][1:-1].split()))
        newmbox = pymupdf.Rect(newmbox)
        mbox = newmbox + (10, 20, 10, 20)
        cbox = mbox + (10, 10, -10, -10)
        doc.xref_set_key(xref, "MediaBox", "[%g %g %g %g]" % tuple(mbox))
        doc.xref_set_key(xref, "CrobBox", "[%g %g %g %g]" % tuple(cbox))
        # set page to desired rotation
        page.set_rotation(rot)
        page.insert_text((50, 50), "Text inserted at (50,50)")
        tw = pymupdf.TextWriter(page.rect)
        tw.append((50, 50), "Text inserted at (50,50)")
        tw.write_text(page)
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            for l in b["lines"]:
                for s in l["spans"]:
                    # store bbox rounded to 3 decimal places
                    bboxes.add(pymupdf.Rect(pymupdf.JM_TUPLE3(s["bbox"])))
        return len(bboxes)  # should be 1!

    # the following tests must all pass
    assert bbox_count(0) == 1
    assert bbox_count(90) == 1
    assert bbox_count(180) == 1
    assert bbox_count(270) == 1


def test_2430():
    """Confirm that multiple font property checks will not destroy Py_None."""
    font = pymupdf.Font("helv")
    for i in range(1000):
        _ = font.flags

def test_2692():
    document = pymupdf.Document(f'{scriptdir}/resources/2.pdf')
    for page in document:
        pix = page.get_pixmap(clip=pymupdf.Rect(0,0,10,10))
        dl = page.get_displaylist(annots=True)
        pix = dl.get_pixmap(
                matrix=pymupdf.Identity,
                colorspace=pymupdf.csRGB,
                alpha=False,
                clip=pymupdf.Rect(0,0,10,10),
                )
        pix = dl.get_pixmap(
                matrix=pymupdf.Identity,
                #colorspace=pymupdf.csRGB,
                alpha=False,
                clip=pymupdf.Rect(0,0,10,10),
                )
    

def test_2596():
    """Confirm correctly abandoning cache when reloading a page."""
    doc = pymupdf.Document(f"{scriptdir}/resources/test_2596.pdf")
    page = doc[0]
    pix0 = page.get_pixmap()  # render the page
    _ = doc.tobytes(garbage=3)  # save with garbage collection

    # Note this will invalidate cache content for this page.
    # Reloading the page now empties the cache, so rendering
    # will deliver the same pixmap
    page = doc.reload_page(page)
    pix1 = page.get_pixmap()
    assert pix1.samples == pix0.samples
    rebased = hasattr(pymupdf, 'mupdf')
    if rebased:
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == 'too many indirections (possible indirection cycle involving 24 0 R)'


def test_2730():
    """Ensure identical output across text extractions."""
    doc = pymupdf.open(f"{scriptdir}/resources/test_2730.pdf")
    page = doc[0]
    s1 = set(page.get_text())  # plain text extraction
    s2 = set(page.get_text(sort=True))  # uses "blocks" extraction
    s3 = set(page.get_textbox(page.rect))
    assert s1 == s2
    assert s1 == s3


def test_2553():
    """Ensure identical output across text extractions."""
    verbose = 0
    doc = pymupdf.open(f"{scriptdir}/resources/test_2553.pdf")
    page = doc[0]

    # extract plain text, build set of all characters
    list1 = page.get_text()
    set1 = set(list1)

    # extract text blocks, build set of all characters
    list2 = page.get_text(sort=True)  # internally uses "blocks"
    set2 = set(list2)
    
    # extract textbox content, build set of all characters
    list3 = page.get_textbox(page.rect)
    set3 = set(list3)
    
    def show(l):
        ret = f'len={len(l)}\n'
        for c in l:
            cc = ord(c)
            if (cc >= 32 and cc < 127) or c == '\n':
                ret += c
            else:
                ret += f' [0x{hex(cc)}]'
        return ret
    
    if verbose:
        print(f'list1:\n{show(list1)}')
        print(f'list2:\n{show(list2)}')
        print(f'list3:\n{show(list3)}')
    
    # all sets must be equal
    assert set1 == set2
    assert set1 == set3

    # With mupdf later than 1.23.4, this special page contains no invalid
    # Unicodes.
    #
    if pymupdf.mupdf_version_tuple > (1, 23, 4):
        print(f'Checking no occurrence of 0xFFFD, {pymupdf.mupdf_version_tuple=}.')
        assert chr(0xFFFD) not in set1
    else:
        print(f'Checking occurrence of 0xFFFD, {pymupdf.mupdf_version_tuple=}.')
        assert chr(0xFFFD) in set1

def test_2553_2():
    doc = pymupdf.open(f"{scriptdir}/resources/test_2553-2.pdf")
    page = doc[0]

    # extract plain text, ensure that there are no 0xFFFD characters
    text = page.get_text()
    if pymupdf.mupdf_version_tuple >= (1, 23, 7):
        assert chr(0xfffd) not in text
    else:
        # Bug not fixed in MuPDF.
        assert chr(0xfffd) in text

def test_2635():
    """Rendering a page before and after cleaning it should yield the same pixmap."""
    doc = pymupdf.open(f"{scriptdir}/resources/test_2635.pdf")
    page = doc[0]
    pix1 = page.get_pixmap()  # pixmap before cleaning

    page.clean_contents()  # clean page
    pix2 = page.get_pixmap()  # pixmap after cleaning
    assert pix1.samples == pix2.samples  # assert equality


def test_resolve_names():
    """Test PDF name resolution."""
    # guard against wrong PyMuPDF architecture version
    if not hasattr(pymupdf.Document, "resolve_names"):
        print("PyMuPDF version does not support resolving PDF names")
        return
    pickle_in = open(f"{scriptdir}/resources/cython.pickle", "rb")
    old_names = pickle.load(pickle_in)
    doc = pymupdf.open(f"{scriptdir}/resources/cython.pdf")
    new_names = doc.resolve_names()
    assert new_names == old_names

def test_2777():
    document = pymupdf.Document()
    page = document.new_page()
    print(page.mediabox.width)

def test_2710():
    doc = pymupdf.open(f'{scriptdir}/resources/test_2710.pdf')
    page = doc.load_page(0)
    
    print(f'test_2710(): {page.cropbox=}')
    print(f'test_2710(): {page.mediabox=}')
    print(f'test_2710(): {page.rect=}')
    
    def numbers_approx_eq(a, b):
        return abs(a-b) < 0.001
    def points_approx_eq(a, b):
        return numbers_approx_eq(a.x, b.x) and numbers_approx_eq(a.y, b.y)
    def rects_approx_eq(a, b):
        return points_approx_eq(a.bottom_left, b.bottom_left) and points_approx_eq(a.top_right, b.top_right)
    def assert_rects_approx_eq(a, b):
        assert rects_approx_eq(a, b), f'Not nearly identical: {a=} {b=}'
                
    blocks = page.get_text('blocks')
    print(f'test_2710(): {blocks=}')
    assert len(blocks) == 2
    block = blocks[1]
    rect = pymupdf.Rect(block[:4])
    text = block[4]
    print(f'test_2710(): {rect=}')
    print(f'test_2710(): {text=}')
    assert text == 'Text at left page border\n'
    
    assert_rects_approx_eq(page.cropbox, pymupdf.Rect(30.0, 30.0, 565.3200073242188, 811.9199829101562))
    assert_rects_approx_eq(page.mediabox, pymupdf.Rect(0.0, 0.0, 595.3200073242188, 841.9199829101562))
    print(f'test_2710(): {pymupdf.mupdf_version_tuple=}')
    if pymupdf.mupdf_version_tuple < (1, 23, 5):
        print(f'test_2710(): Not Checking page.rect and rect.')
    elif pymupdf.mupdf_version_tuple < (1, 24.0):
        print(f'test_2710(): Checking page.rect and rect.')
        assert_rects_approx_eq(page.rect, pymupdf.Rect(0.0, 0.0, 535.3200073242188, 781.9199829101562))
        assert_rects_approx_eq(rect, pymupdf.Rect(0.7872352600097656, 64.7560043334961, 124.85531616210938, 78.1622543334961))
    else:
        # 2023-11-05: Currently broken in mupdf master.
        print(f'test_2710(): Not Checking page.rect and rect.')
    rebased = hasattr(pymupdf, 'mupdf')
    if rebased:
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == (
                "syntax error: cannot find ExtGState resource 'GS7'\n"
                "syntax error: cannot find ExtGState resource 'GS8'\n"
                "encountered syntax errors; page may not be correct"
                )


def test_2736():
    """Check handling of CropBox changes vis-a-vis a MediaBox with
       negative coordinates."""
    doc = pymupdf.open()
    page = doc.new_page()

    # fake a MediaBox for demo purposes
    doc.xref_set_key(page.xref, "MediaBox", "[-30 -20 595 842]")

    assert page.cropbox == pymupdf.Rect(-30, 0, 595, 862)
    assert page.rect == pymupdf.Rect(0, 0, 625, 862)

    # change the CropBox: shift by (10, 10) in both dimensions. Please note:
    # To achieve this, 10 must be subtracted from 862! yo must never be negative!
    page.set_cropbox(pymupdf.Rect(-20, 0, 595, 852))

    # get CropBox from the page definition
    assert doc.xref_get_key(page.xref, "CropBox")[1] == "[-20 -10 595 842]"
    assert page.rect == pymupdf.Rect(0, 0, 615, 852)

    error = False
    text = ""
    try:  # check error detection
        page.set_cropbox((-35, -10, 595, 842))
    except Exception as e:
        text = str(e)
        error = True
    assert error == True
    assert text == "CropBox not in MediaBox"


def test_subset_fonts():
    """Confirm subset_fonts is working."""
    if not hasattr(pymupdf, "mupdf"):
        print("Not testing 'test_subset_fonts' in classic.")
        return
    text = "Just some arbitrary text."
    arch = pymupdf.Archive()
    css = pymupdf.css_for_pymupdf_font("ubuntu", archive=arch)
    css += "* {font-family: ubuntu;}"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_htmlbox(page.rect, text, css=css, archive=arch)
    doc.subset_fonts(verbose=True)
    found = False
    for xref in range(1, doc.xref_length()):
        if "+Ubuntu#20Regular" in doc.xref_object(xref):
            found = True
            break
    assert found is True


def test_2957_1():
    """Text following a redaction must not change coordinates."""
    # test file with redactions
    doc = pymupdf.open(os.path.join(scriptdir, "resources", "test_2957_1.pdf"))
    page = doc[0]
    # search for string that must not move by redactions
    rects0 = page.search_for("6e9f73dfb4384a2b8af6ebba")
    # sort rectangles vertically
    rects0 = sorted(rects0, key=lambda r: r.y1)
    assert len(rects0) == 2  # must be 2 redactions
    page.apply_redactions()

    # reload page to finalize updates
    page = doc.reload_page(page)

    # the two string must retain their positions (except rounding errors)
    rects1 = page.search_for("6e9f73dfb4384a2b8af6ebba")
    rects1 = sorted(rects1, key=lambda r: r.y1)

    assert page.first_annot is None  # make sure annotations have disappeared
    for i in range(2):
        r0 = rects0[i].irect  # take rounded rects
        r1 = rects1[i].irect
        assert r0 == r1


def test_2957_2():
    """Redacted text must not change positions of remaining text."""
    doc = pymupdf.open(os.path.join(scriptdir, "resources", "test_2957_2.pdf"))
    page = doc[0]
    words0 = page.get_text("words")  # all words before redacting
    page.apply_redactions()  # remove/redact the word "longer"
    words1 = page.get_text("words")  # extract words again
    assert len(words1) == len(words0) - 1  # must be one word less
    assert words0[3][4] == "longer"  # just confirm test file is correct one
    del words0[3]  # remove the redacted word from first list
    for i in range(len(words1)):  # compare words
        w1 = words1[i]  # word after redaction
        bbox1 = pymupdf.Rect(w1[:4]).irect  # its IRect coordinates
        w0 = words0[i]  # word before redaction
        bbox0 = pymupdf.Rect(w0[:4]).irect  # its IRect coordinates
        assert bbox0 == bbox1  # must be same coordinates


def test_707560():
    """https://bugs.ghostscript.com/show_bug.cgi?id=707560
    Ensure that redactions also remove characters with an empty width bbox.
    """
    # Make text that will contain characters with an empty bbox.

    greetings = (
        "Hello, World!",  # english
        "Hallo, Welt!",  # german
        "سلام دنیا!",  # persian
        "வணக்கம், உலகம்!",  # tamil
        "สวัสดีชาวโลก!",  # thai
        "Привіт Світ!",  # ucranian
        "שלום עולם!",  # hebrew
        "ওহে বিশ্ব!",  # bengali
        "你好世界！",  # chinese
        "こんにちは世界！",  # japanese
        "안녕하세요, 월드!",  # korean
        "नमस्कार, विश्व !",  # sanskrit
        "हैलो वर्ल्ड!",  # hindi
    )
    text = " ... ".join([g for g in greetings])
    where = (50, 50, 400, 500)
    story = pymupdf.Story(text)
    bio = io.BytesIO()
    writer = pymupdf.DocumentWriter(bio)
    more = True
    while more:
        dev = writer.begin_page(pymupdf.paper_rect("a4"))
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
    writer.close()
    doc = pymupdf.open("pdf", bio)
    page = doc[0]
    text = page.get_text()
    assert text, "Unexpected: test page has no text."
    page.add_redact_annot(page.rect)
    page.apply_redactions()
    assert not page.get_text(), "Unexpected: text not fully redacted."


def test_3070():
    with pymupdf.open(os.path.abspath(f'{__file__}/../../tests/resources/test_3070.pdf')) as pdf:
      links = pdf[0].get_links()
      links[0]['uri'] = "https://www.ddg.gg"
      pdf[0].update_link(links[0])
      pdf.save(os.path.abspath(f'{__file__}/../../tests/test_3070_out.pdf'))

def test_bboxlog_2885():
    doc = pymupdf.open(os.path.abspath(f'{__file__}/../../tests/resources/test_2885.pdf'))
    page=doc[0]
    
    bbl = page.get_bboxlog()
    if pymupdf.mupdf_version_tuple >= (1, 24, 9):
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == 'invalid marked content and clip nesting'
    
    bbl = page.get_bboxlog(layers=True)
    if pymupdf.mupdf_version_tuple >= (1, 24, 9):
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == 'invalid marked content and clip nesting'

def test_3081():
    '''
    Check Document.close() closes file handles, even if a Page instance exists.
    '''
    path1 = os.path.abspath(f'{__file__}/../../tests/resources/1.pdf')
    path2 = os.path.abspath(f'{__file__}/../../tests/test_3081-2.pdf')
    
    rebased = hasattr(pymupdf, 'mupdf')
    
    import shutil
    import sys
    import traceback
    shutil.copy2(path1, path2)
    
    # Find next two available fds.
    next_fd_1 = os.open(path2, os.O_RDONLY)
    next_fd_2 = os.open(path2, os.O_RDONLY)
    os.close(next_fd_1)
    os.close(next_fd_2)

    def next_fd():
        fd = os.open(path2, os.O_RDONLY)
        os.close(fd)
        return fd
    
    fd1 = next_fd()
    document = pymupdf.open(path2)
    page = document[0]
    fd2 = next_fd()
    document.close()
    if rebased:
        assert document.this is None
        assert page.this is None
    try:
        document.page_count()
    except Exception as e:
        print(f'Received expected exception: {e}')
        #traceback.print_exc(file=sys.stdout)
        assert str(e) == 'document closed'
    else:
        assert 0, 'Did not receive expected exception.'
    fd3 = next_fd()
    try:
        page.bound()
    except Exception as e:
        print(f'Received expected exception: {e}')
        #traceback.print_exc(file=sys.stdout)
        if rebased:
            assert str(e) == 'page is None'
        else:
            assert str(e) == 'orphaned object: parent is None'
    else:
        assert 0, 'Did not receive expected exception.'
    page = None
    fd4 = next_fd()
    print(f'{next_fd_1=} {next_fd_2=}')
    print(f'{fd1=} {fd2=} {fd3=} {fd4=}')
    print(f'{document=}')
    assert fd1 == next_fd_1
    assert fd2 == next_fd_2 # Checks document only uses one fd.
    assert fd3 == next_fd_1 # Checks no leaked fds after document close.
    assert fd4 == next_fd_1 # Checks no leaked fds after failed page access.

def test_xml():
    path = os.path.abspath(f'{__file__}/../../tests/resources/2.pdf')
    with pymupdf.open(path) as document:
        document.get_xml_metadata()

def test_3112_set_xml_metadata():
    document = pymupdf.Document()
    document.set_xml_metadata('hello world')

def test_archive_3126():
    if not hasattr(pymupdf, 'mupdf'):
        print(f'Not running because known to fail with classic.')
        return
    p = os.path.abspath(f'{__file__}/../../tests/resources')
    p = pathlib.Path(p)
    archive = pymupdf.Archive(p)
    
def test_3140():
    if not hasattr(pymupdf, 'mupdf'):
        print(f'Not running test_3140 on classic, because Page.insert_htmlbox() not available.')
        return
    css2 = ''
    path = os.path.abspath(f'{__file__}/../../tests/resources/2.pdf')
    oldfile = os.path.abspath(f'{__file__}/../../tests/test_3140_old.pdf')
    newfile = os.path.abspath(f'{__file__}/../../tests/test_3140_new.pdf')
    import shutil
    shutil.copy2(path, oldfile)
    def next_fd():
        fd = os.open(path, os.O_RDONLY)
        os.close(fd)
        return fd
    fd1 = next_fd()
    with pymupdf.open(oldfile) as doc:  # open document
        page = doc[0]
        rect = pymupdf.Rect(130, 400, 430, 600)
        CELLS = pymupdf.make_table(rect, cols=3, rows=5)
        shape = page.new_shape()  # create Shape
        for i in range(5):
            for j in range(3):
                qtext = "<b>" + "Ques #" + str(i*3+j+1) + ": " + "</b>" # codespell:ignore
                atext = "<b>" + "Ans:" + "</b>" # codespell:ignore
                qtext = qtext + '<br>' + atext
                shape.draw_rect(CELLS[i][j])  # draw rectangle
                page.insert_htmlbox(CELLS[i][j], qtext, css=css2, scale_low=0)
        shape.finish(width=2.5, color=pymupdf.pdfcolor["blue"], )
        shape.commit()  # write all stuff to the page
        doc.subset_fonts()
        doc.ez_save(newfile)
    fd2 = next_fd()
    assert fd2 == fd1, f'{fd1=} {fd2=}'
    os.remove(oldfile)

def test_cli():
    if not hasattr(pymupdf, 'mupdf'):
        print('test_cli(): Not running on classic because of fitz_old.')
        return
    import subprocess
    subprocess.run(f'pymupdf -h', shell=1, check=1)


def check_lines(expected_regexes, actual):
    '''
    Checks lines in <actual> match regexes in <expected_regexes>.
    '''
    print(f'check_lines():', flush=1)
    print(f'{expected_regexes=}', flush=1)
    print(f'{actual=}', flush=1)
    def str_to_list(s):
        if isinstance(s, str):
            return s.split('\n') if s else list()
        return s
    expected_regexes = str_to_list(expected_regexes)
    actual = str_to_list(actual)
    if expected_regexes and expected_regexes[-1]:
        expected_regexes.append('') # Always expect a trailing empty line.
    # Remove `None` regexes and make all regexes match entire lines.
    expected_regexes = [f'^{i}$' for i in expected_regexes if i is not None]
    print(f'{expected_regexes=}', flush=1)
    for expected_regex_line, actual_line in zip(expected_regexes, actual):
        print(f'    {expected_regex_line=}', flush=1)
        print(f'            {actual_line=}', flush=1)
        assert re.match(expected_regex_line, actual_line)
    assert len(expected_regexes) == len(actual), \
            f'expected/actual lines mismatch: {len(expected_regexes)=} {len(actual)=}.'

def test_cli_out():
    '''
    Check redirection of messages and log diagnostics with environment
    variables PYMUPDF_LOG and PYMUPDF_MESSAGE.
    '''
    if not hasattr(pymupdf, 'mupdf'):
        print('test_cli(): Not running on classic because of fitz_old.')
        return
    import platform
    import re
    import subprocess
    log_prefix = None
    if os.environ.get('PYMUPDF_USE_EXTRA') == '0':
        log_prefix = f'.+Using non-default setting from PYMUPDF_USE_EXTRA: \'0\''
    
    def check(
            expect_out,
            expect_err,
            message=None,
            log=None,
            verbose=0,
            ):
        '''
        Sets PYMUPDF_MESSAGE to `message` and PYMUPDF_LOG to `log`, runs
        `pymupdf internal`, and checks lines stdout and stderr match regexes in
        `expect_out` and `expect_err`. Note that we enclose regexes in `^...$`.
        '''
        env = dict()
        if log:
            env['PYMUPDF_LOG'] = log
        if message:
            env['PYMUPDF_MESSAGE'] = message
        env = os.environ | env
        print(f'Running with {env=}: pymupdf internal', flush=1)
        cp = subprocess.run(f'pymupdf internal', shell=1, check=1, capture_output=1, env=env, text=True)
        
        if verbose:
            #print(f'{cp.stdout=}.', flush=1)
            #print(f'{cp.stderr=}.', flush=1)
            sys.stdout.write(f'stdout:\n{textwrap.indent(cp.stdout, "    ")}')
            sys.stdout.write(f'stderr:\n{textwrap.indent(cp.stderr, "    ")}')
        check_lines(expect_out, cp.stdout)
        check_lines(expect_err, cp.stderr)
    
    #
    print(f'Checking default, all output to stdout.')
    check(
            [
                log_prefix,
                'This is from PyMuPDF message[(][)][.]',
                '.+This is from PyMuPDF log[(][)].',
            ],
            '',
            )
    
    #
    if platform.system() != 'Windows':
        print(f'Checking redirection of everything to /dev/null.')
        check('', '', 'path:/dev/null', 'path:/dev/null')
    
    #
    print(f'Checking redirection to files.')
    path_out = os.path.abspath(f'{__file__}/../../tests/test_cli_out.out')
    path_err = os.path.abspath(f'{__file__}/../../tests/test_cli_out.err')
    check('', '', f'path:{path_out}', f'path:{path_err}')
    def read(path):
        with open(path) as f:
            return f.read()
    out = read(path_out)
    err = read(path_err)
    check_lines(['This is from PyMuPDF message[(][)][.]'], out)
    check_lines([log_prefix, '.+This is from PyMuPDF log[(][)][.]'], err)
    
    #
    print(f'Checking redirection to fds.')
    check(
            [
                'This is from PyMuPDF message[(][)][.]',
            ],
            [
                log_prefix,
                '.+This is from PyMuPDF log[(][)].',
            ],
            'fd:1',
            'fd:2',
            )


def test_use_python_logging():
    '''
    Checks pymupdf.use_python_logging().
    '''
    log_prefix = None
    if os.environ.get('PYMUPDF_USE_EXTRA') == '0':
        log_prefix = f'.+Using non-default setting from PYMUPDF_USE_EXTRA: \'0\''
    
    if os.path.basename(__file__).startswith(f'test_fitz_'):
        # Do nothing, because command `pymupdf` outputs diagnostics containing
        # `pymupdf` which are not renamed to `fitz`, which breaks our checking.
        print(f'Not testing with fitz alias.')
        return
    
    def check(
            code,
            regexes_stdout,
            regexes_stderr,
            env = None,
            ):
        code = textwrap.dedent(code)
        path = os.path.abspath(f'{__file__}/../../tests/resources_test_logging.py')
        with open(path, 'w') as f:
            f.write(code)
        command = f'{sys.executable} {path}'
        if env:
            print(f'{env=}.')
            env = os.environ | env
        print(f'Running: {command}', flush=1)
        try:
            cp = subprocess.run(command, shell=1, check=1, capture_output=1, text=True, env=env)
        except Exception as e:
            print(f'Command failed: {command}.', flush=1)
            print(f'Stdout\n{textwrap.indent(e.stdout, "    ")}', flush=1)
            print(f'Stderr\n{textwrap.indent(e.stderr, "    ")}', flush=1)
            raise
        check_lines(regexes_stdout, cp.stdout)
        check_lines(regexes_stderr, cp.stderr)
    
    print(f'## Basic use of `logging` sends output to stderr instead of default stdout.')
    check(
            '''
            import pymupdf
            pymupdf.message('this is pymupdf.message()')
            pymupdf.log('this is pymupdf.log()')
            pymupdf.set_messages(pylogging=1)
            pymupdf.set_log(pylogging=1)
            pymupdf.message('this is pymupdf.message() 2')
            pymupdf.log('this is pymupdf.log() 2')
            ''',
            [
                log_prefix,
                'this is pymupdf.message[(][)]',
                '.+this is pymupdf.log[(][)]',
            ],
            [
                'this is pymupdf.message[(][)] 2',
                '.+this is pymupdf.log[(][)] 2',
            ],
            )
    
    print(f'## Calling logging.basicConfig() makes logging output contain <LEVEL>:<name> prefixes.')
    check(
            '''
            import pymupdf
            
            import logging
            logging.basicConfig()
            pymupdf.set_messages(pylogging=1)
            pymupdf.set_log(pylogging=1)
            
            pymupdf.message('this is pymupdf.message()')
            pymupdf.log('this is pymupdf.log()')
            ''',
            [
                log_prefix,
            ],
            [
                'WARNING:pymupdf:this is pymupdf.message[(][)]',
                'WARNING:pymupdf:.+this is pymupdf.log[(][)]',
            ],
            )
    
    print(f'## Setting PYMUPDF_USE_PYTHON_LOGGING=1 makes PyMuPDF use logging on startup.')
    check(
            '''
            import pymupdf
            pymupdf.message('this is pymupdf.message()')
            pymupdf.log('this is pymupdf.log()')
            ''',
            '',
            [
                log_prefix,
                'this is pymupdf.message[(][)]',
                '.+this is pymupdf.log[(][)]',
            ],
            env = dict(
                    PYMUPDF_MESSAGE='logging:',
                    PYMUPDF_LOG='logging:',
                    ),
            )
    
    print(f'## Pass explicit logger to pymupdf.use_python_logging() with logging.basicConfig().')
    check(
            '''
            import pymupdf
            
            import logging
            logging.basicConfig()
            
            logger = logging.getLogger('foo')
            pymupdf.set_messages(pylogging_logger=logger, pylogging_level=logging.WARNING)
            pymupdf.set_log(pylogging_logger=logger, pylogging_level=logging.ERROR)
            
            pymupdf.message('this is pymupdf.message()')
            pymupdf.log('this is pymupdf.log()')
            ''',
            [
                log_prefix,
            ],
            [
                'WARNING:foo:this is pymupdf.message[(][)]',
                'ERROR:foo:.+this is pymupdf.log[(][)]',
            ],
            )
    
    print(f'## Check pymupdf.set_messages() pylogging_level args.')
    check(
            '''
            import pymupdf
            
            import logging
            logging.basicConfig(level=logging.DEBUG)
            logger = logging.getLogger('pymupdf')
            
            pymupdf.set_messages(pylogging_level=logging.CRITICAL)
            pymupdf.set_log(pylogging_level=logging.INFO)
            
            pymupdf.message('this is pymupdf.message()')
            pymupdf.log('this is pymupdf.log()')
            ''',
            [
                log_prefix,
            ],
            [
                'CRITICAL:pymupdf:this is pymupdf.message[(][)]',
                'INFO:pymupdf:.+this is pymupdf.log[(][)]',
            ],
            )
    
    print(f'## Check messages() with sys.stdout=None.')
    check(
            '''
            import sys
            sys.stdout = None
            import pymupdf
            
            pymupdf.message('this is pymupdf.message()')
            pymupdf.log('this is pymupdf.log()')
            ''',
            [],
            [],
            )
    

def relpath(path, start=None):
    '''
    A 'safe' alternative to os.path.relpath(). Avoids an exception on Windows
    if the drive needs to change - in this case we use os.path.abspath().
    '''
    try:
        return os.path.relpath(path, start)
    except ValueError:
        # os.path.relpath() fails if trying to change drives.
        assert platform.system() == 'Windows'
        return os.path.abspath(path)


def test_open():

    if not hasattr(pymupdf, 'mupdf'):
        print('test_open(): not running on classic.')
        return
    
    if pymupdf.mupdf_version_tuple < (1, 24):
        print('test_open(): not running on mupdf < 1.24.')
        return
    
    import re
    import textwrap
    import traceback
    
    resources = relpath(os.path.abspath(f'{__file__}/../../tests/resources'))
    
    # We convert all strings to use `/` instead of os.sep, which avoids
    # problems with regex's on windows.
    resources = resources.replace(os.sep, '/')
    
    def check(filename=None, stream=None, filetype=None, exception=None):
        '''
        Checks we receive expected exception if specified.
        '''
        if isinstance(filename, str):
            filename = filename.replace(os.sep, '/')
        if exception:
            etype, eregex = exception
            if isinstance(eregex, (tuple, list)):
                # Treat as sequence of regexes to look for.
                eregex = '.*'.join(eregex)
            try:
                pymupdf.open(filename=filename, stream=stream, filetype=filetype)
            except etype as e:
                text = traceback.format_exc(limit=0)
                text = text.replace(os.sep, '/')
                text = textwrap.indent(text, '    ', lambda line: 1)
                assert re.search(eregex, text, re.DOTALL), \
                        f'Incorrect exception text, expected {eregex=}, received:\n{text}'
                print(f'Received expected exception for {filename=} {stream=} {filetype=}:\n{text}')
            except Exception as e:
                assert 0, \
                        f'Incorrect exception, expected {etype}, received {type(e)=}.'
            else:
                assert 0, f'Did not received exception, expected {etype=}.'
        else:
            document = pymupdf.open(filename=filename, stream=stream, filetype=filetype)
            return document
    
    check(f'{resources}/1.pdf')
    
    check(f'{resources}/Bezier.epub')
    
    path = 1234
    etype = TypeError
    eregex = re.escape(f'bad filename: type(filename)=<class \'int\'> filename={path}.')
    check(path, exception=(etype, eregex))
    
    path = 'test_open-this-file-will-not-exist'
    etype = pymupdf.FileNotFoundError
    eregex = f'no such file: \'{path}\''
    check(path, exception=(etype, eregex))
    
    path = resources
    etype = pymupdf.FileDataError
    eregex = re.escape(f'\'{path}\' is no file')
    check(path, exception=(etype, eregex))
    
    path = relpath(os.path.abspath(f'{resources}/../test_open_empty'))
    path = path.replace(os.sep, '/')
    with open(path, 'w') as f:
        pass
    etype = pymupdf.EmptyFileError
    eregex = re.escape(f'Cannot open empty file: filename={path!r}.')
    check(path, exception=(etype, eregex))
    
    path = f'{resources}/1.pdf'
    filetype = 'xps'
    etype = pymupdf.FileDataError
    # 2023-12-12: On OpenBSD, for some reason the SWIG catch code only catches
    # the exception as FzErrorBase.
    etype2 = 'FzErrorBase' if platform.system() == 'OpenBSD' else 'FzErrorFormat'
    eregex = (
            # With a sysinstall with separate MuPDF install, we get
            # `mupdf.FzErrorFormat` instead of `pymupdf.mupdf.FzErrorFormat`. So
            # we just search for the former.
            re.escape(f'mupdf.{etype2}: code=7: cannot recognize zip archive'),
            re.escape(f'pymupdf.FileDataError: Failed to open file {path!r} as type {filetype!r}.'),
            )
    check(path, filetype=filetype, exception=(etype, eregex))
    
    path = f'{resources}/chinese-tables.pickle'
    etype = pymupdf.FileDataError
    etype2 = 'FzErrorBase' if platform.system() == 'OpenBSD' else 'FzErrorUnsupported'
    etext = (
            re.escape(f'mupdf.{etype2}: code=6: cannot find document handler for file: {path}'),
            re.escape(f'pymupdf.FileDataError: Failed to open file {path!r}.'),
            )
    check(path, exception=(etype, etext))
    
    stream = 123
    etype = TypeError
    etext = re.escape('bad stream: type(stream)=<class \'int\'>.')
    check(stream=stream, exception=(etype, etext))
    
    check(stream=b'', exception=(pymupdf.EmptyFileError, re.escape('Cannot open empty stream.')))

def test_533():
    if not hasattr(pymupdf, 'mupdf'):
        print('test_533(): Not running on classic.')
        return
    path = os.path.abspath(f'{__file__}/../../tests/resources/2.pdf')
    doc = pymupdf.open(path)
    print()
    for p in doc:
        print(f'test_533(): for p in doc: {p=}.')
    for p in list(doc)[:]:
        print(f'test_533(): for p in list(doc)[:]: {p=}.')
    for p in doc[:]:
        print(f'test_533(): for p in doc[:]: {p=}.')

def test_3354():
    document = pymupdf.open(filename)
    v = dict(foo='bar')
    document.metadata = v
    assert document.metadata == v

def test_scientific_numbers():
    '''
    This is #3381.
    '''
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    point = pymupdf.Point(1e-11, -1e-10)
    page.insert_text(point, "Test")
    contents = page.read_contents()
    print(f'{contents=}')
    if pymupdf.mupdf_version_tuple >= (1, 24, 2):
        assert b" 1e-" not in contents
    else:
        assert b" 1e-" in contents

def test_3615():
    print('')
    print(f'{pymupdf.pymupdf_version=}', flush=1)
    print(f'{pymupdf.VersionBind=}', flush=1)
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3615.epub')
    doc = pymupdf.open(path)
    print(doc.pagemode)
    print(doc.pagelayout)
    wt = pymupdf.TOOLS.mupdf_warnings()
    assert wt

def test_3654():
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3654.docx')
    content = ""
    with pymupdf.open(path) as document:
        for page in document:
            content += page.get_text() + '\n\n'
    content = content.strip()
    
    # As of 2024-07-04 we get a warning for this input file.
    wt = pymupdf.TOOLS.mupdf_warnings()
    assert wt == 'dropping unclosed output'

def test_3727():
    if pymupdf.mupdf_version_tuple < (1, 24, 9):
        print('test_3727(): not running because known to segv: {pymupdf.mupdf_version=}')
        return
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3727.pdf')
    doc = pymupdf.open(path)
    for page in doc:
        page.get_pixmap(matrix = pymupdf.Matrix(2,2))

def test_3569():
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3569.pdf')
    document = pymupdf.open(path)
    page = document[0]
    svg = page.get_svg_image(text_as_path=False)
    print(f'{svg=}')
    assert svg == (
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" version="1.1" width="3024" height="2160" viewBox="0 0 3024 2160">\n'
            '<defs>\n'
            '<clipPath id="clip_1">\n'
            '<path transform="matrix(0,-.06,-.06,-0,3024,2160)" d="M25432 10909H29692V15642H25432V10909"/>\n'
            '</clipPath>\n'
            '<clipPath id="clip_2">\n'
            '<path transform="matrix(0,-.06,-.06,-0,3024,2160)" d="M28526 38017 31807 40376V40379L31312 41314V42889H28202L25092 42888V42887L28524 38017H28526"/>\n'
            '</clipPath>\n'
            '</defs>\n'
            '<g clip-path="url(#clip_1)">\n'
            '<g inkscape:groupmode="layer" inkscape:label="CED - Text">\n'
            '<text xml:space="preserve" transform="matrix(.06 0 0 .06 3024 2160)" font-size="174.644" font-family="ArialMT"><tspan y="-28538" x="-14909 -14841.063 -14773.127 -14676.024 -14578.922 -14520.766 -14423.663">**L1-13</tspan></text>\n'
            '</g>\n'
            '</g>\n'
            '<g clip-path="url(#clip_2)">\n'
            '<g inkscape:groupmode="layer" inkscape:label="Level 03|S-COLS">\n'
            '<path transform="matrix(0,-.06,-.06,-0,3024,2160)" d="M31130 41483V42083L30530 41483ZM31130 42083 30530 41483V42083Z" fill="#7f7f7f"/>\n'
            '<path transform="matrix(0,-.06,-.06,-0,3024,2160)" stroke-width="0" stroke-linecap="butt" stroke-miterlimit="10" stroke-linejoin="miter" fill="none" stroke="#7f7f7f" d="M31130 41483V42083L30530 41483ZM31130 42083 30530 41483V42083Z"/>\n'
            '<path transform="matrix(0,-.06,-.06,-0,3024,2160)" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" fill="none" stroke="#7f7f7f" d="M30530 41483H31130V42083H30530V41483"/>\n'
            '</g>\n'
            '</g>\n'
            '</svg>\n'
            )
    wt = pymupdf.TOOLS.mupdf_warnings()
    assert wt == 'unknown cid collection: PDFAUTOCAD-Indentity0\nnon-embedded font using identity encoding: ArialMT (mapping via )\ninvalid marked content and clip nesting'

def test_3450():
    # This issue is a slow-down, so we just show time taken - it's not safe
    # to fail if test takes too long because that can give spurious failures
    # depending on hardware etc.
    #
    # On a mac-mini, PyMuPDF-1.24.8 takes 60s, PyMuPDF-1.24.9 takes 4s.
    #
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3450.pdf')
    pdf = pymupdf.open(path)
    page = pdf[0]
    t = time.time()
    pix = page.get_pixmap(alpha=False, dpi=150)
    t = time.time() - t
    print(f'test_3450(): {t=}')

def test_3859():
    if pymupdf.mupdf_version_tuple > (1, 24, 9):
        print(f'{pymupdf.mupdf.PDF_NULL=}.')
        print(f'{pymupdf.mupdf.PDF_TRUE=}.')
        print(f'{pymupdf.mupdf.PDF_FALSE=}.')
        for name in ('NULL', 'TRUE', 'FALSE'):
            name2 = f'PDF_{name}'
            v = getattr(pymupdf.mupdf, name2)
            print(f'{name=} {name2=} {v=} {type(v)=}')
            assert type(v)==pymupdf.mupdf.PdfObj, f'`v` is not a pymupdf.mupdf.PdfObj.'
    else:
        assert not hasattr(pymupdf.mupdf, 'PDF_TRUE')

def test_3905():
    data = b'A,B,C,D\r\n1,2,1,2\r\n2,2,1,2\r\n'
    try:
        document = pymupdf.open(stream=data)
    except pymupdf.FileDataError as e:
        pass
    else:
        assert 0
    wt = pymupdf.TOOLS.mupdf_warnings()
    assert wt == 'format error: cannot recognize version marker\ntrying to repair broken xref\nrepairing PDF document'

def test_3624():
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3624.pdf')
    path_png_expected = os.path.normpath(f'{__file__}/../../tests/resources/test_3624_expected.png')
    path_png = os.path.normpath(f'{__file__}/../../tests/test_3624.png')
    with pymupdf.open(path) as document:
        page = document[0]
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
        print(f'Saving to {path_png=}.')
        pixmap.save(path_png)
        rms = gentle_compare.pixmaps_rms(path_png_expected, path_png)
        if pymupdf.mupdf_version_tuple < (1, 24, 10):
            assert rms > 12
        else:
            # We get small differences in sysinstall tests, where some
            # thirdparty libraries can differ.
            assert rms < 1
