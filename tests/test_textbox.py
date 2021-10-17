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
