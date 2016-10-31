#!/usr/bin/python
# -*- coding: latin-1 -*-

'''
Created on Sun May 03 16:15:08 2015

@author: Jorj McKie
Copyright (c) 2015 Jorj X. McKie

The license of this program is governed by the GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007. See the "COPYING" file of this repository.

Example program for the Python binding PyMuPDF of MuPDF.

Dependencies:
-------------
PyMuPDF v1.9.2 or later
wxPython v3.0.2 or later
All Python and bitness versions are now supported that are also supported by
PyMuPDF, MuPDF and wxPython.

This is a program for editing a PDF file's table of contents (ToC).
After choosing a file in a file selection dialog, its ToC is displayed
in a grid, together with an image of the currently displayed PDF page.
ToC entries can be edited, added, deleted and moved.
The thus modified PDF can be saved elsewhere or replace the original.

The overall screen layout is as follows:

        +--------------------+--------------------+
        |                    |                    |
        |      le_szr        |       ri_szr       |
        |                    |                    |
        +--------------------+--------------------+

Layout of left sizer "le_szr"

        +--------------------------------------------+
        | szr10:    Button "New Row", expl. text     |
        +--------------------------------------------+
        | tocgrid:  MyGrid (table of contents)       |
        +--------------------------------------------+
        | metagrid: PDF metadata                     |
        +--------------------------------------------+
        | szr31:    check data fields                |
        +--------------------------------------------+
        | szr40:    OK / Cancel buttons              |
        +--------------------------------------------+

Layout of right sizer "ri_szr"

        +-----------------------------------------+
        | re_szr20: forw / backw / pages          |
        +-----------------------------------------+
        | PDFBild: Bitmap image of pdf page       |
        +-----------------------------------------+

'''
import os, sys, traceback, json, time
import wx
import wx.grid as gridlib
import wx.lib.gridmovers as gridmovers
import fitz
try:
    from icons import ico_pdf          # PDF icon in upper left screen corner
    show_icon = True
except:
    show_icon = False
    
pyversion = sys.version_info[0]

# make some adjustments between wxPython versions
if wx.version() >= "3.0.3":
    table_base = gridlib.GridTableBase
    bmp_from_buffer = wx.Bitmap.FromBuffer
else:
    table_base = gridlib.PyGridTableBase
    bmp_from_buffer = wx.BitmapFromBuffer
 
def getint(v):
    import types
    # extract digits from a string to form an integer >= 0
    try:
        return int(v)
    except ValueError:
        pass
    if not isinstance(v, types.StringTypes):
        return 0
    a = "0"
    for d in v:
        if d in "0123456789":
            a += d
    return int(a)

#==============================================================================
# some abbreviations and global parameters
#==============================================================================
defPos = wx.DefaultPosition            # just an abbreviation
defSiz = wx.DefaultSize                # just an abbreviation
khaki  = wx.Colour(240, 230, 140)      # our background color

#==============================================================================
# convenience class for storing information across functions
#==============================================================================
class ScratchPad():
    def __init__(self):
        self.doc = None                  # fitz.Document
        self.meta = {}                   # PDF meta information
        self.seiten = 0                  # max pages
        self.inhalt = []                 # table of contents storage
        self.file = None                 # pdf filename
        self.oldpage = 0                 # stores last displayed page number
        self.fromjson = False            # autosaved input switch
        self.height = 0                  # store current page height
        self.lastsave = -1.0             # stores last save time
        self.grid_changed = False        # any TOC changes?
        self.timezone = "%s'%s'" % (str(time.timezone / 3600).rjust(2,"0"),
                                    str((time.timezone / 60)%60).rjust(2, "0"))
        if time.timezone > 0:
            self.timezone = "-" + self.timezone
        elif time.timezone < 0:
            self.timezone = "+" + self.timezone
        else:
            self.timezone = ""


#==============================================================================
# render a PDF page and return its wx.Bitmap
#==============================================================================
def pdf_show(dlg, seite):
    pno = getint(seite) - 1
    pix = spad.doc.getPagePixmap(pno)
    spad.height = pix.h
    a = pix.samplesRGB()                  # samples without alpha bytes
    bmp = bmp_from_buffer(pix.w, pix.h, a)
    pix = None
    a   = None
    return bmp

#==============================================================================
# Slider dialog for vertical bookmark positions (Height column)
#==============================================================================
class Slider(wx.Dialog):
    def __init__(self, parent, val, maxval):
        wx.Dialog.__init__(self, parent, id = wx.ID_ANY,
                   title = u"Slide", pos = defPos, size = (70, 340),
                   style = wx.CLOSE_BOX|wx.DEFAULT_DIALOG_STYLE)
        boxszr = wx.BoxSizer(wx.HORIZONTAL)
        self.slider = wx.Slider( self, wx.ID_ANY, val, 1, maxval,
                                   defPos, wx.Size(-1, 300),
                                   wx.SL_RIGHT|wx.SL_LABELS|wx.SL_INVERSE)
        boxszr.Add( self.slider, 0, 0, 5 )
        self.slider.Bind(wx.EVT_SCROLL, self.scrolling)
        self.SetSizer(boxszr)
        self.Layout()
        self.Centre(wx.BOTH)

    def scrolling(self, evt):
        self.GetParent().bookmark = self.slider.GetValue()
        evt.Skip()

