#!/usr/bin/env python
"""
Created on Sun Jul 12 07:00:00 2015

@author: Jorj McKie
Copyright (c) 2015 Jorj X. McKie

The license of this program is governed by the GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007. See the "COPYING" file of this repository.

This is an example for using the Python binding PyMuPDF of MuPDF.

This program extracts the text of an input PDF and writes it in a text file.
The input file name is provided as a parameter to this script (sys.argv[1])
The output file name is input-filename + ".txt".
Encoding of the text in the PDF is assumed to be UTF-8.
Change the ENCODING variable as required.
"""

import fitz
import sys

ENCODING = "utf-8"

#==============================================================================
# Main Program
#==============================================================================
ifile = sys.argv[1]
ofile = ifile + ".txt"

doc = fitz.Document(ifile)
pages = doc.pageCount

fout = open(ofile,"w")

for i in range(pages):
    text = doc.getPageText(i)
    fout.write(text.encode(ENCODING,"ignore"))

fout.close()
