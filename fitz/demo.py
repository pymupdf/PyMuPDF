#!/usr/bin/env python2
#This is a demo which prints number of pages

import fitz
import sys

fitz.initContext()
doc = fitz.Document(sys.argv[1])
print '%d pages' % doc.pageCount
#page = doc.loadPage(0)