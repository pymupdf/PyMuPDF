#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Created on Sun Jun 07 06:57:08 2015

@author: Jorj McKie
Copyright (c) 2015 Jorj X. McKie

The license of this program is governed by the GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007. See the "COPYING" file of this repository.

This is an example for using the Python bindings PyMuPDF for MuPDF.

This program joins PDF files into one output file. Its features include:
* Selection of page ranges - in ascending or descending sequence
* Optional rotation in steps of 90 degrees
* Copy any table of content segments to the output (can be switched off)
* Specify PDF metadata of resulting PDF

Dependencies:
wxPython v3.0.x, PyMuPDF v1.9.2

Changes 2016-10-27
------------------
Now also runs under Python 3, since wxPython supports it.

Changes 2016-08-06
-------------------
Dependency on PyPDF2 has been removed, because v1.9.2 of PyMuPDF now has all
required functionality.
This also has generated a **huge** speed improvement!
"""
from __future__ import print_function
import os, sys, time
print("Python:", sys.version)
try:
    import wx
    import wx.grid as gridlib
    import wx.lib.gridmovers as gridmovers
except:
    print(__file__, "needs wxPython.")
    raise SystemExit
print("wxPython:", wx.version())
    
try:
    import fitz
except:
    print(__file__, "needs PyMuPDF (fitz).")
    raise SystemExit
print(fitz.__doc__)

try:
    from icons import ico_pdf
    show_icon = True
except:
    show_icon = False
    
# some abbreviations
defPos = wx.DefaultPosition
defSiz = wx.DefaultSize
khaki  = wx.Colour(240, 230, 140)

# make some adjustments between wxPython versions
if wx.version() >= "3.0.3":
    table_base = gridlib.GridTableBase
else:
    table_base = gridlib.PyGridTableBase
    
class PDFTable(table_base):
    def __init__(self):
        table_base.__init__(self)

        self.colLabels = ['File','Pages','from','to','rotate']
        self.dataTypes = [gridlib.GRID_VALUE_STRING,
                          gridlib.GRID_VALUE_NUMBER,
                          gridlib.GRID_VALUE_NUMBER,
                          gridlib.GRID_VALUE_NUMBER,
                          gridlib.GRID_VALUE_NUMBER,
                          ]

        self.data = []

#==============================================================================
# Methods for the wxPyGridTableBase interface (mostly mandatory)
#==============================================================================

    def GetNumberRows(self):
        return len(self.data)

    def GetNumberCols(self):
        return len(self.colLabels)

    def IsEmptyCell(self, row, col):
        try:
            return not self.data[row][col]
        except IndexError:
            return True

    def GetValue(self, row, col):
        return str(self.data[row][col])

    def SetValue(self, row, col, value):
        self.data[row][col] = value

#==============================================================================
# Provide column header names
#==============================================================================
    def GetColLabelValue(self, col):
        return self.colLabels[col]

#==============================================================================
# Provide row header names (just the line numbers in our case)
#==============================================================================
    def GetRowLabelValue(self,row):
        return str(row +1)

#==============================================================================
# Provide type of a cell value
#==============================================================================
    def GetTypeName(self, row, col):
        return self.dataTypes[col]

#==============================================================================
# Move a row
#==============================================================================
    def MoveRow(self,frm,to):
        grid = self.GetView()

        if grid:
            # Move the rowLabels and data rows
            oldData = self.data[frm]
            del self.data[frm]

            if to > frm:
                self.data.insert(to-1,oldData)
            else:
                self.data.insert(to,oldData)
#==============================================================================
#           inform the grid about our doing
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
# Insert a row
#==============================================================================
    def NewRow(self, zeile):
        grid = self.GetView()
        if grid:
            self.data.append(zeile)
            grid.BeginBatch()
            msg = gridlib.GridTableMessage(
                   self, gridlib.GRIDTABLE_NOTIFY_ROWS_APPENDED, 1)
            grid.ProcessTableMessage(msg)
            grid.EndBatch()

#==============================================================================
# Duplicate a row
#==============================================================================
    def DuplicateRow(self, row):
        grid = self.GetView()
        if grid:
            zeile = [self.data[row][0], self.data[row][1],
                     self.data[row][2], self.data[row][3],
                     self.data[row][4]]
            self.data.insert(row, zeile)
            grid.BeginBatch()
            msg = gridlib.GridTableMessage(
                    self, gridlib.GRIDTABLE_NOTIFY_ROWS_INSERTED, row, 1)
            grid.ProcessTableMessage(msg)
            grid.EndBatch()

#==============================================================================
# Remove a row
#==============================================================================
    def DeleteRow(self, row):
        grid = self.GetView()
        if grid:
            del self.data[row]
            grid.BeginBatch()
            msg = gridlib.GridTableMessage(self,
                    gridlib.GRIDTABLE_NOTIFY_ROWS_DELETED, row, 1)
            grid.ProcessTableMessage(msg)
            grid.EndBatch()

#==============================================================================
# Define the grid
#==============================================================================
class MyGrid(gridlib.Grid):
    def __init__(self, parent):
        gridlib.Grid.__init__(self, parent, -1)

        table = PDFTable()      # create PDFTable object

#==============================================================================
# Announce our table to the grid and let it manage it ('True')
#==============================================================================
        self.SetTable(table, True)

#==============================================================================
# do some cell attribute setting
#==============================================================================
        align1 = gridlib.GridCellAttr()
        align1.SetAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
        self.SetColAttr(2, align1)
        self.SetColAttr(3, align1)
        self.SetColAttr(4, align1)
        align2 = gridlib.GridCellAttr()
        align2.SetAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        self.SetColAttr(5, align2)

#==============================================================================
# Enable Row moving
#==============================================================================
        gridmovers.GridRowMover(self)

#==============================================================================
# Bind: move a row
#==============================================================================
        self.Bind(gridmovers.EVT_GRID_ROW_MOVE, self.OnRowMove, self)
#==============================================================================
# Bind: delete a row
#==============================================================================
        self.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.OnRowDel, self)
#==============================================================================
# Bind: duplicate a row
#==============================================================================
        self.Bind(gridlib.EVT_GRID_LABEL_LEFT_DCLICK, self.OnRowDup, self)

#==============================================================================
# Event Method: move a row
#==============================================================================
    def OnRowMove(self,evt):
        frm = evt.GetMoveRow()          # Row being moved
        to = evt.GetBeforeRow()         # Before which row to insert
        self.GetTable().MoveRow(frm,to)

#==============================================================================
# Event Method: delete a row
#==============================================================================
    def OnRowDel(self, evt):
        row = evt.GetRow()
        col = evt.GetCol()
        if row < 0 or col >= 0 or not evt.ControlDown():
            evt.Skip()
            return
        self.GetTable().DeleteRow(row)
        evt.Skip()

#==============================================================================
# Event Method: duplicate a row
#==============================================================================
    def OnRowDup(self, evt):
        row = evt.GetRow()
        col = evt.GetCol()
        if col < 0 and row >= 0:       # else it is not a row duplication!
            self.GetTable().DuplicateRow(row)
        evt.Skip()

#==============================================================================
#
# Define the dialog
#
#==============================================================================
class PDFDialog (wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__ (self, parent, id = wx.ID_ANY,
                             title = u"Join PDF files",
                             pos = defPos,
                             size = wx.Size(900,710),
                             style = wx.CAPTION|
                                     wx.CLOSE_BOX|
                                     wx.DEFAULT_DIALOG_STYLE|
                                     wx.MAXIMIZE_BOX|
                                     wx.MINIMIZE_BOX|
                                     wx.RESIZE_BORDER)
        self.FileList = {}
        if show_icon: self.SetIcon(ico_pdf.img.GetIcon())
        self.SetBackgroundColour(khaki)

#==============================================================================
# Create Sizer 01 (browse button and explaining text)
#==============================================================================
        szr01 = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_neu = wx.FilePickerCtrl(self, wx.ID_ANY,
                        wx.EmptyString,
                        u"Select a PDF file",
                        u"*.pdf",
                        defPos, defSiz,
                        wx.FLP_CHANGE_DIR|wx.FLP_FILE_MUST_EXIST|wx.FLP_SMALL,
                        )
        szr01.Add(self.btn_neu, 0, wx.ALIGN_TOP|wx.ALL, 5)

        msg_txt ="""ADD files with this button. Path and total page number will be appended to the table below.\nDUPLICATE row: double-click its number. MOVE row: drag its number with the mouse. DELETE row: CTRL+RightClick its number.\nAdjust "from" / "to" (also for reversing sequences)."""
        msg = wx.StaticText(self, wx.ID_ANY, msg_txt,
                    defPos, wx.Size(-1, 50), wx.ALIGN_LEFT)
        msg.Wrap(-1)
        msg.SetFont(wx.Font(10, 74, 90, 90, False, "Arial"))

        szr01.Add(msg, 0, wx.ALIGN_TOP|wx.ALL, 5)

#==============================================================================
# Create Sizer 02 (contains the grid)
#==============================================================================
        self.szr02 = MyGrid(self)
        self.szr02.AutoSizeColumn(0)
        self.szr02.AutoSizeColumn(1)
        self.szr02.SetColSize(2, 45)
        self.szr02.SetColSize(3, 45)
        self.szr02.SetColSize(4, 45)
        self.szr02.SetRowLabelSize(30)
        # Columns 1 and 2 are read only
        attr_ro = gridlib.GridCellAttr()
        attr_ro.SetReadOnly(True)
        self.szr02.SetColAttr(0, attr_ro)
        self.szr02.SetColAttr(1, attr_ro)

#==============================================================================
# Create Sizer 03 (output parameters)
#==============================================================================
        szr03 = wx.FlexGridSizer( 6, 2, 0, 0 )   # 6 rows, 2 cols, gap sizes 0
        szr03.SetFlexibleDirection( wx.BOTH )
        szr03.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        tx_ausdat = wx.StaticText(self, wx.ID_ANY, u"Output:",
                            defPos, defSiz, 0)
        szr03.Add(tx_ausdat, 0, wx.ALL|wx.ALIGN_RIGHT, 5)

        self.btn_aus = wx.FilePickerCtrl(self, wx.ID_ANY,
                        os.path.join(os.path.expanduser('~'), "joined.pdf"),
                        u"Specify output file",
                        u"*.pdf",
                        defPos, wx.Size(480,-1),
                        wx.FLP_OVERWRITE_PROMPT|
                        wx.FLP_SAVE|wx.FLP_SMALL|
                        wx.FLP_USE_TEXTCTRL)
        szr03.Add(self.btn_aus, 0, wx.ALL, 5)

        tx_autor = wx.StaticText( self, wx.ID_ANY, u"Author:",
                         defPos, defSiz, 0 )
        szr03.Add( tx_autor, 0, wx.ALIGN_RIGHT, 5 )

        self.ausaut = wx.TextCtrl( self, wx.ID_ANY,
                       os.path.basename(os.path.expanduser('~')),
                       defPos, wx.Size(480, -1), wx.NO_BORDER)
        szr03.Add( self.ausaut, 0, wx.LEFT, 5 )

        pdf_titel = wx.StaticText( self, wx.ID_ANY, u"Title:",
                          defPos, defSiz, 0 )
        szr03.Add( pdf_titel, 0, wx.ALIGN_RIGHT, 5 )

        self.austit = wx.TextCtrl( self, wx.ID_ANY, u"Joined PDF files",
                       defPos, wx.Size(480, -1), wx.NO_BORDER )
        szr03.Add( self.austit, 0, wx.LEFT, 5 )

        tx_subject = wx.StaticText( self, wx.ID_ANY, u"Subject:",
                           defPos, defSiz, wx.ALIGN_RIGHT)
        szr03.Add( tx_subject, 0, wx.ALIGN_RIGHT, 5 )

        self.aussub = wx.TextCtrl( self, wx.ID_ANY, u"Joined PDF files",
                       defPos, wx.Size(480, -1), wx.NO_BORDER )
        szr03.Add( self.aussub, 0, wx.LEFT, 5 )

        tx_keywords = wx.StaticText(self, wx.ID_ANY, "Keywords:",
                           defPos, defSiz, 0)
        szr03.Add(tx_keywords, 0, wx.ALIGN_RIGHT, 5)

        self.keywords = wx.TextCtrl(self, wx.ID_ANY, u" ",
                       defPos, wx.Size(480, -1), wx.NO_BORDER)
        szr03.Add(self.keywords, 0, wx.LEFT, 5)
        tx_blank = wx.StaticText( self, wx.ID_ANY, u" ",
                           defPos, defSiz, wx.ALIGN_RIGHT)
        szr03.Add( tx_blank, 0, wx.RIGHT, 5 )
        self.noToC = wx.CheckBox( self, wx.ID_ANY,
                           u"check to suppress table of content",
                           defPos, defSiz, wx.ALIGN_LEFT)
        szr03.Add( self.noToC, 0, wx.ALL, 5 )


#==============================================================================
# Create Sizer 04 (OK / Cancel buttons)
#==============================================================================
        szr04 = wx.StdDialogButtonSizer()
        szr04OK = wx.Button(self, wx.ID_OK, "SAVE",
                            defPos, defSiz, wx.BU_EXACTFIT)
        szr04.AddButton(szr04OK)
        szr04Cancel = wx.Button(self, wx.ID_CANCEL, "QUIT",
                                defPos, defSiz, wx.BU_EXACTFIT)
        szr04.AddButton(szr04Cancel)
        szr04.Realize();

#==============================================================================
# 3 horizontal lines (decoration only)
#==============================================================================
        linie1 = wx.StaticLine(self, wx.ID_ANY,
                       defPos, defSiz, wx.LI_HORIZONTAL)
        linie2 = wx.StaticLine(self, wx.ID_ANY,
                       defPos, defSiz, wx.LI_HORIZONTAL)
        linie3 = wx.StaticLine(self, wx.ID_ANY,
                       defPos, defSiz, wx.LI_HORIZONTAL)

        mainszr = wx.BoxSizer(wx.VERTICAL)
        mainszr.Add(szr01, 0, wx.EXPAND, 5)
        mainszr.Add(linie1, 0, wx.EXPAND |wx.ALL, 5)
        mainszr.Add(self.szr02, 1, wx.EXPAND, 5)
        mainszr.Add(linie2, 0, wx.EXPAND|wx.ALL, 5)
        mainszr.Add(szr03, 0, wx.EXPAND|wx.ALL, 5)
        mainszr.Add(linie3, 0, wx.EXPAND |wx.ALL, 5)
        mainszr.Add(szr04, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        self.SetSizer(mainszr)
        self.Layout()

        self.Centre(wx.BOTH)

#==============================================================================
# Define event handlers for the buttons
#==============================================================================
        self.btn_neu.Bind(wx.EVT_FILEPICKER_CHANGED, self.NewFile)
        self.btn_aus.Bind(wx.EVT_FILEPICKER_CHANGED, self.AusgabeDatei)

    def __del__(self):
        pass

#==============================================================================
# "NewFile" - Event Handler for including new files
#==============================================================================
    def NewFile(self, event):
        pdf = event.GetPath()
        if pdf not in self.FileList:
            doc = fitz.Document(pdf)
            if doc.needsPass:
                wx.MessageBox("Cannot process encrypted file\n" + pdf,
                      "Encrypted File Error")
                doc.close()
                event.Skip()
                return
            self.FileList[pdf] = len(doc)
            doc.close()
        seiten = self.FileList[pdf]
        zeile = [pdf, str(seiten), 1, str(seiten), -1]
        self.szr02.Table.NewRow(zeile)
        self.szr02.AutoSizeColumn(0)
        self.Layout()
        event.Skip()

#==============================================================================
# "AusgabeDatei" - Event Handler for out file
#==============================================================================
    def AusgabeDatei(self, event):
        event.Skip()

#==============================================================================
# Create the joined PDF
#==============================================================================
def make_pdf(dlg):
    # no file selected: treat like "QUIT"
    if not len(dlg.szr02.Table.data):       # no files there - quit
        return None
    # create time zone value in PDF format
    cdate = fitz.getPDFnow()
    ausgabe = dlg.btn_aus.GetPath()
    pdf_out = fitz.open()              # empty new PDF document
    aus_nr = 0                         # current page number in output
    pdf_dict = {"creator": "PDF Joiner",
                "producer": "PyMuPDF",
                "creationDate": cdate,
                "modDate": cdate,
                "title": dlg.austit.Value,
                "author": dlg.ausaut.Value,
                "subject": dlg.aussub.Value,
                "keywords": dlg.keywords.Value}
    pdf_out.setMetadata(pdf_dict)      # put in meta data
    total_toc = []                     # initialize TOC
#==============================================================================
# process one input file
#==============================================================================
    for zeile in dlg.szr02.Table.data:
        dateiname = zeile[0]
        doc = fitz.open(dateiname)
        max_seiten = len(doc)
#==============================================================================
# user input minus 1, PDF pages count from zero
# also correct any inconsistent input
#==============================================================================
        von = int(zeile[2]) - 1             # first PDF page number
        bis = int(zeile[3]) - 1             # last PDF page number

        von = min(max(0, von), max_seiten - 1)   # "from" must be in range
        bis = min(max(0, bis), max_seiten - 1)   # "to" must be in range
        rot = int(zeile[4])                 # get rotation angle
        # now copy the page range
        pdf_out.insertPDF(doc, from_page = von, to_page = bis,
                          rotate = rot)
        if dlg.noToC.Value:                 # no ToC wanted - get next file
            continue

        incr = 1                            # standard increment for page range
        if bis < von:
            incr = -1                       # increment for reversed sequence
        # list of page numbers in range
        pno_range = list(range(von, bis + incr, incr))
        # standard bokkmark title = "infile [pp from-to of max.pages]"
        bm_main_title = "%s [pp. %s-%s of %s]" % \
              (os.path.basename(dateiname[:-4]), von + 1,
               bis + 1, max_seiten)
        # insert standard bookmark ahead of any page range
        total_toc.append([1, bm_main_title, aus_nr + 1])
        toc = doc.getToC(simple = False)    # get file's TOC
        last_lvl = 1                        # immunize against hierarchy gaps
        for t in toc:
            lnk_type = t[3]["kind"]         # if "goto", page must be in range
            if (t[2] - 1) not in pno_range and lnk_type == fitz.LINK_GOTO:
                continue
            if lnk_type == fitz.LINK_GOTO:
                pno = pno_range.index(t[2] - 1) + aus_nr + 1
            # repair hierarchy gaps by filler bookmarks
            while (t[0] > last_lvl + 1):
                total_toc.append([last_lvl + 1, "<>", pno, t[3]])
                last_lvl += 1
            last_lvl = t[0]
            t[2] = pno
            total_toc.append(t)

        aus_nr += len(pno_range)       # increase output counter
        doc.close()
        doc = None

#==============================================================================
# all input files processed
#==============================================================================
    if total_toc:
        pdf_out.setToC(total_toc)
    pdf_out.save(ausgabe)
    pdf_out.close()
    return ausgabe

#==============================================================================
#
# Main program
#
#==============================================================================
assert (wx.VERSION[0], wx.VERSION[1], wx.VERSION[2]) >= (3,0,2), "need wxPython 3.0.2 or later"
assert [int(x) for x in fitz.VersionBind.split(".")] >= [1,11,0], "need PyMuPDF 1.11.0 or later"
app = None
app = wx.App()
this_dir = os.getcwd()

#==============================================================================
# create dialog, show it and wait
#==============================================================================
dlg = PDFDialog(None)
rc = dlg.ShowModal()

#==============================================================================
# if SAVE pressed, create output PDF
#==============================================================================
if rc == wx.ID_OK:
    ausgabe = make_pdf(dlg)
dlg.Destroy()
app = None
