import csv
import fitz
import argparse
#--------------------------------------------------------------------
# use argparse to handle invocation arguments
#--------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Enter CSV delimiter [;], CSV filename and documment filename")
parser.add_argument('-d', nargs=1, help='CSV delimiter [;]', default = ';')
parser.add_argument('-csv', help='CSV filename')
parser.add_argument('-pdf', help='PDF filename')
args = parser.parse_args()
delim = args.d               # requested CSV delimiter character
assert args.csv, "missing CSV filename"
assert args.pdf, "missing PDF filename"

doc = fitz.open(args.pdf)
toc = []
with open(args.csv) as tocfile:
    tocreader = csv.reader(tocfile, delimiter = delim)
    for row in tocreader:
        assert len(row) <= 4, "cannot handle more than 4 entries:\n %s" % (str(row),)
        if len(row) == 4:
            p4 = float(row[3])
            toc.append([int(row[0]), row[1], int(row[2]), p4])
        else:
            toc.append([int(row[0]), row[1], int(row[2])])
doc.setToC(toc)
doc.saveIncr()
