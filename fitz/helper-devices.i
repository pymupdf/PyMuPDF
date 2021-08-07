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
} jm_tracedraw_device;

static void
jm_tracedraw_matrix(fz_context *ctx, PyObject *out, fz_matrix ctm)
{
	PyObject *list = PyList_New(0);
    LIST_APPEND_DROP(list, PyUnicode_FromString("matrix"));
    LIST_APPEND_DROP(list, JM_py_from_matrix(ctm));
    LIST_APPEND_DROP(out, list);
}

static void
jm_tracedraw_color(fz_context *ctx, PyObject *out, fz_colorspace *colorspace, const float *color, float alpha)
{
	int i, n;
	if (colorspace)
	{
		n = fz_colorspace_n(ctx, colorspace);
		LIST_APPEND_DROP(out, Py_BuildValue("ss", "colorspace", fz_colorspace_name(ctx, colorspace)));
		PyObject *xlist=PyList_New(0);
		LIST_APPEND_DROP(xlist, Py_BuildValue("s", "color"));
		for (i = 0; i < n; i++)
			LIST_APPEND_DROP(xlist, Py_BuildValue("f", color[i]));
		LIST_APPEND_DROP(out, xlist);
	}
	if (alpha < 1)
		LIST_APPEND_DROP(out, Py_BuildValue("sf", "alpha", alpha));
}

static void
trace_moveto(fz_context *ctx, void *dev_, float x, float y)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *)dev_;
	PyObject *out = dev->out;
    PyObject *list = PyList_New(0);
    LIST_APPEND_DROP(list, PyUnicode_FromString("m"));
    LIST_APPEND_DROP(list, JM_py_from_point(fz_make_point(x, y)));
    LIST_APPEND_DROP(out, list);
}

static void
trace_lineto(fz_context *ctx, void *dev_, float x, float y)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *)dev_;
	PyObject *out = dev->out;
    PyObject *list = PyList_New(0);
    LIST_APPEND_DROP(list, PyUnicode_FromString("l"));
    LIST_APPEND_DROP(list, JM_py_from_point(fz_make_point(x, y)));
    LIST_APPEND_DROP(out, list);
}

static void
trace_curveto(fz_context *ctx, void *dev_, float x1, float y1, float x2, float y2, float x3, float y3)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *)dev_;
	PyObject *out = dev->out;
    PyObject *list = PyList_New(0);
    LIST_APPEND_DROP(list, PyUnicode_FromString("c"));
    LIST_APPEND_DROP(list, JM_py_from_point(fz_make_point(x1, y1)));
    LIST_APPEND_DROP(list, JM_py_from_point(fz_make_point(x2, y2)));
    LIST_APPEND_DROP(list, JM_py_from_point(fz_make_point(x3, y3)));
    LIST_APPEND_DROP(out, list);
}

static void
trace_close(fz_context *ctx, void *dev_)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *)dev_;
	PyObject *out = dev->out;
    LIST_APPEND_DROP(out, Py_BuildValue("s", "closePath"));
}

static const fz_path_walker trace_path_walker =
	{
		trace_moveto,
		trace_lineto,
		trace_curveto,
		trace_close};

static void
jm_tracedraw_path(fz_context *ctx, jm_tracedraw_device *dev, const fz_path *path)
{
	fz_walk_path(ctx, path, &trace_path_walker, dev);
}

static void
jm_tracedraw_fill_path(fz_context *ctx, fz_device *dev_, const fz_path *path, int even_odd, fz_matrix ctm, fz_colorspace *colorspace, const float *color, float alpha, fz_color_params color_params)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *) dev_;
	PyObject *out = dev->out;
	PyObject *list = PyList_New(0);
	LIST_APPEND_DROP(list, PyUnicode_FromString("fill"));
	if (even_odd)
		LIST_APPEND_DROP(list, PyUnicode_FromString("even-odd"));
	else
		LIST_APPEND_DROP(list, PyUnicode_FromString("non-zero"));
	jm_tracedraw_matrix(ctx, list, ctm);
	jm_tracedraw_color(ctx, list, colorspace, color, alpha);
	LIST_APPEND_DROP(out, list);
	jm_tracedraw_path(ctx, dev, path);
	LIST_APPEND_DROP(out, PyUnicode_FromString("efill"));
}