#==============================================================================
# PDFTable = a tabular grid class in wx
#==============================================================================
class PDFTable(table_base):
    def __init__(self):
        table_base.__init__(self)

        self.colLabels = ['Level','Title','Page','Height']
        self.dataTypes = [gridlib.GRID_VALUE_NUMBER,
                          gridlib.GRID_VALUE_STRING,
                          gridlib.GRID_VALUE_NUMBER,
                          gridlib.GRID_VALUE_NUMBER,
                          ]
        # initial load of table with outline data
        # each line consists of [lvl, title, page, top (height)]
        self.data = []
        for z in spad.inhalt:
            top = -1
            lvl = z[0]
            tit = z[1]
            if pyversion < 3 and not spad.fromjson:   # data comes from the PDF!
                tit = tit.decode("utf-8","ignore")
            pno = z[2]
            if len(z) > 3:
                if type(z[3]) is int or type(z[3]) is float:
                    top = int(round(z[3]))
                else:
                    try:
                        top = int(round(z[3]["to"].y))
                    except: pass
            self.data.append([lvl, tit, pno, top])
        if not spad.inhalt:
            self.data = [[1, "*** contains no outline ***", 1, 0]]

#==============================================================================
# Methods required by wxPyGridTableBase interface.
# Will be called by the grid.
#==============================================================================
    def GetNumberRows(self):           # row count in my data table
        return len(self.data)

    def GetNumberCols(self):           # column count in my data table
        return len(self.colLabels)

    def IsEmptyCell(self, row, col):   # is-cell-empty checker
        try:
            return not self.data[row][col]
        except IndexError:
            return True

    def GetValue(self, row, col):           # get value for display
        if col != 1:
            return str(self.data[row][col])
        lvl = int(self.data[row][0]) - 1
        val = " "*lvl + self.data[row][1]   # simulate hierarchy lvl by spaces
        return val

    def SetValue(self, row, col, val):    # put value from cell to data table
        if col == 1:
            x_val = val.strip()           # strip off indentations
        else:
            x_val = int(val)
        self.data[row][col] = x_val

#==============================================================================
# set col names
#==============================================================================
    def GetColLabelValue(self, col):
        return self.colLabels[col]

#==============================================================================
# set row names (just row counters in our case). Only needed, because we have
# row-based operations (dragging, etc.), and these require some label.
#==============================================================================
    def GetRowLabelValue(self,row):
        return str(row +1)

#==============================================================================
# determine cell content type, controls the grid behaviour for the cells
#==============================================================================
    def GetTypeName(self, row, col):
        return self.dataTypes[col]

#==============================================================================
# move a row, called when user drags rows with the mouse.
# called with row numbers from -> to
#==============================================================================
    def MoveRow(self, frm, to):
        grid = self.GetView()

        if grid and frm != to:                  # actually moving something?
            # Move the data rows
            oldData = self.data[frm]            # list of row values
            del self.data[frm]                  # delete it from the data
            # determine place for the moving row, and insert it
            if to > frm:
                self.data.insert(to-1,oldData)
            else:
                self.data.insert(to,oldData)
#==============================================================================
#           inform the Grid about this by special "message batches"
#==============================================================================
            grid.BeginBatch()
            msg = gridlib.GridTableMessage(
                    self, gridlib.GRIDTABLE_NOTIFY_ROWS_DELETED, frm, 1)
            grid.ProcessTableMessage(msg)
            msg = gridlib.GridTableMessage(
                    self, gridlib.GRIDTABLE_NOTIFY_ROWS_INSERTED, to, 1)
            grid.ProcessTableMessage(msg)
            grid.EndBatch()

#==============================================================================
# Duplicate a row, called with row number
#==============================================================================
    def DuplicateRow(self, row):
        grid = self.GetView()
        if grid:
            zeile = [self.data[row][0], self.data[row][1], self.data[row][2],
                     self.data[row][3], ]
            self.data.insert(row, zeile)
            grid.BeginBatch()
            msg = gridlib.GridTableMessage(self,
                        gridlib.GRIDTABLE_NOTIFY_ROWS_INSERTED, row, 1)
            grid.ProcessTableMessage(msg)
            grid.EndBatch()

#==============================================================================
# Delete a row. called with row number.
#==============================================================================
    def DeleteRow(self, row):
        grid = self.GetView()
        if grid:
            del self.data[row]
            grid.BeginBatch()                         # inform the grid
            msg = gridlib.GridTableMessage(self,
                   gridlib.GRIDTABLE_NOTIFY_ROWS_DELETED, row, 1)
            grid.ProcessTableMessage(msg)
            grid.EndBatch()

