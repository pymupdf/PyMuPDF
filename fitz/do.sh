#!/bin/bash
swig -python fitz.i
gcc -ansi -Wpedantic -fPIC -c fitz_wrap.c -I/usr/include/python3.4m/ -I/usr/include/mupdf
gcc -ansi -Wpedantic -shared fitz_wrap.o -lmupdf -lmujs -lssl -ljbig2dec -lopenjp2 -ljpeg -lfreetype -o _fitz.so
