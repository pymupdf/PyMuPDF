======================
README for python-fitz
======================

This branch intends for MuPDF 1.7. It's still in heavy development.

Start Developing
---------------

First, we need MuPDF 1.7 header files, which are already included in this repo(in the folder ``fitz``).

Next, we need mupdf libraries. For linux, there are 2: ``libmupdf.a`` and ``libmujs.a``. Make sure that these 2 libs are compiled as position independent(gcc with ``-fPIC``).

Besides, some 3rd party libraries are also needed. For linux, there are: ``libssl.so``, ``libjbig2dec.so``, ``libopenjp2.so``, ``libjpeg.so``, ``libfreetype.so``. The code of these libs can also be found in MuPDF's source.

Now that we have the env ready, we can edit the SWIG file, ``fitz/fitz.i``, to add more symbols. Then we generate the wrapper .c file using:

    swig -python fitz.i

And compile it to get the python module.

For linux, there's a simple bash script ``fitz/do.sh`` to do the stuff.

Once we get the module(``_fitz.so`` on linux), we can import it in python. There's a demo script, ``fitz/demo.py``, which will display number of pages of a given PDF file.
