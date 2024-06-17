"""
Fill a given text in a rectangle on some PDF page using
1. TextWriter object
2. Basic text output

Check text is indeed contained in given rectangle.
"""
import pymupdf

text = """Der Kleine Schwertwal (Pseudorca crassidens), auch bekannt als Unechter oder Schwarzer Schwertwal, ist eine Art der Delfine (Delphinidae) und der einzige rezente Vertreter der Gattung Pseudorca.

Er ähnelt dem Orca in Form und Proportionen, ist aber einfarbig schwarz und mit einer Maximallänge von etwa sechs Metern deutlich kleiner.

Kleine Schwertwale bilden Schulen von durchschnittlich zehn bis fünfzig Tieren, wobei sie sich auch mit anderen Delfinen vergesellschaften und sich meistens abseits der Küsten aufhalten.

Sie sind in allen Ozeanen gemäßigter, subtropischer und tropischer Breiten beheimatet, sind jedoch vor allem in wärmeren Jahreszeiten auch bis in die gemäßigte bis subpolare Zone südlich der Südspitze Südamerikas, vor Nordeuropa und bis vor Kanada anzutreffen."""


def test_textbox1():
    """Use TextWriter for text insertion."""
    doc = pymupdf.open()
    page = doc.new_page()
    rect = pymupdf.Rect(50, 50, 400, 400)
    blue = (0, 0, 1)
    tw = pymupdf.TextWriter(page.rect, color=blue)
    tw.fill_textbox(
        rect,
        text,
        align=pymupdf.TEXT_ALIGN_LEFT,
        fontsize=12,
    )
    tw.write_text(page, morph=(rect.tl, pymupdf.Matrix(1, 1)))
    # check text containment
    assert page.get_text() == page.get_text(clip=rect)
    page.write_text(writers=tw)


def test_textbox2():
    """Use basic text insertion."""
    doc = pymupdf.open()
    ocg = doc.add_ocg("ocg1")
    page = doc.new_page()
    rect = pymupdf.Rect(50, 50, 400, 400)
    blue = pymupdf.utils.getColor("lightblue")
    red = pymupdf.utils.getColorHSV("red")
    page.insert_textbox(
        rect,
        text,
        align=pymupdf.TEXT_ALIGN_LEFT,
        fontsize=12,
        color=blue,
        oc=ocg,
    )
    # check text containment
    assert page.get_text() == page.get_text(clip=rect)


def test_textbox3():
    """Use TextWriter for text insertion."""
    doc = pymupdf.open()
    page = doc.new_page()
    font = pymupdf.Font("cjk")
    rect = pymupdf.Rect(50, 50, 400, 400)
    blue = (0, 0, 1)
    tw = pymupdf.TextWriter(page.rect, color=blue)
    tw.fill_textbox(
        rect,
        text,
        align=pymupdf.TEXT_ALIGN_LEFT,
        font=font,
        fontsize=12,
        right_to_left=True,
    )
    tw.write_text(page, morph=(rect.tl, pymupdf.Matrix(1, 1)))
    # check text containment
    assert page.get_text() == page.get_text(clip=rect)
    doc.scrub()
    doc.subset_fonts()


def test_textbox4():
    """Use TextWriter for text insertion."""
    doc = pymupdf.open()
    ocg = doc.add_ocg("ocg1")
    page = doc.new_page()
    rect = pymupdf.Rect(50, 50, 400, 600)
    blue = (0, 0, 1)
    tw = pymupdf.TextWriter(page.rect, color=blue)
    tw.fill_textbox(
        rect,
        text,
        align=pymupdf.TEXT_ALIGN_LEFT,
        fontsize=12,
        font=pymupdf.Font("cour"),
        right_to_left=True,
    )
    tw.write_text(page, oc=ocg, morph=(rect.tl, pymupdf.Matrix(1, 1)))
    # check text containment
    assert page.get_text() == page.get_text(clip=rect)


def test_textbox5():
    """Using basic text insertion."""
    small_glyph_heights0 = pymupdf.TOOLS.set_small_glyph_heights()
    pymupdf.TOOLS.set_small_glyph_heights(True)
    try:
        doc = pymupdf.open()
        page = doc.new_page()
        r = pymupdf.Rect(100, 100, 150, 150)
        text = "words and words and words and more words..."
        rc = -1
        fontsize = 12
        page.draw_rect(r)
        while rc < 0:
            rc = page.insert_textbox(
                r,
                text,
                fontsize=fontsize,
                align=pymupdf.TEXT_ALIGN_JUSTIFY,
            )
            fontsize -= 0.5

        blocks = page.get_text("blocks")
        bbox = pymupdf.Rect(blocks[0][:4])
        assert bbox in r
    finally:
        # Must restore small_glyph_heights, otherwise other tests can fail.
        pymupdf.TOOLS.set_small_glyph_heights(small_glyph_heights0)


