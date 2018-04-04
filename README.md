# PyMuPDF 1.12.6 [![Build Status](https://travis-ci.org/rk700/PyMuPDF.svg?branch=master)](https://travis-ci.org/rk700/PyMuPDF)

![logo](https://github.com/rk700/PyMuPDF/blob/master/demo/pymupdf.jpg)

Release date: January 15, 2018

# Authors
* [Ruikai Liu](mailto:lrk700@gmail.com)
* [Jorj X. McKie](mailto:jorj.x.mckie@outlook.de)

# Introduction

This is **version 1.12.6 of PyMuPDF (formerly python-fitz)**, a Python binding which supports [MuPDF 1.12](http://mupdf.com/) - "a lightweight PDF and XPS viewer".

MuPDF can access files in PDF, XPS, OpenXPS, CBZ, EPUB and FB2 (e-books) formats, and it is known for its top performance and high rendering quality.

With PyMuPDF you therefore can also access files with extensions ``*.pdf``, ``*.xps``, ``*.oxps``, ``*.cbz``, ``*.fb2`` or ``*.epub`` from your Python scripts.

See the [Wiki](https://github.com/rk700/PyMuPDF/wiki) for more information, [news](https://github.com/rk700/PyMuPDF/wiki/Change-and-News-Log), release notes and usage recipies.

# Installation

For all Windows and the major Mac OS and Linux versions we offer wheel-based installation options. Look [here](https://github.com/rk700/PyMuPDF/releases/latest) to download the latest version for your OS. The files can also be found in the download section of PyPI.

If - for whatever reason - you need to generate PyMuPDF yourself, you must first download and generate MuPDF. This process depends very much on your system. For most platforms, the MuPDF source contains prepared procedures on how to achieve this.

Be sure to download the official MuPDF release from [here](https://mupdf.com/downloads). Although MuPDF also has a GitHub repo, this contains their current **development source**, which more often than not is incompatible with this PyMuPDF.

Once this is done, adjust directories in ``setup.py`` and the rest should be as easy as running ``python setup.py install``.

In the following you find some comments for various operating systems and please do refer to our documentation for more.

## Arch Linux
AUR: https://aur.archlinux.org/packages/python2-pymupdf/ currently only provides PyMuPDF version 1.9.2 for Python 2.

## Ubuntu
The required MuPDF version in the official Ubuntu repositories is often not timely available, so you do need to build it from source. Make sure to add ``-fPIC`` to CFLAGS when compiling.

When MuPDF is ready, edit ``setup.py`` in PyMuPDF and comment out the line of ``library_dirs=[]`` to specify the directory which contains ``libmupdf.a`` and other 3rd party libraries. Remove ``crypto`` from ``libraries`` in ``setup.py`` if it complains. One of our users (thanks to @gileadslostson) has documented his MuPDF installation experience from sources in this [Wiki page](https://github.com/rk700/PyMuPDF/wiki/Experience-from-an-Ubuntu-installation).

## OSX
First, install the MuPDF headers and libraries, which are provided by mupdf-tools: ``brew install mupdf-tools``.

Then you might need to ``export ARCHFLAGS='-arch x86_64'``, since ``libmupdf.a`` is for x86_64 only.

Finally, please double check ``setup.py`` before building. Update ``include_dirs`` and ``library_dirs`` if necessary.

## MS Windows

If you don't use ``pip`` or [PyPI](https://pypi.org/project/PyMuPDF/), you can still download [pre-generated binaries](https://github.com/JorjMcKie/PyMuPDF-Optional-Material) that are suitable for your Python / Windows combination. This, too, avoids any other downloads or compilation hassle. Again, make sure to consult our documentation.

If you do want to make your own binary however, have a look at this [Wiki page](https://github.com/rk700/PyMuPDF/wiki/Windows-Binaries-Generation). It explains how to use Visual Studio for generating MuPDF in quite some detail. Also do not hesitate to contact us if you need help.

# Usage and Documentation
Have a look at the basic [demos](https://github.com/rk700/PyMuPDF/tree/master/demo), the [examples](https://github.com/rk700/PyMuPDF/tree/master/examples) (which contain complete, working programs), and the **recipies** section of our [Wiki](https://github.com/rk700/PyMuPDF/wiki) sidebar.

You have a number of options to access the documentation:

* You can view it online at [Read the Docs](https://pymupdf.readthedocs.io/). Do not **download** from here, instead use the following links.
* You can download a zipped [HTML](https://github.com/rk700/PyMuPDF/tree/master/doc/html.zip) version.
* You can download a [Windows CHM](https://github.com/JorjMcKie/PyMuPDF-optional-material/tree/master/doc/PyMuPDF.chm).
* You can download a [PDF](https://github.com/rk700/PyMuPDF/tree/master/doc/pymupdf.pdf).

Earlier Versions
================
* [PyMuPDF Version 1.12.0](https://github.com/rk700/PyMuPDF/tree/1.12.0)

* [PyMuPDF Version 1.11.2](https://github.com/rk700/PyMuPDF/tree/1.11.2)

* [PyMuPDF Version 1.10.0](https://github.com/rk700/PyMuPDF/tree/1.10.0)

* [PyMuPDF Version 1.9.3](https://github.com/rk700/PyMuPDF/tree/1.9.3)

* [PyMuPDF Version 1.9.2](https://github.com/rk700/PyMuPDF/releases/tag/v1.9.2)

* [PyMuPDF Version 1.9.1](https://github.com/rk700/PyMuPDF/releases/tag/v1.9.1)

* [Code compatible with MuPDF v1.8](https://github.com/rk700/PyMuPDF/releases/tag/v1.8)

* [Code compatible with MuPDF v1.7a](https://github.com/rk700/PyMuPDF/releases/tag/v1.7)

* [Code compatible with MuPDF v1.2](https://github.com/rk700/PyMuPDF/releases/tag/v1.2)

# License
PyMuPDF is distributed under GNU GPL V3. The implied use of MuPDF also implies its license GNU AFFERO GPL V3. A copy of both licenses are included in this repository.

# Contact
You can also find us on the Python Package Index [PyPI](https://pypi.org/project/PyMuPDF/).

> Please note, that the project description there may be less up-to-date than the one you are currently looking at. This is because information on PyPI, once stored, **cannot be changed**. Previously, this has been true only for the downloadable files, but since **PyPI Warehouse**, it obviously applies to all data of a full release.

We invite you to join our efforts by contributing to the [Wiki](https://github.com/rk700/PyMuPDF/wiki) pages.

Please submit comments or issues [here](https://github.com/rk700/PyMuPDF/issues), or directly contact the authors.
