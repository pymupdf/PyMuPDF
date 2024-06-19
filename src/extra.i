%module fitz_extra

%pythoncode %{
# pylint: disable=all
%}

%begin
%{
#define SWIG_PYTHON_INTERPRETER_NO_DEBUG
%}

%init
%{
    /* Initialise some globals that require Python functions.
    
    [Prior to 2023-08-18 we initialised these global variables inline,
    but this causes a SEGV on Windows with Python-3.10 for `dictkey_c`
    (actually any string of length 1 failed).] */
    
    dictkey_align = PyUnicode_InternFromString("align");
    dictkey_ascender = PyUnicode_InternFromString("ascender");
    dictkey_bbox = PyUnicode_InternFromString("bbox");
    dictkey_blocks = PyUnicode_InternFromString("blocks");
    dictkey_bpc = PyUnicode_InternFromString("bpc");
    dictkey_c = PyUnicode_InternFromString("c");
    dictkey_chars = PyUnicode_InternFromString("chars");
    dictkey_color = PyUnicode_InternFromString("color");
    dictkey_colorspace = PyUnicode_InternFromString("colorspace");
    dictkey_content = PyUnicode_InternFromString("content");
    dictkey_creationDate = PyUnicode_InternFromString("creationDate");
    dictkey_cs_name = PyUnicode_InternFromString("cs-name");
    dictkey_da = PyUnicode_InternFromString("da");
    dictkey_dashes = PyUnicode_InternFromString("dashes");
    dictkey_desc = PyUnicode_InternFromString("descender");
    dictkey_descender = PyUnicode_InternFromString("descender");
    dictkey_dir = PyUnicode_InternFromString("dir");
    dictkey_effect = PyUnicode_InternFromString("effect");
    dictkey_ext = PyUnicode_InternFromString("ext");
    dictkey_filename = PyUnicode_InternFromString("filename");
    dictkey_fill = PyUnicode_InternFromString("fill");
    dictkey_flags = PyUnicode_InternFromString("flags");
    dictkey_font = PyUnicode_InternFromString("font");
    dictkey_glyph = PyUnicode_InternFromString("glyph");
    dictkey_height = PyUnicode_InternFromString("height");
    dictkey_id = PyUnicode_InternFromString("id");
    dictkey_image = PyUnicode_InternFromString("image");
    dictkey_items = PyUnicode_InternFromString("items");
    dictkey_length = PyUnicode_InternFromString("length");
    dictkey_lines = PyUnicode_InternFromString("lines");
    dictkey_matrix = PyUnicode_InternFromString("transform");
    dictkey_modDate = PyUnicode_InternFromString("modDate");
    dictkey_name = PyUnicode_InternFromString("name");
    dictkey_number = PyUnicode_InternFromString("number");
    dictkey_origin = PyUnicode_InternFromString("origin");
    dictkey_rect = PyUnicode_InternFromString("rect");
    dictkey_size = PyUnicode_InternFromString("size");
    dictkey_smask = PyUnicode_InternFromString("smask");
    dictkey_spans = PyUnicode_InternFromString("spans");
    dictkey_stroke = PyUnicode_InternFromString("stroke");
    dictkey_style = PyUnicode_InternFromString("style");
    dictkey_subject = PyUnicode_InternFromString("subject");
    dictkey_text = PyUnicode_InternFromString("text");
    dictkey_title = PyUnicode_InternFromString("title");
    dictkey_type = PyUnicode_InternFromString("type");
    dictkey_ufilename = PyUnicode_InternFromString("ufilename");
    dictkey_width = PyUnicode_InternFromString("width");
    dictkey_wmode = PyUnicode_InternFromString("wmode");
    dictkey_xref = PyUnicode_InternFromString("xref");
    dictkey_xres = PyUnicode_InternFromString("xres");
    dictkey_yres = PyUnicode_InternFromString("yres");
%}

%include std_string.i

%include exception.i
%exception {
    try {
        $action
    }

/* this might not be ok on windows.
catch (Swig::DirectorException &e) {
    SWIG_fail;
}*/
catch(std::exception& e) {
    SWIG_exception(SWIG_RuntimeError, e.what());
}
catch(...) {
        SWIG_exception(SWIG_RuntimeError, "Unknown exception");
    }
}