def test_2637():
    """Ensure correct calculation of fitting text."""
    doc = pymupdf.open()
    page = doc.new_page()
    text = (
        "The morning sun painted the sky with hues of orange and pink. "
        "Birds chirped harmoniously, greeting the new day. "
        "Nature awakened, filling the air with life and promise."
    )
    rect = pymupdf.Rect(50, 50, 500, 280)
    fontsize = 50
    rc = -1
    while rc < 0:  # look for largest font size that makes the text fit
        rc = page.insert_textbox(rect, text, fontname="hebo", fontsize=fontsize)
        fontsize -= 1

    # confirm text won't lap outside rect
    blocks = page.get_text("blocks")
    bbox = pymupdf.Rect(blocks[0][:4])
    assert bbox in rect


def test_htmlbox1():
    """Write HTML-styled text into a rect with different rotations.

    The text is styled and contains a link.
    Then extract the text again, and
    - assert that text was written in the 4 different angles,
    - assert that text properties are correct (bold, italic, color),
    - assert that the link has been correctly inserted.

    We try to insert into a rectangle that is too small, setting
    scale=False and confirming we have a negative return code.
    """
    if not hasattr(pymupdf, "mupdf"):
        print("'test_htmlbox1' not executed in classic.")
        return

    rect = pymupdf.Rect(100, 100, 200, 200)  # this only works with scale=True

    base_text = """Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat. Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""

    text = """Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation <b>ullamco</b> <i>laboris</i> nisi ut aliquid ex ea commodi consequat. Quis aute iure reprehenderit in <span style="color: #0f0;font-weight:bold;">voluptate</span> velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui <a href="https://www.artifex.com">officia</a> deserunt mollit anim id est laborum."""

    doc = pymupdf.Document()

    for rot in (0, 90, 180, 270):
        wdirs = ((1, 0), (0, -1), (-1, 0), (0, 1))  # all writing directions
        page = doc.new_page()
        spare_height, scale = page.insert_htmlbox(rect, text, rotate=rot, scale_low=1)
        assert spare_height < 0
        assert scale == 1
        spare_height, scale = page.insert_htmlbox(rect, text, rotate=rot, scale_low=0)
        assert spare_height == 0
        assert 0 < scale < 1
        page = doc.reload_page(page)
        link = page.get_links()[0]  # extracts the links on the page

        assert link["uri"] == "https://www.artifex.com"

        # Assert plain text is complete.
        # We must remove line breaks and any ligatures for this.
        assert base_text == page.get_text(flags=0)[:-1].replace("\n", " ")

        encounters = 0  # counts the words with selected properties
        for b in page.get_text("dict")["blocks"]:
            for l in b["lines"]:
                wdir = l["dir"]  # writing direction
                assert wdir == wdirs[page.number]
                for s in l["spans"]:
                    stext = s["text"]
                    color = pymupdf.sRGB_to_pdf(s["color"])
                    bold = bool(s["flags"] & 16)
                    italic = bool(s["flags"] & 2)
                    if stext in ("ullamco", "laboris", "voluptate"):
                        encounters += 1
                        if stext == "ullamco":
                            assert bold is True
                            assert italic is False
                            assert color == pymupdf.pdfcolor["black"]
                        elif stext == "laboris":
                            assert bold is False
                            assert italic is True
                            assert color == pymupdf.pdfcolor["black"]
                        elif stext == "voluptate":
                            assert bold is True
                            assert italic is False
                            assert color == pymupdf.pdfcolor["green"]
                    else:
                        assert bold is False
                        assert italic is False
        # all 3 special special words were encountered
        assert encounters == 3


def test_htmlbox2():
    """Test insertion without scaling"""
    if not hasattr(pymupdf, "mupdf"):
        print("'test_htmlbox2' not executed in classic.")
        return

    doc = pymupdf.open()
    rect = pymupdf.Rect(100, 100, 200, 200)  # large enough to hold text
    page = doc.new_page()
    bottoms = set()
    for rot in (0, 90, 180, 270):
        spare_height, scale = page.insert_htmlbox(
            rect, "Hello, World!", scale_low=1, rotate=rot
        )
        assert scale == 1
        assert 0 < spare_height < rect.height
        bottoms.add(spare_height)
    assert len(bottoms) == 1  # same result for all rotations


def test_htmlbox3():
    """Test insertion with opacity"""
    if not hasattr(pymupdf, "mupdf"):
        print("'test_htmlbox3' not executed in classic.")
        return

    rect = pymupdf.Rect(100, 250, 300, 350)
    text = """<span style="color:red;font-size:20px;">Just some text.</span>"""
    doc = pymupdf.open()
    page = doc.new_page()

    # insert some text with opacity
    page.insert_htmlbox(rect, text, opacity=0.5)

    # lowlevel-extract inserted text to access opacity
    span = page.get_texttrace()[0]
    assert span["opacity"] == 0.5


def test_3559():
    if pymupdf.mupdf_version_tuple < (1, 24, 4):
        print(f'test_3559(): Not running because mupdf known to SEGV.')
        return
    doc = pymupdf.Document()
    page = doc.new_page()
    text_insert="""<body><h3></h3></body>"""
    rect = pymupdf.Rect(100, 100, 200, 200)
    page.insert_htmlbox(rect, text_insert)
