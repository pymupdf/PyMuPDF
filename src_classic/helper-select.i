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
