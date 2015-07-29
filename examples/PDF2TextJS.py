#!/usr/bin/env python
"""
Created on Wed Jul 29 07:00:00 2015

@author: Jorj McKie
Copyright (c) 2015 Jorj X. McKie

The license of this program is governed by the GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007. See the "COPYING" file of this repository.

This is an example for using the Python binding PyMuPDF of MuPDF.

This program extracts the text of an input PDF and writes it in a text file.
The input file name is provided as a parameter to this script (sys.argv[1])
The output file name is equal to input with the extension ".pdf" replaced by
".txt".
Encoding of the text in the PDF is assumed to be UTF-8.
Change the ENCODING variable as required.

-------------------------------------------------------------------------------
The result of this program is similar to that of PDF2Text.py -- the difference
is an internal one:

This program uses method extractJSON() of text page which delivers less
information than extractXML(), but sufficient to reconstruct a text
version of a PDF.
The benefit of it is a vastly higher performance: expect to see an improvement
by a factor of 20 or more!
-------------------------------------------------------------------------------
"""
import fitz
import sys, json

ENCODING = "utf-8"

def SortBlocks(blocks):
    '''
    Sort the blocks of a TextPage in ascending vertical pixel order,
    then in ascending horizontal pixel order.
    This ensures sequencing the text in a more readable form, at least by
    convention of the Western hemisphere: from top-left to bottom-right.
    If you need something else, change the sortkey variable accordingly ...
    '''
    sblocks = []
    for b in blocks:
        x0 = str(int(b["bbox"][0]+0.99999)).rjust(4,"0") # x coord in pixels
        y0 = str(int(b["bbox"][1]+0.99999)).rjust(4,"0") # y coord in pixels
        sortkey = y0 + x0                                # = "yx"
        sblocks.append([sortkey, b])
    sblocks.sort()
    return sblocks

def GetPageText(pg):
    dl = fitz.DisplayList()
    dv = fitz.Device(dl)
    pg.run(dv, fitz.Identity)
    ts = fitz.TextSheet()
    tp = fitz.TextPage()
    rect = pg.bound()
    dl.run(fitz.Device(ts, tp), fitz.Identity, rect)
    return tp.extractJSON()

#==============================================================================
# Main Program
#==============================================================================
ifile = sys.argv[1]
ofile = ifile.replace(".pdf",".txt")
doc = fitz.Document(ifile)
pages = doc.pageCount
fout = open(ofile,"w")

for i in range(pages):
    print "========== processing page", i, "=========="
    pg_text = ""
    pg = doc.loadPage(i)
    text = GetPageText(pg)
    pgdict = json.loads(text)
    blocks = SortBlocks(pgdict["blocks"])
    for bx in blocks:
        b = bx[1]
        for l in b["lines"]:
            for s in l["spans"]:
                pg_text += unicode(s["text"])
            pg_text += "\n"

    pg_text = pg_text.encode(ENCODING, "ignore")
    fout.write(pg_text)

fout.close()