%{
#include "mupdf/classes2.h"
#include "mupdf/exceptions.h"
#include "mupdf/internal.h"

#include <algorithm>
#include <float.h>


/* Returns equivalent of `repr(x)`. */
static std::string repr(PyObject* x)
{
    PyObject* repr = PyObject_Repr(x);
    PyObject* repr_str = PyUnicode_AsEncodedString(repr, "utf-8", "~E~");
    const char* repr_str_s = PyBytes_AS_STRING(repr_str);
    std::string ret = repr_str_s;
    Py_DECREF(repr_str);
    Py_DECREF(repr);
    return ret;
}

/* These are also in pymupdf/__init__.py. */
const char MSG_BAD_ANNOT_TYPE[] = "bad annot type";
const char MSG_BAD_APN[] = "bad or missing annot AP/N";
const char MSG_BAD_ARG_INK_ANNOT[] = "arg must be seq of seq of float pairs";
const char MSG_BAD_ARG_POINTS[] = "bad seq of points";
const char MSG_BAD_BUFFER[] = "bad type: 'buffer'";
const char MSG_BAD_COLOR_SEQ[] = "bad color sequence";
const char MSG_BAD_DOCUMENT[] = "cannot open broken document";
const char MSG_BAD_FILETYPE[] = "bad filetype";
const char MSG_BAD_LOCATION[] = "bad location";
const char MSG_BAD_OC_CONFIG[] = "bad config number";
const char MSG_BAD_OC_LAYER[] = "bad layer number";
const char MSG_BAD_OC_REF[] = "bad 'oc' reference";
const char MSG_BAD_PAGEID[] = "bad page id";
const char MSG_BAD_PAGENO[] = "bad page number(s)";
const char MSG_BAD_PDFROOT[] = "PDF has no root";
const char MSG_BAD_RECT[] = "rect is infinite or empty";
const char MSG_BAD_TEXT[] = "bad type: 'text'";
const char MSG_BAD_XREF[] = "bad xref";
const char MSG_COLOR_COUNT_FAILED[] = "color count failed";
const char MSG_FILE_OR_BUFFER[] = "need font file or buffer";
const char MSG_FONT_FAILED[] = "cannot create font";
const char MSG_IS_NO_ANNOT[] = "is no annotation";
const char MSG_IS_NO_IMAGE[] = "is no image";
const char MSG_IS_NO_PDF[] = "is no PDF";
const char MSG_IS_NO_DICT[] = "object is no PDF dict";
const char MSG_PIX_NOALPHA[] = "source pixmap has no alpha";
const char MSG_PIXEL_OUTSIDE[] = "pixel(s) outside image";

#define JM_BOOL(x) PyBool_FromLong((long) (x))

static PyObject *JM_UnicodeFromStr(const char *c);


#ifdef _WIN32

/* These functions are not provided on Windows. */

int vasprintf(char** str, const char* fmt, va_list ap)
{
    va_list ap2;

    va_copy(ap2, ap);
    int len = vsnprintf(nullptr, 0, fmt, ap2);
    va_end(ap2);
    
    char* buffer = (char*) malloc(len + 1);
    if (!buffer)
    {
        *str = nullptr;
        return -1;
    }
    va_copy(ap2, ap);
    int len2 = vsnprintf(buffer, len + 1, fmt, ap2);
    va_end(ap2);
    assert(len2 == len);
    *str = buffer;
    return len;
}

int asprintf(char** str, const char* fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    int ret = vasprintf(str, fmt, ap);
    va_end(ap);

    return ret;
}
#endif


static void messagev(const char* format, va_list va)
{
    static PyObject* pymupdf_module = PyImport_ImportModule("pymupdf");
    static PyObject* message_fn = PyObject_GetAttrString(pymupdf_module, "message");
    char* text;
    vasprintf(&text, format, va);
    PyObject* text_py = PyString_FromString(text);
    PyObject* args = PyTuple_Pack(1, text_py);
    PyObject* ret = PyObject_CallObject(message_fn, args);
    Py_XDECREF(ret);
    Py_XDECREF(args);
    Py_XDECREF(text_py);
    free(text);
}

static void messagef(const char* format, ...)
{
    va_list args;
    va_start(args, format);
    messagev(format, args);
    va_end(args);
}

PyObject* JM_EscapeStrFromStr(const char* c)
{
    if (!c) return PyUnicode_FromString("");
    PyObject* val = PyUnicode_DecodeRawUnicodeEscape(c, (Py_ssize_t) strlen(c), "replace");
    if (!val)
    {
        val = PyUnicode_FromString("");
        PyErr_Clear();
    }
    return val;
}

PyObject* JM_EscapeStrFromBuffer(fz_buffer* buff)
{
    if (!buff) return PyUnicode_FromString("");
    unsigned char* s = nullptr;
    size_t len = mupdf::ll_fz_buffer_storage(buff, &s);
    PyObject* val = PyUnicode_DecodeRawUnicodeEscape((const char*) s, (Py_ssize_t) len, "replace");
    if (!val)
    {
        val = PyUnicode_FromString("");
        PyErr_Clear();
    }
    return val;
}

// Only used for mupdf < 1.24. mupdf >= 1.24 has pdf_rearrange_pages2().
void rearrange_pages2(
        mupdf::PdfDocument& doc,
        PyObject *new_pages
    )
{
    int len = (int) PyTuple_Size(new_pages);
    int *pages = (int *) malloc((int) len * sizeof(int));
    int i;
    for (i = 0; i < len; i++) {
        pages[i] = (int) PyLong_AsLong(PyTuple_GET_ITEM(new_pages, (Py_ssize_t) i));
    }
    mupdf::pdf_rearrange_pages(doc, len, pages);
    free(pages);
}


//----------------------------------------------------------------------------
// Deep-copies a source page to the target.
// Modified version of function of pdfmerge.c: we also copy annotations, but
// we skip some subtypes. In addition we rotate output.
//----------------------------------------------------------------------------
static void page_merge(
        mupdf::PdfDocument& doc_des,
        mupdf::PdfDocument& doc_src,
        int page_from,
        int page_to,
        int rotate,
        int links,
        int copy_annots,
        mupdf::PdfGraftMap& graft_map
        )
{
    // list of object types (per page) we want to copy

    /* Fixme: on linux these get destructed /after/
    mupdf/platform/c++/implementation/internal.cpp:s_thread_state, which causes
    problems - s_thread_state::m_ctx will have been freed. We have a hack
    that sets s_thread_state::m_ctx when destructed, so it mostly works when
    s_thread_state.get_context() is called after destruction, but this causes
    memento leaks and is clearly incorrect.
    
    Perhaps we could use pdf_obj* known_page_objs[] = {...} and create PdfObj
    wrappers as used - this would avoid any cleanup at exit. And it's a general
    solution to problem of ordering of cleanup of globals.
    */
    static pdf_obj* known_page_objs[] = {
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
    int known_page_objs_num = sizeof(known_page_objs) / sizeof(known_page_objs[0]);
    mupdf::PdfObj   page_ref = mupdf::pdf_lookup_page_obj(doc_src, page_from);

    // make new page dict in dest doc
    mupdf::PdfObj   page_dict = mupdf::pdf_new_dict(doc_des, 4);
    mupdf::pdf_dict_put(page_dict, PDF_NAME(Type), PDF_NAME(Page));

    for (int i = 0; i < known_page_objs_num; ++i)
    {
        mupdf::PdfObj   known_page_obj(known_page_objs[i]);
        mupdf::PdfObj   obj = mupdf::pdf_dict_get_inheritable(page_ref, known_page_obj);
        if (obj.m_internal)
        {
            mupdf::pdf_dict_put(
                    page_dict,
                    known_page_obj,
                    mupdf::pdf_graft_mapped_object(graft_map, obj)
                    );
        }
    }

    // Copy annotations, but skip Link, Popup, IRT, Widget types
    // If selected, remove dict keys P (parent) and Popup
    if (copy_annots)
    {
        mupdf::PdfObj old_annots = mupdf::pdf_dict_get(page_ref, PDF_NAME(Annots));
        int n = mupdf::pdf_array_len(old_annots);
        if (n > 0)
        {
            mupdf::PdfObj new_annots = mupdf::pdf_dict_put_array(page_dict, PDF_NAME(Annots), n);
            for (int i = 0; i < n; i++)
            {
                mupdf::PdfObj o = mupdf::pdf_array_get(old_annots, i);
                if (!o.m_internal || !mupdf::pdf_is_dict(o)) // skip non-dict items
                {
                    continue;   // skip invalid/null/non-dict items
                }
                if (mupdf::pdf_dict_get(o, PDF_NAME(IRT)).m_internal) continue;
                mupdf::PdfObj subtype = mupdf::pdf_dict_get(o, PDF_NAME(Subtype));
                if (mupdf::pdf_name_eq(subtype, PDF_NAME(Link))) continue;
                if (mupdf::pdf_name_eq(subtype, PDF_NAME(Popup))) continue;
                if (mupdf::pdf_name_eq(subtype, PDF_NAME(Widget)))
                {
                    mupdf::fz_warn("skipping widget annotation");
                    continue;
                }
                if (mupdf::pdf_name_eq(subtype, PDF_NAME(Widget))) continue;
                mupdf::pdf_dict_del(o, PDF_NAME(Popup));
                mupdf::pdf_dict_del(o, PDF_NAME(P));
                mupdf::PdfObj copy_o = mupdf::pdf_graft_mapped_object(graft_map, o);
                mupdf::PdfObj annot = mupdf::pdf_new_indirect(
                        doc_des,
                        mupdf::pdf_to_num(copy_o),
                        0
                        );
                mupdf::pdf_array_push(new_annots, annot);
            }
        }
    }
    // rotate the page
    if (rotate != -1)
    {
        mupdf::pdf_dict_put_int(page_dict, PDF_NAME(Rotate), rotate);
    }
    // Now add the page dictionary to dest PDF
    mupdf::PdfObj ref = mupdf::pdf_add_object(doc_des, page_dict);

    // Insert new page at specified location
    mupdf::pdf_insert_page(doc_des, page_to, ref);
}

//-----------------------------------------------------------------------------
// Copy a range of pages (spage, epage) from a source PDF to a specified
// location (apage) of the target PDF.
// If spage > epage, the sequence of source pages is reversed.
//-----------------------------------------------------------------------------
static void JM_merge_range(
        mupdf::PdfDocument& doc_des,
        mupdf::PdfDocument& doc_src,
        int spage,
        int epage,
        int apage,
        int rotate,
        int links,
        int annots,
        int show_progress,
        mupdf::PdfGraftMap& graft_map
        )
{
    int afterpage = apage;
    int counter = 0;  // copied pages counter
    int total = mupdf::ll_fz_absi(epage - spage) + 1;  // total pages to copy

    if (spage < epage)
    {
        for (int page = spage; page <= epage; page++, afterpage++)
        {
            page_merge(doc_des, doc_src, page, afterpage, rotate, links, annots, graft_map);
            counter++;
            if (show_progress > 0 && counter % show_progress == 0)
            {
                messagef("Inserted %i of %i pages.", counter, total);
            }
        }
    }
    else
    {
        for (int page = spage; page >= epage; page--, afterpage++)
        {
            page_merge(doc_des, doc_src, page, afterpage, rotate, links, annots, graft_map);
            counter++;
            if (show_progress > 0 && counter % show_progress == 0)
            {
                messagef("Inserted %i of %i pages.", counter, total);
            }
        }
    }
}

static bool JM_have_operation(mupdf::PdfDocument& pdf)
{
    // Ensure valid journalling state
    if (pdf.m_internal->journal and !mupdf::pdf_undoredo_step(pdf, 0))
    {
        return 0;
    }
    return 1;
}

static void JM_ensure_operation(mupdf::PdfDocument& pdf)
{
    if (!JM_have_operation(pdf))
    {
        throw std::runtime_error("No journalling operation started");
    }
}


static void FzDocument_insert_pdf(
        mupdf::FzDocument& doc,
        mupdf::FzDocument& src,
        int from_page,
        int to_page,
        int start_at,
        int rotate,
        int links,
        int annots,
        int show_progress,
        int final,
        mupdf::PdfGraftMap& graft_map
        )
{
    //std::cerr << __FILE__ << ":" << __LINE__ << ":" << __FUNCTION__ << "\n";
    mupdf::PdfDocument pdfout = mupdf::pdf_specifics(doc);
    mupdf::PdfDocument pdfsrc = mupdf::pdf_specifics(src);
    int outCount = mupdf::fz_count_pages(doc);
    int srcCount = mupdf::fz_count_pages(src);

    // local copies of page numbers
    int fp = from_page;
    int tp = to_page;
    int sa = start_at;

    // normalize page numbers
    fp = std::max(fp, 0);               // -1 = first page
    fp = std::min(fp, srcCount - 1);    // but do not exceed last page

    if (tp < 0) tp = srcCount - 1;      // -1 = last page
    tp = std::min(tp, srcCount - 1);    // but do not exceed last page

    if (sa < 0) sa = outCount;          // -1 = behind last page
    sa = std::min(sa, outCount);        // but that is also the limit

    if (!pdfout.m_internal || !pdfsrc.m_internal)
    {
        throw std::runtime_error("source or target not a PDF");
    }
    JM_ensure_operation(pdfout);
    JM_merge_range(pdfout, pdfsrc, fp, tp, sa, rotate, links, annots, show_progress, graft_map);
}

static int page_xref(mupdf::FzDocument& this_doc, int pno)
{
    int page_count = mupdf::fz_count_pages(this_doc);
    int n = pno;
    while (n < 0)
    {
        n += page_count;
    }
    mupdf::PdfDocument pdf = mupdf::pdf_specifics(this_doc);
    assert(pdf.m_internal);
    int xref = 0;
    if (n >= page_count)
    {
        throw std::runtime_error(MSG_BAD_PAGENO);//, PyExc_ValueError);
    }
    xref = mupdf::pdf_to_num(mupdf::pdf_lookup_page_obj(pdf, n));
    return xref;
}

static void _newPage(mupdf::PdfDocument& pdf, int pno=-1, float width=595, float height=842)
{
    if (!pdf.m_internal)
    {
        throw std::runtime_error("is no PDF");
    }
    mupdf::FzRect mediabox(0, 0, width, height);
    if (pno < -1)
    {
        throw std::runtime_error("bad page number(s)");  // Should somehow be Python ValueError
    }
    JM_ensure_operation(pdf);
    // create /Resources and /Contents objects
    mupdf::PdfObj resources = mupdf::pdf_add_new_dict(pdf, 1);
    mupdf::FzBuffer contents;
    mupdf::PdfObj page_obj = mupdf::pdf_add_page(pdf, mediabox, 0, resources, contents);
    mupdf::pdf_insert_page(pdf, pno, page_obj);
}

static void _newPage(mupdf::FzDocument& self, int pno=-1, float width=595, float height=842)
{
    mupdf::PdfDocument pdf = mupdf::pdf_specifics(self);
    _newPage(pdf, pno, width, height);
}


//------------------------------------------------------------------------
// return the annotation names (list of /NM entries)
//------------------------------------------------------------------------
static std::vector< std::string> JM_get_annot_id_list(mupdf::PdfPage& page)
{
    std::vector< std::string> names;
    mupdf::PdfObj annots = mupdf::pdf_dict_get(page.obj(), PDF_NAME(Annots));
    if (!annots.m_internal) return names;
    int n = mupdf::pdf_array_len(annots);
    for (int i = 0; i < n; i++)
    {
        mupdf::PdfObj annot_obj = mupdf::pdf_array_get(annots, i);
        mupdf::PdfObj name = mupdf::pdf_dict_gets(annot_obj, "NM");
        if (name.m_internal)
        {
            names.push_back(mupdf::pdf_to_text_string(name));
        }
    }
    return names;
}

//------------------------------------------------------------------------
// Add a unique /NM key to an annotation or widget.
// Append a number to 'stem' such that the result is a unique name.
//------------------------------------------------------------------------
static void JM_add_annot_id(mupdf::PdfAnnot& annot, const char* stem)
{
    mupdf::PdfPage page = mupdf::pdf_annot_page(annot);
    mupdf::PdfObj annot_obj = mupdf::pdf_annot_obj(annot);
    std::vector< std::string> names = JM_get_annot_id_list(page);
    char* stem_id = nullptr;
    for (int i=0; ; ++i)
    {
        free(stem_id);
        asprintf(&stem_id,  "fitz-%s%d", stem, i);
        if (std::find(names.begin(), names.end(), stem_id) == names.end())
        {
            break;
        }
    }
    mupdf::PdfObj name = mupdf::pdf_new_string(stem_id, strlen(stem_id));
    free(stem_id);
    mupdf::pdf_dict_puts(annot_obj, "NM", name);
    page.m_internal->doc->resynth_required = 0;
}

//----------------------------------------------------------------
// page add_caret_annot
//----------------------------------------------------------------
static mupdf::PdfAnnot _add_caret_annot(mupdf::PdfPage& page, mupdf::FzPoint& point)
{
    mupdf::PdfAnnot annot = mupdf::pdf_create_annot(page, ::PDF_ANNOT_CARET);
    mupdf::FzPoint  p = point;
    mupdf::FzRect   r = mupdf::pdf_annot_rect(annot);
    r = mupdf::fz_make_rect(p.x, p.y, p.x + r.x1 - r.x0, p.y + r.y1 - r.y0);
    mupdf::pdf_set_annot_rect(annot, r);
    mupdf::pdf_update_annot(annot);
    JM_add_annot_id(annot, "A");
    return annot;
}

static mupdf::PdfAnnot _add_caret_annot(mupdf::FzPage& page, mupdf::FzPoint& point)
{
    mupdf::PdfPage  pdf_page = mupdf::pdf_page_from_fz_page(page);
    return _add_caret_annot(pdf_page, point);
}

static const char* Tools_parse_da(mupdf::PdfAnnot& this_annot)
{
    const char* da_str = nullptr;
    mupdf::PdfObj this_annot_obj = mupdf::pdf_annot_obj(this_annot);
    mupdf::PdfDocument pdf = mupdf::pdf_get_bound_document(this_annot_obj);
    try
    {
        mupdf::PdfObj da = mupdf::pdf_dict_get_inheritable(this_annot_obj, PDF_NAME(DA));
        if (!da.m_internal)
        {
            mupdf::PdfObj trailer = mupdf::pdf_trailer(pdf);
            da = mupdf::pdf_dict_getl(
                    &trailer,
                    PDF_NAME(Root),
                    PDF_NAME(AcroForm),
                    PDF_NAME(DA),
                    nullptr
                    );
        }
        da_str = mupdf::pdf_to_text_string(da);
    }
    catch (std::exception&)
    {
        return nullptr;
    }
    return da_str;
}

//----------------------------------------------------------------------------
// Turn fz_buffer into a Python bytes object
//----------------------------------------------------------------------------
static PyObject* JM_BinFromBuffer(fz_buffer* buffer)
{
    if (!buffer)
    {
        return PyBytes_FromStringAndSize("", 0);
    }
    unsigned char* c = nullptr;
    size_t len = mupdf::ll_fz_buffer_storage(buffer, &c);
    return PyBytes_FromStringAndSize((const char*) c, len);
}
static PyObject* JM_BinFromBuffer(mupdf::FzBuffer& buffer)
{
    return JM_BinFromBuffer( buffer.m_internal);
}

static PyObject* Annot_getAP(mupdf::PdfAnnot& annot)
{
    mupdf::PdfObj annot_obj = mupdf::pdf_annot_obj(annot);
    mupdf::PdfObj ap = mupdf::pdf_dict_getl(
            &annot_obj,
            PDF_NAME(AP),
            PDF_NAME(N),
            nullptr
            );
    if (mupdf::pdf_is_stream(ap))
    {
        mupdf::FzBuffer res = mupdf::pdf_load_stream(ap);
        return JM_BinFromBuffer(res);
    }
    return PyBytes_FromStringAndSize("", 0);
}

void Tools_update_da(mupdf::PdfAnnot& this_annot, const char* da_str)
{
    mupdf::PdfObj this_annot_obj = mupdf::pdf_annot_obj(this_annot);
    mupdf::pdf_dict_put_text_string(this_annot_obj, PDF_NAME(DA), da_str);
    mupdf::pdf_dict_del(this_annot_obj, PDF_NAME(DS)); /* not supported */
    mupdf::pdf_dict_del(this_annot_obj, PDF_NAME(RC)); /* not supported */
}

static int
jm_float_item(PyObject* obj, Py_ssize_t idx, double* result)
{
    PyObject* temp = PySequence_ITEM(obj, idx);
    if (!temp) return 1;
    *result = PyFloat_AsDouble(temp);
    Py_DECREF(temp);
    if (PyErr_Occurred())
    {
        PyErr_Clear();
        return 1;
    }
    return 0;
}


static mupdf::FzPoint JM_point_from_py(PyObject* p)
{
    fz_point p0 = fz_make_point(FZ_MIN_INF_RECT, FZ_MIN_INF_RECT);
    if (!p || !PySequence_Check(p) || PySequence_Size(p) != 2)
    {
        return p0;
    }
    double x;
    double y;
    if (jm_float_item(p, 0, &x) == 1) return p0;
    if (jm_float_item(p, 1, &y) == 1) return p0;
    if (x < FZ_MIN_INF_RECT) x = FZ_MIN_INF_RECT;
    if (y < FZ_MIN_INF_RECT) y = FZ_MIN_INF_RECT;
    if (x > FZ_MAX_INF_RECT) x = FZ_MAX_INF_RECT;
    if (y > FZ_MAX_INF_RECT) y = FZ_MAX_INF_RECT;

    return fz_make_point(x, y);
}

static int s_list_append_drop(PyObject* list, PyObject* item)
{
    if (!list || !PyList_Check(list) || !item)
    {
        return -2;
    }
    int rc = PyList_Append(list, item);
    Py_DECREF(item);
    return rc;
}

static int LIST_APPEND_DROP(PyObject *list, PyObject *item)
{
    if (!list || !PyList_Check(list) || !item) return -2;
    int rc = PyList_Append(list, item);
    Py_DECREF(item);
    return rc;
}

static int LIST_APPEND(PyObject *list, PyObject *item)
{
    if (!list || !PyList_Check(list) || !item) return -2;
    int rc = PyList_Append(list, item);
    return rc;
}

static int DICT_SETITEM_DROP(PyObject *dict, PyObject *key, PyObject *value)
{
    if (!dict || !PyDict_Check(dict) || !key || !value) return -2;
    int rc = PyDict_SetItem(dict, key, value);
    Py_DECREF(value);
    return rc;
}

static int DICT_SETITEMSTR_DROP(PyObject *dict, const char *key, PyObject *value)
{
    if (!dict || !PyDict_Check(dict) || !key || !value) return -2;
    int rc = PyDict_SetItemString(dict, key, value);
    Py_DECREF(value);
    return rc;
}


//-----------------------------------------------------------------------------
// Functions converting betwenn PySequences and pymupdf geometry objects
//-----------------------------------------------------------------------------
static int
jm_init_item(PyObject* obj, Py_ssize_t idx, int* result)
{
    PyObject* temp = PySequence_ITEM(obj, idx);
    if (!temp)
    {
        return 1;
    }
    if (PyLong_Check(temp))
    {
        *result = (int) PyLong_AsLong(temp);
        Py_DECREF(temp);
    }
    else if (PyFloat_Check(temp))
    {
        *result = (int) PyFloat_AsDouble(temp);
        Py_DECREF(temp);
    }
    else
    {
        Py_DECREF(temp);
        return 1;
    }
    if (PyErr_Occurred())
    {
        PyErr_Clear();
        return 1;
    }
    return 0;
}


//----------------------------------------------------------------------------
// Return list of outline xref numbers. Recursive function. Arguments:
// 'obj' first OL item
// 'xrefs' empty Python list
//----------------------------------------------------------------------------
static PyObject* JM_outline_xrefs(mupdf::PdfObj obj, PyObject* xrefs)
{
    if (!obj.m_internal)
    {
        return xrefs;
    }
    PyObject* newxref = nullptr;
    mupdf::PdfObj thisobj = obj;
    while (thisobj.m_internal)
    {
        int nxr = mupdf::pdf_to_num(thisobj);
        newxref = PyLong_FromLong((long) nxr);
        if (PySequence_Contains(xrefs, newxref)
                or mupdf::pdf_dict_get(thisobj, PDF_NAME(Type)).m_internal
                )
        {
            // circular ref or top of chain: terminate
            Py_DECREF(newxref);
            break;
        }
        s_list_append_drop(xrefs, newxref);
        mupdf::PdfObj first = mupdf::pdf_dict_get(thisobj, PDF_NAME(First));  // try go down
        if (mupdf::pdf_is_dict(first))
        {
            xrefs = JM_outline_xrefs(first, xrefs);
        }
        thisobj = mupdf::pdf_dict_get(thisobj, PDF_NAME(Next));  // try go next
        mupdf::PdfObj parent = mupdf::pdf_dict_get(thisobj, PDF_NAME(Parent));  // get parent
        if (!mupdf::pdf_is_dict(thisobj))
        {
            thisobj = parent;
        }
    }
    return xrefs;
}


PyObject* dictkey_align = NULL;
PyObject* dictkey_ascender = NULL;
PyObject* dictkey_bbox = NULL;
PyObject* dictkey_blocks = NULL;
PyObject* dictkey_bpc = NULL;
PyObject* dictkey_c = NULL;
PyObject* dictkey_chars = NULL;
PyObject* dictkey_color = NULL;
PyObject* dictkey_colorspace = NULL;
PyObject* dictkey_content = NULL;
PyObject* dictkey_creationDate = NULL;
PyObject* dictkey_cs_name = NULL;
PyObject* dictkey_da = NULL;
PyObject* dictkey_dashes = NULL;
PyObject* dictkey_desc = NULL;
PyObject* dictkey_descender = NULL;
PyObject* dictkey_dir = NULL;
PyObject* dictkey_effect = NULL;
PyObject* dictkey_ext = NULL;
PyObject* dictkey_filename = NULL;
PyObject* dictkey_fill = NULL;
PyObject* dictkey_flags = NULL;
PyObject* dictkey_font = NULL;
PyObject* dictkey_glyph = NULL;
PyObject* dictkey_height = NULL;
PyObject* dictkey_id = NULL;
PyObject* dictkey_image = NULL;
PyObject* dictkey_items = NULL;
PyObject* dictkey_length = NULL;
PyObject* dictkey_lines = NULL;
PyObject* dictkey_matrix = NULL;
PyObject* dictkey_modDate = NULL;
PyObject* dictkey_name = NULL;
PyObject* dictkey_number = NULL;
PyObject* dictkey_origin = NULL;
PyObject* dictkey_rect = NULL;
PyObject* dictkey_size = NULL;
PyObject* dictkey_smask = NULL;
PyObject* dictkey_spans = NULL;
PyObject* dictkey_stroke = NULL;
PyObject* dictkey_style = NULL;
PyObject* dictkey_subject = NULL;
PyObject* dictkey_text = NULL;
PyObject* dictkey_title = NULL;
PyObject* dictkey_type = NULL;
PyObject* dictkey_ufilename = NULL;
PyObject* dictkey_width = NULL;
PyObject* dictkey_wmode = NULL;
PyObject* dictkey_xref = NULL;
PyObject* dictkey_xres = NULL;
PyObject* dictkey_yres = NULL;

static int dict_setitem_drop(PyObject* dict, PyObject* key, PyObject* value)
{
    if (!dict || !PyDict_Check(dict) || !key || !value)
    {
        return -2;
    }
    int rc = PyDict_SetItem(dict, key, value);
    Py_DECREF(value);
    return rc;
}

static int dict_setitemstr_drop(PyObject* dict, const char* key, PyObject* value)
{
    if (!dict || !PyDict_Check(dict) || !key || !value)
    {
        return -2;
    }
    int rc = PyDict_SetItemString(dict, key, value);
    Py_DECREF(value);
    return rc;
}


static void Document_extend_toc_items(mupdf::PdfDocument& pdf, PyObject* items)
{
    PyObject* item=nullptr;
    PyObject* itemdict=nullptr;
    PyObject* xrefs=nullptr;
    
    PyObject* bold = PyUnicode_FromString("bold");
    PyObject* italic = PyUnicode_FromString("italic");
    PyObject* collapse = PyUnicode_FromString("collapse");
    PyObject* zoom = PyUnicode_FromString("zoom");
    
    try
    {
        /* Need to define these things early because later code uses
        `goto`; otherwise we get compiler warnings 'jump bypasses variable
        initialization' */
        int xref = 0;
        mupdf::PdfObj   root;
        mupdf::PdfObj   olroot;
        mupdf::PdfObj   first;
        Py_ssize_t  n;
        Py_ssize_t  m;
        
        root = mupdf::pdf_dict_get(mupdf::pdf_trailer(pdf), PDF_NAME(Root));
        if (!root.m_internal) goto end;
        
        olroot = mupdf::pdf_dict_get(root, PDF_NAME(Outlines));
        if (!olroot.m_internal) goto end;
        
        first = mupdf::pdf_dict_get(olroot, PDF_NAME(First));
        if (!first.m_internal) goto end;
        
        xrefs = PyList_New(0);  // pre-allocate an empty list
        xrefs = JM_outline_xrefs(first, xrefs);
        n = PySequence_Size(xrefs);
        m = PySequence_Size(items);
        if (!n) goto end;
        
        if (n != m)
        {
            throw std::runtime_error("internal error finding outline xrefs");
        }

        // update all TOC item dictionaries
        for (int i = 0; i < n; i++)
        {
            jm_init_item(xrefs, i, &xref);
            item = PySequence_ITEM(items, i);
            itemdict = PySequence_ITEM(item, 3);
            if (!itemdict || !PyDict_Check(itemdict))
            {
                throw std::runtime_error("need non-simple TOC format");
            }
            PyDict_SetItem(itemdict, dictkey_xref, PySequence_ITEM(xrefs, i));
            mupdf::PdfObj bm = mupdf::pdf_load_object(pdf, xref);
            int flags = mupdf::pdf_to_int(mupdf::pdf_dict_get(bm, PDF_NAME(F)));
            if (flags == 1)
            {
                PyDict_SetItem(itemdict, italic, Py_True);
            }
            else if (flags == 2)
            {
                PyDict_SetItem(itemdict, bold, Py_True);
            }
            else if (flags == 3)
            {
                PyDict_SetItem(itemdict, italic, Py_True);
                PyDict_SetItem(itemdict, bold, Py_True);
            }
            int count = mupdf::pdf_to_int(mupdf::pdf_dict_get(bm, PDF_NAME(Count)));
            if (count < 0)
            {
                PyDict_SetItem(itemdict, collapse, Py_True);
            }
            else if (count > 0)
            {
                PyDict_SetItem(itemdict, collapse, Py_False);
            }
            mupdf::PdfObj col = mupdf::pdf_dict_get(bm, PDF_NAME(C));
            if (mupdf::pdf_is_array(col) && mupdf::pdf_array_len(col) == 3)
            {
                PyObject* color = PyTuple_New(3);
                PyTuple_SET_ITEM(color, 0, Py_BuildValue("f", mupdf::pdf_to_real(mupdf::pdf_array_get(col, 0))));
                PyTuple_SET_ITEM(color, 1, Py_BuildValue("f", mupdf::pdf_to_real(mupdf::pdf_array_get(col, 1))));
                PyTuple_SET_ITEM(color, 2, Py_BuildValue("f", mupdf::pdf_to_real(mupdf::pdf_array_get(col, 2))));
                dict_setitem_drop(itemdict, dictkey_color, color);
            }
            float z=0;
            mupdf::PdfObj obj = mupdf::pdf_dict_get(bm, PDF_NAME(Dest));
            if (!obj.m_internal || !mupdf::pdf_is_array(obj))
            {
                obj = mupdf::pdf_dict_getl(&bm, PDF_NAME(A), PDF_NAME(D), nullptr);
            }
            if (mupdf::pdf_is_array(obj) && mupdf::pdf_array_len(obj) == 5)
            {
                z = mupdf::pdf_to_real(mupdf::pdf_array_get(obj, 4));
            }
            dict_setitem_drop(itemdict, zoom, Py_BuildValue("f", z));
            PyList_SetItem(item, 3, itemdict);
            PyList_SetItem(items, i, item);
        }
        end:;
    }
    catch (std::exception&)
    {
    }
    Py_CLEAR(xrefs);
    Py_CLEAR(bold);
    Py_CLEAR(italic);
    Py_CLEAR(collapse);
    Py_CLEAR(zoom);
}

static void Document_extend_toc_items(mupdf::FzDocument& document, PyObject* items)
{
    mupdf::PdfDocument  pdf = mupdf::pdf_document_from_fz_document(document);
    return Document_extend_toc_items(pdf, items);
}

//-----------------------------------------------------------------------------
// PySequence from fz_rect
//-----------------------------------------------------------------------------
static PyObject* JM_py_from_rect(fz_rect r)
{
    return Py_BuildValue("ffff", r.x0, r.y0, r.x1, r.y1);
}
static PyObject* JM_py_from_rect(mupdf::FzRect r)
{
    return JM_py_from_rect(*r.internal());
}

//-----------------------------------------------------------------------------
// PySequence from fz_point
//-----------------------------------------------------------------------------
static PyObject* JM_py_from_point(fz_point p)
{
    return Py_BuildValue("ff", p.x, p.y);
}

//-----------------------------------------------------------------------------
// PySequence from fz_quad.
//-----------------------------------------------------------------------------
static PyObject *
JM_py_from_quad(fz_quad q)
{
    return Py_BuildValue("((f,f),(f,f),(f,f),(f,f))",
                          q.ul.x, q.ul.y, q.ur.x, q.ur.y,
                          q.ll.x, q.ll.y, q.lr.x, q.lr.y);
}

//----------------------------------------------------------------
// annotation rectangle
//----------------------------------------------------------------
static mupdf::FzRect Annot_rect(mupdf::PdfAnnot& annot)
{
    mupdf::FzRect rect = mupdf::pdf_bound_annot(annot);
    return rect;
}

static PyObject* Annot_rect3(mupdf::PdfAnnot& annot)
{
    fz_rect rect = mupdf::ll_pdf_bound_annot(annot.m_internal);
    return JM_py_from_rect(rect);
}

//-----------------------------------------------------------------------------
// PySequence to fz_rect. Default: infinite rect
//-----------------------------------------------------------------------------
static fz_rect JM_rect_from_py(PyObject* r)
{
    if (!r || !PySequence_Check(r) || PySequence_Size(r) != 4)
    {
        return *mupdf::FzRect(mupdf::FzRect::Fixed_INFINITE).internal();// fz_infinite_rect;
    }
    double f[4];
    for (int i = 0; i < 4; i++)
    {
        if (jm_float_item(r, i, &f[i]) == 1)
        {
            return *mupdf::FzRect(mupdf::FzRect::Fixed_INFINITE).internal();
        }
        if (f[i] < FZ_MIN_INF_RECT) f[i] = FZ_MIN_INF_RECT;
        if (f[i] > FZ_MAX_INF_RECT) f[i] = FZ_MAX_INF_RECT;
    }
    return mupdf::ll_fz_make_rect(
            (float) f[0],
            (float) f[1],
            (float) f[2],
            (float) f[3]
            );
}

//-----------------------------------------------------------------------------
// PySequence to fz_matrix. Default: fz_identity
//-----------------------------------------------------------------------------
static fz_matrix JM_matrix_from_py(PyObject* m)
{
    double a[6];

    if (!m || !PySequence_Check(m) || PySequence_Size(m) != 6)
    {
        return fz_identity;
    }
    for (int i = 0; i < 6; i++)
    {
        if (jm_float_item(m, i, &a[i]) == 1)
        {
            return *mupdf::FzMatrix().internal();
        }
    }
    return mupdf::ll_fz_make_matrix(
            (float) a[0],
            (float) a[1],
            (float) a[2],
            (float) a[3],
            (float) a[4],
            (float) a[5]
            );
}

PyObject* util_transform_rect(PyObject* rect, PyObject* matrix)
{
    return JM_py_from_rect(
            mupdf::ll_fz_transform_rect(
                JM_rect_from_py(rect),
                JM_matrix_from_py(matrix)
                )
            );
}

//----------------------------------------------------------------------------
// return normalized /Rotate value:one of 0, 90, 180, 270
//----------------------------------------------------------------------------
static int JM_norm_rotation(int rotate)
{
    while (rotate < 0) rotate += 360;
    while (rotate >= 360) rotate -= 360;
    if (rotate % 90 != 0) return 0;
    return rotate;
}


//----------------------------------------------------------------------------
// return a PDF page's /Rotate value: one of (0, 90, 180, 270)
//----------------------------------------------------------------------------
static int JM_page_rotation(mupdf::PdfPage& page)
{
    int rotate = 0;
    rotate = mupdf::pdf_to_int(
            mupdf::pdf_dict_get_inheritable(page.obj(), PDF_NAME(Rotate))
            );
    rotate = JM_norm_rotation(rotate);
    return rotate;
}


//----------------------------------------------------------------------------
// return a PDF page's MediaBox
//----------------------------------------------------------------------------
static mupdf::FzRect JM_mediabox(mupdf::PdfObj& page_obj)
{
    mupdf::FzRect mediabox = mupdf::pdf_to_rect(
            mupdf::pdf_dict_get_inheritable(page_obj, PDF_NAME(MediaBox))
            );
    if (mupdf::fz_is_empty_rect(mediabox) || mupdf::fz_is_infinite_rect(mediabox))
    {
        mediabox.x0 = 0;
        mediabox.y0 = 0;
        mediabox.x1 = 612;
        mediabox.y1 = 792;
    }
    mupdf::FzRect   page_mediabox;
    page_mediabox.x0 = mupdf::fz_min(mediabox.x0, mediabox.x1);
    page_mediabox.y0 = mupdf::fz_min(mediabox.y0, mediabox.y1);
    page_mediabox.x1 = mupdf::fz_max(mediabox.x0, mediabox.x1);
    page_mediabox.y1 = mupdf::fz_max(mediabox.y0, mediabox.y1);
    if (0
            || page_mediabox.x1 - page_mediabox.x0 < 1
            || page_mediabox.y1 - page_mediabox.y0 < 1
            )
    {
        page_mediabox = *mupdf::FzRect(mupdf::FzRect::Fixed_UNIT).internal(); //fz_unit_rect;
    }
    return page_mediabox;
}


//----------------------------------------------------------------------------
// return a PDF page's CropBox
//----------------------------------------------------------------------------
mupdf::FzRect JM_cropbox(mupdf::PdfObj& page_obj)
{
    mupdf::FzRect mediabox = JM_mediabox(page_obj);
    mupdf::FzRect cropbox = mupdf::pdf_to_rect(
                mupdf::pdf_dict_get_inheritable(page_obj, PDF_NAME(CropBox))
                );
    if (mupdf::fz_is_infinite_rect(cropbox) || mupdf::fz_is_empty_rect(cropbox))
    {
        cropbox = mediabox;
    }
    float y0 = mediabox.y1 - cropbox.y1;
    float y1 = mediabox.y1 - cropbox.y0;
    cropbox.y0 = y0;
    cropbox.y1 = y1;
    return cropbox;
}


//----------------------------------------------------------------------------
// calculate width and height of the UNROTATED page
//----------------------------------------------------------------------------
static mupdf::FzPoint JM_cropbox_size(mupdf::PdfObj& page_obj)
{
    mupdf::FzPoint size;
    mupdf::FzRect rect = JM_cropbox(page_obj);
    float w = (rect.x0 < rect.x1) ? rect.x1 - rect.x0 : rect.x0 - rect.x1;
    float h = (rect.y0 < rect.y1) ? rect.y1 - rect.y0 : rect.y0 - rect.y1;
    size = fz_make_point(w, h);
    return size;
}


//----------------------------------------------------------------------------
// calculate page rotation matrices
//----------------------------------------------------------------------------
static mupdf::FzMatrix JM_rotate_page_matrix(mupdf::PdfPage& page)
{
    if (!page.m_internal)
    {
        return *mupdf::FzMatrix().internal();  // no valid pdf page given
    }
    int rotation = JM_page_rotation(page);
    if (rotation == 0)
    {
        return *mupdf::FzMatrix().internal();  // no rotation
    }
    auto po = page.obj();
    mupdf::FzPoint cb_size = JM_cropbox_size(po);
    float w = cb_size.x;
    float h = cb_size.y;
    mupdf::FzMatrix m;
    if (rotation == 90)
    {
        m = mupdf::fz_make_matrix(0, 1, -1, 0, h, 0);
    }
    else if (rotation == 180)
    {
        m = mupdf::fz_make_matrix(-1, 0, 0, -1, w, h);
    }
    else
    {
        m = mupdf::fz_make_matrix(0, -1, 1, 0, 0, w);
    }
    return m;
}


static mupdf::FzMatrix JM_derotate_page_matrix(mupdf::PdfPage& page)
{  // just the inverse of rotation
    return mupdf::fz_invert_matrix(JM_rotate_page_matrix(page));
}

//-----------------------------------------------------------------------------
// PySequence from fz_matrix
//-----------------------------------------------------------------------------
static PyObject* JM_py_from_matrix(mupdf::FzMatrix m)
{
    return Py_BuildValue("ffffff", m.a, m.b, m.c, m.d, m.e, m.f);
}

static mupdf::FzMatrix Page_derotate_matrix(mupdf::PdfPage& pdfpage)
{
    if (!pdfpage.m_internal)
    {
        return mupdf::FzMatrix();
    }
    return JM_derotate_page_matrix(pdfpage);
}

static mupdf::FzMatrix Page_derotate_matrix(mupdf::FzPage& page)
{
    mupdf::PdfPage pdf_page = mupdf::pdf_page_from_fz_page(page);
    return Page_derotate_matrix(pdf_page);
}


static PyObject *lll_JM_get_annot_xref_list(pdf_obj *page_obj)
{
    fz_context* ctx = mupdf::internal_context_get();
    PyObject *names = PyList_New(0);
    pdf_obj *id, *subtype, *annots, *annot_obj;
    int xref, type, i, n;
    fz_try(ctx) {
        annots = pdf_dict_get(ctx, page_obj, PDF_NAME(Annots));
        n = pdf_array_len(ctx, annots);
        for (i = 0; i < n; i++) {
            annot_obj = pdf_array_get(ctx, annots, i);
            xref = pdf_to_num(ctx, annot_obj);
            subtype = pdf_dict_get(ctx, annot_obj, PDF_NAME(Subtype));
            if (!subtype) {
                continue;  // subtype is required
            }
            type = pdf_annot_type_from_string(ctx, pdf_to_name(ctx, subtype));
            if (type == PDF_ANNOT_UNKNOWN) {
                continue;  // only accept valid annot types
            }
            id = pdf_dict_gets(ctx, annot_obj, "NM");
            LIST_APPEND_DROP(names, Py_BuildValue("iis", xref, type, pdf_to_text_string(ctx, id)));
        }
    }
    fz_catch(ctx) {
        return names;
    }
    return names;
}
//------------------------------------------------------------------------
// return the xrefs and /NM ids of a page's annots, links and fields
//------------------------------------------------------------------------
static PyObject* JM_get_annot_xref_list(const mupdf::PdfObj& page_obj)
{
    PyObject* names = PyList_New(0);
    if (!page_obj.m_internal)
    {
        return names;
    }
    return lll_JM_get_annot_xref_list( page_obj.m_internal);
}

static mupdf::FzBuffer JM_object_to_buffer(const mupdf::PdfObj& what, int compress, int ascii)
{
    mupdf::FzBuffer res = mupdf::fz_new_buffer(512);
    mupdf::FzOutput out(res);
    mupdf::pdf_print_obj(out, what, compress, ascii);
    out.fz_close_output();
    mupdf::fz_terminate_buffer(res);
    return res;
}

static PyObject* JM_EscapeStrFromBuffer(mupdf::FzBuffer& buff)
{
    if (!buff.m_internal)
    {
        return PyUnicode_FromString("");
    }
    unsigned char* s = nullptr;
    size_t len = mupdf::fz_buffer_storage(buff, &s);
    PyObject* val = PyUnicode_DecodeRawUnicodeEscape((const char*) s, (Py_ssize_t) len, "replace");
    if (!val)
    {
        val = PyUnicode_FromString("");
        PyErr_Clear();
    }
    return val;
}

static PyObject* xref_object(mupdf::PdfDocument& pdf, int xref, int compressed=0, int ascii=0)
{
    if (!pdf.m_internal)
    {
        throw std::runtime_error(MSG_IS_NO_PDF);
    }
    int xreflen = mupdf::pdf_xref_len(pdf);
    if ((xref < 1 || xref >= xreflen) and xref != -1) 
    {
        throw std::runtime_error(MSG_BAD_XREF);
    }
    mupdf::PdfObj obj = (xref > 0) ? mupdf::pdf_load_object(pdf, xref) : mupdf::pdf_trailer(pdf);
    mupdf::FzBuffer res = JM_object_to_buffer(mupdf::pdf_resolve_indirect(obj), compressed, ascii);
    PyObject* text = JM_EscapeStrFromBuffer(res);
    return text;
}

static PyObject* xref_object(mupdf::FzDocument& document, int xref, int compressed=0, int ascii=0)
{
    mupdf::PdfDocument pdf = mupdf::pdf_document_from_fz_document(document);
    return xref_object(pdf, xref, compressed, ascii);
}


//-------------------------------------
// fz_output for Python file objects
//-------------------------------------

static PyObject* Link_is_external(mupdf::FzLink& this_link)
{
    const char* uri = this_link.m_internal->uri;
    if (!uri)
    {
        return PyBool_FromLong(0);
    }
    bool ret = mupdf::fz_is_external_link(uri);
    return PyBool_FromLong((long) ret);
}

static mupdf::FzLink Link_next(mupdf::FzLink& this_link)
{
    return this_link.next();
}


//-----------------------------------------------------------------------------
// create PDF object from given string (new in v1.14.0: MuPDF dropped it)
//-----------------------------------------------------------------------------
static pdf_obj *lll_JM_pdf_obj_from_str(fz_context *ctx, pdf_document *doc, const char *src)
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
        mupdf::internal_throw_exception(ctx);
    }

    return result;

}

