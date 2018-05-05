"""
Demo script: Convert input file to a PDF
-----------------------------------------
Intended for multi-page input files like XPS, EPUB etc.

Features:
---------
Recovery of table of contents and links of input file.
While this works well for bookmarks (outlines, table of contents),
links will only work if they are not of type "LINK_NAMED".
This link type is skipped by the script.

For XPS and EPUB input, internal links however **are** of type "LINK_NAMED".
Base library MuPDF does not resolve them to page numbers.

So, for anyone expert enough to know the internal structure of these
document types, can further interpret and resolve these link types.

Dependencies
--------------
PyMuPDF v1.13.3
"""
import fitz
import sys
if not (list(map(int, fitz.VersionBind.split("."))) >= [1,13,3]):
    raise SystemExit("insufficient PyMuPDF version")
fn = sys.argv[1]
doc = fitz.open(fn)
print("Converting '%s' to '%s.pdf'" % (fn, fn))
b = doc.convertToPDF()            # convert to pdf
pdf = fitz.open("pdf", b)         # open as pdf

toc= doc.getToC()                 # table of contents of input
pdf.setToC(toc)                   # simply set it for output

# now process the links
link_cnti = 0
link_skip = 0
for pinput in doc:                # iterate through input pages
    links = pinput.getLinks()     # get list of links
    link_cnti += len(links)       # count how many
    pout = pdf[pinput.number]     # read corresp. output page
    for l in links:               # iterate though the links
        if l["kind"] == fitz.LINK_NAMED:    # we do not handle named links
            link_skip += 1        # count them
            continue
        pout.insertLink(l)        # simply output the others

# save the conversion result
pdf.save(fn + ".pdf", garbage=4, deflate=True)
# say how many named links we skipped
print("Skipped %i named links of a total of %i in input." % (link_skip, link_cnti))