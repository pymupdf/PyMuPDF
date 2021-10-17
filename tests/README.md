# Testing your PyMuPDF Installation
This folder contains a number of basic tests to confirm that PyMuPDF is correctly installed.

The following areas are currently covered:
* encryption and decryption
* extraction of drawings
* "geometry": correct working of points, rectangles, matrices and operator algebra
* image bbox computation
* handling of embedded files
* image insertion
* PDF document joining
* computation of quadrilaterals for non-horizontal text
* extraction of non-unicode fontnames
* handling of PDF standard metadata
* handling of non-PDF document types
* programmatic editing of PDF object definition sources
* mass deletion of PDF pages
* handling of PDF page labels
* pixmap handling
* show PDF pages inside other PDF pages
* text extraction
* text searching
* handling of PDF Tables of Contents
* annotation handling
* field / widget handling
* image extraction

This is **_not a coverage test_**, although a significant part of the relevant Python part **_does_** get executed (ca. 80%). Achieving a much higher code coverage remains an ongoing task.

To use these scripts, you must have installed `pytest`:

`python -m pip install pytest`

Then simply execute `python -m pytest` in a terminal of this folder. `pytest` will automatically locate all scripts and execute them. All tests should run successfully and you will see an output like this:

```
pytest --cov=fitz
============================ test session starts =============================
platform linux -- Python 3.8.5, pytest-6.2.4, py-1.10.0, pluggy-0.13.1
rootdir: /mnt/d/harald/desktop/fitzPython119/pymupdf
plugins: cov-2.12.0
collected 79 items

test_annots.py ...............                                          [ 18%]
test_badfonts.py .                                                      [ 20%]
test_crypting.py .                                                      [ 21%]
test_drawings.py ..                                                     [ 24%]
test_embeddedfiles.py .                                                 [ 25%]
test_font.py ..                                                         [ 27%]
test_general.py ............                                            [ 43%]
test_geometry.py .......                                                [ 51%]
test_imagebbox.py .                                                     [ 53%]
test_insertimage.py .                                                   [ 54%]
test_insertpdf.py .                                                     [ 55%]
test_linequad.py .                                                      [ 56%]
test_metadata.py ..                                                     [ 59%]
test_nonpdf.py ...                                                      [ 63%]
test_object_manipulation.py ...                                         [ 67%]
test_optional_content.py ..                                             [ 69%]
test_pagedelete.py .                                                    [ 70%]
test_pagelabels.py .                                                    [ 72%]
test_pixmap.py ......                                                   [ 79%]
test_showpdfpage.py .                                                   [ 81%]
test_textbox.py ....                                                    [ 86%]
test_textextract.py .                                                   [ 87%]
test_textsearch.py .                                                    [ 88%]
test_toc.py ....                                                        [ 93%]
test_widgets.py .....                                                   [100%]

----------- coverage: platform linux, python 3.8.5-final-0 -----------
Name                                                      Stmts   Miss  Cover
-----------------------------------------------------------------------------
/usr/local/lib/python3.8/dist-packages/fitz/__init__.py     335     13    96%
/usr/local/lib/python3.8/dist-packages/fitz/fitz.py        4183    740    82%
/usr/local/lib/python3.8/dist-packages/fitz/utils.py       2196    669    70%
-----------------------------------------------------------------------------
TOTAL                                                      6714   1422    79%


============================ 79 passed in 5.76s ==============================
```
