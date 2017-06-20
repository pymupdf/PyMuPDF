#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Sun June 11 16:00:00 2017

@author: Jorj McKie
Copyright (c) 2017 Jorj X. McKie

The license of this program is governed by the GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007 or later.

Demonstrative program for the Python binding PyMuPDF of MuPDF.

Dependencies:
-------------
* PyMuPDF v1.11.0 (generation date 2017-06-14 or later)
* calendar (either use LocaleTextCalendar or just TextCalendar)

All Python and bitness versions are supported on Windows, MacOS and Linux.

This program creates calendars for three years in a row (starting with
the one given as parameter) and stores the result in a PDF.

'''
import fitz
import calendar
import sys
assert len(sys.argv) == 2, "need start year as the one and only parameter"
startyear = sys.argv[1]

assert startyear.isdigit(), "year must be positive numeric"
startyear = int(startyear)

assert startyear > 0, "year must be positive numeric"

# We use a nicer mono-spaced font than the PDF builtin 'Courier'.
# If you do not know one, set ffile to None and fname to 'Courier'
ffile = "c:/windows/fonts/dejavusansmono.ttf"
fname = "F0"

doc = fitz.open()
cal = calendar.LocaleTextCalendar(locale = "es") # use your locale
#cal = calendar.TextCalendar()                   # or stick with English

w, h = fitz.PaperSize("a4-l")          # get sizes for A4 landscape paper

txt = cal.formatyear(startyear, m = 4)
doc.insertPage(-1, txt, fontsize = 12, fontname = fname, fontfile = ffile,
               width = w, height = h)

txt = cal.formatyear(startyear + 1, m = 4)
doc.insertPage(-1, txt, fontsize = 12, fontname = fname, fontfile = ffile,
               width = w, height = h)

txt = cal.formatyear(startyear + 2, m = 4)
doc.insertPage(-1, txt, fontsize = 12, fontname = fname, fontfile = ffile,
               width = w, height = h)

doc.save(str(startyear) + ".pdf", garbage = 4, deflate = True)