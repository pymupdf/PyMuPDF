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
//-----------------------------------------------------------------------------
// pixmap helper functions
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
// Clear a pixmap rectangle - my version also supports non-alpha pixmaps
//-----------------------------------------------------------------------------
int
JM_clear_pixmap_rect_with_value(fz_context *ctx, fz_pixmap *dest, int value, fz_irect b)
{
    unsigned char *destp;
    int x, y, w, k, destspan;

    b = fz_intersect_irect(b, fz_pixmap_bbox(ctx, dest));
    w = b.x1 - b.x0;
    y = b.y1 - b.y0;
    if (w <= 0 || y <= 0)
        return 0;

    destspan = dest->stride;
    destp = dest->samples + (unsigned int)(destspan * (b.y0 - dest->y) + dest->n * (b.x0 - dest->x));

    /* CMYK needs special handling (and potentially any other subtractive colorspaces) */
    if (fz_colorspace_n(ctx, dest->colorspace) == 4) {
        value = 255 - value;
        do {
            unsigned char *s = destp;
            for (x = 0; x < w; x++) {
                *s++ = 0;
                *s++ = 0;
                *s++ = 0;
                *s++ = value;
                if (dest->alpha) *s++ = 255;
            }
            destp += destspan;
        } while (--y);
        return 1;
    }

    do {
        unsigned char *s = destp;
        for (x = 0; x < w; x++) {
            for (k = 0; k < dest->n - 1; k++)
                *s++ = value;
            if (dest->alpha) *s++ = 255;
            else *s++ = value;
        }
        destp += destspan;
    } while (--y);
    return 1;
}

//-----------------------------------------------------------------------------
// fill a rect with a color tuple
//-----------------------------------------------------------------------------
int
JM_fill_pixmap_rect_with_color(fz_context *ctx, fz_pixmap *dest, unsigned char col[5], fz_irect b)
{
    unsigned char *destp;
    int x, y, w, i, destspan;

    b = fz_intersect_irect(b, fz_pixmap_bbox(ctx, dest));
    w = b.x1 - b.x0;
    y = b.y1 - b.y0;
    if (w <= 0 || y <= 0)
        return 0;

    destspan = dest->stride;
    destp = dest->samples + (unsigned int)(destspan * (b.y0 - dest->y) + dest->n * (b.x0 - dest->x));

    do {
        unsigned char *s = destp;
        for (x = 0; x < w; x++) {
            for (i = 0; i < dest->n; i++)
                *s++ = col[i];
        }
        destp += destspan;
    } while (--y);
    return 1;
}

//-----------------------------------------------------------------------------
// invert a rectangle - also supports non-alpha pixmaps
//-----------------------------------------------------------------------------
int
JM_invert_pixmap_rect(fz_context *ctx, fz_pixmap *dest, fz_irect b)
{
    unsigned char *destp;
    int x, y, w, i, destspan;

    b = fz_intersect_irect(b, fz_pixmap_bbox(ctx, dest));
    w = b.x1 - b.x0;
    y = b.y1 - b.y0;
    if (w <= 0 || y <= 0)
        return 0;

    destspan = dest->stride;
    destp = dest->samples + (unsigned int)(destspan * (b.y0 - dest->y) + dest->n * (b.x0 - dest->x));
    int n0 = dest->n - dest->alpha;
    do {
        unsigned char *s = destp;
        for (x = 0; x < w; x++) {
            for (i = 0; i < n0; i++) {
                *s = 255 - *s;
                s++;
            }
            if (dest->alpha) s++;
        }
        destp += destspan;
    } while (--y);
    return 1;
}

