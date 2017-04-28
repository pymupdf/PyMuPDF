from __future__ import print_function
import sys
import fitz
#------------------------------------------------------------------------------    
# Example script:
# Copy embedded files from one PDF to another
# Invocation line:
# python embedded-copy.py  in.pdf out.pdf
#------------------------------------------------------------------------------
ifn = sys.argv[1]                      # input PDF
ofn = sys.argv[2]                      # output PDF
docin = fitz.open(ifn)
docout = fitz.open(ofn)
print("Copying embedded files from '%s' to '%s'" % (ifn, ofn))
for i in range(docin.embeddedFileCount):
    d = docin.embeddedFileInfo(i)
    b = docin.embeddedFileGet(i)
    try:
        print ("copying entry:", d["name"])
        docout.embeddedFileAdd(b, d["name"], d["file"], d["desc"])
    except:
        pass
    
docout.saveIncr()                      # save output changes incrementally