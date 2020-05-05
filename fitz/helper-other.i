%{

int LIST_APPEND_DROP(PyObject *list, PyObject *item)
{
    if (!list || !PyList_Check(list) || !item) return -2;
    int rc = PyList_Append(list, item);
    Py_DECREF(item);
    return rc;
}

int DICT_SETITEM_DROP(PyObject *dict, PyObject *key, PyObject *value)
{
    if (!dict || !PyDict_Check(dict) || !key || !value) return -2;
    int rc = PyDict_SetItem(dict, key, value);
    Py_DECREF(value);
    return rc;
}

int DICT_SETITEMSTR_DROP(PyObject *dict, const char *key, PyObject *value)
{
    if (!dict || !PyDict_Check(dict) || !key || !value) return -2;
    int rc = PyDict_SetItemString(dict, key, value);
    Py_DECREF(value);
    return rc;
}


PyObject *JM_EscapeStrFromBuffer(fz_context *ctx, fz_buffer *buff)
{
    if (!buff) return PyUnicode_FromString("");
    unsigned char *s = NULL;
    size_t len = fz_buffer_storage(ctx, buff, &s);
    PyObject *val = PyUnicode_DecodeRawUnicodeEscape(s, (Py_ssize_t) len, "replace");
    if (!val)
    {
        val = PyUnicode_FromString("");
        PyErr_Clear();
    }
    return val;
}

PyObject *JM_UnicodeFromStr(const char *c)
{
    if (!c) return PyUnicode_FromString("");
    PyObject *val = Py_BuildValue("s", c);
    if (!val)
    {
        val = PyUnicode_FromString("");
        PyErr_Clear();
    }
    return val;
}

PyObject *JM_EscapeStrFromStr(const char *c)
{
    if (!c) return PyUnicode_FromString("");
    PyObject *val = PyUnicode_DecodeRawUnicodeEscape(c, (Py_ssize_t) strlen(c), "replace");
    if (!val)
    {
        val = PyUnicode_FromString("");
        PyErr_Clear();
    }
    return val;
}

// redirect MuPDF warnings
void JM_mupdf_warning(void *user, const char *message)
{
    LIST_APPEND_DROP(JM_mupdf_warnings_store, JM_EscapeStrFromStr(message));
}

// redirect MuPDF errors
void JM_mupdf_error(void *user, const char *message)
{
    LIST_APPEND_DROP(JM_mupdf_warnings_store, JM_EscapeStrFromStr(message));
    if (JM_mupdf_show_errors == Py_True)
        PySys_WriteStderr("mupdf: %s\n", message);
}

// a simple tracer
void JM_TRACE(const char *id)
{
    PySys_WriteStdout("%s\n", id);
}


// put a warning on Python-stdout
void JM_Warning(const char *id)
{
    PySys_WriteStdout("warning: %s\n", id);
}

#if JM_MEMORY == 1
//-----------------------------------------------------------------------------
// The following 3 functions replace MuPDF standard memory allocation.
// This will ensure, that MuPDF memory handling becomes part of Python's
// memory management.
//-----------------------------------------------------------------------------
static void *JM_Py_Malloc(void *opaque, size_t size)
{
    return PyMem_Malloc(size);
}

static void *JM_Py_Realloc(void *opaque, void *old, size_t size)
{
    return PyMem_Realloc(old, size);
}

static void JM_PY_Free(void *opaque, void *ptr)
{
    PyMem_Free(ptr);
}

const fz_alloc_context JM_Alloc_Context =
{
	NULL,
	JM_Py_Malloc,
	JM_Py_Realloc,
	JM_PY_Free
};
#endif

// return Python bools for a given integer
PyObject *JM_BOOL(int v)
{
    if (v == 0)
        Py_RETURN_FALSE;
    Py_RETURN_TRUE;
}

PyObject *JM_fitz_config()
{
#if defined(TOFU)
#define have_TOFU JM_BOOL(0)
#else
#define have_TOFU JM_BOOL(1)
#endif
#if defined(TOFU_CJK)
#define have_TOFU_CJK JM_BOOL(0)
#else
#define have_TOFU_CJK JM_BOOL(1)
#endif
#if defined(TOFU_CJK_EXT)
#define have_TOFU_CJK_EXT JM_BOOL(0)
#else
#define have_TOFU_CJK_EXT JM_BOOL(1)
#endif
#if defined(TOFU_CJK_LANG)
#define have_TOFU_CJK_LANG JM_BOOL(0)
#else
#define have_TOFU_CJK_LANG JM_BOOL(1)
#endif
#if defined(TOFU_EMOJI)
#define have_TOFU_EMOJI JM_BOOL(0)
#else
#define have_TOFU_EMOJI JM_BOOL(1)
#endif
#if defined(TOFU_HISTORIC)
#define have_TOFU_HISTORIC JM_BOOL(0)
#else
#define have_TOFU_HISTORIC JM_BOOL(1)
#endif
#if defined(TOFU_SYMBOL)
#define have_TOFU_SYMBOL JM_BOOL(0)
#else
#define have_TOFU_SYMBOL JM_BOOL(1)
#endif
#if defined(TOFU_SIL)
#define have_TOFU_SIL JM_BOOL(0)
#else
#define have_TOFU_SIL JM_BOOL(1)
#endif
#if defined(TOFU_BASE14)
#define have_TOFU_BASE14 JM_BOOL(0)
#else
#define have_TOFU_BASE14 JM_BOOL(1)
#endif
    PyObject *dict = PyDict_New();
    DICT_SETITEMSTR_DROP(dict, "plotter-g", JM_BOOL(FZ_PLOTTERS_G));
    DICT_SETITEMSTR_DROP(dict, "plotter-rgb", JM_BOOL(FZ_PLOTTERS_RGB));
    DICT_SETITEMSTR_DROP(dict, "plotter-cmyk", JM_BOOL(FZ_PLOTTERS_CMYK));
    DICT_SETITEMSTR_DROP(dict, "plotter-n", JM_BOOL(FZ_PLOTTERS_N));
    DICT_SETITEMSTR_DROP(dict, "pdf", JM_BOOL(FZ_ENABLE_PDF));
    DICT_SETITEMSTR_DROP(dict, "xps", JM_BOOL(FZ_ENABLE_XPS));
    DICT_SETITEMSTR_DROP(dict, "svg", JM_BOOL(FZ_ENABLE_SVG));
    DICT_SETITEMSTR_DROP(dict, "cbz", JM_BOOL(FZ_ENABLE_CBZ));
    DICT_SETITEMSTR_DROP(dict, "img", JM_BOOL(FZ_ENABLE_IMG));
    DICT_SETITEMSTR_DROP(dict, "html", JM_BOOL(FZ_ENABLE_HTML));
    DICT_SETITEMSTR_DROP(dict, "epub", JM_BOOL(FZ_ENABLE_EPUB));
    DICT_SETITEMSTR_DROP(dict, "jpx", JM_BOOL(FZ_ENABLE_JPX));
    DICT_SETITEMSTR_DROP(dict, "js", JM_BOOL(FZ_ENABLE_JS));
    DICT_SETITEMSTR_DROP(dict, "tofu", have_TOFU);
    DICT_SETITEMSTR_DROP(dict, "tofu-cjk", have_TOFU_CJK);
    DICT_SETITEMSTR_DROP(dict, "tofu-cjk-ext", have_TOFU_CJK_EXT);
    DICT_SETITEMSTR_DROP(dict, "tofu-cjk-lang", have_TOFU_CJK_LANG);
    DICT_SETITEMSTR_DROP(dict, "tofu-emoji", have_TOFU_EMOJI);
    DICT_SETITEMSTR_DROP(dict, "tofu-historic", have_TOFU_HISTORIC);
    DICT_SETITEMSTR_DROP(dict, "tofu-symbol", have_TOFU_SYMBOL);
    DICT_SETITEMSTR_DROP(dict, "tofu-sil", have_TOFU_SIL);
    DICT_SETITEMSTR_DROP(dict, "icc", JM_BOOL(FZ_ENABLE_ICC));
    DICT_SETITEMSTR_DROP(dict, "base14", have_TOFU_BASE14);
    DICT_SETITEMSTR_DROP(dict, "py-memory", JM_BOOL(JM_MEMORY));
    return dict;
}

//----------------------------------------------------------------------------
// Update a color float array with values from a Python sequence.
// Any error condition is treated as a no-op.
//----------------------------------------------------------------------------
void JM_color_FromSequence(PyObject *color, int *n, float col[4])
{
    if (!color || (!PySequence_Check(color) && !PyFloat_Check(color)))
    {
        *n = 1;
        return;
    }
    if (PyFloat_Check(color)) // maybe just a single float
    {
        float c = (float) PyFloat_AsDouble(color);
        if (!INRANGE(c, 0.0f, 1.0f))
        {
            *n = 1;
            return;
        }
        col[0] = c;
        *n = 1;
        return;
    }

    int len = (int) PySequence_Size(color), i;
    if (!INRANGE(len, 1, 4) || len == 2)
    {
        *n = 1;
        return;
    }

    float mcol[4] = {0,0,0,0}; // local color storage
    for (i = 0; i < len; i++)
    {
        mcol[i] = (float) PyFloat_AsDouble(PySequence_ITEM(color, i));
        if (PyErr_Occurred())
        {
            PyErr_Clear(); // reset Py error indicator
            return;
        }
        if (!INRANGE(mcol[i], 0.0f, 1.0f)) return;
    }

    *n = len;
    for (i = 0; i < len; i++)
        col[i] = mcol[i];
    return;
}

// return extension for fitz image type
const char *JM_image_extension(int type)
{
    switch (type)
    {
        case(FZ_IMAGE_RAW): return "raw";
        case(FZ_IMAGE_FLATE): return "flate";
        case(FZ_IMAGE_LZW): return "lzw";
        case(FZ_IMAGE_RLD): return "rld";
        case(FZ_IMAGE_BMP): return "bmp";
        case(FZ_IMAGE_GIF): return "gif";
        case(FZ_IMAGE_JBIG2): return "jbig2";
        case(FZ_IMAGE_JPEG): return "jpeg";
        case(FZ_IMAGE_JPX): return "jpx";
        case(FZ_IMAGE_JXR): return "jxr";
        case(FZ_IMAGE_PNG): return "png";
        case(FZ_IMAGE_PNM): return "pnm";
        case(FZ_IMAGE_TIFF): return "tiff";
        default: return "n/a";
    }
}

//----------------------------------------------------------------------------
// Turn fz_buffer into a Python bytes object
//----------------------------------------------------------------------------
PyObject *JM_BinFromBuffer(fz_context *ctx, fz_buffer *buffer)
{

#if  PY_VERSION_HEX < 0x03000000
 #define PyBytes_FromString(x) PyString_FromString(x)
 #define PyBytes_FromStringAndSize(c, l) PyString_FromStringAndSize(c, l)
#endif

    if (!buffer)
    {
        return PyBytes_FromString("");
    }
    char *c = NULL;
    size_t len = fz_buffer_storage(ctx, buffer, &c);
    return PyBytes_FromStringAndSize(c, (Py_ssize_t) len);
}

//----------------------------------------------------------------------------
// Turn fz_buffer into a Python bytearray object
//----------------------------------------------------------------------------
PyObject *JM_BArrayFromBuffer(fz_context *ctx, fz_buffer *buffer)
{
    if (!buffer)
    {
        return PyByteArray_FromStringAndSize("", 0);
    }
    char *c = NULL;
    size_t len = fz_buffer_storage(ctx, buffer, &c);
    return PyByteArray_FromStringAndSize(c, (Py_ssize_t) len);
}

//----------------------------------------------------------------------------
// Turn fz_buffer to a base64 encoded bytes object
//----------------------------------------------------------------------------
PyObject *JM_B64FromBuffer(fz_context *ctx, fz_buffer *buffer)
{
    PyObject *bytes = PyBytes_FromString("");
    char *c = NULL;
    char *b64 = NULL;
    if (buffer)
    {
        size_t len = fz_buffer_storage(ctx, buffer, &c);
        fz_buffer *res = fz_new_buffer(ctx, len);
        fz_output *out = fz_new_output_with_buffer(ctx, res);
        fz_write_base64(ctx, out, (const unsigned char *) c, (int) len, 0);
        size_t nlen = fz_buffer_storage(ctx, res, &b64);
        Py_DECREF(bytes);
        bytes = PyBytes_FromStringAndSize(b64, (Py_ssize_t) nlen);
        fz_drop_buffer(ctx, res);
        fz_drop_output(ctx, out);
    }
    return bytes;
}

//----------------------------------------------------------------------------
// compress char* into a new buffer
//----------------------------------------------------------------------------
fz_buffer *JM_compress_buffer(fz_context *ctx, fz_buffer *inbuffer)
{
    fz_buffer *buf = NULL;
    fz_try(ctx)
    {
        size_t compressed_length = 0;
        unsigned char *data = fz_new_deflated_data_from_buffer(ctx,
                              &compressed_length, inbuffer, FZ_DEFLATE_BEST);
        if (data == NULL || compressed_length == 0)
            return NULL;
        buf = fz_new_buffer_from_data(ctx, data, compressed_length);
        fz_resize_buffer(ctx, buf, compressed_length);
    }
    fz_catch(ctx)
    {
        fz_drop_buffer(ctx, buf);
        fz_rethrow(ctx);
    }
    return buf;
}

//----------------------------------------------------------------------------
// update a stream object
// compress stream when beneficial
//----------------------------------------------------------------------------
void JM_update_stream(fz_context *ctx, pdf_document *doc, pdf_obj *obj, fz_buffer *buffer, int compress)
{
    
    fz_buffer *nres = NULL;
    size_t len = fz_buffer_storage(ctx, buffer, NULL);
    size_t nlen = len;

    if (len > 30)       // ignore small stuff
    {
        nres = JM_compress_buffer(ctx, buffer);
        nlen = fz_buffer_storage(ctx, nres, NULL);
    }

    if (nlen < len && nres && compress==1)  // was it worth the effort?
    {
        pdf_dict_put(ctx, obj, PDF_NAME(Filter), PDF_NAME(FlateDecode));
        pdf_update_stream(ctx, doc, obj, nres, 1);
    }
    else
    {
        pdf_update_stream(ctx, doc, obj, buffer, 0);
    }
    fz_drop_buffer(ctx, nres);
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
// Make fz_buffer from a PyBytes, PyByteArray, io.BytesIO object
//----------------------------------------------------------------------------
fz_buffer *JM_BufferFromBytes(fz_context *ctx, PyObject *stream)
{
    if (!stream) return NULL;
    if (stream == Py_None) return NULL;
    char *c = NULL;
    PyObject *mybytes = NULL;
    size_t len = 0;
    fz_buffer *res = NULL;
    fz_var(res);
    fz_try(ctx)
    {
        if (PyBytes_Check(stream))
        {
            c = PyBytes_AS_STRING(stream);
            len = (size_t) PyBytes_GET_SIZE(stream);
        }
        else if (PyByteArray_Check(stream))
        {
            c = PyByteArray_AS_STRING(stream);
            len = (size_t) PyByteArray_GET_SIZE(stream);
        }
        else if (PyObject_HasAttrString(stream, "getvalue"))
        {   // we assume here that this delivers what we expect
            mybytes = PyObject_CallMethod(stream, "getvalue", NULL);
            c = PyBytes_AS_STRING(mybytes);
            len = (size_t) PyBytes_GET_SIZE(mybytes);
        }
        // all the above leave c as NULL pointer if unsuccessful
        if (c) res = fz_new_buffer_from_copied_data(ctx, c, len);
    }
    fz_always(ctx)
    {
        Py_CLEAR(mybytes);
        PyErr_Clear();
    }
    fz_catch(ctx)
    {
        fz_drop_buffer(ctx, res);
        fz_rethrow(ctx);
    }
    return res;
}

//----------------------------------------------------------------------------
// Modified copy of SWIG_Python_str_AsChar
// If Py3, the SWIG original v3.0.12 does *not* deliver NULL for a
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
    size_t l = len + 1;
    newstr = JM_Alloc(char, l);
    memcpy(newstr, cstr, l);
    Py_XDECREF(xstr);
  }
  return newstr;
#else
  return PyString_AsString(str);
#endif
}

