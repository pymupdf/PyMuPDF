%{
/*
# ------------------------------------------------------------------------
# Copyright 2020-2021, Harald Lieder, mailto:harald.lieder@outlook.com
# License: GNU AFFERO GPL 3.0, https://www.gnu.org/licenses/agpl-3.0.html
#
# Part of "PyMuPDF", a Python binding for "MuPDF" (http://mupdf.com), a
# lightweight PDF, XPS, and E-book viewer, renderer and toolkit which is
# maintained and developed by Artifex Software, Inc. https://artifex.com.
# ------------------------------------------------------------------------
*/
typedef struct
{
	fz_device super;
	PyObject *out;
	size_t seqno;
} jm_tracedraw_device;

static float trace_device_Linewidth = 0;  // border width if present
static fz_matrix trace_device_ptm;  // page transformation matrix
static fz_matrix trace_device_ctm;  // trace device matrix
static fz_matrix trace_device_rot;
static fz_point trace_pathpoint = {0, 0};
static PyObject *trace_pathdict = NULL;
static fz_rect trace_pathrect;
static float trace_pathfactor;


static void
jm_increase_seqno(fz_context *ctx, fz_device *dev_, ...)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *) dev_;
	dev->seqno += 1;
}


//--------------------------------------------------------------------------
// Check whether the last 3 path items represent a rectangle. This means the
// following conditions must be true:
// (1) 3 connected lines, (2) line 1 and 3 must be horizontal, line 2 must
// vertical. If all is true, modify the path accordngly.
//--------------------------------------------------------------------------
static int
jm_checkrect()
{
	float ftemp;
	PyObject *cmd, *rect, *p1, *p2, *p3, *p4, *p5, *p6, *p7, *p8;
	PyObject *line0, *line1, *line2, *line4;
	PyObject *items = PyDict_GetItem(trace_pathdict, dictkey_items);
	Py_ssize_t len = PyList_Size(items);
	if (len < 3) {
		return 0; // not enough items
	}

	line0 = PyList_GET_ITEM(items, len - 3);
	cmd = PyTuple_GET_ITEM(line0, 0);
	if (strcmp(PyUnicode_AsUTF8(cmd), "l") != 0) {
		return 0; // not a line
	}
	p1 = PyTuple_GET_ITEM(line0, 1);
	p2 = PyTuple_GET_ITEM(line0, 2);

	line1 = PyList_GET_ITEM(items, len - 2);
	cmd = PyTuple_GET_ITEM(line1, 0);
	if (strcmp(PyUnicode_AsUTF8(cmd), "l") != 0) {
		return 0; // not a line
	}
	p3 = PyTuple_GET_ITEM(line1, 1);
	p4 = PyTuple_GET_ITEM(line1, 2);

	line2 = PyList_GET_ITEM(items, len - 1);
	cmd = PyTuple_GET_ITEM(line2, 0);
	if (strcmp(PyUnicode_AsUTF8(cmd), "l") != 0) {
		return 0; // not a line
	}
	p5 = PyTuple_GET_ITEM(line2, 1);
	p6 = PyTuple_GET_ITEM(line2, 2);

	if (PyObject_RichCompareBool(p2, p3, Py_NE)) {
		return 0;  // not connected
	}
	if (PyObject_RichCompareBool(p4, p5, Py_NE)) {
		return 0; // not connected
	}

	// we do have three connected lines, ie at least a quad!
	// now check whether it even is a rectangle.
	PyObject *p1y = PyTuple_GET_ITEM(p1, 1);
	PyObject *p2y = PyTuple_GET_ITEM(p2, 1);
	if (PyObject_RichCompareBool(p1y, p2y, Py_NE)) {
		goto make_quad;
	}
	PyObject *p3x = PyTuple_GET_ITEM(p3, 0);
	PyObject *p4x = PyTuple_GET_ITEM(p4, 0);
	if (PyObject_RichCompareBool(p3x, p4x, Py_NE)) {
		goto make_quad;
	}
	PyObject *p5y = PyTuple_GET_ITEM(p5, 1);
	PyObject *p6y = PyTuple_GET_ITEM(p6, 1);
	if (PyObject_RichCompareBool(p5y, p6y, Py_NE)) {
		goto make_quad;
	}

	// All check have passed, so replace last 3 "l" items by one "re" item.
	// rect is represented by Rect(p6, p2)
	fz_point tl = JM_point_from_py(p6);
	fz_point br = JM_point_from_py(p2);
	if (tl.x > br.x) {
		ftemp = tl.x;
		tl.x = br.x;
		br.x = ftemp;
	}
	if (tl.y > br.y) {
		ftemp = tl.y;
		tl.y = br.y;
		br.y = ftemp;
	}
	fz_rect r = fz_make_rect(tl.x, tl.y, br.x, br.y);
	rect = PyTuple_New(2);
	PyTuple_SET_ITEM(rect, 0, PyUnicode_FromString("re"));
	PyTuple_SET_ITEM(rect, 1, JM_py_from_rect(r));
	PyList_SetItem(items, len - 3, rect); // replace item -3 by rect
	PyList_SetSlice(items, len - 2, len, NULL); // delete next 2 items
	return 1;

	make_quad:;
	rect = PyTuple_New(2);
	PyTuple_SET_ITEM(rect, 0, PyUnicode_FromString("qu"));
	fz_point ul = JM_point_from_py(p6);
	fz_point ur = JM_point_from_py(p5);
	fz_point ll = JM_point_from_py(p1);
	fz_point lr = JM_point_from_py(p2);
	fz_quad q = fz_make_quad(ul.x, ul.y, ur.x, ur.y, ll.x, ll.y, lr.x, lr.y);
	PyTuple_SET_ITEM(rect, 1, JM_py_from_quad(q));
	// check if item[-4] is a line connected with line0 and line2
	if (len >= 4) {
		line4 = PyList_GET_ITEM(items, len - 4);
		cmd = PyTuple_GET_ITEM(line4, 0);
		if (strcmp(PyUnicode_AsUTF8(cmd), "l") == 0) {
			p7 = PyTuple_GET_ITEM(line4, 1);
			p8 = PyTuple_GET_ITEM(line4, 2);
			if (PyObject_RichCompareBool(p7, p6, Py_EQ) &&
				PyObject_RichCompareBool(p8, p1, Py_EQ)) {
				PyList_SetItem(items, len - 4, rect);
				PyList_SetSlice(items, len - 3, len, NULL);
			}
		}
	} else {
		PyList_SetItem(items, len - 3, rect); // replace item -3 by rect
		PyList_SetSlice(items, len - 2, len, NULL); // delete remaining 2 items
	}
	return 1;
}

