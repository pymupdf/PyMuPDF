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
//------------------------------------------------------------------------
// return pdf_obj "border style" from Python str
//------------------------------------------------------------------------
pdf_obj *JM_get_border_style(fz_context *ctx, PyObject *style)
{
    pdf_obj *val = PDF_NAME(S);
    if (!style) return val;
    char *s = JM_StrAsChar(style);
    JM_PyErr_Clear;
    if (!s) return val;
    if      (!strncmp(s, "b", 1) || !strncmp(s, "B", 1)) val = PDF_NAME(B);
    else if (!strncmp(s, "d", 1) || !strncmp(s, "D", 1)) val = PDF_NAME(D);
    else if (!strncmp(s, "i", 1) || !strncmp(s, "I", 1)) val = PDF_NAME(I);
    else if (!strncmp(s, "u", 1) || !strncmp(s, "U", 1)) val = PDF_NAME(U);
    return val;
}

//------------------------------------------------------------------------
// Make /DA string of annotation
//------------------------------------------------------------------------
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
        else if (ncol == 3 || ncol == 0)
            fz_append_printf(ctx, buf, "%g %g %g rg ", col[0], col[1], col[2]);
        else
            fz_append_printf(ctx, buf, "%g %g %g %g k ", col[0], col[1], col[2], col[3]);
        fz_append_printf(ctx, buf, "/%s %g Tf", JM_expand_fname(&fontname), fontsize);
        unsigned char *da = NULL;
        size_t len = fz_buffer_storage(ctx, buf, &da);
        pdf_obj *annot_obj = pdf_annot_obj(ctx, annot);
        pdf_dict_put_string(ctx, annot_obj, PDF_NAME(DA), (const char *) da, len);
    }
    fz_always(ctx) fz_drop_buffer(ctx, buf);
    fz_catch(ctx) fz_rethrow(ctx);
    return;
}

