======================
README for python-fitz
======================

python-fitz is a set of python bindings for MuPDF's rendering library. Most of the work is done by SWIG with ``-builtin`` option on.

A online document can be found at http://rk700.github.com/python-fitz/index.html

Dependencies
------------

This module depends on `MuPDF <http://www.mupdf.com>`_ (version=1.2). 

By default, fitz is compiled as a static lib. If that's the case, you need to recompile MuPDF with ``-fPIC`` option.

Install
-------
Extract the tarball and run

	python setup.py install

Run

	python setup.py --help

for more information about installation.


Comments and bug reports
------------------------
Project page is on
https://github.com/rk700/python-fitz

You can also send email to the author:
`Ruikai Liu`_ 

.. _Ruikai Liu: lrk700@gmail.com
