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
//----------------------------------------------------------------------------
// Helpers for document page selection - main logic was imported
// from pdf_clean_file.c. But instead of analyzing a string-based spec of
// selected pages, we accept a Python sequence.
//----------------------------------------------------------------------------
typedef struct globals_s
{
    pdf_document *doc;
    fz_context *ctx;
} globals;

int string_in_names_list(fz_context *ctx, pdf_obj *p, pdf_obj *names_list)
{
    int n = pdf_array_len(ctx, names_list);
    int i;
    const char *str = pdf_to_text_string(ctx, p);

    for (i = 0; i < n ; i += 2)
    {
        if (!strcmp(pdf_to_text_string(ctx, pdf_array_get(ctx, names_list, i)), str))
            return 1;
    }
    return 0;
}

//----------------------------------------------------------------------------
// Recreate page tree to only retain specified pages.
//----------------------------------------------------------------------------
void retainpage(fz_context *ctx, pdf_document *doc, pdf_obj *parent, pdf_obj *kids, int page)
{
    pdf_obj *pageref = pdf_lookup_page_obj(ctx, doc, page);

    pdf_flatten_inheritable_page_items(ctx, pageref);

    pdf_dict_put(ctx, pageref, PDF_NAME(Parent), parent);

    /* Store page object in new kids array */
    pdf_array_push(ctx, kids, pageref);
}

int dest_is_valid_page(fz_context *ctx, pdf_obj *obj, int *page_object_nums, int pagecount)
{
    int i;
    int num = pdf_to_num(ctx, obj);

    if (num == 0)
        return 0;
    for (i = 0; i < pagecount; i++)
    {
        if (page_object_nums[i] == num)
            return 1;
    }
    return 0;
}

int dest_is_valid(fz_context *ctx, pdf_obj *o, int page_count, int *page_object_nums, pdf_obj *names_list)
{
    pdf_obj *p;

    p = pdf_dict_get(ctx, o, PDF_NAME(A));
    if (pdf_name_eq(ctx, pdf_dict_get(ctx, p, PDF_NAME(S)), PDF_NAME(GoTo)) &&
        !string_in_names_list(ctx, pdf_dict_get(ctx, p, PDF_NAME(D)), names_list))
        return 0;

    p = pdf_dict_get(ctx, o, PDF_NAME(Dest));
    if (p == NULL)
    {}
    else if (pdf_is_string(ctx, p))
    {
        return string_in_names_list(ctx, p, names_list);
    }
    else if (!dest_is_valid_page(ctx, pdf_array_get(ctx, p, 0), page_object_nums, page_count))
        return 0;

    return 1;
}

int strip_outlines(fz_context *ctx, pdf_document *doc, pdf_obj *outlines, int page_count, int *page_object_nums, pdf_obj *names_list);

int strip_outline(fz_context *ctx, pdf_document *doc, pdf_obj *outlines, int page_count, int *page_object_nums, pdf_obj *names_list, pdf_obj **pfirst, pdf_obj **plast)
{
    pdf_obj *prev = NULL;
    pdf_obj *first = NULL;
    pdf_obj *current;
    int count = 0;

    for (current = outlines; current != NULL; )
    {
        int nc;

        /*********************************************************************/
        // Strip any children to start with. This takes care of
        // First / Last / Count for us.
        /*********************************************************************/
        nc = strip_outlines(ctx, doc, current, page_count, page_object_nums, names_list);

        if (!dest_is_valid(ctx, current, page_count, page_object_nums, names_list))
        {
            if (nc == 0)
            {
                /*************************************************************/
                // Outline with invalid dest and no children. Drop it by
                // pulling the next one in here.
                /*************************************************************/
                pdf_obj *next = pdf_dict_get(ctx, current, PDF_NAME(Next));
                if (next == NULL)
                {
                    // There is no next one to pull in
                    if (prev != NULL)
                        pdf_dict_del(ctx, prev, PDF_NAME(Next));
                }
                else if (prev != NULL)
                {
                    pdf_dict_put(ctx, prev, PDF_NAME(Next), next);
                    pdf_dict_put(ctx, next, PDF_NAME(Prev), prev);
                }
                else
                {
                    pdf_dict_del(ctx, next, PDF_NAME(Prev));
                }
                current = next;
            }
            else
            {
                // Outline with invalid dest, but children. Just drop the dest.
                pdf_dict_del(ctx, current, PDF_NAME(Dest));
                pdf_dict_del(ctx, current, PDF_NAME(A));
                current = pdf_dict_get(ctx, current, PDF_NAME(Next));
            }
        }
        else
        {
            // Keep this one
            if (first == NULL)
                first = current;
            prev = current;
            current = pdf_dict_get(ctx, current, PDF_NAME(Next));
            count++;
        }
    }

    *pfirst = first;
    *plast = prev;

    return count;
}

