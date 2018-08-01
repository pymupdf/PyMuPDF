%{
//----------------------------------------------------------------------------
// deflate char* into a buffer
// this is a copy of function "deflatebuf" of pdf_write.c
//----------------------------------------------------------------------------
fz_buffer *JM_deflatebuf(fz_context *ctx, unsigned char *p, size_t n)
{
    fz_buffer *buf = NULL;
    uLongf csize;
    int t;
    uLong longN = (uLong) n;
    unsigned char *data = NULL;
    size_t cap;
    fz_try(ctx)
    {
        if (n != (size_t)longN) THROWMSG("buffer too large to deflate");
        cap = compressBound(longN);
        data = fz_malloc(ctx, cap);
        buf = fz_new_buffer_from_data(ctx, data, cap);
        csize = (uLongf)cap;
        t = compress(data, &csize, p, longN);
        if (t != Z_OK) THROWMSG("cannot deflate buffer");
    }
    fz_catch(ctx)
    {
        fz_drop_buffer(ctx, buf);
        fz_rethrow(ctx);
    }
    fz_resize_buffer(ctx, buf, csize);
    return buf;
}

//----------------------------------------------------------------------------
// update a stream object
// compress stream where beneficial
//----------------------------------------------------------------------------
void JM_update_stream(fz_context *ctx, pdf_document *doc, pdf_obj *obj, fz_buffer *buffer)
{
    size_t len, nlen;
    char *data;
    fz_buffer *nres = NULL;
    len = fz_buffer_storage(ctx, buffer, &data);
    nlen = len;
    if (len > 20)       // ignore small stuff
    {
        nres = JM_deflatebuf(ctx, data, len);
        nlen = fz_buffer_storage(ctx, nres, NULL);
    }
    if (nlen < len)     // was it worth the effort?
    {
        pdf_dict_put(ctx, obj, PDF_NAME_Filter, PDF_NAME_FlateDecode);
        pdf_update_stream(ctx, doc, obj, nres, 1);
    }
    else
    {
        pdf_update_stream(ctx, doc, obj, buffer, 0);
    }
    fz_drop_buffer(ctx, nres);
}

//-----------------------------------------------------------------------------
// Version of fz_pixmap_from_display_list (utils.c) to support rendering
// of only the 'clip' part of the displaylist rectangle
//-----------------------------------------------------------------------------
fz_pixmap *
JM_pixmap_from_display_list(fz_context *ctx, fz_display_list *list, const fz_matrix *ctm, fz_colorspace *cs, int alpha, const fz_rect *clip)
{
    fz_rect rect;
    fz_irect irect;
    fz_pixmap *pix;
    fz_device *dev;
    fz_separations *seps = NULL;
    fz_bound_display_list(ctx, list, &rect);
    if (clip) fz_intersect_rect(&rect, clip);
    fz_transform_rect(&rect, ctm);
    fz_round_rect(&irect, &rect);

    pix = fz_new_pixmap_with_bbox(ctx, cs, &irect, seps, alpha);
    if (alpha)
        fz_clear_pixmap(ctx, pix);
    else
        fz_clear_pixmap_with_value(ctx, pix, 0xFF);

    fz_try(ctx)
    {
        if (clip)
            dev = fz_new_draw_device_with_bbox(ctx, ctm, pix, &irect);
        else
            dev = fz_new_draw_device(ctx, ctm, pix);
        fz_run_display_list(ctx, list, dev, &fz_identity, clip, NULL);
        fz_close_device(ctx, dev);
    }
    fz_always(ctx)
    {
        fz_drop_device(ctx, dev);
    }
    fz_catch(ctx)
    {
        fz_drop_pixmap(ctx, pix);
        fz_rethrow(ctx);
    }
    return pix;
}

PyObject *JM_BOOL(int v)
{
    if (v == 0)
        Py_RETURN_FALSE;
    Py_RETURN_TRUE;
}

//-----------------------------------------------------------------------------
// return hex characters for n characters in input 'in'
//-----------------------------------------------------------------------------
void hexlify(int n, unsigned char *in, unsigned char *out)
{
    const unsigned char hdigit[17] = "0123456789abcedf";
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
// Turn Python a bytes or bytearray object into char* string
// using the "_AsString" functions. Returns string size or 0 on error.
//----------------------------------------------------------------------------
size_t JM_CharFromBytesOrArray(PyObject *stream, char **data)
{
    if (PyBytes_Check(stream))
    {
        *data = PyBytes_AsString(stream);
        return (size_t) PyBytes_Size(stream);
    }
    if (PyByteArray_Check(stream))
    {
        *data = PyByteArray_AsString(stream);
        return (size_t) PyByteArray_Size(stream);
    }
    return 0;
}

//----------------------------------------------------------------------------
// Modified copy of SWIG_Python_str_AsChar
// If Py3, the SWIG original v3.0.12does *not* deliver NULL for a
// non-string input, as does PyString_AsString in Py2.
//----------------------------------------------------------------------------
char *JM_Python_str_AsChar(PyObject *str)
{
    if (!str) return NULL;
#if PY_VERSION_HEX >= 0x03000000
  char *newstr = NULL;
  PyObject *xstr = PyUnicode_AsUTF8String(str);
  if (xstr)
  {
    char *cstr;
    Py_ssize_t len;
    PyBytes_AsStringAndSize(xstr, &cstr, &len);
    newstr = (char *) malloc(len+1);
    memcpy(newstr, cstr, len+1);
    Py_XDECREF(xstr);
  }
  return newstr;
#else
  return PyString_AsString(str);
#endif
}

#if PY_VERSION_HEX >= 0x03000000
#  define JM_Python_str_DelForPy3(x) free((void*) (x))
#else
#  define JM_Python_str_DelForPy3(x) 
#endif

//----------------------------------------------------------------------------
// Deep-copies a specified source page to the target location.
// Modified copy of function of pdfmerge.c: we also copy annotations, but
// we skip **link** annotations. In addition we rotate output.
//----------------------------------------------------------------------------
void page_merge(fz_context *ctx, pdf_document *doc_des, pdf_document *doc_src, int page_from, int page_to, int rotate, pdf_graft_map *graft_map)
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

    fz_try(ctx)
    {
        pageref = pdf_lookup_page_obj(ctx, doc_src, page_from);
        pdf_flatten_inheritable_page_items(ctx, pageref);
        // make a new page
        page_dict = pdf_new_dict(ctx, doc_des, 4);
        pdf_dict_put_drop(ctx, page_dict, PDF_NAME_Type, PDF_NAME_Page);

        // copy objects of source page into it
        for (i = 0; i < n; i++)
            {
            obj = pdf_dict_get(ctx, pageref, known_page_objs[i]);
            if (obj != NULL)
                pdf_dict_put_drop(ctx, page_dict, known_page_objs[i], pdf_graft_mapped_object(ctx, graft_map, obj));
            }
        // remove any links from annots array
        pdf_obj *annots = pdf_dict_get(ctx, page_dict, PDF_NAME_Annots);
        int len = pdf_array_len(ctx, annots);
        for (j = 0; j < len; j++)
        {
            pdf_obj *o = pdf_array_get(ctx, annots, j);
            if (!pdf_name_eq(ctx, pdf_dict_get(ctx, o, PDF_NAME_Subtype), PDF_NAME_Link))
                continue;
            // remove the link annotation
            pdf_array_delete(ctx, annots, j);
            len--;
            j--;
        }
        // rotate the page as requested
        if (rotate != -1)
            {
            pdf_obj *rotateobj = pdf_new_int(ctx, doc_des, rotate);
            pdf_dict_put_drop(ctx, page_dict, PDF_NAME_Rotate, rotateobj);
            }
        // Now add the page dictionary to dest PDF
        obj = pdf_add_object_drop(ctx, doc_des, page_dict);

        // Get indirect ref of the page
        num = pdf_to_num(ctx, obj);
        ref = pdf_new_indirect(ctx, doc_des, num, 0);

        // Insert new page at specified location
        pdf_insert_page(ctx, doc_des, page_to, ref);

    }
    fz_always(ctx)
    {
        pdf_drop_obj(ctx, obj);
        pdf_drop_obj(ctx, ref);
    }
    fz_catch(ctx)
    {
        fz_rethrow(ctx);
    }
}

//-----------------------------------------------------------------------------
// Copy a range of pages (spage, epage) from a source PDF to a specified
// location (apage) of the target PDF.
// If spage > epage, the sequence of source pages is reversed.
//-----------------------------------------------------------------------------
void merge_range(fz_context *ctx, pdf_document *doc_des, pdf_document *doc_src, int spage, int epage, int apage, int rotate)
{
    int page, afterpage, count;
    pdf_graft_map *graft_map;
    afterpage = apage;
    count = pdf_count_pages(ctx, doc_src);
    graft_map = pdf_new_graft_map(ctx, doc_des);

    fz_try(ctx)
    {
        if (spage < epage)
            for (page = spage; page <= epage; page++, afterpage++)
                page_merge(ctx, doc_des, doc_src, page, afterpage, rotate, graft_map);
        else
            for (page = spage; page >= epage; page--, afterpage++)
                page_merge(ctx, doc_des, doc_src, page, afterpage, rotate, graft_map);
    }

    fz_always(ctx)
    {
        pdf_drop_graft_map(ctx, graft_map);
    }
    fz_catch(ctx)
    {
        fz_rethrow(ctx);
    }
}

//----------------------------------------------------------------------------
// Fills table 'res' with outline xref numbers
// 'res' must be a correctly pre-allocated table of integers
// 'obj' must be the first OL item
// returns (int) number of filled-in outline item xref numbers.
//----------------------------------------------------------------------------
int fillOLNumbers(fz_context *ctx, int *res, pdf_obj *obj, int oc, int argc)
{
    int onum;
    pdf_obj *first, *parent, *thisobj;
    if (!obj) return oc;
    if (oc >= argc) return oc;
    thisobj = obj;
    while (thisobj) {
        onum = pdf_to_num(ctx, thisobj);
        res[oc] = onum;
        oc += 1;
        first = pdf_dict_get(ctx, thisobj, PDF_NAME_First);   /* try go down */
        if (first) oc = fillOLNumbers(ctx, res, first, oc, argc);   /* recurse     */
        thisobj = pdf_dict_get(ctx, thisobj, PDF_NAME_Next);  /* try go next */
        parent = pdf_dict_get(ctx, thisobj, PDF_NAME_Parent); /* get parent  */
        if (!thisobj) thisobj = parent;         /* goto parent if no next obj */
    }
    return oc;
}

//----------------------------------------------------------------------------
// Returns number of outlines
// 'obj' must be first OL item
//----------------------------------------------------------------------------
int countOutlines(fz_context *ctx, pdf_obj *obj, int oc)
{
    pdf_obj *first, *parent, *thisobj;
    if (!obj) return oc;
    thisobj = obj;
    while (thisobj) {
        oc += 1;
        first = pdf_dict_get(ctx, thisobj, PDF_NAME_First);   /* try go down */
        if (first) oc = countOutlines(ctx, first, oc);
        thisobj = pdf_dict_get(ctx, thisobj, PDF_NAME_Next);  /* try go next */
        parent = pdf_dict_get(ctx, thisobj, PDF_NAME_Parent); /* get parent  */
        if (!thisobj) thisobj = parent;      /* goto parent if no next exists */
    }
    return oc;
}

//-----------------------------------------------------------------------------
// Return the contents of a font file
//-----------------------------------------------------------------------------
fz_buffer *fontbuffer(fz_context *ctx, pdf_document *doc, int xref)
{
    if (xref < 1) return NULL;
    pdf_obj *o, *obj = NULL, *desft, *stream = NULL;
    char *ext = "";
    o = pdf_load_object(ctx, doc, xref);
    desft = pdf_dict_get(ctx, o, PDF_NAME_DescendantFonts);
    if (desft)
    {
        obj = pdf_resolve_indirect(ctx, pdf_array_get(ctx, desft, 0));
        obj = pdf_dict_get(ctx, obj, PDF_NAME_FontDescriptor);
    }
    else
        obj = pdf_dict_get(ctx, o, PDF_NAME_FontDescriptor);

    if (!obj)
    {
        pdf_drop_obj(ctx, o);
        PySys_WriteStdout("invalid font - FontDescriptor missing");
        return NULL;
    }
    pdf_drop_obj(ctx, o);
    o = obj;

    obj = pdf_dict_get(ctx, o, PDF_NAME_FontFile);
    if (obj) stream = obj;             // ext = "pfa"

    obj = pdf_dict_get(ctx, o, PDF_NAME_FontFile2);
    if (obj) stream = obj;             // ext = "ttf"

    obj = pdf_dict_get(ctx, o, PDF_NAME_FontFile3);
    if (obj)
    {
        stream = obj;

        obj = pdf_dict_get(ctx, obj, PDF_NAME_Subtype);
        if (obj && !pdf_is_name(ctx, obj))
        {
            PySys_WriteStdout("invalid font descriptor subtype");
            return NULL;
        }

        if (pdf_name_eq(ctx, obj, PDF_NAME_Type1C))
            ext = "cff";
        else if (pdf_name_eq(ctx, obj, PDF_NAME_CIDFontType0C))
            ext = "cid";
        else if (pdf_name_eq(ctx, obj, PDF_NAME_OpenType))
            ext = "otf";
        else
            PySys_WriteStdout("warning: unhandled font type '%s'", pdf_to_name(ctx, obj));
    }

    if (!stream)
    {
        PySys_WriteStdout("warning: unhandled font type");
        return NULL;
    }

    return pdf_load_stream(ctx, stream);
}

//-----------------------------------------------------------------------------
// Return the file extension of an embedded font file
//-----------------------------------------------------------------------------
char *fontextension(fz_context *ctx, pdf_document *doc, int xref)
{
    if (xref < 1) return "n/a";
    pdf_obj *o, *obj = NULL, *desft;
    o = pdf_load_object(ctx, doc, xref);
    desft = pdf_dict_get(ctx, o, PDF_NAME_DescendantFonts);
    if (desft)
    {
        obj = pdf_resolve_indirect(ctx, pdf_array_get(ctx, desft, 0));
        obj = pdf_dict_get(ctx, obj, PDF_NAME_FontDescriptor);
    }
    else
        obj = pdf_dict_get(ctx, o, PDF_NAME_FontDescriptor);

    pdf_drop_obj(ctx, o);
    if (!obj) return "n/a";           // this is a base-14 font

    o = obj;                           // we have the FontDescriptor

    obj = pdf_dict_get(ctx, o, PDF_NAME_FontFile);
    if (obj) return "pfa";

    obj = pdf_dict_get(ctx, o, PDF_NAME_FontFile2);
    if (obj) return "ttf";

    obj = pdf_dict_get(ctx, o, PDF_NAME_FontFile3);
    if (obj)
    {
        obj = pdf_dict_get(ctx, obj, PDF_NAME_Subtype);
        if (obj && !pdf_is_name(ctx, obj))
        {
            PySys_WriteStdout("invalid font descriptor subtype");
            return "n/a";
        }
        if (pdf_name_eq(ctx, obj, PDF_NAME_Type1C))
            return "cff";
        else if (pdf_name_eq(ctx, obj, PDF_NAME_CIDFontType0C))
            return "cid";
        else if (pdf_name_eq(ctx, obj, PDF_NAME_OpenType))
            return "otf";
        else
            PySys_WriteStdout("unhandled font type '%s'", pdf_to_name(ctx, obj));
    }

    return "n/a";
}

//-----------------------------------------------------------------------------
// dummy structure for various tools and utilities
//-----------------------------------------------------------------------------
struct Tools {int index;};

typedef struct fz_item_s fz_item;

struct fz_item_s
{
	void *key;
	fz_storable *val;
	size_t size;
	fz_item *next;
	fz_item *prev;
	fz_store *store;
	const fz_store_type *type;
};

struct fz_store_s
{
	int refs;

	/* Every item in the store is kept in a doubly linked list, ordered
	 * by usage (so LRU entries are at the end). */
	fz_item *head;
	fz_item *tail;

	/* We have a hash table that allows to quickly find a subset of the
	 * entries (those whose keys are indirect objects). */
	fz_hash_table *hash;

	/* We keep track of the size of the store, and keep it below max. */
	size_t max;
	size_t size;

	int defer_reap_count;
	int needs_reaping;
};

%}