======================
README for python-fitz
======================

This branch intends for MuPDF 1.7. It's still in heavy development.

Start Developing
---------------

First, we need MuPDF 1.7 header files. Make sure that these headers are in the compiler's search path when compiling it.

Next, we need mupdf libraries. For linux, there are 2: ``libmupdf.a`` and ``libmujs.a``. Make sure that these 2 libs are compiled as position independent(gcc with ``-fPIC``).

Besides, some 3rd party libraries are also needed. For linux, there are: ``libssl.so``, ``libjbig2dec.so``, ``libopenjp2.so``, ``libjpeg.so``, ``libfreetype.so``, ``libz.so``. The code of these libs can also be found in MuPDF's source.  

For Windows, only the following two files are needed: ``libmupdf.lib`` and ``libthirdparty.lib``. Any 3rd party software is already included.  
We may be able to supply pre-compiled / pre-linked copies of these with this repository to save a major setup step for using MuPDF in Windows.

Now that we have the env ready, we can edit the SWIG file, ``fitz/fitz.i``, to add more symbols. Then we generate the wrapper .c file using:

    swig -python fitz.i

And compile the ``fitz_wrap.c`` to get the python module.

For linux, there's a simple bash script ``fitz/do.sh`` to do compiling stuff.

Once we get the module, we can import it in python. 

There are several demo scripts, ``fitz/demo.py``, ``PDF_display.py``, and ``PDF_outline.py``, which open PDF documents to save pages to PNG files, display them using a dialog manager like wxPython, or create Python lists from PDF outlines.  
These demos are all ports from the corresponding demo application of python-fitz 1.2.
