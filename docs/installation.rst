.. include:: header.rst



Installation
=============

Requirements
---------------------------------------------------------

All the examples below assume that you are running inside a Python virtual
environment. See: https://docs.python.org/3/library/venv.html for details.
We also assume that `pip` is up to date.

For example:

* Windows::

    py -m venv pymupdf-venv
    .\pymupdf-venv\Scripts\activate
    python -m pip install --upgrade pip

* Linux, MacOS::

    python -m venv pymupdf-venv
    . pymupdf-venv/bin/activate
    python -m pip install --upgrade pip


Installation
---------------------------------------------------------

PyMuPDF should be installed using pip with::

  pip install --upgrade pymupdf

This will install from a Python wheel if one is available for your platform.


Installation when a suitable wheel is not available
---------------------------------------------------------

If a suitable Python wheel is not available, pip will automatically build from
source using a Python sdist.

**This requires C/C++ development tools to be installed**:

* On Windows:

  *
    Install Visual Studio 2019. If not installed in a standard location, set
    environmental variable `PYMUPDF_SETUP_DEVENV` to the location of the
    `devenv.com` binary.

  *
    Having other installed versions of Visual Studio, for example Visual Studio
    2022, can cause problems because one can end up with MuPDF and PyMuPDF code
    being compiled with different compiler versions.

As of `PyMuPDF-1.20.0`, the required MuPDF source code is already in the
sdist and is automatically built into PyMuPDF.


Problems after installation
---------------------------------------------------------

* On Windows `ImportError: DLL load failed while importing _fitz`.

  This has been occasionally seen if `MSVCP140.dll` is missing, and appears
  to be caused by a bug in some versions (2015-2017) of `Microsoft Visual C++
  Redistributables`.

  It is recommended to search for `MSVCP140.dll` in https://msdn.com
  to find instructions for how to reinstall it. For example
  https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist has
  permalinks to the latest supported versions.

  See https://github.com/pymupdf/PyMuPDF/issues/2678 for more details.


Notes
---------------------------------------------------------

Wheels are available for Windows (32-bit Intel, 64-bit Intel), Linux (64-bit Intel, 64-bit ARM) and Mac OSX (64-bit Intel, 64-bit ARM), Python versions 3.7 and up.

Wheels are not available for Python installed with `Chocolatey
<https://chocolatey.org/>`_ on Windows. Instead install Python
using the Windows installer from the python.org website, see:
http://www.python.org/downloads

PyMuPDF does not support Python versions prior to 3.8. Older wheels can be found in `this <https://github.com/pymupdf/PyMuPDF-Optional-Material/tree/master/wheels-upto-Py3.5>`_ repository and on `PyPI <https://pypi.org/project/PyMuPDF/>`_.
Please note that we generally follow the official Python release schedules. For Python versions dropping out of official support this means, that generation of wheels will also be ceased for them.

There are no **mandatory** external dependencies. However, some optional feature are available only if additional components are installed:

* `Pillow <https://pypi.org/project/Pillow/>`_ is required for :meth:`Pixmap.pil_save` and :meth:`Pixmap.pil_tobytes`.
* `fontTools <https://pypi.org/project/fonttools/>`_ is required for :meth:`Document.subset_fonts`.
* `pymupdf-fonts <https://pypi.org/project/pymupdf-fonts/>`_ is a collection of nice fonts to be used for text output methods.
* `Tesseract-OCR <https://github.com/tesseract-ocr/tesseract>`_ for optical character recognition in images and document pages. Tesseract is separate software, not a Python package. To enable OCR functions in PyMuPDF, the software must be installed and the system environment variable `"TESSDATA_PREFIX"` must be defined and contain the `tessdata` folder name of the Tesseract installation location. See below.

.. note:: You can install these additional components at any time -- before or after installing PyMuPDF. PyMuPDF will detect their presence during import or when the respective functions are being used.


