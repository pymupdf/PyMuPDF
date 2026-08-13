.. include:: header.rst

.. _CompressingFiles:

==============================
Compressing Files
==============================


PyMuPDF & Compression
-------------------------

There are various ways to reduce the size of a PDF file and a variety of options for doing so with the :meth:`Document.save()` method parameters.

By using the `mupdf_explored <https://mupdf.readthedocs.io/en/1.28.2/cookbook/mupdf-explored.html>`_ PDF as a control file let's look at the effect of various save-time parameters on the file size of a PDF document.

The original file is 1.8 MB in size. Let's see what happens when we save it with various optional parameters defined.


`use_objstms`
~~~~~~~~~~~~~~~~~~~~~~~~~

This boolean option packs object definitions into compressible streams. 

**Example**

.. code-block:: python

    import pymupdf

    doc = pymupdf.open("mupdf_explored.pdf")

    doc.save(
        "output.pdf",
        use_objstms=True,  # pack object definitions into compressible streams
    )
    doc.close()


The result is a file size of 1.5 MB. However, we can achieve a better result by using the `deflate` parameter to compress the uncompressed streams.



`deflate`
~~~~~~~~~~~~~~~~~~~~

By setting this option we can compress uncompressed streams.

Available options are:

.. list-table::
   :header-rows: 1

   * - **Value**
     - **Meaning**
   * - `0`
     - No compression (this is the default)
   * - `1`
     - Use standard `Flate compression <https://en.wikipedia.org/wiki/Deflate>`_ 
   * - `2`
     - Use `Brotli compression <https://en.wikipedia.org/wiki/Brotli>`_ (slowest, smallest output, but experimental and unsupported in many tools and viewers) [1]_ 


Used in combination with `use_objstms` to pack object definitions into compressible streams we can achieve even better results.

Flate
"""""""""""""""

**Flate Example**

.. code-block:: python

    import pymupdf

    doc = pymupdf.open("mupdf_explored.pdf")

    doc.save(
        "output.pdf",
        use_objstms=True,    # pack object definitions into compressible streams
        deflate=1,           # compress uncompressed streams with Flate compression
    )
    doc.close()

The result is a file size of 903 KB.


.. note::

    :meth:`Document.ez_save()` automatically applies these parameters for you, so the same result can be achieved with:

    .. code-block:: python

        doc.ez_save("output.pdf")

Brotli
"""""""""""""""

**Brotli Example**

.. warning::

    Brotli is experimental and unsupported in many tools and viewers. [1]_ 


.. code-block:: python

    import pymupdf

    doc = pymupdf.open("mupdf_explored.pdf")

    doc.save(
        "output.pdf",
        use_objstms=True,    # pack object definitions into compressible streams
        deflate=2,           # compress uncompressed streams with Brotli compression
    )
    doc.close()

The result is a file size of 863 KB.

Brotli is expected to **yield meaningful differences** on text- and vector-heavy documents, and close to
**none** on scanned or photo-heavy ones.

