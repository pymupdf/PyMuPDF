import fitz

import os


def test_2886():
    """Confirm correct insertion of a 'named' link."""
    path = os.path.abspath(f"{__file__}/../../tests/resources/cython.pdf")
    doc = fitz.open(path)
    # name "Doc-Start" is a valid named destination in that file
    link = {
        "kind": fitz.LINK_NAMED,
        "from": fitz.Rect(0, 0, 50, 50),
        "name": "Doc-Start",
    }
    # insert this link in an arbitrary page & rect
    page = doc[-1]
    page.insert_link(link)
    # need this to update the internal MuPDF annotations array
    page = doc.reload_page(page)

    # our new link must be the last in the following list
    links = page.get_links()
    l_dict = links[-1]
    assert l_dict["kind"] == fitz.LINK_NAMED
    assert l_dict["nameddest"] == link["name"]
    assert l_dict["from"] == link["from"]