int strip_outlines(fz_context *ctx, pdf_document *doc, pdf_obj *outlines, int page_count, int *page_object_nums, pdf_obj *names_list)
{
    int nc;
    pdf_obj *first;
    pdf_obj *last;

    if (outlines == NULL)
        return 0;

    first = pdf_dict_get(ctx, outlines, PDF_NAME(First));
    if (first == NULL)
        nc = 0;
    else
        nc = strip_outline(ctx, doc, first, page_count, page_object_nums,
                           names_list, &first, &last);

    if (nc == 0)
    {
        pdf_dict_del(ctx, outlines, PDF_NAME(First));
        pdf_dict_del(ctx, outlines, PDF_NAME(Last));
        pdf_dict_del(ctx, outlines, PDF_NAME(Count));
    }
    else
    {
        int old_count = pdf_to_int(ctx, pdf_dict_get(ctx, outlines, PDF_NAME(Count)));
        pdf_dict_put(ctx, outlines, PDF_NAME(First), first);
        pdf_dict_put(ctx, outlines, PDF_NAME(Last), last);
        pdf_dict_put_drop(ctx, outlines, PDF_NAME(Count), pdf_new_int(ctx, old_count > 0 ? nc : -nc));
    }
    return nc;
}

//----------------------------------------------------------------------------
//   This is called by PyMuPDF:
//   liste = page numbers to retain
//----------------------------------------------------------------------------
void retainpages(fz_context *ctx, globals *glo, PyObject *liste)
{
    pdf_obj *oldroot, *root, *pages, *kids, *countobj, *olddests;
    Py_ssize_t argc = PySequence_Size(liste);
    pdf_document *doc = glo->doc;
    pdf_obj *names_list = NULL;
    pdf_obj *outlines;
    pdf_obj *ocproperties;
    int pagecount = pdf_count_pages(ctx, doc);

    int i;
    int *page_object_nums;

/******************************************************************************/
//    Keep only pages/type and (reduced) dest entries to avoid
//    references to dropped pages
/******************************************************************************/
    oldroot = pdf_dict_get(ctx, pdf_trailer(ctx, doc), PDF_NAME(Root));
    pages = pdf_dict_get(ctx, oldroot, PDF_NAME(Pages));
    olddests = pdf_load_name_tree(ctx, doc, PDF_NAME(Dests));
    outlines = pdf_dict_get(ctx, oldroot, PDF_NAME(Outlines));
    ocproperties = pdf_dict_get(ctx, oldroot, PDF_NAME(OCProperties));

    root = pdf_new_dict(ctx, doc, 3);
    pdf_dict_put(ctx, root, PDF_NAME(Type), pdf_dict_get(ctx, oldroot, PDF_NAME(Type)));
    pdf_dict_put(ctx, root, PDF_NAME(Pages), pdf_dict_get(ctx, oldroot, PDF_NAME(Pages)));
    if (outlines)
        pdf_dict_put(ctx, root, PDF_NAME(Outlines), outlines);
    if (ocproperties)
        pdf_dict_put(ctx, root, PDF_NAME(OCProperties), ocproperties);

    pdf_update_object(ctx, doc, pdf_to_num(ctx, oldroot), root);

    // Create a new kids array with only the pages we want to keep
    kids = pdf_new_array(ctx, doc, 1);

    // Retain pages specified
    Py_ssize_t page;
    fz_try(ctx) {
        for (page = 0; page < argc; page++) {
            i = (int) PyInt_AsLong(PySequence_ITEM(liste, page));
            if (i < 0 || i >= pagecount) {
                RAISEPY(ctx, MSG_BAD_PAGENO, PyExc_ValueError);
            }
            retainpage(ctx, doc, pages, kids, i);
        }
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }

    // Update page count and kids array
    countobj = pdf_new_int(ctx, pdf_array_len(ctx, kids));
    pdf_dict_put_drop(ctx, pages, PDF_NAME(Count), countobj);
    pdf_dict_put_drop(ctx, pages, PDF_NAME(Kids), kids);

    pagecount = pdf_count_pages(ctx, doc);
    page_object_nums = fz_calloc(ctx, pagecount, sizeof(*page_object_nums));
    for (i = 0; i < pagecount; i++)
    {
        pdf_obj *pageref = pdf_lookup_page_obj(ctx, doc, i);
        page_object_nums[i] = pdf_to_num(ctx, pageref);
    }

/******************************************************************************/
// If we had an old Dests tree (now reformed as an olddests dictionary),
// keep any entries in there that point to valid pages.
// This may mean we keep more than we need, but it is safe at least.
/******************************************************************************/
    if (olddests)
    {
        pdf_obj *names = pdf_new_dict(ctx, doc, 1);
        pdf_obj *dests = pdf_new_dict(ctx, doc, 1);
        int len = pdf_dict_len(ctx, olddests);

        names_list = pdf_new_array(ctx, doc, 32);

        for (i = 0; i < len; i++)
        {
            pdf_obj *key = pdf_dict_get_key(ctx, olddests, i);
            pdf_obj *val = pdf_dict_get_val(ctx, olddests, i);
            pdf_obj *dest = pdf_dict_get(ctx, val, PDF_NAME(D));

            dest = pdf_array_get(ctx, dest ? dest : val, 0);
            if (dest_is_valid_page(ctx, dest, page_object_nums, pagecount))
            {
                pdf_obj *key_str = pdf_new_string(ctx, pdf_to_name(ctx, key), strlen(pdf_to_name(ctx, key)));
                pdf_array_push_drop(ctx, names_list, key_str);
                pdf_array_push(ctx, names_list, val);
            }
        }

        pdf_dict_put(ctx, dests, PDF_NAME(Names), names_list);
        pdf_dict_put(ctx, names, PDF_NAME(Dests), dests);
        pdf_dict_put(ctx, root, PDF_NAME(Names), names);

        pdf_drop_obj(ctx, names);
        pdf_drop_obj(ctx, dests);
        pdf_drop_obj(ctx, olddests);
    }

/*****************************************************************************/
// Edit each pages /Annot list to remove any links pointing to nowhere.
/*****************************************************************************/
    for (i = 0; i < pagecount; i++)
    {
        pdf_obj *pageref = pdf_lookup_page_obj(ctx, doc, i);

        pdf_obj *annots = pdf_dict_get(ctx, pageref, PDF_NAME(Annots));

        int len = pdf_array_len(ctx, annots);
        int j;

        for (j = 0; j < len; j++)
        {
            pdf_obj *o = pdf_array_get(ctx, annots, j);

            if (!pdf_name_eq(ctx, pdf_dict_get(ctx, o, PDF_NAME(Subtype)), PDF_NAME(Link)))
                continue;

            if (!dest_is_valid(ctx, o, pagecount, page_object_nums, names_list))
            {
                // Remove this annotation
                pdf_array_delete(ctx, annots, j);
                len--;
                j--;
            }
        }
    }

    if (strip_outlines(ctx, doc, outlines, pagecount, page_object_nums, names_list) == 0)
    {
        pdf_dict_del(ctx, root, PDF_NAME(Outlines));
    }

    fz_free(ctx, page_object_nums);
    pdf_drop_obj(ctx, names_list);
    pdf_drop_obj(ctx, root);
}

