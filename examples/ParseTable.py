#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import fitz

"""
Created on Mon Apr 05 07:00:00 2016

@author: Jorj McKie
Copyright (c) 2015 Jorj X. McKie

The license of this program is governed by the GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007. See the "COPYING" file of this repository.

This is an example for using the Python binding PyMuPDF for MuPDF.

The ParseTab function parses tables contained in a page of a PDF 
(or OpenXPS, EPUB) file and passes back a list of lists of strings
that represents the original table in matrix form.

Dependencies:
PyMuPDF, json, sqlite3
"""

def ParseTab(doc, page, bbox):
    ''' Returns the parsed table of a page in a PDF / (open) XPS / EPUB document.
    Parameters:
    doc: a fitz.Document
    page: integer page number (0-based)
    bbox: rectangle containing the table, list of floats [xmin, ymin, xmax, ymax]
    Returns the parsed table as a list of lists of strings.
    The number of columns and rows are determined automatically
    from parsing the specified rectangle.
    '''
    import json
    import sqlite3
    pno = page                # PDF page number, 1-based
    xmin = bbox[0]
    ymin = bbox[1]
    xmax = bbox[2]
    ymax = bbox[3]
    txt = doc.getPageText(pno, output="json")
    txtdict = json.loads(txt)       # transform JSON into dictionary
    blocks = txtdict["blocks"]      # get the blocks sub dict
    db = sqlite3.connect(":memory:")        # create RAM database
    cur = db.cursor()                       # all purpose cursor
    # create a table of all spans (text pieces)
    cur.execute("CREATE TABLE `spans` (`x0` REAL,`y0` REAL, `text` TEXT)")

    # populate database with all spans in the requested bbox
    # required because we cannot rely on blocks
    # containing complete lines (left to right)
    for block in blocks:
        for line in block["lines"]:
            for span in line["spans"]:
                x0  = span["bbox"][0]       # top-left x-coord
                y0  = span["bbox"][1]       # top-left y-coord
                x1  = span["bbox"][2]       # bottom-right x-coord
                y1  = span["bbox"][3]       # bottom-right y-coord
                txt = span["text"]          # the text piece
                if x0 < xmin or x1 > xmax or y0 < ymin or y1 > ymax:
                    continue
                x0 = round(x0, 0)
                y0 = round(y0, 0)
                cur.execute("insert into spans values (?,?,?)", (x0, y0, txt))

    # determine how many different span starts occur on the page and
    # create a list of all the begin coordinates (needed for column index).
    cur.execute("select distinct x0 from spans order by x0")
    coltab = [t[0] for t in cur.fetchall()]

    # now read all text pieces from top to bottom.
    # SQL sort needed because PDF's are not reliable in that respect.
    cur.execute("select x0, y0, text from spans order by y0")
    alltxt = cur.fetchall()

    # create a matrix of table entries
    spantab = []

    # re-build (now correct) lines out of the spans
    y0 = alltxt[0][1]                       # first y0
    zeile = [""] * len(coltab)
    for c in alltxt:
        c_idx = coltab.index(c[0])          # col number of the text
        if y0 < c[1]:                       # beginning new line?
            # output old line because we are done with it
            spantab.append(zeile)
            # create new line skeleton
            y0 = c[1]
            zeile = [""] * len(coltab)
        zeile[c_idx] = c[2]

    # output last line
    spantab.append(zeile)
    db.close()
    return spantab

#==============================================================================
# Main program
#==============================================================================
''' This is just an stub program to illustrate the functioning of ParseTab.
After opening a PDF and reading a page, we
(1) search the strings that encapsulate our table
(2) from coordinates of those string occurences, we define the surrounding
    rectangle. We use zero or large numbers to specify "no limit".
(3) call ParseTab to get the recovered table
'''
doc = fitz.Document("adobe.pdf")
pno = 49
page = doc.loadPage(pno)

# search for top of table
search1 = page.searchFor("TABLE 3.1 ")
if not search1:
    raise ValueError("table top delimiter not found")

rect1 = search1[0]

ymin = rect1.y1                   # end of table header is lower height limit

# search for bottom of table
search2 = page.searchFor("The carriage return (CR) ")
if not search2:
    print("warning: table bottom delimiter not found - using end of page")
    ymax = 99999
else:
    rect2 = search2[0]
    ymax = rect2.y0                   # y coord of this line is upper limit

tab = ParseTab(doc, page.number, [0, ymin, 9999, ymax])
print("Parsed TABLE 3.1 on page 50 of Adobe's manual:")
for t in tab:
    print(t)
