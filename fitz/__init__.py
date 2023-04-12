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

from fitz.fitz import *

# define the supported colorspaces for convenience
fitz.csRGB = fitz.Colorspace(fitz.CS_RGB)
fitz.csGRAY = fitz.Colorspace(fitz.CS_GRAY)
fitz.csCMYK = fitz.Colorspace(fitz.CS_CMYK)
csRGB = fitz.csRGB
csGRAY = fitz.csGRAY
csCMYK = fitz.csCMYK

# create the TOOLS object.
#
# Unfortunately it seems that this is never be destructed even if we use an
# atexit() handler, which makes MuPDF's Memento list it as a leak. In fitz.i
# we use Memento_startLeaking()/Memento_stopLeaking() when allocating
# the Tools instance so at least the leak is marked as known.
#
TOOLS = fitz.Tools()
TOOLS.thisown = True
fitz.TOOLS = TOOLS

# This atexit handler runs, but doesn't cause ~Tools() to be run.
#
import atexit


def cleanup_tools(TOOLS):
    # print(f'cleanup_tools: TOOLS={TOOLS} id(TOOLS)={id(TOOLS)}')
    # print(f'TOOLS.thisown={TOOLS.thisown}')
    del TOOLS
    del fitz.TOOLS


atexit.register(cleanup_tools, TOOLS)


# Require that MuPDF matches fitz.TOOLS.mupdf_version(); also allow use with
# next minor version (e.g. 1.21.2 => 1.22), so we can test with mupdf master.
#
def v_str_to_tuple(s):
    return tuple(map(int, s.split('.')))

def v_tuple_to_string(t):
    return '.'.join(map(str, t))

mupdf_version_tuple = v_str_to_tuple(fitz.TOOLS.mupdf_version())
mupdf_version_tuple_required = v_str_to_tuple(fitz.VersionFitz)
mupdf_version_tuple_required_prev = (mupdf_version_tuple_required[0], mupdf_version_tuple_required[1]-1)
mupdf_version_tuple_required_next = (mupdf_version_tuple_required[0], mupdf_version_tuple_required[1]+1)

if mupdf_version_tuple[:2] not in (
        mupdf_version_tuple_required_prev[:2],
        mupdf_version_tuple_required[:2], 
        mupdf_version_tuple_required_next[:2],
        ):
    raise ValueError(
            f'MuPDF library {v_tuple_to_string(mupdf_version_tuple)!r} mismatch:'
            f' require'
            f' {v_tuple_to_string(mupdf_version_tuple_required_prev)!r}'
            f' or {v_tuple_to_string(mupdf_version_tuple_required)!r}'
            f' or {v_tuple_to_string(mupdf_version_tuple_required_next)!r}'
            f'.'
            )

# copy functions in 'utils' to their respective fitz classes
import fitz.utils

# ------------------------------------------------------------------------------
# General
# ------------------------------------------------------------------------------
fitz.recover_quad = fitz.utils.recover_quad
fitz.recover_bbox_quad = fitz.utils.recover_bbox_quad
fitz.recover_line_quad = fitz.utils.recover_line_quad
fitz.recover_span_quad = fitz.utils.recover_span_quad
fitz.recover_char_quad = fitz.utils.recover_char_quad

