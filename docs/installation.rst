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

The build will automatically download and build MuPDF.


.. _problems-after-installation:

Problems after installation
---------------------------------------------------------

* On Windows, Python error::

      ImportError: DLL load failed while importing _fitz

  This has been occasionally seen if `MSVCP140.dll` is missing, and appears
  to be caused by a bug in some versions (2015-2017) of `Microsoft Visual C++
  Redistributables`.

  It is recommended to search for `MSVCP140.dll` in https://msdn.com
  to find instructions for how to reinstall it. For example
  https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist has
  permalinks to the latest supported versions.

  See https://github.com/pymupdf/PyMuPDF/issues/2678 for more details.

*
  Python error::

      ModuleNotFoundError: No module named 'frontend'
  
  This can happen if PyMuPDF's legacy name `fitz` is used (for example `import
  fitz` instead of `import pymupdf`), and an unrelated Python package called
  `fitz` (https://pypi.org/project/fitz/) is installed.

  The fitz package appears to be no longer maintained (the latest release is
  from 2017), but unfortunately it does not seem possible to remove it from
  pypi.org. It does not even work on its own, as well as breaking the use of
  PyMuPDF's legacy name.

  There are a few ways to avoid this problem:

  *
    Use `import pymupdf` instead of `import fitz`, and update one's code to
    match.

  * Or uninstall the `fitz` package and reinstall PyMuPDF::
  
        pip uninstall fitz
        pip install --force-reinstall pymupdf

  * Or use `import pymupdf as fitz`. However this has not been well tested.

* With Jupyter labs on Apple Silicon (arm64), Python error::

      ImportError: /opt/conda/lib/python3.11/site-packages/pymupdf/libmupdf.so.24.4: undefined symbol: fz_pclm_write_options_usage

  This appears to be a problem in Jupyter labs; see:
  https://github.com/pymupdf/PyMuPDF/issues/3643#issuecomment-2210588778.


Notes
---------------------------------------------------------

*
  Wheels are available for the following platforms:
  
   * Windows 32-bit Intel.
   * Windows 64-bit Intel.
   * Linux 64-bit Intel.
   * Linux 64-bit ARM.
   * MacOS 64-bit Intel.
   * MacOS 64-bit ARM.
  
  Details:
  
  * We release a single wheel for each of the above platforms.
  
  *
    Each wheel uses the Python Stable ABI of the current oldest supported
    Python version (currently 3.9), and so works with all later Python
    versions, including new Python releases.
  
  *
    Wheels are tested on all Python versions currently marked as "Supported" on
    https://devguide.python.org/versions/, currently 3.9, 3.10, 3.11, 3.12 and
    3.13.

*
  Wheels are not available for Python installed with `Chocolatey
  <https://chocolatey.org/>`_ on Windows. Instead install Python
  using the Windows installer from the python.org website, see:
  http://www.python.org/downloads

*
  Wheels are not available for Linux-aarch64 with `Musl libc
  <https://musl.libc.org/>`_ (For example `Alpine Linux
  <https://alpinelinux.org/>`_ on aarch64), and building from source is known
  to fail.

* There are no **mandatory** external dependencies. However, some optional feature are available only if additional components are installed:

  * `Pillow <https://pypi.org/project/Pillow/>`_ is required for :meth:`Pixmap.pil_save` and :meth:`Pixmap.pil_tobytes`.
  * `fontTools <https://pypi.org/project/fonttools/>`_ is required for :meth:`Document.subset_fonts`.
  * `pymupdf-fonts <https://pypi.org/project/pymupdf-fonts/>`_ is a collection of nice fonts to be used for text output methods.
  * 
    `Tesseract-OCR <https://github.com/tesseract-ocr/tesseract>`_ for optical
    character recognition in images and document pages. Tesseract is separate
    software, not a Python package. To enable OCR functions in PyMuPDF,
    Tesseract must be installed and the `tessdata` folder name specified; see
    below.

  .. note:: You can install these additional components at any time -- before or after installing PyMuPDF. PyMuPDF will detect their presence during import or when the respective functions are being used.


Build and install from a local PyMuPDF source tree
---------------------------------------------------------

Initial setup:

* Install C/C++ development tools as described above.
* Enter a Python venv and update pip, as described above.

* Get a PyMuPDF source tree:

  * Clone the PyMuPDF git repository::

        git clone https://github.com/pymupdf/PyMuPDF.git

  *
    Or download and extract a `.zip` or `.tar.gz` source release from
    https://github.com/pymupdf/PyMuPDF/releases.

Then one can build PyMuPDF in two ways:

* Build and install PyMuPDF with default MuPDF version::

      cd PyMuPDF && pip install .

  This will automatically download a specific hard-coded MuPDF source
  release, and build it into PyMuPDF.

* Or build and install PyMuPDF using a local MuPDF source tree:

  * Clone the MuPDF git repository::

      git clone --recursive https://git.ghostscript.com/mupdf.git

  *
    Build PyMuPDF, specifying the location of the local MuPDF tree with the
    environmental variables `PYMUPDF_SETUP_MUPDF_BUILD`::

      cd PyMuPDF && PYMUPDF_SETUP_MUPDF_BUILD=../mupdf pip install .

Also, one can build for different Python versions in the same PyMuPDF tree:

*
  PyMuPDF will build for the version of Python that is being used to run
  `pip`. To run `pip` with a specific Python version, use `python -m pip`
  instead of `pip`.

  So for example on Windows one can build different versions with::

    cd PyMuPDF && py -3.9 -m pip install .

  or::

    cd PyMuPDF && py -3.10-32 -m pip install .


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


Using with Pyodide
------------------

See :doc:`pyodide`.


.. _installation_ocr:

Enabling Integrated OCR Support
---------------------------------------------------------

If you do not intend to use this feature, skip this step. Otherwise, it is required for both installation paths: **from wheels and from sources.**

PyMuPDF will already contain all the logic to support OCR functions. But it additionally does need `Tesseract’s language support data <https://github.com/tesseract-ocr/tessdata>`_.

If not specified explicitly, PyMuPDF will attempt to find the installed
Tesseract's tessdata, but this should probably not be relied upon.

Otherwise PyMuPDF requires that Tesseract's language support folder is
specified explicitly either in PyMuPDF OCR functions' `tessdata` arguments or
`os.environ["TESSDATA_PREFIX"]`.

So for a working OCR functionality, make sure to complete this checklist:

1. Locate Tesseract's language support folder. Typically you will find it here:

   * Windows: `C:/Program Files/Tesseract-OCR/tessdata`
   * Unix systems: `/usr/share/tesseract-ocr/4.00/tessdata`

2. Specify the language support folder when calling PyMuPDF OCR functions:
   
   * Set the `tessdata` argument.
   * Or set `os.environ["TESSDATA_PREFIX"]` from within Python.
   * Or set environment variable `TESSDATA_PREFIX` before running Python, for example:
   
     * Windows: `setx TESSDATA_PREFIX "C:/Program Files/Tesseract-OCR/tessdata"`
     * Unix systems: `declare -x TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata`

.. include:: footer.rst
