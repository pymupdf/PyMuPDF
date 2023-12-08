import fitz

import os

    
def merge_pdf(content: bytes, coverpage: bytes):
   with fitz.Document(stream=coverpage, filetype="pdf") as coverpage_pdf:
       with fitz.Document(stream=content, filetype="pdf") as content_pdf:
            coverpage_pdf.insert_pdf(content_pdf)
            doc = coverpage_pdf.write()
            return doc 

def test_2861():
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_2861.pdf')
    with open(path, "rb") as content_pdf:
        with open(path, "rb") as coverpage_pdf:
            content = content_pdf.read()
            coverpage = coverpage_pdf.read()
            merge_pdf(content, coverpage)
