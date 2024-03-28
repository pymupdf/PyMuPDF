.. include:: header.rst

.. _RecipesMultiprocessing:


.. |toggleStart| raw:: html

   <details>
   <summary><a>See code</a></summary>

.. |toggleEnd| raw:: html

   </details>

==============================
Multiprocessing
==============================

:title:`MuPDF` has no integrated support for threading - calling itself "thread-agnostic". While there do exist tricky possibilities to still use threading with :title:`MuPDF`, the baseline consequence for |PyMuPDF| is:

**No Python threading support**.

Using |PyMuPDF| in a :title:`Python` threading environment will lead to blocking effects for the main thread.

However, there is the option to use :title:`Python's` *multiprocessing* module in a variety of ways.

If you are looking to speed up page-oriented processing for a large document, use this script as a starting point. It should be at least twice as fast as the corresponding sequential processing.


|toggleStart|

.. literalinclude:: samples/multiprocess-render.py
   :language: python

|toggleEnd|


Here is a more complex example involving inter-process communication between a main process (showing a GUI) and a child process doing |PyMuPDF| access to a document.


|toggleStart|

.. literalinclude:: samples/multiprocess-gui.py
   :language: python

|toggleEnd|


.. include:: footer.rst
