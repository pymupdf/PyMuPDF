#!/usr/bin/env python
import fitz
f="test.pdf"
d = fitz.Document(f)
seiten = d.pageCount

for seite in range(10,seiten):
    print "=============== processing page", seite, " ==============="
    pg = d.loadPage(seite)
    dl = fitz.DisplayList()
    print "ok: dl = fitz.DisplayList()"
    dv = fitz.Device(dl)
    print "ok: dv = fitz.Device(dl)"
    pg.run(dv, fitz.Identity)
    print "ok: pg.run(dv, fitz.Identity)"
    ts = fitz.TextSheet()
    print "ok: ts = fitz.TextSheet()"
    tp = fitz.TextPage()
    print "ok: tp = fitz.TextPage()"
    rect = pg.bound()
    dl.run(fitz.Device(ts, tp), fitz.Identity, rect)
    print "ok: dl.run(fitz.Device(ts, tp), fitz.Identity, rect)"
