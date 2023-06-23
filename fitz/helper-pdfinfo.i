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
// Store ID in PDF trailer
//------------------------------------------------------------------------
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


//------------------------------------------------------------------------
// Ensure OCProperties, return /OCProperties key
//------------------------------------------------------------------------
pdf_obj *
JM_ensure_ocproperties(fz_context *ctx, pdf_document *pdf)
{
    pdf_obj *D, *ocp;
    fz_try(ctx) {
        ocp = pdf_dict_get(ctx, pdf_dict_get(ctx, pdf_trailer(ctx, pdf), PDF_NAME(Root)), PDF_NAME(OCProperties));
        if (ocp) goto finished;
        pdf_obj *root = pdf_dict_get(ctx, pdf_trailer(ctx, pdf), PDF_NAME(Root));
        ocp = pdf_dict_put_dict(ctx, root, PDF_NAME(OCProperties), 2);
        pdf_dict_put_array(ctx, ocp, PDF_NAME(OCGs), 0);
        D = pdf_dict_put_dict(ctx, ocp, PDF_NAME(D), 5);
        pdf_dict_put_array(ctx, D, PDF_NAME(ON), 0);
        pdf_dict_put_array(ctx, D, PDF_NAME(OFF), 0);
        pdf_dict_put_array(ctx, D, PDF_NAME(Order), 0);
        pdf_dict_put_array(ctx, D, PDF_NAME(RBGroups), 0);
    finished:;
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return ocp;
}


//------------------------------------------------------------------------
// Add OC configuration to the PDF catalog
//------------------------------------------------------------------------
void
JM_add_layer_config(fz_context *ctx, pdf_document *pdf, char *name, char *creator, PyObject *ON)
{
    pdf_obj *D, *ocp, *configs;
    fz_try(ctx) {
        ocp = JM_ensure_ocproperties(ctx, pdf);
        configs = pdf_dict_get(ctx, ocp, PDF_NAME(Configs));
        if (!pdf_is_array(ctx, configs)) {
            configs = pdf_dict_put_array(ctx,ocp, PDF_NAME(Configs), 1);
        }
        D = pdf_new_dict(ctx, pdf, 5);
        pdf_dict_put_text_string(ctx, D, PDF_NAME(Name), name);
        if (creator) {
            pdf_dict_put_text_string(ctx, D, PDF_NAME(Creator), creator);
        }
        pdf_dict_put(ctx, D, PDF_NAME(BaseState), PDF_NAME(OFF));
        pdf_obj *onarray = pdf_dict_put_array(ctx, D, PDF_NAME(ON), 5);
        if (!EXISTS(ON) || !PySequence_Check(ON) || !PySequence_Size(ON)) {
            ;
        } else {
            pdf_obj *ocgs = pdf_dict_get(ctx, ocp, PDF_NAME(OCGs));
            int i, n = PySequence_Size(ON);
            for (i = 0; i < n; i++) {
                int xref = 0;
                if (JM_INT_ITEM(ON, (Py_ssize_t) i, &xref) == 1) continue;
                pdf_obj *ind = pdf_new_indirect(ctx, pdf, xref, 0);
                if (pdf_array_contains(ctx, ocgs, ind)) {
                    pdf_array_push_drop(ctx, onarray, ind);
                } else {
                    pdf_drop_obj(ctx, ind);
                }
            }
        }
        pdf_array_push_drop(ctx, configs, D);
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
}


//------------------------------------------------------------------------
// Get OCG arrays from OC configuration
// Returns dict
// {"basestate":name, "on":list, "off":list, "rbg":list, "locked":list}
//------------------------------------------------------------------------
static PyObject *
JM_get_ocg_arrays_imp(fz_context *ctx, pdf_obj *arr)
{
    int i, n;
    PyObject *list = PyList_New(0), *item = NULL;
    pdf_obj *obj = NULL;
    if (pdf_is_array(ctx, arr)) {
        n = pdf_array_len(ctx, arr);
        for (i = 0; i < n; i++) {
            obj = pdf_array_get(ctx, arr, i);
            item = Py_BuildValue("i", pdf_to_num(ctx, obj));
            if (!PySequence_Contains(list, item)) {
                LIST_APPEND_DROP(list, item);
            } else {
                Py_DECREF(item);
            }
        }
    }
    return list;
}

PyObject *
JM_get_ocg_arrays(fz_context *ctx, pdf_obj *conf)
{
    PyObject *rc = PyDict_New(), *list = NULL, *list1 = NULL;
    int i, n;
    pdf_obj *arr = NULL, *obj = NULL;
    fz_try(ctx) {
        arr = pdf_dict_get(ctx, conf, PDF_NAME(ON));
        list = JM_get_ocg_arrays_imp(ctx, arr);
        if (PySequence_Size(list)) {
            PyDict_SetItemString(rc, "on", list);
        }
        Py_DECREF(list);
        arr = pdf_dict_get(ctx, conf, PDF_NAME(OFF));
        list = JM_get_ocg_arrays_imp(ctx, arr);
        if (PySequence_Size(list)) {
            PyDict_SetItemString(rc, "off", list);
        }
        Py_DECREF(list);
        arr = pdf_dict_get(ctx, conf, PDF_NAME(Locked));
        list = JM_get_ocg_arrays_imp(ctx, arr);
        if (PySequence_Size(list)) {
            PyDict_SetItemString(rc, "locked", list);
        }
        Py_DECREF(list);
        list = PyList_New(0);
        arr = pdf_dict_get(ctx, conf, PDF_NAME(RBGroups));
        if (pdf_is_array(ctx, arr)) {
            n = pdf_array_len(ctx, arr);
            for (i = 0; i < n; i++) {
                obj = pdf_array_get(ctx, arr, i);
                list1 = JM_get_ocg_arrays_imp(ctx, obj);
                LIST_APPEND_DROP(list, list1);
            }
        }
        if (PySequence_Size(list)) {
            PyDict_SetItemString(rc, "rbgroups", list);
        }
        Py_DECREF(list);
        obj = pdf_dict_get(ctx, conf, PDF_NAME(BaseState));

        if (obj) {
            PyObject *state = NULL;
            state = Py_BuildValue("s", pdf_to_name(ctx, obj));
            PyDict_SetItemString(rc, "basestate", state);
            Py_DECREF(state);
        }
    }
    fz_always(ctx) {
    }
    fz_catch(ctx) {
        Py_CLEAR(rc);
        PyErr_Clear();
        fz_rethrow(ctx);
    }
    return rc;
}


//------------------------------------------------------------------------
// Set OCG arrays from dict of Python lists
// Works with dict like {"basestate":name, "on":list, "off":list, "rbg":list}
//------------------------------------------------------------------------
static void
JM_set_ocg_arrays_imp(fz_context *ctx, pdf_obj *arr, PyObject *list)
{
    int i, n = PySequence_Size(list);
    pdf_obj *obj = NULL;
    pdf_document *pdf = pdf_get_bound_document(ctx, arr);
    for (i = 0; i < n; i++) {
        int xref = 0;
        if (JM_INT_ITEM(list, i, &xref) == 1) continue;
        obj = pdf_new_indirect(ctx, pdf, xref, 0);
        pdf_array_push_drop(ctx, arr, obj);
    }
    return;
}

static void
JM_set_ocg_arrays(fz_context *ctx, pdf_obj *conf, const char *basestate,
                  PyObject *on, PyObject *off, PyObject *rbgroups, PyObject *locked)
{
    int i, n;
    pdf_obj *arr = NULL, *obj = NULL;
    fz_try(ctx) {
        if (basestate) {
            pdf_dict_put_name(ctx, conf, PDF_NAME(BaseState), basestate);
        }

        if (on != Py_None) {
            pdf_dict_del(ctx, conf, PDF_NAME(ON));
            if (PySequence_Size(on)) {
                arr = pdf_dict_put_array(ctx, conf, PDF_NAME(ON), 1);
                JM_set_ocg_arrays_imp(ctx, arr, on);
            }
        }

        if (off != Py_None) {
            pdf_dict_del(ctx, conf, PDF_NAME(OFF));
            if (PySequence_Size(off)) {
                arr = pdf_dict_put_array(ctx, conf, PDF_NAME(OFF), 1);
                JM_set_ocg_arrays_imp(ctx, arr, off);
            }
        }

        if (locked != Py_None) {
            pdf_dict_del(ctx, conf, PDF_NAME(Locked));
            if (PySequence_Size(locked)) {
                arr = pdf_dict_put_array(ctx, conf, PDF_NAME(Locked), 1);
                JM_set_ocg_arrays_imp(ctx, arr, locked);
            }
        }

        if (rbgroups != Py_None) {
            pdf_dict_del(ctx, conf, PDF_NAME(RBGroups));
            if (PySequence_Size(rbgroups)) {
                arr = pdf_dict_put_array(ctx, conf, PDF_NAME(RBGroups), 1);
                n = PySequence_Size(rbgroups);
                for (i = 0; i < n; i++) {
                    PyObject *item0 = PySequence_ITEM(rbgroups, i);
                    obj = pdf_array_push_array(ctx, arr, 1);
                    JM_set_ocg_arrays_imp(ctx, obj, item0);
                    Py_DECREF(item0);
                }
            }
        }
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return;
}


//------------------------------------------------------------------------
// Return the items of Resources/Properties (used for Marked Content)
// Argument may be e.g. a page object or a Form XObject
//------------------------------------------------------------------------
PyObject *
JM_get_resource_properties(fz_context *ctx, pdf_obj *ref)
{
    PyObject *rc = NULL;
    fz_try(ctx) {
        pdf_obj *properties = pdf_dict_getl(ctx, ref,
                         PDF_NAME(Resources),
                         PDF_NAME(Properties), NULL);
        if (!properties) {
            rc = PyTuple_New(0);
        } else {
            int i, n = pdf_dict_len(ctx, properties);
            if (n < 1) {
                rc = PyTuple_New(0);
                goto finished;
            }
            rc = PyTuple_New(n);
            for (i = 0; i < n; i++) {
                pdf_obj *key = pdf_dict_get_key(ctx, properties, i);
                pdf_obj *val = pdf_dict_get_val(ctx, properties, i);
                const char *c = pdf_to_name(ctx, key);
                int xref = pdf_to_num(ctx, val);
                PyTuple_SET_ITEM(rc, i, Py_BuildValue("si", c, xref));
            }
        }
        finished:;
    }
    fz_catch(ctx) {
        Py_CLEAR(rc);
        fz_rethrow(ctx);
    }
    return rc;
}


//------------------------------------------------------------------------
// Insert an item into Resources/Properties (used for Marked Content)
// Arguments:
// (1) e.g. page object, Form XObject
// (2) marked content name
// (3) xref of the referenced object (insert as indirect reference)
//------------------------------------------------------------------------
void
JM_set_resource_property(fz_context *ctx, pdf_obj *ref, const char *name, int xref)
{
    pdf_obj *ind = NULL;
    pdf_obj *properties = NULL;
    pdf_document *pdf = pdf_get_bound_document(ctx, ref);
    pdf_obj *name2 = NULL;
    fz_var(ind);
    fz_var(name2);
    fz_try(ctx) {
        ind = pdf_new_indirect(ctx, pdf, xref, 0);
        if (!ind) {
            RAISEPY(ctx, MSG_BAD_XREF, PyExc_ValueError);
        }
        pdf_obj *resources = pdf_dict_get(ctx, ref, PDF_NAME(Resources));
        if (!resources) {
            resources = pdf_dict_put_dict(ctx, ref, PDF_NAME(Resources), 1);
        }
        properties = pdf_dict_get(ctx, resources, PDF_NAME(Properties));
        if (!properties) {
            properties = pdf_dict_put_dict(ctx, resources, PDF_NAME(Properties), 1);
        }
        name2 = pdf_new_name(ctx, name);
        pdf_dict_put(ctx, properties, name2, ind);
    }
    fz_always(ctx) {
        pdf_drop_obj(ctx, ind);
        pdf_drop_obj(ctx, name2);
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return;
}


//------------------------------------------------------------------------
// Add OC object reference to a dictionary
//------------------------------------------------------------------------
void
JM_add_oc_object(fz_context *ctx, pdf_document *pdf, pdf_obj *ref, int xref)
{
    pdf_obj *indobj = NULL;
    fz_try(ctx) {
        indobj = pdf_new_indirect(ctx, pdf, xref, 0);
        if (!pdf_is_dict(ctx, indobj)) {
            RAISEPY(ctx, MSG_BAD_OC_REF, PyExc_ValueError);
        }
        pdf_obj *type = pdf_dict_get(ctx, indobj, PDF_NAME(Type));
        if (pdf_objcmp(ctx, type, PDF_NAME(OCG)) == 0 ||
            pdf_objcmp(ctx, type, PDF_NAME(OCMD)) == 0) {
            pdf_dict_put(ctx, ref, PDF_NAME(OC), indobj);
        } else {
            RAISEPY(ctx, MSG_BAD_OC_REF, PyExc_ValueError);
        }
    }
    fz_always(ctx) {
        pdf_drop_obj(ctx, indobj);
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
}


//-------------------------------------------------------------------------
// Store info of a font in Python list
//-------------------------------------------------------------------------
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
        if (!basefont || pdf_is_null(ctx, basefont)) {
            name = pdf_dict_get(ctx, fontdict, PDF_NAME(Name));
        } else {
            name = basefont;
        }
        encoding = pdf_dict_get(ctx, fontdict, PDF_NAME(Encoding));
        if (pdf_is_dict(ctx, encoding)) {
            encoding = pdf_dict_get(ctx, encoding, PDF_NAME(BaseEncoding));
        }
        int xref = pdf_to_num(ctx, fontdict);
        char *ext = "n/a";
        if (xref) {
            ext = JM_get_fontextension(ctx, pdf, xref);
        }
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

//-------------------------------------------------------------------------
// Store info of an image in Python list
//-------------------------------------------------------------------------
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
        smask = pdf_dict_geta(ctx, imagedict, PDF_NAME(SMask), PDF_NAME(Mask));
        if (smask)
            gen = pdf_to_num(ctx, smask);

        filter = pdf_dict_geta(ctx, imagedict, PDF_NAME(Filter), PDF_NAME(F));
        if (pdf_is_array(ctx, filter)) {
            filter = pdf_array_get(ctx, filter, 0);
        }

        altcs = NULL;
        cs = pdf_dict_geta(ctx, imagedict, PDF_NAME(ColorSpace), PDF_NAME(CS));
        if (pdf_is_array(ctx, cs)) {
            pdf_obj *cses = cs;
            cs = pdf_array_get(ctx, cses, 0);
            if (pdf_name_eq(ctx, cs, PDF_NAME(DeviceN)) ||
                pdf_name_eq(ctx, cs, PDF_NAME(Separation))) {
                altcs = pdf_array_get(ctx, cses, 2);
                if (pdf_is_array(ctx, altcs)) {
                    altcs = pdf_array_get(ctx, altcs, 0);
                }
            }
        }

        width = pdf_dict_geta(ctx, imagedict, PDF_NAME(Width), PDF_NAME(W));
        height = pdf_dict_geta(ctx, imagedict, PDF_NAME(Height), PDF_NAME(H));
        bpc = pdf_dict_geta(ctx, imagedict, PDF_NAME(BitsPerComponent), PDF_NAME(BPC));

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

//-------------------------------------------------------------------------
// Store info of a /Form xobject in Python list
//-------------------------------------------------------------------------
int JM_gather_forms(fz_context *ctx, pdf_document *doc, pdf_obj *dict,
                     PyObject *imagelist, int stream_xref)
{
    int i, rc = 1, n = pdf_dict_len(ctx, dict);
    fz_rect bbox;
    fz_matrix mat;
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
        if (m) {
            mat = pdf_to_matrix(ctx, m);
        } else {
            mat = fz_identity;
        }
        if (o) {
            bbox = fz_transform_rect(pdf_to_rect(ctx, o), mat);
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

//-------------------------------------------------------------------------
// Step through /Resources, looking up image, xobject or font information
//-------------------------------------------------------------------------
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
