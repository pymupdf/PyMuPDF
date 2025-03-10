"""
Tests for the Font class.
"""
import pymupdf
import os

def test_font1():
    text = "PyMuPDF"
    font = pymupdf.Font("helv")
    assert font.name == "Helvetica"
    tl = font.text_length(text, fontsize=20)
    cl = font.char_lengths(text, fontsize=20)
    assert len(text) == len(cl)
    assert abs(sum(cl) - tl) < pymupdf.EPSILON
    for i in range(len(cl)):
        assert cl[i] == font.glyph_advance(ord(text[i])) * 20
    font2 = pymupdf.Font(fontbuffer=font.buffer)
    codepoints1 = font.valid_codepoints()
    codepoints2 = font2.valid_codepoints()
    print('')
    print(f'{len(codepoints1)=}')
    print(f'{len(codepoints2)=}')
    if 0:
        for i, (ucs1, ucs2) in enumerate(zip(codepoints1, codepoints2)):
            print(f'    {i}: {ucs1=} {ucs2=} {"" if ucs2==ucs2 else "*"}')
    assert font2.valid_codepoints() == font.valid_codepoints()
    
    # Also check we can get font's bbox.
    bbox1 = font.bbox
    print(f'{bbox1=}')
    if hasattr(pymupdf, 'mupdf'):
        bbox2 = font.this.fz_font_bbox()
        assert bbox2 == bbox1


def test_font2():
    """Old and new length computation must be the same."""
    font = pymupdf.Font("helv")
    text = "PyMuPDF"
    assert font.text_length(text) == pymupdf.get_text_length(text)


def test_fontname():
    """Assert a valid PDF fontname."""
    doc = pymupdf.open()
    page = doc.new_page()
    assert page.insert_font()  # assert: a valid fontname works!
    detected = False  # preset indicator
    try:  # fontname check will fail first - don't need a font at all here
        page.insert_font(fontname="illegal/char", fontfile="unimportant")
    except ValueError as e:
        if str(e).startswith("bad fontname chars"):
            detected = True  # illegal fontname detected
    assert detected

def test_2608():
    flags = (pymupdf.TEXT_DEHYPHENATE | pymupdf.TEXT_MEDIABOX_CLIP)
    with pymupdf.open(os.path.abspath(f'{__file__}/../../tests/resources/2201.00069.pdf')) as doc:
        page = doc[0]
        blocks = page.get_text_blocks(flags=flags)
        text = blocks[10][4]
        with open(os.path.abspath(f'{__file__}/../../tests/test_2608_out'), 'wb') as f:
            f.write(text.encode('utf8'))
        path_expected = os.path.normpath(f'{__file__}/../../tests/resources/test_2608_expected')
        with open(path_expected, 'rb') as f:
            expected = f.read().decode('utf8')
        # Github windows x32 seems to insert \r characters; maybe something to
        # do with the Python installation's line endings settings.
        expected = expected.replace('\r', '')
        print(f'test_2608(): {text.encode("utf8")=}')
        print(f'test_2608(): {expected.encode("utf8")=}')
        assert text == expected

def test_fontarchive():
    import subprocess
    arch = pymupdf.Archive()
    css = pymupdf.css_for_pymupdf_font("notos", archive=arch, name="sans-serif")
    print(css)
    print(arch.entry_list)
    assert arch.entry_list == \
            [
                {
                    'fmt': 'tree',
                    'entries':
                    [
                        'notosbo', 'notosbi', 'notosit', 'notos'
                    ],
                    'path': None
                }
            ]

def test_load_system_font():
    if not hasattr(pymupdf, 'mupdf'):
        print(f'test_load_system_font(): Not running on classic.')
        return
    trace = list()
    def font_f(name, bold, italic, needs_exact_metrics):
        trace.append((name, bold, italic, needs_exact_metrics))
        print(f'test_load_system_font():font_f(): Looking for font: {name=} {bold=} {italic=} {needs_exact_metrics=}.')
        return None
    def f_cjk(name, ordering, serif):
        trace.append((name, ordering, serif))
        print(f'test_load_system_font():f_cjk(): Looking for font: {name=} {ordering=} {serif=}.')
        return None
    def f_fallback(script, language, serif, bold, italic):
        trace.append((script, language, serif, bold, italic))
        print(f'test_load_system_font():f_fallback(): looking for font: {script=} {language=} {serif=} {bold=} {italic=}.')
        return None
    pymupdf.mupdf.fz_install_load_system_font_funcs(font_f, f_cjk, f_fallback)
    f = pymupdf.mupdf.fz_load_system_font("some-font-name", 0, 0, 0)
    assert trace == [
            ('some-font-name', 0, 0, 0),
            ], f'Incorrect {trace=}.'
    print(f'test_load_system_font(): {f.m_internal=}')