Build and install from local PyMuPDF checkout and optional local MuPDF checkout
-------------------------------------------------------------------------------

* Install C/C++ development tools as described above.

* Enter a Python venv and update pip, as described above.

* Get a PyMuPDF source tree:

  * Clone the PyMuPDF git repository::

      git clone https://github.com/pymupdf/PyMuPDF.git

  * Or download and extract a `.zip` or `.tar.gz` source release from
    https://github.com/pymupdf/PyMuPDF/releases.


* Build and install PyMuPDF::

    cd PyMuPDF && pip install .

  This will automatically download a specific hard-coded MuPDF source release,
  and build it into PyMuPDF.


Build and install PyMuPDF using a local MuPDF source tree:

* Clone the MuPDF git repository::

    git clone --recursive https://ghostscript.com:/home/git/mupdf.git

*
  Build PyMuPDF, specifying the location of the local MuPDF tree with the
  environmental variables `PYMUPDF_SETUP_MUPDF_BUILD`::

    cd PyMuPDF && PYMUPDF_SETUP_MUPDF_BUILD=../mupdf pip install .


Building for different Python versions in same PyMuPDF tree:

*
  PyMuPDF will build for the version of Python that is being used to run
  `pip`. To run `pip` with a specific Python version, use `python -m pip`
  instead of `pip`.

  So for example on Windows one can build different versions with::

    cd PyMuPDF && py -3.9 -m pip install .

  or::

    cd PyMuPDF && py -3.10-32 -m pip install .


.. note:: When running Python scripts that use PyMuPDF, make sure that the
  current directory is not the `PyMuPDF/` directory.

  Otherwise, confusingly, Python will attempt to import `fitz` from the local
  `fitz/` directory, which will fail because it only contains source files.


Running tests
---------------------------------------------------------

Having a PyMuPDF tree available allows one to run PyMuPDF's `pytest` test
suite::

  pip install pytest fontTools
  pytest PyMuPDF/tests



Notes about using a non-default MuPDF
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Using a non-default build of MuPDF by setting environmental variable
`PYMUPDF_SETUP_MUPDF_BUILD` can cause various things to go wrong and so is
not generally supported:

* If MuPDF's major version number differs from what PyMuPDF uses by default,
  PyMuPDF can fail to build, because MuPDF's API can change between major
  versions.

* Runtime behaviour of PyMuPDF can change because MuPDF's runtime behaviour
  changes between different minor releases. This can also break some PyMuPDF
  tests.

* If MuPDF was built with its default config instead of PyMuPDF's customised
  config (for example if MuPDF is a system install), it is possible that
  `tests/test_textbox.py:test_textbox3()` will fail. One can skip this
  particular test by adding `-k 'not test_textbox3'` to the `pytest`
  command line.


Packaging
---------

See :doc:`packaging`.


Enabling Integrated OCR Support
---------------------------------------------------------

If you do not intend to use this feature, skip this step. Otherwise, it is required for both installation paths: **from wheels and from sources.**

PyMuPDF will already contain all the logic to support OCR functions. But it additionally does need `Tesseract’s language support data <https://github.com/tesseract-ocr/tessdata>`_.

The language support folder location must be communicated either via storing it in the environment variable `"TESSDATA_PREFIX"`, or as a parameter in the applicable functions.

So for a working OCR functionality, make sure to complete this checklist:

1. Locate Tesseract's language support folder. Typically you will find it here:
    - Windows: `C:/Program Files/Tesseract-OCR/tessdata`
    - Unix systems: `/usr/share/tesseract-ocr/4.00/tessdata`

2. Set the environment variable `TESSDATA_PREFIX`
    - Windows: `setx TESSDATA_PREFIX "C:/Program Files/Tesseract-OCR/tessdata"`
    - Unix systems: `declare -x TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata`

.. note:: On Windows systems, this must happen outside Python -- before starting your script. Just manipulating `os.environ` will not work!

.. include:: footer.rst
