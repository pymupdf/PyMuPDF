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

.. image:: images/icons/icon-docx.svg
          :width: 40
          :height: 40

.. image:: images/icons/icon-xlsx.svg
          :width: 40
          :height: 40

.. image:: images/icons/icon-pptx.svg
          :width: 40
          :height: 40


.. image:: images/icons/icon-hangul.svg
          :width: 40
          :height: 40



.. note::

   A note about **Office** document types (DOCX, XLXS, PPTX) and **Hangul** documents (HWPX). These documents can be loaded into |PyMuPDF| and you will receive a :ref:`Document <Document>` object.

   There are some caveats:


      - we convert the input to **HTML** to layout the content.
      - because of this the original page separation has gone.

   When saving out the result any faithful representation of the original layout cannot be expected.

   Therefore input files are mostly in a form that's useful for text extraction.


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



|PyMuPDF| and :title:`MuPDF` are now available under both, open-source :title:`AGPL` and commercial license agreements. Please read the full text of the :title:`AGPL` license agreement, available in the distribution material (file COPYING) and `here <https://www.gnu.org/licenses/agpl-3.0.html>`_, to ensure that your use case complies with the guidelines of the license. If you determine you cannot meet the requirements of the :title:`AGPL`, please contact `Artifex <https://artifex.com/contact/pymupdf-inquiry.php?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=inline-link>`_ for more information regarding a commercial license.

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
