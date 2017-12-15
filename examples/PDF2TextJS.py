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
The output file name is input-filename appended with ".txt".

Motivation:
------------
Try to output the text in a "natural" reading order, as this is not guarantied
by e.g. PDF itself.
Therefore, the blocks of a text page (highest hierarchy level) are sorted in
ascending order of their top left corner.
This approach is a help, but by no means bulletproof, because pages can be
almost arbitrarily complex, so that for every algorithm there will be examples
where it fails.
-------------------------------------------------------------------------------
"""
import fitz
import sys, json
from operator import itemgetter

assert len(sys.argv) == 2, "need filename as parameter"

def SortBlocks(blocks):
    sblocks = []
    for b in blocks:
        if b["type"] != 0:
            continue
        r = fitz.Rect(b["bbox"])
        sblocks.append([r.x0, r.y0, b])     # sorting by top-left corner
        # adjust to your needs

    sb = sorted(sblocks, key = itemgetter(1, 0))

    return [b[2] for b in sb] # return sorted list of blocks

#==============================================================================
# Main Program
#==============================================================================
ifile = sys.argv[1]
ofile = ifile + ".txt"

doc = fitz.open(ifile)

if str is bytes:
    fout = open(ofile,"w")         # Python 2
else:
    fout = open(ofile, "wb")       # Python 3

for page in doc:
    dl = page.getDisplayList()
    tp = dl.getTextPage(3)         # enforce ignoring images (for speed only)
    text = tp.extractJSON()
    pgdict = json.loads(text)
            
    blocks = SortBlocks(pgdict["blocks"])
    for b in blocks:
        btxt = "-"
        lines = b["lines"]

        for l in lines:
            ltxt = ""
            spans = l["spans"]
            for s in spans:
                ltxt += s["text"]
            if btxt.endswith("-"):
                btxt = btxt[:-1] + ltxt
            else:
                btxt += " " + ltxt
        btxt += "\n"
        fout.write(btxt.encode("utf-8"))

fout.close()