# ------------------------------------------------------------------------------
# Document
# ------------------------------------------------------------------------------
fitz.open = fitz.Document
fitz.Document._do_links = fitz.utils.do_links
fitz.Document.del_toc_item = fitz.utils.del_toc_item
fitz.Document.get_char_widths = fitz.utils.get_char_widths
fitz.Document.get_ocmd = fitz.utils.get_ocmd
fitz.Document.get_page_labels = fitz.utils.get_page_labels
fitz.Document.get_page_numbers = fitz.utils.get_page_numbers
fitz.Document.get_page_pixmap = fitz.utils.get_page_pixmap
fitz.Document.get_page_text = fitz.utils.get_page_text
fitz.Document.get_toc = fitz.utils.get_toc
fitz.Document.has_annots = fitz.utils.has_annots
fitz.Document.has_links = fitz.utils.has_links
fitz.Document.insert_page = fitz.utils.insert_page
fitz.Document.new_page = fitz.utils.new_page
fitz.Document.scrub = fitz.utils.scrub
fitz.Document.search_page_for = fitz.utils.search_page_for
fitz.Document.set_metadata = fitz.utils.set_metadata
fitz.Document.set_ocmd = fitz.utils.set_ocmd
fitz.Document.set_page_labels = fitz.utils.set_page_labels
fitz.Document.set_toc = fitz.utils.set_toc
fitz.Document.set_toc_item = fitz.utils.set_toc_item
fitz.Document.tobytes = fitz.Document.write
fitz.Document.subset_fonts = fitz.utils.subset_fonts
fitz.Document.get_oc = fitz.utils.get_oc
fitz.Document.set_oc = fitz.utils.set_oc
fitz.Document.xref_copy = fitz.utils.xref_copy


# ------------------------------------------------------------------------------
# Page
# ------------------------------------------------------------------------------
fitz.Page.apply_redactions = fitz.utils.apply_redactions
fitz.Page.delete_widget = fitz.utils.delete_widget
fitz.Page.draw_bezier = fitz.utils.draw_bezier
fitz.Page.draw_circle = fitz.utils.draw_circle
fitz.Page.draw_curve = fitz.utils.draw_curve
fitz.Page.draw_line = fitz.utils.draw_line
fitz.Page.draw_oval = fitz.utils.draw_oval
fitz.Page.draw_polyline = fitz.utils.draw_polyline
fitz.Page.draw_quad = fitz.utils.draw_quad
fitz.Page.draw_rect = fitz.utils.draw_rect
fitz.Page.draw_sector = fitz.utils.draw_sector
fitz.Page.draw_squiggle = fitz.utils.draw_squiggle
fitz.Page.draw_zigzag = fitz.utils.draw_zigzag
fitz.Page.get_links = fitz.utils.get_links
fitz.Page.get_pixmap = fitz.utils.get_pixmap
fitz.Page.get_text = fitz.utils.get_text
fitz.Page.get_image_info = fitz.utils.get_image_info
fitz.Page.get_text_blocks = fitz.utils.get_text_blocks
fitz.Page.get_text_selection = fitz.utils.get_text_selection
fitz.Page.get_text_words = fitz.utils.get_text_words
fitz.Page.get_textbox = fitz.utils.get_textbox
fitz.Page.insert_image = fitz.utils.insert_image
fitz.Page.insert_link = fitz.utils.insert_link
fitz.Page.insert_text = fitz.utils.insert_text
fitz.Page.insert_textbox = fitz.utils.insert_textbox
fitz.Page.new_shape = lambda x: fitz.utils.Shape(x)
fitz.Page.search_for = fitz.utils.search_for
fitz.Page.show_pdf_page = fitz.utils.show_pdf_page
fitz.Page.update_link = fitz.utils.update_link
fitz.Page.write_text = fitz.utils.write_text
fitz.Page.get_label = fitz.utils.get_label
fitz.Page.get_image_rects = fitz.utils.get_image_rects
fitz.Page.get_textpage_ocr = fitz.utils.get_textpage_ocr
fitz.Page.delete_image = fitz.utils.delete_image
fitz.Page.replace_image = fitz.utils.replace_image

# ------------------------------------------------------------------------
# Annot
# ------------------------------------------------------------------------
fitz.Annot.get_text = fitz.utils.get_text
fitz.Annot.get_textbox = fitz.utils.get_textbox

# ------------------------------------------------------------------------
# Rect and IRect
# ------------------------------------------------------------------------
fitz.Rect.get_area = fitz.utils.get_area
fitz.IRect.get_area = fitz.utils.get_area

