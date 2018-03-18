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
// Object "id" contains either entry name (str) or supposed index.
// Int "id" is returned as result if in valid range.
//-----------------------------------------------------------------------------
int FindEmbedded(fz_context *ctx, PyObject *id, pdf_document *pdf)
{
    char *name = NULL;
    Py_ssize_t name_len = 0;
    char *tname= NULL;
    int i = -1;
    int count = pdf_count_portfolio_entries(ctx, pdf);
    if (count < 1) return -1;
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
        if (strcmp(tname, name) == 0) break;
    }
    if (strcmp(tname, name) != 0)
    {
        JM_Python_str_DelForPy3(name);
        i = -1;
    }
    JM_Python_str_DelForPy3(name);
    return i;
}
%}