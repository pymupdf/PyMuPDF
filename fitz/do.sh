#!/bin/bash
swig -python fitz.i
gcc -fPIC -c fitz_wrap.c -I/usr/include/python2.7/
gcc -shared fitz_wrap.o -lmupdf -lmujs -lssl -ljbig2dec -lopenjp2 -ljpeg -lfreetype -o _fitz.so
