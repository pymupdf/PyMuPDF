import pymupdf
import os.path


def test_4505():
    """Copy field flags to Parent widget and all of its kids."""
    path = os.path.abspath(f"{__file__}/../../tests/resources/test_4505.pdf")
    doc = pymupdf.open(path)
    page = doc[0]
    text1_flags_before = {}
    text1_flags_after = {}
    # extract all widgets having the same field name
    for w in page.widgets():
        if w.field_name != "text_1":
            continue
        text1_flags_before[w.xref] = w.field_flags
    # expected exiting field flags
    assert text1_flags_before == {8: 1, 10: 0, 33: 0}
    w = page.load_widget(8)  # first of these widgets
    # give all connected widgets that field flags value
    w.update(sync_flags=True)
    # confirm that all connected widgets have the same field flags
    for w in page.widgets():
        if w.field_name != "text_1":
            continue
        text1_flags_after[w.xref] = w.field_flags
    assert text1_flags_after == {8: 1, 10: 1, 33: 1}
