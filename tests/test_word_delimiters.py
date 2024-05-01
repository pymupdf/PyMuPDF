import pymupdf
import string


def test_delimiters():
    """Test changing word delimiting characters."""
    doc = pymupdf.open()
    page = doc.new_page()
    text = "word1,word2 - word3. word4?word5."
    page.insert_text((50, 50), text)

    # Standard words extraction:
    # only spaces and line breaks start a new word
    words0 = [w[4] for w in page.get_text("words")]
    assert words0 == ["word1,word2", "-", "word3.", "word4?word5."]

    # extract words again
    words1 = [w[4] for w in page.get_text("words", delimiters=string.punctuation)]
    assert words0 != words1
    assert " ".join(words1) == "word1 word2 word3 word4 word5"

    # confirm we will be getting old extraction
    assert [w[4] for w in page.get_text("words")] == words0