static PyObject *
jm_tracedraw_color(fz_context *ctx, fz_colorspace *colorspace, const float *color)
{
	float rgb[3];
	if (colorspace) {
		fz_convert_color(ctx, colorspace, color, fz_device_rgb(ctx),
		                 rgb, NULL, fz_default_color_params);
		return Py_BuildValue("fff", rgb[0], rgb[1], rgb[2]);
	}
	return PyTuple_New(0);
}

static void
trace_moveto(fz_context *ctx, void *dev_, float x, float y)
{
	trace_pathpoint = fz_make_point(x, y);
	trace_pathpoint = fz_transform_point(trace_pathpoint, trace_device_ctm);
	if (fz_is_infinite_rect(trace_pathrect)) {
		trace_pathrect = fz_make_rect(trace_pathpoint.x, trace_pathpoint.y,trace_pathpoint.x, trace_pathpoint.y);
	}
}

static void
trace_lineto(fz_context *ctx, void *dev_, float x, float y)
{
	fz_point p1 = fz_make_point(x, y);
	p1 = fz_transform_point(p1, trace_device_ctm);
	trace_pathrect = fz_include_point_in_rect(trace_pathrect, p1);
    PyObject *list = PyTuple_New(3);
	PyTuple_SET_ITEM(list, 0, PyUnicode_FromString("l"));
	PyTuple_SET_ITEM(list, 1, JM_py_from_point(trace_pathpoint));
	PyTuple_SET_ITEM(list, 2, JM_py_from_point(p1));
	trace_pathpoint = p1;
	PyObject *items = PyDict_GetItem(trace_pathdict, dictkey_items);
	LIST_APPEND_DROP(items, list);
}

