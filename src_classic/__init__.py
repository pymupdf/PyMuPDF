# ------------------------------------------------------------------------
# Copyright 2020-2022, Harald Lieder, mailto:harald.lieder@outlook.com
# License: GNU AFFERO GPL 3.0, https://www.gnu.org/licenses/agpl-3.0.html
#
# Part of "PyMuPDF", a Python binding for "MuPDF" (http://mupdf.com), a
# lightweight PDF, XPS, and E-book viewer, renderer and toolkit which is
# maintained and developed by Artifex Software, Inc. https://artifex.com.
# ------------------------------------------------------------------------
import sys

import glob
import os
if os.path.exists( 'fitz/__init__.py'):
    if not glob.glob( 'fitz/_fitz*'):
        print( '#' * 40)
        print( '# Warning: current directory appears to contain an incomplete')
        print( '# fitz/ installation directory so "import fitz" may fail.')
        print( '# This can happen if current directory is a PyMuPDF source tree.')
        print( '# Suggest changing to a different current directory.')
        print( '#' * 40)

def message(text=''):
    print(text)

from fitz_old.fitz_old import *

# Allow this to work:
#   import fitz_old as fitz
#   fitz.fitz.TEXT_ALIGN_CENTER
#
fitz = fitz_old

# define the supported colorspaces for convenience
fitz_old.csRGB = fitz_old.Colorspace(fitz_old.CS_RGB)
fitz_old.csGRAY = fitz_old.Colorspace(fitz_old.CS_GRAY)
fitz_old.csCMYK = fitz_old.Colorspace(fitz_old.CS_CMYK)
csRGB = fitz_old.csRGB
csGRAY = fitz_old.csGRAY
csCMYK = fitz_old.csCMYK

# create the TOOLS object.
#
# Unfortunately it seems that this is never be destructed even if we use an
# atexit() handler, which makes MuPDF's Memento list it as a leak. In fitz_old.i
# we use Memento_startLeaking()/Memento_stopLeaking() when allocating
# the Tools instance so at least the leak is marked as known.
#
TOOLS = fitz_old.Tools()
TOOLS.thisown = True
fitz_old.TOOLS = TOOLS

# This atexit handler runs, but doesn't cause ~Tools() to be run.
#
import atexit


def cleanup_tools(TOOLS):
    # print(f'cleanup_tools: TOOLS={TOOLS} id(TOOLS)={id(TOOLS)}')
    # print(f'TOOLS.thisown={TOOLS.thisown}')
    del TOOLS
    del fitz_old.TOOLS


atexit.register(cleanup_tools, TOOLS)


# Require that MuPDF matches fitz_old.TOOLS.mupdf_version(); also allow use with
# next minor version (e.g. 1.21.2 => 1.22), so we can test with mupdf master.
#
def v_str_to_tuple(s):
    return tuple(map(int, s.split('.')))

def v_tuple_to_string(t):
    return '.'.join(map(str, t))

mupdf_version_tuple = v_str_to_tuple(fitz_old.TOOLS.mupdf_version())
mupdf_version_tuple_required = v_str_to_tuple(fitz_old.VersionFitz)
mupdf_version_tuple_required_prev = (mupdf_version_tuple_required[0], mupdf_version_tuple_required[1]-1)
mupdf_version_tuple_required_next = (mupdf_version_tuple_required[0], mupdf_version_tuple_required[1]+1)

# copy functions in 'utils' to their respective fitz classes
import fitz_old.utils
from .table import find_tables

# ------------------------------------------------------------------------------
# General
# ------------------------------------------------------------------------------
fitz_old.recover_quad = fitz_old.utils.recover_quad
fitz_old.recover_bbox_quad = fitz_old.utils.recover_bbox_quad
fitz_old.recover_line_quad = fitz_old.utils.recover_line_quad
fitz_old.recover_span_quad = fitz_old.utils.recover_span_quad
fitz_old.recover_char_quad = fitz_old.utils.recover_char_quad

