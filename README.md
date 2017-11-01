# PyMuPDF 1.11.1

![logo](https://github.com/rk700/PyMuPDF/blob/master/demo/pymupdf.jpg)

Release date: Sept 1, 2017

# Authors
* Ruikai Liu
* Jorj X. McKie

# Introduction

This is **version 1.11.1 of PyMuPDF (formerly python-fitz)**, a Python binding which supports [MuPDF 1.11](http://mupdf.com/) - "a lightweight PDF and XPS viewer".

MuPDF can access files in PDF, XPS, OpenXPS, CBZ, EPUB and FB2 (e-books) formats, and it is known for its top performance and high rendering quality.

With PyMuPDF you therefore can also access files with extensions ``*.pdf``, ``*.xps``, ``*.oxps``, ``*.cbz``, ``*.fb2`` or ``*.epub`` from your Python scripts.

See the [Wiki](https://github.com/rk700/PyMuPDF/wiki) for more information, [news](https://github.com/rk700/PyMuPDF/wiki/Change-and-News-Log), release notes and usage recipies.


# Installation
If you had not previously installed MuPDF, you must first do this. This process highly depends on your system. For most platforms, the MuPDF source contains prepared procedures on how to achieve this. If you decide to generate MuPDF from sources, be sure to download the official release from https://mupdf.com/downloads/. MuPDF also has a GitHub repo, but it contains the current **development source**, which probably is not compatible with this PyMuPDF.

Once MuPDF is in place, installing PyMuPDF comes down to running the usual ``python setup.py install``.

Also refer to our documentation for details.

## Arch Linux
AUR: https://aur.archlinux.org/packages/python2-pymupdf/

## Ubuntu
The required MuPDF version in the official Ubuntu repositories is often not timely available, so you need to build it from source. Make sure to add ``-fPIC`` to CFLAGS when compiling.

When MuPDF is ready, edit ``setup.py`` in PyMuPDF and comment out the line of ``library_dirs=[]`` to specify the directory which contains ``libmupdf.a`` and other 3rd party libraries. Remove ``crypto`` from ``libraries`` in ``setup.py`` if it complains. For a MuPDF installation experience from sources visit this [Wiki page](https://github.com/rk700/PyMuPDF/wiki/Experience-from-an-Ubuntu-installation).

## OSX
First, install the MuPDF headers and libraries, which are provided by mupdf-tools: ``brew install mupdf-tools``.

Then you might need to ``export ARCHFLAGS='-arch x86_64'`` since ``libmupdf.a`` is for x86_64 only.

Finally, please double check ``setup.py`` before building. Update ``include_dirs`` and ``library_dirs`` if necessary.

## Windows
You can download pre-generated binaries or Python wheels from [here](https://github.com/JorjMcKie/PyMuPDF-Optional-Material) that are suitable for your Python / Windows combination, and thereby avoid any compilation hassle. Again, make sure to consult our documentation.

If you do want to make your own binary however, have a look at this [Wiki page](https://github.com/rk700/PyMuPDF/wiki/Windows-Binaries-Generation). It explains how to use Visual Studio for generating MuPDF in quite some detail. Also do not hesitate to contact us if you need help.

# Usage and Documentation
Please have a look at the basic [demos](https://github.com/rk700/PyMuPDF/tree/master/demo), the [examples](https://github.com/rk700/PyMuPDF/tree/master/examples) which contain complete, working programs, and the **recipies** section of our [Wiki](https://github.com/rk700/PyMuPDF/wiki).

You have a variety of options to access the **documentation**:

* You can view it online at [Read the Docs](https://pymupdf.readthedocs.io/en/latest/).
* You can download a [Windows CHM](https://github.com/JorjMcKie/PyMuPDF-optional-material/tree/master/doc/PyMuPDF.chm).
* You can download a [PDF](https://github.com/rk700/PyMuPDF/tree/master/doc/pymupdf.pdf).
* You can download a [HTML ZIP file](https://github.com/rk700/PyMuPDF/tree/master/doc/html.zip).


Earlier Versions
================
* [PyMuPDF Version 1.10.0](https://github.com/rk700/PyMuPDF/tree/1.10.0)

* [PyMuPDF Version 1.9.3](https://github.com/rk700/PyMuPDF/tree/1.9.3)

* [PyMuPDF Version 1.9.2](https://github.com/rk700/PyMuPDF/releases/tag/v1.9.2)

* [PyMuPDF Version 1.9.1](https://github.com/rk700/PyMuPDF/releases/tag/v1.9.1)

* [Code compatible with MuPDF v1.8](https://github.com/rk700/PyMuPDF/releases/tag/v1.8)

* [Code compatible with MuPDF v1.7a](https://github.com/rk700/PyMuPDF/releases/tag/v1.7)

* [Code compatible with MuPDF v1.2](https://github.com/rk700/PyMuPDF/releases/tag/v1.2)_

# License
PyMuPDF is distributed under GNU GPL V3. The implied use of MuPDF also implies its license GNU AFFERO GPL V3. A copy of both licenses are included in this repository.

# Contact
You can also find PyMuPDF on the Python Package Index [PyPI](https://pypi.python.org/pypi/PyMuPDF/1.11.0)

We invite you to join our efforts by contributing to the the wiki pages.

Please submit comments or any issues either to this site or by sending an e-mail to the authors [Ruikai Liu](lrk700@gmail.com) and [Jorj X. McKie](jorj.x.mckie@outlook.de).
