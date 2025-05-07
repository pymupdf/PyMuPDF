# -*- coding: utf-8 -*-
"""
Test PDF annotation insertions.
"""

import os
import platform

import pymupdf
import gentle_compare


red = (1, 0, 0)
blue = (0, 0, 1)
gold = (1, 1, 0)
green = (0, 1, 0)
scriptdir = os.path.dirname(__file__)

displ = pymupdf.Rect(0, 50, 0, 50)
r = pymupdf.Rect(72, 72, 220, 100)
t1 = "têxt üsès Lätiñ charß,\nEUR: €, mu: µ, super scripts: ²³!"
rect = pymupdf.Rect(100, 100, 200, 200)


def test_caret():
    doc = pymupdf.open()
    page = doc.new_page()
    annot = page.add_caret_annot(rect.tl)
    assert annot.type == (14, "Caret")
    annot.update(rotate=20)
    page.annot_names()
    page.annot_xrefs()


def test_freetext():
    doc = pymupdf.open()
    page = doc.new_page()
    annot = page.add_freetext_annot(
        rect,
        t1,
        fontsize=10,
        rotate=90,
        text_color=blue,
        fill_color=gold,
        align=pymupdf.TEXT_ALIGN_CENTER,
    )
    annot.set_border(width=0.3, dashes=[2])
    annot.update(text_color=blue, fill_color=gold)
    assert annot.type == (2, "FreeText")


def test_text():
    doc = pymupdf.open()
    page = doc.new_page()
    annot = page.add_text_annot(r.tl, t1)
    assert annot.type == (0, "Text")


def test_highlight():
    doc = pymupdf.open()
    page = doc.new_page()
    annot = page.add_highlight_annot(rect)
    assert annot.type == (8, "Highlight")


def test_underline():
    doc = pymupdf.open()
    page = doc.new_page()
    annot = page.add_underline_annot(rect)
    assert annot.type == (9, "Underline")


def test_squiggly():
    doc = pymupdf.open()
    page = doc.new_page()
    annot = page.add_squiggly_annot(rect)
    assert annot.type == (10, "Squiggly")


def test_strikeout():
    doc = pymupdf.open()
    page = doc.new_page()
    annot = page.add_strikeout_annot(rect)
    assert annot.type == (11, "StrikeOut")
    page.delete_annot(annot)


def test_polyline():
    doc = pymupdf.open()
    page = doc.new_page()
    rect = page.rect + (100, 36, -100, -36)
    cell = pymupdf.make_table(rect, rows=10)
    for i in range(10):
        annot = page.add_polyline_annot((cell[i][0].bl, cell[i][0].br))
        annot.set_line_ends(i, i)
        annot.update()
    for i, annot in enumerate(page.annots()):
        assert annot.line_ends == (i, i)
    assert annot.type == (7, "PolyLine")


def test_polygon():
    doc = pymupdf.open()
    page = doc.new_page()
    annot = page.add_polygon_annot([rect.bl, rect.tr, rect.br, rect.tl])
    assert annot.type == (6, "Polygon")


def test_line():
    doc = pymupdf.open()
    page = doc.new_page()
    rect = page.rect + (100, 36, -100, -36)
    cell = pymupdf.make_table(rect, rows=10)
    for i in range(10):
        annot = page.add_line_annot(cell[i][0].bl, cell[i][0].br)
        annot.set_line_ends(i, i)
        annot.update()
    for i, annot in enumerate(page.annots()):
        assert annot.line_ends == (i, i)
    assert annot.type == (3, "Line")


def test_square():
    doc = pymupdf.open()
    page = doc.new_page()
    annot = page.add_rect_annot(rect)
    assert annot.type == (4, "Square")


def test_circle():
    doc = pymupdf.open()
    page = doc.new_page()
    annot = page.add_circle_annot(rect)
    assert annot.type == (5, "Circle")


