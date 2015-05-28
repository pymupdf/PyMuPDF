#!/usr/bin/env python2
#this demo will open an encrypted PDF document
#decrypt it with the provided password
#and save as a new PDF document
#usage: removePass.py <input file> <password> <output file>

import fitz
import sys

if len(sys.argv) != 4:
    print('Usage: %s <input file> <password> <output file>' % sys.argv[0])
    exit(0)

doc = fitz.Document(sys.argv[1])
#the document should be password protected
assert doc.needsPass

#decrypt the document
#return non-zero if failed
if doc.authenticate(sys.argv[2]):
    print('cannot decrypt %s with password %s' % (sys.argv[1], sys.argv[2]))
    exit(1)

#save as a new PDF
doc.save(sys.argv[3])
