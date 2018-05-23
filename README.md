# PyMuPDF 1.13.5 [![Build Status](https://travis-ci.org/rk700/PyMuPDF.svg?branch=master)](https://travis-ci.org/rk700/PyMuPDF)

![logo](https://github.com/rk700/PyMuPDF/blob/master/demo/pymupdf.jpg)

Release date: May 11, 2018

# Authors
* [Ruikai Liu](mailto:lrk700@gmail.com)
* [Jorj X. McKie](mailto:jorj.x.mckie@outlook.de)

# Introduction

This is **version 1.13.5 of PyMuPDF (formerly python-fitz)**, a Python binding with support for [MuPDF 1.13.0](http://mupdf.com/) - "a lightweight PDF and XPS viewer".

MuPDF can access files in PDF, XPS, OpenXPS, CBZ, EPUB and FB2 (e-books) formats, and it is known for its top performance and high rendering quality.

With PyMuPDF you therefore can also access files with extensions ``*.pdf``, ``*.xps``, ``*.oxps``, ``*.cbz``, ``*.fb2`` or ``*.epub`` from your Python scripts.

See the [Wiki](https://github.com/rk700/PyMuPDF/wiki) for more information, [news](https://github.com/rk700/PyMuPDF/wiki/Change-and-News-Log), release notes and usage recipies.

# Installation

For all **Windows** and - thanks to our user @jbarlow83 - the major **Mac OSX** and **Linux** versions we offer wheel-based installation options. Look [here](https://github.com/rk700/PyMuPDF/releases/latest) to find the version for your OS. These files can also be found in the [download section of PyPI](https://pypi.org/project/PyMuPDF/#files).

If - for whatever reason - you need to generate PyMuPDF yourself, you must download and generate MuPDF before you can generate PyMuPDF. This process depends very much on your system. For most platforms, the MuPDF source contains prepared procedures to achieve this.

Be sure to download the official MuPDF release from [here](https://mupdf.com/downloads). MuPDF also has a GitHub repo, but this contains their current **development source**, which more often than not is incompatible with this PyMuPDF.

Once this is done, adjust directories in ``setup.py`` and the rest should be as easy as running ``python setup.py install``.

The following sections contain some platform-specific comments, but please do refer to our documentation for more.

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

If you don't use ``pip`` or [PyPI](https://pypi.org/project/PyMuPDF/), you can still download [pre-generated binaries](https://github.com/JorjMcKie/PyMuPDF-Optional-Material) that are suitable for your Python / Windows combination. This, too, avoids any other download or compilation hassle. Again, make sure to consult our documentation.

If you do want to make your own binary however, have a look at this [Wiki page](https://github.com/rk700/PyMuPDF/wiki/Windows-Binaries-Generation). It explains how to use Visual Studio for generating MuPDF in quite some detail. Also do not hesitate to contact us if you need help.

# Usage and Documentation
Have a look at the basic [demos](https://github.com/rk700/PyMuPDF/tree/master/demo), the [examples](https://github.com/rk700/PyMuPDF/tree/master/examples) (which contain complete, working programs), and the **recipies** section of our [Wiki](https://github.com/rk700/PyMuPDF/wiki) sidebar, which contains more than a dozen of guides in How-To-style.

Our documentation, written using Sphinx, is available in various formats from the following sources.

* You can view it online at [Read the Docs](https://pymupdf.readthedocs.io/). For **download**, only use the following links.
* [HTML](https://github.com/rk700/PyMuPDF/tree/master/doc/html.zip)
* [Windows CHM](https://github.com/JorjMcKie/PyMuPDF-optional-material/tree/master/doc/PyMuPDF.chm)
* [PDF](https://github.com/rk700/PyMuPDF/tree/master/doc/pymupdf.pdf)

Earlier Versions
================
Earlier versions are available in the [releases](https://github.com/rk700/PyMuPDF/releases) directory.

# License
PyMuPDF is distributed under GNU GPL V3. Because you will also be using MuPDF, its license GNU AFFERO GPL V3 applies as well. Copies of both licenses are included in this repository.

# Contact
You can also find us on the Python Package Index [PyPI](https://pypi.org/project/PyMuPDF/).

> Please note, that the project description there may be less up-to-date than the one you are currently looking at.

We invite you to join our efforts by contributing to the [Wiki](https://github.com/rk700/PyMuPDF/wiki) pages.

Please submit comments or issues [here](https://github.com/rk700/PyMuPDF/issues), or directly contact the authors.
