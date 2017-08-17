from __future__ import print_function
import sys
import fitz
#------------------------------------------------------------------------------
# Example program
# License: GNU GPL V3
# Imports a new file into an existing PDF
# Command line:
# python embedded-import.py out.pdf input.file
#------------------------------------------------------------------------------
pdffn = sys.argv[1]
impfn = sys.argv[2]

doc = fitz.open(pdffn)

# to be on the safe side, always open as binary
content = open(impfn, "rb").read()  # read all file content in

# now some description of what is going to imported
name = "import1"                  # mandatory: unique name inside the PDF
filename = impfn                  # optional filename, need not be the original
desc = "something documentary"    # optional other comments

# import the file into the PDF
doc.embeddedFileAdd(content, name, filename, desc)
# save PDF (either incremental or to new PDF file)
doc.saveIncr()