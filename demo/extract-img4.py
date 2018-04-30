#! python
'''
This demo saves all images of any MuPDF-supported document referenced by pages.
Images are extracted from a page's DICT output, and then saved to disk.
To avoid duplicate image extractions, an MD5 hash value is computed.

Usage:
------
extract_img4.py input.file

'''
from __future__ import print_function
import fitz

import hashlib
import sys, time

assert len(sys.argv) == 2, 'Usage: %s <input file>' % sys.argv[0]
    
t0 = time.clock() if str is bytes else time.perf_counter()
doc = fitz.open(sys.argv[1])           # the PDF
imgcount = 0                           # counts extracted images
hash_list = []                         # records images already extracted

# display some file info
print("file: %s, pages: %i" % (sys.argv[1], len(doc)))

for page in doc:                  # cycle through the document's pages
    js = page.getText("dict")     # get a page's content in dict format
    blocks = js["blocks"]         # we are interested in the blocks
    j = 0                         # counts images per page

    for b in blocks:
        if b["type"] != 1:        # not an image block
            continue 
        fname = "p%i-%i." % (page.number, j)     # file names look like so
        j += 1                    # increase img number
        img = b["image"]          # img binary content
        hasher = hashlib.md5()    # avoud storing the same
        hasher.update(img)        # thing ...
        h = hasher.hexdigest()    # more than ...
        if h in hash_list:        # once.
            continue 
        hash_list.append(h)
        ext = b["ext"]            # extentsion indicates img type
        fout = open(fname + ext, "wb") # store in this file
        fout.write(img)
        fout.close()
        imgcount += 1             # count total images stored

t1 = time.clock() if str is bytes else time.perf_counter()
print("run time", round(t1-t0, 2))
print("extracted images", imgcount)