/*********************************************************************/
// Page._addAnnot_FromString
// Add new links provided as an array of string object definitions.
/*********************************************************************/
PyObject* Page_addAnnot_FromString(mupdf::PdfPage& page, PyObject* linklist)
{
    PyObject* txtpy = nullptr;
    int lcount = (int) PySequence_Size(linklist); // link count
    //printf("Page_addAnnot_FromString(): lcount=%i\n", lcount);
    if (lcount < 1)
    {
        Py_RETURN_NONE;
    }
    try
    {
        // insert links from the provided sources
        if (!page.m_internal)
        {
            throw std::runtime_error(MSG_IS_NO_PDF);
        }
        if (!mupdf::pdf_dict_get(page.obj(), PDF_NAME(Annots)).m_internal)
        {
            mupdf::pdf_dict_put_array(page.obj(), PDF_NAME(Annots), lcount);
        }
        mupdf::PdfObj annots = mupdf::pdf_dict_get(page.obj(), PDF_NAME(Annots));
        mupdf::PdfDocument doc = page.doc();
        //printf("lcount=%i\n", lcount);
        fz_context* ctx = mupdf::internal_context_get();
        for (int i = 0; i < lcount; i++)
        {
            const char* text = nullptr;
            txtpy = PySequence_ITEM(linklist, (Py_ssize_t) i);
            text = PyUnicode_AsUTF8(txtpy);
            Py_CLEAR(txtpy);
            if (!text)
            {
                messagef("skipping bad link / annot item %i.", i);
                continue;
            }
            try
            {
                pdf_obj* obj = lll_JM_pdf_obj_from_str(ctx, doc.m_internal, text);
                pdf_obj* annot = pdf_add_object_drop(
                        ctx,
                        doc.m_internal,
                        obj
                        );
                pdf_obj* ind_obj = pdf_new_indirect(ctx, doc.m_internal, pdf_to_num(ctx, annot), 0);
                pdf_array_push_drop(ctx, annots.m_internal, ind_obj);
                pdf_drop_obj(ctx, annot);
             }
            catch (std::exception&)
            {
                messagef("skipping bad link / annot item %i.", i);
            }
        }
    }
    catch (std::exception&)
    {
        PyErr_Clear();
        return nullptr;
    }
    Py_RETURN_NONE;
}

PyObject* Page_addAnnot_FromString(mupdf::FzPage& page, PyObject* linklist)
{
    mupdf::PdfPage pdf_page = mupdf::pdf_page_from_fz_page(page);
    return Page_addAnnot_FromString(pdf_page, linklist);
}

static int page_count_fz2(void* document)
{
    mupdf::FzDocument* document2 = (mupdf::FzDocument*) document;
    return mupdf::fz_count_pages(*document2);
}

static int page_count_fz(mupdf::FzDocument& document)
{
    return mupdf::fz_count_pages(document);
}

static int page_count_pdf(mupdf::PdfDocument& pdf)
{
    mupdf::FzDocument document = pdf.super();
    return page_count_fz(document);
}

static int page_count(mupdf::FzDocument& document)
{
    return mupdf::fz_count_pages(document);
}

static int page_count(mupdf::PdfDocument& pdf)
{
    mupdf::FzDocument document = pdf.super();
    return page_count(document);
}

static PyObject* page_annot_xrefs(mupdf::FzDocument& document, mupdf::PdfDocument& pdf, int pno)
{
    int page_count = mupdf::fz_count_pages(document);
    int n = pno;
    while (n < 0)
    {
        n += page_count;
    }
    PyObject* annots = nullptr;
    if (n >= page_count)
    {
        throw std::runtime_error(MSG_BAD_PAGENO);
    }
    if (!pdf.m_internal)
    {
        throw std::runtime_error(MSG_IS_NO_PDF);
    }
    annots = JM_get_annot_xref_list(mupdf::pdf_lookup_page_obj(pdf, n));
    return annots;
}

static PyObject* page_annot_xrefs(mupdf::FzDocument& document, int pno)
{
    mupdf::PdfDocument pdf = mupdf::pdf_specifics(document);
    return page_annot_xrefs(document, pdf, pno);
}

static PyObject* page_annot_xrefs(mupdf::PdfDocument& pdf, int pno)
{
    mupdf::FzDocument document = pdf.super();
    return page_annot_xrefs(document, pdf, pno);
}

static bool Outline_is_external(mupdf::FzOutline* outline)
{
    if (!outline->m_internal->uri)
    {
        return false;
    }
    return mupdf::ll_fz_is_external_link(outline->m_internal->uri);
}

