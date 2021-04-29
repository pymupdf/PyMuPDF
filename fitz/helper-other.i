%{
fz_buffer *JM_object_to_buffer(fz_context *ctx, pdf_obj *val, int a, int b);
PyObject *JM_EscapeStrFromBuffer(fz_context *ctx, fz_buffer *buff);
pdf_obj *JM_pdf_obj_from_str(fz_context *ctx, pdf_document *doc, char *src);

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

//----------------------------------
// Set a PDF dict key to some value
//----------------------------------
static pdf_obj
*JM_set_object_value(fz_context *ctx, pdf_obj *obj, const char *key, char *value)
{
    fz_buffer *res = NULL;
    pdf_obj *new_obj = NULL, *testkey = NULL;
    PyObject *skey = PyUnicode_FromString(key);  // Python version of dict key
    PyObject *slash = PyUnicode_FromString("/");  // PDF path separator
    PyObject *list = NULL, *newval=NULL, *newstr=NULL, *nullval=NULL;
    const char eyecatcher[] = "fitz: replace me!";
    fz_try(ctx)
    {
        pdf_document *pdf = pdf_get_bound_document(ctx, obj);
        // split PDF key at path seps and take last key part
        list = PyUnicode_Split(skey, slash, -1);
        Py_ssize_t len = PySequence_Size(list);
        Py_ssize_t i = len - 1;
        Py_DECREF(skey);
        skey = PySequence_GetItem(list, i);

        PySequence_DelItem(list, i);  // del the last sub-key
        len =  PySequence_Size(list);  // remaining length
        testkey = pdf_dict_getp(ctx, obj, key);  // check if key already exists
        if (!testkey) {
            /*-----------------------------------------------------------------
            No, it will be created here. But we cannot allow this happening if
            indirect objects are referenced. So we check all higher level
            sub-paths for indirect references.
            -----------------------------------------------------------------*/
            while (len > 0) {
                PyObject *t = PyUnicode_Join(slash, list);  // next high level
                if (pdf_is_indirect(ctx, pdf_dict_getp(ctx, obj, JM_StrAsChar(t)))) {
                    Py_DECREF(t);
                    fz_throw(ctx, FZ_ERROR_GENERIC, "path to '%s' has indirects", JM_StrAsChar(skey));
                }
                PySequence_DelItem(list, len - 1);  // del last sub-key
                len = PySequence_Size(list);  // remaining length
                Py_DECREF(t);
            }
        }
        // Insert our eyecatcher. Will create all sub-paths in the chain, or
        // respectively remove old value of key-path.
        pdf_dict_putp_drop(ctx, obj, key, pdf_new_text_string(ctx, eyecatcher));
        testkey = pdf_dict_getp(ctx, obj, key);
        if (!pdf_is_string(ctx, testkey)) {
            fz_throw(ctx, FZ_ERROR_GENERIC, "cannot insert value for '%s'", key);
        }
        const char *temp = pdf_to_text_string(ctx, testkey);
        if (strcmp(temp, eyecatcher) != 0) {
            fz_throw(ctx, FZ_ERROR_GENERIC, "cannot insert value for '%s'", key);
        }
        // read the result as a string
        res = JM_object_to_buffer(ctx, obj, 1, 0);
        PyObject *objstr = JM_EscapeStrFromBuffer(ctx, res);

        // replace 'eyecatcher' by desired 'value'
        nullval = PyUnicode_FromFormat("/%s(%s)", JM_StrAsChar(skey), eyecatcher);
        newval = PyUnicode_FromFormat("/%s %s", JM_StrAsChar(skey), value);
        newstr = PyUnicode_Replace(objstr, nullval, newval, 1);

        // make PDF object from resulting string
        new_obj = JM_pdf_obj_from_str(gctx, pdf, JM_StrAsChar(newstr));
    }
    fz_always(ctx) {
        fz_drop_buffer(ctx, res);
        Py_CLEAR(skey);
        Py_CLEAR(slash);
        Py_CLEAR(list);
        Py_CLEAR(newval);
        Py_CLEAR(newstr);
        Py_CLEAR(nullval);
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return new_obj;
}


static void
JM_get_page_labels(fz_context *ctx, PyObject *liste, pdf_obj *nums)
{
    int pno, i, n = pdf_array_len(ctx, nums);
    char *c = NULL;
    pdf_obj *val;
    fz_buffer *res = NULL;
    for (i = 0; i < n; i += 2) {
        pdf_obj *key = pdf_resolve_indirect(ctx, pdf_array_get(ctx, nums, i));
        pno = pdf_to_int(ctx, key);
        val = pdf_resolve_indirect(ctx, pdf_array_get(ctx, nums, i + 1));
        res = JM_object_to_buffer(ctx, val, 1, 0);
        fz_buffer_storage(ctx, res, &c);
        LIST_APPEND_DROP(liste, Py_BuildValue("is", pno, c));
        fz_drop_buffer(ctx, res);
    }
}


PyObject *JM_EscapeStrFromBuffer(fz_context *ctx, fz_buffer *buff)
{
    if (!buff) return EMPTY_STRING;
    unsigned char *s = NULL;
    size_t len = fz_buffer_storage(ctx, buff, &s);
    PyObject *val = PyUnicode_DecodeRawUnicodeEscape((const char *) s, (Py_ssize_t) len, "replace");
    if (!val) {
        val = EMPTY_STRING;
        PyErr_Clear();
    }
    return val;
}

PyObject *JM_UnicodeFromBuffer(fz_context *ctx, fz_buffer *buff)
{
    unsigned char *s = NULL;
    Py_ssize_t len = (Py_ssize_t) fz_buffer_storage(ctx, buff, &s);
    PyObject *val = PyUnicode_DecodeUTF8((const char *) s, len, "replace");
    if (!val) {
        val = EMPTY_STRING;
        PyErr_Clear();
    }
    return val;
}

PyObject *JM_UnicodeFromStr(const char *c)
{
    if (!c) return EMPTY_STRING;
    PyObject *val = Py_BuildValue("s", c);
    if (!val) {
        val = EMPTY_STRING;
        PyErr_Clear();
    }
    return val;
}

PyObject *JM_EscapeStrFromStr(const char *c)
{
    if (!c) return EMPTY_STRING;
    PyObject *val = PyUnicode_DecodeRawUnicodeEscape(c, (Py_ssize_t) strlen(c), "replace");
    if (!val) {
        val = EMPTY_STRING;
        PyErr_Clear();
    }
    return val;
}


// list of valid unicodes of a fz_font
void JM_valid_chars(fz_context *ctx, fz_font *font, void *arr)
{
	FT_Face face = font->ft_face;
	FT_ULong ucs;
	FT_UInt gid;
	long *table = (long *)arr;
	fz_lock(ctx, FZ_LOCK_FREETYPE);
	ucs = FT_Get_First_Char(face, &gid);
	while (gid > 0)
	{
		if (gid < (FT_ULong)face->num_glyphs && face->num_glyphs > 0)
			table[gid] = (long)ucs;
		ucs = FT_Get_Next_Char(face, ucs, &gid);
	}
	fz_unlock(ctx, FZ_LOCK_FREETYPE);
	return;
}


// redirect MuPDF warnings
void JM_mupdf_warning(void *user, const char *message)
{
    LIST_APPEND_DROP(JM_mupdf_warnings_store, JM_EscapeStrFromStr(message));
    if (JM_mupdf_show_warnings) {
        PySys_WriteStderr("mupdf: %s\n", message);
    }
}

// redirect MuPDF errors
void JM_mupdf_error(void *user, const char *message)
{
    LIST_APPEND_DROP(JM_mupdf_warnings_store, JM_EscapeStrFromStr(message));
    if (JM_mupdf_show_errors) {
        PySys_WriteStderr("mupdf: %s\n", message);
    }
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
    void *mem = PyMem_Malloc((Py_ssize_t) size);
    if (mem) return mem;
    fz_throw(gctx, FZ_ERROR_MEMORY, "malloc of %zu bytes failed", size);
}

static void *JM_Py_Realloc(void *opaque, void *old, size_t size)
{
    void *mem = PyMem_Realloc(old, (Py_ssize_t) size);
    if (mem) return mem;
    fz_throw(gctx, FZ_ERROR_MEMORY, "realloc of %zu bytes failed", size);
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

// return Python bool for a given integer
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
    if (!color || (!PySequence_Check(color) && !PyFloat_Check(color))) {
        *n = 1;
        return;
    }
    if (PyFloat_Check(color)) { // maybe just a single float
        float c = (float) PyFloat_AsDouble(color);
        if (!INRANGE(c, 0, 1)) {
            *n = 1;
            return;
        }
        col[0] = c;
        *n = 1;
        return;
    }

    int len = (int) PySequence_Size(color), rc;
    if (!INRANGE(len, 1, 4) || len == 2) {
        *n = 1;
        return;
    }

    double mcol[4] = {0,0,0,0}; // local color storage
    Py_ssize_t i;
    for (i = 0; i < len; i++) {
        rc = JM_FLOAT_ITEM(color, i, &mcol[i]);
        if (!INRANGE(mcol[i], 0, 1) || rc == 1) mcol[i] = 1;
    }

    *n = len;
    for (i = 0; i < len; i++)
        col[i] = (float) mcol[i];
    return;
}

// return extension for fitz image type
const char *JM_image_extension(int type)
{
    switch (type) {
        case(FZ_IMAGE_RAW): return "raw";
        case(FZ_IMAGE_FLATE): return "flate";
        case(FZ_IMAGE_LZW): return "lzw";
        case(FZ_IMAGE_RLD): return "rld";
        case(FZ_IMAGE_BMP): return "bmp";
        case(FZ_IMAGE_GIF): return "gif";
        case(FZ_IMAGE_JBIG2): return "jb2";
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

    if (!buffer) {
        return PyBytes_FromString("");
    }
    unsigned char *c = NULL;
    size_t len = fz_buffer_storage(ctx, buffer, &c);
    return PyBytes_FromStringAndSize((const char *) c, (Py_ssize_t) len);
}

//----------------------------------------------------------------------------
// Turn fz_buffer into a Python bytearray object
//----------------------------------------------------------------------------
PyObject *JM_BArrayFromBuffer(fz_context *ctx, fz_buffer *buffer)
{
    if (!buffer) {
        return PyByteArray_FromStringAndSize("", 0);
    }
    unsigned char *c = NULL;
    size_t len = fz_buffer_storage(ctx, buffer, &c);
    return PyByteArray_FromStringAndSize((const char *) c, (Py_ssize_t) len);
}


//----------------------------------------------------------------------------
// compress char* into a new buffer
//----------------------------------------------------------------------------
fz_buffer *JM_compress_buffer(fz_context *ctx, fz_buffer *inbuffer)
{
    fz_buffer *buf = NULL;
    fz_try(ctx) {
        size_t compressed_length = 0;
        unsigned char *data = fz_new_deflated_data_from_buffer(ctx,
                              &compressed_length, inbuffer, FZ_DEFLATE_BEST);
        if (data == NULL || compressed_length == 0)
            return NULL;
        buf = fz_new_buffer_from_data(ctx, data, compressed_length);
        fz_resize_buffer(ctx, buf, compressed_length);
    }
    fz_catch(ctx) {
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

    if (compress == 1 && len > 30) {  // ignore small stuff
        nres = JM_compress_buffer(ctx, buffer);
        nlen = fz_buffer_storage(ctx, nres, NULL);
    }

    if (nlen < len && nres && compress==1) {  // was it worth the effort?
        pdf_dict_put(ctx, obj, PDF_NAME(Filter), PDF_NAME(FlateDecode));
        pdf_update_stream(ctx, doc, obj, nres, 1);
    } else {
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
    for (i = 0; i < n; i++) {
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
    char *c = NULL;
    PyObject *mybytes = NULL;
    size_t len = 0;
    fz_buffer *res = NULL;
    fz_var(res);
    fz_try(ctx) {
        if (PyBytes_Check(stream)) {
            c = PyBytes_AS_STRING(stream);
            len = (size_t) PyBytes_GET_SIZE(stream);
        } else if (PyByteArray_Check(stream)) {
            c = PyByteArray_AS_STRING(stream);
            len = (size_t) PyByteArray_GET_SIZE(stream);
        } else if (PyObject_HasAttrString(stream, "getvalue")) {
            // we assume here that this delivers what we expect
            mybytes = PyObject_CallMethod(stream, "getvalue", NULL);
            c = PyBytes_AS_STRING(mybytes);
            len = (size_t) PyBytes_GET_SIZE(mybytes);
        }
        // if none of the above, c is NULL and we return an empty buffer
        if (c) {
            res = fz_new_buffer_from_copied_data(ctx, (const unsigned char *) c, len);
        } else {
            res = fz_new_buffer(ctx, 1);
            fz_append_byte(ctx, res, 10);
        }
        fz_terminate_buffer(ctx, res);
    }
    fz_always(ctx) {
        Py_CLEAR(mybytes);
        PyErr_Clear();
    }
    fz_catch(ctx) {
        fz_drop_buffer(ctx, res);
        fz_rethrow(ctx);
    }
    return res;
}


//----------------------------------------------------------------------------
// Deep-copies a specified source page to the target location.
// Modified copy of function of pdfmerge.c: we also copy annotations, but
// we skip **link** annotations. In addition we rotate output.
//----------------------------------------------------------------------------
static void
page_merge(fz_context *ctx, pdf_document *doc_des, pdf_document *doc_src, int page_from, int page_to, int rotate, int links, int copy_annots, pdf_graft_map *graft_map)
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
    int i, n = (int) nelem(known_page_objs);  // number of list elements
    fz_var(ref);
    fz_var(page_dict);
    fz_try(ctx) {
        page_ref = pdf_lookup_page_obj(ctx, doc_src, page_from);
        pdf_flatten_inheritable_page_items(ctx, page_ref);

        // make new page dict in dest doc
        page_dict = pdf_new_dict(ctx, doc_des, 4);
        pdf_dict_put(ctx, page_dict, PDF_NAME(Type), PDF_NAME(Page));

        // copy objects of source page into it
        for (i = 0; i < n; i++) {
            obj = pdf_dict_get(ctx, page_ref, known_page_objs[i]);
            if (obj != NULL) {
                pdf_dict_put_drop(ctx, page_dict, known_page_objs[i], pdf_graft_mapped_object(ctx, graft_map, obj));
            }
        }

        // Copy the annotations, but skip types Link, Popup, IRT.
        // Remove dict keys P (parent) and Popup from copied annot.
        if (copy_annots) {
            pdf_obj *old_annots = pdf_dict_get(ctx, page_ref, PDF_NAME(Annots));
            if (old_annots) {
                n = pdf_array_len(ctx, old_annots);
                pdf_obj *new_annots = pdf_dict_put_array(ctx, page_dict, PDF_NAME(Annots), n);
                for (i = 0; i < n; i++) {
                    pdf_obj *o = pdf_array_get(ctx, old_annots, i);
                    if (pdf_dict_gets(ctx, o, "IRT")) continue;
                    pdf_obj *subtype = pdf_dict_get(ctx, o, PDF_NAME(Subtype));
                    if (pdf_name_eq(ctx, subtype, PDF_NAME(Link))) continue;
                    if (pdf_name_eq(ctx, subtype, PDF_NAME(Popup))) continue;
                    pdf_dict_del(ctx, o, PDF_NAME(Popup));
                    pdf_dict_del(ctx, o, PDF_NAME(P));
                    pdf_obj *copy_o = pdf_graft_mapped_object(ctx, graft_map, o);
                    pdf_obj *annot = pdf_new_indirect(ctx, doc_des,
                                     pdf_to_num(ctx, copy_o), 0);
                    pdf_array_push_drop(ctx, new_annots, annot);
                    pdf_drop_obj(ctx, copy_o);
                }
            }
        }
        // rotate the page
        if (rotate != -1) {
            pdf_dict_put_int(ctx, page_dict, PDF_NAME(Rotate), (int64_t) rotate);
        }
        // Now add the page dictionary to dest PDF
        ref = pdf_add_object(ctx, doc_des, page_dict);

        // Insert new page at specified location
        pdf_insert_page(ctx, doc_des, page_to, ref);

    }
    fz_always(ctx) {
        pdf_drop_obj(ctx, ref);
        pdf_drop_obj(ctx, page_dict);
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
}

//-----------------------------------------------------------------------------
// Copy a range of pages (spage, epage) from a source PDF to a specified
// location (apage) of the target PDF.
// If spage > epage, the sequence of source pages is reversed.
//-----------------------------------------------------------------------------
void JM_merge_range(fz_context *ctx, pdf_document *doc_des, pdf_document *doc_src, int spage, int epage, int apage, int rotate, int links, int annots, int show_progress, pdf_graft_map *graft_map)
{
    int page, afterpage;
    afterpage = apage;
    int counter = 0;  // copied pages counter
    int total = fz_absi(epage - spage) + 1;  // total pages to copy

    fz_try(ctx) {
        if (spage < epage) {
            for (page = spage; page <= epage; page++, afterpage++) {
                page_merge(ctx, doc_des, doc_src, page, afterpage, rotate, links, annots, graft_map);
                counter++;
                if (show_progress > 0 && counter % show_progress == 0) {
                    PySys_WriteStdout("Inserted %i of %i pages.\n", counter, total);
                }
            }
        } else {
            for (page = spage; page >= epage; page--, afterpage++) {
                page_merge(ctx, doc_des, doc_src, page, afterpage, rotate, links, annots, graft_map);
                counter++;
                if (show_progress > 0 && counter % show_progress == 0) {
                    PySys_WriteStdout("Inserted %i of %i pages.\n", counter, total);
                }
            }
        }
    }

    fz_catch(ctx) {
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
    while (thisobj) {
        LIST_APPEND_DROP(xrefs, Py_BuildValue("i", pdf_to_num(ctx, thisobj)));
        first = pdf_dict_get(ctx, thisobj, PDF_NAME(First));  // try go down
        if (first) xrefs = JM_outline_xrefs(ctx, first, xrefs);
        thisobj = pdf_dict_get(ctx, thisobj, PDF_NAME(Next));  // try go next
        parent = pdf_dict_get(ctx, thisobj, PDF_NAME(Parent));  // get parent
        if (!thisobj) thisobj = parent;  // goto parent if no next
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
    o = pdf_load_object(ctx, doc, xref);
    desft = pdf_dict_get(ctx, o, PDF_NAME(DescendantFonts));
    char *ext = NULL;
    if (desft) {
        obj = pdf_resolve_indirect(ctx, pdf_array_get(ctx, desft, 0));
        obj = pdf_dict_get(ctx, obj, PDF_NAME(FontDescriptor));
    } else {
        obj = pdf_dict_get(ctx, o, PDF_NAME(FontDescriptor));
    }

    if (!obj) {
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
    if (obj) {
        stream = obj;

        obj = pdf_dict_get(ctx, obj, PDF_NAME(Subtype));
        if (obj && !pdf_is_name(ctx, obj)) {
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

    if (!stream) {
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
    if (desft) {
        obj = pdf_resolve_indirect(ctx, pdf_array_get(ctx, desft, 0));
        obj = pdf_dict_get(ctx, obj, PDF_NAME(FontDescriptor));
    } else {
        obj = pdf_dict_get(ctx, o, PDF_NAME(FontDescriptor));
    }

    pdf_drop_obj(ctx, o);
    if (!obj) return "n/a";           // this is a base-14 font

    o = obj;                           // we have the FontDescriptor

    obj = pdf_dict_get(ctx, o, PDF_NAME(FontFile));
    if (obj) return "pfa";

    obj = pdf_dict_get(ctx, o, PDF_NAME(FontFile2));
    if (obj) return "ttf";

    obj = pdf_dict_get(ctx, o, PDF_NAME(FontFile3));
    if (obj) {
        obj = pdf_dict_get(ctx, obj, PDF_NAME(Subtype));
        if (obj && !pdf_is_name(ctx, obj)) {
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

    fz_try(ctx) {
        result = pdf_parse_stm_obj(ctx, doc, stream, &lexbuf);
    }

    fz_always(ctx) {
        pdf_lexbuf_fin(ctx, &lexbuf);
        fz_drop_stream(ctx, stream);
    }

    fz_catch(ctx) {
        fz_rethrow(ctx);
    }

    return result;

}

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
fz_rect JM_mediabox(fz_context *ctx, pdf_obj *page_obj)
{
    fz_rect mediabox, page_mediabox;

    mediabox = pdf_to_rect(ctx, pdf_dict_get_inheritable(ctx, page_obj,
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
fz_rect JM_cropbox(fz_context *ctx, pdf_obj *page_obj)
{
    fz_rect mediabox = JM_mediabox(ctx, page_obj);
    fz_rect cropbox = pdf_to_rect(ctx,
                pdf_dict_get_inheritable(ctx, page_obj, PDF_NAME(CropBox)));
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
fz_point JM_cropbox_size(fz_context *ctx, pdf_obj *page_obj)
{
    fz_point size;
    fz_try(ctx)
    {
        fz_rect rect = JM_cropbox(ctx, page_obj);
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
    fz_point cb_size = JM_cropbox_size(ctx, page->obj);
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


//-----------------------------------------------------------------------------
// Insert a font in a PDF
//-----------------------------------------------------------------------------
PyObject *
JM_insert_font(fz_context *ctx, pdf_document *pdf, char *bfname, char *fontfile,
    PyObject *fontbuffer, int set_simple, int idx, int wmode, int serif,
    int encoding, int ordering)
{
    pdf_obj *font_obj;
    fz_font *font = NULL;
    fz_buffer *res = NULL;
    const unsigned char *data = NULL;
    int size, ixref = 0, index = 0, simple = 0;
    PyObject *value, *name, *subt, *exto = NULL;

    fz_try(ctx) {
        //-------------------------------------------------------------
        // check for CJK font
        //-------------------------------------------------------------
        if (ordering > -1) {
            data = fz_lookup_cjk_font(ctx, ordering, &size, &index);
        }
        if (data) {
            font = fz_new_font_from_memory(ctx, NULL, data, size, index, 0);
            font_obj = pdf_add_cjk_font(ctx, pdf, font, ordering, wmode, serif);
            exto = JM_UnicodeFromStr("n/a");
            simple = 0;
            goto weiter;
        }

        //-------------------------------------------------------------
        // check for PDF Base-14 font
        //-------------------------------------------------------------
        if (bfname) {
            data = fz_lookup_base14_font(ctx, bfname, &size);
        }
        if (data) {
            font = fz_new_font_from_memory(ctx, bfname, data, size, 0, 0);
            font_obj = pdf_add_simple_font(ctx, pdf, font, encoding);
            exto = JM_UnicodeFromStr("n/a");
            simple = 1;
            goto weiter;
        }

        if (fontfile) {
            font = fz_new_font_from_file(ctx, NULL, fontfile, idx, 0);
        } else {
            res = JM_BufferFromBytes(ctx, fontbuffer);
            if (!res) {
                THROWMSG(ctx, "need one of fontfile, fontbuffer");
            }
            font = fz_new_font_from_buffer(ctx, NULL, res, idx, 0);
        }

        if (!set_simple) {
            font_obj = pdf_add_cid_font(ctx, pdf, font);
            simple = 0;
        } else {
            font_obj = pdf_add_simple_font(ctx, pdf, font, encoding);
            simple = 2;
        }

        weiter: ;
        font_obj = pdf_keep_obj(ctx, font_obj);
        ixref = pdf_to_num(ctx, font_obj);
        if (fz_font_is_monospaced(ctx, font)) {
            float adv = fz_advance_glyph(ctx, font,
                            fz_encode_character(ctx, font, 32), 0);
            int width = (int) floor(adv * 1000.0f + 0.5f);
            pdf_obj *dfonts = pdf_dict_get(ctx, font_obj, PDF_NAME(DescendantFonts));
            if (pdf_is_array(ctx, dfonts)) {
                int i, n = pdf_array_len(ctx, dfonts);
                for (i = 0; i < n; i++) {
                    pdf_obj *dfont = pdf_array_get(ctx, dfonts, i);
                    pdf_obj *warray = pdf_new_array(ctx, pdf, 3);
                    pdf_array_push(ctx, warray, pdf_new_int(ctx, 0));
                    pdf_array_push(ctx, warray, pdf_new_int(ctx, 65535));
                    pdf_array_push(ctx, warray, pdf_new_int(ctx, (int64_t) width));
                    pdf_dict_put_drop(ctx, dfont, PDF_NAME(W), warray);
                }
            }
        }
        name = JM_EscapeStrFromStr(pdf_to_name(ctx,
                    pdf_dict_get(ctx, font_obj, PDF_NAME(BaseFont))));

        subt = JM_UnicodeFromStr(pdf_to_name(ctx,
                    pdf_dict_get(ctx, font_obj, PDF_NAME(Subtype))));

        if (!exto)
            exto = JM_UnicodeFromStr(JM_get_fontextension(ctx, pdf, ixref));

        float asc = fz_font_ascender(ctx, font);
        float dsc = fz_font_descender(ctx, font);
        value = Py_BuildValue("[i,{s:O,s:O,s:O,s:O,s:i,s:f,s:f}]",
                                ixref,
                                "name", name,        // base font name
                                "type", subt,        // subtype
                                "ext", exto,         // file extension
                                "simple", JM_BOOL(simple), // simple font?
                                "ordering", ordering, // CJK font?
                                "ascender", asc,
                                "descender", dsc
                                );
    }
    fz_always(ctx) {
        Py_CLEAR(exto);
        Py_CLEAR(name);
        Py_CLEAR(subt);
        fz_drop_buffer(ctx, res);
        fz_drop_font(ctx, font);
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return value;
}

//-----------------------------------------------------------------------------
// dummy structure for various tools and utilities
//-----------------------------------------------------------------------------
struct Tools {int index;};

typedef struct fz_item fz_item;

struct fz_item
{
	void *key;
	fz_storable *val;
	size_t size;
	fz_item *next;
	fz_item *prev;
	fz_store *store;
	const fz_store_type *type;
};

struct fz_store
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
