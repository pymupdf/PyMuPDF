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

Changes in PyMuPDF 1.9.2
------------------------
- supporting Python 3 as wxPython now supports it
- optionally show links in displayed pages
- when clicking on a link, attempt to follow it
- remove inline code for dialog icon and import from a library

Changes in PyMuPDF 1.8.0
------------------------
- display a fancy icon on the dialogs, defined as inline code in base64 format
- display pages with a zoom factor of 120%
- dynamically resize dialog to reflect each page's image size / orientation
- minor cosmetic changes
"""
import fitz
import wx
import sys
try:
    from PageFormat import FindFit
except ImportError:
    def FindFit(*args):
        return "not implemented"
try:
    from icons import ico_pdf            # PDF icon in upper left screen corner
    do_icon = True
except ImportError:
    do_icon = False

app = None
app = wx.App()
assert wx.VERSION[0:3] >= (3,0,2), "need wxPython 3.0.2 or later"
assert tuple(map(int, fitz.VersionBind.split("."))) >= (1,9,2), "need PyMuPDF 1.9.2 or later"
# make some adjustments for differences between wxPython versions 3.0.2 / 3.0.3
if wx.VERSION[0:3] >= (3,0,3):
    cursor_hand  = wx.Cursor(wx.CURSOR_HAND)
    cursor_norm  = wx.Cursor(wx.CURSOR_DEFAULT)
    bmp_buffer = wx.Bitmap.FromBuffer
else:
    cursor_hand  = wx.StockCursor(wx.CURSOR_HAND)
    cursor_norm  = wx.StockCursor(wx.CURSOR_DEFAULT)
    bmp_buffer = wx.BitmapFromBuffer

if sys.version_info[0] > 2:
    stringtypes = (str, bytes)
else:
    stringtypes = (str, unicode)

def getint(v):
    try:
        return int(v)
    except:
        pass
    if type(v) not in stringtypes:
        return 0
    a = "0"
    for d in v:
        if d in "0123456789":
            a += d
    return int(a)

# abbreviations to get rid of those long pesky names ...
#==============================================================================
# Define our dialog as a subclass of wx.Dialog.
# Only special thing is, that we are being invoked with a filename ...
#==============================================================================
class PDFdisplay(wx.Dialog):
    def __init__(self, parent, filename):
        defPos = wx.DefaultPosition
        defSiz = wx.DefaultSize
        zoom   = 1.2                        # zoom factor of display
        wx.Dialog.__init__ (self, parent, id = wx.ID_ANY,
            title = u"Display with PyMuPDF: ",
            pos = defPos, size = defSiz,
            style = wx.CAPTION|wx.CLOSE_BOX|
                    wx.DEFAULT_DIALOG_STYLE|
                    wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|
                    wx.RESIZE_BORDER)

        #======================================================================
        # display an icon top left of dialog, append filename to title
        #======================================================================
        if do_icon:
            self.SetIcon(ico_pdf.img.GetIcon())      # set a screen icon
        self.SetTitle(self.Title + filename)
        self.SetBackgroundColour(wx.Colour(240, 230, 140))

        #======================================================================
        # open the document with MuPDF when dialog gets created
        #======================================================================
        self.doc = fitz.open(filename) # create Document object
        if self.doc.needsPass:         # check password protection
            self.decrypt_doc()
        if self.doc.isEncrypted:       # quit if we cannot decrpt
            self.Destroy()
            return
        self.last_page = -1            # memorize last page displayed
        self.link_rects = []           # store link rectangles here
        self.link_texts = []           # store link texts here
        self.current_idx = -1          # store entry of found rectangle
        self.current_lnks = []         # store entry of found rectangle

        #======================================================================
        # define zooming matrix for displaying PDF page images
        # we increase images by 20%, so take 1.2 as scale factors
        #======================================================================
        self.matrix = fitz.Matrix(zoom, zoom)    # will use a constant zoom

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

        # forward button
        self.ButtonNext = wx.Button(self, wx.ID_ANY, u"forw",
                           defPos, defSiz, wx.BU_EXACTFIT)
        # backward button
        self.ButtonPrevious = wx.Button(self, wx.ID_ANY, u"back",
                           defPos, defSiz, wx.BU_EXACTFIT)
        #======================================================================
        # text field for entering a target page. wx.TE_PROCESS_ENTER is
        # required to get data entry fired as events.
        #======================================================================
        self.TextToPage = wx.TextCtrl(self, wx.ID_ANY, u"1", defPos, wx.Size(40, -1), 
                             wx.TE_RIGHT|wx.TE_PROCESS_ENTER)
        # displays total pages and page paper format
        self.statPageMax = wx.StaticText(self, wx.ID_ANY,
                              "of " + str(len(self.doc)) + " pages.",
                              defPos, defSiz, 0)
        self.links = wx.CheckBox( self, wx.ID_ANY, u"show links",
                           defPos, defSiz, wx.ALIGN_LEFT)
        self.links.Value = True
        self.paperform = wx.StaticText(self, wx.ID_ANY, "", defPos, defSiz, 0)
        # define the area for page images and load page 1 for primary display
        self.PDFimage = wx.StaticBitmap(self, wx.ID_ANY, self.pdf_show(1),
                           defPos, defSiz, style = 0)
        #======================================================================
        # the main sizer of the dialog
        #======================================================================
        self.szr10 = wx.BoxSizer(wx.VERTICAL)
        szr20 = wx.BoxSizer(wx.HORIZONTAL)
        szr20.Add(self.ButtonNext, 0, wx.ALL, 5)
        szr20.Add(self.ButtonPrevious, 0, wx.ALL, 5)
        szr20.Add(self.TextToPage, 0, wx.ALL, 5)
        szr20.Add(self.statPageMax, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Add( self.links, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
        szr20.Add(self.paperform, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        # sizer ready, represents top dialog line
        self.szr10.Add(szr20, 0, wx.EXPAND, 5)
        self.szr10.Add(self.PDFimage, 0, wx.ALL, 5)
        # main sizer now ready - request final size & layout adjustments
        self.szr10.Fit(self)
        self.SetSizer(self.szr10)
        self.Layout()
        # center dialog on screen
        self.Centre(wx.BOTH)

        # Bind buttons and fields to event handlers
        self.ButtonNext.Bind(wx.EVT_BUTTON, self.NextPage)
        self.ButtonPrevious.Bind(wx.EVT_BUTTON, self.PreviousPage)
        self.TextToPage.Bind(wx.EVT_TEXT_ENTER, self.GotoPage)
        self.PDFimage.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
        self.PDFimage.Bind(wx.EVT_MOTION, self.move_mouse)
        self.PDFimage.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)

    def __del__(self):
        pass

#==============================================================================
# Button handlers and other functions
#==============================================================================
    def OnLeftDown(self, evt):
        if self.current_idx < 0:
            evt.Skip()
            return
        lnk = self.current_lnks[self.current_idx]
        if lnk["kind"] == fitz.LINK_GOTO:
            self.TextToPage.Value = str(lnk["page"] + 1)
            self.GotoPage(evt)
        elif lnk["kind"] == fitz.LINK_URI:
            import webbrowser
            try:
                webbrowser.open_new(self.link_texts[self.current_idx])
            except:
                pass
        elif lnk["kind"] == fitz.LINK_GOTOR:
            import subprocess
            try:
                subprocess.Popen(self.link_texts[self.current_idx])
            except:
                pass
        elif lnk["kind"] == fitz.LINK_NAMED:
            if lnk["name"] == "FirstPage":
                self.TextToPage.Value = "1"
            elif lnk["name"] == "LastPage":
                self.TextToPage.Value = str(len(self.doc))
            elif lnk["name"] == "NextPage":
                self.TextToPage.Value = str(int(self.TextToPage.Value) + 1)
            elif lnk["name"] == "PrevPage":
                self.TextToPage.Value = str(int(self.TextToPage.Value) - 1)
            self.GotoPage(evt)
        evt.Skip()
        return

    def cursor_in_rect(self, pos, rect):         # is mouse in a hot area?
        # check whether cursor is in rectangle
        if (rect[0] <= pos.x <= (rect[0] + rect[2])) and \
           (rect[1] <= pos.y <= (rect[1] + rect[3])):
            return True
        return False

    def move_mouse(self, evt):                   # show hand if in a rectangle
        if not self.links.Value:                 # do not process links
            evt.Skip()
            return
        if len(self.link_rects) == 0:
            evt.Skip()
            return
        pos = evt.GetPosition()
        in_rect = False
        for i, rect in enumerate(self.link_rects):
            if self.cursor_in_rect(pos, rect):
                in_rect = True
                self.current_idx = i
                break
        if in_rect:
            self.PDFimage.SetCursor(cursor_hand)
            if wx.VERSION[0:3] >= (3,0,3):
                self.PDFimage.SetToolTip(self.link_texts[i])
            else:
                self.PDFimage.SetToolTipString(self.link_texts[i])
            self.current_idx = i
        else:
            self.PDFimage.SetCursor(cursor_norm)
            self.PDFimage.UnsetToolTip()
            self.current_idx = -1
        evt.Skip()
        return

    def OnMouseWheel(self, evt):
        # process wheel as paging operations
        d = evt.GetWheelRotation()               # int indicating direction
        if d < 0:
            self.NextPage(evt)
        elif d > 0:
            self.PreviousPage(evt)
        return

    def NextPage(self, event):                   # means: page forward
        page = getint(self.TextToPage.Value) + 1 # current page + 1
        page = min(page, self.doc.pageCount)     # cannot go beyond last page
        self.TextToPage.Value = str(page)        # put target page# in screen
        self.NeuesImage(page)                    # refresh the layout
        event.Skip()

    def PreviousPage(self, event):               # means: page back
        page = getint(self.TextToPage.Value) - 1 # current page - 1
        page = max(page, 1)                      # cannot go before page 1
        self.TextToPage.Value = str(page)        # put target page# in screen
        self.NeuesImage(page)
        event.Skip()

    def GotoPage(self, event):                   # means: go to page number
        page = getint(self.TextToPage.Value)     # get page# from screen
        page = min(page, len(self.doc))          # cannot go beyond last page
        page = max(page, 1)                      # cannot go before page 1
        self.TextToPage.Value = str(page)        # make sure it's on the screen
        self.NeuesImage(page)
        event.Skip()

#==============================================================================
# Read / render a PDF page. Parameters are: pdf = document, page = page#
#==============================================================================
    def NeuesImage(self, page):
        if page == self.last_page:
            return
        self.last_page = page
        self.link_rects = []
        self.link_texts = []
        bitmap = self.pdf_show(page)        # read page image
        self.PDFimage.SetSize(bitmap.Size)  # adjust screen to image size
        self.PDFimage.SetBitmap(bitmap)     # put it in screen
        self.szr10.Fit(self)
        self.Layout()
        if self.links.Value:                     # show links?
            bitmap = self.PDFimage.GetBitmap()
            self.draw_links(bitmap, page)
            self.PDFimage.SetBitmap(bitmap)     # put it in screen
        return

    def draw_links(self, bmp, pno):
        dc = wx.MemoryDC()
        dc.SelectObject(bmp)
        dc.SetPen(wx.Pen("BLUE", width=1))
        dc.SetBrush(wx.Brush("BLUE", style=wx.BRUSHSTYLE_TRANSPARENT))
        pg_w = self.pg_ir.x1 - self.pg_ir.x0
        pg_h = self.pg_ir.y1 - self.pg_ir.y0
        zoom_w = float(bmp.Size[0]) / float(pg_w)
        zoom_h = float(bmp.Size[1]) / float(pg_h)
        for lnk in self.current_lnks:
            r = lnk["from"].round()
            wx_r = wx.Rect(int(r.x0 * zoom_w),
                           int(r.y0 * zoom_h),
                           int(r.width * zoom_w),
                           int(r.height * zoom_h))
            dc.DrawRectangle(wx_r[0], wx_r[1], wx_r[2]+1, wx_r[3]+1)
            self.link_rects.append(wx_r)
            if lnk["kind"] == fitz.LINK_GOTO:
                txt = "page " + str(lnk["page"] + 1)
            elif lnk["kind"] == fitz.LINK_GOTOR:
                txt = lnk["file"]
            elif lnk["kind"] == fitz.LINK_URI:
                txt = lnk["uri"]
            else:
                txt = "unkown destination"
            self.link_texts.append(txt)
        dc.SelectObject(wx.NullBitmap)
        dc = None
        return

    def pdf_show(self, pg_nr):
        page = self.doc.loadPage(int(pg_nr) - 1) # load the page & get Pixmap
        pix = page.getPixmap(matrix = self.matrix)
        bmp = bmp_buffer(pix.w, pix.h, pix.samples)
        paper = FindFit(page.bound().x1, page.bound().y1)
        self.paperform.Label = "Page format: " + paper
        if self.links.Value:
            self.current_lnks = page.getLinks()
            self.pg_ir = page.bound().round()
        page = None
        pix = None
        return bmp

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
                dlg.SetTitle("Wrong password. Enter correct one or cancel.")
        return

#==============================================================================
# main program
#------------------------------------------------------------------------------
# Show a standard FileSelect dialog to choose a file for display
#==============================================================================
# Wildcard: offer all supported filetypes for display
wild = "*.pdf;*.xps;*.oxps;*.epub;*.cbz;*.fb2"

#==============================================================================
# define the file selection dialog
#==============================================================================
dlg = wx.FileDialog(None, message = "Choose a file to display",
                    wildcard = wild, style=wx.FD_OPEN|wx.FD_CHANGE_DIR)

# We got a file only when one was selected and OK pressed
if dlg.ShowModal() == wx.ID_OK:
    # This returns a Python list of selected files (we only have one though)
    filename = dlg.GetPath()
else:
    filename = None

# destroy this dialog
dlg.Destroy()

# only continue if we have a filename
if filename:
    # create the dialog
    dlg = PDFdisplay(None, filename)
    # show it - this will only return for final housekeeping
    rc = dlg.ShowModal()
app = None
