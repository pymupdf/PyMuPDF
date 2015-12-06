PyMuPDF 1.8.0

Release date: Nov 15th, 2015

Authors
=======

* Ruikai Liu
* Jorj X. McKie


Introduction
============

This is the **new version 1.8 of PyMuPDF (formerly python-fitz)**, a Python binding which supports `MuPDF 1.8 <http://mupdf.com/>`_ - "a lightweight PDF and XPS viewer".

MuPDF can access files in PDF, XPS, OpenXPS and EPUB (e-book) formats, and it is known for its top performance and high rendering quality.

With PyMuPDF you therefore can also access files with extensions ``*.pdf``, ``*.xps``, ``*.oxps`` or ``*.epub`` from your Python scripts.


Installation
============

Normally it should be as easy as running ``python setup.py install`` once MuPDF is in place (i.e. its binaries have been built / generated).

For linux users, please make sure that the following libraries are available: ``libmupdf``, ``libmujs``, ``libcrypto``, ``libjbig2dec``, ``libopenjp2``, ``libjpeg``, ``libfreetype``.

Refer to this `document <http://pythonhosted.org/PyMuPDF/installation.html>`_ for details.


Usage
=====

Please have a look at the basic `demos <https://github.com/rk700/PyMuPDF/tree/master/demo>`_ or the `examples <https://github.com/rk700/PyMuPDF/tree/master/examples>`_ which contain complete, working programs.

You can also access the complete documentation as a `PDF <https://github.com/rk700/PyMuPDF/tree/master/doc/PyMuPDF.pdf>`_ or as a `Windows compiled html <https://github.com/JorjMcKie/PyMuPDF-optional-material/tree/master/doc/PyMuPDF.chm>`_.

Legacy Support
==============

* `Code compatible with MuPDF v1.7a <https://github.com/rk700/PyMuPDF/releases/tag/v1.7>`_

* `Code compatible with MuPDF v1.2 <https://github.com/rk700/PyMuPDF/releases/tag/v1.2>`_

License
=======

PyMuPDF is distributed under GNU GPL v3.

Contact
=======

You can also find PyMuPDF on the Python Package Index `PyPI <https://pypi.python.org/pypi/PyMuPDF/1.8.0>`_.

We invite you to join our efforts by contributing to the the wiki pages.

Please submit comments or any issues either to this site or by sending an e-mail to the authors
`Ruikai Liu`_, `Jorj X. McKie`_.

.. _Ruikai Liu: lrk700@gmail.com 
.. _Jorj X. McKie: jorj.x.mckie@outlook.de