#==============================================================================
# define Grid
#==============================================================================
class MyGrid(gridlib.Grid):
    def __init__(self, parent):
        gridlib.Grid.__init__(self, parent, -1)
        table = PDFTable()             # initialize table
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.do_title = False          # idling event: autosize title column
        self.bookmark_page = 0         # idling event: redisplay PDF image
        self.bookmark = -1             # idling event: bookmark position change
        self.bookmark_row = 0          # idling event: row number
#==============================================================================
# announce table to Grid
# 'True' = enable Grid to manage the table (destroy, etc.)
#==============================================================================
        self.SetTable(table, True)
#==============================================================================
# set font, width, alignment in the grid
#==============================================================================
        self.SetDefaultCellFont(wx.Font(wx.NORMAL_FONT.GetPointSize(),
                 70, 90, 90, False, "DejaVu Sans Mono"))

        # center columns (indent level)
        ct_al1 = gridlib.GridCellAttr()
        ct_al1.SetAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        self.SetColAttr(0, ct_al1)
        self.SetColAttr(3, ct_al1)
        # page number right aligned
        re_al1 = gridlib.GridCellAttr()
        re_al1.SetAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
        self.SetColAttr(2, re_al1)

#==============================================================================
# Enable Row moving
#==============================================================================
        gridmovers.GridRowMover(self)

        self.Bind(gridmovers.EVT_GRID_ROW_MOVE, self.OnRowMove)
        self.Bind(gridlib.EVT_GRID_LABEL_LEFT_DCLICK, self.OnRowDup)
        self.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.OnRowDel)
        self.Bind(gridlib.EVT_GRID_CELL_LEFT_DCLICK, self.OnCellDClick)
        self.Bind(gridlib.EVT_GRID_CELL_LEFT_CLICK, self.OnCellClick)
        self.Bind(gridlib.EVT_GRID_CELL_CHANGING, self.OnCellChanging)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

#==============================================================================
# Event Method: handle key press events - only navigation tasks performed
#==============================================================================
    def OnKeyDown(self, evt):
        if evt.ControlDown() or evt.ShiftDown(): # ignore all CTRL+ / SHIFT+
            evt.Skip()
            return
        key = evt.GetKeyCode()         # only handling UP, DOWN, ENTER
        if key not in (wx.WXK_DOWN, wx.WXK_UP, wx.WXK_RETURN):
            evt.Skip()
            return
        oldRow = self.GetGridCursorRow()
        oldCol = self.GetGridCursorCol()
        self.set_row_background(oldRow)     # ensure current row is khaki color
        maxRow = self.GetTable().GetNumberRows()

        if key == wx.WXK_UP:
            if oldRow > 0:        # only handled if not past start of grid
                self.set_row_background(oldRow - 1)
                self.MakeCellVisible(oldRow - 1, oldCol)
            evt.Skip()
            return

        if key == wx.WXK_DOWN:    # only handled if not past end of grid
            if oldRow + 1 < maxRow:
                self.set_row_background(oldRow + 1)
                self.MakeCellVisible(oldRow + 1, oldCol)
            evt.Skip()
            return

        self.DisableCellEditControl()
        success = self.MoveCursorRight(False)
        if not success:           # we are in last cell, so move to next row
            newRow = self.GetGridCursorRow() + 1
            if newRow >= maxRow:       # wrap to top if end of grid
                newRow = 0
            self.SetGridCursor(newRow, 0)
            self.MakeCellVisible(newRow, 0)
            self.set_row_background(newRow)       # recolor rows

        return

#==============================================================================
# Event Method: what to do if idling
#==============================================================================
    def OnIdle(self, evt):
        dlg = self.GetParent()
        if self.do_title:                   # did title changes happen?
            self.AutoSizeColumn(1)          # resize title column
            w1 = max(self.GetEffectiveMinSize()[0], dlg.minwidth)
            w2 = dlg.PDFbild.Size[0]
            h = dlg.Size[1]
            dlg.Size = wx.Size(w1 + w2 + 60, h)
            dlg.Layout()                    # adjust the grid
            self.do_title = False
        if self.bookmark > 0:               # did height changes happen?
            self.GetTable().SetValue(self.bookmark_row, 3, self.bookmark)
            self.Table.data[self.bookmark_row][3] = self.bookmark
            spad.oldpage = 0              # make sure page re-display
            PicRefresh(dlg, self.bookmark_page)
            self.bookmark = -1
        if (time.clock() - spad.lastsave) > 60.0 and spad.lastsave >= 0.0:
            dlg.auto_save()
        evt.Skip()

