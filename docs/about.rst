.. include:: header.rst




.. _About:


.. image:: images/pymupdf-logo.png
   :align: left
   :scale: 10%



:title:`PyMuPDF` is an enhanced :title:`Python` binding for `MuPDF <https://www.mupdf.com/>`_ --  a lightweight :title:`PDF`, :title:`XPS`, and :title:`E-book` viewer, renderer, and toolkit, which is maintained and developed by :title:`Artifex Software, Inc`.

:title:`PyMuPDF` is hosted on `GitHub <https://github.com/pymupdf/PyMuPDF>`_ and registered on `PyPI <https://pypi.org/project/PyMuPDF/>`_.

|

.. _features:

Features Comparison
-----------------------------------------------


.. include:: feature-matrix.rst


.. _performance:

Performance
-----------------------------------------------

To benchmark :title:`PyMuPDF` performance against a range of tasks a test suite with a fixed set of 15 :title:`PDFs` with a total of 3800 pages containing text & images is used to obtain performance timings.


Here are current results, grouped by task:

**Copying**
   This refers to opening a document and then saving it to a new file. This test measures the speed of reading a :title:`PDF` and re-writing as a new :title:`PDF`. This process is also at the core of functions like merging / joining multiple documents. The numbers below therefore apply to :title:`PDF` joining and merging. The results for all 3,800 pages are:


   .. list-table::
      :header-rows: 1

      * - :title:`PyMuPDF`
        - :title:`PDFrw`
        - :title:`PikePDF`
        - :title:`PDFtk`
        - :title:`PyPDF2`
      * - 4.2 seconds
        - 18.06 seconds
        - 59.34 seconds
        - 138.6 seconds
        - 496.86 seconds

**Text Extraction**
   This refers to extracting simple, plain text from every page of the document and storing it in a text file. The results for all 3,800 pages are:

   .. list-table::
      :header-rows: 1

      * - :title:`PyMuPDF`
        - :title:`XPDF`
        - :title:`PyPDF2`
        - :title:`PDFMiner`
      * - 9.1 seconds
        - 19.11 seconds
        - 127.4 seconds
        - 318.5 seconds


**Rendering**
   This refers to making an image (like PNG) from every page of a document at a given DPI resolution. This feature is the basis for displaying a document in a GUI window.

   .. list-table::
      :header-rows: 1

      * - :title:`PyMuPDF`
        - :title:`XPDF`
        - :title:`PyPDF2`
      * - 1 (baseline)
        - 1.7 times slower
        - More then **100** times (!!!) slower :sup:`✼`.


:sup:`✼` There is no real rendering support for :title:`PyPDF2`, but there are application solutions (e.g. in :title:`wxPython`) based on low-level “home-made” interpretation of the page ``/Contents``, which have been used here.

.. _license:

License and Copyright
----------------------

:title:`PyMuPDF` and :title:`MuPDF` are now available under both, open-source :title:`AGPL` and commercial license agreements. Please read the full text of the :title:`AGPL` license agreement, available in the distribution material (file COPYING) and `here <https://www.gnu.org/licenses/agpl-3.0.html>`_, to ensure that your use case complies with the guidelines of the license. If you determine you cannot meet the requirements of the :title:`AGPL`, please contact `Artifex <https://artifex.com/contact/>`_ for more information regarding a commercial license.

:title:`Artifex` is the exclusive commercial licensing agent for :title:`MuPDF`.

:title:`Artifex`, the :title:`Artifex` logo, :title:`MuPDF`, and the :title:`MuPDF` logo are registered trademarks of :title:`Artifex Software Inc.`




.. include:: footer.rst
