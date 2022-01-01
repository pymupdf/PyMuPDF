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
%}
