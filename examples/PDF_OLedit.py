# -*- coding: cp1252 -*-
'''
Created on Sun May 03 16:15:08 2015

@author: Jorj McKie
Copyright (c) 2015 Jorj X. McKie

The license of this program is governed by the GNU GENERAL PUBLIC LICENSE 
Version 3, 29 June 2007. See the "COPYING" file of this repository.

This an example program for the Python binding python-fitz of MuPDF.

This a program for editing a PDF file's table of contents (ToC).
After choosing a file in a file selection dialog, its ToC is displayed
in a grid, together with an image of the currently displayed PDF page.
ToC entries can be edited, added, deleted and moved.
The thus modified PDF can be saved elsewhere or replace the original file.

The overall screen layout is as follows:

        +--------------------+--------------------+
        |                    |                    |
        |      le_szr        |       ri_szr       |
        |                    |                    |
        +--------------------+--------------------+
        
Layout of left sizer "le_szr"

        +-----------------------------------------+
        | szr10: Button "New Row", expl. text     |
        +-----------------------------------------+
        | szr20: MyGrid (table of contents)       |
        +-----------------------------------------+
        | szr30: PDF metadata                     |
        +-----------------------------------------+
        | szr31: check data fields                |
        +-----------------------------------------+
        | szr40: OK / Cancel buttons              |
        +-----------------------------------------+
        
Layout of right sizer "ri_szr"

        +-----------------------------------------+
        | re_szr20: forw / backw / pages          |
        +-----------------------------------------+
        | PDFBild: Bitmap image of pdf page       |
        +-----------------------------------------+

Please note that you need a wxPython version 3.x for this to work.
'''
import os
import tempfile
import wx
import wx.grid as gridlib
import wx.lib.gridmovers as gridmovers
import PyPDF2  # only used for output (make_pdf)
import fitz
#==============================================================================
# just abbreviations
#==============================================================================
defPos = wx.DefaultPosition
defSiz = wx.DefaultSize

#==============================================================================
# convenience class for storing information across functions
#==============================================================================
class PDFconfig():
    def __init__(self):
        self.doc = None                  # fitz.Document
        self.meta = {}                   # PDF meta information
        self.seiten = 0                  # max pages
        self.inhalt = []                 # table of contents storage
        self.oldPage = 0               # last displayed page number 
        self.file = None                 # pdf filename
        # we use temp png files for buffering already displayed pages
        tmppic = tempfile.NamedTemporaryFile(suffix = ".png",
                    delete = False)
        tmppic.file.close()              # created temp file for PNG images
        self.pic = tmppic.name           # save its filename
        self.pics = self.pic[:-4] + "%s.png"  # mask for other PDF pages
        # list of existing temp png files
        self.pic_pages = []              # saves displayed page pic filenames 
        self.pic_pages.append(self.pic)  # store the one just created
    
    def TempPDF(self, dir = None):
#==============================================================================
#       temp PDF for the save process (only needed when infile = outfile)
#==============================================================================
        temppdf = tempfile.NamedTemporaryFile(suffix = ".pdf",
                    dir = dir, delete = False)
        self.opdfname = temppdf.name
        self.opdffile = temppdf.file

#==============================================================================
# render a PDF page and store image in png file
#==============================================================================
def pdf_show(datei, seite):
    page_idx = int(seite) - 1
    page = PDFcfg.doc.loadPage(page_idx)    # get the page
    irect = page.bound().round()            # integer rectangle representing it
    pix = fitz.Pixmap(fitz.Colorspace(fitz.CS_RGB),
                      irect)                # empty RGB pixmap of this size
    pix.clearWith(255)                      # clear it with color "white"
    dev = fitz.Device(pix)                  # create a "draw" device
    page.run(dev, fitz.Identity)            # render the page
    pix.writePNG(datei)
    return 

