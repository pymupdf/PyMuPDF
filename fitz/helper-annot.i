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
// return code for line end style string
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
    pdf_obj *val = PDF_NAME(S);
    if (!style) return val;
    char *s = JM_Python_str_AsChar(style);
    JM_PyErr_Clear;
    if (!s) return val;
    if      (!strncmp(s, "b", 1) || !strncmp(s, "B", 1)) val = PDF_NAME(B);
    else if (!strncmp(s, "d", 1) || !strncmp(s, "D", 1)) val = PDF_NAME(D);
    else if (!strncmp(s, "i", 1) || !strncmp(s, "I", 1)) val = PDF_NAME(I);
    else if (!strncmp(s, "u", 1) || !strncmp(s, "U", 1)) val = PDF_NAME(U);
    JM_Python_str_DelForPy3(s);
    return val;
}

//----------------------------------------------------------------------------
// Make /DA string of annotation
//----------------------------------------------------------------------------
const char *JM_expand_fname(const char **name)
{
    if (!*name) return "Helv";
    if (!strncmp(*name, "Co", 2)) return "Cour";
    if (!strncmp(*name, "co", 2)) return "Cour";
    if (!strncmp(*name, "Ti", 2)) return "TiRo";
    if (!strncmp(*name, "ti", 2)) return "TiRo";
    if (!strncmp(*name, "Sy", 2)) return "Symb";
    if (!strncmp(*name, "sy", 2)) return "Symb";
    if (!strncmp(*name, "Za", 2)) return "ZaDb";
    if (!strncmp(*name, "za", 2)) return "ZaDb";
    return "Helv";
}

void JM_make_annot_DA(fz_context *ctx, pdf_annot *annot, int ncol, float col[4], const char *fontname, float fontsize)
{
    fz_buffer *buf = NULL;
    fz_try(ctx)
    {
        buf = fz_new_buffer(ctx, 50);
       if (ncol == 1)
            fz_append_printf(ctx, buf, "%g g ", col[0]);
        else if (ncol == 3)
            fz_append_printf(ctx, buf, "%g %g %g rg ", col[0], col[1], col[2]);
        else
            fz_append_printf(ctx, buf, "%g %g %g %g k ", col[0], col[1], col[2], col[3]);
        fz_append_printf(ctx, buf, "/%s %g Tf", JM_expand_fname(&fontname), fontsize);
        char *da = NULL;
        size_t len = fz_buffer_storage(ctx, buf, &da);
        pdf_dict_put_string(ctx, annot->obj, PDF_NAME(DA), (const char *)da, len);
    }
    fz_always(ctx) fz_drop_buffer(ctx, buf);
    fz_catch(ctx) fz_rethrow(ctx);
    return;
}

//----------------------------------------------------------------------------
// refreshes the link and annotation tables of a page
//----------------------------------------------------------------------------
void refresh_link_table(fz_context *ctx, pdf_page *page)
{
    pdf_obj *annots_arr = pdf_dict_get(ctx, page->obj, PDF_NAME(Annots));
    if (annots_arr)
    {
        fz_rect page_mediabox;
        fz_matrix page_ctm;
        pdf_page_transform(ctx, page, &page_mediabox, &page_ctm);
        page->links = pdf_load_link_annots(ctx, page->doc, annots_arr,
                                           pdf_to_num(ctx, page->obj), page_ctm);
        pdf_load_annots(ctx, page, annots_arr);
    }
    return;
}

//-----------------------------------------------------------------------------
// create a strike-out / underline / highlight annotation
//-----------------------------------------------------------------------------
struct fz_annot_s *JM_AnnotTextmarker(fz_context *ctx, pdf_page *page, fz_quad q, int type)
{
    pdf_annot *annot = NULL;
    float width = 0;
    float color[3] = {0,0,0};
    switch (type)
    {
        case PDF_ANNOT_HIGHLIGHT:
            color[0] = color[1] = 1; color[2] = 0;
            width = 1.0f;
            break;
        case PDF_ANNOT_UNDERLINE:
            color[0] = color[1] = 0; color[2] = 1;
            width = 0.07f;
            break;
        case PDF_ANNOT_SQUIGGLY:
            color[0] = color[1] = 0; color[2] = 1;
            width = 0.07f;
            break;
        case PDF_ANNOT_STRIKE_OUT:
            color[0] = 1; color[1] = color[2] = 0;
            width = 0.07f;
            break;
    }
    fz_try(ctx)
    {
        pdf_document *pdf = page->doc;
        annot = pdf_create_annot(ctx, page, type);
        pdf_set_annot_color(ctx, annot, 3, color);
        pdf_set_annot_border(ctx, annot, width);
        pdf_add_annot_quad_point(ctx, annot, q);
        pdf_set_annot_rect(ctx, annot, fz_rect_from_quad(q));
        pdf_update_annot(ctx, annot);
    }
    fz_catch(ctx) fz_rethrow(ctx);
    return (fz_annot *) annot;
}

