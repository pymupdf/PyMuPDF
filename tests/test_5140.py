import pymupdf


def test_5140():
    doc = pymupdf.open()
    doc.new_page()
    doc.new_page()
    doc.set_page_labels(
        [
            {
                "startpage": 1,
                "prefix": "",
                "firstpagenum": 1,
                "style": "D",
            }
        ]
    )
    assert doc[0].get_label() == ""  # IndexError: list index out of range
    assert doc[1].get_label() == "1"
