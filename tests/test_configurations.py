import pymupdf
import pathlib
import util


def test_configuration_layout():
    if not util._use_layout() :
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

