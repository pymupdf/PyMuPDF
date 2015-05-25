#!/bin/bash
swig -python fitz.i
gcc -ansi -Wpedantic -fPIC -c fitz_wrap.c -I/usr/include/python2.7/ -I/usr/include/mupdf
gcc -shared fitz_wrap.o -lmupdf -lmujs -lcrypto -ljbig2dec -lopenjp2 -ljpeg -lfreetype -o _fitz.so
