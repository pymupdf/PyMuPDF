import csv
import fitz
import argparse
#--------------------------------------------------------------------
# License: GNU GPL V3
# use argparse to handle invocation arguments
#--------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Enter CSV delimiter [;], CSV filename and documment filename")
parser.add_argument('-d', help='CSV delimiter [;]', default = ';')
parser.add_argument('-x', help='delete XML info [n]', default = 'n')
parser.add_argument('-csv', help='CSV filename')
parser.add_argument('-pdf', help='PDF filename')
args = parser.parse_args()
delim = args.d               # requested CSV delimiter character
assert args.csv, "missing CSV filename"
assert args.pdf, "missing PDF filename"
print "delimiter", args.d
print "xml delete", args.x
print "csv file", args.csv
print "pdf file", args.pdf
print "----------------------------------------"
doc = fitz.open(args.pdf)
oldmeta = doc.metadata
print "old metadata:"
for k,v in oldmeta.items():
    print k, ":",v

with open(args.csv) as tocfile:
    tocreader = csv.reader(tocfile, delimiter = delim)
    for row in tocreader:
        assert len(row) == 2, "each row must contain 2 entries"
        oldmeta[row[0]] = row[1]
print "----------------------------------------"
print "\nnew metadata:"
for k,v in oldmeta.items():
    print k, ":",v
doc.setMetadata(oldmeta)
doc.saveIncr()