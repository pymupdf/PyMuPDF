%{
//----------------------------------------------------------------------------
// return code for line end style string
//----------------------------------------------------------------------------
int JM_le_value(fz_context *ctx, char *le)
{
    if (!le) return PDF_ANNOT_LE_NONE;
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
void JM_refresh_link_table(fz_context *ctx, pdf_page *page)
{
    fz_try(ctx)
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
    }
    fz_catch(ctx)
    {
        fz_rethrow(ctx);
    }
    return;
}


PyObject *JM_annot_border(fz_context *ctx, pdf_obj *annot_obj)
{
    PyObject *res = PyDict_New();
    PyObject *dash_py   = PyList_New(0);
    PyObject *effect_py = PyList_New(0);
    PyObject *val;
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
            {
                val = Py_BuildValue("i", pdf_to_int(ctx, pdf_array_get(ctx, dash, i)));
                LIST_APPEND_DROP(dash_py, val);
            }
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
            {
                val = Py_BuildValue("i", pdf_to_int(ctx, pdf_array_get(ctx, o, i)));
                LIST_APPEND_DROP(dash_py, val);
            }
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

    LIST_APPEND_DROP(effect_py, Py_BuildValue("i", effect1));
    LIST_APPEND_DROP(effect_py, JM_UNICODE(effect2));
    DICT_SETITEM_DROP(res, dictkey_width, Py_BuildValue("f", width));
    DICT_SETITEM_DROP(res, dictkey_dashes, dash_py);
    DICT_SETITEM_DROP(res, dictkey_style, JM_UNICODE(style));
    if (effect1 > -1) PyDict_SetItem(res, dictkey_effect, effect_py);
    Py_CLEAR(effect_py);
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

    nwidth = PyFloat_AsDouble(PyDict_GetItem(border, dictkey_width));
    ndashes = PyDict_GetItem(border, dictkey_dashes);
    nstyle  = PyDict_GetItem(border, dictkey_style);

    // first get old border properties
    PyObject *oborder = JM_annot_border(ctx, annot_obj);
    owidth = PyFloat_AsDouble(PyDict_GetItem(oborder, dictkey_width));
    odashes = PyDict_GetItem(oborder, dictkey_dashes);
    ostyle = PyDict_GetItem(oborder, dictkey_style);

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
        nstyle = PyUnicode_FromString("D");
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
            LIST_APPEND_DROP(bc, Py_BuildValue("f", col));
        }
    }
    DICT_SETITEM_DROP(res, dictkey_stroke, bc);

    o = pdf_dict_gets(ctx, annot_obj, "IC");
    if (pdf_is_array(ctx, o))
    {
        int n = pdf_array_len(ctx, o);
        for (i = 0; i < n; i++)
        {
            col = pdf_to_real(ctx, pdf_array_get(ctx, o, i));
            LIST_APPEND_DROP(fc, Py_BuildValue("f", col));
        }
    }
    DICT_SETITEM_DROP(res, dictkey_fill, fc);

    return res;
}

//----------------------------------------------------------------------------
// delete an annotation using mupdf functions, but first delete the /AP and
// /Popup dict keys in the annot->obj. Also remove the 'Popup' annotation
// from the page's /Annots array which may exist.
//----------------------------------------------------------------------------
void JM_delete_annot(fz_context *ctx, pdf_page *page, pdf_annot *annot)
{
    if (!annot) return;
    fz_try(ctx)
    {
        pdf_obj *popup = pdf_dict_get(ctx, annot->obj, PDF_NAME(Popup));
        pdf_dict_del(ctx, annot->obj, PDF_NAME(Popup));
        pdf_dict_del(ctx, annot->obj, PDF_NAME(AP));
        if (popup)  // now look for the popup entry
        {
            pdf_obj *annots = pdf_dict_get(ctx, page->obj, PDF_NAME(Annots));
            int i, n = pdf_array_len(ctx, annots);
            for (i = 0; i < n; i++)
            {
                pdf_obj *o = pdf_array_get(ctx, annots, i);
                pdf_obj *p = pdf_dict_get(ctx, o, PDF_NAME(Parent));
                if (!p) continue;
                if (!pdf_objcmp(ctx, p, annot->obj))
                {
                    pdf_array_delete(ctx, annots, i);
                    break;
                }
            }
        }
        pdf_delete_annot(ctx, page, annot);
    }
    fz_catch(ctx)
    {
        fz_warn(ctx, "could not delete annotation");
    }
    return;
}

//----------------------------------------------------------------------------
// locate and return the first annotation whose /IRT key points to annot.
//----------------------------------------------------------------------------
pdf_annot *JM_find_annot_irt(fz_context *ctx, pdf_annot *annot)
{
    pdf_annot *irt_annot = NULL;  // returning this
    pdf_obj *o = NULL;
    pdf_annot **annotptr;
    int found = 0;
    fz_try(ctx)
    {   // loop thru MuPDF's internal annots array
        pdf_page *page = annot->page;
        for (annotptr = &page->annots; *annotptr; annotptr = &(*annotptr)->next)
        {
            irt_annot = *annotptr;  // check if this is what we are looking for
            o = pdf_dict_gets(ctx, irt_annot->obj, "IRT");
            if (o)
            {
                if (!pdf_objcmp(ctx, o, annot->obj))
                {
                    found = 1;
                    break;
                }
            }
        }
    }
    fz_catch(ctx) {;}
    if (found)
        return irt_annot;
    return NULL;
}
%}
