import pymupdf

import os


def test_page_links_generator():
    # open some arbitrary PDF
    path = os.path.abspath(f"{__file__}/../../tests/resources/2.pdf")
    doc = pymupdf.open(path)

    # select an arbitrary page
    page = doc[-1]

    # iterate over pages.links
    link_generator = page.links()
    links = list(link_generator)
    assert len(links) == 7
