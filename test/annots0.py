#! python
from __future__ import print_function
import fitz

datei = "test.pdf"
doc = fitz.open(datei)
p0 = doc[0]
a = p0.firstAnnot
da = dir(a)
i=0
while a:
    print("=".ljust(80,"="))
    for x in da:
        if x.startswith("_") or x in ["next", "super", "this", "page", "getPixmap"]:
            continue
        s = "a." + x
        print (x.ljust(12), "====>", eval(s))
    pix = a.getPixmap()
    pix.writePNG("a-%s.png" % (i,))
    i += 1
    a = a.next
