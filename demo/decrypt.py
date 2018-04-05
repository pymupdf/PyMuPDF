#!/usr/bin/env python2
#this demo will open an encrypted PDF document
#decrypt it with the provided password
#and save as a new PDF document
#usage: removePass.py <input file> <password> <output file>

import fitz
import sys

assert len(sys.argv) == 4, \
 'Usage: %s <input file> <password> <output file>' % sys.argv[0]

doc = fitz.Document(sys.argv[1])
#the document should be password protected
assert doc.needsPass, sys.argv[0] + " not password protected"

#decrypt the document
#return non-zero if failed
assert doc.authenticate(sys.argv[2]), \
 'cannot decrypt %s with password "%s"' % (sys.argv[1], sys.argv[2])

#save as a new PDF
doc.save(sys.argv[3])
