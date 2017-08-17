import csv
import fitz
import argparse
'''
load a PDF TOC from CSV file contents
-------------------------------------
License: GNU GPL V3

!!! All existing outline entries (bookmarks) of the PDF will be replaced by this. !!!
Each CSV line must contain 3 or 4 entries:
lvl     A positive integer indicating the hierarchy level of the entry. First line must have lvl = 1.
        Hierarchy level of lines may increase by at most 1 but decrease by any number.

title   A string containing the entry's title. Must not be empty. 

page    An integer 1-based page number (1st page has number 1). Must be in PDF's page range. 

height  An optional positive number indicating the positioning of the entry on the page,
        given as points and counting from page bottom.
        If omitted, 36 points (half an inch) below top of page are taken.

Notes
-----
(1) Page numbers do not need to be in any particular order
(2) The PDF will be updated during the process
'''
parser = argparse.ArgumentParser(description="Enter CSV delimiter [;], CSV filename and PDF filename")
parser.add_argument('-d', help='CSV delimiter [;]', default = ';')
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
        try:
            p4 = float(row[3])
            toc.append([int(row[0]), row[1], int(row[2]), p4])
        except:
            toc.append([int(row[0]), row[1], int(row[2])])
doc.setToC(toc)
doc.saveIncr()
