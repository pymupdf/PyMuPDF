#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@created: 2015-10-23 13:40:00

@author: Jorj X. McKie

Let the user select a Python file and then scroll through it.

Dependencies:
PyMuPDF, wxPython 3.x

License:
 GNU GPL 3.x

Changes in PyMuPDF 1.8.0
------------------------
- display a fancy icon on the dialogs, defined as inline code in base64 format
- display PDF pages with a zoom factor of 120%
- dynamically resize dialog to reflect each page's image size / orientation
- minor cosmetic changes
- adjust the scaling matrix in function pdf_show as you like it.
"""

import fitz
import wx
import os
from wx.lib.embeddedimage import PyEmbeddedImage
#==============================================================================
# The following data has been created by the wxPython tool img2py.py
# It contains SumatraPDF's icon (only for demonstration purposes) as a base64
# version (like PyMuPDF, SumatraPDF software is licensed under GNU GPL 3.x).
#==============================================================================
img = PyEmbeddedImage(
    "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")

# first abbreviations to get rid of those long pesky names ...
defPos = wx.DefaultPosition
defSiz = wx.DefaultSize

#==============================================================================
# Define our dialog as a subclass of wx.Dialog.
# Only special thing is, that we are being invoked with a filename ...
#==============================================================================
class PDFdisplay (wx.Dialog):

    def __init__(self, parent, filename):
        wx.Dialog.__init__ (self, parent, id = wx.ID_ANY,
            title = u"PDF Display with PyMuPDF: ",
            pos = defPos, size = defSiz,
            style = wx.CAPTION|wx.CLOSE_BOX|wx.DEFAULT_DIALOG_STYLE|
                    wx.DIALOG_NO_PARENT|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|
                    wx.RESIZE_BORDER)

        #======================================================================
        # display an icon top left of dialog, append filename to title
        #======================================================================
        self.SetIcon(img.GetIcon())
        self.SetTitle(self.Title + filename)

        #======================================================================
        # open the document with MuPDF when dialog gets created
        #======================================================================
        self.doc = fitz.Document(filename)

        #======================================================================
        # define zooming matrix for displaying PDF page images
        # we increase images by 20%, so take 1.2 as scale factors
        #======================================================================
        self.matrix = fitz.Matrix(1, 1).preScale(1.2, 1.2)

        '''
        =======================================================================
        Overall Dialog Structure:
        -------------------------
        szr10 (main sizer for the whole dialog - vertical orientation)
        +-> szr20 (sizer for buttons etc. - horizontal orientation)
          +-> button forward
          +-> button backward
          +-> field for page number to jump to
          +-> field displaying total pages
        +-> PDF image area
        =======================================================================
        '''

        #======================================================================
        # the main sizer of the dialog
        #======================================================================
        self.szr10 = wx.BoxSizer(wx.VERTICAL)

        #======================================================================
        # this sizer will contain scrolling buttons, page numbers etc.
        #======================================================================
        szr20 = wx.BoxSizer(wx.HORIZONTAL)

        #======================================================================
        # forward button
        #======================================================================
        self.ButtonNext = wx.Button(self, wx.ID_ANY, u"forw",
                           defPos, defSiz, 0)
        szr20.Add(self.ButtonNext, 0, wx.ALL, 5)

        #======================================================================
        # backward button
        #======================================================================
        self.ButtonPrevious = wx.Button(self, wx.ID_ANY, u"back",
                           defPos, defSiz, 0)
        szr20.Add(self.ButtonPrevious, 0, wx.ALL, 5)

        #======================================================================
        # text field for entering a target page. wx.TE_PROCESS_ENTER is
        # required to get data entry fired as events.
        #======================================================================
        self.TextToPage = wx.TextCtrl(self, wx.ID_ANY, u"1", defPos, defSiz,
                             wx.TE_PROCESS_ENTER)
        szr20.Add(self.TextToPage, 0, wx.ALL, 5)

        #======================================================================
        # displays total pages
        #======================================================================
        self.statPageMax = wx.StaticText(self, wx.ID_ANY,
                              str(self.doc.pageCount), defPos, defSiz, 0)
        szr20.Add(self.statPageMax, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        #======================================================================
        # sizer ready, represents top dialog line
        #======================================================================
        self.szr10.Add(szr20, 0, wx.EXPAND, 5)

        #======================================================================
        # define the area for page images and load page 1 for primary display
        #======================================================================
        self.PDFimage = wx.StaticBitmap(self, wx.ID_ANY, self.pdf_show(1),
                           defPos, defSiz, wx.NO_BORDER)
        self.szr10.Add(self.PDFimage, 0, wx.ALL, 0)

        #======================================================================
        # main sizer now ready - request final size & layout adjustments
        #======================================================================
        self.szr10.Fit(self)
        self.SetSizer(self.szr10)
        self.Layout()

        #======================================================================
        # center dialog on screen
        #======================================================================
        self.Centre(wx.BOTH)

        #======================================================================
        # Bind buttons and fields to event handlers
        #======================================================================
        self.ButtonNext.Bind(wx.EVT_BUTTON, self.NextPage)
        self.ButtonPrevious.Bind(wx.EVT_BUTTON, self.PreviousPage)
        self.TextToPage.Bind(wx.EVT_TEXT_ENTER, self.GotoPage)

    def __del__(self):
        pass

#==============================================================================
# Button handlers
#==============================================================================
    def NextPage(self, event):                   # means: page forward
        page = int(self.TextToPage.Value) + 1    # current page + 1
        page = min(page, self.doc.pageCount)     # cannot go beyond last page
        self.TextToPage.Value = str(page)        # put target page# in screen
        self.bitmap = self.pdf_show(page)        # get page image
        self.NeuesImage(page)                    # refresh the layout
        event.Skip()

    def PreviousPage(self, event):               # means: page back
        page = int(self.TextToPage.Value) - 1    # current page - 1
        page = max(page, 1)                      # cannot go before page 1
        self.TextToPage.Value = str(page)        # put target page# in screen
        self.NeuesImage(page)
        event.Skip()

    def GotoPage(self, event):                   # means: go to page number
        page = int(self.TextToPage.Value)        # get page# from screen
        page = min(page, self.doc.pageCount)     # cannot go beyond last page
        page = max(page, 1)                      # cannot go before page 1
        self.TextToPage.Value = str(page)        # make sure it's on the screen
        self.NeuesImage(page)
        event.Skip()

#==============================================================================
# Read / render a PDF page. Parameters are: pdf = document, page = page#
#==============================================================================
    def NeuesImage(self, page):
        self.bitmap = self.pdf_show(page)        # read page image
        self.PDFimage.SetSize(self.bitmap.Size)  # adjust screen to image size
        self.PDFimage.SetBitmap(self.bitmap)     # put it in screen
        self.PDFimage.Refresh(True)              # refresh the image
        self.szr10.Fit(self)
        self.Layout()                            # and the layout
        return

    def pdf_show(self, pg_nr):
        page = self.doc.loadPage(int(pg_nr) - 1) # load the page & get Pixmap
        pix = page.getPixmap(matrix = self.matrix,
                             colorspace = 'RGB')
        data = str(pix.samples)                  # point to pixel area

        #bitmap = wx.BitmapFromBufferRGBA(pix.width, pix.height, data)

        # If you experience issues with this function, try the following code.
        # It will use "wx.BitmapFromBuffer" and thus ignore the transparency (alpha).
        data2 = "".join([data[4*i:4*i+3] for i in range(len(data)/4)])
        bitmap = wx.BitmapFromBuffer(pix.width, pix.height, data2)

        return bitmap

#==============================================================================
# main program
#==============================================================================
# start the wx application
app = wx.App()
#==============================================================================
# Show a FileSelect dialog to choose a file for display
#==============================================================================

# Wildcard: offer all supported filetypes for display
wild = "supported files|*.pdf;*.xps;*.oxps;*.epub"

#==============================================================================
# define the file selection dialog
#==============================================================================
dlg = wx.FileDialog(None, message = "Choose a file to display",
                    defaultDir = os.path.expanduser("~"),
                    defaultFile = "",
                    wildcard = wild, style=wx.OPEN|wx.CHANGE_DIR)

#==============================================================================
# give an icon before we display it
#==============================================================================
dlg.SetIcon(img.GetIcon())

#==============================================================================
# now display and ask for return code in one go
#==============================================================================
# We got a file only when one was selected and OK pressed
if dlg.ShowModal() == wx.ID_OK:
    # This returns a Python list of selected files (we only have one though)
    filename = dlg.GetPaths()[0]
else:
    filename = None

# destroy this dialog
dlg.Destroy()

if filename:
    if not os.path.exists(filename):   # should not happen actually
        filename = None
#==============================================================================
# only continue if we have a filename
#==============================================================================
if filename:
    # create the dialog
    dlg = PDFdisplay(None, filename)
    # show it - this will only return for final housekeeping
    rc = dlg.ShowModal()
app = None