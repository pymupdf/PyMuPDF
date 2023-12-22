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
// Read and concatenate a PDF page's /Conents object(s) in a buffer
//-----------------------------------------------------------------------------
fz_buffer *JM_read_contents(fz_context * ctx, pdf_obj * pageref)
{
    fz_buffer *res = NULL, *nres = NULL;
    int i;
    fz_try(ctx) {
        pdf_obj *contents = pdf_dict_get(ctx, pageref, PDF_NAME(Contents));
        if (pdf_is_array(ctx, contents)) {
            res = fz_new_buffer(ctx, 1024);
            for (i = 0; i < pdf_array_len(ctx, contents); i++) {
                nres = pdf_load_stream(ctx, pdf_array_get(ctx, contents, i));
                fz_append_buffer(ctx, res, nres);
                fz_drop_buffer(ctx, nres);
            }
        }
        else if (contents) {
            res = pdf_load_stream(ctx, contents);
        }
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return res;
}

//-----------------------------------------------------------------------------
// Make an XObject from a PDF page
// For a positive xref assume that its object can be used instead
//-----------------------------------------------------------------------------
pdf_obj *JM_xobject_from_page(fz_context * ctx, pdf_document * pdfout, fz_page * fsrcpage, int xref, pdf_graft_map *gmap)
{
    pdf_obj *xobj1, *resources = NULL, *o, *spageref;
    fz_try(ctx) {
        if (xref > 0) {
            xobj1 = pdf_new_indirect(ctx, pdfout, xref, 0);
        } else {
            fz_buffer *res = NULL;
            fz_rect mediabox;
            pdf_page *srcpage = pdf_page_from_fz_page(ctx, fsrcpage);
            spageref = srcpage->obj;
            mediabox = pdf_to_rect(ctx, pdf_dict_get_inheritable(ctx, spageref, PDF_NAME(MediaBox)));
            // Deep-copy resources object of source page
            o = pdf_dict_get_inheritable(ctx, spageref, PDF_NAME(Resources));
            if (gmap) // use graftmap when possible
                resources = pdf_graft_mapped_object(ctx, gmap, o);
            else
                resources = pdf_graft_object(ctx, pdfout, o);

            // get spgage contents source
            res = JM_read_contents(ctx, spageref);

            //-------------------------------------------------------------
            // create XObject representing the source page
            //-------------------------------------------------------------
            xobj1 = pdf_new_xobject(ctx, pdfout, mediabox, fz_identity, NULL, res);
            // store spage contents
            JM_update_stream(ctx, pdfout, xobj1, res, 1);
            fz_drop_buffer(ctx, res);

            // store spage resources
            pdf_dict_put_drop(ctx, xobj1, PDF_NAME(Resources), resources);
        }
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return xobj1;
}

//-----------------------------------------------------------------------------
// Insert a buffer as a new separate /Contents object of a page.
// 1. Create a new stream object from buffer 'newcont'
// 2. If /Contents already is an array, then just prepend or append this object
// 3. Else, create new array and put old content obj and this object into it.
//    If the page had no /Contents before, just create a 1-item array.
//-----------------------------------------------------------------------------
int JM_insert_contents(fz_context * ctx, pdf_document * pdf,
                        pdf_obj * pageref, fz_buffer * newcont, int overlay)
{
    int xref = 0;
    pdf_obj *newconts = NULL;
    pdf_obj *carr = NULL;
    fz_var(newconts);
    fz_var(carr);
    fz_try(ctx) {
        pdf_obj *contents = pdf_dict_get(ctx, pageref, PDF_NAME(Contents));
        newconts = pdf_add_stream(ctx, pdf, newcont, NULL, 0);
        xref = pdf_to_num(ctx, newconts);
        if (pdf_is_array(ctx, contents)) {
            if (overlay) // append new object
                pdf_array_push(ctx, contents, newconts);
            else // prepend new object
                pdf_array_insert(ctx, contents, newconts, 0);
        } else {
            carr = pdf_new_array(ctx, pdf, 5);
            if (overlay) {
                if (contents)
                    pdf_array_push(ctx, carr, contents);
                pdf_array_push(ctx, carr, newconts);
            } else {
                pdf_array_push(ctx, carr, newconts);
                if (contents)
                    pdf_array_push(ctx, carr, contents);
            }
            pdf_dict_put(ctx, pageref, PDF_NAME(Contents), carr);
        }
    }
    fz_always(ctx) {
        pdf_drop_obj(ctx, newconts);
        pdf_drop_obj(ctx, carr);
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return xref;
}

static void show(const char* prefix, PyObject* obj)
{
    if (!obj)
    {
        printf( "%s <null>\n", prefix);
        return;
    }
    PyObject* obj_repr = PyObject_Repr( obj);
    PyObject* obj_repr_u = PyUnicode_AsEncodedString( obj_repr, "utf-8", "~E~");
    const char* obj_repr_s = PyString_AsString( obj_repr_u);
    printf( "%s%s\n", prefix, obj_repr_s);
    fflush(stdout);
}

static PyObject *g_img_info = NULL;
static fz_matrix g_img_info_matrix = {0};

static fz_image *
JM_image_filter(fz_context *ctx, void *opaque, fz_matrix ctm, const char *name, fz_image *image)
{
    fz_quad q = fz_transform_quad(fz_quad_from_rect(fz_unit_rect), ctm);
    #if FZ_VERSION_MAJOR == 1 && FZ_VERSION_MINOR >= 22
    q = fz_transform_quad( q, g_img_info_matrix);
    #endif
    PyObject *temp = Py_BuildValue("sN", name, JM_py_from_quad(q));
    
    LIST_APPEND_DROP(g_img_info, temp);
    return image;
}

#if FZ_VERSION_MAJOR == 1 && FZ_VERSION_MINOR >= 22

static PyObject *
JM_image_reporter(fz_context *ctx, pdf_page *page)
{
    pdf_document *doc = page->doc;
    
    pdf_page_transform(ctx, page, NULL, &g_img_info_matrix);
    pdf_filter_options filter_options = {0};
    filter_options.recurse = 0;
    filter_options.instance_forms = 1;
    filter_options.ascii = 1;
    filter_options.no_update = 1;
    
    pdf_sanitize_filter_options sanitize_filter_options = {0};
    sanitize_filter_options.opaque = page;
    sanitize_filter_options.image_filter = JM_image_filter;
    
    pdf_filter_factory filter_factory[2] = {0};
    filter_factory[0].filter = pdf_new_sanitize_filter;
    filter_factory[0].options = &sanitize_filter_options;
    
    filter_options.filters = filter_factory; // was &
    
    g_img_info = PyList_New(0);
    
    pdf_filter_page_contents(ctx, doc, page, &filter_options);
    
    PyObject *rc = PySequence_Tuple(g_img_info);
    Py_CLEAR(g_img_info);
    
    return rc;
}

#else

void
JM_filter_content_stream(
    fz_context * ctx,
    pdf_document * doc,
    pdf_obj * in_stm,
    pdf_obj * in_res,
    fz_matrix transform,
    pdf_filter_options * filter,
    int struct_parents,
    fz_buffer **out_buf,
    pdf_obj **out_res)
{
    pdf_processor *proc_buffer = NULL;
    pdf_processor *proc_filter = NULL;

    fz_var(proc_buffer);
    fz_var(proc_filter);

    *out_buf = NULL;
    *out_res = NULL;

    fz_try(ctx) {
		*out_buf = fz_new_buffer(ctx, 1024);
		proc_buffer = pdf_new_buffer_processor(ctx, *out_buf, filter->ascii);
		if (filter->sanitize) {
			*out_res = pdf_new_dict(ctx, doc, 1);
			proc_filter = pdf_new_filter_processor(ctx, doc, proc_buffer, in_res, *out_res, struct_parents, transform, filter);
			pdf_process_contents(ctx, proc_filter, doc, in_res, in_stm, NULL);
			pdf_close_processor(ctx, proc_filter);
		} else {
			*out_res = pdf_keep_obj(ctx, in_res);
			pdf_process_contents(ctx, proc_buffer, doc, in_res, in_stm, NULL);
		}
		pdf_close_processor(ctx, proc_buffer);
    }
    fz_always(ctx) {
        pdf_drop_processor(ctx, proc_filter);
        pdf_drop_processor(ctx, proc_buffer);
    }
    fz_catch(ctx) {
        fz_drop_buffer(ctx, *out_buf);
        *out_buf = NULL;
        pdf_drop_obj(ctx, *out_res);
        *out_res = NULL;
        fz_rethrow(ctx);
    }
}

PyObject *
JM_image_reporter(fz_context *ctx, pdf_page *page)
{
    pdf_document *doc = page->doc;
    pdf_filter_options filter;
    memset(&filter, 0, sizeof filter);
    filter.opaque = page;
    filter.text_filter = NULL;
    filter.image_filter = JM_image_filter;
    filter.end_page = NULL;
    filter.recurse = 0;
    filter.instance_forms = 1;
    filter.sanitize = 1;
    filter.ascii = 1;

    pdf_obj *contents, *old_res;
    pdf_obj *struct_parents_obj;
    pdf_obj *new_res;
    fz_buffer *buffer;
    int struct_parents;
    fz_matrix ctm = fz_identity;
    pdf_page_transform(ctx, page, NULL, &ctm);
    struct_parents_obj = pdf_dict_get(ctx, page->obj, PDF_NAME(StructParents));
    struct_parents = -1;
    if (pdf_is_number(ctx, struct_parents_obj))
        struct_parents = pdf_to_int(ctx, struct_parents_obj);

    contents = pdf_page_contents(ctx, page);
    old_res = pdf_page_resources(ctx, page);
    g_img_info = PyList_New(0);
    JM_filter_content_stream(ctx, doc, contents, old_res, ctm, &filter, struct_parents, &buffer, &new_res);
    fz_drop_buffer(ctx, buffer);
    pdf_drop_obj(ctx, new_res);
    PyObject *rc = PySequence_Tuple(g_img_info);
    Py_CLEAR(g_img_info);
    return rc;
}

#endif

%}
