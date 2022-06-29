Installation
=============

PyMuPDF should be installed using pip with::

  python -m pip install --upgrade pip
  python -m pip install --upgrade pymupdf

This will install from a Python wheel if one is available for your platform.

If a suitable Python wheel is not available, pip will automatically build from
source using a Python sdist. **This requires that SWIG is installed**:

* On Unix-style systems such as Linux, OpenBSD and FreeBSD,
  use the system package manager to install SWIG.

  * For example on Debian Linux, do: ``sudo apt install swig``

* On Windows, install SWIG by following the instructions at:
  https://swig.org/Doc4.0/Windows.html#Windows_installation.

* On MacOS, install MacPorts using the instructions at:
  https://www.macports.org/install.php

  * Then install SWIG with: ``sudo port install swig``

As of ``PyMuPDF-1.20.0``, the required MuPDF source code is already in the
sdist and is automatically built into PyMuPDF.


Notes
~~~~~

Wheels are available for Windows (32-bit Intel, 64-bit Intel), Linux (64-bit Intel, 64-bit ARM) and Mac OSX (64-bit Intel), Python versions 3.7 and up.

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

First get a PyMuPDF source tree:

* Clone the git repository at https://github.com/pymupdf/PyMuPDF,
  for example::

      git clone https://github.com/pymupdf/PyMuPDF.git

* Or download a ``.zip`` or ``.tar.gz`` source release from
  https://github.com/pymupdf/PyMuPDF/releases.

Install SWIG as described above, then build PyMuPDF::

  cd PyMuPDF && python setup.py install

* This will automatically download a specific hard-coded MuPDF source release,
  and build it into PyMuPDF.

* One can build with a different MuPDF (for example one installed on the
  system, or a local custom build) by setting environmental variables.

  * See the documentation at the start of ``setup.py`` for more information.


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
