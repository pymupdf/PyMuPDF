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
// finds index of an embedded file
// Object "id" contains either entry name (str) or supposed index
// pdf is the document in question
//-----------------------------------------------------------------------------
int FindEmbedded(fz_context *ctx, PyObject *id, pdf_document *pdf)
{
    char *name = NULL;
    Py_ssize_t name_len = 0;
    char *tname= NULL;
    int i = -1;
    int count = pdf_count_portfolio_entries(ctx, pdf);
    name = getPDFstr(ctx, id, &name_len, "id");
    if (name == NULL)           // entry number provided
    {
        if (!PyInt_Check(id))
            fz_throw(ctx, FZ_ERROR_GENERIC, "id must be string or number");

        i = (int) PyInt_AsLong(id);
        if ((i < 0) || (i >= count))
            fz_throw(ctx, FZ_ERROR_GENERIC, "index out of range");
    }
    else                        // entry name provided
    {
        for (i = 0; i < count; i++)
            {
                tname = pdf_to_utf8(ctx, pdf_portfolio_entry_name(ctx, pdf, i));
                if (strcmp(tname, name) == 0) break;
            }
        if (strcmp(tname, name) != 0)
        fz_throw(ctx, FZ_ERROR_GENERIC, "name not found");
    }
    return i;
}
%}