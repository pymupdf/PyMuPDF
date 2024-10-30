import pymupdf


def test_parent():
    """Test invalidating parent on page re-assignment."""
    doc = pymupdf.open()
    page = doc.new_page()
    a = page.add_highlight_annot(page.rect)  # insert annotation on page 0
    page = doc.new_page()  # make a new page, should orphanate annotation
    try:
        print(a)  # should raise
        error = False
    except ValueError as e:
        assert str(e) == "orphaned object: parent is dead"
        error = True
    assert error
