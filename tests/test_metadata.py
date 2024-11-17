"""
1. Read metadata and compare with stored expected result.
2. Erase metadata and assert object has indeed been deleted.
"""
import json
import os
import sys

import pymupdf

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "001003ED.pdf")
metafile = os.path.join(scriptdir, "resources", "metadata.txt")
doc = pymupdf.open(filename)


def test_metadata():
    assert json.dumps(doc.metadata) == open(metafile).read()


def test_erase_meta():
    doc.set_metadata({})
    # Check PDF trailer and assert that there is no more /Info object
    # or is set to "null".
    statement1 = doc.xref_get_key(-1, "Info")[1] == "null"
    statement2 = "Info" not in doc.xref_get_keys(-1)
    assert statement2 or statement1


def test_3237():
    filename = os.path.abspath(f'{__file__}/../../tests/resources/001003ED.pdf')
    with pymupdf.open(filename) as doc:
        # We need to explicitly encode in utf8 on windows.
        metadata1 = doc.metadata
        metadata1 = repr(metadata1).encode('utf8')
        doc.set_metadata({})

        metadata2 = doc.metadata
        metadata2 = repr(metadata2).encode('utf8')
        print(f'{metadata1=}')
        print(f'{metadata2=}')
        assert metadata1 == b'{\'format\': \'PDF 1.6\', \'title\': \'RUBRIK_Editorial_01-06.indd\', \'author\': \'Natalie Schaefer\', \'subject\': \'\', \'keywords\': \'\', \'creator\': \'\', \'producer\': \'Acrobat Distiller 7.0.5 (Windows)\', \'creationDate\': "D:20070113191400+01\'00\'", \'modDate\': "D:20070120104154+01\'00\'", \'trapped\': \'\', \'encryption\': None}'
        assert metadata2 == b"{'format': 'PDF 1.6', 'title': '', 'author': '', 'subject': '', 'keywords': '', 'creator': '', 'producer': '', 'creationDate': '', 'modDate': '', 'trapped': '', 'encryption': None}"
