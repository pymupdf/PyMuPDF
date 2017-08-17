from __future__ import print_function
import fitz
import argparse
#--------------------------------------------------------------------
# License: GNU GPL V3
# use argparse to handle invocation arguments
#--------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Enter CSV delimiter [;] and documment filename")
parser.add_argument('-d', help='CSV delimiter [;]', default = ';')
parser.add_argument('doc', help='document filename')
args = parser.parse_args()
delim = args.d               # requested CSV delimiter character
fname = args.doc          # input document filename

doc = fitz.open(fname)
meta = doc.metadata
ext = fname[-3:].lower()
fname1 = fname[:-4] + "-meta.csv"
outf = open(fname1, "w")
for k in meta.keys():
    v = meta.get(k)
    if not v:
        v = ""
    rec = delim.join([k, v])
    outf.writelines([rec, "\n"])
outf.close()
