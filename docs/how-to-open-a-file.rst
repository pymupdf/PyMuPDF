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


File Recognizer: Opening with :index:`a Wrong File Extension <pair: wrong; file extension>`
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

If you have a document with a wrong file extension for its type, do not worry: it will still be opened correctly, thanks to the integrated file "content recognizer" in the base library.

This component looks at the actual data in the file using a number of heuristics -- independent of the file extension. This of course is also true for file names **without** an extension.

Here is a list of details about how the file content recognizer works:

* Whether opening from a file name or from memory, the recognizer in most cases will determine the correct document type. It does not need or even look at the file extension - which is not available anyway when opening from memory.

* Text files are an exception: they do not contain recognizable internal structures at all. Here, the file extension ".txt" and the ``filetype`` parameter continue to play a role and are used to create a "Text" document. Correspondingly, text files with other / no extensions, can successfully be opened using `filetype="txt"`.

* Currently, two e-book formats, FictionBook and MOBI, are not automatically recognized. They require the extensions ".fb2" and ".mobi" respectively. Use the ``filetype`` parameter accordingly to open them from memory.

* Using `filetype="txt"` will treat **any** file as containing plain text -- even when its content is a supported document type.


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


Opening Django Files
~~~~~~~~~~~~~~~~~~~~~~~~~~

Django implements a `File Storage API <https://docs.djangoproject.com/en/5.1/ref/files/storage/>`_ to store files. The default is the `FileSystemStorage <https://docs.djangoproject.com/en/5.1/ref/files/storage/#the-filesystemstorage-class>`_, but the `django-storages <https://django-storages.readthedocs.io/en/latest/index.html>`_ library provides a number of other storage backends.

You can open the file, move the contents into memory, then pass the contents to |PyMuPDF| as a stream.

.. code-block:: python

    import pymupdf
    from django.core.files.storage import default_storage

    from .models import MyModel

    obj = MyModel.objects.get(id=1)
    with default_storage.open(obj.file.name) as f:
        data = f.read()

    doc = pymupdf.Document(stream=data)

Please note that if the file you open is large, you may run out of memory.

The File Storage API works well if you're using different storage backends in different environments. If you're only using the `FileSystemStorage`, you can simply use the `obj.file.name` to open the file directly with |PyMuPDF| as shown in an earlier example.


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

As you can imagine many text based file formats can be *very simply opened* and *interpreted* by |PyMuPDF|. This can make data analysis and extraction for a wide range of previously unavailable files possible.


.. include:: footer.rst
