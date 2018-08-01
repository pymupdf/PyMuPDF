%{
//----------------------------------------------------------------------------
// annotation types
//----------------------------------------------------------------------------
#define ANNOT_TEXT 0
#define ANNOT_LINK 1
#define ANNOT_FREETEXT 2
#define ANNOT_LINE 3
#define ANNOT_SQUARE 4
#define ANNOT_CIRCLE 5
#define ANNOT_POLYGON 6
#define ANNOT_POLYLINE 7
#define ANNOT_HIGHLIGHT 8
#define ANNOT_UNDERLINE 9
#define ANNOT_SQUIGGLY 10
#define ANNOT_STRIKEOUT 11
#define ANNOT_STAMP 12
#define ANNOT_CARET 13
#define ANNOT_INK 14
#define ANNOT_POPUP 15
#define ANNOT_FILEATTACHMENT 16
#define ANNOT_SOUND 17
#define ANNOT_MOVIE 18
#define ANNOT_WIDGET 19
#define ANNOT_SCREEN 20
#define ANNOT_PRINTERMARK 21
#define ANNOT_TRAPNET 22
#define ANNOT_WATERMARK 23
#define ANNOT_3D 24

//----------------------------------------------------------------------------
// annotation flag bits
//----------------------------------------------------------------------------
#define ANNOT_XF_Invisible 1 << (1-1)
#define ANNOT_XF_Hidden 1 << (2-1)
#define ANNOT_XF_Print 1 << (3-1)
#define ANNOT_XF_NoZoom 1 << (4-1)
#define ANNOT_XF_NoRotate 1 << (5-1)
#define ANNOT_XF_NoView 1 << (6-1)
#define ANNOT_XF_ReadOnly 1 << (7-1)
#define ANNOT_XF_Locked 1 << (8-1)
#define ANNOT_XF_ToggleNoView 1 << (9-1)
#define ANNOT_XF_LockedContents 1 << (10-1)

//----------------------------------------------------------------------------
// annotation line ending styles
//----------------------------------------------------------------------------
#define ANNOT_LE_None 0
#define ANNOT_LE_Square 1
#define ANNOT_LE_Circle 2
#define ANNOT_LE_Diamond 3
#define ANNOT_LE_OpenArrow 4
#define ANNOT_LE_ClosedArrow 5
#define ANNOT_LE_Butt 6
#define ANNOT_LE_ROpenArrow 7
#define ANNOT_LE_RClosedArrow 8
#define ANNOT_LE_Slash 9

//----------------------------------------------------------------------------
// annotation field (widget) types
//----------------------------------------------------------------------------
#define ANNOT_WG_NOT_WIDGET -1
#define ANNOT_WG_PUSHBUTTON 0
#define ANNOT_WG_CHECKBOX 1
#define ANNOT_WG_RADIOBUTTON 2
#define ANNOT_WG_TEXT 3
#define ANNOT_WG_LISTBOX 4
#define ANNOT_WG_COMBOBOX 5
#define ANNOT_WG_SIGNATURE 6

//----------------------------------------------------------------------------
// annotation text widget subtypes
//----------------------------------------------------------------------------
#define ANNOT_WG_TEXT_UNRESTRAINED 0
#define ANNOT_WG_TEXT_NUMBER 1
#define ANNOT_WG_TEXT_SPECIAL 2
#define ANNOT_WG_TEXT_DATE 3
#define ANNOT_WG_TEXT_TIME 4

//----------------------------------------------------------------------------
// annotation widget flags
//----------------------------------------------------------------------------
// Common to all field types
#define WIDGET_Ff_ReadOnly 1
#define WIDGET_Ff_Required 2
#define WIDGET_Ff_NoExport 4

// Text fields
#define WIDGET_Ff_Multiline 4096
#define WIDGET_Ff_Password 8192

#define WIDGET_Ff_FileSelect 1048576
#define WIDGET_Ff_DoNotSpellCheck 4194304
#define WIDGET_Ff_DoNotScroll 8388608
#define WIDGET_Ff_Comb 16777216
#define WIDGET_Ff_RichText 33554432

// Button fields
#define WIDGET_Ff_NoToggleToOff 16384
#define WIDGET_Ff_Radio 32768
#define WIDGET_Ff_Pushbutton 65536
#define WIDGET_Ff_RadioInUnison 33554432

// Choice fields
#define WIDGET_Ff_Combo 131072
#define WIDGET_Ff_Edit 262144
#define WIDGET_Ff_Sort 524288
#define WIDGET_Ff_MultiSelect 2097152
#define WIDGET_Ff_CommitOnSelCHange 67108864

//----------------------------------------------------------------------------
// return string for line end style
//----------------------------------------------------------------------------
int JM_le_value(fz_context *ctx, char *le)
{
    if (!le) return ANNOT_LE_None;
    return pdf_line_ending_from_string(ctx, le);
}

//----------------------------------------------------------------------------
// return pdf_obj "border style" from Python str
//----------------------------------------------------------------------------
pdf_obj *JM_get_border_style(fz_context *ctx, PyObject *style)
{
    pdf_obj *val = PDF_NAME_S;
    if (!style) return val;
    char *s = JM_Python_str_AsChar(style);
    JM_PyErr_Clear;
    if (!s) return val;
    if      (!strncmp(s, "b", 1) || !strncmp(s, "B", 1)) val = PDF_NAME_B;
    else if (!strncmp(s, "d", 1) || !strncmp(s, "D", 1)) val = PDF_NAME_D;
    else if (!strncmp(s, "i", 1) || !strncmp(s, "I", 1)) val = PDF_NAME_I;
    else if (!strncmp(s, "u", 1) || !strncmp(s, "U", 1)) val = PDF_NAME_U;
    JM_Python_str_DelForPy3(s);
    return val;
}

//----------------------------------------------------------------------------
// refreshes the link and annotation tables of a page
//----------------------------------------------------------------------------
void refresh_link_table(fz_context *ctx, pdf_page *page)
{
    pdf_obj *annots_arr = pdf_dict_get(ctx, page->obj, PDF_NAME_Annots);
    if (annots_arr)
    {
        fz_rect page_mediabox;
        fz_matrix page_ctm;
        pdf_page_transform(ctx, page, &page_mediabox, &page_ctm);
        page->links = pdf_load_link_annots(ctx, page->doc, annots_arr,
                                           pdf_to_num(ctx, page->obj), &page_ctm);
        pdf_load_annots(ctx, page, annots_arr);
    }
    return;
}

//-----------------------------------------------------------------------------
// create a strike-out / underline / highlight annotation
//-----------------------------------------------------------------------------
struct fz_annot_s *JM_AnnotTextmarker(fz_context *ctx, pdf_page *page, fz_rect *rect, int type)
{
    pdf_annot *annot = NULL;
    float line_thickness = 0.0f;
    float line_height = 0.0f;
    float alpha = 1.0f;
    float h  = rect->y1 - rect->y0;
    fz_rect bbox = {rect->x0, rect->y0, rect->x1, rect->y1};
    float color[3] = {0,0,0};
    switch (type)
    {
        case PDF_ANNOT_HIGHLIGHT:
            color[0] = 1.0f;
            color[1] = 1.0f;
            color[2] = 0.0f;
            alpha = 0.3f;
            line_thickness = 1.0f;
            line_height = 0.5f;
            break;
        case PDF_ANNOT_UNDERLINE:
            color[0] = 0.0f;
            color[1] = 0.0f;
            color[2] = 1.0f;
            alpha = 1.0f;
            line_thickness = 0.07f;
            line_height = 0.075f;
            bbox.y0 += 0.8f * h;
            bbox.y1 += 0.8f * h;
            break;
        case PDF_ANNOT_STRIKE_OUT:
            color[0] = 1.0f;
            color[1] = 0.0f;
            color[2] = 0.0f;
            alpha = 1.0f;
            line_thickness = 0.07f;
            line_height = 0.375f;
            bbox.y0 += 0.17f * h;
            bbox.y1 += 0.17f * h;
            break;
    }
    fz_try(ctx)
    {
        pdf_document *pdf = page->doc;
        annot = pdf_create_annot(ctx, page, type);
        pdf_set_annot_color(ctx, annot, 3, color);
        pdf_set_annot_border(ctx, annot, line_thickness);
        pdf_add_annot_quad_point(ctx, annot, bbox);
        pdf_set_annot_rect(ctx, annot, &bbox);
        pdf_set_markup_appearance(ctx, pdf, annot, color, alpha, line_thickness, line_height);
    }
    fz_catch(ctx) fz_rethrow(ctx);
    pdf_dirty_annot(ctx, annot);
    return (fz_annot *) annot;
}

//-----------------------------------------------------------------------------
// create a circle or rectangle annotation
//-----------------------------------------------------------------------------
struct fz_annot_s *JM_AnnotCircleOrRect(fz_context *ctx, pdf_page *page, fz_rect *rect, int type)
{
    pdf_annot *annot;
    float col[3] = {0,0,0};
    float width  = 1;
    fz_try(ctx)
    {
        pdf_document *pdf = page->doc;
        annot = pdf_create_annot(ctx, page, type);
        pdf_set_annot_border(ctx, annot, width);
        pdf_set_annot_color(ctx, annot, 3, col);
        pdf_set_annot_rect(ctx, annot, rect);
    }
    fz_catch(ctx) fz_rethrow(ctx);
    pdf_dirty_annot(ctx, annot);
    return (fz_annot *) annot;
}

//-----------------------------------------------------------------------------
// create a polyline or polygon annotation
//-----------------------------------------------------------------------------
struct fz_annot_s *JM_AnnotMultiline(fz_context *ctx, pdf_page *page, PyObject *points, int type)
{
    pdf_annot *annot;
    fz_try(ctx)
    {
        float col[3] = {0,0,0};
        float width  = 1;
        fz_point point = {0,0};
        fz_rect rect;
        
        int n = 0, i;
        if (PySequence_Check(points)) n = PySequence_Size(points);
        if (n < 2) THROWMSG("invalid points list");
        annot = pdf_create_annot(ctx, page, type);
        for (i = 0; i < n; i++)
        {
            PyObject *p = PySequence_ITEM(points, i);
            if (!PySequence_Check(p) || PySequence_Size(p) != 2)
                THROWMSG("invalid points list");
            point.x = (float) PyFloat_AsDouble(PySequence_GetItem(p, 0));
            point.y = (float) PyFloat_AsDouble(PySequence_GetItem(p, 1));
            Py_CLEAR(p);
            pdf_add_annot_vertex(ctx, annot, point);
            if (i == 0)
            {
                rect.x0 = point.x;
                rect.y0 = point.y;
                rect.x1 = point.x;
                rect.y1 = point.y;
            }
            else
                fz_include_point_in_rect(&rect, &point);
        }
        pdf_set_annot_border(ctx, annot, width); // standard: width = 1
        pdf_set_annot_color(ctx, annot, 3, col); // standard: black
        fz_expand_rect(&rect, 3 * width);
        pdf_set_annot_rect(ctx, annot, &rect);
    }
    fz_catch(ctx) fz_rethrow(ctx);
    pdf_dirty_annot(ctx, annot);
    return (fz_annot *) annot;
}

void JM_draw_pushpin1(fz_context *ctx, fz_path *path)
{
    fz_moveto(ctx, path, 2.8f, 29.0f);
    fz_lineto(ctx, path, 17.2f, 29.0f);
    fz_lineto(ctx, path, 13.6f, 22.0f);
    fz_lineto(ctx, path, 13.6f, 17.8f);
    fz_lineto(ctx, path, 19.0f, 10.8f);
    fz_lineto(ctx, path, 1.0f, 10.8f);
    fz_lineto(ctx, path, 6.4f, 17.8f);
    fz_lineto(ctx, path, 6.4f, 22.0f);
    fz_lineto(ctx, path, 2.8f, 29.0f);
    fz_closepath(ctx, path);
}

void JM_draw_pushpin2(fz_context *ctx, fz_path *path)
{
    fz_moveto(ctx, path, 13.6f, 22.0f);
    fz_lineto(ctx, path, 6.4f, 22.0f);
    fz_moveto(ctx, path, 13.6f, 17.8f);
    fz_lineto(ctx, path, 6.4f, 17.8f);
    fz_closepath(ctx, path);
}

void JM_draw_pushpin3(fz_context *ctx, fz_path *path)
{
    fz_moveto(ctx, path, 9.1f, 10.8f);
    fz_lineto(ctx, path, 10.0f, 1.0f);
    fz_lineto(ctx, path, 10.9f, 10.8f);
    fz_closepath(ctx, path);
}

void JM_update_file_attachment_annot(fz_context *ctx, pdf_document *doc, pdf_annot *annot)
{
    static float yellow[3] = {1.0f, 1.0f, 0.0f};
    static float blue[3] = {0.0f, 0.0f, 1.0f};
    static float black[3] = {0.0f, 0.0f, 0.0f};
    static float outline_thickness = 0.9f;
    fz_display_list *dlist = NULL;
    fz_device *dev = NULL;
    fz_colorspace *cs = NULL;
    fz_path *path = NULL;
    fz_stroke_state *stroke = NULL;
    fz_matrix page_ctm;
    pdf_page_transform(ctx, annot->page, NULL, &page_ctm);
    fz_var(path);
    fz_var(stroke);
    fz_var(dlist);
    fz_var(dev);
    fz_var(cs);
    fz_try(ctx)
    {
        fz_rect rect;

        pdf_to_rect(ctx, pdf_dict_get(ctx, annot->obj, PDF_NAME_Rect), &rect);
        dlist = fz_new_display_list(ctx, NULL);
        dev = fz_new_list_device(ctx, dlist);
        cs = fz_device_rgb(ctx); /* Borrowed reference */
        stroke = fz_new_stroke_state(ctx);
        stroke->linewidth = outline_thickness;
        stroke->linejoin = FZ_LINEJOIN_ROUND;

        path = fz_new_path(ctx);
        JM_draw_pushpin1(ctx, path);
        fz_fill_path(ctx, dev, path, 0, &page_ctm, cs, yellow, 1.0f, NULL);
        fz_stroke_path(ctx, dev, path, stroke, &page_ctm, cs, black, 1.0f, NULL);
        fz_drop_path(ctx, path);
        path = NULL;

        path = fz_new_path(ctx);
        JM_draw_pushpin2(ctx, path);
        fz_stroke_path(ctx, dev, path, stroke, &page_ctm, cs, black, 1.0f, NULL);
        fz_drop_path(ctx, path);
        path = NULL;

        path = fz_new_path(ctx);
        JM_draw_pushpin3(ctx, path);
        fz_fill_path(ctx, dev, path, 0, &page_ctm, cs, blue, 1.0f, NULL);
        fz_stroke_path(ctx, dev, path, stroke, &page_ctm, cs, black, 1.0f, NULL);
        fz_close_device(ctx, dev);

        fz_transform_rect(&rect, &page_ctm);
        pdf_set_annot_appearance(ctx, doc, annot, &rect, dlist);
        rect.x0 = rect.y0 = 0;
        rect.x1 = 20;
        rect.y1 = 30;
        pdf_obj *ap = pdf_dict_getl(ctx, annot->obj, PDF_NAME_AP, PDF_NAME_N, NULL);
        pdf_dict_put_rect(ctx, ap, PDF_NAME_BBox, &rect);
        pdf_drop_obj(ctx, annot->ap);
        annot->ap = NULL;
    }
    fz_always(ctx)
    {
        fz_drop_device(ctx, dev);
        fz_drop_display_list(ctx, dlist);
        fz_drop_stroke_state(ctx, stroke);
        fz_drop_path(ctx, path);
    }
    fz_catch(ctx)
    {
        fz_rethrow(ctx);
    }
}

%}