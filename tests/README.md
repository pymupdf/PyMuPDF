# Testing your PyMuPDF Installation
This folder contains a number of basic tests to confirm that PyMuPDF is correctly installed.

The following areas are currently covered:
* encryption and decryption
* extraction of drawings
* "geometry": correct working of points, rectangles, matrices
* image bbox computation
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
* textbox text extraction
* text searching
* handling of PDF Tables of Contents

To use these scripts, you must have installed `pytest`:

`python -m pip install pytest`

Then simply execute `python -m pytest` in a terminal of this folder. `pytest` will automatically locate all scripts and execute them. All tests should run successfully and you will see an output like this:

```
python3.8 -m pytest
============================ test session starts =====================
platform linux -- Python 3.8.5, pytest-6.2.3, py-1.10.0, pluggy-0.13.1
rootdir: .../pymupdf
collected 31 items

test_badfonts.py .                                            [  3%]
test_crypting.py .                                            [  6%]
test_drawings.py .                                            [  9%]
test_geometry.py ...                                          [ 19%]
test_imagebbox.py .                                           [ 22%]
test_insertimage.py .                                         [ 25%]
test_insertpdf.py .                                           [ 29%]
test_linequad.py .                                            [ 32%]
test_metadata.py ..                                           [ 38%]
test_nonpdf.py ...                                            [ 48%]
test_object_manipulation.py ...                               [ 58%]
test_pagedelete.py .                                          [ 61%]
test_pagelabels.py .                                          [ 64%]
test_pixmap.py ...                                            [ 74%]
test_showpdfpage.py .                                         [ 77%]
test_textbox.py ..                                            [ 83%]
test_textsearch.py .                                          [ 87%]
test_toc.py ....                                              [100%]

======================== 31 passed in 2.25s ==========================
```