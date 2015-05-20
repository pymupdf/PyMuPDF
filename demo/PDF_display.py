# -*- coding: utf-8 -*- 

import fitz
import wx
import wx.xrc
import sys
# define fitz context
ctx = fitz.Context(fitz.FZ_STORE_UNLIMITED)
#==============================================================================
# define the dialog
#==============================================================================
class PDFdispl (wx.Dialog):
    
    def __init__(self, parent):
        wx.Dialog.__init__ (self, parent, id = wx.ID_ANY,
            title = u"PDF Display with MuPDF",
            pos = wx.DefaultPosition, size = wx.DefaultSize,
            style = wx.CAPTION|
                    wx.CLOSE_BOX|
                    wx.DEFAULT_DIALOG_STYLE|
                    wx.DIALOG_NO_PARENT|
                    wx.MAXIMIZE_BOX|
                    wx.MINIMIZE_BOX|
                    wx.RESIZE_BORDER)
                
        szr10 = wx.BoxSizer(wx.VERTICAL)
        
        szr20 = wx.BoxSizer(wx.HORIZONTAL)
        
        self.bm = wx.EmptyBitmap(5, 5)        # bitmap to be shown at start
        
        self.btn_vor = wx.Button(self, wx.ID_ANY, u"forw",
                           wx.DefaultPosition, wx.DefaultSize, 0)
        szr20.Add(self.btn_vor, 0, wx.ALL, 5)
        
        self.btn_zur = wx.Button(self, wx.ID_ANY, u"back",
                           wx.DefaultPosition, wx.DefaultSize, 0)
        szr20.Add(self.btn_zur, 0, wx.ALL, 5)
        
        self.zuSeite = wx.TextCtrl(self, wx.ID_ANY,
                             u"0",            # pag# 0 to be clear it's a start 
                             wx.DefaultPosition, wx.DefaultSize,
                             wx.TE_PROCESS_ENTER)
        szr20.Add(self.zuSeite, 0, wx.ALL, 5)
        
        self.statSeiteMax = wx.StaticText(self, wx.ID_ANY,
                               str(seiten),    # show maxpages
                               wx.DefaultPosition, wx.DefaultSize, 0)
        self.statSeiteMax.Wrap(-1)
        szr20.Add(self.statSeiteMax, 0, wx.ALL, 5)
                
        szr10.Add(szr20, 0, wx.EXPAND, 5)
        # this contains the PDF pages
        self.PDFbild = wx.StaticBitmap(self, wx.ID_ANY, self.bm,
                           wx.DefaultPosition, wx.Size(600, 800), wx.NO_BORDER)
        szr10.Add(self.PDFbild, 0, wx.ALL, 0)
                
        self.SetSizer(szr10)
        self.Layout()
        szr10.Fit(self)
        
        self.Centre(wx.BOTH)
        
        # Bind buttons and fields to event handlers
        self.btn_vor.Bind(wx.EVT_BUTTON, self.Seitevor)
        self.btn_zur.Bind(wx.EVT_BUTTON, self.Seitezur)
        self.zuSeite.Bind(wx.EVT_TEXT_ENTER, self.SeiteZiel)
    
    def __del__(self):
        pass

#==============================================================================
# Button Handlers
#==============================================================================
    def Seitevor(self, event):                 # means: page forward
        seite = int(self.zuSeite.Value) + 1    # current page + 1
        if seite > seiten:                     # cannot go beyond last page
            seite = seiten
        self.zuSeite.Value = str(seite)        # put target page# in screen
        self.bm = pdf_show(doc, seite)         # get page image 
        self.PDFbild.SetBitmap(self.bm)        # put it in screen
        self.PDFbild.Refresh(True)             # refresh the image
        self.Layout()                          # refresh the layout  
        event.Skip()
    
    def Seitezur(self, event):                 # means: page back
        seite = int(self.zuSeite.Value) - 1    # current page - 1
        if seite < 1:                          # cannot go before page 1
            seite = 1               
        self.zuSeite.Value = str(seite)        # put target page# in screen 
        self.bm = pdf_show(doc, seite)         # get page image 
        self.PDFbild.SetBitmap(self.bm)        # put it in screen
        self.PDFbild.Refresh(True)             # refresh the image
        self.Layout()                          # refresh the layout
        event.Skip()
    
    def SeiteZiel(self, event):                # means: go to page #
        seite = int(self.zuSeite.Value)        # get page# from screen
        if seite > seiten:                     # must be:
            seite = seiten                     # 0 < page# <= maxpages (seiten)
        if seite < 1:
            seite = 1
        self.zuSeite.Value = str(seite)        # make sure it's on the screen
        self.bm = pdf_show(doc, seite)         # read page image
        self.PDFbild.SetBitmap(self.bm)        # put it in screen
        self.PDFbild.Refresh(True)             # refresh the image
        self.Layout()                          # and the layout
        event.Skip()
    
#==============================================================================
# Read / render a PDF page. Parameters are: pdf = document, seite = page#
#==============================================================================
def pdf_show(pdf, seite):
    page = pdf.load_page(seite - 1)            # load the page
    rect = page.bound_page()                   # rectangle representing it
    width = int(rect.get_width())              # width in pixels
    height = int(rect.get_height())            # height in pixels
    # create an empty RGB pixmap of this size
    pix = ctx.new_pixmap(fitz.fz_device_rgb, width, height)
    pix.clear_pixmap(255)                      # clear it with color "white"
    dev = pix.new_draw_device()                # create a "draw" device
    page.run_page(dev, fitz.fz_identity, None) # render the page
    data = pix.get_samples()                   # point to pixel area
    bm = wx.BitmapFromBufferRGBA(width, height, data)  # turn in wx.Bitmap
    return bm

    
#==============================================================================
# Hauptprogramm
#==============================================================================
# PDF filename goes here
f = sys.argv[1] 
# open it with fitz
doc = ctx.open_document(f)
# get # of pages (maxpages)
seiten = doc.count_pages()
# prepare the dialog application
app = None
app = wx.App()
# create the dialog
dlg = PDFdispl(None)
# show it - only return for final housekeeping
rc = dlg.ShowModal()
