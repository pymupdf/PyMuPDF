import pymupdf, os


def test_4942():
    path = os.path.abspath(f"{__file__}/../../tests/resources/test_4942.pdf")
    document = pymupdf.Document(path)
    page = document[0]
    page.clip_to_rect(page.rect)
    page.get_links()
