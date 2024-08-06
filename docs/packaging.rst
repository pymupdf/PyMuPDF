.. include:: header.rst


Packaging for Linux distributions
=================================


Requirements
------------

* Python
* MuPDF checkout (including submodules).
* PyMuPDF checkout.
* System packages listed in `scripts/sysinstall.py:g_sys_packages`.
* Python packages listed in `pyproject.toml`.

Extra requirements for running tests:

* Python packages listed in `scripts/gh_release.py:test_packages`.


General steps
-------------

* Build and install MuPDF:
  
  * Install required system packages.
  * Run `make install-shared-python` on MuPDF's `Makefile` with at least
    these make variables:
  
    * `DESTDIR` set to the install directory, e.g. `/`.
    *
      `prefix` set to location relative to DESTDIR, such as `/usr/local` or
      `/usr`. Must start with `/`.
    * `USE_SYSTEM_LIBS=yes`.
    * `HAVE_LEPTONICA=yes`.
    * `HAVE_TESSERACT=yes`.

* Build and install PyMuPDF:

  *
    Run `pip install ./PyMuPDF` or `pip wheel ./PyMuPDF` with at least these
    environment variables:
    
    *
      `PYMUPDF_SETUP_MUPDF_BUILD=` (empty string) to prevent download and build
      of hard-coded MuPDF release.
    *
      `CFLAGS`, `CXXFLAGS` and `LDFLAGS` set to allow visibility of the
      installed MuPDF headers and shared libraries.

* Run PyMuPDF tests:

  * Ensure required Python packages are available.
  *
    Run `pytest -k "not test_color_count and not test_3050" PyMuPDF`
    
    * Test `test_color_count` is known fail if MuPDF is not built with PyMuPDF's custom config.h.
    * Test `test_3050` is known to fail if MuPDF is built without its own third-party libraries.


Use of scripts/sysinstall.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`scripts/sysinstall.py` provides a useful example of build, install and test
commands that are known to to work, because it is run regularly by Github
action `.github/workflows/test_sysinstall.yml`.

* Run with `-h` or look at the doc-string to see detailed usage information.
* It uses Debian-style `apt` commands to install system packages.
* By default it assumes local git checkouts `mupdf/` and `PyMuPDF/`.

To run a full build, install and test for both a local fake root and the system
root:

.. code-block:: shell

    ./PyMuPDF/scripts/sysinstall.py
    ./PyMuPDF/scripts/sysinstall.py --root /

To see what commands would be run without actually running them:

.. code-block:: shell

    ./PyMuPDF/scripts/sysinstall.py -m 0 -p 0 -t 0


See also
--------

*
  `setup.py`'s initial doc-comment has detailed information about the
  environment variables used when building PyMuPDF.
