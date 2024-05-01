import pymupdf


def test_objectstream1():
    """Test save option "use_objstms".
    This option compresses PDF object definitions into a special object type
    "ObjStm". We test its presence by searching for that /Type.
    """
    if not hasattr(pymupdf, "mupdf"):
        # only implemented for rebased
        return

    # make some arbitrary page with content
    text = "Hello, World! Hallo, Welt!"
    doc = pymupdf.open()
    page = doc.new_page()
    rect = (50, 50, 200, 500)

    page.insert_htmlbox(rect, text)  # place into the rectangle
    _ = doc.write(use_objstms=True)
    found = False
    for xref in range(1, doc.xref_length()):
        objstring = doc.xref_object(xref, compressed=True)
        if "/Type/ObjStm" in objstring:
            found = True
            break
    assert found, "No object stream found"


def test_objectstream2():
    """Test save option "use_objstms".
    This option compresses PDF object definitions into a special object type
    "ObjStm". We test its presence by searching for that /Type.
    """
    if not hasattr(pymupdf, "mupdf"):
        # only implemented for rebased
        return

    # make some arbitrary page with content
    text = "Hello, World! Hallo, Welt!"
    doc = pymupdf.open()
    page = doc.new_page()
    rect = (50, 50, 200, 500)

    page.insert_htmlbox(rect, text)  # place into the rectangle
    _ = doc.write(use_objstms=False)

    found = False
    for xref in range(1, doc.xref_length()):
        objstring = doc.xref_object(xref, compressed=True)
        if "/Type/ObjStm" in objstring:
            found = True
            break
    assert not found, "Unexpected: Object stream found!"


def test_objectstream3():
    """Test ez_save().
    Should automatically use object streams
    """
    if not hasattr(pymupdf, "mupdf"):
        # only implemented for rebased
        return
    import io

    fp = io.BytesIO()

    # make some arbitrary page with content
    text = "Hello, World! Hallo, Welt!"
    doc = pymupdf.open()
    page = doc.new_page()
    rect = (50, 50, 200, 500)

    page.insert_htmlbox(rect, text)  # place into the rectangle

    doc.ez_save(fp)  # save PDF to memory
    found = False
    for xref in range(1, doc.xref_length()):
        objstring = doc.xref_object(xref, compressed=True)
        if "/Type/ObjStm" in objstring:
            found = True
            break
    assert found, "No object stream found!"