# ------------------------------------------------------------------------------
# Document
# ------------------------------------------------------------------------------
fitz_old.open = fitz_old.Document
fitz_old.Document._do_links = fitz_old.utils.do_links
fitz_old.Document.del_toc_item = fitz_old.utils.del_toc_item
fitz_old.Document.get_char_widths = fitz_old.utils.get_char_widths
fitz_old.Document.get_ocmd = fitz_old.utils.get_ocmd
fitz_old.Document.get_page_labels = fitz_old.utils.get_page_labels
fitz_old.Document.get_page_numbers = fitz_old.utils.get_page_numbers
fitz_old.Document.get_page_pixmap = fitz_old.utils.get_page_pixmap
fitz_old.Document.get_page_text = fitz_old.utils.get_page_text
fitz_old.Document.get_toc = fitz_old.utils.get_toc
fitz_old.Document.has_annots = fitz_old.utils.has_annots
fitz_old.Document.has_links = fitz_old.utils.has_links
fitz_old.Document.insert_page = fitz_old.utils.insert_page
fitz_old.Document.new_page = fitz_old.utils.new_page
fitz_old.Document.scrub = fitz_old.utils.scrub
fitz_old.Document.search_page_for = fitz_old.utils.search_page_for
fitz_old.Document.set_metadata = fitz_old.utils.set_metadata
fitz_old.Document.set_ocmd = fitz_old.utils.set_ocmd
fitz_old.Document.set_page_labels = fitz_old.utils.set_page_labels
fitz_old.Document.set_toc = fitz_old.utils.set_toc
fitz_old.Document.set_toc_item = fitz_old.utils.set_toc_item
fitz_old.Document.tobytes = fitz_old.Document.write
fitz_old.Document.subset_fonts = fitz_old.utils.subset_fonts
fitz_old.Document.get_oc = fitz_old.utils.get_oc
fitz_old.Document.set_oc = fitz_old.utils.set_oc
fitz_old.Document.xref_copy = fitz_old.utils.xref_copy


# ------------------------------------------------------------------------------
# Page
# ------------------------------------------------------------------------------
fitz_old.Page.apply_redactions = fitz_old.utils.apply_redactions
fitz_old.Page.delete_widget = fitz_old.utils.delete_widget
fitz_old.Page.draw_bezier = fitz_old.utils.draw_bezier
fitz_old.Page.draw_circle = fitz_old.utils.draw_circle
fitz_old.Page.draw_curve = fitz_old.utils.draw_curve
fitz_old.Page.draw_line = fitz_old.utils.draw_line
fitz_old.Page.draw_oval = fitz_old.utils.draw_oval
fitz_old.Page.draw_polyline = fitz_old.utils.draw_polyline
fitz_old.Page.draw_quad = fitz_old.utils.draw_quad
fitz_old.Page.draw_rect = fitz_old.utils.draw_rect
fitz_old.Page.draw_sector = fitz_old.utils.draw_sector
fitz_old.Page.draw_squiggle = fitz_old.utils.draw_squiggle
fitz_old.Page.draw_zigzag = fitz_old.utils.draw_zigzag
fitz_old.Page.get_links = fitz_old.utils.get_links
fitz_old.Page.get_pixmap = fitz_old.utils.get_pixmap
fitz_old.Page.get_text = fitz_old.utils.get_text
fitz_old.Page.get_image_info = fitz_old.utils.get_image_info
fitz_old.Page.get_text_blocks = fitz_old.utils.get_text_blocks
fitz_old.Page.get_text_selection = fitz_old.utils.get_text_selection
fitz_old.Page.get_text_words = fitz_old.utils.get_text_words
fitz_old.Page.get_textbox = fitz_old.utils.get_textbox
fitz_old.Page.insert_image = fitz_old.utils.insert_image
fitz_old.Page.insert_link = fitz_old.utils.insert_link
fitz_old.Page.insert_text = fitz_old.utils.insert_text
fitz_old.Page.insert_textbox = fitz_old.utils.insert_textbox
fitz_old.Page.new_shape = lambda x: fitz_old.utils.Shape(x)
fitz_old.Page.search_for = fitz_old.utils.search_for
fitz_old.Page.show_pdf_page = fitz_old.utils.show_pdf_page
fitz_old.Page.update_link = fitz_old.utils.update_link
fitz_old.Page.write_text = fitz_old.utils.write_text
fitz_old.Page.get_label = fitz_old.utils.get_label
fitz_old.Page.get_image_rects = fitz_old.utils.get_image_rects
fitz_old.Page.get_textpage_ocr = fitz_old.utils.get_textpage_ocr
fitz_old.Page.delete_image = fitz_old.utils.delete_image
fitz_old.Page.replace_image = fitz_old.utils.replace_image
fitz_old.Page.find_tables = find_tables
# ------------------------------------------------------------------------
# Annot
# ------------------------------------------------------------------------
fitz_old.Annot.get_text = fitz_old.utils.get_text
fitz_old.Annot.get_textbox = fitz_old.utils.get_textbox

