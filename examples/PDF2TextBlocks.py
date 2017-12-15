#!/usr/bin/env python
"""
Created on Thu Dec 14 17:00:00 2017

@author: Jorj McKie
Copyright (c) 2017 Jorj X. McKie

The license of this program is governed by the GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007. See the "COPYING" file of this repository.

This is an example for using the Python binding PyMuPDF for MuPDF.

This program extracts the text of any supported input document
and writes it to a text file.
The input file name is provided as a parameter to this script (sys.argv[1])
The output file name is input-filename + ".txt".

In an effort to ensure correct reading sequence, text blocks are sort in
ascending vertical, then horizontal direction. Please note that this will not
work for all pages.
"""

import fitz
import sys
from operator import itemgetter

assert len(sys.argv) == 2, "need filename as parameter"
#==============================================================================
# Main Program
#==============================================================================
ifile = sys.argv[1]
ofile = ifile + ".txt"

doc = fitz.open(ifile)
pages = len(doc)

fout = open(ofile,"w")

for page in doc:
    blocks = page.getTextBlocks()
    sb = sorted(blocks, key = itemgetter(1, 0))
    for b in sb:
        fout.write(b[4].encode("utf-8"))

fout.close()