int ll_fz_absi(int i)
{
    return mupdf::ll_fz_absi(i);
}

enum
{
    TEXT_FONT_SUPERSCRIPT = 1,
    TEXT_FONT_ITALIC = 2,
    TEXT_FONT_SERIFED = 4,
    TEXT_FONT_MONOSPACED = 8,
    TEXT_FONT_BOLD = 16,
};

/* todo: implement fns to set these and sync with __init__.py. */
int g_skip_quad_corrections = 0;
int g_subset_fontnames = 0;
int g_small_glyph_heights = 0;

void set_small_glyph_heights(int on)
{
    g_small_glyph_heights = on;
}

struct jm_lineart_device
{
    fz_device super;
    
    PyObject* out = {};
    PyObject* method = {};
    PyObject* pathdict = {};
    PyObject* scissors = {};
    float pathfactor = {};
    fz_matrix ctm = {};
    fz_matrix ptm = {};
    fz_matrix rot = {};
    fz_point lastpoint = {};
    fz_point firstpoint = {};
    int havemove = 0;
    fz_rect pathrect = {};
    int clips = {};
    int linecount = {};
    float linewidth = {};
    int path_type = {};
    long depth = {};
    size_t seqno = {};
    char* layer_name;
};


static void jm_lineart_drop_device(fz_context *ctx, fz_device *dev_)
{
    jm_lineart_device *dev = (jm_lineart_device *)dev_;
    if (PyList_Check(dev->out)) {
        Py_CLEAR(dev->out);
    }
    Py_CLEAR(dev->method);
    Py_CLEAR(dev->scissors);
    mupdf::ll_fz_free(dev->layer_name);
    dev->layer_name = nullptr;
}

typedef jm_lineart_device jm_tracedraw_device;

// need own versions of ascender / descender
static float JM_font_ascender(fz_font* font)
{
    if (g_skip_quad_corrections)
    {
        return 0.8f;
    }
    return mupdf::ll_fz_font_ascender(font);
}

static float JM_font_descender(fz_font* font)
{
    if (g_skip_quad_corrections)
    {
        return -0.2f;
    }
    return mupdf::ll_fz_font_descender(font);
}


//----------------------------------------------------------------
// Return true if character is considered to be a word delimiter
//----------------------------------------------------------------
static int 
JM_is_word_delimiter(int c, PyObject *delimiters)
{
    if (c <= 32 || c == 160) return 1;  // a standard delimiter

    // extra delimiters must be a non-empty sequence
    if (!delimiters || PyObject_Not(delimiters) || !PySequence_Check(delimiters)) {  
        return 0;
    }

    // convert to tuple for easier looping
    PyObject *delims = PySequence_Tuple(delimiters);
    if (!delims) {
        PyErr_Clear();
        return 0;
    }

    // Make 1-char PyObject from character given as integer
    PyObject *cchar = Py_BuildValue("C", c);  // single character PyObject
    Py_ssize_t i, len = PyTuple_Size(delims);
    for (i = 0; i < len; i++) {
        int rc = PyUnicode_Compare(cchar, PyTuple_GET_ITEM(delims, i));
        if (rc == 0) {  // equal to a delimiter character
            Py_DECREF(cchar);
            Py_DECREF(delims);
            PyErr_Clear();
            return 1;
        }
    }

    Py_DECREF(delims);
    PyErr_Clear();
    return 0;
}


static const char* JM_font_name(fz_font* font)
{
    const char* name = mupdf::ll_fz_font_name(font);
    const char* s = strchr(name, '+');
    if (g_subset_fontnames || !s || s-name != 6)
    {
        return name;
    }
    return s + 1;
}

static void jm_trace_text_span(
        jm_tracedraw_device* dev,
        fz_text_span* span,
        int type,
        fz_matrix ctm,
        fz_colorspace* colorspace,
        const float* color,
        float alpha,
        size_t seqno
        )
{
    //printf("extra.jm_trace_text_span(): seqno=%zi\n", seqno);
    //fz_matrix join = mupdf::ll_fz_concat(span->trm, ctm);
    //double fsize = sqrt(fabs((double) span->trm.a * (double) span->trm.d));
    fz_matrix mat = mupdf::ll_fz_concat(span->trm, ctm); // text transformation matrix
    fz_point dir = mupdf::ll_fz_transform_vector(mupdf::ll_fz_make_point(1, 0), mat); // writing direction
    double fsize = sqrt(dir.x * dir.x + dir.y * dir.y); // font size

    dir = mupdf::ll_fz_normalize_vector(dir);

    // compute effective ascender / descender
    double asc = (double) JM_font_ascender(span->font);
    double dsc = (double) JM_font_descender(span->font);
    if (asc < 1e-3) {  // probably Tesseract font
        dsc = -0.1;
        asc = 0.9;
    }

    double ascsize = asc * fsize / (asc - dsc);
    double dscsize = dsc * fsize / (asc - dsc);
    int fflags = 0; // font flags
    int mono = mupdf::ll_fz_font_is_monospaced(span->font);
    fflags += mono * TEXT_FONT_MONOSPACED;
    fflags += mupdf::ll_fz_font_is_italic(span->font) * TEXT_FONT_ITALIC;
    fflags += mupdf::ll_fz_font_is_serif(span->font) * TEXT_FONT_SERIFED;
    fflags += mupdf::ll_fz_font_is_bold(span->font) * TEXT_FONT_BOLD;

    // walk through characters of span
    fz_matrix rot = mupdf::ll_fz_make_matrix(dir.x, dir.y, -dir.y, dir.x, 0, 0);
    if (dir.x == -1)
    {
        // left-right flip
        rot.d = 1;
    }
    PyObject* chars = PyTuple_New(span->len);
    double space_adv = 0;
    double last_adv = 0;
    fz_rect span_bbox;
    
    for (int i = 0; i < span->len; i++)
    {
        double adv = 0;
        if (span->items[i].gid >= 0)
        {
            adv = (double) mupdf::ll_fz_advance_glyph(span->font, span->items[i].gid, span->wmode);
        }
        adv *= fsize;
        last_adv = adv;
        if (span->items[i].ucs == 32)
        {
            space_adv = adv;
        }
        fz_point char_orig;
        char_orig = fz_make_point(span->items[i].x, span->items[i].y);
        char_orig = fz_transform_point(char_orig, ctm);
        fz_matrix m1 = mupdf::ll_fz_make_matrix(1, 0, 0, 1, -char_orig.x, -char_orig.y);
        m1 = mupdf::ll_fz_concat(m1, rot);
        m1 = mupdf::ll_fz_concat(m1, mupdf::ll_fz_make_matrix(1, 0, 0, 1, char_orig.x, char_orig.y));
        float x0 = char_orig.x;
        float x1 = x0 + adv;
        float y0;
        float y1;
        if (
                (mat.d > 0 && (dir.x == 1 || dir.x == -1))
                ||
                (mat.b !=0 && mat.b == -mat.c)
                )   // up-down flip
        {
            // up-down flip
            y0 = char_orig.y + dscsize;
            y1 = char_orig.y + ascsize;
        }
        else
        {
            y0 = char_orig.y - ascsize;
            y1 = char_orig.y - dscsize;
        }
        fz_rect char_bbox = mupdf::ll_fz_make_rect(x0, y0, x1, y1);
        char_bbox = mupdf::ll_fz_transform_rect(char_bbox, m1);
        PyTuple_SET_ITEM(
                chars,
                (Py_ssize_t) i,
                Py_BuildValue(
                    "ii(ff)(ffff)",
                    span->items[i].ucs,
                    span->items[i].gid,
                    char_orig.x,
                    char_orig.y,
                    char_bbox.x0,
                    char_bbox.y0,
                    char_bbox.x1,
                    char_bbox.y1
                    )
                );
        if (i > 0)
        {
            span_bbox = mupdf::ll_fz_union_rect(span_bbox, char_bbox);
        }
        else
        {
            span_bbox = char_bbox;
        }
    }
    if (!space_adv)
    {
        if (!mono)
        {
            fz_font* out_font = nullptr;
            space_adv = mupdf::ll_fz_advance_glyph(
                    span->font,
                    mupdf::ll_fz_encode_character_with_fallback(span->font, 32, 0, 0, &out_font),
                    span->wmode
                    );
            space_adv *= fsize;
            if (!space_adv)
            {
                space_adv = last_adv;
            }
        }
        else
        {
            space_adv = last_adv; // for mono any char width suffices
        }
    }
    // make the span dictionary
    PyObject* span_dict = PyDict_New();
    dict_setitemstr_drop(span_dict, "dir", JM_py_from_point(dir));
    dict_setitem_drop(span_dict, dictkey_font, JM_EscapeStrFromStr(JM_font_name(span->font)));
    dict_setitem_drop(span_dict, dictkey_wmode, PyLong_FromLong((long) span->wmode));
    dict_setitem_drop(span_dict, dictkey_flags, PyLong_FromLong((long) fflags));
    dict_setitemstr_drop(span_dict, "bidi_lvl", PyLong_FromLong((long) span->bidi_level));
    dict_setitemstr_drop(span_dict, "bidi_dir", PyLong_FromLong((long) span->markup_dir));
    dict_setitem_drop(span_dict, dictkey_ascender, PyFloat_FromDouble(asc));
    dict_setitem_drop(span_dict, dictkey_descender, PyFloat_FromDouble(dsc));
    dict_setitem_drop(span_dict, dictkey_colorspace, PyLong_FromLong(3));
    float rgb[3];
    if (colorspace)
    {
        mupdf::ll_fz_convert_color(
                colorspace,
                color,
                mupdf::ll_fz_device_rgb(),
                rgb,
                nullptr,
                fz_default_color_params
                );
    }
    else
    {
        rgb[0] = rgb[1] = rgb[2] = 0;
    }
    double linewidth;
    if (dev->linewidth > 0)  // width of character border
    {
        linewidth = (double) dev->linewidth;
    }
    else
    {
	linewidth = fsize * 0.05;  // default: 5% of font size
    }
    if (0) std::cout
            << " dev->linewidth=" << dev->linewidth
            << " fsize=" << fsize
            << " linewidth=" << linewidth
            << "\n";
    
    dict_setitem_drop(span_dict, dictkey_color, Py_BuildValue("fff", rgb[0], rgb[1], rgb[2]));
    dict_setitem_drop(span_dict, dictkey_size, PyFloat_FromDouble(fsize));
    dict_setitemstr_drop(span_dict, "opacity", PyFloat_FromDouble((double) alpha));
    dict_setitemstr_drop(span_dict, "linewidth", PyFloat_FromDouble((double) linewidth));
    dict_setitemstr_drop(span_dict, "spacewidth", PyFloat_FromDouble(space_adv));
    dict_setitem_drop(span_dict, dictkey_type, PyLong_FromLong((long) type));
    dict_setitem_drop(span_dict, dictkey_bbox, JM_py_from_rect(span_bbox));
    dict_setitemstr_drop(span_dict, "layer", JM_UnicodeFromStr(dev->layer_name));
    dict_setitemstr_drop(span_dict, "seqno", PyLong_FromSize_t(seqno));
    dict_setitem_drop(span_dict, dictkey_chars, chars);
    //std::cout << "span_dict=" << repr(span_dict) << "\n";
    s_list_append_drop(dev->out, span_dict);
}

static inline void jm_increase_seqno(fz_context* ctx, fz_device* dev_)
{
    jm_tracedraw_device* dev = (jm_tracedraw_device*) dev_;
    dev->seqno += 1;
}

static void jm_fill_path(
        fz_context* ctx,
        fz_device* dev,
        const fz_path*,
        int even_odd,
        fz_matrix,
        fz_colorspace*,
        const float* color,
        float alpha,
        fz_color_params
        )
{
    jm_increase_seqno(ctx, dev);
}

static void jm_fill_shade(
        fz_context* ctx,
        fz_device* dev,
        fz_shade* shd,
        fz_matrix ctm,
        float alpha,
        fz_color_params color_params
        )
{
    jm_increase_seqno(ctx, dev);
}

static void jm_fill_image(
        fz_context* ctx,
        fz_device* dev,
        fz_image* img,
        fz_matrix ctm,
        float alpha,
        fz_color_params color_params
        )
{
    jm_increase_seqno(ctx, dev);
}

static void jm_fill_image_mask(
        fz_context* ctx,
        fz_device* dev,
        fz_image* img,
        fz_matrix ctm,
        fz_colorspace* cs,
        const float* color,
        float alpha,
        fz_color_params color_params
        )
{
    jm_increase_seqno(ctx, dev);
}

static void jm_dev_linewidth(
        fz_context* ctx,
        fz_device* dev_,
        const fz_path* path,
        const fz_stroke_state* stroke,
        fz_matrix ctm,
        fz_colorspace* colorspace,
        const float* color,
        float alpha,
        fz_color_params color_params
        )
{
    jm_tracedraw_device* dev = (jm_tracedraw_device*) dev_;
    if (0) std::cout << "jm_dev_linewidth(): changing dev->linewidth from " << dev->linewidth
            << " to stroke->linewidth=" << stroke->linewidth
            << "\n";
    dev->linewidth = stroke->linewidth;
    jm_increase_seqno(ctx, dev_);
}

static void jm_trace_text(
        jm_tracedraw_device* dev,
        const fz_text* text,
        int type,
        fz_matrix ctm,
        fz_colorspace* colorspace,
        const float* color,
        float alpha,
        size_t seqno
        )
{
    fz_text_span* span;
    for (span = text->head; span; span = span->next)
    {
        jm_trace_text_span(dev, span, type, ctm, colorspace, color, alpha, seqno);
    }
}

/*---------------------------------------------------------
There are 3 text trace types:
0 - fill text (PDF Tr 0)
1 - stroke text (PDF Tr 1)
3 - ignore text (PDF Tr 3)
---------------------------------------------------------*/
static void
jm_tracedraw_fill_text(
        fz_context* ctx,
        fz_device* dev_,
        const fz_text* text,
        fz_matrix ctm,
        fz_colorspace* colorspace,
        const float* color,
        float alpha,
        fz_color_params color_params
        )
{
    jm_tracedraw_device* dev = (jm_tracedraw_device*) dev_;
    jm_trace_text(dev, text, 0, ctm, colorspace, color, alpha, dev->seqno);
    dev->seqno += 1;
}

static void
jm_tracedraw_stroke_text(
        fz_context* ctx,
        fz_device* dev_,
        const fz_text* text,
        const fz_stroke_state* stroke,
        fz_matrix ctm,
        fz_colorspace* colorspace,
        const float* color,
        float alpha,
        fz_color_params color_params
        )
{
    jm_tracedraw_device* dev = (jm_tracedraw_device*) dev_;
    jm_trace_text(dev, text, 1, ctm, colorspace, color, alpha, dev->seqno);
    dev->seqno += 1;
}


static void
jm_tracedraw_ignore_text(
        fz_context* ctx,
        fz_device* dev_,
        const fz_text* text,
        fz_matrix ctm
        )
{
    jm_tracedraw_device* dev = (jm_tracedraw_device*) dev_;
    jm_trace_text(dev, text, 3, ctm, nullptr, nullptr, 1, dev->seqno);
    dev->seqno += 1;
}

static void
jm_lineart_begin_layer(fz_context *ctx, fz_device *dev_, const char *name)
{
    jm_tracedraw_device* dev = (jm_tracedraw_device*) dev_;
    mupdf::ll_fz_free(dev->layer_name);
    dev->layer_name = mupdf::ll_fz_strdup(name);
}

static void
jm_lineart_end_layer(fz_context *ctx, fz_device *dev_)
{
    jm_tracedraw_device* dev = (jm_tracedraw_device*) dev_;
    mupdf::ll_fz_free(dev->layer_name);
    dev->layer_name = nullptr;
}


mupdf::FzDevice JM_new_texttrace_device(PyObject* out)
{
    mupdf::FzDevice device(sizeof(jm_tracedraw_device));
    jm_tracedraw_device* dev = (jm_tracedraw_device*) device.m_internal;
    
    dev->super.close_device = nullptr;    
    dev->super.drop_device = jm_lineart_drop_device;    
    dev->super.fill_path = jm_fill_path;
    dev->super.stroke_path = jm_dev_linewidth;
    dev->super.clip_path = nullptr;
    dev->super.clip_stroke_path = nullptr;

    dev->super.fill_text = jm_tracedraw_fill_text;
    dev->super.stroke_text = jm_tracedraw_stroke_text;
    dev->super.clip_text = nullptr;
    dev->super.clip_stroke_text = nullptr;
    dev->super.ignore_text = jm_tracedraw_ignore_text;

    dev->super.fill_shade = jm_fill_shade;
    dev->super.fill_image = jm_fill_image;
    dev->super.fill_image_mask = jm_fill_image_mask;
    dev->super.clip_image_mask = nullptr;

    dev->super.pop_clip = nullptr;

    dev->super.begin_mask = nullptr;
    dev->super.end_mask = nullptr;
    dev->super.begin_group = nullptr;
    dev->super.end_group = nullptr;

    dev->super.begin_tile = nullptr;
    dev->super.end_tile = nullptr;

    dev->super.begin_layer = jm_lineart_begin_layer;
    dev->super.end_layer = jm_lineart_end_layer;

    dev->super.begin_structure = nullptr;
    dev->super.end_structure = nullptr;

    dev->super.begin_metatext = nullptr;
    dev->super.end_metatext = nullptr;

    dev->super.render_flags = nullptr;
    dev->super.set_default_colorspaces = nullptr;

    Py_XINCREF(out);
    dev->out = out;
    dev->seqno = 0;
    return device;
}