# ------------------------------------------------------------------------
# Rect and IRect
# ------------------------------------------------------------------------
fitz_old.Rect.get_area = fitz_old.utils.get_area
fitz_old.IRect.get_area = fitz_old.utils.get_area

# ------------------------------------------------------------------------
# TextWriter
# ------------------------------------------------------------------------
fitz_old.TextWriter.fill_textbox = fitz_old.utils.fill_textbox


class FitzDeprecation(DeprecationWarning):
    pass


def restore_aliases():
    import warnings

    warnings.filterwarnings(
        "once",
        category=FitzDeprecation,
    )

    def showthis(msg, cat, filename, lineno, file=None, line=None):
        text = warnings.formatwarning(msg, cat, filename, lineno, line=line)
        s = text.find("FitzDeprecation")
        if s < 0:
            print(text, file=sys.stderr)
            return
        text = text[s:].splitlines()[0][4:]
        print(text, file=sys.stderr)

    warnings.showwarning = showthis

    def _alias(fitz_class, old, new):
        fname = getattr(fitz_class, new)
        r = str(fitz_class)[1:-1]
        objname = " ".join(r.split()[:2])
        objname = objname.replace("fitz_old.fitz_old.", "")
        objname = objname.replace("fitz_old.utils.", "")
        if callable(fname):

            def deprecated_function(*args, **kw):
                msg = "'%s' removed from %s after v1.19 - use '%s'." % (
                    old,
                    objname,
                    new,
                )
                if not VersionBind.startswith("1.18"):
                    warnings.warn(msg, category=FitzDeprecation)
                return fname(*args, **kw)

            setattr(fitz_class, old, deprecated_function)
        else:
            if type(fname) is property:
                setattr(fitz_class, old, property(fname.fget))
            else:
                setattr(fitz_class, old, fname)

        eigen = getattr(fitz_class, old)
        x = fname.__doc__
        if not x:
            x = ""
        try:
            if callable(fname) or type(fname) is property:
                eigen.__doc__ = (
                    "*** Deprecated and removed after v1.19 - use '%s'. ***\n" % new + x
                )
        except:
            pass

    # deprecated Document aliases
    _alias(fitz_old.Document, "chapterCount", "chapter_count")
    _alias(fitz_old.Document, "chapterPageCount", "chapter_page_count")
    _alias(fitz_old.Document, "convertToPDF", "convert_to_pdf")
    _alias(fitz_old.Document, "copyPage", "copy_page")
    _alias(fitz_old.Document, "deletePage", "delete_page")
    _alias(fitz_old.Document, "deletePageRange", "delete_pages")
    _alias(fitz_old.Document, "embeddedFileAdd", "embfile_add")
    _alias(fitz_old.Document, "embeddedFileCount", "embfile_count")
    _alias(fitz_old.Document, "embeddedFileDel", "embfile_del")
    _alias(fitz_old.Document, "embeddedFileGet", "embfile_get")
    _alias(fitz_old.Document, "embeddedFileInfo", "embfile_info")
    _alias(fitz_old.Document, "embeddedFileNames", "embfile_names")
    _alias(fitz_old.Document, "embeddedFileUpd", "embfile_upd")
    _alias(fitz_old.Document, "extractFont", "extract_font")
    _alias(fitz_old.Document, "extractImage", "extract_image")
    _alias(fitz_old.Document, "findBookmark", "find_bookmark")
    _alias(fitz_old.Document, "fullcopyPage", "fullcopy_page")
    _alias(fitz_old.Document, "getCharWidths", "get_char_widths")
    _alias(fitz_old.Document, "getOCGs", "get_ocgs")
    _alias(fitz_old.Document, "getPageFontList", "get_page_fonts")
    _alias(fitz_old.Document, "getPageImageList", "get_page_images")
    _alias(fitz_old.Document, "getPagePixmap", "get_page_pixmap")
    _alias(fitz_old.Document, "getPageText", "get_page_text")
    _alias(fitz_old.Document, "getPageXObjectList", "get_page_xobjects")
    _alias(fitz_old.Document, "getSigFlags", "get_sigflags")
    _alias(fitz_old.Document, "getToC", "get_toc")
    _alias(fitz_old.Document, "getXmlMetadata", "get_xml_metadata")
    _alias(fitz_old.Document, "insertPage", "insert_page")
    _alias(fitz_old.Document, "insertPDF", "insert_pdf")
    _alias(fitz_old.Document, "isDirty", "is_dirty")
    _alias(fitz_old.Document, "isFormPDF", "is_form_pdf")
    _alias(fitz_old.Document, "isPDF", "is_pdf")
    _alias(fitz_old.Document, "isReflowable", "is_reflowable")
    _alias(fitz_old.Document, "isRepaired", "is_repaired")
    _alias(fitz_old.Document, "isStream", "xref_is_stream")
    _alias(fitz_old.Document, "is_stream", "xref_is_stream")
    _alias(fitz_old.Document, "lastLocation", "last_location")
    _alias(fitz_old.Document, "loadPage", "load_page")
    _alias(fitz_old.Document, "makeBookmark", "make_bookmark")
    _alias(fitz_old.Document, "metadataXML", "xref_xml_metadata")
    _alias(fitz_old.Document, "movePage", "move_page")
    _alias(fitz_old.Document, "needsPass", "needs_pass")
    _alias(fitz_old.Document, "newPage", "new_page")
    _alias(fitz_old.Document, "nextLocation", "next_location")
    _alias(fitz_old.Document, "pageCount", "page_count")
    _alias(fitz_old.Document, "pageCropBox", "page_cropbox")
    _alias(fitz_old.Document, "pageXref", "page_xref")
    _alias(fitz_old.Document, "PDFCatalog", "pdf_catalog")
    _alias(fitz_old.Document, "PDFTrailer", "pdf_trailer")
    _alias(fitz_old.Document, "previousLocation", "prev_location")
    _alias(fitz_old.Document, "resolveLink", "resolve_link")
    _alias(fitz_old.Document, "searchPageFor", "search_page_for")
    _alias(fitz_old.Document, "setLanguage", "set_language")
    _alias(fitz_old.Document, "setMetadata", "set_metadata")
    _alias(fitz_old.Document, "setToC", "set_toc")
    _alias(fitz_old.Document, "setXmlMetadata", "set_xml_metadata")
    _alias(fitz_old.Document, "updateObject", "update_object")
    _alias(fitz_old.Document, "updateStream", "update_stream")
    _alias(fitz_old.Document, "xrefLength", "xref_length")
    _alias(fitz_old.Document, "xrefObject", "xref_object")
    _alias(fitz_old.Document, "xrefStream", "xref_stream")
    _alias(fitz_old.Document, "xrefStreamRaw", "xref_stream_raw")

    # deprecated Page aliases
    _alias(fitz_old.Page, "_isWrapped", "is_wrapped")
    _alias(fitz_old.Page, "addCaretAnnot", "add_caret_annot")
    _alias(fitz_old.Page, "addCircleAnnot", "add_circle_annot")
    _alias(fitz_old.Page, "addFileAnnot", "add_file_annot")
    _alias(fitz_old.Page, "addFreetextAnnot", "add_freetext_annot")
    _alias(fitz_old.Page, "addHighlightAnnot", "add_highlight_annot")
    _alias(fitz_old.Page, "addInkAnnot", "add_ink_annot")
    _alias(fitz_old.Page, "addLineAnnot", "add_line_annot")
    _alias(fitz_old.Page, "addPolygonAnnot", "add_polygon_annot")
    _alias(fitz_old.Page, "addPolylineAnnot", "add_polyline_annot")
    _alias(fitz_old.Page, "addRectAnnot", "add_rect_annot")
    _alias(fitz_old.Page, "addRedactAnnot", "add_redact_annot")
    _alias(fitz_old.Page, "addSquigglyAnnot", "add_squiggly_annot")
    _alias(fitz_old.Page, "addStampAnnot", "add_stamp_annot")
    _alias(fitz_old.Page, "addStrikeoutAnnot", "add_strikeout_annot")
    _alias(fitz_old.Page, "addTextAnnot", "add_text_annot")
    _alias(fitz_old.Page, "addUnderlineAnnot", "add_underline_annot")
    _alias(fitz_old.Page, "addWidget", "add_widget")
    _alias(fitz_old.Page, "cleanContents", "clean_contents")
    _alias(fitz_old.Page, "CropBox", "cropbox")
    _alias(fitz_old.Page, "CropBoxPosition", "cropbox_position")
    _alias(fitz_old.Page, "deleteAnnot", "delete_annot")
    _alias(fitz_old.Page, "deleteLink", "delete_link")
    _alias(fitz_old.Page, "deleteWidget", "delete_widget")
    _alias(fitz_old.Page, "derotationMatrix", "derotation_matrix")
    _alias(fitz_old.Page, "drawBezier", "draw_bezier")
    _alias(fitz_old.Page, "drawCircle", "draw_circle")
    _alias(fitz_old.Page, "drawCurve", "draw_curve")
    _alias(fitz_old.Page, "drawLine", "draw_line")
    _alias(fitz_old.Page, "drawOval", "draw_oval")
    _alias(fitz_old.Page, "drawPolyline", "draw_polyline")
    _alias(fitz_old.Page, "drawQuad", "draw_quad")
    _alias(fitz_old.Page, "drawRect", "draw_rect")
    _alias(fitz_old.Page, "drawSector", "draw_sector")
    _alias(fitz_old.Page, "drawSquiggle", "draw_squiggle")
    _alias(fitz_old.Page, "drawZigzag", "draw_zigzag")
    _alias(fitz_old.Page, "firstAnnot", "first_annot")
    _alias(fitz_old.Page, "firstLink", "first_link")
    _alias(fitz_old.Page, "firstWidget", "first_widget")
    _alias(fitz_old.Page, "getContents", "get_contents")
    _alias(fitz_old.Page, "getDisplayList", "get_displaylist")
    _alias(fitz_old.Page, "getDrawings", "get_drawings")
    _alias(fitz_old.Page, "getFontList", "get_fonts")
    _alias(fitz_old.Page, "getImageBbox", "get_image_bbox")
    _alias(fitz_old.Page, "getImageList", "get_images")
    _alias(fitz_old.Page, "getLinks", "get_links")
    _alias(fitz_old.Page, "getPixmap", "get_pixmap")
    _alias(fitz_old.Page, "getSVGimage", "get_svg_image")
    _alias(fitz_old.Page, "getText", "get_text")
    _alias(fitz_old.Page, "getTextBlocks", "get_text_blocks")
    _alias(fitz_old.Page, "getTextbox", "get_textbox")
    _alias(fitz_old.Page, "getTextPage", "get_textpage")
    _alias(fitz_old.Page, "getTextWords", "get_text_words")
    _alias(fitz_old.Page, "insertFont", "insert_font")
    _alias(fitz_old.Page, "insertImage", "insert_image")
    _alias(fitz_old.Page, "insertLink", "insert_link")
    _alias(fitz_old.Page, "insertText", "insert_text")
    _alias(fitz_old.Page, "insertTextbox", "insert_textbox")
    _alias(fitz_old.Page, "loadAnnot", "load_annot")
    _alias(fitz_old.Page, "loadLinks", "load_links")
    _alias(fitz_old.Page, "MediaBox", "mediabox")
    _alias(fitz_old.Page, "MediaBoxSize", "mediabox_size")
    _alias(fitz_old.Page, "newShape", "new_shape")
    _alias(fitz_old.Page, "readContents", "read_contents")
    _alias(fitz_old.Page, "rotationMatrix", "rotation_matrix")
    _alias(fitz_old.Page, "searchFor", "search_for")
    _alias(fitz_old.Page, "setCropBox", "set_cropbox")
    _alias(fitz_old.Page, "setMediaBox", "set_mediabox")
    _alias(fitz_old.Page, "setRotation", "set_rotation")
    _alias(fitz_old.Page, "showPDFpage", "show_pdf_page")
    _alias(fitz_old.Page, "transformationMatrix", "transformation_matrix")
    _alias(fitz_old.Page, "updateLink", "update_link")
    _alias(fitz_old.Page, "wrapContents", "wrap_contents")
    _alias(fitz_old.Page, "writeText", "write_text")

    # deprecated Shape aliases
    _alias(fitz_old.utils.Shape, "drawBezier", "draw_bezier")
    _alias(fitz_old.utils.Shape, "drawCircle", "draw_circle")
    _alias(fitz_old.utils.Shape, "drawCurve", "draw_curve")
    _alias(fitz_old.utils.Shape, "drawLine", "draw_line")
    _alias(fitz_old.utils.Shape, "drawOval", "draw_oval")
    _alias(fitz_old.utils.Shape, "drawPolyline", "draw_polyline")
    _alias(fitz_old.utils.Shape, "drawQuad", "draw_quad")
    _alias(fitz_old.utils.Shape, "drawRect", "draw_rect")
    _alias(fitz_old.utils.Shape, "drawSector", "draw_sector")
    _alias(fitz_old.utils.Shape, "drawSquiggle", "draw_squiggle")
    _alias(fitz_old.utils.Shape, "drawZigzag", "draw_zigzag")
    _alias(fitz_old.utils.Shape, "insertText", "insert_text")
    _alias(fitz_old.utils.Shape, "insertTextbox", "insert_textbox")

    # deprecated Annot aliases
    _alias(fitz_old.Annot, "getText", "get_text")
    _alias(fitz_old.Annot, "getTextbox", "get_textbox")
    _alias(fitz_old.Annot, "fileGet", "get_file")
    _alias(fitz_old.Annot, "fileUpd", "update_file")
    _alias(fitz_old.Annot, "getPixmap", "get_pixmap")
    _alias(fitz_old.Annot, "getTextPage", "get_textpage")
    _alias(fitz_old.Annot, "lineEnds", "line_ends")
    _alias(fitz_old.Annot, "setBlendMode", "set_blendmode")
    _alias(fitz_old.Annot, "setBorder", "set_border")
    _alias(fitz_old.Annot, "setColors", "set_colors")
    _alias(fitz_old.Annot, "setFlags", "set_flags")
    _alias(fitz_old.Annot, "setInfo", "set_info")
    _alias(fitz_old.Annot, "setLineEnds", "set_line_ends")
    _alias(fitz_old.Annot, "setName", "set_name")
    _alias(fitz_old.Annot, "setOpacity", "set_opacity")
    _alias(fitz_old.Annot, "setRect", "set_rect")
    _alias(fitz_old.Annot, "setOC", "set_oc")
    _alias(fitz_old.Annot, "soundGet", "get_sound")

    # deprecated TextWriter aliases
    _alias(fitz_old.TextWriter, "writeText", "write_text")
    _alias(fitz_old.TextWriter, "fillTextbox", "fill_textbox")

    # deprecated DisplayList aliases
    _alias(fitz_old.DisplayList, "getPixmap", "get_pixmap")
    _alias(fitz_old.DisplayList, "getTextPage", "get_textpage")

    # deprecated Pixmap aliases
    _alias(fitz_old.Pixmap, "setAlpha", "set_alpha")
    _alias(fitz_old.Pixmap, "gammaWith", "gamma_with")
    _alias(fitz_old.Pixmap, "tintWith", "tint_with")
    _alias(fitz_old.Pixmap, "clearWith", "clear_with")
    _alias(fitz_old.Pixmap, "copyPixmap", "copy")
    _alias(fitz_old.Pixmap, "getImageData", "tobytes")
    _alias(fitz_old.Pixmap, "getPNGData", "tobytes")
    _alias(fitz_old.Pixmap, "getPNGdata", "tobytes")
    _alias(fitz_old.Pixmap, "writeImage", "save")
    _alias(fitz_old.Pixmap, "writePNG", "save")
    _alias(fitz_old.Pixmap, "pillowWrite", "pil_save")
    _alias(fitz_old.Pixmap, "pillowData", "pil_tobytes")
    _alias(fitz_old.Pixmap, "invertIRect", "invert_irect")
    _alias(fitz_old.Pixmap, "setPixel", "set_pixel")
    _alias(fitz_old.Pixmap, "setOrigin", "set_origin")
    _alias(fitz_old.Pixmap, "setRect", "set_rect")
    _alias(fitz_old.Pixmap, "setResolution", "set_dpi")

    # deprecated geometry aliases
    _alias(fitz_old.Rect, "getArea", "get_area")
    _alias(fitz_old.IRect, "getArea", "get_area")
    _alias(fitz_old.Rect, "getRectArea", "get_area")
    _alias(fitz_old.IRect, "getRectArea", "get_area")
    _alias(fitz_old.Rect, "includePoint", "include_point")
    _alias(fitz_old.IRect, "includePoint", "include_point")
    _alias(fitz_old.Rect, "includeRect", "include_rect")
    _alias(fitz_old.IRect, "includeRect", "include_rect")
    _alias(fitz_old.Rect, "isInfinite", "is_infinite")
    _alias(fitz_old.IRect, "isInfinite", "is_infinite")
    _alias(fitz_old.Rect, "isEmpty", "is_empty")
    _alias(fitz_old.IRect, "isEmpty", "is_empty")
    _alias(fitz_old.Quad, "isEmpty", "is_empty")
    _alias(fitz_old.Quad, "isRectangular", "is_rectangular")
    _alias(fitz_old.Quad, "isConvex", "is_convex")
    _alias(fitz_old.Matrix, "isRectilinear", "is_rectilinear")
    _alias(fitz_old.Matrix, "preRotate", "prerotate")
    _alias(fitz_old.Matrix, "preScale", "prescale")
    _alias(fitz_old.Matrix, "preShear", "preshear")
    _alias(fitz_old.Matrix, "preTranslate", "pretranslate")

    # deprecated other aliases
    _alias(fitz_old.Outline, "isExternal", "is_external")
    _alias(fitz_old.Outline, "isOpen", "is_open")
    _alias(fitz_old.Link, "isExternal", "is_external")
    _alias(fitz_old.Link, "setBorder", "set_border")
    _alias(fitz_old.Link, "setColors", "set_colors")
    _alias(fitz, "getPDFstr", "get_pdf_str")
    _alias(fitz, "getPDFnow", "get_pdf_now")
    _alias(fitz, "PaperSize", "paper_size")
    _alias(fitz, "PaperRect", "paper_rect")
    _alias(fitz, "paperSizes", "paper_sizes")
    _alias(fitz, "ImageProperties", "image_profile")
    _alias(fitz, "planishLine", "planish_line")
    _alias(fitz, "getTextLength", "get_text_length")
    _alias(fitz, "getTextlength", "get_text_length")


fitz_old.__doc__ = """
PyMuPDF %s: Python bindings for the MuPDF %s library.
Version date: %s.
Built for Python %i.%i on %s (%i-bit).
""" % (
    fitz_old.VersionBind,
    fitz_old.VersionFitz,
    fitz_old.VersionDate,
    sys.version_info[0],
    sys.version_info[1],
    sys.platform,
    64 if sys.maxsize > 2**32 else 32,
)

if VersionBind.startswith("1.19"):  # don't generate aliases after v1.19.*
    restore_aliases()

pdfcolor = dict(
    [
        (k, (r / 255, g / 255, b / 255))
        for k, (r, g, b) in fitz_old.utils.getColorInfoDict().items()
    ]
)
__version__ = fitz_old.VersionBind
