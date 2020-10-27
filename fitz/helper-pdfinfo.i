%{

//----------------------------------------------------------------------------
// Store ID in PDF trailer
//----------------------------------------------------------------------------
void JM_ensure_identity(fz_context *ctx, pdf_document *pdf)
{
    unsigned char rnd[16];
    pdf_obj *id;
    id = pdf_dict_get(ctx, pdf_trailer(ctx, pdf), PDF_NAME(ID));
    if (!id) {
        fz_memrnd(ctx, rnd, nelem(rnd));
        id = pdf_dict_put_array(ctx, pdf_trailer(ctx, pdf), PDF_NAME(ID), 2);
        pdf_array_push_drop(ctx, id, pdf_new_string(ctx, (char *) rnd + 0, nelem(rnd)));
        pdf_array_push_drop(ctx, id, pdf_new_string(ctx, (char *) rnd + 0, nelem(rnd)));
    }
}


//-----------------------------------------------------------------------------
// Store info of a font in Python list
//-----------------------------------------------------------------------------
int JM_gather_fonts(fz_context *ctx, pdf_document *pdf, pdf_obj *dict,
                    PyObject *fontlist, int stream_xref)
{
    int i, n, rc = 1;
    n = pdf_dict_len(ctx, dict);
    for (i = 0; i < n; i++) {
        pdf_obj *fontdict = NULL;
        pdf_obj *subtype = NULL;
        pdf_obj *basefont = NULL;
        pdf_obj *name = NULL;
        pdf_obj *refname = NULL;
        pdf_obj *encoding = NULL;

        refname = pdf_dict_get_key(ctx, dict, i);
        fontdict = pdf_dict_get_val(ctx, dict, i);
        if (!pdf_is_dict(ctx, fontdict)) {
            fz_warn(ctx, "'%s' is no font dict (%d 0 R)",
                    pdf_to_name(ctx, refname), pdf_to_num(ctx, fontdict));
            continue;
        }

        subtype = pdf_dict_get(ctx, fontdict, PDF_NAME(Subtype));
        basefont = pdf_dict_get(ctx, fontdict, PDF_NAME(BaseFont));
        if (!basefont || pdf_is_null(ctx, basefont))
            name = pdf_dict_get(ctx, fontdict, PDF_NAME(Name));
        else
            name = basefont;
        encoding = pdf_dict_get(ctx, fontdict, PDF_NAME(Encoding));
        if (pdf_is_dict(ctx, encoding))
            encoding = pdf_dict_get(ctx, encoding, PDF_NAME(BaseEncoding));
        int xref = pdf_to_num(ctx, fontdict);
        char *ext = "n/a";
        if (xref) ext = JM_get_fontextension(ctx, pdf, xref);
        PyObject *entry = PyTuple_New(7);
        PyTuple_SET_ITEM(entry, 0, Py_BuildValue("i", xref));
        PyTuple_SET_ITEM(entry, 1, Py_BuildValue("s", ext));
        PyTuple_SET_ITEM(entry, 2, Py_BuildValue("s", pdf_to_name(ctx, subtype)));
        PyTuple_SET_ITEM(entry, 3, JM_EscapeStrFromStr(pdf_to_name(ctx, name)));
        PyTuple_SET_ITEM(entry, 4, Py_BuildValue("s", pdf_to_name(ctx, refname)));
        PyTuple_SET_ITEM(entry, 5, Py_BuildValue("s", pdf_to_name(ctx, encoding)));
        PyTuple_SET_ITEM(entry, 6, Py_BuildValue("i", stream_xref));
        LIST_APPEND_DROP(fontlist, entry);
    }
    return rc;
}

//-----------------------------------------------------------------------------
// Store info of an image in Python list
//-----------------------------------------------------------------------------
int JM_gather_images(fz_context *ctx, pdf_document *doc, pdf_obj *dict,
                     PyObject *imagelist, int stream_xref)
{
    int i, n, rc = 1;
    n = pdf_dict_len(ctx, dict);
    for (i = 0; i < n; i++) {
        pdf_obj *imagedict, *smask;
        pdf_obj *refname = NULL;
        pdf_obj *type;
        pdf_obj *width;
        pdf_obj *height;
        pdf_obj *bpc = NULL;
        pdf_obj *filter = NULL;
        pdf_obj *cs = NULL;
        pdf_obj *altcs;

        refname = pdf_dict_get_key(ctx, dict, i);
        imagedict = pdf_dict_get_val(ctx, dict, i);
        if (!pdf_is_dict(ctx, imagedict)) {
            fz_warn(ctx, "'%s' is no image dict (%d 0 R)",
                    pdf_to_name(ctx, refname), pdf_to_num(ctx, imagedict));
            continue;
        }

        type = pdf_dict_get(ctx, imagedict, PDF_NAME(Subtype));
        if (!pdf_name_eq(ctx, type, PDF_NAME(Image)))
            continue;

        int xref = pdf_to_num(ctx, imagedict);
        int gen = 0;
        smask = pdf_dict_get(ctx, imagedict, PDF_NAME(SMask));
        if (smask)
            gen = pdf_to_num(ctx, smask);
        smask = pdf_dict_get(ctx, imagedict, PDF_NAME(Mask));
        if (smask)
            gen = pdf_to_num(ctx, smask);
        filter = pdf_dict_get(ctx, imagedict, PDF_NAME(Filter));
        if (pdf_is_array(ctx, filter)) {
            filter = pdf_array_get(ctx, filter, 0);
        }

        altcs = NULL;
        cs = pdf_dict_get(ctx, imagedict, PDF_NAME(ColorSpace));
        if (pdf_is_array(ctx, cs)) {
            pdf_obj *cses = cs;
            cs = pdf_array_get(ctx, cses, 0);
            if (pdf_name_eq(ctx, cs, PDF_NAME(DeviceN)) ||
                pdf_name_eq(ctx, cs, PDF_NAME(Separation))) {
                altcs = pdf_array_get(ctx, cses, 2);
                if (pdf_is_array(ctx, altcs))
                    altcs = pdf_array_get(ctx, altcs, 0);
            }
        }

        width = pdf_dict_get(ctx, imagedict, PDF_NAME(Width));
        height = pdf_dict_get(ctx, imagedict, PDF_NAME(Height));
        bpc = pdf_dict_get(ctx, imagedict, PDF_NAME(BitsPerComponent));

        PyObject *entry = PyTuple_New(10);
        PyTuple_SET_ITEM(entry, 0, Py_BuildValue("i", xref));
        PyTuple_SET_ITEM(entry, 1, Py_BuildValue("i", gen));
        PyTuple_SET_ITEM(entry, 2, Py_BuildValue("i", pdf_to_int(ctx, width)));
        PyTuple_SET_ITEM(entry, 3, Py_BuildValue("i", pdf_to_int(ctx, height)));
        PyTuple_SET_ITEM(entry, 4, Py_BuildValue("i", pdf_to_int(ctx, bpc)));
        PyTuple_SET_ITEM(entry, 5, JM_EscapeStrFromStr(pdf_to_name(ctx, cs)));
        PyTuple_SET_ITEM(entry, 6, JM_EscapeStrFromStr(pdf_to_name(ctx, altcs)));
        PyTuple_SET_ITEM(entry, 7, JM_EscapeStrFromStr(pdf_to_name(ctx, refname)));
        PyTuple_SET_ITEM(entry, 8, JM_EscapeStrFromStr(pdf_to_name(ctx, filter)));
        PyTuple_SET_ITEM(entry, 9, Py_BuildValue("i", stream_xref));
        LIST_APPEND_DROP(imagelist, entry);
    }
    return rc;
}

//-----------------------------------------------------------------------------
// Store info of a /Form xobject in Python list
//-----------------------------------------------------------------------------
int JM_gather_forms(fz_context *ctx, pdf_document *doc, pdf_obj *dict,
                     PyObject *imagelist, int stream_xref)
{
    int i, rc = 1, n = pdf_dict_len(ctx, dict);
    fz_rect bbox;
    pdf_obj *o = NULL, *m = NULL;
    for (i = 0; i < n; i++) {
        pdf_obj *imagedict;
        pdf_obj *refname = NULL;
        pdf_obj *type;

        refname = pdf_dict_get_key(ctx, dict, i);
        imagedict = pdf_dict_get_val(ctx, dict, i);
        if (!pdf_is_dict(ctx, imagedict)) {
            fz_warn(ctx, "'%s' is no form dict (%d 0 R)",
                    pdf_to_name(ctx, refname), pdf_to_num(ctx, imagedict));
            continue;
        }

        type = pdf_dict_get(ctx, imagedict, PDF_NAME(Subtype));
        if (!pdf_name_eq(ctx, type, PDF_NAME(Form)))
            continue;

        o = pdf_dict_get(ctx, imagedict, PDF_NAME(BBox));
        m = pdf_dict_get(ctx, imagedict, PDF_NAME(Matrix));
        if (o) {
            if (m) {
                bbox = fz_transform_rect(pdf_to_rect(ctx, o), pdf_to_matrix(ctx, m));
            } else {
                bbox = pdf_to_rect(ctx, o);
            }
        } else {
            bbox = fz_infinite_rect;
        }
        int xref = pdf_to_num(ctx, imagedict);

        PyObject *entry = PyTuple_New(4);
        PyTuple_SET_ITEM(entry, 0, Py_BuildValue("i", xref));
        PyTuple_SET_ITEM(entry, 1, Py_BuildValue("s", pdf_to_name(ctx, refname)));
        PyTuple_SET_ITEM(entry, 2, Py_BuildValue("i", stream_xref));
        PyTuple_SET_ITEM(entry, 3, JM_py_from_rect(bbox));
        LIST_APPEND_DROP(imagelist, entry);
    }
    return rc;
}

//-----------------------------------------------------------------------------
// Step through /Resources, looking up image, xobject or font information
//-----------------------------------------------------------------------------
void JM_scan_resources(fz_context *ctx, pdf_document *pdf, pdf_obj *rsrc,
                 PyObject *liste, int what, int stream_xref,
                 PyObject *tracer)
{
    pdf_obj *font, *xobj, *subrsrc;
    int i, n, sxref;
    if (pdf_mark_obj(ctx, rsrc)) {
        fz_warn(ctx, "Circular dependencies! Consider page cleaning.");
        return;  // Circular dependencies!
    }

    fz_try(ctx) {

        xobj = pdf_dict_get(ctx, rsrc, PDF_NAME(XObject));

        if (what == 1) {  // lookup fonts
            font = pdf_dict_get(ctx, rsrc, PDF_NAME(Font));
            JM_gather_fonts(ctx, pdf, font, liste, stream_xref);
        } else if (what == 2) {  // look up images
            JM_gather_images(ctx, pdf, xobj, liste, stream_xref);
        } else if (what == 3) {  // look up form xobjects
            JM_gather_forms(ctx, pdf, xobj, liste, stream_xref);
        } else {  // should never happen
            goto finished;
        }

        // check if we need to recurse into Form XObjects
        n = pdf_dict_len(ctx, xobj);
        for (i = 0; i < n; i++) {
            pdf_obj *obj = pdf_dict_get_val(ctx, xobj, i);
            if (pdf_is_stream(ctx, obj)) {
                sxref = pdf_to_num(ctx, obj);
            } else {
                sxref = 0;
            }
            subrsrc = pdf_dict_get(ctx, obj, PDF_NAME(Resources));
            if (subrsrc) {
                PyObject *sxref_t = Py_BuildValue("i", sxref);
                if (PySequence_Contains(tracer, sxref_t) == 0) {
                    LIST_APPEND_DROP(tracer, sxref_t);
                    JM_scan_resources(ctx, pdf, subrsrc, liste, what, sxref, tracer);
                } else {
                    Py_DECREF(sxref_t);
                    PyErr_Clear();
                    fz_warn(ctx, "Circular dependencies! Consider page cleaning.");
                    goto finished;
                }
            }
        }
        finished:;
    }
    fz_always(ctx) {
        pdf_unmark_obj(ctx, rsrc);
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
}
%}