static void
jm_tracedraw_stroke_path(fz_context *ctx, fz_device *dev_, const fz_path *path, const fz_stroke_state *stroke, fz_matrix ctm, fz_colorspace *colorspace, const float *color, float alpha, fz_color_params color_params)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *)dev_;
	PyObject *out = dev->out;
	int i;
    PyObject *list = PyList_New(0);
    LIST_APPEND_DROP(list, PyUnicode_FromString("stroke"));
	jm_tracedraw_matrix(ctx, list, ctm);
	LIST_APPEND_DROP(list, Py_BuildValue("sf", "w", stroke->linewidth));
	LIST_APPEND_DROP(list, Py_BuildValue("sf", "miter", stroke->miterlimit));
	LIST_APPEND_DROP(list, Py_BuildValue("siii", "lineCap",
					 stroke->start_cap, stroke->dash_cap, stroke->end_cap));
	LIST_APPEND_DROP(list, Py_BuildValue("si", "lineJoin", stroke->linejoin));

	if (stroke->dash_len)
	{
		LIST_APPEND_DROP(list, Py_BuildValue("sf", "dashPhase", stroke->dash_phase));
		PyObject *xlist=PyList_New(0);
		LIST_APPEND_DROP(xlist, Py_BuildValue("s", "dashes"));
		for (i = 0; i < stroke->dash_len; i++)
			LIST_APPEND_DROP(xlist, Py_BuildValue("f", stroke->dash_list[i]));
		LIST_APPEND_DROP(list, xlist);
	}
	jm_tracedraw_color(ctx, list, colorspace, color, alpha);
	LIST_APPEND_DROP(out, list);
	jm_tracedraw_path(ctx, dev, path);
	LIST_APPEND_DROP(out, Py_BuildValue("s", "estroke"));
}

static void
jm_tracedraw_clip_path(fz_context *ctx, fz_device *dev_, const fz_path *path, int even_odd, fz_matrix ctm, fz_rect scissor)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *)dev_;
	PyObject *out = dev->out;
	PyObject *list = PyList_New(0);
	LIST_APPEND_DROP(list, Py_BuildValue("s", "clip"));

	if (even_odd)
		LIST_APPEND_DROP(list, Py_BuildValue("s", "even-odd"));
	else
		LIST_APPEND_DROP(list, Py_BuildValue("s", "non-zero"));
	jm_tracedraw_matrix(ctx, list, ctm);
	LIST_APPEND_DROP(out, list);
	jm_tracedraw_path(ctx, dev, path);
	LIST_APPEND_DROP(out, Py_BuildValue("s", "eclip"));
}

static void
jm_tracedraw_clip_stroke_path(fz_context *ctx, fz_device *dev_, const fz_path *path, const fz_stroke_state *stroke, fz_matrix ctm, fz_rect scissor)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *)dev_;
	PyObject *out = dev->out;
	PyObject *list = PyList_New(0);
	LIST_APPEND_DROP(list, Py_BuildValue("s", "clip-stroke"));
	jm_tracedraw_matrix(ctx, list, ctm);
	LIST_APPEND_DROP(out, list);
	jm_tracedraw_path(ctx, dev, path);
	LIST_APPEND_DROP(out, Py_BuildValue("s", "eclip-stroke"));
}


static float trace_text_linewidth = 0;  // text border width if present
static fz_matrix trace_text_ptm;  // page transformation matrix
static fz_matrix trace_text_rot;  // page derotation matrix
static void
jm_trace_text_linewidth(fz_context *ctx, fz_device *dev_, const fz_path *path, const fz_stroke_state *stroke, fz_matrix ctm, fz_colorspace *colorspace, const float *color, float alpha, fz_color_params color_params)
{
	trace_text_linewidth = stroke->linewidth;
}


