%{
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
    if (fz_colorspace_n(ctx, dest->colorspace) == 4)
    {
        value = 255 - value;
        do
        {
            unsigned char *s = destp;
            for (x = 0; x < w; x++)
            {
                *s++ = 0;
                *s++ = 0;
                *s++ = 0;
                *s++ = value;
                if (dest->alpha) *s++ = 255;
            }
            destp += destspan;
        }
        while (--y);
        return 1;
    }

    do
    {
        unsigned char *s = destp;
        for (x = 0; x < w; x++)
        {
            for (k = 0; k < dest->n - 1; k++)
                *s++ = value;
            if (dest->alpha) *s++ = 255;
            else *s++ = value;
        }
        destp += destspan;
    }
    while (--y);
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

    do
    {
        unsigned char *s = destp;
        for (x = 0; x < w; x++)
        {
            for (i = 0; i < dest->n; i++)
                *s++ = col[i];
        }
        destp += destspan;
    }
    while (--y);
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
    do
    {
        unsigned char *s = destp;
        for (x = 0; x < w; x++)
        {
            for (i = 0; i < n0; i++)
                *s++ = 255 - *s;
            if (dest->alpha) *s++;
        }
        destp += destspan;
    }
    while (--y);
    return 1;
}

//-----------------------------------------------------------------------------
// Return basic properties of an image provided as bytes or bytearray
// The function creates an fz_image and optionally returns it.
//-----------------------------------------------------------------------------
PyObject *JM_image_profile(fz_context *ctx, PyObject *imagedata, int keep_image)
{
    if (!EXISTS(imagedata))
    {
        return NONE;  // nothing given
    }
    fz_image *image = NULL;
    fz_buffer *res = NULL;
    PyObject *result = NULL;
    unsigned char *c = NULL;
    Py_ssize_t len = 0;

    if (PyBytes_Check(imagedata))
    {
        c = PyBytes_AS_STRING(imagedata);
        len = PyBytes_GET_SIZE(imagedata);
    }
    else if (PyByteArray_Check(imagedata))
    {
        c = PyByteArray_AS_STRING(imagedata);
        len = PyByteArray_GET_SIZE(imagedata);
    }
    else
    {
        PySys_WriteStderr("stream not bytes-like\n");
        return PyDict_New();
    }

    if (len < 8)
    {
        PySys_WriteStderr("stream too short\n");
        return PyDict_New();
    }

    fz_try(ctx)
    {
        if (keep_image)
        {
            res = fz_new_buffer_from_copied_data(ctx, c, (size_t) len);
        }
        else
        {
            res = fz_new_buffer_from_shared_data(ctx, c, (size_t) len);
        }
        image = fz_new_image_from_buffer(ctx, res);
        int type = fz_recognize_image_format(ctx, c);
        result = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:s,s:n}",
                                "width", image->w,
                                "height", image->h,
                                "colorspace", image->n,
                                "bpc", image->bpc,
                                "format", type,
                                "ext", JM_image_extension(type),
                                "size", len
                              );
        if (keep_image)
        {   // keep fz_image: hand over address, do not drop
            PyDict_SetItemString(result, "image", PyLong_FromVoidPtr((void *) fz_keep_image(ctx, image)));
        }
    }
    fz_always(ctx)
    {
        if (!keep_image)
        {
            fz_drop_image(ctx, image);  // conditional drop
        }
        else
        {
            fz_drop_buffer(ctx, res);  // drop the buffer copy
        }
    }
    fz_catch(ctx)
    {
        PySys_WriteStderr("%s\n", fz_caught_message(ctx));
        result = PyDict_New();
    }
    return result;
}

%}