static void
trace_curveto(fz_context *ctx, void *dev_, float x1, float y1, float x2, float y2, float x3, float y3)
{
	fz_point p1 = fz_make_point(x1, y1);
	fz_point p2 = fz_make_point(x2, y2);
	fz_point p3 = fz_make_point(x3, y3);
	p1 = fz_transform_point(p1, trace_device_ctm);
	p2 = fz_transform_point(p2, trace_device_ctm);
	p3 = fz_transform_point(p3, trace_device_ctm);
	trace_pathrect = fz_include_point_in_rect(trace_pathrect, p1);
	trace_pathrect = fz_include_point_in_rect(trace_pathrect, p2);
	trace_pathrect = fz_include_point_in_rect(trace_pathrect, p3);

	PyObject *list = PyTuple_New(5);
	PyTuple_SET_ITEM(list, 0, PyUnicode_FromString("c"));
	PyTuple_SET_ITEM(list, 1, JM_py_from_point(trace_pathpoint));
	PyTuple_SET_ITEM(list, 2, JM_py_from_point(p1));
	PyTuple_SET_ITEM(list, 3, JM_py_from_point(p2));
	PyTuple_SET_ITEM(list, 4, JM_py_from_point(p3));
	trace_pathpoint = p3;
	PyObject *items = PyDict_GetItem(trace_pathdict, dictkey_items);
	LIST_APPEND_DROP(items, list);
}

static void
trace_close(fz_context *ctx, void *dev_)
{
	if (!jm_checkrect()) {
		DICT_SETITEMSTR_DROP(trace_pathdict, "closePath", JM_BOOL(1));
	}
}

static const fz_path_walker trace_path_walker =
	{
		trace_moveto,
		trace_lineto,
		trace_curveto,
		trace_close
	};

static void
jm_tracedraw_path(fz_context *ctx, jm_tracedraw_device *dev, const fz_path *path)
{
	fz_walk_path(ctx, path, &trace_path_walker, dev);
}

//---------------------------------------------------------------------------
// Append current path to list or merge into last path of list.
// (1) Append if first path, different item list or not 'stroke' version of
//     previous
// (2) If new path has the same items, merge its content into previous path
//     and indicate this via path["type"] = "fs".
//---------------------------------------------------------------------------
static void
jm_append_merge(PyObject *out)
{
	Py_ssize_t len = PyList_Size(out);
	if (len == 0) {  // 1st path
		goto append;
	}
	const char *thistype = PyUnicode_AsUTF8(PyDict_GetItem(trace_pathdict, dictkey_type));
	if (strcmp(thistype, "f") != 0 && strcmp(thistype, "s") != 0) {
		goto append;
	}
	PyObject *prev = PyList_GET_ITEM(out, len - 1);  // get prev path
	const char *prevtype = PyUnicode_AsUTF8(PyDict_GetItem(prev, dictkey_type));
	if (strcmp(prevtype, "f") != 0 && strcmp(prevtype, "s") != 0
		|| strcmp(prevtype, thistype) == 0) {
		goto append;
	}
	PyObject *previtems = PyDict_GetItem(prev, dictkey_items);
	PyObject *thisitems = PyDict_GetItem(trace_pathdict, dictkey_items);
	if (PyObject_RichCompareBool(previtems, thisitems, Py_NE)) {
		goto append;
	}
	int rc = PyDict_Merge(trace_pathdict, prev, 0);  // merge, do not override
	if (rc == 0) {
		DICT_SETITEM_DROP(trace_pathdict, dictkey_type, PyUnicode_FromString("fs"));
		PyList_SetItem(out, len - 1, trace_pathdict);
		return;
	} else {
		PySys_WriteStderr("could not merge stroke and fill path");
		goto append;
	}
	append:;
	PyList_Append(out, trace_pathdict);
	Py_CLEAR(trace_pathdict);
}


