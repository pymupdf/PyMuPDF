#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@created: 2015-10-23 13:40:00

@author: Jorj X. McKie

Let the user select a PDF file and then scroll through it.

Dependencies:
PyMuPDF, wxPython 3.x, json, sqlite3

License:
 GNU GPL 3.x

Changes in PyMuPDF 1.8.0
------------------------
- display a fancy icon on the dialogs, defined as inline code in base64 format
- dynamically resize dialog to reflect each page's image size / orientation
- minor cosmetic changes

"""

import fitz
import wx
import os
from ParseTab import ParseTab
import itertools as it
from wx.lib.embeddedimage import PyEmbeddedImage
#==============================================================================
# The following data has been created by the wxPython tool img2py.py
# It contains SumatraPDF's icon (only for demonstration purposes) as a base64
# version (like PyMuPDF, SumatraPDF software is licensed under GNU GPL 3.x).
#==============================================================================
img = PyEmbeddedImage(
    "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")

# some abbreviations to get rid of those long pesky names ...
defPos = wx.DefaultPosition
defSiz = wx.DefaultSize

#==============================================================================
# Define our dialog as a subclass of wx.Dialog.
# Only special thing is, that we are being invoked with a filename ...
#==============================================================================
class PDFdisplay (wx.Dialog):

    def __init__(self, parent, filename):
        wx.Dialog.__init__ (self, parent, id = wx.ID_ANY,
            title = u"Parse Tables from ",
            pos = defPos, size = defSiz,
            style = wx.CAPTION|wx.CLOSE_BOX|wx.DEFAULT_DIALOG_STYLE)

        #======================================================================
        # display an icon top left of dialog, append filename to title
        #======================================================================
        self.SetIcon(img.GetIcon())
        self.SetTitle(self.Title + filename)
        self.set_rectangle = False
        #======================================================================
        # open the document with MuPDF when dialog gets created
        #======================================================================
        self.doc = fitz.Document(filename)

        #======================================================================
        # define zooming matrix for displaying PDF page images
        # we increase images by 20%, so take 1.2 as scale factors
        #======================================================================
        self.matrix = fitz.Matrix(1, 1).preScale(1.0, 1.0)
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
          +-> fields for controlling the rectangle
        +-> szr30 (sizer for columns)
          +-> button "New Column"
          +-> fields for controlling a column
          +-> button to extract selected table
        +-> PDF image area
        =======================================================================
        '''
        #======================================================================
        # the main sizer of the dialog
        #======================================================================
        szr10 = wx.BoxSizer(wx.VERTICAL)
        #======================================================================
        # this sizer will contain scrolling buttons, page numbers etc.
        #======================================================================
        szr20 = wx.BoxSizer(wx.HORIZONTAL)
        #======================================================================
        # this sizer will contain table column information
        #======================================================================
        szr30 = wx.BoxSizer(wx.HORIZONTAL)
        #======================================================================
        # forward button
        #======================================================================
        self.BtnNext = wx.Button(self, wx.ID_ANY, u"forw",
                           defPos, defSiz, wx.BU_EXACTFIT)
        #======================================================================
        # backward button
        #======================================================================
        self.BtnPrev = wx.Button(self, wx.ID_ANY, u"back",
                           defPos, defSiz, wx.BU_EXACTFIT)
        #======================================================================
        # text field for entering a target page. wx.TE_PROCESS_ENTER is
        # required to get data entry fired as events.
        #======================================================================
        self.TextToPage = wx.TextCtrl(self, wx.ID_ANY, u"1", defPos,
                             wx.Size(40, -1), wx.TE_PROCESS_ENTER)
        #======================================================================
        # displays total pages
        #======================================================================
        self.statPageMax = wx.StaticText(self, wx.ID_ANY,
                              str(self.doc.pageCount), defPos,
                              wx.Size(40, -1), 0)
        #======================================================================
        # activate rectangle drawing
        #======================================================================
        self.BtnRect = wx.Button(self, wx.ID_ANY, u"rect",
                           defPos, defSiz, wx.BU_EXACTFIT)
        #======================================================================
        # "Left" literal
        #======================================================================
        self.statLeft = wx.StaticText(self, wx.ID_ANY,
                              u"L:", defPos, wx.Size(15, -1), 0)
        #======================================================================
        # modify rectangle left
        #======================================================================
        self.CtrlLeft = wx.SpinCtrl( self, wx.ID_ANY, u"0", defPos,
                        wx.Size(50, -1), wx.SP_ARROW_KEYS, 0, 999, 0 )
        #======================================================================
        # "Top" literal
        #======================================================================
        self.statTop = wx.StaticText(self, wx.ID_ANY, u"T:", defPos,
                              wx.Size(15, -1), 0)
        #======================================================================
        # modify rectangle top
        #======================================================================
        self.CtrlTop = wx.SpinCtrl( self, wx.ID_ANY, u"0", defPos,
                        wx.Size(50, -1), wx.SP_ARROW_KEYS, 0, 999, 0 )
        #======================================================================
        # "Height" literal
        #======================================================================
        self.statHeight = wx.StaticText(self, wx.ID_ANY, u"H:", defPos,
                              wx.Size(15, -1), 0)
        #======================================================================
        # modify rectangle Height
        #======================================================================
        self.CtrlHeight = wx.SpinCtrl( self, wx.ID_ANY, u"0", defPos,
                        wx.Size(50, -1), wx.SP_ARROW_KEYS, 0, 999, 0 )
        #======================================================================
        # "Width" literal
        #======================================================================
        self.statWidth = wx.StaticText(self, wx.ID_ANY, u"W:", defPos,
                              wx.Size(15, -1), 0)
        #======================================================================
        # modify rectangle Width
        #======================================================================
        self.CtrlWidth = wx.SpinCtrl( self, wx.ID_ANY, u"0", defPos,
                        wx.Size(50, -1), wx.SP_ARROW_KEYS, 0, 999, 0 )
        #======================================================================
        # parse table within rectangle
        #======================================================================
        self.BtnMatrix = wx.Button(self, wx.ID_ANY, u"Get Table",
                           defPos, defSiz, wx.BU_EXACTFIT)
        #======================================================================
        # add a column
        #======================================================================
        self.BtnNewCol = wx.Button(self, wx.ID_ANY, u"New Col",
                           defPos, defSiz, wx.BU_EXACTFIT)
        self.col_coords = {}
        self.ColList = wx.Choice( self, wx.ID_ANY, defPos, defSiz,
                           [], 0 )
        self.CtrlCols = wx.SpinCtrl( self, wx.ID_ANY, u"0", defPos,
                           wx.Size(50, -1), wx.SP_ARROW_KEYS, 0, 999, 0)
        #======================================================================
        # sizers ready, compose them and add them to main sizer
        #======================================================================
        szr20.Add(self.BtnNext, 0, wx.ALL, 5)
        szr20.Add(self.BtnPrev, 0, wx.ALL, 5)
        szr20.Add(self.TextToPage, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Add(self.statPageMax, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Add(self.BtnRect, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Add(self.statLeft, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Add(self.CtrlLeft, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Add(self.statTop, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Add(self.CtrlTop, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Add(self.statHeight, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Add(self.CtrlHeight, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Add(self.statWidth, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Add(self.CtrlWidth, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Fit(self)
        szr10.Add(szr20, 0, wx.EXPAND, 5)

        #======================================================================
        # sizer szr30 ready, represents column information
        #======================================================================
        szr30.Add(self.BtnNewCol, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr30.Add(self.ColList, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr30.Add(self.CtrlCols, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr30.Add(self.BtnMatrix, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr30.Fit(self)
        szr10.Add(szr30, 0, wx.EXPAND, 5)

        #======================================================================
        # define the area for page images and load page 1 for display
        #======================================================================
        self.bitmap = self.pdf_show(1)
        self.PDFimage = wx.StaticBitmap(self, wx.ID_ANY, self.bitmap,
                           defPos, self.bitmap.Size, wx.NO_BORDER)
        szr10.Add(self.PDFimage, 0, wx.ALL, 0)

        #======================================================================
        # main sizer now ready - request final size & layout adjustments
        #======================================================================
        szr10.Fit(self)
        self.SetSizer(szr10)
        self.Layout()

        #======================================================================
        # center dialog on screen
        #======================================================================
        self.Centre(wx.BOTH)

        #======================================================================
        # Bind buttons and fields to event handlers
        #======================================================================
        self.BtnNewCol.Bind(wx.EVT_BUTTON, self.AddCol)
        self.BtnNext.Bind(wx.EVT_BUTTON, self.NextPage)
        self.BtnPrev.Bind(wx.EVT_BUTTON, self.PreviousPage)
        self.TextToPage.Bind(wx.EVT_TEXT_ENTER, self.GotoPage)
        self.BtnRect.Bind(wx.EVT_BUTTON, self.ActivateRect)
        self.BtnMatrix.Bind(wx.EVT_BUTTON, self.GetMatrix)
        self.CtrlTop.Bind( wx.EVT_SPINCTRL, self.UpdateRect)
        self.CtrlHeight.Bind( wx.EVT_SPINCTRL, self.UpdateRect )
        self.CtrlLeft.Bind( wx.EVT_SPINCTRL, self.UpdateRect )
        self.CtrlWidth.Bind( wx.EVT_SPINCTRL, self.UpdateRect )
        self.CtrlCols.Bind( wx.EVT_SPINCTRL, self.UpdateCol)
        self.ColList.Bind(wx.EVT_CHOICE, self.OnColSelect)
        self.PDFimage.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.PDFimage.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.PDFimage.Bind(wx.EVT_MOTION, self.OnMoving)
        self.disable_fields()

    def __del__(self):
        pass

#==============================================================================
# Event handlers and other subroutines
#==============================================================================
    def OnColSelect(self, evt):
        col = evt.GetString()
        self.CtrlCols.Value = self.col_coords[col]
        self.CtrlCols.Enable()
        self.col_selected = col

    def AddCol(self, evt):
        self.PDFimage.SetCursor(wx.StockCursor(wx.CURSOR_SIZENS))
        self.adding_column = True
        self.BtnNewCol.Enable()
        self.ColList.Enable()
        self.CtrlCols.Disable()
        self.col_selected = None
        return

    def disable_fields(self):
        self.CtrlHeight.Disable()
        self.CtrlTop.Disable()
        self.CtrlLeft.Disable()
        self.CtrlWidth.Disable()
        self.ColList.Disable()
        self.CtrlCols.Disable()
        self.BtnMatrix.Disable()
        self.BtnNewCol.Disable()
        self.col_coords = {}
        self.CtrlCols.Value = 0
        self.col_selected = None
        self.adding_column = False
        return

    def enable_fields(self):
        self.BtnMatrix.Enable()
        self.CtrlHeight.Enable()
        self.CtrlTop.Enable()
        self.CtrlLeft.Enable()
        self.CtrlWidth.Enable()
        return

    def OnLeftDown(self, evt):
        if self.set_rectangle:
            pos = evt.GetPosition()
            self.rect_x = pos.x
            self.rect_y = pos.y
            self.rect_w = 0
            self.rect_h = 0
            self.ColListChoices = []
            return
        elif not self.adding_column:
            return
        pos = evt.GetPosition()
        if pos.x >= self.rect_x + self.rect_w or\
           pos.x <= self.rect_x:
            return
        n = self.ColList.Count + 1
        col_name = "Col" + str(n)
        self.col_coords[col_name] = pos.x
        self.ColList.Append("Col" + str(n))
        self.CtrlCols.Value = pos.x
        self.adding_column = False
        self.DrawColumn(pos.x)
        self.PDFimage.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
        return

    def OnLeftUp(self, evt):
        if not self.set_rectangle:
            return
        pos = evt.GetPosition()
        self.rect_w = abs(pos.x - self.rect_x)
        self.rect_h = abs(pos.y - self.rect_y)
        if self.rect_x > pos.x:
            self.rect_x = pos.x
        if self.rect_y > pos.y:
            self.rect_y = pos.y
        self.enable_fields()
        self.PDFimage.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
        self.set_rectangle = False
        self.BtnNewCol.Enable()
        return

    def OnMoving(self, evt):
        if not evt.LeftIsDown():
            return
        if not self.set_rectangle:
            return
        pos = evt.GetPosition()
        tolerance = 2
        w = abs(pos.x - self.rect_x)
        h = abs(pos.y - self.rect_y)
        if not w > tolerance and h > tolerance:
            return
        x = self.rect_x
        if pos.x < x:
            x = pos.x
        y = self.rect_y
        if pos.y < y:
            y = pos.y
        self.CtrlHeight.Value = h
        self.CtrlWidth.Value  = w
        self.CtrlLeft.Value   = x
        self.CtrlTop.Value    = y
        self.DrawRect(x, y, w, h)
        return

    def UpdateCol(self, evt):
        if not self.col_selected:
            return
        v = self.CtrlCols.Value
        x = self.rect_x
        y = self.rect_y
        w = self.rect_w
        h = self.rect_h
        self.col_coords[self.col_selected] = v
        if v <= x or v >= x + w:
            self.UpdateRect(evt)
            self.ColList.SetFocus()
            return
        self.DrawRect(x, y, w, h)
        for k in self.col_coords:
            self.DrawColumn(self.col_coords[k])

    def DrawColumn(self, x):
        # draw a vertical line
        dc = wx.ClientDC(self.PDFimage)
        dc.SetPen(wx.Pen("RED"))
        dc.SetBrush(wx.Brush("RED", style=wx.BRUSHSTYLE_TRANSPARENT))
        dc.DrawLine(x, self.rect_y, x, self.rect_y + self.rect_h)

    def DrawRect(self, x, y, w, h):
        # Draw a rectangle
        dc = wx.ClientDC(self.PDFimage)
        dc.SetPen(wx.Pen("RED"))
        dc.SetBrush(wx.Brush("RED", style=wx.BRUSHSTYLE_TRANSPARENT))
        self.PDFimage.SetBitmap(self.bitmap)
        dc.DrawRectangle(x, y, w, h)

    def upd_collist(self):
        self.ColList.Clear()
        self.CtrlCols.Disable()
        vlist = self.col_coords.values()
        if not vlist:
            self.ColList.Disable()
            return
        self.ColList.Enable()
        self.col_coords = {}
        vlist.sort()
        i = 1
        for v in vlist:
            if v > self.rect_x and v < self.rect_x + self.rect_w:
                cname = "Col" + str(i)
                self.col_coords[cname] = v
                self.ColList.Append(cname)
                i += 1

    def UpdateRect(self, evt):
        # Update the rectangle
        x = self.CtrlLeft.Value
        y = self.CtrlTop.Value
        w = self.CtrlWidth.Value
        h = self.CtrlHeight.Value
        xmax = self.PDFimage.Size[0]
        ymax = self.PDFimage.Size[1]
        if not (x > 0 and (x + w) < xmax and y > 0 and (y + h) < ymax):
            return
        self.rect_x = x
        self.rect_y = y
        self.rect_h = h
        self.rect_w = w
        self.DrawRect(x, y, w, h)
        self.ColList.Clear()
        self.ColList.Disable()
        self.CtrlCols.Disable()
        self.CtrlCols.Value = 0
        self.col_selected = None
        self.upd_collist()
        for k in self.col_coords:
            self.DrawColumn(self.col_coords[k])

    def GetMatrix(self, evt):
        # parse table within rectangle
        # currently, the table is just stored away as a matrix:
        # add functionality as desired
        x0 = self.CtrlLeft.Value
        y0 = self.CtrlTop.Value
        x1 = x0 + self.CtrlWidth.Value
        y1 = y0 + self.CtrlHeight.Value
        cols = self.col_coords.values()
        if not cols:
            self.parsed_table = ParseTab(self.doc,
                                         int(self.TextToPage.Value) - 1,
                                         [x0, y0, x1, y1])
        else:
            cols.sort()
            self.parsed_table = ParseTab(self.doc,
                                         int(self.TextToPage.Value) - 1,
                                         [x0, y0, x1, y1],
                                         columns = cols)

    def ActivateRect(self, evt):
        # Draw a rectangle
        self.set_rectangle = True
        self.PDFimage.SetBitmap(self.bitmap)
        self.PDFimage.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        self.col_coords = {}
        self.CtrlCols.Value = 0
        self.BtnNewCol.Disable()
        self.CtrlCols.Disable()
        self.ColList.Disable()

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
        self.CtrlTop.Value    = 0
        self.CtrlLeft.Value   = 0
        self.CtrlHeight.Value = 0
        self.CtrlWidth.Value  = 0
        self.set_rectangle = False
        self.disable_fields()
        self.PDFimage.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
        self.bitmap = self.pdf_show(page)        # read page image
        self.PDFimage.SetSize(self.bitmap.Size)  # adjust screen to image size
        self.PDFimage.SetBitmap(self.bitmap)     # put it in screen
        return

    def pdf_show(self, pg_nr):
        page = self.doc.loadPage(int(pg_nr) - 1) # load the page & get Pixmap
        pix = page.getPixmap(matrix = self.matrix,
                             colorspace = 'RGB')
        a = str(pix.samples)                          # point to pixel area
        a2 = "".join([a[4*i:4*i+3] for i in range(len(a)/4)])
        bitmap = wx.BitmapFromBuffer(pix.width, pix.height, a2)
        return bitmap

#==============================================================================
# main program
#==============================================================================
# start the wx application
app = None
app = wx.App()
#==============================================================================
# Show a FileSelect dialog to choose a file
#==============================================================================

# Wildcard: offer all supported filetypes
wild = "supported files|*.pdf;*.xps;*.oxps;*.epub"

#==============================================================================
# define the file selection dialog
#==============================================================================
dlg = wx.FileDialog(None, message = "Choose a document",
                    defaultDir = os.path.expanduser("~"),
                    defaultFile = "",
                    wildcard = wild, style=wx.OPEN|wx.CHANGE_DIR)

#==============================================================================
# gimmick: provide an icon
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