import pymupdf


def test_q_count():
    """Testing graphics state balances and wrap_contents().

    Take page's contents and generate various imbalanced graphics state
    situations. Each time compare q-count with expected results.
    Finally confirm we are out of balance using "is_wrapped", wrap the
    contents object(s) via "wrap_contents()" and confirm success.
    PDF commands "q" / "Q" stand for "push", respectively "pop".
    """
    doc = pymupdf.open()
    page = doc.new_page()
    # the page has no /Contents objects at all yet. Create one causing
    # an initial imbalance (so prepended "q" is needed)
    pymupdf.TOOLS._insert_contents(page, b"Q", True)  # append
    assert page._count_q_balance() == (1, 0)
    assert page.is_wrapped is False

    # Prepend more data that yield a different type of imbalanced contents:
    # Although counts of q and Q are equal now, the unshielded 'cm' before
    # the first 'q' makes the contents unusable for insertions.
    pymupdf.TOOLS._insert_contents(page, b"1 0 0 -1 0 0 cm q ", False)  # prepend
    if pymupdf.mupdf_version_tuple >= (1, 24, 2):
        assert page.is_wrapped is False
    else:
        assert page.is_wrapped
    if page._count_q_balance() == (0, 0):
        print("imbalance undetected by q balance count")

    text = "Hello, World!"
    page.insert_text((100, 100), text)  # establishes balance!

    # this should have produced a balanced graphics state
    assert page._count_q_balance() == (0, 0)
    assert page.is_wrapped

    # an appended "pop" must be balanced by a prepended "push"
    pymupdf.TOOLS._insert_contents(page, b"Q", True)  # append
    assert page._count_q_balance() == (1, 0)

    # a prepended "pop" yet needs another push
    pymupdf.TOOLS._insert_contents(page, b"Q", False)  # prepend
    assert page._count_q_balance() == (2, 0)

    # an appended "push" needs an additional "pop"
    pymupdf.TOOLS._insert_contents(page, b"q", True)  # append
    assert page._count_q_balance() == (2, 1)

    # wrapping the contents should yield a balanced state again
    assert page.is_wrapped is False
    page.wrap_contents()
    assert page.is_wrapped is True
    assert page._count_q_balance() == (0, 0)
