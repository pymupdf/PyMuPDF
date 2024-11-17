.. include:: header.rst

Pyodide
=======


Overview
--------

*
  `Pyodide <https://pyodide.org>`_ is a client-side Python implementation that
  runs in a web browser.

* The Pyodide build of PyMuPDF is currently experimental.


Building a PyMuPDF wheel for Pyodide
------------------------------------

A PyMuPDF wheel for Pyodide can be built by running `scripts/gh_release.py`
with some environmental variable settings. This is regularly tested on Github
by `.github/workflows/test_pyodide.yml`.

Here is an example of this, a single Linux command (to be run with the current
directory set to a PyMuPDF checkout), that builds a Pyodide wheel::

    inputs_sdist=0 \
    inputs_PYMUPDF_SETUP_MUPDF_BUILD="git:--recursive --depth 1 --shallow-submodules --branch master https://github.com/ArtifexSoftware/mupdf.git" \
    inputs_wheels_default=0 \
    inputs_wheels_linux_pyodide=1 \
    ./scripts/gh_release.py build

This does the following (all inside Python venv's):

* Download (git clone and pip install) and customise a Pyodide build environment.
* Download (git clone) the latest MuPDF.
* Build MuPDF and PyMuPDF in the Pyodide build environment.
* Create a wheel in `dist/`.

For more information, see the comments for functions `build_pyodide_wheel()`
and `pyodide_setup()` in `scripts/gh_release.py`.


Using a Pyodide wheel
---------------------

*
  Upload the wheel (for example
  `PyMuPDF/dist/PyMuPDF-1.24.2-cp311-cp311-emscripten_3_1_32_wasm32.whl`) to a
  webserver which has been configured to allow Cross-origin resource sharing
  (https://en.wikipedia.org/wiki/Cross-origin_resource_sharing).

*
  The wheel can be used in a Pyodide console running in a web browser, or a
  JupyterLite notebook running in a web browser.

  * To create a Pyodide console, go to:

    https://pyodide.org/en/stable/console.html

  * To create a JupyterLite notebook, go to:

    https://jupyterlite.readthedocs.io/en/latest/_static/lab/index.html

*
  In both these cases, one can use the following code to download the wheel
  (replace `url` with the URL of the uploaded wheel) and import it::

      import pyodide_js
      await pyodide_js.loadPackage(url)
      import pymupdf

  *
    Note that `micropip.install()` does not work, because of PyMuPDF's use of
    shared libraries.


Loading a PDF document from a URL into PyMuPDF
----------------------------------------------

*
  Pyodide browser console does not have generic network access, so for
  example `urllib.request.urlopen(url)` fails. But Pyodide has a built-in
  `pyodide.http` module that uses javascript internally, which one can use
  to download into a `bytes` instance, which can be used to create a PyMuPDF
  `Document` instance::

      import pyodide.http
      r = await pyodide.http.pyfetch('https://...')
      data = await r.bytes()
      doc = pymupdf.Document(stream=data)

* It looks like this only works with `https://`, not `http://`.


.. include:: footer.rst
