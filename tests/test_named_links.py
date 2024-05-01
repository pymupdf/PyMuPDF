import pymupdf

import os


def test_2886():
    """Confirm correct insertion of a 'named' link."""
    if not hasattr(pymupdf, "mupdf"):
        print(f"test_2886(): not running on classic.")
        return

    path = os.path.abspath(f"{__file__}/../../tests/resources/cython.pdf")
    doc = pymupdf.open(path)
    # name "Doc-Start" is a valid named destination in that file
    link = {
        "kind": pymupdf.LINK_NAMED,
        "from": pymupdf.Rect(0, 0, 50, 50),
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
    assert l_dict["kind"] == pymupdf.LINK_NAMED
    assert l_dict["nameddest"] == link["name"]
    assert l_dict["from"] == link["from"]


def test_2922():
    """Confirm correct recycling of a 'named' link.

    Re-insertion of a named link item in 'Page.get_links()' does not have
    the required "name" key. We test the fallback here that uses key
    "nameddest" instead.
    """
    if not hasattr(pymupdf, "mupdf"):
        print(f"test_2922(): not running on classic.")
        return

    path = os.path.abspath(f"{__file__}/../../tests/resources/cython.pdf")
    doc = pymupdf.open(path)
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


def test_3301():
    """Test correct differentiation between URI and LAUNCH links.

    Links encoded as /URI in PDF are converted to either LINK_URI or
    LINK_LAUNCH in PyMuPDF.
    This function ensures that the 'Link.uri' containing a ':' colon
    is converted to a URI if not explicitly starting with "file://".
    """
    if not hasattr(pymupdf, "mupdf"):
        print(f"test_3301(): not running on classic.")
        return

    # list of links and their expected link "kind" upon extraction
    text = {
        "https://www.google.de": pymupdf.LINK_URI,
        "http://www.google.de": pymupdf.LINK_URI,
        "mailto:jorj.x.mckie@outlook.de": pymupdf.LINK_URI,
        "www.wikipedia.de": pymupdf.LINK_LAUNCH,
        "awkward:resource": pymupdf.LINK_URI,
        "ftp://www.google.de": pymupdf.LINK_URI,
        "some.program": pymupdf.LINK_LAUNCH,
        "file://some.program": pymupdf.LINK_LAUNCH,
        "another.exe": pymupdf.LINK_LAUNCH,
    }

    # make enough "from" rectangles
    r = pymupdf.Rect(0, 0, 50, 20)
    rects = [r + (0, r.height * i, 0, r.height * i) for i in range(len(text.keys()))]

    # make test page and insert above links as kind=LINK_URI
    doc = pymupdf.open()
    page = doc.new_page()
    for i, k in enumerate(text.keys()):
        link = {"kind": pymupdf.LINK_URI, "uri": k, "from": rects[i]}
        page.insert_link(link)

    # re-cycle the PDF preparing for link extraction
    pdfdata = doc.write()
    doc = pymupdf.open("pdf", pdfdata)
    page = doc[0]
    for link in page.get_links():
        # Extract the link text. Must be 'file' or 'uri'.
        t = link["uri"] if (_ := link.get("file")) is None else _
        assert text[t] == link["kind"]