`compression_effort`
'''''''''''''''''''''

When using Brotli (`deflate=2`) by setting a further parameter `compression_effort` we can control how hard MuPDF works when compressing stream data. It trades CPU time for file size and *never changes what the document looks like*.

.. code-block:: python

    import pymupdf

    doc = pymupdf.open("mupdf_explored.pdf")

    doc.save(
        "output.pdf",
        use_objstms=True,    # pack object definitions into compressible streams
        deflate=2,           # compress uncompressed streams with Brotli compression
        compression_effort=100, # ask Brotli to work hard at it
    )
    doc.close()

The result now is a file size of 834 KB.


`compression_effort`: What it does and does not affect
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

It is an `int`, not a `bool`!

.. list-table::
   :header-rows: 1

   * - **Value**
     - **Meaning**
   * - `0`
     - Zero effort (this is the default)
   * - `1`
     - Minimum effort — fastest, largest output
   * - `100`
     - Maximum effort — slowest, smallest output


This is the single most common mistake:

.. code-block:: python

    # WRONG — True == 1 == minimum effort
    doc.save("out.pdf", use_objstms=True, deflate=2, compression_effort=True)   
    
    # CORRECT - maximum effort defined
    doc.save("out.pdf", use_objstms=True, deflate=2, compression_effort=100)    

Because Python's `True` is `1`, passing a boolean silently selects an effort setting of `1`.
No warning is raised, and the file simply comes out larger than
you expected.

Artifex published effort guidance in `Brotli is Here! <https://artifex.com/blog/brotli-is-here>`_
for the equivalent `-e` flag on `mutool clean`:

- **40** — roughly the speed of default Flate compression.
- **75** — roughly the speed of maximum Flate compression.
- **100** — squeezes out everything available, at a noticeably longer runtime.

That guidance is written in the context of Brotli compression, so treat the exact
numbers as indicative.


`compression_effort` tunes the compressor applied to stream objects as the file is
written. It does not decide *whether* streams are compressed using Brotli — that is `deflate=2`
— and it does not repack object definitions — that is `use_objstms=True`. Ensures that you have correctly set those two parameters before you start tuning `compression_effort`.

It has an effect on:

- content streams (text and vector graphics),
- font programs and other uncompressed binary streams,
- object streams produced by `use_objstms=True`.

It has little or no effect on:

- images already stored in a compressed format (JPEG, JPEG2000, JBIG2). Re-running
  a general-purpose compressor over them buys nothing. Use
  `Document.rewrite_images()` for those.
- documents whose bulk is unreferenced objects. Use `garbage=3` or `garbage=4`.


`garbage`
~~~~~~~~~~~~~~~~~~~~

Documents with unreferenced objects can be reduced in size by setting the `garbage` parameter to `3` or `4`. This will de-duplicate and drop unreferenced objects.

.. list-table::
   :header-rows: 1

   * - **Value**
     - **Meaning**
   * - `0`
     - none (default)
   * - `1`
     - remove unused (unreferenced) objects.
   * - `2`
     - in addition to 1, compact the :data:`xref` table.
   * - `3`
     - in addition to 2, merge duplicate objects.
   * - `4`
     - in addition to 3, check :data:`stream` objects for duplication. This may be slow because such data are typically large.


How much is saved here depends on the document, and how much "garbage" it may contain. For example, if we set `garbage=4` we only save a few KB:


.. code-block:: python

    import pymupdf

    doc = pymupdf.open("mupdf_explored.pdf")

    doc.save(
        "output.pdf",
        use_objstms=True,    # pack object definitions into compressible streams
        deflate=2,           # compress uncompressed streams with Brotli compression
        compression_effort=100, # ask Brotli to work hard at it
        garbage=4            # drop unreferenced objects, compact xref table, merge duplicate objects, check streams for duplication
    )
    doc.close()


Now we have a resulting PDF with a file size of 831 KB.


Results Summary
--------------------

.. list-table::
   :header-rows: 1

   * - **Description**
     - **File size result**
     - **Comments**
   * - Original file
     - 1.8 MB
     -
   * - `use_objstms=True`
     - 1.5 MB
     -
   * - `use_objstms=True`, `deflate=1`
     - 903 KB
     -
   * - `use_objstms=True`, `deflate=2`
     - 863 KB
     - Warning: Brotli is experimental and unsupported in many tools and viewers [1]_ 
   * - `use_objstms=True`, `deflate=2`, `compression_effort=100`
     - 834 KB
     - Warning: Brotli is experimental and unsupported in many tools and viewers [1]_ 
   * - `use_objstms=True`, `deflate=2`, `compression_effort=100`, `garbage=4`
     - 831 KB
     - Warning: Brotli is experimental and unsupported in many tools and viewers [1]_ 

PyMuPDF & Compression Benchmarking
----------------------------------------

Gains are corpus-dependent. Measure before paying the CPU cost in a batch job:

.. code-block:: python

    import pathlib
    import time

    import pymupdf

    src = "input.pdf"
    for effort in (0, 40, 75, 100):
        doc = pymupdf.open(src)
        out = f"out_{effort}.pdf"
        start = time.perf_counter()
        doc.save(out, garbage=4, deflate=1, use_objstms=True,
                compression_effort=effort)
        elapsed = time.perf_counter() - start
        doc.close()
        size = pathlib.Path(out).stat().st_size
        print(f"effort={effort:>3}  {size/1e6:6.2f} MB  {elapsed:5.2f}s")

See also
--------------------

- :meth:`Document.save()`
- :meth:`Document.ez_save()`
- :meth:`Document.rewrite_images()`
- :meth:`Document.subset_fonts()`
- `Brotli is Here! <https://artifex.com/blog/brotli-is-here>`_



.. [1] If you've used Brotli to compress your PDFs and found that they don't work in your favorite viewer, please try `MUPDF GL <https://mupdf.readthedocs.io/en/1.28.2/tools/mupdf-gl.html>`_. If you still find a problem viewing the file then please file an issue on our `Github tracker <https://github.com/pymupdf/PyMuPDF/issues>`_.


.. include:: footer.rst