#==============================================================================
# PDFTable = a tabular grid class in wx
#==============================================================================
class PDFTable(gridlib.PyGridTableBase):
    def __init__(self):
        gridlib.PyGridTableBase.__init__(self)

        self.colLabels = ['Level','Title','Page','del?']
        self.dataTypes = [gridlib.GRID_VALUE_NUMBER,
                          gridlib.GRID_VALUE_STRING,
                          gridlib.GRID_VALUE_NUMBER,
                          gridlib.GRID_VALUE_BOOL]
        # initial load of table with outline data
        # each line consists of [lvl, title page, del], where 'del' means a 
        # delete indicator: "" = no, "1" = yes
        # for display, we "indent" the title with spaces
        self.data = [[PDFcfg.inhalt[i][0],          # indentation level
                      " "*(PDFcfg.inhalt[i][0] -1) + \
                      PDFcfg.inhalt[i][1],
                      PDFcfg.inhalt[i][2] + 1, ""] \
                              for i in range(len(PDFcfg.inhalt))]
        if not PDFcfg.inhalt:
            self.data = [[0, "*** contains no outline ***", 0, "1"]]
        # used for correctly placing new lines. insert at end = -1
        self.cur_row = -1

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
            
    def GetValue(self, row, col):      # get value (to be put into a cell)
        if col == 1:                   # simulate indentation if title column
            lvl = int(self.data[row][0]) - 1
            value = "  " * lvl + self.data[row][1].strip()
        else:
            value = self.data[row][col]
        return value

    def SetValue(self, row, col, value):    # put value from cell to data table
        if col == 1:
            x_val = value.strip()           # strip off simulated indentations
        else:
            x_val = value
        self.data[row][col] = x_val

#==============================================================================
# set col names
#==============================================================================
    def GetColLabelValue(self, col):
        return self.colLabels[col]

#==============================================================================
# set row names (just row counters in our case). Only needed, because we have
# row-based operations (dragging, duplicating) and these require some label.
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
            self.cur_row = to
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
# insert a new row, called with the new cell value list (zeile).
# we use self.cur_row to determine where to put it.
#==============================================================================
    def NewRow(self, zeile):
        grid = self.GetView()
        if grid:
            if self.cur_row in range(len(self.data)): # insert in the middle?
                self.data.insert(self.cur_row, zeile)
                grid.BeginBatch()                     # inform grid
                msg = gridlib.GridTableMessage(self,
                       gridlib.GRIDTABLE_NOTIFY_ROWS_INSERTED, self.cur_row, 1)
                grid.ProcessTableMessage(msg)
                grid.EndBatch()
            else:                                     # insert at end (append)
                self.data.append(zeile)
                grid.BeginBatch()                     # inform grid
                msg = gridlib.GridTableMessage(self,
                       gridlib.GRIDTABLE_NOTIFY_ROWS_APPENDED, 1)
                grid.ProcessTableMessage(msg)
                grid.EndBatch()
                
#==============================================================================
# Duplicate a row, called with row number
#==============================================================================
    def DuplicateRow(self, row):
        grid = self.GetView()
        if grid:
            zeile = [self.data[row][0], self.data[row][1],
                     self.data[row][2], self.data[row][3],]
            self.data.insert(row, zeile)
            grid.BeginBatch()
            msg = gridlib.GridTableMessage(self,
                        gridlib.GRIDTABLE_NOTIFY_ROWS_INSERTED, row, 1)
            grid.ProcessTableMessage(msg)
            grid.EndBatch()
            self.cur_row = row
            
#==============================================================================
# delete a row. called with row number.
#==============================================================================
    def DeleteRow(self, row):
        grid = self.GetView()
        self.cur_row = row
        if grid and self.data[row][3] == '1':         # indicator must be "on"
            del self.data[row]
            grid.BeginBatch()                         # inform grid
            msg = gridlib.GridTableMessage(self,
                   gridlib.GRIDTABLE_NOTIFY_ROWS_DELETED, row, 1)
            grid.ProcessTableMessage(msg)
            grid.EndBatch()
        if self.cur_row not in range(len(self.data)): # update indicator
            self.cur_row = -1

#==============================================================================
# define Grid
#==============================================================================
class MyGrid(gridlib.Grid):
    def __init__(self, parent):
        gridlib.Grid.__init__(self, parent, -1)

        table = PDFTable()             # initialize table
        
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
        
        # center columns (indent level, delete check box)
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
        
#==============================================================================
# Bind: move row
#==============================================================================
        self.Bind(gridmovers.EVT_GRID_ROW_MOVE, self.OnRowMove, self)

#==============================================================================
# Bind: delete row        
#==============================================================================
        self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.OnRowDel, self)
