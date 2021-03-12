Introduction
==============

.. image:: images/img-pymupdf.*
   :align: center
   :scale: 20

**PyMuPDF** is a Python binding for `MuPDF <http://www.mupdf.com/>`_ --  a lightweight PDF, XPS, and E-book viewer, renderer, and toolkit, which is maintained and developed by Artifex Software, Inc

MuPDF can access files in PDF, XPS, OpenXPS, CBZ, EPUB and FB2 (e-books) formats, and it is known for its top performance and high rendering quality.

MuPDF stands out among all similar products for its top rendering capability and unsurpassed processing speed. At the same time, its "light weight" makes it an excellent choice for platforms where resources are typically limited, like smartphones.

Check this out yourself and compare the various free PDF-viewers. In terms of speed and rendering quality `SumatraPDF <http://www.sumatrapdfreader.org/>`_ ranges at the top (apart from MuPDF's own standalone viewer) -- since it has changed its library basis to  MuPDF!

With PyMuPDF you can access files with extensions like “.pdf”, “.xps”, “.oxps”, “.cbz”, “.fb2” or “.epub”. In addition, about 10 popular image formats can also be opened and handled like documents.

PyMuPDF provides access to many important functions of MuPDF from within a Python environment, and we are continuously seeking to expand this function set.

PyMuPDF runs and has been tested on Mac, Linux and Windows for Python versions 3.6 and up. Other platforms should work too, as long as MuPDF and Python support them.

PyMuPDF is hosted on `GitHub <https://github.com/pymupdf/PyMuPDF>`_. We also are registered on `PyPI <https://pypi.org/project/PyMuPDF/>`_.

For MS Windows and popular Python versions on Mac OSX and Linux we have created wheels. So installation should be convenient enough for hopefully most of our users: just issue

*pip install --upgrade pymupdf*

If your platform is not among those supported with a wheel, your installation consists of two separate steps:

1. Installation of MuPDF: this involves downloading the source from their website and then compiling it on your machine. Adjust *setup.py* to point to the right directories (next step), before you try generating PyMuPDF.

2. Installation of PyMuPDF: this step is normal Python procedure. Usually you will have to adapt the *setup.py* to point to correct *include* and *lib* directories of your generated MuPDF.

For installation details check out the respective chapter.

There exist several `demo <https://github.com/pymupdf/PyMuPDF/tree/master/demo>`_ and `example <https://github.com/pymupdf/PyMuPDF/tree/master/examples>`_ programs in the main repository, ranging from simple code snippets to full-featured utilities, like text extraction, PDF joiners and bookmark maintenance.

Interesting **PDF manipulation and generation** functions have been added over time, including metadata and bookmark maintenance, document restructuring, annotation / link handling and document or page creation.

Note on the Name *fitz*
--------------------------
The standard Python import statement for this library is *import fitz*. This has a historical reason:

The original rendering library for MuPDF was called *Libart*.

*"After Artifex Software acquired the MuPDF project, the development focus shifted on writing a new modern graphics library called "Fitz". Fitz was originally intended as an R&D project to replace the aging Ghostscript graphics library, but has instead become the rendering engine powering MuPDF."* (Quoted from `Wikipedia <https://en.wikipedia.org/wiki/MuPDF>`_).

License and Copyright
----------------------
In order to comply with MuPDF’s dual licensing model, PyMuPDF has entered into an agreement with Artifex who has the right to sublicense PyMuPDF to third parties.

PyMuPDF and MuPDF are now available under both, open-source AGPL and commercial license agreements. Please read the full text of the AGPL license agreement, available in the distribution material (file COPYING) and `here <https://www.gnu.org/licenses/agpl-3.0.html>`_, to ensure that your use case complies with the guidelines of the license. If you determine you cannot meet the requirements of the AGPL, please contact `Artifex <https://artifex.com/contact/>`_ for more information regarding a commercial license.

Artifex is the exclusive commercial licensing agent for MuPDF.

Artifex, the Artifex logo, MuPDF, and the MuPDF logo are registered trademarks of Artifex Software Inc. © 2021 Artifex Software, Inc. All rights reserved.

.. include:: version.rst
