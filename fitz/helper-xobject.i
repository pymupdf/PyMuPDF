%{
pdf_obj *xobject_from_page(fz_context *ctx, pdf_obj *spageref, pdf_document *pdfout, fz_rect *mediabox, fz_rect *cropbox)
{
    fz_buffer *nres, *res;
    pdf_obj *xobj1, *contents, *resources, *o;
    int i;
    fz_try(ctx)
    {
        pdf_to_rect(ctx, pdf_dict_get(ctx, spageref, PDF_NAME_MediaBox), mediabox);
        o = pdf_dict_get(ctx, spageref, PDF_NAME_CropBox);
        if (!o)
            pdf_to_rect(ctx, pdf_dict_get(ctx, spageref, PDF_NAME_MediaBox), cropbox);
        else
            pdf_to_rect(ctx, o, cropbox);

        // Deep-copy resources object of source page
        o = pdf_dict_get(ctx, spageref, PDF_NAME_Resources);
        resources = pdf_graft_object(ctx, pdfout, o);
        // get spgage contents source; maybe several objects
        contents = pdf_dict_get(ctx, spageref, PDF_NAME_Contents);
        if (pdf_is_array(ctx, contents))     // more than one!
        {
            res = fz_new_buffer(ctx, 1024);
            for (i=0; i < pdf_array_len(ctx, contents); i++)
            {
                nres = pdf_load_stream(ctx, pdf_array_get(ctx, contents, i));
                fz_append_buffer(ctx, res, nres);
                fz_drop_buffer(ctx, nres);
            }
        }
        else
        {
            res = pdf_load_stream(ctx, contents);
        }

        //-------------------------------------------------------------
        // create XObject representing the source page
        //-------------------------------------------------------------
        xobj1 = pdf_new_xobject(ctx, pdfout, mediabox, &fz_identity);
        pdf_xobject *xobj1x = pdf_load_xobject(ctx, pdfout, xobj1);
        // store spage contents
        pdf_update_xobject_contents(ctx, pdfout, xobj1x, res);
        fz_drop_buffer(ctx, res);

        // store spage resources
        pdf_dict_put_drop(ctx, xobj1, PDF_NAME_Resources, resources);
    }
    fz_catch(ctx)
    {
        fz_rethrow(ctx);
    }
    return xobj1;
}

pdf_obj *xobject_from_xref(fz_context *ctx, int xref, pdf_document *pdfout, fz_rect *mediabox, fz_rect *cropbox)
{
    pdf_obj *x;
    pdf_xobject *xobj1x;
    fz_try(ctx)
    {
        x = pdf_new_indirect(ctx, pdfout, xref, 0);
        xobj1x = pdf_load_xobject(ctx, pdfout, x);
        pdf_xobject_bbox(ctx, xobj1x, mediabox);
        pdf_xobject_bbox(ctx, xobj1x, cropbox);
    }
    fz_catch(ctx)
    {
        fz_rethrow(ctx);
    }
    return x;
}
%}