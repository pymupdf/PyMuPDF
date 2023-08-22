# PyMuPDF 1.23.0

![logo](https://artifex.com/images/logos/py-mupdf-github-icon.png)


Release date: August 22, 2023


On **[PyPI](https://pypi.org/project/PyMuPDF)** since August 2016: [![Downloads](https://static.pepy.tech/personalized-badge/pymupdf?period=total&units=international_system&left_color=black&right_color=orange&left_text=Downloads)](https://pepy.tech/project/pymupdf)

# Author
[Artifex](mailto:support@artifex.com), based on code by [Jorj X. McKie](mailto:jorj.x.mckie@outlook.de) and [Ruikai Liu](mailto:lrk700@gmail.com).

# Introduction

PyMuPDF adds Python bindings and abstractions to [MuPDF](https://mupdf.com/), a lightweight PDF, XPS, and eBook viewer, renderer, and toolkit. Both PyMuPDF and MuPDF are maintained and developed by Artifex Software, Inc.

MuPDF can access files in PDF, XPS, OpenXPS, CBZ, EPUB, MOBI and FB2 (eBooks) formats, and it is known for its top performance and exceptional rendering quality.

With PyMuPDF you can access files with extensions like `.pdf`, `.xps`, `.oxps`, `.cbz`, `.fb2`, `.mobi` or `.epub`. In addition, about 10 popular image formats can also be handled like documents: `.png`, `.jpg`, `.bmp`, `.tiff`, `.svg` etc.

# Usage
For all supported document types (i.e. **_including images_**) you can
* Decrypt the document.
* Access meta information, links and bookmarks.
* Render pages in raster formats (PNG and some others), or the vector format SVG.
* Search for text.
* Extract text and images.
* Convert to other formats: PDF, (X)HTML, XML, JSON, text.
* Do OCR (Optical Character Recognition) if Tesseract is installed.

> To some degree, PyMuPDF can also be used as an [image converter](https://github.com/pymupdf/PyMuPDF/wiki/How-to-Convert-Images): it can read a range of input formats and can produce **Portable Network Graphics (PNG)**, **Portable Anymaps** (**PNM**, etc.), **Portable Arbitrary Maps (PAM)**, **Adobe PostScript** and **Adobe Photoshop** documents, making the use of other graphics packages obselete in these cases. But interfacing with e.g. PIL/Pillow for image input and output is easy as well.

For **PDF documents,** there exists a plethora of additional features: they can be created, joined or split up. Pages can be inserted, deleted, re-arranged or modified in many ways (including annotations and form fields).

* Images and fonts can be extracted or inserted.
    > You may want to have a look at [this](https://github.com/pymupdf/PyMuPDF-Utilities/blob/master/examples/edit-images/edit.py) cool GUI example script, which lets you **_insert, delete, replace_** or **_re-position_** images under your visual control.

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

Documentation is written using Sphinx and is available online. It is currently a combination of a reference guide and user manual.

* You can view it online at [Read the Docs](https://pymupdf.readthedocs.io). This site also provides download options for PDF.
* For a **quick start** look at the [tutorial](https://pymupdf.readthedocs.io/en/latest/tutorial.html) and the [recipes](https://pymupdf.readthedocs.io/en/latest/faq.html) chapters.

The latest changelog can be viewed [here](https://pymupdf.readthedocs.io/en/latest/changes.html).


# Installation

PyMuPDF **requires Python 3.8 or later**.

For versions 3.8 and up, Python wheels exist for **Windows** (32bit and 64bit), **Linux** (64bit, Intel and ARM) and **Mac OSX** (64bit, Intel only), so it can be installed from [PyPI](https://pypi.org/search/?q=pymupdf) in the usual way. To ensure pip support for the latest wheel platform tags, we strongly recommend to always upgrade pip first.

    python -m pip install --upgrade pip
    python -m pip install --upgrade pymupdf

There are **no mandatory** external dependencies. However, some **optional features** become available only if additional packages are installed:

* [Pillow](https://pypi.org/project/Pillow/) for using pillow image output directly from PyMuPDF
* [fontTools](https://pypi.org/project/fonttools/) for creating font subsets.
* [pymupdf-fonts](https://pypi.org/project/pymupdf-fonts/) contains some nice fonts for your text output.
* [Tesseract-OCR](https://github.com/tesseract-ocr/tesseract) for optical character recognition in images and document pages. Tesseract is separate software, not a Python package. To enable OCR functions in PyMuPDF, the system environment variable `"TESSDATA_PREFIX"` must be defined and contain the `tessdata` folder name of the Tesseract installation location.


Older wheels - also with support for older Python versions - can be found [here](https://github.com/pymupdf/PyMuPDF-Optional-Material/tree/master/wheels-upto-Py3.5) and on PyPI.

> **Note:** If `pip` cannot find a wheel that is compatible with your platform, it will automatically build and install from source using the PyMuPDF sdist; this requires only that SWIG is installed on your system.


# Alternative 'rebased' implementation.

A new implementation of PyMuPDF is available as module `fitz_new`.

*
  Uses the [MuPDF C++ and Python
  APIs](https://mupdf.readthedocs.io/en/latest/language-bindings.html)
  instead of the MuPDF C API.

* Use as a drop-in replace with: `import fitz_new as fitz`

## Benefits

* Access to the underlying MuPDF Python API.

  The MuPDF Python API is available as `fitz_new.mupdf` - this is not possible
  with native PyMuPDF, and can give useful flexibility to the user.

* Simplified implementation.

  The underlying MuPDF C++/Python APIs' automated reference counting, automatic
  contexts, and native C++ and Python exceptions, make the implementation
  simpler than classic PyMuPDF.

  This also simplifies development of new PyMuPDF functionality.

* Optional tracing of MuPDF C function calls using environment variables.

  This is a feature of the MuPDF C++ and Python APIs, which can be
  very useful during development and when reporting bugs. See:
  <https://mupdf.readthedocs.io/en/latest/language-bindings.html#environmental-variables>

* Possible future support for multithreaded use.

  Classic PyMuPDF is explicitly single-threaded, but the MuPDF C++/Python APIs
  have automated per-thread contexts.


## Known issues

*
  `import fitz_new` is known to fail with a SEGV on Windows with Python-3.10.

# Secondary wheel `PyMuPDFb`

Installation of PyMuPDF with pip will automatically install a second
wheel called `PyMuPDFb` containing Python-independent libraries.


# License and Copyright

PyMuPDF and MuPDF are available under both, open-source AGPL and commercial license agreements.

Please read the full text of the [AGPL license agreement](https://www.gnu.org/licenses/agpl-3.0.html) (which is also included here in file COPYING) to ensure that your use case complies with the guidelines of this license. If you determine you cannot meet the requirements of the AGPL, please contact [Artifex](https://artifex.com/contact/pymupdf-inquiry.php) for more information regarding a commercial license.

Artifex is the exclusive commercial licensing agent for MuPDF.

Artifex, the Artifex logo, MuPDF, and the MuPDF logo are registered trademarks of Artifex Software Inc. PyMuPDF and the PyMuPDF logo are trademarks of Artifex Software, Inc. &copy; 2022 Artifex Software, Inc. All rights reserved.

# Contact
Please use the [Discussions](https://github.com/pymupdf/PyMuPDF/discussions) menu for questions, comments, or asking for help, and submit issues [here](https://github.com/pymupdf/PyMuPDF/issues).
