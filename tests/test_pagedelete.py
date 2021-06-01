"""
----------------------------------------------------
This tests correct functioning of multi-page delete
----------------------------------------------------
Create a PDF in memory with 100 pages with a unique text each.
Also create a TOC with a bookmark per page.
On every page after the first to-be-deleted page, also insert a link, which
points to this page.
The bookmark text equals the text on the page for easy verification.

Then delete some pages and verify:
- the new TOC has empty items exactly for every deleted page
- the remaining TOC items still point to the correct page
- the document has no more links at all
"""
import fitz

page_count = 100  # initial document length
r = range(5, 35, 5)  # contains page numbers we will delete
# insert this link on pages after first deleted one
link = {
    "from": fitz.Rect(100, 100, 120, 120),
    "kind": fitz.LINK_GOTO,
    "page": r[0],
    "to": fitz.Point(100, 100),
}


def test_deletion():
    # First prepare the document.
    doc = fitz.open()
    toc = []
    for i in range(page_count):
        page = doc.new_page()  # make a page
        page.insert_text((100, 100), "%i" % i)  # insert unique text
        if i > r[0]:  # insert a link
            page.insert_link(link)
        toc.append([1, "%i" % i, i + 1])  # TOC bookmark to this page

    doc.set_toc(toc)  # insert the TOC
    assert doc.has_links()  # check we did insert links

    # Test page deletion.
    # Delete pages in range and verify result
    del doc[r]
    assert not doc.has_links()  # verify all links have gone
    assert doc.page_count == page_count - len(r)  # correct number deleted?
    toc_new = doc.get_toc()  # this is the modified TOC
    # verify number of emptied items (have page number -1)
    assert len([item for item in toc_new if item[-1] == -1]) == len(r)
    # Deleted page numbers must correspond to TOC items with page number -1.
    for i in r:
        assert toc_new[i][-1] == -1
    # Remaining pages must be correctly pointed to by the non-empty TOC items
    for item in toc_new:
        pno = item[-1]
        if pno == -1:  # one of the emptied items
            continue
        pno -= 1  # PDF page number
        text = doc[pno].get_text().replace("\n", "")
        # toc text must equal text on page
        assert text == item[1]

    doc.delete_page(0)  # just for the coverage stats
    del doc[5:10]
    doc.select(range(doc.page_count))
    doc.copy_page(0)
    doc.move_page(0)
    doc.fullcopy_page(0)
