# -*- coding: utf-8 -*-
"""
Created on Sun Jun 07 06:57:08 2015

@author: Jorj McKie
Copyright (c) 2015 Jorj X. McKie

The license of this program is governed by the GNU GENERAL PUBLIC LICENSE 
Version 3, 29 June 2007. See the "COPYING" file of this repository.

This is an example for using the Python binding python-fitz of MuPDF.

This program joins PDF files into one output file. Its features include:
* Selection of page ranges
* Optional rotation in steps of 90 degrees
* Copying any table of contents to the output

Please note that you need wxPython version of 3.x
"""

import os
import wx
import wx.grid as gridlib
import wx.lib.gridmovers as gridmovers
import PyPDF2                          # only used for output (make_pdf)
import fitz

class PDFTable(gridlib.PyGridTableBase):
    def __init__(self):
        gridlib.PyGridTableBase.__init__(self)

        self.colLabels = ['File','Pages','from','to','rotate','del?']
        self.dataTypes = [gridlib.GRID_VALUE_STRING,
                          gridlib.GRID_VALUE_NUMBER,
                          gridlib.GRID_VALUE_NUMBER,
                          gridlib.GRID_VALUE_NUMBER,
                          gridlib.GRID_VALUE_CHOICE + ':0, 90, 180, 270',
                          gridlib.GRID_VALUE_BOOL
                          ]

        self.data = [["Delete: check the box and right-click cell",
                      '', '', '', '', u"1"]]

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
        return self.data[row][col]

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
                     self.data[row][4], self.data[row][5],]
            self.data.insert(row, zeile)
            grid.BeginBatch()
            msg = gridlib.GridTableMessage(
                    self, gridlib.GRIDTABLE_NOTIFY_ROWS_INSERTED, row, 1)
            grid.ProcessTableMessage(msg)
            grid.EndBatch()
            
#==============================================================================
# Remove a row
#==============================================================================
    def DeleteRow(self, row, col):
        grid = self.GetView()
        if grid:
            if self.data[row][col]:
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
        self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.OnRowDel, self)
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
        self.GetTable().DeleteRow(row, col)

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
                             pos = wx.Point(-1, -1),
                             size = wx.Size(900,710),
                             style = wx.CAPTION|
                                     wx.CLOSE_BOX|
                                     wx.DEFAULT_DIALOG_STYLE|
                                     wx.MAXIMIZE_BOX|
                                     wx.MINIMIZE_BOX|
                                     wx.RESIZE_BORDER)
        
        self.SetSizeHintsSz(wx.Size(-1, -1), wx.Size(-1, -1))
        self.FileList = {}
#==============================================================================
# Create Sizer 01 (browse button and explaining text)
#==============================================================================
        szr01 = wx.BoxSizer(wx.HORIZONTAL)
        
        self.btn_neu = wx.FilePickerCtrl(self, wx.ID_ANY,
                        wx.EmptyString,
                        u"Select a PDF file",
                        u"*.pdf",
                        wx.Point(-1, -1), wx.Size(-1, -1),
                        wx.FLP_CHANGE_DIR|wx.FLP_FILE_MUST_EXIST|wx.FLP_SMALL,
                        )
        szr01.Add(self.btn_neu, 0, wx.ALIGN_TOP|wx.ALL, 5)
 
        msg_txt ="""ADD files with this button. Path and total page number will be appended to the table below.\nDUPLICATE row: double-click its number. MOVE row: drag it with the mouse. DELETE row: check the box and right-click its cell."""
        msg = wx.StaticText(self, wx.ID_ANY, msg_txt,
                    wx.Point(-1, -1), wx.Size(-1, 50), wx.ALIGN_LEFT)
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
        self.szr02.AutoSizeColumn(5)
        self.szr02.SetRowLabelSize(30)
        # Columns 1 and 2 are read only
        attr_ro = gridlib.GridCellAttr()
        attr_ro.SetReadOnly(True)
        self.szr02.SetColAttr(0, attr_ro)
        self.szr02.SetColAttr(1, attr_ro)
          