static void
jm_tracedraw_fill_path(fz_context *ctx, fz_device *dev_, const fz_path *path,
				int even_odd, fz_matrix ctm, fz_colorspace *colorspace,
				const float *color, float alpha, fz_color_params color_params)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *) dev_;
	PyObject *out = dev->out;
	trace_pathdict = PyDict_New();
	trace_pathrect = fz_infinite_rect;
	trace_pathfactor = 1;
	if (fz_abs(ctm.a) == fz_abs(ctm.d)) {
		trace_pathfactor = fz_abs(ctm.a);
	}
	trace_device_ctm = ctm; //fz_concat(ctm, trace_device_ptm);
	DICT_SETITEM_DROP(trace_pathdict, dictkey_items, PyList_New(0));
	DICT_SETITEM_DROP(trace_pathdict, dictkey_type, PyUnicode_FromString("f"));
	DICT_SETITEMSTR_DROP(trace_pathdict, "even_odd", JM_BOOL(even_odd));
	DICT_SETITEMSTR_DROP(trace_pathdict, "fill_opacity", Py_BuildValue("f", alpha));
	DICT_SETITEMSTR_DROP(trace_pathdict, "closePath", JM_BOOL(0));
	DICT_SETITEMSTR_DROP(trace_pathdict, "fill", jm_tracedraw_color(ctx, colorspace, color));
	jm_tracedraw_path(ctx, dev, path);
	DICT_SETITEM_DROP(trace_pathdict, dictkey_rect, JM_py_from_rect(trace_pathrect));
	Py_ssize_t item_count = PyList_Size(PyDict_GetItem(trace_pathdict, dictkey_items));
	if (item_count == 0) {
		Py_CLEAR(trace_pathdict);
		return;
	}
	DICT_SETITEMSTR_DROP(trace_pathdict, "seqno", PyLong_FromSize_t(dev->seqno));
	dev->seqno += 1;
	jm_append_merge(out);
}

static void
jm_tracedraw_stroke_path(fz_context *ctx, fz_device *dev_, const fz_path *path,
				const fz_stroke_state *stroke, fz_matrix ctm,
				fz_colorspace *colorspace, const float *color, float alpha,
				fz_color_params color_params)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *)dev_;
	PyObject *out = dev->out;
	int i;
	trace_pathdict = PyDict_New();
	trace_pathrect = fz_infinite_rect;
	trace_pathfactor = 1;
	if (fz_abs(ctm.a) == fz_abs(ctm.d)) {
		trace_pathfactor = fz_abs(ctm.a);
	}
	trace_device_ctm = ctm; //fz_concat(ctm, trace_device_ptm);
	DICT_SETITEM_DROP(trace_pathdict, dictkey_items, PyList_New(0));
	DICT_SETITEM_DROP(trace_pathdict, dictkey_type, PyUnicode_FromString("s"));
	DICT_SETITEMSTR_DROP(trace_pathdict, "stroke_opacity", Py_BuildValue("f", alpha));
	DICT_SETITEMSTR_DROP(trace_pathdict, "color", jm_tracedraw_color(ctx, colorspace, color));
	DICT_SETITEM_DROP(trace_pathdict, dictkey_width, Py_BuildValue("f", trace_pathfactor * stroke->linewidth));
	DICT_SETITEMSTR_DROP(trace_pathdict, "lineCap", Py_BuildValue("iii", stroke->start_cap, stroke->dash_cap, stroke->end_cap));
	DICT_SETITEMSTR_DROP(trace_pathdict, "lineJoin", Py_BuildValue("f", trace_pathfactor * stroke->linejoin));
	DICT_SETITEMSTR_DROP(trace_pathdict, "closePath", JM_BOOL(0));

	if (stroke->dash_len)
	{
		fz_buffer *buff = fz_new_buffer(ctx, 50);
		fz_append_string(ctx, buff, "[ ");
		for (i = 0; i < stroke->dash_len; i++) {
			fz_append_printf(ctx, buff, "%g ", trace_pathfactor * stroke->dash_list[i]);
		}
		fz_append_printf(ctx, buff, "] %g", trace_pathfactor * stroke->dash_phase);
		DICT_SETITEMSTR_DROP(trace_pathdict, "dashes", JM_EscapeStrFromBuffer(ctx, buff));
		fz_drop_buffer(ctx, buff);
	} else {
		DICT_SETITEMSTR_DROP(trace_pathdict, "dashes", PyUnicode_FromString("[] 0"));
	}
	jm_tracedraw_path(ctx, dev, path);
	DICT_SETITEM_DROP(trace_pathdict, dictkey_rect, JM_py_from_rect(trace_pathrect));
	Py_ssize_t item_count = PyList_Size(PyDict_GetItem(trace_pathdict, dictkey_items));
	if (item_count == 0) {
		Py_CLEAR(trace_pathdict);
		return;
	}
	DICT_SETITEMSTR_DROP(trace_pathdict, "seqno", PyLong_FromSize_t(dev->seqno));
	dev->seqno += 1;
	jm_append_merge(out);
}