void remove_dest_range(fz_context *ctx, pdf_document *pdf, PyObject *numbers)
{
    fz_try(ctx) {
        int i, j, pno, len, pagecount = pdf_count_pages(ctx, pdf);
        PyObject *n1 = NULL;
        pdf_obj *target, *annots, *pageref, *o, *action, *dest;
        for (i = 0; i < pagecount; i++) {
            n1 = PyLong_FromLong((long) i);
            if (PySet_Contains(numbers, n1)) {
                Py_DECREF(n1);
                continue;
            }
            Py_DECREF(n1);

            pageref = pdf_lookup_page_obj(ctx, pdf, i);
            annots = pdf_dict_get(ctx, pageref, PDF_NAME(Annots));
            if (!annots) continue;
            len = pdf_array_len(ctx, annots);
            for (j = len - 1; j >= 0; j -= 1) {
                o = pdf_array_get(ctx, annots, j);
                if (!pdf_name_eq(ctx, pdf_dict_get(ctx, o, PDF_NAME(Subtype)), PDF_NAME(Link))) {
                    continue;
                }
                action = pdf_dict_get(ctx, o, PDF_NAME(A));
                dest =  pdf_dict_get(ctx, o, PDF_NAME(Dest));
                if (action) {
                    if (!pdf_name_eq(ctx, pdf_dict_get(ctx, action,
                        PDF_NAME(S)), PDF_NAME(GoTo)))
                        continue;
                    dest = pdf_dict_get(ctx, action, PDF_NAME(D));
                }
                pno = -1;
                if (pdf_is_array(ctx, dest)) {
                    target = pdf_array_get(ctx, dest, 0);
                    pno = pdf_lookup_page_number(ctx, pdf, target);
                }
                else if (pdf_is_string(ctx, dest)) {
                    fz_location location = fz_resolve_link(ctx, &pdf->super,
                                            pdf_to_text_string(ctx, dest),
                                            NULL, NULL);
                    pno = location.page;
                }
                if (pno < 0) { // page number lookup did not work
                    continue;
                }
                n1 = PyLong_FromLong((long) pno);
                if (PySet_Contains(numbers, n1)) {
                    pdf_array_delete(ctx, annots, j);
                }
                Py_DECREF(n1);
            }
        }
    }

    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return;
}
%}
