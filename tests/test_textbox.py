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
    tw.write_text(page)
    # check text containment
    assert page.get_text() == page.get_text(clip=rect)


def test_textbox2():
    """Basic text insertion."""
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 400, 400)
    blue = (0, 0, 1)
    page.insert_textbox(
        rect,
        text,
        align=fitz.TEXT_ALIGN_LEFT,
        fontsize=12,
        color=blue,
    )
    # check text containment
    assert page.get_text() == page.get_text(clip=rect)
