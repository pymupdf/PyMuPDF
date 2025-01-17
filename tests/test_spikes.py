import pymupdf
import pathlib
import os


def test_spikes():
    """Check suppression of text spikes caused by long miters."""
    root = os.path.abspath(f"{__file__}/../..")
    spikes_yes = pathlib.Path(f"{root}/docs/images/spikes-yes.png")
    spikes_no = pathlib.Path(f"{root}/docs/images/spikes-no.png")
    doc = pymupdf.open()
    text = "NATO MEMBERS"  # some text provoking spikes ("N", "M")
    point = (10, 35)  # insert point

    # make text provoking spikes
    page = doc.new_page(width=200, height=50)  # small page
    page.insert_text(
        point,
        text,
        fontsize=20,
        render_mode=1,  # stroke text only
        border_width=0.3,  # causes thick border lines
        miter_limit=None,  # do not care about miter spikes
    )
    # write same text in white over the previous for better demo purpose
    page.insert_text(point, text, fontsize=20, color=(1, 1, 1))
    pix1 = page.get_pixmap()
    assert pix1.tobytes() == spikes_yes.read_bytes()

    # make text suppressing spikes
    page = doc.new_page(width=200, height=50)
    page.insert_text(
        point,
        text,
        fontsize=20,
        render_mode=1,
        border_width=0.3,
        miter_limit=1,  # suppress each and every miter spike
    )
    page.insert_text(point, text, fontsize=20, color=(1, 1, 1))
    pix2 = page.get_pixmap()
    assert pix2.tobytes() == spikes_no.read_bytes()
