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
#==============================================================================
# Function ParseTab - parse a document table into a Python list of lists
#==============================================================================
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
    pno = page                                   # PDF page number, 0-based
    xmin, ymin, xmax, ymax = bbox                # rectangle coordinates
    if not (xmin < xmax and ymin < ymax):
        print("Warning: incorrect rectangle coordinates!")
        return []
    txt = doc.getPageText(pno, output="json")    # page text in JSON format
    txtdict = json.loads(txt)               # transform JSON into dictionary
    blocks = txtdict["blocks"]              # get the blocks sub dict
    db = sqlite3.connect(":memory:")        # create RAM database
    cur = db.cursor()                       # all purpose cursor
    # create a table of all spans (text pieces)
    cur.execute("CREATE TABLE `spans` (`x0` REAL,`y0` REAL, `text` TEXT)")

#==============================================================================
#   Function spanout - store a table entry in database
#==============================================================================
    def spanout(s, y0):
        x0  = s["bbox"][0]
        txt = s["text"]          # the text piece
        cur.execute("insert into spans values (?,?,?)", (int(x0), int(y0), txt))
        return
#==============================================================================
    # populate database with all spans in the requested bbox
    for block in blocks:
        for line in block["lines"]:
            y0 = line["bbox"][1]            # top-left y-coord
            y1 = line["bbox"][3]            # bottom-right y-coord
            if y0 < ymin or y1 > ymax:      # line outside bbox limits - skip it
                continue
            spans = []                      # sort spans by their left coord's
            for s in line["spans"]:
                if s["bbox"][0] >= xmin and s["bbox"][2] <= xmax:
                    spans.append([s["bbox"][0], s])
            if spans:                       # any spans left at all?
                spans.sort()                # sort them
            else:
                continue
            # concatenate spans that are close to each other
            for i, s in enumerate(spans):
                span = s[1]
                if i == 0:
                    s0 = span                    # memorize 1st span
                    continue
                x0  = span["bbox"][0]            # left borger of span
                x1  = span["bbox"][2]            # right border of span
                txt = span["text"]               # text of this span
                if abs(x0 - s0["bbox"][2]) > 3:  # if more than 3 pixels away
                    spanout(s0, y0)              # from previous span, output it
                    s0 = span                    # store this one as new 1st
                    continue
                s0["text"] += txt                # join current span with prev
                s0["bbox"][2] = x1               # save new right border
            spanout(s0, y0)                      # output the orphan

    # create a list of all the begin coordinates (used for column indices).
    cur.execute("select distinct x0 from spans order by x0")
    coltab = [t[0] for t in cur.fetchall()]

    # now read all text pieces from top to bottom.
    cur.execute("select x0, y0, text from spans order by y0")
    alltxt = cur.fetchall()
    db.close()                                   # do not need database anymore

    # create the matrix
    spantab = []

    try:
        y0 = alltxt[0][1]                   # y-coord of first line
    except IndexError:                      # nothing there:
        print("Warning: no text found within rectangle!")
        return []
    
    zeile = [""] * len(coltab)
    
    for c in alltxt:
        c_idx = coltab.index(c[0])          # col number of the text piece
        if y0 < c[1]:                       # beginning a new line?
            # output old line
            spantab.append(zeile)
            # create new line skeleton
            y0 = c[1]
            zeile = [""] * len(coltab)
        zeile[c_idx] = c[2]

    # output last line
    spantab.append(zeile)
    return spantab

#==============================================================================
# Main program
#==============================================================================
''' This is just a stub to illustrate the functioning of ParseTab.
After reading a page, we
(1) search the strings that encapsulate our table
(2) from coordinates of those string occurences, we define the surrounding
    rectangle. We use zero or large numbers to specify "no limit".
(3) call ParseTab to get the parsed table
'''
doc = fitz.Document("adobe.pdf")
pno = 61
page = doc.loadPage(pno)

#==============================================================================
# search for top of table
#==============================================================================
table_title = "Table 3.4 "
search1 = page.searchFor(table_title, hit_max = 1)
if not search1:
    raise ValueError("table top delimiter not found")
rect1 = search1[0]  # the rectangle that surrounds the search string
ymin = rect1.y1     # table starts below this value

#==============================================================================
# search for bottom of table
#==============================================================================
search2 = page.searchFor("related tasks", hit_max = 1)
if not search2:
    print("warning: table bottom delimiter not found - using end of page")
    ymax = 99999
else:
    rect2 = search2[0]  # the rectangle that surrounds the search string
    ymax = rect2.y0     # table ends above this value

if not ymin < ymax:     # something was wrong with the search strings
    raise ValueError("table bottom delimiter higher than top")

#==============================================================================
# now get the table
#==============================================================================
tab = ParseTab(doc, page.number, [0, ymin, 9999, ymax])

#print(table_title)
#for t in tab:
#    print(t)
csv = open("p%s.csv" % (pno+1,), "w")
csv.write(table_title + "\n")
for t in tab:
    csv.write("|".join(t).encode("utf-8","ignore") + "\n")
csv.close()