static void
jm_trace_device_Linewidth(fz_context *ctx, fz_device *dev_, const fz_path *path, const fz_stroke_state *stroke, fz_matrix ctm, fz_colorspace *colorspace, const float *color, float alpha, fz_color_params color_params)
{
	trace_device_Linewidth = stroke->linewidth;
	jm_increase_seqno(ctx, dev_);
}


static void
jm_trace_text_span(fz_context *ctx, PyObject *out, fz_text_span *span, int type, fz_matrix ctm, fz_colorspace *colorspace, const float *color, float alpha, size_t seqno)
{
	fz_font *out_font = NULL;
	int i, n;
	const char *fontname = JM_font_name(ctx, span->font);
	float rgb[3];
	PyObject *chars = PyTuple_New(span->len);
	fz_matrix join = fz_concat(span->trm, ctm);
	fz_point dir = fz_transform_vector(fz_make_point(1, 0), join);
	double fsize = sqrt((double) dir.x * dir.x + (double) dir.y * dir.y);
	double linewidth, adv, asc, dsc;
	double space_adv = 0;
	float x0, y0, x1, y1;
	asc = (double) JM_font_ascender(ctx, span->font);
	dsc = (double) JM_font_descender(ctx, span->font);
	if (asc - dsc >= 1 && small_glyph_heights == 0) {
		;
	} else {
		if (asc < 1e-3) {
			dsc = -0.1;
		}
		asc = 1 + dsc;
	}
	double ascsize = asc * fsize / (asc - dsc);
	double dscsize = dsc * fsize / (asc - dsc);
	int fflags = 0;
	int mono = fz_font_is_monospaced(ctx, span->font);
	fflags += mono * TEXT_FONT_MONOSPACED;
	fflags += fz_font_is_italic(ctx, span->font) * TEXT_FONT_ITALIC;
	fflags += fz_font_is_serif(ctx, span->font) * TEXT_FONT_SERIFED;
	fflags += fz_font_is_bold(ctx, span->font) * TEXT_FONT_BOLD;
	fz_matrix mat = trace_device_ptm;
	fz_matrix ctm_rot = fz_concat(ctm, trace_device_rot);
	mat = fz_concat(mat, ctm_rot);

	if (trace_device_Linewidth > 0) {
		linewidth = (double) trace_device_Linewidth;
	} else {
		linewidth = fsize * 0.05;
	}
	fz_point char_orig;
	double last_adv = 0;

	// walk through characters of span
	fz_rect span_bbox;
	for (i = 0; i < span->len; i++) {
		adv = 0;
		if (span->items[i].gid >= 0) {
			adv = (double) fz_advance_glyph(ctx, span->font, span->items[i].gid, span->wmode);
		}
		adv *= fsize;
		last_adv = adv;
		if (span->items[i].ucs == 32) {
			space_adv = adv;
		}
		char_orig = fz_make_point(span->items[i].x, span->items[i].y);
		char_orig.y = trace_device_ptm.f - char_orig.y;
		char_orig = fz_transform_point(char_orig, mat);
		x0 = char_orig.x;
		x1 = x0 + adv;
		y0 = char_orig.y - ascsize;
		y1 = char_orig.y - dscsize;
		fz_rect char_bbox = fz_make_rect(x0, y0, x1, y1);
		PyTuple_SET_ITEM(chars, (Py_ssize_t) i, Py_BuildValue("ii(ff)(ffff)",
			span->items[i].ucs, span->items[i].gid,
			char_orig.x, char_orig.y, x0, y0, x1, y1));
		if (i > 0) {
			span_bbox = fz_union_rect(span_bbox, char_bbox);
		} else {
			span_bbox = char_bbox;
		}
	}
	if (!space_adv) {
		if (!mono) {
			space_adv = fz_advance_glyph(ctx, span->font,
			fz_encode_character_with_fallback(ctx, span->font, 32, 0, 0, &out_font),
			span->wmode);
			space_adv *= fsize;
			if (!space_adv) {
				space_adv = last_adv;
			}
		} else {
			space_adv = last_adv; // in mono fonts this suffices
		}
	}
	// make the span dictionary
	PyObject *span_dict = PyDict_New();
	DICT_SETITEMSTR_DROP(span_dict, "dir", JM_py_from_point(fz_normalize_vector(dir)));
	DICT_SETITEM_DROP(span_dict, dictkey_font, Py_BuildValue("s",fontname));
	DICT_SETITEM_DROP(span_dict, dictkey_wmode, PyLong_FromLong((long) span->wmode));
	DICT_SETITEM_DROP(span_dict, dictkey_flags, PyLong_FromLong((long) fflags));
	DICT_SETITEMSTR_DROP(span_dict, "bidi", PyLong_FromLong((long) span->bidi_level));
	DICT_SETITEM_DROP(span_dict, dictkey_ascender, PyFloat_FromDouble(asc));
	DICT_SETITEM_DROP(span_dict, dictkey_descender, PyFloat_FromDouble(dsc));
	if (colorspace) {
		fz_convert_color(ctx, colorspace, color, fz_device_rgb(ctx),
						 rgb, NULL, fz_default_color_params);
		DICT_SETITEM_DROP(span_dict, dictkey_colorspace, PyLong_FromLong(3));
		DICT_SETITEM_DROP(span_dict, dictkey_color, Py_BuildValue("fff", rgb[0], rgb[1], rgb[2]));
	} else {
		DICT_SETITEM_DROP(span_dict, dictkey_colorspace, PyLong_FromLong(1));
		DICT_SETITEM_DROP(span_dict, dictkey_color, PyFloat_FromDouble(1));
	}
	DICT_SETITEM_DROP(span_dict, dictkey_size, PyFloat_FromDouble(fsize));
	DICT_SETITEMSTR_DROP(span_dict, "opacity", PyFloat_FromDouble((double) alpha));
	DICT_SETITEMSTR_DROP(span_dict, "linewidth", PyFloat_FromDouble((double) linewidth));
	DICT_SETITEMSTR_DROP(span_dict, "spacewidth", PyFloat_FromDouble(space_adv));
	DICT_SETITEM_DROP(span_dict, dictkey_type, PyLong_FromLong((long) type));
	DICT_SETITEM_DROP(span_dict, dictkey_chars, chars);
	DICT_SETITEM_DROP(span_dict, dictkey_bbox, JM_py_from_rect(span_bbox));
	DICT_SETITEMSTR_DROP(span_dict, "seqno", PyLong_FromSize_t(seqno));
	LIST_APPEND_DROP(out, span_dict);
}

