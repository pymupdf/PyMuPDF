#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@created: 2017-03-10 13:40:00

@author: Jorj X. McKie

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
        wx.Dialog.__init__ (self, parent, id = wx.ID_ANY,
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
        self.SetBackgroundColour(wx.Colour(240, 230, 140))

        #======================================================================
        # open the document with MuPDF when dialog gets created
        #======================================================================
        self.doc = fitz.open(filename) # create Document object
        if self.doc.needsPass:         # check password protection
            self.decrypt_doc()
        if self.doc.isEncrypted:       # quit if we cannot decrypt
            self.Destroy()
            return
        self.last_pno = -1             # memorize last page displayed
        self.link_rects = []           # store link rectangles here
        self.link_bottom_rects = []    # store bottom rectangles here
        self.link_texts = []           # store link texts here
        self.current_idx = -1          # store entry of found rectangle
        self.page_links = []           # list of links of page
        self.page_height = 0           # page height in pixels
        self.adding_link = False       # indicate new link in the making
        self.dragging_link = False     # indicate moving rect
        self.dragstart_x = -1          # for drags: original x
        self.dragstart_y = -1          # for drags: original y
        self.resize_rect = False       # indicate resizing rect
        self.sense = 5                 # cursor tolerance, e.g. min. rectangle
                                       # side is 2 * self.sense pixels

        # forward button
        self.btn_Next = wx.Button(self, wx.ID_ANY, "forw",
                           defPos, defSiz, wx.BU_EXACTFIT)
        # backward button
        self.btn_Previous = wx.Button(self, wx.ID_ANY, "back",
                           defPos, defSiz, wx.BU_EXACTFIT)
        #======================================================================
        # text field for entering a target page. wx.TE_PROCESS_ENTER is
        # required to get data entry fired as events.
        #======================================================================
        self.TextToPage = wx.TextCtrl(self, wx.ID_ANY, "1", defPos,
                            wx.Size(40, -1), wx.TE_RIGHT|wx.TE_PROCESS_ENTER)
        # displays total pages and page paper format
        self.statPageMax = wx.StaticText(self, wx.ID_ANY,
                              "of " + str(len(self.doc)) + " pages.",
                              defPos, defSiz, 0)
        self.paperform = wx.StaticText(self, wx.ID_ANY, wx.EmptyString,
                            defPos, defSiz, 0)
        #======================================================================
        # define zooming matrix for displaying PDF page images
        # we increase images by 20%, so take 1.2 as scale factors
        #======================================================================
        self.matrix = fitz.Matrix(zoom, zoom)    # will use a constant zoom
        self.imatrix = ~self.matrix              # corresp. shrink matrix
        self.bitmap = self.pdf_show(1)
        self.PDFimage = wx.StaticBitmap(self, wx.ID_ANY, self.bitmap,
                           defPos, defSiz, style = 0)
        #======================================================================
        # Fields defining a PDF link
        #======================================================================
        t_size = wx.Size(60, -1)

        t_blank1 = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, defPos,
                        defSiz, 0)
        t_head1 = wx.StaticText(self, wx.ID_ANY, "=== Link Details ===",
                     defPos, wx.Size(300, -1), 0)
        t_blank2 = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, defPos,
                      defSiz, 0)
        t_head2 = wx.StaticText(self, wx.ID_ANY, "--- Hot Spot ---", defPos,
                     wx.Size(300, -1), 0)
        t_blank3 = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, defPos,
                      defSiz, 0)
        t_head3 = wx.StaticText(self, wx.ID_ANY, "--- Link Destination ---",
                     defPos, wx.Size(300, -1), 0)
        t_linkType = wx.StaticText(self, wx.ID_ANY, "Link Type:", defPos,
                        t_size, wx.ALIGN_RIGHT)
        t_fromLeft = wx.StaticText(self, wx.ID_ANY, "Left:", defPos,
                        t_size, wx.ALIGN_RIGHT)
        t_fromTop = wx.StaticText(self, wx.ID_ANY, "Top:", defPos,
                       t_size, wx.ALIGN_RIGHT)
        t_fromWidth = wx.StaticText(self, wx.ID_ANY, "Width:", defPos,
                         t_size, wx.ALIGN_RIGHT)
        t_fromHeight = wx.StaticText(self, wx.ID_ANY, "Height:", defPos,
                          t_size, wx.ALIGN_RIGHT)
        t_toFile = wx.StaticText(self, wx.ID_ANY, "File:", defPos,
                      t_size, wx.ALIGN_RIGHT)
        t_toURI = wx.StaticText(self, wx.ID_ANY, "URL:", defPos,
                     t_size, wx.ALIGN_RIGHT)
        t_toPage = wx.StaticText(self, wx.ID_ANY, "To Page:", defPos,
                      t_size, wx.ALIGN_RIGHT)
        t_toName = wx.StaticText(self, wx.ID_ANY, "Name:", defPos,
                      t_size, wx.ALIGN_RIGHT)
        t_toLeft = wx.StaticText(self, wx.ID_ANY, "@Left:", defPos,
                      t_size, wx.ALIGN_RIGHT)
        t_toHeight = wx.StaticText(self, wx.ID_ANY, "@Height:", defPos,
                        t_size, wx.ALIGN_RIGHT)
        t_Update = wx.StaticText(self, wx.ID_ANY, "Apply link changes before paging",
                      defPos, defSiz, 0)
        t_NewLink = wx.StaticText(self, wx.ID_ANY, "Create new link",
                       defPos, defSiz, 0)
        t_Save = wx.StaticText(self, wx.ID_ANY, "Save changes to file",
                    defPos, defSiz, 0)
        self.linkTypeStrings = ["NONE", "GOTO", "URI", "LAUNCH",
                                "NAMED", "GOTOR"]
        self.linkType = wx.Choice(self, wx.ID_ANY, defPos, defSiz,
                           self.linkTypeStrings, 0)
        self.linkType.SetBackgroundColour(wx.Colour(240, 230, 140))
        self.fromLeft = wx.SpinCtrl(self, wx.ID_ANY, wx.EmptyString,
                           defPos, wx.Size(60, -1), 
                           wx.TE_RIGHT|wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER,
                           0, 9999, 0 )
        self.fromTop = wx.SpinCtrl(self, wx.ID_ANY, wx.EmptyString,
                          defPos, wx.Size(60, -1), 
                          wx.TE_RIGHT|wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER,
                          0, 9999, 0 )
        self.fromWidth = wx.SpinCtrl(self, wx.ID_ANY, wx.EmptyString,
                            defPos, wx.Size(60, -1), 
                            wx.TE_RIGHT|wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER,
                            0, 9999, 0 )
        self.fromHeight = wx.SpinCtrl(self, wx.ID_ANY, wx.EmptyString,
                             defPos, wx.Size(60, -1), 
                             wx.TE_RIGHT|wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER,
                             0, 9999, 0 )
        self.toFile = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, defPos,
                         wx.Size(300, -1), wx.TE_PROCESS_ENTER)
        self.toURI = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, defPos,
                        wx.Size(300, -1), wx.TE_PROCESS_ENTER)
        self.toPage = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, defPos,
                         wx.Size(40, -1), wx.TE_RIGHT|wx.TE_PROCESS_ENTER)
        self.toNameStrings = ["FirstPage", "LastPage",
                              "NextPage", "PrevPage"]
        self.toName = wx.Choice(self, wx.ID_ANY, defPos, defSiz,
                         self.toNameStrings, 0)
        self.toLeft = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, defPos,
                         wx.Size(40, -1), wx.TE_RIGHT|wx.TE_PROCESS_ENTER)
        self.toHeight = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, defPos,
                           wx.Size(40, -1), wx.TE_RIGHT|wx.TE_PROCESS_ENTER)
        self.btn_Update = wx.Button(self, wx.ID_ANY, "update",
                             defPos, wx.Size(70, -1), 0)
        self.btn_NewLink = wx.Button(self, wx.ID_ANY, "new",
                              defPos, wx.Size(70, -1), 0)
        self.btn_Save = wx.Button(self, wx.ID_ANY, "save",
                           defPos, wx.Size(70, -1), 0)
        linie1 = wx.StaticLine(self, wx.ID_ANY,
                    defPos, defSiz, wx.LI_VERTICAL)
        #======================================================================
        # the main sizer of the dialog
        #======================================================================
        self.szr00 = wx.BoxSizer(wx.HORIZONTAL)
        szr10 = wx.BoxSizer(wx.VERTICAL)
        szr20 = wx.BoxSizer(wx.HORIZONTAL)
        szr20.Add(self.btn_Next, 0, wx.ALL, 5)
        szr20.Add(self.btn_Previous, 0, wx.ALL, 5)
        szr20.Add(self.TextToPage, 0, wx.ALL, 5)
        szr20.Add(self.statPageMax, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        szr20.Add(self.paperform, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        
        szr30 = wx.FlexGridSizer(17, 2, 0, 0)
        szr30.Add(t_blank1, 0, wx.ALL, 5)
        szr30.Add(t_head1, 0, wx.ALL, 5)
        szr30.Add(t_linkType, 0, wx.ALL, 5)
        szr30.Add(self.linkType, 0, wx.ALL, 5)
        szr30.Add(t_blank2, 0, wx.ALL, 5)
        szr30.Add(t_head2, 0, wx.ALL, 5)
        szr30.Add(t_fromLeft, 0, wx.ALL, 5)
        szr30.Add(self.fromLeft, 0, wx.ALL, 5)
        szr30.Add(t_fromTop, 0, wx.ALL, 5)
        szr30.Add(self.fromTop, 0, wx.ALL, 5)
        szr30.Add(t_fromWidth, 0, wx.ALL, 5)
        szr30.Add(self.fromWidth, 0, wx.ALL, 5)
        szr30.Add(t_fromHeight, 0, wx.ALL, 5)
        szr30.Add(self.fromHeight, 0, wx.ALL, 5)
        szr30.Add(t_blank3, 0, wx.ALL, 5)
        szr30.Add(t_head3, 0, wx.ALL, 5)
        szr30.Add(t_toPage, 0, wx.ALL, 5)
        szr30.Add(self.toPage, 0, wx.ALL, 5)
        szr30.Add(t_toLeft, 0, wx.ALL, 5)
        szr30.Add(self.toLeft, 0, wx.ALL, 5)
        szr30.Add(t_toHeight, 0, wx.ALL, 5)
        szr30.Add(self.toHeight, 0, wx.ALL, 5)
        szr30.Add(t_toFile, 0, wx.ALL, 5)
        szr30.Add(self.toFile, 0, wx.ALL, 5)
        szr30.Add(t_toURI, 0, wx.ALL, 5)
        szr30.Add(self.toURI, 0, wx.ALL, 5)
        szr30.Add(t_toName, 0, wx.ALL, 5)
        szr30.Add(self.toName, 0, wx.ALL, 5)
        szr30.Add(self.btn_Update, 0, wx.ALL, 5)
        szr30.Add(t_Update, 0, wx.ALL, 5)
        szr30.Add(self.btn_NewLink, 0, wx.ALL, 5)
        szr30.Add(t_NewLink, 0, wx.ALL, 5)
        szr30.Add(self.btn_Save, 0, wx.ALL, 5)
        szr30.Add(t_Save, 0, wx.ALL, 5)
        # sizer ready, represents top dialog line
        szr10.Add(szr20, 0, wx.EXPAND, 5)
        szr10.Add(self.PDFimage, 0, wx.ALL, 5)
        self.szr00.Add(szr30, 0, wx.EXPAND, 5)
        self.szr00.Add(linie1, 0, wx.EXPAND, 5)
        self.szr00.Add(szr10, 0, wx.EXPAND, 5)
        # main sizer now ready - request final size & layout adjustments
        self.szr00.Fit(self)
        self.SetSizer(self.szr00)
        self.Layout()
        # center dialog on screen
        self.Centre(wx.BOTH)

        # Bind buttons and fields to event handlers
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
        self.toURI.Bind(wx.EVT_TEXT_ENTER, self.on_link_changed)
        self.toPage.Bind(wx.EVT_TEXT_ENTER, self.on_link_changed)
        self.toName.Bind(wx.EVT_CHOICE, self.on_link_changed)
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
        if len(self.page_links) > len(self.link_rects):
            # will only happen on 1st time if page 0 contains links
            self.draw_links()
        evt.Skip()
        return
    
    def on_move_mouse(self, evt):
        pos = evt.GetPosition()
        in_rect = self.get_linkrect_idx(pos)
        in_brect = self.get_bottomrect_idx(pos)
        self.PDFimage.SetCursor(cur_norm)
            
        if in_brect >= 0:
            self.PDFimage.SetCursor(cur_nwse)
        elif in_rect >= 0:
            self.PDFimage.SetCursor(cur_hand)
        
        if self.adding_link:
            if in_rect >= 0 or in_brect >= 0:
                evt.Skip()
                return
            self.PDFimage.SetCursor(cur_cross)
            if evt.LeftIsDown():
                w = abs(pos.x - self.addrect.x)
                h = abs(pos.y - self.addrect.y)
                x = min(self.addrect.x, pos.x)
                y = min(self.addrect.y, pos.y)
                if not self.is_in_free_area(wx.Rect(x, y, w, h)):
                    evt.Skip()
                    return
                if h <= self.sense or w <= self.sense: # too small!
                    evt.Skip()
                    return
                self.fromHeight.SetValue(h)       # update ...
                self.fromWidth.SetValue(w)       # ... spin ...
                self.fromLeft.SetValue(x)       # ... controls
                self.fromTop.SetValue(y)
                self.redraw_bitmap()
                self.draw_links()
                self.draw_rect(x, y, w, h, "BLUE")  # draw rectangle
                self.current_idx = -1
            evt.Skip()
            return

        if len(self.page_links) == 0:     # there are no links yet
            evt.Skip()
            return
        
        if self.resize_rect:
            self.PDFimage.SetCursor(cur_nwse)
            if evt.LeftIsDown():
                r = self.link_rects[in_brect]
                w = pos.x - r.x
                h = pos.y - r.y
                nr = wx.Rect(r.x, r.y, w, h)
                if w >= 2 * self.sense and h >= 2 * self.sense and \
                    self.is_in_free_area(nr, ok = in_brect):
                    l = self.page_links[in_brect]
                    l["from"] = self.wxRect_to_Rect(nr)
                    l["update"] = True
                    self.page_links[in_brect] = l
                    self.fromHeight.SetValue(h)
                    self.fromWidth.SetValue(w)
                    self.redraw_bitmap()
                    self.draw_links()
            evt.Skip()
            return
            
        if in_rect >= 0:
            self.PDFimage.SetCursor(cur_hand)
            self.PDFimage.SetToolTip(self.link_texts[in_rect])
            if self.dragging_link:
                if evt.LeftIsDown():
                    r = self.link_rects[in_rect]
                    x = pos.x - self.dragstart_x
                    y = pos.y - self.dragstart_y
                    w = r.width
                    h = r.height
                    newrect = wx.Rect(x, y, w, h)
                    if self.is_in_free_area(newrect, ok = in_rect):
                        self.fromLeft.SetValue(x)
                        self.fromTop.SetValue(y)
                        fr = self.wxRect_to_Rect(newrect)
                        l = self.page_links[in_rect]
                        l["from"] = fr
                        l["update"] = True
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

    def on_next_page(self, event):                   # means: page forward
        page = getint(self.TextToPage.Value) + 1 # current page + 1
        page = min(page, self.doc.pageCount)     # cannot go beyond last page
        self.TextToPage.ChangeValue(str(page))        # put target page# in screen
        self.new_image(page)                    # refresh the layout
        event.Skip()

    def on_previous_page(self, event):               # means: page back
        page = getint(self.TextToPage.Value) - 1 # current page - 1
        page = max(page, 1)                      # cannot go before page 1
        self.TextToPage.ChangeValue(str(page))        # put target page# in screen
        self.new_image(page)
        event.Skip()

    def on_goto_page(self, event):                   # means: go to page number
        page = getint(self.TextToPage.Value)     # get page# from screen
        page = min(page, len(self.doc))          # cannot go beyond last page
        page = max(page, 1)                      # cannot go before page 1
        self.TextToPage.ChangeValue(str(page))   # make sure it's on the screen
        self.new_image(page)
        event.Skip()

    def on_update_page_links(self, evt):
        pg = self.doc[getint(self.TextToPage.Value) - 1]
        for i in range(len(self.page_links)):
            l = self.page_links[i]
            if l.get("update", False):
                if l["xref"] == 0:
                    pg.insertLink(l)
                elif l["kind"] < 1 or l["kind"] > len(self.linkTypeStrings):
                    pg.deleteLink(l)
                else:
                    pg.updateLink(l)
            l["update"] = False
            self.page_links[i] = l
        evt.Skip()
        return
    
    def on_link_changed(self, evt):
        if  self.current_idx < 0:
            evt.Skip()
            return
        repaint = False
        lnk = self.page_links[self.current_idx]
        lkind = self.linkType.GetSelection()
        lnk["kind"] = lkind
        
        r = wx.Rect(self.fromLeft.Value, self.fromTop.Value,
                    self.fromWidth.Value, self.fromHeight.Value)
        lr = self.link_rects[self.current_idx]

        if tuple(r) != tuple(lr):
            if self.is_in_free_area(r, ok = self.current_idx):
                lnk["from"] = self.wxRect_to_Rect(r)
                lnk["update"] = True
                repaint = True
            else:
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

        lnk["to"] = new_to
        
        if self.toPage.IsModified:
            if self.toPage.Value.isdecimal():
                lnk["page"] = int(self.toPage.Value) - 1
            else:
                lnk["page"] = 0
            repaint = True
            lnk["update"] = True

        if self.toURI.IsModified:
            lnk["uri"] = self.toURI.Value
            repaint = True
            lnk["update"] = True

        if self.toFile.IsModified:
            lnk["file"] = self.toFile.Value
            repaint = True
            lnk["update"] = True

        n = self.toName.GetSelection()
        scr_name = self.toName.GetString(n)
        if scr_name != lnk.get("name", ""):
            lnk["name"] = scr_name 
            repaint = True
            lnk["update"] = True
                
        self.page_links[self.current_idx] = lnk
        if repaint:
            self.redraw_bitmap()
            self.draw_links()
            r = self.link_rects[self.current_idx]
            self.draw_rect(r.x, r.y, r.width, r.height, "RED")
        evt.Skip()
        return
    
    def on_linkType_changed(self, evt):
        """User changed link kind, so prepare available fields."""
        lt = self.linkType.GetSelection()
        self.prep_link_details(lt)
            
        if lt == fitz.LINK_GOTO:
            if not self.toPage.Value.isdecimal():
                self.toPage.ChangeValue("?")
            self.toPage.Enable()
            if not self.toLeft.Value.isdecimal():
                self.toLeft.ChangeValue("?")
            self.toLeft.Enable()
            if not self.toHeight.Value.isdecimal():
                self.toHeight.ChangeValue("?")
            self.toHeight.Enable()

        elif lt == fitz.LINK_GOTOR:
            if not self.toFile.Value:
                self.toFile.ChangeValue("filename?")
            self.toFile.Enable()
            if not self.toPage.Value.isdecimal():
                self.toPage.ChangeValue("?")
            self.toPage.Enable()
            if not self.toLeft.Value.isdecimal():
                self.toLeft.ChangeValue("?")
            self.toLeft.Enable()
            if not self.toHeight.Value.isdecimal():
                self.toHeight.ChangeValue("?")
            self.toHeight.Enable()
            
        elif lt == fitz.LINK_URI:
            if not self.toURI.Value:
                self.toURI.ChangeValue("URL?")
            self.toURI.Enable()
            
        elif lt == fitz.LINK_LAUNCH:
            if not self.toFile.Value:
                self.toFile.ChangeValue("filename?")
            self.toFile.Enable()
            
        elif lt == fitz.LINK_NAMED:
            self.toName.SetSelection(0)
            self.toName.Enable()
            
        lnk = self.page_links[self.current_idx]
        lnk["update"] = True
        lnk["kind"] = lt
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
        self.toLeft.ChangeValue("36")
        self.toHeight.ChangeValue(str(self.page_height -36))
        self.toPage.Enable()
        self.toLeft.Enable()
        self.toHeight.Enable()
        evt.Skip()
        return
    
    def on_left_up(self, evt):
        if self.adding_link:
            n = self.linkType.GetSelection()
            wx_r = wx.Rect(self.fromLeft.Value, self.fromTop.Value,
                           self.fromWidth.Value, self.fromHeight.Value)
            l_from = self.wxRect_to_Rect(wx_r)
            l_to = fitz.Point(float(self.toLeft.Value),
                              float(self.toHeight.Value))
            lnk = {"kind": n, "xref": 0, "from": l_from, "to": l_to,
                   "page": int(self.toPage.Value) - 1, "update": True}
            
            self.link_rects.append(wx_r)
            self.page_links.append(lnk)
            p = wx_r.BottomRight
            br = wx.Rect(p.x - self.sense, p.y - self.sense,
                         2*self.sense, 2*self.sense)
            self.link_bottom_rects.append(br)
            self.link_texts.append("page " + self.toPage.Value)
            self.adding_link = False
            del self.addrect
            self.current_idx = -1
            self.PDFimage.SetCursor(cur_norm)
            self.clear_link_details()
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

    def draw_links(self):
        dc = wx.ClientDC(self.PDFimage)
        dc.SetPen(wx.Pen("BLUE", width=1))
        dc.SetBrush(wx.Brush("BLUE", style=wx.BRUSHSTYLE_TRANSPARENT))
        self.link_rects = []
        self.link_bottom_rects = []
        self.link_texts = []

        for lnk in self.page_links:
            wx_r = self.Rect_to_wxRect(lnk["from"])
            dc.DrawRectangle(wx_r[0], wx_r[1], wx_r[2], wx_r[3])
            self.link_rects.append(wx_r)
            p = wx_r.BottomRight
            br = wx.Rect(p.x - self.sense, p.y - self.sense,
                         2*self.sense, 2*self.sense)
            self.link_bottom_rects.append(br)
            if lnk["kind"] == fitz.LINK_GOTO:
                txt = "page " + str(lnk["page"] + 1)
            elif lnk["kind"] == fitz.LINK_GOTOR:
                txt = lnk["file"]
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
        self.toFile.Disable()
        self.toLeft.Disable()
        self.toHeight.Disable()
        self.toURI.Disable()
        self.toPage.Disable()
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

    def Rect_to_wxRect(self, fr):
        """ Return a zoomed wx.Rect for given fitz.Rect."""
        r = (fr * self.matrix).irect   # zoomed IRect
        return wx.Rect(r.x0, r.y0, r.width, r.height)   # wx.Rect version
    
    def wxRect_to_Rect(self, wr):
        """ Return a shrunk fitz.Rect for given wx.Rect."""
        r = fitz.Rect(wr.x, wr.y, wr.x + wr.width, wr.y + wr.height)
        return r * self.imatrix        # shrunk fitz.Rect version
    
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
        pix = page.getPixmap(matrix = self.matrix)
        bmp = bmp_buffer(pix.w, pix.h, pix.samples)
        paper = FindFit(page.bound().x1, page.bound().y1)
        self.paperform.Label = "Page format: " + paper
        self.page_links = page.getLinks()
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