static fz_quad
JM_char_quad(fz_stext_line *line, fz_stext_char *ch)
{
    if (g_skip_quad_corrections) {  // no special handling
        return ch->quad;
    }
    if (line->wmode) {  // never touch vertical write mode
        return ch->quad;
    }
    fz_font *font = ch->font;
    float asc = JM_font_ascender(font);
    float dsc = JM_font_descender(font);
    float c, s, fsize = ch->size;
    float asc_dsc = asc - dsc + FLT_EPSILON;
    if (asc_dsc >= 1 && g_small_glyph_heights == 0) {  // no problem
       return ch->quad;
    }
    if (asc < 1e-3) {  // probably Tesseract glyphless font
        dsc = -0.1f;
        asc = 0.9f;
        asc_dsc = 1.0f;
    }

    if (g_small_glyph_heights || asc_dsc < 1) {
        dsc = dsc / asc_dsc;
        asc = asc / asc_dsc;
    }
    asc_dsc = asc - dsc;
    asc = asc * fsize / asc_dsc;
    dsc = dsc * fsize / asc_dsc;

    /* ------------------------------
    Re-compute quad with the adjusted ascender / descender values:
    Move ch->origin to (0,0) and de-rotate quad, then adjust the corners,
    re-rotate and move back to ch->origin location.
    ------------------------------ */
    fz_matrix trm1, trm2, xlate1, xlate2;
    fz_quad quad;
    c = line->dir.x;  // cosine
    s = line->dir.y;  // sine
    trm1 = mupdf::ll_fz_make_matrix(c, -s, s, c, 0, 0);  // derotate
    trm2 = mupdf::ll_fz_make_matrix(c, s, -s, c, 0, 0);  // rotate
    if (c == -1) {  // left-right flip
        trm1.d = 1;
        trm2.d = 1;
    }
    xlate1 = mupdf::ll_fz_make_matrix(1, 0, 0, 1, -ch->origin.x, -ch->origin.y);
    xlate2 = mupdf::ll_fz_make_matrix(1, 0, 0, 1, ch->origin.x, ch->origin.y);

    quad = mupdf::ll_fz_transform_quad(ch->quad, xlate1);  // move origin to (0,0)
    quad = mupdf::ll_fz_transform_quad(quad, trm1);  // de-rotate corners

    // adjust vertical coordinates
    if (c == 1 && quad.ul.y > 0) {  // up-down flip
        quad.ul.y = asc;
        quad.ur.y = asc;
        quad.ll.y = dsc;
        quad.lr.y = dsc;
    } else {
        quad.ul.y = -asc;
        quad.ur.y = -asc;
        quad.ll.y = -dsc;
        quad.lr.y = -dsc;
    }

    // adjust horizontal coordinates that are too crazy:
    // (1) left x must be >= 0
    // (2) if bbox width is 0, lookup char advance in font.
    if (quad.ll.x < 0) {
        quad.ll.x = 0;
        quad.ul.x = 0;
    }
    float cwidth = quad.lr.x - quad.ll.x;
    if (cwidth < FLT_EPSILON) {
        int glyph = mupdf::ll_fz_encode_character( font, ch->c);
        if (glyph) {
            float fwidth = mupdf::ll_fz_advance_glyph( font, glyph, line->wmode);
            quad.lr.x = quad.ll.x + fwidth * fsize;
            quad.ur.x = quad.lr.x;
        }
    }

    quad = mupdf::ll_fz_transform_quad(quad, trm2);  // rotate back
    quad = mupdf::ll_fz_transform_quad(quad, xlate2);  // translate back
    return quad;
}


static fz_rect JM_char_bbox(fz_stext_line* line, fz_stext_char* ch)
{
    fz_rect r = mupdf::ll_fz_rect_from_quad(JM_char_quad( line, ch));
    if (!line->wmode) {
        return r;
    }
    if (r.y1 < r.y0 + ch->size) {
        r.y0 = r.y1 - ch->size;
    }
    return r;
}

fz_rect JM_char_bbox(const mupdf::FzStextLine& line, const mupdf::FzStextChar& ch)
{
    return JM_char_bbox( line.m_internal, ch.m_internal);
}

static int JM_rects_overlap(const fz_rect a, const fz_rect b)
{
    if (0
            || a.x0 >= b.x1
            || a.y0 >= b.y1
            || a.x1 <= b.x0
            || a.y1 <= b.y0
            )
        return 0;
    return 1;
}

//
void JM_append_rune(fz_buffer *buff, int ch);

//-----------------------------------------------------------------------------
// Plain text output. An identical copy of fz_print_stext_page_as_text,
// but lines within a block are concatenated by space instead a new-line
// character (which else leads to 2 new-lines).
//-----------------------------------------------------------------------------
void JM_print_stext_page_as_text(mupdf::FzBuffer& res, mupdf::FzStextPage& page)
{
    fz_rect rect = page.m_internal->mediabox;

    for (auto block: page)
    {
        if (block.m_internal->type == FZ_STEXT_BLOCK_TEXT)
        {
            for (auto line: block)
            {
                int last_char = 0;
                for (auto ch: line)
                {
                    fz_rect chbbox = JM_char_bbox( line, ch);
                    if (mupdf::ll_fz_is_infinite_rect(rect)
                            || JM_rects_overlap(rect, chbbox)
                            )
                    {
                        last_char = ch.m_internal->c;
                        JM_append_rune(res.m_internal, last_char);
                    }
                }
                if (last_char != 10 && last_char > 0)
                {
                    mupdf::ll_fz_append_string(res.m_internal, "\n");
                }
            }
        }
    }
}



// path_type is one of:
#define FILL_PATH 1
#define STROKE_PATH 2
#define CLIP_PATH 3
#define CLIP_STROKE_PATH 4

// Every scissor of a clip is a sub rectangle of the preceeding clip
// scissor if the clip level is larger.
static fz_rect compute_scissor(jm_lineart_device *dev)
{
    PyObject *last_scissor = NULL;
    fz_rect scissor;
    if (!dev->scissors) {
        dev->scissors = PyList_New(0);
    }
    Py_ssize_t num_scissors = PyList_Size(dev->scissors);
    if (num_scissors > 0) {
        last_scissor = PyList_GET_ITEM(dev->scissors, num_scissors-1);
        scissor = JM_rect_from_py(last_scissor);
        scissor = fz_intersect_rect(scissor, dev->pathrect);
    } else {
        scissor = dev->pathrect;
    }
    LIST_APPEND_DROP(dev->scissors, JM_py_from_rect(scissor));
    return scissor;
}


/*
--------------------------------------------------------------------------
Check whether the last 4 lines represent a quad.
Because of how we count, the lines are a polyline already, i.e. last point
of a line equals 1st point of next line.
So we check for a polygon (last line's end point equals start point).
If not true we return 0.
--------------------------------------------------------------------------
*/
static int
jm_checkquad(jm_lineart_device* dev)
{
    PyObject *items = PyDict_GetItem(dev->pathdict, dictkey_items);
    Py_ssize_t i, len = PyList_Size(items);
    float f[8]; // coordinates of the 4 corners
    mupdf::FzPoint temp, lp; // line = (temp, lp)
    PyObject *rect;
    PyObject *line;
    // fill the 8 floats in f, start from items[-4:]
    for (i = 0; i < 4; i++) {  // store line start points
        line = PyList_GET_ITEM(items, len - 4 + i);
        temp = JM_point_from_py(PyTuple_GET_ITEM(line, 1));
        f[i * 2] = temp.x;
        f[i * 2 + 1] = temp.y;
        lp = JM_point_from_py(PyTuple_GET_ITEM(line, 2));
    }
    if (lp.x != f[0] || lp.y != f[1]) {
        // not a polygon!
        //dev_linecount -= 1;
        return 0;
    }

    // we have detected a quad
    dev->linecount = 0;  // reset this
    // a quad item is ("qu", (ul, ur, ll, lr)), where the tuple items
    // are pairs of floats representing a quad corner each.
    rect = PyTuple_New(2);
    PyTuple_SET_ITEM(rect, 0, PyUnicode_FromString("qu"));
    /* ----------------------------------------------------
    * relationship of float array to quad points:
    * (0, 1) = ul, (2, 3) = ll, (6, 7) = ur, (4, 5) = lr
    ---------------------------------------------------- */
    fz_quad q = fz_make_quad(f[0], f[1], f[6], f[7], f[2], f[3], f[4], f[5]);
    PyTuple_SET_ITEM(rect, 1, JM_py_from_quad(q));
    PyList_SetItem(items, len - 4, rect); // replace item -4 by rect
    PyList_SetSlice(items, len - 3, len, NULL); // delete remaining 3 items
    return 1;
}


/*
--------------------------------------------------------------------------
Check whether the last 3 path items represent a rectangle.
Line 1 and 3 must be horizontal, line 2 must be vertical.
Returns 1 if we have modified the path, otherwise 0.
--------------------------------------------------------------------------
*/
static int
jm_checkrect(jm_lineart_device* dev)
{
    dev->linecount = 0; // reset line count
    long orientation = 0; // area orientation of rectangle
    mupdf::FzPoint ll, lr, ur, ul;
    mupdf::FzRect r;
    PyObject *rect;
    PyObject *line0, *line2;
    PyObject *items = PyDict_GetItem(dev->pathdict, dictkey_items);
    Py_ssize_t len = PyList_Size(items);

    line0 = PyList_GET_ITEM(items, len - 3);
    ll = JM_point_from_py(PyTuple_GET_ITEM(line0, 1));
    lr = JM_point_from_py(PyTuple_GET_ITEM(line0, 2));
    // no need to extract "line1"!
    line2 = PyList_GET_ITEM(items, len - 1);
    ur = JM_point_from_py(PyTuple_GET_ITEM(line2, 1));
    ul = JM_point_from_py(PyTuple_GET_ITEM(line2, 2));

    /*
    ---------------------------------------------------------------------
    Assumption:
    When decomposing rects, MuPDF always starts with a horizontal line,
    followed by a vertical line, followed by a horizontal line.
    First line: (ll, lr), third line: (ul, ur).
    If 1st line is below 3rd line, we record anti-clockwise (+1), else
    clockwise (-1) orientation.
    ---------------------------------------------------------------------
    */
    if (ll.y != lr.y ||
        ll.x != ul.x ||
        ur.y != ul.y ||
        ur.x != lr.x) {
        goto drop_out;  // not a rectangle
    }

    // we have a rect, replace last 3 "l" items by one "re" item.
    if (ul.y < lr.y) {
        r = fz_make_rect(ul.x, ul.y, lr.x, lr.y);
        orientation = 1;
    } else {
        r = fz_make_rect(ll.x, ll.y, ur.x, ur.y);
        orientation = -1;
    }
    rect = PyTuple_New(3);
    PyTuple_SET_ITEM(rect, 0, PyUnicode_FromString("re"));
    PyTuple_SET_ITEM(rect, 1, JM_py_from_rect(r));
    PyTuple_SET_ITEM(rect, 2, PyLong_FromLong(orientation));
    PyList_SetItem(items, len - 3, rect); // replace item -3 by rect
    PyList_SetSlice(items, len - 2, len, NULL); // delete remaining 2 items
    return 1;
    drop_out:;
    return 0;
}

static PyObject *
jm_lineart_color(fz_colorspace *colorspace, const float *color)
{
    float rgb[3];
    if (colorspace) {
        mupdf::ll_fz_convert_color(colorspace, color, mupdf::ll_fz_device_rgb(),
                         rgb, NULL, fz_default_color_params);
        return Py_BuildValue("fff", rgb[0], rgb[1], rgb[2]);
    }
    return PyTuple_New(0);
}

static void
trace_moveto(fz_context *ctx, void *dev_, float x, float y)
{
    jm_lineart_device* dev = (jm_lineart_device*) dev_;
    dev->lastpoint = mupdf::ll_fz_transform_point(fz_make_point(x, y), dev->ctm);
    if (mupdf::ll_fz_is_infinite_rect(dev->pathrect))
    {
        dev->pathrect = mupdf::ll_fz_make_rect(
                dev->lastpoint.x,
                dev->lastpoint.y,
                dev->lastpoint.x,
                dev->lastpoint.y
                );
    }
    dev->firstpoint = dev->lastpoint;
    dev->havemove = 1;
    dev->linecount = 0;  // reset # of consec. lines
}

static void
trace_lineto(fz_context *ctx, void *dev_, float x, float y)
{
    jm_lineart_device* dev = (jm_lineart_device*) dev_;
    fz_point p1 = fz_transform_point(fz_make_point(x, y), dev->ctm);
    dev->pathrect = fz_include_point_in_rect(dev->pathrect, p1);
    PyObject *list = PyTuple_New(3);
    PyTuple_SET_ITEM(list, 0, PyUnicode_FromString("l"));
    PyTuple_SET_ITEM(list, 1, JM_py_from_point(dev->lastpoint));
    PyTuple_SET_ITEM(list, 2, JM_py_from_point(p1));
    dev->lastpoint = p1;
    PyObject *items = PyDict_GetItem(dev->pathdict, dictkey_items);
    LIST_APPEND_DROP(items, list);
    dev->linecount += 1;  // counts consecutive lines
    if (dev->linecount == 4 && dev->path_type != FILL_PATH) {  // shrink to "re" or "qu" item
        jm_checkquad(dev);
    }
}

static void
trace_curveto(fz_context *ctx, void *dev_, float x1, float y1, float x2, float y2, float x3, float y3)
{
    jm_lineart_device* dev = (jm_lineart_device*) dev_;
    dev->linecount = 0;  // reset # of consec. lines
    fz_point p1 = fz_make_point(x1, y1);
    fz_point p2 = fz_make_point(x2, y2);
    fz_point p3 = fz_make_point(x3, y3);
    p1 = fz_transform_point(p1, dev->ctm);
    p2 = fz_transform_point(p2, dev->ctm);
    p3 = fz_transform_point(p3, dev->ctm);
    dev->pathrect = fz_include_point_in_rect(dev->pathrect, p1);
    dev->pathrect = fz_include_point_in_rect(dev->pathrect, p2);
    dev->pathrect = fz_include_point_in_rect(dev->pathrect, p3);

    PyObject *list = PyTuple_New(5);
    PyTuple_SET_ITEM(list, 0, PyUnicode_FromString("c"));
    PyTuple_SET_ITEM(list, 1, JM_py_from_point(dev->lastpoint));
    PyTuple_SET_ITEM(list, 2, JM_py_from_point(p1));
    PyTuple_SET_ITEM(list, 3, JM_py_from_point(p2));
    PyTuple_SET_ITEM(list, 4, JM_py_from_point(p3));
    dev->lastpoint = p3;
    PyObject *items = PyDict_GetItem(dev->pathdict, dictkey_items);
    LIST_APPEND_DROP(items, list);
}

static void
trace_close(fz_context *ctx, void *dev_)
{
    jm_lineart_device* dev = (jm_lineart_device*) dev_;
    if (dev->linecount == 3) {
        if (jm_checkrect(dev)) {
            return;
        }
    }
    dev->linecount = 0;  // reset # of consec. lines
	if (dev->havemove) {
		if (dev->firstpoint.x != dev->lastpoint.x || dev->firstpoint.y != dev->lastpoint.y) {
			PyObject *list = PyTuple_New(3);
			PyTuple_SET_ITEM(list, 0, PyUnicode_FromString("l"));
			PyTuple_SET_ITEM(list, 1, JM_py_from_point(dev->lastpoint));
			PyTuple_SET_ITEM(list, 2, JM_py_from_point(dev->firstpoint));
			dev->lastpoint = dev->firstpoint;
			PyObject *items = PyDict_GetItem(dev->pathdict, dictkey_items);
			LIST_APPEND_DROP(items, list);
		}
		dev->havemove = 0;
		DICT_SETITEMSTR_DROP(dev->pathdict, "closePath", JM_BOOL(0));
	} else {
		DICT_SETITEMSTR_DROP(dev->pathdict, "closePath", JM_BOOL(1));
	}
}

static const fz_path_walker trace_path_walker =
    {
        trace_moveto,
        trace_lineto,
        trace_curveto,
        trace_close
    };

/*
---------------------------------------------------------------------
Create the "items" list of the path dictionary
* either create or empty the path dictionary
* reset the end point of the path
* reset count of consecutive lines
* invoke fz_walk_path(), which create the single items
* if no items detected, empty path dict again
---------------------------------------------------------------------
*/
static void
jm_lineart_path(jm_lineart_device *dev, const fz_path *path)
{
    dev->pathrect = fz_infinite_rect;
    dev->linecount = 0;
    dev->lastpoint = fz_make_point(0, 0);
    dev->firstpoint = fz_make_point(0, 0);
    if (dev->pathdict) {
        Py_CLEAR(dev->pathdict);
    }
    dev->pathdict = PyDict_New();
    DICT_SETITEM_DROP(dev->pathdict, dictkey_items, PyList_New(0));
    mupdf::ll_fz_walk_path(path, &trace_path_walker, dev);
    // Check if any items were added ...
    if (!PyDict_GetItem(dev->pathdict, dictkey_items) || !PyList_Size(PyDict_GetItem(dev->pathdict, dictkey_items)))
    {
        Py_CLEAR(dev->pathdict);
    }
}

//---------------------------------------------------------------------------
// Append current path to list or merge into last path of the list.
// (1) Append if first path, different item lists or not a 'stroke' version
//     of previous path
// (2) If new path has the same items, merge its content into previous path
//     and change path["type"] to "fs".
// (3) If "out" is callable, skip the previous and pass dictionary to it.
//---------------------------------------------------------------------------
static void
// todo: remove `method` arg - it is dev->method.
jm_append_merge(jm_lineart_device *dev)
{
    Py_ssize_t len;
    int rc;
    PyObject *prev;
    PyObject *previtems;
    PyObject *thisitems;
    const char *thistype;
    const char *prevtype;
    if (PyCallable_Check(dev->out) || dev->method != Py_None) {  // function or method
        goto callback;
    }
    len = PyList_Size(dev->out);  // len of output list so far
    if (len == 0) {  // always append first path 
        goto append;
    }
    thistype = PyUnicode_AsUTF8(PyDict_GetItem(dev->pathdict, dictkey_type));
    if (strcmp(thistype, "s") != 0) {  // if not stroke, then append
        goto append;
    }
    prev = PyList_GET_ITEM(dev->out, len - 1);  // get prev path
    prevtype = PyUnicode_AsUTF8(PyDict_GetItem(prev, dictkey_type));
    if (strcmp(prevtype, "f") != 0) {  // if previous not fill, append
        goto append;
    }
    // last check: there must be the same list of items for "f" and "s".
    previtems = PyDict_GetItem(prev, dictkey_items);
    thisitems = PyDict_GetItem(dev->pathdict, dictkey_items);
    if (PyObject_RichCompareBool(previtems, thisitems, Py_NE)) {
        goto append;
    }
    rc = PyDict_Merge(prev, dev->pathdict, 0);  // merge, do not override
    if (rc == 0) {
        DICT_SETITEM_DROP(prev, dictkey_type, PyUnicode_FromString("fs"));
        goto postappend;
    } else {
        messagef("could not merge stroke and fill path");
        goto append;
    }
    append:;
    //printf("Appending to dev->out. len(dev->out)=%zi\n", PyList_Size(dev->out));
    PyList_Append(dev->out, dev->pathdict);
    postappend:;
    Py_CLEAR(dev->pathdict);
    return;

    callback:;  // callback function or method
    PyObject *resp = NULL;
    if (dev->method == Py_None) {
        resp = PyObject_CallFunctionObjArgs(dev->out, dev->pathdict, NULL);
    } else {
        resp = PyObject_CallMethodObjArgs(dev->out, dev->method, dev->pathdict, NULL);
    }
    if (resp) {
        Py_DECREF(resp);
    } else {
        messagef("calling cdrawings callback function/method failed!");
        PyErr_Clear();
    }
    Py_CLEAR(dev->pathdict);
    return;
}