def test_fileattachment():
    doc = pymupdf.open()
    page = doc.new_page()
    annot = page.add_file_annot(rect.tl, b"just anything for testing", "testdata.txt")
    assert annot.type == (17, "FileAttachment")


def test_stamp():
    doc = pymupdf.open()
    page = doc.new_page()
    annot = page.add_stamp_annot(r, stamp=0)
    assert annot.type == (13, "Stamp")
    assert annot.info["content"] == "Approved"
    annot_id = annot.info["id"]
    annot_xref = annot.xref
    page.load_annot(annot_id)
    page.load_annot(annot_xref)
    page = doc.reload_page(page)


def test_image_stamp():
    doc = pymupdf.open()
    page = doc.new_page()
    filename = os.path.join(scriptdir, "resources", "nur-ruhig.jpg")
    annot = page.add_stamp_annot(r, stamp=filename)
    assert annot.info["content"] == "Image Stamp"


def test_redact1():
    doc = pymupdf.open()
    page = doc.new_page()
    annot = page.add_redact_annot(r, text="Hello")
    annot.update(
        cross_out=True,
        rotate=-1,
    )
    assert annot.type == (12, "Redact")
    annot.get_pixmap()
    info = annot.info
    annot.set_info(info)
    assert not annot.has_popup
    annot.set_popup(r)
    s = annot.popup_rect
    assert s == r
    page.apply_redactions()