//------------------------------------------------------------------------
// refreshes the link and annotation tables of a page
//------------------------------------------------------------------------
void JM_refresh_links(fz_context *ctx, pdf_page *page)
{
    if (!page) return;
    fz_try(ctx)
    {
		pdf_obj *obj = pdf_dict_get(ctx, page->obj, PDF_NAME(Annots));
		if (obj)
		{
			pdf_document *pdf = page->doc;
            int number = pdf_lookup_page_number(ctx, pdf, page->obj);
            fz_rect page_mediabox;
			fz_matrix page_ctm;
			pdf_page_transform(ctx, page, &page_mediabox, &page_ctm);
			page->links = pdf_load_link_annots(ctx, pdf, obj, number, page_ctm);
		}
    }
    fz_catch(ctx) {
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
    if (pdf_is_array(ctx, o)) {
        width = pdf_to_real(ctx, pdf_array_get(ctx, o, 2));
        if (pdf_array_len(ctx, o) == 4) {
            pdf_obj *dash = pdf_array_get(ctx, o, 3);
            for (i = 0; i < pdf_array_len(ctx, dash); i++) {
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
        if (o) {
            for (i = 0; i < pdf_array_len(ctx, o); i++) {
                val = Py_BuildValue("i", pdf_to_int(ctx, pdf_array_get(ctx, o, i)));
                LIST_APPEND_DROP(dash_py, val);
            }
        }
    }

    pdf_obj *be_o = pdf_dict_gets(ctx, annot_obj, "BE");
    if (be_o) {
        o = pdf_dict_get(ctx, be_o, PDF_NAME(S));
        if (o) effect2 = (char *) pdf_to_name(ctx, o);
        o = pdf_dict_get(ctx, be_o, PDF_NAME(I));
        if (o) effect1 = pdf_to_int(ctx, o);
    }

    LIST_APPEND_DROP(effect_py, Py_BuildValue("i", effect1));
    LIST_APPEND_DROP(effect_py, Py_BuildValue("s", effect2));
    DICT_SETITEM_DROP(res, dictkey_width, Py_BuildValue("f", width));
    DICT_SETITEM_DROP(res, dictkey_dashes, dash_py);
    DICT_SETITEM_DROP(res, dictkey_style, Py_BuildValue("s", style));
    if (effect1 > -1) PyDict_SetItem(res, dictkey_effect, effect_py);
    Py_CLEAR(effect_py);
    return res;
}

PyObject *JM_annot_set_border(fz_context *ctx, PyObject *border, pdf_document *doc, pdf_obj *annot_obj)
{
    if (!PyDict_Check(border)) {
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

    if (ndashes && PySequence_Check(ndashes) && PySequence_Size(ndashes) > 0) {
        n = PySequence_Size(ndashes);
        pdf_obj *darr = pdf_new_array(ctx, doc, n);
        for (i = 0; i < n; i++) {
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
    PyObject *color = NULL;
    int i, n;
    float col;
    pdf_obj *o = NULL;
    
    o = pdf_dict_get(ctx, annot_obj, PDF_NAME(C));
    if (pdf_is_array(ctx, o)) {
        n = pdf_array_len(ctx, o);
        color = PyTuple_New((Py_ssize_t) n);
        for (i = 0; i < n; i++) {
            col = pdf_to_real(ctx, pdf_array_get(ctx, o, i));
            PyTuple_SET_ITEM(color, i, Py_BuildValue("f", col));
        }
        DICT_SETITEM_DROP(res, dictkey_stroke, color);
    } else {
        DICT_SETITEM_DROP(res, dictkey_stroke, Py_BuildValue("s", NULL));
    }

    o = pdf_dict_get(ctx, annot_obj, PDF_NAME(IC));
    if (pdf_is_array(ctx, o)) {
        n = pdf_array_len(ctx, o);
        color = PyTuple_New((Py_ssize_t) n);
        for (i = 0; i < n; i++) {
            col = pdf_to_real(ctx, pdf_array_get(ctx, o, i));
            PyTuple_SET_ITEM(color, i, Py_BuildValue("f", col));
        }
        DICT_SETITEM_DROP(res, dictkey_fill, color);
    } else {
        DICT_SETITEM_DROP(res, dictkey_fill, Py_BuildValue("s", NULL));
    }

    return res;
}


//------------------------------------------------------------------------
// Return the first annotation whose /IRT key ("In Response To") points to
// annot. Used to remove the response chain of a given annotation.
//------------------------------------------------------------------------
pdf_annot *JM_find_annot_irt(fz_context *ctx, pdf_annot *annot)
{
    pdf_annot *irt_annot = NULL;  // returning this
    pdf_obj *annot_obj = pdf_annot_obj(ctx, annot);
    pdf_obj *o = NULL;
    int found = 0;
    fz_try(ctx) {   // loop thru MuPDF's internal annots array
        pdf_page *page = pdf_annot_page(ctx, annot);
        irt_annot = pdf_first_annot(ctx, page);
        while (irt_annot) {
            pdf_obj *irt_annot_obj = pdf_annot_obj(ctx, irt_annot);
            o = pdf_dict_gets(ctx, irt_annot_obj, "IRT");
            if (o) {
                if (!pdf_objcmp(ctx, o, annot_obj)) {
                    found = 1;
                    break;
                }
            }
            irt_annot = pdf_next_annot(ctx, irt_annot);
        }
    }
    fz_catch(ctx) {;}
    if (found) return pdf_keep_annot(ctx, irt_annot);
    return NULL;
}

//------------------------------------------------------------------------
// return the annotation names (list of /NM entries)
//------------------------------------------------------------------------
PyObject *JM_get_annot_id_list(fz_context *ctx, pdf_page *page)
{
    PyObject *names = PyList_New(0);
    pdf_obj *annot_obj = NULL;
    pdf_obj *annots = pdf_dict_get(ctx, page->obj, PDF_NAME(Annots));
    pdf_obj *name = NULL;
    if (!annots) return names;
    fz_try(ctx) {
        int i, n = pdf_array_len(ctx, annots);
        for (i = 0; i < n; i++) {
            annot_obj = pdf_array_get(ctx, annots, i);
            name = pdf_dict_gets(ctx, annot_obj, "NM");
            if (name) {
                LIST_APPEND_DROP(names, Py_BuildValue("s", pdf_to_text_string(ctx, name)));
            }
        }
    }
    fz_catch(ctx) {
        return names;
    }
    return names;
}


//------------------------------------------------------------------------
// return the xrefs and /NM ids of a page's annots, links and fields
//------------------------------------------------------------------------
PyObject *JM_get_annot_xref_list(fz_context *ctx, pdf_obj *page_obj)
{
    PyObject *names = PyList_New(0);
    pdf_obj *id, *annot_obj = NULL;
    pdf_obj *annots = pdf_dict_get(ctx, page_obj, PDF_NAME(Annots));
    if (!annots) return names;
    fz_try(ctx) {
        int i, n = pdf_array_len(ctx, annots);
        for (i = 0; i < n; i++) {
            annot_obj = pdf_array_get(ctx, annots, i);
            int xref = pdf_to_num(ctx, annot_obj);
            pdf_obj *subtype = pdf_dict_get(ctx, annot_obj, PDF_NAME(Subtype));
            int type = PDF_ANNOT_UNKNOWN;
            if (subtype) {
                const char *name = pdf_to_name(ctx, subtype);
                type = pdf_annot_type_from_string(ctx, name);
            }
            id = pdf_dict_gets(ctx, annot_obj, "NM");
            LIST_APPEND_DROP(names, Py_BuildValue("iis", xref, type, pdf_to_text_string(ctx, id)));
        }
    }
    fz_catch(ctx) {
        return names;
    }
    return names;
}


//------------------------------------------------------------------------
// Add a unique /NM key to an annotation or widget.
// Append a number to 'stem' such that the result is a unique name.
//------------------------------------------------------------------------
static char JM_annot_id_stem[50] = "fitz";
void JM_add_annot_id(fz_context *ctx, pdf_annot *annot, char *stem)
{
    fz_try(ctx) {
        PyObject *names = NULL;
        pdf_page *page = pdf_annot_page(ctx, annot);
        pdf_obj *annot_obj = pdf_annot_obj(ctx, annot);
        names = JM_get_annot_id_list(ctx, page);
        int i = 0;
        PyObject *stem_id = NULL;
        while (1) {
            stem_id = PyUnicode_FromFormat("%s-%s%d", JM_annot_id_stem, stem, i);
            if (!PySequence_Contains(names, stem_id)) break;
            i += 1;
            Py_DECREF(stem_id);
        }
        char *response = JM_StrAsChar(stem_id);
        pdf_obj *name = pdf_new_string(ctx, (const char *) response, strlen(response));
        pdf_dict_puts_drop(ctx, annot_obj, "NM", name);
        Py_CLEAR(stem_id);
        Py_CLEAR(names);
        page->doc->resynth_required = 0;
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
}

//------------------------------------------------------------------------
// retrieve annot by name (/NM key)
//------------------------------------------------------------------------
pdf_annot *JM_get_annot_by_name(fz_context *ctx, pdf_page *page, char *name)
{
    if (!name || strlen(name) == 0) {
        return NULL;
    }
    pdf_annot *annot = NULL;
    int found = 0;
    size_t len = 0;

    fz_try(ctx) {   // loop thru MuPDF's internal annots and widget arrays
        annot = pdf_first_annot(ctx, page);
        while (annot) {
            pdf_obj *annot_obj = pdf_annot_obj(ctx, annot);
            const char *response = pdf_to_string(ctx, pdf_dict_gets(ctx, annot_obj, "NM"), &len);
            if (strcmp(name, response) == 0) {
                found = 1;
                break;
            annot = pdf_next_annot(ctx, annot);
            }
        }
        if (!found) {
            fz_throw(ctx, FZ_ERROR_GENERIC, "'%s' is not an annot of this page", name);
        }
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return pdf_keep_annot(ctx, annot);
}

//------------------------------------------------------------------------
// retrieve annot by its xref
//------------------------------------------------------------------------
pdf_annot *JM_get_annot_by_xref(fz_context *ctx, pdf_page *page, int xref)
{
    pdf_annot *annot = NULL;
    int found = 0;

    fz_try(ctx) {   // loop thru MuPDF's internal annots array
        annot = pdf_first_annot(ctx, page);
        while (annot) {
            pdf_obj *annot_obj = pdf_annot_obj(ctx, annot);
            if (xref == pdf_to_num(ctx, annot_obj)) {
                found = 1;
                break;
            }
            annot = pdf_next_annot(ctx, annot);
        }
        if (!found) {
            fz_throw(ctx, FZ_ERROR_GENERIC, "xref %d is not an annot of this page", xref);
        }
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return pdf_keep_annot(ctx, annot);
}

//------------------------------------------------------------------------
// retrieve widget by its xref
//------------------------------------------------------------------------
pdf_annot *JM_get_widget_by_xref(fz_context *ctx, pdf_page *page, int xref)
{
    pdf_annot *annot = NULL;
    int found = 0;

    fz_try(ctx) {   // loop thru MuPDF's internal annots array
        annot = pdf_first_widget(ctx, page);
        while (annot) {
            pdf_obj *annot_obj = pdf_annot_obj(ctx, annot);
            if (xref == pdf_to_num(ctx, annot_obj)) {
                found = 1;
                break;
            }
            annot = pdf_next_widget(ctx, annot);
        }
        if (!found) {
            fz_throw(ctx, FZ_ERROR_GENERIC, "xref %d is not a widget of this page", xref);
        }
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return pdf_keep_annot(ctx, annot);
}

%}
