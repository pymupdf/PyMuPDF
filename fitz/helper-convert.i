%{
//-----------------------------------------------------------------------------
// Convert any MuPDF document to a PDF
// Returns bytes object containing the PDF, created via 'write' function.
//-----------------------------------------------------------------------------
PyObject *JM_convert_to_pdf(fz_context *ctx, fz_document *doc, int fp, int tp, int rotate)
{
    pdf_document *pdfout = pdf_create_document(ctx);  // new PDF document
    int i, incr = 1, s = fp, e = tp;
    if (fp > tp)             // revert page sequence
    {
        incr = -1;           // count backwards
        s = tp;              // adjust ...
        e = fp;              // ... range
    }
    fz_rect mediabox;
    fz_device *dev = NULL;
    fz_buffer *contents = NULL;
    pdf_obj *resources = NULL;
    fz_page *page;
    fz_var(dev);
    fz_var(contents);
    fz_var(resources);
    fz_var(page);
    for (i = fp; INRANGE(i, s, e); i += incr)
    {   // interpret & write document pages as PDF pages
        fz_try(ctx)
        {
            page = fz_load_page(ctx, doc, i);
            mediabox = fz_bound_page(ctx, page);
            dev = pdf_page_write(ctx, pdfout, mediabox, &resources, &contents);
            fz_run_page(ctx, page, dev, fz_identity, NULL);
            fz_close_device(ctx, dev);
            fz_drop_device(ctx, dev);
            dev = NULL;
            pdf_obj *page_obj = pdf_add_page(ctx, pdfout, mediabox, rotate, resources, contents);
            pdf_insert_page(ctx, pdfout, -1, page_obj);
            pdf_drop_obj(ctx, page_obj);
        }
        fz_always(ctx)
        {
            pdf_drop_obj(ctx, resources);
            fz_drop_buffer(ctx, contents);
            fz_drop_device(ctx, dev);
        }
        fz_catch(ctx)
        {
            fz_drop_page(ctx, page);
            fz_rethrow(ctx);
        }
    }
    // PDF created - now write it to Python bytes
    PyObject *r;
    fz_buffer *res = NULL;
    fz_output *out = NULL;
    // prepare write options structure
    int errors = 0;
    pdf_write_options opts = { 0 };
    opts.do_garbage         = 4;
    opts.do_compress        = 1;
    opts.do_compress_images = 1;
    opts.do_compress_fonts  = 1;
    opts.do_sanitize        = 1;
    opts.do_incremental     = 0;
    opts.do_ascii           = 0;
    opts.do_decompress      = 0;
    opts.do_linear          = 0;
    opts.do_clean           = 1;
    opts.do_pretty          = 0;
    opts.continue_on_error  = 1;
    opts.errors = &errors;
    fz_try(ctx)
    {
        res = fz_new_buffer(ctx, 1024);
        out = fz_new_output_with_buffer(ctx, res);
        pdf_write_document(ctx, pdfout, out, &opts);
        r = JM_BinFromBuffer(ctx, res);
    }
    fz_always(ctx)
    {
        fz_drop_output(ctx, out);
        fz_drop_buffer(ctx, res);
    }
    fz_catch(ctx) fz_rethrow(ctx);
    return r;
}
%}