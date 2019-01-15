from __future__ import print_function
import numpy as np
import PIL
from PIL import Image
import fitz
import sys, time
print("Python:", sys.version)
print("NumPy version", np.__version__)
print(fitz.__doc__)
print("PIL version", PIL.PILLOW_VERSION)
'''
==============================================================================
Create any height*width*3 RGB pixel area using numpy and then use fitz to
save it as a PNG image.
This is 10+ times faster than saving with pure python solutions like
pypng and almost 2 times faster than saving with PIL.
However, PIL images are smaller than those of MuPDF.
==============================================================================

Changes
-------------------
[v1.10.0] do not use alpha channel to save 25% image memory
[v1.13.0] include PIL output for comparison timings

'''
height = 2048            # choose whatever you want here; image will consist
width  = 2028            # of 256 x 256 sized tiles, each colored as follows

image = np.ndarray((height, width, 3), dtype=np.uint8)

for i in range(height):
    for j in range(width):
        # colorize the 3 components as you like it
        image[i, j] = np.array([i % 256, j % 256, (i + j) % 256], dtype=np.uint8)
        
# create string / bytes object from the array and output the picture
samples = image.tostring()

ttab = [(time.perf_counter(), "")]

pix = fitz.Pixmap(fitz.csRGB, width, height, samples, 0)
pix.writePNG("numpy2fitz.png")
ttab.append((time.perf_counter(), "fitz"))

pix = Image.frombuffer("RGB", [width, height], samples,
                       "raw", "RGB", 0, 1)
pix.save("numpy2PIL.png")
ttab.append((time.perf_counter(), "PIL"))

for i, t in enumerate(ttab):
    if i > 0: print("storing with %s: %g sec." % (t[1], t[0] - ttab[i-1][0]))
