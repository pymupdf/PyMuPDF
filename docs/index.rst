.. include:: header.rst

.. raw:: html

   <style>
      /* This is the TOC in the sidebar */
      .toc-drawer {
        display: none;
      }

      .main .content {
        width:  100% !important;
      }

      .cross-marketing-panel {
        margin: 20px auto;
        width: auto;
        background-image:linear-gradient(160deg, #DC2626, #FF4545, #FF8A3D);
        color: #fff;
        border-radius: 5px;
        padding: 20px;
        font-size: 18px;
        font-weight: bold;
      }

      .cross-marketing-panel a {
        color: #fff;
        text-decoration: underline;
      }

   </style>

Welcome to |PyMuPDF|
================================

|PyMuPDF| is a layout-aware document engine for AI and a feature-rich **Python** toolkit for extracting, rendering and editing PDFs and other documents. Since version 2.0, its ML-based layout analysis turns PDFs and Office files into high-quality |Markdown| for RAG and agents, running fast on CPU and grounding every result to its source page.

|PyMuPDF| is hosted on `GitHub <https://github.com/pymupdf/PyMuPDF>`_ and registered on `PyPI <https://pypi.org/project/PyMuPDF/>`_.


.. raw:: html

    <div class="cross-marketing-panel">
      <p>Want to extract text from every scanned PDF added to a Google Drive folder?</p>
      <p><a href="https://pdf.co/tutorials/how-to-extract-text-from-scanned-pdf-using-integromat?utm_source=pymupdf_docs&utm_medium=referral&utm_campaign=rtd_drive_ocr_pilot" target="_blank">See the Make workflow with PDF.co for an automated solution</a>.</p>
    </div>

.. if we want a Github repo badge

   .. raw:: html

      <a href="https://trendshift.io/repositories/11536" target="_blank"><img src="https://trendshift.io/api/badge/repositories/11536" alt="pymupdf%2FPyMuPDF | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>


----

This documentation covers all versions up to |version|.

----

.. toctree::
   :caption: About
   :maxdepth: 1

   about.rst
   pymupdf-office/index.rst
   rag.rst
   grounding.rst

.. toctree::
   :caption: User Guide
   :maxdepth: 1

   installation.rst
   the-basics.rst
   tutorial.rst
   ocr/index.rst
   chunking/index.rst
   resources.rst
   faq/index.rst



.. toctree::
   :caption: How to Guide
   :maxdepth: 3

   recipes.rst


.. toctree::
   :caption: API Reference
   :maxdepth: 2

   classes.rst
   json-schema.rst
   algebra.rst
   lowlevel.rst
   glossary.rst
   vars.rst
   colors.rst


.. toctree::
   :caption: Other
   :maxdepth: 2

   app1.rst
   app2.rst
   app3.rst
   app4.rst
   changes.rst
   znames.rst

|

----



.. include:: footer.rst