#==============================================================================
# Event Method: cell is changing
#==============================================================================
    def OnCellChanging(self, evt):
        DisableOK()                    # disable SAVE
        if evt.GetCol() == 1:          # if title changes,
            self.do_title = True       # trigger col resize when idle
        elif evt.GetCol() == 3:        # trigger height changes when idle
            self.bookmark      = int(evt.GetString())
            self.bookmark_row  = evt.GetRow()
            self.bookmark_page = self.GetTable().GetValue(self.bookmark_row, 2)
        evt.Skip()

#==============================================================================
# Event Method: cell click
#==============================================================================
    def OnCellClick(self, evt):
        row = evt.GetRow()
        self.set_row_background(row)
        evt.Skip()

#==============================================================================
# Event Method: cell double click
#==============================================================================
    def OnCellDClick(self, evt):
        row = evt.GetRow()             # row
        col = evt.GetCol()             # col
        dlg = self.GetParent()
        seite = self.GetTable().GetValue(row, 2) # make sure page is displayed
        PicRefresh(dlg, seite)
        if col != 3:                   # further handling only for height col
            evt.Skip()
            return
        self.bookmark_page = self.GetTable().GetValue(row, 2)   # store page no
        self.bookmark_row  = row                 # store grid row
        self.MakeCellVisible(row, col)
        h = self.GetTable().GetValue(row, 3)     # get current height value
        h = max(int(h), 1)                       # should be > 0
        maxh = spad.height                     # maxh is page height
        d = Slider(self, h, maxh)                # create slider dialog
        d.ShowModal()                            # show it
        self.bookmark = d.slider.GetValue()      # extract & store value
        evt.Skip()
        return

#==============================================================================
# Event Method: move row
#==============================================================================
    def OnRowMove(self,evt):
        frm = evt.GetMoveRow()               # the row to move
        to = evt.GetBeforeRow()              # before which row to insert
        self.GetTable().MoveRow(frm, to)
        self.GetParent().Layout()            # adjust the grid
        DisableOK()
        evt.Skip()

#==============================================================================
# Event Method: delete row
#==============================================================================
    def OnRowDel(self, evt):
        row = evt.GetRow()
        col = evt.GetCol()
        if row < 0 or col >= 0 or not evt.ControlDown():
            evt.Skip()
            return
        self.GetTable().DeleteRow(row)
        self.GetParent().Layout()            # adjust the grid
        DisableOK()
        evt.Skip()

#==============================================================================
# Event Method: duplicate row
#==============================================================================
    def OnRowDup(self, evt):
        row = evt.GetRow()
        col = evt.GetCol()
        if evt.ControlDown():
            evt.Skip()
            return
        if col < 0 and row >= 0:                 # a row duplication?
            self.GetTable().DuplicateRow(row)    # duplicate the row and ...
            self.GetParent().Layout()            # adjust the grid
            DisableOK()
        evt.Skip()

#==============================================================================
# Change background to KHAKI and that of others to WHITE
#==============================================================================
    def set_row_background(self, row):
        cols = self.GetNumberCols()
        rows = self.GetNumberRows()
        for i in list(range(rows)):
            for j in list(range(cols)):
                if i == row:
                    self.SetCellBackgroundColour(i, j, khaki)
                else:
                    self.SetCellBackgroundColour(i, j, "WHITE")
                self.RefreshAttr(i, j)
        self.Refresh()
        return