static void
jm_lineart_fill_path(fz_context *ctx, fz_device *dev_, const fz_path *path,
                int even_odd, fz_matrix ctm, fz_colorspace *colorspace,
                const float *color, float alpha, fz_color_params color_params)
{
    jm_lineart_device *dev = (jm_lineart_device *) dev_;
    //printf("extra.jm_lineart_fill_path(): dev->seqno=%zi\n", dev->seqno);
    dev->ctm = ctm; //fz_concat(ctm, trace_device_ptm);
    dev->path_type = FILL_PATH;
    jm_lineart_path(dev, path);
    if (!dev->pathdict) {
        return;
    }
    DICT_SETITEM_DROP(dev->pathdict, dictkey_type, PyUnicode_FromString("f"));
    DICT_SETITEMSTR_DROP(dev->pathdict, "even_odd", JM_BOOL(even_odd));
    DICT_SETITEMSTR_DROP(dev->pathdict, "fill_opacity", Py_BuildValue("f", alpha));
    DICT_SETITEMSTR_DROP(dev->pathdict, "fill", jm_lineart_color(colorspace, color));
    DICT_SETITEM_DROP(dev->pathdict, dictkey_rect, JM_py_from_rect(dev->pathrect));
    DICT_SETITEMSTR_DROP(dev->pathdict, "seqno", PyLong_FromSize_t(dev->seqno));
    DICT_SETITEMSTR_DROP(dev->pathdict, "layer", JM_UnicodeFromStr(dev->layer_name));
    if (dev->clips)    {
        DICT_SETITEMSTR_DROP(dev->pathdict, "level", PyLong_FromLong(dev->depth));
    }
    jm_append_merge(dev);
    dev->seqno += 1;
}

static void
jm_lineart_stroke_path(fz_context *ctx, fz_device *dev_, const fz_path *path,
                const fz_stroke_state *stroke, fz_matrix ctm,
                fz_colorspace *colorspace, const float *color, float alpha,
                fz_color_params color_params)
{
    jm_lineart_device *dev = (jm_lineart_device *)dev_;
    //printf("extra.jm_lineart_stroke_path(): dev->seqno=%zi\n", dev->seqno);
    int i;
    dev->pathfactor = 1;
    if (ctm.a != 0 && fz_abs(ctm.a) == fz_abs(ctm.d)) {
        dev->pathfactor = fz_abs(ctm.a);
    } else {
        if (ctm.b != 0 && fz_abs(ctm.b) == fz_abs(ctm.c)) {
            dev->pathfactor = fz_abs(ctm.b);
        }
    }
    dev->ctm = ctm; // fz_concat(ctm, trace_device_ptm);
    dev->path_type = STROKE_PATH;

    jm_lineart_path(dev, path);
    if (!dev->pathdict) {
        return;
    }
    DICT_SETITEM_DROP(dev->pathdict, dictkey_type, PyUnicode_FromString("s"));
    DICT_SETITEMSTR_DROP(dev->pathdict, "stroke_opacity", Py_BuildValue("f", alpha));
    DICT_SETITEMSTR_DROP(dev->pathdict, "color", jm_lineart_color(colorspace, color));
    DICT_SETITEM_DROP(dev->pathdict, dictkey_width, Py_BuildValue("f", dev->pathfactor * stroke->linewidth));
    DICT_SETITEMSTR_DROP(dev->pathdict, "lineCap", Py_BuildValue("iii", stroke->start_cap, stroke->dash_cap, stroke->end_cap));
    DICT_SETITEMSTR_DROP(dev->pathdict, "lineJoin", Py_BuildValue("f", dev->pathfactor * stroke->linejoin));
    if (!PyDict_GetItemString(dev->pathdict, "closePath")) {
        DICT_SETITEMSTR_DROP(dev->pathdict, "closePath", JM_BOOL(0));
    }

    // output the "dashes" string
    if (stroke->dash_len) {
        mupdf::FzBuffer buff(256);
        mupdf::fz_append_string(buff, "[ ");  // left bracket
        for (i = 0; i < stroke->dash_len; i++) {
            fz_append_printf(ctx, buff.m_internal, "%g ", dev->pathfactor * stroke->dash_list[i]);
        }
        fz_append_printf(ctx, buff.m_internal, "] %g", dev->pathfactor * stroke->dash_phase);
        DICT_SETITEMSTR_DROP(dev->pathdict, "dashes", JM_EscapeStrFromBuffer(buff));
    } else {
        DICT_SETITEMSTR_DROP(dev->pathdict, "dashes", PyUnicode_FromString("[] 0"));
    }

    DICT_SETITEM_DROP(dev->pathdict, dictkey_rect, JM_py_from_rect(dev->pathrect));
    DICT_SETITEMSTR_DROP(dev->pathdict, "layer", JM_UnicodeFromStr(dev->layer_name));
    DICT_SETITEMSTR_DROP(dev->pathdict, "seqno", PyLong_FromSize_t(dev->seqno));
    if (dev->clips) {
        DICT_SETITEMSTR_DROP(dev->pathdict, "level", PyLong_FromLong(dev->depth));
    }
    // output the dict - potentially merging it with a previous fill_path twin
    jm_append_merge(dev);
    dev->seqno += 1;
}

static void
jm_lineart_clip_path(fz_context *ctx, fz_device *dev_, const fz_path *path, int even_odd, fz_matrix ctm, fz_rect scissor)
{
    jm_lineart_device *dev = (jm_lineart_device *)dev_;
    if (!dev->clips) return;
    dev->ctm = ctm; //fz_concat(ctm, trace_device_ptm);
    dev->path_type = CLIP_PATH;
    jm_lineart_path(dev, path);
	if (!dev->pathdict) {
		return;
	}
    DICT_SETITEM_DROP(dev->pathdict, dictkey_type, PyUnicode_FromString("clip"));
    DICT_SETITEMSTR_DROP(dev->pathdict, "even_odd", JM_BOOL(even_odd));
    if (!PyDict_GetItemString(dev->pathdict, "closePath")) {
        DICT_SETITEMSTR_DROP(dev->pathdict, "closePath", JM_BOOL(0));
    }
    DICT_SETITEMSTR_DROP(dev->pathdict, "scissor", JM_py_from_rect(compute_scissor(dev)));
    DICT_SETITEMSTR_DROP(dev->pathdict, "level", PyLong_FromLong(dev->depth));
    DICT_SETITEMSTR_DROP(dev->pathdict, "layer", JM_UnicodeFromStr(dev->layer_name));
    jm_append_merge(dev);
    dev->depth++;
}

static void
jm_lineart_clip_stroke_path(fz_context *ctx, fz_device *dev_, const fz_path *path, const fz_stroke_state *stroke, fz_matrix ctm, fz_rect scissor)
{
    jm_lineart_device *dev = (jm_lineart_device *)dev_;
    if (!dev->clips) return;
    dev->ctm = ctm; //fz_concat(ctm, trace_device_ptm);
    dev->path_type = CLIP_STROKE_PATH;
    jm_lineart_path(dev, path);
	if (!dev->pathdict) {
		return;
	}
    DICT_SETITEM_DROP(dev->pathdict, dictkey_type, PyUnicode_FromString("clip"));
    DICT_SETITEMSTR_DROP(dev->pathdict, "even_odd", Py_BuildValue("s", NULL));
    if (!PyDict_GetItemString(dev->pathdict, "closePath")) {
        DICT_SETITEMSTR_DROP(dev->pathdict, "closePath", JM_BOOL(0));
    }
    DICT_SETITEMSTR_DROP(dev->pathdict, "scissor", JM_py_from_rect(compute_scissor(dev)));
    DICT_SETITEMSTR_DROP(dev->pathdict, "level", PyLong_FromLong(dev->depth));
    DICT_SETITEMSTR_DROP(dev->pathdict, "layer", JM_UnicodeFromStr(dev->layer_name));
    jm_append_merge(dev);
    dev->depth++;
}


static void
jm_lineart_clip_stroke_text(fz_context *ctx, fz_device *dev_, const fz_text *text, const fz_stroke_state *stroke, fz_matrix ctm, fz_rect scissor)
{
   jm_lineart_device *dev = (jm_lineart_device *)dev_;
   if (!dev->clips) return;
   compute_scissor(dev);
   dev->depth++;
}

static void
jm_lineart_clip_text(fz_context *ctx, fz_device *dev_, const fz_text *text, fz_matrix ctm, fz_rect scissor)
{
   jm_lineart_device *dev = (jm_lineart_device *)dev_;
   if (!dev->clips) return;
   compute_scissor(dev);
   dev->depth++;
}

static void
jm_lineart_clip_image_mask(fz_context *ctx, fz_device *dev_, fz_image *image, fz_matrix ctm, fz_rect scissor)
{
   jm_lineart_device *dev = (jm_lineart_device *)dev_;
   if (!dev->clips) return;
   compute_scissor(dev);
   dev->depth++;
}
 
static void
jm_lineart_pop_clip(fz_context *ctx, fz_device *dev_)
{
    jm_lineart_device *dev = (jm_lineart_device *)dev_;
    if (!dev->clips) return;
    if (!dev->scissors) return;
    Py_ssize_t len = PyList_Size(dev->scissors);
    if (len < 1) return;
    PyList_SetSlice(dev->scissors, len - 1, len, NULL);
    dev->depth--;
}


static void
jm_lineart_begin_group(fz_context *ctx, fz_device *dev_, fz_rect bbox, fz_colorspace *cs, int isolated, int knockout, int blendmode, float alpha)
{
    jm_lineart_device *dev = (jm_lineart_device *)dev_;
    if (!dev->clips) return;
    dev->pathdict = Py_BuildValue("{s:s,s:N,s:N,s:N,s:s,s:f,s:i,s:N}",
                        "type", "group",
                        "rect", JM_py_from_rect(bbox),
                        "isolated", JM_BOOL(isolated),
                        "knockout", JM_BOOL(knockout),
                        "blendmode", fz_blendmode_name(blendmode),
                        "opacity", alpha,
                        "level", dev->depth,
                        "layer", JM_UnicodeFromStr(dev->layer_name)
                    );
    jm_append_merge(dev);
    dev->depth++;
}

static void
jm_lineart_end_group(fz_context *ctx, fz_device *dev_)
{
    jm_lineart_device *dev = (jm_lineart_device *)dev_;
    if (!dev->clips) return;
    dev->depth--;
}

static void jm_lineart_fill_text(fz_context *ctx, fz_device *dev, const fz_text *, fz_matrix, fz_colorspace *, const float *color, float alpha, fz_color_params)
{
    jm_increase_seqno(ctx, dev);
}

static void jm_lineart_stroke_text(fz_context *ctx, fz_device *dev, const fz_text *, const fz_stroke_state *, fz_matrix, fz_colorspace *, const float *color, float alpha, fz_color_params)
{
    jm_increase_seqno(ctx, dev);
}

static void jm_lineart_fill_shade(fz_context *ctx, fz_device *dev, fz_shade *shd, fz_matrix ctm, float alpha, fz_color_params color_params)
{
    jm_increase_seqno(ctx, dev);
}

static void jm_lineart_fill_image(fz_context *ctx, fz_device *dev, fz_image *img, fz_matrix ctm, float alpha, fz_color_params color_params)
{
    jm_increase_seqno(ctx, dev);
}

static void jm_lineart_fill_image_mask(fz_context *ctx, fz_device *dev, fz_image *img, fz_matrix ctm, fz_colorspace *, const float *color, float alpha, fz_color_params color_params)
{
    jm_increase_seqno(ctx, dev);
}

static void jm_lineart_ignore_text(fz_context *ctx, fz_device *dev, const fz_text *, fz_matrix)
{
    jm_increase_seqno(ctx, dev);
}


//-------------------------------------------------------------------
// LINEART device for Python method Page.get_cdrawings()
//-------------------------------------------------------------------
mupdf::FzDevice JM_new_lineart_device(PyObject *out, int clips, PyObject *method)
{
    //printf("extra.JM_new_lineart_device()\n");
    jm_lineart_device* dev = (jm_lineart_device*) mupdf::ll_fz_new_device_of_size(sizeof(jm_lineart_device));

    dev->super.close_device = NULL;
    dev->super.drop_device = jm_lineart_drop_device;
    dev->super.fill_path = jm_lineart_fill_path;
    dev->super.stroke_path = jm_lineart_stroke_path;
    dev->super.clip_path = jm_lineart_clip_path;
    dev->super.clip_stroke_path = jm_lineart_clip_stroke_path;

    dev->super.fill_text = jm_lineart_fill_text;
    dev->super.stroke_text = jm_lineart_stroke_text;
    dev->super.clip_text = jm_lineart_clip_text;
    dev->super.clip_stroke_text = jm_lineart_clip_stroke_text;
    dev->super.ignore_text = jm_lineart_ignore_text;

    dev->super.fill_shade = jm_lineart_fill_shade;
    dev->super.fill_image = jm_lineart_fill_image;
    dev->super.fill_image_mask = jm_lineart_fill_image_mask;
    dev->super.clip_image_mask = jm_lineart_clip_image_mask;

    dev->super.pop_clip = jm_lineart_pop_clip;

    dev->super.begin_mask = NULL;
    dev->super.end_mask = NULL;
    dev->super.begin_group = jm_lineart_begin_group;
    dev->super.end_group = jm_lineart_end_group;

    dev->super.begin_tile = NULL;
    dev->super.end_tile = NULL;

    dev->super.begin_layer = jm_lineart_begin_layer;
    dev->super.end_layer = jm_lineart_end_layer;

    dev->super.begin_structure = NULL;
    dev->super.end_structure = NULL;

    dev->super.begin_metatext = NULL;
    dev->super.end_metatext = NULL;

    dev->super.render_flags = NULL;
    dev->super.set_default_colorspaces = NULL;

    if (PyList_Check(out)) {
        Py_INCREF(out);
    }
    Py_INCREF(method);
    dev->out = out;
    dev->seqno = 0;
    dev->depth = 0;
    dev->clips = clips;
    dev->method = method;
    dev->pathdict = nullptr;

    return mupdf::FzDevice(&dev->super);
}

PyObject* get_cdrawings(mupdf::FzPage& page, PyObject *extended=NULL, PyObject *callback=NULL, PyObject *method=NULL)
{
    //fz_page *page = (fz_page *) $self;
    //fz_device *dev = NULL;
    PyObject *rc = NULL;
    int clips = PyObject_IsTrue(extended);

    mupdf::FzDevice dev;
    if (PyCallable_Check(callback) || method != Py_None) {
        dev = JM_new_lineart_device(callback, clips, method);
    } else {
        rc = PyList_New(0);
        dev = JM_new_lineart_device(rc, clips, method);
    }
    mupdf::FzRect prect = mupdf::fz_bound_page(page);
    ((jm_lineart_device*) dev.m_internal)->ptm = mupdf::ll_fz_make_matrix(1, 0, 0, -1, 0, prect.y1);
    
    mupdf::FzCookie cookie;
    mupdf::FzMatrix identity;
    mupdf::fz_run_page( page, dev, *identity.internal(), cookie);
    mupdf::fz_close_device( dev);
    if (PyCallable_Check(callback) || method != Py_None)
    {
        Py_RETURN_NONE;
    }
    return rc;
}


static int detect_super_script(fz_stext_line *line, fz_stext_char *ch)
{
    if (line->wmode == 0 && line->dir.x == 1 && line->dir.y == 0)
    {
        return ch->origin.y < line->first_char->origin.y - ch->size * 0.1f;
    }
    return 0;
}

static int JM_char_font_flags(fz_font *font, fz_stext_line *line, fz_stext_char *ch)
{
    int flags = detect_super_script(line, ch);
    flags += mupdf::ll_fz_font_is_italic(font) * TEXT_FONT_ITALIC;
    flags += mupdf::ll_fz_font_is_serif(font) * TEXT_FONT_SERIFED;
    flags += mupdf::ll_fz_font_is_monospaced(font) * TEXT_FONT_MONOSPACED;
    flags += mupdf::ll_fz_font_is_bold(font) * TEXT_FONT_BOLD;
    return flags;
}

//---------------------------------------------------------------------------
// APPEND non-ascii runes in unicode escape format to fz_buffer
//---------------------------------------------------------------------------
void JM_append_rune(fz_buffer *buff, int ch)
{
    char text[32];
    if (ch == 92)  // prevent accidental "\u", "\U" sequences
    {
        mupdf::ll_fz_append_string(buff, "\\u005c");
    }
    else if ((ch >= 32 && ch <= 127) || ch == 10)
    {
        mupdf::ll_fz_append_byte(buff, ch);
    }
    else if (ch >= 0xd800 && ch <= 0xdfff)  // orphaned surrogate Unicodes
    {
        mupdf::ll_fz_append_string(buff, "\\ufffd");
    }
    else if (ch <= 0xffff)
    {
        // 4 hex digits
        snprintf(text, sizeof(text), "\\u%04x", ch);
        mupdf::ll_fz_append_string(buff, text);
    }
    else
    {
        // 8 hex digits
        snprintf(text, sizeof(text), "\\U%08x", ch);
        mupdf::ll_fz_append_string(buff, text);
    }
}