#if PY_VERSION_HEX >= 0x03000000
#  define JM_Python_str_DelForPy3(x) JM_Free(x)
#else
#  define JM_Python_str_DelForPy3(x)
#endif

//----------------------------------------------------------------------------
// Deep-copies a specified source page to the target location.
// Modified copy of function of pdfmerge.c: we also copy annotations, but
// we skip **link** annotations. In addition we rotate output.
//----------------------------------------------------------------------------
void page_merge(fz_context *ctx, pdf_document *doc_des, pdf_document *doc_src, int page_from, int page_to, int rotate, int links, int copy_annots, pdf_graft_map *graft_map)
{
    pdf_obj *page_ref = NULL;
    pdf_obj *page_dict = NULL;
    pdf_obj *obj = NULL, *ref = NULL;

    // list of object types (per page) we want to copy
    pdf_obj *known_page_objs[] = {
        PDF_NAME(Contents),
        PDF_NAME(Resources),
        PDF_NAME(MediaBox),
        PDF_NAME(CropBox),
        PDF_NAME(BleedBox),
        PDF_NAME(TrimBox),
        PDF_NAME(ArtBox),
        PDF_NAME(Rotate),
        PDF_NAME(UserUnit)
    };
    int i, n = nelem(known_page_objs);  // number of list elements
    fz_var(obj);
    fz_var(ref);
    fz_var(page_dict);
    fz_try(ctx)
    {
        page_ref = pdf_lookup_page_obj(ctx, doc_src, page_from);
        pdf_flatten_inheritable_page_items(ctx, page_ref);

        // make a new page
        page_dict = pdf_new_dict(ctx, doc_des, 4);
        pdf_dict_put(ctx, page_dict, PDF_NAME(Type), PDF_NAME(Page));

        // copy objects of source page into it
        for (i = 0; i < n; i++)
        {
            obj = pdf_dict_get(ctx, page_ref, known_page_objs[i]);
            if (obj != NULL)
                pdf_dict_put_drop(ctx, page_dict, known_page_objs[i], pdf_graft_mapped_object(ctx, graft_map, obj));
        }

        if (copy_annots)  // we shall copy annotations also
        {
            pdf_obj *old_annots = pdf_dict_get(ctx, page_ref, PDF_NAME(Annots));
            if (old_annots)  // there is an annot array
            {
                n = pdf_array_len(ctx, old_annots);
                pdf_obj *new_annots = pdf_new_array(ctx, doc_des, n);
                for (i = 0; i < n; i++)
                {
                    pdf_obj *o = pdf_array_get(ctx, old_annots, i);
                    if (!pdf_name_eq(ctx, pdf_dict_get(ctx, o, PDF_NAME(Subtype)),
                                     PDF_NAME(Link)))
                    {
                        pdf_array_push_drop(ctx, new_annots,
                                pdf_graft_mapped_object(ctx, graft_map, o));
                    }
                }
                if (pdf_array_len(ctx, new_annots))
                {
                    pdf_dict_put_drop(ctx, page_dict, PDF_NAME(Annots), new_annots);
                }
                else
                {
                    pdf_drop_obj(ctx, new_annots);
                }
            }
        }
        // rotate the page as requested
        if (rotate != -1)
        {
            pdf_dict_put_int(ctx, page_dict, PDF_NAME(Rotate), (int64_t) rotate);
        }
        // Now add the page dictionary to dest PDF
        obj = pdf_add_object(ctx, doc_des, page_dict);

        // Get indirect ref of the new page
        int num = pdf_to_num(ctx, obj);
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
void merge_range(fz_context *ctx, pdf_document *doc_des, pdf_document *doc_src, int spage, int epage, int apage, int rotate, int links, int annots)
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
                page_merge(ctx, doc_des, doc_src, page, afterpage, rotate, links, annots, graft_map);
        else
            for (page = spage; page >= epage; page--, afterpage++)
                page_merge(ctx, doc_des, doc_src, page, afterpage, rotate, links, annots, graft_map);
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
// Return list of outline xref numbers. Recursive function. Arguments:
// 'obj' first OL item
// 'xrefs' empty Python list
//----------------------------------------------------------------------------
PyObject *JM_outline_xrefs(fz_context *ctx, pdf_obj *obj, PyObject *xrefs)
{
    pdf_obj *first, *parent, *thisobj;
    if (!obj) return xrefs;
    thisobj = obj;
    while (thisobj)
    {
        LIST_APPEND_DROP(xrefs, Py_BuildValue("i", pdf_to_num(ctx, thisobj)));
        first = pdf_dict_get(ctx, thisobj, PDF_NAME(First));   // try go down
        if (first) xrefs = JM_outline_xrefs(ctx, first, xrefs);
        thisobj = pdf_dict_get(ctx, thisobj, PDF_NAME(Next));  // try go next
        parent = pdf_dict_get(ctx, thisobj, PDF_NAME(Parent)); // get parent
        if (!thisobj) thisobj = parent;      /* goto parent if no next exists */
    }
    return xrefs;
}

//-----------------------------------------------------------------------------
// Return the contents of a font file, identified by xref
//-----------------------------------------------------------------------------
fz_buffer *JM_get_fontbuffer(fz_context *ctx, pdf_document *doc, int xref)
{
    if (xref < 1) return NULL;
    pdf_obj *o, *obj = NULL, *desft, *stream = NULL;
    char *ext = "";
    o = pdf_load_object(ctx, doc, xref);
    desft = pdf_dict_get(ctx, o, PDF_NAME(DescendantFonts));
    if (desft)
    {
        obj = pdf_resolve_indirect(ctx, pdf_array_get(ctx, desft, 0));
        obj = pdf_dict_get(ctx, obj, PDF_NAME(FontDescriptor));
    }
    else
        obj = pdf_dict_get(ctx, o, PDF_NAME(FontDescriptor));

    if (!obj)
    {
        pdf_drop_obj(ctx, o);
        PySys_WriteStdout("invalid font - FontDescriptor missing");
        return NULL;
    }
    pdf_drop_obj(ctx, o);
    o = obj;

    obj = pdf_dict_get(ctx, o, PDF_NAME(FontFile));
    if (obj) stream = obj;             // ext = "pfa"

    obj = pdf_dict_get(ctx, o, PDF_NAME(FontFile2));
    if (obj) stream = obj;             // ext = "ttf"

    obj = pdf_dict_get(ctx, o, PDF_NAME(FontFile3));
    if (obj)
    {
        stream = obj;

        obj = pdf_dict_get(ctx, obj, PDF_NAME(Subtype));
        if (obj && !pdf_is_name(ctx, obj))
        {
            PySys_WriteStdout("invalid font descriptor subtype");
            return NULL;
        }

        if (pdf_name_eq(ctx, obj, PDF_NAME(Type1C)))
            ext = "cff";
        else if (pdf_name_eq(ctx, obj, PDF_NAME(CIDFontType0C)))
            ext = "cid";
        else if (pdf_name_eq(ctx, obj, PDF_NAME(OpenType)))
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
// Return the file extension of a font file, identified by xref
//-----------------------------------------------------------------------------
char *JM_get_fontextension(fz_context *ctx, pdf_document *doc, int xref)
{
    if (xref < 1) return "n/a";
    pdf_obj *o, *obj = NULL, *desft;
    o = pdf_load_object(ctx, doc, xref);
    desft = pdf_dict_get(ctx, o, PDF_NAME(DescendantFonts));
    if (desft)
    {
        obj = pdf_resolve_indirect(ctx, pdf_array_get(ctx, desft, 0));
        obj = pdf_dict_get(ctx, obj, PDF_NAME(FontDescriptor));
    }
    else
        obj = pdf_dict_get(ctx, o, PDF_NAME(FontDescriptor));

    pdf_drop_obj(ctx, o);
    if (!obj) return "n/a";           // this is a base-14 font

    o = obj;                           // we have the FontDescriptor

    obj = pdf_dict_get(ctx, o, PDF_NAME(FontFile));
    if (obj) return "pfa";

    obj = pdf_dict_get(ctx, o, PDF_NAME(FontFile2));
    if (obj) return "ttf";

    obj = pdf_dict_get(ctx, o, PDF_NAME(FontFile3));
    if (obj)
    {
        obj = pdf_dict_get(ctx, obj, PDF_NAME(Subtype));
        if (obj && !pdf_is_name(ctx, obj))
        {
            PySys_WriteStdout("invalid font descriptor subtype");
            return "n/a";
        }
        if (pdf_name_eq(ctx, obj, PDF_NAME(Type1C)))
            return "cff";
        else if (pdf_name_eq(ctx, obj, PDF_NAME(CIDFontType0C)))
            return "cid";
        else if (pdf_name_eq(ctx, obj, PDF_NAME(OpenType)))
            return "otf";
        else
            PySys_WriteStdout("unhandled font type '%s'", pdf_to_name(ctx, obj));
    }

    return "n/a";
}


//-----------------------------------------------------------------------------
// create PDF object from given string (new in v1.14.0: MuPDF dropped it)
//-----------------------------------------------------------------------------
pdf_obj *JM_pdf_obj_from_str(fz_context *ctx, pdf_document *doc, char *src)
{
    pdf_obj *result = NULL;
    pdf_lexbuf lexbuf;
    fz_stream *stream = fz_open_memory(ctx, (unsigned char *)src, strlen(src));

    pdf_lexbuf_init(ctx, &lexbuf, PDF_LEXBUF_SMALL);

    fz_try(ctx)
        result = pdf_parse_stm_obj(ctx, doc, stream, &lexbuf);

    fz_always(ctx)
    {
        pdf_lexbuf_fin(ctx, &lexbuf);
        fz_drop_stream(ctx, stream);
    }

    fz_catch(ctx)
        fz_rethrow(ctx);

    return result;

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


//----------------------------------------------------------------------------
// return normalized /Rotate value
//----------------------------------------------------------------------------
int JM_norm_rotation(int rotate)
{
    while (rotate < 0) rotate += 360;
    while (rotate >= 360) rotate -= 360;
    if (rotate % 90 != 0) return 0;
    return rotate;
}


//----------------------------------------------------------------------------
// return a PDF page's /Rotate value: one of (0, 90, 180, 270)
//----------------------------------------------------------------------------
int JM_page_rotation(fz_context *ctx, pdf_page *page)
{
    int rotate = 0;
    fz_try(ctx)
    {
        rotate = pdf_to_int(ctx,
                pdf_dict_get_inheritable(ctx, page->obj, PDF_NAME(Rotate)));
        rotate = JM_norm_rotation(rotate);
    }
    fz_catch(ctx) return 0;
    return rotate;
}


//----------------------------------------------------------------------------
// return a PDF page's MediaBox
//----------------------------------------------------------------------------
fz_rect JM_mediabox(fz_context *ctx, pdf_page *page)
{
    fz_rect mediabox, page_mediabox;
    pdf_obj *obj;
    float userunit = 1;

    obj = pdf_dict_get(ctx, page->obj, PDF_NAME(UserUnit));
    if (pdf_is_real(ctx, obj))
        userunit = pdf_to_real(ctx, obj);

    mediabox = pdf_to_rect(ctx, pdf_dict_get_inheritable(ctx, page->obj,
        PDF_NAME(MediaBox)));
    if (fz_is_empty_rect(mediabox) || fz_is_infinite_rect(mediabox))
    {
        mediabox.x0 = 0;
        mediabox.y0 = 0;
        mediabox.x1 = 612;
        mediabox.y1 = 792;
    }

    page_mediabox.x0 = fz_min(mediabox.x0, mediabox.x1);
    page_mediabox.y0 = fz_min(mediabox.y0, mediabox.y1);
    page_mediabox.x1 = fz_max(mediabox.x0, mediabox.x1);
    page_mediabox.y1 = fz_max(mediabox.y0, mediabox.y1);

    if (page_mediabox.x1 - page_mediabox.x0 < 1 ||
        page_mediabox.y1 - page_mediabox.y0 < 1)
        page_mediabox = fz_unit_rect;

    return page_mediabox;
}


//----------------------------------------------------------------------------
// return a PDF page's CropBox
//----------------------------------------------------------------------------
fz_rect JM_cropbox(fz_context *ctx, pdf_page *page)
{
    fz_rect mediabox = JM_mediabox(ctx, page);
    fz_rect cropbox = pdf_to_rect(ctx,
                pdf_dict_get_inheritable(ctx, page->obj, PDF_NAME(CropBox)));
    if (fz_is_infinite_rect(cropbox) || fz_is_empty_rect(cropbox))
        return mediabox;
    float y0 = mediabox.y1 - cropbox.y1;
    float y1 = mediabox.y1 - cropbox.y0;
    cropbox.y0 = y0;
    cropbox.y1 = y1;
    return cropbox;
}


//----------------------------------------------------------------------------
// calculate width and height of the UNROTATED page
//----------------------------------------------------------------------------
fz_point JM_cropbox_size(fz_context *ctx, pdf_page *page)
{
    fz_point size;
    fz_try(ctx)
    {
        fz_rect rect = JM_cropbox(ctx, page);
        float w = (rect.x0 < rect.x1 ? rect.x1 - rect.x0 : rect.x0 - rect.x1);
        float h = (rect.y0 < rect.y1 ? rect.y1 - rect.y0 : rect.y0 - rect.y1);
        size = fz_make_point(w, h);
    }
    fz_catch(ctx) fz_rethrow(ctx);
    return size;
}


//----------------------------------------------------------------------------
// calculate page rotation matrices
//----------------------------------------------------------------------------
fz_matrix JM_rotate_page_matrix(fz_context *ctx, pdf_page *page)
{
    if (!page) return fz_identity;  // no valid pdf page given
    int rotation = JM_page_rotation(ctx, page);
    if (rotation == 0) return fz_identity;  // no rotation
    fz_matrix m;
    fz_point cb_size = JM_cropbox_size(ctx, page);
    float w = cb_size.x;
    float h = cb_size.y;
    if (rotation == 90)
        m = fz_make_matrix(0, 1, -1, 0, h, 0);
    else if (rotation == 180)
        m = fz_make_matrix(-1, 0, 0, -1, w, h);
    else
        m = fz_make_matrix(0, -1, 1, 0, 0, w);
    return m;
}


fz_matrix JM_derotate_page_matrix(fz_context *ctx, pdf_page *page)
{  // just the inverse of rotation
    return fz_invert_matrix(JM_rotate_page_matrix(ctx, page));
}
%}
