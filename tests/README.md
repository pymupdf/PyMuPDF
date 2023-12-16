# PyMuPDF tests

To run these tests:

* Create and enter a venv.
* Install PyMuPDF.
* Install the Python packages listed in
  `PyMuPDF/scripts/gh_release.py:test_packages`.
* Run pytest on the PyMuPDF directory.

For example, as of 2023-12-11:

```
> python -m pip install pytest fontTools psutil pymupdf-fonts pillow
> pytest PyMuPDF
============================= test session starts ==============================
platform linux -- Python 3.11.2, pytest-7.4.3, pluggy-1.3.0
rootdir: /home/jules/artifex-remote/PyMuPDF
configfile: pytest.ini
collected 171 items

PyMuPDF/tests/test_2548.py .                                             [  0%]
PyMuPDF/tests/test_2634.py .                                             [  1%]
PyMuPDF/tests/test_2736.py .                                             [  1%]
PyMuPDF/tests/test_2791.py .                                             [  2%]
PyMuPDF/tests/test_2861.py .                                             [  2%]
PyMuPDF/tests/test_annots.py ..................                          [ 13%]
PyMuPDF/tests/test_badfonts.py .                                         [ 14%]
PyMuPDF/tests/test_crypting.py .                                         [ 14%]
PyMuPDF/tests/test_docs_samples.py .............                         [ 22%]
PyMuPDF/tests/test_drawings.py ......                                    [ 25%]
PyMuPDF/tests/test_embeddedfiles.py .                                    [ 26%]
PyMuPDF/tests/test_extractimage.py ..                                    [ 27%]
PyMuPDF/tests/test_flake8.py .                                           [ 28%]
PyMuPDF/tests/test_font.py .....                                         [ 30%]
PyMuPDF/tests/test_general.py .......................................... [ 55%]
...                                                                      [ 57%]
PyMuPDF/tests/test_geometry.py ........                                  [ 61%]
PyMuPDF/tests/test_imagebbox.py ..                                       [ 63%]
PyMuPDF/tests/test_insertimage.py ..                                     [ 64%]
PyMuPDF/tests/test_insertpdf.py ..                                       [ 65%]
PyMuPDF/tests/test_linequad.py .                                         [ 66%]
PyMuPDF/tests/test_metadata.py ..                                        [ 67%]
PyMuPDF/tests/test_nonpdf.py ...                                         [ 69%]
PyMuPDF/tests/test_object_manipulation.py ....                           [ 71%]
PyMuPDF/tests/test_optional_content.py ..                                [ 72%]
PyMuPDF/tests/test_pagedelete.py .                                       [ 73%]
PyMuPDF/tests/test_pagelabels.py .                                       [ 73%]
PyMuPDF/tests/test_pixmap.py ..........                                  [ 79%]
PyMuPDF/tests/test_showpdfpage.py .                                      [ 80%]
PyMuPDF/tests/test_story.py ...                                          [ 81%]
PyMuPDF/tests/test_tables.py ...                                         [ 83%]
PyMuPDF/tests/test_tesseract.py .                                        [ 84%]
PyMuPDF/tests/test_textbox.py ......                                     [ 87%]
PyMuPDF/tests/test_textextract.py ..                                     [ 88%]
PyMuPDF/tests/test_textsearch.py ..                                      [ 90%]
PyMuPDF/tests/test_toc.py ........                                       [ 94%]
PyMuPDF/tests/test_widgets.py ........                                   [ 99%]
PyMuPDF/tests/test_word_delimiters.py .                                  [100%]

======================== 171 passed in 78.65s (0:01:18) ========================
> 
```

## Known test failure with non-default build of MuPDF

If PyMuPDF has been built with a non-default build of MuPDF (using
environmental variable ``PYMUPDF_SETUP_MUPDF_BUILD``), it is possible that
``tests/test_textbox.py:test_textbox3()`` will fail, because it relies on MuPDF
having been built with PyMuPDF's customized configuration, ``fitz/_config.h``.

One can skip this particular test by adding ``-k 'not test_textbox3'`` to the
pytest command line.
