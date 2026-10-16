.. include:: header.rst


Packaging for Linux distributions
=================================


Changes in v2.0
---------------

The default package/wheel name has changed from `pymupdf` to `pymupdf_lite`.

* This will not effect direct installation with (for example) `pip install ./PyMuPDF`.
* But it will change any generated wheel's filename.


Requirements
------------

* Python
* MuPDF checkout (including submodules).
* PyMuPDF checkout.
* System packages installed by `scripts/sysinstall.py`.
* Python packages `libclang` and `swig`.

Extra requirements for running tests:

* Python packages listed in `tests/conftest.py:install_required_packages()`.


General steps
-------------

* Build and install MuPDF:
  
  * Install required system packages.
  * Run `make` in MuPDF checkout.
  * Run `make install-shared-python` in MuPDF's checkout.
    See `scripts/sysinstall.py` for example extra make flags.

* Build and install PyMuPDF:

  * Run `pip install ./PyMuPDF` or `pip wheel ./PyMuPDF` with at least these
    environment variables:
    
    * `PYMUPDF_SETUP_MUPDF_BUILD=` (empty string) to prevent download and build
      of hard-coded MuPDF release.
    * `CFLAGS`, `CXXFLAGS` and `LDFLAGS` set to allow visibility of the
      installed MuPDF headers and shared libraries.
    * Note that `pip wheel ./PyMuPDF` will generate a wheel called `pymupdf_lite`.

* Run PyMuPDF tests:

  * Ensure required Python packages are available;
    see PyMuPDF's `tests/conftest.py:install_required_packages()`.
  
  * Set `PYMUPDF_SYSINSTALL_ROOT=-` in environment.
    
    * This will prevent `tests/conftest.py:install_required_packages()` from
      attempting to use pip to install required packages.


Use of scripts/sysinstall.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`scripts/sysinstall.py` provides an example of build, install and test commands
that are known to to work, because it is run regularly by Github action
`.github/workflows/test_sysinstall.yml`.

* Run with `-h` or look at the doc-string to see usage information.


Building with integrated layout and 4llm support (experimental)
---------------------------------------------------------------

In theory one should be able to do a system build/install with integrated
layout and 4llm support, but this has not been tested.

The general idea is to clone the pymupdf_layout and pymupdf4llm repositories,
and set `PYMUPDF_SETUP_PATH_LAYOUT` and `PYMUPDF_SETUP_PATH_4LLM` to point to
the local checkouts before building PyMuPDF.

For example::

    git clone https://github.com/ArtifexSoftware/pymupdf_layout
    git clone https://github.com/Pymupdf/pymupdf4llm
    export PYMUPDF_SETUP_PATH_LAYOUT=pymupdf_layout
    export PYMUPDF_SETUP_PATH_4LLM=pymupdf4llm

[Setting only one of `PYMUPDF_SETUP_PATH_LAYOUT` and `PYMUPDF_SETUP_PATH_4LLM`
is not supported.]

When `PYMUPDF_SETUP_PATH_LAYOUT` and `PYMUPDF_SETUP_PATH_4LLM` are set like
this:

* Extra Python packages will be required at runtime;
  see PyMuPDF's `setup.py:g_requires_dist` for details.
* The Python package/wheel name will be `pymupdf`.


See also
--------

*
  `setup.py`'s initial doc-comment has detailed information about the
  environment variables used when building PyMuPDF.
