# encoding utf-8
"""
* Confirm sample doc has no links and no annots.
* Confirm proper release of file handles via Document.close()
* Confirm properly raising exceptions in document creation
"""
import io
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "001003ED.pdf")


def test_haslinks():
    doc = fitz.open(filename)
    assert doc.has_links() == False


def test_hasannots():
    doc = fitz.open(filename)
    assert doc.has_annots() == False


def test_haswidgets():
    doc = fitz.open(filename)
    assert doc.is_form_pdf == False


def test_isrepaired():
    doc = fitz.open(filename)
    assert doc.is_repaired == False
    fitz.TOOLS.mupdf_warnings()


def test_isdirty():
    doc = fitz.open(filename)
    assert doc.is_dirty == False


def test_cansaveincrementally():
    doc = fitz.open(filename)
    assert doc.can_save_incrementally() == True


def test_iswrapped():
    doc = fitz.open(filename)
    page = doc[0]
    assert page.is_wrapped


def test_wrapcontents():
    doc = fitz.open(filename)
    page = doc[0]
    page.wrap_contents()
    xref = page.get_contents()[0]
    cont = page.read_contents()
    doc.update_stream(xref, cont)
    page.set_contents(xref)
    assert len(page.get_contents()) == 1
    page.clean_contents()


def test_config():
    assert fitz.TOOLS.fitz_config["py-memory"] in (True, False)


def test_glyphnames():
    name = "infinity"
    infinity = fitz.glyph_name_to_unicode(name)
    assert fitz.unicode_to_glyph_name(infinity) == name


def test_rgbcodes():
    sRGB = 0xFFFFFF
    assert fitz.sRGB_to_pdf(sRGB) == (1, 1, 1)
    assert fitz.sRGB_to_rgb(sRGB) == (255, 255, 255)


def test_pdfstring():
    fitz.get_pdf_now()
    fitz.get_pdf_str("Beijing, chinesisch 北京")
    fitz.get_text_length("Beijing, chinesisch 北京", fontname="china-s")
    fitz.get_pdf_str("Latin characters êßöäü")


def test_open_exceptions():
    try:
        doc = fitz.open(filename, filetype="xps")
    except RuntimeError as e:
        assert repr(e).startswith("FileDataError")

    try:
        doc = fitz.open(filename, filetype="xxx")
    except Exception as e:
        assert repr(e).startswith("ValueError")

    try:
        doc = fitz.open("x.y")
    except Exception as e:
        assert repr(e).startswith("FileNotFoundError")

    try:
        doc = fitz.open("pdf", b"")
    except RuntimeError as e:
        assert repr(e).startswith("EmptyFileError")


def test_bug1945():
    pdf = fitz.open(f'{scriptdir}/resources/bug1945.pdf')
    buffer_ = io.BytesIO()
    pdf.save(buffer_, clean=True)


def test_bug1971():
    for _ in range(2):
        doc = fitz.Document(f'{scriptdir}/resources/bug1971.pdf')
        page = next(doc.pages())
        page.get_drawings()
        doc.close()

def test_default_font():
    f = fitz.Font()
    assert str(f) == "Font('Noto Serif Regular')"
    assert repr(f) == "Font('Noto Serif Regular')"

def test_add_ink_annot():
    import math
    document = fitz.Document()
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
    print(fitz.__doc__)
    doc = fitz.open()
    page = doc.new_page()
    tw = fitz.TextWriter(page.rect)
    text = "Red rectangle = TextWriter.text_rect, blue circle = .last_point"
    r = tw.append((100, 100), text)
    print(f'r={r!r}')
    tw.write_text(page)
    page.draw_rect(tw.text_rect, color=fitz.pdfcolor["red"])
    page.draw_circle(tw.last_point, 2, color=fitz.pdfcolor["blue"])
    path = f"{scriptdir}/resources/test_techwriter_append.pdf"
    doc.ez_save(path)
    print( f'Have saved to: {path}')

def test_opacity():
    doc = fitz.open()
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
    doc=fitz.open(f'{scriptdir}/resources/v110-changes.pdf')
    page=doc[0]
    blocks=page.get_text("dict")["blocks"]
    # Check no opaque types in `blocks`.
    json.dumps( blocks, indent=4)

def test_font():
    font = fitz.Font()
    print(repr(font))
    bbox = font.glyph_bbox( 65)
    print( f'bbox={bbox!r}')

def test_insert_font():
    doc=fitz.open(f'{scriptdir}/resources/v110-changes.pdf')
    page = doc[0]
    i = page.insert_font()
    print( f'page.insert_font() => {i}')

