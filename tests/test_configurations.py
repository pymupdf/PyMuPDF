import pymupdf
import pathlib
import util

use_layout = util._use_layout() and hasattr(pymupdf, "layout")
use_4llm = util._use_4llm() and hasattr(pymupdf, "pymupdf4llm")


def test_configuration_layout():
    if pymupdf.__version__ < "2.0":
        print(f"not testing version < {pymupdf.__version__}")
        return
    if not use_layout or not use_4llm:
        print("not testing: layout feature not available")
        return

    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hallo Welt!\nSeid umschlungen, Millionen!")

    out1 = doc.to_markdown()
    out2 = pymupdf.pymupdf4llm.to_markdown(doc)
    assert out1 == out2

    out1 = doc.to_text()
    out2 = pymupdf.pymupdf4llm.to_text(doc)
    assert out1 == out2

    out1 = doc.to_chunks()
    out2 = pymupdf.pymupdf4llm.to_chunks(doc)
    assert repr(out1) == repr(out2), f"{out1=} != {out2=}"

    out1 = doc.to_json()
    out2 = pymupdf.pymupdf4llm.to_json(doc)
    assert out1 == out2


def test_configuration_non_layout():
    if pymupdf.__version__ < "2.0":
        print(f"not testing version < {pymupdf.__version__}")
        return
    if use_layout:
        print("not testing: layout feature available")
        return
    if not use_4llm:
        print("not testing: 4llm feature not available")
        return

    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hallo Welt!\nSeid umschlungen, Millionen!")

    out1 = doc.to_markdown()
    out2 = pymupdf.pymupdf4llm.to_markdown(doc)
    assert out1 == out2

    # The remaining functions / methods should fail!
    try:
        out1 = doc.to_text()
        failed = False
    except NotImplementedError:
        failed = True
    assert failed

    try:
        out1 = doc.to_chunks()
        failed = False
    except NotImplementedError:
        failed = True
    assert failed

    try:
        out1 = doc.to_json()
        failed = False
    except NotImplementedError:
        failed = True
    assert failed
