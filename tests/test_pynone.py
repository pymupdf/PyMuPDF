import sys, pymupdf

def test_none_refcount():
    doc = pymupdf.open()
    page = doc.new_page()
    for i in range(10):
        page.insert_text((72, 72 + i * 20), f"Hello world span {i}")

    before = sys.getrefcount(None)
    for _ in range(200):
        page.get_texttrace()
    after = sys.getrefcount(None)
    assert before == after, f"refcount of None changed: {before} -> {after}"