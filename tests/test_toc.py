"""
* Verify equality of generated TOCs and expected results.
* Verify TOC deletion works
* Verify manipulation of single TOC item works
* Verify stability against circular TOC items
"""

import os
import sys
import pymupdf
import pathlib

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "001003ED.pdf")
filename2 = os.path.join(scriptdir, "resources", "2.pdf")
circular = os.path.join(scriptdir, "resources", "circular-toc.pdf")
full_toc = os.path.join(scriptdir, "resources", "full_toc.txt")
simple_toc = os.path.join(scriptdir, "resources", "simple_toc.txt")
doc = pymupdf.open(filename)


def test_simple_toc():
    simple_lines = open(simple_toc, "rb").read()
    toc = b"".join([str(t).encode() for t in doc.get_toc(True)])
    assert toc == simple_lines


def test_full_toc():
    if not hasattr(pymupdf, "mupdf"):
        # Classic implementation does not have fix for this test.
        print(f"Not running test_full_toc on classic implementation.")
        return
    expected_path = f"{scriptdir}/resources/full_toc.txt"
    expected = pathlib.Path(expected_path).read_bytes()
    # Github windows x32 seems to insert \r characters; maybe something to
    # do with the Python installation's line endings settings.
    expected = expected.decode("utf8")
    expected = expected.replace('\r', '')
    toc = "\n".join([str(t) for t in doc.get_toc(False)])
    toc += "\n"
    assert toc == expected


def test_erase_toc():
    doc.set_toc([])
    assert doc.get_toc() == []


def test_replace_toc():
    toc = doc.get_toc(False)
    doc.set_toc(toc)


def test_setcolors():
    doc = pymupdf.open(filename2)
    toc = doc.get_toc(False)
    for i in range(len(toc)):
        d = toc[i][3]
        d["color"] = (1, 0, 0)
        d["bold"] = True
        d["italic"] = True
        doc.set_toc_item(i, dest_dict=d)

    toc2 = doc.get_toc(False)
    assert len(toc2) == len(toc)

    for t in toc2:
        d = t[3]
        assert d["bold"]
        assert d["italic"]
        assert d["color"] == (1, 0, 0)


def test_circular():
    """The test file contains circular bookmarks."""
    doc = pymupdf.open(circular)
    toc = doc.get_toc(False)  # this must not loop
    rebased = hasattr(pymupdf, 'mupdf')
    if rebased:
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == 'Bad or missing prev pointer in outline tree, repairing', \
                f'{wt=}'

def test_2355():
    
    # Create a test PDF with toc.
    doc = pymupdf.Document()
    for _ in range(10):
        doc.new_page(doc.page_count)
    doc.set_toc([[1, 'test', 1], [1, 'test2', 5]])
    
    path = 'test_2355.pdf'
    doc.save(path)

    # Open many times
    for i in range(10):
        with pymupdf.open(path) as new_doc:
            new_doc.get_toc()

    # Open once and read many times
    with pymupdf.open(path) as new_doc:
        for i in range(10):
            new_doc.get_toc()

def test_2788():
    '''
    Check handling of Document.get_toc() when toc item has kind=4.
    '''
    if not hasattr(pymupdf, 'mupdf'):
        # Classic implementation does not have fix for this test.
        print(f'Not running test_2788 on classic implementation.')
        return
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_2788.pdf')        
    document = pymupdf.open(path)
    toc0 = [[1, 'page2', 2, {'kind': 4, 'xref': 14, 'page': 1, 'to': pymupdf.Point(100.0, 760.0), 'zoom': 0.0, 'nameddest': 'page.2'}]]
    toc1 = document.get_toc(simple=False)
    print(f'{toc0=}')
    print(f'{toc1=}')
    assert toc1 == toc0
    
    doc.set_toc(toc0)
    toc2 = document.get_toc(simple=False)
    print(f'{toc0=}')
    print(f'{toc2=}')
    assert toc2 == toc0
    
    # Also test Page.get_links() bugfix from #2817.
    for page in document:
        page.get_links()
    rebased = hasattr(pymupdf, 'mupdf')
    if rebased:
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt == (
                "syntax error: expected 'obj' keyword (0 3 ?)\n"
                "trying to repair broken xref\n"
                "repairing PDF document"
                ), f'{wt=}'
