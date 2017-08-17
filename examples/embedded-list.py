from __future__ import print_function
import sys
import fitz
#------------------------------------------------------------------------------
# Example script
# License: GNU GPL V3
# List embedded files of a PDF
# Invocation line:
# python embedded-list.py in.pf
# 
# Example output:
# -----------------------------------------------------------------
# Name          Filename      Description         Length       Size
# -----------------------------------------------------------------
# pdftest       pdftest       pdftest                609        460
# testann.py    testann.py    Beschreibung          1222        577
# pdftest1      pdftest       none                     1          1
# minpdf.py     minpdf.py     minpdf.py             1693       1101
# -----------------------------------------------------------------
# 4 embedded files in 'in.pdf'. Totals:
# File length: 3525, compressed: 2139, ratio: 0.61% (savings: 0.39%).
# -----------------------------------------------------------------
#------------------------------------------------------------------------------

def char_repl(x):
    """A little embarrassing: couldn't figure out how to avoid crashes when
    hardcore unicode occurs in description fields ..."""
    r = ""
    for c in x:
        if ord(c) > 255:
            r += "?"
        else:
            r += c
    return r
    
fn = sys.argv[1]
doc = fitz.open(fn)                    # oprn input

desc_len = name_len = fname_len = 0    # some fields of interest
tlength = tsize = 0                    # total length and compressed sizes

ef_list = []  # store file infos here, because I wanted
# to adjust column widths of the report to actually occurring data ...
# Of yourse, a direct print is perfectly possible.

for i in range(doc.embeddedFileCount): # number of embedded files
    info = doc.embeddedFileInfo(i)     # get one info dict
    ef = (info["name"], info["file"], char_repl(info["desc"]),
          info["length"], info["size"])
    ef_list.append(ef)                 # save in the info list
    name_len = max(len(ef[0]), name_len)    # column width of 'name'
    desc_len = max(len(ef[2]), desc_len)    # column width of 'desc'
    fname_len = max(len(ef[1]), fname_len)  # column width of 'filename' 
    tlength += ef[4]                        # add to total orignal file size
    tsize += ef[3]                          # add to total compressed file size
    
if len(ef_list) < 1:                        # are we being fooled?
    print("no embedded files in", fn)
    exit(1)

ratio = float(tsize)/ tlength          # compression ration
saves = 1 - ratio                      # savings percentage
# define header line
header = "Name".ljust(name_len+4) + "Filename".ljust(fname_len+4) +\
      "Description".ljust(desc_len+4) + "Length".rjust(10) + "Size".rjust(11)
line = "-".ljust(len(header), "-")     # horizontal line
print(line)                            # print header
print(header)                          # ... 
print(line)                            # ...
# now print each file info ...
for info in ef_list:
    print(info[0].ljust(name_len+3), info[1].ljust(fname_len+3),
          info[2].ljust(desc_len+3), str(info[3]).rjust(10),
          str(info[4]).rjust(10))
# print some wrap up information
print(line)
print(len(ef_list), "embedded files in '%s'. Totals:" % (fn,))
print("File lengths: %s, compressed: %s, ratio: %s%% (savings: %s%%)." % (tlength,
      tsize, str(round(ratio*100, 2)), str(round(saves*100, 2))))
print(line)