%module fitz
%pythonbegin %{
from __future__ import division, print_function
%}
//-----------------------------------------------------------------------------
// SWIG macro: generate fitz exceptions
//-----------------------------------------------------------------------------
%define FITZEXCEPTION(meth, cond)
%exception meth
{
    $action
    if (cond) {PyErr_SetString(PyExc_RuntimeError, fz_caught_message(gctx));
        return NULL;}
}
%enddef

//-----------------------------------------------------------------------------
// SWIG macro: check that a document is not closed / encrypted
//-----------------------------------------------------------------------------
%define CLOSECHECK(meth, doc)
%pythonprepend meth %{doc
if self.isClosed or self.isEncrypted:
    raise ValueError("document closed or encrypted")%}
%enddef

%define CLOSECHECK0(meth, doc)
%pythonprepend meth%{doc
if self.isClosed:
    raise ValueError("document closed")%}
%enddef

//-----------------------------------------------------------------------------
// SWIG macro: check if object has a valid parent
//-----------------------------------------------------------------------------
%define PARENTCHECK(meth, doc)
%pythonprepend meth %{doc
CheckParent(self)%}
%enddef


%{
#define MEMDEBUG 0
#if MEMDEBUG == 1
    #define DEBUGMSG1(x) PySys_WriteStderr("[DEBUG] free %s ", x)
    #define DEBUGMSG2 PySys_WriteStderr("... done!\n")
#else
    #define DEBUGMSG1(x)
    #define DEBUGMSG2
#endif

#ifndef FLT_EPSILON
  #define FLT_EPSILON 1e-5
#endif

#define return_none Py_RETURN_NONE
#define SWIG_FILE_WITH_INIT
#define SWIG_PYTHON_2_UNICODE

// memory allocation macros
#define JM_MEMORY 1
#if  PY_MAJOR_VERSION < 3
    #undef JM_MEMORY
    #define JM_MEMORY 0
#endif

#if JM_MEMORY == 1
    #define JM_Alloc(type, len) PyMem_New(type, len)
    #define JM_Free(x) PyMem_Del(x)
#else
    #define JM_Alloc(type, len) (type *) malloc(sizeof(type)*len)
    #define JM_Free(x) free(x)
#endif

#define EMPTY_STRING PyUnicode_FromString("")
#define EXISTS(x) (x != NULL && PyObject_IsTrue(x)==1)
#define THROWMSG(ctx, msg) fz_throw(ctx, FZ_ERROR_GENERIC, msg)
#define ASSERT_PDF(cond) if (cond == NULL) fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF")
#define INRANGE(v, low, high) ((low) <= v && v <= (high))
#define MAX(a, b) ((a) < (b)) ? (b) : (a)
#define MIN(a, b) ((a) < (b)) ? (a) : (b)

#define JM_PyErr_Clear if (PyErr_Occurred()) PyErr_Clear()

// binary output depends on Python major
# if PY_MAJOR_VERSION >= 3
    #define JM_BinFromChar(x) PyBytes_FromString(x)
    #define JM_BinFromCharSize(x, y) PyBytes_FromStringAndSize(x, (Py_ssize_t) y)
# else
    #define JM_BinFromChar(x) PyByteArray_FromStringAndSize(x, (Py_ssize_t) strlen(x))
    #define JM_BinFromCharSize(x, y) PyByteArray_FromStringAndSize(x, (Py_ssize_t) y)
# endif

#include <fitz.h>
#include <pdf.h>
#include <time.h>
// freetype includes >> --------------------------------------------------
#include <ft2build.h>
#include FT_FREETYPE_H
#ifdef FT_FONT_FORMATS_H
#include FT_FONT_FORMATS_H
#else
#include FT_XFREE86_H
#endif
#include FT_TRUETYPE_TABLES_H

#ifndef FT_SFNT_HEAD
#define FT_SFNT_HEAD ft_sfnt_head
#endif
// << freetype includes --------------------------------------------------


char *JM_Python_str_AsChar(PyObject *str);

// additional headers from MuPDF ----------------------------------------------
pdf_obj *pdf_lookup_page_loc(fz_context *ctx, pdf_document *doc, int needle, pdf_obj **parentp, int *indexp);
fz_pixmap *fz_scale_pixmap(fz_context *ctx, fz_pixmap *src, float x, float y, float w, float h, const fz_irect *clip);
int fz_pixmap_size(fz_context *ctx, fz_pixmap *src);
void fz_subsample_pixmap(fz_context *ctx, fz_pixmap *tile, int factor);
void fz_copy_pixmap_rect(fz_context *ctx, fz_pixmap *dest, fz_pixmap *src, fz_irect b, const fz_default_colorspaces *default_cs);

// end of additional MuPDF headers --------------------------------------------

PyObject *JM_mupdf_warnings_store;
PyObject *JM_mupdf_show_errors;
%}

//-----------------------------------------------------------------------------
// global context
//-----------------------------------------------------------------------------
%init %{
#if JM_MEMORY == 1
    gctx = fz_new_context(&JM_Alloc_Context, NULL, FZ_STORE_DEFAULT);
#else
    gctx = fz_new_context(NULL, NULL, FZ_STORE_DEFAULT);
#endif
    if(!gctx)
    {
        PyErr_SetString(PyExc_RuntimeError, "Fatal error: could not create global context.");
# if PY_MAJOR_VERSION >= 3
       return NULL;
# else
       return;
# endif
    }
    fz_register_document_handlers(gctx);

//-----------------------------------------------------------------------------
// START redirect stdout/stderr
//-----------------------------------------------------------------------------
JM_mupdf_warnings_store = PyList_New(0);
JM_mupdf_show_errors = Py_True;
char user[] = "PyMuPDF";
fz_set_warning_callback(gctx, JM_mupdf_warning, &user);
fz_set_error_callback(gctx, JM_mupdf_error, &user);
//-----------------------------------------------------------------------------
// STOP redirect stdout/stderr
//-----------------------------------------------------------------------------
// init global constants
//-----------------------------------------------------------------------------
dictkey_align = PyString_InternFromString("align");
dictkey_bbox = PyString_InternFromString("bbox");
dictkey_blocks = PyString_InternFromString("blocks");
dictkey_bpc = PyString_InternFromString("bpc");
dictkey_c = PyString_InternFromString("c");
dictkey_chars = PyString_InternFromString("chars");
dictkey_color = PyString_InternFromString("color");
dictkey_colorspace = PyString_InternFromString("colorspace");
dictkey_content = PyString_InternFromString("content");
dictkey_creationDate = PyString_InternFromString("creationDate");
dictkey_cs_name = PyString_InternFromString("cs-name");
dictkey_da = PyString_InternFromString("da");
dictkey_dashes = PyString_InternFromString("dashes");
dictkey_desc = PyString_InternFromString("desc");
dictkey_dir = PyString_InternFromString("dir");
dictkey_effect = PyString_InternFromString("effect");
dictkey_ext = PyString_InternFromString("ext");
dictkey_filename = PyString_InternFromString("filename");
dictkey_fill = PyString_InternFromString("fill");
dictkey_flags = PyString_InternFromString("flags");
dictkey_font = PyString_InternFromString("font");
dictkey_height = PyString_InternFromString("height");
dictkey_id = PyString_InternFromString("id");
dictkey_image = PyString_InternFromString("image");
dictkey_length = PyString_InternFromString("length");
dictkey_lines = PyString_InternFromString("lines");
dictkey_modDate = PyString_InternFromString("modDate");
dictkey_name = PyString_InternFromString("name");
dictkey_number = PyString_InternFromString("number");
dictkey_origin = PyString_InternFromString("origin");
dictkey_size = PyString_InternFromString("size");
dictkey_smask = PyString_InternFromString("smask");
dictkey_spans = PyString_InternFromString("spans");
dictkey_stroke = PyString_InternFromString("stroke");
dictkey_style = PyString_InternFromString("style");
dictkey_subject = PyString_InternFromString("subject");
dictkey_text = PyString_InternFromString("text");
dictkey_title = PyString_InternFromString("title");
dictkey_type = PyString_InternFromString("type");
dictkey_ufilename = PyString_InternFromString("ufilename");
dictkey_width = PyString_InternFromString("width");
dictkey_wmode = PyString_InternFromString("wmode");
dictkey_xref = PyString_InternFromString("xref");
dictkey_xres = PyString_InternFromString("xres");
dictkey_yres = PyString_InternFromString("yres");
%}

%header %{
fz_context *gctx;
static int JM_UNIQUE_ID = 0;

struct DeviceWrapper {
    fz_device *device;
    fz_display_list *list;
};
%}

//-----------------------------------------------------------------------------
// include version information and several other helpers
//-----------------------------------------------------------------------------
%pythoncode %{
import io
import math
import os
import weakref
import hashlib
from binascii import hexlify

fitz_py2 = str is bytes  # if true, this is Python 2
string_types = (str, unicode) if fitz_py2 else (str,)

try:
    from pymupdf_fonts import fontdescriptors

    fitz_fontdescriptors = fontdescriptors.copy()
    del fontdescriptors
except ImportError:
    fitz_fontdescriptors = {}
%}
%include version.i
%include helper-defines.i
%include helper-geo-c.i
%include helper-other.i
%include helper-pixmap.i
%include helper-geo-py.i
%include helper-annot.i
%include helper-stext.i
%include helper-fields.i
%include helper-python.i
%include helper-portfolio.i
%include helper-select.i
%include helper-xobject.i
%include helper-pdfinfo.i
%include helper-convert.i
%include helper-trace.i

//-----------------------------------------------------------------------------
// fz_document
//-----------------------------------------------------------------------------
struct Document
{
    %extend
    {
        ~Document()
        {
            DEBUGMSG1("Document w/o close");
            fz_document *this_doc = (fz_document *) $self;
            fz_drop_document(gctx, this_doc);
            DEBUGMSG2;
        }
        FITZEXCEPTION(Document, !result)

        %pythonprepend Document %{
        """Creates a document. Use 'open' as a synonym.

        Notes:
            Basic usages:
            open() - new PDF document
            open(filename) - string or pathlib.Path, must have supported
                    file extension.
            open(type, buffer) - type: valid extension, buffer: bytes object.
            open(stream=buffer, filetype=type) - keyword version of previous.
            open(filename, fileype=type) - filename with unrecognized extension.
            rect, width, height, fontsize: layout reflowable document
            on open (e.g. EPUB). Ignored if n/a.
        """

        if not filename or type(filename) is str:
            pass
        else:
            if fitz_py2:  # Python 2
                if type(filename) is unicode:
                    filename = filename.encode("utf8")
            else:
                filename = str(filename)  # takes care of pathlib.Path

        if stream:
            if not (filename or filetype):
                raise ValueError("need filetype for opening a stream")

            if type(stream) is bytes:
                self.stream = stream
            elif type(stream) is bytearray:
                self.stream = bytes(stream)
            elif type(stream) is io.BytesIO:
                self.stream = stream.getvalue()
            else:
                raise ValueError("bad type: 'stream'")
            stream = self.stream
        else:
            self.stream = None

        if filename and not stream:
            self.name = filename
        else:
            self.name = ""

        self.isClosed    = False
        self.isEncrypted = False
        self.metadata    = None
        self.FontInfos   = []
        self.Graftmaps   = {}
        self.ShownPages  = {}
        self.InsertedImages  = {}
        self._page_refs  = weakref.WeakValueDictionary()%}

        %pythonappend Document %{
            if self.thisown:
                self._graft_id = TOOLS.gen_id()
                if self.needsPass is True:
                    self.isEncrypted = True
                else: # we won't init until doc is decrypted
                    self.initData()
        %}

        Document(const char *filename=NULL, PyObject *stream=NULL,
                      const char *filetype=NULL, PyObject *rect=NULL,
                      float width=0, float height=0,
                      float fontsize=11)
        {
            gctx->error.errcode = 0;       // reset any error code
            gctx->error.message[0] = 0;    // reset any error message
            fz_document *doc = NULL;
            char *c = NULL;
            size_t len = 0;
            fz_stream *data = NULL;
            float w = width, h = height;
            fz_rect r = JM_rect_from_py(rect);
            if (!fz_is_infinite_rect(r)) {
                w = r.x1 - r.x0;
                h = r.y1 - r.y0;
            }

            fz_try(gctx) {
                if (stream != Py_None) { // stream given, **MUST** be bytes!

                    c = PyBytes_AS_STRING(stream); // just a pointer, no new obj
                    len = (size_t) PyBytes_Size(stream);
                    data = fz_open_memory(gctx, (const unsigned char *) c, len);
                    char *magic = (char *)filename;
                    if (!magic) magic = (char *)filetype;
                    doc = fz_open_document_with_stream(gctx, magic, data);
                } else {
                    if (filename) {
                        if (!filetype || strlen(filetype) == 0) {
                            doc = fz_open_document(gctx, filename);
                        } else {
                            const fz_document_handler *handler;
                            handler = fz_recognize_document(gctx, filetype);
                            if (handler && handler->open)
                                doc = handler->open(gctx, filename);
                            else THROWMSG(gctx, "unrecognized file type");
                        }
                    } else {
                        pdf_document *pdf = pdf_create_document(gctx);
                        pdf->dirty = 1;
                        doc = (fz_document *) pdf;
                    }
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            if (w > 0 && h > 0) {
                fz_layout_document(gctx, doc, w, h, fontsize);
            }
            return (struct Document *) doc;
        }

        %pythonprepend close %{
            """Close document."""
            if self.isClosed:
                raise ValueError("document closed")
            if hasattr(self, "_outline") and self._outline:
                self._dropOutline(self._outline)
                self._outline = None
            self._reset_page_refs()
            self.metadata    = None
            self.stream      = None
            self.isClosed    = True
            self.FontInfos   = []
            for k in self.Graftmaps.keys():
                self.Graftmaps[k] = None
            self.Graftmaps = {}
            self.ShownPages = {}
            self.InsertedImages  = {}
        %}

        %pythonappend close %{self.thisown = False%}
        void close()
        {
            DEBUGMSG1("Document after close");
            fz_document *doc = (fz_document *) $self;
            while(doc->refs > 1) {
                fz_drop_document(gctx, doc);
            }
            fz_drop_document(gctx, doc);
            DEBUGMSG2;
        }

        FITZEXCEPTION(loadPage, !result)
        %pythonprepend loadPage %{
        """Load a page.

        'page_id' is either a 0-based page number or a tuple (chapter, pno),
        with chapter number and page number within that chapter.
        """

        if self.isClosed or self.isEncrypted:
            raise ValueError("document closed or encrypted")
        if page_id is None:
            page_id = 0
        if page_id not in self:
            raise ValueError("page not in document")
        if type(page_id) is int and page_id < 0:
            np = self.pageCount
            while page_id < 0:
                page_id += np
        %}
        %pythonappend loadPage %{
        val.thisown = True
        val.parent = weakref.proxy(self)
        self._page_refs[id(val)] = val
        val._annot_refs = weakref.WeakValueDictionary()
        val.number = page_id
        %}
        struct Page *
        loadPage(PyObject *page_id)
        {
            fz_page *page = NULL;
            fz_document *doc = (fz_document *) $self;
            int pno;
            PyObject *val = NULL;
            fz_try(gctx) {
                if (PySequence_Check(page_id)) {
                    val = PySequence_GetItem(page_id, 0);
                    if (!val) THROWMSG(gctx, "bad page page id");
                    int chapter = (int) PyLong_AsLong(val);
                    Py_DECREF(val);
                    if (PyErr_Occurred()) THROWMSG(gctx, "bad page id");

                    val = PySequence_GetItem(page_id, 1);
                    if (!val) THROWMSG(gctx, "bad page page id");
                    pno = (int) PyLong_AsLong(val);
                    Py_DECREF(val);
                    if (PyErr_Occurred()) THROWMSG(gctx, "bad page id");

                    page = fz_load_chapter_page(gctx, doc, chapter, pno);
                } else {
                    pno = (int) PyLong_AsLong(page_id);
                    if (PyErr_Occurred()) THROWMSG(gctx, "bad page id");
                    page = fz_load_page(gctx, doc, pno);
                }
            }
            fz_catch(gctx) {
                PyErr_Clear();
                return NULL;
            }
            PyErr_Clear();
            return (struct Page *) page;
        }


        FITZEXCEPTION(_remove_links_to, !result)
        PyObject *_remove_links_to(int first, int last)
        {
            fz_try(gctx) {
                fz_document *doc = (fz_document *) $self;
                pdf_document *pdf = pdf_specifics(gctx, doc);
                pdf_drop_page_tree(gctx, pdf);
                pdf_load_page_tree(gctx, pdf);
                remove_dest_range(gctx, pdf, first, last);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }


        CLOSECHECK0(_loadOutline, """Load first outline.""")
        struct Outline *_loadOutline()
        {
            fz_outline *ol = NULL;
            fz_document *doc = (fz_document *) $self;
            fz_try(gctx) {
                ol = fz_load_outline(gctx, doc);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct Outline *) ol;
        }

        void _dropOutline(struct Outline *ol) {
            DEBUGMSG1("Outline");
            fz_outline *this_ol = (fz_outline *) ol;
            fz_drop_outline(gctx, this_ol);
            DEBUGMSG2;
        }

        //---------------------------------------------------------------------
        // EmbeddedFiles utility functions
        //---------------------------------------------------------------------
        FITZEXCEPTION(_embeddedFileNames, !result)
        CLOSECHECK0(_embeddedFileNames, """Get list of embedded file names.""")
        PyObject *_embeddedFileNames(PyObject *namelist)
        {
            fz_document *doc = (fz_document *) $self;
            pdf_document *pdf = pdf_specifics(gctx, doc);
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                PyObject *val;
                pdf_obj *names = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf),
                                      PDF_NAME(Root),
                                      PDF_NAME(Names),
                                      PDF_NAME(EmbeddedFiles),
                                      PDF_NAME(Names),
                                      NULL);
                if (pdf_is_array(gctx, names)) {
                    int i, n = pdf_array_len(gctx, names);
                    for (i=0; i < n; i+=2) {
                        val = JM_EscapeStrFromStr(pdf_to_text_string(gctx,
                                         pdf_array_get(gctx, names, i)));
                        LIST_APPEND_DROP(namelist, val);
                    }
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        FITZEXCEPTION(_embeddedFileDel, !result)
        PyObject *_embeddedFileDel(int idx)
        {
            fz_try(gctx) {
                fz_document *doc = (fz_document *) $self;
                pdf_document *pdf = pdf_document_from_fz_document(gctx, doc);
                pdf_obj *names = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf),
                                      PDF_NAME(Root),
                                      PDF_NAME(Names),
                                      PDF_NAME(EmbeddedFiles),
                                      PDF_NAME(Names),
                                      NULL);
                pdf_array_delete(gctx, names, idx + 1);
                pdf_array_delete(gctx, names, idx);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        FITZEXCEPTION(_embeddedFileInfo, !result)
        PyObject *_embeddedFileInfo(int idx, PyObject *infodict)
        {
            fz_document *doc = (fz_document *) $self;
            pdf_document *pdf = pdf_document_from_fz_document(gctx, doc);
            char *name;
            fz_try(gctx) {
                pdf_obj *names = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf),
                                      PDF_NAME(Root),
                                      PDF_NAME(Names),
                                      PDF_NAME(EmbeddedFiles),
                                      PDF_NAME(Names),
                                      NULL);

                pdf_obj *o = pdf_array_get(gctx, names, 2*idx+1);

                name = (char *) pdf_to_text_string(gctx,
                                          pdf_dict_get(gctx, o, PDF_NAME(F)));
                DICT_SETITEM_DROP(infodict, dictkey_filename, JM_EscapeStrFromStr(name));

                name = (char *) pdf_to_text_string(gctx,
                                    pdf_dict_get(gctx, o, PDF_NAME(UF)));
                DICT_SETITEM_DROP(infodict, dictkey_ufilename, JM_EscapeStrFromStr(name));

                name = (char *) pdf_to_text_string(gctx,
                                    pdf_dict_get(gctx, o, PDF_NAME(Desc)));
                DICT_SETITEM_DROP(infodict, dictkey_desc, JM_UnicodeFromStr(name));

                int len = -1, DL = -1;
                pdf_obj *ef = pdf_dict_get(gctx, o, PDF_NAME(EF));
                o = pdf_dict_getl(gctx, ef, PDF_NAME(F),
                                            PDF_NAME(Length), NULL);
                if (o) len = pdf_to_int(gctx, o);

                o = pdf_dict_getl(gctx, ef, PDF_NAME(F), PDF_NAME(DL), NULL);
                if (o) {
                    DL = pdf_to_int(gctx, o);
                } else {
                    o = pdf_dict_getl(gctx, ef, PDF_NAME(F), PDF_NAME(Params),
                                   PDF_NAME(Size), NULL);
                    if (o) DL = pdf_to_int(gctx, o);
                }
                DICT_SETITEM_DROP(infodict, dictkey_size, Py_BuildValue("i", DL));
                DICT_SETITEM_DROP(infodict, dictkey_length, Py_BuildValue("i", len));
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        FITZEXCEPTION(_embeddedFileUpd, !result)
        PyObject *_embeddedFileUpd(int idx, PyObject *buffer = NULL, char *filename = NULL, char *ufilename = NULL, char *desc = NULL)
        {
            fz_document *doc = (fz_document *) $self;
            pdf_document *pdf = pdf_document_from_fz_document(gctx, doc);
            fz_buffer *res = NULL;
            fz_var(res);
            fz_try(gctx) {
                pdf_obj *names = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf),
                                      PDF_NAME(Root),
                                      PDF_NAME(Names),
                                      PDF_NAME(EmbeddedFiles),
                                      PDF_NAME(Names),
                                      NULL);

                pdf_obj *entry = pdf_array_get(gctx, names, 2*idx+1);

                pdf_obj *filespec = pdf_dict_getl(gctx, entry, PDF_NAME(EF),
                                                  PDF_NAME(F), NULL);
                if (!filespec) THROWMSG(gctx, "bad PDF: /EF object not found");

                res = JM_BufferFromBytes(gctx, buffer);
                if (EXISTS(buffer) && !res) THROWMSG(gctx, "bad type: 'buffer'");
                if (res)
                {
                    JM_update_stream(gctx, pdf, filespec, res, 1);
                    // adjust /DL and /Size parameters
                    int64_t len = (int64_t) fz_buffer_storage(gctx, res, NULL);
                    pdf_obj *l = pdf_new_int(gctx, len);
                    pdf_dict_put(gctx, filespec, PDF_NAME(DL), l);
                    pdf_dict_putl(gctx, filespec, l, PDF_NAME(Params), PDF_NAME(Size), NULL);
                }

                if (filename)
                    pdf_dict_put_text_string(gctx, entry, PDF_NAME(F), filename);

                if (ufilename)
                    pdf_dict_put_text_string(gctx, entry, PDF_NAME(UF), ufilename);

                if (desc)
                    pdf_dict_put_text_string(gctx, entry, PDF_NAME(Desc), desc);
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx)
                return NULL;
            pdf->dirty = 1;
            return_none;
        }

        FITZEXCEPTION(_embeddedFileGet, !result)
        PyObject *_embeddedFileGet(int idx)
        {
            fz_document *doc = (fz_document *) $self;
            PyObject *cont = NULL;
            pdf_document *pdf = pdf_document_from_fz_document(gctx, doc);
            fz_buffer *buf = NULL;
            fz_var(buf);
            fz_try(gctx) {
                pdf_obj *names = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf),
                                      PDF_NAME(Root),
                                      PDF_NAME(Names),
                                      PDF_NAME(EmbeddedFiles),
                                      PDF_NAME(Names),
                                      NULL);

                pdf_obj *entry = pdf_array_get(gctx, names, 2*idx+1);
                pdf_obj *filespec = pdf_dict_getl(gctx, entry, PDF_NAME(EF),
                                                  PDF_NAME(F), NULL);
                buf = pdf_load_stream(gctx, filespec);
                cont = JM_BinFromBuffer(gctx, buf);
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, buf);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return cont;
        }

        FITZEXCEPTION(_embeddedFileAdd, !result)
        PyObject *_embeddedFileAdd(const char *name, PyObject *buffer, char *filename=NULL, char *ufilename=NULL, char *desc=NULL)
        {
            fz_document *doc = (fz_document *) $self;
            pdf_document *pdf = pdf_document_from_fz_document(gctx, doc);
            fz_buffer *data = NULL;
            unsigned char *buffdata;
            fz_var(data);
            int entry = 0;
            size_t size = 0;
            pdf_obj *names = NULL;
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                data = JM_BufferFromBytes(gctx, buffer);
                if (!data) THROWMSG(gctx, "bad type: 'buffer'");
                size = fz_buffer_storage(gctx, data, &buffdata);

                names = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf),
                                      PDF_NAME(Root),
                                      PDF_NAME(Names),
                                      PDF_NAME(EmbeddedFiles),
                                      PDF_NAME(Names),
                                      NULL);
                if (!pdf_is_array(gctx, names)) {
                    pdf_obj *root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf),
                                                 PDF_NAME(Root));
                    names = pdf_new_array(gctx, pdf, 6);  // an even number!
                    pdf_dict_putl_drop(gctx, root, names,
                                      PDF_NAME(Names),
                                      PDF_NAME(EmbeddedFiles),
                                      PDF_NAME(Names),
                                      NULL);
                }

                pdf_obj *fileentry = JM_embed_file(gctx, pdf, data,
                                                   filename,
                                                   ufilename,
                                                   desc, 1);
                pdf_array_push(gctx, names, pdf_new_text_string(gctx, name));
                pdf_array_push_drop(gctx, names, fileentry);
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, data);
            }
            fz_catch(gctx) {
                return NULL;
            }
            pdf->dirty = 1;
            return_none;
        }

        %pythoncode %{
        def embeddedFileNames(self):
            """Get list of names of EmbeddedFiles."""
            filenames = []
            self._embeddedFileNames(filenames)
            return filenames

        def _embeddedFileIndex(self, item):
            filenames = self.embeddedFileNames()
            msg = "'%s' not in EmbeddedFiles array." % str(item)
            if item in filenames:
                idx = filenames.index(item)
            elif item in range(len(filenames)):
                idx = item
            else:
                raise ValueError(msg)
            return idx

        def embeddedFileCount(self):
            """Get number of EmbeddedFiles."""
            return len(self.embeddedFileNames())

        def embeddedFileDel(self, item):
            """Delete an entry from EmbeddedFiles.

            Notes:
                The argument must be name or index of an EmbeddedFiles item.
                Physical deletion of data will happen on save to a new
                file with appropriate garbage option.
            Args:
                item: (str/int) name or number of the entry.
            Returns:
                None
            """
            idx = self._embeddedFileIndex(item)
            return self._embeddedFileDel(idx)

        def embeddedFileInfo(self, item):
            """Get information of an item in the EmbeddedFiles array.

            Args:
                item: number or name of item.
            Returns:
                Information dictionary.
            """
            idx = self._embeddedFileIndex(item)
            infodict = {"name": self.embeddedFileNames()[idx]}
            self._embeddedFileInfo(idx, infodict)
            return infodict

        def embeddedFileGet(self, item):
            """Get the content of an item in the EmbeddedFiles array.

            Args:
                item: number or name of item.
            Returns:
                (bytes) The file content.
            """
            idx = self._embeddedFileIndex(item)
            return self._embeddedFileGet(idx)

        def embeddedFileUpd(self, item, buffer=None,
                                  filename=None,
                                  ufilename=None,
                                  desc=None):
            """Change an item of the EmbeddedFiles array.

            Notes:
                All parameter are optional. If all arguments are omitted, the
                method is a no-op.
            Args:
                item: the number or the name of the item.
                buffer: (binary data) the new file content.
                filename: (str) the new file name.
                ufilename: (unicode) the new filen ame.
                desc: (str) the new description.
            """
            idx = self._embeddedFileIndex(item)
            return self._embeddedFileUpd(idx, buffer=buffer,
                                         filename=filename,
                                         ufilename=ufilename,
                                         desc=desc)

        def embeddedFileAdd(self, name, buffer,
                                  filename=None,
                                  ufilename=None,
                                  desc=None):
            """Add an item to the EmbeddedFiles array.

            Args:
                name: the name of the new item.
                buffer: (binary data) the file content.
                filename: (str) the file name.
                ufilename: (unicode) the filen ame.
                desc: (str) the description.
            """
            filenames = self.embeddedFileNames()
            msg = "Name '%s' already in EmbeddedFiles array." % str(name)
            if name in filenames:
                raise ValueError(msg)

            if filename is None:
                filename = name
            if ufilename is None:
                ufilename = unicode(filename, "utf8") if str is bytes else filename
            if desc is None:
                desc = name
            return self._embeddedFileAdd(name, buffer=buffer,
                                         filename=filename,
                                         ufilename=ufilename,
                                         desc=desc)
        %}

        FITZEXCEPTION(convertToPDF, !result)
        CLOSECHECK(convertToPDF, """Convert document to a PDF, selecting page range and optional rotation. Output bytes object.""")
        PyObject *convertToPDF(int from_page=0, int to_page=-1, int rotate=0)
        {
            PyObject *doc = NULL;
            fz_document *fz_doc = (fz_document *) $self;
            fz_try(gctx) {
                int fp = from_page, tp = to_page, srcCount = fz_count_pages(gctx, fz_doc);
                if (pdf_specifics(gctx, fz_doc))
                    THROWMSG(gctx, "bad document type");
                if (fp < 0) fp = 0;
                if (fp > srcCount - 1) fp = srcCount - 1;
                if (tp < 0) tp = srcCount - 1;
                if (tp > srcCount - 1) tp = srcCount - 1;
                doc = JM_convert_to_pdf(gctx, fz_doc, fp, tp, rotate);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return doc;
        }

        FITZEXCEPTION(pageCount, !result)
        CLOSECHECK0(pageCount, """Number of pages.""")
        %pythoncode%{@property%}
        PyObject *pageCount()
        {
            PyObject *ret;
            fz_try(gctx) {
                ret = Py_BuildValue("i", fz_count_pages(gctx, (fz_document *) $self));
            }
            fz_catch(gctx) {
                return NULL;
            }
            return ret;
        }

        FITZEXCEPTION(chapterCount, !result)
        CLOSECHECK0(chapterCount, """Number of chapters.""")
        %pythoncode%{@property%}
        PyObject *chapterCount()
        {
            PyObject *ret;
            fz_try(gctx) {
                ret = Py_BuildValue("i", fz_count_chapters(gctx, (fz_document *) $self));
            }
            fz_catch(gctx) {
                return NULL;
            }
            return ret;
        }

        FITZEXCEPTION(lastLocation, !result)
        CLOSECHECK0(lastLocation, """Id (chapter, page) of last page.""")
        %pythoncode%{@property%}
        PyObject *lastLocation()
        {
            fz_document *this_doc = (fz_document *) $self;
            fz_location last_loc;
            fz_try(gctx) {
                last_loc = fz_last_page(gctx, this_doc);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return Py_BuildValue("ii", last_loc.chapter, last_loc.page);
        }


        FITZEXCEPTION(chapterPageCount, !result)
        CLOSECHECK0(chapterPageCount, """Page count of chapter.""")
        PyObject *chapterPageCount(int chapter)
        {
            int pages = 0;
            fz_try(gctx) {
                int chapters = fz_count_chapters(gctx, (fz_document *) $self);
                if (chapter < 0 || chapter >= chapters)
                    THROWMSG(gctx, "bad chapter number");
                pages = fz_count_chapter_pages(gctx, (fz_document *) $self, chapter);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return Py_BuildValue("i", pages);
        }

        FITZEXCEPTION(previousLocation, !result)
        %pythonprepend previousLocation %{
        """Get (chapter, page) of previous page."""
        if self.isClosed or self.isEncrypted:
            raise ValueError("document closed or encrypted")
        if type(page_id) is int:
            page_id = (0, page_id)
        if page_id not in self:
            raise ValueError("page id not in document")
        if page_id  == (0, 0):
            return ()
        %}
        PyObject *previousLocation(PyObject *page_id)
        {
            fz_document *this_doc = (fz_document *) $self;
            fz_location prev_loc, loc;
            PyObject *val;
            int pno;
            fz_try(gctx) {
                val = PySequence_GetItem(page_id, 0);
                if (!val) THROWMSG(gctx, "bad page id");
                int chapter = (int) PyLong_AsLong(val);
                Py_DECREF(val);
                if (PyErr_Occurred()) THROWMSG(gctx, "bad page id");

                val = PySequence_GetItem(page_id, 1);
                if (!val) THROWMSG(gctx, "bad page id");
                pno = (int) PyLong_AsLong(val);
                Py_DECREF(val);
                if (PyErr_Occurred()) THROWMSG(gctx, "bad page id");

                loc = fz_make_location(chapter, pno);
                prev_loc = fz_previous_page(gctx, this_doc, loc);
            }
            fz_catch(gctx) {
                PyErr_Clear();
                return NULL;
            }
            return Py_BuildValue("ii", prev_loc.chapter, prev_loc.page);
        }


        FITZEXCEPTION(nextLocation, !result)
        %pythonprepend nextLocation %{
        """Get (chapter, page) of next page."""
        if self.isClosed or self.isEncrypted:
            raise ValueError("document closed or encrypted")
        if type(page_id) is int:
            page_id = (0, page_id)
        if page_id not in self:
            raise ValueError("page id not in document")
        if tuple(page_id)  == self.lastLocation:
            return ()
        %}
        PyObject *nextLocation(PyObject *page_id)
        {
            fz_document *this_doc = (fz_document *) $self;
            fz_location next_loc, loc;
            int page_n = -1;
            PyObject *val;
            int pno;
            fz_try(gctx) {
                val = PySequence_GetItem(page_id, 0);
                if (!val) THROWMSG(gctx, "bad page id");
                int chapter = (int) PyLong_AsLong(val);
                Py_DECREF(val);
                if (PyErr_Occurred()) THROWMSG(gctx, "bad page id");

                val = PySequence_GetItem(page_id, 1);
                if (!val) THROWMSG(gctx, "bad page id");
                pno = (int) PyLong_AsLong(val);
                Py_DECREF(val);
                if (PyErr_Occurred()) THROWMSG(gctx, "bad page id");

                loc = fz_make_location(chapter, pno);
                next_loc = fz_next_page(gctx, this_doc, loc);
            }
            fz_catch(gctx) {
                PyErr_Clear();
                return NULL;
            }
            return Py_BuildValue("ii", next_loc.chapter, next_loc.page);
        }


        FITZEXCEPTION(location_from_page_number, !result)
        CLOSECHECK0(location_from_page_number, """Convert pno to (chapter, page).""")
        PyObject *location_from_page_number(int pno)
        {
            fz_document *this_doc = (fz_document *) $self;
            fz_location loc = fz_make_location(-1, -1);
            int pageCount = fz_count_pages(gctx, this_doc);
            while (pno < 0) pno += pageCount;
            fz_try(gctx) {
                if (pno >= pageCount)
                    THROWMSG(gctx, "bad page number(s)");
                loc = fz_location_from_page_number(gctx, this_doc, pno);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return Py_BuildValue("ii", loc.chapter, loc.page);
        }

        FITZEXCEPTION(page_number_from_location, !result)
        %pythonprepend page_number_from_location%{
        """Convert (chapter, pno) to page number."""
        if type(page_id) is int:
            np = self.pageCount
            while page_id < 0:
                page_id += np
            page_id = (0, page_id)
        if page_id not in self:
            raise ValueError("page id not in document")
        %}
        PyObject *page_number_from_location(PyObject *page_id)
        {
            fz_document *this_doc = (fz_document *) $self;
            fz_location loc;
            int page_n = -1;
            PyObject *val;
            int pno;
            fz_try(gctx) {
                val = PySequence_GetItem(page_id, 0);
                if (!val) THROWMSG(gctx, "bad page id");
                int chapter = (int) PyLong_AsLong(val);
                Py_DECREF(val);
                if (PyErr_Occurred()) THROWMSG(gctx, "bad page id");

                val = PySequence_GetItem(page_id, 1);
                if (!val) THROWMSG(gctx, "bad page id");
                pno = (int) PyLong_AsLong(val);
                Py_DECREF(val);
                if (PyErr_Occurred()) THROWMSG(gctx, "bad page id");

                loc = fz_make_location(chapter, pno);
                page_n = fz_page_number_from_location(gctx, this_doc, loc);
            }
            fz_catch(gctx) {
                PyErr_Clear();
                return NULL;
            }
            return Py_BuildValue("i", page_n);
        }

        CLOSECHECK0(_getMetadata, """Get metadata.""")
        char *_getMetadata(const char *key)
        {
            PyObject *res;
            fz_document *doc = (fz_document *) $self;
            int vsize;
            char *value;
            vsize = fz_lookup_metadata(gctx, doc, key, NULL, 0)+1;
            if(vsize > 1) {
                value = JM_Alloc(char, vsize);
                fz_lookup_metadata(gctx, doc, key, value, vsize);
                res = PyString_FromString(value);
                PyMem_Del(value);
            }
            return res;
        }

        CLOSECHECK0(needsPass, """Indicate password required.""")
        %pythoncode%{@property%}
        PyObject *needsPass() {
            return JM_BOOL(fz_needs_password(gctx, (fz_document *) $self));
        }

        %pythoncode%{@property%}
        CLOSECHECK0(language, """Document language.""")
        PyObject *language()
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            if (!pdf) return_none;
            fz_text_language lang = pdf_document_language(gctx, pdf);
            char buf[8];
            if (lang == FZ_LANG_UNSET) return_none;
            return Py_BuildValue("s", fz_string_from_text_language(buf, lang));
        }

        FITZEXCEPTION(setLanguage, !result)
        PyObject *setLanguage(char *language=NULL)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                fz_text_language lang;
                if (!language)
                    lang = FZ_LANG_UNSET;
                else
                    lang = fz_text_language_from_string(language);
                pdf_set_document_language(gctx, pdf, lang);
            }
            fz_catch(gctx) {
                return NULL;
            }
            Py_RETURN_TRUE;
        }


        %pythonprepend resolveLink %{
        """Calculate internal link destination.

        Args:
            uri: (str) some Link.uri
            chapters: (bool) whether to use (chapter, page) format
        Returns:
            (page_id, x, y) where x, y are point coordinates on the page.
            page_id is either page number (if chapters=0), or (chapter, pno).
        """
        %}
        PyObject *resolveLink(char *uri=NULL, int chapters=0)
        {
            if (!uri) {
                if (chapters) return Py_BuildValue("(ii)ff", -1, -1, 0, 0);
                return Py_BuildValue("iff", -1, 0, 0);
            }
            fz_document *this_doc = (fz_document *) $self;
            float xp = 0, yp = 0;
            fz_location loc = {0, 0};
            fz_try(gctx) {
                loc = fz_resolve_link(gctx, (fz_document *) $self, uri, &xp, &yp);
            }
            fz_catch(gctx) {
                if (chapters) return Py_BuildValue("(ii)ff", -1, -1, 0, 0);
                return Py_BuildValue("iff", -1, 0, 0);
            }
            if (chapters)
                return Py_BuildValue("(ii)ff", loc.chapter, loc.page, xp, yp);
            int pno = fz_page_number_from_location(gctx, this_doc, loc);
            return Py_BuildValue("iff", pno, xp, yp);
        }

        FITZEXCEPTION(layout, !result)
        CLOSECHECK(layout, """Re-layout a reflowable document.""")
        %pythonappend layout %{
            self._reset_page_refs()
            self.initData()%}
        PyObject *layout(PyObject *rect = NULL, float width = 0, float height = 0, float fontsize = 11)
        {
            fz_document *doc = (fz_document *) $self;
            if (!fz_is_document_reflowable(gctx, doc)) return_none;
            fz_try(gctx) {
                float w = width, h = height;
                fz_rect r = JM_rect_from_py(rect);
                if (!fz_is_infinite_rect(r)) {
                    w = r.x1 - r.x0;
                    h = r.y1 - r.y0;
                }
                if (w <= 0.0f || h <= 0.0f)
                        THROWMSG(gctx, "invalid page size");
                fz_layout_document(gctx, doc, w, h, fontsize);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        FITZEXCEPTION(makeBookmark, !result)
        CLOSECHECK(makeBookmark, """Make a page pointer before layouting document.""")
        PyObject *makeBookmark(PyObject *loc)
        {
            fz_document *doc = (fz_document *) $self;
            fz_location location;
            fz_bookmark mark;
            fz_try(gctx) {
                if (JM_INT_ITEM(loc, 0, &location.chapter) == 1)
                    THROWMSG(gctx, "Bad location");
                if (JM_INT_ITEM(loc, 1, &location.page) == 1)
                    THROWMSG(gctx, "Bad location");
                mark = fz_make_bookmark(gctx, doc, location);
                if (!mark) THROWMSG(gctx, "Bad location");
            }
            fz_catch(gctx) {
                return NULL;
            }
            return PyLong_FromVoidPtr((void *) mark);
        }


        FITZEXCEPTION(findBookmark, !result)
        CLOSECHECK(findBookmark, """Find new location after layouting a document.""")
        PyObject *findBookmark(PyObject *bm)
        {
            fz_document *doc = (fz_document *) $self;
            fz_location location;
            fz_try(gctx) {
                intptr_t mark = (intptr_t) PyLong_AsVoidPtr(bm);
                location = fz_lookup_bookmark(gctx, doc, mark);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return Py_BuildValue("ii", location.chapter, location.page);
        }


        CLOSECHECK0(isReflowable, """Check if document is layoutable.""")
        %pythoncode%{@property%}
        PyObject *isReflowable()
        {
            return JM_BOOL(fz_is_document_reflowable(gctx, (fz_document *) $self));
        }

        FITZEXCEPTION(_deleteObject, !result)
        CLOSECHECK0(_deleteObject, """Delete object.""")
        PyObject *_deleteObject(int xref)
        {
            fz_document *doc = (fz_document *) $self;
            pdf_document *pdf = pdf_specifics(gctx, doc);
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                if (!INRANGE(xref, 1, pdf_xref_len(gctx, pdf)-1))
                    THROWMSG(gctx, "bad xref");
                pdf_delete_object(gctx, pdf, xref);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        CLOSECHECK0(_getPDFroot, """Get xref of PDF catalog.""")
        PyObject *_getPDFroot()
        {
            fz_document *doc = (fz_document *) $self;
            pdf_document *pdf = pdf_specifics(gctx, doc);
            int xref = 0;
            if (!pdf) return Py_BuildValue("i", xref);
            fz_try(gctx) {
                pdf_obj *root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf),
                                             PDF_NAME(Root));
                xref = pdf_to_num(gctx, root);
            }
            fz_catch(gctx) {;}
            return Py_BuildValue("i", xref);
        }

        CLOSECHECK0(_getPDFfileid, """Get PDF file id.""")
        PyObject *_getPDFfileid()
        {
            fz_document *doc = (fz_document *) $self;
            pdf_document *pdf = pdf_specifics(gctx, doc);
            if (!pdf) return_none;
            PyObject *idlist = PyList_New(0);
            fz_buffer *buffer = NULL;
            unsigned char *hex;
            pdf_obj *o;
            int n, i, len;
            PyObject *bytes;

            fz_try(gctx) {
                pdf_obj *identity = pdf_dict_get(gctx, pdf_trailer(gctx, pdf),
                                             PDF_NAME(ID));
                if (identity)
                {
                    n = pdf_array_len(gctx, identity);
                    for (i = 0; i < n; i++)
                    {
                        o = pdf_array_get(gctx, identity, i);
                        len = (int) pdf_to_str_len(gctx, o);
                        buffer = fz_new_buffer(gctx, 2 * len);
                        fz_buffer_storage(gctx, buffer, &hex);
                        hexlify(len, (unsigned char *) pdf_to_text_string(gctx, o), hex);
                        LIST_APPEND_DROP(idlist, JM_UnicodeFromStr(hex));
                        Py_CLEAR(bytes);
                        fz_drop_buffer(gctx, buffer);
                        buffer = NULL;
                    }
                }
            }
            fz_catch(gctx) fz_drop_buffer(gctx, buffer);
            return idlist;
        }

        CLOSECHECK0(isPDF, """Check for PDF.""")
        %pythoncode%{@property%}
        PyObject *isPDF()
        {
            if (pdf_specifics(gctx, (fz_document *) $self)) Py_RETURN_TRUE;
            else Py_RETURN_FALSE;
        }

        CLOSECHECK0(_hasXrefStream, """Check if xref table is a stream.""")
        %pythoncode%{@property%}
        PyObject *_hasXrefStream()
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            if (!pdf) Py_RETURN_FALSE;
            if (pdf->has_xref_streams) Py_RETURN_TRUE;
            Py_RETURN_FALSE;
        }

        CLOSECHECK0(_hasXrefOldStyle, """Check if xref table is old style.""")
        %pythoncode%{@property%}
        PyObject *_hasXrefOldStyle()
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            if (!pdf) Py_RETURN_FALSE;
            if (pdf->has_old_style_xrefs) Py_RETURN_TRUE;
            Py_RETURN_FALSE;
        }

        CLOSECHECK0(isDirty, """True if PDF has unsaved changes.""")
        %pythoncode%{@property%}
        PyObject *isDirty()
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            if (!pdf) Py_RETURN_FALSE;
            return JM_BOOL(pdf_has_unsaved_changes(gctx, pdf));
        }

        CLOSECHECK0(can_save_incrementally, """Check whether incremental saves are possible.""")
        PyObject *can_save_incrementally()
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, (fz_document *) $self);
            if (!pdf) Py_RETURN_FALSE; // gracefully handle non-PDF
            return JM_BOOL(pdf_can_be_saved_incrementally(gctx, pdf));
        }

        CLOSECHECK0(isRepaired, """Check whether PDF was repaired.""")
        %pythoncode%{@property%}
        PyObject *isRepaired()
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, (fz_document *) $self);
            if (!pdf) Py_RETURN_FALSE; // gracefully handle non-PDF
            return JM_BOOL(pdf_was_repaired(gctx, pdf));
        }

        CLOSECHECK0(authenticate, """Decrypt document.""")
        %pythonappend authenticate %{
        if val:  # the doc is decrypted successfully and we init the outline
            self.isEncrypted = False
            self.initData()
            self.thisown = True
        %}
        PyObject *authenticate(char *password)
        {
            return Py_BuildValue("i", fz_authenticate_password(gctx, (fz_document *) $self, (const char *) password));
        }

        //------------------------------------------------------------------
        // save PDF file
        //------------------------------------------------------------------
        FITZEXCEPTION(save, !result)
        %pythonprepend save %{
        """Save PDF to filename."""
        if self.isClosed or self.isEncrypted:
            raise ValueError("document closed or encrypted")
        if type(filename) == str:
            pass
        elif str is bytes and type(filename) == unicode:
            filename = filename.encode('utf8')
        else:
            filename = str(filename)
        if filename == self.name and not incremental:
            raise ValueError("save to original must be incremental")
        if self.pageCount < 1:
            raise ValueError("cannot save with zero pages")
        if incremental:
            if self.name != filename or self.stream:
                raise ValueError("incremental needs original file")
        %}

        PyObject *
        save(char *filename, int garbage=0, int clean=0,
            int deflate=0, int deflate_images=0, int deflate_fonts=0,
            int incremental=0, int ascii=0, int expand=0, int linear=0,
            int pretty=0, int encryption=1, int permissions=-1,
            char *owner_pw=NULL, char *user_pw=NULL)
        {
            pdf_write_options opts = pdf_default_write_options;
            opts.do_incremental     = incremental;
            opts.do_ascii           = ascii;
            opts.do_compress        = deflate;
            opts.do_compress_images = deflate_images;
            opts.do_compress_fonts  = deflate_fonts;
            opts.do_decompress      = expand;
            opts.do_garbage         = garbage;
            opts.do_pretty          = pretty;
            opts.do_linear          = linear;
            opts.do_clean           = clean;
            opts.do_sanitize        = clean;
            opts.do_encrypt         = encryption;
            opts.permissions        = permissions;
            if (owner_pw) {
                memcpy(&opts.opwd_utf8, owner_pw, strlen(owner_pw)+1);
            } else if (user_pw) {
                memcpy(&opts.opwd_utf8, user_pw, strlen(user_pw)+1);
            }
            if (user_pw) {
                memcpy(&opts.upwd_utf8, user_pw, strlen(user_pw)+1);
            }

            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                JM_embedded_clean(gctx, pdf);
                JM_ensure_identity(gctx, pdf);
                pdf_save_document(gctx, pdf, filename, &opts);
                pdf->dirty = 0;
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        //------------------------------------------------------------------
        // write document to memory
        //------------------------------------------------------------------
        FITZEXCEPTION(write, !result)
        %pythonprepend write %{
        """Write the PDF to a bytes object."""
        if self.isClosed or self.isEncrypted:
            raise ValueError("document closed or encrypted")
        if self.pageCount < 1:
            raise ValueError("cannot write with zero pages")%}

        PyObject *
        write(int garbage=0, int clean=0,
            int deflate=0, int deflate_images=0, int deflate_fonts=0,
            int ascii=0, int expand=0, int pretty=0, int encryption=1,
            int permissions=-1, char *owner_pw=NULL, char *user_pw=NULL)
        {
            PyObject *r = NULL;
            fz_output *out = NULL;
            fz_buffer *res = NULL;
            pdf_write_options opts = pdf_default_write_options;
            opts.do_incremental     = 0;
            opts.do_ascii           = ascii;
            opts.do_compress        = deflate;
            opts.do_compress_images = deflate_images;
            opts.do_compress_fonts  = deflate_fonts;
            opts.do_decompress      = expand;
            opts.do_garbage         = garbage;
            opts.do_linear          = 0;
            opts.do_clean           = clean;
            opts.do_sanitize        = clean;
            opts.do_pretty          = pretty;
            opts.do_encrypt         = encryption;
            opts.permissions        = permissions;
            if (owner_pw) {
                memcpy(&opts.opwd_utf8, owner_pw, strlen(owner_pw)+1);
            } else if (user_pw) {
                memcpy(&opts.opwd_utf8, user_pw, strlen(user_pw)+1);
            }
            if (user_pw) {
                memcpy(&opts.upwd_utf8, user_pw, strlen(user_pw)+1);
            }

            fz_document *doc = (fz_document *) $self;
            pdf_document *pdf = pdf_specifics(gctx, doc);
            fz_var(out);
            fz_var(r);
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                if (pdf_count_pages(gctx, pdf) < 1)
                    THROWMSG(gctx, "cannot save with zero pages");
                JM_embedded_clean(gctx, pdf);
                JM_ensure_identity(gctx, pdf);
                res = fz_new_buffer(gctx, 8192);
                out = fz_new_output_with_buffer(gctx, res);
                pdf_write_document(gctx, pdf, out, &opts);
                r = JM_BinFromBuffer(gctx, res);
                pdf->dirty = 0;
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, res);
                fz_drop_output(gctx, out);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return r;
        }

        //---------------------------------------------------------------------
        // Insert pages from a source PDF into this PDF.
        // For reconstructing the links (_do_links method), we must save the
        // insertion point (start_at) if it was specified as -1.
        //---------------------------------------------------------------------
        FITZEXCEPTION(insertPDF, !result)
        %pythonprepend insertPDF %{
        """Insert a page range from another PDF.

        Args:
            docsrc: PDF to copy from. Must be different object, but may be same file.
            from_page: (int) first source page to copy, 0-based, default 0.
            to_page: (int) last source page to copy, 0-based, default last page.
            start_at: (int) from_page will become this page number in target.
            rotate: (int) rotate copied pages, default -1 is no change.
            links: (int/bool) whether to also copy links.
            annots: (int/bool) whether to also copy annotations.
            show_progress: (int) progress message interval, 0 is no messages.
            final: (bool) indicates last insertion from this source PDF.
            _gmap: internal use only

        Copy sequence will reversed if from_page > to_page."""

        if self.isClosed or self.isEncrypted:
            raise ValueError("document closed or encrypted")
        if self._graft_id == docsrc._graft_id:
            raise ValueError("source and target cannot be same object")
        sa = start_at
        if sa < 0:
            sa = self.pageCount
        if len(docsrc) > show_progress > 0:
            inname = os.path.basename(docsrc.name)
            if not inname:
                inname = "memory PDF"
            outname = os.path.basename(self.name)
            if not outname:
                outname = "memory PDF"
            print("Inserting '%s' at '%s'" % (inname, outname))

        # retrieve / make a Graftmap to avoid duplicate objects
        isrt = docsrc._graft_id
        _gmap = self.Graftmaps.get(isrt, None)
        if _gmap is None:
            _gmap = Graftmap(self)
            self.Graftmaps[isrt] = _gmap
        %}

        %pythonappend insertPDF %{
        self._reset_page_refs()
        if links:
            self._do_links(docsrc, from_page = from_page, to_page = to_page,
                        start_at = sa)
        if final == 1:
            self.Graftmaps[isrt] = None%}

        PyObject *
        insertPDF(struct Document *docsrc,
            int from_page=-1,
            int to_page=-1,
            int start_at=-1,
            int rotate=-1,
            int links=1,
            int annots=1,
            int show_progress=0,
            int final = 1,
            struct Graftmap *_gmap=NULL)
        {
            fz_document *doc = (fz_document *) $self;
            pdf_document *pdfout = pdf_specifics(gctx, doc);
            pdf_document *pdfsrc = pdf_specifics(gctx, (fz_document *) docsrc);
            int outCount = fz_count_pages(gctx, doc);
            int srcCount = fz_count_pages(gctx, (fz_document *) docsrc);

            // local copies of page numbers
            int fp = from_page, tp = to_page, sa = start_at;

            // normalize page numbers
            fp = MAX(fp, 0);                // -1 = first page
            fp = MIN(fp, srcCount - 1);     // but do not exceed last page

            if (tp < 0) tp = srcCount - 1;  // -1 = last page
            tp = MIN(tp, srcCount - 1);     // but do not exceed last page

            if (sa < 0) sa = outCount;      // -1 = behind last page
            sa = MIN(sa, outCount);         // but that is also the limit

            fz_try(gctx) {
                if (!pdfout || !pdfsrc) THROWMSG(gctx, "source or target not a PDF");
                JM_merge_range(gctx, pdfout, pdfsrc, fp, tp, sa, rotate, links, annots, show_progress, (pdf_graft_map *) _gmap);
            }
            fz_catch(gctx) {
                return NULL;
            }
            pdfout->dirty = 1;
            return_none;
        }

        //------------------------------------------------------------------
        // Create and insert a new page (PDF)
        //------------------------------------------------------------------
        FITZEXCEPTION(_newPage, !result)
        CLOSECHECK(_newPage, """Make a new PDF page.""")
        %pythonappend _newPage %{self._reset_page_refs()%}
        PyObject *_newPage(int pno=-1, float width=595, float height=842)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            fz_rect mediabox = fz_unit_rect;
            mediabox.x1 = width;
            mediabox.y1 = height;
            pdf_obj *resources = NULL, *page_obj = NULL;
            fz_buffer *contents = NULL;
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                if (pno < -1) THROWMSG(gctx, "bad page number(s)");
                // create /Resources and /Contents objects
                resources = pdf_add_object_drop(gctx, pdf, pdf_new_dict(gctx, pdf, 1));
                page_obj = pdf_add_page(gctx, pdf, mediabox, 0, resources, contents);
                pdf_insert_page(gctx, pdf, pno, page_obj);
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, contents);
                pdf_drop_obj(gctx, page_obj);
            }
            fz_catch(gctx) {
                return NULL;
            }
            pdf->dirty = 1;
            return_none;
        }

        //------------------------------------------------------------------
        // Create sub-document to keep only selected pages.
        // Parameter is a Python sequence of the wanted page numbers.
        //------------------------------------------------------------------
        FITZEXCEPTION(select, !result)
        %pythonprepend select %{"""Build sub-pdf with page numbers in the list."""
if self.isClosed or self.isEncrypted:
    raise ValueError("document closed or encrypted")
if not self.isPDF:
    raise ValueError("not a PDF")
if not hasattr(pyliste, "__getitem__"):
    raise ValueError("sequence required")
if len(pyliste) == 0 or min(pyliste) not in range(len(self)) or max(pyliste) not in range(len(self)):
    raise ValueError("bad page number(s)")%}
        %pythonappend select %{self._reset_page_refs()%}
        PyObject *select(PyObject *pyliste)
        {
            // preparatory stuff:
            // (1) get underlying pdf document,
            // (2) transform Python list into integer array

            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            fz_try(gctx) {
                // call retainpages (code copy of fz_clean_file.c)
                globals glo = {0};
                glo.ctx = gctx;
                glo.doc = pdf;
                retainpages(gctx, &glo, pyliste);
                if (pdf->rev_page_map)
                {
                    pdf_drop_page_tree(gctx, pdf);
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            pdf->dirty = 1;
            return_none;
        }

        //------------------------------------------------------------------
        // remove one page
        //------------------------------------------------------------------
        FITZEXCEPTION(_deletePage, !result)
        PyObject *_deletePage(int pno)
        {
            fz_try(gctx) {
                fz_document *doc = (fz_document *) $self;
                pdf_document *pdf = pdf_specifics(gctx, doc);
                pdf_delete_page(gctx, pdf, pno);
                if (pdf->rev_page_map)
                {
                    pdf_drop_page_tree(gctx, pdf);
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        //------------------------------------------------------------------
        // get document permissions
        //------------------------------------------------------------------
        %pythoncode%{@property%}
        %pythonprepend permissions %{
        """Document permissions."""

        if self.isEncrypted:
            return 0
        %}
        PyObject *permissions()
        {
            fz_document *doc = (fz_document *) $self;
            pdf_document *pdf = pdf_document_from_fz_document(gctx, doc);

            // for PDF return result of standard function
            if (pdf)
                return Py_BuildValue("i", pdf_document_permissions(gctx, pdf));

            // otherwise simulate the PDF return value
            int perm = (int) 0xFFFFFFFC;  // all permissions granted
            // now switch off where needed
            if (!fz_has_permission(gctx, doc, FZ_PERMISSION_PRINT))
                perm = perm ^ PDF_PERM_PRINT;
            if (!fz_has_permission(gctx, doc, FZ_PERMISSION_EDIT))
                perm = perm ^ PDF_PERM_MODIFY;
            if (!fz_has_permission(gctx, doc, FZ_PERMISSION_COPY))
                perm = perm ^ PDF_PERM_COPY;
            if (!fz_has_permission(gctx, doc, FZ_PERMISSION_ANNOTATE))
                perm = perm ^ PDF_PERM_ANNOTATE;
            return Py_BuildValue("i", perm);
        }

        FITZEXCEPTION(_getCharWidths, !result)
        CLOSECHECK(_getCharWidths, """Return list of glyphs and glyph widths of a font.""")
        PyObject *_getCharWidths(int xref, char *bfname, char *ext,
                                 int ordering, int limit, int idx = 0)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            PyObject *wlist = NULL;
            int i, glyph, mylimit;
            mylimit = limit;
            if (mylimit < 256) mylimit = 256;
            int cwlen = 0;
            int lang = 0;
            const unsigned char *data;
            int size, index;
            fz_font *font = NULL, *fb_font= NULL;
            fz_buffer *buf = NULL;

            fz_try(gctx) {
                ASSERT_PDF(pdf);
                if (ordering >= 0) {
                    data = fz_lookup_cjk_font(gctx, ordering, &size, &index);
                    font = fz_new_font_from_memory(gctx, NULL, data, size, index, 0);
                    goto weiter;
                }
                data = fz_lookup_base14_font(gctx, bfname, &size);
                if (data) {
                    font = fz_new_font_from_memory(gctx, bfname, data, size, 0, 0);
                    goto weiter;
                }
                buf = JM_get_fontbuffer(gctx, pdf, xref);
                if (!buf) {
                    fz_throw(gctx, FZ_ERROR_GENERIC, "font at xref %d is not supported", xref);
                }
                font = fz_new_font_from_buffer(gctx, NULL, buf, idx, 0);

                weiter:;
                wlist = PyList_New(0);
                float adv;
                for (i = 0; i < mylimit; i++)
                {
                    glyph = fz_encode_character(gctx, font, i);
                    adv = fz_advance_glyph(gctx, font, glyph, 0);
                    if (ordering >= 0)
                        glyph = i;


                    if (glyph > 0)
                    {
                        LIST_APPEND_DROP(wlist, Py_BuildValue("if", glyph, adv));
                    }
                    else
                    {
                        LIST_APPEND_DROP(wlist, Py_BuildValue("if", glyph, 0.0));
                    }
                }
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, buf);
                fz_drop_font(gctx, font);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return wlist;
        }


        FITZEXCEPTION(_getPageObjNumber, !result)
        CLOSECHECK0(_getPageObjNumber, """Get (xref, generation) of page number.""")
        PyObject *_getPageObjNumber(int pno)
        {
            fz_document *this_doc = (fz_document *) $self;
            int pageCount = fz_count_pages(gctx, this_doc);
            int n = pno;
            while (n < 0) n += pageCount;
            pdf_obj *pageref = NULL;
            fz_var(pageref);
            pdf_document *pdf = pdf_specifics(gctx, this_doc);
            fz_try(gctx) {
                if (n >= pageCount) THROWMSG(gctx, "bad page number(s)");
                ASSERT_PDF(pdf);
                pageref = pdf_lookup_page_obj(gctx, pdf, n);
            }
            fz_catch(gctx) {
                return NULL;
            }

            return Py_BuildValue("ii", pdf_to_num(gctx, pageref),
                                       pdf_to_gen(gctx, pageref));
        }


        FITZEXCEPTION(pageCropBox, !result)
        CLOSECHECK0(pageCropBox, """Get CropBox of page number (without loading page).""")
        %pythonappend pageCropBox %{val = Rect(val)%}
        PyObject *pageCropBox(int pno)
        {
            fz_document *this_doc = (fz_document *) $self;
            int pageCount = fz_count_pages(gctx, this_doc);
            int n = pno;
            while (n < 0) n += pageCount;
            pdf_obj *pageref = NULL;
            fz_var(pageref);
            pdf_document *pdf = pdf_specifics(gctx, this_doc);
            fz_try(gctx) {
                if (n >= pageCount) THROWMSG(gctx, "bad page number(s)");
                ASSERT_PDF(pdf);
                pageref = pdf_lookup_page_obj(gctx, pdf, n);
            }
            fz_catch(gctx) {
                return NULL;
            }

            fz_rect cropbox = JM_cropbox(gctx, pageref);
            return JM_py_from_rect(cropbox);
        }


        FITZEXCEPTION(_getPageInfo, !result)
        CLOSECHECK(_getPageInfo, """List fonts, images, XObjects used on a page.""")
        PyObject *_getPageInfo(int pno, int what)
        {
            fz_document *doc = (fz_document *) $self;
            pdf_document *pdf = pdf_specifics(gctx, doc);
            pdf_obj *pageref, *rsrc;
            PyObject *liste = NULL, *tracer = NULL;
            fz_var(liste);
            fz_var(tracer);
            fz_try(gctx) {
                int pageCount = fz_count_pages(gctx, doc);
                int n = pno;  // pno < 0 is allowed
                while (n < 0) n += pageCount;  // make it non-negative
                if (n >= pageCount) THROWMSG(gctx, "bad page number(s)");
                ASSERT_PDF(pdf);
                pageref = pdf_lookup_page_obj(gctx, pdf, n);
                rsrc = pdf_dict_get_inheritable(gctx,
                           pageref, PDF_NAME(Resources));
                liste = PyList_New(0);
                tracer = PyList_New(0);
                if (rsrc) {
                    JM_scan_resources(gctx, pdf, rsrc, liste, what, 0, tracer);
                }
            }
            fz_always(gctx) {
                Py_DECREF(tracer);
            }
            fz_catch(gctx) {
                Py_XDECREF(liste);
                return NULL;
            }
            return liste;
        }

        FITZEXCEPTION(extractFont, !result)
        CLOSECHECK(extractFont, """Get a font by xref.""")
        PyObject *extractFont(int xref = 0, int info_only = 0)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);

            fz_try(gctx) {
                ASSERT_PDF(pdf);
            }
            fz_catch(gctx) {
                return NULL;
            }

            fz_buffer *buffer = NULL;
            pdf_obj *obj, *basefont, *bname;
            PyObject *bytes = PyBytes_FromString("");
            char *ext = NULL;
            char *fontname = NULL;
            PyObject *nulltuple = Py_BuildValue("sssO", "", "", "", bytes);
            PyObject *tuple;
            Py_ssize_t len = 0;
            fz_try(gctx) {
                obj = pdf_load_object(gctx, pdf, xref);
                pdf_obj *type = pdf_dict_get(gctx, obj, PDF_NAME(Type));
                pdf_obj *subtype = pdf_dict_get(gctx, obj, PDF_NAME(Subtype));
                if(pdf_name_eq(gctx, type, PDF_NAME(Font)) &&
                   strncmp(pdf_to_name(gctx, subtype), "CIDFontType", 11) != 0)
                {
                    basefont = pdf_dict_get(gctx, obj, PDF_NAME(BaseFont));
                    if (!basefont || pdf_is_null(gctx, basefont))
                        bname = pdf_dict_get(gctx, obj, PDF_NAME(Name));
                    else
                        bname = basefont;
                    ext = JM_get_fontextension(gctx, pdf, xref);
                    if (strcmp(ext, "n/a") != 0 && !info_only)
                    {
                        buffer = JM_get_fontbuffer(gctx, pdf, xref);
                        bytes = JM_BinFromBuffer(gctx, buffer);
                        fz_drop_buffer(gctx, buffer);
                    }
                    tuple = PyTuple_New(4);
                    PyTuple_SET_ITEM(tuple, 0, JM_EscapeStrFromStr(pdf_to_name(gctx, bname)));
                    PyTuple_SET_ITEM(tuple, 1, JM_UnicodeFromStr(ext));
                    PyTuple_SET_ITEM(tuple, 2, JM_UnicodeFromStr(pdf_to_name(gctx, subtype)));
                    PyTuple_SET_ITEM(tuple, 3, bytes);
                }
                else
                {
                    tuple = nulltuple;
                }
            }
            fz_always(gctx) {
                JM_PyErr_Clear;
                JM_Free(fontname);
            }
            fz_catch(gctx)
            {
                tuple = Py_BuildValue("sssO", "invalid-name", "", "", bytes);
            }
            return tuple;
        }


        FITZEXCEPTION(extractImage, !result)
        CLOSECHECK(extractImage, """Get image by xref.""")
        PyObject *extractImage(int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            pdf_obj *obj = NULL;
            fz_buffer *res = NULL;
            fz_image *img = NULL;
            PyObject *rc = NULL;
            const char *ext = NULL;
            const char *cs_name = NULL;
            int img_type = 0, xres, yres, colorspace;
            int smask = 0, width, height, bpc;
            fz_compressed_buffer *cbuf = NULL;
            fz_var(img);
            fz_var(res);
            fz_var(obj);

            fz_try(gctx) {
                ASSERT_PDF(pdf);
                if (!INRANGE(xref, 1, pdf_xref_len(gctx, pdf)-1))
                    THROWMSG(gctx, "bad xref");

                obj = pdf_new_indirect(gctx, pdf, xref, 0);
                pdf_obj *subtype = pdf_dict_get(gctx, obj, PDF_NAME(Subtype));

                if (!pdf_name_eq(gctx, subtype, PDF_NAME(Image)))
                    THROWMSG(gctx, "not an image");

                pdf_obj *o = pdf_dict_get(gctx, obj, PDF_NAME(SMask));
                if (o) smask = pdf_to_num(gctx, o);

                o = pdf_dict_get(gctx, obj, PDF_NAME(Mask));
                if (o) smask = pdf_to_num(gctx, o);
                if (pdf_is_jpx_image(gctx, obj)) {
                    img_type = FZ_IMAGE_JPX;
                    ext = "jpx";
                }
                if (JM_is_jbig2_image(gctx, obj)) {
                    img_type = FZ_IMAGE_JBIG2;
                    ext = "jb2";
                }
                res = pdf_load_raw_stream(gctx, obj);
                if (img_type == FZ_IMAGE_UNKNOWN) {
                    unsigned char *c = NULL;
                    fz_buffer_storage(gctx, res, &c);
                    img_type = fz_recognize_image_format(gctx, c);
                    ext = JM_image_extension(img_type);
                }
                if (img_type == FZ_IMAGE_UNKNOWN) {
                    fz_drop_buffer(gctx, res);
                    res = NULL;
                    img = pdf_load_image(gctx, pdf, obj);
                    res = fz_new_buffer_from_image_as_png(gctx, img,
                                fz_default_color_params);
                    ext = "png";
                } else /*if (smask == 0)*/ {
                    img = fz_new_image_from_buffer(gctx, res);
                }
                /*
                            else {
                                fz_drop_buffer(gctx, res);
                                res = NULL;
                                img = pdf_load_image(gctx, pdf, obj);
                                cbuf = fz_compressed_image_buffer(gctx, img);
                                if (!cbuf) {
                                    res = fz_new_buffer_from_image_as_png(gctx, img,
                                                    fz_default_color_params);
                                    ext = "png";
                                } else {
                                    res = cbuf->buffer;
                                    img_type = cbuf->params.type;
                                    ext = JM_image_extension(img_type);
                                }
                            }
                */
                fz_image_resolution(img, &xres, &yres);
                width = img->w;
                height = img->h;
                colorspace = img->n;
                bpc = img->bpc;
                cs_name = fz_colorspace_name(gctx, img->colorspace);

                rc = PyDict_New();
                DICT_SETITEM_DROP(rc, dictkey_ext,
                                    JM_UnicodeFromStr(ext));
                DICT_SETITEM_DROP(rc, dictkey_smask,
                                    Py_BuildValue("i", smask));
                DICT_SETITEM_DROP(rc, dictkey_width,
                                    Py_BuildValue("i", width));
                DICT_SETITEM_DROP(rc, dictkey_height,
                                    Py_BuildValue("i", height));
                DICT_SETITEM_DROP(rc, dictkey_colorspace,
                                    Py_BuildValue("i", colorspace));
                DICT_SETITEM_DROP(rc, dictkey_bpc,
                                    Py_BuildValue("i", bpc));
                DICT_SETITEM_DROP(rc, dictkey_xres,
                                    Py_BuildValue("i", xres));
                DICT_SETITEM_DROP(rc, dictkey_yres,
                                    Py_BuildValue("i", yres));
                DICT_SETITEM_DROP(rc, dictkey_cs_name,
                                    JM_UnicodeFromStr(cs_name));
                DICT_SETITEM_DROP(rc, dictkey_image,
                                    JM_BinFromBuffer(gctx, res));
            }
            fz_always(gctx) {
                fz_drop_image(gctx, img);
                if (!cbuf) fz_drop_buffer(gctx, res);
                pdf_drop_obj(gctx, obj);
            }

            fz_catch(gctx)
            {
                Py_CLEAR(rc);
                return_none;
            }
            if (!rc)
                return_none;
            return rc;
        }


        //------------------------------------------------------------------
        // Delete all bookmarks (table of contents)
        // returns list of deleted (now available) xref numbers
        //------------------------------------------------------------------
        CLOSECHECK(_delToC, """Delete the TOC.""")
        %pythonappend _delToC %{self.initData()%}
        PyObject *_delToC()
        {
            PyObject *xrefs = PyList_New(0);          // create Python list
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            if (!pdf) return xrefs;                   // not a pdf

            pdf_obj *root, *olroot, *first;
            int xref_count, olroot_xref, i, xref;

            // get the main root
            root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Root));
            // get the outline root
            olroot = pdf_dict_get(gctx, root, PDF_NAME(Outlines));
            if (!olroot) return xrefs;                // no outlines or some problem

            first = pdf_dict_get(gctx, olroot, PDF_NAME(First)); // first outline

            xrefs = JM_outline_xrefs(gctx, first, xrefs);
            xref_count = (int) PyList_Size(xrefs);

            olroot_xref = pdf_to_num(gctx, olroot);        // delete OL root
            pdf_delete_object(gctx, pdf, olroot_xref);     // delete OL root
            pdf_dict_del(gctx, root, PDF_NAME(Outlines));  // delete OL root

            for (i = 0; i < xref_count; i++)
            {
                xref = (int) PyInt_AsLong(PyList_GetItem(xrefs, i));
                pdf_delete_object(gctx, pdf, xref);      // delete outline item
            }
            LIST_APPEND_DROP(xrefs, Py_BuildValue("i", olroot_xref));
            pdf->dirty = 1;
            return xrefs;
        }

        //------------------------------------------------------------------
        // Return outline xref by index.
        // Performs a linear search
        //------------------------------------------------------------------
        CLOSECHECK0(outlineXref, """Get outline xref by index.""")
        int outlineXref(int index)
        {
            if (index < 0) return 0;  // nonsense call
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            if (!pdf) return 0;  // only works for PDF
            // get the main root
            pdf_obj *root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Root));
            // get the outline root
            pdf_obj *olroot = pdf_dict_get(gctx, root, PDF_NAME(Outlines));
            if (!olroot) return 0;  // no outlines / some problem
            // first outline
            pdf_obj *first = pdf_dict_get(gctx, olroot, PDF_NAME(First));
            if (!first) return 0;
            return JM_outline_xref(gctx, first, index);
        }

        //------------------------------------------------------------------
        // Check: is xref a stream object?
        //------------------------------------------------------------------
        CLOSECHECK0(isStream, """Check if xref is a stream object.""")
        PyObject *isStream(int xref=0)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            if (!pdf) Py_RETURN_FALSE;  // not a PDF
            return JM_BOOL(pdf_obj_num_is_stream(gctx, pdf, xref));
        }

        //------------------------------------------------------------------
        // Return or set NeedAppearances
        //------------------------------------------------------------------
        %pythonprepend need_appearances
%{"""Get/set the NeedAppearances value."""
if self.isClosed:
    raise ValueError("document closed")
if not self.isFormPDF:
    return None
%}
        PyObject *need_appearances(PyObject *value=NULL)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            int oldval = -1;
            pdf_obj *app = NULL;
            char appkey[] = "NeedAppearances";
            fz_try(gctx) {
                pdf_obj *form = pdf_dict_getp(gctx, pdf_trailer(gctx, pdf),
                                "Root/AcroForm");
                app = pdf_dict_gets(gctx, form, appkey);
                if (pdf_is_bool(gctx, app)) {
                    oldval = pdf_to_bool(gctx, app);
                }

                if (EXISTS(value)) {
                    pdf_dict_puts_drop(gctx, form, appkey, PDF_TRUE);
                } else if (value == Py_False) {
                    pdf_dict_puts_drop(gctx, form, appkey, PDF_FALSE);
                }
            }
            fz_catch(gctx) {
                return_none;
            }
            if (value != Py_None) {
                return value;
            }
            if (oldval >= 0) {
                return JM_BOOL(oldval);
            }
            return_none;
        }

        //------------------------------------------------------------------
        // Return the /SigFlags value
        //------------------------------------------------------------------
        CLOSECHECK0(getSigFlags, """Get the /SigFlags value.""")
        int getSigFlags()
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            if (!pdf) return -1;  // not a PDF
            int sigflag = -1;
            fz_try(gctx) {
                pdf_obj *sigflags = pdf_dict_getl(gctx,
                                        pdf_trailer(gctx, pdf),
                                        PDF_NAME(Root),
                                        PDF_NAME(AcroForm),
                                        PDF_NAME(SigFlags),
                                        NULL);
                if (sigflags) {
                    sigflag = (int) pdf_to_int(gctx, sigflags);
                }
            }
            fz_catch(gctx) {
                return -1;  // any problem
            }
            return sigflag;
        }

        //------------------------------------------------------------------
        // Check: is this an AcroForm with at least one field?
        //------------------------------------------------------------------
        CLOSECHECK0(isFormPDF, """Check if PDF Form document.""")
        %pythoncode%{@property%}
        PyObject *isFormPDF()
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            if (!pdf) Py_RETURN_FALSE;  // not a PDF
            int count = -1;  // init count
            fz_try(gctx) {
                pdf_obj *fields = pdf_dict_getl(gctx,
                                                pdf_trailer(gctx, pdf),
                                                PDF_NAME(Root),
                                                PDF_NAME(AcroForm),
                                                PDF_NAME(Fields),
                                                NULL);
                if (pdf_is_array(gctx, fields)) {
                    count = pdf_array_len(gctx, fields);
                }
            }
            fz_catch(gctx) {
                Py_RETURN_FALSE;
            }
            if (count >= 0) {
                return Py_BuildValue("i", count);
            } else {
                Py_RETURN_FALSE;
            }
        }

        //------------------------------------------------------------------
        // Return the list of field font resource names
        //------------------------------------------------------------------
        CLOSECHECK0(FormFonts, """Get list of field font resource names.""")
        %pythoncode%{@property%}
        PyObject *FormFonts()
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            if (!pdf) return_none;           // not a PDF
            pdf_obj *fonts = NULL;
            PyObject *liste = PyList_New(0);
            fz_var(liste);
            fz_try(gctx) {
                fonts = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Root), PDF_NAME(AcroForm), PDF_NAME(DR), PDF_NAME(Font), NULL);
                if (fonts && pdf_is_dict(gctx, fonts))       // fonts exist
                {
                    int i, n = pdf_dict_len(gctx, fonts);
                    for (i = 0; i < n; i++)
                    {
                        pdf_obj *f = pdf_dict_get_key(gctx, fonts, i);
                        LIST_APPEND_DROP(liste, JM_UnicodeFromStr(pdf_to_name(gctx, f)));
                    }
                }
            }
            fz_catch(gctx) {
                Py_DECREF(liste);
                return_none;  // any problem yields None
            }
            return liste;
        }

        //------------------------------------------------------------------
        // Add a field font
        //------------------------------------------------------------------
        FITZEXCEPTION(_addFormFont, !result)
        CLOSECHECK(_addFormFont, """Add new form font.""")
        PyObject *_addFormFont(char *name, char *font)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            if (!pdf) return_none;  // not a PDF
            pdf_obj *fonts = NULL;
            fz_try(gctx) {
                fonts = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Root),
                             PDF_NAME(AcroForm), PDF_NAME(DR), PDF_NAME(Font), NULL);
                if (!fonts || !pdf_is_dict(gctx, fonts))
                    THROWMSG(gctx, "PDF has no form fonts yet");
                pdf_obj *k = pdf_new_name(gctx, (const char *) name);
                pdf_obj *v = JM_pdf_obj_from_str(gctx, pdf, font);
                pdf_dict_put(gctx, fonts, k, v);
            }
            fz_catch(gctx) NULL;
            return_none;
        }

        //------------------------------------------------------------------
        // Get Xref Number of Outline Root, create it if missing
        //------------------------------------------------------------------
        FITZEXCEPTION(_getOLRootNumber, !result)
        CLOSECHECK(_getOLRootNumber, """Get xref of Outline Root, create it if missing.""")
        PyObject *_getOLRootNumber()
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            pdf_obj *root, *olroot, *ind_obj;
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                // get main root
                root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Root));
                // get outline root
                olroot = pdf_dict_get(gctx, root, PDF_NAME(Outlines));
                if (!olroot)
                {
                    olroot = pdf_new_dict(gctx, pdf, 4);
                    pdf_dict_put(gctx, olroot, PDF_NAME(Type), PDF_NAME(Outlines));
                    ind_obj = pdf_add_object(gctx, pdf, olroot);
                    pdf_dict_put(gctx, root, PDF_NAME(Outlines), ind_obj);
                    olroot = pdf_dict_get(gctx, root, PDF_NAME(Outlines));
                    pdf_drop_obj(gctx, ind_obj);
                    pdf->dirty = 1;
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            return Py_BuildValue("i", pdf_to_num(gctx, olroot));
        }

        //------------------------------------------------------------------
        // Get a new Xref number
        //------------------------------------------------------------------
        FITZEXCEPTION(_getNewXref, !result)
        CLOSECHECK(_getNewXref, """Make new xref.""")
        PyObject *_getNewXref()
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            fz_try(gctx) {
                ASSERT_PDF(pdf);
            }
            fz_catch(gctx) {
                return NULL;
            }
            pdf->dirty = 1;
            return Py_BuildValue("i", pdf_create_object(gctx, pdf));
        }

        //------------------------------------------------------------------
        // Get Length of Xref
        //------------------------------------------------------------------
        CLOSECHECK0(_getXrefLength, """Get length of xref table.""")
        PyObject *_getXrefLength()
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            int xreflen = 0;
            if (pdf) xreflen = pdf_xref_len(gctx, pdf);
            return Py_BuildValue("i", xreflen);
        }

        //------------------------------------------------------------------
        // Get XML Metadata
        //------------------------------------------------------------------
        CLOSECHECK0(getXmlMetadata, """Get document XML metadata.""")
        PyObject *getXmlMetadata()
        {
            PyObject *rc = NULL;
            fz_buffer *buff = NULL;
            pdf_obj *xml = NULL;
            fz_try(gctx) {
                pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
                if (pdf) {
                    xml = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Root), PDF_NAME(Metadata), NULL);
                }
                if (xml) {
                    buff = pdf_load_stream(gctx, xml);
                    rc = JM_UnicodeFromBuffer(gctx, buff);
                } else {
                    rc = EMPTY_STRING;
                }
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, buff);
                PyErr_Clear();
            }
            fz_catch(gctx) {
                return EMPTY_STRING;
            }
            return rc;
        }

        //------------------------------------------------------------------
        // Get XML Metadata xref
        //------------------------------------------------------------------
        CLOSECHECK0(_getXmlMetadataXref, """Get xref of document XML metadata.""")
        PyObject *_getXmlMetadataXref()
        {
            int xref = 0;
            fz_try(gctx) {
                pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
                ASSERT_PDF(pdf);
                pdf_obj *root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Root));
                if (!root) THROWMSG(gctx, "PDF has no root");
                pdf_obj *xml = pdf_dict_get(gctx, root, PDF_NAME(Metadata));
                if (xml) xref = pdf_to_num(gctx, xml);
            }
            fz_catch(gctx) {;}
            return Py_BuildValue("i", xref);
        }

        //------------------------------------------------------------------
        // Delete XML Metadata
        //------------------------------------------------------------------
        FITZEXCEPTION(_delXmlMetadata, !result)
        CLOSECHECK(_delXmlMetadata, """Delete XML metadata.""")
        PyObject *_delXmlMetadata()
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                pdf_obj *root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Root));
                if (root) pdf_dict_del(gctx, root, PDF_NAME(Metadata));
            }
            fz_catch(gctx) {
                return NULL;
            }
            pdf->dirty = 1;
            return_none;
        }

        //------------------------------------------------------------------
        // Set XML-based Metadata
        //------------------------------------------------------------------
        FITZEXCEPTION(setXmlMetadata, !result)
        CLOSECHECK(setXmlMetadata, """Store XML metadata.""")
        PyObject *setXmlMetadata(char *metadata)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            fz_buffer *res = NULL;
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                pdf_obj *root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Root));
                if (!root) THROWMSG(gctx, "PDF has no root");
                res = fz_new_buffer_from_copied_data(gctx, (const unsigned char *) metadata, strlen(metadata));
                pdf_obj *xml = pdf_dict_get(gctx, root, PDF_NAME(Metadata));
                if (xml) {
                    JM_update_stream(gctx, pdf, xml, res, 0);
                } else {
                    xml = pdf_add_stream(gctx, pdf, res, NULL, 0);
                    pdf_dict_put(gctx, xml, PDF_NAME(Type), PDF_NAME(Metadata));
                    pdf_dict_put(gctx, xml, PDF_NAME(Subtype), PDF_NAME(XML));
                    pdf_dict_put_drop(gctx, root, PDF_NAME(Metadata), xml);
                }
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) {
                return NULL;
            }
            pdf->dirty = 1;
            return_none;
        }

        //------------------------------------------------------------------
        // Get Object String of xref
        //------------------------------------------------------------------
        FITZEXCEPTION(_getXrefString, !result)
        CLOSECHECK0(_getXrefString, """Get xref object source as a string.""")
        PyObject *_getXrefString(int xref, int compressed=0, int ascii=0)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            pdf_obj *obj = NULL;
            PyObject *text = NULL;
            
            fz_buffer *res=NULL;
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if (!INRANGE(xref, 1, xreflen-1))
                    THROWMSG(gctx, "bad xref");
                obj = pdf_load_object(gctx, pdf, xref);
                res = JM_object_to_buffer(gctx, pdf_resolve_indirect(gctx, obj), compressed, ascii);
                text = JM_EscapeStrFromBuffer(gctx, res);
            }
            fz_always(gctx) {
                pdf_drop_obj(gctx, obj);
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) return EMPTY_STRING;
            return text;
        }

        //------------------------------------------------------------------
        // Get String of PDF trailer
        //------------------------------------------------------------------
        FITZEXCEPTION(_getTrailerString, !result)
        CLOSECHECK0(_getTrailerString, """Get PDF trailer as a string.""")
        PyObject *_getTrailerString(int compressed=0, int ascii=0)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            if (!pdf) return_none;
            PyObject *text = NULL;
            fz_buffer *res=NULL;
            fz_try(gctx) {
                res = JM_object_to_buffer(gctx, pdf_trailer(gctx, pdf), compressed, ascii);
                text = JM_EscapeStrFromBuffer(gctx, res);
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) {
                return PyUnicode_FromString("PDF trailer damaged");
            }
            return text;
        }

        //------------------------------------------------------------------
        // Get compressed stream of an object by xref
        // return_none if not stream
        //------------------------------------------------------------------
        FITZEXCEPTION(_getXrefStreamRaw, !result)
        CLOSECHECK(_getXrefStreamRaw, """Get xref stream without decompression.""")
        PyObject *_getXrefStreamRaw(int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            PyObject *r = Py_None;
            pdf_obj *obj = NULL;
            fz_var(obj);
            fz_buffer *res = NULL;
            fz_var(res);
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if (!INRANGE(xref, 1, xreflen-1))
                    THROWMSG(gctx, "bad xref");
                obj = pdf_new_indirect(gctx, pdf, xref, 0);
                if (pdf_is_stream(gctx, obj))
                {
                    res = pdf_load_raw_stream_number(gctx, pdf, xref);
                    r = JM_BinFromBuffer(gctx, res);
                }
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, res);
                pdf_drop_obj(gctx, obj);
            }
            fz_catch(gctx)
            {
                Py_CLEAR(r);
                return NULL;
            }
            return r;
        }

        //------------------------------------------------------------------
        // Get decompressed stream of an object by xref
        // return_none if not stream
        //------------------------------------------------------------------
        FITZEXCEPTION(_getXrefStream, !result)
        CLOSECHECK(_getXrefStream, """Get decompressed xref stream.""")
        PyObject *_getXrefStream(int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            PyObject *r = Py_None;
            pdf_obj *obj = NULL;
            fz_var(obj);
            fz_buffer *res = NULL;
            fz_var(res);
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if (!INRANGE(xref, 1, xreflen-1))
                    THROWMSG(gctx, "bad xref");
                obj = pdf_new_indirect(gctx, pdf, xref, 0);
                if (pdf_is_stream(gctx, obj))
                {
                    res = pdf_load_stream_number(gctx, pdf, xref);
                    r = JM_BinFromBuffer(gctx, res);
                }
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, res);
                pdf_drop_obj(gctx, obj);
            }
            fz_catch(gctx)
            {
                Py_CLEAR(r);
                return NULL;
            }
            return r;
        }

        //------------------------------------------------------------------
        // Update an Xref number with a new object given as a string
        //------------------------------------------------------------------
        FITZEXCEPTION(_updateObject, !result)
        CLOSECHECK(_updateObject, """Replace object definition source.""")
        PyObject *_updateObject(int xref, char *text, struct Page *page = NULL)
        {
            pdf_obj *new_obj;
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if (!INRANGE(xref, 1, xreflen-1))
                    THROWMSG(gctx, "bad xref");
                // create new object with passed-in string
                new_obj = JM_pdf_obj_from_str(gctx, pdf, text);
                pdf_update_object(gctx, pdf, xref, new_obj);
                pdf_drop_obj(gctx, new_obj);
                if (page)
                    JM_refresh_link_table(gctx, pdf_page_from_fz_page(gctx, (fz_page *)page));
            }
            fz_catch(gctx) {
                return NULL;
            }
            pdf->dirty = 1;
            return_none;
        }

        //------------------------------------------------------------------
        // Update a stream identified by its xref
        //------------------------------------------------------------------
        FITZEXCEPTION(_updateStream, !result)
        CLOSECHECK(_updateStream, """Replace xref stream part.""")
        PyObject *_updateStream(int xref = 0, PyObject *stream = NULL, int new = 0)
        {
            pdf_obj *obj = NULL;
            fz_var(obj);
            fz_buffer *res = NULL;
            fz_var(res);
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if (!INRANGE(xref, 1, xreflen-1))
                    THROWMSG(gctx, "bad xref");
                // get the object
                obj = pdf_new_indirect(gctx, pdf, xref, 0);
                if (!new && !pdf_is_stream(gctx, obj))
                    THROWMSG(gctx, "no stream object at xref");
                res = JM_BufferFromBytes(gctx, stream);
                if (!res) THROWMSG(gctx, "bad type: 'stream'");
                JM_update_stream(gctx, pdf, obj, res, 1);

            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, res);
                pdf_drop_obj(gctx, obj);
            }
            fz_catch(gctx)
                return NULL;
            pdf->dirty = 1;
            return_none;
        }

        //------------------------------------------------------------------
        // Add or update metadata based on provided raw string
        //------------------------------------------------------------------
        FITZEXCEPTION(_setMetadata, !result)
        CLOSECHECK(_setMetadata, """Set old style metadata.""")
        PyObject *_setMetadata(char *text)
        {
            pdf_obj *info, *new_info, *new_info_ind;
            int info_num = 0;               // will contain xref no of info object
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                // create new /Info object based on passed-in string
                new_info = JM_pdf_obj_from_str(gctx, pdf, text);
            }
            fz_catch(gctx) {
                return NULL;
            }
            pdf->dirty = 1;
            // replace existing /Info object
            info = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Info));
            if (info)
            {
                info_num = pdf_to_num(gctx, info);    // get xref no of old info
                pdf_update_object(gctx, pdf, info_num, new_info);  // insert new
                pdf_drop_obj(gctx, new_info);
                return_none;
            }
            // create new indirect object from /Info object
            new_info_ind = pdf_add_object(gctx, pdf, new_info);
            // put this in the trailer dictionary
            pdf_dict_put_drop(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Info), new_info_ind);
            return_none;
        }

        //------------------------------------------------------------------
        // create / refresh the page map
        //------------------------------------------------------------------
        FITZEXCEPTION(_make_page_map, !result)
        CLOSECHECK0(_make_page_map, """Make an array page number -> page object.""")
        PyObject *_make_page_map()
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            if (!pdf) return_none;
            fz_try(gctx) {
                pdf_drop_page_tree(gctx, pdf);
                pdf_load_page_tree(gctx, pdf);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return Py_BuildValue("i", pdf->rev_page_count);
        }


        //------------------------------------------------------------------
        // full (deep) copy of one page
        //------------------------------------------------------------------
        FITZEXCEPTION(fullcopyPage, !result)
        CLOSECHECK0(fullcopyPage, """Make full page duplication.""")
        %pythonappend fullcopyPage %{self._reset_page_refs()%}
        PyObject *fullcopyPage(int pno, int to = -1)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            int pageCount = pdf_count_pages(gctx, pdf);
            fz_buffer *res = NULL, *nres=NULL;
            pdf_obj *page2 = NULL;
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                if (!INRANGE(pno, 0, pageCount - 1) ||
                    !INRANGE(to, -1, pageCount - 1))
                    THROWMSG(gctx, "bad page number(s)");

                pdf_obj *page1 = pdf_resolve_indirect(gctx,
                                 pdf_lookup_page_obj(gctx, pdf, pno));

                pdf_obj *page2 = pdf_deep_copy_obj(gctx, page1);
                pdf_obj *old_annots = pdf_dict_get(gctx, page2, PDF_NAME(Annots));

                // copy annotations, but remove Popup and IRT types
                if (old_annots) {
                    int i, n = pdf_array_len(gctx, old_annots);
                    pdf_obj *new_annots = pdf_new_array(gctx, pdf, n);
                    for (i = 0; i < n; i++) {
                        pdf_obj *o = pdf_array_get(gctx, old_annots, i);
                        pdf_obj *subtype = pdf_dict_get(gctx, o, PDF_NAME(Subtype));
                        if (pdf_name_eq(gctx, subtype, PDF_NAME(Popup))) continue;
                        if (pdf_dict_gets(gctx, o, "IRT")) continue;
                        pdf_obj *copy_o = pdf_deep_copy_obj(gctx,
                                            pdf_resolve_indirect(gctx, o));
                        int xref = pdf_create_object(gctx, pdf);
                        pdf_update_object(gctx, pdf, xref, copy_o);
                        pdf_drop_obj(gctx, copy_o);
                        copy_o = pdf_new_indirect(gctx, pdf, xref, 0);
                        pdf_dict_del(gctx, copy_o, PDF_NAME(Popup));
                        pdf_dict_del(gctx, copy_o, PDF_NAME(P));
                        pdf_array_push_drop(gctx, new_annots, copy_o);
                    }
                pdf_dict_put_drop(gctx, page2, PDF_NAME(Annots), new_annots);
                }

                // copy the old contents stream(s)
                res = JM_read_contents(gctx, page1);

                // create new /Contents object for page2
                if (res) {
                    pdf_obj *contents = pdf_add_stream(gctx, pdf,
                               fz_new_buffer_from_copied_data(gctx, "  ", 1), NULL, 0);
                    JM_update_stream(gctx, pdf, contents, res, 1);
                    pdf_dict_put_drop(gctx, page2, PDF_NAME(Contents), contents);
                }

                // now insert target page, making sure it is an indirect object
                int xref = pdf_create_object(gctx, pdf);  // get new xref
                pdf_update_object(gctx, pdf, xref, page2);  // store new page
                pdf_drop_obj(gctx, page2);  // give up this object for now

                page2 = pdf_new_indirect(gctx, pdf, xref, 0);  // reread object
                pdf_insert_page(gctx, pdf, to, page2);  // and store the page
                pdf_drop_obj(gctx, page2);
            }
            fz_always(gctx) {
                pdf_drop_page_tree(gctx, pdf);
                fz_drop_buffer(gctx, res);
                fz_drop_buffer(gctx, nres);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }


        //------------------------------------------------------------------
        // move or copy one page
        //------------------------------------------------------------------
        FITZEXCEPTION(_move_copy_page, !result)
        CLOSECHECK0(_move_copy_page, """Move or copy a PDF page reference.""")
        %pythonappend _move_copy_page %{self._reset_page_refs()%}
        PyObject *_move_copy_page(int pno, int nb, int before, int copy)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            int i1, i2, pos, count, same = 0;
            pdf_obj *parent1 = NULL, *parent2 = NULL, *parent = NULL;
            pdf_obj *kids1, *kids2;
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                // get the two page objects -----------------------------------
                // locate the /Kids arrays and indices in each
                pdf_obj *page1 = pdf_lookup_page_loc(gctx, pdf, pno, &parent1, &i1);
                kids1 = pdf_dict_get(gctx, parent1, PDF_NAME(Kids));

                pdf_obj *page2 = pdf_lookup_page_loc(gctx, pdf, nb, &parent2, &i2);
                kids2 = pdf_dict_get(gctx, parent2, PDF_NAME(Kids));

                if (before)  // calc index of source page in target /Kids
                    pos = i2;
                else
                    pos = i2 + 1;

                // same /Kids array? ------------------------------------------
                same = pdf_objcmp(gctx, kids1, kids2);

                // put source page in target /Kids array ----------------------
                if (!copy && same != 0)  // update parent in page object
                {
                    pdf_dict_put(gctx, page1, PDF_NAME(Parent), parent2);
                }
                pdf_array_insert(gctx, kids2, page1, pos);

                if (same != 0) // different /Kids arrays ----------------------
                {
                    parent = parent2;
                    while (parent)  // increase /Count objects in parents
                    {
                        count = pdf_dict_get_int(gctx, parent, PDF_NAME(Count));
                        pdf_dict_put_int(gctx, parent, PDF_NAME(Count), count + 1);
                        parent = pdf_dict_get(gctx, parent, PDF_NAME(Parent));
                    }
                    if (!copy)  // delete original item
                    {
                        pdf_array_delete(gctx, kids1, i1);
                        parent = parent1;
                        while (parent) // decrease /Count objects in parents
                        {
                            count = pdf_dict_get_int(gctx, parent, PDF_NAME(Count));
                            pdf_dict_put_int(gctx, parent, PDF_NAME(Count), count - 1);
                            parent = pdf_dict_get(gctx, parent, PDF_NAME(Parent));
                        }
                    }
                }
                else // same /Kids array --------------------------------------
                {
                    if (copy) // source page is copied
                    {
                        parent = parent2;
                        while (parent) // increase /Count object in parents
                        {
                            count = pdf_dict_get_int(gctx, parent, PDF_NAME(Count));
                            pdf_dict_put_int(gctx, parent, PDF_NAME(Count), count + 1);
                            parent = pdf_dict_get(gctx, parent, PDF_NAME(Parent));
                        }
                    }
                    else
                    {
                        if (i1 < pos)
                            pdf_array_delete(gctx, kids1, i1);
                        else
                            pdf_array_delete(gctx, kids1, i1 + 1);
                    }
                }
                if (pdf->rev_page_map)  // page map no longer valid: drop it
                {
                    pdf_drop_page_tree(gctx, pdf);
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        FITZEXCEPTION(_remove_toc_item, !result)
        PyObject *_remove_toc_item(int xref)
        {
            // "remove" bookmark by letting it point to nowhere
            pdf_obj *item = NULL;
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            fz_try(gctx) {
                item = pdf_new_indirect(gctx, pdf, xref, 0);
                pdf_dict_del(gctx, item, PDF_NAME(Dest));
                pdf_dict_del(gctx, item, PDF_NAME(A));
                pdf_dict_put_text_string(gctx, item, PDF_NAME(Title), "<>");
            }
            fz_always(gctx) {
                pdf_drop_obj(gctx, item);
            }
            fz_catch(gctx){
                return NULL;
            }
            return_none;
        }

        FITZEXCEPTION(_update_toc_item, !result)
        PyObject *_update_toc_item(int xref, char *action=NULL, char *title=NULL)
        {
            // "update" bookmark by letting it point to nowhere
            pdf_obj *item = NULL;
            pdf_obj *obj = NULL;
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) $self);
            fz_try(gctx) {
                item = pdf_new_indirect(gctx, pdf, xref, 0);
                if (title) {
                    pdf_dict_put_text_string(gctx, item, PDF_NAME(Title), title);
                }
                if (action) {
                    pdf_dict_del(gctx, item, PDF_NAME(Dest));
                    obj = JM_pdf_obj_from_str(gctx, pdf, action);
                    pdf_dict_put_drop(gctx, item, PDF_NAME(A), obj);
                }
            }
            fz_always(gctx) {
                pdf_drop_obj(gctx, item);
            }
            fz_catch(gctx){
                return NULL;
            }
            return_none;
        }

        //------------------------------------------------------------------
        // PDF Optional Content functions
        //------------------------------------------------------------------
        FITZEXCEPTION(layerConfigs, !result)
        CLOSECHECK0(layerConfigs, """Show optional content configurations.""")
        PyObject *layerConfigs()
        {
            PyObject *rc = NULL;
            pdf_layer_config info = {NULL, NULL};
            fz_try(gctx) {
                pdf_document *pdf = pdf_specifics(gctx, (fz_document *) self);
                ASSERT_PDF(pdf);
                int i, n = pdf_count_layer_configs(gctx, pdf);
                if (n == 1) {
                    pdf_obj *obj = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf),
                                   PDF_NAME(Root), PDF_NAME(OCProperties), PDF_NAME(Configs), NULL);
                    if (!pdf_is_array(gctx, obj)) n = 0;
                }
                rc = PyTuple_New(n);
                for (i = 0; i < n; i++) {
                    pdf_layer_config_info(gctx, pdf, i, &info);
                    PyObject *item = Py_BuildValue("{s:i,s:s,s:s}",
                        "number", i, "name", info.name, "creator", info.creator);
                    PyTuple_SET_ITEM(rc, i, item);
                    info.name = NULL;
                    info.creator = NULL;
                }
            }
            fz_catch(gctx) {
                Py_CLEAR(rc);
                return NULL;
            }
            return rc;
        }


        FITZEXCEPTION(setLayerConfig, !result)
        CLOSECHECK0(setLayerConfig, """Activate a optional content configuration.""")
        PyObject *setLayerConfig(int config, int as_default=0)
        {
            fz_try(gctx) {
                pdf_document *pdf = pdf_specifics(gctx, (fz_document *) self);
                ASSERT_PDF(pdf);
                pdf_obj *cfgs = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf),
                                   PDF_NAME(Root), PDF_NAME(OCProperties), PDF_NAME(Configs), NULL);
                if (!pdf_is_array(gctx, cfgs) || !pdf_array_len(gctx, cfgs)) {
                    if (config < 1) goto finished;
                    THROWMSG(gctx, "bad config number");
                }
                if (config < 0) goto finished;
                pdf_select_layer_config(gctx, pdf, config);
                if (as_default) {
                    pdf_set_layer_config_as_default(gctx, pdf);
                    pdf_read_ocg(gctx, pdf);
                }
                finished:;
            }
            fz_catch(gctx) {
                return NULL;
            }
            Py_RETURN_NONE;
        }


        FITZEXCEPTION(getOCStates, !result)
        CLOSECHECK0(getOCStates, """Content of ON, OFF, RBGroups of a configuration.""")
        PyObject *getOCStates(int config=-1)
        {
            PyObject *rc;
            pdf_obj *obj = NULL;
            fz_try(gctx) {
                pdf_document *pdf = pdf_specifics(gctx, (fz_document *) self);
                ASSERT_PDF(pdf);
                pdf_obj *ocp = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf),
                                   PDF_NAME(Root), PDF_NAME(OCProperties), NULL);
                if (!ocp) {
                    rc = Py_BuildValue("s", NULL);
                    goto finished;
                }
                if (config == -1) {
                    obj = pdf_dict_get(gctx, ocp, PDF_NAME(D));
                } else {
                    obj = pdf_array_get(gctx, pdf_dict_get(gctx, ocp, PDF_NAME(Configs)), config);
                }
                if (!obj) THROWMSG(gctx, "bad config number");
                rc = JM_get_ocg_arrays(gctx, obj);
                finished:;
            }
            fz_catch(gctx) {
                Py_CLEAR(rc);
                return NULL;
            }
            return rc;
        }


        FITZEXCEPTION(setOCStates, !result)
        %pythonprepend setOCStates %{"""Set ON, OFF, RBGroups of a configuration."""
if self.isClosed:
    raise ValueError("document closed")
if on is not None and type(on) not in (list, tuple):
        raise ValueError("bad type: 'on'")
if off is not None and type(off) not in (list, tuple):
        raise ValueError("bad type: 'off'")
if rbgroups is not None and type(rbgroups) not in (list, tuple):
        raise ValueError("bad type: 'rbgroups'")
if basestate is not None:
    basestate = basestate.upper()
    if basestate == "UNCHANGED":
        basestate = "Unchanged"
    if basestate not in ("ON", "OFF", "Unchanged"):
        raise ValueError("bad value: 'basestate'")
%}
        PyObject *
        setOCStates(int config, const char *basestate=NULL, PyObject *on=NULL,
                    PyObject *off=NULL, PyObject *rbgroups=NULL)
        {
            pdf_obj *obj = NULL;
            fz_try(gctx) {
                pdf_document *pdf = pdf_specifics(gctx, (fz_document *) self);
                ASSERT_PDF(pdf);
                pdf_obj *ocp = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf),
                                   PDF_NAME(Root), PDF_NAME(OCProperties), NULL);
                if (!ocp) {
                    goto finished;
                }
                if (config == -1) {
                    obj = pdf_dict_get(gctx, ocp, PDF_NAME(D));
                } else {
                    obj = pdf_array_get(gctx, pdf_dict_get(gctx, ocp, PDF_NAME(Configs)), config);
                }
                if (!obj) THROWMSG(gctx, "bad config number");
                JM_set_ocg_arrays(gctx, obj, basestate, on, off, rbgroups);
                pdf_read_ocg(gctx, pdf);
                finished:;
            }
            fz_catch(gctx) {
                return NULL;
            }
            Py_RETURN_NONE;
        }


        FITZEXCEPTION(addLayerConfig, !result)
        CLOSECHECK0(addLayerConfig, """Add new optional content configuration.""")
        PyObject *addLayerConfig(char *name, char *creator=NULL, PyObject *on=NULL)
        {
            fz_try(gctx) {
                pdf_document *pdf = pdf_specifics(gctx, (fz_document *) self);
                ASSERT_PDF(pdf);
                JM_add_layer_config(gctx, pdf, name, creator, on);
                pdf_read_ocg(gctx, pdf);
            }
            fz_catch(gctx) {
                return NULL;
            }
            Py_RETURN_NONE;
        }


        FITZEXCEPTION(layerUIConfigs, !result)
        CLOSECHECK0(layerUIConfigs, """Show OC visibility status modifyable by user.""")
        PyObject *layerUIConfigs()
        {
            typedef struct
            {
                const char *text;
                int depth;
                pdf_layer_config_ui_type type;
                int selected;
                int locked;
            } pdf_layer_config_ui;
            PyObject *rc = NULL;

            fz_try(gctx) {
                pdf_document *pdf = pdf_specifics(gctx, (fz_document *) self);
                ASSERT_PDF(pdf);
                pdf_layer_config_ui info;
                int i, n = pdf_count_layer_config_ui(gctx, pdf);
                rc = PyTuple_New(n);
                char *type = NULL;
                for (i = 0; i < n; i++) {
                    pdf_layer_config_ui_info(gctx, pdf, i, (void *) &info);
                    switch (info.type)
                    {
                        case (1): type = "checkbox"; break;
                        case (2): type = "radiobox"; break;
                        default: type = "label"; break;
                    }
                    PyObject *item = Py_BuildValue("{s:i,s:s,s:i,s:s,s:O,s:O}",
                        "number", i,
                        "text", info.text,
                        "depth", info.depth,
                        "type", type,
                        "on", JM_BOOL(info.selected),
                        "locked", JM_BOOL(info.locked));
                    PyTuple_SET_ITEM(rc, i, item);
                }
            }
            fz_catch(gctx) {
                Py_CLEAR(rc);
                return NULL;
            }
            return rc;
        }


        FITZEXCEPTION(setLayerUIConfig, !result)
        CLOSECHECK0(setLayerUIConfig, """Set / unset OC intent configuration.""")
        PyObject *setLayerUIConfig(int number, int action=0)
        {
            fz_try(gctx) {
                pdf_document *pdf = pdf_specifics(gctx, (fz_document *) self);
                ASSERT_PDF(pdf);
                switch (action)
                {
                    case (1):
                        pdf_toggle_layer_config_ui(gctx, pdf, number);
                        break;
                    case (2):
                        pdf_deselect_layer_config_ui(gctx, pdf, number);
                        break;
                    default:
                        pdf_select_layer_config_ui(gctx, pdf, number);
                        break;
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            Py_RETURN_NONE;
        }


        FITZEXCEPTION(getOCGs, !result)
        CLOSECHECK0(getOCGs, """Show existing optional content groups.""")
        PyObject *
        getOCGs()
        {
            PyObject *rc = NULL;
            pdf_obj *ci = pdf_new_name(gctx, "CreatorInfo");
            fz_try(gctx) {
                pdf_document *pdf = pdf_specifics(gctx, (fz_document *) self);
                ASSERT_PDF(pdf);
                pdf_obj *ocgs = pdf_dict_getl(gctx,
                                pdf_dict_get(gctx,
                                pdf_trailer(gctx, pdf), PDF_NAME(Root)),
                                PDF_NAME(OCProperties), PDF_NAME(OCGs), NULL);
                rc = PyDict_New();
                if (!pdf_is_array(gctx, ocgs)) goto fertig;
                int i, n = pdf_array_len(gctx, ocgs);
                for (i = 0; i < n; i++) {
                    pdf_obj *ocg = pdf_array_get(gctx, ocgs, i);
                    int xref = pdf_to_num(gctx, ocg);
                    const char *name = pdf_to_text_string(gctx, pdf_dict_get(gctx, ocg, PDF_NAME(Name)));
                    pdf_obj *obj = pdf_dict_getl(gctx, ocg, PDF_NAME(Usage), ci, PDF_NAME(Subtype), NULL);
                    const char *usage = NULL;
                    if (obj) usage = pdf_to_name(gctx, obj);
                    PyObject *intents = PyList_New(0);
                    pdf_obj *intent = pdf_dict_get(gctx, ocg, PDF_NAME(Intent));
                    if (intent) {
                        if (pdf_is_name(gctx, intent)) {
                            LIST_APPEND_DROP(intents, Py_BuildValue("s", pdf_to_name(gctx, intent)));
                        } else if (pdf_is_array(gctx, intent)) {
                            int j, m = pdf_array_len(gctx, intent);
                            for (j = 0; j < m; j++) {
                                pdf_obj *o = pdf_array_get(gctx, intent, j);
                                if (pdf_is_name(gctx, o))
                                    LIST_APPEND_DROP(intents, Py_BuildValue("s", pdf_to_name(gctx, o)));
                            }
                        }
                    }
                    pdf_ocg_descriptor *desc = pdf->ocg;
                    int hidden = pdf_is_hidden_ocg(gctx, desc, NULL, usage, ocg);
                    PyObject *item = Py_BuildValue("{s:s,s:O,s:O,s:s}",
                            "name", name,
                            "intent", intents,
                            "on", JM_BOOL(!hidden),
                            "usage", usage);
                    Py_DECREF(intents);
                    PyObject *temp = Py_BuildValue("i", xref);
                    DICT_SETITEM_DROP(rc, temp, item);
                    Py_DECREF(temp);
                }
                fertig:;
            }
            fz_always(gctx) {
                pdf_drop_obj(gctx, ci);
            }
            fz_catch(gctx) {
                Py_CLEAR(rc);
                return NULL;
            }
            return rc;
        }

        FITZEXCEPTION(addOCG, !result)
        CLOSECHECK0(addOCG, """Add new optional content group.""")
        PyObject *
        addOCG(char *name, int config=-1, int on=1, PyObject *intent=NULL, const char *usage=NULL)
        {
            PyObject *xref = NULL;
            pdf_obj *obj = NULL, *cfg = NULL;
            pdf_obj *indocg = NULL;
            fz_try(gctx) {
                pdf_document *pdf = pdf_specifics(gctx, (fz_document *) self);
                ASSERT_PDF(pdf);

                // ------------------------------
                // make the OCG
                // ------------------------------
                pdf_obj *ocg = pdf_add_new_dict(gctx, pdf, 3);
                pdf_dict_put(gctx, ocg, PDF_NAME(Type), PDF_NAME(OCG));
                pdf_dict_put_text_string(gctx, ocg, PDF_NAME(Name), name);
                pdf_obj *intents = pdf_dict_put_array(gctx, ocg, PDF_NAME(Intent), 2);
                if (!EXISTS(intent)) {
                    pdf_array_push(gctx, intents, PDF_NAME(View));
                } else if (!PyUnicode_Check(intent)) {
                    int i, n = PySequence_Size(intent);
                    for (i = 0; i < n; i++) {
                        PyObject *item = PySequence_ITEM(intent, i);
                        char *c = JM_Python_str_AsChar(item);
                        if (c) {
                            pdf_array_push(gctx, intents, pdf_new_name(gctx, c));
                            JM_Python_str_DelForPy3(c);
                        }
                        Py_DECREF(item);
                    }
                } else {
                    char *c = JM_Python_str_AsChar(intent);
                    if (c) {
                        pdf_array_push(gctx, intents, pdf_new_name(gctx, c));
                        JM_Python_str_DelForPy3(c);
                    }
                }
                pdf_obj *use_for = pdf_dict_put_dict(gctx, ocg, PDF_NAME(Usage), 3);
                pdf_obj *ci_name = pdf_new_name(gctx, "CreatorInfo");
                pdf_obj *cre_info = pdf_dict_put_dict(gctx, use_for, ci_name, 2);
                pdf_dict_put_text_string(gctx, cre_info, PDF_NAME(Creator), "PyMuPDF");
                if (usage) {
                    pdf_dict_put_name(gctx, cre_info, PDF_NAME(Subtype), usage);
                } else {
                    pdf_dict_put_name(gctx, cre_info, PDF_NAME(Subtype), "Artwork");
                }
                indocg = pdf_add_object(gctx, pdf, ocg);

                // ------------------------------
                // Insert OCG in the right config
                // ------------------------------
                pdf_obj *ocp = JM_ensure_ocproperties(gctx, pdf);
                obj = pdf_dict_get(gctx, ocp, PDF_NAME(OCGs));
                pdf_array_push(gctx, obj, indocg);

                if (config > -1) {
                    obj = pdf_dict_get(gctx, ocp, PDF_NAME(Configs));
                    if (!pdf_is_array(gctx, obj)) {
                        THROWMSG(gctx, "bad config number");
                    }
                    cfg = pdf_array_get(gctx, obj, config);
                    if (!cfg) {
                        THROWMSG(gctx, "bad config number");
                    }
                } else {
                    cfg = pdf_dict_get(gctx, ocp, PDF_NAME(D));
                }

                obj = pdf_dict_get(gctx, cfg, PDF_NAME(Order));
                if (!obj) {
                    obj = pdf_dict_put_array(gctx, cfg, PDF_NAME(Order), 1);
                }
                pdf_array_push(gctx, obj, indocg);
                if (on) {
                    obj = pdf_dict_get(gctx, cfg, PDF_NAME(ON));
                    if (!obj) {
                        obj = pdf_dict_put_array(gctx, cfg, PDF_NAME(ON), 1);
                    }
                } else {
                    obj = pdf_dict_get(gctx, cfg, PDF_NAME(OFF));
                    if (!obj) {
                        obj = pdf_dict_put_array(gctx, cfg, PDF_NAME(OFF), 1);
                    }
                }
                pdf_array_push(gctx, obj, indocg);
                pdf_read_ocg(gctx, pdf);
                xref = Py_BuildValue("i", pdf_to_num(gctx, indocg));
            }
            fz_always(gctx) {
                pdf_drop_obj(gctx, indocg);
            }
            fz_catch(gctx) {
                Py_CLEAR(xref);
                return NULL;
            }
            return xref;
        }


        //------------------------------------------------------------------
        // Initialize document: set outline and metadata properties
        //------------------------------------------------------------------
        %pythoncode %{
            def initData(self):
                if self.isEncrypted:
                    raise ValueError("cannot initData - document still encrypted")
                self._outline = self._loadOutline()
                self.metadata = dict([(k,self._getMetadata(v)) for k,v in {'format':'format', 'title':'info:Title', 'author':'info:Author','subject':'info:Subject', 'keywords':'info:Keywords','creator':'info:Creator', 'producer':'info:Producer', 'creationDate':'info:CreationDate', 'modDate':'info:ModDate'}.items()])
                self.metadata['encryption'] = None if self._getMetadata('encryption')=='None' else self._getMetadata('encryption')

            outline = property(lambda self: self._outline)
            _getPageXref = _getPageObjNumber


            def pageXref(self, pno):
                """Return the xref of page number pno."""
                return self._getPageObjNumber(pno)[0]


            def getPageFontList(self, pno, full=False):
                """Retrieve a list of fonts used on a page.
                """
                if self.isClosed or self.isEncrypted:
                    raise ValueError("document closed or encrypted")
                if not self.isPDF:
                    return ()
                val = self._getPageInfo(pno, 1)
                if full is False:
                    return [v[:-1] for v in val]
                return val


            def getPageImageList(self, pno, full=False):
                """Retrieve a list of images used on a page.
                """
                if self.isClosed or self.isEncrypted:
                    raise ValueError("document closed or encrypted")
                if not self.isPDF:
                    return ()
                val = self._getPageInfo(pno, 2)
                if full is False:
                    return [v[:-1] for v in val]
                return val


            def getPageXObjectList(self, pno):
                """Retrieve a list of XObjects used on a page.
                """
                if self.isClosed or self.isEncrypted:
                    raise ValueError("document closed or encrypted")
                if not self.isPDF:
                    return ()
                val = self._getPageInfo(pno, 3)
                return val


            def copyPage(self, pno, to=-1):
                """Copy a page within a PDF document.

                Args:
                    pno: source page number
                    to: put before this page, '-1' means after last page.
                """
                if self.isClosed:
                    raise ValueError("document closed")

                pageCount = len(self)
                if (
                    pno not in range(pageCount) or
                    to not in range(-1, pageCount)
                   ):
                    raise ValueError("bad page number(s)")
                before = 1
                copy = 1
                if to == -1:
                    to = pageCount - 1
                    before = 0

                return self._move_copy_page(pno, to, before, copy)

            def movePage(self, pno, to = -1):
                """Move a page within a PDF document.

                Args:
                    pno: source page number.
                    to: put before this page, '-1' means after last page.
                """
                if self.isClosed:
                    raise ValueError("document closed")

                pageCount = len(self)
                if (
                    pno not in range(pageCount) or
                    to not in range(-1, pageCount)
                   ):
                    raise ValueError("bad page number(s)")
                before = 1
                copy = 0
                if to == -1:
                    to = pageCount - 1
                    before = 0

                return self._move_copy_page(pno, to, before, copy)

            def deletePage(self, pno=-1):
                """ Delete one page from a PDF.
                """
                if not self.isPDF:
                    raise ValueError("not a PDF")
                if self.isClosed:
                    raise ValueError("document closed")

                pageCount = self.pageCount
                while pno < 0:
                    pno += pageCount

                if not pno in range(pageCount):
                    raise ValueError("bad page number(s)")

                # remove TOC bookmarks pointing to deleted page
                old_toc = self.getToC()
                for i, item in enumerate(old_toc):
                    if item[2] == pno + 1:
                        xref = self.outlineXref(i)
                        self._remove_toc_item(xref)

                self._remove_links_to(pno, pno)
                self._deletePage(pno)
                self._reset_page_refs()



            def deletePageRange(self, from_page = -1, to_page = -1):
                """Delete pages from a PDF.
                """
                if not self.isPDF:
                    raise ValueError("not a PDF")
                if self.isClosed:
                    raise ValueError("document closed")

                pageCount = self.pageCount  # page count of document
                f = from_page  # first page to delete
                t = to_page  # last page to delete
                while f < 0:
                    f += pageCount
                while t < 0:
                    t += pageCount
                if not f <= t < pageCount:
                    raise ValueError("bad page number(s)")

                old_toc = self.getToC()
                for i, item in enumerate(old_toc):
                    if f + 1 <= item[2] <= t + 1:
                        xref = self.outlineXref(i)
                        self._remove_toc_item(xref)

                self._remove_links_to(f, t)

                for i in range(t, f - 1, -1):  # delete pages, last to first
                    self._deletePage(i)

                self._reset_page_refs()


            def saveIncr(self):
                """ Save PDF incrementally"""
                return self.save(self.name, incremental=True, encryption=PDF_ENCRYPT_KEEP)


            def xrefLength(self):
                """Return the length of the xref table.
                """
                return self._getXrefLength()


            def get_pdf_object(self, xref, compressed=False, ascii=False):
                """Return the object definition of an xref.
                """
                return self._getXrefString(xref, compressed, ascii)


            def updateObject(self, xref, text, page=None):
                """Repleace the object at xref with text.

                Optionally reload a page.
                """
                return self._updateObject(xref, text, page=page)


            def xrefStream(self, xref):
                """Return the decompressed stream content of an xref.
                """
                return self._getXrefStream(xref)


            def xrefStreamRaw(self, xref):
                """ Return the raw stream content of an xref.
                """
                return self._getXrefStreamRaw(xref)


            def updateStream(self, xref, stream, new=False):
                """Repleace the stream at xref with stream (bytes).
                """
                return self._updateStream(xref, stream, new=new)


            def PDFTrailer(self, compressed=False, ascii=False):
                """Return the PDF trailer string.
                """
                return self._getTrailerString(compressed, ascii)


            def PDFCatalog(self):
                """Return the xref of the PDF catalog object.
                """
                return self._getPDFroot()


            def metadataXML(self):
                """Get xref of document XML metadata."""
                return self._getXmlMetadataXref()


            def reload_page(self, page):
                """Make a fresh copy of a page."""
                old_annots = {}  # copy annot references to here
                pno = page.number  # save the page number
                for k, v in page._annot_refs.items():  # save the annot dictionary
                    old_annots[k] = v
                page._erase()  # remove the page
                page = None
                page = self.loadPage(pno)  # reload the page

                # copy annot refs over to the new dictionary
                page_proxy = weakref.proxy(page)
                for k, v in old_annots.items():
                    annot = old_annots[k]
                    annot.parent = page_proxy  # refresh parent to new page
                    page._annot_refs[k] = annot
                return page


            xrefObject = get_pdf_object


            def __repr__(self):
                m = "closed " if self.isClosed else ""
                if self.stream is None:
                    if self.name == "":
                        return m + "Document(<new PDF, doc# %i>)" % self._graft_id
                    return m + "Document('%s')" % (self.name,)
                return m + "Document('%s', <memory, doc# %i>)" % (self.name, self._graft_id)


            def __contains__(self, loc):
                if type(loc) is int:
                    if loc < self.pageCount:
                        return True
                    return False
                if type(loc) not in (tuple, list) or len(loc) != 2:
                    return False

                chapter, pno = loc
                if (type(chapter) != int or
                    chapter < 0 or 
                    chapter >= self.chapterCount
                    ):
                    return False
                if (type(pno) != int or
                    pno < 0 or
                    pno >= self.chapterPageCount(chapter)
                    ):
                    return False

                return True


            def __getitem__(self, i=0):
                if i not in self:
                    raise IndexError("page not in document")
                return self.loadPage(i)

            def pages(self, start=None, stop=None, step=None):
                """Return a generator iterator over a page range.

                Arguments have the same meaning as for the range() built-in.
                """
                # set the start value
                start = start or 0
                while start < 0:
                    start += self.pageCount
                if start not in range(self.pageCount):
                    raise ValueError("bad start page number")

                # set the stop value
                stop = stop if stop is not None and stop <= self.pageCount else self.pageCount

                # set the step value
                if step == 0:
                    raise ValueError("arg 3 must not be zero")
                if step is None:
                    if start > stop:
                        step = -1
                    else:
                        step = 1

                for pno in range(start, stop, step):
                    yield (self.loadPage(pno))


            def __len__(self):
                return self.pageCount

            def _forget_page(self, page):
                """Remove a page from document page dict."""
                pid = id(page)
                if pid in self._page_refs:
                    self._page_refs[pid] = None

            def _reset_page_refs(self):
                """Invalidate all pages in document dictionary."""
                if self.isClosed:
                    return
                for page in self._page_refs.values():
                    if page:
                        page._erase()
                        page = None
                self._page_refs.clear()

            def __del__(self):
                if hasattr(self, "_reset_page_refs"):
                    self._reset_page_refs()
                if hasattr(self, "Graftmaps"):
                    for k in self.Graftmaps.keys():
                        self.Graftmaps[k] = None
                if hasattr(self, "this") and self.thisown:
                    self.__swig_destroy__(self)
                    self.thisown = False

                self.Graftmaps = {}
                self.ShownPages = {}
                self.InsertedImages  = {}
                self.stream = None
                self._reset_page_refs = DUMMY
                self.__swig_destroy__ = DUMMY
                self.isClosed = True

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.close()
            %}
    }
};

/*****************************************************************************/
// fz_page
/*****************************************************************************/
%nodefaultctor;
struct Page {
    %extend {
        ~Page()
        {
            DEBUGMSG1("Page");
            fz_page *this_page = (fz_page *) $self;
            fz_drop_page(gctx, this_page);
            DEBUGMSG2;
        }
        //---------------------------------------------------------------------
        // bound()
        //---------------------------------------------------------------------
        PARENTCHECK(bound, """Get page rectangle.""")
        %pythonappend bound %{val = Rect(val)%}
        PyObject *bound() {
            fz_rect rect = fz_bound_page(gctx, (fz_page *) $self);
            return JM_py_from_rect(rect);
        }
        %pythoncode %{rect = property(bound, doc="page rectangle")%}

        //---------------------------------------------------------------------
        // Page.getImageBbox
        //---------------------------------------------------------------------
        %pythonprepend getImageBbox %{
        """Get rectangle occupied by image 'name'.

        'name' is either an item of the image full list, or the referencing
        name string - elem[7] of the resp. item."""
        CheckParent(self)
        doc = self.parent
        if doc.isClosed or doc.isEncrypted:
            raise ValueError("doc is closed or encrypted")
        inf_rect = Rect(1, 1, -1, -1)
        if type(name) in (list, tuple):
            if not type(name[-1]) is int:
                raise ValueError("need a full page image list item")
            item = name
            if item[-1] != 0:
                raise ValueError("unsupported image item")
        else:
            imglist = [i for i in doc.getPageImageList(self.number, True) if i[-1] == 0 and name == i[-3]]
            if len(imglist) == 1:
                item = imglist[0]
            else:
                raise ValueError("no valid image found")%}
        %pythonappend getImageBbox %{
        if not bool(val):
            return inf_rect
        rc = inf_rect
        for v in val:
            if v[0] == item[-3]:
                rc = Quad(v[1]).rect
                break
        val = rc * self.transformationMatrix%}
        PyObject *
        getImageBbox(PyObject *name)
        {
            pdf_page *pdf_page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            PyObject *rc =NULL;
            fz_try(gctx) {
                rc = JM_image_reporter(gctx, pdf_page);
            }
            fz_catch(gctx) {
                return_none;
            }
            return rc;
        }

        //---------------------------------------------------------------------
        // run()
        //---------------------------------------------------------------------
        FITZEXCEPTION(run, !result)
        PARENTCHECK(run, """Run page through a device.""")
        PyObject *run(struct DeviceWrapper *dw, PyObject *m)
        {
            fz_try(gctx) {
                fz_run_page(gctx, (fz_page *) $self, dw->device, JM_matrix_from_py(m), NULL);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        //---------------------------------------------------------------------
        // Page.getTextPage
        //---------------------------------------------------------------------
        FITZEXCEPTION(_get_text_page, !result)
        %pythonappend _get_text_page %{val.thisown = True%}
        struct TextPage *
        _get_text_page(PyObject *clip=NULL, int flags=0)
        {
            fz_stext_page *textpage=NULL;
            fz_try(gctx) {
                fz_rect rect = JM_rect_from_py(clip);
                textpage = JM_new_stext_page_from_page(gctx, (fz_page *) $self, rect, flags);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct TextPage *) textpage;
        }
        %pythoncode %{
        def getTextPage(self, clip=None, flags=0):
            CheckParent(self)
            old_rotation = self.rotation
            if old_rotation != 0:
                self.setRotation(0)
            try:
                if clip is None:
                    clip = self.rect
                textpage = self._get_text_page(clip, flags=flags)
            finally:
                if old_rotation != 0:
                    self.setRotation(old_rotation)
            return textpage
        %}

        //---------------------------------------------------------------------
        // Page.language
        //---------------------------------------------------------------------
        %pythoncode%{@property%}
        %pythonprepend language %{"""Page language."""%}
        PyObject *language()
        {
            pdf_page *pdfpage = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            if (!pdfpage) return_none;
            pdf_obj *lang = pdf_dict_get_inheritable(gctx, pdfpage->obj, PDF_NAME(Lang));
            if (!lang) return_none;
            return Py_BuildValue("s", pdf_to_str_buf(gctx, lang));
        }


        //---------------------------------------------------------------------
        // Page.setLanguage
        //---------------------------------------------------------------------
        FITZEXCEPTION(setLanguage, !result)
        PARENTCHECK(setLanguage, """Set PDF page default language.""")
        PyObject *setLanguage(char *language=NULL)
        {
            pdf_page *pdfpage = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            fz_try(gctx) {
                ASSERT_PDF(pdfpage);
                fz_text_language lang;
                char buf[8];
                if (!language) {
                    pdf_dict_del(gctx, pdfpage->obj, PDF_NAME(Lang));
                } else {
                    lang = fz_text_language_from_string(language);
                    pdf_dict_put_text_string(gctx, pdfpage->obj,
                        PDF_NAME(Lang),
                        fz_string_from_text_language(buf, lang));
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            Py_RETURN_TRUE;
        }


        //---------------------------------------------------------------------
        // Page.getSVGimage
        //---------------------------------------------------------------------
        FITZEXCEPTION(getSVGimage, !result)
        PARENTCHECK(getSVGimage, """Make SVG image from page.""")
        PyObject *getSVGimage(PyObject *matrix = NULL, int text_as_path=1)
        {
            fz_rect mediabox = fz_bound_page(gctx, (fz_page *) $self);
            fz_device *dev = NULL;
            fz_buffer *res = NULL;
            PyObject *text = NULL;
            fz_matrix ctm = JM_matrix_from_py(matrix);
            fz_output *out = NULL;
            fz_separations *seps = NULL;
            fz_var(out);
            fz_var(dev);
            fz_var(res);
            fz_rect tbounds = mediabox;
            int text_option = (text_as_path == 1) ? FZ_SVG_TEXT_AS_PATH : FZ_SVG_TEXT_AS_TEXT;
            tbounds = fz_transform_rect(tbounds, ctm);

            fz_try(gctx) {
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                dev = fz_new_svg_device(gctx, out,
                                        tbounds.x1-tbounds.x0,  // width
                                        tbounds.y1-tbounds.y0,  // height
                                        text_option, 1);
                fz_run_page(gctx, (fz_page *) $self, dev, ctm, NULL);
                fz_close_device(gctx, dev);
                text = JM_EscapeStrFromBuffer(gctx, res);
            }
            fz_always(gctx) {
                fz_drop_device(gctx, dev);
                fz_drop_output(gctx, out);
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return text;
        }


        //---------------------------------------------------------------------
        // page set opacity
        //---------------------------------------------------------------------
        FITZEXCEPTION(_set_opacity, !result)
        %pythonprepend _set_opacity %{
        if min(CA, ca) >= 1:
            return
        tCA = int(round(max(CA , 0) * 100))
        if tCA >= 100:
            tCA = 99
        tca = int(round(max(ca, 0) * 100))
        if tca >= 100:
            tca = 99
        gstate = "fitzca%02i%02i" % (tCA, tca)
        %}
        PyObject *
        _set_opacity(char *gstate=NULL, float CA=1, float ca=1)
        {
            if (!gstate) Py_RETURN_NONE;
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            fz_try(gctx) {
                ASSERT_PDF(page);
                pdf_obj *resources = pdf_dict_get(gctx, page->obj, PDF_NAME(Resources));
                if (!resources) {
                    resources = pdf_dict_put_dict(gctx, page->obj, PDF_NAME(Resources), 2);
                }
                pdf_obj *extg = pdf_dict_get(gctx, resources, PDF_NAME(ExtGState));
                if (!extg) {
                    extg = pdf_dict_put_dict(gctx, resources, PDF_NAME(ExtGState), 2);
                }
                int i, n = pdf_dict_len(gctx, extg);
                for (i = 0; i < n; i++) {
                    pdf_obj *o1 = pdf_dict_get_key(gctx, extg, i);
                    char *name = (char *) pdf_to_name(gctx, o1);
                    if (strcmp(name, gstate) == 0) goto finished;
                }
                pdf_obj *opa = pdf_new_dict(gctx, page->doc, 3);
                pdf_dict_put_real(gctx, opa, PDF_NAME(CA), (double) CA);
                pdf_dict_put_real(gctx, opa, PDF_NAME(ca), (double) ca);
                pdf_dict_puts_drop(gctx, extg, gstate, opa);
                finished:;
            }
            fz_always(gctx) {
            }
            fz_catch(gctx) {
                return NULL;
            }
            return Py_BuildValue("s", gstate);

        }

        //---------------------------------------------------------------------
        // page addCaretAnnot
        //---------------------------------------------------------------------
        FITZEXCEPTION(_add_caret_annot, !result)
        struct Annot *
        _add_caret_annot(PyObject *point)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            pdf_annot *annot = NULL;
            fz_try(gctx) {
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_CARET);
                if (point)
                {
                    fz_point p = JM_point_from_py(point);
                    fz_rect r = pdf_annot_rect(gctx, annot);
                    r = fz_make_rect(p.x, p.y, p.x + r.x1 - r.x0, p.y + r.y1 - r.y0);
                    pdf_set_annot_rect(gctx, annot, r);
                }
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) {
                return NULL;
            }
            annot = pdf_keep_annot(gctx, annot);
            return (struct Annot *) annot;
        }


        //---------------------------------------------------------------------
        // page addRedactAnnot
        //---------------------------------------------------------------------
        FITZEXCEPTION(_add_redact_annot, !result)
        struct Annot *
        _add_redact_annot(PyObject *quad,
            char *text=NULL,
            const char *da_str=NULL,
            int align=0,
            PyObject *fill=NULL,
            PyObject *text_color=NULL)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            pdf_annot *annot = NULL;
            float fcol[4] = { 1, 1, 1, 0};
            int nfcol = 0, i;
            fz_try(gctx) {
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_REDACT);
                fz_quad q = JM_quad_from_py(quad);
                fz_rect r = fz_rect_from_quad(q);

                // TODO calculate de-rotated rect
                pdf_set_annot_rect(gctx, annot, r);
                if (EXISTS(fill)) {
                    JM_color_FromSequence(fill, &nfcol, fcol);
                    pdf_obj *arr = pdf_new_array(gctx, page->doc, nfcol);
                    for (i = 0; i < nfcol; i++)
                    {
                        pdf_array_push_real(gctx, arr, fcol[i]);
                    }
                    pdf_dict_put_drop(gctx, annot->obj, PDF_NAME(IC), arr);
                }
                if (text) {
                    pdf_dict_puts_drop(gctx, annot->obj, "OverlayText",
                                       pdf_new_text_string(gctx, text));
                    pdf_dict_put_text_string(gctx,annot->obj, PDF_NAME(DA), da_str);
                    pdf_dict_put_int(gctx, annot->obj, PDF_NAME(Q), (int64_t) align);
                }
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) {
                return NULL;
            }
            annot = pdf_keep_annot(gctx, annot);
            return (struct Annot *) annot;
        }

        //---------------------------------------------------------------------
        // page addLineAnnot
        //---------------------------------------------------------------------
        FITZEXCEPTION(_add_line_annot, !result)
        struct Annot *
        _add_line_annot(PyObject *p1, PyObject *p2)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            pdf_annot *annot = NULL;
            fz_try(gctx) {
                ASSERT_PDF(page);
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_LINE);
                fz_point a = JM_point_from_py(p1);
                fz_point b = JM_point_from_py(p2);
                pdf_set_annot_line(gctx, annot, a, b);
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) {
                return NULL;
            }
            annot = pdf_keep_annot(gctx, annot);
            return (struct Annot *) annot;
        }

        //---------------------------------------------------------------------
        // page addTextAnnot
        //---------------------------------------------------------------------
        FITZEXCEPTION(_add_text_annot, !result)
        struct Annot *
        _add_text_annot(PyObject *point,
            char *text,
            char *icon=NULL)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            pdf_annot *annot = NULL;
            fz_rect r;
            fz_point p = JM_point_from_py(point);
            fz_var(annot);
            fz_try(gctx) {
                ASSERT_PDF(page);
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_TEXT);
                r = pdf_annot_rect(gctx, annot);
                r = fz_make_rect(p.x, p.y, p.x + r.x1 - r.x0, p.y + r.y1 - r.y0);
                pdf_set_annot_rect(gctx, annot, r);
                int flags = PDF_ANNOT_IS_PRINT;
                pdf_set_annot_flags(gctx, annot, flags);
                pdf_set_annot_contents(gctx, annot, text);
                if (icon) {
                    pdf_set_annot_icon_name(gctx, annot, icon);
                }
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
                pdf_set_annot_rect(gctx, annot, r);
                pdf_set_annot_flags(gctx, annot, flags);
            }
            fz_catch(gctx) {
                return NULL;
            }
            annot = pdf_keep_annot(gctx, annot);
            return (struct Annot *) annot;
        }

        //---------------------------------------------------------------------
        // page addInkAnnot
        //---------------------------------------------------------------------
        FITZEXCEPTION(_add_ink_annot, !result)
        struct Annot *
        _add_ink_annot(PyObject *list)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            pdf_annot *annot = NULL;
            PyObject *p = NULL, *sublist = NULL;
            pdf_obj *inklist = NULL, *stroke = NULL;
            fz_matrix ctm, inv_ctm;
            fz_point point;
            fz_var(annot);
            fz_try(gctx) {
                ASSERT_PDF(page);
                if (!PySequence_Check(list)) THROWMSG(gctx, "arg must be a sequence");
                pdf_page_transform(gctx, page, NULL, &ctm);
                inv_ctm = fz_invert_matrix(ctm);
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_INK);
                Py_ssize_t i, j, n0 = PySequence_Size(list), n1;
                inklist = pdf_new_array(gctx, annot->page->doc, n0);

                for (j = 0; j < n0; j++) {
                    sublist = PySequence_ITEM(list, j);
                    n1 = PySequence_Size(sublist);
                    stroke = pdf_new_array(gctx, annot->page->doc, 2 * n1);

                    for (i = 0; i < n1; i++) {
                        p = PySequence_ITEM(sublist, i);
                        if (!PySequence_Check(p) || PySequence_Size(p) != 2)
                            THROWMSG(gctx, "3rd level entries must be pairs of floats");
                        point = fz_transform_point(JM_point_from_py(p), inv_ctm);
                        Py_CLEAR(p);
                        pdf_array_push_real(gctx, stroke, point.x);
                        pdf_array_push_real(gctx, stroke, point.y);
                    }

                    pdf_array_push_drop(gctx, inklist, stroke);
                    stroke = NULL;
                    Py_CLEAR(sublist);
                }

                pdf_dict_put_drop(gctx, annot->obj, PDF_NAME(InkList), inklist);
                inklist = NULL;
                pdf_dirty_annot(gctx, annot);
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }

            fz_catch(gctx) {
                Py_CLEAR(p);
                Py_CLEAR(sublist);
                return NULL;
            }
            annot = pdf_keep_annot(gctx, annot);
            return (struct Annot *) annot;
        }

        //---------------------------------------------------------------------
        // page addStampAnnot
        //---------------------------------------------------------------------
        FITZEXCEPTION(_add_stamp_annot, !result)
        struct Annot *
        _add_stamp_annot(PyObject *rect, int stamp=0)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            pdf_annot *annot = NULL;
            pdf_obj *stamp_id[] = {PDF_NAME(Approved), PDF_NAME(AsIs),
                                   PDF_NAME(Confidential), PDF_NAME(Departmental),
                                   PDF_NAME(Experimental), PDF_NAME(Expired),
                                   PDF_NAME(Final), PDF_NAME(ForComment),
                                   PDF_NAME(ForPublicRelease), PDF_NAME(NotApproved),
                                   PDF_NAME(NotForPublicRelease), PDF_NAME(Sold),
                                   PDF_NAME(TopSecret), PDF_NAME(Draft)};
            int n = nelem(stamp_id);
            pdf_obj *name = stamp_id[0];
            fz_try(gctx) {
                ASSERT_PDF(page);
                fz_rect r = JM_rect_from_py(rect);
                if (fz_is_infinite_rect(r) || fz_is_empty_rect(r))
                    THROWMSG(gctx, "rect must be finite and not empty");
                if (INRANGE(stamp, 0, n-1))
                    name = stamp_id[stamp];
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_STAMP);
                pdf_set_annot_rect(gctx, annot, r);
                pdf_dict_put(gctx, annot->obj, PDF_NAME(Name), name);
                pdf_set_annot_contents(gctx, annot,
                        pdf_dict_get_name(gctx, annot->obj, PDF_NAME(Name)));
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) {
                return NULL;
            }
            annot = pdf_keep_annot(gctx, annot);
            return (struct Annot *) annot;
        }

        //---------------------------------------------------------------------
        // page addFileAnnot
        //---------------------------------------------------------------------
        FITZEXCEPTION(_add_file_annot, !result)
        struct Annot *
        _add_file_annot(PyObject *point,
            PyObject *buffer,
            char *filename,
            char *ufilename=NULL,
            char *desc=NULL,
            char *icon=NULL)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            pdf_annot *annot = NULL;
            char *uf = ufilename, *d = desc;
            if (!ufilename) uf = filename;
            if (!desc) d = filename;
            fz_buffer *filebuf = NULL;
            fz_rect r;
            fz_point p = JM_point_from_py(point);
            fz_var(annot);
            fz_try(gctx) {
                ASSERT_PDF(page);
                filebuf = JM_BufferFromBytes(gctx, buffer);
                if (!filebuf) THROWMSG(gctx, "bad type: 'buffer'");
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_FILE_ATTACHMENT);
                r = pdf_annot_rect(gctx, annot);
                r = fz_make_rect(p.x, p.y, p.x + r.x1 - r.x0, p.y + r.y1 - r.y0);
                pdf_set_annot_rect(gctx, annot, r);
                int flags = PDF_ANNOT_IS_PRINT;
                pdf_set_annot_flags(gctx, annot, flags);

                if (icon)
                    pdf_set_annot_icon_name(gctx, annot, icon);

                pdf_obj *val = JM_embed_file(gctx, page->doc, filebuf,
                                    filename, uf, d, 1);
                pdf_dict_put(gctx, annot->obj, PDF_NAME(FS), val);
                pdf_dict_put_text_string(gctx, annot->obj, PDF_NAME(Contents), filename);
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
                pdf_set_annot_rect(gctx, annot, r);
                pdf_set_annot_flags(gctx, annot, flags);
            }
            fz_catch(gctx) {
                return NULL;
            }
            annot = pdf_keep_annot(gctx, annot);
            return (struct Annot *) annot;
        }


        //---------------------------------------------------------------------
        // page: add a text marker annotation
        //---------------------------------------------------------------------
        FITZEXCEPTION(_add_text_marker, !result)
        %pythonprepend _add_text_marker %{
        CheckParent(self)
        if not self.parent.isPDF:
            raise ValueError("not a PDF")%}

        %pythonappend _add_text_marker %{
        if not val:
            return None
        val.parent = weakref.proxy(self)
        self._annot_refs[id(val)] = val%}

        struct Annot *
        _add_text_marker(PyObject *quads, int annot_type)
        {
            pdf_page *pdfpage = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            pdf_annot *annot = NULL;
            PyObject *item = NULL;
            int rotation = JM_page_rotation(gctx, pdfpage);
            fz_quad q;
            fz_var(annot);
            fz_var(item);
            fz_try(gctx) {
                if (rotation != 0) {
                    pdf_dict_put_int(gctx, pdfpage->obj, PDF_NAME(Rotate), 0);
                }
                annot = pdf_create_annot(gctx, pdfpage, annot_type);
                Py_ssize_t i, len = PySequence_Size(quads);
                for (i = 0; i < len; i++) {
                    item = PySequence_ITEM(quads, i);
                    q = JM_quad_from_py(item);
                    Py_DECREF(item);
                    pdf_add_annot_quad_point(gctx, annot, q);
                }
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_always(gctx) {
                if (rotation != 0) {
                    pdf_dict_put_int(gctx, pdfpage->obj, PDF_NAME(Rotate), rotation);
                }
            }
            fz_catch(gctx) {
                pdf_drop_annot(gctx, annot);
                return NULL;
            }
            annot = pdf_keep_annot(gctx, annot);
            return (struct Annot *) annot;
        }


        //---------------------------------------------------------------------
        // page: add circle or rectangle annotation
        //---------------------------------------------------------------------
        FITZEXCEPTION(_add_square_or_circle, !result)
        struct Annot *
        _add_square_or_circle(PyObject *rect, int annot_type)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            pdf_annot *annot = NULL;
            fz_try(gctx) {
                fz_rect r = JM_rect_from_py(rect);
                if (fz_is_infinite_rect(r) || fz_is_empty_rect(r))
                    THROWMSG(gctx, "rect must be finite and not empty");
                annot = pdf_create_annot(gctx, page, annot_type);
                pdf_set_annot_rect(gctx, annot, r);
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) {
                return NULL;
            }
            annot = pdf_keep_annot(gctx, annot);
            return (struct Annot *) annot;
        }


        //---------------------------------------------------------------------
        // page: add multiline annotation
        //---------------------------------------------------------------------
        FITZEXCEPTION(_add_multiline, !result)
        struct Annot *
        _add_multiline(PyObject *points, int annot_type)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            pdf_annot *annot = NULL;
            fz_try(gctx) {
                Py_ssize_t i, n = PySequence_Size(points);
                if (n < 2) THROWMSG(gctx, "bad list of points");
                annot = pdf_create_annot(gctx, page, annot_type);
                for (i = 0; i < n; i++) {
                    PyObject *p = PySequence_ITEM(points, i);
                    if (PySequence_Size(p) != 2) {
                        Py_DECREF(p);
                        THROWMSG(gctx, "bad list of points");
                    }
                    fz_point point = JM_point_from_py(p);
                    Py_DECREF(p);
                    pdf_add_annot_vertex(gctx, annot, point);
                }

                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) {
                return NULL;
            }
            annot = pdf_keep_annot(gctx, annot);
            return (struct Annot *) annot;
        }


        //---------------------------------------------------------------------
        // page addFreetextAnnot
        //---------------------------------------------------------------------
        FITZEXCEPTION(_add_freetext_annot, !result)
        struct Annot *
        _add_freetext_annot(PyObject *rect, char *text,
            float fontsize=11,
            char *fontname=NULL,
            PyObject *text_color=NULL,
            PyObject *fill_color=NULL,
            int align=0,
            int rotate=0)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            float fcol[4] = {1, 1, 1, 1}; // fill color: white
            int nfcol = 0;
            JM_color_FromSequence(fill_color, &nfcol, fcol);
            float tcol[4] = {0, 0, 0, 0}; // std. text color: black
            int ntcol = 0;
            JM_color_FromSequence(text_color, &ntcol, tcol);
            fz_rect r = JM_rect_from_py(rect);
            pdf_annot *annot = NULL;
            fz_try(gctx) {
                if (fz_is_infinite_rect(r) || fz_is_empty_rect(r))
                    THROWMSG(gctx, "rect must be finite and not empty");
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_FREE_TEXT);
                pdf_set_annot_contents(gctx, annot, text);
                pdf_set_annot_rect(gctx, annot, r);
                pdf_dict_put_int(gctx, annot->obj, PDF_NAME(Rotate), rotate);
                pdf_dict_put_int(gctx, annot->obj, PDF_NAME(Q), align);

                if (fill_color) {
                    pdf_set_annot_color(gctx, annot, nfcol, fcol);
                }

                // insert the default appearance string
                JM_make_annot_DA(gctx, annot, ntcol, tcol, fontname, fontsize);
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) {
                return NULL;
            }
            annot = pdf_keep_annot(gctx, annot);
            return (struct Annot *) annot;
        }


    %pythoncode %{
        @property
        def rotationMatrix(self):
            """Reflects page rotation."""
            return Matrix(TOOLS._rotate_matrix(self))

        @property
        def derotationMatrix(self):
            """Reflects page de-rotation."""
            return Matrix(TOOLS._derotate_matrix(self))

        def addCaretAnnot(self, point):
            """Add a 'Caret' annotation."""
            old_rotation = annot_preprocess(self)
            try:
                annot = self._add_caret_annot(point)
            finally:
                if old_rotation != 0:
                    self.setRotation(old_rotation)
            annot_postprocess(self, annot)
            return annot


        def addStrikeoutAnnot(self, quads=None, start=None, stop=None, clip=None):
            """Add a 'StrikeOut' annotation."""
            if quads is None:
                q = get_highlight_selection(self, start=start, stop=stop, clip=clip)
            else:
                q = CheckMarkerArg(quads)
            return self._add_text_marker(q, PDF_ANNOT_STRIKE_OUT)


        def addUnderlineAnnot(self, quads=None, start=None, stop=None, clip=None):
            """Add a 'Underline' annotation."""
            if quads is None:
                q = get_highlight_selection(self, start=start, stop=stop, clip=clip)
            else:
                q = CheckMarkerArg(quads)
            return self._add_text_marker(q, PDF_ANNOT_UNDERLINE)


        def addSquigglyAnnot(self, quads=None, start=None,
                             stop=None, clip=None):
            """Add a 'Squiggly' annotation."""
            if quads is None:
                q = get_highlight_selection(self, start=start, stop=stop, clip=clip)
            else:
                q = CheckMarkerArg(quads)
            return self._add_text_marker(q, PDF_ANNOT_SQUIGGLY)


        def addHighlightAnnot(self, quads=None, start=None,
                              stop=None, clip=None):
            """Add a 'Highlight' annotation."""
            if quads is None:
                q = get_highlight_selection(self, start=start, stop=stop, clip=clip)
            else:
                q = CheckMarkerArg(quads)
            return self._add_text_marker(q, PDF_ANNOT_HIGHLIGHT)


        def addRectAnnot(self, rect):
            """Add a 'Square' (rectangle) annotation."""
            old_rotation = annot_preprocess(self)
            try:
                annot = self._add_square_or_circle(rect, PDF_ANNOT_SQUARE)
            finally:
                if old_rotation != 0:
                    self.setRotation(old_rotation)
            annot_postprocess(self, annot)
            return annot


        def addCircleAnnot(self, rect):
            """Add a 'Circle' (ellipse, oval) annotation."""
            old_rotation = annot_preprocess(self)
            try:
                annot = self._add_square_or_circle(rect, PDF_ANNOT_CIRCLE)
            finally:
                if old_rotation != 0:
                    self.setRotation(old_rotation)
            annot_postprocess(self, annot)
            return annot


        def addTextAnnot(self, point, text, icon="Note"):
            """Add a 'Text' (sticky note) annotation."""
            old_rotation = annot_preprocess(self)
            try:
                annot = self._add_text_annot(point, text, icon=icon)
            finally:
                if old_rotation != 0:
                    self.setRotation(old_rotation)
            annot_postprocess(self, annot)
            return annot


        def addLineAnnot(self, p1, p2):
            """Add a 'Line' annotation."""
            old_rotation = annot_preprocess(self)
            try:
                annot = self._add_line_annot(p1, p2)
            finally:
                if old_rotation != 0:
                    self.setRotation(old_rotation)
            annot_postprocess(self, annot)
            return annot


        def addPolylineAnnot(self, points):
            """Add a 'PolyLine' annotation."""
            old_rotation = annot_preprocess(self)
            try:
                annot = self._add_multiline(points, PDF_ANNOT_POLY_LINE)
            finally:
                if old_rotation != 0:
                    self.setRotation(old_rotation)
            annot_postprocess(self, annot)
            return annot


        def addPolygonAnnot(self, points):
            """Add a 'Polygon' annotation."""
            old_rotation = annot_preprocess(self)
            try:
                annot = self._add_multiline(points, PDF_ANNOT_POLYGON)
            finally:
                if old_rotation != 0:
                    self.setRotation(old_rotation)
            annot_postprocess(self, annot)
            return annot


        def addStampAnnot(self, rect, stamp=0):
            """Add a ('rubber') 'Stamp' annotation."""
            old_rotation = annot_preprocess(self)
            try:
                annot = self._add_stamp_annot(rect, stamp)
            finally:
                if old_rotation != 0:
                    self.setRotation(old_rotation)
            annot_postprocess(self, annot)
            return annot


        def addInkAnnot(self, handwriting):
            """Add a 'Ink' ('handwriting') annotation.

            The argument must be a list of lists of point_likes.
            """
            old_rotation = annot_preprocess(self)
            try:
                annot = self._add_ink_annot(handwriting)
            finally:
                if old_rotation != 0:
                    self.setRotation(old_rotation)
            annot_postprocess(self, annot)
            return annot


        def addFileAnnot(self, point,
            buffer,
            filename,
            ufilename=None,
            desc=None,
            icon=None):
            """Add a 'FileAttachment' annotation."""

            old_rotation = annot_preprocess(self)
            try:
                annot = self._add_file_annot(point,
                            buffer,
                            filename,
                            ufilename=ufilename,
                            desc=desc,
                            icon=icon)
            finally:
                if old_rotation != 0:
                    self.setRotation(old_rotation)
            annot_postprocess(self, annot)
            return annot


        def addFreetextAnnot(self, rect, text, fontsize=12,
                             fontname=None, text_color=None,
                             fill_color=None, align=0, rotate=0):
            """Add a 'FreeText' annotation."""

            old_rotation = annot_preprocess(self)
            try:
                annot = self._add_freetext_annot(rect, text, fontsize=fontsize,
                        fontname=fontname, text_color=text_color,
                        fill_color=fill_color, align=align, rotate=rotate)
            finally:
                if old_rotation != 0:
                    self.setRotation(old_rotation)
            annot_postprocess(self, annot)
            return annot


        def addRedactAnnot(self, quad, text=None, fontname=None,
                           fontsize=11, align=0, fill=None, text_color=None,
                           cross_out=True):
            """Add a 'Redact' annotation."""
            da_str = None
            if text:
                CheckColor(fill)
                CheckColor(text_color)
                if not fontname:
                    fontname = "Helv"
                if not fontsize:
                    fontsize = 11
                if not text_color:
                    text_color = (0, 0, 0)
                if hasattr(text_color, "__float__"):
                    text_color = (text_color, text_color, text_color)
                if len(text_color) > 3:
                    text_color = text_color[:3]
                fmt = "{:g} {:g} {:g} rg /{f:s} {s:g} Tf"
                da_str = fmt.format(*text_color, f=fontname, s=fontsize)
                if fill is None:
                    fill = (1, 1, 1)
                if fill:
                    if hasattr(fill, "__float__"):
                        fill = (fill, fill, fill)
                    if len(fill) > 3:
                        fill = fill[:3]

            old_rotation = annot_preprocess(self)
            try:
                annot = self._add_redact_annot(quad, text=text, da_str=da_str,
                           align=align, fill=fill)
            finally:
                if old_rotation != 0:
                    self.setRotation(old_rotation)
            annot_postprocess(self, annot)
            #------------------------------------------------------------------
            # change the generated appearance to show a crossed-out rectangle
            #------------------------------------------------------------------
            if cross_out:
                ap_tab = annot._getAP().splitlines()[:-1]  # get the 4 commands only
                _, LL, LR, UR, UL = ap_tab
                ap_tab.append(LR)
                ap_tab.append(LL)
                ap_tab.append(UR)
                ap_tab.append(LL)
                ap_tab.append(UL)
                ap_tab.append(b"S")
                ap = b"\n".join(ap_tab)
                annot._setAP(ap, 0)
            return annot
        %}


        //---------------------------------------------------------------------
        // page load annot by name or xref
        //---------------------------------------------------------------------
        FITZEXCEPTION(_load_annot, !result)
        struct Annot *
        _load_annot(char *name, int xref)
        {
            pdf_annot *annot = NULL;
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            fz_try(gctx) {
                ASSERT_PDF(page);
                if (xref == 0)
                    annot = JM_get_annot_by_name(gctx, page, name);
                else
                    annot = JM_get_annot_by_xref(gctx, page, xref);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct Annot *) annot;
        }


        //---------------------------------------------------------------------
        // page get list of annot names
        //---------------------------------------------------------------------
        PARENTCHECK(annot_names, """List of names of annotations, fields and links.""")
        PyObject *annot_names()
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            if (!page) return_none;
            return JM_get_annot_id_list(gctx, page);
        }


        //---------------------------------------------------------------------
        // page retrieve list of annotation xrefs
        //---------------------------------------------------------------------
        PARENTCHECK(annot_xrefs,"""List of xref numbers of annotations, fields and links.""")
        PyObject *annot_xrefs()
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            if (!page) return_none;
            return JM_get_annot_xref_list(gctx, page);
        }


        %pythoncode %{
        def loadAnnot(self, ident):
            """Load an annot by name (/NM key) or xref.
            
            Args:
                ident: identifier, either name (str) or xref (int).
            """

            CheckParent(self)
            if type(ident) is str:
                xref = 0
                name = ident
            elif type(ident) is int:
                xref = ident
                name = None
            else:
                raise ValueError("identifier must be string or integer")
            val = self._load_annot(name, xref)
            if not val:
                return val
            val.thisown = True
            val.parent = weakref.proxy(self)
            self._annot_refs[id(val)] = val
            return val

        load_annot = loadAnnot


        #---------------------------------------------------------------------
        # page addWidget
        #---------------------------------------------------------------------
        def addWidget(self, widget):
            """Add a 'Widget' (form field)."""
            CheckParent(self)
            doc = self.parent
            if not doc.isPDF:
                raise ValueError("not a PDF")
            widget._validate()
            annot = self._addWidget(widget.field_type, widget.field_name)
            if not annot:
                return None
            annot.thisown = True
            annot.parent = weakref.proxy(self) # owning page object
            self._annot_refs[id(annot)] = annot
            widget.parent = annot.parent
            widget._annot = annot
            widget.update()
            return annot
        %}

        FITZEXCEPTION(_addWidget, !result)
        struct Annot *_addWidget(int field_type, char *field_name)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            pdf_document *pdf = page->doc;
            pdf_annot *annot = NULL;
            fz_var(annot);
            fz_try(gctx) {
                annot = JM_create_widget(gctx, pdf, page, field_type, field_name);
                if (!annot) THROWMSG(gctx, "could not create widget");
                JM_add_annot_id(gctx, annot, "fitzwidget");
            }
            fz_catch(gctx) {
                return NULL;
            }
            annot = pdf_keep_annot(gctx, annot);
            return (struct Annot *) annot;
        }

        //---------------------------------------------------------------------
        // Page.getDisplayList
        //---------------------------------------------------------------------
        FITZEXCEPTION(getDisplayList, !result)
        %pythonprepend getDisplayList %{
        """Make a DisplayList from the page for Pixmap generation.

        Include (default) or exclude annotations."""

        CheckParent(self)
        %}
        %pythonappend getDisplayList %{val.thisown = True%}
        struct DisplayList *getDisplayList(int annots=1)
        {
            fz_display_list *dl = NULL;
            fz_try(gctx) {
                if (annots) {
                    dl = fz_new_display_list_from_page(gctx, (fz_page *) $self);
                } else {
                    dl = fz_new_display_list_from_page_contents(gctx, (fz_page *) $self);
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct DisplayList *) dl;
        }


        //----------------------------------------------------------------
        // Page.getDrawings
        //----------------------------------------------------------------
        %pythoncode %{
        def getDrawings(self):
            """Get page draw paths."""

            CheckParent(self)
            val = self._getDrawings()  # read raw list from trace device
            paths = []

            def new_path():
                """Return empty path dict to use as template."""
                return {
                    "color": None,
                    "fill": None,
                    "width": 1.0,
                    "lineJoin": 0,
                    "lineCap": (0, 0, 0),
                    "dashes": "[] 0",
                    "closePath": False,
                    "even_odd": False,
                    "rect": Rect(),
                    "items": [],
                    "opacity": 1.0,
                }

            def is_rectangle(path):
                """Check if path represents a rectangle.
                
                For this, it must be exactly three connected lines, of which
                the first and the last one must be horizontal and line two
                must be vertical.
                """
                if not path["closePath"]:
                    return False
                if [item[0] for item in path["items"]] != ["l", "l", "l"]:
                    return False
                p1, p2 = path["items"][0][1:]  # first line
                p3, p4 = path["items"][1][1:]  # second line
                p5, p6 = path["items"][2][1:]  # third line
                if p2 != p3 or p4 != p5:  # must be connected
                    return False
                if p1.y != p2.y or p3.x != p4.x or p5.y != p6.y:
                    return False
                return True

            def check_and_merge(this, prev):
                """Check if "this" is the "stroke" version of "prev".

                If so, update "prev" with appropriate values and return True,
                else do nothing and return False.
                """
                if prev is None:
                    return False
                if this["items"] != prev["items"]:  # must have same items
                    return False
                if this["closePath"] != prev["closePath"]:
                    return False
                if this["color"] is not None:
                    prev["color"] = this["color"]
                if this["width"] != 1:
                    prev["width"] = this["width"]
                if this["dashes"] != "[] 0":
                    prev["dashes"] = this["dashes"]
                if this["lineCap"] != (0, 0, 0):
                    prev["lineCap"] = this["lineCap"]
                if this["lineJoin"] != 0:
                    prev["lineJoin"] = this["lineJoin"]
                return True

            for item in val:
                if type(item) is list:
                    if item[0] in ("fill", "stroke", "clip", "clip-stroke"):
                        # this begins a new path
                        path = new_path()
                        ctm = Matrix(1, 1)
                        factor = 1  # modify width and dash length
                        current = None  # the current point
                        for x in item[1:]:  # loop through path parms that follow
                            if x == "non-zero":
                                path["even_odd"] = False
                            elif x == "even-odd":
                                path["even_odd"] = True
                            elif x[0] == "matrix":
                                ctm = Matrix(x[1])
                                if abs(ctm.a) == abs(ctm.d):
                                    factor = abs(ctm.a)
                            elif x[0] == "w":
                                path["width"] = x[1] * factor
                            elif x[0] == "lineCap":
                                path["lineCap"] = x[1:]
                            elif x[0] == "lineJoin":
                                path["lineJoin"] = x[1]
                            elif x[0] == "color":
                                if item[0] == "fill":
                                    path["fill"] = x[1:]
                                else:
                                    path["color"] = x[1:]
                            elif x[0] == "dashPhase":
                                dashPhase = x[1] * factor
                            elif x[0] == "dashes":
                                dashes = x[1:]
                                l = list(map(lambda y: float(y) * factor, dashes))
                                l = list(map(str, l))
                                path["dashes"] = "[%s] %g" % (" ".join(l), dashPhase)
                            elif x[0] == "alpha":
                                path["opacity"] = round(x[1], 2)

                    if item[0] == "m":
                        p = Point(item[1]) * ctm
                        current = p
                        path["rect"] = Rect(p, p)
                    elif item[0] == "l":
                        p2 = Point(item[1]) * ctm
                        path["items"].append(("l", current, p2))
                        current = p2
                        path["rect"] |= p2
                    elif item[0] == "c":
                        p2 = Point(item[1]) * ctm
                        p3 = Point(item[2]) * ctm
                        p4 = Point(item[3]) * ctm
                        path["items"].append(("c", current, p2, p3, p4))
                        current = p4
                        path["rect"] |= p2
                        path["rect"] |= p3
                        path["rect"] |= p4
                elif item == "closePath":
                    path["closePath"] = True
                elif item in ("estroke", "efill", "eclip", "eclip-stroke"):
                    if is_rectangle(path):
                        path["items"] = [("re", path["rect"])]
                        path["closePath"] = False

                    try:  # check if path is "stroke" duplicate of previous
                        prev = paths.pop()  # get previous path in list
                    except IndexError:
                        prev = None  # we are the first
                    if prev is None:
                        paths.append(path)
                    elif check_and_merge(path, prev) is False:  # no duplicates
                        paths.append(prev)  # re-append old one
                        paths.append(path)  # append new one
                    else:
                        paths.append(prev)  # append modified old one

                    path = None
                else:
                    print("unexpected item:", item)

            return paths
        %}

        FITZEXCEPTION(_getDrawings, !result)
        PyObject *
        _getDrawings()
        {
            fz_page *page = (fz_page *) $self;
            fz_device *dev = NULL;
            PyObject *rc = NULL;
            fz_try(gctx) {
                rc = PyList_New(0);
                dev = JM_new_tracedraw_device(gctx, rc);
                fz_run_page(gctx, page, dev, fz_identity, NULL);
                fz_close_device(gctx, dev);
            }
            fz_always(gctx) {
                fz_drop_device(gctx, dev);
            }
            fz_catch(gctx) {
                Py_CLEAR(rc);
                return NULL;
            }
            return rc;
        }


        //---------------------------------------------------------------------
        // Page apply redactions
        //---------------------------------------------------------------------
        FITZEXCEPTION(_apply_redactions, !result)
        PyObject *_apply_redactions(int images=PDF_REDACT_IMAGE_PIXELS)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            int success = 0;
            pdf_redact_options opts;
            opts.black_boxes = 0;  // no black boxes
            opts.image_method = images;  // how to treat images
            fz_try(gctx) {
                ASSERT_PDF(page);
                success = pdf_redact_page(gctx, page->doc, page, &opts);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return JM_BOOL(success);
        }


        //---------------------------------------------------------------------
        // Page._makePixmap
        //---------------------------------------------------------------------
        FITZEXCEPTION(_makePixmap, !result)
        struct Pixmap *
        _makePixmap(struct Document *doc,
            PyObject *ctm,
            struct Colorspace *cs,
            int alpha=0,
            int annots=1,
            PyObject *clip=NULL)
        {
            fz_pixmap *pix = NULL;
            fz_try(gctx) {
                pix = JM_pixmap_from_page(gctx, (fz_document *) doc, (fz_page *) $self, ctm, (fz_colorspace *) cs, alpha, annots, clip);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct Pixmap *) pix;
        }


        //---------------------------------------------------------------------
        // Page.setMediaBox
        //---------------------------------------------------------------------
        FITZEXCEPTION(setMediaBox, !result)
        PARENTCHECK(setMediaBox, """Set the MediaBox.""")
        PyObject *setMediaBox(PyObject *rect)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            fz_try(gctx) {
                ASSERT_PDF(page);
                fz_rect mediabox = JM_rect_from_py(rect);
                if (fz_is_empty_rect(mediabox) ||
                    fz_is_infinite_rect(mediabox)) {
                    THROWMSG(gctx, "rect must be finite and not empty");
                }
                pdf_dict_put_rect(gctx, page->obj, PDF_NAME(MediaBox), mediabox);
                pdf_dict_put_rect(gctx, page->obj, PDF_NAME(CropBox), mediabox);
            }
            fz_catch(gctx) {
                return NULL;
            }
            page->doc->dirty = 1;
            return_none;
        }

        //---------------------------------------------------------------------
        // Page.setCropBox
        // ATTENTION: This will also change the value returned by Page.bound()
        //---------------------------------------------------------------------
        FITZEXCEPTION(setCropBox, !result)
        PARENTCHECK(setCropBox, """Set the CropBox.""")
        PyObject *setCropBox(PyObject *rect)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            fz_try(gctx) {
                ASSERT_PDF(page);
                fz_rect mediabox = pdf_bound_page(gctx, page);
                pdf_obj *o = pdf_dict_get_inheritable(gctx, page->obj, PDF_NAME(MediaBox));
                if (o) mediabox = pdf_to_rect(gctx, o);
                fz_rect cropbox = fz_empty_rect;
                fz_rect r = JM_rect_from_py(rect);
                cropbox.x0 = r.x0;
                cropbox.y0 = mediabox.y1 - r.y1;
                cropbox.x1 = r.x1;
                cropbox.y1 = mediabox.y1 - r.y0;
                pdf_dict_put_drop(gctx, page->obj, PDF_NAME(CropBox),
                                  pdf_new_rect(gctx, page->doc, cropbox));
            }
            fz_catch(gctx) {
                return NULL;
            }
            page->doc->dirty = 1;
            return_none;
        }

        //---------------------------------------------------------------------
        // loadLinks()
        //---------------------------------------------------------------------
        PARENTCHECK(loadLinks, """Get first Link.""")
        %pythonappend loadLinks %{
            if val:
                val.thisown = True
                val.parent = weakref.proxy(self) # owning page object
                self._annot_refs[id(val)] = val
                if self.parent.isPDF:
                    val.xref = self._getLinkXrefs()[0]
                else:
                    val.xref = 0
        %}
        struct Link *loadLinks()
        {
            fz_link *l = NULL;
            fz_try(gctx) {
                l = fz_load_links(gctx, (fz_page *) $self);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct Link *) l;
        }
        %pythoncode %{firstLink = property(loadLinks, doc="First link on page")%}

        //---------------------------------------------------------------------
        // firstAnnot
        //---------------------------------------------------------------------
        PARENTCHECK(firstAnnot, """First annotation.""")
        %pythonappend firstAnnot %{
        if val:
            val.thisown = True
            val.parent = weakref.proxy(self) # owning page object
            self._annot_refs[id(val)] = val
        %}
        %pythoncode %{@property%}
        struct Annot *firstAnnot()
        {
            pdf_annot *annot = NULL;
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            if (page)
            {
                annot = pdf_first_annot(gctx, page);
                if (annot) pdf_keep_annot(gctx, annot);
            }
            return (struct Annot *) annot;
        }

        //---------------------------------------------------------------------
        // firstWidget
        //---------------------------------------------------------------------
        %pythoncode %{@property%}
        PARENTCHECK(firstWidget, """First widget/field.""")
        %pythonappend firstWidget %{
        if val:
            val.thisown = True
            val.parent = weakref.proxy(self) # owning page object
            self._annot_refs[id(val)] = val
            widget = Widget()
            TOOLS._fill_widget(val, widget)
            val = widget
        %}
        struct Annot *firstWidget()
        {
            pdf_annot *annot = NULL;
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            if (page)
            {
                annot = pdf_first_widget(gctx, page);
                if (annot) pdf_keep_annot(gctx, annot);
            }
            return (struct Annot *) annot;
        }


        //---------------------------------------------------------------------
        // Page.deleteLink() - delete link
        //---------------------------------------------------------------------
        PARENTCHECK(deleteLink, """Delete a Link.""")
        %pythonappend deleteLink
%{if linkdict["xref"] == 0: return
try:
    linkid = linkdict["id"]
    linkobj = self._annot_refs[linkid]
    linkobj._erase()
except:
    pass
%}
        void deleteLink(PyObject *linkdict)
        {
            if (!PyDict_Check(linkdict)) return; // have no dictionary
            fz_try(gctx) {
                pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
                if (!page) goto finished;  // have no PDF
                int xref = (int) PyInt_AsLong(PyDict_GetItem(linkdict, dictkey_xref));
                if (xref < 1) goto finished;  // invalid xref
                pdf_obj *annots = pdf_dict_get(gctx, page->obj, PDF_NAME(Annots));
                if (!annots) goto finished;  // have no annotations
                int len = pdf_array_len(gctx, annots);
                if (len == 0) goto finished;
                int i, oxref = 0;

                for (i = 0; i < len; i++) {
                    oxref = pdf_to_num(gctx, pdf_array_get(gctx, annots, i));
                    if (xref == oxref) break;        // found xref in annotations
                }

                if (xref != oxref) goto finished;  // xref not in annotations
                pdf_array_delete(gctx, annots, i);   // delete entry in annotations
                pdf_delete_object(gctx, page->doc, xref);      // delete link object
                pdf_dict_put(gctx, page->obj, PDF_NAME(Annots), annots);
                JM_refresh_link_table(gctx, page);  // reload link / annot tables
                page->doc->dirty = 1;
                finished:;
            }
            fz_catch(gctx) {;}
        }

        //---------------------------------------------------------------------
        // Page.deleteAnnot() - delete annotation and return the next one
        //---------------------------------------------------------------------
        %pythonprepend deleteAnnot %{
        """Delete annot and return next one."""
        CheckParent(self)
        CheckParent(annot)%}

        %pythonappend deleteAnnot %{
        if val:
            val.thisown = True
            val.parent = weakref.proxy(self) # owning page object
            val.parent._annot_refs[id(val)] = val
        annot._erase()
        %}

        struct Annot *deleteAnnot(struct Annot *annot)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            pdf_annot *irt_annot = NULL;
            while (1)  // first loop through all /IRT annots and remove them
            {
                irt_annot = JM_find_annot_irt(gctx, (pdf_annot *) annot);
                if (!irt_annot)  // no more there
                    break;
                JM_delete_annot(gctx, page, irt_annot);
            }
            pdf_annot *nextannot = pdf_next_annot(gctx, (pdf_annot *) annot);  // store next
            JM_delete_annot(gctx, page, (pdf_annot *) annot);
            if (nextannot)
            {
                nextannot = pdf_keep_annot(gctx, nextannot);
            }
            page->doc->dirty = 1;
            return (struct Annot *) nextannot;
        }


        //---------------------------------------------------------------------
        // MediaBox: get the /MediaBox (PDF only)
        //---------------------------------------------------------------------
        %pythoncode %{@property%}
        PARENTCHECK(MediaBox, """The MediaBox.""")
        %pythonappend MediaBox %{val = Rect(val)%}
        PyObject *MediaBox()
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            if (!page)
                return JM_py_from_rect(fz_bound_page(gctx, (fz_page *) $self));
            return JM_py_from_rect(JM_mediabox(gctx, page->obj));
        }


        //---------------------------------------------------------------------
        // CropBox: get the /CropBox (PDF only)
        //---------------------------------------------------------------------
        %pythoncode %{@property%}
        PARENTCHECK(CropBox, """The CropBox.""")
        %pythonappend CropBox %{val = Rect(val)%}
        PyObject *CropBox()
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            if (!page)
                return JM_py_from_rect(fz_bound_page(gctx, (fz_page *) $self));
            return JM_py_from_rect(JM_cropbox(gctx, page->obj));
        }


        //---------------------------------------------------------------------
        // CropBox position: x0, y0 of /CropBox
        //---------------------------------------------------------------------
        %pythoncode %{
        @property
        def CropBoxPosition(self):
            return self.CropBox.tl
        %}


        //---------------------------------------------------------------------
        // rotation - return page rotation
        //---------------------------------------------------------------------
        PARENTCHECK(rotation, """Page rotation.""")
        %pythoncode %{@property%}
        int rotation()
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            if (!page) return 0;
            return JM_page_rotation(gctx, page);
        }

        /*********************************************************************/
        // setRotation() - set page rotation
        /*********************************************************************/
        FITZEXCEPTION(setRotation, !result)
        PARENTCHECK(setRotation, """Set page rotation.""")
        PyObject *setRotation(int rotation)
        {
            fz_try(gctx) {
                pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
                ASSERT_PDF(page);
                int rot = JM_norm_rotation(rotation);
                pdf_dict_put_int(gctx, page->obj, PDF_NAME(Rotate), (int64_t) rot);
                page->doc->dirty = 1;
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        /*********************************************************************/
        // Page._addAnnot_FromString
        // Add new links provided as an array of string object definitions.
        /*********************************************************************/
        FITZEXCEPTION(_addAnnot_FromString, !result)
        PARENTCHECK(_addAnnot_FromString, """Add links from list of object sources.""")
        PyObject *_addAnnot_FromString(PyObject *linklist)
        {
            pdf_obj *annots, *annot, *ind_obj;
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            PyObject *txtpy = NULL;
            char *text = NULL;
            int lcount = (int) PySequence_Size(linklist); // link count
            if (lcount < 1) return_none;
            int i = -1;
            fz_var(text);

            // insert links from the provided sources
            fz_try(gctx) {
                ASSERT_PDF(page);
                if (!pdf_dict_get(gctx, page->obj, PDF_NAME(Annots))) {
                    pdf_dict_put_array(gctx, page->obj, PDF_NAME(Annots), lcount);
                }
                annots = pdf_dict_get(gctx, page->obj, PDF_NAME(Annots));
                for (i = 0; i < lcount; i++) {
                    text = NULL;
                    txtpy = PySequence_ITEM(linklist, (Py_ssize_t) i);
                    text = JM_Python_str_AsChar(txtpy);
                    Py_CLEAR(txtpy);
                    if (!text) THROWMSG(gctx, "bad linklist item");
                    annot = pdf_add_object_drop(gctx, page->doc,
                            JM_pdf_obj_from_str(gctx, page->doc, text));
                    JM_Python_str_DelForPy3(text);
                    ind_obj = pdf_new_indirect(gctx, page->doc, pdf_to_num(gctx, annot), 0);
                    pdf_array_push_drop(gctx, annots, ind_obj);
                    pdf_drop_obj(gctx, annot);
                }
            }
            fz_catch(gctx) {
                if (text) {
                    PySys_WriteStderr("%s (%i): '%s'\n", fz_caught_message(gctx), i, text);
                    JM_Python_str_DelForPy3(text);
                }
                else if (i >= 0) {
                    PySys_WriteStderr("%s (%i)\n", fz_caught_message(gctx), i);
                }
                PyErr_Clear();
                return NULL;
            }
            page->doc->dirty = 1;
            return_none;
        }

        //---------------------------------------------------------------------
        // Page._getLinkXrefs - get list of link xref numbers.
        // return_none for non-PDF
        //---------------------------------------------------------------------
        PyObject *_getLinkXrefs()
        {
            pdf_obj *annots, *annots_arr, *link, *obj;
            int i, lcount;
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            PyObject *linkxrefs = PyList_New(0);
            if (!page) return linkxrefs;  // empty list for non-PDF
            annots = pdf_dict_get(gctx, page->obj, PDF_NAME(Annots));
            if (!annots) return linkxrefs;  // no links on this page
            if (pdf_is_indirect(gctx, annots))
                annots_arr = pdf_resolve_indirect(gctx, annots);
            else
                annots_arr = annots;
            lcount = pdf_array_len(gctx, annots_arr);
            for (i = 0; i < lcount; i++)
            {
                link = pdf_array_get(gctx, annots_arr, i);
                obj = pdf_dict_get(gctx, link, PDF_NAME(Subtype));
                if (pdf_name_eq(gctx, obj, PDF_NAME(Link)))
                {
                    LIST_APPEND_DROP(linkxrefs, Py_BuildValue("i", pdf_to_num(gctx, link)));
                }
            }
            return linkxrefs;
        }

        //---------------------------------------------------------------------
        // Page clean contents stream
        //---------------------------------------------------------------------
        PARENTCHECK(_cleanContents, """Clean page /Contents object(s).""")
        PyObject *_cleanContents(int sanitize=0)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            if (!page) {
                return_none;
            }
            pdf_filter_options filter = {
                NULL,  // opaque
                NULL,  // image filter
                NULL,  // text filter
                NULL,  // after text
                NULL,  // end page
                1,     // recurse: true
                1,     // instance forms
                1,     // sanitize plus filtering
                0      // do not ascii-escape binary data
                };
            filter.sanitize = sanitize;
            fz_try(gctx) {
                pdf_filter_page_contents(gctx, page->doc, page, &filter);
            }
            fz_catch(gctx) {
                return_none;
            }
            page->doc->dirty = 1;
            return_none;
        }

        //---------------------------------------------------------------------
        // Show a PDF page
        //---------------------------------------------------------------------
        FITZEXCEPTION(_showPDFpage, !result)
        PyObject *_showPDFpage(struct Page *fz_srcpage, int overlay=1, PyObject *matrix=NULL, int xref=0, int oc=0, PyObject *clip = NULL, struct Graftmap *graftmap = NULL, char *_imgname = NULL)
        {
            pdf_obj *xobj1, *xobj2, *resources;
            fz_buffer *res=NULL, *nres=NULL;
            fz_rect cropbox = JM_rect_from_py(clip);
            fz_matrix mat = JM_matrix_from_py(matrix);
            int rc_xref = xref;
            fz_try(gctx) {
                pdf_page *tpage = pdf_page_from_fz_page(gctx, (fz_page *) $self);
                pdf_obj *tpageref = tpage->obj;
                pdf_document *pdfout = tpage->doc;    // target PDF

                //-------------------------------------------------------------
                // convert the source page to a Form XObject
                //-------------------------------------------------------------
                xobj1 = JM_xobject_from_page(gctx, pdfout, (fz_page *) fz_srcpage,
                                             xref, (pdf_graft_map *) graftmap);
                if (!rc_xref) rc_xref = pdf_to_num(gctx, xobj1);

                //-------------------------------------------------------------
                // create referencing XObject (controls display on target page)
                //-------------------------------------------------------------
                // fill reference to xobj1 into the /Resources
                //-------------------------------------------------------------
                pdf_obj *subres1 = pdf_new_dict(gctx, pdfout, 5);
                pdf_dict_puts(gctx, subres1, "fullpage", xobj1);
                pdf_obj *subres  = pdf_new_dict(gctx, pdfout, 5);
                pdf_dict_put_drop(gctx, subres, PDF_NAME(XObject), subres1);

                res = fz_new_buffer(gctx, 20);
                fz_append_string(gctx, res, "/fullpage Do");

                xobj2 = pdf_new_xobject(gctx, pdfout, cropbox, mat, subres, res);
                if (oc > 0) {
                    JM_add_oc_object(gctx, pdfout, pdf_resolve_indirect(gctx, xobj2), oc);
                }
                pdf_drop_obj(gctx, subres);
                fz_drop_buffer(gctx, res);

                //-------------------------------------------------------------
                // update target page with xobj2:
                //-------------------------------------------------------------
                // 1. insert Xobject in Resources
                //-------------------------------------------------------------
                resources = pdf_dict_get_inheritable(gctx, tpageref, PDF_NAME(Resources));
                subres = pdf_dict_get(gctx, resources, PDF_NAME(XObject));
                if (!subres) {
                    subres = pdf_dict_put_dict(gctx, resources, PDF_NAME(XObject), 5);
                }

                pdf_dict_puts(gctx, subres, _imgname, xobj2);

                //-------------------------------------------------------------
                // 2. make and insert new Contents object
                //-------------------------------------------------------------
                nres = fz_new_buffer(gctx, 50);       // buffer for Do-command
                fz_append_string(gctx, nres, " q /");    // Do-command
                fz_append_string(gctx, nres, _imgname);
                fz_append_string(gctx, nres, " Do Q ");

                JM_insert_contents(gctx, pdfout, tpageref, nres, overlay);
                fz_drop_buffer(gctx, nres);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return Py_BuildValue("i", rc_xref);
        }

        //---------------------------------------------------------------------
        // insert an image
        //---------------------------------------------------------------------
        FITZEXCEPTION(_insertImage, !result)
        PyObject *_insertImage(const char *filename=NULL, struct Pixmap *pixmap=NULL, PyObject *stream=NULL, PyObject *imask=NULL, int overlay=1, int oc=0, int xref = 0, PyObject *matrix=NULL,
        const char *_imgname=NULL, PyObject *_imgpointer=NULL)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            pdf_document *pdf;
            fz_pixmap *pm = NULL;
            fz_pixmap *pix = NULL;
            fz_image *mask = NULL;
            fz_separations *seps = NULL;
            pdf_obj *resources, *xobject, *ref;
            fz_buffer *nres = NULL,  *imgbuf = NULL, *maskbuf = NULL;
            fz_matrix mat = JM_matrix_from_py(matrix); // pre-calculated
            fz_compressed_buffer *cbuf1 = NULL;
            int img_xref = 0;

            const char *template = "\nq\n%g %g %g %g %g %g cm\n/%s Do\nQ\n";
            fz_image *zimg = NULL, *image = NULL;
            fz_try(gctx) {
                if (xref > 0) {
                    goto image_exists;
                }
                //-------------------------------------------------------------
                // create the image
                //-------------------------------------------------------------
                if (filename || EXISTS(stream) || EXISTS(_imgpointer))
                {
                    if (filename) {
                        image = fz_new_image_from_file(gctx, filename);
                    } else if (EXISTS(stream)) {
                        imgbuf = JM_BufferFromBytes(gctx, stream);
                        image = fz_new_image_from_buffer(gctx, imgbuf);
                    } else {  // fz_image pointer has been handed in
                        image = (fz_image *)PyLong_AsVoidPtr(_imgpointer);
                    }
                    int xres, yres, w = image->w, h = image->h, bpc = image->bpc;
                    fz_colorspace *colorspace = image->colorspace;
                    fz_image_resolution(image, &xres, &yres);
                    if (EXISTS(imask)) {
                        cbuf1 = fz_compressed_image_buffer(gctx, image);
                        if (!cbuf1) THROWMSG(gctx, "cannot mask uncompressed image");
                        maskbuf = JM_BufferFromBytes(gctx, imask);
                        mask = fz_new_image_from_buffer(gctx, maskbuf);
                        zimg = fz_new_image_from_compressed_buffer(gctx, w, h,
                                    bpc, colorspace, xres, yres, 1, 0, NULL,
                                    NULL, cbuf1, mask);
                        fz_drop_image(gctx, image);
                        image = zimg;
                        zimg = NULL;
                    } else {
                        pix = fz_get_pixmap_from_image(gctx, image, NULL, NULL, 0, 0);
                        pix->xres = xres;
                        pix->yres = yres;
                        if (pix->alpha == 1) {  // have alpha: create an SMask
                            pm = fz_convert_pixmap(gctx, pix, NULL, NULL, NULL, fz_default_color_params, 1);
                            pm->alpha = 0;
                            pm->colorspace = fz_keep_colorspace(gctx, fz_device_gray(gctx));
                            mask = fz_new_image_from_pixmap(gctx, pm, NULL);
                            zimg = fz_new_image_from_pixmap(gctx, pix, mask);
                            fz_drop_image(gctx, image);
                            image = zimg;
                            zimg = NULL;
                        } else {
                            fz_drop_pixmap(gctx, pix);
                            pix = NULL;
                        }
                    }
                } else {  // pixmap specified
                    fz_pixmap *arg_pix = (fz_pixmap *) pixmap;
                    if (arg_pix->alpha == 0) {
                        image = fz_new_image_from_pixmap(gctx, arg_pix, NULL);
                    } else {  // pixmap has alpha: create an SMask
                        pm = fz_convert_pixmap(gctx, arg_pix, NULL, NULL, NULL, fz_default_color_params, 1);
                        pm->alpha = 0;
                        pm->colorspace = fz_keep_colorspace(gctx, fz_device_gray(gctx));
                        mask = fz_new_image_from_pixmap(gctx, pm, NULL);
                        image = fz_new_image_from_pixmap(gctx, arg_pix, mask);
                    }
                }

                //-------------------------------------------------------------
                // image created - now put it in the PDF
                //-------------------------------------------------------------
                image_exists:;
                pdf = page->doc;  // owning PDF

                // get /Resources, /XObject
                resources = pdf_dict_get_inheritable(gctx, page->obj, PDF_NAME(Resources));
                xobject = pdf_dict_get(gctx, resources, PDF_NAME(XObject));
                if (!xobject) {  // has no XObject yet, create one
                    xobject = pdf_dict_put_dict(gctx, resources, PDF_NAME(XObject), 5);
                }
                if (xref > 0) {
                    ref = pdf_new_indirect(gctx, page->doc, xref, 0);
                    img_xref = xref;
                } else {
                    ref = pdf_add_image(gctx, pdf, image);
                    img_xref = pdf_to_num(gctx, ref);
                }
                if (oc) JM_add_oc_object(gctx, pdf, ref, oc);
                
                pdf_dict_puts_drop(gctx, xobject, _imgname, ref);  // update XObject
                // make contents stream that invokes the image
                nres = fz_new_buffer(gctx, 50);
                fz_append_printf(gctx, nres, template,
                                 mat.a, mat.b, mat.c, mat.d, mat.e, mat.f,
                                 _imgname);
                JM_insert_contents(gctx, pdf, page->obj, nres, overlay);
                fz_drop_buffer(gctx, nres);
                nres = NULL;
            }
            fz_always(gctx) {
                fz_drop_image(gctx, image);
                fz_drop_image(gctx, mask);
                fz_drop_image(gctx, zimg);
                fz_drop_pixmap(gctx, pix);
                fz_drop_pixmap(gctx, pm);
                fz_drop_buffer(gctx, imgbuf);
                fz_drop_buffer(gctx, maskbuf);
                fz_drop_buffer(gctx, nres);
            }
            fz_catch(gctx) {
                return NULL;
            }
            pdf->dirty = 1;
            return Py_BuildValue("i", img_xref);
        }

        //---------------------------------------------------------------------
        // Page.refresh()
        //---------------------------------------------------------------------
        FITZEXCEPTION(refresh, !result)
        PARENTCHECK(refresh, """Refresh page after link/annot/widget updates.""")
        PyObject *refresh()
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            if (!page) return_none;
            fz_try(gctx) {
                JM_refresh_link_table(gctx, page);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }


        //---------------------------------------------------------------------
        // insert font
        //---------------------------------------------------------------------
        %pythoncode
%{
def insertFont(self, fontname="helv", fontfile=None, fontbuffer=None,
               set_simple=False, wmode=0, encoding=0):
    doc = self.parent
    if doc is None:
        raise ValueError("orphaned object: parent is None")
    idx = 0

    if fontname.startswith("/"):
        fontname = fontname[1:]

    font = CheckFont(self, fontname)
    if font is not None:                    # font already in font list of page
        xref = font[0]                      # this is the xref
        if CheckFontInfo(doc, xref):        # also in our document font list?
            return xref                     # yes: we are done
        # need to build the doc FontInfo entry - done via getCharWidths
        doc.getCharWidths(xref)
        return xref

    #--------------------------------------------------------------------------
    # the font is not present for this page
    #--------------------------------------------------------------------------

    bfname = Base14_fontdict.get(fontname.lower(), None) # BaseFont if Base-14 font

    serif = 0
    CJK_number = -1
    CJK_list_n = ["china-t", "china-s", "japan", "korea"]
    CJK_list_s = ["china-ts", "china-ss", "japan-s", "korea-s"]

    try:
        CJK_number = CJK_list_n.index(fontname)
        serif = 0
    except:
        pass

    if CJK_number < 0:
        try:
            CJK_number = CJK_list_s.index(fontname)
            serif = 1
        except:
            pass

    if fontname.lower() in fitz_fontdescriptors.keys():
        # one of the extra fonts
        import pymupdf_fonts
        fontbuffer = pymupdf_fonts.myfont(fontname)  # make a copy
        del pymupdf_fonts

    # install the font for the page
    val = self._insertFont(fontname, bfname, fontfile, fontbuffer, set_simple, idx,
                           wmode, serif, encoding, CJK_number)

    if not val:                   # did not work, error return
        return val

    xref = val[0]                 # xref of installed font

    if CheckFontInfo(doc, xref):  # check again: document already has this font
        return xref               # we are done

    # need to create document font info
    doc.getCharWidths(xref)
    return xref

%}

        FITZEXCEPTION(_insertFont, !result)
        PyObject *_insertFont(char *fontname, char *bfname,
                             char *fontfile,
                             PyObject *fontbuffer,
                             int set_simple, int idx,
                             int wmode, int serif,
                             int encoding, int ordering)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            pdf_document *pdf;
            pdf_obj *resources, *fonts, *font_obj;
            fz_font *font = NULL;
            fz_buffer *res = NULL;
            const unsigned char *data = NULL;
            int size, ixref = 0, index = 0, simple = 0;
            PyObject *value;
            PyObject *exto = NULL;
            fz_try(gctx) {
                ASSERT_PDF(page);
                pdf = page->doc;
                // get the objects /Resources, /Resources/Font
                resources = pdf_dict_get_inheritable(gctx, page->obj, PDF_NAME(Resources));
                fonts = pdf_dict_get(gctx, resources, PDF_NAME(Font));
                if (!fonts) {  // page has no fonts yet
                    fonts = pdf_new_dict(gctx, pdf, 10);
                    pdf_dict_putl_drop(gctx, page->obj, fonts, PDF_NAME(Resources), PDF_NAME(Font), NULL);
                }

                //-------------------------------------------------------------
                // check for CJK font
                //-------------------------------------------------------------
                if (ordering > -1) data = fz_lookup_cjk_font(gctx, ordering, &size, &index);
                if (data) {
                    font = fz_new_font_from_memory(gctx, NULL, data, size, index, 0);
                    font_obj = pdf_add_cjk_font(gctx, pdf, font, ordering, wmode, serif);
                    exto = JM_UnicodeFromStr("n/a");
                    simple = 0;
                    goto weiter;
                }

                //-------------------------------------------------------------
                // check for PDF Base-14 font
                //-------------------------------------------------------------
                if (bfname) data = fz_lookup_base14_font(gctx, bfname, &size);
                if (data) {
                    font = fz_new_font_from_memory(gctx, bfname, data, size, 0, 0);
                    font_obj = pdf_add_simple_font(gctx, pdf, font, encoding);
                    exto = JM_UnicodeFromStr("n/a");
                    simple = 1;
                    goto weiter;
                }

                if (fontfile) {
                    font = fz_new_font_from_file(gctx, NULL, fontfile, idx, 0);
                } else {
                    res = JM_BufferFromBytes(gctx, fontbuffer);
                    if (!res) THROWMSG(gctx, "need one of fontfile, fontbuffer");
                    font = fz_new_font_from_buffer(gctx, NULL, res, idx, 0);
                }

                if (!set_simple) {
                    font_obj = pdf_add_cid_font(gctx, pdf, font);
                    simple = 0;
                } else {
                    font_obj = pdf_add_simple_font(gctx, pdf, font, encoding);
                    simple = 2;
                }

                weiter: ;
                ixref = pdf_to_num(gctx, font_obj);
                if (fz_font_is_monospaced(gctx, font)) {
                    float adv = fz_advance_glyph(gctx, font,
                                    fz_encode_character(gctx, font, 32), 0);
                    int width = (int) floor(adv * 1000.0f + 0.5f);
                    pdf_obj *dfonts = pdf_dict_get(gctx, font_obj, PDF_NAME(DescendantFonts));
                    if (pdf_is_array(gctx, dfonts)) {
                        int i, n = pdf_array_len(gctx, dfonts);
                        for (i = 0; i < n; i++) {
                            pdf_obj *dfont = pdf_array_get(gctx, dfonts, i);
                            pdf_obj *warray = pdf_new_array(gctx, pdf, 3);
                            pdf_array_push(gctx, warray, pdf_new_int(gctx, 0));
                            pdf_array_push(gctx, warray, pdf_new_int(gctx, 65535));
                            pdf_array_push(gctx, warray, pdf_new_int(gctx, (int64_t) width));
                            pdf_dict_put_drop(gctx, dfont, PDF_NAME(W), warray);
                        }
                    }
                }
                PyObject *name = JM_EscapeStrFromStr(pdf_to_name(gctx,
                            pdf_dict_get(gctx, font_obj, PDF_NAME(BaseFont))));

                PyObject *subt = JM_UnicodeFromStr(pdf_to_name(gctx,
                            pdf_dict_get(gctx, font_obj, PDF_NAME(Subtype))));

                if (!exto)
                    exto = JM_UnicodeFromStr(JM_get_fontextension(gctx, pdf, ixref));

                value = Py_BuildValue("[i, {s:O, s:O, s:O, s:O, s:i}]",
                                      ixref,
                                      "name", name,        // base font name
                                      "type", subt,        // subtype
                                      "ext", exto,         // file extension
                                      "simple", JM_BOOL(simple), // simple font?
                                      "ordering", ordering); // CJK font?
                Py_CLEAR(exto);
                Py_CLEAR(name);
                Py_CLEAR(subt);

                // store font in resources and fonts objects will contain named reference to font
                pdf_dict_puts_drop(gctx, fonts, fontname, font_obj);
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, res);
                fz_drop_font(gctx, font);
            }
            fz_catch(gctx) {
                return NULL;
            }
            pdf->dirty = 1;
            return value;
        }

        //---------------------------------------------------------------------
        // Get page transformation matrix
        //---------------------------------------------------------------------
        %pythoncode %{@property%}
        PARENTCHECK(transformationMatrix, """Page transformation matrix.""")
        %pythonappend transformationMatrix %{
        if self.rotation % 360 == 0:
            val = Matrix(val)
        else:
            val = Matrix(1, 0, 0, -1, 0, self.CropBox.height)
        %}
        PyObject *transformationMatrix()
        {
            fz_matrix ctm = fz_identity;
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            if (!page) return JM_py_from_matrix(ctm);
            fz_try(gctx) {
                pdf_page_transform(gctx, page, NULL, &ctm);
            }
            fz_catch(gctx) {;}
            return JM_py_from_matrix(ctm);
        }

        //---------------------------------------------------------------------
        // Page Get list of contents objects
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getContents, !result)
        PARENTCHECK(_getContents, """Get xref list of /Contents objects.""")
        PyObject *_getContents()
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            PyObject *list = NULL;
            pdf_obj *contents = NULL, *icont = NULL;
            int i, xref;
            size_t n = 0;
            fz_try(gctx) {
                ASSERT_PDF(page);
                contents = pdf_dict_get(gctx, page->obj, PDF_NAME(Contents));
                if (pdf_is_array(gctx, contents)) {
                    n = pdf_array_len(gctx, contents);
                    list = PyList_New(n);
                    for (i = 0; i < n; i++) {
                        icont = pdf_array_get(gctx, contents, i);
                        xref = pdf_to_num(gctx, icont);
                        PyList_SET_ITEM(list, i, Py_BuildValue("i", xref));
                    }
                }
                else if (contents) {
                    list = PyList_New(1);
                    xref = pdf_to_num(gctx, contents);
                    PyList_SET_ITEM(list, 0, Py_BuildValue("i", xref));
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            if (list) {
                return list;
            }
            return PyList_New(0);
        }

        //---------------------------------------------------------------------
        // Set given object as the /Contents of a page
        //---------------------------------------------------------------------
        FITZEXCEPTION(_setContents, !result)
        PARENTCHECK(_setContents, """Set bytes as the (only) /Contents object.""")
        PyObject *_setContents(int xref = 0)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) $self);
            pdf_obj *contents = NULL;

            fz_try(gctx) {
                ASSERT_PDF(page);

                if (!INRANGE(xref, 1, pdf_xref_len(gctx, page->doc) - 1))
                    THROWMSG(gctx, "bad xref");

                contents = pdf_new_indirect(gctx, page->doc, xref, 0);
                if (!pdf_is_stream(gctx, contents))
                    THROWMSG(gctx, "no stream at xref");

                pdf_dict_put_drop(gctx, page->obj, PDF_NAME(Contents), contents);
            }
            fz_catch(gctx) {
                return NULL;
            }
            page->doc->dirty = 1;
            return_none;
        }

        %pythoncode %{
        @property
        def _isWrapped(self):
            """Check if /Contents is wrapped in string pair "q" / "Q".
            """
            cont = self.readContents().split()
            if len(cont) < 1 or cont[0] != b"q" or cont[-1] != b"Q":
                return False
            return True

        def _wrapContents(self):
            TOOLS._insert_contents(self, b"q\n", False)
            TOOLS._insert_contents(self, b"\nQ", True)

        wrapContents = _wrapContents


        def links(self, kinds=None):
            """ Generator over the links of a page.

            Args:
                kinds: (tuple) link kinds to subselect from. If none,
                        all links are returned. E.g. kinds=(LINK_URI,)
                        will only yield URI links.
            """
            all_links = self.getLinks()
            for link in all_links:
                if kinds is None or link["kind"] in kinds:
                    yield (link)


        def annots(self, types=None):
            """ Generator over the annotations of a page.

            Args:
                types: (tuple) annotation types to subselect from. If none,
                        all annotations are returned. E.g. types=(PDF_ANNOT_LINE,)
                        will only yield line annotations.
            """
            annot = self.firstAnnot
            while annot:
                if types is None or annot.type[0] in types:
                    yield (annot)
                annot = annot.next


        def widgets(self, types=None):
            """ Generator over the widgets of a page.

            Args:
                types: (tuple) field types to subselect from. If none,
                        all fields are returned. E.g. types=(PDF_WIDGET_TYPE_TEXT,)
                        will only yield text fields.
            """
            widget = self.firstWidget
            while widget:
                if types is None or widget.field_type in types:
                    yield (widget)
                widget = widget.next


        def __str__(self):
            CheckParent(self)
            x = self.parent.name
            if self.parent.stream is not None:
                x = "<memory, doc# %i>" % (self.parent._graft_id,)
            if x == "":
                x = "<new PDF, doc# %i>" % self.parent._graft_id
            return "page %s of %s" % (self.number, x)

        def __repr__(self):
            CheckParent(self)
            x = self.parent.name
            if self.parent.stream is not None:
                x = "<memory, doc# %i>" % (self.parent._graft_id,)
            if x == "":
                x = "<new PDF, doc# %i>" % self.parent._graft_id
            return "page %s of %s" % (self.number, x)

        def _forget_annot(self, annot):
            """Remove an annot from reference dictionary."""
            aid = id(annot)
            if aid in self._annot_refs:
                self._annot_refs[aid] = None

        def _reset_annot_refs(self):
            """Invalidate / delete all annots of this page."""
            for annot in self._annot_refs.values():
                if annot:
                    annot._erase()
            self._annot_refs.clear()

        @property
        def xref(self):
            """PDF xref number of page."""
            CheckParent(self)
            return self.parent._getPageXref(self.number)[0]

        def _erase(self):
            self._reset_annot_refs()
            try:
                self.parent._forget_page(self)
            except:
                pass
            if getattr(self, "thisown", False):
                self.__swig_destroy__(self)
            self.parent = None
            self.thisown = False
            self.number = None

        def __del__(self):
            self._erase()

        def getFontList(self, full=False):
            """List of fonts defined in the page object."""
            CheckParent(self)
            return self.parent.getPageFontList(self.number, full=full)

        def getImageList(self, full=False):
            """List of images defined in the page object."""
            CheckParent(self)
            return self.parent.getPageImageList(self.number, full=full)


        def readContents(self):
            """All /Contents streams concatenated in one bytes object."""
            return TOOLS._get_all_contents(self)


        @property
        def MediaBoxSize(self):
            return Point(self.MediaBox.width, self.MediaBox.height)

        def cleanContents(self, sanitize=True):
            if not sanitize and not self._isWrapped:
                self.wrapContents()
            self._cleanContents(sanitize)

        getContents = _getContents
        %}
    }
};
%clearnodefaultctor;

//-----------------------------------------------------------------------------
// Pixmap
//-----------------------------------------------------------------------------
struct Pixmap
{
    %extend {
        ~Pixmap() {
            DEBUGMSG1("Pixmap");
            fz_pixmap *this_pix = (fz_pixmap *) $self;
            fz_drop_pixmap(gctx, this_pix);
            DEBUGMSG2;
        }
        FITZEXCEPTION(Pixmap, !result)
        %pythonprepend Pixmap
%{"""Pixmap(colorspace, irect, alpha) - empty pixmap.
Pixmap(colorspace, src) - copy changing colorspace.
Pixmap(src, width, height,[clip]) - scaled copy, float dimensions.
Pixmap(src, alpha=1) - copy and add or drop alpha channel.
Pixmap(filename) - from an image in a file.
Pixmap(image) - from an image in memory (bytes).
Pixmap(colorspace, width, height, samples, alpha) - from samples data.
Pixmap(PDFdoc, xref) - from an image at xref in a PDF document.
"""%}
        //---------------------------------------------------------------------
        // create empty pixmap with colorspace and IRect
        //---------------------------------------------------------------------
        Pixmap(struct Colorspace *cs, PyObject *bbox, int alpha = 0)
        {
            fz_pixmap *pm = NULL;
            fz_try(gctx) {
                pm = fz_new_pixmap_with_bbox(gctx, (fz_colorspace *) cs, JM_irect_from_py(bbox), NULL, alpha);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct Pixmap *) pm;
        }

        //---------------------------------------------------------------------
        // copy pixmap, converting colorspace
        // New in v1.11: option to remove alpha
        // Changed in v1.13: alpha = 0 does not work since at least v1.12
        //---------------------------------------------------------------------
        Pixmap(struct Colorspace *cs, struct Pixmap *spix)
        {
            fz_pixmap *pm = NULL;
            fz_try(gctx) {
                if (!fz_pixmap_colorspace(gctx, (fz_pixmap *) spix))
                    THROWMSG(gctx, "cannot copy pixmap with NULL colorspace");
                pm = fz_convert_pixmap(gctx, (fz_pixmap *) spix, (fz_colorspace *) cs, NULL, NULL, fz_default_color_params, 1);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct Pixmap *) pm;
        }


        //---------------------------------------------------------------------
        // create pixmap as scaled copy of another one
        //---------------------------------------------------------------------
        Pixmap(struct Pixmap *spix, float w, float h, PyObject *clip=NULL)
        {
            fz_pixmap *pm = NULL;
            fz_pixmap *src_pix = (fz_pixmap *) spix;
            fz_try(gctx) {
                fz_irect bbox = JM_irect_from_py(clip);
                if (!fz_is_infinite_irect(bbox)) {
                    pm = fz_scale_pixmap(gctx, src_pix, src_pix->x, src_pix->y, w, h, &bbox);
                } else {
                    pm = fz_scale_pixmap(gctx, src_pix, src_pix->x, src_pix->y, w, h, NULL);
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct Pixmap *) pm;
        }


        //---------------------------------------------------------------------
        // copy pixmap & add / drop the alpha channel
        //---------------------------------------------------------------------
        Pixmap(struct Pixmap *spix, int alpha=1)
        {
            fz_pixmap *pm = NULL, *src_pix = (fz_pixmap *) spix;
            int n, w, h, i;
            fz_separations *seps = NULL;
            fz_try(gctx) {
                if (!INRANGE(alpha, 0, 1))
                    THROWMSG(gctx, "bad alpha value");
                fz_colorspace *cs = fz_pixmap_colorspace(gctx, src_pix);
                if (!cs && !alpha)
                    THROWMSG(gctx, "cannot drop alpha for 'NULL' colorspace");
                n = fz_pixmap_colorants(gctx, src_pix);
                w = fz_pixmap_width(gctx, src_pix);
                h = fz_pixmap_height(gctx, src_pix);
                pm = fz_new_pixmap(gctx, cs, w, h, seps, alpha);
                pm->x = src_pix->x;
                pm->y = src_pix->y;
                pm->xres = src_pix->xres;
                pm->yres = src_pix->yres;

                // copy samples data ------------------------------------------
                unsigned char *sptr = src_pix->samples;
                unsigned char *tptr = pm->samples;
                if (src_pix->alpha == pm->alpha) {  // identical samples
                    memcpy(tptr, sptr, w * h * (n + alpha));
                } else {
                    for (i = 0; i < w * h; i++) {
                        memcpy(tptr, sptr, n);
                        tptr += n;
                        if (pm->alpha) {
                            tptr[0] = 255;
                            tptr++;
                        }
                        sptr += n + src_pix->alpha;
                    }
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct Pixmap *) pm;
        }

        //---------------------------------------------------------------------
        // create pixmap from samples data
        //---------------------------------------------------------------------
        Pixmap(struct Colorspace *cs, int w, int h, PyObject *samples, int alpha=0)
        {
            int n = fz_colorspace_n(gctx, (fz_colorspace *) cs);
            int stride = (n + alpha)*w;
            fz_separations *seps = NULL;
            fz_buffer *res = NULL;
            fz_pixmap *pm = NULL;
            fz_try(gctx) {
                size_t size = 0;
                unsigned char *c = NULL;
                res = JM_BufferFromBytes(gctx, samples);
                if (!res) THROWMSG(gctx, "bad samples data");
                size = fz_buffer_storage(gctx, res, &c);
                if (stride * h != size) THROWMSG(gctx, "bad samples length");
                pm = fz_new_pixmap(gctx, (fz_colorspace *) cs, w, h, seps, alpha);
                memcpy(pm->samples, c, size);
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct Pixmap *) pm;
        }

        //---------------------------------------------------------------------
        // create pixmap from filename
        //---------------------------------------------------------------------
        Pixmap(char *filename)
        {
            fz_image *img = NULL;
            fz_pixmap *pm = NULL;
            fz_try(gctx) {
                img = fz_new_image_from_file(gctx, filename);
                pm = fz_get_pixmap_from_image(gctx, img, NULL, NULL, NULL, NULL);
                int xres, yres;
                fz_image_resolution(img, &xres, &yres);
                pm->xres = xres;
                pm->yres = yres;
            }
            fz_always(gctx) {
                fz_drop_image(gctx, img);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct Pixmap *) pm;
        }

        //---------------------------------------------------------------------
        // create pixmap from in-memory image
        //---------------------------------------------------------------------
        Pixmap(PyObject *imagedata)
        {
            fz_buffer *res = NULL;
            fz_image *img = NULL;
            fz_pixmap *pm = NULL;
            fz_try(gctx) {
                res = JM_BufferFromBytes(gctx, imagedata);
                if (!res) THROWMSG(gctx, "bad image data");
                img = fz_new_image_from_buffer(gctx, res);
                pm = fz_get_pixmap_from_image(gctx, img, NULL, NULL, NULL, NULL);
                int xres, yres;
                fz_image_resolution(img, &xres, &yres);
                pm->xres = xres;
                pm->yres = yres;
            }
            fz_always(gctx) {
                fz_drop_image(gctx, img);
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct Pixmap *) pm;
        }


        //---------------------------------------------------------------------
        // Create pixmap from PDF image identified by XREF number
        //---------------------------------------------------------------------
        Pixmap(struct Document *doc, int xref)
        {
            fz_image *img = NULL;
            fz_pixmap *pix = NULL;
            pdf_obj *ref = NULL;
            pdf_obj *type;
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) doc);
            fz_try(gctx) {
                ASSERT_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if (!INRANGE(xref, 1, xreflen-1))
                    THROWMSG(gctx, "bad xref");
                ref = pdf_new_indirect(gctx, pdf, xref, 0);
                type = pdf_dict_get(gctx, ref, PDF_NAME(Subtype));
                if (!pdf_name_eq(gctx, type, PDF_NAME(Image)))
                    THROWMSG(gctx, "not an image");
                img = pdf_load_image(gctx, pdf, ref);
                pix = fz_get_pixmap_from_image(gctx, img, NULL, NULL, NULL, NULL);
            }
            fz_always(gctx) {
                fz_drop_image(gctx, img);
                pdf_drop_obj(gctx, ref);
            }
            fz_catch(gctx) {
                fz_drop_pixmap(gctx, pix);
                return NULL;
            }
            return (struct Pixmap *) pix;
        }


        //---------------------------------------------------------------------
        // shrink
        //---------------------------------------------------------------------
        %pythonprepend shrink
%{"""Divide width and height by 2**factor.
E.g. factor=1 shrinks to 25% of original size (in place)."""%}
        void shrink(int factor)
        {
            if (factor < 1)
            {
                JM_Warning("ignoring shrink factor < 1");
                return;
            }
            fz_subsample_pixmap(gctx, (fz_pixmap *) $self, factor);
        }

        //---------------------------------------------------------------------
        // apply gamma correction
        //---------------------------------------------------------------------
        %pythonprepend gammaWith
%{"""Apply correction with some float.
gamma=1 is a no-op."""}
        void gammaWith(float gamma)
        {
            if (!fz_pixmap_colorspace(gctx, (fz_pixmap *) $self))
            {
                JM_Warning("colorspace invalid for function");
                return;
            }
            fz_gamma_pixmap(gctx, (fz_pixmap *) $self, gamma);
        }

        //---------------------------------------------------------------------
        // tint pixmap with color
        //---------------------------------------------------------------------
        %pythonprepend tintWith
%{"""Tint colors with modifiers for black and white."""

if not self.colorspace or self.colorspace.n > 3:
    print("warning: colorspace invalid for function")
    return%}
        void tintWith(int black, int white)
        {
            fz_tint_pixmap(gctx, (fz_pixmap *) $self, black, white);
        }

        //----------------------------------------------------------------------
        // clear all of pixmap samples to 0x00 */
        //----------------------------------------------------------------------
        %pythonprepend clearWith
        %{"""Fill all color components with same value."""%}
        void clearWith()
        {
            fz_clear_pixmap(gctx, (fz_pixmap *) $self);
        }

        //----------------------------------------------------------------------
        // clear total pixmap with value */
        //----------------------------------------------------------------------
        void clearWith(int value)
        {
            fz_clear_pixmap_with_value(gctx, (fz_pixmap *) $self, value);
        }

        //----------------------------------------------------------------------
        // clear pixmap rectangle with value
        //----------------------------------------------------------------------
        void clearWith(int value, PyObject *bbox)
        {
            JM_clear_pixmap_rect_with_value(gctx, (fz_pixmap *) $self, value, JM_irect_from_py(bbox));
        }

        //----------------------------------------------------------------------
        // copy pixmaps
        //----------------------------------------------------------------------
        FITZEXCEPTION(copyPixmap, !result)
        %pythonprepend copyPixmap %{"""Copy bbox from another Pixmap."""%}
        PyObject *copyPixmap(struct Pixmap *src, PyObject *bbox)
        {
            fz_try(gctx) {
                fz_pixmap *pm = (fz_pixmap *) $self, *src_pix = (fz_pixmap *) src;
                if (!fz_pixmap_colorspace(gctx, src_pix))
                    THROWMSG(gctx, "cannot copy pixmap with NULL colorspace");
                if (pm->alpha != src_pix->alpha)
                    THROWMSG(gctx, "source and target alpha must be equal");
                fz_copy_pixmap_rect(gctx, pm, src_pix, JM_irect_from_py(bbox), NULL);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        //----------------------------------------------------------------------
        // set alpha values
        //----------------------------------------------------------------------
        FITZEXCEPTION(setAlpha, !result)
        %pythonprepend setAlpha
%{"""Set alphas to values contained in a byte array.
If omitted, set alphas to 255."""%}
        PyObject *setAlpha(PyObject *alphavalues=NULL, int premultiply=1)
        {
            fz_buffer *res = NULL;
            fz_pixmap *pix = (fz_pixmap *) $self;
            fz_try(gctx) {
                if (pix->alpha == 0) THROWMSG(gctx, "pixmap has no alpha");
                size_t n = fz_pixmap_colorants(gctx, pix);
                size_t w = fz_pixmap_width(gctx, pix);
                size_t h = fz_pixmap_height(gctx, pix);
                size_t balen = w * h * (n+1);
                unsigned char *data = NULL;
                size_t data_len = 0;
                if (alphavalues) {
                    res = JM_BufferFromBytes(gctx, alphavalues);
                    if (res) {
                        data_len = fz_buffer_storage(gctx, res, &data);
                        if (data && data_len < w * h)
                            THROWMSG(gctx, "not enough alpha values");
                    }
                    else THROWMSG(gctx, "bad type: 'alphavalues'");
                }
                size_t i = 0, k = 0, j = 0;
                while (i < balen) {
                    if (data_len) {
                        pix->samples[i+n] = data[k];
                        if (premultiply) {
                            for (j = i; j < n; j++) {
                                pix->samples[j] = pix->samples[j] * data[k] / 255 * data[k] / 255;
                            }
                        }
                    } else {
                        pix->samples[i+n] = 255;
                    }
                    i += n+1;
                    k += 1;
                }
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        //----------------------------------------------------------------------
        // Pixmap._getImageData
        //----------------------------------------------------------------------
        FITZEXCEPTION(_getImageData, !result)
        PyObject *_getImageData(int format)
        {
            fz_output *out = NULL;
            fz_buffer *res = NULL;
            PyObject *barray = NULL;
            fz_pixmap *pm = (fz_pixmap *) $self;
            fz_try(gctx) {
                size_t size = fz_pixmap_stride(gctx, pm) * pm->h;
                res = fz_new_buffer(gctx, size);
                out = fz_new_output_with_buffer(gctx, res);

                switch(format) {
                    case(1):
                        fz_write_pixmap_as_png(gctx, out, pm);
                        break;
                    case(2):
                        fz_write_pixmap_as_pnm(gctx, out, pm);
                        break;
                    case(3):
                        fz_write_pixmap_as_pam(gctx, out, pm);
                        break;
                    case(5):           // Adobe Photoshop Document
                        fz_write_pixmap_as_psd(gctx, out, pm);
                        break;
                    case(6):           // Postscript format
                        fz_write_pixmap_as_ps(gctx, out, pm);
                        break;
                    default:
                        fz_write_pixmap_as_png(gctx, out, pm);
                        break;
                }
                barray = JM_BinFromBuffer(gctx, res);
            }
            fz_always(gctx) {
                fz_drop_output(gctx, out);
                fz_drop_buffer(gctx, res);
            }

            fz_catch(gctx) {
                return NULL;
            }
            return barray;
        }

        %pythoncode %{
def getImageData(self, output="png"):
    """Convert to binary image stream of desired type.

    Can be used as input to GUI packages like tkinter.

    Args:
        output: (str) image type, default is PNG. Others are PNM, PGM, PPM,
                PBM, PAM, PSD, PS.
    Returns:
        Bytes object.
    """
    valid_formats = {"png": 1, "pnm": 2, "pgm": 2, "ppm": 2, "pbm": 2,
                     "pam": 3, "tga": 4, "tpic": 4,
                     "psd": 5, "ps": 6}
    idx = valid_formats.get(output.lower(), 1)
    if self.alpha and idx in (2, 6):
        raise ValueError("'%s' cannot have alpha" % output)
    if self.colorspace and self.colorspace.n > 3 and idx in (1, 2, 4):
        raise ValueError("unsupported colorspace for '%s'" % output)
    barray = self._getImageData(idx)
    return barray

def getPNGdata(self):
    """Wrapper for Pixmap.getImageData("png")."""
    barray = self._getImageData(1)
    return barray

def getPNGData(self):
    """Wrapper for Pixmap.getImageData("png")."""
    barray = self._getImageData(1)
    return barray
    %}

        //----------------------------------------------------------------------
        // _writeIMG
        //----------------------------------------------------------------------
        FITZEXCEPTION(_writeIMG, !result)
        PyObject *_writeIMG(char *filename, int format)
        {
            fz_try(gctx) {
                fz_pixmap *pm = (fz_pixmap *) $self;
                switch(format) {
                    case(1):
                        fz_save_pixmap_as_png(gctx, pm, filename);
                        break;
                    case(2):
                        fz_save_pixmap_as_pnm(gctx, pm, filename);
                        break;
                    case(3):
                        fz_save_pixmap_as_pam(gctx, pm, filename);
                        break;
                    case(5): // Adobe Photoshop Document
                        fz_save_pixmap_as_psd(gctx, pm, filename);
                        break;
                    case(6): // Postscript
                        fz_save_pixmap_as_ps(gctx, pm, filename, 0);
                        break;
                    default:
                        fz_save_pixmap_as_png(gctx, pm, filename);
                        break;
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }
        %pythoncode %{
def writeImage(self, filename, output=None):
    """Output as image in format determined by filename extension.

    Args:
        output: (str) only use to override filename extension. Default is PNG.
                Others are PNM, PGM, PPM, PBM, PAM, PSD, PS.
    Returns:
        Bytes object.
    """
    valid_formats = {"png": 1, "pnm": 2, "pgm": 2, "ppm": 2, "pbm": 2,
                     "pam": 3, "tga": 4, "tpic": 4,
                     "psd": 5, "ps": 6}
    if output is None:
        _, ext = os.path.splitext(filename)
        output = ext[1:]

    idx = valid_formats.get(output.lower(), 1)

    if self.alpha and idx in (2, 6):
        raise ValueError("'%s' cannot have alpha" % output)
    if self.colorspace and self.colorspace.n > 3 and idx in (1, 2, 4):
        raise ValueError("unsupported colorspace for '%s'" % output)

    return self._writeIMG(filename, idx)

def writePNG(self, filename):
    """Wrapper for Pixmap.writeImage(filename, "png")."""
    return self._writeIMG(filename, 1)


def pillowWrite(self, *args, **kwargs):
    """Write to image file using Pillow.

    Arguments are passed to Pillow's Image.save() method.
    Use instead of writeImage when other output formats are desired.
    """
    try:
        from PIL import Image
    except ImportError:
        print("PIL/Pillow not instralled")
        raise

    cspace = self.colorspace
    if cspace is None:
        mode = "L"
    elif cspace.n == 1:
        mode = "L" if self.alpha == 0 else "LA"
    elif cspace.n == 3:
        mode = "RGB" if self.alpha == 0 else "RGBA"
    else:
        mode = "CMYK"

    img = Image.frombytes(mode, (self.width, self.height), self.samples)

    if "dpi" not in kwargs.keys():
        kwargs["dpi"] = (self.xres, self.yres)

    img.save(*args, **kwargs)

def pillowData(self, *args, **kwargs):
    """Convert to binary image stream using pillow.

    Arguments are passed to Pillow's Image.save() method.
    Use it instead of writeImage when other output formats are needed.
    """
    from io import BytesIO
    bytes_out = BytesIO()
    self.pillowSave(bytes_out, *args, **kwargs)
    return bytes_out.get_value()

        %}
        //----------------------------------------------------------------------
        // invertIRect
        //----------------------------------------------------------------------
        %pythonprepend invertIRect
        %{"""Invert the colors inside a bbox."""%}
        PyObject *invertIRect(PyObject *bbox = NULL)
        {
            fz_pixmap *pm = (fz_pixmap *) $self;
            if (!fz_pixmap_colorspace(gctx, pm))
                {
                    JM_Warning("ignored for stencil pixmap");
                    return JM_BOOL(0);
                }

            fz_irect r = JM_irect_from_py(bbox);
            if (fz_is_infinite_irect(r))
                r = fz_pixmap_bbox(gctx, pm);

            return JM_BOOL(JM_invert_pixmap_rect(gctx, pm, r));
        }

        //----------------------------------------------------------------------
        // get one pixel as a list
        //----------------------------------------------------------------------
        FITZEXCEPTION(pixel, !result)
        %pythonprepend pixel
%{"""Get color tuple of pixel (x, y).
Last item is the alpha if Pixmap.alpha is true."""%}
        PyObject *pixel(int x, int y)
        {
            PyObject *p = NULL;
            fz_try(gctx) {
                fz_pixmap *pm = (fz_pixmap *) $self;
                if (!INRANGE(x, 0, pm->w - 1) || !INRANGE(y, 0, pm->h - 1))
                    THROWMSG(gctx, "outside image");
                int n = pm->n;
                int stride = fz_pixmap_stride(gctx, pm);
                int j, i = stride * y + n * x;
                p = PyTuple_New(n);
                for (j = 0; j < n; j++) {
                    PyTuple_SET_ITEM(p, j, Py_BuildValue("i", pm->samples[i + j]));
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            return p;
        }

        //----------------------------------------------------------------------
        // Set one pixel to a given color tuple
        //----------------------------------------------------------------------
        FITZEXCEPTION(setPixel, !result)
        %pythonprepend setPixel
        %{"""Set color of pixel (x, y)."""%}
        PyObject *setPixel(int x, int y, PyObject *color)
        {
            fz_try(gctx) {
                fz_pixmap *pm = (fz_pixmap *) $self;
                if (!INRANGE(x, 0, pm->w - 1) || !INRANGE(y, 0, pm->h - 1))
                    THROWMSG(gctx, "outside image");
                int n = pm->n;
                if (!PySequence_Check(color) || PySequence_Size(color) != n)
                    THROWMSG(gctx, "bad color arg");
                int i, j;
                unsigned char c[5];
                for (j = 0; j < n; j++) {
                    if (JM_INT_ITEM(color, j, &i) == 1)
                        THROWMSG(gctx, "bad color sequence");
                    if (!INRANGE(i, 0, 255))
                        THROWMSG(gctx, "bad color sequence");
                    c[j] = (unsigned char) i;
                }
                int stride = fz_pixmap_stride(gctx, pm);
                i = stride * y + n * x;
                for (j = 0; j < n; j++) {
                    pm->samples[i + j] = c[j];
                }
            }
            fz_catch(gctx) {
                PyErr_Clear();
                return NULL;
            }
            return_none;
        }


        //----------------------------------------------------------------------
        // Set Pixmap resolution
        //----------------------------------------------------------------------
        %pythonprepend setOrigin
        %{"""Set top-left coordinates."""%}
        PyObject *setOrigin(int x, int y)
        {
            fz_pixmap *pm = (fz_pixmap *) $self;
            pm->x = x;
            pm->y = y;
            Py_RETURN_NONE;
        }

        %pythonprepend setResolution
%{"""Set resolution in both dimensions.

Use pillowWrite to reflect this in output image."""%}
        PyObject *setResolution(int xres, int yres)
        {
            fz_pixmap *pm = (fz_pixmap *) $self;
            pm->xres = xres;
            pm->yres = yres;
            Py_RETURN_NONE;
        }

        //----------------------------------------------------------------------
        // Set a rect to a given color tuple
        //----------------------------------------------------------------------
        FITZEXCEPTION(setRect, !result)
        %pythonprepend setRect
        %{"""Set color of all pixels in bbox."""%}
        PyObject *setRect(PyObject *bbox, PyObject *color)
        {
            PyObject *rc = NULL;
            fz_try(gctx) {
                fz_pixmap *pm = (fz_pixmap *) $self;
                Py_ssize_t j, n = (Py_ssize_t) pm->n;
                if (!PySequence_Check(color) || PySequence_Size(color) != n)
                    THROWMSG(gctx, "bad color arg");
                unsigned char c[5];
                int i;
                for (j = 0; j < n; j++) {
                    if (JM_INT_ITEM(color, j, &i) == 1)
                        THROWMSG(gctx, "bad color component");
                    if (!INRANGE(i, 0, 255))
                        THROWMSG(gctx, "bad color component");
                    c[j] = (unsigned char) i;
                }
                i = JM_fill_pixmap_rect_with_color(gctx, pm, c, JM_irect_from_py(bbox));
                rc = JM_BOOL(i);
            }
            fz_catch(gctx) {
                PyErr_Clear();
                return NULL;
            }
            return rc;
        }

        //----------------------------------------------------------------------
        // get length of one image row
        //----------------------------------------------------------------------
        %pythoncode %{@property%}
        %pythonprepend stride %{"""Length of one image line (width * n)."""%}
        PyObject *stride()
        {
            return PyLong_FromSize_t((size_t) fz_pixmap_stride(gctx, (fz_pixmap *) $self));
        }

        //----------------------------------------------------------------------
        // x, y, width, height, xres, yres, n
        //----------------------------------------------------------------------
        %pythoncode %{@property%}
        %pythonprepend xres %{"""Resolution in x direction."""%}
        int xres()
        {
            fz_pixmap *this_pix = (fz_pixmap *) $self;
            return this_pix->xres;
        }

        %pythoncode %{@property%}
        %pythonprepend yres %{"""Resolution in y direction."""%}
        int yres()
        {
            fz_pixmap *this_pix = (fz_pixmap *) $self;
            return this_pix->yres;
        }

        %pythoncode %{@property%}
        %pythonprepend w %{"""The width."""%}
        PyObject *w()
        {
            return PyLong_FromSize_t((size_t) fz_pixmap_width(gctx, (fz_pixmap *) $self));
        }

        %pythoncode %{@property%}
        %pythonprepend h %{"""The height."""%}
        PyObject *h()
        {
            return PyLong_FromSize_t((size_t) fz_pixmap_height(gctx, (fz_pixmap *) $self));
        }

        %pythoncode %{@property%}
        %pythonprepend x %{"""x component of Pixmap origin."""%}
        int x()
        {
            return fz_pixmap_x(gctx, (fz_pixmap *) $self);
        }

        %pythoncode %{@property%}
        %pythonprepend y %{"""y component of Pixmap origin."""%}
        int y()
        {
            return fz_pixmap_y(gctx, (fz_pixmap *) $self);
        }

        %pythoncode %{@property%}
        %pythonprepend n %{"""The size of one pixel."""%}
        int n()
        {
            return fz_pixmap_components(gctx, (fz_pixmap *) $self);
        }

        //----------------------------------------------------------------------
        // check alpha channel
        //----------------------------------------------------------------------
        %pythoncode %{@property%}
        %pythonprepend alpha %{"""Indicates presence of alpha channel."""%}
        int alpha()
        {
            return fz_pixmap_alpha(gctx, (fz_pixmap *) $self);
        }

        //----------------------------------------------------------------------
        // get colorspace of pixmap
        //----------------------------------------------------------------------
        %pythoncode %{@property%}
        %pythonprepend colorspace %{"""Pixmap Colorspace."""%}
        struct Colorspace *colorspace()
        {
            return (struct Colorspace *) fz_pixmap_colorspace(gctx, (fz_pixmap *) $self);
        }

        //----------------------------------------------------------------------
        // return irect of pixmap
        //----------------------------------------------------------------------
        %pythoncode %{@property%}
        %pythonprepend irect %{"""Pixmap bbox - an IRect object."""%}
        %pythonappend irect %{val = IRect(val)%}
        PyObject *irect()
        {
            return JM_py_from_irect(fz_pixmap_bbox(gctx, (fz_pixmap *) $self));
        }

        //----------------------------------------------------------------------
        // return size of pixmap
        //----------------------------------------------------------------------
        %pythoncode %{@property%}
        %pythonprepend size %{"""Pixmap size."""%}
        PyObject *size()
        {
            fz_pixmap *pix = (fz_pixmap *) $self;
            size_t s = (size_t) pix->w;
            s *= pix->h;
            s *= pix->n;
            s += sizeof(*pix);
            return PyLong_FromSize_t(s);
        }

        //----------------------------------------------------------------------
        // samples
        //----------------------------------------------------------------------
        %pythoncode %{@property%}
        %pythonprepend samples %{"""The area of all pixels."""%}
        PyObject *samples()
        {
            fz_pixmap *pm = (fz_pixmap *) $self;
            Py_ssize_t s = (Py_ssize_t) pm->w;
            s *= pm->h;
            s *= pm->n;
            return PyBytes_FromStringAndSize((const char *) pm->samples, s);
        }

        %pythoncode %{
        width  = w
        height = h

        def __len__(self):
            return self.size

        def __repr__(self):
            if not type(self) is Pixmap: return
            if self.colorspace:
                return "Pixmap(%s, %s, %s)" % (self.colorspace.name, self.irect, self.alpha)
            else:
                return "Pixmap(%s, %s, %s)" % ('None', self.irect, self.alpha)

        def __del__(self):
            if not type(self) is Pixmap: return
            self.__swig_destroy__(self)
        %}
    }
};

/* fz_colorspace */
struct Colorspace
{
    %extend {
        ~Colorspace()
        {
            DEBUGMSG1("Colorspace");
            fz_colorspace *this_cs = (fz_colorspace *) $self;
            fz_drop_colorspace(gctx, this_cs);
            DEBUGMSG2;
        }

        %pythonprepend Colorspace
        %{"""Supported are GRAY, RGB and CMYK."""%}
        Colorspace(int type)
        {
            fz_colorspace *cs = NULL;
            switch(type) {
                case CS_GRAY:
                    cs = fz_device_gray(gctx);
                    break;
                case CS_CMYK:
                    cs = fz_device_cmyk(gctx);
                    break;
                case CS_RGB:
                default:
                    cs = fz_device_rgb(gctx);
                    break;
            }
            return (struct Colorspace *) cs;
        }
        //----------------------------------------------------------------------
        // number of bytes to define color of one pixel
        //----------------------------------------------------------------------
        %pythoncode %{@property%}
        %pythonprepend n %{"""Size of one pixel."""%}
        PyObject *n()
        {
            return Py_BuildValue("i", fz_colorspace_n(gctx, (fz_colorspace *) $self));
        }

        //----------------------------------------------------------------------
        // name of colorspace
        //----------------------------------------------------------------------
        PyObject *_name()
        {
            return JM_UnicodeFromStr(fz_colorspace_name(gctx, (fz_colorspace *) $self));
        }

        %pythoncode %{
        @property
        def name(self):
            """Name of the Colorspace."""

            if self.n == 1:
                return csGRAY._name()
            elif self.n == 3:
                return csRGB._name()
            elif self.n == 4:
                return csCMYK._name()
            return self._name()

        def __repr__(self):
            x = ("", "GRAY", "", "RGB", "CMYK")[self.n]
            return "Colorspace(CS_%s) - %s" % (x, self.name)
        %}
    }
};


/* fz_device wrapper */
%rename(Device) DeviceWrapper;
struct DeviceWrapper
{
    %extend {
        FITZEXCEPTION(DeviceWrapper, !result)
        DeviceWrapper(struct Pixmap *pm, PyObject *clip) {
            struct DeviceWrapper *dw = NULL;
            fz_try(gctx) {
                dw = (struct DeviceWrapper *)calloc(1, sizeof(struct DeviceWrapper));
                fz_irect bbox = JM_irect_from_py(clip);
                if (fz_is_infinite_irect(bbox))
                    dw->device = fz_new_draw_device(gctx, fz_identity, (fz_pixmap *) pm);
                else
                    dw->device = fz_new_draw_device_with_bbox(gctx, fz_identity, (fz_pixmap *) pm, &bbox);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return dw;
        }
        DeviceWrapper(struct DisplayList *dl) {
            struct DeviceWrapper *dw = NULL;
            fz_try(gctx) {
                dw = (struct DeviceWrapper *)calloc(1, sizeof(struct DeviceWrapper));
                dw->device = fz_new_list_device(gctx, (fz_display_list *) dl);
                dw->list = (fz_display_list *) dl;
                fz_keep_display_list(gctx, (fz_display_list *) dl);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return dw;
        }
        DeviceWrapper(struct TextPage *tp, int flags = 0) {
            struct DeviceWrapper *dw = NULL;
            fz_try(gctx) {
                dw = (struct DeviceWrapper *)calloc(1, sizeof(struct DeviceWrapper));
                fz_stext_options opts = { 0 };
                opts.flags = flags;
                dw->device = fz_new_stext_device(gctx, (fz_stext_page *) tp, &opts);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return dw;
        }
        ~DeviceWrapper() {
            fz_display_list *list = $self->list;
            DEBUGMSG1("Device");
            fz_close_device(gctx, $self->device);
            fz_drop_device(gctx, $self->device);
            DEBUGMSG2;
            if(list)
            {
                DEBUGMSG1("DisplayList after Device");
                fz_drop_display_list(gctx, list);
                DEBUGMSG2;
            }
        }
    }
};

//-----------------------------------------------------------------------------
// fz_outline
//-----------------------------------------------------------------------------
%nodefaultctor;
struct Outline {
    %immutable;
/*
    fz_outline doesn't keep a ref number in mupdf's code,
    which means that if the root outline node is dropped,
    all the outline nodes will also be destroyed.

    As a result, if the root Outline python object drops ref,
    then other Outline will point to already freed area. E.g.:
    >>> import fitz
    >>> doc=fitz.Document('3.pdf')
    >>> ol=doc.loadOutline()
    >>> oln=ol.next
    >>> oln.dest.page
    5
    >>> #drops root outline
    ...
    >>> ol=4
    free outline
    >>> oln.dest.page
    0

    I do not like to change struct of fz_document, so I decide
    to delegate the outline destruction work to fz_document. That is,
    when the Document is created, its outline is loaded in advance.
    The outline will only be freed when the doc is destroyed, which means
    in the python code, we must keep ref to doc if we still want to use outline
    This is a nasty way but it requires little change to the mupdf code.
    */
/*
    %extend {
        ~Outline()
        {
            DEBUGMSG1("Outline");
            fz_outline *this_ol = (fz_outline *) $self;
            fz_drop_outline(gctx, this_ol);
            DEBUGMSG2;
        }
    }
*/
    %extend {
        %pythoncode %{@property%}
        PyObject *uri()
        {
            fz_outline *ol = (fz_outline *) $self;
            return JM_UnicodeFromStr(ol->uri);
        }

        %pythoncode %{@property%}
        struct Outline *next()
        {
            fz_outline *ol = (fz_outline *) $self;
            fz_outline *next_ol = ol->next;
            if (!next_ol) return NULL;
            next_ol = fz_keep_outline(gctx, next_ol);
            return (struct Outline *) next_ol;
        }

        %pythoncode %{@property%}
        struct Outline *down()
        {
            fz_outline *ol = (fz_outline *) $self;
            fz_outline *down_ol = ol->down;
            if (!down_ol) return NULL;
            down_ol = fz_keep_outline(gctx, down_ol);
            return (struct Outline *) down_ol;
        }

        %pythoncode %{@property%}
        PyObject *isExternal()
        {
            fz_outline *ol = (fz_outline *) $self;
            if (!ol->uri) Py_RETURN_FALSE;
            return JM_BOOL(fz_is_external_link(gctx, ol->uri));
        }

        %pythoncode %{@property%}
        int page()
        {
            fz_outline *ol = (fz_outline *) $self;
            return ol->page;
        }

        %pythoncode %{@property%}
        float x()
        {
            fz_outline *ol = (fz_outline *) $self;
            return ol->x;
        }

        %pythoncode %{@property%}
        float y()
        {
            fz_outline *ol = (fz_outline *) $self;
            return ol->y;
        }

        %pythoncode %{@property%}
        PyObject *title()
        {
            fz_outline *ol = (fz_outline *) $self;
            return JM_UnicodeFromStr(ol->title);
        }

        %pythoncode %{@property%}
        PyObject *is_open()
        {
            fz_outline *ol = (fz_outline *) $self;
            return JM_BOOL(ol->is_open);
        }

        %pythoncode %{isOpen = is_open%}
        %pythoncode %{
        @property
        def dest(self):
            '''outline destination details'''
            return linkDest(self, None)
        %}
    }
};
%clearnodefaultctor;


//-----------------------------------------------------------------------------
// Annotation
//-----------------------------------------------------------------------------
%nodefaultctor;
struct Annot
{
    %extend
    {
        ~Annot()
        {
            DEBUGMSG1("Annot");
            pdf_drop_annot(gctx, (pdf_annot *) $self);
            DEBUGMSG2;
        }
        //---------------------------------------------------------------------
        // annotation rectangle
        //---------------------------------------------------------------------
        %pythoncode %{@property%}
        PARENTCHECK(rect, """Annotation rectangle.""")
        %pythonappend rect %{
        val = Rect(val)
        val *= self.parent.derotationMatrix
        %}
        PyObject *rect()
        {
            fz_rect r = pdf_bound_annot(gctx, (pdf_annot *) $self);
            return JM_py_from_rect(r);
        }

        //---------------------------------------------------------------------
        // annotation get xref number
        //---------------------------------------------------------------------
        PARENTCHECK(xref, """Annotation xref.""")
        %pythoncode %{@property%}
        PyObject *xref()
        {
            pdf_annot *annot = (pdf_annot *) $self;
            return Py_BuildValue("i", pdf_to_num(gctx, annot->obj));
        }

        //---------------------------------------------------------------------
        // annotation get AP/N Matrix
        //---------------------------------------------------------------------
        PARENTCHECK(APNMatrix, """Annotation appearance matrix.""")
        %pythonappend APNMatrix %{val = Matrix(val)%}
        %pythoncode %{@property%}
        PyObject *
        APNMatrix()
        {
            pdf_annot *annot = (pdf_annot *) $self;
            pdf_obj *ap = pdf_dict_getl(gctx, annot->obj, PDF_NAME(AP),
                            PDF_NAME(N), NULL);
            if (!ap)
                return JM_py_from_matrix(fz_identity);
            fz_matrix mat = pdf_dict_get_matrix(gctx, ap, PDF_NAME(Matrix));
            return JM_py_from_matrix(mat);
        }

        //---------------------------------------------------------------------
        // annotation get AP/N BBox
        //---------------------------------------------------------------------
        PARENTCHECK(APNBBox, """Annotation appearance bbox.""")
        %pythonappend APNBBox %{
        val = Rect(val) * self.parent.transformationMatrix
        val *= self.parent.derotationMatrix%}
        %pythoncode %{@property%}
        PyObject *
        APNBBox()
        {
            pdf_annot *annot = (pdf_annot *) $self;
            pdf_obj *ap = pdf_dict_getl(gctx, annot->obj, PDF_NAME(AP),
                            PDF_NAME(N), NULL);
            if (!ap)
                return JM_py_from_rect(fz_infinite_rect);
            fz_rect rect = pdf_dict_get_rect(gctx, ap, PDF_NAME(BBox));
            return JM_py_from_rect(rect);
        }


        //---------------------------------------------------------------------
        // annotation set AP/N Matrix
        //---------------------------------------------------------------------
        FITZEXCEPTION(setAPNMatrix, !result)
        PARENTCHECK(setAPNMatrix, """Set annotation appearance matrix.""")
        PyObject *
        setAPNMatrix(PyObject *matrix)
        {
            pdf_annot *annot = (pdf_annot *) $self;
            fz_try(gctx) {
                pdf_obj *ap = pdf_dict_getl(gctx, annot->obj, PDF_NAME(AP),
                                                PDF_NAME(N), NULL);
                if (!ap) THROWMSG(gctx, "annot has no appearance stream");
                fz_matrix mat = JM_matrix_from_py(matrix);
                pdf_dict_put_matrix(gctx, ap, PDF_NAME(Matrix), mat);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }


        //---------------------------------------------------------------------
        // annotation set AP/N BBox
        //---------------------------------------------------------------------
        FITZEXCEPTION(setAPNBBox, !result)
        %pythonprepend setAPNBBox %{
        """Set annotation appearance bbox."""

        CheckParent(self)
        page = self.parent
        rot = page.rotationMatrix
        mat = page.transformationMatrix
        bbox *= rot * ~mat
        %}
        PyObject *
        setAPNBBox(PyObject *bbox)
        {
            pdf_annot *annot = (pdf_annot *) $self;
            fz_try(gctx) {
                pdf_obj *ap = pdf_dict_getl(gctx, annot->obj, PDF_NAME(AP),
                                                PDF_NAME(N), NULL);
                if (!ap) THROWMSG(gctx, "annot has no appearance stream");
                fz_rect rect = JM_rect_from_py(bbox);
                pdf_dict_put_rect(gctx, ap, PDF_NAME(BBox), rect);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }


        //---------------------------------------------------------------------
        // annotation show blend mode (/BM)
        //---------------------------------------------------------------------
        PARENTCHECK(blendMode, """Annotation BlendMode.""")
        PyObject *blendMode()
        {
            PyObject *blend_mode = NULL;
            fz_try(gctx) {
                pdf_annot *annot = (pdf_annot *) $self;
                pdf_obj *obj, *obj1, *obj2;
                obj = pdf_dict_get(gctx, annot->obj, PDF_NAME(BM));
                if (obj) {  // check the annot object for /BM
                    blend_mode = JM_UnicodeFromStr(pdf_to_name(gctx, obj));
                    goto fertig;
                }
                // loop through the /AP/N/Resources/ExtGState objects
                obj = pdf_dict_getl(gctx, annot->obj, PDF_NAME(AP),
                    PDF_NAME(N),
                    PDF_NAME(Resources),
                    PDF_NAME(ExtGState),
                    NULL);

                if (pdf_is_dict(gctx, obj)) {
                    int i, j, m, n = pdf_dict_len(gctx, obj);
                    for (i = 0; i < n; i++) {
                        obj1 = pdf_dict_get_val(gctx, obj, i);
                        if (pdf_is_dict(gctx, obj1)) {
                            m = pdf_dict_len(gctx, obj1);
                            for (j = 0; j < m; j++) {
                                obj2 = pdf_dict_get_key(gctx, obj1, j);
                                if (pdf_objcmp(gctx, obj2, PDF_NAME(BM)) == 0) {
                                    blend_mode = JM_UnicodeFromStr(pdf_to_name(gctx, pdf_dict_get_val(gctx, obj1, j)));
                                    goto fertig;
                                }
                            }
                        }
                    }
                }
                fertig:;
            }
            fz_catch(gctx) {
                return_none;
            }
            if (blend_mode) return blend_mode;
            return_none;
        }


        //---------------------------------------------------------------------
        // annotation set blend mode (/BM)
        //---------------------------------------------------------------------
        FITZEXCEPTION(setBlendMode, !result)
        PARENTCHECK(setBlendMode, """Set annotation BlendMode.""")
        PyObject *setBlendMode(char *blend_mode)
        {
            fz_try(gctx) {
                pdf_annot *annot = (pdf_annot *) $self;
                pdf_dict_put_name(gctx, annot->obj, PDF_NAME(BM), blend_mode);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }


        //---------------------------------------------------------------------
        // annotation set optional content
        //---------------------------------------------------------------------
        FITZEXCEPTION(getOC, !result)
        PARENTCHECK(getOC, """Get annotation optional content reference.""")
        PyObject *getOC()
        {
            PyObject *oc = NULL;
            fz_try(gctx) {
                pdf_annot *annot = (pdf_annot *) $self;
                pdf_obj *obj = pdf_dict_get(gctx, annot->obj, PDF_NAME(OC));
                if (!obj) {
                    oc = Py_BuildValue("i", 0);
                } else {
                    int n = pdf_to_num(gctx, obj);
                    oc = Py_BuildValue("i", n);
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            return oc;;
        }


        //---------------------------------------------------------------------
        // annotation set optional content
        //---------------------------------------------------------------------
        FITZEXCEPTION(setOC, !result)
        PARENTCHECK(setOC, """Set annotation optional content reference.""")
        PyObject *setOC(int oc=0)
        {
            fz_try(gctx) {
                pdf_annot *annot = (pdf_annot *) $self;
                if (!oc) {
                    pdf_dict_del(gctx, annot->obj, PDF_NAME(OC));
                } else {
                    JM_add_oc_object(gctx, pdf_get_bound_document(gctx, annot->obj), annot->obj, oc);
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }


        %pythoncode%{@property%}
        %pythonprepend language %{"""Annotation language."""%}
        PyObject *language()
        {
            pdf_annot *this_annot = (pdf_annot *) $self;
            fz_text_language lang = pdf_annot_language(gctx, this_annot);
            char buf[8];
            if (lang == FZ_LANG_UNSET) return_none;
            return Py_BuildValue("s", fz_string_from_text_language(buf, lang));
        }

        //---------------------------------------------------------------------
        // annotation set language (/Lang)
        //---------------------------------------------------------------------
        FITZEXCEPTION(setLaguage, !result)
        PARENTCHECK(setLaguage, """Set annotation language.""")
        PyObject *setLaguage(char *language=NULL)
        {
            pdf_annot *this_annot = (pdf_annot *) $self;
            fz_try(gctx) {
                fz_text_language lang;
                if (!language)
                    lang = FZ_LANG_UNSET;
                else
                    lang = fz_text_language_from_string(language);
                pdf_set_annot_language(gctx, this_annot, lang);
            }
            fz_catch(gctx) {
                return NULL;
            }
            Py_RETURN_TRUE;
        }


        //---------------------------------------------------------------------
        // annotation get decompressed appearance stream source
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getAP, !result)
        PyObject *_getAP()
        {
            PyObject *r = Py_None;
            fz_buffer *res = NULL;
            fz_try(gctx) {
                pdf_annot *annot = (pdf_annot *) $self;
                pdf_obj *ap = pdf_dict_getl(gctx, annot->obj, PDF_NAME(AP),
                                              PDF_NAME(N), NULL);

                if (pdf_is_stream(gctx, ap))  res = pdf_load_stream(gctx, ap);
                if (res) r = JM_BinFromBuffer(gctx, res);
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) {
                return_none;
            }
            return r;
        }

        //---------------------------------------------------------------------
        // annotation update /AP stream
        //---------------------------------------------------------------------
        FITZEXCEPTION(_setAP, !result)
        PyObject *_setAP(PyObject *ap, int rect = 0)
        {
            fz_buffer *res = NULL;
            fz_var(res);
            fz_try(gctx) {
                pdf_annot *annot = (pdf_annot *) $self;
                pdf_obj *apobj = pdf_dict_getl(gctx, annot->obj, PDF_NAME(AP),
                                              PDF_NAME(N), NULL);
                if (!apobj) THROWMSG(gctx, "annot has no /AP/N object");
                if (!pdf_is_stream(gctx, apobj))
                    THROWMSG(gctx, "/AP/N object is no stream");
                res = JM_BufferFromBytes(gctx, ap);
                if (!res) THROWMSG(gctx, "invalid /AP stream argument");
                JM_update_stream(gctx, annot->page->doc, apobj, res, 1);
                if (rect) {
                    fz_rect bbox = pdf_dict_get_rect(gctx, annot->obj, PDF_NAME(Rect));
                    pdf_dict_put_rect(gctx, apobj, PDF_NAME(BBox), bbox);
                    annot->ap = NULL;
                }
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }


        //---------------------------------------------------------------------
        // redaction annotation get values
        //---------------------------------------------------------------------
        FITZEXCEPTION(_get_redact_values, !result)
        %pythonappend _get_redact_values %{
        if not val:
            return val
        val["rect"] = self.rect
        text_color, fontname, fontsize = TOOLS._parse_da(self)
        val["text_color"] = text_color
        val["fontname"] = fontname
        val["fontsize"] = fontsize
        fill = self.colors["fill"]
        val["fill"] = fill

        %}
        PyObject *
        _get_redact_values()
        {
            pdf_annot *annot = (pdf_annot *) $self;
            if (pdf_annot_type(gctx, annot) != PDF_ANNOT_REDACT)
                return_none;

            PyObject *values = PyDict_New();
            pdf_obj *obj = NULL;
            const char *text = NULL;
            fz_try(gctx) {
                obj = pdf_dict_gets(gctx, annot->obj, "RO");
                if (obj) {
                    JM_Warning("Ignoring redaction key '/RO'.");
                    int xref = pdf_to_num(gctx, obj);
                    DICT_SETITEM_DROP(values, dictkey_xref, Py_BuildValue("i", xref));
                }
                obj = pdf_dict_gets(gctx, annot->obj, "OverlayText");
                if (obj) {
                    text = pdf_to_text_string(gctx, obj);
                    DICT_SETITEM_DROP(values, dictkey_text, JM_UnicodeFromStr(text));
                } else {
                    DICT_SETITEM_DROP(values, dictkey_text, Py_BuildValue("s", ""));
                }
                obj = pdf_dict_get(gctx, annot->obj, PDF_NAME(Q));
                int align = 0;
                if (obj) {
                    align = pdf_to_int(gctx, obj);
                }
                DICT_SETITEM_DROP(values, dictkey_align, Py_BuildValue("i", align));
            }
            fz_catch(gctx) {
                Py_DECREF(values);
                return NULL;
            }
            return values;
        }

        //---------------------------------------------------------------------
        // annotation get TextPage
        //---------------------------------------------------------------------
        FITZEXCEPTION(getTextPage, !result)
        PARENTCHECK(getTextPage, """Get annotation TextPage.""")
        struct TextPage *
        getTextPage(PyObject *clip=NULL, int flags = 0)
        {
            fz_stext_page *textpage=NULL;
            fz_stext_options options = { 0 };
            options.flags = flags;
            fz_try(gctx) {
                pdf_annot *annot = (pdf_annot *) $self;
                textpage = pdf_new_stext_page_from_annot(gctx, annot, &options);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct TextPage *) textpage;
        }

        //---------------------------------------------------------------------
        // annotation set name
        //---------------------------------------------------------------------
        PARENTCHECK(setName, """Set /Name (icon) of annotation.""")
        PyObject *setName(char *name)
        {
            fz_try(gctx) {
                pdf_annot *annot = (pdf_annot *) $self;
                pdf_dict_put_name(gctx, annot->obj, PDF_NAME(Name), name);
                pdf_dirty_annot(gctx, annot);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        //---------------------------------------------------------------------
        // annotation set rectangle
        //---------------------------------------------------------------------
        PARENTCHECK(setRect, """Set annotation rectangle.""")
        PyObject *setRect(PyObject *rect)
        {
            fz_try(gctx) {
                pdf_annot *annot = (pdf_annot *) $self;
                pdf_page *pdfpage = annot->page;
                fz_matrix rot = JM_rotate_page_matrix(gctx, pdfpage);
                fz_rect r = fz_transform_rect(JM_rect_from_py(rect), rot);
                pdf_set_annot_rect(gctx, annot, r);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        //---------------------------------------------------------------------
        // annotation set rotation
        //---------------------------------------------------------------------
        PARENTCHECK(setRotation, """Set annotation rotation.""")
        PyObject *setRotation(int rotate=0)
        {
            pdf_annot *annot = (pdf_annot *) $self;
            int type = pdf_annot_type(gctx, annot);
            switch (type)
            {
                case PDF_ANNOT_CARET: break;
                case PDF_ANNOT_CIRCLE: break;
                case PDF_ANNOT_FREE_TEXT: break;
                case PDF_ANNOT_FILE_ATTACHMENT: break;
                case PDF_ANNOT_INK: break;
                case PDF_ANNOT_LINE: break;
                case PDF_ANNOT_POLY_LINE: break;
                case PDF_ANNOT_POLYGON: break;
                case PDF_ANNOT_SQUARE: break;
                case PDF_ANNOT_STAMP: break;
                case PDF_ANNOT_TEXT: break;
                default: return_none;
            }
            int rot = rotate;
            while (rot < 0) rot += 360;
            while (rot >= 360) rot -= 360;
            if (type == PDF_ANNOT_FREE_TEXT && rot % 90 != 0)
                rot = 0;

            pdf_dict_put_int(gctx, annot->obj, PDF_NAME(Rotate), rot);
            return_none;
        }

        //---------------------------------------------------------------------
        // annotation get rotation
        //---------------------------------------------------------------------
        %pythoncode %{@property%}
        PARENTCHECK(rotation, """Annotation rotation.""")
        int rotation()
        {
            pdf_annot *annot = (pdf_annot *) $self;
            pdf_obj *rotation = pdf_dict_get(gctx, annot->obj, PDF_NAME(Rotate));
            if (!rotation) return -1;
            return pdf_to_int(gctx, rotation);
        }

        //---------------------------------------------------------------------
        // annotation vertices (for "Line", "Polgon", "Ink", etc.
        //---------------------------------------------------------------------
        PARENTCHECK(vertices, """Vertex points.""")
        %pythoncode %{@property%}
        PyObject *vertices()
        {
            PyObject *res = NULL, *res1 = NULL;
            pdf_obj *o, *o1;
            pdf_annot *annot = (pdf_annot *) $self;
            int i, j;
            fz_point point;  // point object to work with
            fz_matrix page_ctm;  // page transformation matrix
            pdf_page_transform(gctx, annot->page, NULL, &page_ctm);
            fz_matrix derot = JM_derotate_page_matrix(gctx, annot->page);
            page_ctm = fz_concat(page_ctm, derot);

            //----------------------------------------------------------------
            // The following objects occur in different annotation types.
            // So we are sure that (!o) occurs at most once.
            // Every pair of floats is one point, that needs to be separately
            // transformed with the page transformation matrix.
            //----------------------------------------------------------------
            o = pdf_dict_get(gctx, annot->obj, PDF_NAME(Vertices));
            if (o) goto weiter;
            o = pdf_dict_get(gctx, annot->obj, PDF_NAME(L));
            if (o) goto weiter;
            o = pdf_dict_get(gctx, annot->obj, PDF_NAME(QuadPoints));
            if (o) goto weiter;
            o = pdf_dict_gets(gctx, annot->obj, "CL");
            if (o) goto weiter;
            o = pdf_dict_get(gctx, annot->obj, PDF_NAME(InkList));
            if (o) goto inklist;
            return_none;

            // handle lists with 1-level depth --------------------------------
            weiter:;
            res = PyList_New(0);  // create Python list
            for (i = 0; i < pdf_array_len(gctx, o); i += 2)
            {
                point.x = pdf_to_real(gctx, pdf_array_get(gctx, o, i));
                point.y = pdf_to_real(gctx, pdf_array_get(gctx, o, i+1));
                point = fz_transform_point(point, page_ctm);
                LIST_APPEND_DROP(res, Py_BuildValue("ff", point.x, point.y));
            }
            return res;

            // InkList has 2-level lists --------------------------------------
            inklist:;
            res = PyList_New(0);
            for (i = 0; i < pdf_array_len(gctx, o); i++)
            {
                res1 = PyList_New(0);
                o1 = pdf_array_get(gctx, o, i);
                for (j = 0; j < pdf_array_len(gctx, o1); j += 2)
                {
                    point.x = pdf_to_real(gctx, pdf_array_get(gctx, o1, j));
                    point.y = pdf_to_real(gctx, pdf_array_get(gctx, o1, j+1));
                    point = fz_transform_point(point, page_ctm);
                    LIST_APPEND_DROP(res1, Py_BuildValue("ff", point.x, point.y));
                }
                LIST_APPEND_DROP(res, res1);
            }
            return res;
        }

        //---------------------------------------------------------------------
        // annotation colors
        //---------------------------------------------------------------------
        %pythoncode %{@property%}
        PARENTCHECK(colors, """Color definitions.""")
        PyObject *colors()
        {
            pdf_annot *annot = (pdf_annot *) $self;
            return JM_annot_colors(gctx, annot->obj);
        }

        //---------------------------------------------------------------------
        // annotation update appearance
        //---------------------------------------------------------------------
        PyObject *_update_appearance(float opacity=-1, char *blend_mode=NULL,
            PyObject *fill_color=NULL,
            int rotate = -1)
        {
            pdf_annot *annot = (pdf_annot *) $self;
            int type = pdf_annot_type(gctx, annot);
            float fcol[4] = {1,1,1,1};  // std fill color: white
            int nfcol = 0;  // number of color components
            JM_color_FromSequence(fill_color, &nfcol, fcol);
            fz_try(gctx) {
                pdf_dirty_annot(gctx, annot); // enforce MuPDF /AP formatting
                if (type == PDF_ANNOT_FREE_TEXT && EXISTS(fill_color))
                    pdf_set_annot_color(gctx, annot, nfcol, fcol);

                int insert_rot = (rotate >= 0) ? 1 : 0;
                switch (type) {
                    case PDF_ANNOT_CARET:
                    case PDF_ANNOT_CIRCLE:
                    case PDF_ANNOT_FREE_TEXT:
                    case PDF_ANNOT_FILE_ATTACHMENT:
                    case PDF_ANNOT_INK:
                    case PDF_ANNOT_LINE:
                    case PDF_ANNOT_POLY_LINE:
                    case PDF_ANNOT_POLYGON:
                    case PDF_ANNOT_SQUARE:
                    case PDF_ANNOT_STAMP:
                    case PDF_ANNOT_TEXT: break;
                    default: insert_rot = 0;
                }

                if (insert_rot)
                    pdf_dict_put_int(gctx, annot->obj, PDF_NAME(Rotate), rotate);
                annot->needs_new_ap = 1;  // re-create appearance stream
                pdf_update_annot(gctx, annot);  // update the annotation

            }
            fz_catch(gctx) {
                PySys_WriteStderr("cannot update annot: '%s'\n", fz_caught_message(gctx));
                Py_RETURN_FALSE;
            }

            if ((opacity < 0 || opacity >= 1) && !blend_mode)  // no opacity, no blend_mode
                Py_RETURN_TRUE;

            fz_try(gctx) {  // create or update /ExtGState
                pdf_obj *ap = pdf_dict_getl(gctx, annot->obj, PDF_NAME(AP),
                                        PDF_NAME(N), NULL);
                if (!ap)  // should never happen
                    THROWMSG(gctx, "annot has no /AP object");

                pdf_obj *resources = pdf_dict_get(gctx, ap, PDF_NAME(Resources));
                if (!resources) {  // no Resources yet: make one
                    resources = pdf_dict_put_dict(gctx, ap, PDF_NAME(Resources), 2);
                }
                pdf_obj *alp0 = pdf_new_dict(gctx, annot->page->doc, 3);
                if (opacity >= 0 && opacity < 1) {
                    pdf_dict_put_real(gctx, alp0, PDF_NAME(CA), (double) opacity);
                    pdf_dict_put_real(gctx, alp0, PDF_NAME(ca), (double) opacity);
                    pdf_dict_put_real(gctx, annot->obj, PDF_NAME(CA), (double) opacity);
                }
                if (blend_mode) {
                    pdf_dict_put_name(gctx, alp0, PDF_NAME(BM), blend_mode);
                    pdf_dict_put_name(gctx, annot->obj, PDF_NAME(BM), blend_mode);
                }
                pdf_obj *extg = pdf_dict_get(gctx, resources, PDF_NAME(ExtGState));
                if (!extg) {  // no ExtGState yet: make one
                    extg = pdf_dict_put_dict(gctx, resources, PDF_NAME(ExtGState), 2);
                }
                pdf_dict_put_drop(gctx, extg, PDF_NAME(H), alp0);
            }

            fz_catch(gctx) {
                PySys_WriteStderr("could not set opacity or blend mode\n");
                Py_RETURN_FALSE;
            }
            Py_RETURN_TRUE;
        }


        %pythoncode %{
        def update(self,
                   blend_mode=None,
                   opacity=None,
                   fontsize=0,
                   fontname=None,
                   text_color=None,
                   border_color=None,
                   fill_color=None,
                   cross_out=True,
                   rotate=-1,
                   ):

            """Update annot appearance.

            Notes:
                Depending on the annot type, some parameters make no sense,
                while others are only available in this method to achieve the
                desired result - especially for 'FreeText' annots.
            Args:
                blend_mode: set the blend mode, all annotations.
                opacity: set the opacity, all annotations.
                fontsize: set fontsize, 'FreeText' only.
                fontname: set the font, 'FreeText' only.
                border_color: set border color, 'FreeText' only.
                text_color: set text color, 'FreeText' only.
                fill_color: set fill color, all annotations.
                cross_out: draw diagonal lines, 'Redact' only.
                rotate: set rotation, 'FreeText' and some others.
            """
            CheckParent(self)
            def color_string(cs, code):
                """Return valid PDF color operator for a given color sequence.
                """
                if not cs:
                    return b""
                if hasattr(cs, "__float__") or len(cs) == 1:
                    app = " g\n" if code == "f" else " G\n"
                elif len(cs) == 3:
                    app = " rg\n" if code == "f" else " RG\n"
                elif len(cs) == 4:
                    app = " k\n" if code == "f" else " K\n"
                else:
                    return b""

                if hasattr(cs, "__len__"):
                    col = " ".join(map(str, cs)) + app
                else:
                    col = "%g" % cs + app

                return bytes(col, "utf8") if not fitz_py2 else col

            type = self.type[0]  # get the annot type
            dt = self.border["dashes"]  # get the dashes spec
            bwidth = self.border["width"]  # get border line width
            stroke = self.colors["stroke"]  # get the stroke color
            if fill_color is not None and type in (PDF_ANNOT_FREE_TEXT, PDF_ANNOT_REDACT):
                fill = fill_color
            else:
                fill = self.colors["fill"]
                if not fill:
                    fill = None

            rect = None  # self.rect  # prevent MuPDF fiddling with it
            apnmat = self.APNMatrix  # prevent MuPDF fiddling with it
            if rotate != -1:  # sanitize rotation value
                while rotate < 0:
                    rotate += 360
                while rotate >= 360:
                    rotate -= 360
                if type == PDF_ANNOT_FREE_TEXT and rotate % 90 != 0:
                    rotate = 0

            #------------------------------------------------------------------
            # handle opacity and blend mode
            #------------------------------------------------------------------
            if blend_mode is None:
                blend_mode = self.blendMode()
            if not hasattr(opacity, "__float__"):
                opacity = self.opacity

            if 0 <= opacity < 1 or blend_mode is not None:
                opa_code = "/H gs\n"  # then we must reference this 'gs'
            else:
                opa_code = ""

            #------------------------------------------------------------------
            # now invoke MuPDF to update the annot appearance
            #------------------------------------------------------------------
            val = self._update_appearance(
                opacity=opacity,
                blend_mode=blend_mode,
                fill_color=fill,
                rotate=rotate,
            )
            if not val:  # something went wrong, skip the rest
                return val

            bfill = color_string(fill, "f")
            bstroke = color_string(stroke, "s")

            p_ctm = self.parent.transformationMatrix
            imat = ~p_ctm  # inverse page transf. matrix

            if dt:
                dashes = "[" + " ".join(map(str, dt)) + "] 0 d\n"
                dashes = dashes.encode("utf-8")
            else:
                dashes = None

            if self.lineEnds:
                line_end_le, line_end_ri = self.lineEnds
            else:
                line_end_le, line_end_ri = 0, 0  # init line end codes

            # read contents as created by MuPDF
            ap = self._getAP()
            ap_tab = ap.splitlines()  # split in single lines
            ap_updated = False  # assume we did nothing

            if type == PDF_ANNOT_REDACT:
                if cross_out:  # create crossed-out rect
                    ap_updated = True
                    ap_tab = ap_tab[:-1]
                    _, LL, LR, UR, UL = ap_tab
                    ap_tab.append(LR)
                    ap_tab.append(LL)
                    ap_tab.append(UR)
                    ap_tab.append(LL)
                    ap_tab.append(UL)
                    ap_tab.append(b"S")

                if bwidth > 0 or bstroke != b"":
                    ap_updated = True
                    ntab = [b"%g w" % bwidth] if bwidth > 0 else []
                    for line in ap_tab:
                        if line.endswith(b"w"):
                            continue
                        if line.endswith(b"RG") and bstroke != b"":
                            line = bstroke[:-1]
                        ntab.append(line)
                    ap_tab = ntab

                ap = b"\n".join(ap_tab)

            if type == PDF_ANNOT_FREE_TEXT:
                CheckColor(border_color)
                CheckColor(text_color)
                tcol, fname, fsize = TOOLS._parse_da(self)

                # read and update default appearance as necessary
                update_default_appearance = False
                if fsize <= 0:
                    fsize = 12
                    update_default_appearance = True
                if text_color is not None:
                    tcol = text_color
                    update_default_appearance = True
                if fontname is not None:
                    fname = fontname
                    update_default_appearance = True
                if fontsize > 0:
                    fsize = fontsize
                    update_default_appearance = True

                da_str = ""
                if len(tcol) == 3:
                    fmt = "{:g} {:g} {:g} rg /{f:s} {s:g} Tf"
                elif len(tcol) == 1:
                    fmt = "{:g} g /{f:s} {s:g} Tf"
                elif len(tcol) == 4:
                    fmt = "{:g} {:g} {:g} {:g} k /{f:s} {s:g} Tf"
                da_str = fmt.format(*tcol, f=fname, s=fsize)
                TOOLS._update_da(self, da_str)
                
                for i, item in enumerate(ap_tab):
                    if (item.endswith(b" w")
                        and bwidth > 0
                        and border_color is not None
                       ):  # update border color
                        ap_tab[i + 1] = color_string(border_color, "s")
                        continue
                    if item == b"BT":  # update text color
                        ap_tab[i + 1] = color_string(tcol, "f")
                        continue

                if dashes is not None:  # handle dashes
                    ap_tab.insert(0, dashes)
                    dashes = None

                ap = b"\n".join(ap_tab)         # updated AP stream
                ap_updated = True

            if type in (PDF_ANNOT_POLYGON, PDF_ANNOT_POLY_LINE):
                ap = b"\n".join(ap_tab[:-1]) + b"\n"
                ap_updated = True
                if bfill != b"":
                    if type == PDF_ANNOT_POLYGON:
                        ap = ap + bfill + b"b"  # close, fill, and stroke
                    elif type == PDF_ANNOT_POLY_LINE:
                        ap = ap + bfill + b"B"  # fill and stroke
                else:
                    if type == PDF_ANNOT_POLYGON:
                        ap = ap + b"s"  # close and stroke
                    elif type == PDF_ANNOT_POLY_LINE:
                        ap = ap + b"S"  # stroke

            if dashes is not None:  # handle dashes
                ap = dashes + ap
                # reset dashing - only applies for LINE annots with line ends given
                ap = ap.replace(b"\nS\n", b"\nS\n[] 0 d\n", 1)
                ap_updated = True

            if opa_code:
                ap = opa_code.encode("utf-8") + ap
                ap_updated = True

            ap = b"q\n" + ap + b"\nQ\n"
            #----------------------------------------------------------------------
            # the following handles line end symbols for 'Polygon' and 'Polyline'
            #----------------------------------------------------------------------
            if line_end_le + line_end_ri > 0 and type in (PDF_ANNOT_POLYGON, PDF_ANNOT_POLY_LINE):

                le_funcs = (None, TOOLS._le_square, TOOLS._le_circle,
                            TOOLS._le_diamond, TOOLS._le_openarrow,
                            TOOLS._le_closedarrow, TOOLS._le_butt,
                            TOOLS._le_ropenarrow, TOOLS._le_rclosedarrow,
                            TOOLS._le_slash)
                le_funcs_range = range(1, len(le_funcs))
                d = 2 * max(1, self.border["width"])
                rect = self.rect + (-d, -d, d, d)
                ap_updated = True
                points = self.vertices
                if line_end_le in le_funcs_range:
                    p1 = Point(points[0]) * imat
                    p2 = Point(points[1]) * imat
                    left = le_funcs[line_end_le](self, p1, p2, False, fill_color)
                    ap += bytes(left, "utf8") if not fitz_py2 else left
                if line_end_ri in le_funcs_range:
                    p1 = Point(points[-2]) * imat
                    p2 = Point(points[-1]) * imat
                    left = le_funcs[line_end_ri](self, p1, p2, True, fill_color)
                    ap += bytes(left, "utf8") if not fitz_py2 else left

            if ap_updated:
                if rect:                        # rect modified here?
                    self.setRect(rect)
                    self._setAP(ap, rect=1)
                else:
                    self._setAP(ap, rect=0)

            #-------------------------------
            # handle annotation rotations
            #-------------------------------
            if type not in (  # only these types are supported
                PDF_ANNOT_CARET,
                PDF_ANNOT_CIRCLE,
                PDF_ANNOT_FILE_ATTACHMENT,
                PDF_ANNOT_INK,
                PDF_ANNOT_LINE,
                PDF_ANNOT_POLY_LINE,
                PDF_ANNOT_POLYGON,
                PDF_ANNOT_SQUARE,
                PDF_ANNOT_STAMP,
                PDF_ANNOT_TEXT,
                ):
                return

            rot = self.rotation  # get value from annot object
            if rot == -1:  # nothing to change
                return

            M = (self.rect.tl + self.rect.br) / 2  # center of annot rect

            if rot == 0:  # undo rotations
                if abs(apnmat - Matrix(1, 1)) < 1e-5:
                    return  # matrix already is a no-op
                quad = self.rect.morph(M, ~apnmat)  # derotate rect
                self.setRect(quad.rect)
                self.setAPNMatrix(Matrix(1, 1))  # appearance matrix = no-op
                return

            mat = Matrix(rot)
            quad = self.rect.morph(M, mat)
            self.setRect(quad.rect)
            self.setAPNMatrix(apnmat * mat)

        %}

        //---------------------------------------------------------------------
        // annotation set colors
        //---------------------------------------------------------------------
        %pythonprepend setColors %{
        """Set 'stroke' and 'fill' colors.

        Use either a dict or the direct arguments.
        """
        CheckParent(self)
        if type(colors) is not dict:
            colors = {"fill": fill, "stroke": stroke}
        %}
        void setColors(PyObject *colors=NULL, PyObject *fill=NULL, PyObject *stroke=NULL)
        {
            if (!PyDict_Check(colors)) return;
            pdf_annot *annot = (pdf_annot *) $self;
            int type = pdf_annot_type(gctx, annot);
            PyObject *ccol, *icol;
            ccol = PyDict_GetItem(colors, dictkey_stroke);
            icol = PyDict_GetItem(colors, dictkey_fill);
            int i, n;
            float col[4];
            n = 0;
            if (EXISTS(ccol)) {
                JM_color_FromSequence(ccol, &n, col);
                fz_try(gctx) {
                    pdf_set_annot_color(gctx, annot, n, col);
                }
                fz_catch(gctx) {
                    JM_Warning("annot type has no stroke color");
                }
            }
            n = 0;
            if (EXISTS(icol)) {
                JM_color_FromSequence(icol, &n, col);
                if (type != PDF_ANNOT_REDACT) {
                    fz_try(gctx)
                        pdf_set_annot_interior_color(gctx, annot, n, col);
                    fz_catch(gctx)
                        JM_Warning("annot type has no fill color");
                } else {
                    pdf_obj *arr = pdf_new_array(gctx, annot->page->doc, n);
                    for (i = 0; i < n; i++) {
                        pdf_array_push_real(gctx, arr, col[i]);
                    }
                    pdf_dict_put_drop(gctx, annot->obj, PDF_NAME(IC), arr);
                }
            }
            return;
        }

        //---------------------------------------------------------------------
        // annotation lineEnds
        //---------------------------------------------------------------------
        %pythoncode %{@property%}
        PARENTCHECK(lineEnds, """Line end codes.""")
        PyObject *lineEnds()
        {
            pdf_annot *annot = (pdf_annot *) $self;

            // return nothing for invalid annot types
            if (!pdf_annot_has_line_ending_styles(gctx, annot))
                return_none;

            int lstart = (int) pdf_annot_line_start_style(gctx, annot);
            int lend = (int) pdf_annot_line_end_style(gctx, annot);
            return Py_BuildValue("ii", lstart, lend);
        }

        //---------------------------------------------------------------------
        // annotation set line ends
        //---------------------------------------------------------------------
        PARENTCHECK(setLineEnds, """Set line end codes.""")
        void setLineEnds(int start, int end)
        {
            pdf_annot *annot = (pdf_annot *) $self;
            if (pdf_annot_has_line_ending_styles(gctx, annot))
                pdf_set_annot_line_ending_styles(gctx, annot, start, end);
            else
                JM_Warning("annot type has no line ends");
        }

        //---------------------------------------------------------------------
        // annotation type
        //---------------------------------------------------------------------
        PARENTCHECK(type, """Annotation type.""")
        %pythoncode %{@property%}
        PyObject *type()
        {
            pdf_annot *annot = (pdf_annot *) $self;
            int type = pdf_annot_type(gctx, annot);
            const char *c = pdf_string_from_annot_type(gctx, type);
            pdf_obj *o = pdf_dict_gets(gctx, annot->obj, "IT");
            if (!o || !pdf_is_name(gctx, o))
                return Py_BuildValue("is", type, c);         // no IT entry
            const char *it = pdf_to_name(gctx, o);
            return Py_BuildValue("iss", type, c, it);
        }

        //---------------------------------------------------------------------
        // annotation opacity
        //---------------------------------------------------------------------
        PARENTCHECK(opacity, """Opacity.""")
        %pythoncode %{@property%}
        PyObject *opacity()
        {
            pdf_annot *annot = (pdf_annot *) $self;
            double opy = -1;
            pdf_obj *ca = pdf_dict_get(gctx, annot->obj, PDF_NAME(CA));
            if (pdf_is_number(gctx, ca))
                opy = pdf_to_real(gctx, ca);
            return Py_BuildValue("f", opy);
        }

        //---------------------------------------------------------------------
        // annotation set opacity
        //---------------------------------------------------------------------
        PARENTCHECK(setOpacity, """Set opacity.""")
        void setOpacity(float opacity)
        {
            pdf_annot *annot = (pdf_annot *) $self;
            if (!INRANGE(opacity, 0.0f, 1.0f))
            {
                pdf_set_annot_opacity(gctx, annot, 1);
                return;
            }
            pdf_set_annot_opacity(gctx, annot, opacity);
            if (opacity < 1.0f)
            {
                annot->page->transparency = 1;
            }
        }


        //---------------------------------------------------------------------
        // annotation get attached file info
        //---------------------------------------------------------------------
        FITZEXCEPTION(fileInfo, !result)
        PARENTCHECK(fileInfo, """Attached file information.""")
        PyObject *fileInfo()
        {
            PyObject *res = PyDict_New();  // create Python dict
            char *filename = NULL;
            char *desc = NULL;
            int length = -1, size = -1;
            pdf_obj *stream = NULL, *o = NULL, *fs = NULL;
            pdf_annot *annot = (pdf_annot *) $self;

            fz_try(gctx) {
                int type = (int) pdf_annot_type(gctx, annot);
                if (type != PDF_ANNOT_FILE_ATTACHMENT)
                    THROWMSG(gctx, "bad annot type");
                stream = pdf_dict_getl(gctx, annot->obj, PDF_NAME(FS),
                                   PDF_NAME(EF), PDF_NAME(F), NULL);
                if (!stream) THROWMSG(gctx, "bad PDF: file entry not found");
            }
            fz_catch(gctx) {
                return NULL;
            }

            fs = pdf_dict_get(gctx, annot->obj, PDF_NAME(FS));

            o = pdf_dict_get(gctx, fs, PDF_NAME(UF));
            if (o) {
                filename = (char *) pdf_to_text_string(gctx, o);
            } else {
                o = pdf_dict_get(gctx, fs, PDF_NAME(F));
                if (o) filename = (char *) pdf_to_text_string(gctx, o);
            }

            o = pdf_dict_get(gctx, fs, PDF_NAME(Desc));
            if (o) desc = (char *) pdf_to_text_string(gctx, o);

            o = pdf_dict_get(gctx, stream, PDF_NAME(Length));
            if (o) length = pdf_to_int(gctx, o);

            o = pdf_dict_getl(gctx, stream, PDF_NAME(Params),
                                PDF_NAME(Size), NULL);
            if (o) size = pdf_to_int(gctx, o);

            DICT_SETITEM_DROP(res, dictkey_filename, JM_EscapeStrFromStr(filename));
            DICT_SETITEM_DROP(res, dictkey_desc, JM_UnicodeFromStr(desc));
            DICT_SETITEM_DROP(res, dictkey_length, Py_BuildValue("i", length));
            DICT_SETITEM_DROP(res, dictkey_size, Py_BuildValue("i", size));
            return res;
        }

        //---------------------------------------------------------------------
        // annotation get attached file content
        //---------------------------------------------------------------------
        FITZEXCEPTION(fileGet, !result)
        PARENTCHECK(fileGet, """Attached file content.""")
        PyObject *fileGet()
        {
            PyObject *res = NULL;
            pdf_obj *stream = NULL;
            fz_buffer *buf = NULL;
            pdf_annot *annot = (pdf_annot *) $self;
            fz_var(buf);
            fz_try(gctx) {
                int type = (int) pdf_annot_type(gctx, annot);
                if (type != PDF_ANNOT_FILE_ATTACHMENT)
                    THROWMSG(gctx, "bad annot type");
                stream = pdf_dict_getl(gctx, annot->obj, PDF_NAME(FS),
                                   PDF_NAME(EF), PDF_NAME(F), NULL);
                if (!stream) THROWMSG(gctx, "bad PDF: file entry not found");
                buf = pdf_load_stream(gctx, stream);
                res = JM_BinFromBuffer(gctx, buf);
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, buf);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return res;
        }

        //---------------------------------------------------------------------
        // annotation get attached sound stream
        //---------------------------------------------------------------------
        FITZEXCEPTION(soundGet, !result)
        PARENTCHECK(soundGet, """Retrieve sound stream.""")
        PyObject *soundGet()
        {
            PyObject *res = NULL;
            PyObject *stream = NULL;
            fz_buffer *buf = NULL;
            pdf_obj *obj = NULL;
            pdf_annot *annot = (pdf_annot *) $self;
            fz_var(buf);
            fz_try(gctx) {
                int type = (int) pdf_annot_type(gctx, annot);
                pdf_obj *sound = pdf_dict_get(gctx, annot->obj, PDF_NAME(Sound));
                if (type != PDF_ANNOT_SOUND || !sound)
                    THROWMSG(gctx, "bad annot type");
                if (pdf_dict_get(gctx, sound, PDF_NAME(F))) {
                    THROWMSG(gctx, "unsupported sound stream");
                }
                res = PyDict_New();
                obj = pdf_dict_get(gctx, sound, PDF_NAME(R));
                if (obj) {
                    DICT_SETITEMSTR_DROP(res, "rate",
                            Py_BuildValue("f", pdf_to_real(gctx, obj)));
                }
                obj = pdf_dict_get(gctx, sound, PDF_NAME(C));
                if (obj) {
                    DICT_SETITEMSTR_DROP(res, "channels",
                            Py_BuildValue("i", pdf_to_int(gctx, obj)));
                }
                obj = pdf_dict_get(gctx, sound, PDF_NAME(B));
                if (obj) {
                    DICT_SETITEMSTR_DROP(res, "bps",
                            Py_BuildValue("i", pdf_to_int(gctx, obj)));
                }
                obj = pdf_dict_get(gctx, sound, PDF_NAME(E));
                if (obj) {
                    DICT_SETITEMSTR_DROP(res, "encoding",
                            Py_BuildValue("s", pdf_to_name(gctx, obj)));
                }
                obj = pdf_dict_gets(gctx, sound, "CO");
                if (obj) {
                    DICT_SETITEMSTR_DROP(res, "compression",
                            Py_BuildValue("s", pdf_to_name(gctx, obj)));
                }
                buf = pdf_load_stream(gctx, sound);
                stream = JM_BinFromBuffer(gctx, buf);
                DICT_SETITEMSTR_DROP(res, "stream", stream);
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, buf);
            }
            fz_catch(gctx) {
                Py_CLEAR(res);
                return NULL;
            }
            return res;
        }

        //---------------------------------------------------------------------
        // annotation update attached file
        //---------------------------------------------------------------------
        FITZEXCEPTION(fileUpd, !result)
        %pythonprepend fileUpd %{
        """Update attached file."""
        CheckParent(self)%}

        PyObject *fileUpd(PyObject *buffer=NULL, char *filename=NULL, char *ufilename=NULL, char *desc=NULL)
        {
            pdf_document *pdf = NULL;       // to be filled in
            char *data = NULL;              // for new file content
            fz_buffer *res = NULL;          // for compressed content
            pdf_obj *stream = NULL, *fs = NULL;
            int64_t size = 0;
            pdf_annot *annot = (pdf_annot *) $self;
            fz_try(gctx) {
                pdf = annot->page->doc;     // the owning PDF
                int type = (int) pdf_annot_type(gctx, annot);
                if (type != PDF_ANNOT_FILE_ATTACHMENT)
                    THROWMSG(gctx, "bad annot type");
                stream = pdf_dict_getl(gctx, annot->obj, PDF_NAME(FS),
                                   PDF_NAME(EF), PDF_NAME(F), NULL);
                // the object for file content
                if (!stream) THROWMSG(gctx, "bad PDF: no /EF object");

                fs = pdf_dict_get(gctx, annot->obj, PDF_NAME(FS));

                // file content given
                res = JM_BufferFromBytes(gctx, buffer);
                if (buffer && !res) THROWMSG(gctx, "bad type: 'buffer'");
                if (res) {
                    JM_update_stream(gctx, pdf, stream, res, 1);
                    // adjust /DL and /Size parameters
                    int64_t len = (int64_t) fz_buffer_storage(gctx, res, NULL);
                    pdf_obj *l = pdf_new_int(gctx, len);
                    pdf_dict_put(gctx, stream, PDF_NAME(DL), l);
                    pdf_dict_putl(gctx, stream, l, PDF_NAME(Params), PDF_NAME(Size), NULL);
                }

                if (filename) {
                    pdf_dict_put_text_string(gctx, stream, PDF_NAME(F), filename);
                    pdf_dict_put_text_string(gctx, fs, PDF_NAME(F), filename);
                    pdf_dict_put_text_string(gctx, stream, PDF_NAME(UF), filename);
                    pdf_dict_put_text_string(gctx, fs, PDF_NAME(UF), filename);
                    pdf_dict_put_text_string(gctx, annot->obj, PDF_NAME(Contents), filename);
                }

                if (ufilename) {
                    pdf_dict_put_text_string(gctx, stream, PDF_NAME(UF), ufilename);
                    pdf_dict_put_text_string(gctx, fs, PDF_NAME(UF), ufilename);
                }

                if (desc) {
                    pdf_dict_put_text_string(gctx, stream, PDF_NAME(Desc), desc);
                    pdf_dict_put_text_string(gctx, fs, PDF_NAME(Desc), desc);
                }
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) {
                return NULL;
            }
            pdf->dirty = 1;
            return_none;
        }

        //---------------------------------------------------------------------
        // annotation info
        //---------------------------------------------------------------------
        %pythoncode %{@property%}
        PARENTCHECK(info, """Various information details.""")
        PyObject *info()
        {
            pdf_annot *annot = (pdf_annot *) $self;
            PyObject *res = PyDict_New();
            pdf_obj *o;

            DICT_SETITEM_DROP(res, dictkey_content,
                          JM_UnicodeFromStr(pdf_annot_contents(gctx, annot)));

            o = pdf_dict_get(gctx, annot->obj, PDF_NAME(Name));
            DICT_SETITEM_DROP(res, dictkey_name, JM_UnicodeFromStr(pdf_to_name(gctx, o)));

            // Title (= author)
            o = pdf_dict_get(gctx, annot->obj, PDF_NAME(T));
            DICT_SETITEM_DROP(res, dictkey_title, JM_UnicodeFromStr(pdf_to_text_string(gctx, o)));

            // CreationDate
            o = pdf_dict_gets(gctx, annot->obj, "CreationDate");
            DICT_SETITEM_DROP(res, dictkey_creationDate,
                          JM_UnicodeFromStr(pdf_to_text_string(gctx, o)));

            // ModDate
            o = pdf_dict_get(gctx, annot->obj, PDF_NAME(M));
            DICT_SETITEM_DROP(res, dictkey_modDate, JM_UnicodeFromStr(pdf_to_text_string(gctx, o)));

            // Subj
            o = pdf_dict_gets(gctx, annot->obj, "Subj");
            DICT_SETITEM_DROP(res, dictkey_subject,
                          Py_BuildValue("s",pdf_to_text_string(gctx, o)));

            // Identification (PDF key /NM)
            o = pdf_dict_gets(gctx, annot->obj, "NM");
            DICT_SETITEM_DROP(res, dictkey_id,
                          JM_UnicodeFromStr(pdf_to_text_string(gctx, o)));

            return res;
        }

        //---------------------------------------------------------------------
        // annotation set information
        //---------------------------------------------------------------------
        FITZEXCEPTION(setInfo, !result)
        %pythonprepend setInfo %{
        """Set various properties."""
        CheckParent(self)
        if type(info) is dict:  # build the args from the dictionary
            content = info.get("content", None)
            title = info.get("title", None)
            creationDate = info.get("creationDate", None)
            modDate = info.get("modDate", None)
            subject = info.get("subject", None)
            info = None
        %}
        PyObject *setInfo(PyObject *info=NULL, char *content=NULL, char *title=NULL,
                          char *creationDate=NULL, char *modDate=NULL, char *subject=NULL)
        {
            pdf_annot *annot = (pdf_annot *) $self;
            // use this to indicate a 'markup' annot type
            int is_markup = pdf_annot_has_author(gctx, annot);
            fz_try(gctx) {
                // contents
                if (content)
                    pdf_set_annot_contents(gctx, annot, content);

                if (is_markup) {
                    // title (= author)
                    if (title)
                        pdf_set_annot_author(gctx, annot, title);

                    // creation date
                    if (creationDate)
                        pdf_dict_put_text_string(gctx, annot->obj,
                                                 PDF_NAME(CreationDate), creationDate);

                    // mod date
                    if (modDate)
                        pdf_dict_put_text_string(gctx, annot->obj,
                                                 PDF_NAME(M), modDate);

                    // subject
                    if (subject)
                        pdf_dict_puts_drop(gctx, annot->obj, "Subj",
                                           pdf_new_text_string(gctx, subject));
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        //---------------------------------------------------------------------
        // annotation border
        //---------------------------------------------------------------------
        %pythoncode %{@property%}
        PARENTCHECK(border, """Border information.""")
        PyObject *border()
        {
            pdf_annot *annot = (pdf_annot *) $self;
            return JM_annot_border(gctx, annot->obj);
        }

        //---------------------------------------------------------------------
        // set annotation border
        //---------------------------------------------------------------------
        %pythonprepend setBorder %{
        """Set border properties.

        Either a dict, or direct arguments width, style and dashes."""
        CheckParent(self)
        if type(border) is not dict:
            border = {"width": width, "style": style, "dashes": dashes}
        %}
        PyObject *setBorder(PyObject *border=NULL, float width=0, char *style=NULL, PyObject *dashes=NULL)
        {
            pdf_annot *annot = (pdf_annot *) $self;
            return JM_annot_set_border(gctx, border, annot->page->doc, annot->obj);
        }

        //---------------------------------------------------------------------
        // annotation flags
        //---------------------------------------------------------------------
        %pythoncode %{@property%}
        PARENTCHECK(flags, """Flags field.""")
        int flags()
        {
            pdf_annot *annot = (pdf_annot *) $self;
            return pdf_annot_flags(gctx, annot);
        }

        //---------------------------------------------------------------------
        // annotation clean contents
        //---------------------------------------------------------------------
        FITZEXCEPTION(_cleanContents, !result)
        PARENTCHECK(_cleanContents, """Clean appearance contents object.""")
        PyObject *_cleanContents(int sanitize=0)
        {
            pdf_annot *annot = (pdf_annot *) $self;
            pdf_filter_options filter = {
                NULL,  // opaque
                NULL,  // image filter
                NULL,  // text filter
                NULL,  // after text
                NULL,  // end page
                1,     // recurse: true
                1,     // instance forms
                1,     // sanitize,
                0      // do not ascii-escape binary data
                };
            filter.sanitize = sanitize;
            fz_try(gctx) {
                pdf_filter_annot_contents(gctx, annot->page->doc, annot, &filter);
            }
            fz_catch(gctx) {
                return NULL;
            }
            pdf_dirty_annot(gctx, annot);
            return_none;
        }

        //---------------------------------------------------------------------
        // set annotation flags
        //---------------------------------------------------------------------
        PARENTCHECK(setFlags, """Set annotation flags.""")
        void setFlags(int flags)
        {
            pdf_annot *annot = (pdf_annot *) $self;
            pdf_set_annot_flags(gctx, annot, flags);
        }

        //---------------------------------------------------------------------
        // annotation delete responses
        //---------------------------------------------------------------------
        FITZEXCEPTION(delete_responses, !result)
        PARENTCHECK(delete_responses, """Delete responding annotations.""")
        PyObject *delete_responses()
        {
            pdf_annot *annot = (pdf_annot *) $self;
            pdf_page *page = annot->page;
            pdf_annot *irt_annot = NULL;
            fz_try(gctx) {
                while (1) {
                    irt_annot = JM_find_annot_irt(gctx, annot);
                    if (!irt_annot)
                        break;
                    JM_delete_annot(gctx, page, irt_annot);
                }
                pdf_dict_del(gctx, annot->obj, PDF_NAME(Popup));
                pdf_obj *annots = pdf_dict_get(gctx, page->obj, PDF_NAME(Annots));
                int i, n = pdf_array_len(gctx, annots), found = 0;
                for (i = n - 1; i >= 0; i--) {
                    pdf_obj *o = pdf_array_get(gctx, annots, i);
                    pdf_obj *p = pdf_dict_get(gctx, o, PDF_NAME(Parent));
                    if (!p)
                        continue;
                    if (!pdf_objcmp(gctx, p, annot->obj)) {
                        pdf_array_delete(gctx, annots, i);
                        found = 1;
                    }
                }
                if (found > 0) {
                    pdf_dict_put(gctx, page->obj, PDF_NAME(Annots), annots);
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            pdf_dirty_annot(gctx, annot);
            return_none;
        }

        //---------------------------------------------------------------------
        // next annotation
        //---------------------------------------------------------------------
        PARENTCHECK(next, """Next annotation.""")
        %pythonappend next %{
        if not val:
            return None
        val.thisown = True
        val.parent = self.parent  # copy owning page object from previous annot
        val.parent._annot_refs[id(val)] = val

        if val.type[0] == PDF_ANNOT_WIDGET:
            widget = Widget()
            TOOLS._fill_widget(val, widget)
            val = widget
        %}
        %pythoncode %{@property%}
        struct Annot *next()
        {
            pdf_annot *this_annot = (pdf_annot *) $self;
            int type = pdf_annot_type(gctx, this_annot);
            pdf_annot *annot;

            if (type != PDF_ANNOT_WIDGET)
            {
                annot = pdf_next_annot(gctx, this_annot);
            }
            else
            {
                annot = (pdf_widget *) pdf_next_widget(gctx, (pdf_widget *) this_annot);
            }

            if (annot)
                pdf_keep_annot(gctx, annot);
            return (struct Annot *) annot;
        }


        //---------------------------------------------------------------------
        // annotation pixmap
        //---------------------------------------------------------------------
        FITZEXCEPTION(getPixmap, !result)
        PARENTCHECK(getPixmap, """Annotation Pixmap.""")
        %pythonprepend getPixmap
%{"""Annotation Pixmap."""

CheckParent(self)
cspaces = {"gray": csGRAY, "rgb": csRGB, "cmyk": csCMYK}
if type(colorspace) is str:
    colorspace = cspaces.get(colorspace.lower(), None)
%}
        struct Pixmap *
        getPixmap(PyObject *matrix = NULL, struct Colorspace *colorspace = NULL, int alpha = 0)
        {
            fz_matrix ctm = JM_matrix_from_py(matrix);
            fz_colorspace *cs = (fz_colorspace *) colorspace;
            fz_pixmap *pix = NULL;
            if (!cs) {
                cs = fz_device_rgb(gctx);
            }

            fz_try(gctx) {
                pix = pdf_new_pixmap_from_annot(gctx, (pdf_annot *) $self, ctm, cs, NULL, alpha);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct Pixmap *) pix;
        }


        %pythoncode %{
        def _erase(self):
            try:
                self.parent._forget_annot(self)
            except:
                return
            if getattr(self, "thisown", False):
                self.__swig_destroy__(self)
                self.thisown = False
            self.parent = None

        def __str__(self):
            CheckParent(self)
            return "'%s' annotation on %s" % (self.type[1], str(self.parent))

        def __repr__(self):
            CheckParent(self)
            return "'%s' annotation on %s" % (self.type[1], str(self.parent))

        def __del__(self):
            if self.parent is None:
                return
            self._erase()%}
    }
};
%clearnodefaultctor;

//-----------------------------------------------------------------------------
// fz_link
//-----------------------------------------------------------------------------
%nodefaultctor;
struct Link
{
    %immutable;
    %extend {
        ~Link() {
            DEBUGMSG1("Link");
            fz_drop_link(gctx, (fz_link *) $self);
            DEBUGMSG2;
        }

        PyObject *_border(struct Document *doc, int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) doc);
            if (!pdf) return_none;
            pdf_obj *link_obj = pdf_new_indirect(gctx, pdf, xref, 0);
            if (!link_obj) return_none;
            PyObject *b = JM_annot_border(gctx, link_obj);
            pdf_drop_obj(gctx, link_obj);
            return b;
        }

        PyObject *_setBorder(PyObject *border, struct Document *doc, int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) doc);
            if (!pdf) return_none;
            pdf_obj *link_obj = pdf_new_indirect(gctx, pdf, xref, 0);
            if (!link_obj) return_none;
            PyObject *b = JM_annot_set_border(gctx, border, pdf, link_obj);
            pdf_drop_obj(gctx, link_obj);
            return b;
        }

        PyObject *_colors(struct Document *doc, int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) doc);
            if (!pdf) return_none;
            pdf_obj *link_obj = pdf_new_indirect(gctx, pdf, xref, 0);
            if (!link_obj) return_none;
            PyObject *b = JM_annot_colors(gctx, link_obj);
            pdf_drop_obj(gctx, link_obj);
            return b;
        }

        PyObject *_setColors(PyObject *colors, struct Document *doc, int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) doc);
            pdf_obj *arr = NULL;
            int i;
            if (!pdf) return_none;
            if (!PyDict_Check(colors)) return_none;
            float scol[4] = {0.0f, 0.0f, 0.0f, 0.0f};
            int nscol = 0;
            float fcol[4] = {0.0f, 0.0f, 0.0f, 0.0f};
            int nfcol = 0;
            PyObject *stroke = PyDict_GetItem(colors, dictkey_stroke);
            PyObject *fill = PyDict_GetItem(colors, dictkey_fill);
            JM_color_FromSequence(stroke, &nscol, scol);
            JM_color_FromSequence(fill, &nfcol, fcol);
            if (!nscol && !nfcol) return_none;
            pdf_obj *link_obj = pdf_new_indirect(gctx, pdf, xref, 0);
            if (!link_obj) return_none;
            if (nscol > 0)
            {
                arr = pdf_new_array(gctx, pdf, nscol);
                for (i = 0; i < nscol; i++)
                    pdf_array_push_real(gctx, arr, scol[i]);
                pdf_dict_put_drop(gctx, link_obj, PDF_NAME(C), arr);
            }
            if (nfcol > 0) JM_Warning("this annot type has no fill color)");
            pdf_drop_obj(gctx, link_obj);
            return_none;
        }

        %pythoncode %{
        @property
        def border(self):
            return self._border(self.parent.parent.this, self.xref)

        def setBorder(self, border=None, width=0, dashes=None, style=None):
            if type(border) is not dict:
                border = {"width": width, "style": style, "dashes": dashes}
            return self._setBorder(border, self.parent.parent.this, self.xref)

        @property
        def colors(self):
            return self._colors(self.parent.parent.this, self.xref)

        def setColors(self, colors=None, stroke=None, fill=None):
            if type(colors) is not dict:
                colors = {"fill": fill, "stroke": stroke}
            return self._setColors(colors, self.parent.parent.this, self.xref)
        %}
        %pythoncode %{@property%}
        PARENTCHECK(uri, """Uri string.""")
        PyObject *uri()
        {
            fz_link *this_link = (fz_link *) $self;
            return JM_UnicodeFromStr(this_link->uri);
        }

        %pythoncode %{@property%}
        PARENTCHECK(isExternal, """External indicator.""")
        PyObject *isExternal()
        {
            fz_link *this_link = (fz_link *) $self;
            if (!this_link->uri) Py_RETURN_FALSE;
            return JM_BOOL(fz_is_external_link(gctx, this_link->uri));
        }

        %pythoncode
        %{
        page = -1
        @property
        def dest(self):
            """Create link destination details."""
            if hasattr(self, "parent") and self.parent is None:
                raise ValueError("orphaned object: parent is None")
            if self.parent.parent.isClosed or self.parent.parent.isEncrypted:
                raise ValueError("document closed or encrypted")
            doc = self.parent.parent

            if self.isExternal or self.uri.startswith("#"):
                uri = None
            else:
                uri = doc.resolveLink(self.uri)

            return linkDest(self, uri)
        %}

        PARENTCHECK(rect, """Rectangle ('hot area').""")
        %pythoncode %{@property%}
        %pythonappend rect %{val = Rect(val)%}
        PyObject *rect()
        {
            fz_link *this_link = (fz_link *) $self;
            return JM_py_from_rect(this_link->rect);
        }

        //---------------------------------------------------------------------
        // next link
        //---------------------------------------------------------------------
        // we need to increase the link refs number
        // so that it will not be freed when the head is dropped
        PARENTCHECK(next, """Next link.""")
        %pythonappend next %{
            if val:
                val.thisown = True
                val.parent = self.parent  # copy owning page from prev link
                val.parent._annot_refs[id(val)] = val
                if self.xref > 0:  # prev link has an xref
                    link_xrefs = self.parent._getLinkXrefs()
                    idx = link_xrefs.index(self.xref)
                    val.xref = link_xrefs[idx + 1]
                else:
                    val.xref = 0
        %}
        %pythoncode %{@property%}
        struct Link *next()
        {
            fz_link *this_link = (fz_link *) $self;
            fz_link *next_link = this_link->next;
            if (!next_link) return NULL;
            next_link = fz_keep_link(gctx, next_link);
            return (struct Link *) next_link;
        }

        %pythoncode %{
        def _erase(self):
            try:
                self.parent._forget_annot(self)
            except:
                pass
            if getattr(self, "thisown", False):
                self.__swig_destroy__(self)
            self.parent = None
            self.thisown = False

        def __str__(self):
            CheckParent(self)
            return "link on " + str(self.parent)

        def __repr__(self):
            CheckParent(self)
            return "link on " + str(self.parent)

        def __del__(self):
            self._erase()%}

    }
};
%clearnodefaultctor;

//-----------------------------------------------------------------------------
// fz_display_list
//-----------------------------------------------------------------------------
struct DisplayList {
    %extend
    {
        ~DisplayList() {
            DEBUGMSG1("DisplayList");
            fz_drop_display_list(gctx, (fz_display_list *) $self);
            DEBUGMSG2;
        }
        FITZEXCEPTION(DisplayList, !result)
        %pythonappend DisplayList %{self.thisown = True%}
        DisplayList(PyObject *mediabox)
        {
            fz_display_list *dl = NULL;
            fz_try(gctx) {
                dl = fz_new_display_list(gctx, JM_rect_from_py(mediabox));
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct DisplayList *) dl;
        }

        FITZEXCEPTION(run, !result)
        PyObject *run(struct DeviceWrapper *dw, PyObject *m, PyObject *area) {
            fz_try(gctx) {
                fz_run_display_list(gctx, (fz_display_list *) $self, dw->device,
                    JM_matrix_from_py(m), JM_rect_from_py(area), NULL);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        //---------------------------------------------------------------------
        // DisplayList.rect
        //---------------------------------------------------------------------
        %pythoncode%{@property%}
        %pythonappend rect %{val = Rect(val)%}
        PyObject *rect()
        {
            return JM_py_from_rect(fz_bound_display_list(gctx, (fz_display_list *) $self));
        }

        //---------------------------------------------------------------------
        // DisplayList.getPixmap
        //---------------------------------------------------------------------
        FITZEXCEPTION(getPixmap, !result)
        %pythonappend getPixmap %{val.thisown = True%}
        struct Pixmap *getPixmap(PyObject *matrix=NULL,
                                      struct Colorspace *colorspace=NULL,
                                      int alpha=0,
                                      PyObject *clip=NULL)
        {
            fz_colorspace *cs = NULL;
            fz_pixmap *pix = NULL;

            if (colorspace) cs = (fz_colorspace *) colorspace;
            else cs = fz_device_rgb(gctx);

            fz_try(gctx) {
                pix = JM_pixmap_from_display_list(gctx,
                          (fz_display_list *) $self, matrix, cs,
                           alpha, clip, NULL);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct Pixmap *) pix;
        }

        //---------------------------------------------------------------------
        // DisplayList.getTextPage
        //---------------------------------------------------------------------
        FITZEXCEPTION(getTextPage, !result)
        %pythonappend getTextPage %{val.thisown = True%}
        struct TextPage *getTextPage(int flags = 3)
        {
            fz_display_list *this_dl = (fz_display_list *) $self;
            fz_stext_page *tp = NULL;
            fz_try(gctx) {
                fz_stext_options stext_options = { 0 };
                stext_options.flags = flags;
                tp = fz_new_stext_page_from_display_list(gctx, this_dl, &stext_options);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct TextPage *) tp;
        }
        %pythoncode %{
        def __del__(self):
            if not type(self) is DisplayList: return
            if getattr(self, "thisown", False):
                self.__swig_destroy__(self)
            self.thisown = False
        %}
    }
};

//-----------------------------------------------------------------------------
// fz_stext_page
//-----------------------------------------------------------------------------
struct TextPage {
    %extend {
        ~TextPage()
        {
            DEBUGMSG1("TextPage");
            fz_drop_stext_page(gctx, (fz_stext_page *) $self);
            DEBUGMSG2;
        }

        FITZEXCEPTION(TextPage, !result)
        %pythonappend TextPage %{self.thisown = True%}
        TextPage(PyObject *mediabox)
        {
            fz_stext_page *tp = NULL;
            fz_try(gctx) {
                tp = fz_new_stext_page(gctx, JM_rect_from_py(mediabox));
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct TextPage *) tp;
        }

        //---------------------------------------------------------------------
        // method search()
        //---------------------------------------------------------------------
        FITZEXCEPTION(search, !result)
        %pythonprepend search
        %{"""Locate 'needle' returning rects or quads."""%}
        %pythonappend search %{
        if not val:
            return val
        items = len(val)
        for i in range(items):  # change entries to quads or rects
            q = Quad(val[i])
            if quads:
                val[i] = q
            else:
                val[i] = q.rect
        if quads:
            return val
        i = 0  # join overlapping rects on the same line
        while i < items - 1:
            v1 = val[i]
            v2 = val[i + 1]
            if v1.y1 != v2.y1 or (v1 & v2).isEmpty:
                i += 1
                continue  # no overlap on same line
            val[i] = v1 | v2  # join rectangles
            del val[i + 1]  # remove v2
            items -= 1  # reduce item count
        %}
        PyObject *search(const char *needle, int hit_max=0, int quads=1)
        {
            PyObject *liste = NULL;
            fz_try(gctx) {
                liste = JM_search_stext_page(gctx, (fz_stext_page *) $self, needle);
            }
            fz_always(gctx) {
                ;
            }
            fz_catch(gctx) {
                return NULL;
            }
            return liste;
        }


        //---------------------------------------------------------------------
        // Get list of all blocks with block type and bbox as a Python list
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getNewBlockList, !result)
        PyObject *
        _getNewBlockList(PyObject *page_dict, int raw)
        {
            fz_try(gctx) {
                JM_make_textpage_dict(gctx, (fz_stext_page *) $self, page_dict, raw);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }

        %pythoncode %{
        def _textpage_dict(self, raw=False):
            page_dict = {"width": self.rect.width, "height": self.rect.height}
            self._getNewBlockList(page_dict, raw)
            return page_dict
        %}


        //---------------------------------------------------------------------
        // Get text blocks with their bbox and concatenated lines
        // as a Python list
        //---------------------------------------------------------------------
        FITZEXCEPTION(extractBLOCKS, !result)
        %pythonprepend extractBLOCKS
        %{"""Return a list with text block information."""%}
        PyObject *
        extractBLOCKS()
        {
            fz_stext_block *block;
            fz_stext_line *line;
            fz_stext_char *ch;
            int block_n = -1;
            PyObject *text = NULL, *litem;
            fz_buffer *res = NULL;
            fz_var(res);
            fz_stext_page *this_tpage = (fz_stext_page *) $self;
            fz_rect tp_rect = this_tpage->mediabox;
            PyObject *lines = NULL;
            fz_try(gctx) {
                res = fz_new_buffer(gctx, 1024);
                lines = PyList_New(0);
                for (block = this_tpage->first_block; block; block = block->next) {
                    block_n++;
                    fz_rect blockrect = fz_empty_rect;
                    if (block->type == FZ_STEXT_BLOCK_TEXT) {
                        fz_clear_buffer(gctx, res);  // set text buffer to empty
                        int line_n = -1;
                        float last_y0 = 0.0;
                        int last_char = 0;
                        for (line = block->u.t.first_line; line; line = line->next) {
                            line_n++;
                            if (fz_is_empty_rect(fz_intersect_rect(tp_rect, line->bbox))) {
                                continue;
                            }
                            fz_rect linerect = fz_empty_rect;
                            /* append line no. 2 with new-line
                                    if (line_n > 0) {
                                        if (linerect.y0 != last_y0)
                                            fz_append_byte(gctx, res, 10);
                                        else
                                            fz_append_byte(gctx, res, 32);
                                    }
                                    last_y0 = linerect.y0;
                            */
                            for (ch = line->first_char; ch; ch = ch->next) {
                                fz_rect cbbox = JM_char_bbox(ch);
                                if (!fz_contains_rect(tp_rect, cbbox)) {
                                    continue;
                                }
                                JM_append_rune(gctx, res, ch->c);
                                last_char = ch->c;
                                linerect = fz_union_rect(linerect, JM_char_bbox(ch));
                            }
                            if (last_char != 10) {
                                fz_append_byte(gctx, res, 10);
                            }
                            blockrect = fz_union_rect(blockrect, linerect);
                        }
                        text = JM_EscapeStrFromBuffer(gctx, res);
                    } else if (fz_contains_rect(tp_rect, block->bbox)) {
                        fz_image *img = block->u.i.image;
                        fz_colorspace *cs = img->colorspace;
                        text = PyUnicode_FromFormat("<image: %s, width %d, height %d, bpc %d>", fz_colorspace_name(gctx, cs), img->w, img->h, img->bpc);
                        blockrect = fz_union_rect(blockrect, block->bbox);
                    }
                    if (!fz_is_empty_rect(blockrect)) {
                        litem = PyTuple_New(7);
                        PyTuple_SET_ITEM(litem, 0, Py_BuildValue("f", blockrect.x0));
                        PyTuple_SET_ITEM(litem, 1, Py_BuildValue("f", blockrect.y0));
                        PyTuple_SET_ITEM(litem, 2, Py_BuildValue("f", blockrect.x1));
                        PyTuple_SET_ITEM(litem, 3, Py_BuildValue("f", blockrect.y1));
                        PyTuple_SET_ITEM(litem, 4, Py_BuildValue("O", text));
                        PyTuple_SET_ITEM(litem, 5, Py_BuildValue("i", block_n));
                        PyTuple_SET_ITEM(litem, 6, Py_BuildValue("i", block->type));
                        LIST_APPEND_DROP(lines, litem);
                    }
                    Py_CLEAR(text);
                }
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, res);
                PyErr_Clear();
            }
            fz_catch(gctx) {
                return NULL;
            }
            return lines;
        }

        //---------------------------------------------------------------------
        // Get text words with their bbox
        //---------------------------------------------------------------------
        FITZEXCEPTION(extractWORDS, !result)
        %pythonprepend extractWORDS
        %{"""Return a list with text word information."""%}
        PyObject *
        extractWORDS()
        {
            fz_stext_block *block;
            fz_stext_line *line;
            fz_stext_char *ch;
            fz_buffer *buff = NULL;
            fz_var(buff);
            size_t buflen = 0;
            int block_n = -1, line_n, word_n;
            fz_rect wbbox = {0,0,0,0};  // word bbox
            fz_stext_page *this_tpage = (fz_stext_page *) $self;
            fz_rect tp_rect = this_tpage->mediabox;
            PyObject *lines = NULL;
            fz_try(gctx) {
                buff = fz_new_buffer(gctx, 64);
                lines = PyList_New(0);
                for (block = this_tpage->first_block; block; block = block->next) {
                    block_n++;
                    if (block->type != FZ_STEXT_BLOCK_TEXT) {
                        continue;
                    }
                    line_n = 0;
                    for (line = block->u.t.first_line; line; line = line->next) {
                        word_n = 0;                       // word counter per line
                        fz_clear_buffer(gctx, buff);      // reset word buffer
                        buflen = 0;                       // reset char counter
                        for (ch = line->first_char; ch; ch = ch->next) {
                            fz_rect cbbox = JM_char_bbox(ch);
                            if (!fz_contains_rect(tp_rect, cbbox)) {
                                continue;
                            }
                            if (ch->c == 32 && buflen == 0)
                                continue;                 // skip spaces at line start
                            if (ch->c == 32) {
                                word_n = JM_append_word(gctx, lines, buff, &wbbox,
                                                        block_n, line_n, word_n);
                                fz_clear_buffer(gctx, buff);
                                buflen = 0;               // reset char counter
                                continue;
                            }
                            // append one unicode character to the word
                            JM_append_rune(gctx, buff, ch->c);
                            buflen++;
                            // enlarge word bbox
                            wbbox = fz_union_rect(wbbox, JM_char_bbox(ch));
                        }
                        if (buflen) {
                            word_n = JM_append_word(gctx, lines, buff, &wbbox,
                                                    block_n, line_n, word_n);
                            fz_clear_buffer(gctx, buff);
                            buflen = 0;
                        }
                        line_n++;
                    }
                }
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, buff);
                PyErr_Clear();
            }
            fz_catch(gctx) {
                return NULL;
            }
            return lines;
        }

        //---------------------------------------------------------------------
        // TextPage rectangle
        //---------------------------------------------------------------------
        %pythoncode %{@property%}
        %pythonprepend rect
        %{"""Page rectangle."""%}
        %pythonappend rect %{val = Rect(val)%}
        PyObject *rect()
        {
            fz_stext_page *this_tpage = (fz_stext_page *) $self;
            fz_rect mediabox = this_tpage->mediabox;
            return JM_py_from_rect(mediabox);
        }

        //---------------------------------------------------------------------
        // method _extractText()
        //---------------------------------------------------------------------
        FITZEXCEPTION(_extractText, !result)
        %newobject _extractText;
        PyObject *_extractText(int format)
        {
            fz_buffer *res = NULL;
            fz_output *out = NULL;
            PyObject *text = NULL;
            fz_var(res);
            fz_var(out);
            fz_stext_page *this_tpage = (fz_stext_page *) $self;
            fz_try(gctx) {
                res = fz_new_buffer(gctx, 1024);
                switch(format) {
                    case(1):
                        out = fz_new_output_with_buffer(gctx, res);
                        fz_print_stext_page_as_html(gctx, out, this_tpage, 0);
                        break;
                    case(3):
                        out = fz_new_output_with_buffer(gctx, res);
                        fz_print_stext_page_as_xml(gctx, out, this_tpage, 0);
                        break;
                    case(4):
                        out = fz_new_output_with_buffer(gctx, res);
                        fz_print_stext_page_as_xhtml(gctx, out, this_tpage, 0);
                        break;
                    default:
                        out = fz_new_output_with_buffer(gctx, res);
                        JM_print_stext_page_as_text(gctx, out, this_tpage);
                        break;
                }
                text = JM_UnicodeFromBuffer(gctx, res);

            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, res);
                fz_drop_output(gctx, out);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return text;
        }


        //---------------------------------------------------------------------
        // method extractSelection()
        //---------------------------------------------------------------------
        PyObject *extractSelection(PyObject *pointa, PyObject *pointb)
        {
            fz_stext_page *this_tpage = (fz_stext_page *) $self;
            fz_point a = JM_point_from_py(pointa);
            fz_point b = JM_point_from_py(pointb);
            char *found = fz_copy_selection(gctx, this_tpage, a, b, 0);
            PyObject *rc = NULL;
            if (found) {
                rc = PyUnicode_FromString(found);
                JM_Free(found);
            } else {
                rc = EMPTY_STRING;
            }
            return rc;
        }

        %pythoncode %{
            def extractText(self):
                """Return simple, bare text on the page."""
                return self._extractText(0)


            def extractHTML(self):
                """Return page content as a HTML string."""
                return self._extractText(1)

            def extractJSON(self):
                """Return 'extractDICT' converted to JSON format."""
                import base64, json
                val = self._textpage_dict(raw=False)

                class b64encode(json.JSONEncoder):
                    def default(self,s):
                        if not fitz_py2 and type(s) is bytes:
                            return base64.b64encode(s).decode()
                        if type(s) is bytearray:
                            if fitz_py2:
                                return base64.b64encode(s)
                            else:
                                return base64.b64encode(s).decode()

                val = json.dumps(val, separators=(",", ":"), cls=b64encode, indent=1)
                return val

            def extractRAWJSON(self):
                """Return 'extractRAWDICT' converted to JSON format."""
                import base64, json
                val = self._textpage_dict(raw=True)

                class b64encode(json.JSONEncoder):
                    def default(self,s):
                        if not fitz_py2 and type(s) is bytes:
                            return base64.b64encode(s).decode()
                        if type(s) is bytearray:
                            if fitz_py2:
                                return base64.b64encode(s)
                            else:
                                return base64.b64encode(s).decode()

                val = json.dumps(val, separators=(",", ":"), cls=b64encode, indent=1)
                return val

            def extractXML(self):
                """Return page content as a XML string."""
                return self._extractText(3)

            def extractXHTML(self):
                """Return page content as a XHTML string."""
                return self._extractText(4)

            def extractDICT(self):
                """Return page content as a Python dict of images and text spans."""
                return self._textpage_dict(raw=False)

            def extractRAWDICT(self):
                """Return page content as a Python dict of images and text characters."""
                return self._textpage_dict(raw=True)

            def __del__(self):
                if not type(self) is TextPage: return
                if getattr(self, "thisown", False):
                    self.__swig_destroy__(self)
                self.thisown = False
        %}
    }
};

//-----------------------------------------------------------------------------
// Graftmap - only used internally for inter-PDF object copy operations
//-----------------------------------------------------------------------------
struct Graftmap
{
    %extend
    {
        ~Graftmap()
        {
            DEBUGMSG1("Graftmap");
            pdf_drop_graft_map(gctx, (pdf_graft_map *) $self);
            DEBUGMSG2;
        }

        FITZEXCEPTION(Graftmap, !result)
        %pythonappend Graftmap %{self.thisown = True%}
        Graftmap(struct Document *doc)
        {
            pdf_graft_map *map = NULL;
            fz_try(gctx) {
                pdf_document *dst = pdf_specifics(gctx, (fz_document *) doc);
                ASSERT_PDF(dst);
                map = pdf_new_graft_map(gctx, dst);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct Graftmap *) pdf_keep_graft_map(gctx, map);
        }
        %pythoncode %{
        def __del__(self):
            if not type(self) is Graftmap:
                return
            if getattr(self, "thisown", False):
                self.__swig_destroy__(self)
            self.thisown = False
        %}
    }
};


//-----------------------------------------------------------------------------
// TextWriter
//-----------------------------------------------------------------------------
struct TextWriter
{
    %extend {
        ~TextWriter()
        {
            DEBUGMSG1("TextWriter");
            fz_drop_text(gctx, (fz_text *) $self);
            DEBUGMSG2;
        }

        FITZEXCEPTION(TextWriter, !result)
        %pythonprepend TextWriter
        %{"""Stores text spans for later output on compatible PDF pages."""%}
        %pythonappend TextWriter %{
        self.opacity = opacity
        self.color = color
        self.rect = Rect(page_rect)
        self.ctm = Matrix(1, 0, 0, -1, 0, self.rect.height)
        self.ictm = ~self.ctm
        self.lastPoint = Point()
        self.lastPoint.__doc__ = "Position following last text insertion."
        self.textRect = Rect(0, 0, -1, -1)
        self.textRect.__doc__ = "Accumulated area of text spans."
        self.used_fonts = set()
        %}
        TextWriter(PyObject *page_rect, float opacity=1, PyObject *color=NULL )
        {
            fz_text *text = NULL;
            fz_try(gctx) {
                text = fz_new_text(gctx);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct TextWriter *) text;
        }

        FITZEXCEPTION(append, !result)
        %pythonprepend append %{
        """Store 'text' at point 'pos' using 'font' and 'fontsize'."""

        pos = Point(pos) * self.ictm
        if font is None:
            font = Font("helv")
        if not font.isWritable:
            raise ValueError("Unsupported font '%s'." % font.name)%}
        %pythonappend append %{
        self.lastPoint = Point(val[-2:]) * self.ctm
        self.textRect = self._bbox * self.ctm
        val = self.textRect, self.lastPoint
        if font.flags["mono"] == 1:
            self.used_fonts.add(font)
        %}
        PyObject *
        append(PyObject *pos, char *text, struct Font *font=NULL, float fontsize=11, char *language=NULL)
        {
            fz_text_language lang = fz_text_language_from_string(language);
            fz_point p = JM_point_from_py(pos);
            fz_matrix trm = fz_make_matrix(fontsize, 0, 0, fontsize, p.x, p.y);
            int bidi_level = 0, markup_dir = 0, wmode = 0;
            fz_try(gctx) {
                trm = fz_show_string(gctx, (fz_text *) $self, (fz_font *) font, trm, text, wmode, bidi_level, markup_dir, lang);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return JM_py_from_matrix(trm);
        }

        %pythoncode %{
        def appendv(self, pos, text, font=None, fontsize=11,
            language=None):
            lheight = fontsize * 1.2
            for c in text:
                self.append(pos, c, font=font, fontsize=fontsize,
                    language=language)
                pos.y += lheight
            return self.textRect, self.lastPoint
        %}


        %pythoncode %{@property%}
        %pythonappend _bbox%{val = Rect(val)%}
        PyObject *_bbox()
        {
            return JM_py_from_rect(fz_bound_text(gctx, (fz_text *) $self, NULL, fz_identity));
        }

        FITZEXCEPTION(writeText, !result)
        %pythonprepend writeText%{
        """Write the text to a PDF page having the TextWriter's page size.

        Args:
            page: a PDF page having same size.
            color: override text color.
            opacity: override transparency.
            overlay: put in foreground or background.
            morph: tuple(Point, Matrix), apply Matrix with fixpoint Point.
            render_mode: (int) PDF render mode operator 'Tr'.
        """

        CheckParent(page)
        if abs(self.rect - page.rect) > 1e-3:
            raise ValueError("incompatible page rect")
        if morph != None:
            if (type(morph) not in (tuple, list)
                or type(morph[0]) is not Point
                or type(morph[1]) is not Matrix
                ):
                raise ValueError("morph must be (Point, Matrix) or None")
        if getattr(opacity, "__float__", None) is None or opacity == -1:
            opacity = self.opacity
        if color is None:
            color = self.color
        %}
        %pythonappend writeText%{
        max_nums = val[0]
        content = val[1]
        max_alp, max_font = max_nums
        old_cont_lines = content.splitlines()

        new_cont_lines = ["q"]

        cb = page.CropBoxPosition
        if bool(cb):
            new_cont_lines.append("1 0 0 1 %g %g cm" % (cb.x, cb.y))

        if morph:
            p = morph[0] * self.ictm
            delta = Matrix(1, 1).preTranslate(p.x, p.y)
            matrix = ~delta * morph[1] * delta
            new_cont_lines.append("%g %g %g %g %g %g cm" % JM_TUPLE(matrix))

        for line in old_cont_lines:
            if line.endswith(" cm"):
                continue
            if line == "BT":
                new_cont_lines.append(line)
                new_cont_lines.append("%i Tr" % render_mode)
                continue
            if line.endswith(" gs"):
                alp = int(line.split()[0][4:]) + max_alp
                line = "/Alp%i gs" % alp
            elif line.endswith(" Tf"):
                temp = line.split()
                font = int(temp[0][2:]) + max_font
                line = " ".join(["/F%i" % font] + temp[1:])
            elif line.endswith(" rg"):
                new_cont_lines.append(line.replace("rg", "RG"))
            elif line.endswith(" g"):
                new_cont_lines.append(line.replace(" g", " G"))
            elif line.endswith(" k"):
                new_cont_lines.append(line.replace(" k", " K"))
            new_cont_lines.append(line)
        new_cont_lines.append("Q\n")
        content = "\n".join(new_cont_lines).encode("utf-8")
        TOOLS._insert_contents(page, content, overlay=overlay)
        val = None
        for font in self.used_fonts:
            repair_mono_font(page, font)
        %}
        PyObject *writeText(struct Page *page, PyObject *color=NULL, float opacity=-1, int overlay=1, PyObject *morph=NULL, int render_mode=0)
        {
            pdf_page *pdfpage = pdf_page_from_fz_page(gctx, (fz_page *) page);
            fz_rect mediabox = fz_bound_page(gctx, (fz_page *) page);
            pdf_obj *resources = NULL;
            fz_buffer *contents = NULL;
            fz_device *dev = NULL;
            PyObject *result = NULL, *max_nums, *cont_string;
            float alpha = 1;
            if (opacity >= 0 && opacity < 1)
                alpha = opacity;
            fz_colorspace *colorspace;
            int ncol = 1;
            float dev_color[4] = {0, 0, 0, 0};
            if (color) JM_color_FromSequence(color, &ncol, dev_color);
            switch(ncol) {
                case 3: colorspace = fz_device_rgb(gctx); break;
                case 4: colorspace = fz_device_cmyk(gctx); break;
                default: colorspace = fz_device_gray(gctx); break;
            }

            fz_try(gctx) {
                ASSERT_PDF(pdfpage);
                resources = pdf_new_dict(gctx, pdfpage->doc, 5);
                contents = fz_new_buffer(gctx, 1024);
                dev = pdf_new_pdf_device(gctx, pdfpage->doc, fz_identity,
                            mediabox, resources, contents);
                fz_fill_text(gctx, dev, (fz_text *) $self, fz_identity,
                    colorspace, dev_color, alpha, fz_default_color_params);
                fz_close_device(gctx, dev);

                // copy generated resources into the one of the page
                max_nums = JM_merge_resources(gctx, pdfpage, resources);
                cont_string = JM_EscapeStrFromBuffer(gctx, contents);
                result = Py_BuildValue("OO", max_nums, cont_string);
                Py_DECREF(cont_string);
                Py_DECREF(max_nums);
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, contents);
                pdf_drop_obj(gctx, resources);
                fz_drop_device(gctx, dev);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return result;
        }
        %pythoncode %{
        def __del__(self):
            if not type(self) is TextWriter:
                return
            self.__swig_destroy__(self)
        %}
    }
};


//-----------------------------------------------------------------------------
// Font
//-----------------------------------------------------------------------------
struct Font
{
    %extend
    {
        ~Font()
        {
            DEBUGMSG1("Font");
            fz_drop_font(gctx, (fz_font *) $self);
            DEBUGMSG2;
        }

        FITZEXCEPTION(Font, !result)
        %pythonprepend Font %{
        if fontname:
            if "/" in fontname or "\\" in fontname or "." in fontname:
                print("Warning: did you mean a fontfile?")

            if fontname.lower() in ("china-t", "china-s", "japan", "korea","china-ts", "china-ss", "japan-s", "korea-s", "cjk"):
                ordering = 0

            elif fontname.lower() in fitz_fontdescriptors.keys():
                import pymupdf_fonts  # optional fonts
                fontbuffer = pymupdf_fonts.myfont(fontname)  # make a copy
                fontname = None  # ensure using fontbuffer only
                del pymupdf_fonts  # remove package again

            elif ordering < 0:
                fontname = Base14_fontdict.get(fontname.lower(), fontname)
        %}
        Font(char *fontname=NULL, char *fontfile=NULL,
             PyObject *fontbuffer=NULL, int script=0,
             char *language=NULL, int ordering=-1, int is_bold=0,
             int is_italic=0, int is_serif=0)
        {
            fz_font *font = NULL;
            fz_try(gctx) {
                fz_text_language lang = fz_text_language_from_string(language);
                font = JM_get_font(gctx, fontname, fontfile,
                           fontbuffer, script, lang, ordering,
                           is_bold, is_italic, is_serif);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return (struct Font *) font;
        }


        %pythonprepend glyph_advance
        %{"""Return the glyph width of a unicode (font size 1)."""%}
        float glyph_advance(int chr, char *language=NULL, int script=0, int wmode=0)
        {
            fz_font *font;
            fz_text_language lang = fz_text_language_from_string(language);
            int gid = fz_encode_character_with_fallback(gctx, (fz_font *) $self, chr, script, lang, &font);
            return fz_advance_glyph(gctx, font, gid, wmode);
        }

        %pythonprepend glyph_bbox
        %{"""Return the glyph bbox of a unicode (font size 1)."""%}
        %pythonappend glyph_bbox %{val = Rect(val)%}
        PyObject *glyph_bbox(int chr, char *language=NULL, int script=0)
        {
            fz_font *font;
            fz_text_language lang = fz_text_language_from_string(language);
            int gid = fz_encode_character_with_fallback(gctx, (fz_font *) $self, chr, script, lang, &font);
            return JM_py_from_rect(fz_bound_glyph(gctx, font, gid, fz_identity));
        }

        %pythonprepend has_glyph
        %{"""Check whether font has a glyph for this unicode."""%}
        PyObject *has_glyph(int chr, char *language=NULL, int script=0, int fallback=0)
        {
            fz_font *font;
            fz_text_language lang;
            int gid = 0;
            if (fallback) {
                lang = fz_text_language_from_string(language);
                gid = fz_encode_character_with_fallback(gctx, (fz_font *) $self, chr, script, lang, &font);
            } else {
                gid = fz_encode_character(gctx, (fz_font *) $self, chr);
            }
            return Py_BuildValue("i", gid);
        }


        %pythoncode %{
        def valid_codepoints(self):
            from array import array
            gc = self.glyph_count
            cp = array("l", (0,) * gc)
            arr = cp.buffer_info()
            self._valid_unicodes(arr)
            return array("l", sorted(set(cp))[1:])
        %}
        void _valid_unicodes(PyObject *arr)
        {
            fz_font *font = (fz_font *) $self;
            PyObject *temp = PySequence_ITEM(arr, 0);
            void *ptr = PyLong_AsVoidPtr(temp);
            JM_valid_chars(gctx, font, ptr);
            Py_DECREF(temp);
        }


        %pythoncode %{@property%}
        PyObject *flags()
        {
            fz_font_flags_t *f = fz_font_flags((fz_font *) $self);
            if (!f) Py_RETURN_NONE;
            return Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i}",
            "mono", f->is_mono, "serif", f->is_serif, "bold", f->is_bold,
            "italic", f->is_italic, "substitute", f->ft_substitute,
            "stretch", f->ft_stretch, "fake-bold", f->fake_bold,
            "fake-italic", f->fake_italic, "opentype", f->has_opentype,
            "invalid-bbox", f->invalid_bbox);
        }


        %pythoncode %{@property%}
        PyObject *isWritable()
        {
            fz_font *font = (fz_font *) $self;
            if (fz_font_t3_procs(gctx, font) ||
                fz_font_flags(font)->ft_substitute ||
                !pdf_font_writing_supported(font)) {
                Py_RETURN_FALSE;
            }
            Py_RETURN_TRUE;
        }

        %pythoncode %{@property%}
        PyObject *name()
        {
            return JM_UnicodeFromStr(fz_font_name(gctx, (fz_font *) $self));
        }

        %pythoncode %{@property%}
        int glyph_count()
        {
            fz_font *this_font = (fz_font *) $self;
            return this_font->glyph_count;
        }

        %pythoncode %{@property%}
        PyObject *buffer()
        {
            fz_font *this_font = (fz_font *) $self;
            unsigned char *data = NULL;
            size_t len = fz_buffer_storage(gctx, this_font->buffer, &data);
            return JM_BinFromCharSize(data, len);
        }

        %pythoncode %{@property%}
        %pythonappend bbox%{val = Rect(val)%}
        PyObject *bbox()
        {
            fz_font *this_font = (fz_font *) $self;
            return JM_py_from_rect(fz_font_bbox(gctx, this_font));
        }

        %pythoncode %{@property%}
        %pythonprepend ascender
        %{"""Return the glyph ascender value."""%}
        float ascender()
        {
            return fz_font_ascender(gctx, (fz_font *) $self);
        }


        %pythoncode %{@property%}
        %pythonprepend descender
        %{"""Return the glyph descender value."""%}
        float descender()
        {
            return fz_font_descender(gctx, (fz_font *) $self);
        }


        %pythoncode %{
            def glyph_name_to_unicode(self, name):
                """Return the unicode for a glyph name."""
                return glyph_name_to_unicode(name)

            def unicode_to_glyph_name(self, ch):
                """Return the glyph name for a unicode."""
                return unicode_to_glyph_name(ch)

            def text_length(self, text, fontsize=11, wmode=0):
                """Calculate the length of a string for this font."""
                return fontsize * sum([self.glyph_advance(ord(c), wmode=wmode) for c in text])

            def __repr__(self):
                return "Font('%s')" % self.name

            def __del__(self):
                if type(self) is not Font:
                    return None
                self.__swig_destroy__(self)
        %}
    }
};


//-----------------------------------------------------------------------------
// Tools - a collection of tools and utilities
//-----------------------------------------------------------------------------
struct Tools
{
    %extend
    {
        %pythonprepend gen_id
        %{"""Return a unique positive integer."""%}
        PyObject *gen_id()
        {
            JM_UNIQUE_ID += 1;
            if (JM_UNIQUE_ID < 0) JM_UNIQUE_ID = 1;
            return Py_BuildValue("i", JM_UNIQUE_ID);
        }


        FITZEXCEPTION(set_icc, !result)
        %pythonprepend set_icc
        %{"""Set ICC color handling on or off."""%}
        PyObject *set_icc(int on=0)
        {
            fz_try(gctx) {
                if (on) {
                    if (FZ_ENABLE_ICC)
                        fz_enable_icc(gctx);
                    else
                        THROWMSG(gctx, "MuPDF generated without ICC suppot.");
                } else if (FZ_ENABLE_ICC) {
                    fz_disable_icc(gctx);
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }


        %pythonprepend store_shrink
        %{"""Free 'percent' of current store size."""%}
        PyObject *store_shrink(int percent)
        {
            if (percent >= 100) {
                fz_empty_store(gctx);
                return Py_BuildValue("i", 0);
            }
            if (percent > 0) fz_shrink_store(gctx, 100 - percent);
            return Py_BuildValue("i", (int) gctx->store->size);
        }


        %pythoncode%{@property%}
        %pythonprepend store_size
        %{"""MuPDF current store size."""%}
        PyObject *store_size()
        {
            return Py_BuildValue("i", (int) gctx->store->size);
        }


        %pythoncode%{@property%}
        %pythonprepend store_maxsize
        %{"""MuPDF store size limit."""%}
        PyObject *store_maxsize()
        {
            return Py_BuildValue("i", (int) gctx->store->max);
        }


        %pythonprepend show_aa_level
        %{"""Show anti-aliasing values."""%}
        %pythonappend show_aa_level %{
        temp = {"graphics": val[0], "text": val[1], "graphics_min_line_width": val[2]}
        val = temp%}
        PyObject *show_aa_level()
        {
            return Py_BuildValue("iif",
                fz_graphics_aa_level(gctx),
                fz_text_aa_level(gctx),
                fz_graphics_min_line_width(gctx));
        }


        %pythonprepend set_aa_level
        %{"""Set anti-aliasing level."""%}
        void set_aa_level(int level)
        {
            fz_set_aa_level(gctx, level);
        }


        %pythonprepend set_graphics_min_line_width
        %{"""Set the graphics minimum line width."""%}
        void set_graphics_min_line_width(float min_line_width)
        {
            fz_set_graphics_min_line_width(gctx, min_line_width);
        }


        %pythonprepend image_profile
        %{"""Metadata of an image binary stream."""%}
        PyObject *image_profile(PyObject *stream, int keep_image=0)
        {
            return JM_image_profile(gctx, stream, keep_image);
        }


        PyObject *_rotate_matrix(struct Page *page)
        {
            pdf_page *pdfpage = pdf_page_from_fz_page(gctx, (fz_page *) page);
            if (!pdfpage) return JM_py_from_matrix(fz_identity);
            return JM_py_from_matrix(JM_rotate_page_matrix(gctx, pdfpage));
        }


        PyObject *_derotate_matrix(struct Page *page)
        {
            pdf_page *pdfpage = pdf_page_from_fz_page(gctx, (fz_page *) page);
            if (!pdfpage) return JM_py_from_matrix(fz_identity);
            return JM_py_from_matrix(JM_derotate_page_matrix(gctx, pdfpage));
        }


        %pythoncode%{@property%}
        %pythonprepend fitz_config
        %{"""PyMuPDF configuration parameters."""%}
        PyObject *fitz_config()
        {
            return JM_fitz_config();
        }


        %pythonprepend glyph_cache_empty
        %{"""Empty the glyph cache."""%}
        void glyph_cache_empty()
        {
            fz_purge_glyph_cache(gctx);
        }


        FITZEXCEPTION(_fill_widget, !result)
        %pythonappend _fill_widget %{
            widget.rect = Rect(annot.rect)
            widget.xref = annot.xref
            widget.parent = annot.parent
            widget._annot = annot  # backpointer to annot object
            if not widget.script:
                widget.script = None
            if not widget.script_stroke:
                widget.script_stroke = None
            if not widget.script_format:
                widget.script_format = None
            if not widget.script_change:
                widget.script_change = None
            if not widget.script_calc:
                widget.script_calc = None
        %}
        PyObject *_fill_widget(struct Annot *annot, PyObject *widget)
        {
            fz_try(gctx) {
                JM_get_widget_properties(gctx, (pdf_annot *) annot, widget);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }


        FITZEXCEPTION(_save_widget, !result)
        PyObject *_save_widget(struct Annot *annot, PyObject *widget)
        {
            fz_try(gctx) {
                JM_set_widget_properties(gctx, (pdf_annot *) annot, widget);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }


        FITZEXCEPTION(_reset_widget, !result)
        PyObject *_reset_widget(struct Annot *annot)
        {
            fz_try(gctx) {
                pdf_annot *this_annot = (pdf_annot *) annot;
                pdf_document *pdf = pdf_get_bound_document(gctx, this_annot->obj);
                pdf_field_reset(gctx, pdf, this_annot->obj);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }


        FITZEXCEPTION(_parse_da, !result)
        %pythonappend _parse_da %{
        if not val:
            return ((0,), "", 0)
        font = "Helv"
        fsize = 12
        col = (0, 0, 0)
        dat = val.split()  # split on any whitespace
        for i, item in enumerate(dat):
            if item == "Tf":
                font = dat[i - 2][1:]
                fsize = float(dat[i - 1])
                dat[i] = dat[i-1] = dat[i-2] = ""
                continue
            if item == "g":            # unicolor text
                col = [(float(dat[i - 1]))]
                dat[i] = dat[i-1] = ""
                continue
            if item == "rg":           # RGB colored text
                col = [float(f) for f in dat[i - 3:i]]
                dat[i] = dat[i-1] = dat[i-2] = dat[i-3] = ""
                continue
            if item == "k":           # CMYK colored text
                col = [float(f) for f in dat[i - 4:i]]
                dat[i] = dat[i-1] = dat[i-2] = dat[i-3] = dat[i-4] = ""
                continue

        val = (col, font, fsize)
        %}
        PyObject *_parse_da(struct Annot *annot)
        {
            char *da_str = NULL;
            pdf_annot *this_annot = (pdf_annot *) annot;
            fz_try(gctx) {
                pdf_obj *da = pdf_dict_get_inheritable(gctx, this_annot->obj,
                                                       PDF_NAME(DA));
                if (!da) {
                    pdf_obj *trailer = pdf_trailer(gctx, this_annot->page->doc);
                    da = pdf_dict_getl(gctx, trailer, PDF_NAME(Root),
                                       PDF_NAME(AcroForm),
                                       PDF_NAME(DA),
                                       NULL);
                }
                da_str = (char *) pdf_to_text_string(gctx, da);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return JM_UnicodeFromStr(da_str);
        }


        PyObject *_update_da(struct Annot *annot, char *da_str)
        {
            fz_try(gctx) {
                pdf_annot *this_annot = (pdf_annot *) annot;
                pdf_dict_put_text_string(gctx, this_annot->obj, PDF_NAME(DA), da_str);
                pdf_dict_del(gctx, this_annot->obj, PDF_NAME(DS)); /* not supported */
                pdf_dict_del(gctx, this_annot->obj, PDF_NAME(RC)); /* not supported */
                pdf_dirty_annot(gctx, this_annot);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return_none;
        }


        FITZEXCEPTION(_get_all_contents, !result)
        %pythonprepend _get_all_contents
        %{"""Concatenate all /Contents objects of a page into a bytes object."""%}
        PyObject *_get_all_contents(struct Page *fzpage)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, (fz_page *) fzpage);
            fz_buffer *res = NULL;
            PyObject *result = NULL;
            fz_try(gctx) {
                ASSERT_PDF(page);
                res = JM_read_contents(gctx, page->obj);
                result = JM_BinFromBuffer(gctx, res);
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return result;
        }


        FITZEXCEPTION(_insert_contents, !result)
        %pythonprepend _insert_contents
        %{"""Add bytes as a new /Contents object for a page, and return its xref."""%}
        PyObject *_insert_contents(struct Page *page, PyObject *newcont, int overlay=1)
        {
            fz_buffer *contbuf = NULL;
            int xref = 0;
            pdf_page *pdfpage = pdf_page_from_fz_page(gctx, (fz_page *) page);
            fz_try(gctx) {
                ASSERT_PDF(pdfpage);
                contbuf = JM_BufferFromBytes(gctx, newcont);
                xref = JM_insert_contents(gctx, pdfpage->doc, pdfpage->obj, contbuf, overlay);
                pdfpage->doc->dirty = 1;
            }
            fz_always(gctx) {
                fz_drop_buffer(gctx, contbuf);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return Py_BuildValue("i", xref);
        }

        %pythonprepend mupdf_version
        %{"""Get version of MuPDF binary build."""%}
        PyObject *mupdf_version()
        {
            return Py_BuildValue("s", FZ_VERSION);
        }

        %pythonprepend mupdf_warnings
        %{"""Get the MuPDF warnings/errors with optional reset (default)."""%}
        %pythonappend mupdf_warnings %{
        val = "\n".join(val)
        if reset:
            self.reset_mupdf_warnings()%}
        PyObject *mupdf_warnings(int reset=1)
        {
            Py_INCREF(JM_mupdf_warnings_store);
            return JM_mupdf_warnings_store;
        }

        int _int_from_language(char *language)
        {
            return fz_text_language_from_string(language);
        }

        %pythonprepend reset_mupdf_warnings
        %{"""Empty the MuPDF warnings/errors store."""%}
        void reset_mupdf_warnings()
        {
            Py_CLEAR(JM_mupdf_warnings_store);
            JM_mupdf_warnings_store = PyList_New(0);
        }

        %pythonprepend mupdf_display_errors
        %{"""Set MuPDF error display to True or False."""%}
        PyObject *mupdf_display_errors(PyObject *value = NULL)
        {
            if (value == Py_True)
                JM_mupdf_show_errors = Py_True;
            else if (value == Py_False)
                JM_mupdf_show_errors = Py_False;
            Py_INCREF(JM_mupdf_show_errors);
            return JM_mupdf_show_errors;
        }

        PyObject *_transform_rect(PyObject *rect, PyObject *matrix)
        {
            return JM_py_from_rect(fz_transform_rect(JM_rect_from_py(rect), JM_matrix_from_py(matrix)));
        }

        PyObject *_intersect_rect(PyObject *r1, PyObject *r2)
        {
            return JM_py_from_rect(fz_intersect_rect(JM_rect_from_py(r1),
                                                     JM_rect_from_py(r2)));
        }

        PyObject *_include_point_in_rect(PyObject *r, PyObject *p)
        {
            return JM_py_from_rect(fz_include_point_in_rect(JM_rect_from_py(r),
                                                     JM_point_from_py(p)));
        }

        PyObject *_transform_point(PyObject *point, PyObject *matrix)
        {
            return JM_py_from_point(fz_transform_point(JM_point_from_py(point), JM_matrix_from_py(matrix)));
        }

        PyObject *_union_rect(PyObject *r1, PyObject *r2)
        {
            return JM_py_from_rect(fz_union_rect(JM_rect_from_py(r1),
                                                 JM_rect_from_py(r2)));
        }

        PyObject *_concat_matrix(PyObject *m1, PyObject *m2)
        {
            return JM_py_from_matrix(fz_concat(JM_matrix_from_py(m1),
                                               JM_matrix_from_py(m2)));
        }

        PyObject *_invert_matrix(PyObject *matrix)
        {
            fz_matrix src = JM_matrix_from_py(matrix);
            float a = src.a;
            float det = a * src.d - src.b * src.c;
            if (det < -FLT_EPSILON || det > FLT_EPSILON)
            {
                fz_matrix dst;
                float rdet = 1 / det;
                dst.a = src.d * rdet;
                dst.b = -src.b * rdet;
                dst.c = -src.c * rdet;
                dst.d = a * rdet;
                a = -src.e * dst.a - src.f * dst.c;
                dst.f = -src.e * dst.b - src.f * dst.d;
                dst.e = a;
                return Py_BuildValue("(i, O)", 0, JM_py_from_matrix(dst));
            }
            return Py_BuildValue("(i, ())", 1);
        }


        float _measure_string(const char *text, const char *fontname, float fontsize, int encoding = 0)
        {
            fz_font *font = fz_new_base14_font(gctx, fontname);
            float w = 0;
            while (*text)
            {
                int c, g;
                text += fz_chartorune(&c, text);
                switch (encoding)
                {
                    case PDF_SIMPLE_ENCODING_GREEK:
                        c = fz_iso8859_7_from_unicode(c); break;
                    case PDF_SIMPLE_ENCODING_CYRILLIC:
                        c = fz_windows_1251_from_unicode(c); break;
                    default:
                        c = fz_windows_1252_from_unicode(c); break;
                }
                if (c < 0) c = 0xB7;
                g = fz_encode_character(gctx, font, c);
                w += fz_advance_glyph(gctx, font, g, 0);
            }
            return w * fontsize;
        }

        PyObject *
        _sine_between(PyObject *C, PyObject *P, PyObject *Q)
        {
            // for points C, P, Q compute the sine between lines CP and QP
            fz_point c = JM_point_from_py(C);
            fz_point p = JM_point_from_py(P);
            fz_point q = JM_point_from_py(Q);
            fz_point s = fz_normalize_vector(fz_make_point(q.x - p.x, q.y - p.y));
            fz_matrix m1 = fz_make_matrix(1, 0, 0, 1, -p.x, -p.y);
            fz_matrix m2 = fz_make_matrix(s.x, -s.y, s.y, s.x, 0, 0);
            m1 = fz_concat(m1, m2);
            c = fz_transform_point(c, m1);
            c = fz_normalize_vector(c);
            return Py_BuildValue("f", c.y);
        }

        PyObject *
        _hor_matrix(PyObject *C, PyObject *P)
        {
            // calculate matrix m that maps line CP to the x-axis,
            // such that C * m = (0, 0), and target line has same length.
            fz_point c = JM_point_from_py(C);
            fz_point p = JM_point_from_py(P);
            fz_point s = fz_normalize_vector(fz_make_point(p.x - c.x, p.y - c.y));
            fz_matrix m1 = fz_make_matrix(1, 0, 0, 1, -c.x, -c.y);
            fz_matrix m2 = fz_make_matrix(s.x, -s.y, s.y, s.x, 0, 0);
            return JM_py_from_matrix(fz_concat(m1, m2));
        }


        FITZEXCEPTION(set_font_width, !result)
        PyObject *
        set_font_width(struct Document *doc, int xref, int width)
        {
            pdf_document *pdf = pdf_specifics(gctx, (fz_document *) doc);
            if (!pdf) Py_RETURN_FALSE;
            pdf_obj *font=NULL, *dfonts=NULL;
            fz_try(gctx) {
                font = pdf_load_object(gctx, pdf, xref);
                dfonts = pdf_dict_get(gctx, font, PDF_NAME(DescendantFonts));
                if (pdf_is_array(gctx, dfonts)) {
                    int i, n = pdf_array_len(gctx, dfonts);
                    for (i = 0; i < n; i++) {
                        pdf_obj *dfont = pdf_array_get(gctx, dfonts, i);
                        pdf_obj *warray = pdf_new_array(gctx, pdf, 3);
                        pdf_array_push(gctx, warray, pdf_new_int(gctx, 0));
                        pdf_array_push(gctx, warray, pdf_new_int(gctx, 65535));
                        pdf_array_push(gctx, warray, pdf_new_int(gctx, (int64_t) width));
                        pdf_dict_put_drop(gctx, dfont, PDF_NAME(W), warray);
                    }
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            Py_RETURN_TRUE;
        }


        %pythoncode %{
def _le_annot_parms(self, annot, p1, p2, fill_color):
    """Get common parameters for making annot line end symbols.

    Returns:
        m: matrix that maps p1, p2 to points L, P on the x-axis
        im: its inverse
        L, P: transformed p1, p2
        w: line width
        scol: stroke color string
        fcol: fill color store_shrink
        opacity: opacity string (gs command)
    """
    w = annot.border["width"]  # line width
    sc = annot.colors["stroke"]  # stroke color
    if not sc:  # black if missing
        sc = (0,0,0)
    scol = " ".join(map(str, sc)) + " RG\n"
    if fill_color:
        fc = fill_color
    else:
        fc = annot.colors["fill"]  # fill color
    if not fc:
        fc = (1,1,1)  # white if missing
    fcol = " ".join(map(str, fc)) + " rg\n"
    # nr = annot.rect
    np1 = p1                   # point coord relative to annot rect
    np2 = p2                   # point coord relative to annot rect
    m = Matrix(self._hor_matrix(np1, np2))  # matrix makes the line horizontal
    im = ~m                            # inverted matrix
    L = np1 * m                        # converted start (left) point
    R = np2 * m                        # converted end (right) point
    if 0 <= annot.opacity < 1:
        opacity = "/H gs\n"
    else:
        opacity = ""
    return m, im, L, R, w, scol, fcol, opacity

def _oval_string(self, p1, p2, p3, p4):
    """Return /AP string defining an oval within a 4-polygon provided as points
    """
    def bezier(p, q, r):
        f = "%f %f %f %f %f %f c\n"
        return f % (p.x, p.y, q.x, q.y, r.x, r.y)

    kappa = 0.55228474983              # magic number
    ml = p1 + (p4 - p1) * 0.5          # middle points ...
    mo = p1 + (p2 - p1) * 0.5          # for each ...
    mr = p2 + (p3 - p2) * 0.5          # polygon ...
    mu = p4 + (p3 - p4) * 0.5          # side
    ol1 = ml + (p1 - ml) * kappa       # the 8 bezier
    ol2 = mo + (p1 - mo) * kappa       # helper points
    or1 = mo + (p2 - mo) * kappa
    or2 = mr + (p2 - mr) * kappa
    ur1 = mr + (p3 - mr) * kappa
    ur2 = mu + (p3 - mu) * kappa
    ul1 = mu + (p4 - mu) * kappa
    ul2 = ml + (p4 - ml) * kappa
    # now draw, starting from middle point of left side
    ap = "%f %f m\n" % (ml.x, ml.y)
    ap += bezier(ol1, ol2, mo)
    ap += bezier(or1, or2, mr)
    ap += bezier(ur1, ur2, mu)
    ap += bezier(ul1, ul2, ml)
    return ap

def _le_diamond(self, annot, p1, p2, lr, fill_color):
    """Make stream commands for diamond line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2, fill_color)
    shift = 2.5             # 2*shift*width = length of square edge
    d = shift * max(1, w)
    M = R - (d/2., 0) if lr else L + (d/2., 0)
    r = Rect(M, M) + (-d, -d, d, d)         # the square
    # the square makes line longer by (2*shift - 1)*width
    p = (r.tl + (r.bl - r.tl) * 0.5) * im
    ap = "q\n%s%f %f m\n" % (opacity, p.x, p.y)
    p = (r.tl + (r.tr - r.tl) * 0.5) * im
    ap += "%f %f l\n"   % (p.x, p.y)
    p = (r.tr + (r.br - r.tr) * 0.5) * im
    ap += "%f %f l\n"   % (p.x, p.y)
    p = (r.br + (r.bl - r.br) * 0.5) * im
    ap += "%f %f l\n"   % (p.x, p.y)
    ap += "%g w\n" % w
    ap += scol + fcol + "b\nQ\n"
    return ap

def _le_square(self, annot, p1, p2, lr, fill_color):
    """Make stream commands for square line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2, fill_color)
    shift = 2.5             # 2*shift*width = length of square edge
    d = shift * max(1, w)
    M = R - (d/2., 0) if lr else L + (d/2., 0)
    r = Rect(M, M) + (-d, -d, d, d)         # the square
    # the square makes line longer by (2*shift - 1)*width
    p = r.tl * im
    ap = "q\n%s%f %f m\n" % (opacity, p.x, p.y)
    p = r.tr * im
    ap += "%f %f l\n"   % (p.x, p.y)
    p = r.br * im
    ap += "%f %f l\n"   % (p.x, p.y)
    p = r.bl * im
    ap += "%f %f l\n"   % (p.x, p.y)
    ap += "%g w\n" % w
    ap += scol + fcol + "b\nQ\n"
    return ap

def _le_circle(self, annot, p1, p2, lr, fill_color):
    """Make stream commands for circle line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2, fill_color)
    shift = 2.5             # 2*shift*width = length of square edge
    d = shift * max(1, w)
    M = R - (d/2., 0) if lr else L + (d/2., 0)
    r = Rect(M, M) + (-d, -d, d, d)         # the square
    ap = "q\n" + opacity + self._oval_string(r.tl * im, r.tr * im, r.br * im, r.bl * im)
    ap += "%g w\n" % w
    ap += scol + fcol + "b\nQ\n"
    return ap

def _le_butt(self, annot, p1, p2, lr, fill_color):
    """Make stream commands for butt line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2, fill_color)
    shift = 3
    d = shift * max(1, w)
    M = R if lr else L
    top = (M + (0, -d/2.)) * im
    bot = (M + (0, d/2.)) * im
    ap = "\nq\n%s%f %f m\n" % (opacity, top.x, top.y)
    ap += "%f %f l\n" % (bot.x, bot.y)
    ap += "%g w\n" % w
    ap += scol + "s\nQ\n"
    return ap

def _le_slash(self, annot, p1, p2, lr, fill_color):
    """Make stream commands for slash line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2, fill_color)
    rw = 1.1547 * max(1, w) * 1.0         # makes rect diagonal a 30 deg inclination
    M = R if lr else L
    r = Rect(M.x - rw, M.y - 2 * w, M.x + rw, M.y + 2 * w)
    top = r.tl * im
    bot = r.br * im
    ap = "\nq\n%s%f %f m\n" % (opacity, top.x, top.y)
    ap += "%f %f l\n" % (bot.x, bot.y)
    ap += "%g w\n" % w
    ap += scol + "s\nQ\n"
    return ap

def _le_openarrow(self, annot, p1, p2, lr, fill_color):
    """Make stream commands for open arrow line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2, fill_color)
    shift = 2.5
    d = shift * max(1, w)
    p2 = R + (d/2., 0) if lr else L - (d/2., 0)
    p1 = p2 + (-2*d, -d) if lr else p2 + (2*d, -d)
    p3 = p2 + (-2*d, d) if lr else p2 + (2*d, d)
    p1 *= im
    p2 *= im
    p3 *= im
    ap = "\nq\n%s%f %f m\n" % (opacity, p1.x, p1.y)
    ap += "%f %f l\n" % (p2.x, p2.y)
    ap += "%f %f l\n" % (p3.x, p3.y)
    ap += "%g w\n" % w
    ap += scol + "S\nQ\n"
    return ap

def _le_closedarrow(self, annot, p1, p2, lr, fill_color):
    """Make stream commands for closed arrow line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2, fill_color)
    shift = 2.5
    d = shift * max(1, w)
    p2 = R + (d/2., 0) if lr else L - (d/2., 0)
    p1 = p2 + (-2*d, -d) if lr else p2 + (2*d, -d)
    p3 = p2 + (-2*d, d) if lr else p2 + (2*d, d)
    p1 *= im
    p2 *= im
    p3 *= im
    ap = "\nq\n%s%f %f m\n" % (opacity, p1.x, p1.y)
    ap += "%f %f l\n" % (p2.x, p2.y)
    ap += "%f %f l\n" % (p3.x, p3.y)
    ap += "%g w\n" % w
    ap += scol + fcol + "b\nQ\n"
    return ap

def _le_ropenarrow(self, annot, p1, p2, lr, fill_color):
    """Make stream commands for right open arrow line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2, fill_color)
    shift = 2.5
    d = shift * max(1, w)
    p2 = R - (d/3., 0) if lr else L + (d/3., 0)
    p1 = p2 + (2*d, -d) if lr else p2 + (-2*d, -d)
    p3 = p2 + (2*d, d) if lr else p2 + (-2*d, d)
    p1 *= im
    p2 *= im
    p3 *= im
    ap = "\nq\n%s%f %f m\n" % (opacity, p1.x, p1.y)
    ap += "%f %f l\n" % (p2.x, p2.y)
    ap += "%f %f l\n" % (p3.x, p3.y)
    ap += "%g w\n" % w
    ap += scol + fcol + "S\nQ\n"
    return ap

def _le_rclosedarrow(self, annot, p1, p2, lr, fill_color):
    """Make stream commands for right closed arrow line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2, fill_color)
    shift = 2.5
    d = shift * max(1, w)
    p2 = R - (2*d, 0) if lr else L + (2*d, 0)
    p1 = p2 + (2*d, -d) if lr else p2 + (-2*d, -d)
    p3 = p2 + (2*d, d) if lr else p2 + (-2*d, d)
    p1 *= im
    p2 *= im
    p3 *= im
    ap = "\nq\n%s%f %f m\n" % (opacity, p1.x, p1.y)
    ap += "%f %f l\n" % (p2.x, p2.y)
    ap += "%f %f l\n" % (p3.x, p3.y)
    ap += "%g w\n" % w
    ap += scol + fcol + "b\nQ\n"
    return ap
        %}
    }
};
