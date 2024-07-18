.. include:: header.rst

.. _HowToOpenAFile:

==============================
Opening Files
==============================




.. _Supported_File_Types:

Supported File Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|PyMuPDF| can open files other than just |PDF|.

The following file types are supported:

.. include:: supported-files-table.rst



How to Open a File
~~~~~~~~~~~~~~~~~~~~~

To open a file, do the following:

.. code-block:: python

    doc = pymupdf.open("a.pdf")


.. note:: The above creates a :ref:`Document`. The instruction `doc = pymupdf.Document("a.pdf")` does exactly the same. So, `open` is just a convenient alias  and you can find its full API documented in that chapter. 


Opening with :index:`a Wrong File Extension <pair: wrong; file extension>`
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

If you have a document with a wrong file extension for its type, you can still correctly open it.

Assume that *"some.file"* is actually an **XPS**. Open it like so:

.. code-block:: python

    doc = pymupdf.open("some.file", filetype="xps")



.. note::

    |PyMuPDF| itself does not try to determine the file type from the file contents. **You** are responsible for supplying the file type information in some way -- either implicitly, via the file extension, or explicitly as shown with the `filetype` parameter. There are pure :title:`Python` packages like `filetype <https://pypi.org/project/filetype/>`_ that help you doing this. Also consult the :ref:`Document` chapter for a full description.

    If |PyMuPDF| encounters a file with an unknown / missing extension, it will try to open it as a |PDF|. So in these cases there is no need for additional precautions. Similarly, for memory documents, you can just specify `doc=pymupdf.open(stream=mem_area)` to open it as a |PDF| document.

    If you attempt to open an unsupported file then |PyMuPDF| will throw a file data error.




----------


Opening Remote Files
~~~~~~~~~~~~~~~~~~~~~~~~~~


For remote files on a server (i.e. non-local files), you will need to *stream* the file data to |PyMuPDF|.

For example use the `requests <https://requests.readthedocs.io/en/latest/>`_ library as follows:

.. code-block:: python

    import pymupdf
    import requests

    r = requests.get('https://mupdf.com/docs/mupdf_explored.pdf')
    data = r.content
    doc = pymupdf.Document(stream=data)


Opening Files from Cloud Services
""""""""""""""""""""""""""""""""""""""

For further examples which deal with files held on typical cloud services please see these `Cloud Interactions code snippets <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/cloud-interactions>`_.



----------



Opening Files as Text
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


|PyMuPDF| has the capability to open any plain text file as a document. In order to do this you should provide the `filetype` parameter for the `pymupdf.open` function as `"txt"`.

.. code-block:: python

    doc = pymupdf.open("my_program.py", filetype="txt")


In this way you are able to open a variety of file types and perform the typical **non-PDF** specific features like text searching, text extracting and page rendering. Obviously, once you have rendered your `txt` content, then saving as |PDF| or merging with other |PDF| files is no problem.


Examples
""""""""""""""""""


Opening a `C#` file
...........................


.. code-block:: python

    doc = pymupdf.open("MyClass.cs", filetype="txt")


Opening an ``XML`` file
...........................

.. code-block:: python

    doc = pymupdf.open("my_data.xml", filetype="txt")


Opening a `JSON` file
...........................

.. code-block:: python

    doc = pymupdf.open("more_of_my_data.json", filetype="txt")


And so on!

As you can imagine many text based file formats can be *very simply opened* and *interpreted* by |PyMuPDF|. This can make data analysis and extraction for a wide range of previously unavailable files suddenly possible.









.. include:: footer.rst
