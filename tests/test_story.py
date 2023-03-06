import fitz
import os


def test_story():
    otf = os.path.abspath(f'{__file__}/../resources/PragmaticaC.otf')
    CSS = f"""
        @font-face {{font-family: test; src: url({otf});}}
    """

    HTML = """
    <p style="font-family: test;color: blue">We shall meet again at a place where there is no darkness.</p>
    """

    MEDIABOX = fitz.paper_rect("letter")
    WHERE = MEDIABOX + (36, 36, -36, -36)
    # the font files are located in /home/chinese
    arch = fitz.Archive(".")
    # if not specfied user_css, the output pdf has content
    story = fitz.Story(HTML, user_css=CSS, archive=arch)  

    writer = fitz.DocumentWriter("output.pdf")

    more = 1

    while more:
        device = writer.begin_page(MEDIABOX)
        more, _ = story.place(WHERE)
        story.draw(device)
        writer.end_page()

    writer.close()