static void
jm_trace_text(fz_context *ctx, PyObject *out, const fz_text *text, int type, fz_matrix ctm, fz_colorspace *colorspace, const float *color, float alpha, size_t seqno)
{
	fz_text_span *span;
	for (span = text->head; span; span = span->next)
		jm_trace_text_span(ctx, out, span, type, ctm, colorspace, color, alpha, seqno);
}

/*---------------------------------------------------------
There are 3 text trace types:
0 - fill text (PDF Tr 0)
1 - stroke text (PDF Tr 1)
3 - ignore text (PDF Tr 3)
---------------------------------------------------------*/
static void
jm_tracedraw_fill_text(fz_context *ctx, fz_device *dev_, const fz_text *text, fz_matrix ctm, fz_colorspace *colorspace, const float *color, float alpha, fz_color_params color_params)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *)dev_;
	PyObject *out = dev->out;
	jm_trace_text(ctx, out, text, 0, ctm, colorspace, color, alpha, dev->seqno);
	dev->seqno += 1;
}

static void
jm_tracedraw_stroke_text(fz_context *ctx, fz_device *dev_, const fz_text *text, const fz_stroke_state *stroke, fz_matrix ctm, fz_colorspace *colorspace, const float *color, float alpha, fz_color_params color_params)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *)dev_;
	PyObject *out = dev->out;
	jm_trace_text(ctx, out, text, 1, ctm, colorspace, color, alpha, dev->seqno);
	dev->seqno += 1;
}


