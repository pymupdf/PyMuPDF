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


def test_toc_count():
    file_in = os.path.abspath(f'{__file__}/../../tests/resources/test_toc_count.pdf')
    file_out = os.path.abspath(f'{__file__}/../../tests/test_toc_count_out.pdf')

    def get(doc):
        outlines = doc.xref_get_key(doc.pdf_catalog(), "Outlines")
        ret = doc.xref_object(int(outlines[1].split()[0]))
        return ret
    print()
    with pymupdf.open(file_in) as doc:
        print(f'1: {get(doc)}')
        toc = doc.get_toc(simple=False)
        doc.set_toc([])
        #print(f'2: {get(doc)}')
        doc.set_toc(toc)
        print(f'3: {get(doc)}')
        doc.save(file_out, garbage=4)
    with pymupdf.open(file_out) as doc:
        print(f'4: {get(doc)}')
    pymupdf._log_items_clear()


def test_3347():
    '''
    Check fix for #3347 - link destination rectangles when source/destination
    pages have different sizes.
    '''
    doc = pymupdf.open()
    doc.new_page(width=500, height=800)
    doc.new_page(width=800, height=500)
    rects = [
        (0, pymupdf.Rect(10, 20, 50, 40), pymupdf.utils.getColor('red')),
        (0, pymupdf.Rect(300, 350, 400, 450), pymupdf.utils.getColor('green')),
        (1, pymupdf.Rect(20, 30, 40, 50), pymupdf.utils.getColor('blue')),
        (1, pymupdf.Rect(350, 300, 450, 400), pymupdf.utils.getColor('black'))
    ]

    for page, rect, color in rects:
        doc[page].draw_rect(rect, color=color)

    for (from_page, from_rect, _), (to_page, to_rect, _) in zip(rects, rects[1:] + rects[:1]):
        doc[from_page].insert_link({
            'kind': 1,
            'from': from_rect,
            'page': to_page,
            'to': to_rect.top_left,
        })

    links_expected = [
            (0, {'kind': 1, 'xref': 11, 'from': pymupdf.Rect(10.0, 20.0, 50.0, 40.0), 'page': 0, 'to': pymupdf.Point(300.0, 350.0), 'zoom': 0.0, 'id': 'jorj-L0'}),
            (0, {'kind': 1, 'xref': 12, 'from': pymupdf.Rect(300.0, 350.0, 400.0, 450.0), 'page': 1, 'to': pymupdf.Point(20.0, 30.0), 'zoom': 0.0, 'id': 'jorj-L1'}),
            (1, {'kind': 1, 'xref': 13, 'from': pymupdf.Rect(20.0, 30.0, 40.0, 50.0), 'page': 1, 'to': pymupdf.Point(350.0, 300.0), 'zoom': 0.0, 'id': 'jorj-L0'}),
            (1, {'kind': 1, 'xref': 14, 'from': pymupdf.Rect(350.0, 300.0, 450.0, 400.0), 'page': 0, 'to': pymupdf.Point(10.0, 20.0), 'zoom': 0.0, 'id': 'jorj-L1'}),
            ]

    path = os.path.normpath(f'{__file__}/../../tests/test_3347_out.pdf')
    doc.save(path)
    print(f'Have saved to {path=}.')

    links_actual = list()
    for page_i, page in enumerate(doc):
        links = page.get_links()
        for link_i, link in enumerate(links):
            print(f'{page_i=} {link_i=}: {link!r}')
            links_actual.append( (page_i, link) )
    
    assert links_actual == links_expected


def test_3400():
    '''
    Check fix for #3400 - link destination rectangles when source/destination
    pages have different rotations.
    '''
    width = 750
    height = 1110
    circle_middle_point = pymupdf.Point(height / 4, width / 4)
    print(f'{circle_middle_point=}')
    with pymupdf.open() as doc:
        
        page = doc.new_page(width=width, height=height)
        page.set_rotation(270)
        # draw a circle at the middle point to facilitate debugging
        page.draw_circle(circle_middle_point, color=(0, 0, 1), radius=5, width=2)
        
        for i in range(10):
            for j in range(10):
                x = i/10 * width
                y = j/10 * height
                page.draw_circle(pymupdf.Point(x, y), color=(0,0,0), radius=0.2, width=0.1)
                page.insert_htmlbox(pymupdf.Rect(x, y, x+width/10, y+height/20), f'<small><small><small><small>({x=:.1f},{y=:.1f})</small></small></small></small>', )

        # rotate the middle point by the page rotation for the new toc entry
        toc_link_coords = circle_middle_point
        print(f'{toc_link_coords=}')
        
        toc = [
            (
                1,
                "Link to circle",
                1,
                {
                    "kind": pymupdf.LINK_GOTO,
                    "page": 1,
                    "to": toc_link_coords,
                    "from": pymupdf.Rect(0, 0, height / 4, width / 4),
                },
            )
        ]
        doc.set_toc(toc, 0)  # set the toc
        
        page = doc.new_page(width=200, height=300)
        from_rect = pymupdf.Rect(10, 10, 100, 50)
        page.insert_htmlbox(from_rect, 'link')
        link = dict()
        link['from'] = from_rect
        link['kind'] = pymupdf.LINK_GOTO
        link['to'] = toc_link_coords
        link['page'] = 0
        page.insert_link(link)
        
        path = os.path.normpath(f'{__file__}/../../tests/test_3400.pdf')
        doc.save(path)
        print(f'Saved to {path=}.')
        
        links_expected = [
                (1, {'kind': 1, 'xref': 1120, 'from': pymupdf.Rect(10.0, 10.0, 100.0, 50.0), 'page': 0, 'to': pymupdf.Point(187.5, 472.5), 'zoom': 0.0, 'id': 'jorj-L0'})
                ]

        links_actual = list()
        for page_i, page in enumerate(doc):
            links = page.get_links()
            for link_i, link in enumerate(links):
                print(f'({page_i}, {link!r})')
                links_actual.append( (page_i, link) )
    
        assert links_actual == links_expected
