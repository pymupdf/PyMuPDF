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
Encoding of the text in the PDF is assumed to be UTF-8.
Change the ENCODING variable as required.
-------------------------------------------------------------------------------
"""
import fitz
import sys, json

ENCODING = "UTF-8"

def SortBlocks(blocks):
    '''
    Sort the blocks of a TextPage in ascending vertical pixel order,
    then in ascending horizontal pixel order.
    This should sequence the text in a more readable form, at least by
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
    return [b[1] for b in sblocks] # return sorted list of blocks

def SortLines(lines):
    ''' Sort the lines of a block in ascending vertical direction. See comment
    in SortBlocks function.
    '''
    slines = []
    for l in lines:
        y0 = str(int(l["bbox"][1] + 0.99999)).rjust(4,"0")
        slines.append([y0, l])
    slines.sort()
    return [l[1] for l in slines]

def SortSpans(spans):
    ''' Sort the spans of a line in ascending horizontal direction. See comment
    in SortBlocks function.
    '''
    sspans = []
    for s in spans:
        x0 = str(int(s["bbox"][0] + 0.99999)).rjust(4,"0")
        sspans.append([x0, s])
    sspans.sort()
    return [s[1] for s in sspans]

#==============================================================================
# Main Program
#==============================================================================
ifile = sys.argv[1]
ofile = ifile + ".txt"

doc = fitz.Document(ifile)
pages = doc.pageCount
fout = open(ofile,"w")

for i in range(pages):
    print "========== processing page", i, "=========="
    pg_text = ""                                 # initialize page text buffer
    pg = doc.loadPage(i)                         # load page number i
    text = pg.getText(output = 'json')           # get its text in JSON format
    pgdict = json.loads(text)                    # create a dict out of it
    blocks = SortBlocks(pgdict["blocks"])        # now re-arrange ... blocks
    for b in blocks:
        lines = SortLines(b["lines"])            # ... lines
        for l in lines:
            spans = SortSpans(l["spans"])        # ... spans
            for s in spans:
                # ensure that spans are separated by at least 1 blank
                # (should make sense in most cases)
                if pg_text.endswith(" ") or s["text"].startswith(" "):
                    pg_text += unicode(s["text"])
                else:
                    pg_text += u" " + unicode(s["text"])
            pg_text += "\n"                      # separate lines by newline

    pg_text = pg_text.encode(ENCODING, "ignore")
    fout.write(pg_text)

fout.close()
