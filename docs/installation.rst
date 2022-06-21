Installation
=============

PyMuPDF should be installed using pip with::

  python -m pip install --upgrade pip
  python -m pip install --upgrade pymupdf

This will install from a Python wheel if one is available for your platform.

Otherwise it will automatically build from source using a Python sdist:

* This requires that SWIG is installed.
* As of ``PyMuPDF-1.20.0``, the required MuPDF source code is already in the sdist and is automatically built into PyMuPDF.


Notes
~~~~~

Wheels are available for Windows (32bit and 64bit), Linux (64bit, Intel and ARM) and Mac OSX (64bit, Intel), Python versions 3.7 and up.

PyMuPDF does not support Python versions prior to 3.7. Older wheels can be found in `this <https://github.com/pymupdf/PyMuPDF-Optional-Material/tree/master/wheels-upto-Py3.5>`_ repository and on `PyPI <https://pypi.org/project/PyMuPDF/>`_.
Please note that we generally follow the official Python release schedules. For Python versions dropping out of official support this means, that generation of wheels will also be ceased for them.

There are no **mandatory** external dependencies. However, some optional feature are available only if additional components are installed:

* `Pillow <https://pypi.org/project/Pillow/>`_ is required for :meth:`Pixmap.pil_save` and :meth:`Pixmap.pil_tobytes`.
* `fontTools <https://pypi.org/project/fonttools/>`_ is required for :meth:`Document.subset_fonts`.
* `pymupdf-fonts <https://pypi.org/project/pymupdf-fonts/>`_ is a collection of nice fonts to be used for text output methods.
* `Tesseract-OCR <https://github.com/tesseract-ocr/tesseract>`_ for optical character recognition in images and document pages. Tesseract is separate software, not a Python package. To enable OCR functions in PyMuPDF, the software must be installed and the system environment variable ``"TESSDATA_PREFIX"`` must be defined and contain the ``tessdata`` folder name of the Tesseract installation location. See below.

.. note:: You can install these additional components at any time -- before or after installing PyMuPDF. PyMuPDF will detect their presence during import or when the respective functions are being used.


Install from source without using an sdist
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install SWIG on the system. Then::

  python setup.py install

This will automatically download a specific hard-coded MuPDF release, and build it into PyMuPDF.

See comments at the start of ``setup.py`` for more information.


Enabling Integrated OCR Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you do not intend to use this feature, skip this step. Otherwise, it is required for both installation paths: **from wheels and from sources.**

PyMuPDF will already contain all the logic to support OCR functions. But it additionally does need Tesseract's language support data, so installation of Tesseract-OCR is still required.

The language support folder location must currently [#f1]_ be communicated via storing it in the environment variable ``"TESSDATA_PREFIX"``.

So for a working OCR functionality, make sure to complete this checklist:

1. Install Tesseract.

2. Locate Tesseract's language support folder. Typically you will find it here:
    - Windows: ``C:\Program Files\Tesseract-OCR\tessdata``
    - Unix systems: ``/usr/share/tesseract-ocr/4.00/tessdata``

3. Set the environment variable ``TESSDATA_PREFIX``
    - Windows: ``set TESSDATA_PREFIX=C:\Program Files\Tesseract-OCR\tessdata``
    - Unix systems: ``export TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata``

.. note:: This must happen outside Python -- before starting your script. Just manipulating ``os.environ`` will not work!

.. rubric:: Footnotes

.. [#f1] In the next MuPDF version, it will be possible to pass this value as a parameter -- directly in the OCR invocations.