def test_mupdf_subset_fonts2():
    if not hasattr(pymupdf, 'mupdf'):
        print('Not running on rebased.')
        return
    path = os.path.abspath(f'{__file__}/../../tests/resources/2.pdf')
    with pymupdf.open(path) as doc:
        n = len(doc)
        pages = [i*2 for i in range(n//2)]
        print(f'{pages=}.')
        pymupdf.mupdf.pdf_subset_fonts2(pymupdf._as_pdf_document(doc), pages)


def test_3677():
    pymupdf.TOOLS.set_subset_fontnames(True)
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_3677.pdf')
    font_names_expected = [
            'BCDEEE+Aptos',
            'BCDFEE+Aptos',
            'BCDGEE+Calibri-Light',
            'BCDHEE+Calibri-Light',
            ]
    font_names = list()
    with pymupdf.open(path) as document:
        for page in document:
             for block in page.get_text('dict')['blocks']:
                    if block['type'] == 0:
                        if 'lines' in block.keys():
                            for line in block['lines']:
                                for span in line['spans']:
                                    font_name=span['font']
                                    print(font_name)
                                    font_names.append(font_name)
    assert font_names == font_names_expected, f'{font_names=}'


def test_3933():
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3933.pdf')
    with pymupdf.open(path) as document:
        page = document[0]
        print(f'{len(page.get_fonts())=}')
    
        expected = {
                'BCDEEE+Calibri': 39,
                'BCDFEE+SwissReSan-Regu':  53,
                'BCDGEE+SwissReSan-Ital':  20,
                'BCDHEE+SwissReSan-Bold':  20,
                'BCDIEE+SwissReSan-Regu':  53,
                'BCDJEE+Calibri':  39,
                }
                
        for xref, _, _, name, _, _ in page.get_fonts():
            _, _, _, content = document.extract_font(xref)

            if content:
                font = pymupdf.Font(fontname=name, fontbuffer=content)
                supported_symbols = font.valid_codepoints()
                print(f'Font {name}: {len(supported_symbols)=}.', flush=1)
                if pymupdf.mupdf_version_tuple < (1, 24, 11):
                    assert len(supported_symbols) == 0
                else:
                    assert len(supported_symbols) == expected.get(name)


def test_3780():
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3780.pdf')
    with pymupdf.open(path) as document:
        for page_i, page in enumerate(document):
            for itm in page.get_fonts():
                buff=document.extract_font(itm[0])[-1]
                font=pymupdf.Font(fontbuffer=buff)
                print(f'{page_i=}: xref {itm[0]} {font.name=} {font.ascender=} {font.descender=}.')
            if page_i == 0:
                d = page.get_text('dict')
                #for n, v in d.items():
                #    print(f'    {n}: {v!r}')
                for i, block in enumerate(d['blocks']):
                    print(f'block {i}:')
                    for j, line in enumerate(block['lines']):
                        print(f'    line {j}:')
                        for k, span in enumerate(line['spans']):
                            print(f'        span {k}:')
                            for n, v in span.items():
                                print(f'            {n}: {v!r}')


def test_3887():
    print(f'{pymupdf.version=}')
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3887.pdf')
    
    path2 = os.path.normpath(f'{__file__}/../../tests/resources/test_3887.pdf.ez.pdf')
    with pymupdf.open(path) as document:
        document.subset_fonts(fallback=False)
        document.ez_save(path2)
    
    with pymupdf.open(path2) as document:
        text = f"\u0391\u3001\u0392\u3001\u0393\u3001\u0394\u3001\u0395\u3001\u0396\u3001\u0397\u3001\u0398\u3001\u0399\u3001\u039a\u3001\u039b\u3001\u039c\u3001\u039d\u3001\u039e\u3001\u039f\u3001\u03a0\u3001\u03a1\u3001\u03a3\u3001\u03a4\u3001\u03a5\u3001\u03a6\u3001\u03a7\u3001\u03a8\u3001\u03a9\u3002\u03b1\u3001\u03b2\u3001\u03b3\u3001\u03b4\u3001\u03b5\u3001\u03b6\u3001\u03b7\u3001\u03b8\u3001\u03b9\u3001\u03ba\u3001\u03bb\u3001\u03bc\u3001\u03bd\u3001\u03be\u3001\u03bf\u3001\u03c0\u3001\u03c1\u3001\u03c2\u3001\u03c4\u3001\u03c5\u3001\u03c6\u3001\u03c7\u3001\u03c8\u3001\u03c9\u3002"
        page = document[0]
        chars = [c for b in page.get_text("rawdict",flags=0)["blocks"] for l in b["lines"] for s in l["spans"] for c in s["chars"]]
        output = [c["c"] for c in chars]
        print(f'text:\n    {text}')
        print(f'output:\n    {output}')
        pixmap = page.get_pixmap()
        path_pixmap = f'{path}.0.png'
        pixmap.save(path_pixmap)
        print(f'Have saved to: {path_pixmap=}')
        assert set(output)==set(text)

