======================
README for python-fitz
======================

python-fitz is a set of python bindings for MuPDF's rendering library. Most of the work is done by SWIG with ``-builtin`` option on.

An online document can be found at http://rk700.github.com/python-fitz/index.html

Dependencies
------------

This module depends on the source code of `MuPDF <http://mupdf.com/downloads/archive/>`_ (version 1.2). 

The source must be compiled / generated in order to be used by this package.  

Non-Windows: You need to generate MuPDF with the ``-fPIC`` option.  

Windows: Use one of the (free) Visual Studio editions and the process is straightforward and almost hassle-free.

Install
-------
Download mupdf source version 1.2 and unzip it.  

Generate / compile mupdf according to your platform.  

Download and unzip this repository.  
Update setup.py as necessary. Under Windows / Visual Studio, required changes are quite significant. Therefore a separate setup file, setupwin.py is provided.  

Then run

	python setup.py install

If you are unsure what this process does, you can always do this

	python setup.py --help

and / or consult the Python documentation on distutils.


Comments and bug reports
------------------------
Project page is on
https://github.com/rk700/python-fitz

You can also send email to the author:
`Ruikai Liu`_ 

.. _Ruikai Liu: lrk700@gmail.com
