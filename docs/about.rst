.. include:: header.rst

.. _About:



.. _About_Features:

Features Comparison
-----------------------------------------------


.. _About_Feature_Matrix:

Feature Matrix
~~~~~~~~~~~~~~~~~~~

The following table illustrates how |PyMuPDF| compares with other typical solutions.


.. include:: about-feature-matrix.rst


----





.. note::

    .. image:: images/icons/icon-docx.svg
        :width: 40
        :height: 40
        :alt: DOCX icon

    .. image:: images/icons/icon-xlsx.svg
            :width: 40
            :height: 40
            :alt: XLSX icon

    .. image:: images/icons/icon-pptx.svg
            :width: 40
            :height: 40
            :alt: PPTX icon 

    .. image:: images/icons/icon-hangul.svg
            :width: 40
            :height: 40
            :alt: HWPX icon

    A note about **Office** document types (DOCX, XLXS, PPTX) and **Hangul** documents (HWPX). These documents can be loaded into |PyMuPDF| and you will receive a :ref:`Document <Document>` object.

    There are some caveats:

    - we convert the input to **HTML** to layout the content.
    - because of this the original page separation has gone.

    When saving out the result any faithful representation of the original layout cannot be expected.

    Therefore input files are mostly in a form that's useful for text extraction.


----

.. _About_PyMuPDF_Product_Suite:

PyMuPDF Product Suite
-----------------------------------------------

|PyMuPDF| is the standard version of the library, however there are a family of additional products each with different features and functionality. 

**Additional products** in the |PyMuPDF| product suite are:
   
- |PyMuPDF Pro| adds support for Office document formats.
- |PyMuPDF4LLM| is optimized for large language model (LLM) applications, providing enhanced text extraction and processing capabilities.
- |PyMuPDF Layout| focuses on layout analysis and semantic understanding, ideal for document conversion and formatting tasks with enhanced results.

.. note::
    All of the products above depend on the same core product - |PyMuPDF| and therefore have full access to all of its features.
    These additional products can be seen as optional extras to the enhance the core |PyMuPDF| library.


.. _About_PyMuPDF_Products_Comparison:

PyMuPDF Products Comparison
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following table illustrates what features the products offer:

.. list-table:: PyMuPDF Products Comparison
   :widths: 8 23 23 23 23
   :header-rows: 1

   * - 
     - PyMuPDF
     - PyMuPDF Pro
     - PyMuPDF4LLM
     - PyMuPDF Layout
   * - **Input Documents**
     - `PDF`, `XPS`, `EPUB`, `CBZ`, `MOBI`, `FB2`, `SVG`, `TXT`, Images (*standard document types*)
     - *as PyMuPDF* and:
       `DOC`/`DOCX`, `XLS`/`XLSX`, `PPT`/`PPTX`, `HWP`/`HWPX`
     - *as PyMuPDF*
     - *as PyMuPDF*
   * - **Output Documents**
     - Can convert any input document to `PDF`, `SVG` or Image
     - *as PyMuPDF*
     - *as PyMuPDF* and:
       Markdown (`MD`)
     - *as PyMuPDF4LLM* and:
       `JSON` or `TXT`
   * - **Page Analysis**
     - Basic page analysis to return document structure
     - *as PyMuPDF*
     - *as PyMuPDF*
     - Advanced Page Analysis with trained data for enhanced results
   * - **Data extraction**
     - Basic data extraction with structured layout information and bounding box data
     - *as PyMuPDF*
     - Advanced data extraction with structure tags such as headings, lists, tables
     - Advanced layout analysis and semantic understanding
   * - **Table extraction**
     - Basic table extraction as part of text extraction
     - *as PyMuPDF*
     - Advanced table extraction with cell structure and data types
     - Superior table detection
   * - **Image extraction**
     - Basic image extraction
     - *as PyMuPDF*
     - Advanced detection and rendering of image areas on page saving them to disk or embedding in MD output
     - Superior detection of "picture" areas
   * - **Vector extraction**
     - Vector extraction and clustering
     - *as PyMuPDF*
     - *as PyMuPDF*
     - Superior detection of "picture" areas
   * - **Popular RAG Integrations** 
     - Langchane, LlamaIndex
     - *as PyMuPDF*
     - *as PyMuPDF* and with some addiotnal help methods for RAG workflows
     - *as PyMuPDF4LLM*
   * - **OCR**
     - On-demand invocation of built-in Tesseract for text detection on pages or images.
     - *as PyMuPDF*
     - *as PyMuPDF*
     - Automatic OCR based on page content analysis.



----

.. _About_Performance:

Performance
-----------------------------------------------



To benchmark |PyMuPDF| performance against a range of tasks a test suite with a fixed set of :ref:`8 PDFs with a total of 7,031 pages<Appendix4_Files_Used>` containing text & images is used to obtain performance timings.


Here are current results, grouped by task:



.. include:: about-performance.rst


.. note::

   For more detail regarding the methodology for these performance timings see: :ref:`Performance Comparison Methodology<Appendix4>`.




.. _About_License:

License and Copyright
----------------------



|PyMuPDF| and |MuPDF| are now available under both, open-source |AGPL| and commercial license agreements. Please read the full text of the |AGPL| license agreement, available in the distribution material (file COPYING) and `on the GNU license page <https://www.gnu.org/licenses/agpl-3.0.html>`_, to ensure that your use case complies with the guidelines of the license. If you determine you cannot meet the requirements of the |AGPL|, please contact `Artifex <https://artifex.com/contact/pymupdf-inquiry.php?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=inline-link>`_ for more information regarding a commercial license.

.. raw:: html

   <button id="licenseButton" class="cta orange" onclick="window.location='https://artifex.com/licensing?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=cta-button'">Find out more about Licensing</button>
   <p></p>

   <script>
      let langC = document.getElementsByTagName('html')[0].getAttribute('lang');

      if (langC=="ja") {
         document.getElementById("licenseButton").innerHTML = "さらに詳しく";
      }

   </script>



:title:`Artifex` is the exclusive commercial licensing agent for :title:`MuPDF`.

:title:`Artifex`, the :title:`Artifex` logo, :title:`MuPDF`, and the :title:`MuPDF` logo are registered trademarks of :title:`Artifex Software Inc.`


.. include:: version.rst


.. include:: footer.rst
