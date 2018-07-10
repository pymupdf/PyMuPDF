%{
//----------------------------------------------------------------------------
// portfolio schema types
//----------------------------------------------------------------------------
#define PDF_SCHEMA_NUMBER 0
#define PDF_SCHEMA_SIZE 1
#define PDF_SCHEMA_TEXT 2
#define PDF_SCHEMA_DATE 3
#define PDF_SCHEMA_DESC 4
#define PDF_SCHEMA_MODDATE 5
#define PDF_SCHEMA_CREATIONDATE 6
#define PDF_SCHEMA_FILENAME 7
#define PDF_SCHEMA_UNKNOWN 8
//-----------------------------------------------------------------------------
// finds index of an embedded file in a pdf
// Object "id" contains either the entry name (str) or the index. An index is
// only checked for valid range.
//-----------------------------------------------------------------------------
int JM_find_embedded(fz_context *ctx, PyObject *id, pdf_document *pdf)
{
    char *name = NULL;
    char *tname= NULL;
    int i = -1, count = pdf_count_portfolio_entries(ctx, pdf);
    if (count < 1) return -1;

    // just return the integer id if in range
    if (PyInt_Check(id))
    {
        i = (int) PyInt_AsLong(id);
        if (!INRANGE(i, 0, (count-1))) return -1;
        return i;
    }
    name = JM_Python_str_AsChar(id);
    if (!name || strlen(name) == 0) return -1;
    for (i = 0; i < count; i++)
    {
        tname = pdf_to_utf8(ctx, pdf_portfolio_entry_name(ctx, pdf, i));
        if (!strcmp(tname, name))
        {
            JM_Python_str_DelForPy3(name);
            return i;
        }
    }
    JM_Python_str_DelForPy3(name);
    return -1;
}

//-----------------------------------------------------------------------------
// Return the /Names object for embedded files
//-----------------------------------------------------------------------------
pdf_obj *JM_embedded_names(fz_context *ctx, pdf_document *pdf)
{
    pdf_obj *names = NULL, *kids = NULL, *o = NULL;
    int i, n;
    names = pdf_dict_getl(ctx, pdf_trailer(ctx, pdf), PDF_NAME_Root,                                         PDF_NAME_Names, PDF_NAME_EmbeddedFiles,
                         PDF_NAME_Names, NULL);
    if (names) return names;
    
    // not found, therefore a /Kids object contains the /Names
    kids = pdf_dict_getl(ctx, pdf_trailer(ctx, pdf), PDF_NAME_Root,
                         PDF_NAME_Names, PDF_NAME_EmbeddedFiles,
                        PDF_NAME_Kids, NULL);
    //-------------------------------------------------------------------------
    // 'kids' is an array of indirect references pointing to dictionaries.
    // Only /Limits and /Names can occur in those dictionaries
    // We take the first encounter of /Names.
    //-------------------------------------------------------------------------
    if (!pdf_is_array(ctx, kids) || !(n = pdf_array_len(ctx, kids)))
        return NULL;         // should never occur

    for (i = 0; i < n; i++)
    {
        o = pdf_resolve_indirect(ctx, pdf_array_get(ctx, kids, i));
        names = pdf_dict_get(ctx, o, PDF_NAME_Names);
        if (names) return names;
    }
    return NULL;             // should never execute
}

//-----------------------------------------------------------------------------
// perform some cleaning if we have /EmbeddedFiles:
// (1) remove any /Limits if /Names exists
// (2) remove any empty /Collection
// (3) set /PageMode/UseAttachments
//-----------------------------------------------------------------------------
void JM_embedded_clean(fz_context *ctx, pdf_document *pdf)
{
    pdf_obj *root = pdf_dict_get(ctx, pdf_trailer(ctx, pdf), PDF_NAME_Root);

    // remove any empty /Collection entry
    pdf_obj *coll = pdf_dict_get(ctx, root, PDF_NAME_Collection);
    if (coll && pdf_dict_len(ctx, coll) == 0)
        pdf_dict_del(ctx, root, PDF_NAME_Collection);
    
    if (!pdf_count_portfolio_entries(ctx, pdf))
        return;

    pdf_obj *efiles = pdf_dict_getl(ctx, root, PDF_NAME_Names,
                                    PDF_NAME_EmbeddedFiles, NULL);
    if (efiles)         // we have embedded files
    {   // make sure they are displayed
        pdf_dict_put_name(ctx, root, PDF_NAME_PageMode, "UseAttachments");
        // remove the limits entry: seems to be a MuPDF bug
        pdf_dict_del(ctx, efiles, PDF_NAME_Limits);
    }

    return;
}

//-----------------------------------------------------------------------------
// insert new embedded file in PDF
// not necessarily an /EmbeddedFiles entry
//-----------------------------------------------------------------------------
pdf_obj *JM_embed_file(fz_context *ctx, pdf_document *pdf, fz_buffer *buf,
                       char *filename, char *ufilename, char *desc)
{
    size_t len = 0;
    pdf_obj *ef, *f, *params;
    pdf_obj *val = NULL;
    fz_buffer *tbuf;
    fz_var(val);
    fz_try(ctx)
    {
        val = pdf_new_dict(ctx, pdf, 6);
        pdf_dict_put_dict(ctx, val, PDF_NAME_CI, 4);
        ef = pdf_dict_put_dict(ctx, val, PDF_NAME_EF, 4);
        pdf_dict_put_text_string(ctx, val, PDF_NAME_F, filename);
        pdf_dict_put_text_string(ctx, val, PDF_NAME_UF, filename);
        pdf_dict_put_text_string(ctx, val, PDF_NAME_Desc, desc);
        pdf_dict_put(ctx, val, PDF_NAME_Type, PDF_NAME_Filespec);
        tbuf = fz_new_buffer(ctx, strlen(filename)+1);
        fz_append_string(ctx, tbuf, filename);
        fz_terminate_buffer(ctx, tbuf);
        pdf_dict_put_drop(ctx, ef, PDF_NAME_F,
                         (f = pdf_add_stream(ctx, pdf, tbuf, NULL, 0)));
        fz_drop_buffer(ctx, tbuf);
        JM_update_stream(ctx, pdf, f, buf);
        len = fz_buffer_storage(ctx, buf, NULL);
        pdf_dict_put_int(ctx, f, PDF_NAME_DL, len);
        pdf_dict_put_int(ctx, f, PDF_NAME_Length, len);
        params = pdf_dict_put_dict(ctx, f, PDF_NAME_Params, 4);
        pdf_dict_put_int(ctx, params, PDF_NAME_Size, len);
    }
    fz_always(ctx)
    {
        ;
    }
    fz_catch(ctx) fz_rethrow(ctx);
    return val;
}
%}