%{
//=============================================================================
// Circumvention of MuPDF bug in 'pdf_preload_image_resources'
// This bug affects 'pdf_add_image' calls when images already exist, i.e.
// almost always!
// This fix uses a modified version of 'pdf_preload_image_resources'.
// Because of 'static' declarations, 'fz_md5_image',
// 'pdf_preload_image_resources' and 'pdf_find_image_resource' had to
// special-versioned as well ...
// Start
//=============================================================================

void
JM_fz_md5_image(fz_context *ctx, fz_image *image, unsigned char digest[16])
{
    fz_pixmap *pixmap;
    fz_md5 state;
    int h;
    unsigned char *d;

    pixmap = fz_get_pixmap_from_image(ctx, image, NULL, NULL, 0, 0);
    fz_md5_init(&state);
    d = pixmap->samples;
    h = pixmap->h;
    while (h--)
    {
        fz_md5_update(&state, d, pixmap->w * pixmap->n);
        d += pixmap->stride;
    }
    fz_md5_final(&state, digest);
    fz_drop_pixmap(ctx, pixmap);
}

void
JM_pdf_preload_image_resources(fz_context *ctx, pdf_document *doc)
{
    int len, k;
    pdf_obj *obj;
    pdf_obj *type;
    pdf_obj *res = NULL;
    fz_image *image = NULL;
    unsigned char digest[16];

    fz_var(obj);
    fz_var(image);
    fz_var(res);
    fz_try(ctx)
    {
        len = pdf_count_objects(ctx, doc);
        for (k = 1; k < len; k++)
        {
            // this is the buggy statement: -----------------------------------
            // obj = pdf_load_object(ctx, doc, k);
            // replaced with the following: -----------------------------------
            obj = pdf_new_indirect(gctx, doc, k, 0);
            type = pdf_dict_get(ctx, obj, PDF_NAME_Subtype);
            if (pdf_name_eq(ctx, type, PDF_NAME_Image))
            {
                image = pdf_load_image(ctx, doc, obj);
                JM_fz_md5_image(ctx, image, digest);
                fz_drop_image(ctx, image);
                image = NULL;

                /* Do not allow overwrites. */
                if (!fz_hash_find(ctx, doc->resources.images, digest))
                    fz_hash_insert(ctx, doc->resources.images, digest, pdf_keep_obj(ctx, obj));
            }
            pdf_drop_obj(ctx, obj);
            obj = NULL;
        }
    }
    fz_always(ctx)
    {
        fz_drop_image(ctx, image);
        pdf_drop_obj(ctx, obj);
    }
    fz_catch(ctx)
    {
        fz_rethrow(ctx);
    }
}

pdf_obj *
JM_pdf_find_image_resource(fz_context *ctx, pdf_document *doc, fz_image *item, unsigned char digest[16])
{
    pdf_obj *res;
    if (!doc->resources.images)
    {
        doc->resources.images = fz_new_hash_table(ctx, 4096, 16, -1, (fz_hash_table_drop_fn)pdf_drop_obj);
        JM_pdf_preload_image_resources(ctx, doc);
    }

    /* Create md5 and see if we have the item in our table */
    JM_fz_md5_image(ctx, item, digest);
    res = fz_hash_find(ctx, doc->resources.images, digest);
    if (res)
        pdf_keep_obj(ctx, res);
    return res;
}

pdf_obj *
JM_add_image(fz_context *ctx, pdf_document *doc, fz_image *image, int mask, unsigned char *digest)
{
    pdf_obj *imref = NULL;
    imref = JM_pdf_find_image_resource(ctx, doc, image, digest);
    if (imref) return imref;
    return pdf_add_image(ctx, doc, image, mask);
}
//=============================================================================
// End
// Circumvention of MuPDF bug in pdf_preload_image_resources
//=============================================================================

void hexlify(int n, unsigned char *in, unsigned char *out)
{
    const unsigned char hdigit[16] = "0123456789abcedf";
    int i, i1, i2;
    for (i = 0; i < n; i++)
    {
        i1 = in[i]>>4;
        i2 = in[i] - i1*16;
        out[2*i] = hdigit[i1];
        out[2*i + 1] = hdigit[i2];
    }
    out[2*n] = 0;
}





//----------------------------------------------------------------------------
// Return set(dict.keys()) <= set([vkeys, ...])
// keys of dict must be string or unicode in Py2 and string in Py3!
// Parameters:
// dict - the Python dictionary object to be checked
// vkeys - a null-terminated list of keys (char *)
//----------------------------------------------------------------------------
int checkDictKeys(PyObject *dict, const char *vkeys, ...)
{
    int i, j, rc;
    PyObject *dkeys = PyDict_Keys(dict);              // = dict.keys()
    if (!dkeys) return 0;                             // no valid dictionary
    j = PySequence_Size(dkeys);                       // len(dict.keys())
    PyObject *validkeys = PyList_New(0);            // make list of valid keys
    va_list ap;                                       // def var arg list
    va_start(ap, vkeys);                              // start of args
    while (vkeys != 0)                                // reached end yet?
        { // build list of valid keys to check against
#if PY_MAJOR_VERSION < 3
        PyList_Append(validkeys, PyBytes_FromString(vkeys));    // Python 2
#else
        PyList_Append(validkeys, PyUnicode_FromString(vkeys));  // python 3
#endif
        vkeys = va_arg(ap, const char *);             // get next char string
        }
    va_end(ap);                                       // end the var args loop
    rc = 1;                                           // prepare for success
    for (i = 0; i < j; i++)
    {   // loop through dictionary keys
        if (!PySequence_Contains(validkeys, PySequence_GetItem(dkeys, i)))
            {
            rc = 0;
            break;
            }
    }
    Py_DECREF(validkeys);
    Py_DECREF(dkeys);
    return rc;
}

//----------------------------------------------------------------------------
// returns Python True / False for an integer
//----------------------------------------------------------------------------
PyObject *truth_value(int v)
{
    if (v == 0) Py_RETURN_FALSE;
    Py_RETURN_TRUE;
}

//----------------------------------------------------------------------------
// deflate data in a buffer
//----------------------------------------------------------------------------
fz_buffer *deflatebuf(fz_context *ctx, unsigned char *p, size_t n)
{
    fz_buffer *buf;
    uLongf csize;
    int t;
    uLong longN = (uLong)n;
    unsigned char *data;
    size_t cap;

    if (n != (size_t)longN)
        fz_throw(ctx, FZ_ERROR_GENERIC, "Buffer to large to deflate");

    cap = compressBound(longN);
    data = fz_malloc(ctx, cap);
    buf = fz_new_buffer_from_data(ctx, data, cap);
    csize = (uLongf)cap;
    t = compress(data, &csize, p, longN);
    if (t != Z_OK)
    {
        fz_drop_buffer(ctx, buf);
        fz_throw(ctx, FZ_ERROR_GENERIC, "cannot deflate buffer");
    }
    fz_resize_buffer(ctx, buf, csize);
    return buf;
}

//----------------------------------------------------------------------------
// Return (char *) for PyBytes, PyString (Python 2) or PyUnicode objects.
// For PyBytes, a conversion to PyUnicode is first performed, if Python 3.
// In Python 2, this is an alias for PyString and its (char *) is returned.
// PyUnicode objects are converted to UTF16BE bytes objects (all Python
// versions). Its (char *) version is returned.
// If only 1-byte code points are present, BOM and high-order 0-bytes are
// deleted and the (compressed) rest is returned.
// Parameters:
// obj = PyBytes / PyString / PyUnicode object
// psize = pointer to a Py_ssize_t number for storing the returned length
// name = name of object to use in error messages
//----------------------------------------------------------------------------
char *getPDFstr(PyObject *obj, Py_ssize_t* psize, const char *name)
{
    if (obj == NULL) return NULL;
    if (!PyBytes_Check(obj) && !PyUnicode_Check(obj)) return NULL;
    int ok;
    Py_ssize_t j, k;
    PyObject *me;
    unsigned char *nc;
    int have_uc = 0;    // indicates unicode points > 255
    me = obj;
    if (PyBytes_Check(me))
        {
        ok = PyBytes_AsStringAndSize(me, &nc, psize);
        if (ok != 0)
            {
            fz_throw(gctx, FZ_ERROR_GENERIC, "could not get string of '%s'", name);
            return NULL;
            }
#if PY_MAJOR_VERSION < 3
        return nc;                     // we are done when Python 2
#endif
        me = PyUnicode_FromStringAndSize(nc, *psize);      // assumes nc is UTF8
        }
    PyObject *uc = PyUnicode_AsUTF16String(me);
    if (!uc)
        {
        fz_throw(gctx, FZ_ERROR_GENERIC, "could not create UTF16 for '%s'", name);
        return NULL;
        }
    ok = PyBytes_AsStringAndSize(uc, &nc, psize);
    if (ok != 0)
        {
        fz_throw(gctx, FZ_ERROR_GENERIC, "could not get UTF16 string of '%s'", name);
        return NULL;
        }
    // UTF16-BE (big endian) is required for PDF if code points > 0xff
    if (nc[0] == 255)                  // non-BE UTF16, so swap bytes
    {
        j = 2;
        nc[0] = 254;                   // set BOM to "BE"
        nc[1] = 255;
        while ((j+1) < *psize)
        {
            k = nc[j];                      // save 1st byte
            nc[j] = nc[j+1];                // copy 2nd byte
            nc[j+1] = k;                    // copy 1st byte
            if (nc[j] > 0) have_uc = 1;     // code point outside latin-1
            j = j + 2;
        }
    }
    else                               // have UTF16BE, just check code points
    {
        j = 2;
        while (j < *psize)
        {
            if (nc[j] > 0) have_uc = 1;     // code point outside latin-1
            j = j + 2;
        }
    }
    if (have_uc == 1) return nc;            // have large code points: done
    *psize = (*psize - 2)/2;                // reduced size
    j=3;
    for (k = 0; k < *psize; k++)            // kick out BOM & high order zeros
    {
        nc[k] = nc[j];
        j += 2;
    }
    nc[*psize] = 0;                         // end of string delimiter
    return nc;
}

//----------------------------------------------------------------------------
// Deep-copies a specified source page to the target location.
//----------------------------------------------------------------------------
void page_merge(pdf_document* doc_des, pdf_document* doc_src, int page_from, int page_to, int rotate, pdf_graft_map *graft_map)
{
    pdf_obj *pageref = NULL;
    pdf_obj *page_dict;
    pdf_obj *obj = NULL, *ref = NULL, *subt = NULL;

    // list of object types (per page) we want to copy
    pdf_obj *known_page_objs[] = {PDF_NAME_Contents, PDF_NAME_Resources,
        PDF_NAME_MediaBox, PDF_NAME_CropBox, PDF_NAME_BleedBox, PDF_NAME_Annots,
        PDF_NAME_TrimBox, PDF_NAME_ArtBox, PDF_NAME_Rotate, PDF_NAME_UserUnit};
    int n = nelem(known_page_objs);                   // number of list elements
    int i;
    int num, j;
    fz_var(obj);
    fz_var(ref);

    fz_try(gctx)
    {
        pageref = pdf_lookup_page_obj(gctx, doc_src, page_from);
        pdf_flatten_inheritable_page_items(gctx, pageref);
        // make a new page
        page_dict = pdf_new_dict(gctx, doc_des, 4);
        pdf_dict_put_drop(gctx, page_dict, PDF_NAME_Type, PDF_NAME_Page);

        // copy objects of source page into it
        for (i = 0; i < n; i++)
            {
            obj = pdf_dict_get(gctx, pageref, known_page_objs[i]);
            if (obj != NULL)
                pdf_dict_put_drop(gctx, page_dict, known_page_objs[i], pdf_graft_object(gctx, doc_des, doc_src, obj, graft_map));
            }
        // remove any links from annots array
        pdf_obj *annots = pdf_dict_get(gctx, page_dict, PDF_NAME_Annots);
        int len = pdf_array_len(gctx, annots);
        for (j = 0; j < len; j++)
        {
            pdf_obj *o = pdf_array_get(gctx, annots, j);
            if (!pdf_name_eq(gctx, pdf_dict_get(gctx, o, PDF_NAME_Subtype), PDF_NAME_Link))
                continue;
            // remove the link annotation
            pdf_array_delete(gctx, annots, j);
            len--;
            j--;
        }
        // rotate the page as requested
        if (rotate != -1)
            {
            pdf_obj *rotateobj = pdf_new_int(gctx, doc_des, rotate);
            pdf_dict_put_drop(gctx, page_dict, PDF_NAME_Rotate, rotateobj);
            }
        // Now add the page dictionary to dest PDF
        obj = pdf_add_object_drop(gctx, doc_des, page_dict);

        // Get indirect ref of the page
        num = pdf_to_num(gctx, obj);
        ref = pdf_new_indirect(gctx, doc_des, num, 0);

        // Insert new page at specified location
        pdf_insert_page(gctx, doc_des, page_to, ref);

    }
    fz_always(gctx)
    {
        pdf_drop_obj(gctx, obj);
        pdf_drop_obj(gctx, ref);
    }
    fz_catch(gctx)
    {
        fz_rethrow(gctx);
    }
}

//----------------------------------------------------------------------------
// Copy a range of pages (spage, epage) from a source PDF to a specified location
// (apage) of the target PDF.
// If spage > epage, the sequence of source pages is reversed.
//----------------------------------------------------------------------------
void merge_range(pdf_document* doc_des, pdf_document* doc_src, int spage, int epage, int apage, int rotate)
{
    int page, afterpage;
    pdf_graft_map *graft_map;
    afterpage = apage;

    graft_map = pdf_new_graft_map(gctx, doc_src);

    fz_try(gctx)
    {
        if (spage < epage)
            for (page = spage; page <= epage; page++, afterpage++)
                page_merge(doc_des, doc_src, page, afterpage, rotate, graft_map);
        else
            for (page = spage; page >= epage; page--, afterpage++)
                page_merge(doc_des, doc_src, page, afterpage, rotate, graft_map);
    }

    fz_always(gctx)
    {
        pdf_drop_graft_map(gctx, graft_map);
    }
    fz_catch(gctx)
    {
        fz_rethrow(gctx);
    }
}

//----------------------------------------------------------------------------
// Fills table 'res' with outline xref numbers
// 'res' must be a correctly pre-allocated table of integers
// 'obj' must be the first OL item
// returns (int) number of filled-in outline item xref numbers.
//----------------------------------------------------------------------------
int fillOLNumbers(int *res, pdf_obj *obj, int oc, int argc)
{
    int onum;
    pdf_obj *first, *parent, *thisobj;
    if (!obj) return oc;
    if (oc >= argc) return oc;
    thisobj = obj;
    while (thisobj) {
        onum = pdf_to_num(gctx, thisobj);
        res[oc] = onum;
        oc += 1;
        first = pdf_dict_get(gctx, thisobj, PDF_NAME_First);   /* try go down */
        if (first) oc = fillOLNumbers(res, first, oc, argc);   /* recurse     */
        thisobj = pdf_dict_get(gctx, thisobj, PDF_NAME_Next);  /* try go next */
        parent = pdf_dict_get(gctx, thisobj, PDF_NAME_Parent); /* get parent  */
        if (!thisobj) thisobj = parent;         /* goto parent if no next obj */
    }
    return oc;
}

//----------------------------------------------------------------------------
// Returns (int) number of outlines
// 'obj' must be first OL item
//----------------------------------------------------------------------------
int countOutlines(pdf_obj *obj, int oc)
{
    pdf_obj *first, *parent, *thisobj;
    if (!obj) return oc;
    thisobj = obj;
    while (thisobj) {
        oc += 1;
        first = pdf_dict_get(gctx, thisobj, PDF_NAME_First);   /* try go down */
        if (first) oc = countOutlines(first, oc);
        thisobj = pdf_dict_get(gctx, thisobj, PDF_NAME_Next);  /* try go next */
        parent = pdf_dict_get(gctx, thisobj, PDF_NAME_Parent); /* get parent  */
        if (!thisobj) thisobj = parent;      /* goto parent if no next exists */
    }
    return oc;
}

//----------------------------------------------------------------------------
// Read text from a document page - the short way.
// Main logic is contained in function fz_new_stext_page_from_page of file
// utils.c in the fitz directory.
// In essence, it creates an stext device, runs the stext page through it,
// deletes the device and returns the text buffer in the requested format.
// A display list is not used in the process.
//----------------------------------------------------------------------------
const char *readPageText(fz_page *page, int output) {
    fz_buffer *res;
    fz_output *out;
    fz_stext_sheet *ts;
    fz_stext_page *tp;
    fz_try(gctx) {
        ts = fz_new_stext_sheet(gctx);
        tp = fz_new_stext_page_from_page(gctx, page, ts, NULL);
        res = fz_new_buffer(gctx, 1024);
        out = fz_new_output_with_buffer(gctx, res);
        if (output<=0) fz_print_stext_page(gctx, out, tp);
        if (output==1) fz_print_stext_page_html(gctx, out, tp);
        if (output==2) fz_print_stext_page_json(gctx, out, tp);
        if (output>=3) fz_print_stext_page_xml(gctx, out, tp);
    }
    fz_always(gctx)
    {
        fz_drop_output(gctx, out);
        fz_drop_stext_page(gctx, tp);
        fz_drop_stext_sheet(gctx, ts);
    }
    fz_catch(gctx) {
        if (res) fz_drop_buffer(gctx, res);
        fz_rethrow(gctx);
    }
    return fz_string_from_buffer(gctx, res);
}
%}