#==============================================================================
#
# define dialog
#
#==============================================================================
class PDFDialog (wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__ (self, parent, id = wx.ID_ANY,
                             title = "Maintain a PDF Table of Contents",
                             pos = defPos, size = wx.Size(1250, 950),
                             style = wx.CAPTION|wx.CLOSE_BOX|
                                     wx.DEFAULT_DIALOG_STYLE|
                                     wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|
                                     wx.RESIZE_BORDER)
        if show_icon: self.SetIcon(ico_pdf.img.GetIcon())  # set a screen icon
        self.SetBackgroundColour(khaki)
#==============================================================================
# Sizer 10: Button 'new row' and an explaining text
#==============================================================================
        self.szr10 = wx.BoxSizer(wx.HORIZONTAL)

        msg_txt = """DUPLICATE row: DoubleClick its number.  DELETE row: CTRL+Click its number. MOVE row: grab row number. DoubleClick a not selected row cell to display page image."""
        explain = wx.StaticText(self, wx.ID_ANY, msg_txt,
                      defPos, wx.Size(-1, 40), 0)
        self.szr10.Add(explain, 0, wx.ALIGN_CENTER, 5)

#==============================================================================
# Sizer 20: define outline grid and do some layout adjustments
#==============================================================================
        self.tocgrid = MyGrid(self)
        self.tocgrid.AutoSizeColumn(0)
        self.tocgrid.AutoSizeColumn(1)
        self.tocgrid.SetColSize(2, 50)
        self.tocgrid.SetColSize(3, 50)
        self.tocgrid.SetRowLabelSize(30)

#==============================================================================
# Sizer 30: PDF meta information
#==============================================================================
        self.metagrid = wx.FlexGridSizer(7, 2, 0, 0)
        self.metagrid.SetFlexibleDirection(wx.BOTH)
        self.metagrid.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        tx_input = wx.StaticText(self, wx.ID_ANY, "Input:",
                            defPos, defSiz, 0)
        self.metagrid.Add(tx_input, 0, wx.ALIGN_RIGHT, 5)

        tx_eindat = wx.StaticText(self, wx.ID_ANY,
                          "%s  (%s pages)" % (spad.file, str(spad.seiten)),
                            defPos, defSiz, 0)
        self.metagrid.Add(tx_eindat, 0, wx.LEFT, 5)

        tx_autor = wx.StaticText(self, wx.ID_ANY, "Author:",
                         defPos, defSiz, 0)
        self.metagrid.Add(tx_autor, 0, wx.ALIGN_RIGHT, 5)

        self.ausaut = wx.TextCtrl(self, wx.ID_ANY,
                       spad.meta["author"],
                       defPos, wx.Size(480, -1), wx.NO_BORDER)
        self.metagrid.Add(self.ausaut, 0, wx.LEFT, 5)

        pdf_titel = wx.StaticText(self, wx.ID_ANY, "Title:",
                          defPos, defSiz, 0)
        self.metagrid.Add(pdf_titel, 0, wx.ALIGN_RIGHT, 5)

        self.austit = wx.TextCtrl(self, wx.ID_ANY,
                       spad.meta["title"],
                       defPos, wx.Size(480, -1), wx.NO_BORDER)
        self.metagrid.Add(self.austit, 0, wx.LEFT, 5)

        tx_subject = wx.StaticText(self, wx.ID_ANY, "Subject:",
                           defPos, defSiz, 0)
        self.metagrid.Add(tx_subject, 0, wx.ALIGN_RIGHT, 5)

        self.aussub = wx.TextCtrl(self, wx.ID_ANY,
                       spad.meta["subject"],
                       defPos, wx.Size(480, -1), wx.NO_BORDER)
        self.metagrid.Add(self.aussub, 0, wx.LEFT, 5)

        tx_keywords = wx.StaticText(self, wx.ID_ANY, "Keywords:",
                           defPos, defSiz, 0)
        self.metagrid.Add(tx_keywords, 0, wx.ALIGN_RIGHT, 5)

        self.keywords = wx.TextCtrl(self, wx.ID_ANY,
                       spad.meta["keywords"],
                       defPos, wx.Size(480, -1), wx.NO_BORDER)
        self.metagrid.Add(self.keywords, 0, wx.LEFT, 5)

#==============================================================================
# Sizer 31: check data
#==============================================================================
        self.szr31 = wx.FlexGridSizer(1, 2, 0, 0)
        self.btn_chk = wx.Button(self, wx.ID_ANY, "Check Data",
                        defPos, defSiz, wx.BU_EXACTFIT)
        self.szr31.Add(self.btn_chk, 0, wx.ALIGN_TOP|wx.ALL, 5)
        self.msg = wx.StaticText(self, wx.ID_ANY,
                    "Before changes to the PDF can be saved, "
                    "you must check your input with this button.",
                    defPos, defSiz, 0)
        self.szr31.Add(self.msg, 0, wx.ALL, 5)

#==============================================================================
# Sizer 40: OK / Cancel
#==============================================================================
        self.szr40 = wx.StdDialogButtonSizer()
        self.szr40OK = wx.Button(self, wx.ID_OK, "SAVE",
                        defPos, defSiz, wx.BU_EXACTFIT)
        self.szr40OK.Disable()
        self.szr40.AddButton(self.szr40OK)
        self.szr40Cancel = wx.Button(self, wx.ID_CANCEL, "QUIT",
                            defPos, defSiz, wx.BU_EXACTFIT)
        self.szr40.AddButton(self.szr40Cancel)
        self.szr40.Realize()

#==============================================================================
# define lines (decoration only)
#==============================================================================
        linie1 = wx.StaticLine(self, wx.ID_ANY,
                       defPos, defSiz, wx.LI_HORIZONTAL)
        linie2 = wx.StaticLine(self, wx.ID_ANY,
                       defPos, defSiz, wx.LI_HORIZONTAL)
        linie3 = wx.StaticLine(self, wx.ID_ANY,
                       defPos, defSiz, wx.LI_HORIZONTAL)

#==============================================================================
# Left Sizer: Outline and other PDF information
#==============================================================================
        le_szr = wx.BoxSizer(wx.VERTICAL)
        le_szr.Add(self.szr10, 0, wx.EXPAND, 5)
        le_szr.Add(linie1, 0, wx.EXPAND|wx.ALL, 5)

        le_szr.Add(self.tocgrid, 1, wx.EXPAND, 5)
        le_szr.Add(self.szr31, 0, wx.EXPAND, 5)
        le_szr.Add(linie2, 0, wx.EXPAND|wx.ALL, 5)

        le_szr.Add(self.metagrid, 0, wx.EXPAND, 5)
        le_szr.Add(linie3, 0, wx.EXPAND|wx.ALL, 5)

        le_szr.Add(self.szr40, 0, wx.ALIGN_TOP|wx.ALIGN_CENTER_HORIZONTAL, 5)
        le_szr.RecalcSizes()

#==============================================================================
# Right Sizer: display a PDF page image
#==============================================================================
        ri_szr = wx.BoxSizer(wx.VERTICAL)     # a control line and the picture

        ri_szr20 = wx.BoxSizer(wx.HORIZONTAL) # defines the control line

        self.btn_vor = wx.Button(self, wx.ID_ANY, "forw",
                           defPos, defSiz, wx.BU_EXACTFIT)
        ri_szr20.Add(self.btn_vor, 0, wx.ALL, 5)

        self.btn_zur = wx.Button(self, wx.ID_ANY, "back",
                           defPos, defSiz, wx.BU_EXACTFIT)
        ri_szr20.Add(self.btn_zur, 0, wx.ALL, 5)

        self.zuSeite = wx.TextCtrl(self, wx.ID_ANY, "1",
                             defPos, wx.Size(40, -1),
                             wx.TE_PROCESS_ENTER|wx.TE_RIGHT)
        ri_szr20.Add(self.zuSeite, 0, wx.LEFT|wx.TOP|wx.RIGHT, 5)

        max_pages = wx.StaticText(self, wx.ID_ANY,
                            "of %s pages" % (str(spad.seiten),),
                            defPos, defSiz, 0)
        ri_szr20.Add(max_pages, 0, wx.ALIGN_CENTER, 5)

        # control line sizer composed, now add it to the vertical sizer
        ri_szr.Add(ri_szr20, 0, wx.EXPAND, 5)

        # define the bitmap for the pdf image ...
        bmp = pdf_show(self, 1)
        self.PDFbild = wx.StaticBitmap(self, wx.ID_ANY, bmp,
                           defPos, defSiz, wx.BORDER_NONE)
        # ... and add it to the vertical sizer
        ri_szr.Add(self.PDFbild, 0, wx.ALL, 0)

#==============================================================================
# Main Sizer composition
#==============================================================================
        mainszr= wx.BoxSizer(wx.HORIZONTAL)
        mainszr.Add(le_szr, 1, wx.ALL, 5)
        mainszr.Add(ri_szr, 0, wx.ALL, 5)

        self.SetSizer(mainszr)
        self.minwidth = self.metagrid.ComputeFittingWindowSize(self)[0]
        w1 = max(self.tocgrid.GetEffectiveMinSize()[0], self.minwidth)
        w2 = self.PDFbild.Size[0]
        h = self.Size[1]
        self.Size = wx.Size(w1 + w2 + 60, h)
        self.Layout()
        self.Centre(wx.BOTH)
        bmp = None

#==============================================================================
# bind buttons
#==============================================================================
        self.btn_chk.Bind(wx.EVT_BUTTON, self.DataOK)         # "check data"
        self.btn_vor.Bind(wx.EVT_BUTTON, self.forwPage)       # "forward"
        self.btn_zur.Bind(wx.EVT_BUTTON, self.backPage)       # "backward"
        self.zuSeite.Bind(wx.EVT_TEXT_ENTER, self.gotoPage)   # "page number"
        self.PDFbild.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel) # mouse scroll

    def __del__(self):
        pass

    def OnMouseWheel(self, evt):
        # process wheel as paging operations
        d = evt.GetWheelRotation()     # int indicating direction
        if d < 0:
            self.forwPage(evt)
        elif d > 0:
            self.backPage(evt)
        return

    def forwPage(self, evt):
        seite = getint(self.zuSeite.Value) + 1
        PicRefresh(self, seite)
        evt.Skip()

    def backPage(self, evt):
        seite = getint(self.zuSeite.Value) - 1
        PicRefresh(self, seite)
        evt.Skip()

    def gotoPage(self, evt):
        seite = self.zuSeite.Value
        PicRefresh(self, seite)
        evt.Skip()

