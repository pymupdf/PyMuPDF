#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@created: 2017-03-10 13:40:00

@author: Jorj X. McKie
License: GNU GPL V3

Let the user select a Python file to display and update its links.

Dependencies:
PyMuPDF v1.10.x, wxPython Phoenix version

License:
 GNU GPL 3.x

Copyright:
 (c) 2017 Jorj X. McKie

"""
import fitz
import wx
import sys, os
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
assert wx.VERSION[0:3] >= (3,0,3), "need wxPython Phoenix version"
assert tuple(map(int, fitz.VersionBind.split("."))) >= (1,10,0), "need PyMuPDF 1.10.0 or later"
cur_hand  = wx.Cursor(wx.CURSOR_HAND)
cur_cross = wx.Cursor(wx.CURSOR_CROSS)
cur_nwse  = wx.Cursor(wx.CURSOR_SIZENWSE)
cur_norm  = wx.Cursor(wx.CURSOR_DEFAULT)
bmp_buffer = wx.Bitmap.FromBuffer

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
        wx.Dialog.__init__ (self, parent, id = -1,
            title = "Link Maintenance of ",
            pos = defPos, size = defSiz,
            style = wx.CAPTION|wx.CLOSE_BOX|
                    wx.DEFAULT_DIALOG_STYLE)

        #======================================================================
        # display an icon top left of dialog, append filename to title
        #======================================================================
        if do_icon:
            self.SetIcon(ico_pdf.img.GetIcon())      # set a screen icon
        self.SetTitle(self.Title + filename)
        KHAKI = wx.Colour(240, 230, 140)
        self.SetBackgroundColour(KHAKI)

        #======================================================================
        # open the document with MuPDF when dialog gets created
        #======================================================================
        self.doc = fitz.open(filename) # create Document object
        if self.doc.needsPass:         # check password protection
            self.decrypt_doc()
        if self.doc.isEncrypted:       # quit if we cannot decrypt
            self.Destroy()
            return
        self.link_code = {"NONE":0, "GOTO":1, "URI":2, "LAUNCH":3,
                           "NAMED":0, "GOTOR":5}
        self.last_pno = -1             # memorize last page displayed
        self.link_rects = []           # store link rectangles here
        self.link_bottom_rects = []    # store bottom rectangles here
        self.link_texts = []           # store link texts here
        self.current_idx = -1          # store entry of found rectangle
        self.page_links = []           # list of links of page
        self.update_links = True       # False if unsupported links
        self.page_height = 0           # page height in pixels
        self.adding_link = False       # indicate new link in the making
        self.dragging_link = False     # indicate moving rect
        self.dragstart_x = -1          # for drags: original x
        self.dragstart_y = -1          # for drags: original y
        self.resize_rect = False       # indicate resizing rect
        self.sense = 5                 # cursor tolerance, e.g. min. rectangle
                                       # side is 2 * self.sense pixels

        # forward button
        self.btn_Next = wx.Button(self, -1, "forw",
                           defPos, defSiz, wx.BU_EXACTFIT)
        # backward button
        self.btn_Previous = wx.Button(self, -1, "back",
                               defPos, defSiz, wx.BU_EXACTFIT)
        #======================================================================
        # text field for entering a target page. wx.TE_PROCESS_ENTER is
        # required to get data entry fired as events.
        #======================================================================
        self.TextToPage = wx.TextCtrl(self, -1, "1", defPos,
                             wx.Size(40, -1), wx.TE_RIGHT|wx.TE_PROCESS_ENTER)
        # displays total pages and page paper format
        self.statPageMax = wx.StaticText(self, -1,
                              "of " + str(len(self.doc)) + " pages.",
                              defPos, defSiz, 0)
        self.paperform = wx.StaticText(self, -1, "", defPos, defSiz, 0)
        #======================================================================
        # define zooming matrix for displaying PDF page images
        # we increase images by 20%, so take 1.2 as scale factors
        #======================================================================
        self.zoom = fitz.Matrix(zoom, zoom)    # will use a constant zoom
        self.shrink = ~self.zoom               # corresp. shrink matrix
        self.bitmap = self.pdf_show(1)
        self.PDFimage = wx.StaticBitmap(self, -1, self.bitmap,
                           defPos, defSiz, style = 0)
        #======================================================================
        # Fields defining a PDF link
        #======================================================================

        self.t_Update = wx.StaticText(self, -1, "")

        self.t_Save = wx.StaticText(self, -1, "")
        self.linkTypeStrings = ["NONE", "GOTO", "URI", "LAUNCH", "GOTOR"]
        self.linkType = wx.Choice(self, -1, defPos, defSiz,
                           self.linkTypeStrings)
        self.linkType.SetBackgroundColour(wx.Colour(240, 230, 140))
        self.fromLeft = wx.SpinCtrl(self, -1, wx.EmptyString,
                           defPos, wx.Size(60, -1), 
                           wx.TE_RIGHT|wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER,
                           0, 9999)
        self.fromTop = wx.SpinCtrl(self, -1, wx.EmptyString,
                          defPos, wx.Size(60, -1), 
                          wx.TE_RIGHT|wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER,
                          0, 9999)
        self.fromWidth = wx.SpinCtrl(self, -1, wx.EmptyString,
                            defPos, wx.Size(60, -1), 
                            wx.TE_RIGHT|wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER,
                            0, 9999)
        self.fromHeight = wx.SpinCtrl(self, -1, wx.EmptyString,
                             defPos, wx.Size(60, -1), 
                             wx.TE_RIGHT|wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER,
                             0, 9999)
        self.toFile = wx.TextCtrl(self, -1, wx.EmptyString, defPos,
                         wx.Size(350,-1), wx.TE_PROCESS_ENTER)
        self.toURI = wx.TextCtrl(self, -1, wx.EmptyString, defPos,
                        wx.Size(350,-1), wx.TE_PROCESS_ENTER)
        self.toPage = wx.TextCtrl(self, -1, wx.EmptyString, defPos,
                         wx.Size(50, -1), wx.TE_RIGHT|wx.TE_PROCESS_ENTER)
        self.toNameStrings = ["FirstPage", "LastPage",
                              "NextPage", "PrevPage"]
        self.toName = wx.Choice(self, -1, defPos, defSiz,
                         self.toNameStrings)
        self.toLeft = wx.TextCtrl(self, -1, wx.EmptyString, defPos,
                         wx.Size(50, -1), wx.TE_RIGHT|wx.TE_PROCESS_ENTER)
        self.toHeight = wx.TextCtrl(self, -1, wx.EmptyString, defPos,
                           wx.Size(50, -1), wx.TE_RIGHT|wx.TE_PROCESS_ENTER)
        self.btn_Update = wx.Button(self, -1, "UPDATE PAGE",
                             defPos, defSiz, wx.BU_EXACTFIT)
        self.btn_NewLink = wx.Button(self, -1, "NEW LINK",
                              defPos, self.btn_Update.Size, 0)
        self.btn_Save = wx.Button(self, -1, "SAVE FILE",
                           defPos, self.btn_Update.Size, 0)
        linie1 = wx.StaticLine(self, -1,
                    defPos, defSiz, wx.LI_VERTICAL)
        #======================================================================
        # sizers of the dialog
        #======================================================================
        szr00 = wx.BoxSizer(wx.HORIZONTAL)        
        szr10 = wx.BoxSizer(wx.VERTICAL)
        szr20 = wx.BoxSizer(wx.HORIZONTAL)
        szr30 = wx.GridBagSizer(5, 5)
        
        szr20.Add(self.btn_Next, 0, wx.ALL, 5)
        szr20.Add(self.btn_Previous, 0, wx.ALL, 5)
        szr20.Add(self.TextToPage, 0, wx.ALL, 5)
        szr20.Add(self.statPageMax, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Add(self.paperform, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
#==============================================================================
#       use GridBagSizer for link details  
#==============================================================================
        line_span = wx.GBSpan(1, 5)
        t = wx.StaticText(self, -1, "Link Details", defPos, defSiz,
                          wx.ALIGN_CENTER)
        t.SetBackgroundColour("STEEL BLUE")
        t.SetForegroundColour("WHITE")
        szr30.Add(t,
                  (0,0), line_span, wx.EXPAND) # overall header
        szr30.Add(wx.StaticLine(self, -1, defPos, defSiz, wx.LI_HORIZONTAL),
                  (1,0), line_span, wx.EXPAND)

        t = wx.StaticText(self, -1, "Hot Spot", defPos, defSiz,
                          wx.ALIGN_CENTER)
        t.SetBackgroundColour("GOLD")
        szr30.Add(t,
                  (2,0), line_span, wx.EXPAND) # hot area header
        szr30.Add(wx.StaticText(self, -1, "Left:"),
                  (3,0), (1,1), wx.ALIGN_RIGHT)
        szr30.Add(self.fromLeft,
                  (3,1), (1,1), wx.ALIGN_LEFT)
        szr30.Add(wx.StaticText(self, -1, "Top:"),
                  (3,2), (1,1), wx.ALIGN_RIGHT)
        szr30.Add(self.fromTop, (3,3), (1,1), wx.ALIGN_LEFT)
        szr30.Add(wx.StaticText(self, -1, "Width:"),
                  (4,0), (1,1), wx.ALIGN_RIGHT)
        szr30.Add(self.fromWidth,
                  (4,1), (1,1), wx.ALIGN_LEFT)
        szr30.Add(wx.StaticText(self, -1, "Height:"),
                  (4,2), (1,1), wx.ALIGN_RIGHT)
        szr30.Add(self.fromHeight,
                  (4,3), (1,1), wx.ALIGN_LEFT)

        szr30.Add(wx.StaticLine(self, -1, defPos, defSiz, wx.LI_HORIZONTAL),
                  (5,0), line_span, wx.EXPAND)
        t = wx.StaticText(self, -1, "Link Destination", defPos, defSiz,
                          wx.ALIGN_CENTER)
        t.SetBackgroundColour("YELLOW GREEN")
        szr30.Add(t,
                  (6,0), line_span, wx.EXPAND) # destination header
        szr30.Add(wx.StaticText(self, -1, "Link Type:"),
                  (7,0), (1,1), wx.ALIGN_RIGHT)
        szr30.Add(self.linkType,
                  (7,1))
        szr30.Add(wx.StaticText(self, -1, " to Page:"),
                  (8,0), (1,1), wx.ALIGN_RIGHT)
        szr30.Add(self.toPage,
                  (8,1))
        szr30.Add(wx.StaticText(self, -1, "at left/top:"),
                  (8,2), (1,1), wx.ALIGN_RIGHT)
        szr30.Add(self.toLeft,
                  (8,3))
        szr30.Add(self.toHeight,
                  (8,4), (1,1), wx.ALIGN_LEFT)
        szr30.Add(wx.StaticText(self, -1, " to File:"),
                  (9,0), line_span)
        szr30.Add(self.toFile,
                  (10,0), line_span)
        szr30.Add(wx.StaticText(self, -1, " to URL:"),
                  (11,0), line_span)
        szr30.Add(self.toURI,
                  (12,0), line_span)
        self.toName.Hide()
        szr30.Add(wx.StaticText(self, -1, ""),
                  (13,0), (1,1), wx.ALIGN_RIGHT)
        szr30.Add(self.toName, (13,1))
        # buttons
        szr30.Add(wx.StaticLine(self, -1, defPos, defSiz, wx.LI_HORIZONTAL),
                  (14,0), line_span, wx.EXPAND)
        szr30.Add(self.btn_Update, (15,0))
        szr30.Add(self.t_Update, (15,1))
        szr30.Add(self.btn_NewLink, (16,0))
        szr30.Add(wx.StaticText(self, -1, "Create a new link"),
                  (16,1), (1,1), wx.ALIGN_RIGHT)
        szr30.Add(self.btn_Save, (17,0))
        szr30.Add(self.t_Save, (17,1))
        szr30.Add(wx.StaticLine(self, -1, defPos, defSiz, wx.LI_HORIZONTAL),
                  (18,0), line_span, wx.EXPAND)
        
        szr10.Add(szr20, 0, wx.EXPAND, 5)
        szr10.Add(self.PDFimage, 0, wx.ALL, 5)
        
        szr00.Add(szr30, 0, wx.EXPAND, 5)
        szr00.Add(linie1, 0, wx.EXPAND, 5)
        szr00.Add(szr10, 0, wx.EXPAND, 5)
        
        szr00.Fit(self)
        self.SetSizer(szr00)
        self.Layout()
        
        self.Centre(wx.BOTH)

        # Bind dialog elements to event handlers
        self.btn_Save.Bind(wx.EVT_BUTTON, self.on_save_file)
        self.btn_Update.Bind(wx.EVT_BUTTON, self.on_update_page_links)
        self.btn_Next.Bind(wx.EVT_BUTTON, self.on_next_page)
        self.btn_Previous.Bind(wx.EVT_BUTTON, self.on_previous_page)
        self.btn_NewLink.Bind(wx.EVT_BUTTON, self.on_new_link)
        self.TextToPage.Bind(wx.EVT_TEXT_ENTER, self.on_goto_page)
        self.PDFimage.Bind(wx.EVT_ENTER_WINDOW, self.on_enter_window)
        self.PDFimage.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        self.PDFimage.Bind(wx.EVT_MOTION, self.on_move_mouse)
        self.PDFimage.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.PDFimage.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.linkType.Bind(wx.EVT_CHOICE, self.on_linkType_changed)
        self.fromHeight.Bind(wx.EVT_SPINCTRL, self.on_link_changed)
        self.fromLeft.Bind(wx.EVT_SPINCTRL, self.on_link_changed)
        self.fromTop.Bind(wx.EVT_SPINCTRL, self.on_link_changed)
        self.fromWidth.Bind(wx.EVT_SPINCTRL, self.on_link_changed)
        self.toLeft.Bind(wx.EVT_TEXT_ENTER, self.on_link_changed)
        self.toHeight.Bind(wx.EVT_TEXT_ENTER, self.on_link_changed)
        self.toURI.Bind(wx.EVT_TEXT_ENTER, self.on_link_changed)
        self.toFile.Bind(wx.EVT_TEXT_ENTER, self.on_link_changed)
        self.toPage.Bind(wx.EVT_TEXT_ENTER, self.on_link_changed)
        self.toLeft.Bind(wx.EVT_TEXT, self.on_link_changed)
        self.toHeight.Bind(wx.EVT_TEXT, self.on_link_changed)
        self.toURI.Bind(wx.EVT_TEXT, self.on_link_changed)
        self.toFile.Bind(wx.EVT_TEXT, self.on_link_changed)
        self.toPage.Bind(wx.EVT_TEXT, self.on_link_changed)
        self.toName.Bind(wx.EVT_CHOICE, self.on_link_changed)
        self.btn_Update.Disable()
        self.btn_Save.Disable()
        self.clear_link_details()

    def __del__(self):
        pass

#==============================================================================
# Button handlers and other functions
#==============================================================================

    def on_enter_window(self, evt):
        self.draw_links()
        evt.Skip()
        return
    
    def on_move_mouse(self, evt):
        pos = evt.GetPosition()
        in_rect = self.get_linkrect_idx(pos)     # rect number we are in
        in_brect = self.get_bottomrect_idx(pos)  # bottom-right corner we are in
        self.PDFimage.SetCursor(cur_norm)        # standard cursor
            
        if in_brect >= 0:                        # cursor if in br corner
            self.PDFimage.SetCursor(cur_nwse)
        elif in_rect >= 0:                       # cursor if in a rect
            self.PDFimage.SetCursor(cur_hand)
        
        if self.adding_link:                     # painting new hot spot?
            if in_rect >= 0 or in_brect >= 0:    # must be outside others
                evt.Skip()
                return
            self.PDFimage.SetCursor(cur_cross)   # cursor if painting
            if evt.LeftIsDown():                 # mouse pressed? go!
                w = abs(pos.x - self.addrect.x)  # new rect values
                h = abs(pos.y - self.addrect.y)
                x = min(self.addrect.x, pos.x)
                y = min(self.addrect.y, pos.y)
                if not self.is_in_free_area(wx.Rect(x, y, w, h)):
                    evt.Skip()                   # do not allow overlaps
                    return
                if h <= self.sense or w <= self.sense: # too small!
                    evt.Skip()
                    return
                self.fromHeight.SetValue(h)      # update ...
                self.fromWidth.SetValue(w)       # ... spin ...
                self.fromLeft.SetValue(x)        # ... controls
                self.fromTop.SetValue(y)
                self.redraw_bitmap()
                self.draw_links()
                self.draw_rect(x, y, w, h, "BLUE")  # draw rectangle
                self.current_idx = -1            # means: not in an old rect
            evt.Skip()
            return

        if len(self.page_links) == 0:            # there are no links yet
            evt.Skip()
            return
        
        if self.resize_rect:                     # resizing hot spot?
            self.PDFimage.SetCursor(cur_nwse)    # adjust cursor
            if evt.LeftIsDown():                 # mouse pressed? go!
                r = self.link_rects[in_brect]    # resizing this rectangle
                w = pos.x - r.x                  # new width
                h = pos.y - r.y                  # new height
                nr = wx.Rect(r.x, r.y, w, h)     # new retangle
                # if large anough and no overlaps:
                if w >= 2 * self.sense and h >= 2 * self.sense and \
                    self.is_in_free_area(nr, ok = in_brect):
                    l = self.page_links[in_brect]     # page link entry 
                    l["from"] = self.wxRect_to_Rect(nr)    # get fitz format
                    l["update"] = True
                    self.page_links[in_brect] = l     # store change link
                    self.fromHeight.SetValue(h)
                    self.fromWidth.SetValue(w)
                    self.redraw_bitmap()
                    self.draw_links()
            evt.Skip()
            return
            
        if in_rect >= 0:                         # still here and inside a rect?
            self.PDFimage.SetCursor(cur_hand)    # adjust cursor
            self.PDFimage.SetToolTip(self.link_texts[in_rect])
            if self.dragging_link:               # are we moving the hot spot?
                if evt.LeftIsDown():
                    r = self.link_rects[in_rect] # this is the rectangle
                    x = pos.x - self.dragstart_x # new left ...
                    y = pos.y - self.dragstart_y # ... and top values
                    w = r.width                  # shape does ...
                    h = r.height                 # ... not change
                    nr = wx.Rect(x, y, w, h)     # new rectangle
                    if self.is_in_free_area(nr, ok = in_rect):  # no overlaps?
                        self.fromLeft.SetValue(x)     # new screen value
                        self.fromTop.SetValue(y)      # new screen value
                        fr = self.wxRect_to_Rect(nr)  # fitz format of new rect
                        l = self.page_links[in_rect]  # this is the link
                        l["from"] = fr                # update its hot spot
                        l["update"] = True       # we need to update
                        self.page_links[in_rect] = l
                        self.redraw_bitmap()
                        self.draw_links()
            evt.Skip()
            return
        
        self.PDFimage.UnsetToolTip()

        evt.Skip()
        return

    def on_mouse_wheel(self, evt):
        # process wheel as paging operations
        d = evt.GetWheelRotation()               # int indicating direction
        if d < 0:
            self.on_next_page(evt)
        elif d > 0:
            self.on_previous_page(evt)
        return

    def on_next_page(self, event):                # means: page forward
        page = getint(self.TextToPage.Value) + 1  # current page + 1
        page = min(page, self.doc.pageCount)      # cannot go beyond last page
        self.TextToPage.ChangeValue(str(page))    # put target page# in screen
        self.new_image(page)                      # refresh the layout
        event.Skip()

    def on_previous_page(self, event):            # means: page back
        page = getint(self.TextToPage.Value) - 1  # current page - 1
        page = max(page, 1)                       # cannot go before page 1
        self.TextToPage.ChangeValue(str(page))    # put target page# in screen
        self.new_image(page)
        event.Skip()

    def on_goto_page(self, event):                # means: go to page number
        page = getint(self.TextToPage.Value)      # get page# from screen
        page = min(page, len(self.doc))           # cannot go beyond last page
        page = max(page, 1)                       # cannot go before page 1
        self.TextToPage.ChangeValue(str(page))    # make sure it's on the screen
        self.new_image(page)
        event.Skip()

    def on_update_page_links(self, evt):
        """ Perform PDF update of changed links."""
        if not self.update_links:                 # skip if unsupported links
            evt.Skip()
            return
        pg = self.doc[getint(self.TextToPage.Value) -1]
        for i in range(len(self.page_links)):
            l = self.page_links[i]
            if l.get("update", False):            # "update" must be True
                if l["xref"] == 0:                # no xref => new link
                    pg.insertLink(l)
                elif l["kind"] < 1 or l["kind"] > len(self.linkTypeStrings):
                    pg.deleteLink(l)              # delete invalid link
                else:
                    pg.updateLink(l)              # else link update
            l["update"] = False                   # reset update indicator
            self.page_links[i] = l                # update list of page links
        self.btn_Update.Disable()                 # disable update button
        self.t_Update.Label = ""                  # and its message
        self.btn_Save.Enable()
        self.t_Save.Label = "There are changes. Press to save them to file."
        evt.Skip()
        return
    
    def on_link_changed(self, evt):
        if  self.current_idx < 0:                 # invalid index should not occur
            evt.Skip()
            return
        repaint = False                           # reset when we must repaint
        lnk = self.page_links[self.current_idx]   # we deal with this link
        n = self.linkType.GetSelection()
        lstr = self.linkType.GetString(n)
        lnk["kind"] = self.link_code[lstr]
        # rectangle in link details on screen:
        r = wx.Rect(self.fromLeft.Value, self.fromTop.Value,
                    self.fromWidth.Value, self.fromHeight.Value)
        lr = self.link_rects[self.current_idx]    # stored rectangle

        if tuple(r) != tuple(lr):                 # something changed
            if self.is_in_free_area(r, ok = self.current_idx):
                lnk["from"] = self.wxRect_to_Rect(r)
                lnk["update"] = True              # update rectangle in list
                repaint = True
            else:                                 # reset values: invalid change
                self.fromHeight.SetValue(lr.Height)
                self.fromWidth.SetValue(lr.Width)
                self.fromTop.SetValue(lr.y)
                self.fromLeft.SetValue(lr.x)

        new_to = lnk.get("to", fitz.Point(0,0))
        try:
            new_to.x = float(self.toLeft.Value)
        except:
            pass

        try:
            new_to.y = float(self.toHeight.Value)
        except:
            pass

        lnk["to"] = new_to                        # destination point
        
        if self.toPage.IsModified:                # dest page modified
            if self.toPage.Value.isdecimal():
                lnk["page"] = int(self.toPage.Value) - 1
            else:
                lnk["page"] = 0
            repaint = True
            lnk["update"] = True

        if self.toURI.IsModified:                 # dest URI modified
            lnk["uri"] = self.toURI.Value
            repaint = True
            lnk["update"] = True

        if self.toFile.IsModified:                # dest file modified
            lnk["file"] = self.toFile.Value
            repaint = True
            lnk["update"] = True

        n = self.toName.GetSelection()            # named dest modified
        scr_name = self.toName.GetString(n)
        if scr_name != lnk.get("name", ""):
            lnk["name"] = scr_name 
            repaint = True
            lnk["update"] = True
                
        self.page_links[self.current_idx] = lnk   # update page link list
        if repaint:
            self.redraw_bitmap()
            self.draw_links()
            r = self.link_rects[self.current_idx]
            self.draw_rect(r.x, r.y, r.width, r.height, "RED")
        evt.Skip()
        return
    
    def on_linkType_changed(self, evt):
        """User changed link kind, so prepare available fields."""
        if self.current_idx < 0:
            evt.Skip()
            return
        n = self.linkType.GetSelection()
        lt_str = self.linkType.GetString(n)
        lt = self.link_code[lt_str]
        self.prep_link_details(lt)
            
        lnk = self.page_links[self.current_idx]
        lnk["update"] = True
        lnk["kind"] = lt
        self.enable_update()

        if lt == fitz.LINK_GOTO:
            if not self.toPage.Value.isdecimal():
                self.toPage.ChangeValue("1")
            self.toPage.Enable()
            if not self.toLeft.Value.isdecimal():
                self.toLeft.ChangeValue("0")
            self.toLeft.Enable()
            if not self.toHeight.Value.isdecimal():
                self.toHeight.ChangeValue("0")
            self.toHeight.Enable()
            lnk["page"] = int(self.toPage.Value) - 1
            lnk["to"] = fitz.Point(int(self.toLeft.Value),
                                   int(self.toHeight.Value))

        elif lt == fitz.LINK_GOTOR:
            if not self.toFile.Value:
                self.toFile.SetValue(self.text_in_rect())
                self.toFile.MarkDirty()
            if not self.toPage.Value.isdecimal():
                self.toPage.ChangeValue("1")
            if not self.toLeft.Value.isdecimal():
                self.toLeft.ChangeValue("0")
            if not self.toHeight.Value.isdecimal():
                self.toHeight.ChangeValue("0")
            self.toLeft.Enable()
            self.toPage.Enable()
            self.toFile.Enable()
            self.toHeight.Enable()
            lnk["file"] = self.toFile.Value
            lnk["page"] = int(self.toPage.Value) - 1
            lnk["to"] = fitz.Point(int(self.toLeft.Value),
                                   int(self.toHeight.Value))
            
        elif lt == fitz.LINK_URI:
            if not self.toURI.Value:
                self.toURI.SetValue(self.text_in_rect())
                self.toURI.MarkDirty()
            lnk["uri"] = self.toURI.Value
            self.toURI.Enable()
            
        elif lt == fitz.LINK_LAUNCH:
            if not self.toFile.Value:
                self.toFile.SetValue(self.text_in_rect())
                self.toFile.MarkDirty()
            lnk["file"] = self.toFile.Value
            self.toFile.Enable()
            
        elif lt == fitz.LINK_NAMED:
            self.toName.SetSelection(0)
            self.toName.Enable()
            
        self.page_links[self.current_idx] = lnk
            
        evt.Skip()
        return
    
    def on_save_file(self, evt):
        indir, infile = os.path.split(self.doc.name)
        odir = indir
        ofile = infile
        if self.doc.openErrCode or self.doc.needsPass:
            ofile = ""
        sdlg = wx.FileDialog(self, "Specify Output", odir, ofile,
                                   "PDF files (*.pdf)|*.pdf", wx.FD_SAVE)
        if sdlg.ShowModal() == wx.ID_CANCEL:
            evt.Skip()
            return
        outfile = sdlg.GetPath()
        if self.doc.needsPass or self.doc.openErrCode:
            title =  "Repaired / decrypted PDF requires new output file"
            while outfile == self.doc.name:
                sdlg = wx.FileDialog(self, title, odir, "",
                                     "PDF files (*.pdf)|*.pdf", wx.FD_SAVE)
                if sdlg.ShowModal() == wx.ID_CANCEL:
                    evt.Skip()
                    return
                outfile = sdlg.GetPath()
        self.doc._delXmlMetadata()
        if outfile == self.doc.name:
            self.doc.saveIncr()                       # equal: update input file
        else:
            self.doc.save(outfile, garbage=4)
        
        sdlg.Destroy()
        self.btn_Save.Disable()
        evt.Skip()
        return

    def on_new_link(self, evt):
        self.adding_link = True
        self.linkType.SetSelection(1)
        self.prep_link_details(1)
        self.current_idx = -1
        self.fromHeight.SetValue(0)
        self.fromLeft.SetValue(0)
        self.fromTop.SetValue(0)
        self.fromWidth.SetValue(0)
        self.toPage.ChangeValue("1")
        self.toLeft.ChangeValue("0")
        self.toHeight.ChangeValue("0")
        evt.Skip()
        return
    
    def on_left_up(self, evt):
        if self.adding_link:
            n = self.linkType.GetSelection()
            wxr = wx.Rect(self.fromLeft.Value, self.fromTop.Value,
                           self.fromWidth.Value, self.fromHeight.Value)
            l_from = self.wxRect_to_Rect(wxr)
            l_to = fitz.Point(float(self.toLeft.Value),
                              float(self.toHeight.Value))
            lnk = {"kind": n, "xref": 0, "from": l_from, "to": l_to,
                   "page": int(self.toPage.Value) - 1, "update": True}
            
            self.link_rects.append(wxr)
            self.page_links.append(lnk)
            p = wxr.BottomRight
            br = wx.Rect(p.x - self.sense, p.y - self.sense,
                         2*self.sense, 2*self.sense)
            self.link_bottom_rects.append(br)
            self.link_texts.append("page " + self.toPage.Value)
            self.adding_link = False
            del self.addrect
            self.current_idx = -1
            self.PDFimage.SetCursor(cur_norm)
            self.clear_link_details()
            self.toPage.Enable()
            self.toLeft.Enable()
            self.toHeight.Enable()
            self.linkType.Enable()
            evt.Skip()
            return
        self.adding_link = False
        self.dragging_link = False
        self.dragstart_x = -1
        self.dragstart_y = -1
        self.resize_rect = False
        self.PDFimage.SetCursor(cur_norm)
        evt.Skip()
        return
    
    def on_left_down(self, evt):
        pos = evt.GetPosition()
        in_rect = self.get_linkrect_idx(pos)
        in_brect = self.get_bottomrect_idx(pos)

        if self.adding_link:
            # pos is top-left of new rectangle
            if in_rect >= 0 or in_brect >= 0:
                self.adding_link = False
            else:
                self.addrect = wx.Rect(pos.x, pos.y, 0, 0)
                self.fromTop.SetValue(pos.y)
                self.fromLeft.SetValue(pos.x)
            evt.Skip()
            return
        
        if in_brect >= 0:
            self.resize_rect = True
            self.current_idx = in_brect
            evt.Skip()
            return
        
        if in_rect >= 0:
            self.dragging_link = True       # we are about to drag
            r = self.link_rects[in_rect]    # wx.Rect we will be dragging
            self.dragstart_x = pos.x - r.x  # delta to left
            self.dragstart_y = pos.y - r.y  # delta to top 
        
        if in_rect < 0:
            self.current_idx = -1
            evt.Skip()
            return
        self.current_idx = in_rect
        lnk = self.page_links[in_rect]
        r = self.link_rects[in_rect]
        self.fromLeft.SetValue(r.x)
        self.fromTop.SetValue(r.y)
        self.fromHeight.SetValue(r.Height)
        self.fromWidth.SetValue(r.Width)
        self.draw_links()
        self.draw_rect(r.x, r.y, r.width, r.height, "RED")

        self.linkType.SetSelection(lnk["kind"])
         
        self.prep_link_details(lnk["kind"])
        if lnk["kind"] in (fitz.LINK_GOTO, fitz.LINK_GOTOR):
            self.toPage.ChangeValue(str(lnk["page"] + 1))
            self.toLeft.ChangeValue(str(lnk["to"][0]))
            self.toHeight.ChangeValue(str(lnk["to"][1]))
            self.toPage.Enable()
            self.toLeft.Enable()
            self.toHeight.Enable()
        
        elif lnk["kind"] == fitz.LINK_URI:
            self.toURI.ChangeValue(lnk["uri"])
            self.toURI.Enable()
        
        elif lnk["kind"] in (fitz.LINK_GOTOR, fitz.LINK_LAUNCH):
            self.toFile.ChangeValue(lnk["file"])
            self.toFile.Enable()

        elif lnk["kind"] == fitz.LINK_NAMED:
            try:
                self.toName.SetSelection(self.toNameStrings.index(lnk["name"]))
            except:
                self.toName.SetSelection(self.toNameStrings[0])
            self.toName.Enable()

        evt.Skip()
        return

    def enable_update(self):
        if self.update_links:
            self.btn_Update.Enable()
            self.t_Update.Label = "Contains changed links. Press to update."
        else:
            self.btn_Update.Disable()
            self.t_Update.Label = "Contains unsupported links. Cannot update!"
        return
        
    def draw_links(self):
        dc = wx.ClientDC(self.PDFimage)
        dc.SetPen(wx.Pen("BLUE", width=1))
        dc.SetBrush(wx.Brush("BLUE", style=wx.BRUSHSTYLE_TRANSPARENT))
        self.link_rects = []
        self.link_bottom_rects = []
        self.link_texts = []
        for lnk in self.page_links:
            if lnk.get("update", False):
                self.enable_update()
            wxr = self.Rect_to_wxRect(lnk["from"])
            dc.DrawRectangle(wxr[0], wxr[1], wxr[2], wxr[3])
            self.link_rects.append(wxr)
            p = wxr.BottomRight
            br = wx.Rect(p.x - self.sense, p.y - self.sense,
                         2*self.sense, 2*self.sense)
            self.link_bottom_rects.append(br)
            if lnk["kind"] == fitz.LINK_GOTO:
                txt = "page " + str(lnk["page"] + 1)
            elif lnk["kind"] == fitz.LINK_GOTOR:
                txt = lnk["file"] + " p. " + str(lnk["page"] + 1)
            elif lnk["kind"] == fitz.LINK_URI:
                txt = lnk["uri"]
            elif lnk["kind"] == fitz.LINK_LAUNCH:
                txt = "open " + lnk["file"]
            elif lnk["kind"] == fitz.LINK_NAMED:
                txt = lnk["name"]
            elif lnk["kind"] == fitz.LINK_NONE:
                txt = "none"
            else:
                txt = "unkown destination"
            self.link_texts.append(txt)
        return

    def redraw_bitmap(self):
        """Refresh bitmap image."""
        w = self.bitmap.Size[0]
        h = self.bitmap.Size[1]
        x = y = 0
        rect = wx.Rect(x, y, w, h)
        bm = self.bitmap.GetSubBitmap(rect)
        dc = wx.ClientDC(self.PDFimage)     # make a device control out of img
        dc.DrawBitmap(bm, x, y)             # refresh bitmap before draw
        return

    def draw_rect(self, x, y, w, h, c):
        dc = wx.ClientDC(self.PDFimage)
        dc.SetPen(wx.Pen(c, width=1))
        dc.SetBrush(wx.Brush(c, style=wx.BRUSHSTYLE_TRANSPARENT))
        dc.DrawRectangle(x, y, w, h)
        return

    def clear_link_details(self):
        self.linkType.SetSelection(wx.NOT_FOUND)
        self.fromLeft.SetValue("")
        self.fromTop.SetValue("")
        self.fromHeight.SetValue("")
        self.fromWidth.SetValue("")
        self.toFile.ChangeValue("")
        self.toPage.ChangeValue("")
        self.toHeight.ChangeValue("")
        self.toLeft.ChangeValue("")
        self.toURI.ChangeValue("")
        self.toName.SetSelection(wx.NOT_FOUND)
        self.toName.Disable()
        self.btn_Update.Disable()
        self.t_Update.Label = ""
        self.toFile.Disable()
        self.toLeft.Disable()
        self.toHeight.Disable()
        self.toURI.Disable()
        self.toPage.Disable()
        self.adding_link = False
        self.resize_rect = False
        
        return

    def prep_link_details(self, lt):
        if lt not in (fitz.LINK_GOTOR, fitz.LINK_LAUNCH):
            self.toFile.ChangeValue("")
            self.toFile.Disable()
        
        if lt not in (fitz.LINK_GOTO, fitz.LINK_GOTOR):
            self.toPage.ChangeValue("")
            self.toHeight.ChangeValue("")
            self.toLeft.ChangeValue("")
            self.toLeft.Disable()
            self.toHeight.Disable()
            self.toPage.Disable()
        
        if lt != fitz.LINK_URI:
            self.toURI.ChangeValue("")
            self.toURI.Disable()
        
        if lt != fitz.LINK_NAMED:
            self.toName.SetSelection(wx.NOT_FOUND)
            self.toName.Disable()
        return

    def text_in_rect(self):
        wxr = wx.Rect(self.fromLeft.Value, self.fromTop.Value,
                      self.fromWidth.Value, self.fromHeight.Value)
        r = self.wxRect_to_Rect(wxr)
        pno = getint(self.TextToPage.Value) - 1
        return self.doc[pno].extractTextRect(r)
        
        
    def Rect_to_wxRect(self, fr):
        """ Return a zoomed wx.Rect for given fitz.Rect."""
        r = (fr * self.zoom).irect   # zoomed IRect
        return wx.Rect(r.x0, r.y0, r.width, r.height)   # wx.Rect version
    
    def wxRect_to_Rect(self, wr):
        """ Return a shrunk fitz.Rect for given wx.Rect."""
        r = fitz.Rect(wr.x, wr.y, wr.x + wr.width, wr.y + wr.height)
        return r * self.shrink        # shrunk fitz.Rect version
    
    def is_in_free_area(self, nr, ok = -1):
        """ Determine if rect covers a free area inside the bitmap."""
        for i, r in enumerate(self.link_rects):
            if r.Intersects(nr) and i != ok:
                return False
        bmrect = wx.Rect(0,0,dlg.bitmap.Size[0],dlg.bitmap.Size[1])
        return bmrect.Contains(nr)
        
    def get_linkrect_idx(self, pos):
        """ Determine if cursor is inside one of the link hot spots."""
        for i, r in enumerate(self.link_rects):
            if r.Contains(pos):
                return i
        return -1
        
    def get_bottomrect_idx(self, pos):
        """ Determine if cursor is on bottom right corner of a hot spot."""
        for i, r in enumerate(self.link_bottom_rects):
            if r.Contains(pos):
                return i
        return -1

#==============================================================================
# Read / render a PDF page. Parameters are: pdf = document, page = page number
#==============================================================================
    def new_image(self, pno):
        if pno == self.last_pno:
            return
        self.last_pno = pno
        self.clear_link_details()
        self.link_rects = []
        self.link_bottom_rects = []
        self.link_texts = []
        self.bitmap = self.pdf_show(pno)         # read page image
        self.PDFimage.SetSize(self.bitmap.Size)  # adjust screen to image size
        self.PDFimage.SetBitmap(self.bitmap)     # put it in screen
        #self.szr00.Fit(self)
        #self.Layout()
        #self.bitmap = self.PDFimage.GetBitmap()
        #self.redraw_bitmap()
        self.draw_links()

        return

    def pdf_show(self, pno):
        page = self.doc.loadPage(getint(pno) - 1) # load page & get Pixmap
        pix = page.getPixmap(matrix = self.zoom)
        bmp = bmp_buffer(pix.w, pix.h, pix.samples)
        paper = FindFit(page.bound().x1, page.bound().y1)
        self.paperform.Label = "Page format: " + paper
        self.page_links = page.getLinks()
        if len(self.page_links) > 0:
            l = self.page_links[0]
            if l["xref"] > 0:
                self.update_links = True
            else:
                self.update_links = False
        else:
            self.update_links = True
        self.page_height = page.rect.height
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
# Show a standard FileSelect dialog to choose a file
#==============================================================================
# Wildcard: only offer PDF files
wild = "*.pdf"

#==============================================================================
# define the file selection dialog
#==============================================================================
dlg = wx.FileDialog(None, message = "Choose a file to display",
                    wildcard = wild, style=wx.FD_OPEN|wx.FD_CHANGE_DIR)

# We got a file only when one was selected and OK pressed
if dlg.ShowModal() == wx.ID_OK:
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
