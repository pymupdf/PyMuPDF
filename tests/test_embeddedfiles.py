"""
Tests for PDF EmbeddedFiles functions.
"""
import fitz


def test_embedded1():
    doc = fitz.open()
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