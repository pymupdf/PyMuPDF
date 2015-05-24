#!/bin/bash
swig -python fitz.i
gcc -fPIC -c fitz_wrap.c -I/usr/include/python3.4m/ -I/usr/include/mupdf
gcc -shared fitz_wrap.o -lmupdf -lmujs -ljbig2dec -lopenjp2 -ljpeg -lfreetype -o _fitz.so