# ------------------------------------------------------------------------
# TextWriter
# ------------------------------------------------------------------------
fitz.TextWriter.fill_textbox = fitz.utils.fill_textbox


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
        objname = objname.replace("fitz.fitz.", "")
        objname = objname.replace("fitz.utils.", "")
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
    _alias(fitz.Document, "chapterCount", "chapter_count")
    _alias(fitz.Document, "chapterPageCount", "chapter_page_count")
    _alias(fitz.Document, "convertToPDF", "convert_to_pdf")
    _alias(fitz.Document, "copyPage", "copy_page")
    _alias(fitz.Document, "deletePage", "delete_page")
    _alias(fitz.Document, "deletePageRange", "delete_pages")
    _alias(fitz.Document, "embeddedFileAdd", "embfile_add")
    _alias(fitz.Document, "embeddedFileCount", "embfile_count")
    _alias(fitz.Document, "embeddedFileDel", "embfile_del")
    _alias(fitz.Document, "embeddedFileGet", "embfile_get")
    _alias(fitz.Document, "embeddedFileInfo", "embfile_info")
    _alias(fitz.Document, "embeddedFileNames", "embfile_names")
    _alias(fitz.Document, "embeddedFileUpd", "embfile_upd")
    _alias(fitz.Document, "extractFont", "extract_font")
    _alias(fitz.Document, "extractImage", "extract_image")
    _alias(fitz.Document, "findBookmark", "find_bookmark")
    _alias(fitz.Document, "fullcopyPage", "fullcopy_page")
    _alias(fitz.Document, "getCharWidths", "get_char_widths")
    _alias(fitz.Document, "getOCGs", "get_ocgs")
    _alias(fitz.Document, "getPageFontList", "get_page_fonts")
    _alias(fitz.Document, "getPageImageList", "get_page_images")
    _alias(fitz.Document, "getPagePixmap", "get_page_pixmap")
    _alias(fitz.Document, "getPageText", "get_page_text")
    _alias(fitz.Document, "getPageXObjectList", "get_page_xobjects")
    _alias(fitz.Document, "getSigFlags", "get_sigflags")
    _alias(fitz.Document, "getToC", "get_toc")
    _alias(fitz.Document, "getXmlMetadata", "get_xml_metadata")
    _alias(fitz.Document, "insertPage", "insert_page")
    _alias(fitz.Document, "insertPDF", "insert_pdf")
    _alias(fitz.Document, "isDirty", "is_dirty")
    _alias(fitz.Document, "isFormPDF", "is_form_pdf")
    _alias(fitz.Document, "isPDF", "is_pdf")
    _alias(fitz.Document, "isReflowable", "is_reflowable")
    _alias(fitz.Document, "isRepaired", "is_repaired")
    _alias(fitz.Document, "isStream", "xref_is_stream")
    _alias(fitz.Document, "is_stream", "xref_is_stream")
    _alias(fitz.Document, "lastLocation", "last_location")
    _alias(fitz.Document, "loadPage", "load_page")
    _alias(fitz.Document, "makeBookmark", "make_bookmark")
    _alias(fitz.Document, "metadataXML", "xref_xml_metadata")
    _alias(fitz.Document, "movePage", "move_page")
    _alias(fitz.Document, "needsPass", "needs_pass")
    _alias(fitz.Document, "newPage", "new_page")
    _alias(fitz.Document, "nextLocation", "next_location")
    _alias(fitz.Document, "pageCount", "page_count")
    _alias(fitz.Document, "pageCropBox", "page_cropbox")
    _alias(fitz.Document, "pageXref", "page_xref")
    _alias(fitz.Document, "PDFCatalog", "pdf_catalog")
    _alias(fitz.Document, "PDFTrailer", "pdf_trailer")
    _alias(fitz.Document, "previousLocation", "prev_location")
    _alias(fitz.Document, "resolveLink", "resolve_link")
    _alias(fitz.Document, "searchPageFor", "search_page_for")
    _alias(fitz.Document, "setLanguage", "set_language")
    _alias(fitz.Document, "setMetadata", "set_metadata")
    _alias(fitz.Document, "setToC", "set_toc")
    _alias(fitz.Document, "setXmlMetadata", "set_xml_metadata")
    _alias(fitz.Document, "updateObject", "update_object")
    _alias(fitz.Document, "updateStream", "update_stream")
    _alias(fitz.Document, "xrefLength", "xref_length")
    _alias(fitz.Document, "xrefObject", "xref_object")
    _alias(fitz.Document, "xrefStream", "xref_stream")
    _alias(fitz.Document, "xrefStreamRaw", "xref_stream_raw")

    # deprecated Page aliases
    _alias(fitz.Page, "_isWrapped", "is_wrapped")
    _alias(fitz.Page, "addCaretAnnot", "add_caret_annot")
    _alias(fitz.Page, "addCircleAnnot", "add_circle_annot")
    _alias(fitz.Page, "addFileAnnot", "add_file_annot")
    _alias(fitz.Page, "addFreetextAnnot", "add_freetext_annot")
    _alias(fitz.Page, "addHighlightAnnot", "add_highlight_annot")
    _alias(fitz.Page, "addInkAnnot", "add_ink_annot")
    _alias(fitz.Page, "addLineAnnot", "add_line_annot")
    _alias(fitz.Page, "addPolygonAnnot", "add_polygon_annot")
    _alias(fitz.Page, "addPolylineAnnot", "add_polyline_annot")
    _alias(fitz.Page, "addRectAnnot", "add_rect_annot")
    _alias(fitz.Page, "addRedactAnnot", "add_redact_annot")
    _alias(fitz.Page, "addSquigglyAnnot", "add_squiggly_annot")
    _alias(fitz.Page, "addStampAnnot", "add_stamp_annot")
    _alias(fitz.Page, "addStrikeoutAnnot", "add_strikeout_annot")
    _alias(fitz.Page, "addTextAnnot", "add_text_annot")
    _alias(fitz.Page, "addUnderlineAnnot", "add_underline_annot")
    _alias(fitz.Page, "addWidget", "add_widget")
    _alias(fitz.Page, "cleanContents", "clean_contents")
    _alias(fitz.Page, "CropBox", "cropbox")
    _alias(fitz.Page, "CropBoxPosition", "cropbox_position")
    _alias(fitz.Page, "deleteAnnot", "delete_annot")
    _alias(fitz.Page, "deleteLink", "delete_link")
    _alias(fitz.Page, "deleteWidget", "delete_widget")
    _alias(fitz.Page, "derotationMatrix", "derotation_matrix")
    _alias(fitz.Page, "drawBezier", "draw_bezier")
    _alias(fitz.Page, "drawCircle", "draw_circle")
    _alias(fitz.Page, "drawCurve", "draw_curve")
    _alias(fitz.Page, "drawLine", "draw_line")
    _alias(fitz.Page, "drawOval", "draw_oval")
    _alias(fitz.Page, "drawPolyline", "draw_polyline")
    _alias(fitz.Page, "drawQuad", "draw_quad")
    _alias(fitz.Page, "drawRect", "draw_rect")
    _alias(fitz.Page, "drawSector", "draw_sector")
    _alias(fitz.Page, "drawSquiggle", "draw_squiggle")
    _alias(fitz.Page, "drawZigzag", "draw_zigzag")
    _alias(fitz.Page, "firstAnnot", "first_annot")
    _alias(fitz.Page, "firstLink", "first_link")
    _alias(fitz.Page, "firstWidget", "first_widget")
    _alias(fitz.Page, "getContents", "get_contents")
    _alias(fitz.Page, "getDisplayList", "get_displaylist")
    _alias(fitz.Page, "getDrawings", "get_drawings")
    _alias(fitz.Page, "getFontList", "get_fonts")
    _alias(fitz.Page, "getImageBbox", "get_image_bbox")
    _alias(fitz.Page, "getImageList", "get_images")
    _alias(fitz.Page, "getLinks", "get_links")
    _alias(fitz.Page, "getPixmap", "get_pixmap")
    _alias(fitz.Page, "getSVGimage", "get_svg_image")
    _alias(fitz.Page, "getText", "get_text")
    _alias(fitz.Page, "getTextBlocks", "get_text_blocks")
    _alias(fitz.Page, "getTextbox", "get_textbox")
    _alias(fitz.Page, "getTextPage", "get_textpage")
    _alias(fitz.Page, "getTextWords", "get_text_words")
    _alias(fitz.Page, "insertFont", "insert_font")
    _alias(fitz.Page, "insertImage", "insert_image")
    _alias(fitz.Page, "insertLink", "insert_link")
    _alias(fitz.Page, "insertText", "insert_text")
    _alias(fitz.Page, "insertTextbox", "insert_textbox")
    _alias(fitz.Page, "loadAnnot", "load_annot")
    _alias(fitz.Page, "loadLinks", "load_links")
    _alias(fitz.Page, "MediaBox", "mediabox")
    _alias(fitz.Page, "MediaBoxSize", "mediabox_size")
    _alias(fitz.Page, "newShape", "new_shape")
    _alias(fitz.Page, "readContents", "read_contents")
    _alias(fitz.Page, "rotationMatrix", "rotation_matrix")
    _alias(fitz.Page, "searchFor", "search_for")
    _alias(fitz.Page, "setCropBox", "set_cropbox")
    _alias(fitz.Page, "setMediaBox", "set_mediabox")
    _alias(fitz.Page, "setRotation", "set_rotation")
    _alias(fitz.Page, "showPDFpage", "show_pdf_page")
    _alias(fitz.Page, "transformationMatrix", "transformation_matrix")
    _alias(fitz.Page, "updateLink", "update_link")
    _alias(fitz.Page, "wrapContents", "wrap_contents")
    _alias(fitz.Page, "writeText", "write_text")

    # deprecated Shape aliases
    _alias(fitz.utils.Shape, "drawBezier", "draw_bezier")
    _alias(fitz.utils.Shape, "drawCircle", "draw_circle")
    _alias(fitz.utils.Shape, "drawCurve", "draw_curve")
    _alias(fitz.utils.Shape, "drawLine", "draw_line")
    _alias(fitz.utils.Shape, "drawOval", "draw_oval")
    _alias(fitz.utils.Shape, "drawPolyline", "draw_polyline")
    _alias(fitz.utils.Shape, "drawQuad", "draw_quad")
    _alias(fitz.utils.Shape, "drawRect", "draw_rect")
    _alias(fitz.utils.Shape, "drawSector", "draw_sector")
    _alias(fitz.utils.Shape, "drawSquiggle", "draw_squiggle")
    _alias(fitz.utils.Shape, "drawZigzag", "draw_zigzag")
    _alias(fitz.utils.Shape, "insertText", "insert_text")
    _alias(fitz.utils.Shape, "insertTextbox", "insert_textbox")

    # deprecated Annot aliases
    _alias(fitz.Annot, "getText", "get_text")
    _alias(fitz.Annot, "getTextbox", "get_textbox")
    _alias(fitz.Annot, "fileGet", "get_file")
    _alias(fitz.Annot, "fileUpd", "update_file")
    _alias(fitz.Annot, "getPixmap", "get_pixmap")
    _alias(fitz.Annot, "getTextPage", "get_textpage")
    _alias(fitz.Annot, "lineEnds", "line_ends")
    _alias(fitz.Annot, "setBlendMode", "set_blendmode")
    _alias(fitz.Annot, "setBorder", "set_border")
    _alias(fitz.Annot, "setColors", "set_colors")
    _alias(fitz.Annot, "setFlags", "set_flags")
    _alias(fitz.Annot, "setInfo", "set_info")
    _alias(fitz.Annot, "setLineEnds", "set_line_ends")
    _alias(fitz.Annot, "setName", "set_name")
    _alias(fitz.Annot, "setOpacity", "set_opacity")
    _alias(fitz.Annot, "setRect", "set_rect")
    _alias(fitz.Annot, "setOC", "set_oc")
    _alias(fitz.Annot, "soundGet", "get_sound")

    # deprecated TextWriter aliases
    _alias(fitz.TextWriter, "writeText", "write_text")
    _alias(fitz.TextWriter, "fillTextbox", "fill_textbox")

    # deprecated DisplayList aliases
    _alias(fitz.DisplayList, "getPixmap", "get_pixmap")
    _alias(fitz.DisplayList, "getTextPage", "get_textpage")

    # deprecated Pixmap aliases
    _alias(fitz.Pixmap, "setAlpha", "set_alpha")
    _alias(fitz.Pixmap, "gammaWith", "gamma_with")
    _alias(fitz.Pixmap, "tintWith", "tint_with")
    _alias(fitz.Pixmap, "clearWith", "clear_with")
    _alias(fitz.Pixmap, "copyPixmap", "copy")
    _alias(fitz.Pixmap, "getImageData", "tobytes")
    _alias(fitz.Pixmap, "getPNGData", "tobytes")
    _alias(fitz.Pixmap, "getPNGdata", "tobytes")
    _alias(fitz.Pixmap, "writeImage", "save")
    _alias(fitz.Pixmap, "writePNG", "save")
    _alias(fitz.Pixmap, "pillowWrite", "pil_save")
    _alias(fitz.Pixmap, "pillowData", "pil_tobytes")
    _alias(fitz.Pixmap, "invertIRect", "invert_irect")
    _alias(fitz.Pixmap, "setPixel", "set_pixel")
    _alias(fitz.Pixmap, "setOrigin", "set_origin")
    _alias(fitz.Pixmap, "setRect", "set_rect")
    _alias(fitz.Pixmap, "setResolution", "set_dpi")

    # deprecated geometry aliases
    _alias(fitz.Rect, "getArea", "get_area")
    _alias(fitz.IRect, "getArea", "get_area")
    _alias(fitz.Rect, "getRectArea", "get_area")
    _alias(fitz.IRect, "getRectArea", "get_area")
    _alias(fitz.Rect, "includePoint", "include_point")
    _alias(fitz.IRect, "includePoint", "include_point")
    _alias(fitz.Rect, "includeRect", "include_rect")
    _alias(fitz.IRect, "includeRect", "include_rect")
    _alias(fitz.Rect, "isInfinite", "is_infinite")
    _alias(fitz.IRect, "isInfinite", "is_infinite")
    _alias(fitz.Rect, "isEmpty", "is_empty")
    _alias(fitz.IRect, "isEmpty", "is_empty")
    _alias(fitz.Quad, "isEmpty", "is_empty")
    _alias(fitz.Quad, "isRectangular", "is_rectangular")
    _alias(fitz.Quad, "isConvex", "is_convex")
    _alias(fitz.Matrix, "isRectilinear", "is_rectilinear")
    _alias(fitz.Matrix, "preRotate", "prerotate")
    _alias(fitz.Matrix, "preScale", "prescale")
    _alias(fitz.Matrix, "preShear", "preshear")
    _alias(fitz.Matrix, "preTranslate", "pretranslate")

    # deprecated other aliases
    _alias(fitz.Outline, "isExternal", "is_external")
    _alias(fitz.Outline, "isOpen", "is_open")
    _alias(fitz.Link, "isExternal", "is_external")
    _alias(fitz.Link, "setBorder", "set_border")
    _alias(fitz.Link, "setColors", "set_colors")
    _alias(fitz, "getPDFstr", "get_pdf_str")
    _alias(fitz, "getPDFnow", "get_pdf_now")
    _alias(fitz, "PaperSize", "paper_size")
    _alias(fitz, "PaperRect", "paper_rect")
    _alias(fitz, "paperSizes", "paper_sizes")
    _alias(fitz, "ImageProperties", "image_profile")
    _alias(fitz, "planishLine", "planish_line")
    _alias(fitz, "getTextLength", "get_text_length")
    _alias(fitz, "getTextlength", "get_text_length")


fitz.__doc__ = """
PyMuPDF %s: Python bindings for the MuPDF %s library.
Version date: %s.
Built for Python %i.%i on %s (%i-bit).
""" % (
    fitz.VersionBind,
    fitz.VersionFitz,
    fitz.VersionDate,
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
        for k, (r, g, b) in fitz.utils.getColorInfoDict().items()
    ]
)