#==============================================================================
# Check Data: enable / disable OK button
#==============================================================================
    def DataOK(self, evt):
        self.auto_save()
        clean = True
        self.msg.Label = "Data OK!"
        d = self.tocgrid.GetTable()
        for i in list(range(self.tocgrid.Table.GetNumberRows())):
            if i == 0 and int(d.GetValue(0, 0)) != 1:
                clean = False
                self.msg.Label = "row 1 must have level 1"
                break
            if int(d.GetValue(i, 0)) < 1:
                clean = False
                self.msg.Label = "row %s: level < 1" % (str(i+1),)
                break
            if not (0 < int(d.GetValue(i, 2)) <= spad.seiten):
                clean = False
                self.msg.Label = "row %s: page# out of range" % (str(i+1),)
                break
            if i > 0 and (int(d.GetValue(i, 0)) - int(d.GetValue(i-1, 0))) > 1:
                clean = False
                self.msg.Label = "row %s: level stepping > 1" % (str(i+1),)
                break
            if not d.GetValue(i, 1):
                clean = False
                self.msg.Label = "row %s: missing title" % (str(i+1),)
                break
            h = spad.height
            if int(d.GetValue(i, 3)) < 1:
                d.SetValue(i, 3, str(h - 36))
                self.tocgrid.Table.data[i][3] = h - 36
            if not (0 < int(d.GetValue(i, 3)) <= h):
                clean = False
                self.msg.Label = "row %s: height not in range" % (str(i+1),)
                break

        if not clean:
            self.szr40OK.Disable()
        else:
            self.szr40OK.Enable()

        self.tocgrid.Refresh()
        evt.Skip()
        return

    def auto_save(self):
        f_toc = open(spad.file + ".json", "w")
        d = {"toc": self.tocgrid.Table.data,
             "author": self.ausaut.Value, "title": self.austit.Value,
             "subject": self.aussub.Value, "keywords": self.keywords.Value}
        json.dump(d, f_toc)
        f_toc.close()
        spad.lastsave = time.clock()
        return

