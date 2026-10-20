.. include:: header.rst


BatchResult
===========

The :class:`BatchResult` object represents the outcome of converting a single
source document during a batch conversion run.

It is returned by :meth:`convert_batch` for each input document in the batch and
contains both the conversion result and any exception raised while processing the
file.


.. class:: BatchResult

    .. attribute:: input

        Original document path or input value passed to the converter.

    .. attribute:: success

        Boolean flag indicating whether the conversion completed without an error.

    .. attribute:: error

        Exception instance raised during conversion, or ``None`` when the conversion
        succeeded.

    .. attribute:: output
        
        Conversion output produced by the selected backend. This may be a Markdown
        string, JSON payload, or text output depending on the backend used.

Example
-------

.. code-block:: python

   from pymupdf import convert_batch

   results = convert_batch(
       ["sample.pdf", "sample2.pdf"],
       workers=2,
       out_dir="output",
       backend="md",
   )

   for item in results:
       if item.success:
           print(item.input, "converted successfully")
       else:
           print(item.input, "failed:", item.error)

See also
--------

- :func:`convert_batch`


.. include:: footer.rst

