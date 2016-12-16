PyMuPDF 1.10.0
================

Release date: December, 2016

Authors
=======

* Ruikai Liu
* Jorj X. McKie


Introduction
============

This is **version 1.10.0 of PyMuPDF (formerly python-fitz)**, a Python binding which supports `MuPDF 1.10a <http://mupdf.com/>`_ - "a lightweight PDF and XPS viewer".

MuPDF can access files in PDF, XPS, OpenXPS, CBZ, EPUB and FB2 (e-books) formats, and it is known for its top performance and high rendering quality.

With PyMuPDF you therefore can also access files with extensions ``*.pdf``, ``*.xps``, ``*.oxps``, ``*.cbz``, ``*.fb2`` or ``*.epub`` from your Python scripts.

See the `Wiki <https://github.com/rk700/PyMuPDF/wiki>`_ for more info/news/release notes/etc.


Installation
============

If you had not previously installed MuPDF, you must first do this. This process highly depends on your system. For most platforms, the MuPDF source contains prepared procedures on how to achieve this. Linux distributions usually also provide their own ways on how to install MuPDF. See below for more details.

Once MuPDF is in place, installing PyMuPDF comes down to running the usual ``python setup.py install``.

Also refer to this `document <http://pythonhosted.org/PyMuPDF/installation.html>`_ for details.

Arch Linux
----------
AUR: https://aur.archlinux.org/packages/python2-pymupdf/

Ubuntu
------
Since MuPDF v1.10a is not available yet in the official repo, you need to first build it from source. Make sure to add ``-fPIC`` to CFLAGS when compiling.

When MuPDF is ready, edit ``setup.py`` in PyMuPDF and comment out the line of ``library_dirs=[]`` to specify the directory which contains ``libmupdf.a`` and other 3rd party libraries. Remove ``crypto`` from ``libraries`` in ``setup.py`` if it complains.

OSX
---
First, install the MuPDF headers and libraries, which are provided by mupdf-tools: ``brew install mupdf-tools``

Then you might need to ``export ARCHFLAGS='-arch x86_64'`` since ``libmupdf.a`` is for x86_64 only.

Finally, please double check ``setup.py`` before building. Update ``include_dirs`` and ``library_dirs`` if necessary.

Windows
-------
You can download pre-generated binaries from `here <https://github.com/JorjMcKie/PyMuPDF-optional-material/tree/master/binary_setups>`_ that are suitable for your Python version, and thereby avoid any compilation hassle. Please refer to this `document <http://pythonhosted.org/PyMuPDF/installation.html>`_ for details.

If you want to make your own binary however, have a look at this `Wiki page <https://github.com/rk700/PyMuPDF/wiki/Windows-Binaries-Generation>`_. It explains how to use Visual Studio for generating MuPDF in quite some detail. Also do not hesitate to contact us if you need help.

Usage and Documentation
=========================

Please have a look at the basic `demos <https://github.com/rk700/PyMuPDF/tree/master/demo>`_ or the `examples <https://github.com/rk700/PyMuPDF/tree/master/examples>`_ which contain complete, working programs.

You have a variety of options to access the **documentation**:

* You can view it online at `PyPI <http://pythonhosted.org/PyMuPDF/>`_ or at `Read the Docs <https://pymupdf.readthedocs.io/en/latest/>`_. **Read the Docs** also lets you download versions in PDF (see below), HTML and EPUB formats.
* You can download a `Windows compiled html <https://github.com/JorjMcKie/PyMuPDF-optional-material/tree/master/doc/PyMuPDF.chm>`_.
* You can download a `PDF <https://media.readthedocs.org/pdf/pymupdf/latest/pymupdf.pdf>`_ from **Read the Docs**.
You can access the complete documentation (which contains a detailed tutorial) as a `PDF <https://github.com/rk700/PyMuPDF/tree/master/doc/PyMuPDF.pdf>`_, as a `Windows compiled html <https://github.com/JorjMcKie/PyMuPDF-optional-material/tree/master/doc/PyMuPDF.chm>`_ or at `PyPI <http://pythonhosted.org/PyMuPDF/>`_.

Earlier Versions
================
* `PyMuPDF Version 1.9.3 <https://github.com/rk700/PyMuPDF/tree/1.9.3>`_

* `PyMuPDF Version 1.9.2 <https://github.com/rk700/PyMuPDF/releases/tag/v1.9.2>`_

* `PyMuPDF Version 1.9.1 <https://github.com/rk700/PyMuPDF/releases/tag/v1.9.1>`_

* `Code compatible with MuPDF v1.8 <https://github.com/rk700/PyMuPDF/releases/tag/v1.8>`_

* `Code compatible with MuPDF v1.7a <https://github.com/rk700/PyMuPDF/releases/tag/v1.7>`_

* `Code compatible with MuPDF v1.2 <https://github.com/rk700/PyMuPDF/releases/tag/v1.2>`_

License
=======

PyMuPDF is distributed under GNU GPL V3.

Contact
=======

You can also find PyMuPDF on the Python Package Index `PyPI <https://pypi.python.org/pypi/PyMuPDF/1.10.0>`_.

We invite you to join our efforts by contributing to the the wiki pages.

Please submit comments or any issues either to this site or by sending an e-mail to the authors
`Ruikai Liu`_, `Jorj X. McKie`_.

.. _Ruikai Liu: lrk700@gmail.com
.. _Jorj X. McKie: jorj.x.mckie@outlook.de
