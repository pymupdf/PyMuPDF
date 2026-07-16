
.. include:: ../header.rst

.. _pymupdf-pro:

.. raw:: html

    <script>
        document.getElementById("headerSearchWidget").action = '../search.html';
    </script>

PyMuPDF Pro
=============


|PyMuPDF Pro| is a set of *commercial extensions* for |PyMuPDF|.

Enhance |PyMuPDF| capability with **Office** document support & **RAG/LLM** integrations.

- Enables Office document handling, including ``doc``, ``docx``, ``hwp``, ``hwpx``, ``ppt``, ``pptx``, ``xls``, ``xlsx``, and others.
- Supports text and table extraction, document conversion and more.
- Includes the commercial version of |PyMuPDF4LLM|.

To enquire about obtaining a commercial license, then `use this contact page <https://artifex.com/contact/?utm_source=rtd-pymupdf&utm_medium=referral&utm_content=page-link&utm_campaign=docs>`_.

Trial license keys are available for evaluation purposes. Please `fill out the form on this page <https://pymupdf.pro/try-pro/?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=cta-button-pymupdf-pro-page&utm_campaign=docs>`_ to obtain a trial key.

.. note::

    A licensed version of |PyMuPDF Pro| also gives you a licensed version of |PyMuPDF4LLM|. If you are interested in using the |PyMuPDF4LLM| package you should install it separately.


Platform support
--------------------

Available for these platforms only:

- Windows x86_64.
- Linux x86_64 (glibc).
- MacOS x86_64.
- MacOS arm64.


Office file support
----------------------

In addition to the `standard file types supported by PyMuPDF <Supported_File_Types>`, |PyMuPDF Pro| supports:

.. list-table::
   :header-rows: 1

   * - **DOC/DOCX**
     - **XLS/XLSX**
     - **PPT/PPTX**
     - **HWP/HWPX**
   * - .. image:: ../images/icons/icon-docx.svg
          :width: 40
          :height: 40
     - .. image:: ../images/icons/icon-xlsx.svg
          :width: 40
          :height: 40
     - .. image:: ../images/icons/icon-pptx.svg
          :width: 40
          :height: 40
     - .. image:: ../images/icons/icon-hangul.svg
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

    To unlock full functionality you should `obtain a trial key <https://pymupdf.pro/try-pro/?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=cta-button-pymupdf-pro-page&utm_campaign=docs>`_.


.. _PyMuPDFPro_TrialKeys:

Trial keys
-----------------------

To obtain a license key `please fill out the form on this page <https://pymupdf.pro/try-pro/?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=cta-button-pymupdf-pro-page&utm_campaign=docs>`_. You will then have the trial key emailled to the address you submitted.


Using a key
~~~~~~~~~~~~~~~~


Initialize |PyMuPDF Pro| with a key as follows:

.. code-block:: python

    import pymupdf.pro
    pymupdf.pro.unlock(my_key)
    # PyMuPDF has now been extended with PyMuPDF Pro features.

This will allow you to evaluate the product for a limited time. If you want to use |PyMuPDF Pro| after this time you should then `enquire about obtaining a commercial license <https://artifex.com/contact/?utm_source=rtd-pymupdf&utm_medium=referral&utm_content=page-link&utm_campaign=docs>`_.




Converting
-------------

**Office** document to |PDF|
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the :meth:`office_to_pdf()` method to convert an **Office** document to |PDF|, e.g.:

.. code-block:: python

    import pymupdf.pro
    pymupdf.pro.unlock()

    pymupdf.pro.office_to_pdf("input.docx", "output.pdf")
    

If you require a byte representation of the PDF data, you can use the :meth:`office_to_pdf()` without specifying an output file, e.g.:

.. code-block:: python

    import pymupdf.pro
    pymupdf.pro.unlock()

    pdfdata = pymupdf.pro.office_to_pdf("input.docx")


**Office** document to Images
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to convert an **Office** document to images, you should iterate the document pages, convert to :doc:`../pixmap` and save, e.g.:

.. code-block:: python

    doc = pymupdf.open("input.docx")

    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=200)
        pix.save(f"page-{i+1}.png")

    doc.close()

**Office** document to |Markdown|
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the :meth:`office_to_markdown()` method to convert an **Office** document to |Markdown|, e.g.:

.. code-block:: python

    import pymupdf.pro
    pymupdf.pro.unlock()

    pymupdf.pro.office_to_markdown("input.docx", "output.md")

If you require a string representation of the Markdown data, you can use the :meth:`office_to_markdown()` without specifying an output file.

**Office** document to |JSON|
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the :meth:`office_to_json()` method to convert an **Office** document to |JSON|, e.g.:

.. code-block:: python

    import pymupdf.pro
    pymupdf.pro.unlock()

    pymupdf.pro.office_to_json("input.docx", "output.json")

If you require a string representation of the JSON data, you can use the :meth:`office_to_json()` without specifying an output file.


Fonts
-----------------------

By default `pymupdf.pro.unlock()` searches for all installed font directories.

This can be controlled with keyword-only args:

* `fontpath`: specific font directories, either as a list/tuple or `os.sep`-separated string.
  If None (the default), we use `os.environ['PYMUPDFPRO_FONT_PATH']` if set.
* `fontpath_auto`: Whether to append system font directories.
  If None (the default) we use true if `os.environ['PYMUPDFPRO_FONT_PATH_AUTO']` is '1'.
  If true we append all system font directories.

Function `pymupdf.pro.get_fontpath()` returns a tuple of all font directories used by `unlock()`.


API
-----------------------


.. method:: office_to_pdf(input_path: str, output_path:str = None) -> bytes | None

    Reads the input file and converts its contents into |PDF| format.

    :arg str input_path: the input file path.

    :arg str output_path: the path to the output file. If `None`, the method returns the bytes of the PDF content.
    
    :returns: Either bytes of the PDF content, `None` if `output_path` is specified.


.. method:: office_to_markdown(input_path: str, output_path:str = None) -> str | None

    Reads the input file and outputs the text of its pages in |Markdown| format.

    :arg str input_path: the input file path.

    :arg str output_path: the path to the output file. If `None`, the method returns the content as a string.

    :returns: Either a string of the Markdown representation, `None` if `output_path` is specified.


.. method:: office_to_json(input_path: str, output_path:str = None) -> str | None

    Reads the input file and outputs the text of its pages in |JSON| format.

    :arg str input_path: the input file path.

    :arg str output_path: the path to the output file. If `None`, the method returns the content as a string.

    :returns: Either a string of the JSON representation, `None` if `output_path` is specified.




.. raw:: html

   <button id="findOutAboutPyMuPDFPro" class="cta orange" onclick="window.location='https://pymupdf.pro/try-pro/?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=cta-button-pymupdf-pro-page&utm_campaign=docs'">Ready to try PyMuPDF Pro?</button>



.. include:: ../footer.rst
