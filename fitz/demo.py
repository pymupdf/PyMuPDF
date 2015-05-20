#!/usr/bin/env python2
#This is a demo which prints number of pages

import fitz
import sys

ctx = fitz.fz_new_context_imp(None, None, fitz.FZ_STORE_UNLIMITED, fitz.FZ_VERSION)
fitz.fz_register_document_handlers(ctx)
#argv[1] is the PDF filename
doc = fitz.fz_open_document(ctx, sys.argv[1])
pagecount = fitz.fz_count_pages(ctx, doc)
print '%d pages' % pagecount