mupdf::FzRect JM_make_spanlist(
        PyObject *line_dict,
        mupdf::FzStextLine& line,
        int raw,
        mupdf::FzBuffer& buff,
        mupdf::FzRect& tp_rect
        )
{
    PyObject *span = NULL, *char_list = NULL, *char_dict;
    PyObject *span_list = PyList_New(0);
    mupdf::fz_clear_buffer(buff);
    fz_rect span_rect = fz_empty_rect;
    fz_rect line_rect = fz_empty_rect;
    fz_point span_origin = {0, 0};
    struct char_style
    {
        float size = -1;
        int flags = -1;
        const char *font = "";
        int color = -1;
        float asc = 0;
        float desc = 0;
    };
    char_style old_style;
    char_style style;

    for (mupdf::FzStextChar ch: line)
    {
        fz_rect r = JM_char_bbox(line, ch);
        if (!JM_rects_overlap(*tp_rect.internal(), r) && !fz_is_infinite_rect(tp_rect))
        {
            continue;
        }
        int flags = JM_char_font_flags( ch.m_internal->font, line.m_internal, ch.m_internal);
        fz_point origin = ch.m_internal->origin;
        style.size = ch.m_internal->size;
        style.flags = flags;
        style.font = JM_font_name(ch.m_internal->font);
        style.color = ch.m_internal->color;
        style.asc = JM_font_ascender(ch.m_internal->font);
        style.desc = JM_font_descender(ch.m_internal->font);

        if (0
                || style.size != old_style.size
                || style.flags != old_style.flags
                || style.color != old_style.color
                || strcmp(style.font, old_style.font) != 0
                )
        {
            if (old_style.size >= 0)
            {
                // not first one, output previous
                if (raw)
                {
                    // put character list in the span
                    DICT_SETITEM_DROP(span, dictkey_chars, char_list);
                    char_list = NULL;
                }
                else
                {
                    // put text string in the span
                    DICT_SETITEM_DROP(span, dictkey_text, JM_EscapeStrFromBuffer(buff));
                    mupdf::fz_clear_buffer(buff);
                }

                DICT_SETITEM_DROP(span, dictkey_origin, JM_py_from_point(span_origin));
                DICT_SETITEM_DROP(span, dictkey_bbox, JM_py_from_rect(span_rect));
                line_rect = mupdf::ll_fz_union_rect(line_rect, span_rect);
                LIST_APPEND_DROP(span_list, span);
                span = NULL;
            }

            span = PyDict_New();
            float asc = style.asc, desc = style.desc;
            if (style.asc < 1e-3)
            {
                asc = 0.9f;
                desc = -0.1f;
            }

            DICT_SETITEM_DROP(span, dictkey_size, Py_BuildValue("f", style.size));
            DICT_SETITEM_DROP(span, dictkey_flags, Py_BuildValue("i", style.flags));
            DICT_SETITEM_DROP(span, dictkey_font, JM_EscapeStrFromStr(style.font));
            DICT_SETITEM_DROP(span, dictkey_color, Py_BuildValue("i", style.color));
            DICT_SETITEMSTR_DROP(span, "ascender", Py_BuildValue("f", asc));
            DICT_SETITEMSTR_DROP(span, "descender", Py_BuildValue("f", desc));

            old_style = style;
            span_rect = r;
            span_origin = origin;

        }
        span_rect = mupdf::ll_fz_union_rect(span_rect, r);

        if (raw)
        {
            // make and append a char dict
            char_dict = PyDict_New();
            DICT_SETITEM_DROP(char_dict, dictkey_origin, JM_py_from_point(ch.m_internal->origin));

            DICT_SETITEM_DROP(char_dict, dictkey_bbox, JM_py_from_rect(r));

            DICT_SETITEM_DROP(char_dict, dictkey_c, Py_BuildValue("C", ch.m_internal->c));

            if (!char_list)
            {
                char_list = PyList_New(0);
            }
            LIST_APPEND_DROP(char_list, char_dict);
        }
        else
        {
            // add character byte to buffer
            JM_append_rune(buff.m_internal, ch.m_internal->c);
        }
    }
    // all characters processed, now flush remaining span
    if (span)
    {
        if (raw)
        {
            DICT_SETITEM_DROP(span, dictkey_chars, char_list);
            char_list = NULL;
        }
        else
        {
            DICT_SETITEM_DROP(span, dictkey_text, JM_EscapeStrFromBuffer(buff));
            mupdf::fz_clear_buffer(buff);
        }
        DICT_SETITEM_DROP(span, dictkey_origin, JM_py_from_point(span_origin));
        DICT_SETITEM_DROP(span, dictkey_bbox, JM_py_from_rect(span_rect));

        if (!fz_is_empty_rect(span_rect))
        {
            LIST_APPEND_DROP(span_list, span);
            line_rect = fz_union_rect(line_rect, span_rect);
        }
        else
        {
            Py_DECREF(span);
        }
        span = NULL;
    }
    if (!mupdf::fz_is_empty_rect(line_rect))
    {
        DICT_SETITEM_DROP(line_dict, dictkey_spans, span_list);
    }
    else
    {
        DICT_SETITEM_DROP(line_dict, dictkey_spans, span_list);
    }
    return line_rect;
}

//-----------------------------------------------------------------------------
// Functions for wordlist output
//-----------------------------------------------------------------------------
int JM_append_word(
        PyObject* lines,
        fz_buffer* buff,
        fz_rect* wbbox,
        int block_n,
        int line_n,
        int word_n
        )
{
    PyObject* s = JM_EscapeStrFromBuffer(buff);
    PyObject* litem = Py_BuildValue(
            "ffffOiii",
            wbbox->x0,
            wbbox->y0,
            wbbox->x1,
            wbbox->y1,
            s,
            block_n,
            line_n,
            word_n
            );
    LIST_APPEND_DROP(lines, litem);
    Py_DECREF(s);
    *wbbox = fz_empty_rect;
    return word_n + 1;  // word counter
}

PyObject* extractWORDS(mupdf::FzStextPage& this_tpage, PyObject *delimiters)
{
    int block_n = -1;
    fz_rect wbbox = fz_empty_rect;  // word bbox
    fz_rect tp_rect = this_tpage.m_internal->mediabox;

    PyObject *lines = NULL;
    mupdf::FzBuffer buff = mupdf::fz_new_buffer(64);
    lines = PyList_New(0);
    for (mupdf::FzStextBlock block: this_tpage)
    {
        block_n++;
        if (block.m_internal->type != FZ_STEXT_BLOCK_TEXT)
        {
            continue;
        }
        int line_n = -1;
        for (mupdf::FzStextLine line: block)
        {
            line_n++;
            int word_n = 0;                 // word counter per line
            mupdf::fz_clear_buffer(buff);   // reset word buffer
            size_t buflen = 0;              // reset char counter
            for (mupdf::FzStextChar ch: line)
            {
                mupdf::FzRect cbbox = JM_char_bbox(line, ch);
                if (!JM_rects_overlap(tp_rect, *cbbox.internal()) && !fz_is_infinite_rect(tp_rect))
                {
                    continue;
                }

                int word_delimiter = JM_is_word_delimiter(ch.m_internal->c, delimiters);
                if (word_delimiter)
                {
                    if (buflen == 0)
                    {
                        continue;  // skip delimiters at line start
                    }
                    if (!fz_is_empty_rect(wbbox))
                    {
                        word_n = JM_append_word(
                                lines,
                                buff.m_internal,
                                &wbbox,
                                block_n,
                                line_n,
                                word_n
                                );
                    }
                    mupdf::fz_clear_buffer(buff);
                    buflen = 0;  // reset char counter
                    continue;
                }
                // append one unicode character to the word
                JM_append_rune(buff.m_internal, ch.m_internal->c);
                buflen++;
                // enlarge word bbox
                wbbox = fz_union_rect(wbbox, JM_char_bbox(line, ch));
            }
            if (buflen && !fz_is_empty_rect(wbbox))
            {
                word_n = JM_append_word(
                        lines,
                        buff.m_internal,
                        &wbbox,
                        block_n,
                        line_n,
                        word_n
                        );
            }
            mupdf::fz_clear_buffer(buff);
            buflen = 0;
        }
    }
    return lines;
}



struct ScopedPyObject
/* PyObject* wrapper, destructor calls Py_CLEAR() unless `release()` has been
called. */
{
    ScopedPyObject(PyObject* rhs=nullptr)
    :
    m_pyobject(rhs)
    {}
    
    PyObject*& get()
    {
        return m_pyobject;
    }
    
    ScopedPyObject& operator= (PyObject* rhs)
    {
        Py_CLEAR(m_pyobject);
        m_pyobject = rhs;
        return *this;
    }
    
    PyObject* release()
    {
        PyObject* ret = m_pyobject;
        m_pyobject = nullptr;
        return ret;
    }
    ~ScopedPyObject()
    {
        Py_CLEAR(m_pyobject);
    }
    
    PyObject*   m_pyobject = nullptr;
};


PyObject* extractBLOCKS(mupdf::FzStextPage& self)
{
    fz_stext_page *this_tpage = self.m_internal;
    fz_rect tp_rect = this_tpage->mediabox;
    mupdf::FzBuffer res(1024);
    ScopedPyObject lines( PyList_New(0));
    int block_n = -1;
    for (fz_stext_block* block = this_tpage->first_block; block; block = block->next)
    {
        ScopedPyObject text;
        block_n++;
        fz_rect blockrect = fz_empty_rect;
        if (block->type == FZ_STEXT_BLOCK_TEXT)
        {
            mupdf::fz_clear_buffer(res);  // set text buffer to empty
            int line_n = -1;
            int last_char = 0;
            (void) line_n;  /* Not actually used, but keeping in the code for now. */
            for (fz_stext_line* line = block->u.t.first_line; line; line = line->next)
            {
                line_n++;
                fz_rect linerect = fz_empty_rect;
                for (fz_stext_char* ch = line->first_char; ch; ch = ch->next)
                {
                    fz_rect cbbox = JM_char_bbox(line, ch);
                    if (!JM_rects_overlap(tp_rect, cbbox) && !fz_is_infinite_rect(tp_rect))
                    {
                        continue;
                    }
                    JM_append_rune(res.m_internal, ch->c);
                    last_char = ch->c;
                    linerect = fz_union_rect(linerect, cbbox);
                }
                if (last_char != 10 && !fz_is_empty_rect(linerect))
                {
                    mupdf::fz_append_byte(res, 10);
                }
                blockrect = fz_union_rect(blockrect, linerect);
            }
            text = JM_EscapeStrFromBuffer(res);
        }
        else if (JM_rects_overlap(tp_rect, block->bbox) || fz_is_infinite_rect(tp_rect))
        {
            fz_image *img = block->u.i.image;
            fz_colorspace *cs = img->colorspace;
            text = PyUnicode_FromFormat(
                    "<image: %s, width: %d, height: %d, bpc: %d>",
                    mupdf::ll_fz_colorspace_name(cs),
                    img->w,
                    img->h,
                    img->bpc
                    );
            blockrect = fz_union_rect(blockrect, block->bbox);
        }
        if (!fz_is_empty_rect(blockrect))
        {
            ScopedPyObject litem = PyTuple_New(7);
            PyTuple_SET_ITEM(litem.get(), 0, Py_BuildValue("f", blockrect.x0));
            PyTuple_SET_ITEM(litem.get(), 1, Py_BuildValue("f", blockrect.y0));
            PyTuple_SET_ITEM(litem.get(), 2, Py_BuildValue("f", blockrect.x1));
            PyTuple_SET_ITEM(litem.get(), 3, Py_BuildValue("f", blockrect.y1));
            PyTuple_SET_ITEM(litem.get(), 4, Py_BuildValue("O", text.get()));
            PyTuple_SET_ITEM(litem.get(), 5, Py_BuildValue("i", block_n));
            PyTuple_SET_ITEM(litem.get(), 6, Py_BuildValue("i", block->type));
            LIST_APPEND(lines.get(), litem.get());
        }
    }
    return lines.release();
}

#define EMPTY_STRING PyUnicode_FromString("")

static PyObject *JM_UnicodeFromStr(const char *c)
{
    if (!c) return EMPTY_STRING;
    PyObject *val = Py_BuildValue("s", c);
    if (!val) {
        val = EMPTY_STRING;
        PyErr_Clear();
    }
    return val;
}

PyObject* link_uri(mupdf::FzLink& link)
{
    return JM_UnicodeFromStr( link.m_internal->uri);
}

fz_stext_page* page_get_textpage(
        mupdf::FzPage& self,
        PyObject* clip,
        int flags,
        PyObject* matrix
        )
{
    fz_context* ctx = mupdf::internal_context_get();
    fz_stext_page *tpage=NULL;
    fz_page *page = self.m_internal;
    fz_device *dev = NULL;
    fz_stext_options options;
    memset(&options, 0, sizeof options);
    options.flags = flags;
    fz_try(ctx) {
        // Default to page's rect if `clip` not specified, for #2048.
        fz_rect rect = (clip==Py_None) ? fz_bound_page(ctx, page) : JM_rect_from_py(clip);
        fz_matrix ctm = JM_matrix_from_py(matrix);
        tpage = fz_new_stext_page(ctx, rect);
        dev = fz_new_stext_device(ctx, tpage, &options);
        fz_run_page(ctx, page, dev, ctm, NULL);
        fz_close_device(ctx, dev);
    }
    fz_always(ctx) {
        fz_drop_device(ctx, dev);
    }
    fz_catch(ctx) {
        mupdf::internal_throw_exception(ctx);
    }
    return tpage;
}

// return extension for pymupdf image type
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

void JM_make_image_block(fz_stext_block *block, PyObject *block_dict)
{
    fz_context* ctx = mupdf::internal_context_get();
    fz_image *image = block->u.i.image;
    fz_buffer *buf = NULL, *freebuf = NULL;
    fz_compressed_buffer *buffer = fz_compressed_image_buffer(ctx, image);
    fz_var(buf);
    fz_var(freebuf);
    int n = fz_colorspace_n(ctx, image->colorspace);
    int w = image->w;
    int h = image->h;
    const char *ext = NULL;
    int type = FZ_IMAGE_UNKNOWN;
    if (buffer)
        type = buffer->params.type;
    if (type < FZ_IMAGE_BMP || type == FZ_IMAGE_JBIG2)
        type = FZ_IMAGE_UNKNOWN;
    PyObject *bytes = NULL;
    fz_var(bytes);
    fz_try(ctx) {
        if (buffer && type != FZ_IMAGE_UNKNOWN) {
            buf = buffer->buffer;
            ext = JM_image_extension(type);
        } else {
            buf = freebuf = fz_new_buffer_from_image_as_png(ctx, image, fz_default_color_params);
            ext = "png";
        }
        bytes = JM_BinFromBuffer(buf);
    }
    fz_always(ctx) {
        if (!bytes)
            bytes = PyBytes_FromString("");
        DICT_SETITEM_DROP(block_dict, dictkey_width,
                        Py_BuildValue("i", w));
        DICT_SETITEM_DROP(block_dict, dictkey_height,
                        Py_BuildValue("i", h));
        DICT_SETITEM_DROP(block_dict, dictkey_ext,
                        Py_BuildValue("s", ext));
        DICT_SETITEM_DROP(block_dict, dictkey_colorspace,
                        Py_BuildValue("i", n));
        DICT_SETITEM_DROP(block_dict, dictkey_xres,
                        Py_BuildValue("i", image->xres));
        DICT_SETITEM_DROP(block_dict, dictkey_yres,
                        Py_BuildValue("i", image->xres));
        DICT_SETITEM_DROP(block_dict, dictkey_bpc,
                        Py_BuildValue("i", (int) image->bpc));
        DICT_SETITEM_DROP(block_dict, dictkey_matrix,
                        JM_py_from_matrix(block->u.i.transform));
        DICT_SETITEM_DROP(block_dict, dictkey_size,
                        Py_BuildValue("n", PyBytes_Size(bytes)));
        DICT_SETITEM_DROP(block_dict, dictkey_image, bytes);

        fz_drop_buffer(ctx, freebuf);
    }
    fz_catch(ctx) {;}
    return;
}

static void JM_make_text_block(fz_stext_block *block, PyObject *block_dict, int raw, fz_buffer *buff, fz_rect tp_rect)
{
    fz_stext_line *line;
    PyObject *line_list = PyList_New(0), *line_dict;
    fz_rect block_rect = fz_empty_rect;
    for (line = block->u.t.first_line; line; line = line->next) {
        if (fz_is_empty_rect(fz_intersect_rect(tp_rect, line->bbox)) &&
            !fz_is_infinite_rect(tp_rect)) {
            continue;
        }
        line_dict = PyDict_New();
        mupdf::FzStextLine line2(line);
        mupdf::FzBuffer buff2( mupdf::ll_fz_keep_buffer( buff));
        mupdf::FzRect tp_rect2( tp_rect);
        mupdf::FzRect line_rect2 = JM_make_spanlist(
                line_dict,
                line2,
                raw,
                buff2,
                tp_rect2
                );
        fz_rect& line_rect = *line_rect2.internal();
        block_rect = fz_union_rect(block_rect, line_rect);
        DICT_SETITEM_DROP(line_dict, dictkey_wmode,
                    Py_BuildValue("i", line->wmode));
        DICT_SETITEM_DROP(line_dict, dictkey_dir, JM_py_from_point(line->dir));
        DICT_SETITEM_DROP(line_dict, dictkey_bbox,
                    JM_py_from_rect(line_rect));
        LIST_APPEND_DROP(line_list, line_dict);
    }
    DICT_SETITEM_DROP(block_dict, dictkey_bbox, JM_py_from_rect(block_rect));
    DICT_SETITEM_DROP(block_dict, dictkey_lines, line_list);
    return;
}

void JM_make_textpage_dict(fz_stext_page *tp, PyObject *page_dict, int raw)
{
    fz_context* ctx = mupdf::internal_context_get();
    fz_stext_block *block;
    fz_buffer *text_buffer = fz_new_buffer(ctx, 128);
    PyObject *block_dict, *block_list = PyList_New(0);
    fz_rect tp_rect = tp->mediabox;
    int block_n = -1;
    for (block = tp->first_block; block; block = block->next) {
        block_n++;
        if (!fz_contains_rect(tp_rect, block->bbox) &&
            !fz_is_infinite_rect(tp_rect) &&
            block->type == FZ_STEXT_BLOCK_IMAGE) {
            continue;
        }
        if (!fz_is_infinite_rect(tp_rect) &&
            fz_is_empty_rect(fz_intersect_rect(tp_rect, block->bbox))) {
            continue;
        }

        block_dict = PyDict_New();
        DICT_SETITEM_DROP(block_dict, dictkey_number, Py_BuildValue("i", block_n));
        DICT_SETITEM_DROP(block_dict, dictkey_type, Py_BuildValue("i", block->type));
        if (block->type == FZ_STEXT_BLOCK_IMAGE) {
            DICT_SETITEM_DROP(block_dict, dictkey_bbox, JM_py_from_rect(block->bbox));
            JM_make_image_block(block, block_dict);
        } else {
            JM_make_text_block(block, block_dict, raw, text_buffer, tp_rect);
        }

        LIST_APPEND_DROP(block_list, block_dict);
    }
    DICT_SETITEM_DROP(page_dict, dictkey_blocks, block_list);
    fz_drop_buffer(ctx, text_buffer);
}

