# PyMuPDF 1.20.0

![logo](https://github.com/pymupdf/PyMuPDF/blob/master/demo/pymupdf.jpg)

Release date: June 6, 2022

On **[PyPI](https://pypi.org/project/PyMuPDF)** since August 2016: [![Downloads](https://static.pepy.tech/personalized-badge/pymupdf?period=total&units=international_system&left_color=black&right_color=orange&left_text=Downloads)](https://pepy.tech/project/pymupdf)

# Author
[Artifex], based on code by [Jorj X. McKie](mailto:jorj.x.mckie@outlook.de), based on original code by [Ruikai Liu](mailto:lrk700@gmail.com).

# Introduction

PyMuPDF (current version 1.20.0) is a Python binding with support for [MuPDF](https://mupdf.com/) (current version 1.20.*), a lightweight PDF, XPS, and E-book viewer, renderer, and toolkit, which is maintained and developed by Artifex Software, Inc.

MuPDF can access files in PDF, XPS, OpenXPS, CBZ, EPUB and FB2 (e-books) formats, and it is known for its top performance and high rendering quality.

With PyMuPDF you can access files with extensions like ".pdf", ".xps", ".oxps", ".cbz", ".fb2" or ".epub". In addition, about 10 popular image formats can also be handled like documents: ".png", ".jpg", ".bmp", ".tiff", etc..

> In partnership with [Artifex](https://artifex.com/), PyMuPDF is now also available for commercial licensing. This agreement has no impact on use cases, that are compliant with the open-source license AGPL. Please see the "License and Copyright" section below for additional information.

# Usage
For all supported document types (i.e. **_including images_**) you can
* decrypt the document
* access meta information, links and bookmarks
* render pages in raster formats (PNG and some others), or the vector format SVG
* search for text
* extract text and images
* convert to other formats: PDF, (X)HTML, XML, JSON, text
* do OCR (Optical Character Recognition) if Tesseract is installed

> To some degree, PyMuPDF can also be used as an [image converter](https://github.com/pymupdf/PyMuPDF/wiki/How-to-Convert-Images): it can read a range of input formats and can produce **Portable Network Graphics (PNG)**, **Portable Anymaps** (**PNM**, etc.), **Portable Arbitrary Maps (PAM)**, **Adobe Postscript** and **Adobe Photoshop** documents, making the use of other graphics packages obselete in these cases. But interfacing with e.g. PIL/Pillow for image input and output is easy as well.

For **PDF documents,** there exists a plethora of additional features: they can be created, joined or split up. Pages can be inserted, deleted, re-arranged or modified in many ways (including annotations and form fields).

* Images and fonts can be extracted or inserted.
    > You may want to have a look at [this](https://github.com/pymupdf/PyMuPDF-Utilities/blob/master/examples/image-maintenance.py) cool GUI example script, which lets you **_insert, delete, replace_** or **_re-position_** images under your visual control.

    > If [fontTools](https://pypi.org/project/fonttools/) is installed, subsets can be built for eligible fonts based on their usage in the document. Especially for new PDFs, this can lead to significant file size reductions.
* Embedded files are fully supported.
* PDFs can be reformatted to support double-sided printing, posterizing, applying logos or watermarks
* Password protection is fully supported: decryption, encryption, encryption method selection, permission level and user / owner password setting.
* Support of the **PDF Optional Content** concept for images, text and drawings.
* Low-level PDF structures can be accessed and modified.
* **Command line module** ``"python -m fitz ..."``. A versatile utility with the following features

    - **encryption / decryption / optimization**
    - creation of **sub-documents**
    - document **joining**
    - **image / font extraction**
    - full support of **embedded files**
    - **_layout-preserving text extraction_** (all documents)


Have a look at the basic [demos](https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/demo), the [examples](https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples) (which contain complete, working programs), and [notebooks](https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/jupyter-notebooks).


# Documentation

Documentation is written using Sphinx and is available in various formats from the following sources. It currently is a combination of reference guide and user manual. For a **quick start** look at the [tutorial](https://pymupdf.readthedocs.io/en/latest/tutorial.html) and the [recipes](https://pymupdf.readthedocs.io/en/latest/faq.html) chapters.

* You can view it online at [Read the Docs](https://readthedocs.org/projects/pymupdf/). This site also provides download options for PDF.
* [Zipped HTML](https://github.com/pymupdf/PyMuPDF-optional-material/tree/master/doc/pymupdf.zip).
* [Windows help file](https://github.com/pymupdf/PyMuPDF-optional-material/tree/master/doc/PyMuPDF.chm).

The latest changelog can be viewed [here](https://pymupdf.readthedocs.io/en/latest/changes.html).


# Installation

PyMuPDF **requires Python 3.6 or later**.

For versions 3.7 and up, Python wheels exist for **Windows** (32bit and 64bit), **Linux** (64bit, Intel and ARM) and **Mac OSX** (64bit, Intel only), so it can be installed from [PyPI](https://pypi.org/search/?q=pymupdf) in the usual way. To ensure pip support for the latest wheel platform tags, we strongly recommend to always upgrade pip first.

```
python -m pip install --upgrade pip
python -m pip install --upgrade pymupdf
```

There are **no mandatory** external dependencies. However, some **optional features** become available only if additional packages are installed:

* [Pillow](https://pypi.org/project/Pillow/) for using pillow image output directly from PyMuPDF
* [fontTools](https://pypi.org/project/fonttools/) for creating font subsets.
* [pymupdf-fonts](https://pypi.org/project/pymupdf-fonts/) contains some nice fonts for your text output.
* [Tesseract-OCR](https://github.com/tesseract-ocr/tesseract) for optical character recognition in images and document pages. Tesseract is separate software, not a Python package. To enable OCR functions in PyMuPDF, the system environment variable `"TESSDATA_PREFIX"` must be defined and contain the `tessdata` folder name of the Tesseract installation location.


Older wheels - also with support for older Python versions - can be found [here](https://github.com/pymupdf/PyMuPDF-Optional-Material/tree/master/wheels-upto-Py3.5) and on PyPI.

Other platforms **require installation from sources**, follow [these](https://pymupdf.readthedocs.io/en/latest/installation.html) instructions in the documentation.

> **Note:** If `pip` cannot find a wheel that is compatible with your platform, it will automatically try an installation from sources - **_which will fail_** if MuPDF (including its sources) is not installed on your system.

This repo's folder [installation](https://github.com/pymupdf/PyMuPDF/tree/master/installation) contains several platform-specific source installation scripts contributed by users. You may also find the following Wiki pages useful:

* [Ubuntu installation experience](https://github.com/pymupdf/PyMuPDF/wiki/Ubuntu-Installation-Experience).
* [Windows wheels](https://github.com/pymupdf/PyMuPDF/wiki/Windows-Binaries-Generation).


# License and Copyright
In order to comply with MuPDF’s dual licensing model, PyMuPDF has entered into an agreement with Artifex who has the right to sublicense PyMuPDF to third parties.

PyMuPDF and MuPDF are now available under both, open-source AGPL and commercial license agreements.

Please read the full text of the [AGPL license agreement](https://www.gnu.org/licenses/agpl-3.0.html) (which is also included here in file COPYING) to ensure that your use case complies with the guidelines of this license. If you determine you cannot meet the requirements of the AGPL, please contact [Artifex](https://artifex.com/contact/) for more information regarding a commercial license.

Artifex is the exclusive commercial licensing agent for MuPDF.

Artifex, the Artifex logo, MuPDF, and the MuPDF logo are registered trademarks of Artifex Software Inc. © 2021 Artifex Software, Inc. All rights reserved.

# Contact
Please use the [Discussions](https://github.com/pymupdf/PyMuPDF/discussions) menu for questions, comments, or asking for help, and submit issues [here](https://github.com/pymupdf/PyMuPDF/issues).
