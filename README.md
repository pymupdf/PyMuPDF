# PyMuPDF 1.18.18

![logo](https://github.com/pymupdf/PyMuPDF/blob/master/demo/pymupdf.jpg)

Release date: September 16, 2021

On **[PyPI](https://pypi.org/project/PyMuPDF)** since August 2016: [![Downloads](https://static.pepy.tech/personalized-badge/pymupdf?period=total&units=international_system&left_color=black&right_color=orange&left_text=Downloads)](https://pepy.tech/project/pymupdf)

# Author
[Jorj X. McKie](mailto:jorj.x.mckie@outlook.de), based on original code by [Ruikai Liu](mailto:lrk700@gmail.com).

# Introduction

PyMuPDF (current version 1.18.18) is a Python binding with support for [MuPDF](https://mupdf.com/) (current version 1.18.*), a lightweight PDF, XPS, and E-book viewer, renderer, and toolkit, which is maintained and developed by Artifex Software, Inc.

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

> To some degree, PyMuPDF can therefore be used as an [image converter](https://github.com/pymupdf/PyMuPDF/wiki/How-to-Convert-Images): it can read a range of input formats and can produce **Portable Network Graphics (PNG)**, **Portable Anymaps** (**PNM**, etc.), **Portable Arbitrary Maps (PAM)**, **Adobe Postscript** and **Adobe Photoshop** documents, making the use of other graphics packages obselete in these cases. But interfacing with e.g. PIL/Pillow for image input and output is easy as well.

For **PDF documents,** there exists a plethora of additional features: they can be created, joined or split up. Pages can be inserted, deleted, re-arranged or modified in many ways (including annotations and form fields).

* Images and fonts can be extracted or inserted.
    > You may want to have a look at [this](https://github.com/pymupdf/PyMuPDF-Utilities/blob/master/examples/image-maintenance.py) cool GUI example script, which lets you **_insert, delete, replace_** or **_re-position_** images under your visual control.

    > Since v1.18.8 there is a `Document` method `subset_fonts()`, which automatically builds subsets based on the usage of all eligible fonts in the document. Especially for new documents, this can lead to significant file size reductions. The method was developed in cooperation with our user @cuteufo - again thanks a lot for the contribution.
* Embedded files are fully supported.
* PDFs can be reformatted to support double-sided printing, posterizing, applying logos or watermarks
* Password protection is fully supported: decryption, encryption, encryption method selection, permmission level and user / owner password setting.
* Support of the **PDF Optional Content** concept for images, text and drawings.
* Low-level PDF structures can be accessed and modified.
* **Command line module** ``"python -m fitz ..."``. A versatile utility with the following features

    - **encryption / decryption / optimization**
    - creation of **sub-documents**
    - document **joining**
    - **image / font extraction**
    - full support of **embedded files**
    - **_layout-preserving text extraction_** (all documents)


Have a look at the basic [demos](https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/demo), the [examples](https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples) (which contain complete, working programs), and the **recipes** section of our [Wiki](https://github.com/pymupdf/PyMuPDF/wiki) sidebar, which contains more than a dozen of guides in How-To-style.

**_New: Layout preserving text extraction!_**

> Via its subcommand "gettext", script [fitzcli.py](https://github.com/pymupdf/PyMuPDF-Utilities/blob/master/text-extraction/fitzcli.py) offers text extraction in different formats. Of special interest surely is layout preservation, which produces text as close to the original physical layout as possible, surrounding areas where there are images, or reproducing text in tables and multi-column text.

See [here](https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/text-extraction#layout-preserving-text-extraction) for more information on layout preserving text extraction.

# Documentation

Our documentation, written using Sphinx, is available in various formats from the following sources. It currently is a combination of reference guide and user manual. For a **quick start** look at the [tutorial](https://pymupdf.readthedocs.io/en/latest/tutorial/) and the [recipes](https://pymupdf.readthedocs.io/en/latest/faq/) chapters.

* You can view it online at [Read the Docs](https://readthedocs.org/projects/pymupdf/). This site also provides download options for PDF.
* The search function on Read the Docs does not work for me currently. If you want a working searchable local version, please download a zipped HTML for [here](https://github.com/pymupdf/PyMuPDF-optional-material/tree/master/doc/pymupdf.zip).
* Find a Windows help file [here](https://github.com/pymupdf/PyMuPDF-optional-material/tree/master/doc/PyMuPDF.chm).

The latest changelog can be viewed [here](https://pymupdf.readthedocs.io/en/latest/changes.html).


# Installation

PyMuPDF requires **Python 3.6 or later**.

Python wheels exist for **Windows** (32bit and 64bit), **Linux** (64bit, Intel and ARM) and **Mac OSX** (64bit, Intel only), so it can be installed from [PyPI](https://pypi.org/search/?q=pymupdf) in the usual way:

```
python -m pip install --upgrade pip
python -m pip install --upgrade pymupdf
```

There are **no mandatory** external dependencies. However, a few **optional methods** become available if additional packages are installed:

* [Pillow](https://pypi.org/project/Pillow/) for using pillow image output directly from PyMuPDF.
* [fontTools](https://pypi.org/project/fonttools/) for creating font subsets on PDF output.
* [pymupdf-fonts](https://pypi.org/project/pymupdf-fonts/) to extend your text output options with some nice fonts.


Older wheels - also with support for older Python versions - can be found [here](https://github.com/pymupdf/PyMuPDF-Optional-Material/tree/master/wheels-upto-Py3.5>) and on PyPI.

> Starting with v1.18.15, to minimize network traffic we no longer redundantly store wheels in this repository's releases folder. You can find older versions back to v1.9.2 on [PyPI](https://pypi.org/project/PyMuPDF/#history). Sources for every release continue to be stored in [here](https://github.com/pymupdf/PyMuPDF/releases).

Other platforms **require installation from sources**, follow [these](https://pymupdf.readthedocs.io/en/latest/installation.html) instructions in the documentation.

> **Note:** If you try installing from PyPI for a platform with no available wheel, pip will automatically start a source installation process - **_which will fail_** if it finds no MuPDF installation.

Folder [installation](https://github.com/pymupdf/PyMuPDF/tree/master/installation) contains platform-specific source installation scripts contributed by users. You may also find the following Wiki pages useful:

* [Ubuntu installation experience](https://github.com/pymupdf/PyMuPDF/wiki/Ubuntu-Installation-Experience).

* [Windows wheels](https://github.com/pymupdf/PyMuPDF/wiki/Windows-Binaries-Generation).


# License and Copyright
In order to comply with MuPDF’s dual licensing model, PyMuPDF has entered into an agreement with Artifex who has the right to sublicense PyMuPDF to third parties.

PyMuPDF and MuPDF are now available under both, open-source AGPL and commercial license agreements.

Please read the full text of the [AGPL license agreement](https://www.gnu.org/licenses/agpl-3.0.html) (which is also included here in file COPYING) to ensure that your use case complies with the guidelines of this license. If you determine you cannot meet the requirements of the AGPL, please contact [Artifex](https://artifex.com/contact/) for more information regarding a commercial license.

Artifex is the exclusive commercial licensing agent for MuPDF.

Artifex, the Artifex logo, MuPDF, and the MuPDF logo are registered trademarks of Artifex Software Inc. © 2021 Artifex Software, Inc. All rights reserved.

# Contact
Please use the [Discussions](https://github.com/pymupdf/PyMuPDF/discussions) menu for questions, comments, or asking for help, and submit issues [here](https://github.com/pymupdf/PyMuPDF/issues). If you wish, you can also contact me directly via jorj.x.mckie@outlook.de.