//-----------------------------------------------------------------
// get one pixel as a list
//-----------------------------------------------------------------
PyObject *pixmap_pixel(fz_pixmap* pm, int x, int y)
{
    fz_context* ctx = mupdf::internal_context_get();
    PyObject *p = NULL;
    if (0
            || x < 0
            || x >= pm->w
            || y < 0
            || y >= pm->h
            )
    {
        throw std::range_error( MSG_PIXEL_OUTSIDE);
    }
    int n = pm->n;
    int stride = fz_pixmap_stride(ctx, pm);
    int i = stride * y + n * x;
    p = PyTuple_New(n);
    for (int j = 0; j < n; j++)
    {
        PyTuple_SET_ITEM(p, j, Py_BuildValue("i", pm->samples[i + j]));
    }
    return p;
}

int pixmap_n(mupdf::FzPixmap& pixmap)
{
    return mupdf::fz_pixmap_components( pixmap);
}

static int
JM_INT_ITEM(PyObject *obj, Py_ssize_t idx, int *result)
{
    PyObject *temp = PySequence_ITEM(obj, idx);
    if (!temp) return 1;
    if (PyLong_Check(temp)) {
        *result = (int) PyLong_AsLong(temp);
        Py_DECREF(temp);
    } else if (PyFloat_Check(temp)) {
        *result = (int) PyFloat_AsDouble(temp);
        Py_DECREF(temp);
    } else {
        Py_DECREF(temp);
        return 1;
    }
    if (PyErr_Occurred()) {
        PyErr_Clear();
        return 1;
    }
    return 0;
}

PyObject *set_pixel(fz_pixmap* pm, int x, int y, PyObject *color)
{
    fz_context* ctx = mupdf::internal_context_get();
    if (0
            || x < 0
            || x >= pm->w
            || y < 0
            || y >= pm->h
            )
    {
        throw std::range_error( MSG_PIXEL_OUTSIDE);
    }
    int n = pm->n;
    if (!PySequence_Check(color) || PySequence_Size(color) != n) {
        throw std::range_error(MSG_BAD_COLOR_SEQ);
    }
    int i, j;
    unsigned char c[5];
    for (j = 0; j < n; j++) {
        if (JM_INT_ITEM(color, j, &i) == 1) {
            throw std::range_error(MSG_BAD_COLOR_SEQ);
        }
        if (i < 0 or i >= 256) {
            throw std::range_error(MSG_BAD_COLOR_SEQ);
        }
        c[j] = (unsigned char) i;
    }
    int stride = fz_pixmap_stride(ctx, pm);
    i = stride * y + n * x;
    for (j = 0; j < n; j++) {
        pm->samples[i + j] = c[j];
    }
    Py_RETURN_NONE;
}
//-------------------------------------------
// make a buffer from an stext_page's text
//-------------------------------------------
fz_buffer *
JM_new_buffer_from_stext_page(fz_stext_page *page)
{
    fz_context* ctx = mupdf::internal_context_get();
    fz_stext_block *block;
    fz_stext_line *line;
    fz_stext_char *ch;
    fz_rect rect = page->mediabox;
    fz_buffer *buf = NULL;

    fz_try(ctx)
    {
        buf = fz_new_buffer(ctx, 256);
        for (block = page->first_block; block; block = block->next) {
            if (block->type == FZ_STEXT_BLOCK_TEXT) {
                for (line = block->u.t.first_line; line; line = line->next) {
                    for (ch = line->first_char; ch; ch = ch->next) {
                        if (!JM_rects_overlap(rect, JM_char_bbox(line, ch)) &&
                            !fz_is_infinite_rect(rect)) {
                            continue;
                        }
                        fz_append_rune(ctx, buf, ch->c);
                    }
                    fz_append_byte(ctx, buf, '\n');
                }
                fz_append_byte(ctx, buf, '\n');
            }
        }
    }
    fz_catch(ctx) {
        fz_drop_buffer(ctx, buf);
        mupdf::internal_throw_exception(ctx);
    }
    return buf;
}

static inline int canon(int c)
{
    /* TODO: proper unicode case folding */
    /* TODO: character equivalence (a matches ä, etc) */
    if (c == 0xA0 || c == 0x2028 || c == 0x2029)
        return ' ';
    if (c == '\r' || c == '\n' || c == '\t')
        return ' ';
    if (c >= 'A' && c <= 'Z')
        return c - 'A' + 'a';
    return c;
}

static inline int chartocanon(int *c, const char *s)
{
    int n = fz_chartorune(c, s);
    *c = canon(*c);
    return n;
}

static const char *match_string(const char *h, const char *n)
{
    int hc, nc;
    const char *e = h;
    h += chartocanon(&hc, h);
    n += chartocanon(&nc, n);
    while (hc == nc)
    {
        e = h;
        if (hc == ' ')
            do
                h += chartocanon(&hc, h);
            while (hc == ' ');
        else
            h += chartocanon(&hc, h);
        if (nc == ' ')
            do
                n += chartocanon(&nc, n);
            while (nc == ' ');
        else
            n += chartocanon(&nc, n);
    }
    return nc == 0 ? e : NULL;
}


static const char *find_string(const char *s, const char *needle, const char **endp)
{
    const char *end;
    while (*s)
    {
        end = match_string(s, needle);
        if (end)
        {
            *endp = end;
            return s;
        }
        ++s;
    }
    *endp = NULL;
    return NULL;
}

struct highlight
{
    Py_ssize_t len;
    PyObject *quads;
    float hfuzz, vfuzz;
};


static int
JM_FLOAT_ITEM(PyObject *obj, Py_ssize_t idx, double *result)
{
    PyObject *temp = PySequence_ITEM(obj, idx);
    if (!temp) return 1;
    *result = PyFloat_AsDouble(temp);
    Py_DECREF(temp);
    if (PyErr_Occurred()) {
        PyErr_Clear();
        return 1;
    }
    return 0;
}


//-----------------------------------------------------------------------------
// fz_quad from PySequence. Four floats are treated as rect.
// Else must be four pairs of floats.
//-----------------------------------------------------------------------------
static fz_quad
JM_quad_from_py(PyObject *r)
{
    fz_quad q = fz_make_quad(FZ_MIN_INF_RECT, FZ_MIN_INF_RECT,
                             FZ_MAX_INF_RECT, FZ_MIN_INF_RECT,
                             FZ_MIN_INF_RECT, FZ_MAX_INF_RECT,
                             FZ_MAX_INF_RECT, FZ_MAX_INF_RECT);
    fz_point p[4];
    double test, x, y;
    Py_ssize_t i;
    PyObject *obj = NULL;

    if (!r || !PySequence_Check(r) || PySequence_Size(r) != 4)
        return q;

    if (JM_FLOAT_ITEM(r, 0, &test) == 0)
        return fz_quad_from_rect(JM_rect_from_py(r));

    for (i = 0; i < 4; i++) {
        obj = PySequence_ITEM(r, i);  // next point item
        if (!obj || !PySequence_Check(obj) || PySequence_Size(obj) != 2)
            goto exit_result;  // invalid: cancel the rest

        if (JM_FLOAT_ITEM(obj, 0, &x) == 1) goto exit_result;
        if (JM_FLOAT_ITEM(obj, 1, &y) == 1) goto exit_result;
        if (x < FZ_MIN_INF_RECT) x = FZ_MIN_INF_RECT;
        if (y < FZ_MIN_INF_RECT) y = FZ_MIN_INF_RECT;
        if (x > FZ_MAX_INF_RECT) x = FZ_MAX_INF_RECT;
        if (y > FZ_MAX_INF_RECT) y = FZ_MAX_INF_RECT;
        p[i] = fz_make_point((float) x, (float) y);

        Py_CLEAR(obj);
    }
    q.ul = p[0];
    q.ur = p[1];
    q.ll = p[2];
    q.lr = p[3];
    return q;

    exit_result:;
    Py_CLEAR(obj);
    return q;
}

static float hdist(fz_point *dir, fz_point *a, fz_point *b)
{
    float dx = b->x - a->x;
    float dy = b->y - a->y;
    return fz_abs(dx * dir->x + dy * dir->y);
}

static float vdist(fz_point *dir, fz_point *a, fz_point *b)
{
    float dx = b->x - a->x;
    float dy = b->y - a->y;
    return fz_abs(dx * dir->y + dy * dir->x);
}

static void on_highlight_char(fz_context *ctx, void *arg, fz_stext_line *line, fz_stext_char *ch)
{
    struct highlight* hits = (struct highlight*) arg;
    float vfuzz = ch->size * hits->vfuzz;
    float hfuzz = ch->size * hits->hfuzz;
    fz_quad ch_quad = JM_char_quad(line, ch);
    if (hits->len > 0) {
        PyObject *quad = PySequence_ITEM(hits->quads, hits->len - 1);
        fz_quad end = JM_quad_from_py(quad);
        Py_DECREF(quad);
        if (hdist(&line->dir, &end.lr, &ch_quad.ll) < hfuzz
            && vdist(&line->dir, &end.lr, &ch_quad.ll) < vfuzz
            && hdist(&line->dir, &end.ur, &ch_quad.ul) < hfuzz
            && vdist(&line->dir, &end.ur, &ch_quad.ul) < vfuzz)
        {
            end.ur = ch_quad.ur;
            end.lr = ch_quad.lr;
            quad = JM_py_from_quad(end);
            PyList_SetItem(hits->quads, hits->len - 1, quad);
            return;
        }
    }
    LIST_APPEND_DROP(hits->quads, JM_py_from_quad(ch_quad));
    hits->len++;
}


PyObject* JM_search_stext_page(fz_stext_page *page, const char *needle)
{
    fz_context* ctx = mupdf::internal_context_get();
    struct highlight hits;
    fz_stext_block *block;
    fz_stext_line *line;
    fz_stext_char *ch;
    fz_buffer *buffer = NULL;
    const char *haystack, *begin, *end;
    fz_rect rect = page->mediabox;
    int c, inside;

    if (strlen(needle) == 0) Py_RETURN_NONE;
    PyObject *quads = PyList_New(0);
    hits.len = 0;
    hits.quads = quads;
    hits.hfuzz = 0.2f; /* merge kerns but not large gaps */
    hits.vfuzz = 0.1f;

    fz_try(ctx) {
        buffer = JM_new_buffer_from_stext_page( page);
        haystack = fz_string_from_buffer(ctx, buffer);
        begin = find_string(haystack, needle, &end);
        if (!begin) goto no_more_matches;

        inside = 0;
        for (block = page->first_block; block; block = block->next) {
            if (block->type != FZ_STEXT_BLOCK_TEXT) {
                continue;
            }
            for (line = block->u.t.first_line; line; line = line->next) {
                for (ch = line->first_char; ch; ch = ch->next) {
                    if (!fz_is_infinite_rect(rect) &&
                        !JM_rects_overlap(rect, JM_char_bbox(line, ch))) {
                            goto next_char;
                        }
try_new_match:
                    if (!inside) {
                        if (haystack >= begin) inside = 1;
                    }
                    if (inside) {
                        if (haystack < end) {
                            on_highlight_char(ctx, &hits, line, ch);
                        } else {
                            inside = 0;
                            begin = find_string(haystack, needle, &end);
                            if (!begin) goto no_more_matches;
                            else goto try_new_match;
                        }
                    }
                    haystack += fz_chartorune(&c, haystack);
next_char:;
                }
                assert(*haystack == '\n');
                ++haystack;
            }
            assert(*haystack == '\n');
            ++haystack;
        }
no_more_matches:;
    }
    fz_always(ctx)
        fz_drop_buffer(ctx, buffer);
    fz_catch(ctx)
        mupdf::internal_throw_exception(ctx);

    return quads;
}

/* MuPDF-1.23.x has an incorrect and unusable
fz_new_image_from_compressed_buffer() wrapper that thinks the `decode` and
`colorkey` args are out-params. So we provide an alternative wrapper where
we always set these to args to null, which is sufficient for PyMuPDF caller
`Document._insert_image()`. */
fz_image* fz_new_image_from_compressed_buffer(
        int w,
        int h,
        int bpc,
        fz_colorspace *colorspace,
        int xres,
        int yres,
        int interpolate,
        int imagemask,
        fz_compressed_buffer *buffer,
        fz_image *mask
        )
{
    return mupdf::ll_fz_new_image_from_compressed_buffer(
            w,
            h,
            bpc,
            colorspace,
            xres,
            yres,
            interpolate,
            imagemask,
            nullptr,
            nullptr,
            buffer,
            mask
            );
}

%}

/* Declarations for functions defined above. */

void page_merge(
        mupdf::PdfDocument& doc_des,
        mupdf::PdfDocument& doc_src,
        int page_from,
        int page_to,
        int rotate,
        int links,
        int copy_annots,
        mupdf::PdfGraftMap& graft_map
        );

void JM_merge_range(
        mupdf::PdfDocument& doc_des,
        mupdf::PdfDocument& doc_src,
        int spage,
        int epage,
        int apage,
        int rotate,
        int links,
        int annots,
        int show_progress,
        mupdf::PdfGraftMap& graft_map
        );

void FzDocument_insert_pdf(
        mupdf::FzDocument& doc,
        mupdf::FzDocument& src,
        int from_page,
        int to_page,
        int start_at,
        int rotate,
        int links,
        int annots,
        int show_progress,
        int final,
        mupdf::PdfGraftMap& graft_map
        );

int page_xref(mupdf::FzDocument& this_doc, int pno);
void _newPage(mupdf::FzDocument& self, int pno=-1, float width=595, float height=842);
void _newPage(mupdf::PdfDocument& self, int pno=-1, float width=595, float height=842);
void JM_add_annot_id(mupdf::PdfAnnot& annot, const char* stem);
std::vector< std::string> JM_get_annot_id_list(mupdf::PdfPage& page);
mupdf::PdfAnnot _add_caret_annot(mupdf::PdfPage& self, mupdf::FzPoint& point);
mupdf::PdfAnnot _add_caret_annot(mupdf::FzPage& self, mupdf::FzPoint& point);
const char* Tools_parse_da(mupdf::PdfAnnot& this_annot);
PyObject* Annot_getAP(mupdf::PdfAnnot& annot);
void Tools_update_da(mupdf::PdfAnnot& this_annot, const char* da_str);
mupdf::FzPoint JM_point_from_py(PyObject* p);
mupdf::FzRect Annot_rect(mupdf::PdfAnnot& annot);
PyObject* util_transform_rect(PyObject* rect, PyObject* matrix);
PyObject* Annot_rect3(mupdf::PdfAnnot& annot);
mupdf::FzMatrix Page_derotate_matrix(mupdf::PdfPage& pdfpage);
mupdf::FzMatrix Page_derotate_matrix(mupdf::FzPage& pdfpage);
PyObject* JM_get_annot_xref_list(const mupdf::PdfObj& page_obj);
PyObject* xref_object(mupdf::PdfDocument& pdf, int xref, int compressed=0, int ascii=0);
PyObject* xref_object(mupdf::FzDocument& document, int xref, int compressed=0, int ascii=0);

PyObject* Link_is_external(mupdf::FzLink& this_link);
PyObject* Page_addAnnot_FromString(mupdf::PdfPage& page, PyObject* linklist);
PyObject* Page_addAnnot_FromString(mupdf::FzPage& page, PyObject* linklist);
mupdf::FzLink Link_next(mupdf::FzLink& this_link);

static int page_count_fz2(void* document);
int page_count_fz(mupdf::FzDocument& document);
int page_count_pdf(mupdf::PdfDocument& pdf);
int page_count(mupdf::FzDocument& document);
int page_count(mupdf::PdfDocument& pdf);

PyObject* page_annot_xrefs(mupdf::PdfDocument& pdf, int pno);
PyObject* page_annot_xrefs(mupdf::FzDocument& document, int pno);
bool Outline_is_external(mupdf::FzOutline* outline);
void Document_extend_toc_items(mupdf::PdfDocument& pdf, PyObject* items);
void Document_extend_toc_items(mupdf::FzDocument& document, PyObject* items);

int ll_fz_absi(int i);

mupdf::FzDevice JM_new_texttrace_device(PyObject* out);

fz_rect JM_char_bbox(const mupdf::FzStextLine& line, const mupdf::FzStextChar& ch);

static fz_quad JM_char_quad( fz_stext_line *line, fz_stext_char *ch);
void JM_print_stext_page_as_text(mupdf::FzBuffer& res, mupdf::FzStextPage& page);

void set_small_glyph_heights(int on);
mupdf::FzRect JM_cropbox(mupdf::PdfObj& page_obj);
PyObject* get_cdrawings(mupdf::FzPage& page, PyObject *extended=NULL, PyObject *callback=NULL, PyObject *method=NULL);

mupdf::FzRect JM_make_spanlist(
        PyObject *line_dict,
        mupdf::FzStextLine& line,
        int raw,
        mupdf::FzBuffer& buff,
        mupdf::FzRect& tp_rect
        );

PyObject* extractWORDS(mupdf::FzStextPage& this_tpage, PyObject *delimiters);
PyObject* extractBLOCKS(mupdf::FzStextPage& self);

PyObject* link_uri(mupdf::FzLink& link);

fz_stext_page* page_get_textpage(
        mupdf::FzPage& self,
        PyObject* clip,
        int flags,
        PyObject* matrix
        );

void JM_make_textpage_dict(fz_stext_page *tp, PyObject *page_dict, int raw);
PyObject *pixmap_pixel(fz_pixmap* pm, int x, int y);
int pixmap_n(mupdf::FzPixmap& pixmap);

PyObject* JM_search_stext_page(fz_stext_page *page, const char *needle);

PyObject *set_pixel(fz_pixmap* pm, int x, int y, PyObject *color);

fz_image* fz_new_image_from_compressed_buffer(
        int w,
        int h,
        int bpc,
        fz_colorspace *colorspace,
        int xres,
        int yres,
        int interpolate,
        int imagemask,
        fz_compressed_buffer *buffer,
        fz_image *mask
        );

void rearrange_pages2( mupdf::PdfDocument& doc, PyObject *new_pages);
