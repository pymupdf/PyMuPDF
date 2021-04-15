"""
Check PDF encryption:
* make a PDF with owber and user passwords
* open and decrypt as owner or user
"""
import fitz


def test_encryption():
    text = "some secret information"  # keep this data secret
    perm = int(
        fitz.PDF_PERM_ACCESSIBILITY  # always use this
        | fitz.PDF_PERM_PRINT  # permit printing
        | fitz.PDF_PERM_COPY  # permit copying
        | fitz.PDF_PERM_ANNOTATE  # permit annotations
    )
    owner_pass = "owner"  # owner password
    user_pass = "user"  # user password
    encrypt_meth = fitz.PDF_ENCRYPT_AES_256  # strongest algorithm
    doc = fitz.open()  # empty pdf
    page = doc.new_page()  # empty page
    page.insert_text((50, 72), text)  # insert the data
    tobytes = doc.tobytes(
        encryption=encrypt_meth,  # set the encryption method
        owner_pw=owner_pass,  # set the owner password
        user_pw=user_pass,  # set the user password
        permissions=perm,  # set permissions
    )
    doc.close()
    doc = fitz.open("pdf", tobytes)
    assert doc.needs_pass
    assert doc.is_encrypted
    rc = doc.authenticate("owner")
    assert rc == 4
    assert not doc.is_encrypted
    doc.close()
    doc = fitz.open("pdf", tobytes)
    rc = doc.authenticate("user")
    assert rc == 2
