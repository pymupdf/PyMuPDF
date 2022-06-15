"""
* Join multiple PDFs into a new one.
* Compare with stored earlier result:
    - must have identical object definitions
    - must have different trailers
* Try inserting files in a loop.
"""
import os
import re
import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
resources = os.path.join(scriptdir, "resources")
oldfile = os.path.join(resources, "joined.pdf")
oldfile_1_20 = os.path.join(resources, "joined-1.20.pdf")

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
        

def test_joining():
    """Join 4 files and compare result with previously stored one."""
    flist = ("1.pdf", "2.pdf", "3.pdf", "4.pdf")
    doc = fitz.open()
    for f in flist:
        fname = os.path.join(resources, f)
        x = fitz.open(fname)
        doc.insert_pdf(x, links=True, annots=True)
        x.close()

    tobytes = doc.tobytes(deflate=True, garbage=4)
    new_output = fitz.open("pdf", tobytes)
    #new_output.save( os.path.join(resources, "joined-1.20.pdf"))
    old_output = fitz.open(oldfile)
    old_output_1_20 = fitz.open(oldfile_1_20)
    # result must have same objects, because MuPDF garbage
    # collection is a predictable process.
    
    # We do approximate comparison if new_output with old_output, and an exact
    # comparison of new_output with old_output_1_20.
    #
    assert old_output.xref_length() == new_output.xref_length() == old_output_1_20.xref_length()
    num_fails = 0
    for xref in range(1, old_output.xref_length()):
        old = old_output.xref_object(xref, compressed=True)
        old_1_20 = old_output_1_20.xref_object(xref, compressed=True)
        new = new_output.xref_object(xref, compressed=True)
        if approx_compare( old, new, max_delta=1.5):
            num_fails += 1
            print(
                    f'xref={xref}'
                    f'\nold={old_output.xref_object(xref, compressed=True)}'
                    f'\nnew={new_output.xref_object(xref, compressed=True)}'
                    )
        assert old_1_20 == new, (
                f'xref={xref}'
                f'\nold_1_20: {old_1_20}'
                f'\nnew@      {new}'
                )
    assert not num_fails
    assert old_output.xref_get_keys(-1) == new_output.xref_get_keys(-1)
    assert old_output.xref_get_key(-1, "ID") != new_output.xref_get_key(-1, "ID")

    assert old_output_1_20.xref_get_keys(-1) == new_output.xref_get_keys(-1)
    assert old_output_1_20.xref_get_key(-1, "ID") != new_output.xref_get_key(-1, "ID")


def test_issue1417_insertpdf_in_loop():
    """Using a context manager instead of explicitly closing files"""
    f = os.path.join(resources, "1.pdf")
    big_doc = fitz.open()
    fd1 = os.open( f, os.O_RDONLY)
    os.close( fd1)
    for n in range(0, 1025):
        with fitz.open(f) as pdf:
            big_doc.insert_pdf(pdf)
        # Create a raw file descriptor. If the above fitz.open() context leaks
        # a file descriptor, fd will be seen to increment.
        fd2 = os.open( f, os.O_RDONLY)
        assert fd2 == fd1
        os.close( fd2)
    big_doc.close()