#==============================================================================
# Bind: duplicate a row
#==============================================================================
        self.Bind(gridlib.EVT_GRID_LABEL_LEFT_DCLICK, self.OnRowDup, self)

#==============================================================================
# Bind: (double) click a cell
#==============================================================================
        self.Bind(gridlib.EVT_GRID_CELL_LEFT_CLICK, self.OnCellClick, self)
        self.Bind(gridlib.EVT_GRID_CELL_LEFT_DCLICK, self.OnCellDClick, self)
#==============================================================================
# Bind: cell is changing
#==============================================================================
        self.Bind(gridlib.EVT_GRID_CELL_CHANGING, self.OnCellChanging, self)
        
#==============================================================================
# Event Method: cell is changing
#==============================================================================
    def OnCellChanging(self, evt):
        if evt.GetCol() == 2:          # page number is changing
            value = evt.GetString()    # new cell value
            PicRefresh(value)          # we show corresponding image
        self.AutoSizeColumn(1)         # as always: title width adjust
        DisableOK()                    # check data before save is possible

#==============================================================================
# Event Method: cell click
#==============================================================================
    def OnCellClick(self, evt):
        row = evt.GetRow()             # row
        col = evt.GetCol()             # col
        table = self.GetTable()
        grid = table.GetView()
        grid.GoToCell(row, col)        # force "select" for the cell
        self.cur_row = row             # memorize current row
        self.AutoSizeColumn(1)         # adjust title col width to content
        
#==============================================================================
# Event Method: cell double click
#==============================================================================
    def OnCellDClick(self, evt):
        row = evt.GetRow()             # row
        col = evt.GetCol()             # col
        table = self.GetTable()
        if col == 1 or col == 2:       # refresh picture if title or page col
            seite = table.GetValue(row, 2)
            PicRefresh(seite)
        grid = table.GetView()
        grid.GoToCell(row, col)        # force "select" of that cell
        self.cur_row = row             # memorize current row
        self.AutoSizeColumn(1)
        
#==============================================================================
# Event Method: move row
#==============================================================================
    def OnRowMove(self,evt):
        frm = evt.GetMoveRow()         # row being moved
        to = evt.GetBeforeRow()        # before which row to insert
        self.GetTable().MoveRow(frm,to)
        DisableOK()
        
#==============================================================================
# Event Method: delete row
#==============================================================================
    def OnRowDel(self, evt):
        row = evt.GetRow()
        self.GetTable().DeleteRow(row)
        DisableOK()

#==============================================================================
# Event Method: delete row
#==============================================================================
    def OnRowDup(self, evt):
        row = evt.GetRow()
        col = evt.GetCol()
        if col < 0 and row >= 0:       # else this is not a row duplication!
            self.GetTable().DuplicateRow(row)    # duplicate the row and ...
            self.GetParent().Layout()  # possibly enlarge the grid
        DisableOK()

#==============================================================================
#
# define dialog       
#
#==============================================================================
class PDFDialog (wx.Dialog):    
    def __init__(self, parent):
        wx.Dialog.__init__ (self, parent, id = wx.ID_ANY,
                             title = u"Maintain PDF Outline",
                             pos = wx.Point(1, 1),
                             size = wx.Size(1300,950),
                             style = wx.CAPTION|
                                     wx.CLOSE_BOX|
                                     wx.DEFAULT_DIALOG_STYLE|
                                     wx.MAXIMIZE_BOX|
                                     wx.MINIMIZE_BOX|
                                     wx.RESIZE_BORDER)
                
