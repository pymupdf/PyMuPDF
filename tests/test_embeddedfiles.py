"""
Tests for PDF EmbeddedFiles functions.
"""
import pymupdf


def test_embedded1():
    doc = pymupdf.open()
    buffer = b"123456678790qwexcvnmhofbnmfsdg4589754uiofjkb-"
    doc.embfile_add(
        "file1",
        buffer,
        filename="testfile.txt",
        ufilename="testfile-u.txt",
        desc="Description of some sort",
    )
    assert doc.embfile_count() == 1
    assert doc.embfile_names() == ["file1"]
    assert doc.embfile_info(0)["name"] == "file1"
    doc.embfile_upd(0, filename="new-filename.txt")
    assert doc.embfile_info(0)["filename"] == "new-filename.txt"
    assert doc.embfile_get(0) == buffer
    doc.embfile_del(0)
    assert doc.embfile_count() == 0

def test_4050():
    with pymupdf.open() as document:
        document.embfile_add('test', b'foobar', desc='some text')
        d = document.embfile_info('test')
        print(f'{d=}')
        # Date is non-trivial to test for.
        del d['creationDate']
        del d['modDate']
        assert d == {
                'name': 'test',
                'collection': 0,
                'filename': 'test',
                'ufilename': 'test',
                'description': 'some text',
                'size': 6,
                'length': 6,
                }
            