int
JM_is_jbig2_image(fz_context *ctx, pdf_obj *dict)
{
    // fixme: should we remove this function?
	return 0;
    /*
    pdf_obj *filter;
	int i, n;

	filter = pdf_dict_get(ctx, dict, PDF_NAME(Filter));
	if (pdf_name_eq(ctx, filter, PDF_NAME(JBIG2Decode)))
		return 1;
	n = pdf_array_len(ctx, filter);
	for (i = 0; i < n; i++)
		if (pdf_name_eq(ctx, pdf_array_get(ctx, filter, i), PDF_NAME(JBIG2Decode)))
			return 1;
	return 0;
    */
}

//-----------------------------------------------------------------------------
// Return basic properties of an image provided as bytes or bytearray
// The function creates an fz_image and optionally returns it.
//-----------------------------------------------------------------------------
PyObject *JM_image_profile(fz_context *ctx, PyObject *imagedata, int keep_image)
{
    if (!EXISTS(imagedata)) {
        Py_RETURN_NONE;  // nothing given
    }
    fz_image *image = NULL;
    fz_buffer *res = NULL;
    PyObject *result = NULL;
    unsigned char *c = NULL;
    Py_ssize_t len = 0;
    if (PyBytes_Check(imagedata)) {
        c = PyBytes_AS_STRING(imagedata);
        len = PyBytes_GET_SIZE(imagedata);
    } else if (PyByteArray_Check(imagedata)) {
        c = PyByteArray_AS_STRING(imagedata);
        len = PyByteArray_GET_SIZE(imagedata);
    } else {
        PySys_WriteStderr("bad image data\n");
        Py_RETURN_NONE;
    }

    if (len < 8) {
        PySys_WriteStderr("bad image data\n");
        Py_RETURN_NONE;
    }
    int type = fz_recognize_image_format(ctx, c);
    if (type == FZ_IMAGE_UNKNOWN) {
        Py_RETURN_NONE;
    }

    fz_try(ctx) {
        if (keep_image) {
            res = fz_new_buffer_from_copied_data(ctx, c, (size_t) len);
        } else {
            res = fz_new_buffer_from_shared_data(ctx, c, (size_t) len);
        }
        image = fz_new_image_from_buffer(ctx, res);
        int xres, yres, orientation;
        fz_matrix ctm = fz_image_orientation_matrix(ctx, image);
        fz_image_resolution(image, &xres, &yres);
        orientation = (int) fz_image_orientation(ctx, image);
        const char *cs_name = fz_colorspace_name(ctx, image->colorspace);
        result = PyDict_New();
        DICT_SETITEM_DROP(result, dictkey_width,
                Py_BuildValue("i", image->w));
        DICT_SETITEM_DROP(result, dictkey_height,
                Py_BuildValue("i", image->h));
        DICT_SETITEMSTR_DROP(result, "orientation",
                Py_BuildValue("i", orientation));
        DICT_SETITEM_DROP(result, dictkey_matrix,
                JM_py_from_matrix(ctm));
        DICT_SETITEM_DROP(result, dictkey_xres,
                Py_BuildValue("i", xres));
        DICT_SETITEM_DROP(result, dictkey_yres,
                Py_BuildValue("i", yres));
        DICT_SETITEM_DROP(result, dictkey_colorspace,
                Py_BuildValue("i", image->n));
        DICT_SETITEM_DROP(result, dictkey_bpc,
                Py_BuildValue("i", image->bpc));
        DICT_SETITEM_DROP(result, dictkey_ext,
                Py_BuildValue("s", JM_image_extension(type)));
        DICT_SETITEM_DROP(result, dictkey_cs_name,
                Py_BuildValue("s", cs_name));

        if (keep_image) {
            DICT_SETITEM_DROP(result, dictkey_image,
                    PyLong_FromVoidPtr((void *) fz_keep_image(ctx, image)));
        }
    }
    fz_always(ctx) {
        if (!keep_image) {
            fz_drop_image(ctx, image);
        } else {
            fz_drop_buffer(ctx, res);  // drop the buffer copy
        }
    }
    fz_catch(ctx) {
        Py_CLEAR(result);
        fz_rethrow(ctx);
    }
    PyErr_Clear();
    return result;
}

