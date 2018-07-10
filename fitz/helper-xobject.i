%{
//-----------------------------------------------------------------------------
// Make an XObject from a PDF page
// For a positive xref, assume its object can be used instead
//-----------------------------------------------------------------------------
pdf_obj *JM_xobject_from_page(fz_context *ctx, pdf_document *pdfout, pdf_document *pdfsrc, int pno, fz_rect *mediabox, fz_rect *cropbox, int xref, pdf_graft_map *gmap)
{
    fz_buffer *nres = NULL, *res = NULL;
    pdf_obj *xobj1, *contents, *resources, *o, *spageref;
    int i;
    fz_try(ctx)
    {
        if (pno < 0 || pno >= pdf_count_pages(ctx, pdfsrc))
            THROWMSG("invalid page number(s)");
        spageref = pdf_lookup_page_obj(ctx, pdfsrc, pno);
        pdf_to_rect(ctx, pdf_dict_get(ctx, spageref, PDF_NAME_MediaBox), mediabox);
        o = pdf_dict_get(ctx, spageref, PDF_NAME_CropBox);
        if (!o)
            pdf_to_rect(ctx, pdf_dict_get(ctx, spageref, PDF_NAME_MediaBox), cropbox);
        else
            pdf_to_rect(ctx, o, cropbox);

        if (xref > 0)        // we can reuse an XObject!
        {
            if (xref >= pdf_xref_len(ctx, pdfout))
                THROWMSG("xref out of range");
            xobj1 = pdf_new_indirect(ctx, pdfout, xref, 0);
        }
        else                 // need to create new XObject
        {
            // Deep-copy resources object of source page
            o = pdf_dict_get(ctx, spageref, PDF_NAME_Resources);
            if (gmap)        // use graftmap when possible
                resources = pdf_graft_mapped_object(ctx, gmap, o);
            else
                resources = pdf_graft_object(ctx, pdfout, o);
            
            // get spgage contents source; combine when several objects
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
            // store spage contents
            JM_update_stream(ctx, pdfout, xobj1, res);
            fz_drop_buffer(ctx, res);

            // store spage resources
            pdf_dict_put_drop(ctx, xobj1, PDF_NAME_Resources, resources);
        }
    }
    fz_catch(ctx) fz_rethrow(ctx);
    return xobj1;
}

//-----------------------------------------------------------------------------
// Append / prepend a buffer to the /Contents of a page.
//-----------------------------------------------------------------------------
void JM_extend_contents(fz_context *ctx, pdf_document *pdfout,
                        pdf_obj *pageref, fz_buffer *newcont, int overlay)
{
    int i;
    fz_buffer *oldcont = NULL, *endcont = NULL;
    pdf_obj *contents = pdf_dict_get(ctx, pageref, PDF_NAME_Contents);
    fz_try(ctx)
    {
        if (pdf_is_array(ctx, contents))     // multiple contents objects!
        {   // choose the correct one (first / last)
            if (overlay == 1) i = pdf_array_len(ctx, contents) - 1;
            else  i = 0;
            contents = pdf_array_get(ctx, contents, i);
        }
        oldcont = pdf_load_stream(ctx, contents);     // old contents buffer

        // allocate result buffer
        endcont = fz_new_buffer(ctx, fz_buffer_storage(ctx, oldcont, NULL) +
                                     fz_buffer_storage(ctx, newcont, NULL));

        if (overlay == 1)                             // append new buffer
        {
            fz_append_buffer(ctx, endcont, oldcont);
            fz_append_buffer(ctx, endcont, newcont);
        }
        else                                          // prepend new buffer
        {
            fz_append_buffer(ctx, endcont, newcont);
            fz_append_buffer(ctx, endcont, oldcont);
        }
        fz_terminate_buffer(ctx, endcont);            // finalize result buffer
    
        // now update the content stream
        JM_update_stream(ctx, pdfout, contents, endcont);
    }
    fz_always(ctx)
    {
        fz_drop_buffer(ctx, endcont);
        fz_drop_buffer(ctx, oldcont);
    }
    fz_catch(ctx) fz_rethrow(ctx);
    return;
}

void JM_make_ap_object(fz_context *ctx, fz_annot *fzannot, fz_rect *rect, char *content)
{
    pdf_annot *annot = pdf_annot_from_fz_annot(ctx, fzannot);
    pdf_document *pdf = annot->page->doc;
    pdf_obj *xobj = pdf_new_xobject(ctx, pdf, rect, &fz_identity);
    fz_buffer *contbuffer;
    if (content)
    {
        contbuffer = fz_new_buffer_from_shared_data(ctx, content, strlen(content));
        JM_update_stream(ctx, pdf, xobj, contbuffer);
    }
    else
    {
        contbuffer = fz_new_buffer(ctx, 10);
        JM_update_stream(ctx, pdf, xobj, contbuffer);
        fz_drop_buffer(ctx, contbuffer);
    }
    pdf_dict_putl_drop(ctx, annot->obj, xobj, PDF_NAME_AP, PDF_NAME_N, NULL);
    annot->ap = NULL;
}

%}