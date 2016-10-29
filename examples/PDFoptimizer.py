#! python
from __future__ import print_function
import fitz
import sys, os, subprocess, tempfile, time
'''
Optimizes a PDF with FileOptimizer. But as "/Producer" and "/Creator" get
spoiled by this, we first save metadata and restore it after optimization.
This means we also accept non-compressed object definitions (as created by 
FileOptimizer).
'''
assert len(sys.argv) == 2, "need filename parameter"
fn = sys.argv[1]
assert fn.lower().endswith(".pdf"), "must be a PDF file"

fullname = os.path.abspath(fn)         # get the full path & name
t0 = time.clock()                      # save current time
doc = fitz.open(fullname)              # open PDF to save metadata
meta = doc.metadata
doc.close()

t1 = time.clock()                      # save current time again
subprocess.call(["fileoptimizer64", fullname])   # now invoke super optimizer
t2 = time.clock()                      # save current time again

cdir = os.path.split(fullname)[0]      # split dir from filename
fnout = tempfile.mkstemp(suffix = ".pdf", dir = cdir) # create temp pdf name 
doc = fitz.open(fullname)              # open now optimized PDF
doc.setMetadata(meta)                  # restore old metadata
doc.save(fnout[1], garbage = 4)        # save temp PDF with it, a little sub opt
doc.close()                            # close it

os.remove(fn)                          # remove super optimized file
os.close(fnout[0])                     # close temp file 
os.rename(fnout[1], fn)                # and rename it to original filename
t3 = time.clock()                      # save current time again

# put out runtime statistics
print("Timings:")
print(str(round(t1-t0, 4)).rjust(10), "save old metata")
print(str(round(t2-t1, 4)).rjust(10), "execute FileOptimizer")
print(str(round(t3-t2, 4)).rjust(10), "restore old metadata")