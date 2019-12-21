# PyMuPDF 1.16.10

![logo](https://github.com/pymupdf/PyMuPDF/blob/master/demo/pymupdf.jpg)

Release date: December 21, 2019

**Travis-CI:** [![Build Status](https://travis-ci.org/JorjMcKie/py-mupdf.svg?branch=master)](https://travis-ci.org/JorjMcKie/py-mupdf)

On **[PyPI](https://pypi.org/project/PyMuPDF)** since August 2016: [![](https://pepy.tech/badge/pymupdf)](https://pepy.tech/project/pymupdf)

# Authors
* [Jorj X. McKie](mailto:jorj.x.mckie@outlook.de)
* [Ruikai Liu](mailto:lrk700@gmail.com)

# Introduction

This is **version 1.16.10 of PyMuPDF (formerly python-fitz)**, a Python binding with support for [MuPDF 1.16.*](http://mupdf.com/) - "a lightweight PDF, XPS, and E-book viewer".

MuPDF can access files in PDF, XPS, OpenXPS, CBZ, EPUB and FB2 (e-books) formats, and it is known for its top performance and high rendering quality.

With PyMuPDF you can access files with extensions like ".pdf", ".xps", ".oxps", ".cbz", ".fb2" or ".epub". About 10 popular image formats are also supported via the document interface.


# Usage and Documentation
For all supported document types (i.e. including images) types you can
* decrypt the document
* access meta information, links and bookmarks
* render pages in raster formats (PNG and some others), or the vector format SVG
* search for text
* extract text and images
* convert to other formats: PDF, (X)HTML, XML, JSON, text

> To some degree, PyMuPDF can therefore be used as an [image converter](https://github.com/pymupdf/PyMuPDF/wiki/How-to-Convert-Images): it can read a range of input formats and can produce **Portable Network Graphics (PNG)**, **Portable Anymaps** (**PNM**, etc.), **Portable Arbitrary Maps (PAM)**, **Adobe Postscript** and **Adobe Photoshop** documents, making the use of other graphics packages obselete in these cases. But interfacing with e.g. PIL/Pillow for image input and output is easy as well.

**PDF files** can be created, joined or split up. Pages can be inserted, deleted, re-arranged or modified in many ways (including annotations and form fields).

* Images and fonts can be extracted or inserted.
* Embedded files are fully supported.
* PDFs can be reformatted to support double-sided printing, posterizing, applying logos or watermarks
* Password protection is fully supported: decryption, encryption, encryption method selection, permmission level and user / owner password setting.
* Low-level PDF structures can be accessed and modified.
* Starting with v1.16.10, PyMuPDF can also be used as a **module in the command line** using ``"python -m fitz ..."``. This is a versatile utility, which we will further develop over time. It currently supports PDF document

    - **encryption / decryption / optimization**
    - creating **sub-documents**
    - document **joining**
    - **image / font extraction**
    - full support of **embedded files**.


Have a look at the basic [demos](https://github.com/pymupdf/PyMuPDF/tree/master/demo), the [examples](https://github.com/pymupdf/PyMuPDF/tree/master/examples) (which contain complete, working programs), and the **recipes** section of our [Wiki](https://github.com/pymupdf/PyMuPDF/wiki) sidebar, which contains more than a dozen of guides in How-To-style.

Our **documentation**, written using Sphinx, is available in various formats from the following sources. It currently is a combination of a reference guide and a user manual. For a **quick start** look at the [tutorial](https://pymupdf.readthedocs.io/en/latest/tutorial/) and the [recipes](https://pymupdf.readthedocs.io/en/latest/faq/) chapters.

* You can view it online at [Read the Docs](https://pymupdf.readthedocs.io/). For **best quality downloads** you should however use the following links.
* zipped [HTML](https://github.com/pymupdf/PyMuPDF/tree/master/doc/html.zip)
* [Windows CHM](https://github.com/pymupdf/PyMuPDF-optional-material/tree/master/doc/PyMuPDF.chm)
* [PDF](https://github.com/pymupdf/PyMuPDF/blob/master/doc/PyMuPDF.pdf)

# Installation

For the major **Windows** and (thanks to our user **@jbarlow83**!) **Mac OSX** or **Linux** versions we offer wheels in the [download section of PyPI](https://pypi.org/project/PyMuPDF/#files).

> The Mac OSX platform tags are `macosx_10_6_intel` (up to Python 3.7) or ``macosx_10_9_x86_64``. For Linux the tag is ``manylinux2010_x86_64``.

> As of November 2019 and starting with PyMuPDF v1.16.10, wheel creation is supported for Python 64bit versions 2.7, 3.5, 3.6, 3.7 and 3.8 only. **Support for Python 3.4 has been dropped.**

For other Python versions or operating systems you need to generate PyMuPDF yourself as follows (and of course you can choose to do so for a wheel-supported platform, too).

This should work for all platforms which support Python and MuPDF. You need the development version of Python.

To do this, you must download and generate MuPDF. This process depends very much on your system. For most platforms, the MuPDF source contains prepared procedures for achieving this. Please observe the following general steps:

* Be sure to download the official MuPDF source release from [here](https://mupdf.com/downloads/archive). Do **not use** MuPDF's [GitHub repo](https://github.com/ArtifexSoftware/mupdf). It contains their current **development source**, which is **not compatible** with this PyMuPDF version most of the time.

* This repo's `fitz` folder contains one or more files whose names start with a sinlge underscore `"_"`. These files contain configuration data and hotfixes. Each one must be copy-renamed to its correct target location **inside the MuPDF source** that you have downloaded, **before you generate MuPDF**. Currently, these files are:
  - fitz configuration file `_config.h` copy-replace to: `mupdf/include/mupdf/fitz/config.h`. It contains configuration data like e.g. which fonts to support.

  - Now MuPDF can be generated.

* Since PyMuPDF v1.14.17, the sources provided in this repository **no longer contain** the interface files ``fitz.py`` and ``fitz.wrap.c`` - they are instead generated **"on the fly"** by ``setup.py`` using the interface generator [SWIG](http://www.swig.org/). So you need SWIG being installed on your system. Please refer to issue #312 for some background.
    - PyMuPDF wheels have been generated using **SWIG v4.0.1**.


* If you do **not (want to) use SWIG**, please download the **sources from PyPI** - they continue to contain those generated files, so installation should work like any other Python extension generation on your system.

Once this is done, adjust directories in ``setup.py`` and run ``python setup.py install``.

The following sections contain further comments for some platforms.

## Ubuntu
Our users (thanks to **@gileadslostson** and **@jbarlow83**!) have documented their MuPDF installation experiences from sources in this [Wiki page](https://github.com/pymupdf/PyMuPDF/wiki/Ubuntu-Installation-Experience).

## OSX
First, install the MuPDF headers and libraries, which are provided by mupdf-tools: ``brew install mupdf-tools``.

Then you might need to ``export ARCHFLAGS='-arch x86_64'``, since ``libmupdf.a`` is for x86_64 only.

Finally, please double check ``setup.py`` before building. Update ``include_dirs`` and ``library_dirs`` if necessary.

## MS Windows
If you are looking to make your own binary, consult this [Wiki page](https://github.com/pymupdf/PyMuPDF/wiki/Windows-Binaries-Generation). It explains how to use Visual Studio for generating MuPDF in quite some detail.

# Earlier Versions
Earlier versions are available in the [releases](https://github.com/pymupdf/PyMuPDF/releases) directory.

# License
PyMuPDF is distributed under GNU GPL V3. Because you will implicitely also be using MuPDF, its license GNU AFFERO GPL V3 applies as well. Copies of both are included in this repository.

# Contact

Please submit questions, comments or issues [here](https://github.com/pymupdf/PyMuPDF/issues), or directly contact the authors via their e-mail addresses.
