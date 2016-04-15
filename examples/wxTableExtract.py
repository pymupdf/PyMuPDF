#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@created: 2016-04-07 07:00:00

@author: Jorj X. McKie

Display and parse tables of a document.

Dependencies:
PyMuPDF, wxPython 3.x, json, sqlite3

License:
 GNU GPL V3

"""
from __future__ import print_function
import fitz
import wx
import os
from ParseTab import ParseTab
from PageFormat import PageFormat
from wx.lib.embeddedimage import PyEmbeddedImage
#==============================================================================
# The following data has been created by the wxPython tool img2py.py
# It contains SumatraPDF's icon (only for demonstration purposes) as a base64
# version (like PyMuPDF, SumatraPDF software is licensed under GNU GPL V3).
#==============================================================================
img = PyEmbeddedImage(
    "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")

def getint(v):
    import types
    # extract digits from a string to form an integer
    try:
        return int(v)
    except ValueError:
        pass
    a = "0"
    if not isinstance(v, types.StringTypes):
        return a
    for d in v:
        if d in "0123456789":
            a += d
    return int(a)

# some abbreviations to get rid of those long pesky names ...
defPos = wx.DefaultPosition
defSiz = wx.DefaultSize
khaki  = wx.Colour(240, 230, 140)
#==============================================================================
# Define our dialog as a subclass of wx.Dialog.
# Only special thing is, that we are being invoked with a filename ...
#==============================================================================
class PDFdisplay (wx.Dialog):

    def __init__(self, parent, filename):
        wx.Dialog.__init__ (self, parent, id = wx.ID_ANY,
            title = u"Parse Tables in ",
            pos = defPos, size = defSiz,
            style = wx.CAPTION|wx.CLOSE_BOX|wx.DEFAULT_DIALOG_STYLE)

        #======================================================================
        # display an icon top left of dialog, append filename to title
        #======================================================================
        self.SetIcon(img.GetIcon())
        self.SetBackgroundColour(khaki)
        self.SetTitle(self.Title + filename)
        self.set_rectangle = False
        self.cursor_hand  = wx.StockCursor(wx.CURSOR_CLOSED_HAND)
        self.cursor_cross = wx.StockCursor(wx.CURSOR_CROSS)
        self.cursor_vert  = wx.StockCursor(wx.CURSOR_SIZENS)
        self.cursor_norm  = wx.StockCursor(wx.CURSOR_DEFAULT)

        #======================================================================
        # open the document with MuPDF when dialog gets created
        #======================================================================
        self.doc = fitz.Document(filename)
        if self.doc.needsPass:
            self.decrypt_doc()
        if self.doc.isEncrypted:
            self.Destroy()
            return
        #======================================================================
        # forward button
        #======================================================================
        self.BtnNext = wx.Button(self, wx.ID_ANY, u"Forward",
                           defPos, defSiz, wx.BU_EXACTFIT)
        #======================================================================
        # backward button
        #======================================================================
        self.BtnPrev = wx.Button(self, wx.ID_ANY, u"Backward",
                           defPos, defSiz, wx.BU_EXACTFIT)
        #======================================================================
        # text field for entering a target page. wx.TE_PROCESS_ENTER is
        # required to get data entry fired as events.
        #======================================================================
        self.TextToPage = wx.TextCtrl(self, wx.ID_ANY, u"1", defPos,
                             wx.Size(40, -1), wx.TE_PROCESS_ENTER|wx.TE_RIGHT)
        #======================================================================
        # displays total pages
        #======================================================================
        self.statPageMax = wx.StaticText(self, wx.ID_ANY,
                              "of " + str(self.doc.pageCount) + " pages.",
                              defPos, defSiz, 0)
        #======================================================================
        # displays page format
        #======================================================================
        self.paperform = wx.StaticText(self, wx.ID_ANY,
                              "", defPos, defSiz, 0)
        #======================================================================
        # activate rectangle drawing
        #======================================================================
        self.BtnRect = wx.Button(self, wx.ID_ANY, u"New Rect",
                           defPos, defSiz, wx.BU_EXACTFIT)
        #======================================================================
        # "Left" literal
        #======================================================================
        self.statLeft = wx.StaticText(self, wx.ID_ANY,
                              u"Left:", defPos, wx.Size(50, -1), 0)
        #======================================================================
        # modify rectangle left
        #======================================================================
        self.CtrlLeft = wx.SpinCtrl( self, wx.ID_ANY, u"0", defPos,
                        wx.Size(50, -1),
                        wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER, 0, 999, 0 )
        #======================================================================
        # "Top" literal
        #======================================================================
        self.statTop = wx.StaticText(self, wx.ID_ANY, u"Top:", defPos,
                              wx.Size(50, -1), 0)
        #======================================================================
        # modify rectangle top
        #======================================================================
        self.CtrlTop = wx.SpinCtrl( self, wx.ID_ANY, u"0", defPos,
                        wx.Size(50, -1),
                        wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER, 0, 999, 0 )
        #======================================================================
        # "Height" literal
        #======================================================================
        self.statHeight = wx.StaticText(self, wx.ID_ANY, u"Height:", defPos,
                              wx.Size(50, -1), 0)
        #======================================================================
        # modify rectangle Height
        #======================================================================
        self.CtrlHeight = wx.SpinCtrl( self, wx.ID_ANY, u"0", defPos,
                        wx.Size(50, -1),
                        wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER, 0, 999, 0 )
        #======================================================================
        # "Width" literal
        #======================================================================
        self.statWidth = wx.StaticText(self, wx.ID_ANY, u"Width:", defPos,
                              wx.Size(50, -1), 0)
        #======================================================================
        # modify rectangle Width
        #======================================================================
        self.CtrlWidth = wx.SpinCtrl( self, wx.ID_ANY, u"0", defPos,
                        wx.Size(50, -1),
                        wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER, 0, 999, 0 )
        #======================================================================
        # parse table within rectangle
        #======================================================================
        self.BtnMatrix = wx.Button(self, wx.ID_ANY, u"Get Table",
                           defPos, defSiz, wx.BU_EXACTFIT)
        #======================================================================
        # column controls
        #======================================================================
        self.BtnNewCol = wx.Button(self, wx.ID_ANY, u"New Col",
                           defPos, defSiz, wx.BU_EXACTFIT)
        self.col_coords = {}
        self.ColList = wx.Choice( self, wx.ID_ANY, defPos, wx.Size(50, -1))
        self.CtrlCols = wx.SpinCtrl( self, wx.ID_ANY, u"0", defPos,
                           wx.Size(50, -1),
                           wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER, 0, 999, 0)
        #======================================================================
        # image of document page
        #======================================================================
        self.bitmap = self.pdf_show(1)
        self.PDFimage = wx.StaticBitmap(self, wx.ID_ANY, self.bitmap,
                           defPos, self.bitmap.Size, wx.NO_BORDER)
        #======================================================================
        # horizonzal lines
        #======================================================================
        l1 = wx.StaticLine(self, wx.ID_ANY, defPos, defSiz, wx.LI_HORIZONTAL)
        l2 = wx.StaticLine(self, wx.ID_ANY, defPos, defSiz, wx.LI_HORIZONTAL)
        l3 = wx.StaticLine(self, wx.ID_ANY, defPos, defSiz, wx.LI_HORIZONTAL)

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
        # sizers
        #======================================================================
        szr10 = wx.BoxSizer(wx.VERTICAL)         # main sizer
        szr20 = wx.BoxSizer(wx.HORIZONTAL)       # paging controls
        szr30 = wx.BoxSizer(wx.HORIZONTAL)       # rect & col controls & image
        szr40 = wx.BoxSizer(wx.VERTICAL)         # rect & col controls

        # szr20: navigation controls
        szr20.Add(self.BtnNext, 0, wx.ALL, 5)
        szr20.Add(self.BtnPrev, 0, wx.ALL, 5)
        szr20.Add(self.TextToPage, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Add(self.statPageMax, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Add(self.paperform, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Fit(self)

        # szr40: rectangle & column controls
        szr40.Add(self.BtnRect, 0,wx.ALL, 5)
        szr40.Add(self.statLeft, 0, wx.ALL, 5)
        szr40.Add(self.CtrlLeft, 0, wx.ALL, 5)
        szr40.Add(self.statTop, 0, wx.ALL, 5)
        szr40.Add(self.CtrlTop, 0, wx.ALL, 5)
        szr40.Add(self.statHeight, 0, wx.ALL, 5)
        szr40.Add(self.CtrlHeight, 0, wx.ALL, 5)
        szr40.Add(self.statWidth, 0, wx.ALL, 5)
        szr40.Add(self.CtrlWidth, 0, wx.ALL, 5)
        szr40.Add(l2, 0, wx.EXPAND|wx.ALL, 5)
        szr40.Add(self.BtnNewCol, 0, wx.ALL, 5)
        szr40.Add(self.ColList, 0, wx.ALL, 5)
        szr40.Add(self.CtrlCols, 0, wx.ALL, 5)
        szr40.Add(l3, 0, wx.EXPAND|wx.ALL, 5)
        szr40.Add(self.BtnMatrix, 0, wx.ALL, 5)
        szr40.Fit(self)

        # szr30: document image
        szr30.Add(szr40, 0, wx.EXPAND, 5)
        szr30.Add(self.PDFimage, 0, wx.ALL, 5)
        szr30.Fit(self)

        # szr10: main sizer
        szr10.Add(szr20, 0, wx.EXPAND, 5)
        szr10.Add(l1, 0, wx.EXPAND|wx.ALL, 5)
        szr10.Add(szr30, 0, wx.EXPAND, 5)
        szr10.Fit(self)
        self.SetSizer(szr10)
        self.Layout()

        self.Centre(wx.BOTH)

        #======================================================================
        # Bind event handlers
        #======================================================================
        self.BtnNewCol.Bind(wx.EVT_BUTTON, self.AddCol)
        self.BtnNext.Bind(wx.EVT_BUTTON, self.NextPage)
        self.BtnPrev.Bind(wx.EVT_BUTTON, self.PreviousPage)
        self.TextToPage.Bind(wx.EVT_TEXT_ENTER, self.GotoPage)
        self.BtnRect.Bind(wx.EVT_BUTTON, self.ActivateRect)
        self.BtnMatrix.Bind(wx.EVT_BUTTON, self.GetMatrix)
        self.CtrlTop.Bind(wx.EVT_SPINCTRL, self.resize_rect)
        self.CtrlHeight.Bind(wx.EVT_SPINCTRL, self.resize_rect)
        self.CtrlLeft.Bind(wx.EVT_SPINCTRL, self.resize_rect)
        self.CtrlWidth.Bind(wx.EVT_SPINCTRL, self.resize_rect)
        self.CtrlCols.Bind(wx.EVT_SPINCTRL, self.UpdateCol)
        self.ColList.Bind(wx.EVT_CHOICE, self.OnColSelect)
        self.PDFimage.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.PDFimage.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.PDFimage.Bind(wx.EVT_MOTION, self.move_mouse)
        self.PDFimage.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
        self.disable_fields()

    def __del__(self):
        pass

#==============================================================================
# Event handlers and other subroutines
#==============================================================================
    def cursor_in_rect(self, pos):
        # check whether cursor is in rectangle
        if not (self.rect_h > 0 and self.rect_w > 0): # does a rect exist?
            return False
        if pos.x < self.rect_x or pos.x > self.rect_x + self.rect_w or\
           pos.y < self.rect_y or pos.y > self.rect_y + self.rect_h:
               return False
        return True

    def rect_in_img(self, x, y, w, h):
        # check whether rectangle is inside page image
        width  = self.PDFimage.Size[0]
        height = self.PDFimage.Size[1]
        if not (x >= 0 and y >= 0 and x + w <= width and y + h <= height):
            return False
        return True

    def disable_fields(self):
        # reset controls & buttons (e.g. b/o page scrolling)
        self.CtrlHeight.Disable()
        self.CtrlTop.Disable()
        self.CtrlLeft.Disable()
        self.CtrlWidth.Disable()
        self.ColList.Disable()
        self.CtrlCols.Disable()
        self.BtnMatrix.Disable()
        self.BtnNewCol.Disable()
        self.CtrlCols.Value   = 0
        self.CtrlTop.Value    = 0
        self.CtrlLeft.Value   = 0
        self.CtrlHeight.Value = 0
        self.CtrlWidth.Value  = 0
        self.set_rectangle    = False
        self.col_selected     = None
        self.adding_column    = False
        self.dragging_rect    = False
        self.col_coords       = {}
        self.rect_x           = 0
        self.rect_y           = 0
        self.rect_w           = 0
        self.rect_h           = 0
        self.ColList.Clear()
        self.PDFimage.SetCursor(self.cursor_norm)
        return

    def enable_fields(self):
        # enable fields (after rectangle was made)
        self.BtnMatrix.Enable()
        self.CtrlHeight.Enable()
        self.CtrlTop.Enable()
        self.CtrlLeft.Enable()
        self.CtrlWidth.Enable()
        return

    def upd_collist(self):
        # update list of columns
        self.ColList.Clear()                # clear drop down list
        self.CtrlCols.Disable()             # disable spin control
        vlist = self.col_coords.values()
        if not vlist:                       # no columns left?
            self.ColList.Disable()
            return
        self.ColList.Enable()               # else recreate column dict
        self.col_coords = {}
        vlist.sort()
        i = 1
        for v in vlist:
            if v > self.rect_x and v < self.rect_x + self.rect_w:
                cname = "Col" + str(i)
                self.col_coords[cname] = v
                self.ColList.Append(cname)
                i += 1

    def resize_rect(self, evt):
        # change rectangle shape via spin controls
        if self.CtrlWidth.Value < 5:
            self.CtrlWidth.Value = 5
        if self.CtrlHeight.Value < 5:
            self.CtrlHeight.Value = 5
        x = self.CtrlLeft.Value
        y = self.CtrlTop.Value
        w = self.CtrlWidth.Value
        h = self.CtrlHeight.Value
        # move no rectangle part outside page image
        if not self.rect_in_img(x, y, w, h):
            self.CtrlLeft.Value   = self.rect_x  # reset invalid coordinates
            self.CtrlTop.Value    = self.rect_y  # ...
            self.CtrlWidth.Value  = self.rect_w  # ...
            self.CtrlHeight.Value = self.rect_h  # ...
            return
        self.rect_x = x
        self.rect_y = y
        self.rect_h = h
        self.rect_w = w
        self.DrawRect(x, y, w, h)           # redraw rectangle
        self.ColList.Clear()                # re-adjust column controls
        self.ColList.Disable()
        self.CtrlCols.Disable()
        self.CtrlCols.Value = 0
        self.col_selected = None
        self.upd_collist()
        for k in self.col_coords:           # also redraw all columns
            self.DrawColumn(self.col_coords[k], "RED")

    def move_rect(self, x, y, w, h):
        # move rectangle around with mouse
        if not self.rect_in_img(x, y, w, h):
            return                      # no rect part outside image
        dx = x - self.rect_x            # remember horizontal movement delta
        self.rect_x         = x
        self.rect_y         = y
        self.CtrlLeft.Value = x
        self.CtrlTop.Value  = y
        self.DrawRect(x, y, w, h)           # redraw rectangle
        self.CtrlCols.Value = 0             # set column info to
        self.ColList.Selection = -1         # none selected
        self.col_selected = None
        for k in self.col_coords:           # also redraw all columns after
            self.col_coords[k] += dx        # repositioning them
            self.DrawColumn(self.col_coords[k], "RED")

    def OnMouseWheel(self, evt):
        # process wheel as paging operations
        d = evt.GetWheelRotation()     # int indicating direction
        if d < 0:
            self.NextPage(evt)
        elif d > 0:
            self.PreviousPage(evt)
        return

    def OnColSelect(self, evt):
        # a column from the drop down box was selected
        self.adding_column = False
        col = evt.GetString()                         # selected item
        self.CtrlCols.Value = self.col_coords[col]    # get its coord
        self.CtrlCols.Enable()                        # enable spin control
        self.col_selected = col                       # store selected string
        for k in self.col_coords:
            if k == col:
                self.DrawColumn(self.col_coords[k], "BLUE")
            else:
                self.DrawColumn(self.col_coords[k], "RED")

    def AddCol(self, evt):
        # insert new column into rectangle
        # change cursor to up-down image
        self.adding_column = True           # store state: adding column
        self.set_rectangle = False
        self.ColList.Enable()               # enable drop-down list
        self.CtrlCols.Disable()             # disable spin control
        self.col_selected = None            # state change: no column selected
        return

    def OnLeftDown(self, evt):
        # left mouse button pressed down
        pos = evt.GetPosition()
        if self.set_rectangle:              # about to make rectangle,
            self.rect_x = pos.x
            self.rect_y = pos.y
            return
        elif self.adding_column:            # about to make a column
            # horizontal coord must be within rectangle
            if not self.cursor_in_rect(pos):
                return
            # store new column info
            n = self.ColList.Count + 1
            col_name = "Col" + str(n)
            self.col_coords[col_name] = pos.x
            self.ColList.Append("Col" + str(n))
            self.CtrlCols.Value = pos.x
            self.adding_column = False      # reset state: not adding column
            self.DrawColumn(pos.x, "RED")          # draw the column
            return
        # potentially a rectangle drag request
        if self.cursor_in_rect(pos):
            self.dragging_rect = True
            self.dragstart_x = pos.x - self.rect_x    # delta cursor to left
            self.dragstart_y = pos.y - self.rect_y    # delta cursor to top
        return

    def OnLeftUp(self, evt):
        self.dragging_rect = False          # reset dragging information
        self.dragstart_x = 0
        self.dragstart_y = 0

        if not self.set_rectangle:          # only handle making a rectangle
            return
        self.PDFimage.SetCursor(self.cursor_norm)     # cursor default again
        pos = evt.GetPosition()
        self.rect_w = abs(pos.x - self.rect_x)        # get width
        self.rect_h = abs(pos.y - self.rect_y)        # get height
        if self.rect_x > pos.x:
            self.rect_x = pos.x             # recover from not painting ...
        if self.rect_y > pos.y:             # from top-left
            self.rect_y = pos.y             # to bottom-right
        self.enable_fields()                # enable fields
        self.set_rectangle = False          # reset state: no more making rect
        self.BtnNewCol.Enable()             # making columns now possible
        return

    def move_mouse(self, evt):
        # handle mouse movements
        pos = evt.GetPosition()
        if not (self.adding_column or self.set_rectangle):
            if self.cursor_in_rect(pos):    # only adjust cursor
                self.PDFimage.SetCursor(self.cursor_hand)
            else:
                self.PDFimage.SetCursor(self.cursor_norm)
        if self.adding_column:
            if self.cursor_in_rect(pos):
                self.PDFimage.SetCursor(self.cursor_vert)
            else:
                self.PDFimage.SetCursor(self.cursor_norm)
            return
        if self.set_rectangle and evt.LeftIsDown():   # if making a rectangle
            w = abs(pos.x - self.rect_x)
            h = abs(pos.y - self.rect_y)
            x = self.rect_x                 # adjust coordinates ...
            if pos.x < x:                   # if not ...
                x = pos.x                   # moving from ...
            y = self.rect_y                 # top-left to ...
            if pos.y < y:                   # bottom-right ...
                y = pos.y                   # direction
            self.rect_w = w
            self.rect_h = h
            self.CtrlHeight.Value = h       # update ...
            self.CtrlWidth.Value  = w       # ... spin ...
            self.CtrlLeft.Value   = x       # ... controls
            self.CtrlTop.Value    = y
            self.DrawRect(x, y, w, h)       # draw rectangle
            return
        if not evt.LeftIsDown():
            self.dragging_rect = False
            self.dragstart_x = 0
            self.dragstart_y = 0
            return
        if self.dragging_rect and evt.LeftIsDown():
            new_x = pos.x - self.dragstart_x
            new_y = pos.y - self.dragstart_y
            self.move_rect(new_x, new_y, self.rect_w, self.rect_h)
            return
        return

    def UpdateCol(self, evt):
        # handle changes to spin control
        self.adding_column = False
        if not self.col_selected:           # only if a column is selected
            return
        v = self.CtrlCols.Value             # position of column
        x = self.rect_x                     # rectangle coord's
        y = self.rect_y
        w = self.rect_w
        h = self.rect_h
        self.col_coords[self.col_selected] = v   # store col coord in dict
        if v <= x or v >= x + w:            # if col coord outside rectangle
            self.resize_rect(evt)           # delete the column
            self.ColList.SetFocus()         # focus to next col selection
            return                          # and return
        self.DrawRect(x, y, w, h)           # else redraw everything we have
        for k in self.col_coords:           # redraw all columns
            if k == self.col_selected:
                c = "BLUE"
            else:
                c = "RED"
            self.DrawColumn(self.col_coords[k], c)

    def DrawColumn(self, x, c):
        # draw a vertical line
        dc = wx.ClientDC(self.PDFimage)     # make a device control out of img
        dc.SetPen(wx.Pen(c))
        # only draw inside the rectangle
        dc.DrawLine(x, self.rect_y, x, self.rect_y + self.rect_h)
        self.adding_column = False

    def DrawRect(self, x, y, w, h):
        # Draw a rectangle (red border, transparent interior)
        dc = wx.ClientDC(self.PDFimage)     # make a device control out of img
        dc.SetPen(wx.Pen("RED"))
        dc.SetBrush(wx.Brush("RED", style=wx.BRUSHSTYLE_TRANSPARENT))
        self.redraw_bitmap()
        dc.DrawRectangle(x, y, w, h)

    def GetMatrix(self, evt):
        # parse table contained in rectangle
        # currently, the table is just stored away as a matrix:
        # add functionality as desired
        x0 = self.rect_x
        y0 = self.rect_y
        x1 = x0 + self.rect_w
        y1 = y0 + self.rect_h
        cols = self.col_coords.values()
        cols.sort()
        pg = getint(self.TextToPage.Value) - 1
        self.parsed_table = ParseTab(self.doc, pg, [x0, y0, x1, y1],
                                     columns = cols)
        if self.parsed_table:
            r = len(self.parsed_table)
            c = len(self.parsed_table[0])
            t = "\nContents of (%s x %s) table at [%s,%s] on page %s"
            print(t % (r, c, x0, y0, pg + 1))
            for t in self.parsed_table:
                print(t)
        else:
            print("No text found in rectangle")

    def redraw_bitmap(self):
        w = self.bitmap.Size[0]
        h = self.bitmap.Size[1]
        x = y = 0
        rect = wx.Rect(x, y, w, h)
        bm = self.bitmap.GetSubBitmap(rect)
        dc = wx.ClientDC(self.PDFimage)     # make a device control out of img
        dc.DrawBitmap(bm, x, y)             # refresh bitmap before draw
        return

    def ActivateRect(self, evt):
        # Start drawing a rectangle
        self.disable_fields()
        self.set_rectangle = True
        self.PDFimage.SetCursor(self.cursor_cross)


    def NextPage(self, event):                   # means: page forward
        page = getint(self.TextToPage.Value) + 1 # current page + 1
        if page > self.doc.pageCount:
            return
        page = min(page, self.doc.pageCount)     # cannot go beyond last page
        self.TextToPage.Value = str(page)        # put target page# in screen
        self.bitmap = self.pdf_show(page)        # get page image
        self.NeuesImage(page)                    # refresh the layout
        event.Skip()

    def PreviousPage(self, event):               # means: page back
        page = getint(self.TextToPage.Value) - 1 # current page - 1
        if page < 1:
            return
        page = max(page, 1)                      # cannot go before page 1
        self.TextToPage.Value = str(page)        # put target page# in screen
        self.NeuesImage(page)
        event.Skip()

    def GotoPage(self, event):                   # means: go to page number
        page = getint(self.TextToPage.Value)     # get screen page number
        page = min(page, self.doc.pageCount)     # cannot go beyond last page
        page = max(page, 1)                      # cannot go before page 1
        self.TextToPage.Value = str(page)        # make sure it's on the screen
        self.NeuesImage(page)
        event.Skip()

#==============================================================================
# Read / render a PDF page. Parameters are: pdf = document, page = page#
#==============================================================================
    def NeuesImage(self, page):
        self.disable_fields()
        self.bitmap = self.pdf_show(page)        # read page image
        self.PDFimage.SetSize(self.bitmap.Size)  # adjust screen to image size
        self.PDFimage.SetBitmap(self.bitmap)     # put it in screen
        return

    def pdf_show(self, pg_nr):
        # get Pixmap of a page
        p = self.doc.loadPage(pg_nr - 1)
        pix = p.getPixmap()
        a = str(pix.samples)                     # string version of pixel area
        a2 = "".join([a[4*i:4*i+3] for i in range(len(a)/4)]) # RGBA -> RGB
        bitmap = wx.BitmapFromBuffer(pix.width, pix.height, a2)
        self.paperform.Label = "Paper format: " + PageFormat(None, p)
        return bitmap

    def decrypt_doc(self):
        # let user enter document password
        pw = None
        dlg = wx.TextEntryDialog(self, 'Please enter password below:',
                 'Document needs password to open', '',
                 style = wx.TextEntryDialogStyle|wx.TE_PASSWORD)
        while pw is None:
            rc = dlg.ShowModal()
            if rc == wx.ID_OK:
                pw = str(dlg.GetValue().encode("utf-8"))
                self.doc.authenticate(pw)
            else:
                return
            if self.doc.isEncrypted:
                pw = None
                dlg.SetTitle("Wrong password, enter correct password or cancel")
        return

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
wild = "supported files|*.pdf;*.xps;*.oxps;*.epub;*.cbz"

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
