"""
* Join multiple PDFs into a new one.
* Compare with stored earlier result:
    - must have identical object definitions
    - must have different trailers
* Try inserting files in a loop.
"""

import io
import os
import re
import pymupdf

scriptdir = os.path.abspath(os.path.dirname(__file__))
resources = os.path.join(scriptdir, "resources")

def approx_parse( text):
    '''
    Splits <text> into sequence of (text, number) pairs. Where sequence of
    [0-9.] is not convertible to a number (e.g. '4.5.6'), <number> will be
    None.
    '''
    ret = []
    for m in re.finditer('([^0-9]+)([0-9.]*)', text):
        text = m.group(1)
        try:
            number = float( m.group(2))
        except Exception:
            text += m.group(2)
            number = None
        ret.append( (text, number))
    return ret

def approx_compare( a, b, max_delta):
    '''
    Compares <a> and <b>, allowing numbers to differ by up to <delta>.
    '''
    aa = approx_parse( a)
    bb = approx_parse( b)
    if len(aa) != len(bb):
        return 1
    ret = 1
    for (at, an), (bt, bn) in zip( aa, bb):
        if at != bt:
            break
        if an is not None and bn is not None:
            if abs( an - bn) >= max_delta:
                print( f'diff={an-bn}: an={an} bn={bn}')
                break
        elif (an is None) != (bn is None):
            break
    else:
        ret = 0
    if ret:
        print( f'Differ:\n    a={a!r}\n    b={b!r}')
    return ret
        

def test_insert():
    all_text_original = []  # text on input pages
    all_text_combined = []  # text on resulting output pages
    # prepare input PDFs
    doc1 = pymupdf.open()
    for i in range(5):  # just arbitrary number of pages
        text = f"doc 1, page {i}"  # the 'globally' unique text
        page = doc1.new_page()
        page.insert_text((100, 72), text)
        all_text_original.append(text)

    doc2 = pymupdf.open()
    for i in range(4):
        text = f"doc 2, page {i}"
        page = doc2.new_page()
        page.insert_text((100, 72), text)
        all_text_original.append(text)

    doc3 = pymupdf.open()
    for i in range(3):
        text = f"doc 3, page {i}"
        page = doc3.new_page()
        page.insert_text((100, 72), text)
        all_text_original.append(text)

    doc4 = pymupdf.open()
    for i in range(6):
        text = f"doc 4, page {i}"
        page = doc4.new_page()
        page.insert_text((100, 72), text)
        all_text_original.append(text)

    new_doc = pymupdf.open()  # make combined PDF of input files
    new_doc.insert_pdf(doc1)
    new_doc.insert_pdf(doc2)
    new_doc.insert_pdf(doc3)
    new_doc.insert_pdf(doc4)
    # read text from all pages and store in list
    for page in new_doc:
        all_text_combined.append(page.get_text().replace("\n", ""))
    # the lists must be equal
    assert all_text_combined == all_text_original


def test_issue1417_insertpdf_in_loop():
    """Using a context manager instead of explicitly closing files"""
    f = os.path.join(resources, "1.pdf")
    big_doc = pymupdf.open()
    fd1 = os.open( f, os.O_RDONLY)
    os.close( fd1)
    for n in range(0, 1025):
        with pymupdf.open(f) as pdf:
            big_doc.insert_pdf(pdf)
        # Create a raw file descriptor. If the above pymupdf.open() context leaks
        # a file descriptor, fd will be seen to increment.
        fd2 = os.open( f, os.O_RDONLY)
        assert fd2 == fd1
        os.close( fd2)
    big_doc.close()


def _test_insert_adobe():
    path = os.path.abspath( f'{__file__}/../../../PyMuPDF-performance/adobe.pdf')
    if not os.path.exists(path):
        print(f'Not running test_insert_adobe() because does not exist: {os.path.relpath(path)}')
        return
    a = pymupdf.Document()
    b = pymupdf.Document(path)
    a.insert_pdf(b)


def _2861_2871_merge_pdf(content: bytes, coverpage: bytes):
    with pymupdf.Document(stream=coverpage, filetype="pdf") as coverpage_pdf:
        with pymupdf.Document(stream=content, filetype="pdf") as content_pdf:
            coverpage_pdf.insert_pdf(content_pdf)
            doc = coverpage_pdf.write()
            return doc 

def test_2861():
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_2861.pdf')
    with open(path, "rb") as content_pdf:
        with open(path, "rb") as coverpage_pdf:
            content = content_pdf.read()
            coverpage = coverpage_pdf.read()
            _2861_2871_merge_pdf(content, coverpage)

def test_2871():
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_2871.pdf')
    with open(path, "rb") as content_pdf:
        with open(path, "rb") as coverpage_pdf:
            content = content_pdf.read()
            coverpage = coverpage_pdf.read()
            _2861_2871_merge_pdf(content, coverpage)


def test_3789():
    
    file_path = os.path.abspath(f'{__file__}/../../tests/resources/test_3789.pdf')
    result_path = os.path.abspath(f'{__file__}/../../tests/test_3789_out')
    pages_per_split = 5
    
    # Clean pdf
    doc = pymupdf.open(file_path)
    tmp = io.BytesIO()
    tmp.write(doc.write(garbage=4, deflate=True))
    
    source_doc = pymupdf.Document('pdf', tmp.getvalue())
    tmp.close()

    # Calculate the number of pages per split file and the number of split files
    page_range = pages_per_split - 1
    split_range = range(0, source_doc.page_count, pages_per_split)
    num_splits = len(split_range)

    # Loop through each split range and create a new PDF file
    for i, start in enumerate(split_range):
        output_doc = pymupdf.open()

        # Determine the ending page for this split file
        to_page = start + page_range if i < num_splits - 1 else -1
        output_doc.insert_pdf(source_doc, from_page=start, to_page=to_page)

        # Save the output document to a file and add the path to the list of split files
        path = f'{result_path}_{i}.pdf'
        output_doc.save(path, garbage=2)
        print(f'Have saved to {path=}.')

        # If this is the last split file, exit the loop
        if to_page == -1:
            break
