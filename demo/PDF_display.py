#!/usr/bin/env python2

import fitz
import wx
import wx.xrc
import sys
#==============================================================================
# define the dialog
#==============================================================================
class PDFdisplay (wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__ (self, parent,
            id = wx.ID_ANY,
            title = u"PDF Display with MuPDF",
            pos = wx.DefaultPosition,
            size = wx.DefaultSize,
            style = wx.CAPTION|
                    wx.CLOSE_BOX|
                    wx.DEFAULT_DIALOG_STYLE|
                    wx.DIALOG_NO_PARENT|
                    wx.MAXIMIZE_BOX|
                    wx.MINIMIZE_BOX|
                    wx.RESIZE_BORDER)

        szr10 = wx.BoxSizer(wx.VERTICAL) # sorry, cryptic variable name

        szr20 = wx.BoxSizer(wx.HORIZONTAL) # cryptic variable name

        self.bitmap = wx.EmptyBitmap(5, 5)        # bitmap to be shown at start

        self.button_next = wx.Button(self, wx.ID_ANY, u"forw",
                           wx.DefaultPosition, wx.DefaultSize, 0)
        szr20.Add(self.button_next, 0, wx.ALL, 5)

        self.button_previous = wx.Button(self, wx.ID_ANY, u"back",
                           wx.DefaultPosition, wx.DefaultSize, 0)
        szr20.Add(self.button_previous, 0, wx.ALL, 5)

        self.button_topage = wx.TextCtrl(self, wx.ID_ANY,
                             u"0",            # pag# 0 to be clear it's a start
                             wx.DefaultPosition, wx.DefaultSize,
                             wx.TE_PROCESS_ENTER)
        szr20.Add(self.button_topage, 0, wx.ALL, 5)

        self.statPageMax = wx.StaticText(self, wx.ID_ANY,
                               str(total_pages),    # show maxpages
                               wx.DefaultPosition, wx.DefaultSize, 0)
        self.statPageMax.Wrap(-1)
        szr20.Add(self.statPageMax, 0, wx.ALL, 5)

        szr10.Add(szr20, 0, wx.EXPAND, 5)
        # this contains the PDF pages
        self.PDFimage = wx.StaticBitmap(self, wx.ID_ANY, self.bitmap,
                           wx.DefaultPosition, wx.Size(600, 800), wx.NO_BORDER)
        szr10.Add(self.PDFimage, 0, wx.ALL, 0)

        self.SetSizer(szr10)
        self.Layout()
        szr10.Fit(self)

        self.Centre(wx.BOTH)

        # Bind buttons and fields to event handlers
        self.button_next.Bind(wx.EVT_BUTTON, self.NextPage)
        self.button_previous.Bind(wx.EVT_BUTTON, self.PreviousPage)
        self.button_topage.Bind(wx.EVT_TEXT_ENTER, self.GotoPage)

    def __del__(self):
        pass

#==============================================================================
# Button handlers
#==============================================================================
    def NextPage(self, event):                 # means: page forward
        page = int(self.button_topage.Value) + 1    # current page + 1
        page = min(page, total_pages)             # cannot go beyond last page
        self.button_topage.Value = str(page)        # put target page# in screen
        self.bitmap = pdf_show(doc, page)         # get page image
        self.PDFimage.SetBitmap(self.bitmap)        # put it in screen
        self.PDFimage.Refresh(True)             # refresh the image
        self.Layout()                          # refresh the layout
        event.Skip()

    def PreviousPage(self, event):                 # means: page back
        page = int(self.button_topage.Value) - 1    # current page - 1
        page = max(page, 1)                  # cannot go before page 1
        self.button_topage.Value = str(page)        # put target page# in screen
        self.bitmap = pdf_show(doc, page)         # get page image
        self.PDFimage.SetBitmap(self.bitmap)        # put it in screen
        self.PDFimage.Refresh(True)             # refresh the image
        self.Layout()                          # refresh the layout
        event.Skip()

    def GotoPage(self, event):                # means: go to page #
        page = int(self.button_topage.Value)        # get page# from screen
        page = min(page, total_pages)             # cannot go beyond last page
        page = max(page, 1)                  # cannot go before page 1
        self.button_topage.Value = str(page)        # make sure it's on the screen
        self.bitmap = pdf_show(doc, page)         # read page image
        self.PDFimage.SetBitmap(self.bitmap)        # put it in screen
        self.PDFimage.Refresh(True)             # refresh the image
        self.Layout()                          # and the layout
        event.Skip()

#==============================================================================
# Read / render a PDF page. Parameters are: pdf = document, page = page#
#==============================================================================
def pdf_show(pdf, page):
    page = pdf.loadPage(page - 1)                           # load the page
    irect = page.bound().round()                            # integer rectangle representing it
    pix = fitz.Pixmap(fitz.Colorspace(fitz.CS_RGB), irect)  # create an empty RGB pixmap of this size
    pix.clearWith(255)                                      # clear it with color "white"
    dev = fitz.Device(pix)                                  # create a "draw" device
    page.run(dev, fitz.Identity)                            # render the page
    data = pix.samples                                      # point to pixel area

    bitmap = wx.BitmapFromBufferRGBA(irect.width, irect.height, data)  # turn in wx.Bitmap
    # If you experience issues with this function, try the following code.
    # It will use "wx.BitmapFromBuffer" and thus ignore the transparency (alpha).
    # data2 = "".join([data[4*i:4*i+3] for i in range(len(data)/4)])
    # bitmap = wx.BitmapFromBuffer(width, height, data2)
    return bitmap


#==============================================================================
# main program
#==============================================================================
# PDF filename goes here
f = sys.argv[1]
# open it with fitz
doc = fitz.Document(f)
# get # of pages (maxpages)
total_pages = doc.pageCount
# prepare the dialog application
app = None
app = wx.App()
# create the dialog
dlg = PDFdisplay(None)
# show it - only return for final housekeeping
rc = dlg.ShowModal()
