
.. include:: header.rst



.. _pymupdf-pro

PyMuPDF Pro
=============


Enhance |PyMuPDF| capability with **Office** document support.

|PyMuPDF Pro| offers all the features of |PyMuPDF|, plus enhanced functionality to support **Office** documents.

- Load, parse and extract text data from **Office** files
- Ablility to render **Office** files


Office file support
----------------------

In addition to the `standard file types supported by PyMuPDF <Supported_File_Types>`, |PyMuPDF Pro| supports:

.. list-table::
   :header-rows: 1

   * - **DOC/DOCX**
     - **XLS/XLSX**
     - **PPT/PPTX**
     - **HWP/HWPX**
   * - .. image:: images/icons/icon-docx.svg
          :width: 40
          :height: 40
     - .. image:: images/icons/icon-xlsx.svg
          :width: 40
          :height: 40
     - .. image:: images/icons/icon-pptx.svg
          :width: 40
          :height: 40
     - .. image:: images/icons/icon-hangul.svg
          :width: 40
          :height: 40



Usage
--------------

Installation
~~~~~~~~~~~~~~~~~~

Install via pip with:

.. code-block:: bash

    pip install pymupdfpro


Loading an **Office** document
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Import |PyMuPDF Pro| and you can then reference **Office** documents directly, e.g.:

.. code-block:: python

    import pymupdf.pro
    pymupdf.pro.unlock()
    # PyMuPDF has now been extended with PyMuPDF Pro features, with some restrictions.
    doc = pymupdf.open("my-office-doc.xls")

.. note::

    All standard |PyMuPDF| functionality is exposed as expected - |PyMuPDF Pro| handles the extended **Office** file types


From then on you can work with document pages just as you would do normally, but with respect to the `restrictions <PyMuPDFPro_Restrictions>`.


.. _PyMuPDFPro_Restrictions:

Restrictions
~~~~~~~~~~~~~~~~~~~~


|PyMuPDF Pro| functionality is restricted without a license key as follows:

    **Only the first 3 pages of any document will be available.**

To unlock full functionality you should `obtain a trial key <https://pymupdf.io/try-pro/>`_.


.. _PyMuPDFPro_TrialKeys:

Trial keys
-----------------------

To obtain a license key `please fill out the form on this page <https://pymupdf.io/try-pro/>`_. You will then have the trial key emailled to the address you submitted.


Using a key
~~~~~~~~~~~~~~~~


Initialize |PyMuPDF Pro| with a key as follows:

.. code-block:: python

    import pymupdf.pro
    pymupdf.pro.unlock(my_key)
    # PyMuPDF has now been extended with PyMuPDF Pro features.

This will allow you to evaluate the product for a limited time. If you want to use |PyMuPDF Pro| after this time you should then `enquire about obtaining a commercial license <https://artifex.com/products/pymupdf-pro/>`_.




.. raw:: html

   <button id="findOutAboutPyMuPDFPro" class="cta orange" onclick="window.location='https://pymupdf.io/try-pro/?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=cta-button'">Ready to try PyMuPDF Pro?</button>





.. include:: footer.rst