#==============================================================================
# display a PDF page
#==============================================================================
def PicRefresh(dlg, seite):
    i_seite = getint(seite)
    i_seite = max(1, i_seite)               # ensure page# is within boundaries
    i_seite = min(spad.seiten, i_seite)

    dlg.zuSeite.Value = str(i_seite)        # set page number in dialog field
    if spad.oldpage == i_seite:             # avoid effort if no page change
        return
    spad.oldpage = i_seite

    bmp = pdf_show(dlg, i_seite)            # get bitmap of page

    dc = wx.MemoryDC()                      # make a device control out of bmp
    dc.SelectObject(bmp)
    dc.SetPen(wx.Pen("RED", width=1))
    d = dlg.tocgrid.GetTable()              # get data of grid
    ltab = dlg.tocgrid.Table.GetNumberRows()

    # draw horizontal line for every bookmark to this page
    # note that we don't assume any page number order!
    for i in list(range(ltab)):
        if int(d.GetValue(i, 2)) != i_seite:
            continue
        x1 = bmp.Size[0] - 1                # don't draw on last pixel
        top = int(d.GetValue(i, 3))
        # adjust to img dimension
        t = float(bmp.Size[1]) * float(top) / float(spad.height)
        t = bmp.Size[1] - int(t)            # DrawLine counts from top
        dc.DrawLine(1, t, x1, t)            # don't draw on 1st pixel

    dc.SelectObject(wx.NullBitmap)          # destroy MemoryDC
    dc = None                               # before further use

    dlg.PDFbild.SetSize(bmp.Size)           # update size
    dlg.PDFbild.SetBitmap(bmp)              # and update the picture
    dlg.Layout()
    bmp = None                              # destroy bitmap
    return
#==============================================================================
# Disable OK button
#==============================================================================
def DisableOK():
    dlg.szr40OK.Disable()
    dlg.msg.Label = "Data have changed. Check them to enable SAVE button."
    spad.grid_changed = True
    if spad.lastsave < 0.0:
        spad.lastsave = 1.0

#==============================================================================
# Read PDF document information
#==============================================================================
def getPDFinfo():
    spad.doc = fitz.open(spad.file)
    if spad.doc.needsPass:
        decrypt_doc()
        if spad.doc.isEncrypted:
            return True
    spad.seiten = spad.doc.pageCount
    spad.meta = {"author":"", "title":"", "subject":""}

    for key, wert in spad.doc.metadata.items():
        if wert:
            if pyversion < 3:
                spad.meta[key] = wert.decode("utf-8", "ignore")
            else:
                spad.meta[key] = wert
        else:
            spad.meta[key] = ""

    spad.fromjson = False
    spad.inhalt = spad.doc.getToC(simple = False)
    tocfile = spad.file + ".json"
    if os.path.exists(tocfile):
        d = wx.MessageDialog(None,
             "Saved data exist for this PDF - Use them instead?",
             "Input available from previous edit session",
             wx.YES_NO | wx.ICON_QUESTION)
        rc = d.ShowModal()
        d.Destroy()
        d = None
        if rc == wx.ID_YES:
            try:
                f_toc = open(tocfile)
                d = json.load(f_toc)
                f_toc.close()
                spad.fromjson         = True
                spad.inhalt           = d["toc"]
                spad.meta["author"]   = d["author"]
                spad.meta["title"]    = d["title"]
                spad.meta["subject"]  = d["subject"]
                spad.meta["keywords"] = d["keywords"]
            except:
                d = wx.MessageDialog(None, "Ignoring saved data",
                      "Invalid input from previous session")
                d.ShowModal()
                d.Destroy()
                d = None
                pass
        else:
            os.remove(tocfile)
    return False