def test_2173():
    from fitz import IRect, Pixmap, CS_RGB, Colorspace
    for i in range( 100):
        #print( f'i={i!r}')
        image = Pixmap(Colorspace(CS_RGB), IRect(0, 0, 13, 37))
    print( 'test_2173() finished')

def test_texttrace():
    import time
    document = fitz.Document( f'{scriptdir}/resources/joined.pdf')
    t = time.time()
    for page in document:
        tt = page.get_texttrace()
    t = time.time() - t
    print( f'test_texttrace(): t={t!r}')
    
    # Repeat, this time writing data to file.
    import json
    path = f'{scriptdir}/resources/test_texttrace.txt'
    print( f'Writing to: {path}')
    with open( path, 'w') as f:
        for i, page in enumerate(document):
            tt = page.get_texttrace()
            print( f'page {i} json:\n{json.dumps(tt, indent="    ")}', file=f)

def test_2108():
    doc = fitz.open(f'{scriptdir}/resources/test_2108.pdf')
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
    
    print(f'fitz.mupdf_version_tuple={fitz.mupdf_version_tuple}')
    if fitz.mupdf_version_tuple >= (1, 21, 2):
        print('Asserting text==text_expected')
        assert text == text_expected
    else:
        print('Asserting text!=text_expected')
        assert text != text_expected


def test_2238():
    filepath = f'{scriptdir}/resources/test2238.pdf'
    doc = fitz.open(filepath)

    first_page = doc.load_page(0).get_text('text', fitz.INFINITE_RECT())
    last_page = doc.load_page(-1).get_text('text', fitz.INFINITE_RECT())

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
    doc = fitz.open(f'{scriptdir}/resources/test2093.pdf')

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

    rect = fitz.Rect(x0, y0, x1, y1)

    font = fitz.Font("Helvetica")
    fill_color=(0,0,0)
    page.add_redact_annot(
        quad=rect,
        #text="null",
        fontname=font.name,
        fontsize=12,
        align=fitz.TEXT_ALIGN_CENTER,
        fill=fill_color,
        text_color=(1,1,1),
    )

    page.apply_redactions()
    pixel_average_after = average_color(page)

    print(f'pixel_average_before={pixel_average_before!r}')
    print(f'pixel_average_after={pixel_average_after!r}')

    # Before this bug was fixed:
    #   pixel_average_before=[130.864323120088, 115.23577810900859, 92.9268559996174]
    #   pixel_average_after=[138.68844553555772, 123.05687162237561, 100.74275056194105]
    # After fix:
    #   pixel_average_before=[130.864323120088, 115.23577810900859, 92.9268559996174]
    #   pixel_average_after=[130.8889209934799, 115.25722751837269, 92.94327384463327]
    #
    if fitz.mupdf_version_tuple[:2] >= (1, 22):
        for i in range(len(pixel_average_before)):
            diff = pixel_average_before[i] - pixel_average_after[i]
            assert abs(diff) < 0.1

    out = f'{scriptdir}/resources/test2093-out.pdf'
    doc.save(out)
    print(f'Have written to: {out}')


def test_2182():
    print(f'test_2182() started')
    doc = fitz.open(f'{scriptdir}/resources/test2182.pdf')
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
        doc = fitz.open()
        # prepare a page with desired MediaBox / CropBox peculiarities
        mediabox = fitz.paper_rect("letter")
        page = doc.new_page(width=mediabox.width, height=mediabox.height)
        xref = page.xref
        newmbox = list(map(float, doc.xref_get_key(xref, "MediaBox")[1][1:-1].split()))
        newmbox = fitz.Rect(newmbox)
        mbox = newmbox + (10, 20, 10, 20)
        cbox = mbox + (10, 10, -10, -10)
        doc.xref_set_key(xref, "MediaBox", "[%g %g %g %g]" % tuple(mbox))
        doc.xref_set_key(xref, "CrobBox", "[%g %g %g %g]" % tuple(cbox))
        # set page to desired rotation
        page.set_rotation(rot)
        page.insert_text((50, 50), "Text inserted at (50,50)")
        tw = fitz.TextWriter(page.rect)
        tw.append((50, 50), "Text inserted at (50,50)")
        tw.write_text(page)
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            for l in b["lines"]:
                for s in l["spans"]:
                    # store bbox rounded to 3 decimal places
                    bboxes.add(fitz.Rect(fitz.JM_TUPLE3(s["bbox"])))
        return len(bboxes)  # should be 1!

    # the following tests must all pass
    assert bbox_count(0) == 1
    assert bbox_count(90) == 1
    assert bbox_count(180) == 1
    assert bbox_count(270) == 1