#==============================================================================
# Sizer 10: Button 'new row' and an explaining text
#==============================================================================
        self.szr10 = wx.BoxSizer(wx.HORIZONTAL)
        
        self.btn_neu = wx.Button(self, wx.ID_ANY, u"New Row",
                        defPos, defSiz, 0)
        self.szr10.Add(self.btn_neu, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        
        msg_txt = """New rows will be inserted at the end, or before the row with a right-clicked field.\nDuplicate: double-click the row number.  Delete: check 'del?' and right-click.\nDouble-click titles or page numbers to display the page image."""
        explain = wx.StaticText(self, wx.ID_ANY, msg_txt,
                      defPos, wx.Size(-1, 50), 0)
        self.szr10.Add(explain, 0, wx.ALIGN_CENTER, 5)

#==============================================================================
# Sizer 20: define outline grid and do some layout adjustments
#==============================================================================
        self.szr20 = MyGrid(self)
        self.szr20.AutoSizeColumn(0)
        self.szr20.AutoSizeColumn(1)
        self.szr20.SetColSize(2, 45)
        self.szr20.SetColSize(3, 35)
        self.szr20.SetRowLabelSize(30)
          
#==============================================================================
# Sizer 30: PDF meta information
#==============================================================================
        self.szr30 = wx.FlexGridSizer(6, 2, 0, 0)
        self.szr30.SetFlexibleDirection(wx.BOTH)
        self.szr30.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
        
        self.tx_input = wx.StaticText(self, wx.ID_ANY, u"Input:",
                            defPos, defSiz, 0)
        self.tx_input.Wrap(-1)
        self.szr30.Add(self.tx_input, 0, wx.ALIGN_CENTER, 5)
 
        self.tx_eindat = wx.StaticText(self, wx.ID_ANY,
                            "  %s  (%s pages)" % (PDFcfg.file, str(PDFcfg.seiten)),
                            defPos, defSiz, 0)
        self.tx_eindat.Wrap(-1)
        self.szr30.Add(self.tx_eindat, 0, wx.ALL, 5)
 
        self.tx_ausdat = wx.StaticText(self, wx.ID_ANY, u"Output:",
                            defPos, defSiz, 0)
        self.tx_ausdat.Wrap(-1)
        self.szr30.Add(self.tx_ausdat, 0, wx.ALIGN_CENTER, 5)
        
        self.btn_aus = wx.FilePickerCtrl(self, wx.ID_ANY,
                        PDFcfg.file,
                        u"set output file",
                        u"*.pdf",
                        defPos, wx.Size(480,-1),
                        wx.FLP_OVERWRITE_PROMPT|
                        wx.FLP_SAVE|
                        wx.FLP_USE_TEXTCTRL)
        self.szr30.Add(self.btn_aus, 0, wx.ALL, 5)
        self.tx_autor = wx.StaticText(self, wx.ID_ANY, "Author:",
                         defPos, defSiz, 0)
        self.tx_autor.Wrap(-1)
        self.szr30.Add(self.tx_autor, 0, wx.ALIGN_CENTER, 5)
        
        self.ausaut = wx.TextCtrl(self, wx.ID_ANY,
                       PDFcfg.meta["author"],
                       defPos, wx.Size(480, -1), 0)
        self.szr30.Add(self.ausaut, 0, wx.ALL, 5)
        
        self.pdf_titel = wx.StaticText(self, wx.ID_ANY, "Title:",
                          defPos, defSiz, 0)
        self.pdf_titel.Wrap(-1)
        self.szr30.Add(self.pdf_titel, 0, wx.ALIGN_CENTER, 5)
        
        self.austit = wx.TextCtrl(self, wx.ID_ANY,
                       PDFcfg.meta["title"],
                       defPos, wx.Size(480, -1), 0)
        self.szr30.Add(self.austit, 0, wx.ALL, 5)
        
        self.tx_subject = wx.StaticText(self, wx.ID_ANY, "Subject:",
                           defPos, defSiz, 0)
        self.tx_subject.Wrap(-1)
        self.szr30.Add(self.tx_subject, 0, wx.ALIGN_CENTER, 5)
        
        self.aussub = wx.TextCtrl(self, wx.ID_ANY,
                       PDFcfg.meta["subject"],
                       defPos, wx.Size(480, -1), 0)
        self.szr30.Add(self.aussub, 0, wx.ALL, 5)

#==============================================================================
# Sizer 31: check data
#==============================================================================
        self.szr31 = wx.FlexGridSizer(1, 2, 0, 0)
        self.btn_chk = wx.Button(self, wx.ID_ANY, u"Check Data",
                        defPos, defSiz, 0)
        self.szr31.Add(self.btn_chk, 0, wx.ALIGN_TOP|wx.ALL, 5)
        self.msg = wx.StaticText(self, wx.ID_ANY, "Before data can be saved, "\
                    "their validity must be checked with this button.\n"\
                    "Warning: Any original 'Output' file will be overwritten, "\
                    "if you press OK!",
                    defPos, defSiz, 0)
        self.msg.Wrap(-1)
        self.szr31.Add(self.msg, 0, wx.ALL, 5)
            
#==============================================================================
# Sizer 40: OK / Cancel
#==============================================================================
        self.szr40 = wx.StdDialogButtonSizer()
        self.szr40OK = wx.Button(self, wx.ID_OK)
        self.szr40OK.Disable()
        self.szr40.AddButton(self.szr40OK)
        self.szr40Cancel = wx.Button(self, wx.ID_CANCEL)
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
        
        le_szr.Add(self.szr20, 1, wx.EXPAND, 5)
        le_szr.Add(self.szr31, 0, wx.EXPAND, 5)
        le_szr.Add(linie2, 0, wx.EXPAND|wx.ALL, 5)
        
        le_szr.Add(self.szr30, 0, wx.EXPAND, 5)
        le_szr.Add(linie3, 0, wx.EXPAND|wx.ALL, 5)
        
        le_szr.Add(self.szr40, 0, wx.ALIGN_TOP|wx.ALIGN_CENTER_HORIZONTAL, 5)
        
#==============================================================================
# Right Sizer: display a PDF page image
#==============================================================================
        ri_szr = wx.BoxSizer(wx.VERTICAL)     # a control line and the picture
        
        ri_szr20 = wx.BoxSizer(wx.HORIZONTAL) # defines the control line
        
        self.btn_vor = wx.Button(self, wx.ID_ANY, u"forward",
                           defPos, defSiz, 0)
        ri_szr20.Add(self.btn_vor, 0, wx.ALL, 5)
        
        self.btn_zur = wx.Button(self, wx.ID_ANY, u"backward",
                           defPos, defSiz, 0)
        ri_szr20.Add(self.btn_zur, 0, wx.ALL, 5)
        
        self.zuSeite = wx.TextCtrl(self, wx.ID_ANY, u"1",
                             defPos, wx.Size(40, -1),
                             wx.TE_PROCESS_ENTER)
        ri_szr20.Add(self.zuSeite, 0, wx.ALL, 5)
        
        max_pages = wx.StaticText(self, wx.ID_ANY,
                            "of %s pages" % (str(PDFcfg.seiten),),
                            defPos, wx.Size(200, -1), 5)
        ri_szr20.Add(max_pages, 0, wx.ALIGN_CENTER, 5)
        # control line sizer composed, now add it to the vertical sizer
        ri_szr.Add(ri_szr20, 0, wx.EXPAND, 5)
        # define the bitmap for the pdf image ...
        self.PDFbild = wx.StaticBitmap(self, wx.ID_ANY,
                           wx.Bitmap(PDFcfg.pic,
                           wx.BITMAP_TYPE_PNG),
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
        self.Layout()

#==============================================================================
# bind buttons
#==============================================================================
        self.btn_neu.Bind(wx.EVT_BUTTON, self.insertRow)      # "new row"
        self.btn_chk.Bind(wx.EVT_BUTTON, self.DataOK)         # "check data"
        self.btn_vor.Bind(wx.EVT_BUTTON, self.forwPage)       # "forward"
        self.btn_zur.Bind(wx.EVT_BUTTON, self.backPage)       # "backward"
        self.zuSeite.Bind(wx.EVT_TEXT_ENTER, self.gotoPage)   # "page number"

    def __del__(self):
        pass

    def forwPage(self, event):
        seite = int(self.zuSeite.Value) + 1
        PicRefresh(seite)
        event.Skip()
    
    def backPage(self, event):
        seite = int(self.zuSeite.Value) - 1
        PicRefresh(seite)
        event.Skip()
    
    def gotoPage(self, event):
        seite = self.zuSeite.Value
        PicRefresh(seite)
        event.Skip()
        
#==============================================================================
# "insertRow" - Event Handler for new rows: insert a model row
#==============================================================================
    def insertRow(self, event):
        zeile = [1, "*** new row ***", 1, ""]
        self.szr20.Table.NewRow(zeile)
        DisableOK()
        self.Layout()

#==============================================================================
# Check Data: enable / disable OK button
#==============================================================================
    def DataOK(self, event):
        valide = True
        self.msg.Label = "Data OK!"
        d = self.szr20.GetTable()
        for i in range(self.szr20.Table.GetNumberRows()):
            if int(d.GetValue(i, 0)) < 1:
                valide = False
                self.msg.Label = "row %s: level < 1" % (str(i+1),)
                break
            if int(d.GetValue(i, 2)) > PDFcfg.seiten:
                valide = False
                self.msg.Label = "row %s: page > max pages" \
                                  % (str(i+1),)
                break
            if i > 0 and (int(d.GetValue(i, 0)) - int(d.GetValue(i-1, 0))) > 1:
                valide = False
                self.msg.Label = "row %s: level stepping > 1" % (str(i+1),)
                break
            if not d.GetValue(i, 1):
                valide = False
                self.msg.Label = "row %s: missing title" % (str(i+1),)
                break
            if d.GetValue(i, 3):
                valide = False
                self.msg.Label = "please delete row %s" % (str(i+1),)

        if not valide:
            self.szr40OK.Disable()
        else:
            self.szr40OK.Enable()
        self.Layout()

#==============================================================================
# display a PDF page
#==============================================================================
def PicRefresh(seite):
    i_seite = int(seite)
    i_seite = max(1, i_seite)           # ensure page number makes sense
    i_seite = min(PDFcfg.seiten, i_seite)
    
    dlg.zuSeite.Value = str(i_seite)
    
    if i_seite == PDFcfg.oldPage:     # same as last page - do nothing
        return
    
    PDFcfg.oldPage = i_seite          # save this page number in memory
    
    datei = PDFcfg.pics % (i_seite,)    # generate PNG filename
    if datei in PDFcfg.pic_pages:       # does this file exist already?
        pass
    else:
        PDFcfg.pic = datei              # memorize filename
        pdf_show(datei, i_seite)        # save PDF page to this file
        PDFcfg.pic_pages.append(datei)  # put its name into the list
        
    dlg.PDFbild.SetBitmap(wx.Bitmap(datei, wx.BITMAP_TYPE_PNG))
    dlg.PDFbild.Refresh(True)
    dlg.Layout()

#==============================================================================
# Disable OK button
#==============================================================================
def DisableOK():
    dlg.szr40OK.Disable()
    dlg.msg.Label = "Data have changed.\nPress Check Data (again) " \
                    + "before saving."

#==============================================================================
# Read PDF document information
#==============================================================================
def getPDFinfo():
    PDFcfg.doc = fitz.Document(PDFcfg.file)
    PDFcfg.inhalt = PDFcfg.doc.ToC()
    PDFcfg.seiten = PDFcfg.doc.pageCount
    PDFmeta = {"author":"", "title":"", "subject":""}
    for key in PDFcfg.doc.metadata:
        wert = PDFcfg.doc.metadata[key]
        if wert:
            PDFmeta[key] = wert.decode("utf-8")
        else:
            PDFmeta[key] = ""
    PDFcfg.meta = PDFmeta
    return PDFcfg.doc.needsPass

#==============================================================================
# Write the changed PDF file
#============================================================================
def make_pdf(dlg):
    # if outline table contains nothing interesting: do nothing!
    if len(dlg.szr20.Table.data) < 1:
        return
    # create a PDF compatible timestamp
    cdate = wx.DateTime.Now().Format("D:%Y%m%d%H%M%S-04'30'") 
    # free MuPDF resources, because the input must be closed if overwritten
    PDFcfg.doc.close()
    PDFmeta = {"/Creator":"PDF Outline Editor",
               "/Producer":"python-fitz, PyPDF2",
               "/CreationDate": cdate,
               "/ModDate": cdate,
               "/Title":dlg.austit.Value,
               "/Author":dlg.ausaut.Value,
               "/Subject":dlg.aussub.Value}

#==============================================================================
# We need PyPDF2 for writing the updated PDF file.
# PdfFileMerger would have been more practical (and perhaps faster?), but it
# contains a bug in its addBookmark method (which is amazingly different from
# the method with the same name in the PdfFileWriter class).
#==============================================================================
    infile = open(PDFcfg.file, "rb")
    PDFif = PyPDF2.PdfFileReader(infile)      
    PDFof = PyPDF2.PdfFileWriter()
    for p in range(PDFcfg.seiten):        # first just copy all pages to output
        page = PDFif.getPage(p)
        # this obviously just means storing a pointer to the page somewhere
        PDFof.addPage(page)
        
#==============================================================================
# add the meta data    
#==============================================================================
    PDFof.addMetadata(PDFmeta)
#==============================================================================
# lvl_tab stores last bookmark of indent level corresponding to index - 1
#==============================================================================
    lvl_tab = [0] * max([int(z[0]) for z in dlg.szr20.Table.data])
#==============================================================================
# store our outline entries as bookmarks
#==============================================================================
    for z in dlg.szr20.Table.data:
        lvl = int(z[0])
        pag = int(z[2]) - 1
        tit = z[1].strip()
        tit = tit.encode("cp1252", "replace")
        if lvl == 1:                        # no parent if level 1
            bm = PDFof.addBookmark(tit, pag, None, None, False, False, "/Fit")
            lvl_tab[0] = bm                 # memorize it: serves as parent!
        else:
            # parent = last entry of next higher level
            bm = PDFof.addBookmark(tit, pag, lvl_tab[lvl - 2], 
            None, False, False, "/Fit")
            lvl_tab[lvl - 1] = bm           # memorize it: serves as parent!
#==============================================================================
# before saving anything, check the outfile situation
#==============================================================================
    outfile = dlg.btn_aus.GetPath()         # get dir & name of file in screen  
    outfile_dir, outfile_name = os.path.split(outfile)

    if outfile != PDFcfg.file:              # if outfile != input file
        PDFof_fle = open(dlg.btn_aus.GetPath(), "wb")
    else:                                   # equal: replace input file 
        PDFcfg.TempPDF(dir = outfile_dir)   # first create temp file
        PDFof_fle = PDFcfg.opdffile         # use it as output
        
    PDFof.write(PDFof_fle)                  # write new content to it
    infile.close()                          # close input file
    PDFof_fle.close()                       # close output file
        
    if outfile != PDFcfg.file:              # done if output != input
        return
    
    # remove the old input file, rename temp file to input file name
    try:
        os.remove(PDFcfg.file)
        os.rename(PDFcfg.opdfname, PDFcfg.file)
        return
    except:
        pass
#==============================================================================
#   Input file is in use, save the precious work to another name
#==============================================================================
    new_file = outfile
    while new_file == outfile:
        dlg = wx.FileDialog(None,
                message="Input file is still in use, choose another name",
                defaultDir = outfile_dir, defaultFile = outfile_name,
                style=wx.SAVE)
        rc = dlg.ShowModal()
        if rc != wx.ID_OK:               # user is giving up, so do we
            os.remove(PDFcfg.opdfname)   # remove the temp file
            return
        new_file = dlg.GetPath()
        if os.path.exists(new_file):
            new_file = outfile
        dlg.Destroy()
        
    os.rename(PDFcfg.opdfname, new_file)
        

#==============================================================================
#
# Main Program
#
#==============================================================================
app = None
app = wx.App()
#==============================================================================
# let user select the file. can only allow true PDFs, because of PyPDF2
#==============================================================================
dlg = wx.FileDialog(None, message = "Choose a PDF file to edit",
                        defaultDir = os.path.expanduser('~'), defaultFile = "",
                        wildcard = "PDF files (*.pdf)|*.pdf",
                        style=wx.OPEN | wx.CHANGE_DIR)
# We got a file only when one was selected and OK pressed
if dlg.ShowModal() == wx.ID_OK:
    # This returns a Python list of selected files.
    infile = dlg.GetPaths()[0]
else:
    infile = None
# destroy this dialog
dlg.Destroy()

if infile:
    PDFcfg = PDFconfig()        # create our PDF descriptor scratchpad
    PDFcfg.file = infile
#==============================================================================
# Generate PDF page 1 image
#==============================================================================
    if getPDFinfo() == 0:              # input is not encrypted
        pdf_show(PDFcfg.pic, 1)
        PDFcfg.oldPage = 1
        dlg = PDFDialog(None)
        
#==============================================================================
# Show dialog
#==============================================================================
        rc = dlg.ShowModal()    
#==============================================================================
# Generate modified PDF file
#==============================================================================
        if rc == wx.ID_OK:              # output PDF only if OK pressed
            make_pdf(dlg)
        dlg.Destroy()
        app = None
        # delete all pdf page images accumulated during the process
        for datei in PDFcfg.pic_pages:
            os.remove(datei)
    else:
        wx.MessageBox("Cannot edit encrypted file\n" + infile,
                      "Encrypted File Error")
        
