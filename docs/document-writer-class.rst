.. include:: header.rst

.. _DocumentWriter:

================
DocumentWriter
================

|pdf_only_class|


* New in v1.21.0

This class represents a utility which can output various :ref:`document types supported by PyMuPDF<Supported_File_Types>`.

In |PyMuPDF| only used for outputting PDF documents whose pages are populated by :ref:`Story` DOMs.

Using DocumentWriter_ also for other document types might happen in the future.

================================= ===================================================
**Method / Attribute**            **Short Description**
================================= ===================================================
:meth:`DocumentWriter.begin_page` start a new output page
:meth:`DocumentWriter.end_page`   finish the current output page
:meth:`DocumentWriter.close`      flush pending output and close the file
================================= ===================================================

**Class API**

.. class:: DocumentWriter

   .. method:: __init__(self, path, options=None)

      Create a document writer object, passing a Python file pointer or a file path. Options to use when saving the file may also be passed.

      This class can also be used as a Python context manager.

      :arg path: the output file. This may be a string file name, or any Python file pointer.
      
         .. note:: By using a `io.BytesIO()` object as file pointer, a document writer can create a PDF in memory. Subsequently, this PDF can be re-opened for input and be further manipulated. This technique is used by several example scripts in :ref:`Stories recipes<RecipesStories>`.

      :arg str options: specify saving options for the output PDF. Typical are "compress" or "clean". More possible values may be taken from help output of the `mutool convert` CLI utility.

   .. method:: begin_page(mediabox)

      Start a new output page of a given dimension.

      :arg rect_like mediabox: a rectangle specifying the page size. After this method, output operations may write content to the page.

   .. method:: end_page()

      Finish a page. This flushes any pending data and appends the page to the output document.

   .. method:: close()

      Close the output file. This method is required for writing any pending data.

   For usage examples consult the section of :ref:`Story`.

.. include:: footer.rst
