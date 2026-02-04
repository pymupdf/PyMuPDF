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

import os

import pymupdf

scriptdir = os.path.dirname(__file__)
page_count = 100  # initial document length
r = range(5, 35, 5)  # contains page numbers we will delete
# insert this link on pages after first deleted one
link = {
    "from": pymupdf.Rect(100, 100, 120, 120),
    "kind": pymupdf.LINK_GOTO,
    "page": r[0],
    "to": pymupdf.Point(100, 100),
}


def test_deletion():
    # First prepare the document.
    doc = pymupdf.open()
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


def test_3094():
    path = os.path.abspath(f"{__file__}/../../tests/resources/test_2871.pdf")
    document = pymupdf.open(path)
    pnos = [i for i in range(0, document.page_count, 2)]
    document.delete_pages(pnos)


def test_3150():
    """Assert correct functioning for problem file.

    Implicitly also check use of new MuPDF function
    pdf_rearrange_pages() since version 1.23.9.
    """
    filename = os.path.join(scriptdir, "resources", "test-3150.pdf")
    pages = [3, 3, 3, 2, 3, 1, 0, 0]
    doc = pymupdf.open(filename)
    doc.select(pages)
    assert doc.page_count == len(pages)


def test_4462():
    path0 = os.path.normpath(f'{__file__}/../../tests/resources/test_4462_0.pdf')
    path1 = os.path.normpath(f'{__file__}/../../tests/resources/test_4462_1.pdf')
    path2 = os.path.normpath(f'{__file__}/../../tests/resources/test_4462_2.pdf')
    with pymupdf.open() as document:
        document.new_page()
        document.new_page()
        document.new_page()
        document.new_page()
        document.save(path0)
    with pymupdf.open(path0) as document:
        assert len(document) == 4
        document.delete_page(-1)
        document.save(path1)
    with pymupdf.open(path1) as document:
        assert len(document) == 3
        document.delete_pages(-1)
        document.save(path2)
    with pymupdf.open(path2) as document:
        assert len(document) == 2


def test_4790():
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_4790.pdf')
    path2 = os.path.normpath(f'{__file__}/../../tests/test_4790_out.pdf')
    print()
    page_to_delete = 1
    
    # Reproduce the problem.
    with pymupdf.open(path) as document:
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert not wt, f'{wt=}'
        assert len(document) == 2, f'{len(document)=}'
        document.delete_pages(page_to_delete)
        assert len(document) == 1, f'{len(document)=}'
        document.save(path2)
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == 'repairing PDF document', f'{wt=}'
    with pymupdf.open(path2) as document:
        # Expect incorrect result.
        assert len(document) == 2, f'{len(document)=}'

    # Call mupdf.pdf_repair_xref() before delete_pages(); this works around the
    # problem.
    with pymupdf.open(path) as document:
        document_pdf = pymupdf._as_pdf_document(document)
        pymupdf.mupdf.pdf_repair_xref(document_pdf)
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == 'repairing PDF document', f'{wt=}'
        document.delete_pages(page_to_delete)
        document.save(path2)
    with pymupdf.open(path2) as document:
        # Expect correct result.
        assert len(document) == 1

    # Call mupdf.pdf_check_document() before delete_pages(); this works around
    # the problem.
    with pymupdf.open(path) as document:
        document_pdf = pymupdf._as_pdf_document(document)
        pymupdf.mupdf.pdf_check_document(document_pdf)
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == 'repairing PDF document', f'{wt=}'
        document.delete_pages(page_to_delete)
        document.save(path2)
    with pymupdf.open(path2) as document:
        # Expect correct result.
        assert len(document) == 1

    # Check that document is marked as repaired after save.
    with pymupdf.open(path) as document:
        assert not document.is_repaired, f'{document.is_repaired=}'
        document.save(path2)
        assert document.is_repaired, f'{document.is_repaired=}'
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == 'repairing PDF document', f'{wt=}'
    
    # Check that raise_on_repair=True works.
    with pymupdf.open(path) as document:
        try:
            document.save(path2, raise_on_repair=True)
        except Exception as e:
            print(f'Received expected exception: {e}', flush=1)
        else:
            assert 0, 'Did not get expected exception.'
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == 'repairing PDF document'
    
    # Check that Document.repair() works.
    with pymupdf.open(path) as document:
        document.repair()
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == 'repairing PDF document'
        document.delete_pages(page_to_delete)
        document.save(path2, raise_on_repair=True)
    with pymupdf.open(path2) as document:
        # Expect correct result.
        assert len(document) == 1, f'{len(document)=}'
    