static void
jm_trace_text_span(fz_context *ctx, PyObject *out, fz_text_span *span, int type, fz_matrix ctm, fz_rect scissor, fz_colorspace *colorspace, const float *color, float alpha)
{
	fz_font *out_font = NULL;
	int i, n;
	const char *fontname = JM_font_name(ctx, span->font);
	PyObject *chars = PyTuple_New(span->len);
	fz_matrix join = fz_concat(span->trm, ctm);
	fz_point dir = fz_transform_vector(fz_make_point(1, 0), join);
	double fsize = sqrt((double) dir.x * dir.x + (double) dir.y * dir.y);
	double linewidth, adv, asc, dsc;
	double space_adv = 0;
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
	
	int fflags = 0;
	int mono = fz_font_is_monospaced(ctx, span->font);
	fflags += mono * TEXT_FONT_MONOSPACED;
	fflags += fz_font_is_italic(ctx, span->font) * TEXT_FONT_ITALIC;
	fflags += fz_font_is_serif(ctx, span->font) * TEXT_FONT_SERIFED;
	fflags += fz_font_is_bold(ctx, span->font) * TEXT_FONT_BOLD;
	fz_matrix mat = trace_text_ptm;
	fz_matrix ctm_rot = fz_concat(ctm, trace_text_rot);
	mat = fz_concat(mat, ctm_rot);

	if (trace_text_linewidth > 0) {
		linewidth = (double) trace_text_linewidth;
	} else {
		linewidth = fsize * 0.05;
	}
	fz_point char_orig;
	double last_adv = 0;
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
		char_orig.y = trace_text_ptm.f - char_orig.y;
		char_orig = fz_transform_point(char_orig, mat);
		PyTuple_SET_ITEM(chars, (Py_ssize_t) i, Py_BuildValue("ii(ff)f",
			span->items[i].ucs, span->items[i].gid,
			char_orig.x, char_orig.y, adv));
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
			space_adv = last_adv;
		}
	}
	// make the span dictionary
	PyObject *span_dict = PyDict_New();
	DICT_SETITEMSTR_DROP(span_dict, "dir", JM_py_from_point(fz_normalize_vector(dir)));
	DICT_SETITEM_DROP(span_dict, dictkey_font, Py_BuildValue("s",fontname));
	DICT_SETITEM_DROP(span_dict, dictkey_wmode, PyLong_FromLong((long) span->wmode));
	DICT_SETITEM_DROP(span_dict, dictkey_flags, PyLong_FromLong((long) fflags));
	DICT_SETITEMSTR_DROP(span_dict, "bidi", PyLong_FromLong((long) span->bidi_level));
	DICT_SETITEMSTR_DROP(span_dict, "ascender", PyFloat_FromDouble(asc));
	DICT_SETITEMSTR_DROP(span_dict, "descender", PyFloat_FromDouble(dsc));
	if (colorspace && color) {
		n = fz_colorspace_n(ctx, colorspace);
		PyObject *col_tuple = PyTuple_New(n);
		for (i = 0; i < n; i++) {
			PyTuple_SET_ITEM(col_tuple, (Py_ssize_t) i, PyFloat_FromDouble((double) color[i]));
		}
		DICT_SETITEM_DROP(span_dict, dictkey_colorspace, PyLong_FromLong((long) n));
		DICT_SETITEM_DROP(span_dict, dictkey_color, col_tuple);
	} else {
		DICT_SETITEM_DROP(span_dict, dictkey_colorspace, PyLong_FromLong(1));
		DICT_SETITEM_DROP(span_dict, dictkey_color, PyFloat_FromDouble(1));
	}
	DICT_SETITEM_DROP(span_dict, dictkey_size, PyFloat_FromDouble(fsize));
	DICT_SETITEMSTR_DROP(span_dict, "opacity", PyFloat_FromDouble((double) alpha));
	DICT_SETITEMSTR_DROP(span_dict, "linewidth", PyFloat_FromDouble((double) linewidth));
	DICT_SETITEMSTR_DROP(span_dict, "spacewidth", PyFloat_FromDouble(space_adv));
	DICT_SETITEMSTR_DROP(span_dict, "type", PyLong_FromLong((long) type));
	DICT_SETITEMSTR_DROP(span_dict, "scissor", JM_py_from_rect(fz_transform_rect(scissor, mat)));
	DICT_SETITEM_DROP(span_dict, dictkey_chars, chars);
	LIST_APPEND_DROP(out, span_dict);
}