//-----------------------------------------------------------------------------
// create a circle or rectangle annotation
//-----------------------------------------------------------------------------
struct fz_annot_s *JM_AnnotCircleOrRect(fz_context *ctx, pdf_page *page, PyObject *rect, int type)
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
        pdf_set_annot_rect(ctx, annot, JM_rect_from_py(rect));
        pdf_update_annot(ctx, annot);
    }
    fz_catch(ctx) fz_rethrow(ctx);
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
            point.x = (float) PyFloat_AsDouble(PySequence_ITEM(p, 0));
            point.y = (float) PyFloat_AsDouble(PySequence_ITEM(p, 1));
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
                rect = fz_include_point_in_rect(rect, point);
        }
        pdf_set_annot_border(ctx, annot, width); // standard: width = 1
        pdf_set_annot_color(ctx, annot, 3, col); // standard: black
        rect = fz_expand_rect(rect, 3 * width);
        pdf_set_annot_rect(ctx, annot, rect);
        pdf_update_annot(ctx, annot);
    }
    fz_catch(ctx) fz_rethrow(ctx);
    return (fz_annot *) annot;
}

PyObject *JM_annot_border(fz_context *ctx, pdf_obj *annot_obj)
{
    PyObject *res = PyDict_New();
    PyObject *dash_py   = PyList_New(0);
    PyObject *effect_py = PyList_New(0);
    int i;
    char *effect2 = NULL, *style = NULL;
    float width = -1.0f;
    int effect1 = -1;

    pdf_obj *o = pdf_dict_get(ctx, annot_obj, PDF_NAME(Border));
    if (pdf_is_array(ctx, o))
    {
        width = pdf_to_real(ctx, pdf_array_get(ctx, o, 2));
        if (pdf_array_len(ctx, o) == 4)
        {
            pdf_obj *dash = pdf_array_get(ctx, o, 3);
            for (i = 0; i < pdf_array_len(ctx, dash); i++)
                PyList_Append(dash_py, Py_BuildValue("i",
                              pdf_to_int(ctx, pdf_array_get(ctx, dash, i))));
        }
    }

    pdf_obj *bs_o = pdf_dict_get(ctx, annot_obj, PDF_NAME(BS));
    if (bs_o)
    {
        o = pdf_dict_get(ctx, bs_o, PDF_NAME(W));
        if (o) width = pdf_to_real(ctx, o);
        o = pdf_dict_get(ctx, bs_o, PDF_NAME(S));
        if (o) style = (char *) pdf_to_name(ctx, o);
        o = pdf_dict_get(ctx, bs_o, PDF_NAME(D));
        if (o)
        {
            for (i = 0; i < pdf_array_len(ctx, o); i++)
                PyList_Append(dash_py, Py_BuildValue("i",
                              pdf_to_int(ctx, pdf_array_get(ctx, o, i))));
        }
    }

    pdf_obj *be_o = pdf_dict_gets(ctx, annot_obj, "BE");
    if (be_o)
    {
        o = pdf_dict_get(ctx, be_o, PDF_NAME(S));
        if (o) effect2 = (char *) pdf_to_name(ctx, o);
        o = pdf_dict_get(ctx, be_o, PDF_NAME(I));
        if (o) effect1 = pdf_to_int(ctx, o);
    }

    PyList_Append(effect_py, Py_BuildValue("i", effect1));
    PyList_Append(effect_py, Py_BuildValue("s", effect2));

    PyDict_SetItemString(res, "width", Py_BuildValue("f", width));

    PyDict_SetItemString(res, "dashes", dash_py);

    PyDict_SetItemString(res, "style", Py_BuildValue("s", style));

    if (effect1 > -1) PyDict_SetItemString(res, "effect", effect_py);
    Py_CLEAR(effect_py);
    Py_CLEAR(dash_py);
    return res;
}

