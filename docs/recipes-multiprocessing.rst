.. _RecipesMultiprocessing:

==============================
Recipes: Multiprocessing
==============================

MuPDF has no integrated support for threading - they call themselves "threading-agnostic". While there do exist tricky possibilities to still use threading with MuPDF, the baseline consequence for **PyMuPDF** is:

**No Python threading support**.

Using PyMuPDF in a Python threading environment will lead to blocking effects for the main thread.

However, there exists the option to use Python's *multiprocessing* module in a variety of ways.

If you are looking to speed up page-oriented processing for a large document, use this script as a starting point. It should be at least twice as fast as the corresponding sequential processing.

.. literalinclude:: multiprocess-render.py
   :language: python

Here is a more complex example involving inter-process communication between a main process (showing a GUI) and a child process doing PyMuPDF access to a document.

.. literalinclude:: multiprocess-gui.py
   :language: python