//----------------------------------------------------------------------------
// Version of fz_new_pixmap_from_display_list (util.c) to also support
// rendering of only the 'clip' part of the displaylist rectangle
//----------------------------------------------------------------------------
fz_pixmap *
JM_pixmap_from_display_list(fz_context *ctx,
                            fz_display_list *list,
                            PyObject *ctm,
                            fz_colorspace *cs,
                            int alpha,
                            PyObject *clip,
                            fz_separations *seps
                           )
{
    fz_rect rect = fz_bound_display_list(ctx, list);
    fz_matrix matrix = JM_matrix_from_py(ctm);
    fz_pixmap *pix = NULL;
    fz_var(pix);
    fz_device *dev = NULL;
    fz_var(dev);
    fz_rect rclip = JM_rect_from_py(clip);
    rect = fz_intersect_rect(rect, rclip);  // no-op if clip is not given

    rect = fz_transform_rect(rect, matrix);
    fz_irect irect = fz_round_rect(rect);

    pix = fz_new_pixmap_with_bbox(ctx, cs, irect, seps, alpha);
    if (alpha)
        fz_clear_pixmap(ctx, pix);
    else
        fz_clear_pixmap_with_value(ctx, pix, 0xFF);

    fz_try(ctx) {
        if (!fz_is_infinite_rect(rclip)) {
            dev = fz_new_draw_device_with_bbox(ctx, matrix, pix, &irect);
            fz_run_display_list(ctx, list, dev, fz_identity, rclip, NULL);
        } else {
            dev = fz_new_draw_device(ctx, matrix, pix);
            fz_run_display_list(ctx, list, dev, fz_identity, fz_infinite_rect, NULL);
        }

        fz_close_device(ctx, dev);
    }
    fz_always(ctx) {
        fz_drop_device(ctx, dev);
    }
    fz_catch(ctx) {
        fz_drop_pixmap(ctx, pix);
        fz_rethrow(ctx);
    }
    return pix;
}

