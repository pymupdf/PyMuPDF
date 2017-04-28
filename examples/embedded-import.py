from __future__ import print_function
import sys
import fitz
#------------------------------------------------------------------------------
# Example program
# Imports a new file into an existing PDF
# Command line:
# python embedded-import.py out.pdf input.file
#
#
#------------------------------------------------------------------------------
pdffn = sys.argv[1]
impfn = sys.argv[2]

doc = fitz.open(pdffn)
infile = open(impfn, "rb")        # to be on the safe side always open binary

content = infile.read()           # read all file content in
infile.close()                    # import file no longer needed

# now some description of what is going to imported
name = "import1"                  # mandatory: unique name inside the PDF
filename = impfn                  # optional filename, need not be the original
desc = "something documentary"    # optional other comments

# import the file into the PDF
doc.embeddedFileAdd(content, name, filename, desc)
# save PDF (may use incremental or to new PDF file)
doc.saveIncr()