%{
/*
# ------------------------------------------------------------------------
# Copyright 2020-2022, Harald Lieder, mailto:harald.lieder@outlook.com
# License: GNU AFFERO GPL 3.0, https://www.gnu.org/licenses/agpl-3.0.html
#
# Part of "PyMuPDF", a Python binding for "MuPDF" (http://mupdf.com), a
# lightweight PDF, XPS, and E-book viewer, renderer and toolkit which is
# maintained and developed by Artifex Software, Inc. https://artifex.com.
# ------------------------------------------------------------------------
*/
// Global switches
// Switch for device hints = no cache
static int no_device_caching = 0;

// Switch for computing glyph of fontsize height
static int small_glyph_heights = 0;

// Switch for returning fontnames including subset prefix
static int subset_fontnames = 0;

// Unset ascender / descender corrections
static int skip_quad_corrections = 0;

// constants: error messages
static const char MSG_BAD_ANNOT_TYPE[] = "bad annot type";
static const char MSG_BAD_APN[] = "bad or missing annot AP/N";
static const char MSG_BAD_ARG_INK_ANNOT[] = "arg must be seq of seq of float pairs";
static const char MSG_BAD_ARG_POINTS[] = "bad seq of points";
static const char MSG_BAD_BUFFER[] = "bad type: 'buffer'";
static const char MSG_BAD_COLOR_SEQ[] = "bad color sequence";
static const char MSG_BAD_DOCUMENT[] = "cannot open broken document";
static const char MSG_BAD_FILETYPE[] = "bad filetype";
static const char MSG_BAD_LOCATION[] = "bad location";
static const char MSG_BAD_OC_CONFIG[] = "bad config number";
static const char MSG_BAD_OC_LAYER[] = "bad layer number";
static const char MSG_BAD_OC_REF[] = "bad 'oc' reference";
static const char MSG_BAD_PAGEID[] = "bad page id";
static const char MSG_BAD_PAGENO[] = "bad page number(s)";
static const char MSG_BAD_PDFROOT[] = "PDF has no root";
static const char MSG_BAD_RECT[] = "rect is infinite or empty";
static const char MSG_BAD_TEXT[] = "bad type: 'text'";
static const char MSG_BAD_XREF[] = "bad xref";
static const char MSG_COLOR_COUNT_FAILED[] = "color count failed";
static const char MSG_FILE_OR_BUFFER[] = "need font file or buffer";
static const char MSG_FONT_FAILED[] = "cannot create font";
static const char MSG_IS_NO_ANNOT[] = "is no annotation";
static const char MSG_IS_NO_IMAGE[] = "is no image";
static const char MSG_IS_NO_PDF[] = "is no PDF";
static const char MSG_IS_NO_DICT[] = "object is no PDF dict";
static const char MSG_PIX_NOALPHA[] = "source pixmap has no alpha";
static const char MSG_PIXEL_OUTSIDE[] = "pixel(s) outside image";
%}