//----------------------------------------------------------------------------
// Pixmap creation directly using a short-lived displaylist, so we can support
// separations.
//----------------------------------------------------------------------------
fz_pixmap *
JM_pixmap_from_page(fz_context *ctx,
                    fz_document *doc,
                    fz_page *page,
                    PyObject *ctm,
                    fz_colorspace *cs,
                    int alpha,
                    int annots,
                    PyObject *clip
                   )
{
    enum { SPOTS_NONE, SPOTS_OVERPRINT_SIM, SPOTS_FULL };
    int spots;
    if (FZ_ENABLE_SPOT_RENDERING)
        spots = SPOTS_OVERPRINT_SIM;
    else
        spots = SPOTS_NONE;

    fz_separations *seps = NULL;
    fz_pixmap *pix = NULL;
    fz_colorspace *oi = NULL;
    fz_var(oi);
    fz_colorspace *colorspace = cs;
    fz_rect rect;
    fz_irect bbox;
    fz_device *dev = NULL;
    fz_var(dev);
    fz_matrix matrix = JM_matrix_from_py(ctm);
    rect = fz_bound_page(ctx, page);
    fz_rect rclip = JM_rect_from_py(clip);
    rect = fz_intersect_rect(rect, rclip);  // no-op if clip is not given
    rect = fz_transform_rect(rect, matrix);
    bbox = fz_round_rect(rect);

    fz_try(ctx) {
        // Pixmap of the document's /OutputIntents ("output intents")
        oi = fz_document_output_intent(ctx, doc);
        // if present and compatible, use it instead of the parameter
        if (oi) {
            if (fz_colorspace_n(ctx, oi) == fz_colorspace_n(ctx, cs)) {
                colorspace = fz_keep_colorspace(ctx, oi);
            }
        }

        // check if spots rendering is available and if so use separations
        if (spots != SPOTS_NONE) {
            seps = fz_page_separations(ctx, page);
            if (seps) {
                int i, n = fz_count_separations(ctx, seps);
                if (spots == SPOTS_FULL)
                    for (i = 0; i < n; i++)
                        fz_set_separation_behavior(ctx, seps, i, FZ_SEPARATION_SPOT);
                else
                    for (i = 0; i < n; i++)
                        fz_set_separation_behavior(ctx, seps, i, FZ_SEPARATION_COMPOSITE);
            } else if (fz_page_uses_overprint(ctx, page)) {
                /* This page uses overprint, so we need an empty
                 * sep object to force the overprint simulation on. */
                seps = fz_new_separations(ctx, 0);
            } else if (oi && fz_colorspace_n(ctx, oi) != fz_colorspace_n(ctx, colorspace)) {
                /* We have an output intent, and it's incompatible
                 * with the colorspace our device needs. Force the
                 * overprint simulation on, because this ensures that
                 * we 'simulate' the output intent too. */
                seps = fz_new_separations(ctx, 0);
            }
        }

        pix = fz_new_pixmap_with_bbox(ctx, colorspace, bbox, seps, alpha);

        if (alpha) {
            fz_clear_pixmap(ctx, pix);
        } else {
            fz_clear_pixmap_with_value(ctx, pix, 0xFF);
        }

        dev = fz_new_draw_device(ctx, matrix, pix);
        if (annots) {
            fz_run_page(ctx, page, dev, fz_identity, NULL);
        } else {
            fz_run_page_contents(ctx, page, dev, fz_identity, NULL);
        }
        fz_close_device(ctx, dev);
    }
    fz_always(ctx) {
        fz_drop_device(ctx, dev);
        fz_drop_separations(ctx, seps);
        fz_drop_colorspace(ctx, oi);
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return pix;
}

PyObject *JM_color_count(fz_context *ctx, fz_pixmap *pm, PyObject *clip)
{
    PyObject *rc = PyDict_New(), *pixel=NULL, *c=NULL;
    long cnt=0;
    fz_irect irect = fz_pixmap_bbox(ctx, pm);
    irect = fz_intersect_irect(irect, fz_round_rect(JM_rect_from_py(clip)));
    size_t stride = pm->stride;
    size_t width = irect.x1 - irect.x0, height = irect.y1 - irect.y0;
    size_t i, j, n = (size_t) pm->n, substride = width * n;
    unsigned char *s = pm->samples + stride * (irect.y0 - pm->y) + (irect.x0 - pm->x) * n;
    unsigned char oldpix[10], newpix[10];
    memcpy(oldpix, s, n);
    cnt = 0;
    fz_try(ctx) {
        if (fz_is_empty_irect(irect)) goto finished;
        for (i = 0; i < height; i++) {
            for (j = 0; j < substride; j += n) {
                memcpy(newpix, s + j, n);
                if (memcmp(oldpix, newpix,n) != 0) {
                    pixel = PyBytes_FromStringAndSize(oldpix, n);
                    c = PyDict_GetItem(rc, pixel);
                    if (c) cnt += PyLong_AsLong(c);
                    DICT_SETITEM_DROP(rc, pixel, PyLong_FromLong(cnt));
                    Py_DECREF(pixel);
                    cnt = 1;
                    memcpy(oldpix, newpix, n);
                } else {
                    cnt += 1;
                }
            }
            s += stride;
        }
        pixel = PyBytes_FromStringAndSize(oldpix, n);
        c = PyDict_GetItem(rc, pixel);
        if (c) cnt += PyLong_AsLong(c);
        DICT_SETITEM_DROP(rc, pixel, PyLong_FromLong(cnt));
        Py_DECREF(pixel);
        finished:;
    }
    fz_catch(ctx) {
        Py_CLEAR(rc);
        fz_rethrow(ctx);
    }
    PyErr_Clear();
    return rc;
}
%}