def decrypt_doc():
    # let user enter document password
    pw = None
    dlg = wx.TextEntryDialog(None, 'Please enter the password below:',
             'Document is password protected', '',
             style = wx.TextEntryDialogStyle|wx.TE_PASSWORD)
    while pw is None:
        rc = dlg.ShowModal()
        if rc == wx.ID_OK:
            pw = dlg.GetValue().encode("latin-1")
            spad.doc.authenticate(pw)
        else:
            return
        if spad.doc.isEncrypted:
            pw = None
            dlg.SetTitle("Wrong password. Enter correct one or cancel.")
    return

#==============================================================================
# Write the changed PDF file
#============================================================================
def make_pdf(dlg):
    f = spad.file
    indir, infile = os.path.split(f)
    odir = indir
    ofile = infile
    if spad.doc.needsPass or spad.doc.openErrCode:
        ofile = ""
    sdlg = wx.FileDialog(None, "Specify Output", odir, ofile,
                                   "PDF files (*.pdf)|*.pdf", wx.FD_SAVE)

    if sdlg.ShowModal() == wx.ID_CANCEL:
        return None

    outfile = sdlg.GetPath()
    if spad.doc.needsPass or spad.doc.openErrCode:
        title =  "Repaired / decrypted PDF requires new output file"
        while outfile == spad.file:
            sdlg = wx.FileDialog(None, title, odir, "",
                                 "PDF files (*.pdf)|*.pdf", wx.FD_SAVE)
            if sdlg.ShowModal() == wx.ID_CANCEL:
                return None
            outfile = sdlg.GetPath()
    cdate = time.strftime("D:%Y%m%d%H%M%S",time.localtime()) + spad.timezone

    m = spad.meta
    if not m["creationDate"].startswith("D:"):
        m["creationDate"] = cdate
    if m["producer"] in ["", "(none)", "unspecified", "none", "(unspecified)"]:
        m["producer"] = "PyMuPDF"
    if m["creator"] in ["", "(none)", "unspecified", "none", "(unspecified)"]:
        m["creator"] = "PDFoutline.py"
    m["modDate"]  = cdate
    m["title"]    = dlg.austit.Value
    m["author"]   = dlg.ausaut.Value
    m["subject"]  = dlg.aussub.Value
    m["keywords"] = dlg.keywords.Value

    spad.doc.setMetadata(m)    # set new metadata
    # store our outline entries as bookmarks
    if spad.grid_changed:
        newtoc = []
        for z in dlg.tocgrid.Table.data:
            lvl = int(z[0])
            pno = int(z[2])
            tit = z[1].strip()
            top = getint(z[3])
            newtoc.append([lvl, tit, pno, top])
        spad.doc.setToC(newtoc)

    if outfile == spad.file:
        spad.doc.save(outfile, incremental=True)
    else:                                   # equal: replace input file
        spad.doc.save(outfile, garbage=3)

    return

#==============================================================================
#
# Main Program
#
#==============================================================================
assert wx.version() >= "3.0.2", "need at least wxPython v3.0.2"
assert fitz.VersionBind >= "1.9.2", "need at least PyMuPDF v1.9.2"

app = None
app = wx.App()

#==============================================================================
# Check if we have been invoked with a PDF to edit
#==============================================================================
if len(sys.argv) == 2:
    infile = sys.argv[1]
    if not infile.endswith(".pdf"):
        infile = None
else:
    infile = None

#==============================================================================
# let user select the file. Can only allow true PDFs.
#==============================================================================
if not infile:
    d = wx.FileDialog(None, message = "Choose a PDF file to edit",
                        defaultDir = os.path.expanduser('~'),
                        defaultFile = wx.EmptyString,
                        wildcard = "PDF files (*.pdf)|*.pdf",
                        style = wx.FD_OPEN | wx.FD_CHANGE_DIR)
    # We got a file only when one was selected and OK pressed
    if d.ShowModal() == wx.ID_OK:
        # This returns a Python list of selected files.
        infile = d.GetPath()
    else:
        infile = None
    # destroy this dialog
    d.Destroy()
    d = None

if infile:                      # if we have a filename ...
    spad = ScratchPad()         # create our scratchpad
    spad.file = infile
    if getPDFinfo() == 0:              # input is not encrypted
        dlg = PDFDialog(None)          # create dialog
        rc = dlg.ShowModal()           # show dialog
        if rc == wx.ID_OK:             # output PDF if SAVE pressed
            try:
                make_pdf(dlg)
                if os.path.exists(infile + ".json"):
                    os.remove(infile + ".json")
            except:
                f_exc = open(infile + ".log", "w")
                txt = traceback.format_exc()
                f_exc.write(txt)
                f_exc.close()
                wx.MessageBox(txt, "An exception occurred while making PDF")
        #spad.doc.close()
        dlg.Destroy()

app = None
