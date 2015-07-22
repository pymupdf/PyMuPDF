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
The output file name is equal to input with the extension ".pdf" replaced by
".txt".
Encoding of the PDF is assumed to be UTF-8. Change the ENCODING variable
as required.
"""

import fitz
import os, sys
ENCODING = "utf-8"

def RunPage(pg):
    dl = fitz.DisplayList()
    dv = fitz.Device(dl)
    ts = fitz.TextSheet()
    tp = fitz.TextPage()
    pg.run(dv, fitz.Identity)
    rect = pg.bound()
    dl.run(fitz.Device(ts, tp), fitz.Identity, rect)
    dv = None
    return tp.extractText()

#==============================================================================
# Main Program
#==============================================================================
f = sys.argv[1]
idir, iname = os.path.split(f)
print " dir ==>", idir
print "file ==>", iname
oname = iname.replace(".pdf",".txt")
ofile = os.path.join(idir, oname)
doc = fitz.Document(f)
seiten = d.pageCount

fout = open(ofile,"w")
for i in range(seiten):
    print "========== processing page", i, " =========="
    pg = doc.loadPage(i)
    text = RunPage(pg)
    fout.write(text.encode(ENCODING,"ignore"))

fout.close()
doc.close()