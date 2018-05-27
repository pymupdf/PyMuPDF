# -*- coding: utf-8 -*-
"""
PyMuPDF Example Script:
------------------------

Split a given PDF into separate files of one page each.
For "input.pdf" the generated files are named "input-%i.pdf".

PyMuPDF license
"""

import fitz
import sys
fn = sys.argv[1]

fn1 = fn[:-4]

src = fitz.open(fn)

for i in range(len(src)):
    doc = fitz.open()
    doc.insertPDF(src, from_page = i, to_page = i)
    doc.save("%s-%i.pdf" % (fn1, i))
    doc.close()
    
