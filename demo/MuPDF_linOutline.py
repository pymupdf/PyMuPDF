#!/usr/bin/env python
# -*- coding: utf8 -*-

import fitz, sys
#==============================================================================
# MuPDF Outline Flattener
#==============================================================================
'''
This is a demo program for using some of the non-rendering capabilities of
MuPDF.
For a given PDF specified in sys.argv[1] this program will scan through the
outline entries and create a linear list of them, i.e. the entry tree is
being flattened out.
This is much the same as you can achieve with the print_outline function, except
you have it in a nice python list instead of a file.
Each entry of the list has the format:
        [indent, title, page]
Where:
indent = indentation level starting with 1 (integer)
title = title of the entry (utf-8)
page = page index (page 1 = 0, integer)
'''
#==============================================================================
# Create the outline list
#==============================================================================
def get_ol_list(outline):
    if not outline:                    # contains no outline:
        return []                      # return empty list
    lvl = 0                            # records current indent level   
    ltab = {}                          # current OutlineItem per level
    liste = []                         # will hold flattened outline
    olItem = outline                   # olItem will be used for iteration
    while olItem:
        while olItem:                  # process one OutlineItem
            lvl += 1                   # its indent level
            # create one outline line
            zeile = [lvl, olItem.title, olItem.dest.page]
            liste.append(zeile)        # append it
            ltab[lvl] = olItem         # record OutlineItem in level table 
            olItem = olItem.down       # go to child OutlineItem
        olItem = ltab[lvl].next        # no more children, look for brothers
        if olItem:                     # have any?
            lvl -= 1                   # prep. proc.: decrease lvl recorder 
            continue
        else:                          # no kids, no brothers, now what?
            while lvl > 1 and not olItem:
                lvl -= 1               # go look for uncles
                olItem = ltab[lvl].next
            if lvl < 1:                # out of relatives
                return liste           # return linearized outline
            lvl -= 1
    return liste                       # return linearized outline

#==============================================================================
# Main program
#==============================================================================
f= sys.argv[1]                         # document dataset name
# open the document
doc = fitz.Document(f)
print("Number of pages:", doc.pageCount)
# get the linear outline list
ol = get_ol_list(doc.outline)
print("linearized outline: %s entries" % (len(ol),))
for o in ol:
    print(o)
