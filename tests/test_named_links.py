import fitz

import os


def test_2886():
    """Confirm correct insertion of a 'named' link."""
    if not hasattr(fitz, "mupdf"):
        print(f"test_2886(): not running on classic.")
        return

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


def test_2922():
    """Confirm correct recycling of a 'named' link.

    Re-insertion of a named link item in 'Page.get_links()' does not have
    the required "name" key. We test the fallback here that uses key
    "nameddest" instead.
    """
    if not hasattr(fitz, "mupdf"):
        print(f"test_2922(): not running on classic.")
        return

    path = os.path.abspath(f"{__file__}/../../tests/resources/cython.pdf")
    doc = fitz.open(path)
    page = doc[2]  # page has a few links, all are named
    links = page.get_links()  # list of all links
    link0 = links[0]  # take arbitrary link (1st one is ok)
    page.insert_link(link0)  # insert it again
    page = doc.reload_page(page)  # ensure page updates
    links = page.get_links()  # access all links again
    link1 = links[-1]  # re-inserted link

    # confirm equality of relevant key-values
    assert link0["nameddest"] == link1["nameddest"]
    assert link0["page"] == link1["page"]
    assert link0["to"] == link1["to"]
    assert link0["from"] == link1["from"]
