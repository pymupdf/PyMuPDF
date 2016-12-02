=============
Introduction
=============
**PyMuPDF** (formerly known as **python-fitz**) is a Python binding for `MuPDF <http://www.mupdf.com/>`_ - "a lightweight PDF and XPS viewer".

MuPDF can access files in PDF, XPS, OpenXPS, CBZ (comic book archive), FB2 and EPUB (e-book) formats.

These are files with extensions ``*.pdf``, ``*.xps``, ``*.oxps``, ``*.cbz``, ``*.fb2``  or ``*.epub`` (so in essence, with this binding you can develop **e-book viewers in Python** ...)

PyMuPDF provides access to all important functions of MuPDF from within a Python environment. Nevertheless, we are continuously expanding this function set.

MuPDF stands out among all similar products for its top rendering capability and unsurpassed processing speed.

Check this out yourself and compare the various free PDF-viewers. In terms of speed and rendering quality `SumatraPDF <http://www.sumatrapdfreader.org/>`_ ranges at the top (apart from MuPDF's own standalone viewer) - since it has changed its library basis to  MuPDF!

While PyMuPDF has been available since several years for an earlier version of MuPDF (1.2), it was until only mid May 2015, that its creator and a few co-workers decided to elevate it to support the current release of MuPDF (first v1.7a  then v1.8 in November 2016, v1.9 and v1.9a since April 2016, and v1.10a in December 2016).

PyMuPDF runs and has been tested on Mac, Linux, Windows 7, Windows 10, Python 2 and Python 3 (x86 and x64 versions). Other platforms should work too, as long as MuPDF and Python support them.

There exist several demo and example programs in the repository, ranging from simple code snippets to full-featured utilities, like text extraction, PDF joiners and bookmark maintenance.

Several interesting PDF output functions have been added recently, covering metadata and bookmark maintenance and document restructuring.

For installation, you can choose between generating from source code (which implies also compiling the MuPDF C library), or, under Windows only, installing pre-generated binaries.

Note on the Name ``fitz``
--------------------------
The Python import statement for this library is ``import fitz``. This has a historical reason:

The original rendering library for MuPDF was called ``Libart``. "After Artifex Software acquired the MuPDF project, the development focus shifted on writing a new modern graphics library called ``Fitz``. Fitz was originally intended as an R&D project to replace the aging Ghostscript graphics library, but has instead become the rendering engine powering MuPDF." (Quoted from `Wikipedia <https://en.wikipedia.org/wiki/MuPDF>`_).

License
--------
PyMuPDF is distributed under GNU GPL V3 or later.

MuPDF is distributed under a variation of it: the **GNU AFFERO GPL V3**. While in earlier days this license has been more restrictive, version 3 is in effect not any more than GNU GPL. There are just some technical details on how / where you must make available any changes you might have made to the **MuPDF library**. Other than that, nothing prevents you from distributing and even selling software you have built on the basis of MuPDF.