static void
jm_tracedraw_ignore_text(fz_context *ctx, fz_device *dev_, const fz_text *text, fz_matrix ctm)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *)dev_;
	PyObject *out = dev->out;
	jm_trace_text(ctx, out, text, 3, ctm, NULL, NULL, 1, dev->seqno);
	dev->seqno += 1;
}


fz_device *JM_new_tracedraw_device(fz_context *ctx, PyObject *out)
{
	jm_tracedraw_device *dev = fz_new_derived_device(ctx, jm_tracedraw_device);

	dev->super.fill_path = jm_tracedraw_fill_path;
	dev->super.stroke_path = jm_tracedraw_stroke_path;
	dev->super.clip_path = NULL;
	dev->super.clip_stroke_path = NULL;

	dev->super.fill_text = jm_increase_seqno;
	dev->super.stroke_text = jm_increase_seqno;
	dev->super.clip_text = NULL;
	dev->super.clip_stroke_text = NULL;
	dev->super.ignore_text = jm_increase_seqno;

	dev->super.fill_shade = jm_increase_seqno;
	dev->super.fill_image = jm_increase_seqno;
	dev->super.fill_image_mask = jm_increase_seqno;
	dev->super.clip_image_mask = NULL;

	dev->super.pop_clip = NULL;

	dev->super.begin_mask = NULL;
	dev->super.end_mask = NULL;
	dev->super.begin_group = NULL;
	dev->super.end_group = NULL;

	dev->super.begin_tile = NULL;
	dev->super.end_tile = NULL;

	dev->super.begin_layer = NULL;
	dev->super.end_layer = NULL;

	dev->super.render_flags = NULL;
	dev->super.set_default_colorspaces = NULL;

	dev->out = out;
	dev->seqno = 0;
	return (fz_device *)dev;
}

fz_device *JM_new_tracetext_device(fz_context *ctx, PyObject *out)
{
	jm_tracedraw_device *dev = fz_new_derived_device(ctx, jm_tracedraw_device);

	dev->super.fill_path = jm_increase_seqno;
	dev->super.stroke_path = jm_trace_device_Linewidth;
	dev->super.clip_path = NULL;
	dev->super.clip_stroke_path = NULL;

	dev->super.fill_text = jm_tracedraw_fill_text;
	dev->super.stroke_text = jm_tracedraw_stroke_text;
	dev->super.clip_text = NULL;
	dev->super.clip_stroke_text = NULL;
	dev->super.ignore_text = jm_tracedraw_ignore_text;

	dev->super.fill_shade = jm_increase_seqno;
	dev->super.fill_image = jm_increase_seqno;
	dev->super.fill_image_mask = jm_increase_seqno;
	dev->super.clip_image_mask = NULL;

	dev->super.pop_clip = NULL;

	dev->super.begin_mask = NULL;
	dev->super.end_mask = NULL;
	dev->super.begin_group = NULL;
	dev->super.end_group = NULL;

	dev->super.begin_tile = NULL;
	dev->super.end_tile = NULL;

	dev->super.begin_layer = NULL;
	dev->super.end_layer = NULL;

	dev->super.render_flags = NULL;
	dev->super.set_default_colorspaces = NULL;

	dev->out = out;
	dev->seqno = 0;
	return (fz_device *)dev;
}
typedef struct jm_bbox_device_s
{
	fz_device super;
	PyObject *result;
} jm_bbox_device;

static void
jm_bbox_add_rect(fz_context *ctx, fz_device *dev, fz_rect rect, char *code)
{
	jm_bbox_device *bdev = (jm_bbox_device *)dev;
	LIST_APPEND_DROP(bdev->result, Py_BuildValue("sN", code, JM_py_from_rect(rect)));
}

