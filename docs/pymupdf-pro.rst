
.. include:: header.rst



.. _pymupdf-pro

PyMuPDF Pro
=============


Enhance |PyMuPDF| capability with **Office** document support.

|PyMuPDF Pro| offers all the features of |PyMuPDF|, plus enhanced functionality to support **Office** documents.

- Load, parse and extract text data from **Office** files
- Able to render **Office** files


Office file support
----------------------

In addition to the `standard file types supported by PyMuPDF <Supported_File_Types>`, |PyMuPDF Pro| supports:

- DOC/DOCX
- PPT/PPTX
- XLS/XLXS
- HWP/HWPX


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

    import pymupdfpro
    doc = pymupdf.open("my-office-doc.xls")

.. note::

    All standard |PyMuPDF| functionality is exposed as expected - |PyMuPDF Pro| handles the extended **Office** file types


From then on you can work with document pages just as you would do normally, but with respect to the `restrictions <PyMuPDFPro_Restrictions>`.


.. _PyMuPDFPro_Restrictions:

Restrictions
~~~~~~~~~~~~~~~~~~~~


|PyMuPDF Pro| functionality is restricted without a license key as follows:

    **Only the first 10KB of any document will be available as extracted text.**

To unlock full functionality you should `obtain a trial key <PyMuPDFPro_TrialKeys>`.


.. _PyMuPDFPro_TrialKeys:

Trial keys
-----------------------

To obtain a license key `please fill out the form on this page <https://artifex.com/products/pymupdf-pro/trial/>`_. You will then have the trial key emailled to the address you submitted.


Using a key
~~~~~~~~~~~~~~~~


Initialize |PyMuPDF Pro| with a key as follows:

.. code-block:: python

    import pymupdfpro
    key = '...' # use key contents directly.
    key = 'foo/my_pymupdfpro_key' # use key file.
    pymupdf.init(key)

This will allow you to evaluate the product for a limited time. If you want to use |PyMuPDF Pro| after this time you should then `enquire about obtaining a commercial license <https://artifex.com/products/pymupdf-pro/>`_.


.. raw:: html

   <button id="findOutAboutPyMuPDFPro" class="cta orange" onclick="window.location='https://artifex.com/products/pymupdf-pro?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=cta-button'">Ready to license PyMuPDF Pro?</button>





.. include:: footer.rst