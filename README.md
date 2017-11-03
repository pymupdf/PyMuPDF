# PyMuPDF 1.11.1

![logo](https://github.com/rk700/PyMuPDF/blob/master/demo/pymupdf.jpg)

Release date: Sept 1, 2017

# Authors
* [Ruikai Liu](lrk700@gmail.com)
* [Jorj X. McKie](jorj.x.mckie@outlook.de)

# Introduction

This is **version 1.11.1 of PyMuPDF (formerly python-fitz)**, a Python binding which supports [MuPDF 1.11](http://mupdf.com/) - "a lightweight PDF and XPS viewer".

MuPDF can access files in PDF, XPS, OpenXPS, CBZ, EPUB and FB2 (e-books) formats, and it is known for its top performance and high rendering quality.

With PyMuPDF you therefore can also access files with extensions ``*.pdf``, ``*.xps``, ``*.oxps``, ``*.cbz``, ``*.fb2`` or ``*.epub`` from your Python scripts.

See the [Wiki](https://github.com/rk700/PyMuPDF/wiki) for more information, [news](https://github.com/rk700/PyMuPDF/wiki/Change-and-News-Log), release notes and usage recipies.


# Installation
If you had not previously installed MuPDF, you must first do this (however, see the **MS Windows** section further down). This process very much depends on your system. For most platforms, the MuPDF source contains prepared procedures on how to achieve this.

If you decide to generate MuPDF from sources (definitely the safest and cleanest way for all platforms except MS Windows), be sure to download the official release from [here](https://mupdf.com/downloads). Although MuPDF also has a GitHub repo, this contains their current **development source**, which usually is incompatible with this PyMuPDF.

Once MuPDF is in place, installing PyMuPDF comes down to running the usual ``python setup.py install``.

Refer to our documentation for additional comments.

## Arch Linux
AUR: https://aur.archlinux.org/packages/python2-pymupdf/ currently only provides PyMuPDF version 1.9.2 for Python 2.

## Ubuntu
The required MuPDF version in the official Ubuntu repositories is often not timely available, so you do need to build it from source. Make sure to add ``-fPIC`` to CFLAGS when compiling.

When MuPDF is ready, edit ``setup.py`` in PyMuPDF and comment out the line of ``library_dirs=[]`` to specify the directory which contains ``libmupdf.a`` and other 3rd party libraries. Remove ``crypto`` from ``libraries`` in ``setup.py`` if it complains. One of our users (thanks to @gileadslostson) has documented his MuPDF installation experience from sources in this [Wiki page](https://github.com/rk700/PyMuPDF/wiki/Experience-from-an-Ubuntu-installation).

## OSX
First, install the MuPDF headers and libraries, which are provided by mupdf-tools: ``brew install mupdf-tools``.

Then you might need to ``export ARCHFLAGS='-arch x86_64'`` since ``libmupdf.a`` is for x86_64 only.

Finally, please double check ``setup.py`` before building. Update ``include_dirs`` and ``library_dirs`` if necessary.

## MS Windows
The lucky Windows user can now just issue `pip install PyMuPDF [--upgrade]` and is done in no more time than a 3 MB download takes. This requires **nothing else** - no MuPDF, no Visual Studio, ... whatsoever.

If you don't use ``pip`` or [PyPI](https://pypi.org/project/PyMuPDF/), you can still download pre-generated binaries or Python wheels from [here](https://github.com/JorjMcKie/PyMuPDF-Optional-Material) that are suitable for your Python / Windows combination. This, too, avoids any other downloads or compilation hassle. Again, make sure to consult our documentation.

If you do want to make your own binary however, have a look at this [Wiki page](https://github.com/rk700/PyMuPDF/wiki/Windows-Binaries-Generation). It explains how to use Visual Studio for generating MuPDF in quite some detail. Also do not hesitate to contact us if you need help.

# Usage and Documentation
Please have a look at the basic [demos](https://github.com/rk700/PyMuPDF/tree/master/demo), the [examples](https://github.com/rk700/PyMuPDF/tree/master/examples) which contain complete, working programs, and the **recipies** section of our [Wiki](https://github.com/rk700/PyMuPDF/wiki) sidebar.

You have a number of options to access the **documentation**:

* You can view it online at [Read the Docs](https://pymupdf.readthedocs.io/en/latest/), which you can also download as [HTML ZIP file](https://github.com/rk700/PyMuPDF/tree/master/doc/html.zip).
* You can download a [Windows CHM](https://github.com/JorjMcKie/PyMuPDF-optional-material/tree/master/doc/PyMuPDF.chm).
* You can download a [PDF](https://github.com/rk700/PyMuPDF/tree/master/doc/pymupdf.pdf).

> The new **PyPI Warehouse** no longer supports the maintenance of documentation hosted at https://pythonhosted.org. Their plans also include to retire this facility altogether as the PyPI Warehouse matures. They are encouraging the use of https://readthedocs.org instead.

> We have decided to immediately follow their recommendation. Therefore, you will now find PyMuPDF's current online documentation on **Read the Docs** as indicated above. Because we haven't been able to update our documentation on **pythonhosted.org** since June of 2017, we also decided to delete it there to avoid confusion.

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
You can also find us on the Python Package Index [PyPI](https://pypi.org/project/PyMuPDF/).

> Please note, that the project description on PyPI may be less current than the one you are looking at. This is because information on PyPI cannot be changed once stored there. Previously, this has been true for download files only, but since **PyPI Warehouse**, it obviously applies to everything else that defines a project (verbal description, classifiers, platforms, etc.).

We invite you to join our efforts by contributing to the [Wiki](https://github.com/rk700/PyMuPDF/wiki) pages.

Please submit comments or issues [here](https://github.com/rk700/PyMuPDF/issues), or directly contact the authors.
