%{
//-----------------------------------------------------------------------------
// pixmap helper functions
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
// Clear a pixmap rectangle - my version also supports non-alpha pixmaps
//-----------------------------------------------------------------------------
void
JM_clear_pixmap_rect_with_value(fz_context *ctx, fz_pixmap *dest, int value, fz_irect b)
{
    unsigned char *destp;
    int x, y, w, k, destspan;

    b = fz_intersect_irect(b, fz_pixmap_bbox(ctx, dest));
    w = b.x1 - b.x0;
    y = b.y1 - b.y0;
    if (w <= 0 || y <= 0)
        return;

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
        return;
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
}

//-----------------------------------------------------------------------------
// fill a rect with a color tuple
//-----------------------------------------------------------------------------
void
JM_fill_pixmap_rect_with_color(fz_context *ctx, fz_pixmap *dest, unsigned char col[5], fz_irect b)
{
    unsigned char *destp;
    int x, y, w, i, destspan;

    b = fz_intersect_irect(b, fz_pixmap_bbox(ctx, dest));
    w = b.x1 - b.x0;
    y = b.y1 - b.y0;
    if (w <= 0 || y <= 0)
        return;

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
}

//-----------------------------------------------------------------------------
// invert a rectangle - also supports non-alpha pixmaps
//-----------------------------------------------------------------------------
//-----------------------------------------------------------------------------
// fill a rect with a color tuple
//-----------------------------------------------------------------------------
void
JM_invert_pixmap_rect(fz_context *ctx, fz_pixmap *dest, fz_irect b)
{
    unsigned char *destp;
    int x, y, w, i, destspan;

    b = fz_intersect_irect(b, fz_pixmap_bbox(ctx, dest));
    w = b.x1 - b.x0;
    y = b.y1 - b.y0;
    if (w <= 0 || y <= 0)
        return;

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
}

%}