#==============================================================================
# Create Sizer 03 (output parameters)
#==============================================================================
        szr03 = wx.FlexGridSizer( 4, 2, 0, 0 )   # 4 rows, 2 cols, gap sizes 0
        szr03.SetFlexibleDirection( wx.BOTH )
        szr03.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
        
        tx_ausdat = wx.StaticText(self, wx.ID_ANY, u"Output:",
                            wx.Point(-1, -1), wx.Size(-1, -1), 0)
        tx_ausdat.Wrap(-1)
        szr03.Add(tx_ausdat, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        
        self.btn_aus = wx.FilePickerCtrl(self, wx.ID_ANY,
                        os.path.join(os.path.expanduser('~'), "joined.pdf"),
                        u"Specify output file",
                        u"*.pdf",
                        wx.Point(-1, -1), wx.Size(480,-1),
                        wx.FLP_OVERWRITE_PROMPT|
                        wx.FLP_SAVE|wx.FLP_SMALL|
                        wx.FLP_USE_TEXTCTRL)
        szr03.Add(self.btn_aus, 0, wx.ALL, 5)
        tx_autor = wx.StaticText( self, wx.ID_ANY, u"Author:",
                         wx.DefaultPosition, wx.DefaultSize, 0 )
        tx_autor.Wrap( -1 )
        szr03.Add( tx_autor, 0, wx.ALL, 5 )
        
        self.ausaut = wx.TextCtrl( self, wx.ID_ANY,
                       os.path.basename(os.path.expanduser('~')),
                       wx.DefaultPosition, wx.Size(480, -1), 0)
        szr03.Add( self.ausaut, 0, wx.ALL, 5 )
        
        pdf_titel = wx.StaticText( self, wx.ID_ANY, u"Title:",
                          wx.DefaultPosition, wx.DefaultSize, 0 )
        pdf_titel.Wrap( -1 )
        szr03.Add( pdf_titel, 0, wx.ALL, 5 )
        
        self.austit = wx.TextCtrl( self, wx.ID_ANY,
                       u"Joined PDF files",
                       wx.DefaultPosition, wx.Size(480, -1), 0 )
        szr03.Add( self.austit, 0, wx.ALL, 5 )
        
        tx_subject = wx.StaticText( self, wx.ID_ANY, u"Subject:",
                           wx.DefaultPosition, wx.DefaultSize, 0 )
        tx_subject.Wrap( -1 )
        szr03.Add( tx_subject, 0, wx.ALL, 5 )
        
        self.aussub = wx.TextCtrl( self, wx.ID_ANY,
                       u"Joined PDF files",
                       wx.DefaultPosition, wx.Size(480, -1), 0 )
        szr03.Add( self.aussub, 0, wx.ALL, 5 )
            
#==============================================================================
# Create Sizer 04 (OK / Cancel buttons)
#==============================================================================
        szr04 = wx.StdDialogButtonSizer()
        szr04OK = wx.Button(self, wx.ID_OK)
        szr04.AddButton(szr04OK)
        szr04Cancel = wx.Button(self, wx.ID_CANCEL)
        szr04.AddButton(szr04Cancel)
        szr04.Realize();

#==============================================================================
# 3 horizontal lines (decoration only)
#==============================================================================
        linie1 = wx.StaticLine(self, wx.ID_ANY,
                       wx.Point(-1, -1), wx.Size(-1, -1), wx.LI_HORIZONTAL)
        linie2 = wx.StaticLine(self, wx.ID_ANY,
                       wx.Point(-1, -1), wx.Size(-1, -1), wx.LI_HORIZONTAL)
        linie3 = wx.StaticLine(self, wx.ID_ANY,
                       wx.Point(-1, -1), wx.Size(-1, -1), wx.LI_HORIZONTAL)

        mainszr = wx.BoxSizer(wx.VERTICAL)
        mainszr.Add(szr01, 0, wx.EXPAND, 5)
        mainszr.Add(linie1, 0, wx.EXPAND |wx.ALL, 5)
        mainszr.Add(self.szr02, 1, wx.EXPAND, 5)
        mainszr.Add(linie2, 0, wx.EXPAND|wx.ALL, 5)
        mainszr.Add(szr03, 0, wx.EXPAND, 5)
        mainszr.Add(linie3, 0, wx.EXPAND |wx.ALL, 5)
        mainszr.Add(szr04, 0, wx.ALIGN_TOP|wx.ALIGN_CENTER_HORIZONTAL, 5)
        
        self.SetSizer(mainszr)
        self.Layout()
        
        self.Centre(wx.BOTH)

#==============================================================================
# Define event handler for the buttons
#==============================================================================
        self.btn_neu.Bind(wx.EVT_FILEPICKER_CHANGED, self.NewFile)
        self.btn_aus.Bind(wx.EVT_FILEPICKER_CHANGED, self.AusgabeDatei)
    
    def __del__(self):
        pass
    
#==============================================================================
# "NewFile" - Event Handler for including new files
#==============================================================================
    def NewFile(self, event):
        dat = event.GetPath()
        if dat not in self.FileList:
            doc = fitz.Document(dat)
            if doc.needsPass:
                wx.MessageBox("Cannot read encrypted file\n" + dat,
                      "Encrypted File Error")
                event.Skip()
                return
            self.FileList[dat] = doc
        else:
            doc = self.FileList[dat]
        seiten = doc.pageCount
        zeile = [dat, str(seiten), 1, str(seiten), 0, ""]
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
    # no file selected: treat like "Cancel"
    if not len(dlg.szr02.Table.data):       # no files there
        return
    # also do nothing if all entries are marked for delete
    if min([z[5] for z in dlg.szr02.Table.data]) == "1":
        return
    cdate = wx.DateTime.Now().Format("D:%Y%m%d%H%M%S-04'30'")
    ausgabe = dlg.btn_aus.GetPath()
    pdf_fle_out = open(ausgabe,"wb")
    pdf_out = PyPDF2.PdfFileWriter()
    aus_nr = 0                              # current page number in output
    pdf_dict = {"/Creator":"PDF-Joiner",
                "/Producer":"python-fitz, PyPDF2",
                "/CreationDate": cdate,
                "/ModDate": cdate,
                "/Title": dlg.austit.Value,
                "/Author": dlg.ausaut.Value,
                "/Subject": dlg.aussub.Value}
    pdf_out.addMetadata(pdf_dict)
    parents = {}
#==============================================================================
# process one input file
#==============================================================================
    for zeile in dlg.szr02.Table.data:
        if zeile[5] == "1":                 # this is a deleted row
            continue
        dateiname = zeile[0]
        doc = dlg.FileList[dateiname]
        max_seiten = int(zeile[1])
#==============================================================================
# user input minus 1, PDF pages count from zero
# also correct any inconsistent input
#==============================================================================
        von = int(zeile[2]) - 1
        bis = int(zeile[3]) - 1

        von = max(0, von)                   # "from" must not be < 0
        bis = min(max_seiten - 1, bis)      # "to" must not be > max pages - 1
        bis = max(von, bis)                 # "to" cannot be < "from"
        rot = int(zeile[4])                 # get rotation angle

        pdfin = PyPDF2.PdfFileReader(dateiname)
        for p in range(von, bis + 1):       # read pages from input file
            pdf_page = pdfin.getPage(p)
            if rot > 0:
                pdf_page.rotateClockwise(rot)  # rotate the page
            pdf_out.addPage(pdf_page)          # output the page
        
        # title = "infile [from-to (max.pages)]"
        bm_main_title = "%s [%s-%s (%s)]" % \
              (os.path.basename(dateiname[:-4]).encode("cp1252"), von + 1,
               bis + 1, max_seiten)
              
        bm_main = pdf_out.addBookmark(bm_main_title, aus_nr,
               None, None, False, False, "/Fit")
        print 1, bm_main_title, aus_nr
        
        parents[1] = bm_main           # lvl 1 bookmark is infile's title

        toc = doc.ToC()                # get infile's table of contents
        bm_lst = []                    # prepare the relevant sub-ToC
        for t in toc:                  
            if t[2] >= von and t[2] <= bis:      # relevant page range only
                bm_lst.append([t[0] + 1,         # indent increased 1 level 
                               t[1],             # the title
                               t[2] + aus_nr - von])  # new page number

        aus_nr += (bis - von + 1)      # increase output counter
        
        if bm_lst == []:               # do we have a sub-ToC?
            continue                   # no, next infile
        # while indent gap is too large, prepend "filler" bookmarks to bm_lst
        while bm_lst[0][0] > 2:
            zeile = [bm_lst[0][0] - 1, "<>", bm_lst[0][2]]
            bm_lst.insert(0, zeile)
        # now add infile's bookmarks
        for b in bm_lst:
            bm = pdf_out.addBookmark(b[1].encode("cp1252"), b[2],
                    parents[b[0]-1], None, False, False, "/Fit")
            parents[b[0]] = bm
#==============================================================================
# all input files processed
#==============================================================================
    pdf_out.write(pdf_fle_out)
    pdf_fle_out.close()

#==============================================================================
#
# Main program
#
#==============================================================================
app = None
app = wx.App()

#==============================================================================
# create dialog
#==============================================================================
dlg = PDFDialog(None)

#==============================================================================
# Show dialog and wait ...
#==============================================================================
rc = dlg.ShowModal()

#==============================================================================
# if OK pressed, create output PDF
#==============================================================================
if rc == wx.ID_OK:
    make_pdf(dlg)
dlg.Destroy()
app = None
