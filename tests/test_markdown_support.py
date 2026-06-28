import pymupdf
import os
import textwrap


def test_archive_markdown():
    """Test Archive support."""
    if pymupdf.mupdf_version_tuple < (1, 28, 0):
        print("no testing on MuPDF < 1.28.0")
        return

    path = os.path.abspath(f"{__file__}/../../tests/resources")
    md = b"![](nur-ruhig.jpg)\n\n**A referenced image.**"
    md_doc = pymupdf.open(stream=md, filetype="md", archive=path)
    pdfdata = md_doc.convert_to_pdf()
    doc = pymupdf.open(stream=pdfdata)
    page = doc[0]
    images = page.get_image_info()
    assert len(images) == 1

def test_archive_links():
    """Create an internal and an external link and confirm
    that they are correctly converted to PDF links."""
    if pymupdf.mupdf_version_tuple < (1, 28, 0):
        print("no testing on MuPDF < 1.28.0")
        return

    md = """Some text containing an external [link](http://www.google.com) to Google.
    Now an internal link to a header in this document: [Some Header](#some-header). The header is here:

    <h2 id="some-header">Some Header</h2>

    Some text following the header.
    """
    md_doc = pymupdf.open(stream=md.encode(), filetype="md")
    pdfdata = md_doc.convert_to_pdf()
    doc = pymupdf.open(stream=pdfdata)
    page = doc[0]
    links=page.get_links()
    assert len(links) == 2
    assert links[0]["uri"] == "http://www.google.com"
    assert links[0]["kind"] == pymupdf.LINK_URI
    assert links[1]["kind"] == pymupdf.LINK_GOTO


def test_markdown_style():
    print()
    if pymupdf.mupdf_version_tuple < (1, 28):
        print('test_markdown_style(): not running because mupdf<1.28.')
        return
    
    font = pymupdf.Font("tiro")
    arch = pymupdf.Archive(font.buffer, "tiro")

    css = """@font-face {font-family: sans-serif; src: url(tiro);}"""
    md = "Overriding sans-serif with Times-Roman."
    for use_css in 0, 1:
        md_doc = pymupdf.open(stream=md.encode(), filetype="md", archive=arch)
        if use_css:
            md_doc.apply_css(css)  # apply the CSS to the document

        md_pdf_stream = md_doc.convert_to_pdf()
        with pymupdf.open(stream=md_pdf_stream) as pdf_doc:
            page = pdf_doc[0]
            spans = [
                s for b in page.get_text("dict")["blocks"] for l in b["lines"] for s in l["spans"]
            ]

        assert len(spans) == 1
        print(f'test_markdown_style(): {use_css=} {spans[0]["font"]=}.')
        if use_css:
            assert "Roman" in spans[0]["font"]
        else:
            assert "Roman" not in spans[0]["font"]

def test_markdown_save():
    md = textwrap.dedent('''
            # title
            
            ## section
            
            text
            ''')
    with pymupdf.open(stream=md.encode(), filetype='md') as document_md:
        out_pdf = os.path.normpath(f'{__file__}/../../tests/test_markdown_save.pdf')
        document_md.save(out_pdf)


def test_markdown_bad_unicode():
    path_md = os.path.normpath(f'{__file__}/../../tests/resources/test_markdown_bad_unicode.md')
    path_md_pdf = os.path.normpath(f'{__file__}/../../tests/test_markdown_bad_unicode.md.pdf')
    with pymupdf.open(path_md) as md_doc:
        md_doc.save(path_md_pdf)
    
    # To check that pymupdf has done the right thing, we extract text from our
    # generated pdf and assert that it is as expected.
    with pymupdf.open(path_md_pdf) as document:
        text = document[0].get_text()
    textb = text.encode('utf8')
    print()
    print(textwrap.indent(text, '    '))
    print(f'textb:')
    for line in textb.split(b'\n'):
        print(f'    {line}')
    print(f'{pymupdf.mupdf_version_tuple=}')
    if pymupdf.mupdf_version_tuple > (1, 28, 0):
        textb_expected = (
                b'Title',
                b'A Table',
                b'Boiling Points \xc8\xb9C',
                b'min',
                b'max',
                b'avg',
                b'Noble gases',
                b'-269',
                b'-62',
                b'-170.5',
                b'Nonmetals',
                b'-253',
                b'4827',
                b'414.1',
                b'Metalloids',
                b'335',
                b'3900',
                b'741.5',
                b'Metals',
                b'357',
                b'>5000',
                b'2755.9',
                b'A List',
                b'\xe2\x80\xa2  Comment 1',
                b'\xe2\x80\xa2  Comment 2',
                b'\xe2\x80\xa2  Comment 3 with a link to Find out more',
                b'My TO-DOs',
                b'\xe2\x80\xa2  \xe2\x98\x92 Done!',
                b'\xe2\x80\xa2  \xe2\x98\x92 Also done!',
                b'\xe2\x80\xa2  \xe2\x98\x90 Still open',
                b'',
                )
    else:
        # Table is not recognised because it contains illegal utf8 sequence.
        textb_expected = (
                b'Title',
                b'A Table',
                b'|Boiling Points \xc8\xb9C|min|max|avg| |---|---|---|---| |Noble',
                b'gases|-269|-62|-170.5| |Nonmetals|-253|4827|414.1| |Metalloids|',
                b'335|3900|741.5| |Metals|357|>5000|2755.9|',
                b'A List',
                b'\xe2\x80\xa2  Comment 1',
                b'\xe2\x80\xa2  Comment 2',
                b'\xe2\x80\xa2  Comment 3 with a link to Find out more',
                b'My TO-DOs',
                b'\xe2\x80\xa2  \xe2\x98\x92 Done!',
                b'\xe2\x80\xa2  \xe2\x98\x92 Also done!',
                b'\xe2\x80\xa2  \xe2\x98\x90 Still open',
                b'',
                )
    textb_expected = b'\n'.join(textb_expected)
    if textb != textb_expected:
        print(f'textb_expected:')
        for line in textb_expected.split(b'\n'):
            print(f'    {line}')
    assert textb == textb_expected
