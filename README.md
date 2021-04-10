# PyMuPDF 1.18.12

![logo](https://github.com/pymupdf/PyMuPDF/blob/master/demo/pymupdf.jpg)

Release date: April 10, 2021

**Travis-CI:** [![Build Status](https://travis-ci.org/JorjMcKie/py-mupdf.svg?branch=master)](https://travis-ci.org/JorjMcKie/py-mupdf)


On **[PyPI](https://pypi.org/project/PyMuPDF)** since August 2016: [![Downloads](https://static.pepy.tech/personalized-badge/pymupdf?period=total&units=international_system&left_color=black&right_color=orange&left_text=Downloads)](https://pepy.tech/project/pymupdf)

# Authors
* [Jorj X. McKie](mailto:jorj.x.mckie@outlook.de)
* [Ruikai Liu](mailto:lrk700@gmail.com)

# Introduction

PyMuPDF (current version 1.18.12) is a Python binding with support for [MuPDF](https://mupdf.com/) (current version 1.18.*), a lightweight PDF, XPS, and E-book viewer, renderer, and toolkit, which is maintained and developed by Artifex Software, Inc.

MuPDF can access files in PDF, XPS, OpenXPS, CBZ, EPUB and FB2 (e-books) formats, and it is known for its top performance and high rendering quality.

With PyMuPDF you can access files with extensions like ".pdf", ".xps", ".oxps", ".cbz", ".fb2" or ".epub". In addition, about 10 popular image formats can also be handled like documents: ".png", ".jpg", ".bmp", ".tiff", etc..

> In partnership with [Artifex](https://artifex.com/), PyMuPDF is now also available for commercial licensing. This agreement has no impact on use cases, that are compliant with the open-source license AGPL. Please see the "License and Copyright" section below for additional information.

# Usage and Documentation
For all supported document types (i.e. **_including images_**) you can
* decrypt the document
* access meta information, links and bookmarks
* render pages in raster formats (PNG and some others), or the vector format SVG
* search for text
* extract text and images
* convert to other formats: PDF, (X)HTML, XML, JSON, text

> To some degree, PyMuPDF can therefore be used as an [image converter](https://github.com/pymupdf/PyMuPDF/wiki/How-to-Convert-Images): it can read a range of input formats and can produce **Portable Network Graphics (PNG)**, **Portable Anymaps** (**PNM**, etc.), **Portable Arbitrary Maps (PAM)**, **Adobe Postscript** and **Adobe Photoshop** documents, making the use of other graphics packages obselete in these cases. But interfacing with e.g. PIL/Pillow for image input and output is easy as well.

For **PDF documents,** there exists a plethorea of additional features: they can be created, joined or split up. Pages can be inserted, deleted, re-arranged or modified in many ways (including annotations and form fields).

* Images and fonts can be extracted or inserted.
    > You may want to have a look at [this](https://github.com/pymupdf/PyMuPDF-Utilities/blob/master/examples/image-maintenance.py) cool GUI example script, which lets you **_insert, delete, replace_** or **_re-position_** images under your visual control.

    > Since v1.18.8 there is a new experimental `Document` method `subset_fonts()`, which automatically builds subsets based on the usage of all eligible fonts in the document. Especially for new documents, this can lead to significant file size reductions. The method was developed in cooperation with our user @cuteufo - again thanks a lot for the contribution.
* Embedded files are fully supported.
* PDFs can be reformatted to support double-sided printing, posterizing, applying logos or watermarks
* Password protection is fully supported: decryption, encryption, encryption method selection, permmission level and user / owner password setting.
* Support of the **PDF Optional Content** concept for images, text and drawings.
* Low-level PDF structures can be accessed and modified.
* PyMuPDF can also be used as a **module in the command line** using ``"python -m fitz ..."``. This is a versatile utility, which we will further develop going forward. It currently supports PDF document

    - **encryption / decryption / optimization**
    - creating **sub-documents**
    - document **joining**
    - **image / font extraction**
    - full support of **embedded files**.


Have a look at the basic [demos](https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/demo), the [examples](https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples) (which contain complete, working programs), and the **recipes** section of our [Wiki](https://github.com/pymupdf/PyMuPDF/wiki) sidebar, which contains more than a dozen of guides in How-To-style.

Our **documentation**, written using Sphinx, is available in various formats from the following sources. It currently is a combination of a reference guide and a user manual. For a **quick start** look at the [tutorial](https://pymupdf.readthedocs.io/en/latest/tutorial/) and the [recipes](https://pymupdf.readthedocs.io/en/latest/faq/) chapters.

* You can view it online at [Read the Docs](https://readthedocs.org/projects/pymupdf/). This site also provides download options for PDF.
* The search function on Read the Docs does not work for me currently. If you want a working searchable local version, please download a zipped HTML for [here](https://github.com/pymupdf/PyMuPDF-optional-material/tree/master/doc/pymupdf.zip).
* Find a Windows help file [here](https://github.com/pymupdf/PyMuPDF-optional-material/tree/master/doc/PyMuPDF.chm).


# Installation

For Windows, Linux and Mac OSX platforms, there are wheels in the [download](https://pypi.org/project/PyMuPDF/#files) section of PyPI. This includes Python 64bit versions **3.6 through 3.9**. For Windows only, 32bit versions are available too.

If your platform is not supported with one of our wheels, you need to generate PyMuPDF yourself as follows. This requires the development version of Python.

Before you can do that, you must first build MuPDF. For most platforms, the MuPDF sources contain prepared procedures for achieving this. Please observe the following general steps:

* Be sure to download the **_official MuPDF source release_** from [here](https://mupdf.com/downloads/archive). Do not use MuPDF's [GitHub repo](https://github.com/ArtifexSoftware/mupdf). It contains their development source for future versions.

* This repo's [fitz](https://github.com/pymupdf/PyMuPDF/tree/master/fitz) folder contains one or more files whose names start with a single underscore `"_"`. These files contain configuration data and potentially other fixes. Copy-rename each of them to their correct target location within the downloaded MuPDF source. Currently, these files are:
  - **Optional:** fitz configuration file `_config.h` copy-replace to: `mupdf/include/mupdf/fitz/config.h`. It contains configuration data like e.g. which fonts to support. If omitting this change, the binary extension module will be over 30 MB (compared to around 11 MB). Does not impact functionality.

  - Now MuPDF can be generated.

* Please note that you will need the interface generator [SWIG](http://www.swig.org/) when building PyMuPDF from the sources of this repository (please refer to issue #312 for some background on this).
    - PyMuPDF wheels are being generated using **SWIG v4.0.2**.

* If you do **not use SWIG**, please download the **sources from PyPI** - they contain sources pre-processed by SWIG, so installation should work like any other Python extension generation on your system.

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

# License and Copyright
In order to comply with MuPDF’s dual licensing model, PyMuPDF has entered into an agreement with Artifex who has the right to sublicense PyMuPDF to third parties.

PyMuPDF and MuPDF are now available under both, open-source AGPL and commercial license agreements.

Please read the full text of the [AGPL license agreement](https://www.gnu.org/licenses/agpl-3.0.html) (which is also included here in file COPYING) to ensure that your use case complies with the guidelines of this license. If you determine you cannot meet the requirements of the AGPL, please contact [Artifex](https://artifex.com/contact/) for more information regarding a commercial license.

Artifex is the exclusive commercial licensing agent for MuPDF.

Artifex, the Artifex logo, MuPDF, and the MuPDF logo are registered trademarks of Artifex Software Inc. © 2021 Artifex Software, Inc. All rights reserved.

# Contact
Please use the [Discussions](https://github.com/pymupdf/PyMuPDF/discussions) menu for questions, comments, or asking others for help, and submit issues [here](https://github.com/pymupdf/PyMuPDF/issues). If you wish, you can also contact me directly via jorj.x.mckie@outlook.de.