PyObject *JM_annot_set_border(fz_context *ctx, PyObject *border, pdf_document *doc, pdf_obj *annot_obj)
{
    if (!PyDict_Check(border))
    {
        JM_Warning("arg must be a dict");
        Py_RETURN_NONE;     // not a dict
    }

    double nwidth = -1;                       // new width
    double owidth = -1;                       // old width
    PyObject *ndashes = NULL;                 // new dashes
    PyObject *odashes = NULL;                 // old dashes
    PyObject *nstyle  = NULL;                 // new style
    PyObject *ostyle  = NULL;                 // old style

    nwidth = PyFloat_AsDouble(PyDict_GetItemString(border, "width"));
    ndashes = PyDict_GetItemString(border, "dashes");
    nstyle  = PyDict_GetItemString(border, "style");

    // first get old border properties
    PyObject *oborder = JM_annot_border(ctx, annot_obj);
    owidth = PyFloat_AsDouble(PyDict_GetItemString(oborder, "width"));
    odashes = PyDict_GetItemString(oborder, "dashes");
    ostyle = PyDict_GetItemString(oborder, "style");

    // then delete any relevant entries
    pdf_dict_del(ctx, annot_obj, PDF_NAME(BS));
    pdf_dict_del(ctx, annot_obj, PDF_NAME(BE));
    pdf_dict_del(ctx, annot_obj, PDF_NAME(Border));

    Py_ssize_t i, n;
    int d;
    // populate new border array
    if (nwidth < 0) nwidth = owidth;     // no new width: take current
    if (nwidth < 0) nwidth = 0.0f;       // default if no width given
    if (!ndashes) ndashes = odashes;     // no new dashes: take old
    if (!nstyle)  nstyle  = ostyle;      // no new style: take old

    if (ndashes && PySequence_Check(ndashes) && PySequence_Size(ndashes) > 0)
    {
        n = PySequence_Size(ndashes);
        pdf_obj *darr = pdf_new_array(ctx, doc, n);
        for (i = 0; i < n; i++)
        {
            d = (int) PyInt_AsLong(PySequence_ITEM(ndashes, i));
            pdf_array_push_int(ctx, darr, (int64_t) d);
        }
        pdf_dict_putl_drop(ctx, annot_obj, darr, PDF_NAME(BS), PDF_NAME(D), NULL);
        nstyle = Py_BuildValue("s", "D");
    }

    pdf_dict_putl_drop(ctx, annot_obj, pdf_new_real(ctx, nwidth),
                               PDF_NAME(BS), PDF_NAME(W), NULL);

    pdf_obj *val = JM_get_border_style(ctx, nstyle);

    pdf_dict_putl_drop(ctx, annot_obj, val,
                               PDF_NAME(BS), PDF_NAME(S), NULL);

    PyErr_Clear();
    Py_RETURN_NONE;
}

PyObject *JM_annot_colors(fz_context *ctx, pdf_obj *annot_obj)
{
    PyObject *res = PyDict_New();
    PyObject *bc = PyList_New(0);        // stroke colors
    PyObject *fc = PyList_New(0);        // fill colors

    int i;
    float col;
    pdf_obj *o = pdf_dict_get(ctx, annot_obj, PDF_NAME(C));
    if (pdf_is_array(ctx, o))
    {
        int n = pdf_array_len(ctx, o);
        for (i = 0; i < n; i++)
        {
            col = pdf_to_real(ctx, pdf_array_get(ctx, o, i));
            PyList_Append(bc, Py_BuildValue("f", col));
        }
    }
    PyDict_SetItemString(res, "stroke", bc);

    o = pdf_dict_gets(ctx, annot_obj, "IC");
    if (pdf_is_array(ctx, o))
    {
        int n = pdf_array_len(ctx, o);
        for (i = 0; i < n; i++)
        {
            col = pdf_to_real(ctx, pdf_array_get(ctx, o, i));
            PyList_Append(fc, Py_BuildValue("f", col));
        }
    }
    PyDict_SetItemString(res, "fill", fc);

    Py_CLEAR(bc);
    Py_CLEAR(fc);
    return res;
}
%}