static void
jm_trace_text(fz_context *ctx, PyObject *out, const fz_text *text, int type, fz_matrix ctm, fz_rect rect, fz_colorspace *colorspace, const float *color, float alpha)
{
	fz_text_span *span;
	for (span = text->head; span; span = span->next)
		jm_trace_text_span(ctx, out, span, type, ctm, rect, colorspace, color, alpha);
}

/*---------------------------------------------------------
There are 5 text trace types:
0 - fill text (PDF Tr 0)
1 - stroke text (PDF Tr 1)
2 - clip text
3 - clip-stroke text
4 - ignore text (PDF Tr 3)
---------------------------------------------------------*/
static void
jm_tracedraw_fill_text(fz_context *ctx, fz_device *dev_, const fz_text *text, fz_matrix ctm, fz_colorspace *colorspace, const float *color, float alpha, fz_color_params color_params)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *)dev_;
	PyObject *out = dev->out;
	jm_trace_text(ctx, out, text, 0, ctm, fz_infinite_rect, colorspace, color, alpha);
}

static void
jm_tracedraw_stroke_text(fz_context *ctx, fz_device *dev_, const fz_text *text, const fz_stroke_state *stroke, fz_matrix ctm, fz_colorspace *colorspace, const float *color, float alpha, fz_color_params color_params)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *)dev_;
	PyObject *out = dev->out;
	jm_trace_text(ctx, out, text, 1, ctm, fz_infinite_rect, colorspace, color, alpha);
}

static void
jm_tracedraw_clip_text(fz_context *ctx, fz_device *dev_, const fz_text *text, fz_matrix ctm, fz_rect scissor)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *)dev_;
	PyObject *out = dev->out;
	jm_trace_text(ctx, out, text, 2, ctm, scissor, NULL, NULL, 1);
}

static void
jm_tracedraw_clip_stroke_text(fz_context *ctx, fz_device *dev_, const fz_text *text, const fz_stroke_state *stroke, fz_matrix ctm, fz_rect scissor)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *)dev_;
	PyObject *out = dev->out;
	jm_trace_text(ctx, out, text, 3, ctm, scissor, NULL, NULL, 1);
}

static void
jm_tracedraw_ignore_text(fz_context *ctx, fz_device *dev_, const fz_text *text, fz_matrix ctm)
{
	jm_tracedraw_device *dev = (jm_tracedraw_device *)dev_;
	PyObject *out = dev->out;
	jm_trace_text(ctx, out, text, 4, ctm, fz_infinite_rect, NULL, NULL, 1);
}


fz_device *JM_new_tracedraw_device(fz_context *ctx, PyObject *out)
{
	jm_tracedraw_device *dev = fz_new_derived_device(ctx, jm_tracedraw_device);

	dev->super.fill_path = jm_tracedraw_fill_path;
	dev->super.stroke_path = jm_tracedraw_stroke_path;
	dev->super.clip_path = NULL; //jm_tracedraw_clip_path;
	dev->super.clip_stroke_path = jm_tracedraw_clip_stroke_path;

	dev->super.fill_text = NULL;
	dev->super.stroke_text = NULL;
	dev->super.clip_text = NULL;
	dev->super.clip_stroke_text = NULL;
	dev->super.ignore_text = NULL;

	dev->super.fill_shade = NULL;
	dev->super.fill_image = NULL;
	dev->super.fill_image_mask = NULL;
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

	return (fz_device *)dev;
}

fz_device *JM_new_tracetext_device(fz_context *ctx, PyObject *out)
{
	jm_tracedraw_device *dev = fz_new_derived_device(ctx, jm_tracedraw_device);

	dev->super.fill_path = NULL;
	dev->super.stroke_path = jm_trace_text_linewidth;
	dev->super.clip_path = NULL;
	dev->super.clip_stroke_path = NULL;

	dev->super.fill_text = jm_tracedraw_fill_text;
	dev->super.stroke_text = jm_tracedraw_stroke_text;
	dev->super.clip_text = jm_tracedraw_clip_text;
	dev->super.clip_stroke_text = jm_tracedraw_clip_stroke_text;
	dev->super.ignore_text = jm_tracedraw_ignore_text;

	dev->super.fill_shade = NULL;
	dev->super.fill_image = NULL;
	dev->super.fill_image_mask = NULL;
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

	return (fz_device *)dev;
}



%}
