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
// perform some cleaning if we have /EmbeddedFiles:
// (1) remove any /Limits if /Names exists
// (2) remove any empty /Collection
// (3) set /PageMode/UseAttachments
//-----------------------------------------------------------------------------
void JM_embedded_clean(fz_context *ctx, pdf_document *pdf)
{
    pdf_obj *root = pdf_dict_get(ctx, pdf_trailer(ctx, pdf), PDF_NAME(Root));

    // remove any empty /Collection entry
    pdf_obj *coll = pdf_dict_get(ctx, root, PDF_NAME(Collection));
    if (coll && pdf_dict_len(ctx, coll) == 0)
        pdf_dict_del(ctx, root, PDF_NAME(Collection));

    pdf_obj *efiles = pdf_dict_getl(ctx, root,
                                    PDF_NAME(Names),
                                    PDF_NAME(EmbeddedFiles),
                                    PDF_NAME(Names),
                                    NULL);
    if (efiles) {
        pdf_dict_put_name(ctx, root, PDF_NAME(PageMode), "UseAttachments");
    }
    return;
}

//-----------------------------------------------------------------------------
// embed a new file in a PDF (not only /EmbeddedFiles entries)
//-----------------------------------------------------------------------------
pdf_obj *JM_embed_file(fz_context *ctx,
                       pdf_document *pdf,
                       fz_buffer *buf,
                       char *filename,
                       char *ufilename,
                       char *desc,
                       int compress)
{
    size_t len = 0;
    pdf_obj *ef, *f, *params, *val = NULL;
    fz_buffer *buff2 = NULL;
    fz_var(buff2);
    fz_try(ctx) {
        val = pdf_new_dict(ctx, pdf, 6);
        pdf_dict_put_dict(ctx, val, PDF_NAME(CI), 4);
        ef = pdf_dict_put_dict(ctx, val, PDF_NAME(EF), 4);
        pdf_dict_put_text_string(ctx, val, PDF_NAME(F), filename);
        pdf_dict_put_text_string(ctx, val, PDF_NAME(UF), ufilename);
        pdf_dict_put_text_string(ctx, val, PDF_NAME(Desc), desc);
        pdf_dict_put(ctx, val, PDF_NAME(Type), PDF_NAME(Filespec));
        buff2 = fz_new_buffer_from_copied_data(ctx, "  ", 1);
        f = pdf_add_stream(ctx, pdf, buff2, NULL, 0);
        pdf_dict_put_drop(ctx, ef, PDF_NAME(F), f);
        JM_update_stream(ctx, pdf, f, buf, compress);
        len = fz_buffer_storage(ctx, buf, NULL);
        pdf_dict_put_int(ctx, f, PDF_NAME(DL), len);
        pdf_dict_put_int(ctx, f, PDF_NAME(Length), len);
        params = pdf_dict_put_dict(ctx, f, PDF_NAME(Params), 4);
        pdf_dict_put_int(ctx, params, PDF_NAME(Size), len);
    }
    fz_always(ctx) {
        fz_drop_buffer(ctx, buff2);
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return val;
}
%}
