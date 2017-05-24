from __future__ import print_function
import fitz
import sys
assert len(sys.argv) == 2,"usage: python %s text.file" % (sys.argv[0],)
ifn = sys.argv[1]
ofn = ifn + ".pdf"           # name of PDF output
"""
------------------------------------------------------------------------------
A very basic text-to-PDF converter.
-------------------------------------
Some text file.xxx will be converted to text.xxx.pdf
Adjust preferred page format, fontsize and possibly fontname below.
Formula of lines per page (nlines) is also used by the 'insertPage' method.
------------------------------------------------------------------------------
"""
width = 595                  # these are DIN-A4
height = 842                 # portrait values
fontsz = 9
font = "Courier"             # choose a Base 14 font here
lineheight = fontsz * 1.2    # line height is 20% larger

# this gives the following lines per page:
nlines = int((height - 108.0) / lineheight)

sourcefile = open(ifn)       # we are going to convert this file
line_ctr = 0
total_ctr = 0
out_buf = ""

doc = fitz.open()            # new empty PDF

def page_out(b):
    doc.insertPage(-1, fontsize = fontsz, text = b, fontname = font,
                   width = width, height = height)
    
while 1:
    line = sourcefile.readline()
    if line == "": break
    out_buf += line
    line_ctr += 1
    total_ctr += 1
    if line_ctr == nlines:
        page_out(out_buf)
        out_buf = ""
        line_ctr = 0

if len(out_buf) > 0:
    page_out(out_buf)

print("Statistics for PDF conversion of", ifn)
print(total_ctr, "lines written,", nlines, "lines per page.")
print(ofn, "contains", len(doc), "pages.")

# for convenience, we insert a header on each page and fill in
# some metadata
txt = "Content of file '%s' - page %i of %i"
for page in doc:
    page.insertText(fitz.Point(50, 50),
                    txt % (ifn, page.number +1, len(doc)),
                    color = (0,0,1),        # this is blue
                    fontsize = 16)
m = {"creationDate": fitz.getPDFnow(),      # current timestamp
     "modDate": fitz.getPDFnow(),           # current timestamp
     "creator": "text2pdf.py",
     "producer": "PyMuPDF v1.11.0",
     "title": "Content of file " + ifn,
     "subject": "Demonstrate the use of methods insertPage and insertText",
     "author": "Jorj McKie"}
doc.setMetadata(m)
doc.save(ofn, garbage=4, deflate=True)
doc.close()
    