PyMuPDF 1.9.1

Release date: May, 2016

Authors
=======

* Ruikai Liu
* Jorj X. McKie


Introduction
============

This is **version 1.9.1 of PyMuPDF (formerly python-fitz)**, a Python binding which supports `MuPDF 1.9a <http://mupdf.com/>`_ - "a lightweight PDF and XPS viewer".

MuPDF can access files in PDF, XPS, OpenXPS and EPUB (e-book) formats, and it is known for its top performance and high rendering quality.

With PyMuPDF you therefore can also access files with extensions ``*.pdf``, ``*.xps``, ``*.oxps`` or ``*.epub`` from your Python scripts.

See the `Wiki <https://github.com/rk700/PyMuPDF/wiki>`_ for more info/news/release notes/etc.


Installation
============

Normally it should be as easy as running ``python setup.py install`` once MuPDF is in place (i.e. its binaries have been built / generated or have been made available otherwise).

Refer to this `document <http://pythonhosted.org/PyMuPDF/installation.html>`_ for details.

Arch Linux
----------
AUR: https://aur.archlinux.org/packages/python2-pymupdf/

Ubuntu
------
Since MuPDF v1.9a is not available yet in the official repo, you need to first build it from source. Make sure to add ``-fPIC`` to CFLAGS when compiling.

When MuPDF is ready, edit ``setup.py`` in PyMuPDF and comment out the line of ``library_dirs=[]`` to specify the directory which contains ``libmupdf.a`` and other 3rd party libraries. Remove ``crypto`` from ``libraries`` in ``setup.py`` if it complains.

OSX
---
First please make sure that the dependencies are satisfied: ``brew install mupdf-tools jpeg jbig2dec freetype openssl``

Then you might need to ``export ARCHFLAGS='-arch x86_64'`` since ``libmupdf.a`` is for x86_64 only.

Finally, please double check ``setup.py`` before building. Update ``include_dirs`` and ``library_dirs`` if necessary.

Windows
-------
You can download pre-generated binaries from `here <https://github.com/JorjMcKie/PyMuPDF-optional-material/tree/master/binary_setups>`_ that are suitable for your Python version, and thereby avoid any compilation hassle. Please refer to this `document <http://pythonhosted.org/PyMuPDF/installation.html>`_ for details.

If you want to make your own binary, have a look at this `Wiki page <https://github.com/rk700/PyMuPDF/wiki/Windows-Binaries-Generation>`_. It explains how to use Visual Studio for generating MuPDF in some detail.

Usage
=====

Please have a look at the basic `demos <https://github.com/rk700/PyMuPDF/tree/master/demo>`_ or the `examples <https://github.com/rk700/PyMuPDF/tree/master/examples>`_ which contain complete, working programs.

You can also access the complete documentation as a `PDF <https://github.com/rk700/PyMuPDF/tree/master/doc/PyMuPDF.pdf>`_ or as a `Windows compiled html <https://github.com/JorjMcKie/PyMuPDF-optional-material/tree/master/doc/PyMuPDF.chm>`_.

Legacy Support
==============
* `Code compatible with MuPDF v1.8 <https://github.com/rk700/PyMuPDF/releases/tag/v1.8>`_

* `Code compatible with MuPDF v1.7a <https://github.com/rk700/PyMuPDF/releases/tag/v1.7>`_

* `Code compatible with MuPDF v1.2 <https://github.com/rk700/PyMuPDF/releases/tag/v1.2>`_

License
=======

PyMuPDF is distributed under GNU GPL V3.

Contact
=======

You can also find PyMuPDF on the Python Package Index `PyPI <https://pypi.python.org/pypi/PyMuPDF/1.9.1>`_.

We invite you to join our efforts by contributing to the the wiki pages.

Please submit comments or any issues either to this site or by sending an e-mail to the authors
`Ruikai Liu`_, `Jorj X. McKie`_.

.. _Ruikai Liu: lrk700@gmail.com
.. _Jorj X. McKie: jorj.x.mckie@outlook.de
