from __future__ import print_function
import fitz
import sys
assert len(sys.argv) == 2,"usage: python %s text.file" % (sys.argv[0],)
ifn = sys.argv[1]
ofn = ifn + ".pdf"           # name of PDF output
#------------------------------------------------------------------------------
# A very basic text-to-PDF converter.
#------------------------------------------------------------------------------
width = 595                  # these are DIN-A4
height = 842                 # portrait values
fontsz = 24
font = "Courier"             # choose a Base 14 font here
lineheight = fontsz * 1.2    # line height is 20% larger

# this gives the following lines per page:
nlines = int((height - 108.0) / lineheight + 0.5) - 1

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
doc.save(ofn, garbage=4, deflate=True)
doc.close()
    