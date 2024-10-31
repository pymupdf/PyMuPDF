import pymupdf


def test_rtl():
    doc = pymupdf.open("resources/test-E+A.pdf")
    page = doc[0]
    # set of all RTL characters
    rtl_chars = set([chr(i) for i in range(0x590, 0x901)])

    for w in page.get_text("words"):
        # every word string must either ONLY contain RTL chars
        cond1 = rtl_chars.issuperset(w[4])
        # ... or NONE.
        cond2 = rtl_chars.intersection(w[4]) == set()
        assert cond1 or cond2
