%{
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
jm_tracedraw_fill_path(fz_context *ctx, fz_device *dev_, const fz_path *path,
						int even_odd, fz_matrix ctm, fz_colorspace *colorspace,
						const float *color, float alpha, fz_color_params color_params)
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
jm_tracedraw_stroke_path(fz_context *ctx, fz_device *dev_, const fz_path *path,
						 const fz_stroke_state *stroke, fz_matrix ctm,
						 fz_colorspace *colorspace, const float *color, float alpha,
						 fz_color_params color_params)
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

%}
