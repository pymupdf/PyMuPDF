%{
void JM_update_xobject_contents(fz_context *ctx, pdf_document *doc, pdf_xobject *form, fz_buffer *buffer)
{   // version of "pdf_update_xobject_contents" with compression
	size_t c_len;
    char *content_str;
    fz_buffer *nres;
    c_len = (size_t) fz_buffer_storage(ctx, buffer, &content_str);
    pdf_dict_put(ctx, form->obj, PDF_NAME_Filter, PDF_NAME_FlateDecode);
    nres = deflatebuf(ctx, content_str, c_len);
    pdf_update_stream(ctx, doc, form->obj, nres, 1);
    fz_drop_buffer(ctx, nres);
	form->iteration ++;
}

pdf_obj *JM_xobject_from_page(fz_context *ctx, pdf_document *pdfout, pdf_document *pdfsrc, int pno, fz_rect *mediabox, fz_rect *cropbox, int xref, pdf_graft_map *gmap)
{
    fz_buffer *nres, *res;
    pdf_obj *xobj1, *contents, *resources, *o, *spageref;
    pdf_xobject *xobj1x;
    int i;
    fz_try(ctx)
    {
        if (pno < 0 || pno >= pdf_count_pages(ctx, pdfsrc))
            fz_throw(ctx, FZ_ERROR_GENERIC, "invalid page number(s)");
        spageref = pdf_lookup_page_obj(ctx, pdfsrc, pno);
        pdf_to_rect(ctx, pdf_dict_get(ctx, spageref, PDF_NAME_MediaBox), mediabox);
        o = pdf_dict_get(ctx, spageref, PDF_NAME_CropBox);
        if (!o)
            pdf_to_rect(ctx, pdf_dict_get(ctx, spageref, PDF_NAME_MediaBox), cropbox);
        else
            pdf_to_rect(ctx, o, cropbox);

        if (xref > 0)
        {
            if (xref >= pdf_xref_len(ctx, pdfout))
                fz_throw(ctx, FZ_ERROR_GENERIC, "xref out of range");
            xobj1 = pdf_new_indirect(ctx, pdfout, xref, 0);
            xobj1x = pdf_load_xobject(ctx, pdfout, xobj1);
        }
        else
        {
            // Deep-copy resources object of source page
            o = pdf_dict_get(ctx, spageref, PDF_NAME_Resources);
            if (gmap)
            {
                resources = pdf_graft_mapped_object(ctx, gmap, o);
            }
            else
            {
                resources = pdf_graft_object(ctx, pdfout, o);
            }
            
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
            xobj1x = pdf_load_xobject(ctx, pdfout, xobj1);
            // store spage contents
            JM_update_xobject_contents(ctx, pdfout, xobj1x, res);
            fz_drop_buffer(ctx, res);

            // store spage resources
            pdf_dict_put_drop(ctx, xobj1, PDF_NAME_Resources, resources);
        }
    }
    fz_catch(ctx) fz_rethrow(ctx);
    return xobj1;
}

void JM_extend_contents(fz_context *ctx, pdf_document *pdfout, pdf_obj *pageref, fz_buffer *nres, int overlay)
{
    int i;
    fz_buffer *res;
    char *content_str;
    size_t c_len = 0;
    pdf_obj *contents = pdf_dict_get(ctx, pageref, PDF_NAME_Contents);
    fz_try(ctx)
    {
        if (pdf_is_array(ctx, contents))     // multiple contents obj
        {   // choose the correct one (1st or last)
            if (overlay == 1) i = pdf_array_len(ctx, contents) - 1;
            else  i = 0;
            contents = pdf_array_get(ctx, contents, i);
        }
        res = pdf_load_stream(ctx, contents); // old contents buffer

        if (overlay == 1)         // append our command
        {
            fz_append_buffer(ctx, res, nres);
            fz_drop_buffer(ctx, nres);
        }
        else                      // prepend our command
        {
            fz_append_buffer(ctx, nres, res);
            fz_drop_buffer(ctx, res);
            res = nres;
        }
        fz_terminate_buffer(ctx, res);
    
        // now compress and put back contents stream
        pdf_dict_put(ctx, contents, PDF_NAME_Filter, PDF_NAME_FlateDecode);
        c_len = (size_t) fz_buffer_storage(ctx, res, &content_str);
        nres = deflatebuf(ctx, content_str, c_len);
        pdf_update_stream(ctx, pdfout, contents, nres, 1);
        fz_drop_buffer(ctx, res);
        fz_drop_buffer(ctx, nres);
    }
    fz_catch(ctx) fz_rethrow(ctx);
    return;
}
%}