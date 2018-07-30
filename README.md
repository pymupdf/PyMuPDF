# PyMuPDF 1.13.15 [![Build Status](https://travis-ci.org/rk700/PyMuPDF.svg?branch=master)](https://travis-ci.org/rk700/PyMuPDF)

![logo](https://github.com/rk700/PyMuPDF/blob/master/demo/pymupdf.jpg)

Release date: July 26, 2018

# Authors
* [Ruikai Liu](mailto:lrk700@gmail.com)
* [Jorj X. McKie](mailto:jorj.x.mckie@outlook.de)

# Introduction

This is **version 1.13.15 of PyMuPDF (formerly python-fitz)**, a Python binding with support for [MuPDF 1.13.0](http://mupdf.com/) - "a lightweight PDF and XPS viewer".

MuPDF can access files in PDF, XPS, OpenXPS, CBZ, EPUB and FB2 (e-books) formats, and it is known for its top performance and high rendering quality.

With PyMuPDF you therefore can access files with extensions ``*.pdf``, ``*.xps``, ``*.oxps``, ``*.cbz``, ``*.fb2`` or ``*.epub`` from your Python scripts.

See the [Wiki](https://github.com/rk700/PyMuPDF/wiki) for more information, [news](https://github.com/rk700/PyMuPDF/wiki/Change-and-News-Log), release notes and usage recipies.

# Installation

For all **Windows** and (thanks to our user **@jbarlow83**) for the major **Mac OSX** and **Linux** versions we offer [wheels](https://github.com/rk700/PyMuPDF/releases/latest). They can also be found in the [download section of PyPI](https://pypi.org/project/PyMuPDF/#files), where we are present since August 2015 - [![](http://pepy.tech/badge/pymupdf)](http://pepy.tech/project/pymupdf) since then.

If - for whatever reason - you need to generate PyMuPDF yourself, you must download and generate MuPDF before you can generate PyMuPDF. This process depends very much on your system. For most platforms, the MuPDF source contains prepared procedures to achieve this.

Be sure to download the official MuPDF source release from [here](https://mupdf.com/downloads). The [GitHub repo](https://github.com/ArtifexSoftware/mupdf) of MuPDF contains their current **development source**, which more often than not is incompatible with this PyMuPDF version.

Once this is done, adjust directories in ``setup.py`` and the rest should be as easy as running the usual ``python setup.py install``.

The following sections contain some platform-specific comments.

## Ubuntu
One of our users (thanks to **@gileadslostson**) has documented his MuPDF installation experience from sources in this [Wiki page](https://github.com/rk700/PyMuPDF/wiki/Experience-from-an-Ubuntu-installation).

## OSX
First, install the MuPDF headers and libraries, which are provided by mupdf-tools: ``brew install mupdf-tools``.

Then you might need to ``export ARCHFLAGS='-arch x86_64'``, since ``libmupdf.a`` is for x86_64 only.

Finally, please double check ``setup.py`` before building. Update ``include_dirs`` and ``library_dirs`` if necessary.

## MS Windows

In addition to wheels, this platform offers [pre-generated binaries](https://github.com/JorjMcKie/PyMuPDF-Optional-Material) in a ZIP format, which can be used without PIP.

If you are looking to make your own binary, consult this [Wiki page](https://github.com/rk700/PyMuPDF/wiki/Windows-Binaries-Generation). It explains how to use Visual Studio for generating MuPDF in quite some detail.

# Usage and Documentation
Have a look at the basic [demos](https://github.com/rk700/PyMuPDF/tree/master/demo), the [examples](https://github.com/rk700/PyMuPDF/tree/master/examples) (which contain complete, working programs), and the **recipies** section of our [Wiki](https://github.com/rk700/PyMuPDF/wiki) sidebar, which contains more than a dozen of guides in How-To-style.

Our documentation, written using Sphinx, is available in various formats from the following sources.

* You can view it online at [Read the Docs](https://pymupdf.readthedocs.io/). For **best quality downloads** use the following links.
* zipped [HTML](https://github.com/rk700/PyMuPDF/tree/master/doc/html.zip)
* [Windows CHM](https://github.com/JorjMcKie/PyMuPDF-optional-material/tree/master/doc/PyMuPDF.chm)
* [PDF](https://github.com/rk700/PyMuPDF/tree/master/doc/pymupdf.pdf)

# Earlier Versions
Earlier versions are available in the [releases](https://github.com/rk700/PyMuPDF/releases) directory.

# License
PyMuPDF is distributed under GNU GPL V3. Because you will also be using MuPDF, its license GNU AFFERO GPL V3 applies as well. Copies of both are included in this repository.

# Contact

Please submit questions, comments or issues [here](https://github.com/rk700/PyMuPDF/issues), or directly contact the authors via their e-mail addresses.
