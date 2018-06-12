from __future__ import print_function
import fitz
import argparse

#------------------------------------------------------------------------------
# Example program
# License: GNU GPL V3
# Imports a new file into an existing PDF
# Command line:
# python embedded-import.py some.pdf embed.file
#------------------------------------------------------------------------------

parser = argparse.ArgumentParser(description="Enter PDF, file to embed, and optional name, description and output pdf.")
parser.add_argument('pdf', help='PDF filename')
parser.add_argument('file', help='name of embedded file')
parser.add_argument('-n', "--name", help='name for embedded file entry (default: file)')
parser.add_argument('-d', "--desc", help='description (default:  file)')
parser.add_argument('-o', "--output", help = 'output PDF (default: modify pdf)')
args = parser.parse_args()
delim = args.desc               # requested CSV delimiter character
pdffn = args.pdf
impfn = args.file

doc = fitz.open(pdffn)
if not args.name:
    name = impfn
desc = args.desc
if not args.desc:
    desc = impfn

# to be on the safe side, always open as binary
content = open(impfn, "rb").read()  # read all file content in

# import the file into the PDF
doc.embeddedFileAdd(content, name, impfn, desc)
# save PDF (either incremental or to new PDF file)
if not args.output:
    doc.saveIncr()
else:
    doc.save(args.output, garbage = 4, deflate = True)