static void
jm_bbox_fill_path(fz_context *ctx, fz_device *dev, const fz_path *path, int even_odd, fz_matrix ctm,
				  fz_colorspace *colorspace, const float *color, float alpha, fz_color_params color_params)
{
	jm_bbox_add_rect(ctx, dev, fz_bound_path(ctx, path, NULL, ctm), "fill-path");
}

static void
jm_bbox_stroke_path(fz_context *ctx, fz_device *dev, const fz_path *path, const fz_stroke_state *stroke,
					fz_matrix ctm, fz_colorspace *colorspace, const float *color, float alpha, fz_color_params color_params)
{
	jm_bbox_add_rect(ctx, dev, fz_bound_path(ctx, path, stroke, ctm), "stroke-path");
}

static void
jm_bbox_fill_text(fz_context *ctx, fz_device *dev, const fz_text *text, fz_matrix ctm, ...)
{
	jm_bbox_add_rect(ctx, dev, fz_bound_text(ctx, text, NULL, ctm), "fill-text");
}

static void
jm_bbox_ignore_text(fz_context *ctx, fz_device *dev, const fz_text *text, fz_matrix ctm)
{
	jm_bbox_add_rect(ctx, dev, fz_bound_text(ctx, text, NULL, ctm), "ignore-text");
}

static void
jm_bbox_stroke_text(fz_context *ctx, fz_device *dev, const fz_text *text, const fz_stroke_state *stroke, fz_matrix ctm, ...)
{
	jm_bbox_add_rect(ctx, dev, fz_bound_text(ctx, text, stroke, ctm), "stroke-text");
}

static void
jm_bbox_fill_shade(fz_context *ctx, fz_device *dev, fz_shade *shade, fz_matrix ctm, float alpha, fz_color_params color_params)
{
	jm_bbox_add_rect(ctx, dev, fz_bound_shade(ctx, shade, ctm), "fill-shade");
}

static void
jm_bbox_fill_image(fz_context *ctx, fz_device *dev, fz_image *image, fz_matrix ctm, float alpha, fz_color_params color_params)
{
	jm_bbox_add_rect(ctx, dev, fz_transform_rect(fz_unit_rect, ctm), "fill-image");
}

static void
jm_bbox_fill_image_mask(fz_context *ctx, fz_device *dev, fz_image *image, fz_matrix ctm,
						fz_colorspace *colorspace, const float *color, float alpha, fz_color_params color_params)
{
	jm_bbox_add_rect(ctx, dev, fz_transform_rect(fz_unit_rect, ctm), "fill-imgmask");
}

fz_device *
JM_new_bbox_device(fz_context *ctx, PyObject *result)
{
	jm_bbox_device *dev = fz_new_derived_device(ctx, jm_bbox_device);

	dev->super.fill_path = jm_bbox_fill_path;
	dev->super.stroke_path = jm_bbox_stroke_path;
	dev->super.clip_path = NULL;
	dev->super.clip_stroke_path = NULL;

	dev->super.fill_text = jm_bbox_fill_text;
	dev->super.stroke_text = jm_bbox_stroke_text;
	dev->super.clip_text = NULL;
	dev->super.clip_stroke_text = NULL;
	dev->super.ignore_text = jm_bbox_ignore_text;

	dev->super.fill_shade = jm_bbox_fill_shade;
	dev->super.fill_image = jm_bbox_fill_image;
	dev->super.fill_image_mask = jm_bbox_fill_image_mask;
	dev->super.clip_image_mask = NULL;

	dev->super.pop_clip = NULL;

	dev->super.begin_mask = NULL;
	dev->super.end_mask = NULL;
	dev->super.begin_group = NULL;
	dev->super.end_group = NULL;

	dev->super.begin_tile = NULL;
	dev->super.end_tile = NULL;

	dev->super.begin_layer = NULL;
	dev->super.end_layer = NULL;

	dev->super.render_flags = NULL;
	dev->super.set_default_colorspaces = NULL;

	dev->result = result;

	return (fz_device *)dev;
}



%}
