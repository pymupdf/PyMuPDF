"""
* Verify equality of generated TOCs and expected results.
* Verify TOC deletion works
* Verify manipulation of single TOC item works
* Verify stability against circular TOC items
"""
import os
import sys
import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "001003ED.pdf")
filename2 = os.path.join(scriptdir, "resources", "2.pdf")
circular = os.path.join(scriptdir, "resources", "circular-toc.pdf")
full_toc = os.path.join(scriptdir, "resources", "full_toc.txt")
simple_toc = os.path.join(scriptdir, "resources", "simple_toc.txt")
doc = fitz.open(filename)


def test_simple_toc():
    simple_lines = open(simple_toc, "rb").read()
    toc = b"".join([str(t).encode() for t in doc.get_toc(True)])
    assert toc == simple_lines


def test_full_toc():
    if fitz.mupdf_version_tuple >= (1, 23, 0):
        # MuPDF changed in 7d41466feaa.
        expected_path = f'{scriptdir}/resources/full_toc2.txt'
    else:
        expected_path = f'{scriptdir}/resources/full_toc.txt'
    with open(expected_path, encoding='utf8') as f:
        expected = f.read()
    toc = '\n'.join([str(t) for t in doc.get_toc(False)])
    toc += '\n'
    assert toc == expected


def test_erase_toc():
    doc.set_toc([])
    assert doc.get_toc() == []


def test_replace_toc():
    toc = doc.get_toc(False)
    doc.set_toc(toc)


def test_setcolors():
    doc = fitz.open(filename2)
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
    doc = fitz.open(circular)
    toc = doc.get_toc(False)  # this must not loop

def test_2355():
    
    # Create a test PDF with toc.
    doc = fitz.Document()
    for _ in range(10):
        doc.new_page(doc.page_count)
    doc.set_toc([[1, 'test', 1], [1, 'test2', 5]])
    
    path = 'test_2355.pdf'
    doc.save(path)

    # Open many times
    for i in range(10):
        with fitz.open(path) as new_doc:
            new_doc.get_toc()

    # Open once and read many times
    with fitz.open(path) as new_doc:
        for i in range(10):
            new_doc.get_toc()

def test_2788():
    '''
    Check handling of Document.get_toc() when toc item has kind=4.
    '''
    if not hasattr(fitz, 'mupdf'):
        # Classic implementation does not have fix for this test.
        print(f'Not running test_2788 on classic implementation.')
        return
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_2788.pdf')        
    document = fitz.open(path)
    toc0 = [[1, 'page2', 2, {'kind': 4, 'xref': 14, 'page': 1, 'to': fitz.Point(100.0, 760.0), 'zoom': 0.0, 'nameddest': 'page.2'}]]
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
