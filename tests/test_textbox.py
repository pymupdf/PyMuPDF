"""
Fill a given text in a rectangle on some PDF page using
1. TextWriter object
2. Basic text output

Check text is indeed contained in given rectangle.
"""
import fitz

text = """Der Kleine Schwertwal (Pseudorca crassidens), auch bekannt als Unechter oder Schwarzer Schwertwal, ist eine Art der Delfine (Delphinidae) und der einzige rezente Vertreter der Gattung Pseudorca.

Er ähnelt dem Orca in Form und Proportionen, ist aber einfarbig schwarz und mit einer Maximallänge von etwa sechs Metern deutlich kleiner.

Kleine Schwertwale bilden Schulen von durchschnittlich zehn bis fünfzig Tieren, wobei sie sich auch mit anderen Delfinen vergesellschaften und sich meistens abseits der Küsten aufhalten.

Sie sind in allen Ozeanen gemäßigter, subtropischer und tropischer Breiten beheimatet, sind jedoch vor allem in wärmeren Jahreszeiten auch bis in die gemäßigte bis subpolare Zone südlich der Südspitze Südamerikas, vor Nordeuropa und bis vor Kanada anzutreffen."""


def test_textbox1():
    """Use TextWriter for text insertion."""
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 400, 400)
    blue = (0, 0, 1)
    tw = fitz.TextWriter(page.rect, color=blue)
    tw.fill_textbox(
        rect,
        text,
        align=fitz.TEXT_ALIGN_LEFT,
        fontsize=12,
    )
    tw.write_text(page, morph=(rect.tl, fitz.Matrix(1, 1)))
    # check text containment
    assert page.get_text() == page.get_text(clip=rect)
    page.write_text(writers=tw)


def test_textbox2():
    """Use basic text insertion."""
    doc = fitz.open()
    ocg = doc.add_ocg("ocg1")
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 400, 400)
    blue = fitz.utils.getColor("lightblue")
    red = fitz.utils.getColorHSV("red")
    page.insert_textbox(
        rect,
        text,
        align=fitz.TEXT_ALIGN_LEFT,
        fontsize=12,
        color=blue,
        oc=ocg,
    )
    # check text containment
    assert page.get_text() == page.get_text(clip=rect)


def test_textbox3():
    """Use TextWriter for text insertion."""
    doc = fitz.open()
    page = doc.new_page()
    font = fitz.Font("cjk")
    rect = fitz.Rect(50, 50, 400, 400)
    blue = (0, 0, 1)
    tw = fitz.TextWriter(page.rect, color=blue)
    tw.fill_textbox(
        rect,
        text,
        align=fitz.TEXT_ALIGN_LEFT,
        font=font,
        fontsize=12,
        right_to_left=True,
    )
    tw.write_text(page, morph=(rect.tl, fitz.Matrix(1, 1)))
    # check text containment
    assert page.get_text() == page.get_text(clip=rect)
    doc.scrub()
    doc.subset_fonts()


def test_textbox4():
    """Use TextWriter for text insertion."""
    doc = fitz.open()
    ocg = doc.add_ocg("ocg1")
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 400, 600)
    blue = (0, 0, 1)
    tw = fitz.TextWriter(page.rect, color=blue)
    tw.fill_textbox(
        rect,
        text,
        align=fitz.TEXT_ALIGN_LEFT,
        fontsize=12,
        font=fitz.Font("cour"),
        right_to_left=True,
    )
    tw.write_text(page, oc=ocg, morph=(rect.tl, fitz.Matrix(1, 1)))
    # check text containment
    assert page.get_text() == page.get_text(clip=rect)


def test_textbox5():
    """Using basic text insertion."""
    fitz.TOOLS.set_small_glyph_heights(True)
    doc = fitz.open()
    page = doc.new_page()
    r = fitz.Rect(100, 100, 150, 150)
    text = "words and words and words and more words..."
    rc = -1
    fontsize = 12
    page.draw_rect(r)
    while rc < 0:
        rc = page.insert_textbox(
            r,
            text,
            fontsize=fontsize,
            align=fitz.TEXT_ALIGN_JUSTIFY,
        )
        fontsize -= 0.5

    blocks = page.get_text("blocks")
    bbox = fitz.Rect(blocks[0][:4])
    assert bbox in r


def test_2637():
    """Ensure correct calculation of fitting text."""
    doc = fitz.open()
    page = doc.new_page()
    text = (
        "The morning sun painted the sky with hues of orange and pink. "
        "Birds chirped harmoniously, greeting the new day. "
        "Nature awakened, filling the air with life and promise."
    )
    rect = fitz.Rect(50, 50, 500, 280)
    fontsize = 50
    rc = -1
    while rc < 0:  # look for largest font size that makes the text fit
        rc = page.insert_textbox(rect, text, fontname="hebo", fontsize=fontsize)
        fontsize -= 1

    # confirm text won't lap outside rect
    blocks = page.get_text("blocks")
    bbox = fitz.Rect(blocks[0][:4])
    assert bbox in rect


def test_htmlbox():
    """Write HTML-styled text in a rect with different rotations.

    The text is styled and contains a link.

    Assert that text is written in 4 different angles,
    assert that text properties are correct (bold, italic, color),
    assert that the link has been correctly inserterd.
    """
    rect = fitz.Rect(100, 100, 400, 300)
    text = """Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation <b>ullamco</b> <i>laboris</i> nisi ut aliquid ex ea commodi consequat. Quis aute iure reprehenderit in <span style="color: #0f0;font-weight:bold;">voluptate</span> velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui <a href="https://www.artifex.com">officia</a> deserunt mollit anim id est laborum."""

    doc = fitz.Document()
    for rot in (0, 90, 180, 270):
        wdirs = ((1, 0), (0, -1), (-1, 0), (0, 1))
        page = doc.new_page()
        page.insert_htmlbox(rect, text, rotate=rot)
        page = doc.reload_page(page)
        link = page.get_links()[0]
        assert link["uri"] == "https://www.artifex.com"
        encounters = 0
        for b in page.get_text("dict")["blocks"]:
            for l in b["lines"]:
                wdir = l["dir"]
                for s in l["spans"]:
                    stext = s["text"]
                    color = fitz.sRGB_to_pdf(s["color"])
                    bold = bool(s["flags"] & 16)
                    italic = bool(s["flags"] & 2)
                    if stext in ("ullamco", "laboris", "voluptate"):
                        encounters += 1
                        assert wdir == wdirs[page.number]
                        if stext == "ullamco":
                            assert bold is True
                            assert italic is False
                            assert color == fitz.pdfcolor["black"]
                        elif stext == "laboris":
                            assert bold is False
                            assert italic is True
                            assert color == fitz.pdfcolor["black"]
                        elif stext == "voluptate":
                            assert bold is True
                            assert italic is False
                            assert color == fitz.pdfcolor["green"]
        assert encounters == 3

