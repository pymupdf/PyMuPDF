from __future__ import print_function
import sys
import fitz
#------------------------------------------------------------------------------
# Example script:
# License: GNU GPL V3
# Copy embedded files between PDF documents
# Invocation line:
# python embedded-copy.py  in.pdf out.pdf
#------------------------------------------------------------------------------
ifn = sys.argv[1]                      # input PDF
ofn = sys.argv[2]                      # output PDF
docin = fitz.open(ifn)
docout = fitz.open(ofn)
print("Copying embedded files from '%s' to '%s'" % (ifn, ofn))
for i in range(docin.embeddedFileCount):
    d = docin.embeddedFileInfo(i)      # file metadata
    b = docin.embeddedFileGet(i)       # file content
    try:                               # safeguarding against duplicate entries
        print ("copying entry:", d["name"])
        docout.embeddedFileAdd(b, d["name"], d["file"], d["desc"])
    except:
        pass

# save output (incrementally or to new PDF)
docout.saveIncr()