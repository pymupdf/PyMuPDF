%{
//----------------------------------------------------------------------------
// convert (char *) to ASCII-only (char*) (which must be freed!)
//----------------------------------------------------------------------------
char *JM_ASCIIFromChar(char *in)
{
    if (!in) return NULL;
    size_t i, j = strlen(in) + 1;
    unsigned char *out = JM_Alloc(unsigned char, j);
    if (!out) return NULL;
    memcpy(out, in, j);
    for (i = 0; i < j-1; i++)
    {
        if (out[i] > 126)
        {
            out[i] = 63;
            continue;
        }
        if (out[i] < 32)
            out[i] = 32;
    }
    return (char *) out;
}

//----------------------------------------------------------------------------
// create an ASCII-only Python string of a (char*)
//----------------------------------------------------------------------------
PyObject *JM_UnicodeFromASCII(const char *in)
{
    char *c = JM_ASCIIFromChar((char *) in);
    PyObject *p = Py_BuildValue("s", c);
    JM_Free(c);
    return p;
}

//-----------------------------------------------------------------------------
// Store info of a font in Python list
//-----------------------------------------------------------------------------
void JM_gather_fonts(fz_context *ctx, pdf_document *pdf, pdf_obj *dict,
                    PyObject *fontlist)
{
    int i, n;
    n = pdf_dict_len(ctx, dict);
    for (i = 0; i < n; i++)
    {
        pdf_obj *fontdict = NULL;
        pdf_obj *subtype = NULL;
        pdf_obj *basefont = NULL;
        pdf_obj *name = NULL;
        pdf_obj *refname = NULL;
        pdf_obj *encoding = NULL;

        fontdict = pdf_dict_get_val(ctx, dict, i);
        if (!pdf_is_dict(ctx, fontdict))
        {
            PySys_WriteStdout("warning: not a font dict (%d 0 R)",
                              pdf_to_num(ctx, fontdict));
            continue;
        }
        refname = pdf_dict_get_key(ctx, dict, i);
        subtype = pdf_dict_get(ctx, fontdict, PDF_NAME(Subtype));
        basefont = pdf_dict_get(ctx, fontdict, PDF_NAME(BaseFont));
        if (!basefont || pdf_is_null(ctx, basefont))
            name = pdf_dict_get(ctx, fontdict, PDF_NAME(Name));
        else
            name = basefont;
        encoding = pdf_dict_get(ctx, fontdict, PDF_NAME(Encoding));
        if (pdf_is_dict(ctx, encoding))
            encoding = pdf_dict_get(ctx, encoding, PDF_NAME(BaseEncoding));
        int xref = pdf_to_num(ctx, fontdict);
        char *ext = "n/a";
        if (xref) ext = fontextension(ctx, pdf, xref);
        PyObject *entry = PyList_New(0);
        PyList_Append(entry, Py_BuildValue("i", xref));
        PyList_Append(entry, Py_BuildValue("s", ext));
        PyList_Append(entry, JM_UnicodeFromASCII(pdf_to_name(ctx, subtype)));
        PyList_Append(entry, JM_UnicodeFromASCII(pdf_to_name(ctx, name)));
        PyList_Append(entry, JM_UnicodeFromASCII(pdf_to_name(ctx, refname)));
        PyList_Append(entry, JM_UnicodeFromASCII(pdf_to_name(ctx, encoding)));
        PyList_Append(fontlist, entry);
        Py_CLEAR(entry);
    }
}

//-----------------------------------------------------------------------------
// Store info of an image in Python list
//-----------------------------------------------------------------------------
void JM_gather_images(fz_context *ctx, pdf_document *doc, pdf_obj *dict,
                     PyObject *imagelist)
{
    int i, n;
    n = pdf_dict_len(ctx, dict);
    for (i = 0; i < n; i++)
    {
        pdf_obj *imagedict, *smask;
        pdf_obj *refname = NULL;
        pdf_obj *type;
        pdf_obj *width;
        pdf_obj *height;
        pdf_obj *bpc = NULL;
        pdf_obj *filter = NULL;
        pdf_obj *cs = NULL;
        pdf_obj *altcs;

        imagedict = pdf_dict_get_val(ctx, dict, i);
        if (!pdf_is_dict(ctx, imagedict))
        {
            PySys_WriteStdout("warning: not an image dict (%d 0 R)",
                              pdf_to_num(ctx, imagedict));
            continue;
        }
        refname = pdf_dict_get_key(ctx, dict, i);

        type = pdf_dict_get(ctx, imagedict, PDF_NAME(Subtype));
        if (!pdf_name_eq(ctx, type, PDF_NAME(Image)))
            continue;
        
        int xref = pdf_to_num(ctx, imagedict);
        int gen = 0;
        smask = pdf_dict_get(ctx, imagedict, PDF_NAME(SMask));
        if (smask)
            gen = pdf_to_num(ctx, smask);
        filter = pdf_dict_get(ctx, imagedict, PDF_NAME(Filter));

        altcs = NULL;
        cs = pdf_dict_get(ctx, imagedict, PDF_NAME(ColorSpace));
        if (pdf_is_array(ctx, cs))
        {
            pdf_obj *cses = cs;
            cs = pdf_array_get(ctx, cses, 0);
            if (pdf_name_eq(ctx, cs, PDF_NAME(DeviceN)) ||
                pdf_name_eq(ctx, cs, PDF_NAME(Separation)))
            {
                altcs = pdf_array_get(ctx, cses, 2);
                if (pdf_is_array(ctx, altcs))
                    altcs = pdf_array_get(ctx, altcs, 0);
            }
        }

        width = pdf_dict_get(ctx, imagedict, PDF_NAME(Width));
        height = pdf_dict_get(ctx, imagedict, PDF_NAME(Height));
        bpc = pdf_dict_get(ctx, imagedict, PDF_NAME(BitsPerComponent));

        PyObject *entry = PyList_New(0);
        PyList_Append(entry, Py_BuildValue("i", xref));
        PyList_Append(entry, Py_BuildValue("i", gen));
        PyList_Append(entry, Py_BuildValue("i", pdf_to_int(ctx, width)));
        PyList_Append(entry, Py_BuildValue("i", pdf_to_int(ctx, height)));
        PyList_Append(entry, Py_BuildValue("i", pdf_to_int(ctx, bpc)));
        PyList_Append(entry, JM_UnicodeFromASCII(pdf_to_name(ctx, cs)));
        PyList_Append(entry, JM_UnicodeFromASCII(pdf_to_name(ctx, altcs)));
        PyList_Append(entry, JM_UnicodeFromASCII(pdf_to_name(ctx, refname)));
        PyList_Append(entry, JM_UnicodeFromASCII(pdf_to_name(ctx, filter)));
        PyList_Append(imagelist, entry);
        Py_CLEAR(entry);
    }
}

//-----------------------------------------------------------------------------
// Store info of a /Form in Python list
//-----------------------------------------------------------------------------
void JM_gather_forms(fz_context *ctx, pdf_document *doc, pdf_obj *dict,
                     PyObject *imagelist)
{
    int i, n;
    n = pdf_dict_len(ctx, dict);
    for (i = 0; i < n; i++)
    {
        pdf_obj *imagedict;
        pdf_obj *refname = NULL;
        pdf_obj *type;

        imagedict = pdf_dict_get_val(ctx, dict, i);
        if (!pdf_is_dict(ctx, imagedict))
        {
            PySys_WriteStdout("warning: not a form dict (%d 0 R)",
                              pdf_to_num(ctx, imagedict));
            continue;
        }
        refname = pdf_dict_get_key(ctx, dict, i);

        type = pdf_dict_get(ctx, imagedict, PDF_NAME(Subtype));
        if (!pdf_name_eq(ctx, type, PDF_NAME(Form)))
            continue;

        int xref = pdf_to_num(ctx, imagedict);

        PyObject *entry = PyList_New(0);
        PyList_Append(entry, Py_BuildValue("i", xref));
        PyList_Append(entry, JM_UnicodeFromASCII(pdf_to_name(ctx, refname)));
        PyList_Append(imagelist, entry);
        Py_CLEAR(entry);
    }
}

//-----------------------------------------------------------------------------
// Step through /Resources, looking up image or font information
//-----------------------------------------------------------------------------
void JM_scan_resources(fz_context *ctx, pdf_document *pdf, pdf_obj *rsrc,
                 PyObject *liste, int what)
{
    pdf_obj *font, *xobj, *subrsrc;
    int i, n;
    if (pdf_mark_obj(ctx, rsrc)) return;    // stop on cylic dependencies
    fz_try(ctx)
    {
        if (what == 1)            // look up fonts
        {
            font = pdf_dict_get(ctx, rsrc, PDF_NAME(Font));
            JM_gather_fonts(ctx, pdf, font, liste);
            n = pdf_dict_len(ctx, font);
            for (i = 0; i < n; i++)
            {
                pdf_obj *obj = pdf_dict_get_val(ctx, font, i);
                subrsrc = pdf_dict_get(ctx, obj, PDF_NAME(Resources));
                if (subrsrc)
                    JM_scan_resources(ctx, pdf, subrsrc, liste, what);
            }
        }

        xobj = pdf_dict_get(ctx, rsrc, PDF_NAME(XObject));

        if (what == 2)            // look up images
        {
            JM_gather_images(ctx, pdf, xobj, liste);
        }

        if (what == 3)            // look up forms
        {
            JM_gather_forms(ctx, pdf, xobj, liste);
        }

        n = pdf_dict_len(ctx, xobj);
        for (i = 0; i < n; i++)
        {
            pdf_obj *obj = pdf_dict_get_val(ctx, xobj, i);
            subrsrc = pdf_dict_get(ctx, obj, PDF_NAME(Resources));
            if (subrsrc)
                JM_scan_resources(ctx, pdf, subrsrc, liste, what);
        }
    }
    fz_always(ctx) pdf_unmark_obj(ctx, rsrc);
    fz_catch(ctx)  fz_rethrow(ctx);
}

%}