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

This is **_not a coverage test_**, although a significant part of the Python part **_does_** get executed (ca. 80%). Achieving a much higher code coverage remains an ongoing task.

To use these scripts, you must have installed `pytest`:

`python -m pip install pytest`

Then simply execute `python -m pytest` in a terminal of this folder. `pytest` will automatically locate all scripts and execute them. All tests should run successfully and you will see an output like this:

```
python3.8 -m pytest
============================ test session starts =====================
platform linux -- Python 3.8.5, pytest-6.2.3, py-1.10.0, pluggy-0.13.1
rootdir: .../pymupdf
collected 72 items

test_annots.py ...............                                [ 20%]
test_badfonts.py .                                            [ 22%]
test_crypting.py .                                            [ 23%]
test_drawings.py .                                            [ 25%]
test_embeddedfiles.py .                                       [ 26%]
test_font.py ..                                               [ 29%]
test_general.py ...........                                   [ 44%]
test_geometry.py .......                                      [ 54%]
test_imagebbox.py .                                           [ 55%]
test_insertimage.py .                                         [ 56%]
test_insertpdf.py .                                           [ 58%]
test_linequad.py .                                            [ 59%]
test_metadata.py ..                                           [ 62%]
test_nonpdf.py ...                                            [ 66%]
test_object_manipulation.py ...                               [ 70%]
test_pagedelete.py .                                          [ 72%]
test_pagelabels.py .                                          [ 73%]
test_pixmap.py .....                                          [ 80%]
test_showpdfpage.py .                                         [ 81%]
test_textbox.py ..                                            [ 84%]
test_textextract.py .                                         [ 86%]
test_textsearch.py .                                          [ 87%]
test_toc.py ....                                              [ 93%]
test_widgets.py .....                                         [100%]

====================== 72 passed in 1.43s ===========================
```