def test_redact2():
    """Test for keeping text and removing graphics."""
    if not hasattr(pymupdf, "mupdf"):
        print("Not executing 'test_redact2' in classic")
        return
    filename = os.path.join(scriptdir, "resources", "symbol-list.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    all_text0 = page.get_text("words")
    page.add_redact_annot(page.rect)
    page.apply_redactions(text=1)
    t = page.get_text("words")
    assert t == all_text0
    assert not page.get_drawings()


def test_redact3():
    """Test for removing text and graphics."""
    if not hasattr(pymupdf, "mupdf"):
        print("Not executing 'test_redact3' in classic")
        return
    filename = os.path.join(scriptdir, "resources", "symbol-list.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    page.add_redact_annot(page.rect)
    page.apply_redactions()
    assert not page.get_text("words")
    assert not page.get_drawings()


def test_redact4():
    """Test for removing text and keeping graphics."""
    if not hasattr(pymupdf, "mupdf"):
        print("Not executing 'test_redact4' in classic")
        return
    filename = os.path.join(scriptdir, "resources", "symbol-list.pdf")
    doc = pymupdf.open(filename)
    page = doc[0]
    line_art = page.get_drawings()
    page.add_redact_annot(page.rect)
    page.apply_redactions(graphics=0)
    assert not page.get_text("words")
    assert line_art == page.get_drawings()


def test_1645():
    '''
    Test fix for #1645.
    '''
    # The expected output files assume annot_stem is 'jorj'. We need to always
    # restore this before returning (this is checked by conftest.py).
    annot_stem = pymupdf.JM_annot_id_stem
    pymupdf.TOOLS.set_annot_stem('jorj')
    try:
        path_in = os.path.abspath( f'{__file__}/../resources/symbol-list.pdf')
        path_expected = os.path.abspath( f'{__file__}/../../tests/resources/test_1645_expected.pdf')
        path_out = os.path.abspath( f'{__file__}/../test_1645_out.pdf')
        doc = pymupdf.open(path_in)
        page = doc[0]
        page_bounds = page.bound()
        annot_loc = pymupdf.Rect(page_bounds.x0, page_bounds.y0, page_bounds.x0 + 75, page_bounds.y0 + 15)
        # Check type of page.derotation_matrix - this is #2911.
        assert isinstance(page.derotation_matrix, pymupdf.Matrix), \
                f'Bad type for page.derotation_matrix: {type(page.derotation_matrix)=} {page.derotation_matrix=}.'
        page.add_freetext_annot(
                annot_loc * page.derotation_matrix,
                "TEST",
                fontsize=18,
                fill_color=pymupdf.utils.getColor("FIREBRICK1"),
                rotate=page.rotation,
                )
        doc.save(path_out, garbage=1, deflate=True, no_new_id=True)
        print(f'Have created {path_out}. comparing with {path_expected}.')
        with open( path_out, 'rb') as f:
            out = f.read()
        with open( path_expected, 'rb') as f:
            expected = f.read()
        assert out == expected, f'Files differ: {path_out} {path_expected}'
    finally:
        # Restore annot_stem.
        pymupdf.TOOLS.set_annot_stem(annot_stem)

def test_1824():
    '''
    Test for fix for #1824: SegFault when applying redactions overlapping a
    transparent image.
    '''
    path = os.path.abspath( f'{__file__}/../resources/test_1824.pdf')
    doc=pymupdf.open(path)
    page=doc[0]
    page.apply_redactions()

def test_2270():
    '''
    https://github.com/pymupdf/PyMuPDF/issues/2270
    '''
    path = os.path.abspath( f'{__file__}/../../tests/resources/test_2270.pdf')
    with pymupdf.open(path) as document:
        for page_number, page in enumerate(document):
            for textBox in page.annots(types=(pymupdf.PDF_ANNOT_FREE_TEXT,pymupdf.PDF_ANNOT_TEXT)):
                print("textBox.type :", textBox.type)
                print(f"{textBox.rect=}")
                print("textBox.get_text('words') : ", textBox.get_text('words'))
                print("textBox.get_text('text') : ", textBox.get_text('text'))
                print("textBox.get_textbox(textBox.rect) : ", textBox.get_textbox(textBox.rect))
                print("textBox.info['content'] : ", textBox.info['content'])
                assert textBox.type == (2, 'FreeText')
                assert textBox.get_text('words')[0][4] == 'abc123'
                assert textBox.get_text('text') == 'abc123\n'
                assert textBox.get_textbox(textBox.rect) == 'abc123'
                assert textBox.info['content'] == 'abc123'

                # Additional check that Annot.get_textpage() returns a
                # TextPage that works with page.get_text() - prior to
                # 2024-01-30 the TextPage had no `.parent` member.
                textpage = textBox.get_textpage()
                text = page.get_text()
                print(f'{text=}')
                text = page.get_text(textpage=textpage)
                print(f'{text=}')
                print(f'{getattr(textpage, "parent")=}')

                if pymupdf.mupdf_version_tuple >= (1, 26):
                    # Check Annotation.get_textpage()'s <clip> arg.
                    clip = textBox.rect
                    clip.x1 = clip.x0 + (clip.x1 - clip.x0) / 3
                    textpage2 = textBox.get_textpage(clip=clip)
                    text = textpage2.extractText()
                    print(f'With {clip=}: {text=}')
                    assert text == 'ab\n'
                else:
                    assert not hasattr(pymupdf.mupdf, 'FZ_STEXT_CLIP_RECT')
                    

def test_2934_add_redact_annot():
    '''
    Test fix for bug mentioned in #2934.
    '''
    path = os.path.abspath(f'{__file__}/../../tests/resources/mupdf_explored.pdf')
    with open(path, 'rb') as f:
        data = f.read()
    doc = pymupdf.Document(stream=data)
    print(f'Is PDF: {doc.is_pdf}')
    print(f'Number of pages: {doc.page_count}')

    import json
    page=doc[0]
    page_json_str =doc[0].get_text("json")
    page_json_data = json.loads(page_json_str)
    span=page_json_data.get("blocks")[0].get("lines")[0].get("spans")[0]
    page.add_redact_annot(span["bbox"], text="")
    page.apply_redactions()

def test_2969():
    '''
    https://github.com/pymupdf/PyMuPDF/issues/2969
    '''
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_2969.pdf')
    doc = pymupdf.open(path)
    page = doc[0]
    first_annot = list(page.annots())[0]
    first_annot.next

def test_file_info():
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_annot_file_info.pdf')
    document = pymupdf.open(path)
    results = list()
    for i, page in enumerate(document):
        print(f'{i=}')
        annotations = page.annots()
        for j, annotation in enumerate(annotations):
            print(f'{j=} {annotation=}')
            t = annotation.type
            print(f'{t=}')
            if t[0] == pymupdf.PDF_ANNOT_FILE_ATTACHMENT:
                file_info = annotation.file_info
                print(f'{file_info=}')
                results.append(file_info)
    assert results == [
            {'filename': 'example.pdf', 'description': '', 'length': 8416, 'size': 8992},
            {'filename': 'photo1.jpeg', 'description': '', 'length': 10154, 'size': 8012},
            ]

def test_3131():
    doc = pymupdf.open()
    page = doc.new_page()

    page.add_line_annot((0, 0), (1, 1))
    page.add_line_annot((1, 0), (0, 1))

    first_annot, _ = page.annots()
    first_annot.next.type

def test_3209():
    pdf = pymupdf.Document(filetype="pdf")
    page = pdf.new_page()
    page.add_ink_annot([[(300,300), (400, 380), (350, 350)]])
    n = 0
    for annot in page.annots():
        n += 1
        assert annot.vertices == [[(300.0, 300.0), (400.0, 380.0), (350.0, 350.0)]]
    assert n == 1
    path = os.path.abspath(f'{__file__}/../../tests/test_3209_out.pdf')
    pdf.save(path)  # Check the output PDF that the annotation is correctly drawn

def test_3863():
    path_in = os.path.normpath(f'{__file__}/../../tests/resources/test_3863.pdf')
    path_out = os.path.normpath(f'{__file__}/../../tests/test_3863.pdf.pdf')
    
    # Create redacted PDF.
    print(f'Loading {path_in=}.')
    with pymupdf.open(path_in) as document:
    
        for num, page in enumerate(document):
            print(f"Page {num + 1} - {page.rect}:")
    
            for image in page.get_images(full=True):
                print(f"  - Image: {image}")

            redact_rect = page.rect

            if page.rotation in (90, 270):
                redact_rect = pymupdf.Rect(0, 0, page.rect.height, page.rect.width)

            page.add_redact_annot(redact_rect)
            page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)

        print(f'Writing to {path_out=}.')
        document.save(path_out)
    
    with pymupdf.open(path_out) as document:
        assert len(document) == 8
        
        # Create PNG for each page of redacted PDF.
        for num, page in enumerate(document):
            path_png = f'{path_out}.{num}.png'
            pixmap = page.get_pixmap()
            print(f'Writing to {path_png=}.')
            pixmap.save(path_png)
            # Compare with expected png.
    
        print(f'Comparing page PNGs with expected PNGs.')
        for num, _ in enumerate(document):
            path_png = f'{path_out}.{num}.png'
            path_png_expected = f'{path_in}.pdf.{num}.png'
            print(f'{path_png=}.')
            print(f'{path_png_expected=}.')
            rms = gentle_compare.pixmaps_rms(path_png, path_png_expected, '    ')
            # We get small differences in sysinstall tests, where some
            # thirdparty libraries can differ.
            assert rms < 1

def test_3758():
    # This test requires input file that is not public, so is usually not
    # available.
    path = os.path.normpath(f'{__file__}/../../../test_3758.pdf')
    if not os.path.exists(path):
        print(f'test_3758(): not running because does not exist: {path=}.')
        return
    import json
    with pymupdf.open(path) as document:
        for page in document:
            info = json.loads(page.get_text('json', flags=pymupdf.TEXTFLAGS_TEXT))
            for block_ind, block in enumerate(info['blocks']):
                for line_ind, line in enumerate(block['lines']):
                    for span_ind, span in enumerate(line['spans']):
                        # print(span)
                        page.add_redact_annot(pymupdf.Rect(*span['bbox']))
            page.apply_redactions()
    wt = pymupdf.TOOLS.mupdf_warnings()
    assert wt


def test_parent():
    """Test invalidating parent on page re-assignment."""
    doc = pymupdf.open()
    page = doc.new_page()
    a = page.add_highlight_annot(page.rect)  # insert annotation on page 0
    page = doc.new_page()  # make a new page, should orphanate annotation
    try:
        print(a)  # should raise
    except Exception as e:
        if platform.system() == 'OpenBSD':
            assert isinstance(e, pymupdf.mupdf.FzErrorBase), f'Incorrect {type(e)=}.'
        else:
            assert isinstance(e, pymupdf.mupdf.FzErrorArgument), f'Incorrect {type(e)=}.'
        assert str(e) == 'code=4: annotation not bound to any page', f'Incorrect error text {str(e)=}.'
    else:
        assert 0, f'Failed to get expected exception.'

def test_4047():
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_4047.pdf')
    with pymupdf.open(path) as document:
        page = document[0]
        fontname = page.get_fonts()[0][3]
        if fontname not in pymupdf.Base14_fontnames:
            fontname = "Courier"
        hits = page.search_for("|")
        for rect in hits:
            page.add_redact_annot(
                rect, " ", fontname=fontname, align=pymupdf.TEXT_ALIGN_CENTER, fontsize=10
            )  # Segmentation Fault...
        page.apply_redactions()

def test_4079():
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_4079.pdf')
    if pymupdf.mupdf_version_tuple >= (1, 25, 5):
        path_after = os.path.normpath(f'{__file__}/../../tests/resources/test_4079_after.pdf')
    else:
        # 2024-11-27 Expect incorrect behaviour.
        path_after = os.path.normpath(f'{__file__}/../../tests/resources/test_4079_after_1.25.pdf')
        
    path_out = os.path.normpath(f'{__file__}/../../tests/test_4079_out')
    with pymupdf.open(path_after) as document_after:
        page = document_after[0]
        pixmap_after_expected = page.get_pixmap()
    with pymupdf.open(path) as document:
        page = document[0]
        rects = [
                [164,213,282,227],
                [282,213,397,233],
                [434,209,525,243],
                [169,228,231,243],
                [377,592,440,607],
                [373,611,444,626],
                ]
        for rect in rects:
            page.add_redact_annot(rect, fill=(1,0,0))
            page.draw_rect(rect, color=(0, 1, 0))
        document.save(f'{path_out}_before.pdf')
        page.apply_redactions(images=0)
        pixmap_after = page.get_pixmap()
        document.save(f'{path_out}_after.pdf')
        rms = gentle_compare.pixmaps_rms(pixmap_after_expected, pixmap_after)
        diff = gentle_compare.pixmaps_diff(pixmap_after_expected, pixmap_after)
        path = os.path.normpath(f'{__file__}/../../tests/test_4079_diff.png')
        diff.save(path)
        print(f'{rms=}')
        assert rms == 0

def test_4254():
    """Ensure that both annotations are fully created

    We do this by asserting equal top-used colors in respective pixmaps.
    """
    doc = pymupdf.open()
    page = doc.new_page()

    rect = pymupdf.Rect(100, 100, 200, 150)
    annot = page.add_freetext_annot(rect, "Test Annotation from minimal example")
    annot.set_border(width=1, dashes=(3, 3))
    annot.set_opacity(0.5)
    try:
        annot.set_colors(stroke=(1, 0, 0))
    except ValueError as e:
        assert 'cannot be used for FreeText annotations' in str(e), f'{e}'
    else:
        assert 0
    annot.update()

    rect = pymupdf.Rect(200, 200, 400, 400)
    annot2 = page.add_freetext_annot(rect, "Test Annotation from minimal example pt 2")
    annot2.set_border(width=1, dashes=(3, 3))
    annot2.set_opacity(0.5)
    try:
        annot2.set_colors(stroke=(1, 0, 0))
    except ValueError as e:
        assert 'cannot be used for FreeText annotations' in str(e), f'{e}'
    else:
        assert 0
    annot.update()
    annot2.update()

    # stores top color for each pixmap
    top_colors = set()
    for annot in page.annots():
        pix = annot.get_pixmap()
        top_colors.add(pix.color_topusage()[1])

    # only one color must exist
    assert len(top_colors) == 1

def test_richtext():
    """Test creation of rich text FreeText annotations.

    We create the same annotation on different pages in different ways,
    with and without using Annotation.update(), and then assert equality
    of the respective images.
    """
    ds = """font-size: 11pt; font-family: sans-serif;"""
    bullet = chr(0x2610) + chr(0x2611) + chr(0x2612)
    text = f"""<p style="text-align:justify;margin-top:-25px;">
    PyMuPDF <span style="color: red;">འདི་ ཡིག་ཆ་བཀྲམ་སྤེལ་གྱི་དོན་ལུ་ པའི་ཐོན་ཐུམ་སྒྲིལ་དྲག་ཤོས་དང་མགྱོགས་ཤོས་ཅིག་ཨིན།</span>
    <span style="color:blue;">Here is some <b>bold</b> and <i>italic</i> text, followed by <b><i>bold-italic</i></b>. Text-based check boxes: {bullet}.</span>
    </p>"""
    gold = (1, 1, 0)
    doc = pymupdf.open()

    # First page.
    page = doc.new_page()
    rect = pymupdf.Rect(100, 100, 350, 200)
    p2 = rect.tr + (50, 30)
    p3 = p2 + (0, 30)
    annot = page.add_freetext_annot(
        rect,
        text,
        fill_color=gold,
        opacity=0.5,
        rotate=90,
        border_width=1,
        dashes=None,
        richtext=True,
        callout=(p3, p2, rect.tr),
    )

    pix1 = page.get_pixmap()

    # Second page.
    # the annotation is created with minimal parameters, which are supplied
    # in a separate call to the .update() method.
    page = doc.new_page()
    annot = page.add_freetext_annot(
        rect,
        text,
        border_width=1,
        dashes=None,
        richtext=True,
        callout=(p3, p2, rect.tr),
    )
    annot.update(fill_color=gold, opacity=0.5, rotate=90)
    pix2 = page.get_pixmap()
    assert pix1.samples == pix2.samples


def test_4447():
    document = pymupdf.open()
    
    page = document.new_page()

    text_color = (1, 0, 0)
    fill_color = (0, 1, 0)
    border_color = (0, 0, 1)

    annot_rect = pymupdf.Rect(90.1, 486.73, 139.26, 499.46)

    try:
        annot = page.add_freetext_annot(
            annot_rect,
            "AETERM",
            fontname="Arial",
            fontsize=10,
            text_color=text_color,
            fill_color=fill_color,
            border_color=border_color,
            border_width=1,
        )
    except ValueError as e:
        assert 'cannot set border_color if rich_text is False' in str(e), str(e)
    else:
        assert 0
    
    try:
        annot = page.add_freetext_annot(
                (30, 400, 100, 450),
                "Two",
                fontname="Arial",
                fontsize=10,
                text_color=text_color,
                fill_color=fill_color,
                border_color=border_color,
                border_width=1,
                )
    except ValueError as e:
        assert 'cannot set border_color if rich_text is False' in str(e), str(e)
    else:
        assert 0
    
    annot = page.add_freetext_annot(
            (30, 500, 100, 550),
            "Three",
            fontname="Arial",
            fontsize=10,
            text_color=text_color,
            border_width=1,
            )
    annot.update(text_color=text_color, fill_color=fill_color)
    try:
        annot.update(border_color=border_color)
    except ValueError as e:
        assert 'cannot set border_color if rich_text is False' in str(e), str(e)
    else:
        assert 0
    
    path_out = os.path.normpath(f'{__file__}/../../tests/test_4447.pdf')
    document.save(path_out)
