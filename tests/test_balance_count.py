import fitz


def test_q_count():
    """Testing graphics state balances and wrap_contents()."""
    if not hasattr(fitz, "mupdf"):
        print("Not executing 'test_q_count' in classic")
        return
    doc = fitz.open()
    page = doc.new_page()
    text = "Hello, World!"
    page.insert_text((100, 100), text)

    # this should have produced a balanced graphics state
    assert page._count_q_balance() == (0, 0)

    # an appended "pop" must be balanced by a prepended "push"
    fitz.TOOLS._insert_contents(page, b"Q", True)  # append
    assert page._count_q_balance() == (1, 0)

    # a prepended "pop" yet needs another push
    fitz.TOOLS._insert_contents(page, b"Q", False)  # prepend
    assert page._count_q_balance() == (2, 0)

    # an appended "push" needs an additional "pop"
    fitz.TOOLS._insert_contents(page, b"q", True)  # append
    assert page._count_q_balance() == (2, 1)

    # wrapping the contents should yield a balanced state again
    page.wrap_contents()
    assert page._count_q_balance() == (0, 0)
