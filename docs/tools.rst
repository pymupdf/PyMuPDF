.. _Tools:

Tools
================

This class is a collection of utility methods and attributes, mainly around memory management. To simplify and speed up its use, it is automatically instantiated under the name *TOOLS* when PyMuPDF is imported.

================================== =================================================
**Method / Attribute**             **Description**
================================== =================================================
:meth:`Tools.gen_id`               generate a unique identifyer
:meth:`Tools.store_shrink`         shrink the storables cache [#f1]_
:meth:`Tools.mupdf_warnings`       return the accumulated MuPDF warnings
:meth:`Tools.mupdf_display_errors` return the accumulated MuPDF warnings
:meth:`Tools.reset_mupdf_warnings` empty MuPDF messages on STDOUT
:attr:`Tools.fitz_config`          configuration settings of PyMuPDF
:attr:`Tools.store_maxsize`        maximum storables cache size
:attr:`Tools.store_size`           current storables cache size
================================== =================================================

**Class API**

.. class:: Tools

   .. method:: gen_id()

      A convenience method returning a unique positive integer which will increase by 1 on every invocation. Example usages include creating unique keys in databases - its creation should be faster than using timestamps by an order of magnitude.

      .. note:: MuPDF has dropped support for this in v1.14.0, so we have re-implemented a similar function with the following differences:

            * It is not part of MuPDF's global context and not threadsafe (not an issue because we do not support threads in PyMuPDF anyway).
            * It is implemented as *int*. This means that the maximum number is *sys.maxsize*. Should this number ever be exceeded, the counter starts over again at 1.

      :rtype: int
      :returns: a unique positive integer.

   .. method:: store_shrink(percent)

      Reduce the storables cache by a percentage of its current size.

      :arg int percent: the percentage of current size to free. If 100+ the store will be emptied, if zero, nothing will happen. MuPDF's caching strategy is "least recently used", so low-usage elements get deleted first.

      :rtype: int
      :returns: the new current store size. Depending on the situation, the size reduction may be larger than the requested percentage.

   .. method:: reset_mupdf_warnings()

      *(New in version 1.16.0)*
      
      Empty MuPDF warnings message buffer.


   .. method:: mupdf_display_errors(value=None)

      *(New in version 1.16.8)*
      
      Show or set whether MuPDF errors should be displayed.

      :arg bool value: if not a bool, the current setting is returned. If true, MuPDF errors will be shown on *sys.stderr*, otherwise suppressed. In any case, messages continue to be stored in the warnings store. Upon import of PyMuPDF this value is *True*.

      :returns: *True* or *False*


   .. method:: mupdf_warnings(reset=True)

      *(New in version 1.16.0)*
      
      Return all stored MuPDF messages as a string with interspersed line-breaks.

      :arg bool reset: *(new in version 1.16.7)* whether to automatically empty the store.


   .. attribute:: fitz_config

      A dictionary containing the actual values used for configuring PyMuPDF and MuPDF. Also refer to the installation chapter. This is an overview of the keys, each of which describes the status of a support aspect.

      ================= ===================================================
      **Key**           **Support included for ...**
      ================= ===================================================
      plotter-g         Gray colorspace rendering
      plotter-rgb       RGB colorspace rendering
      plotter-cmyk      CMYK colorspcae rendering
      plotter-n         overprint rendering
      pdf               PDF documents
      xps               XPS documents
      svg               SVG documents
      cbz               CBZ documents
      img               IMG documents
      html              HTML documents
      epub              EPUB documents
      jpx               JPEG2000 images
      js                JavaScript
      tofu              all TOFU fonts
      tofu-cjk          CJK font subset (China, Japan, Korea)
      tofu-cjk-ext      CJK font extensions
      tofu-cjk-lang     CJK font language extensions
      tofu-emoji        TOFU emoji fonts
      tofu-historic     TOFU historic fonts
      tofu-symbol       TOFU symbol fonts
      tofu-sil          TOFU SIL fonts
      icc               ICC profiles
      py-memory         using Python memory management [#f2]_
      base14            Base-14 fonts (should always be true)
      ================= ===================================================

      For an explanation of the term "TOFU" see `this Wikipedia article <https://en.wikipedia.org/wiki/Noto_fonts>`_.::

       In [1]: import fitz
       In [2]: TOOLS.fitz_config
       Out[2]:
       {'plotter-g': True,
        'plotter-rgb': True,
        'plotter-cmyk': True,
        'plotter-n': True,
        'pdf': True,
        'xps': True,
        'svg': True,
        'cbz': True,
        'img': True,
        'html': True,
        'epub': True,
        'jpx': True,
        'js': True,
        'tofu': False,
        'tofu-cjk': True,
        'tofu-cjk-ext': False,
        'tofu-cjk-lang': False,
        'tofu-emoji': False,
        'tofu-historic': False,
        'tofu-symbol': False,
        'tofu-sil': False,
        'icc': True,
        'py-memory': True, # (False if Python 2)
        'base14': True}

      :rtype: dict

   .. attribute:: store_maxsize

      Maximum storables cache size in bytes. PyMuPDF is generated with a value of 268'435'456 (256 MB, the default value), which you should therefore always see here. If this value is zero, then an "unlimited" growth is permitted.

      :rtype: int

   .. attribute:: store_size

      Current storables cache size in bytes. This value may change (and will usually increase) with every use of a PyMuPDF function. It will (automatically) decrease only when :attr:`Tools.store_maxize` is going to be exceeded: in this case, MuPDF will evict low-usage objects until the value is again in range.

      :rtype: int

Example Session
----------------

.. highlight:: python

::
   >>> import fitz
   # print the maximum and current cache sizes
   >>> fitz.TOOLS.store_maxsize
   268435456
   >>> fitz.TOOLS.store_size
   0
   >>> doc = fitz.open("demo1.pdf")
   # pixmap creation puts lots of object in cache (text, images, fonts),
   # apart from the pixmap itself
   >>> pix = doc[0].getPixmap(alpha=False)
   >>> fitz.TOOLS.store_size
   454519
   # release (at least) 50% of the storage
   >>> fitz.TOOLS.store_shrink(50)
   13471
   >>> fitz.TOOLS.store_size
   13471
   # get a few unique numbers
   >>> fitz.TOOLS.gen_id()
   1
   >>> fitz.TOOLS.gen_id()
   2
   >>> fitz.TOOLS.gen_id()
   3
   # close document and see how much cache is still in use
   >>> doc.close()
   >>> fitz.TOOLS.store_size
   0
   >>>


.. rubric:: Footnotes

.. [#f1] This memory area is internally used by MuPDF, and it serves as a cache for objects that have already been read and interpreted, thus improving performance. The most bulky object types are images and also fonts. When an application starts up the MuPDF library (in our case this happens as part of *import fitz*), it must specify a maximum size for this area. PyMuPDF's uses the default value (256 MB) to limit memory consumption. Use the methods here to control or investigate store usage. For example: even after a document has been closed and all related objects have been deleted, the store usage may still not drop down to zero. So you might want to enforce that before opening another document.

.. [#f2] Optionally, all dynamic management of memory can be done using Python C-level calls. MuPDF offers a hook to insert user-preferred memory managers. We are using option this for Python version 3 since PyMuPDF v1.13.19. At the same time, all memory allocation in PyMuPDF itself is also routed to Python (i.e. no more direct *malloc()* calls in the code). We have seen improved memory usage and slightly reduced runtimes with this option set. If you want to change this, you can set *#define JM_MEMORY 0* (uses standard C malloc, or 1 for Python allocation )in file *fitz.i* and then generate PyMuPDF.
