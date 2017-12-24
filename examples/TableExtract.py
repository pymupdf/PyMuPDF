#!/usr/bin/python
from __future__ import print_function
import fitz
from ParseTab import ParseTab
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
PyMuPDF
"""
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
tab = ParseTab(doc, page, [0, ymin, 9999, ymax])

#print(table_title)
#for t in tab:
#    print(t)
csv = open("p%s.csv" % (pno+1,), "w")
csv.write(table_title + "\n")
for t in tab:
    csv.write("|".join(t).encode("utf-8","ignore") + "\n")
csv.close()
