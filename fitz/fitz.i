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
    if (cond)
    {
        PyErr_SetString(PyExc_RuntimeError, fz_caught_message(gctx));
        return NULL;
    }
}
%enddef

//-----------------------------------------------------------------------------
// SWIG macro: check that a document is not closed / encrypted
//-----------------------------------------------------------------------------
%define CLOSECHECK(meth)
%pythonprepend meth
%{if self.isClosed or self.isEncrypted:
    raise ValueError("document closed or encrypted")%}
%enddef

%define CLOSECHECK0(meth)
%pythonprepend meth
%{if self.isClosed:
    raise ValueError("document closed")%}
%enddef

//-----------------------------------------------------------------------------
// SWIG macro: check if object has a valid parent
//-----------------------------------------------------------------------------
%define PARENTCHECK(meth)
%pythonprepend meth %{CheckParent(self)%}
%enddef

//-----------------------------------------------------------------------------
// SWIG macro: Annotation wrappings
//-----------------------------------------------------------------------------
%define ANNOTWRAP1(meth, doc)
        FITZEXCEPTION(meth, !result)
        %pythonprepend meth %{
        CheckParent(self)
        if not self.parent.isPDF:
            raise ValueError("not a PDF")
        %}
        %feature("autodoc", doc) meth;
        %pythonappend meth %{
        if not val: return
        val.thisown = True
        val.parent = weakref.proxy(self)
        self._annot_refs[id(val)] = val%}
%enddef

%define MARKERWRAP(meth, doc)
        FITZEXCEPTION(meth, !result)
        %pythonprepend meth %{
        CheckParent(self)
        if not self.parent.isPDF:
            raise ValueError("not a PDF")
        if not hasattr(quads, "__getitem__"):
            raise ValueError("'quads' must be a sequence")
        if len(quads) == 4:
            if hasattr(quads[0], "__float__"):
                quads = [quads]
            elif hasattr(quads[0], "__getitem__") and len(quads[0]) == 2:
                quads = [quads]
        if type(quads) not in (list, tuple):
            raise ValueError("bad argument 'quads'")
        for a in quads:
            if not hasattr(a, "__getitem__") or len(a) != 4:
                raise ValueError("bad items in 'quads'")
        %}
        %feature("autodoc", doc) meth;
        %pythonappend meth %{
        if not val:
            return None
        val.thisown = True
        val.parent = weakref.proxy(self)
        self._annot_refs[id(val)] = val%}
%enddef

%feature("autodoc", "0");

%{
//#define MEMDEBUG
#ifdef MEMDEBUG
#define DEBUGMSG1(x) PySys_WriteStderr("[DEBUG] free %s ", x)
#define DEBUGMSG2 PySys_WriteStderr("... done!\n")
#else
#define DEBUGMSG1(x)
#define DEBUGMSG2
#endif

#ifndef FLT_EPSILON
  #define FLT_EPSILON 1e-5
#endif

#define return_none return Py_BuildValue("s", NULL)
#define SWIG_FILE_WITH_INIT
#define SWIG_PYTHON_2_UNICODE

// memory allocation macros
#define JM_MEMORY 1
#if  PY_VERSION_HEX < 0x03000000
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

#define EXISTS(x) (x && x != Py_None)
#define THROWMSG(msg) fz_throw(gctx, FZ_ERROR_GENERIC, msg)
#define assert_PDF(cond) if (cond == NULL) THROWMSG("not a PDF")
#define INRANGE(v, low, high) ((low) <= v && v <= (high))
#define MAX(a, b) ((a) < (b)) ? (b) : (a)
#define MIN(a, b) ((a) < (b)) ? (a) : (b)

#define JM_PyErr_Clear if (PyErr_Occurred()) PyErr_Clear()
#define JM_UNICODE(data) JM_EscapeStrFromStr(data)

// binary output depends on Python major
# if PY_VERSION_HEX >= 0x03000000
#define JM_BinFromChar(x) PyBytes_FromString(x)
#define JM_BinFromCharSize(x, y) PyBytes_FromStringAndSize(x, (Py_ssize_t) y)
# else
#define JM_BinFromChar(x) PyByteArray_FromStringAndSize(x, (Py_ssize_t) strlen(x))
#define JM_BinFromCharSize(x, y) PyByteArray_FromStringAndSize(x, (Py_ssize_t) y)
# endif

#include <fitz.h>
#include <pdf.h>
#include <time.h>
char *JM_Python_str_AsChar(PyObject *str);
pdf_obj *pdf_lookup_page_loc(fz_context *ctx, pdf_document *doc, int needle, pdf_obj **parentp, int *indexp);
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
# if PY_VERSION_HEX >= 0x03000000
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
int JM_UNIQUE_ID = 0;

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
from binascii import hexlify

fitz_py2 = str is bytes           # if true, this is Python 2
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

//-----------------------------------------------------------------------------
// fz_document
//-----------------------------------------------------------------------------
%rename(Document) fz_document_s;
struct fz_document_s
{
    %extend
    {
        ~fz_document_s()
        {
            DEBUGMSG1("document w/o close");
            fz_drop_document(gctx, $self);
            DEBUGMSG2;
        }
        FITZEXCEPTION(fz_document_s, !result)

        %pythonprepend fz_document_s %{
            if not filename or type(filename) is str:
                pass
            else:
                if fitz_py2:  # Python 2
                    if type(filename) is unicode:
                        filename = filename.encode("utf8")
                else:
                    filename = str(filename)  # should take care of pathlib

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
            self._page_refs  = weakref.WeakValueDictionary()%}

        %pythonappend fz_document_s %{
            if self.thisown:
                self._graft_id = TOOLS.gen_id()
                if self.needsPass is True:
                    self.isEncrypted = True
                else: # we won't init until doc is decrypted
                    self.initData()
        %}

        fz_document_s(const char *filename=NULL, PyObject *stream=NULL,
                      const char *filetype=NULL, PyObject *rect=NULL,
                      float width=0, float height=0,
                      float fontsize=11)
        {
            gctx->error.errcode = 0;       // reset any error code
            gctx->error.message[0] = 0;    // reset any error message
            struct fz_document_s *doc = NULL;
            char *c = NULL;
            size_t len = 0;
            fz_stream *data = NULL;
            float w = width, h = height;
            fz_rect r = JM_rect_from_py(rect);
            if (!fz_is_infinite_rect(r))
            {
                w = r.x1 - r.x0;
                h = r.y1 - r.y0;
            }

            fz_try(gctx)
            {
                if (stream != Py_None)  // stream given, **MUST** be bytes!
                {
                    c = PyBytes_AS_STRING(stream); // just a pointer, no new obj
                    len = (size_t) PyBytes_Size(stream);
                    data = fz_open_memory(gctx, c, len);
                    char *magic = (char *)filename;
                    if (!magic) magic = (char *)filetype;
                    doc = fz_open_document_with_stream(gctx, magic, data);
                }
                else
                {
                    if (filename)
                    {
                        if (!filetype || strlen(filetype) == 0)
                        {
                            doc = fz_open_document(gctx, filename);
                        }
                        else
                        {
                            const fz_document_handler *handler;
                            handler = fz_recognize_document(gctx, filetype);
                            if (handler && handler->open)
                                doc = handler->open(gctx, filename);
                            else THROWMSG("unrecognized file type");
                        }
                    }
                    else
                    {
                        pdf_document *pdf = pdf_create_document(gctx);
                        pdf->dirty = 1;
                        doc = (fz_document *) pdf;
                    }
                }
            }
            fz_catch(gctx) return NULL;
            if (w > 0 && h > 0)
                fz_layout_document(gctx, doc, w, h, fontsize);
            return doc;
        }

        %pythonprepend close %{
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
            for gmap in self.Graftmaps:
                self.Graftmaps[gmap] = None
            self.Graftmaps = {}
            self.ShownPages = {}
        %}

        %pythonappend close %{self.thisown = False%}
        void close()
        {
            DEBUGMSG1("doc.close()");
            while($self->refs > 1) {
                fz_drop_document(gctx, $self);
            }
            fz_drop_document(gctx, $self);
            DEBUGMSG2;
        }

        FITZEXCEPTION(loadPage, result==NULL)
        CLOSECHECK(loadPage)
        %pythonappend loadPage %{
            if val:
                val.thisown = True
                val.parent = weakref.proxy(self)
                pageCount = self.pageCount
                n = number
                while n < 0: n += pageCount
                val.number = n
                self._page_refs[id(val)] = val
                val._annot_refs = weakref.WeakValueDictionary()
        %}
        struct fz_page_s *loadPage(int number=0)
        {
            struct fz_page_s *page = NULL;
            fz_try(gctx)
            {
                int pageCount = fz_count_pages(gctx, $self);
                if (pageCount < 1) THROWMSG("document has no pages");
                int n = number;
                while (n < 0) n += pageCount;
                page = fz_load_page(gctx, $self, n);
            }
            fz_catch(gctx) return NULL;
            return page;
        }


        FITZEXCEPTION(_remove_links_to, !result)
        PyObject *_remove_links_to(int first, int last)
        {
            fz_try(gctx)
            {
                pdf_document *pdf = pdf_specifics(gctx, $self);
                pdf_drop_page_tree(gctx, pdf);
                pdf_load_page_tree(gctx, pdf);
                remove_dest_range(gctx, pdf, first, last);
            }
            fz_catch(gctx) return NULL;
            return_none;
        }


        CLOSECHECK0(_loadOutline)
        struct fz_outline_s *_loadOutline()
        {
            fz_outline *ol = NULL;
            fz_try(gctx) ol = fz_load_outline(gctx, $self);
            fz_catch(gctx) return NULL;
            return ol;
        }

        void _dropOutline(struct fz_outline_s *ol) {
            DEBUGMSG1("outline");
            fz_drop_outline(gctx, ol);
            DEBUGMSG2;
        }

        //---------------------------------------------------------------------
        // EmbeddedFiles utility functions
        //---------------------------------------------------------------------
        FITZEXCEPTION(_embeddedFileNames, !result)
        CLOSECHECK0(_embeddedFileNames)
        PyObject *_embeddedFileNames(PyObject *namelist)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); // get pdf document
            fz_try(gctx)
            {
                assert_PDF(pdf);
                PyObject *val;
                pdf_obj *names = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf),
                                      PDF_NAME(Root),
                                      PDF_NAME(Names),
                                      PDF_NAME(EmbeddedFiles),
                                      PDF_NAME(Names),
                                      NULL);
                if (pdf_is_array(gctx, names))
                {
                    int i, n = pdf_array_len(gctx, names);
                    for (i=0; i < n; i+=2)
                    {
                        val = JM_UNICODE(pdf_to_text_string(gctx,
                                         pdf_array_get(gctx, names, i)));
                        LIST_APPEND_DROP(namelist, val);
                    }
                }
            }
            fz_catch(gctx) return NULL;
            return_none;
        }

        FITZEXCEPTION(_embeddedFileDel, !result)
        PyObject *_embeddedFileDel(int idx)
        {
            fz_try(gctx)
            {
                pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
                pdf_obj *names = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf),
                                      PDF_NAME(Root),
                                      PDF_NAME(Names),
                                      PDF_NAME(EmbeddedFiles),
                                      PDF_NAME(Names),
                                      NULL);
                pdf_array_delete(gctx, names, idx + 1);
                pdf_array_delete(gctx, names, idx);
            }
            fz_catch(gctx) return NULL;
            return_none;
        }

        FITZEXCEPTION(_embeddedFileInfo, !result)
        PyObject *_embeddedFileInfo(int idx, PyObject *infodict)
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            char *name;
            fz_try(gctx)
            {
                pdf_obj *names = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf),
                                      PDF_NAME(Root),
                                      PDF_NAME(Names),
                                      PDF_NAME(EmbeddedFiles),
                                      PDF_NAME(Names),
                                      NULL);

                pdf_obj *o = pdf_array_get(gctx, names, 2*idx+1);

                name = (char *) pdf_to_text_string(gctx,
                                          pdf_dict_get(gctx, o, PDF_NAME(F)));
                DICT_SETITEM_DROP(infodict, dictkey_filename, JM_UNICODE(name));

                name = (char *) pdf_to_text_string(gctx,
                                    pdf_dict_get(gctx, o, PDF_NAME(UF)));
                DICT_SETITEM_DROP(infodict, dictkey_ufilename, JM_UNICODE(name));

                name = (char *) pdf_to_text_string(gctx,
                                    pdf_dict_get(gctx, o, PDF_NAME(Desc)));
                DICT_SETITEM_DROP(infodict, dictkey_desc, JM_UNICODE(name));

                int len = -1, DL = -1;
                pdf_obj *ef = pdf_dict_get(gctx, o, PDF_NAME(EF));
                o = pdf_dict_getl(gctx, ef, PDF_NAME(F),
                                            PDF_NAME(Length), NULL);
                if (o) len = pdf_to_int(gctx, o);

                o = pdf_dict_getl(gctx, ef, PDF_NAME(F), PDF_NAME(DL), NULL);
                if (o) DL = pdf_to_int(gctx, o);
                else
                {
                    o = pdf_dict_getl(gctx, ef, PDF_NAME(F), PDF_NAME(Params),
                                   PDF_NAME(Size), NULL);
                    if (o) DL = pdf_to_int(gctx, o);
                }
                DICT_SETITEM_DROP(infodict, dictkey_size, Py_BuildValue("i", DL));
                DICT_SETITEM_DROP(infodict, dictkey_length, Py_BuildValue("i", len));
            }
            fz_catch(gctx) return NULL;
            return_none;
        }

        FITZEXCEPTION(_embeddedFileUpd, !result)
        PyObject *_embeddedFileUpd(int idx, PyObject *buffer = NULL, char *filename = NULL, char *ufilename = NULL, char *desc = NULL)
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            fz_buffer *res = NULL;
            fz_var(res);
            fz_try(gctx)
            {
                pdf_obj *names = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf),
                                      PDF_NAME(Root),
                                      PDF_NAME(Names),
                                      PDF_NAME(EmbeddedFiles),
                                      PDF_NAME(Names),
                                      NULL);

                pdf_obj *entry = pdf_array_get(gctx, names, 2*idx+1);

                pdf_obj *filespec = pdf_dict_getl(gctx, entry, PDF_NAME(EF),
                                                  PDF_NAME(F), NULL);
                if (!filespec) THROWMSG("bad PDF: /EF object not found");

                res = JM_BufferFromBytes(gctx, buffer);
                if (EXISTS(buffer) && !res) THROWMSG("bad type: 'buffer'");
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
            fz_always(gctx)
                fz_drop_buffer(gctx, res);
            fz_catch(gctx)
                return NULL;
            pdf->dirty = 1;
            return_none;
        }

        FITZEXCEPTION(_embeddedFileGet, !result)
        PyObject *_embeddedFileGet(int idx)
        {
            PyObject *cont = NULL;
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            fz_buffer *buf = NULL;
            fz_var(buf);
            fz_try(gctx)
            {
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
            fz_always(gctx) fz_drop_buffer(gctx, buf);
            fz_catch(gctx) return NULL;
            return cont;
        }

        FITZEXCEPTION(_embeddedFileAdd, !result)
        PyObject *_embeddedFileAdd(const char *name, PyObject *buffer, char *filename=NULL, char *ufilename=NULL, char *desc=NULL)
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            fz_buffer *data = NULL;
            char *buffdata;
            fz_var(data);
            int entry = 0;
            size_t size = 0;
            pdf_obj *names = NULL;
            fz_try(gctx)
            {
                assert_PDF(pdf);
                data = JM_BufferFromBytes(gctx, buffer);
                if (!data) THROWMSG("bad type: 'buffer'");
                size = fz_buffer_storage(gctx, data, &buffdata);

                names = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf),
                                      PDF_NAME(Root),
                                      PDF_NAME(Names),
                                      PDF_NAME(EmbeddedFiles),
                                      PDF_NAME(Names),
                                      NULL);
                if (!pdf_is_array(gctx, names))  // no embedded files yet
                {
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
            fz_always(gctx)
            {
                fz_drop_buffer(gctx, data);
            }
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return_none;
        }

        %pythoncode %{
        def embeddedFileNames(self):
            """ Return a list of names of EmbeddedFiles.
            """
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
            """ Return the number of EmbeddedFiles.
            """
            return len(self.embeddedFileNames())

        def embeddedFileDel(self, item):
            """ Delete an entry from EmbeddedFiles.

            Notes:
                The argument must be name or index of an EmbeddedFiles item.
                Physical deletion of associated data will happen on save to a
                new file with appropriate garbage option.
            Args:
                item: (str/int) the name or index of the entry.
            Returns:
                None
            """
            idx = self._embeddedFileIndex(item)
            return self._embeddedFileDel(idx)

        def embeddedFileInfo(self, item):
            """ Return information of an item in the EmbeddedFiles array.

            Args:
                item: the number or the name of the item.
            Returns:
                A dictionary of respective information.
            """
            idx = self._embeddedFileIndex(item)
            infodict = {"name": self.embeddedFileNames()[idx]}
            self._embeddedFileInfo(idx, infodict)
            return infodict

        def embeddedFileGet(self, item):
            """ Return the content of an item in the EmbeddedFiles array.

            Args:
                item: the number or the name of the item.
            Returns:
                (bytes) The file content.
            """
            idx = self._embeddedFileIndex(item)
            return self._embeddedFileGet(idx)

        def embeddedFileUpd(self, item, buffer=None,
                                  filename=None,
                                  ufilename=None,
                                  desc=None):
            """ Make changes to an item in the EmbeddedFiles array.

            Notes:
                All parameter are optional. If all arguments are omitted, the
                method results in a no-op.
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
            """ Add an item to the EmbeddedFiles array.

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
        CLOSECHECK(convertToPDF)
        %feature("autodoc","Convert document to PDF selecting page range and optional rotation. Output bytes object.") convertToPDF;
        PyObject *convertToPDF(int from_page=0, int to_page=-1, int rotate=0)
        {
            PyObject *doc = NULL;
            fz_try(gctx)
            {
                int fp = from_page, tp = to_page, srcCount = fz_count_pages(gctx, $self);
                if (pdf_specifics(gctx, $self))
                    THROWMSG("use select+write or insertPDF for PDF docs instead");
                if (fp < 0) fp = 0;
                if (fp > srcCount - 1) fp = srcCount - 1;
                if (tp < 0) tp = srcCount - 1;
                if (tp > srcCount - 1) tp = srcCount - 1;
                doc = JM_convert_to_pdf(gctx, $self, fp, tp, rotate);
            }
            fz_catch(gctx) return NULL;
            return doc;
        }

        CLOSECHECK0(pageCount)
        %pythoncode%{@property%}
        PyObject *pageCount()
        {
            return Py_BuildValue("i", fz_count_pages(gctx, $self));
        }

        CLOSECHECK0(_getMetadata)
        char *_getMetadata(const char *key)
        {
            int vsize;
            char *value;
            vsize = fz_lookup_metadata(gctx, $self, key, NULL, 0)+1;
            if(vsize > 1)
            {
                value = JM_Alloc(char, vsize);
                fz_lookup_metadata(gctx, $self, key, value, vsize);
                return value;
            }
            else
                return NULL;
        }

        CLOSECHECK0(needsPass)
        %pythoncode%{@property%}
        PyObject *needsPass() {
            return JM_BOOL(fz_needs_password(gctx, $self));
        }

        %feature("autodoc", "Calculate internal link destination.") resolveLink;
        PyObject *resolveLink(char *uri = NULL)
        {
            if (!uri) return_none;
            float xp = 0.0f, yp = 0.0f;
            int pno = -1;
            fz_try(gctx)
                pno = fz_resolve_link(gctx, $self, uri, &xp, &yp);
            fz_catch(gctx)
                return_none;
            if (pno < 0) return_none;
            return Py_BuildValue("iff", pno, xp, yp);
        }

        FITZEXCEPTION(layout, !result)
        %feature("autodoc", "Re-layout a reflowable document.") layout;
        CLOSECHECK(layout)
        %pythonappend layout %{
            self._reset_page_refs()
            self.initData()%}
        PyObject *layout(PyObject *rect = NULL, float width = 0, float height = 0, float fontsize = 11)
        {
            if (!fz_is_document_reflowable(gctx, $self)) return_none;
            fz_try(gctx)
            {
                float w = width, h = height;
                fz_rect r = JM_rect_from_py(rect);
                if (!fz_is_infinite_rect(r))
                {
                    w = r.x1 - r.x0;
                    h = r.y1 - r.y0;
                }
                if (w <= 0.0f || h <= 0.0f)
                        THROWMSG("invalid page size");
                fz_layout_document(gctx, $self, w, h, fontsize);
            }
            fz_catch(gctx) return NULL;
            return_none;
        }

        CLOSECHECK(makeBookmark)
        %feature("autodoc", "Make page bookmark in a reflowable document.") makeBookmark;
        PyObject *makeBookmark(int pno = 0)
        {
            if (!fz_is_document_reflowable(gctx, $self)) return_none;
            int n = pno, cp = fz_count_pages(gctx, $self);
            while(n < 0) n += cp;
            long long mark = (long long) fz_make_bookmark(gctx, $self, n);
            return PyLong_FromLongLong(mark);
        }

        CLOSECHECK(findBookmark)
        %feature("autodoc", "Find page number after layouting a document.") findBookmark;
        PyObject *findBookmark(long long bookmark)
        {
            int i = -1;
            if (fz_is_document_reflowable(gctx, $self))
            {
                fz_bookmark m = (fz_bookmark) bookmark;
                i = fz_lookup_bookmark(gctx, $self, m);
            }
            return Py_BuildValue("i", i);
        }

        CLOSECHECK0(isReflowable)
        %pythoncode%{@property%}
        PyObject *isReflowable()
        {
            return JM_BOOL(fz_is_document_reflowable(gctx, $self));
        }

        FITZEXCEPTION(_deleteObject, !result)
        CLOSECHECK0(_deleteObject)
        %feature("autodoc", "Delete an object given its xref.") _deleteObject;
        PyObject *_deleteObject(int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                if (!INRANGE(xref, 1, pdf_xref_len(gctx, pdf)-1))
                    THROWMSG("xref out of range");
                pdf_delete_object(gctx, pdf, xref);
            }
            fz_catch(gctx) return NULL;
            return_none;
        }

        CLOSECHECK0(_getPDFroot)
        %feature("autodoc", "Get XREF number of PDF catalog.") _getPDFroot;
        PyObject *_getPDFroot()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            int xref = 0;
            if (!pdf) return Py_BuildValue("i", xref);
            fz_try(gctx)
            {
                pdf_obj *root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf),
                                             PDF_NAME(Root));
                xref = pdf_to_num(gctx, root);
            }
            fz_catch(gctx) {;}
            return Py_BuildValue("i", xref);
        }

        CLOSECHECK0(_getPDFfileid)
        %feature("autodoc", "Return PDF file /ID strings (hexadecimal).") _getPDFfileid;
        PyObject *_getPDFfileid()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) return_none;
            PyObject *idlist = PyList_New(0);
            fz_buffer *buffer = NULL;
            char *hex;
            pdf_obj *o;
            int n, i, len;
            PyObject *bytes;
            fz_try(gctx)
            {
                pdf_obj *identity = pdf_dict_get(gctx, pdf_trailer(gctx, pdf),
                                             PDF_NAME(ID));
                if (identity)
                {
                    n = pdf_array_len(gctx, identity);
                    for (i = 0; i < n; i++)
                    {
                        o = pdf_array_get(gctx, identity, i);
                        len = pdf_to_str_len(gctx, o);
                        buffer = fz_new_buffer(gctx, 2 * len);
                        fz_buffer_storage(gctx, buffer, &hex);
                        hexlify(len, (unsigned char *) pdf_to_text_string(gctx, o), (unsigned char *) hex);
                        LIST_APPEND_DROP(idlist, PyUnicode_FromString(hex));
                        Py_CLEAR(bytes);
                        fz_drop_buffer(gctx, buffer);
                        buffer = NULL;
                    }
                }
            }
            fz_catch(gctx) fz_drop_buffer(gctx, buffer);
            return idlist;
        }

        CLOSECHECK0(isPDF)
        %pythoncode%{@property%}
        PyObject *isPDF()
        {
            if (pdf_specifics(gctx, $self)) Py_RETURN_TRUE;
            else Py_RETURN_FALSE;
        }

        CLOSECHECK0(_hasXrefStream)
        %pythoncode%{@property%}
        PyObject *_hasXrefStream()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) Py_RETURN_FALSE;
            if (pdf->has_xref_streams) Py_RETURN_TRUE;
            Py_RETURN_FALSE;
        }

        CLOSECHECK0(_hasXrefOldStyle)
        %pythoncode%{@property%}
        PyObject *_hasXrefOldStyle()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) Py_RETURN_FALSE;
            if (pdf->has_old_style_xrefs) Py_RETURN_TRUE;
            Py_RETURN_FALSE;
        }

        CLOSECHECK0(isDirty)
        %pythoncode%{@property%}
        PyObject *isDirty()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) Py_RETURN_FALSE;
            return JM_BOOL(pdf_has_unsaved_changes(gctx, pdf));
        }

        CLOSECHECK0(can_save_incrementally)
        %feature("autodoc", "Check if can be saved incrementally.") can_save_incrementally;
        PyObject *can_save_incrementally()
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            if (!pdf) Py_RETURN_FALSE; // gracefully handle non-PDF
            return JM_BOOL(pdf_can_be_saved_incrementally(gctx, pdf));
        }

        CLOSECHECK0(authenticate)
        %feature("autodoc", "Decrypt document with a password.") authenticate;
        %pythonappend authenticate %{
            if val: # the doc is decrypted successfully and we init the outline
                self.isEncrypted = False
                self.initData()
                self.thisown = True
        %}
        PyObject *authenticate(char *password)
        {
            return Py_BuildValue("i", fz_authenticate_password(gctx, $self, (const char *) password));
        }

        //---------------------------------------------------------------------
        // save PDF file
        //---------------------------------------------------------------------
        FITZEXCEPTION(save, !result)
        %pythonprepend save %{
            if self.isClosed or self.isEncrypted:
                raise ValueError("document closed or encrypted")
            if type(filename) == str:
                pass
            elif type(filename) == unicode:
                filename = filename.encode('utf8')
            else:
                raise TypeError("filename must be a string")
            if filename == self.name and not incremental:
                raise ValueError("save to original must be incremental")
            if self.pageCount < 1:
                raise ValueError("cannot save with zero pages")
            if incremental:
                if self.name != filename or self.stream:
                    raise ValueError("incremental needs original file")
        %}

        PyObject *save(char *filename, int garbage=0, int clean=0, int deflate=0, int incremental=0, int ascii=0, int expand=0, int linear=0, int pretty=0, int encryption=1, int permissions=-1, char *owner_pw=NULL, char *user_pw=NULL)
        {
            pdf_write_options opts = pdf_default_write_options;
            opts.do_incremental     = incremental;
            opts.do_ascii           = ascii;
            opts.do_compress        = deflate;
            opts.do_compress_images = deflate;
            opts.do_compress_fonts  = deflate;
            opts.do_decompress      = expand;
            opts.do_garbage         = garbage;
            opts.do_pretty          = pretty;
            opts.do_linear          = linear;
            opts.do_clean           = clean;
            opts.do_sanitize        = clean;
            opts.do_encrypt         = encryption;
            opts.permissions        = permissions;
            if (owner_pw)
            {
                memcpy(&opts.opwd_utf8, owner_pw, strlen(owner_pw)+1);
            }

            if (user_pw)
            {
                memcpy(&opts.upwd_utf8, user_pw, strlen(user_pw)+1);
            }

            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                JM_embedded_clean(gctx, pdf);
                pdf_save_document(gctx, pdf, filename, &opts);
                pdf->dirty = 0;
            }
            fz_catch(gctx) return NULL;
            return_none;
        }

        //---------------------------------------------------------------------
        // write document to memory
        //---------------------------------------------------------------------
        FITZEXCEPTION(write, !result)
        %feature("autodoc", "Write document to a bytes object.") write;
        %pythonprepend write %{
            if self.isClosed or self.isEncrypted:
                raise ValueError("document closed or encrypted")
            if self.pageCount < 1:
                raise ValueError("cannot write with zero pages")
        %}

        PyObject *write(int garbage=0, int clean=0, int deflate=0,
                        int ascii=0, int expand=0, int linear=0, int pretty=0,
                        int encryption=1,
                        int permissions=-1,
                        char *owner_pw=NULL,
                        char *user_pw=NULL)
        {
            PyObject *r = NULL;
            fz_output *out = NULL;
            fz_buffer *res = NULL;
            pdf_write_options opts = pdf_default_write_options;
            opts.do_incremental     = 0;
            opts.do_ascii           = ascii;
            opts.do_compress        = deflate;
            opts.do_compress_images = deflate;
            opts.do_compress_fonts  = deflate;
            opts.do_decompress      = expand;
            opts.do_garbage         = garbage;
            opts.do_linear          = linear;
            opts.do_clean           = clean;
            opts.do_sanitize        = clean;
            opts.do_pretty          = pretty;
            opts.do_encrypt         = encryption;
            opts.permissions        = permissions;
            if (owner_pw)
            {
                memcpy(&opts.opwd_utf8, owner_pw, strlen(owner_pw)+1);
            }

            if (user_pw)
            {
                memcpy(&opts.upwd_utf8, user_pw, strlen(user_pw)+1);
            }

            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_var(out);
            fz_var(r);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                if (fz_count_pages(gctx, $self) < 1)
                    THROWMSG("cannot save with zero pages");
                JM_embedded_clean(gctx, pdf);
                res = fz_new_buffer(gctx, 8192);
                out = fz_new_output_with_buffer(gctx, res);
                pdf_write_document(gctx, pdf, out, &opts);
                r = JM_BinFromBuffer(gctx, res);
                pdf->dirty = 0;
            }
            fz_always(gctx)
                {
                    fz_drop_buffer(gctx, res);
                    fz_drop_output(gctx, out);
                }
            fz_catch(gctx)
            {
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
        %pythonprepend insertPDF
%{if self.isClosed or self.isEncrypted:
    raise ValueError("document closed or encrypted")
if id(self) == id(docsrc):
    raise ValueError("source must not equal target PDF")
sa = start_at
if sa < 0:
    sa = self.pageCount%}

        %pythonappend insertPDF
%{self._reset_page_refs()
if links:
    self._do_links(docsrc, from_page = from_page, to_page = to_page,
                   start_at = sa)%}

        %feature("autodoc","Copy page range ['from', 'to'] of source PDF, starting as page number 'start_at'.") insertPDF;

        PyObject *insertPDF(struct fz_document_s *docsrc, int from_page=-1, int to_page=-1, int start_at=-1, int rotate=-1, int links=1, int annots=1)
        {
            pdf_document *pdfout = pdf_specifics(gctx, $self);
            pdf_document *pdfsrc = pdf_specifics(gctx, docsrc);
            int outCount = fz_count_pages(gctx, $self);
            int srcCount = fz_count_pages(gctx, docsrc);

            // local copies of page numbers
            int fp = from_page, tp = to_page, sa = start_at;

            // normalize page numbers
            fp = MAX(fp, 0);                // -1 = first page
            fp = MIN(fp, srcCount - 1);     // but do not exceed last page

            if (tp < 0) tp = srcCount - 1;  // -1 = last page
            tp = MIN(tp, srcCount - 1);     // but do not exceed last page

            if (sa < 0) sa = outCount;      // -1 = behind last page
            sa = MIN(sa, outCount);         // but that is also the limit

            fz_try(gctx)
            {
                if (!pdfout || !pdfsrc) THROWMSG("source or target not a PDF");
                merge_range(gctx, pdfout, pdfsrc, fp, tp, sa, rotate, links, annots);
            }
            fz_catch(gctx) return NULL;
            pdfout->dirty = 1;
            return_none;
        }

        //---------------------------------------------------------------------
        // Create and insert a new page (PDF)
        //---------------------------------------------------------------------
        FITZEXCEPTION(_newPage, !result)
        CLOSECHECK(_newPage)
        %pythonappend _newPage %{self._reset_page_refs()%}
        PyObject *_newPage(int pno=-1, float width=595, float height=842)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_rect mediabox = fz_unit_rect;
            mediabox.x1 = width;
            mediabox.y1 = height;
            pdf_obj *resources = NULL, *page_obj = NULL;
            fz_buffer *contents = NULL;
            fz_try(gctx)
            {
                assert_PDF(pdf);
                if (pno < -1) THROWMSG("bad page number(s)");
                // create /Resources and /Contents objects
                resources = pdf_add_object_drop(gctx, pdf, pdf_new_dict(gctx, pdf, 1));
                page_obj = pdf_add_page(gctx, pdf, mediabox, 0, resources, contents);
                pdf_insert_page(gctx, pdf, pno, page_obj);
            }
            fz_always(gctx)
            {
                fz_drop_buffer(gctx, contents);
                pdf_drop_obj(gctx, page_obj);
            }
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return_none;
        }

        //---------------------------------------------------------------------
        // Create sub-document to keep only selected pages.
        // Parameter is a Python sequence of the wanted page numbers.
        //---------------------------------------------------------------------
        FITZEXCEPTION(select, !result)
        %feature("autodoc","Build sub-pdf with page numbers in 'list'.") select;
        %pythonprepend select %{
if self.isClosed or self.isEncrypted:
    raise ValueError("document closed or encrypted")
if not self.isPDF:
    raise ValueError("not a PDF")
if not hasattr(pyliste, "__getitem__"):
    raise ValueError("sequence required")
if len(pyliste) == 0 or min(pyliste) not in range(len(self)) or max(pyliste) not in range(len(self)):
    raise ValueError("sequence items out of range")
%}
        %pythonappend select %{
            self._reset_page_refs()%}
        PyObject *select(PyObject *pyliste)
        {
            // preparatory stuff:
            // (1) get underlying pdf document,
            // (2) transform Python list into integer array

            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
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
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return_none;
        }

        //---------------------------------------------------------------------
        // remove one page
        //---------------------------------------------------------------------
        FITZEXCEPTION(_deletePage, !result)
        PyObject *_deletePage(int pno)
        {
            fz_try(gctx)
            {
                pdf_document *pdf = pdf_specifics(gctx, $self);
                int count = fz_count_pages(gctx, $self);
                pdf_delete_page(gctx, pdf, pno);
                if (pdf->rev_page_map)
                {
                    pdf_drop_page_tree(gctx, pdf);
                }
            }
            fz_catch(gctx) return NULL;
            return_none;
        }

        //********************************************************************
        // get document permissions
        //********************************************************************
        %feature("autodoc","Get document permissions.") permissions;
        CLOSECHECK0(permissions)
        %pythoncode%{@property%}
        %pythonprepend permissions %{
            if self.isEncrypted:
                return 0
        %}
        PyObject *permissions()
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);

            // for PDF return result of standard function
            if (pdf)
                return Py_BuildValue("i", pdf_document_permissions(gctx, pdf));

            // otherwise simulate the PDF return value
            int perm = (int) 0xFFFFFFFC;  // all permissions granted
            // now switch off where needed
            if (!fz_has_permission(gctx, $self, FZ_PERMISSION_PRINT))
                perm = perm ^ PDF_PERM_PRINT;
            if (!fz_has_permission(gctx, $self, FZ_PERMISSION_EDIT))
                perm = perm ^ PDF_PERM_MODIFY;
            if (!fz_has_permission(gctx, $self, FZ_PERMISSION_COPY))
                perm = perm ^ PDF_PERM_COPY;
            if (!fz_has_permission(gctx, $self, FZ_PERMISSION_ANNOTATE))
                perm = perm ^ PDF_PERM_ANNOTATE;
            return Py_BuildValue("i", perm);
        }

        FITZEXCEPTION(_getCharWidths, !result)
        CLOSECHECK(_getCharWidths)
        %feature("autodoc","Return list of glyphs and glyph widths of a font.") _getCharWidths;
        PyObject *_getCharWidths(int xref, char *bfname, char *ext,
                                 int ordering, int limit, int idx = 0)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            PyObject *wlist = NULL;
            int i, glyph, mylimit;
            mylimit = limit;
            if (mylimit < 256) mylimit = 256;
            int cwlen = 0;
            int lang = 0;
            const char *data;
            int size, index;
            fz_font *font = NULL, *fb_font= NULL;
            fz_buffer *buf = NULL;

            fz_try(gctx)
            {
                assert_PDF(pdf);
                if (ordering >= 0)
                {
                    data = fz_lookup_cjk_font(gctx, ordering, &size, &index);
                    font = fz_new_font_from_memory(gctx, NULL, data, size, index, 0);
                    goto weiter;
                }
                data = fz_lookup_base14_font(gctx, bfname, &size);
                if (data)
                {
                    font = fz_new_font_from_memory(gctx, bfname, data, size, 0, 0);
                    goto weiter;
                }
                buf = fontbuffer(gctx, pdf, xref);
                if (!buf) THROWMSG("xref is not a supported font");
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
            fz_always(gctx)
            {
                fz_drop_buffer(gctx, buf);
                fz_drop_font(gctx, font);
            }
            fz_catch(gctx)
            {
                return NULL;
            }
            return wlist;
        }

        FITZEXCEPTION(_getPageObjNumber, !result)
        CLOSECHECK0(_getPageObjNumber)
        PyObject *_getPageObjNumber(int pno)
        {
            int pageCount = fz_count_pages(gctx, $self);
            pdf_document *pdf = pdf_specifics(gctx, $self);
            int n = pno;
            while (n < 0) n += pageCount;
            pdf_obj *pageref = NULL;
            fz_var(pageref);
            fz_try(gctx)
            {
                if (n >= pageCount) THROWMSG("bad page number(s)");
                assert_PDF(pdf);
                pageref = pdf_lookup_page_obj(gctx, pdf, n);
            }
            fz_catch(gctx) return NULL;

            return Py_BuildValue("ii", pdf_to_num(gctx, pageref),
                                       pdf_to_gen(gctx, pageref));
        }

        FITZEXCEPTION(_getPageInfo, !result)
        CLOSECHECK(_getPageInfo)
        %feature("autodoc","Show fonts or images used on a page.") _getPageInfo;
        %pythonappend _getPageInfo %{
        #x = []
        #for v in val:
        #    if v not in x:
        #        x.append(v)
        #val = x%}
        PyObject *_getPageInfo(int pno, int what)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            int pageCount = fz_count_pages(gctx, $self);
            pdf_obj *pageref, *rsrc;
            PyObject *liste = NULL;         // returned object
            int n = pno;                    // pno < 0 is allowed
            while (n < 0) n += pageCount;
            fz_var(liste);
            fz_try(gctx)
            {
                if (n >= pageCount) THROWMSG("bad page number(s)");
                assert_PDF(pdf);
                pageref = pdf_lookup_page_obj(gctx, pdf, n);
                rsrc = pdf_dict_get_inheritable(gctx, pageref, PDF_NAME(Resources));
                if (!pageref || !rsrc) THROWMSG("cannot retrieve page info");
                liste = PyList_New(0);
                JM_scan_resources(gctx, pdf, rsrc, liste, what, 0);
            }
            fz_catch(gctx)
            {
                Py_XDECREF(liste);
                return NULL;
            }
            return liste;
        }

        FITZEXCEPTION(extractFont, !result)
        CLOSECHECK(extractFont)
        PyObject *extractFont(int xref = 0, int info_only = 0)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);

            fz_try(gctx) assert_PDF(pdf);
            fz_catch(gctx) return NULL;

            fz_buffer *buffer = NULL;
            pdf_obj *obj, *basefont, *bname;
            PyObject *bytes = PyBytes_FromString("");
            char *ext = NULL;
            char *fontname = NULL;
            PyObject *nulltuple = Py_BuildValue("sssO", "", "", "", bytes);
            PyObject *tuple;
            Py_ssize_t len = 0;
            fz_try(gctx)
            {
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
                    ext = fontextension(gctx, pdf, xref);
                    if (strcmp(ext, "n/a") != 0 && !info_only)
                    {
                        buffer = fontbuffer(gctx, pdf, xref);
                        bytes = JM_BinFromBuffer(gctx, buffer);
                        fz_drop_buffer(gctx, buffer);
                    }
                    tuple = PyTuple_New(4);
                    PyTuple_SET_ITEM(tuple, 0, JM_UNICODE(pdf_to_name(gctx, bname)));
                    PyTuple_SET_ITEM(tuple, 1, PyUnicode_FromString(ext));
                    PyTuple_SET_ITEM(tuple, 2, JM_UNICODE(pdf_to_name(gctx, subtype)));
                    PyTuple_SET_ITEM(tuple, 3, bytes);
                }
                else
                {
                    tuple = nulltuple;
                }
            }
            fz_always(gctx)
            {
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
        CLOSECHECK(extractImage)
        %feature("autodoc","Extract image which 'xref' is pointing to.") extractImage;
        PyObject *extractImage(int xref = 0)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                if (!INRANGE(xref, 1, pdf_xref_len(gctx, pdf)-1))
                    THROWMSG("xref out of range");
            }
            fz_catch(gctx) return NULL;

            fz_buffer *buffer = NULL, *freebuf = NULL;
            fz_var(freebuf);
            pdf_obj *obj = NULL;
            PyObject *rc = NULL;
            const char *ext = NULL;
            fz_image *image = NULL;
            fz_var(image);
            fz_compressed_buffer *cbuf = NULL;
            int type = FZ_IMAGE_UNKNOWN, n = 0, xres = 0, yres = 0, is_jpx = 0;
            int smask = 0, width = 0, height = 0, bpc = 0;
            const char *cs_name = NULL;
            fz_try(gctx)
            {
                obj = pdf_new_indirect(gctx, pdf, xref, 0);
                pdf_obj *subtype = pdf_dict_get(gctx, obj, PDF_NAME(Subtype));
                if (pdf_name_eq(gctx, subtype, PDF_NAME(Image)))
                {
                    is_jpx = pdf_is_jpx_image(gctx, obj); // check JPX image type

                    pdf_obj *o = pdf_dict_get(gctx, obj, PDF_NAME(SMask));
                    if (o) smask = pdf_to_num(gctx, o);

                    o = pdf_dict_get(gctx, obj, PDF_NAME(Width));
                    if (o) width = pdf_to_int(gctx, o);

                    o = pdf_dict_get(gctx, obj, PDF_NAME(Height));
                    if (o) height = pdf_to_int(gctx, o);

                    if (!is_jpx) // skip image loading for JPX
                    {
                        image = pdf_load_image(gctx, pdf, obj);

                        n = fz_colorspace_n(gctx, image->colorspace);
                        cs_name = fz_colorspace_name(gctx, image->colorspace);
                        fz_image_resolution(image, &xres, &yres);
                        bpc = (int) image->bpc;

                        cbuf = fz_compressed_image_buffer(gctx, image);
                        if (cbuf)
                        {
                            type = cbuf->params.type;
                            buffer = cbuf->buffer;
                        }
                    }
                    else
                    {
                        // handling JPX
                        buffer = pdf_load_stream_number(gctx, pdf, xref);
                        freebuf = buffer;   // so it will be dropped!
                        type = FZ_IMAGE_JPX;
                        o = pdf_dict_get(gctx, obj, PDF_NAME(ColorSpace));
                        if (o) cs_name = pdf_to_name(gctx, o);
                        o = pdf_dict_get(gctx, obj, PDF_NAME(BitsPerComponent));
                        if (o) bpc = pdf_to_int(gctx, o);
                    }

                    // ensure returning a PNG for unsupported images ----------
                    if (type < FZ_IMAGE_BMP ||
                        type == FZ_IMAGE_JBIG2)
                        type = FZ_IMAGE_UNKNOWN;

                    if (type != FZ_IMAGE_UNKNOWN)
                    {
                        ext = JM_image_extension(type);
                    }
                    else  // need to make a PNG buffer
                    {
                        buffer = freebuf = fz_new_buffer_from_image_as_png(gctx, image, fz_default_color_params);
                        ext = "png";
                    }

                    rc = PyDict_New();
                    DICT_SETITEM_DROP(rc, dictkey_ext,
                                      PyUnicode_FromString(ext));
                    DICT_SETITEM_DROP(rc, dictkey_smask,
                                      PyInt_FromLong((long) smask));
                    DICT_SETITEM_DROP(rc, dictkey_width,
                                      PyInt_FromLong((long) width));
                    DICT_SETITEM_DROP(rc, dictkey_height,
                                      PyInt_FromLong((long) height));
                    DICT_SETITEM_DROP(rc, dictkey_colorspace,
                                      PyInt_FromLong((long) n));
                    DICT_SETITEM_DROP(rc, dictkey_bpc,
                                      PyInt_FromLong((long) bpc));
                    DICT_SETITEM_DROP(rc, dictkey_xres,
                                      PyInt_FromLong((long) xres));
                    DICT_SETITEM_DROP(rc, dictkey_yres,
                                      PyInt_FromLong((long) yres));
                    DICT_SETITEM_DROP(rc, dictkey_cs_name,
                                      PyUnicode_FromString(cs_name));
                    DICT_SETITEM_DROP(rc, dictkey_image,
                                      JM_BinFromBuffer(gctx, buffer));
                }
                else
                    rc = PyDict_New();
            }
            fz_always(gctx)
            {
                fz_drop_image(gctx, image);
                fz_drop_buffer(gctx, freebuf);
                pdf_drop_obj(gctx, obj);
            }

            fz_catch(gctx) return NULL;

            return rc;
        }

        //---------------------------------------------------------------------
        // Delete all bookmarks (table of contents)
        // returns the list of deleted (now available) xref numbers
        //---------------------------------------------------------------------
        CLOSECHECK(_delToC)
        %pythonappend _delToC %{self.initData()%}
        PyObject *_delToC()
        {
            PyObject *xrefs = PyList_New(0);          // create Python list
            pdf_document *pdf = pdf_specifics(gctx, $self);
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

        //---------------------------------------------------------------------
        // Check: is xref a stream object?
        //---------------------------------------------------------------------
        CLOSECHECK0(isStream)
        PyObject *isStream(int xref=0)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) Py_RETURN_FALSE;  // not a PDF
            return JM_BOOL(pdf_obj_num_is_stream(gctx, pdf, xref));
        }

        //---------------------------------------------------------------------
        // Return the /SigFlags value
        //---------------------------------------------------------------------
        CLOSECHECK0(getSigFlags)
        PyObject *getSigFlags()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) return Py_BuildValue("i", -1);  // not a PDF
            size_t sigflag = 0;
            fz_try(gctx)
            {
                pdf_obj *sigflags = pdf_dict_getl(gctx,
                                                  pdf_trailer(gctx, pdf),
                                                  PDF_NAME(Root),
                                                  PDF_NAME(AcroForm),
                                                  PDF_NAME(SigFlags),
                                                  NULL);
                if (sigflags)
                {
                    sigflag = (size_t) pdf_to_int(gctx, sigflags);
                }
            }
            fz_catch(gctx) return Py_BuildValue("i", -1);  // any problem
            return Py_BuildValue("I", sigflag);
        }

        //---------------------------------------------------------------------
        // Check: is this an AcroForm with at least one field?
        //---------------------------------------------------------------------
        CLOSECHECK0(isFormPDF)
        %pythoncode%{@property%}
        PyObject *isFormPDF()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) Py_RETURN_FALSE;  // not a PDF
            int count = 0;  // init count
            fz_try(gctx)
            {
                pdf_obj *fields = pdf_dict_getl(gctx,
                                                pdf_trailer(gctx, pdf),
                                                PDF_NAME(Root),
                                                PDF_NAME(AcroForm),
                                                PDF_NAME(Fields),
                                                NULL);
                if (pdf_is_array(gctx, fields))
                {
                    count = pdf_array_len(gctx, fields);
                };
            }
            fz_catch(gctx) Py_RETURN_FALSE;      // any problem yields false
            if (count)
            {
                return Py_BuildValue("i", count);
            }
            else
            {
                Py_RETURN_FALSE;
            }
        }

        //---------------------------------------------------------------------
        // Return the list of field font resource names
        //---------------------------------------------------------------------
        CLOSECHECK0(FormFonts)
        %pythoncode%{@property%}
        PyObject *FormFonts()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) return_none;           // not a PDF
            pdf_obj *fonts = NULL;
            PyObject *liste = PyList_New(0);
            fz_try(gctx)
            {
                fonts = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Root), PDF_NAME(AcroForm), PDF_NAME(DR), PDF_NAME(Font), NULL);
                if (fonts && pdf_is_dict(gctx, fonts))       // fonts exist
                {
                    int i, n = pdf_dict_len(gctx, fonts);
                    for (i = 0; i < n; i++)
                    {
                        pdf_obj *f = pdf_dict_get_key(gctx, fonts, i);
                        LIST_APPEND_DROP(liste, JM_UNICODE(pdf_to_name(gctx, f)));
                    }
                }
            }
            fz_catch(gctx) return_none;       // any problem yields None
            return liste;
        }

        //---------------------------------------------------------------------
        // Add a field font
        //---------------------------------------------------------------------
        FITZEXCEPTION(_addFormFont, !result)
        CLOSECHECK(_addFormFont)
        PyObject *_addFormFont(char *name, char *font)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) return_none;  // not a PDF
            pdf_obj *fonts = NULL;
            fz_try(gctx)
            {
                fonts = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Root),
                             PDF_NAME(AcroForm), PDF_NAME(DR), PDF_NAME(Font), NULL);
                if (!fonts || !pdf_is_dict(gctx, fonts))
                    THROWMSG("PDF has no form fonts yet");
                pdf_obj *k = pdf_new_name(gctx, (const char *) name);
                pdf_obj *v = JM_pdf_obj_from_str(gctx, pdf, font);
                pdf_dict_put(gctx, fonts, k, v);
            }
            fz_catch(gctx) NULL;
            return_none;
        }

        //---------------------------------------------------------------------
        // Get Xref Number of Outline Root, create it if missing
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getOLRootNumber, !result)
        CLOSECHECK(_getOLRootNumber)
        PyObject *_getOLRootNumber()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            pdf_obj *root, *olroot, *ind_obj;
            fz_try(gctx)
            {
                assert_PDF(pdf);
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
            fz_catch(gctx) return NULL;
            return Py_BuildValue("i", pdf_to_num(gctx, olroot));
        }

        //---------------------------------------------------------------------
        // Get a new Xref number
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getNewXref, !result)
        CLOSECHECK(_getNewXref)
        PyObject *_getNewXref()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); /* conv doc to pdf*/
            fz_try(gctx) assert_PDF(pdf);
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return Py_BuildValue("i", pdf_create_object(gctx, pdf));
        }

        //---------------------------------------------------------------------
        // Get Length of Xref
        //---------------------------------------------------------------------
        CLOSECHECK0(_getXrefLength)
        PyObject *_getXrefLength()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            int xreflen = 0;
            if (pdf) xreflen = pdf_xref_len(gctx, pdf);
            return Py_BuildValue("i", xreflen);
        }

        //---------------------------------------------------------------------
        // Get XML Metadata xref
        //---------------------------------------------------------------------
        CLOSECHECK0(_getXmlMetadataXref)
        PyObject *_getXmlMetadataXref()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); // get pdf document
            pdf_obj *xml;
            int xref = 0;
            fz_try(gctx)
            {
                assert_PDF(pdf);
                pdf_obj *root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Root));
                if (!root) THROWMSG("could not load root object");
                xml = pdf_dict_gets(gctx, root, "Metadata");
                if (xml) xref = pdf_to_num(gctx, xml);
            }
            fz_catch(gctx) {;}
            return Py_BuildValue("i", xref);
        }

        //---------------------------------------------------------------------
        // Delete XML-based Metadata
        //---------------------------------------------------------------------
        FITZEXCEPTION(_delXmlMetadata, !result)
        CLOSECHECK(_delXmlMetadata)
        PyObject *_delXmlMetadata()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); // get pdf document
            fz_try(gctx)
            {
                assert_PDF(pdf);
                pdf_obj *root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Root));
                if (root) pdf_dict_dels(gctx, root, "Metadata");
            }
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return_none;
        }

        //---------------------------------------------------------------------
        // Get Object String of xref
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getXrefString, !result)
        CLOSECHECK0(_getXrefString)
        PyObject *_getXrefString(int xref, int compressed=0, int ascii=0)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); // conv doc to pdf
            pdf_obj *obj = NULL;
            fz_buffer *res = NULL;
            fz_output *out = NULL;
            PyObject *text = NULL;
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if (!INRANGE(xref, 1, xreflen-1))
                    THROWMSG("xref out of range");
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                obj = pdf_load_object(gctx, pdf, xref);
                pdf_print_obj(gctx, out, pdf_resolve_indirect(gctx, obj),
                              compressed, ascii);
                text = JM_EscapeStrFromBuffer(gctx, res);
            }
            fz_always(gctx)
            {
                pdf_drop_obj(gctx, obj);
                fz_drop_output(gctx, out);
                fz_drop_buffer(gctx, res);
                PyErr_Clear();
            }
            fz_catch(gctx) return NULL;
            return text;
        }

        //---------------------------------------------------------------------
        // Get String of PDF trailer
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getTrailerString, !result)
        CLOSECHECK0(_getTrailerString)
        PyObject *_getTrailerString(int compressed=0, int ascii=0)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); // conv doc to pdf
            if (!pdf) return_none;
            pdf_obj *obj = NULL;
            fz_buffer *res = NULL;
            fz_output *out = NULL;
            PyObject *text = NULL;
            fz_try(gctx)
            {
                obj = pdf_trailer(gctx, pdf);
                if (obj)
                {
                    res = fz_new_buffer(gctx, 1024);
                    out = fz_new_output_with_buffer(gctx, res);
                    pdf_print_obj(gctx, out, obj, compressed, ascii);
                    text = JM_EscapeStrFromBuffer(gctx, res);
                }
                else text = Py_None;
            }
            fz_always(gctx)
            {
                fz_drop_output(gctx, out);
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) return NULL;
            return text;
        }

        //---------------------------------------------------------------------
        // Get compressed stream of an object by xref
        // return_none if not stream
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getXrefStreamRaw, !result)
        CLOSECHECK(_getXrefStreamRaw)
        PyObject *_getXrefStreamRaw(int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            PyObject *r = Py_None;
            pdf_obj *obj = NULL;
            fz_var(obj);
            fz_buffer *res = NULL;
            fz_var(res);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if (!INRANGE(xref, 1, xreflen-1))
                    THROWMSG("xref out of range");
                obj = pdf_new_indirect(gctx, pdf, xref, 0);
                if (pdf_is_stream(gctx, obj))
                {
                    res = pdf_load_raw_stream_number(gctx, pdf, xref);
                    r = JM_BinFromBuffer(gctx, res);
                }
            }
            fz_always(gctx)
            {
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

        //---------------------------------------------------------------------
        // Get decompressed stream of an object by xref
        // return_none if not stream
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getXrefStream, !result)
        CLOSECHECK(_getXrefStream)
        PyObject *_getXrefStream(int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            PyObject *r = Py_None;
            pdf_obj *obj = NULL;
            fz_var(obj);
            fz_buffer *res = NULL;
            fz_var(res);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if (!INRANGE(xref, 1, xreflen-1))
                    THROWMSG("xref out of range");
                obj = pdf_new_indirect(gctx, pdf, xref, 0);
                if (pdf_is_stream(gctx, obj))
                {
                    res = pdf_load_stream_number(gctx, pdf, xref);
                    r = JM_BinFromBuffer(gctx, res);
                }
            }
            fz_always(gctx)
            {
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

        //---------------------------------------------------------------------
        // Update an Xref number with a new object given as a string
        //---------------------------------------------------------------------
        FITZEXCEPTION(_updateObject, !result)
        CLOSECHECK(_updateObject)
        PyObject *_updateObject(int xref, char *text, struct fz_page_s *page = NULL)
        {
            pdf_obj *new_obj;
            pdf_document *pdf = pdf_specifics(gctx, $self);     // get pdf doc
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if (!INRANGE(xref, 1, xreflen-1))
                    THROWMSG("xref out of range");
                // create new object with passed-in string
                new_obj = JM_pdf_obj_from_str(gctx, pdf, text);
                pdf_update_object(gctx, pdf, xref, new_obj);
                pdf_drop_obj(gctx, new_obj);
                if (page)
                    JM_refresh_link_table(gctx, pdf_page_from_fz_page(gctx, page));
            }
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return_none;
        }

        //---------------------------------------------------------------------
        // Update a stream identified by its xref
        //---------------------------------------------------------------------
        FITZEXCEPTION(_updateStream, !result)
        CLOSECHECK(_updateStream)
        PyObject *_updateStream(int xref = 0, PyObject *stream = NULL, int new = 0)
        {
            pdf_obj *obj = NULL;
            fz_var(obj);
            fz_buffer *res = NULL;
            fz_var(res);
            pdf_document *pdf = pdf_specifics(gctx, $self);     // get pdf doc
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if (!INRANGE(xref, 1, xreflen-1))
                    THROWMSG("xref out of range");
                // get the object
                obj = pdf_new_indirect(gctx, pdf, xref, 0);
                if (!new && !pdf_is_stream(gctx, obj))
                    THROWMSG("xref not a stream object");
                res = JM_BufferFromBytes(gctx, stream);
                if (!res) THROWMSG("bad type: 'stream'");
                JM_update_stream(gctx, pdf, obj, res, 1);

            }
            fz_always(gctx)
            {
                fz_drop_buffer(gctx, res);
                pdf_drop_obj(gctx, obj);
            }
            fz_catch(gctx)
                return NULL;
            pdf->dirty = 1;
            return_none;
        }

        //---------------------------------------------------------------------
        // Add or update metadata based on provided raw string
        //---------------------------------------------------------------------
        FITZEXCEPTION(_setMetadata, !result)
        CLOSECHECK(_setMetadata)
        PyObject *_setMetadata(char *text)
        {
            pdf_obj *info, *new_info, *new_info_ind;
            int info_num = 0;               // will contain xref no of info object
            pdf_document *pdf = pdf_specifics(gctx, $self);     // get pdf doc
            fz_try(gctx) {
                assert_PDF(pdf);
                // create new /Info object based on passed-in string
                new_info = JM_pdf_obj_from_str(gctx, pdf, text);
            }
            fz_catch(gctx) return NULL;
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

        //---------------------------------------------------------------------
        // create / refresh the page map
        //---------------------------------------------------------------------
        FITZEXCEPTION(_make_page_map, !result)
        CLOSECHECK0(_make_page_map)
        PyObject *_make_page_map()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) return_none;
            fz_try(gctx)
            {
                pdf_drop_page_tree(gctx, pdf);
                pdf_load_page_tree(gctx, pdf);
            }
            fz_catch(gctx) return NULL;
            return Py_BuildValue("i", pdf->rev_page_count);
        }


        //---------------------------------------------------------------------
        // full (deep) copy of one page
        //---------------------------------------------------------------------
        FITZEXCEPTION(fullcopyPage, !result)
        CLOSECHECK0(fullcopyPage)
        %pythonappend fullcopyPage %{
            self._reset_page_refs()%}
        PyObject *fullcopyPage(int pno, int to = -1)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            int pageCount = pdf_count_pages(gctx, pdf);
            fz_buffer *res = NULL, *nres=NULL;
            pdf_obj *page2 = NULL;
            fz_try(gctx)
            {
                assert_PDF(pdf);
                if (!INRANGE(pno, 0, pageCount - 1) ||
                    !INRANGE(to, -1, pageCount - 1))
                    THROWMSG("bad page number(s)");

                pdf_obj *page1 = pdf_resolve_indirect(gctx,
                                 pdf_lookup_page_obj(gctx, pdf, pno));

                pdf_obj *page2 = pdf_deep_copy_obj(gctx, page1);

                // read the old contents stream(s)
                res = JM_read_contents(gctx, page1);

                // create new /Contents object for page2
                if (res)
                {
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
            fz_always(gctx)
            {
                pdf_drop_page_tree(gctx, pdf);
                fz_drop_buffer(gctx, res);
                fz_drop_buffer(gctx, nres);
            }
            fz_catch(gctx) return NULL;
            return_none;
        }


        //---------------------------------------------------------------------
        // move or copy one page
        //---------------------------------------------------------------------
        FITZEXCEPTION(_move_copy_page, !result)
        CLOSECHECK0(_move_copy_page)
        %pythonappend _move_copy_page %{
            self._reset_page_refs()%}
        PyObject *_move_copy_page(int pno, int nb, int before, int copy)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            int i1, i2, pos, count, same = 0;
            pdf_obj *parent1 = NULL, *parent2 = NULL, *parent = NULL;
            pdf_obj *kids1, *kids2;
            fz_try(gctx)
            {
                assert_PDF(pdf);
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
            fz_catch(gctx) return NULL;
            return_none;
        }

        //---------------------------------------------------------------------
        // Initialize document: set outline and metadata properties
        //---------------------------------------------------------------------
        %pythoncode %{
            def initData(self):
                if self.isEncrypted:
                    raise ValueError("cannot initData - document still encrypted")
                self._outline = self._loadOutline()
                self.metadata = dict([(k,self._getMetadata(v)) for k,v in {'format':'format', 'title':'info:Title', 'author':'info:Author','subject':'info:Subject', 'keywords':'info:Keywords','creator':'info:Creator', 'producer':'info:Producer', 'creationDate':'info:CreationDate', 'modDate':'info:ModDate'}.items()])
                self.metadata['encryption'] = None if self._getMetadata('encryption')=='None' else self._getMetadata('encryption')

            outline = property(lambda self: self._outline)
            _getPageXref = _getPageObjNumber

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

            def deletePage(self, pno = -1):
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

                old_toc = self.getToC(False)
                new_toc = _toc_remove_page(old_toc, pno+1, pno+1)
                self._remove_links_to(pno, pno)

                self._deletePage(pno)

                self.setToC(new_toc)
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

                old_toc = self.getToC(False)
                new_toc = _toc_remove_page(old_toc, f+1, t+1)
                self._remove_links_to(f, t)

                for i in range(t, f - 1, -1):  # delete pages, last to first
                    self._deletePage(i)

                self.setToC(new_toc)
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

            xrefObject = get_pdf_object


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
                """Return the xref of the document XML metadata.
                """
                return self._getXmlMetadataXref()


            def reload_page(self, page):
                """Make a fresh copy of a page.
                """
                old_annots = {}  # copy annotation kid references to here
                pno = page.number  # save the page number
                for k, v in page._annot_refs.items():  # save the annot dictionary
                    old_annots[k] = v
                page._erase()  # remove the page
                page = None
                page = self.loadPage(pno)  # reload the page

                # copy previous annotation kids over to the new dictionary
                page_proxy = weakref.proxy(page)
                for k, v in old_annots.items():
                    annot = old_annots[k]
                    annot.parent = page_proxy  # refresh parent to new page
                    page._annot_refs[k] = annot
                return page


            def __repr__(self):
                m = "closed " if self.isClosed else ""
                if self.stream is None:
                    if self.name == "":
                        return m + "fitz.Document(<new PDF, doc# %i>)" % self._graft_id
                    return m + "fitz.Document('%s')" % (self.name,)
                return m + "fitz.Document('%s', <memory, doc# %i>)" % (self.name, self._graft_id)

            def __getitem__(self, i=0):
                if type(i) is not int:
                    raise ValueError("bad page number(s)")
                if i >= self.pageCount:
                    raise IndexError("bad page number(s)")
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
                    for gmap in self.Graftmaps:
                        self.Graftmaps[gmap] = None
                if hasattr(self, "this") and self.thisown:
                    self.__swig_destroy__(self)
                    self.thisown = False

                self.Graftmaps = {}
                self.ShownPages = {}
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
%rename(Page) fz_page_s;
struct fz_page_s {
    %extend {
        ~fz_page_s() {
            DEBUGMSG1("page");
            fz_drop_page(gctx, $self);
            DEBUGMSG2;
        }
        PARENTCHECK(bound)
        %pythonappend bound %{
            if val:
                val.thisown = True
        %}
        //---------------------------------------------------------------------
        // bound()
        //---------------------------------------------------------------------
        %pythonappend bound %{val = Rect(val)%}
        PyObject *bound() {
            fz_rect rect = fz_bound_page(gctx, $self);
            return JM_py_from_rect(rect);
        }
        %pythoncode %{rect = property(bound, doc="page rectangle")%}

        //---------------------------------------------------------------------
        // run()
        //---------------------------------------------------------------------
        FITZEXCEPTION(run, !result)
        PARENTCHECK(run)
        PyObject *run(struct DeviceWrapper *dw, PyObject *m)
        {
            fz_try(gctx) fz_run_page(gctx, $self, dw->device, JM_matrix_from_py(m), NULL);
            fz_catch(gctx) return NULL;
            return_none;
        }

        //---------------------------------------------------------------------
        // Page.getTextPage
        //---------------------------------------------------------------------
        FITZEXCEPTION(getTextPage, !result)
        %feature("autodoc","Create a TextPage directly from the page.") getTextPage;
        %pythonprepend getTextPage %{
        CheckParent(self)
        %}
        struct fz_stext_page_s *getTextPage(int flags=0)
        {
            fz_stext_page *textpage=NULL;
            fz_try(gctx)
            {
                textpage = JM_new_stext_page_from_page(gctx, $self, flags);
            }
            fz_catch(gctx)
            {
                return NULL;
            }
            return textpage;
        }


        //---------------------------------------------------------------------
        // Page.getSVGimage
        //---------------------------------------------------------------------
        FITZEXCEPTION(getSVGimage, !result)
        %feature("autodoc","Create an SVG image from the page.") getSVGimage;
        %pythonprepend getSVGimage %{
        CheckParent(self)
        %}
        PyObject *getSVGimage(PyObject *matrix = NULL)
        {
            fz_rect mediabox = fz_bound_page(gctx, $self);
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
            tbounds = fz_transform_rect(tbounds, ctm);

            fz_try(gctx)
            {
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                dev = fz_new_svg_device(gctx, out,
                                        tbounds.x1-tbounds.x0,  // width
                                        tbounds.y1-tbounds.y0,  // height
                                        FZ_SVG_TEXT_AS_PATH, 1);
                fz_run_page(gctx, $self, dev, ctm, NULL);
                fz_close_device(gctx, dev);
                text = JM_EscapeStrFromBuffer(gctx, res);
            }
            fz_always(gctx)
            {
                fz_drop_device(gctx, dev);
                fz_drop_output(gctx, out);
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx)
            {
                return NULL;
            }
            return text;
        }

        //---------------------------------------------------------------------
        // page addCaretAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addCaretAnnot, "Add 'Caret' annot on the page.")
        struct pdf_annot_s *addCaretAnnot(PyObject *point)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_annot *annot = NULL;
            fz_try(gctx)
            {
                pdf_document *pdf = page->doc;
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_CARET);
                fz_point p = JM_point_from_py(point);
                fz_rect r = {p.x, p.y, p.x + 20, p.y + 20};
                pdf_set_annot_rect(gctx, annot, r);
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) return NULL;
            return pdf_keep_annot(gctx, annot);
        }

        //---------------------------------------------------------------------
        // page addLineAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addLineAnnot, "Add 'Line' annot for points p1 and p2.")
        struct pdf_annot_s *addLineAnnot(PyObject *p1, PyObject *p2)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_annot *annot = NULL;
            fz_point a = JM_point_from_py(p1);
            fz_point b = JM_point_from_py(p2);
            fz_rect r  = fz_make_rect(MIN(a.x, b.x),
                                      MIN(a.y, b.y),
                                      MAX(a.x, b.x),
                                      MAX(a.y, b.y));
            r = fz_expand_rect(r, 3);
            fz_try(gctx)
            {
                assert_PDF(page);
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_LINE);
                pdf_set_annot_line(gctx, annot, a, b);
                pdf_set_annot_rect(gctx, annot, r);
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) return NULL;
            return pdf_keep_annot(gctx, annot);
        }

        //---------------------------------------------------------------------
        // page addTextAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addTextAnnot, "Add a 'sticky note' at position 'point'.")
        struct pdf_annot_s *addTextAnnot(PyObject *point,
                                         char *text,
                                         char *icon=NULL)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_annot *annot = NULL;
            fz_point pos = JM_point_from_py(point);
            fz_var(annot);
            fz_try(gctx)
            {
                assert_PDF(page);
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_TEXT);
                fz_rect r = fz_make_rect(pos.x, pos.y, pos.x + 20, pos.y + 20);
                pdf_set_annot_rect(gctx, annot, r);
                pdf_set_annot_contents(gctx, annot, text);
                if (!icon)
                {
                    pdf_set_annot_icon_name(gctx, annot, "Note");
                }
                else
                {
                    pdf_dict_put_name(gctx, annot->obj, PDF_NAME(Name), icon);
                }
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) return NULL;
            return pdf_keep_annot(gctx, annot);
        }

        //---------------------------------------------------------------------
        // page addInkAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addInkAnnot, "Add a 'handwriting' as a list of list of point-likes. Each sublist forms an independent stroke.")
        struct pdf_annot_s *addInkAnnot(PyObject *list)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_annot *annot = NULL;
            PyObject *p = NULL, *sublist = NULL;
            pdf_obj *inklist = NULL, *stroke = NULL;
            fz_matrix ctm, inv_ctm;
            double x, y;
            fz_point point;
            fz_var(annot);
            fz_try(gctx)
            {
                assert_PDF(page);
                if (!PySequence_Check(list)) THROWMSG("arg must be a sequence");
                pdf_page_transform(gctx, page, NULL, &ctm);
                inv_ctm = fz_invert_matrix(ctm);
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_INK);
                Py_ssize_t i, j, n0 = PySequence_Size(list), n1;
                inklist = pdf_new_array(gctx, annot->page->doc, n0);
                for (j = 0; j < n0; j++)
                {
                    sublist = PySequence_ITEM(list, j);
                    n1 = PySequence_Size(sublist);
                    stroke = pdf_new_array(gctx, annot->page->doc, 2 * n1);
                    for (i = 0; i < n1; i++)
                    {
                        p = PySequence_ITEM(sublist, i);
                        if (!PySequence_Check(p) || PySequence_Size(p) != 2)
                            THROWMSG("3rd level entries must be pairs of floats");
                        x = PyFloat_AsDouble(PySequence_ITEM(p, 0));
                        if (PyErr_Occurred())
                            THROWMSG("invalid point coordinate");
                        y = PyFloat_AsDouble(PySequence_ITEM(p, 1));
                        if (PyErr_Occurred())
                            THROWMSG("invalid point coordinate");
                        Py_CLEAR(p);
                        point = fz_transform_point(fz_make_point(x, y), inv_ctm);
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
            fz_catch(gctx)
            {
                Py_CLEAR(p);
                Py_CLEAR(sublist);
                return NULL;
            }

            return pdf_keep_annot(gctx, annot);
        }

        //---------------------------------------------------------------------
        // page addStampAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addStampAnnot, "Add a 'rubber stamp' in a rectangle.")
        struct pdf_annot_s *addStampAnnot(PyObject *rect, int stamp = 0)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
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
            fz_try(gctx)
            {
                assert_PDF(page);
                if (INRANGE(stamp, 0, n-1))
                    name = stamp_id[stamp];
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_STAMP);
                pdf_set_annot_rect(gctx, annot, JM_rect_from_py(rect));
                pdf_dict_put(gctx, annot->obj, PDF_NAME(Name), name);
                pdf_set_annot_contents(gctx, annot,
                        pdf_dict_get_name(gctx, annot->obj, PDF_NAME(Name)));
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) return NULL;
            return pdf_keep_annot(gctx, annot);
        }

        //---------------------------------------------------------------------
        // page addFileAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addFileAnnot, "Add a 'FileAttachment' annotation at location 'point'.")
        struct pdf_annot_s *addFileAnnot(PyObject *point,
                    PyObject *buffer,
                    char *filename,
                    char *ufilename = NULL,
                    char *desc = NULL,
                    char *icon=NULL)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_annot *annot = NULL;
            char *data = NULL, *uf = ufilename, *d = desc;
            if (!ufilename) uf = filename;
            if (!desc) d = filename;
            size_t len = 0;
            fz_buffer *filebuf = NULL;
            fz_point p = JM_point_from_py(point);
            fz_rect r = {p.x, p.y, p.x + 20, p.y + 20};
            fz_var(annot);
            fz_try(gctx)
            {
                assert_PDF(page);
                filebuf = JM_BufferFromBytes(gctx, buffer);
                if (!filebuf) THROWMSG("bad type: 'buffer'");
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_FILEATTACHMENT);
                pdf_set_annot_rect(gctx, annot, r);

                if (!icon)
                {
                    pdf_set_annot_icon_name(gctx, annot, "PushPin");
                }
                else
                {
                    pdf_dict_put_name(gctx, annot->obj, PDF_NAME(Name), icon);
                }

                pdf_obj *val = JM_embed_file(gctx, page->doc, filebuf,
                                             filename, uf, d, 1);
                pdf_dict_put(gctx, annot->obj, PDF_NAME(FS), val);
                pdf_dict_put_text_string(gctx, annot->obj, PDF_NAME(Contents), filename);
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) return NULL;
            return pdf_keep_annot(gctx, annot);
        }

        //---------------------------------------------------------------------
        // page: add a text marker annotation
        //---------------------------------------------------------------------
        MARKERWRAP(_add_text_marker, "Add a text marker annotation.")
        struct pdf_annot_s *_add_text_marker(PyObject *quads, int annot_type)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_annot *annot = NULL;
            fz_try(gctx)
            {
                annot = pdf_create_annot(gctx, page, annot_type);
                Py_ssize_t i, len = PySequence_Size(quads);
                for (i = 0; i < len; i++)
                {
                    PyObject *val = PySequence_ITEM(quads, i);
                    fz_quad q = JM_quad_from_py(val);
                    Py_DECREF(val);
                    pdf_add_annot_quad_point(gctx, annot, q);
                }
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) return NULL;
            return pdf_keep_annot(gctx, annot);
        }

        %pythoncode %{
        def addStrikeoutAnnot(self, quads):
            """Add a 'StrikeOut' annotation."""
            return self._add_text_marker(quads, PDF_ANNOT_STRIKEOUT)

        def addUnderlineAnnot(self, quads):
            """Add a 'Underline' annotation."""
            return self._add_text_marker(quads, PDF_ANNOT_UNDERLINE)

        def addSquigglyAnnot(self, quads):
            """Add a 'Squiggly' annotation."""
            return self._add_text_marker(quads, PDF_ANNOT_SQUIGGLY)

        def addHighlightAnnot(self, quads):
            """Add a 'Highlight' annotation."""
            return self._add_text_marker(quads, PDF_ANNOT_HIGHLIGHT)
        %}

        //---------------------------------------------------------------------
        // page: add a circle or rectangle annotation
        //---------------------------------------------------------------------
        ANNOTWRAP1(_add_square_or_circle, "Add a 'Square' or 'Circle' annotation.")
        struct pdf_annot_s *_add_square_or_circle(PyObject *rect, int annot_type)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_annot *annot = NULL;
            fz_try(gctx)
            {
                annot = pdf_create_annot(gctx, page, annot_type);
                pdf_set_annot_rect(gctx, annot, JM_rect_from_py(rect));
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) return NULL;
            return pdf_keep_annot(gctx, annot);
        }

        %pythoncode %{
        def addRectAnnot(self, rect):
            """Add a 'Square' annotation."""
            return self._add_square_or_circle(rect, PDF_ANNOT_SQUARE)

        def addCircleAnnot(self, rect):
            """Add a 'Circle' annotation."""
            return self._add_square_or_circle(rect, PDF_ANNOT_CIRCLE)
        %}


        //---------------------------------------------------------------------
        // page: add multiline annotation
        //---------------------------------------------------------------------
        ANNOTWRAP1(_add_multiline, "Add a multiline annotation.")
        struct pdf_annot_s *_add_multiline(PyObject *points, int annot_type)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_annot *annot = NULL;
            fz_try(gctx)
            {
                fz_rect rect;
                Py_ssize_t i, n = PySequence_Size(points);
                if (n < 2) THROWMSG("bad list of points");
                annot = pdf_create_annot(gctx, page, annot_type);
                for (i = 0; i < n; i++)
                {
                    PyObject *p = PySequence_ITEM(points, i);
                    if (PySequence_Size(p) != 2)
                    {
                        Py_DECREF(p);
                        THROWMSG("bad point in points");
                    }
                    fz_point point = JM_point_from_py(p);
                    Py_DECREF(p);
                    pdf_add_annot_vertex(gctx, annot, point);
                    if (i == 0)
                    {
                        rect = fz_make_rect(point.x, point.y, point.x, point.y);
                    }
                    else
                        rect = fz_include_point_in_rect(rect, point);
                }
                rect = fz_expand_rect(rect, 3);
                pdf_set_annot_rect(gctx, annot, rect);
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) return NULL;
            return pdf_keep_annot(gctx, annot);
        }

        %pythoncode %{
        def addPolylineAnnot(self, points):
            """Add a 'PolyLine' annotation."""
            return self._add_multiline(points, PDF_ANNOT_POLYLINE)

        def addPolygonAnnot(self, points):
            """Add a 'Polygon' annotation."""
            return self._add_multiline(points, PDF_ANNOT_POLYGON)
        %}

        //---------------------------------------------------------------------
        // page addFreetextAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addFreetextAnnot, "Add a 'FreeText' annotation in rectangle 'rect'.")
        struct pdf_annot_s *addFreetextAnnot(PyObject *rect, char *text,
                                             float fontsize=12,
                                             char *fontname=NULL,
                                             PyObject *text_color=NULL,
                                             PyObject *fill_color=NULL,
                                             int rotate=0)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            float fcol[4] = {1, 1, 1, 1};    // fill color: white
            int nfcol = 0;
            JM_color_FromSequence(fill_color, &nfcol, fcol);
            float tcol[4] = {0, 0, 0, 0}; // std. text color: black
            int ntcol = 0;
            JM_color_FromSequence(text_color, &ntcol, tcol);
            fz_rect r = JM_rect_from_py(rect);
            pdf_annot *annot = NULL;
            fz_try(gctx)
            {
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_FREE_TEXT);
                pdf_set_annot_contents(gctx, annot, text);
                pdf_set_annot_rect(gctx, annot, r);
                pdf_dict_put_int(gctx, annot->obj, PDF_NAME(Rotate), rotate);

                if (fill_color)
                {
                    pdf_set_annot_color(gctx, annot, nfcol, fcol);
                }

                // insert the default appearance string
                JM_make_annot_DA(gctx, annot, ntcol, tcol, fontname, fontsize);
                JM_add_annot_id(gctx, annot, "fitzannot");
                pdf_update_annot(gctx, annot);
            }
            fz_always(gctx) {;}
            fz_catch(gctx) return NULL;
            return pdf_keep_annot(gctx, annot);
        }

        //---------------------------------------------------------------------
        // page retrieve annotation
        //---------------------------------------------------------------------
        %pythonprepend load_annot %{
        CheckParent(self)
        if not self.parent.isPDF:
            raise ValueError("not a PDF")
        if name not in self.annot_names():
            return None
        %}
        %pythonappend load_annot %{
        if not val:
            return val
        val.thisown = True
        val.parent = weakref.proxy(self)
        self._annot_refs[id(val)] = val
        %}
        struct pdf_annot_s *load_annot(char *name)
        {
            pdf_annot *annot = NULL;
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            annot = JM_get_annot_by_name(gctx, page, name);
            return annot;
        }

        //---------------------------------------------------------------------
        // page retrieve list of annotation names
        //---------------------------------------------------------------------
        PyObject *annot_names()
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            if (!page)
            {
                return_none;
            }
            return JM_get_annot_id_list(gctx, page);
        }


        %pythoncode %{
            #---------------------------------------------------------------------
            # page addWidget
            #---------------------------------------------------------------------
            def addWidget(self, widget):
                """Add a form field.
                """
                CheckParent(self)
                doc = self.parent
                if not doc.isPDF:
                    raise ValueError("not a PDF")
                widget._validate()
                annot = self._addWidget(widget)
                if not annot:
                    return None
                annot.thisown = True
                annot.parent = weakref.proxy(self) # owning page object
                self._annot_refs[id(annot)] = annot
                widget.parent = self
                widget._annot = annot
                widget.update()
                return annot
        %}
        FITZEXCEPTION(_addWidget, !result)
        struct pdf_annot_s *_addWidget(PyObject *Widget)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_document *pdf = page->doc;
            pdf_annot *annot = NULL;
            pdf_widget *widget = NULL;
            fz_var(annot);
            fz_try(gctx)
            {
                //-------------------------------------------------------------
                // create the widget - only need type and field name for this
                //-------------------------------------------------------------
                int field_type = (int) PyInt_AsLong(PyObject_GetAttrString(Widget,
                                                    "field_type"));
                char *field_name = JM_Python_str_AsChar(PyObject_GetAttrString(Widget,
                                                        "field_name"));
                widget = JM_create_widget(gctx, pdf, page, field_type, field_name);
                JM_Python_str_DelForPy3(field_name);
                JM_PyErr_Clear;
                annot = (pdf_annot *) widget;
                JM_add_annot_id(gctx, annot, "fitzwidget");
            }
            fz_always(gctx) JM_PyErr_Clear;
            fz_catch(gctx) return NULL;
            return pdf_keep_annot(gctx, annot);
        }

        //---------------------------------------------------------------------
        // Page.getDisplayList
        //---------------------------------------------------------------------
        FITZEXCEPTION(getDisplayList, !result)
        %pythonprepend getDisplayList %{
        CheckParent(self)
        %}
        struct fz_display_list_s *getDisplayList(int annots=1)
        {
            fz_display_list *dl = NULL;
            fz_try(gctx)
            {
                if (annots)
                {
                    dl = fz_new_display_list_from_page(gctx, $self);
                }
                else
                {
                    dl = fz_new_display_list_from_page_contents(gctx, $self);
                }
            }
            fz_catch(gctx) return NULL;
            return dl;
        }


        //---------------------------------------------------------------------
        // Page._makePixmap
        //---------------------------------------------------------------------
        FITZEXCEPTION(_makePixmap, !result)
        struct fz_pixmap_s *_makePixmap(struct fz_document_s *doc,
                                       PyObject *ctm,
                                       struct fz_colorspace_s *cs,
                                       int alpha=0,
                                       int annots=1,
                                       PyObject *clip=NULL)
        {
            fz_pixmap *pix = NULL;
            fz_try(gctx)
            {
                pix = JM_pixmap_from_page(gctx, doc, $self, ctm,
                                          cs, alpha, annots, clip);
            }
            fz_catch(gctx) return NULL;
            return pix;
        }


        //---------------------------------------------------------------------
        // Page.insertString
        //---------------------------------------------------------------------
        FITZEXCEPTION(insertString, !result)
        PARENTCHECK(insertString)
        PyObject *insertString(PyObject *point, char *text, float fontsize,
                               char *fontname, PyObject *color, char *language)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            fz_text_language lang = fz_text_language_from_string(language);
            fz_rect text_rect = fz_infinite_rect;
            fz_font *user_font = NULL;
            fz_text *text_obj = NULL;
            fz_try(gctx)
            {
                assert_PDF(page);
                fz_matrix ctm = fz_identity;
                pdf_page_transform(gctx, page, NULL, &ctm);
                fz_matrix ictm = fz_invert_matrix(ctm);
                fz_point p = fz_transform_point(JM_point_from_py(point), ictm);
                fz_matrix trm = {1,0,0,1,p.x, p.y};
                int wmode = 0;
                int bidi_level = 0;
                text_obj = fz_new_text(gctx);
                fz_bidi_direction markup_dir = FZ_BIDI_LTR;
                trm = fz_show_string(gctx, text_obj,
                                     user_font,
                                     trm,
                                     text,
                                     wmode,
                                     bidi_level,
                                     markup_dir,
                                     lang);
            }
            fz_always(gctx)
            {
                fz_drop_text(gctx, text_obj);
            }
            fz_catch(gctx)
            {
                return NULL;
            }
            return JM_py_from_rect(text_rect);
        }


        //---------------------------------------------------------------------
        // Page.setCropBox
        // ATTENTION: This will alse change the value returned by Page.bound()
        //---------------------------------------------------------------------
        FITZEXCEPTION(setCropBox, !result)
        PARENTCHECK(setCropBox)
        PyObject *setCropBox(PyObject *rect)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(page);
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
            fz_catch(gctx) return NULL;
            page->doc->dirty = 1;
            return_none;
        }

        //---------------------------------------------------------------------
        // loadLinks()
        //---------------------------------------------------------------------
        PARENTCHECK(loadLinks)
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
        struct fz_link_s *loadLinks()
        {
            fz_link *l = NULL;
            fz_try(gctx) l = fz_load_links(gctx, $self);
            fz_catch(gctx) return NULL;
            return l;
        }
        %pythoncode %{firstLink = property(loadLinks, doc="First link on page")%}

        //---------------------------------------------------------------------
        // firstAnnot
        //---------------------------------------------------------------------
        PARENTCHECK(firstAnnot)
        %feature("autodoc","Points to first annotation on page") firstAnnot;
        %pythonappend firstAnnot
%{if val:
    val.thisown = True
    val.parent = weakref.proxy(self) # owning page object
    self._annot_refs[id(val)] = val
%}
        %pythoncode %{@property%}
        struct pdf_annot_s *firstAnnot()
        {
            pdf_annot *annot = NULL;
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            if (page)
            {
                annot = pdf_first_annot(gctx, page);
                if (annot) pdf_keep_annot(gctx, annot);
            }
            return annot;
        }

        //---------------------------------------------------------------------
        // firstWidget
        //---------------------------------------------------------------------
        %pythoncode %{@property%}
        PARENTCHECK(firstWidget)
        %pythonappend firstWidget
        %{
            if not val:
                return None
            val.thisown = True
            val.parent = weakref.proxy(self) # owning page object
            self._annot_refs[id(val)] = val

            widget = Widget()
            TOOLS._fill_widget(val, widget)
            val = widget
        %}
        struct pdf_annot_s *firstWidget()
        {
            pdf_annot *annot = NULL;
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            if (page)
            {
                annot = pdf_first_widget(gctx, page);
                if (annot) pdf_keep_annot(gctx, annot);
            }
            return annot;
        }


        //---------------------------------------------------------------------
        // Page.deleteLink() - delete link
        //---------------------------------------------------------------------
        PARENTCHECK(deleteLink)
        %feature("autodoc","Delete link if PDF") deleteLink;
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
            fz_try(gctx)
            {
                pdf_page *page = pdf_page_from_fz_page(gctx, $self);
                if (!page) goto finished;  // have no PDF
                int xref = (int) PyInt_AsLong(PyDict_GetItem(linkdict, dictkey_xref));
                if (xref < 1) goto finished;  // invalid xref
                pdf_obj *annots = pdf_dict_get(gctx, page->obj, PDF_NAME(Annots));
                if (!annots) goto finished;  // have no annotations
                int len = pdf_array_len(gctx, annots);
                int i, oxref = 0;
                for (i = 0; i < len; i++)
                {
                    oxref = pdf_to_num(gctx, pdf_array_get(gctx, annots, i));
                    if (xref == oxref) break;        // found xref in annotations
                }
                if (xref != oxref) goto finished;  // xref not in annotations
                pdf_array_delete(gctx, annots, i);   // delete entry in annotations
                pdf_delete_object(gctx, page->doc, xref);      // delete link object
                pdf_dict_put(gctx, page->obj, PDF_NAME(Annots), annots);
                JM_refresh_link_table(gctx, page);            // reload link / annot tables
                page->doc->dirty = 1;
                finished:;
            }
            fz_catch(gctx) {;}
        }

        //---------------------------------------------------------------------
        // Page.deleteAnnot() - delete annotation and return the next one
        //---------------------------------------------------------------------
        %pythonprepend deleteAnnot
%{
CheckParent(self)
CheckParent(annot)
%}
        %pythonappend deleteAnnot
%{
if val:
    val.thisown = True
    val.parent = weakref.proxy(self) # owning page object
    val.parent._annot_refs[id(val)] = val
annot._erase()
%}
        %feature("autodoc","Delete annot and return next one.") deleteAnnot;
        struct pdf_annot_s *deleteAnnot(struct pdf_annot_s *annot)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_annot *irt_annot = NULL;
            while (1)  // first loop through all /IRT annots and remove them
            {
                irt_annot = JM_find_annot_irt(gctx, annot);
                if (!irt_annot)  // no more there
                    break;
                JM_delete_annot(gctx, page, irt_annot);
            }
            pdf_annot *nextannot = pdf_next_annot(gctx, annot);  // store next
            JM_delete_annot(gctx, page, annot);
            if (nextannot)
            {
                nextannot = pdf_keep_annot(gctx, nextannot);
            }
            page->doc->dirty = 1;
            return nextannot;
        }

        //---------------------------------------------------------------------
        // MediaBox size: width, height of /MediaBox (PDF only)
        //---------------------------------------------------------------------
        PARENTCHECK(MediaBoxSize)
        %pythoncode %{@property%}
        %feature("autodoc","Retrieve width, height of /MediaBox.") MediaBoxSize;
        %pythonappend MediaBoxSize %{
        val = Point(val)
        if not bool(val):
            r = self.rect
            val = Point(r.width, r.height)
        %}
        PyObject *MediaBoxSize()
        {
            PyObject *p = JM_py_from_point(fz_make_point(0, 0));
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            if (!page) return p;
            fz_rect r = fz_empty_rect;
            pdf_obj *o = pdf_dict_get_inheritable(gctx, page->obj, PDF_NAME(MediaBox));
            if (!o) return p;

            r = pdf_to_rect(gctx, o);
            return JM_py_from_point(fz_make_point(r.x1 - r.x0, r.y1 - r.y0));
        }

        //---------------------------------------------------------------------
        // CropBox position: top-left of /CropBox (PDF only)
        //---------------------------------------------------------------------
        PARENTCHECK(CropBoxPosition)
        %pythoncode %{@property%}
        %feature("autodoc","Retrieve position of /CropBox. Return (0,0) for non-PDF, or no /CropBox.") CropBoxPosition;
        %pythonappend CropBoxPosition %{val = Point(val)%}
        PyObject *CropBoxPosition()
        {
            PyObject *p = JM_py_from_point(fz_make_point(0, 0));
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            if (!page) return p;                 // not a PDF
            pdf_obj *o = pdf_dict_get_inheritable(gctx, page->obj, PDF_NAME(CropBox));
            if (!o) return p;                    // no CropBox specified
            fz_rect cbox = pdf_to_rect(gctx, o);
            return JM_py_from_point(fz_make_point(cbox.x0, cbox.y0));;
        }

        //---------------------------------------------------------------------
        // rotation - return page rotation
        //---------------------------------------------------------------------
        PARENTCHECK(rotation)
        %pythoncode %{@property%}
        %feature("autodoc","Retrieve page rotation.") rotation;
        int rotation()
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            if (!page) return -1;
            return pdf_to_int(gctx, pdf_dict_get_inheritable(gctx, page->obj, PDF_NAME(Rotate)));
        }

        /*********************************************************************/
        // setRotation() - set page rotation
        /*********************************************************************/
        FITZEXCEPTION(setRotation, !result)
        PARENTCHECK(setRotation)
        %feature("autodoc","Set page rotation to 'rot' degrees.") setRotation;
        PyObject *setRotation(int rot)
        {
            fz_try(gctx)
            {
                pdf_page *page = pdf_page_from_fz_page(gctx, $self);
                assert_PDF(page);
                if (rot % 90) THROWMSG("rotation not multiple of 90");
                pdf_dict_put_int(gctx, page->obj, PDF_NAME(Rotate), (int64_t) rot);
                page->doc->dirty = 1;
            }
            fz_catch(gctx) return NULL;
            return_none;
        }

        /*********************************************************************/
        // Page._addAnnot_FromString
        // Add new links provided as an array of string object definitions.
        /*********************************************************************/
        FITZEXCEPTION(_addAnnot_FromString, !result)
        PARENTCHECK(_addAnnot_FromString)
        PyObject *_addAnnot_FromString(PyObject *linklist)
        {
            pdf_obj *annots, *annot, *ind_obj, *new_array;
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            PyObject *txtpy;
            char *text;
            int lcount = (int) PySequence_Size(linklist); // new object count
            if (lcount < 1) return_none;
            int i;
            fz_try(gctx)
            {
                assert_PDF(page);                // make sure we have a PDF
                // get existing annots array
                annots = pdf_dict_get(gctx, page->obj, PDF_NAME(Annots));
                if (annots)
                {
                    new_array = annots;
                }
                else
                {
                    new_array = pdf_new_array(gctx, page->doc, lcount);
                    pdf_dict_put_drop(gctx, page->obj, PDF_NAME(Annots), new_array);
                    new_array = pdf_dict_get(gctx, page->obj, PDF_NAME(Annots));
                }
            }
            fz_catch(gctx) return NULL;

            // extract object sources from Python list and store as annotations
            for (i = 0; i < lcount; i++)
            {
                fz_try(gctx)
                {
                    text = NULL;
                    txtpy = PySequence_ITEM(linklist, (Py_ssize_t) i);
                    text = JM_Python_str_AsChar(txtpy);
                    if (!text) THROWMSG("non-string linklist item");
                    annot = JM_pdf_obj_from_str(gctx, page->doc, text);
                    JM_Python_str_DelForPy3(text);
                    ind_obj = pdf_add_object(gctx, page->doc, annot);
                    pdf_array_push_drop(gctx, new_array, ind_obj);
                    pdf_drop_obj(gctx, annot);
                }
                fz_catch(gctx)
                {
                    if (text)
                        PySys_WriteStderr("%s (%i): '%s'\n", fz_caught_message(gctx), i, text);
                    else
                        PySys_WriteStderr("%s (%i)\n", fz_caught_message(gctx), i);
                    JM_Python_str_DelForPy3(text);
                    PyErr_Clear();
                }
            }
            fz_try(gctx)
            {
                JM_refresh_link_table(gctx, page);
            }
            fz_catch(gctx) return NULL;
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
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
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
        // clean contents stream
        //---------------------------------------------------------------------
        PARENTCHECK(_cleanContents)
        PyObject *_cleanContents()
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            if (!page)
            {
                return_none;
            }
            fz_try(gctx)
            {
                pdf_clean_page_contents(gctx, page->doc, page, NULL, NULL, NULL, 1, 0);
            }
            fz_catch(gctx) return_none;
            page->doc->dirty = 1;
            return_none;
        }

        //---------------------------------------------------------------------
        // Show a PDF page
        //---------------------------------------------------------------------
        FITZEXCEPTION(_showPDFpage, !result)
        PyObject *_showPDFpage(struct fz_page_s *fz_srcpage, int overlay=1, PyObject *matrix=NULL, int xref=0, PyObject *clip = NULL, struct pdf_graft_map_s *graftmap = NULL, char *_imgname = NULL)
        {
            pdf_obj *xobj1, *xobj2, *resources;
            fz_buffer *res=NULL, *nres=NULL;
            fz_rect cropbox = JM_rect_from_py(clip);
            fz_matrix mat = JM_matrix_from_py(matrix);
            int rc_xref = xref;
            fz_try(gctx)
            {
                pdf_page *tpage = pdf_page_from_fz_page(gctx, $self);
                pdf_obj *tpageref = tpage->obj;
                pdf_document *pdfout = tpage->doc;    // target PDF

                //-------------------------------------------------------------
                // convert the source page to a Form XObject
                //-------------------------------------------------------------
                xobj1 = JM_xobject_from_page(gctx, pdfout, fz_srcpage,
                                             xref, graftmap);
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

                pdf_drop_obj(gctx, subres);
                fz_drop_buffer(gctx, res);

                //-------------------------------------------------------------
                // update target page with xobj2:
                //-------------------------------------------------------------
                // 1. insert Xobject in Resources
                //-------------------------------------------------------------
                resources = pdf_dict_get_inheritable(gctx, tpageref, PDF_NAME(Resources));
                subres = pdf_dict_get(gctx, resources, PDF_NAME(XObject));
                if (!subres)           // has no XObject yet: create one
                {
                    subres = pdf_new_dict(gctx, pdfout, 10);
                    pdf_dict_putl(gctx, tpageref, subres, PDF_NAME(Resources), PDF_NAME(XObject), NULL);
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
            fz_catch(gctx) return NULL;
            return Py_BuildValue("i", rc_xref);
        }

        //---------------------------------------------------------------------
        // insert an image
        //---------------------------------------------------------------------
        FITZEXCEPTION(_insertImage, !result)
        PyObject *_insertImage(const char *filename=NULL, struct fz_pixmap_s *pixmap=NULL, PyObject *stream=NULL, int overlay=1, PyObject *matrix=NULL,
        const char *_imgname=NULL, PyObject *_imgpointer=NULL)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_document *pdf;
            fz_pixmap *pm = NULL;
            fz_pixmap *pix = NULL;
            fz_image *mask = NULL;
            fz_separations *seps = NULL;
            pdf_obj *resources, *xobject, *ref;
            fz_buffer *res = NULL, *nres = NULL,  *imgbuf = NULL;
            fz_matrix mat = JM_matrix_from_py(matrix); // pre-calculated

            const char *template = " q %g %g %g %g %g %g cm /%s Do Q ";
            char *cont = NULL;
            fz_color_params color_params = {0};
            fz_image *zimg = NULL, *image = NULL;
            fz_try(gctx)
            {
                //-------------------------------------------------------------
                // create the image
                //-------------------------------------------------------------
                if (filename || EXISTS(stream) || EXISTS(_imgpointer))
                {
                    if (filename)
                    {
                        image = fz_new_image_from_file(gctx, filename);
                    }

                    else if (EXISTS(stream))
                    {
                        imgbuf = JM_BufferFromBytes(gctx, stream);
                        image = fz_new_image_from_buffer(gctx, imgbuf);
                    }

                    else  // fz_image pointer has been handed in
                    {
                        image = (fz_image *)PyLong_AsVoidPtr(_imgpointer);
                    }

                    // test for alpha (which would require making an SMask)
                    pix = fz_get_pixmap_from_image(gctx, image, NULL, NULL, 0, 0);
                    if (pix->alpha == 1)
                    {   // have alpha: create an SMask

                        pm = fz_convert_pixmap(gctx, pix, NULL, NULL, NULL, color_params, 1);
                        pm->alpha = 0;
                        pm->colorspace = fz_keep_colorspace(gctx, fz_device_gray(gctx));
                        mask = fz_new_image_from_pixmap(gctx, pm, NULL);
                        zimg = fz_new_image_from_pixmap(gctx, pix, mask);
                        fz_drop_image(gctx, image);
                        image = zimg;
                        zimg = NULL;
                    }
                }
                else // pixmap specified
                {
                    if (pixmap->alpha == 0)
                        image = fz_new_image_from_pixmap(gctx, pixmap, NULL);
                    else
                    {   // pixmap has alpha: create an SMask
                        pm = fz_convert_pixmap(gctx, pixmap, NULL, NULL, NULL, color_params, 1);
                        pm->alpha = 0;
                        pm->colorspace = fz_keep_colorspace(gctx, fz_device_gray(gctx));
                        mask = fz_new_image_from_pixmap(gctx, pm, NULL);
                        image = fz_new_image_from_pixmap(gctx, pixmap, mask);
                    }
                }

                //-------------------------------------------------------------
                // image created - now put it in the PDF
                //-------------------------------------------------------------
                pdf = page->doc;  // owning PDF

                // get /Resources, /XObject
                resources = pdf_dict_get_inheritable(gctx, page->obj, PDF_NAME(Resources));
                xobject = pdf_dict_get(gctx, resources, PDF_NAME(XObject));
                if (!xobject)  // has no XObject yet, create one
                {
                    xobject = pdf_new_dict(gctx, pdf, 10);
                    pdf_dict_putl_drop(gctx, page->obj, xobject, PDF_NAME(Resources), PDF_NAME(XObject), NULL);
                }

                ref = pdf_add_image(gctx, pdf, image);
                pdf_dict_puts(gctx, xobject, _imgname, ref);  // update XObject

                // make contents stream that invokes the image
                nres = fz_new_buffer(gctx, 50);
                fz_append_printf(gctx, nres, template,
                                 mat.a, mat.b, mat.c, mat.d, mat.e, mat.f,
                                 _imgname);
                JM_insert_contents(gctx, pdf, page->obj, nres, overlay);
                fz_drop_buffer(gctx, nres);
            }
            fz_always(gctx)
            {
                fz_drop_image(gctx, image);
                fz_drop_image(gctx, mask);
                fz_drop_pixmap(gctx, pix);
                fz_drop_pixmap(gctx, pm);
                fz_drop_buffer(gctx, imgbuf);
            }
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return_none;
        }

        //---------------------------------------------------------------------
        // Page.refresh()
        //---------------------------------------------------------------------
        FITZEXCEPTION(refresh, !result)
        %feature("autodoc","Refresh page after link/annot/widget updates.") refresh;
        PyObject *refresh()
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            if (!page) return_none;
            fz_try(gctx)
            {
                JM_refresh_link_table(gctx, page);
            }
            fz_catch(gctx)
            {
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
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_document *pdf;
            pdf_obj *resources, *fonts, *font_obj;
            fz_font *font;
            fz_buffer *res = NULL;
            const unsigned char *data = NULL;
            int size, ixref = 0, index = 0, simple = 0;
            PyObject *value;
            PyObject *exto = NULL;
            fz_try(gctx)
            {
                assert_PDF(page);
                pdf = page->doc;
                // get the objects /Resources, /Resources/Font
                resources = pdf_dict_get_inheritable(gctx, page->obj, PDF_NAME(Resources));
                fonts = pdf_dict_get(gctx, resources, PDF_NAME(Font));
                if (!fonts)       // page has no fonts yet
                {
                    fonts = pdf_new_dict(gctx, pdf, 10);
                    pdf_dict_putl_drop(gctx, page->obj, fonts, PDF_NAME(Resources), PDF_NAME(Font), NULL);
                }

                //-------------------------------------------------------------
                // check for CJK font
                //-------------------------------------------------------------
                if (ordering > -1) data = fz_lookup_cjk_font(gctx, ordering, &size, &index);
                if (data)
                {
                    font = fz_new_font_from_memory(gctx, NULL, data, size, index, 0);
                    font_obj = pdf_add_cjk_font(gctx, pdf, font, ordering, wmode, serif);
                    exto = PyUnicode_FromString("n/a");
                    simple = 0;
                    goto weiter;
                }

                //-------------------------------------------------------------
                // check for PDF Base-14 font
                //-------------------------------------------------------------
                if (bfname) data = fz_lookup_base14_font(gctx, bfname, &size);
                if (data)
                {
                    font = fz_new_font_from_memory(gctx, bfname, data, size, 0, 0);
                    font_obj = pdf_add_simple_font(gctx, pdf, font, encoding);
                    exto = PyUnicode_FromString("n/a");
                    simple = 1;
                    goto weiter;
                }

                if (fontfile)
                    font = fz_new_font_from_file(gctx, NULL, fontfile, idx, 0);
                else
                {
                    res = JM_BufferFromBytes(gctx, fontbuffer);
                    if (!res) THROWMSG("need one of fontfile, fontbuffer");
                    font = fz_new_font_from_buffer(gctx, NULL, res, idx, 0);
                }

                if (!set_simple)
                {
                    font_obj = pdf_add_cid_font(gctx, pdf, font);
                    simple = 0;
                }
                else
                {
                    font_obj = pdf_add_simple_font(gctx, pdf, font, encoding);
                    simple = 2;
                }

                weiter: ;
                ixref = pdf_to_num(gctx, font_obj);

                PyObject *name = JM_UNICODE(pdf_to_name(gctx,
                            pdf_dict_get(gctx, font_obj, PDF_NAME(BaseFont))));

                PyObject *subt = JM_UNICODE(pdf_to_name(gctx,
                            pdf_dict_get(gctx, font_obj, PDF_NAME(Subtype))));

                if (!exto)
                    exto = PyUnicode_FromString(fontextension(gctx, pdf, ixref));

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

                // resources and fonts objects will contain named reference to font
                pdf_dict_puts(gctx, fonts, fontname, font_obj);
                pdf_drop_obj(gctx, font_obj);
                fz_drop_font(gctx, font);
            }
            fz_always(gctx)
            {
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return value;
        }

        //---------------------------------------------------------------------
        // Get page transformation matrix
        //---------------------------------------------------------------------
        PARENTCHECK(_getTransformation)
        %feature("autodoc","Return page transformation matrix.") _getTransformation;
        %pythonappend _getTransformation %{val = Matrix(val)%}
        PyObject *_getTransformation()
        {
            fz_matrix ctm = fz_identity;
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            if (!page) return JM_py_from_matrix(ctm);
            fz_try(gctx) pdf_page_transform(gctx, page, NULL, &ctm);
            fz_catch(gctx) {;}
            return JM_py_from_matrix(ctm);
        }

        //---------------------------------------------------------------------
        // Get list of contents objects
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getContents, !result)
        PARENTCHECK(_getContents)
        %feature("autodoc","Return list of /Contents objects as xref integers.") _getContents;
        PyObject *_getContents()
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            PyObject *list = NULL;
            pdf_obj *contents = NULL, *icont = NULL;
            int i, xref;
            size_t n = 0;
            fz_try(gctx)
            {
                assert_PDF(page);           // only works for PDF
                contents = pdf_dict_get(gctx, page->obj, PDF_NAME(Contents));
                if (pdf_is_array(gctx, contents))     // may be several
                {
                    n = pdf_array_len(gctx, contents);
                    list = PyList_New(n);
                    for (i=0; i < pdf_array_len(gctx, contents); i++)
                    {
                        icont = pdf_array_get(gctx, contents, i);
                        xref = pdf_to_num(gctx, icont);
                        PyList_SET_ITEM(list, i, Py_BuildValue("i", xref));
                    }
                }
                else if (contents)          // at most 1 object there
                {
                    list = PyList_New(1);
                    xref = pdf_to_num(gctx, contents);
                    PyList_SET_ITEM(list, 0, Py_BuildValue("i", xref));
                }
            }
            fz_catch(gctx) return NULL;
            if (list)
            {
                return list;
            }
            return PyList_New(0);
        }

        //---------------------------------------------------------------------
        // Set given object as the /Contents of a page
        //---------------------------------------------------------------------
        FITZEXCEPTION(_setContents, !result)
        PARENTCHECK(_setContents)
        %feature("autodoc","Set the /Contents object in page definition") _setContents;
        PyObject *_setContents(int xref = 0)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_obj *contents = NULL;

            fz_try(gctx)
            {
                assert_PDF(page);           // only works for PDF

                if (!INRANGE(xref, 1, pdf_xref_len(gctx, page->doc) - 1))
                    THROWMSG("xref out of range");

                contents = pdf_new_indirect(gctx, page->doc, xref, 0);
                if (!pdf_is_stream(gctx, contents))
                    THROWMSG("xref is not a stream");

                pdf_dict_put_drop(gctx, page->obj, PDF_NAME(Contents), contents);
            }
            fz_catch(gctx) return NULL;
            page->doc->dirty = 1;
            return_none;
        }

        %pythoncode %{
        @property
        def _isWrapped(self):
            """Check if /Contents is wrapped in string pair "q" / "Q".
            """
            xrefs = self._getContents()
            doc = self.parent
            if len(xrefs) == 0:
                return True
            if len(xrefs) == 1:
                cont = doc._getXrefStream(xrefs[0]).split()
                if len(cont) < 1:
                    return True
                if cont[0] != b"q" or cont[-1] != b"Q":
                    return False
                return True
            else:
                cont = doc._getXrefStream(xrefs[0]).split()
                if len(cont) < 1 or cont[0] != b"q":
                    return False
                cont = doc._getXrefStream(xrefs[-1]).split()
                if len(cont) < 1 or cont[-1] != b"Q":
                    return False
                return True

        def _wrapContents(self):
            TOOLS._insert_contents(self, b"q\n", False)
            TOOLS._insert_contents(self, b"\nQ", True)


        def links(self, kinds=None):
            """ Generator over the links of a page."""
            all_links = self.getLinks()
            for link in all_links:
                if kinds is None or link["kind"] in kinds:
                    yield (link)


        def annots(self, types=None):
            """ Generator over the annotations of a page."""
            annot = self.firstAnnot
            while annot:
                if types is None or annot.type[0] in types:
                    yield (annot)
                annot = annot.next


        def widgets(self, types=None):
            """ Generator over the widgets of a page."""
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
            """Return PDF XREF number of page."""
            CheckParent(self)
            return self.parent._getPageXref(self.number)[0]

        def _erase(self):
            self._reset_annot_refs()
            try:
                self.parent._forget_page(self)
            except:
                pass
            if getattr(self, "thisown", True):
                self.__swig_destroy__(self)
            self.parent = None
            self.thisown = False
            self.number = None

        def __del__(self):
            self._erase()

        def getFontList(self, full=False):
            CheckParent(self)
            return self.parent.getPageFontList(self.number, full=full)

        def getImageList(self, full=False):
            CheckParent(self)
            return self.parent.getPageImageList(self.number, full=full)

        @property
        def CropBox(self):
            x0 = self.CropBoxPosition.x
            y0 = self.MediaBoxSize.y - self.CropBoxPosition.y - self.rect.height
            x1 = x0 + self.rect.width
            y1 = y0 + self.rect.height
            return Rect(x0, y0, x1, y1)

        @property
        def MediaBox(self):
            return Rect(0, 0, self.MediaBoxSize)

        %}
    }
};
%clearnodefaultctor;

//-----------------------------------------------------------------------------
// Pixmap
//-----------------------------------------------------------------------------
%rename(Pixmap) fz_pixmap_s;
struct fz_pixmap_s
{
    int x, y, w, h, n;
    int xres, yres;
    %extend {
        ~fz_pixmap_s() {
            DEBUGMSG1("pixmap");
            fz_drop_pixmap(gctx, $self);
            DEBUGMSG2;
        }
        FITZEXCEPTION(fz_pixmap_s, !result)
        //---------------------------------------------------------------------
        // create empty pixmap with colorspace and IRect
        //---------------------------------------------------------------------
        fz_pixmap_s(struct fz_colorspace_s *cs, PyObject *bbox, int alpha = 0)
        {
            fz_pixmap *pm = NULL;
            fz_separations *seps = NULL;
            fz_try(gctx)
                pm = fz_new_pixmap_with_bbox(gctx, cs, JM_irect_from_py(bbox), seps, alpha);
            fz_catch(gctx) return NULL;
            return pm;
        }

        //---------------------------------------------------------------------
        // copy pixmap, converting colorspace
        // New in v1.11: option to remove alpha
        // Changed in v1.13: alpha = 0 does not work since at least v1.12
        //---------------------------------------------------------------------
        fz_pixmap_s(struct fz_colorspace_s *cs, struct fz_pixmap_s *spix)
        {
            fz_pixmap *pm = NULL;
            fz_try(gctx)
            {
                if (!fz_pixmap_colorspace(gctx, spix))
                    THROWMSG("cannot copy pixmap with NULL colorspace");
                fz_color_params color_params = {0};
                pm = fz_convert_pixmap(gctx, spix, cs, NULL, NULL, color_params, 1);
            }
            fz_catch(gctx) return NULL;
            return pm;
        }

        //---------------------------------------------------------------------
        // create pixmap as scaled copy of another one
        //---------------------------------------------------------------------
        fz_pixmap_s(struct fz_pixmap_s *spix, float w, float h, PyObject *clip = NULL)
        {
            fz_pixmap *pm = NULL;
            fz_try(gctx)
            {
                fz_irect bbox = JM_irect_from_py(clip);
                if (!fz_is_infinite_irect(bbox))
                {
                    pm = fz_scale_pixmap(gctx, spix, spix->x, spix->y, w, h, &bbox);
                }
                else
                    pm = fz_scale_pixmap(gctx, spix, spix->x, spix->y, w, h, NULL);
            }
            fz_catch(gctx) return NULL;
            return pm;
        }

        //---------------------------------------------------------------------
        // copy pixmap & add / drop the alpha channel
        //---------------------------------------------------------------------
        fz_pixmap_s(struct fz_pixmap_s *spix, int alpha = 1)
        {
            fz_pixmap *pm = NULL;
            int n, w, h, i;
            fz_separations *seps = NULL;
            fz_try(gctx)
            {
                if (!INRANGE(alpha, 0, 1))
                    THROWMSG("illegal alpha value");
                fz_colorspace *cs = fz_pixmap_colorspace(gctx, spix);
                if (!cs && !alpha)
                    THROWMSG("cannot drop alpha for 'NULL' colorspace");
                n = fz_pixmap_colorants(gctx, spix);
                w = fz_pixmap_width(gctx, spix);
                h = fz_pixmap_height(gctx, spix);
                pm = fz_new_pixmap(gctx, cs, w, h, seps, alpha);
                pm->x = spix->x;
                pm->y = spix->y;
                pm->xres = spix->xres;
                pm->yres = spix->yres;

                // copy samples data ------------------------------------------
                unsigned char *sptr = spix->samples;
                unsigned char *tptr = pm->samples;
                if (spix->alpha == pm->alpha)    // identical samples ---------
                    memcpy(tptr, sptr, w * h * (n + alpha));
                else
                {
                    for (i = 0; i < w * h; i++)
                    {
                        memcpy(tptr, sptr, n);
                        tptr += n;
                        if (pm->alpha)
                        {
                            tptr[0] = 255;
                            tptr++;
                        }
                        sptr += n + spix->alpha;
                    }
                }
            }
            fz_catch(gctx) return NULL;
            return pm;
        }

        //---------------------------------------------------------------------
        // create pixmap from samples data
        //---------------------------------------------------------------------
        fz_pixmap_s(struct fz_colorspace_s *cs, int w, int h, PyObject *samples, int alpha = 0)
        {
            int n = fz_colorspace_n(gctx, cs);
            int stride = (n + alpha)*w;
            fz_separations *seps = NULL;
            fz_buffer *res = NULL;
            fz_pixmap *pm = NULL;
            fz_try(gctx)
            {
                size_t size = 0;
                unsigned char *c = NULL;
                res = JM_BufferFromBytes(gctx, samples);
                if (!res) THROWMSG("bad samples data");
                size = fz_buffer_storage(gctx, res, &c);
                if (stride * h != size) THROWMSG("bad samples length");
                pm = fz_new_pixmap(gctx, cs, w, h, seps, alpha);
                memcpy(pm->samples, c, size);
            }
            fz_always(gctx)
            {
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx)
            {
                return NULL;
            }
            return pm;
        }

        //---------------------------------------------------------------------
        // create pixmap from filename
        //---------------------------------------------------------------------
        fz_pixmap_s(char *filename)
        {
            fz_image *img = NULL;
            fz_pixmap *pm = NULL;
            fz_try(gctx) {
                img = fz_new_image_from_file(gctx, filename);
                pm = fz_get_pixmap_from_image(gctx, img, NULL, NULL, NULL, NULL);
            }
            fz_always(gctx)
            {
                fz_drop_image(gctx, img);
            }
            fz_catch(gctx)
            {
                return NULL;
            }
            return pm;
        }

        //---------------------------------------------------------------------
        // create pixmap from in-memory image
        //---------------------------------------------------------------------
        fz_pixmap_s(PyObject *imagedata)
        {
            fz_buffer *res = NULL;
            fz_image *img = NULL;
            fz_pixmap *pm = NULL;
            fz_try(gctx)
            {
                res = JM_BufferFromBytes(gctx, imagedata);
                if (!res) THROWMSG("bad image data");
                img = fz_new_image_from_buffer(gctx, res);
                pm = fz_get_pixmap_from_image(gctx, img, NULL, NULL, NULL, NULL);
            }
            fz_always(gctx)
            {
                fz_drop_image(gctx, img);
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) return NULL;
            return pm;
        }

        //---------------------------------------------------------------------
        // Create pixmap from PDF image identified by XREF number
        //---------------------------------------------------------------------
        fz_pixmap_s(struct fz_document_s *doc, int xref)
        {
            fz_image *img = NULL;
            fz_pixmap *pix = NULL;
            pdf_obj *ref = NULL;
            pdf_obj *type;
            pdf_document *pdf = pdf_specifics(gctx, doc);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if (!INRANGE(xref, 1, xreflen-1))
                    THROWMSG("xref out of range");
                ref = pdf_new_indirect(gctx, pdf, xref, 0);
                type = pdf_dict_get(gctx, ref, PDF_NAME(Subtype));
                if (!pdf_name_eq(gctx, type, PDF_NAME(Image)))
                    THROWMSG("xref not an image");
                img = pdf_load_image(gctx, pdf, ref);
                pix = fz_get_pixmap_from_image(gctx, img, NULL, NULL, NULL, NULL);
            }
            fz_always(gctx)
            {
                fz_drop_image(gctx, img);
                pdf_drop_obj(gctx, ref);
            }
            fz_catch(gctx)
            {
                fz_drop_pixmap(gctx, pix);
                return NULL;
            }
            return pix;
        }

        //---------------------------------------------------------------------
        // shrink
        //---------------------------------------------------------------------
        void shrink(int factor)
        {
            if (factor < 1)
            {
                JM_Warning("ignoring shrink factor < 1");
                return;
            }
            fz_subsample_pixmap(gctx, $self, factor);
        }

        //---------------------------------------------------------------------
        // apply gamma correction
        //---------------------------------------------------------------------
        void gammaWith(float gamma)
        {
            if (!fz_pixmap_colorspace(gctx, $self))
            {
                JM_Warning("colorspace invalid for function");
                return;
            }
            fz_gamma_pixmap(gctx, $self, gamma);
        }

        //---------------------------------------------------------------------
        // tint pixmap with color
        //---------------------------------------------------------------------
        %pythonprepend tintWith%{
            if not self.colorspace or self.colorspace.n > 3:
                print("warning: colorspace invalid for function")
                return%}
        void tintWith(int black, int white)
        {
            fz_tint_pixmap(gctx, $self, black, white);
        }

        //----------------------------------------------------------------------
        // clear all of pixmap samples to 0x00 */
        //----------------------------------------------------------------------
        void clearWith()
        {
            fz_clear_pixmap(gctx, $self);
        }

        //----------------------------------------------------------------------
        // clear total pixmap with value */
        //----------------------------------------------------------------------
        void clearWith(int value)
        {
            fz_clear_pixmap_with_value(gctx, $self, value);
        }

        //----------------------------------------------------------------------
        // clear pixmap rectangle with value
        //----------------------------------------------------------------------
        void clearWith(int value, PyObject *bbox)
        {
            JM_clear_pixmap_rect_with_value(gctx, $self, value, JM_irect_from_py(bbox));
        }

        //----------------------------------------------------------------------
        // copy pixmaps
        //----------------------------------------------------------------------
        FITZEXCEPTION(copyPixmap, !result)
        PyObject *copyPixmap(struct fz_pixmap_s *src, PyObject *bbox)
        {
            fz_try(gctx)
            {
                if (!fz_pixmap_colorspace(gctx, src))
                    THROWMSG("cannot copy pixmap with NULL colorspace");
                if ($self->alpha != src->alpha)
                    THROWMSG("source and target alpha must be equal");
                fz_copy_pixmap_rect(gctx, $self, src, JM_irect_from_py(bbox), NULL);
            }
            fz_catch(gctx) return NULL;
            return_none;
        }

        //----------------------------------------------------------------------
        // set alpha values
        //----------------------------------------------------------------------
        FITZEXCEPTION(setAlpha, !result)
        PyObject *setAlpha(PyObject *alphavalues=NULL)
        {
            fz_buffer *res = NULL;
            fz_try(gctx)
            {
                if ($self->alpha == 0) THROWMSG("pixmap has no alpha");
                int n = fz_pixmap_colorants(gctx, $self);
                int w = fz_pixmap_width(gctx, $self);
                int h = fz_pixmap_height(gctx, $self);
                int balen = w * h * (n+1);
                unsigned char *data = NULL;
                int data_len = 0;
                if (alphavalues)
                {
                    res = JM_BufferFromBytes(gctx, alphavalues);
                    if (res)
                    {
                        data_len = (int) fz_buffer_storage(gctx, res, &data);
                        if (data && data_len < w * h)
                            THROWMSG("not enough alpha values");
                    }
                    else THROWMSG("bad type: 'alphavalues'");
                }
                int i = 0, k = 0;
                while (i < balen)
                {
                    if (data_len) $self->samples[i+n] = data[k];
                    else          $self->samples[i+n] = 255;
                    i += n+1;
                    k += 1;
                }
            }
            fz_always(gctx)
            {
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx)
            {
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
            fz_try(gctx)
            {
                size_t size = fz_pixmap_stride(gctx, $self) * $self->h;
                res = fz_new_buffer(gctx, size);
                out = fz_new_output_with_buffer(gctx, res);

                switch(format)
                {
                    case(1):
                        fz_write_pixmap_as_png(gctx, out, $self);
                        break;
                    case(2):
                        fz_write_pixmap_as_pnm(gctx, out, $self);
                        break;
                    case(3):
                        fz_write_pixmap_as_pam(gctx, out, $self);
                        break;
                    case(5):           // Adobe Photoshop Document
                        fz_write_pixmap_as_psd(gctx, out, $self);
                        break;
                    case(6):           // Postscript format
                        fz_write_pixmap_as_ps(gctx, out, $self);
                        break;
                    default:
                        fz_write_pixmap_as_png(gctx, out, $self);
                        break;
                }
                barray = JM_BinFromBuffer(gctx, res);
            }
            fz_always(gctx)
            {
                fz_drop_output(gctx, out);
                fz_drop_buffer(gctx, res);
            }

            fz_catch(gctx)
            {
                return NULL;
            }
            return barray;
        }

        %pythoncode %{
def getImageData(self, output="png"):
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
    barray = self._getImageData(1)
    return barray

def getPNGData(self):
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
                switch(format)
                {
                    case(1):
                        fz_save_pixmap_as_png(gctx, $self, filename);
                        break;
                    case(2):
                        fz_save_pixmap_as_pnm(gctx, $self, filename);
                        break;
                    case(3):
                        fz_save_pixmap_as_pam(gctx, $self, filename);
                        break;
                    case(5): // Adobe Photoshop Document
                        fz_save_pixmap_as_psd(gctx, $self, filename);
                        break;
                    case(6): // Postscript
                        fz_save_pixmap_as_ps(gctx, $self, filename, 0);
                        break;
                    default:
                        fz_save_pixmap_as_png(gctx, $self, filename);
                        break;
                }
            }
            fz_catch(gctx) return NULL;
            return_none;
        }
        %pythoncode %{
def writeImage(self, filename, output=None):
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

def writePNG(self, filename, savealpha = -1):
    return self._writeIMG(filename, 1)

        %}
        //----------------------------------------------------------------------
        // invertIRect
        //----------------------------------------------------------------------
        PyObject *invertIRect(PyObject *irect = NULL)
        {
            if (!fz_pixmap_colorspace(gctx, $self))
                {
                    JM_Warning("ignored for stencil pixmap");
                    return JM_BOOL(0);
                }

            fz_irect r = JM_irect_from_py(irect);
            if (fz_is_infinite_irect(r))
                r = fz_pixmap_bbox(gctx, $self);

            return JM_BOOL(JM_invert_pixmap_rect(gctx, $self, r));
        }

        //----------------------------------------------------------------------
        // get one pixel as a list
        //----------------------------------------------------------------------
        FITZEXCEPTION(pixel, !result)
        %feature("autodoc","Return the pixel at (x,y) as a list. Last item is the alpha if Pixmap.alpha is true.") pixel;
        PyObject *pixel(int x, int y)
        {
            PyObject *p = NULL;
            fz_try(gctx)
            {
                if (!INRANGE(x, 0, $self->w - 1) || !INRANGE(y, 0, $self->h - 1))
                    THROWMSG("coordinates outside image");
                int n = $self->n;
                int stride = fz_pixmap_stride(gctx, $self);
                int j, i = stride * y + n * x;
                p = PyList_New(n);
                for (j = 0; j < n; j++)
                {
                    PyList_SET_ITEM(p, j, Py_BuildValue("i", $self->samples[i + j]));
                }
            }
            fz_catch(gctx) return NULL;
            return p;
        }

        //----------------------------------------------------------------------
        // Set one pixel to a given color tuple
        //----------------------------------------------------------------------
        FITZEXCEPTION(setPixel, !result)
        %feature("autodoc","Set the pixel at (x,y) to the integers in sequence 'color'.") setPixel;
        PyObject *setPixel(int x, int y, PyObject *color)
        {
            fz_try(gctx)
            {
                if (!INRANGE(x, 0, $self->w - 1) || !INRANGE(y, 0, $self->h - 1))
                    THROWMSG("outside image");
                int n = $self->n;
                if (!PySequence_Check(color) || PySequence_Size(color) != n)
                    THROWMSG("bad color arg");
                int i, j;
                unsigned char c[5];
                for (j = 0; j < n; j++)
                {
                    i = (int) PyInt_AsLong(PySequence_ITEM(color, j));
                    if (!INRANGE(i, 0, 255)) THROWMSG("bad pixel component");
                    c[j] = (unsigned char) i;
                }
                int stride = fz_pixmap_stride(gctx, $self);
                i = stride * y + n * x;
                for (j = 0; j < n; j++)
                {
                    $self->samples[i + j] = c[j];
                }
            }
            fz_catch(gctx)
            {
                PyErr_Clear();
                return NULL;
            }
            return_none;
        }

        //----------------------------------------------------------------------
        // Set a rect to a given color tuple
        //----------------------------------------------------------------------
        FITZEXCEPTION(setRect, !result)
        %feature("autodoc","Set a rectangle to the integers in sequence 'color'.") setRect;
        PyObject *setRect(PyObject *irect, PyObject *color)
        {
            PyObject *rc = JM_BOOL(0);
            fz_try(gctx)
            {
                int n = $self->n;
                if (!PySequence_Check(color) || PySequence_Size(color) != n)
                    THROWMSG("bad color arg");
                int i, j;
                unsigned char c[5];
                for (j = 0; j < n; j++)
                {
                    i = (int) PyInt_AsLong(PySequence_ITEM(color, j));
                    if (!INRANGE(i, 0, 255)) THROWMSG("bad color component");
                    c[j] = (unsigned char) i;
                }
                i = JM_fill_pixmap_rect_with_color(gctx, $self, c, JM_irect_from_py(irect));
                rc = JM_BOOL(i);
            }
            fz_catch(gctx)
            {
                PyErr_Clear();
                return NULL;
            }
            return rc;
        }

        //----------------------------------------------------------------------
        // get length of one image row
        //----------------------------------------------------------------------
        %pythoncode %{@property%}
        int stride()
        {
            return fz_pixmap_stride(gctx, $self);
        }

        //----------------------------------------------------------------------
        // check alpha channel
        //----------------------------------------------------------------------
        %pythoncode %{@property%}
        int alpha()
        {
            return $self->alpha;
        }

        //----------------------------------------------------------------------
        // get colorspace of pixmap
        //----------------------------------------------------------------------
        %pythoncode %{@property%}
        struct fz_colorspace_s *colorspace()
        {
            return fz_pixmap_colorspace(gctx, $self);
        }

        //----------------------------------------------------------------------
        // return irect of pixmap
        //----------------------------------------------------------------------
        %pythoncode %{@property%}
        %pythonappend irect %{val = IRect(val)%}
        PyObject *irect()
        {
            return JM_py_from_irect(fz_pixmap_bbox(gctx, $self));
        }

        //----------------------------------------------------------------------
        // return size of pixmap
        //----------------------------------------------------------------------
        %pythoncode %{@property%}
        int size()
        {
            return (int) fz_pixmap_size(gctx, $self);
        }

        //----------------------------------------------------------------------
        // samples
        //----------------------------------------------------------------------
        %pythoncode %{@property%}
        PyObject *samples()
        {
            return PyBytes_FromStringAndSize((const char *)$self->samples, (Py_ssize_t) ($self->w)*($self->h)*($self->n));
        }

        %pythoncode %{
            width  = w
            height = h

            def __len__(self):
                return self.size

            def __repr__(self):
                if not type(self) is Pixmap: return
                if self.colorspace:
                    return "fitz.Pixmap(%s, %s, %s)" % (self.colorspace.name, self.irect, self.alpha)
                else:
                    return "fitz.Pixmap(%s, %s, %s)" % ('None', self.irect, self.alpha)%}
        %pythoncode %{
        def __del__(self):
            if not type(self) is Pixmap: return
            self.__swig_destroy__(self)
        %}
    }
};

/* fz_colorspace */
%rename(Colorspace) fz_colorspace_s;
struct fz_colorspace_s
{
    %extend {
        ~fz_colorspace_s()
        {
            DEBUGMSG1("colorspace");
            fz_drop_colorspace(gctx, $self);
            DEBUGMSG2;
        }

        fz_colorspace_s(int type)
        {
            switch(type) {
                case CS_GRAY:
                    return fz_device_gray(gctx);
                    break;
                case CS_CMYK:
                    return fz_device_cmyk(gctx);
                    break;
                case CS_RGB:
                default:
                    return fz_device_rgb(gctx);
                    break;
            }
        }
        //----------------------------------------------------------------------
        // number of bytes to define color of one pixel
        //----------------------------------------------------------------------
        %pythoncode %{@property%}
        PyObject *n()
        {
            return Py_BuildValue("i", fz_colorspace_n(gctx, $self));
        }

        //----------------------------------------------------------------------
        // name of colorspace
        //----------------------------------------------------------------------
        PyObject *_name()
        {
            return PyUnicode_FromString(fz_colorspace_name(gctx, $self));
        }

        %pythoncode %{
        @property
        def name(self):
            if self.n == 1:
                return csGRAY._name()
            elif self.n == 3:
                return csRGB._name()
            elif self.n == 4:
                return csCMYK._name()
            return self._name()

        def __repr__(self):
            x = ("", "GRAY", "", "RGB", "CMYK")[self.n]
            return "fitz.Colorspace(fitz.CS_%s) - %s" % (x, self.name)
        %}
    }
};


/* fz_device wrapper */
%rename(Device) DeviceWrapper;
struct DeviceWrapper
{
    %extend {
        FITZEXCEPTION(DeviceWrapper, !result)
        DeviceWrapper(struct fz_pixmap_s *pm, PyObject *clip) {
            struct DeviceWrapper *dw = NULL;
            fz_try(gctx) {
                dw = (struct DeviceWrapper *)calloc(1, sizeof(struct DeviceWrapper));
                fz_irect bbox = JM_irect_from_py(clip);
                if (fz_is_infinite_irect(bbox))
                    dw->device = fz_new_draw_device(gctx, fz_identity, pm);
                else
                    dw->device = fz_new_draw_device_with_bbox(gctx, fz_identity, pm, &bbox);
            }
            fz_catch(gctx) return NULL;
            return dw;
        }
        DeviceWrapper(struct fz_display_list_s *dl) {
            struct DeviceWrapper *dw = NULL;
            fz_try(gctx) {
                dw = (struct DeviceWrapper *)calloc(1, sizeof(struct DeviceWrapper));
                dw->device = fz_new_list_device(gctx, dl);
                dw->list = dl;
                fz_keep_display_list(gctx, dl);
            }
            fz_catch(gctx) return NULL;
            return dw;
        }
        DeviceWrapper(struct fz_stext_page_s *tp, int flags = 0) {
            struct DeviceWrapper *dw = NULL;
            fz_try(gctx) {
                dw = (struct DeviceWrapper *)calloc(1, sizeof(struct DeviceWrapper));
                fz_stext_options opts = { 0 };
                opts.flags = flags;
                dw->device = fz_new_stext_device(gctx, tp, &opts);
            }
            fz_catch(gctx) return NULL;
            return dw;
        }
        ~DeviceWrapper() {
            fz_display_list *list = $self->list;
            DEBUGMSG1("device");
            fz_close_device(gctx, $self->device);
            fz_drop_device(gctx, $self->device);
            DEBUGMSG2;
            if(list)
            {
                DEBUGMSG1("display list after device");
                fz_drop_display_list(gctx, list);
                DEBUGMSG2;
            }
        }
    }
};

//-----------------------------------------------------------------------------
// fz_outline
//-----------------------------------------------------------------------------
%rename(Outline) fz_outline_s;
%nodefaultctor;
struct fz_outline_s {
    %immutable;
    char *title;
    int page;
    struct fz_outline_s *next;
    struct fz_outline_s *down;
    int is_open;
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
        ~fz_outline_s()
        {
            DEBUGMSG1("outline");
            fz_drop_outline(gctx, $self);
            DEBUGMSG2;
        }
    }
*/
    %extend {
        %pythoncode %{@property%}
        %pythonappend uri %{
        if val:
            nval = "".join([c for c in val if 32 <= ord(c) <= 127])
            val = nval
        else:
            val = ""
        %}
        PyObject *uri()
        {
            return JM_UNICODE($self->uri);
        }

        %pythoncode %{@property%}
        PyObject *isExternal()
        {
            if (!$self->uri) Py_RETURN_FALSE;
            return JM_BOOL(fz_is_external_link(gctx, $self->uri));
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
%rename(Annot) pdf_annot_s;
%nodefaultctor;
struct pdf_annot_s
{
    %extend
    {
        ~pdf_annot_s()
        {
            DEBUGMSG1("annot");
            pdf_drop_annot(gctx, $self);
            DEBUGMSG2;
        }
        //---------------------------------------------------------------------
        // annotation rectangle
        //---------------------------------------------------------------------
        PARENTCHECK(rect)
        %feature("autodoc","Rectangle containing the annot") rect;
        %pythoncode %{@property%}
        %pythonappend rect %{val = Rect(val)%}
        PyObject *rect()
        {
            fz_rect r = pdf_bound_annot(gctx, $self);
            return JM_py_from_rect(r);
        }

        //---------------------------------------------------------------------
        // annotation get xref number
        //---------------------------------------------------------------------
        PARENTCHECK(_getXref)
        %feature("autodoc","Xref number of annotation") _getXref;
        %pythoncode %{@property%}
        PyObject *xref()
        {
            int i = pdf_to_num(gctx, $self->obj);
            return Py_BuildValue("i", i);
        }

        //---------------------------------------------------------------------
        // annotation get decompressed appearance stream source
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getAP, !result)
        %feature("autodoc","Get contents source of a PDF annot") _getAP;
        PyObject *_getAP()
        {
            PyObject *r = Py_None;
            fz_buffer *res = NULL;
            fz_try(gctx)
            {
                pdf_obj *ap = pdf_dict_getl(gctx, $self->obj, PDF_NAME(AP),
                                              PDF_NAME(N), NULL);

                if (pdf_is_stream(gctx, ap))  res = pdf_load_stream(gctx, ap);
                if (res) r = JM_BinFromBuffer(gctx, res);
            }
            fz_always(gctx) fz_drop_buffer(gctx, res);
            fz_catch(gctx) return_none;
            return r;
        }

        //---------------------------------------------------------------------
        // annotation update /AP stream
        //---------------------------------------------------------------------
        FITZEXCEPTION(_setAP, !result)
        %feature("autodoc","Update contents source of a PDF annot") _setAP;
        PyObject *_setAP(PyObject *ap, int rect = 0)
        {
            fz_buffer *res = NULL;
            fz_var(res);
            fz_try(gctx)
            {
                pdf_obj *apobj = pdf_dict_getl(gctx, $self->obj, PDF_NAME(AP),
                                              PDF_NAME(N), NULL);
                if (!apobj) THROWMSG("annot has no /AP/N object");
                if (!pdf_is_stream(gctx, apobj))
                    THROWMSG("/AP/N object is no stream");
                res = JM_BufferFromBytes(gctx, ap);
                if (!res) THROWMSG("invalid /AP stream argument");
                JM_update_stream(gctx, $self->page->doc, apobj, res, 1);
                if (rect)
                {
                    fz_rect bbox = pdf_dict_get_rect(gctx, $self->obj, PDF_NAME(Rect));
                    pdf_dict_put_rect(gctx, apobj, PDF_NAME(BBox), bbox);
                    $self->ap = NULL;
                }
            }
            fz_always(gctx)
                fz_drop_buffer(gctx, res);
            fz_catch(gctx) return NULL;
            return_none;
        }

        //---------------------------------------------------------------------
        // annotation set name
        //---------------------------------------------------------------------
        PARENTCHECK(setName)
        %feature("autodoc","Set the (icon) name") setName;
        PyObject *setName(char *name)
        {
            fz_try(gctx)
            {
                pdf_dict_put_name(gctx, $self->obj, PDF_NAME(Name), name);
                pdf_dirty_annot(gctx, $self);
            }
            fz_catch(gctx)
            {
                return NULL;
            }
            return_none;
        }

        //---------------------------------------------------------------------
        // annotation set rectangle
        //---------------------------------------------------------------------
        PARENTCHECK(setRect)
        %feature("autodoc","Set the rectangle") setRect;
        PyObject *setRect(PyObject *rect)
        {
            fz_try(gctx)
            {
                pdf_set_annot_rect(gctx, $self, JM_rect_from_py(rect));
            }
            fz_catch(gctx)
            {
                return NULL;
            }
            return_none;
        }

        //---------------------------------------------------------------------
        // annotation vertices (for "Line", "Polgon", "Ink", etc.
        //---------------------------------------------------------------------
        PARENTCHECK(vertices)
        %feature("autodoc","Point coordinates for various annot types") vertices;
        %pythoncode %{@property%}
        PyObject *vertices()
        {
            PyObject *res = Py_None;
            pdf_obj *o;
            //----------------------------------------------------------------
            // The following objects occur in different annotation types.
            // So we are sure that o != NULL occurs at most once.
            // Every pair of floats is one point, that needs to be separately
            // transformed with the page transformation matrix.
            //----------------------------------------------------------------
            o = pdf_dict_get(gctx, $self->obj, PDF_NAME(Vertices));
            if (o) goto weiter;
            o = pdf_dict_get(gctx, $self->obj, PDF_NAME(L));
            if (o) goto weiter;
            o = pdf_dict_get(gctx, $self->obj, PDF_NAME(QuadPoints));
            if (o) goto weiter;
            o = pdf_dict_gets(gctx, $self->obj, "CL");
            if (o) goto weiter;
            o = pdf_dict_get(gctx, $self->obj, PDF_NAME(InkList));
            if (o) goto weiter;
            return res;

            weiter:;
            int i, n;
            fz_point point;             // point object to work with
            fz_matrix page_ctm;         // page transformation matrix
            pdf_page_transform(gctx, $self->page, NULL, &page_ctm);
            res = PyList_New(0);        // create Python list
            n = pdf_array_len(gctx, o);
            for (i = 0; i < n; i += 2)
            {
                point.x = pdf_to_real(gctx, pdf_array_get(gctx, o, i));
                point.y = pdf_to_real(gctx, pdf_array_get(gctx, o, i+1));
                point = fz_transform_point(point, page_ctm);
                LIST_APPEND_DROP(res,  Py_BuildValue("ff", point.x, point.y));
            }

            return res;
        }

        //---------------------------------------------------------------------
        // annotation colors
        //---------------------------------------------------------------------
        PARENTCHECK(colors)
        %feature("autodoc","dictionary of the annot's colors") colors;
        %pythoncode %{@property%}
        PyObject *colors()
        {
            return JM_annot_colors(gctx, $self->obj);
        }

        //---------------------------------------------------------------------
        // annotation update appearance
        //---------------------------------------------------------------------
        PyObject *_update_appearance(char *opacity=NULL,
                                     PyObject *fill_color=NULL,
                                     int rotate = -1)
        {
            int type = pdf_annot_type(gctx, $self);
            float fcol[4] = {1,1,1,1};  // fill color: white
            int nfcol = 0;
            JM_color_FromSequence(fill_color, &nfcol, fcol);
            fz_try(gctx)
            {
                pdf_dirty_annot(gctx, $self); // enforce MuPDF /AP formatting
                if (type == PDF_ANNOT_FREE_TEXT)
                {
                    if (rotate >= 0)
                    {
                        pdf_dict_put_int(gctx, $self->obj, PDF_NAME(Rotate), rotate);
                    }
                    if (EXISTS(fill_color))
                    {
                        pdf_set_annot_color(gctx, $self, nfcol, fcol); // fill color
                    }
                }
                $self->needs_new_ap = 1;  // force re-creation of appearance stream
                pdf_update_annot(gctx, $self);  // update the annotation
                pdf_clean_annot_contents(gctx, $self->page->doc, $self,
                                         NULL, NULL, NULL, 1, 0);
            }
            fz_catch(gctx)
            {
                PySys_WriteStderr("cannot update annot: '%s'\n", fz_caught_message(gctx));
                Py_RETURN_FALSE;
            }

            if (!opacity)  // no opacity given ==> we are done
            {
                Py_RETURN_TRUE;
            }
            fz_try(gctx)  // we need to create an /ExtGState object
            {
                pdf_obj *ap = pdf_dict_getl(gctx, $self->obj, PDF_NAME(AP),
                                        PDF_NAME(N), NULL);
                if (!ap)
                {
                    THROWMSG("annot has no /AP object");
                }
                pdf_obj *ca = pdf_dict_get(gctx, $self->obj, PDF_NAME(CA));
                pdf_obj *alp0 = pdf_new_dict(gctx, $self->page->doc, 3);
                pdf_dict_put(gctx, alp0, PDF_NAME(Type), PDF_NAME(ExtGState));
                pdf_dict_put(gctx, alp0, PDF_NAME(CA), ca);
                pdf_dict_put(gctx, alp0, PDF_NAME(ca), ca);
                pdf_obj *extg = pdf_dict_getl(gctx, ap, PDF_NAME(Resources),
                                              PDF_NAME(ExtGState), NULL);
                if (!extg)
                {
                    extg = pdf_new_dict(gctx, $self->page->doc, 2);
                    pdf_dict_puts_drop(gctx, extg, opacity, alp0);
                    pdf_dict_putl_drop(gctx, ap, extg, PDF_NAME(Resources), PDF_NAME(ExtGState), NULL);
                }
                else
                {
                    pdf_dict_puts_drop(gctx, extg, opacity, alp0);
                }
                pdf_dict_putl_drop(gctx, $self->obj, ap, PDF_NAME(AP), PDF_NAME(N), NULL);
                $self->ap = NULL;
            }

            fz_catch(gctx)
            {
                PySys_WriteStderr("could not store opacity\n");
                Py_RETURN_FALSE;
            }
            Py_RETURN_TRUE;
        }


        %pythoncode %{
        def update(self,
                   fontsize=0,
                   fontname=None,
                   text_color=None,
                   border_color=None,
                   fill_color=None,
                   rotate=-1,
                   ):

            """
            The following code fixes shortcomings of MuPDF's "pdf_update_annot"
            function. Currently these are:
            1. Opacity (all annots). MuPDF ignores this proprty. This requires
            to add an ExtGState (extended graphics state) object in the
            C code as well.
            2. Dashing (all annots). MuPDF ignores this proprty.
            3. Colors and font size for FreeText annotations.
            4. Line end icons also for POLYGON and POLY_LINE annotations.
            MuPDF only honors them for LINE annotations.
            5. Always perform a "clean" for the annot, because MuPDF does not
            enclose the contents syntax in a string pair "q ... Q", which may
            cause Adobe and other readers not to display the annot.
            """
            CheckParent(self)
            def color_string(cs, code):
                """Return valid PDF color operator for a given color sequence.
                """
                if cs is None or cs == "":
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
            if fill_color is not None:  # get the fill color
                fill = fill_color
            else:
                fill = self.colors["fill"]

            rect = self.rect  # prevent MuPDF fiddling with it

            # Opacity not handled by MuPDF, so we do it here
            if 0 <= self.opacity < 1:
                opacity = "opacity%i" % int(round(self.opacity * 100))
                opa_code = "/%s + gs\n" % opacity
            else:
                opacity = None
                opa_code = None

            # now invoke MuPDF annot appearance update
            val = self._update_appearance(opacity, fill, rotate)
            if not val:  # something went wrong, skip the rest
                return val

            self.setRect(rect)  # re-establish in case MuPDF changed it
            rect = None  # used if we change the rect here
            bfill = color_string(fill, "f")
            p_ctm = self.parent._getTransformation()  # page transformation matrix
            imat = ~p_ctm  # inverse page transf. matrix
            if dt:
                dashes = "[" + " ".join(map(str, dt)) + "] d\n"
                dashes = dashes.encode("utf-8")
            else:
                dashes = None

            if self.lineEnds:
                line_end_le, line_end_ri = self.lineEnds
            else:
                line_end_le, line_end_ri = 0, 0  # init line end codes

            ap = self._getAP()  # get the annot operator source
            ap_tab = ap.splitlines()[1:-1]  # temporary remove of 'q ...Q'
            ap = b"\n".join(ap_tab)
            ap_updated = False  # assume we did nothing

            if type == PDF_ANNOT_FREE_TEXT:
                CheckColor(border_color)
                CheckColor(text_color)

                # read and update default appearance as necessary
                update_default_appearance = False
                tcol, fname, fsize = TOOLS._parse_da(self)
                if fname.lower() not in ("helv", "cour", "tiro", "zadb", "symb"):
                    fname = "Helv"
                    update_default_appearance = True
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
                
                if border_color is not None:
                    for i, item in enumerate(ap_tab):
                        if not item.endswith(b" w"):
                            continue
                        idx = i + 2  # step into wrong border color spec
                        ap_tab[i + 2] = color_string(border_color, "s")
                        break

                if dashes is not None:  # handle dashes
                    ap_tab.insert(0, dashes)
                    dashes = None

                ap = b"\n".join(ap_tab)         # updated AP stream
                ap_updated = True

            if bfill != "":
                if type == PDF_ANNOT_POLYGON:
                    ap = ap[:-1] + bfill + b"b"  # close, fill, and stroke
                    ap_updated = True
                elif type == PDF_ANNOT_POLYLINE:
                    ap = ap[:-1] + bfill + b"B"  # fill and stroke
                    ap_updated = True

            # Dashes not handled by MuPDF, so we do it here.
            if dashes is not None:
                ap = dashes + ap
                # reset dashing - only applies for LINE annots with line ends given
                ap = ap.replace(b"\nS\n", b"\nS\n[] d\n", 1)
                ap_updated = True

            if opa_code:
                ap = opa_code.encode("utf-8") + ap
                ap_updated = True

            #----------------------------------------------------------------------
            # the following handles line end symbols for 'Polygon' and 'Polyline'
            #----------------------------------------------------------------------
            if max(line_end_le, line_end_ri) > 0 and type in (PDF_ANNOT_POLYGON, PDF_ANNOT_POLYLINE):

                le_funcs = (None, TOOLS._le_square, TOOLS._le_circle,
                            TOOLS._le_diamond, TOOLS._le_openarrow,
                            TOOLS._le_closedarrow, TOOLS._le_butt,
                            TOOLS._le_ropenarrow, TOOLS._le_rclosedarrow,
                            TOOLS._le_slash)
                le_funcs_range = range(1, len(le_funcs))
                d = 4 * max(1, self.border["width"])
                rect = self.rect + (-d, -d, d, d)
                ap_updated = True
                points = self.vertices
                ap = b"q\n" + ap + b"\nQ\n"
                if line_end_le in le_funcs_range:
                    p1 = Point(points[0]) * imat
                    p2 = Point(points[1]) * imat
                    left = le_funcs[line_end_le](self, p1, p2, False)
                    ap += bytes(left, "utf8") if not fitz_py2 else left
                if line_end_ri in le_funcs_range:
                    p1 = Point(points[-2]) * imat
                    p2 = Point(points[-1]) * imat
                    left = le_funcs[line_end_ri](self, p1, p2, True)
                    ap += bytes(left, "utf8") if not fitz_py2 else left

            if ap_updated:
                if rect:                        # rect modified here?
                    self.setRect(rect)
                    self._setAP(ap, rect = 1)
                else:
                    self._setAP(ap, rect = 0)

            # always perform a clean to wrap stream by "q" / "Q"
            self._cleanContents()
        %}

        //---------------------------------------------------------------------
        // annotation set colors
        //---------------------------------------------------------------------
        %feature("autodoc","setColors(dict)\nChanges the 'stroke' and 'fill' colors of an annotation. If provided, values must be sequences of up to 4 floats.") setColors;
        %pythonprepend setColors %{
        CheckParent(self)
        if type(colors) is not dict:
            colors = {"fill": fill, "stroke": stroke}
        %}
        void setColors(PyObject *colors=NULL, PyObject *fill=NULL, PyObject *stroke=NULL)
        {
            if (!PyDict_Check(colors)) return;
            PyObject *ccol, *icol;
            ccol = PyDict_GetItem(colors, dictkey_stroke);
            icol = PyDict_GetItem(colors, dictkey_fill);
            int i, n;
            float col[4];
            n = 0;
            if (ccol)
                if (PySequence_Check(ccol))
                    n = (int) PySequence_Size(ccol);
            if (n>0)
            {
                for (i=0; i<n; i++)
                    col[i] = (float) PyFloat_AsDouble(PySequence_ITEM(ccol, i));
                fz_try(gctx)
                    pdf_set_annot_color(gctx, $self, n, col);
                fz_catch(gctx)
                    JM_Warning("cannot set stroke color for this annot type");
            }
            n = 0;
            if (icol)
                if (PySequence_Check(icol))
                    n = (int) PySequence_Size(icol);
            if (n>0)
            {
                if (!pdf_annot_has_interior_color(gctx, $self))
                {
                    JM_Warning("annot type has no fill color");
                    return;
                }
                for (i=0; i<n; i++)
                    col[i] = (float) PyFloat_AsDouble(PySequence_ITEM(icol, i));
                fz_try(gctx)
                    pdf_set_annot_interior_color(gctx, $self, n, col);
                fz_catch(gctx)
                    JM_Warning("cannot set fill color for this annot type");
            }
            return;
        }

        //---------------------------------------------------------------------
        // annotation lineEnds
        //---------------------------------------------------------------------
        PARENTCHECK(lineEnds)
        %pythoncode %{@property%}
        PyObject *lineEnds()
        {
            int i = pdf_annot_type(gctx, $self);
            // return nothing for invalid annot types
            if (!INRANGE(i, 2, 7)) return_none;
            if (INRANGE(i, 4, 5)) return_none;
            PyObject *res = Py_BuildValue("[ii]", 0, 0); // standard
            pdf_obj *o = pdf_dict_gets(gctx, $self->obj, "LE");
            if (!o) return res;                       // no LE: empty dict
            char *lstart = NULL;
            char *lend = NULL;
            if (pdf_is_name(gctx, o)) lstart = (char *) pdf_to_name(gctx, o);
            else if (pdf_is_array(gctx, o))
                {
                lstart = (char *) pdf_to_name(gctx, pdf_array_get(gctx, o, 0));
                if (pdf_array_len(gctx, o) > 1)
                    lend   = (char *) pdf_to_name(gctx, pdf_array_get(gctx, o, 1));
                }
            PyList_SetItem(res, 0, Py_BuildValue("i", JM_le_value(gctx, lstart)));
            PyList_SetItem(res, 1, Py_BuildValue("i", JM_le_value(gctx, lend)));
            return res;
        }

        //---------------------------------------------------------------------
        // annotation set line ends
        //---------------------------------------------------------------------
        PARENTCHECK(setLineEnds)
        void setLineEnds(int start, int end)
        {
            if (pdf_annot_has_line_ending_styles(gctx, $self))
                pdf_set_annot_line_ending_styles(gctx, $self, start, end);
            else
                JM_Warning("annot type has no line ends");
        }

        //---------------------------------------------------------------------
        // annotation type
        //---------------------------------------------------------------------
        PARENTCHECK(type)
        %pythoncode %{@property%}
        PyObject *type()
        {
            int type = pdf_annot_type(gctx, $self);
            const char *c = pdf_string_from_annot_type(gctx, type);
            pdf_obj *o = pdf_dict_gets(gctx, $self->obj, "IT");
            if (!o || !pdf_is_name(gctx, o))
                return Py_BuildValue("is", type, c);         // no IT entry
            const char *it = pdf_to_name(gctx, o);
            return Py_BuildValue("iss", type, c, it);
        }

        //---------------------------------------------------------------------
        // annotation opacity
        //---------------------------------------------------------------------
        PARENTCHECK(opacity)
        %pythoncode %{@property%}
        PyObject *opacity()
        {
            double opy = -1.0f;
            pdf_obj *ca = pdf_dict_get(gctx, $self->obj, PDF_NAME(CA));
            if (pdf_is_number(gctx, ca))
                opy = pdf_to_real(gctx, ca);
            return Py_BuildValue("f", opy);
        }

        //---------------------------------------------------------------------
        // annotation set opacity
        //---------------------------------------------------------------------
        PARENTCHECK(setOpacity)
        void setOpacity(float opacity)
        {
            if (!INRANGE(opacity, 0.0f, 1.0f))
            {
                pdf_set_annot_opacity(gctx, $self, 1.0f);
                return;
            }
            pdf_set_annot_opacity(gctx, $self, opacity);
            if (opacity < 1.0f)
            {
                $self->page->transparency = 1;
            }
        }


        //---------------------------------------------------------------------
        // annotation get attached file info
        //---------------------------------------------------------------------
        FITZEXCEPTION(fileInfo, !result)
        PARENTCHECK(fileInfo)
        %feature("autodoc","Retrieve attached file information.") fileInfo;
        PyObject *fileInfo()
        {
            PyObject *res = PyDict_New();  // create Python dict
            char *filename = NULL;
            char *desc = NULL;
            int length = -1, size = -1;
            pdf_obj *stream = NULL, *o = NULL, *fs = NULL;

            fz_try(gctx)
            {
                int type = (int) pdf_annot_type(gctx, $self);
                if (type != PDF_ANNOT_FILEATTACHMENT)
                    THROWMSG("not a file attachment annot");
                stream = pdf_dict_getl(gctx, $self->obj, PDF_NAME(FS),
                                   PDF_NAME(EF), PDF_NAME(F), NULL);
                if (!stream) THROWMSG("bad PDF: file entry not found");
            }
            fz_catch(gctx) return NULL;

            fs = pdf_dict_get(gctx, $self->obj, PDF_NAME(FS));

            o = pdf_dict_get(gctx, fs, PDF_NAME(UF));
            if (o) filename = (char *) pdf_to_text_string(gctx, o);
            else
            {
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

            DICT_SETITEM_DROP(res, dictkey_filename, JM_UNICODE(filename));
            DICT_SETITEM_DROP(res, dictkey_desc, JM_UNICODE(desc));
            DICT_SETITEM_DROP(res, dictkey_length, Py_BuildValue("i", length));
            DICT_SETITEM_DROP(res, dictkey_size, Py_BuildValue("i", size));
            return res;
        }

        //---------------------------------------------------------------------
        // annotation get attached file content
        //---------------------------------------------------------------------
        FITZEXCEPTION(fileGet, !result)
        PARENTCHECK(fileGet)
        %feature("autodoc","Retrieve annotation attached file content.") fileGet;
        PyObject *fileGet()
        {
            PyObject *res = NULL;
            pdf_obj *stream = NULL;
            fz_buffer *buf = NULL;
            fz_var(buf);
            fz_try(gctx)
            {
                int type = (int) pdf_annot_type(gctx, $self);
                if (type != PDF_ANNOT_FILEATTACHMENT)
                    THROWMSG("not a file attachment annot");
                stream = pdf_dict_getl(gctx, $self->obj, PDF_NAME(FS),
                                   PDF_NAME(EF), PDF_NAME(F), NULL);
                if (!stream) THROWMSG("bad PDF: file entry not found");
                buf = pdf_load_stream(gctx, stream);
                res = JM_BinFromBuffer(gctx, buf);
            }
            fz_always(gctx) fz_drop_buffer(gctx, buf);
            fz_catch(gctx) return NULL;
            return res;
        }

        //---------------------------------------------------------------------
        // annotation update attached file
        //---------------------------------------------------------------------
        FITZEXCEPTION(fileUpd, !result)
        %pythonprepend fileUpd %{
CheckParent(self)
%}

        %feature("autodoc","Update annotation attached file.") fileUpd;
        PyObject *fileUpd(PyObject *buffer=NULL, char *filename=NULL, char *ufilename=NULL, char *desc=NULL)
        {
            pdf_document *pdf = NULL;       // to be filled in
            char *data = NULL;              // for new file content
            fz_buffer *res = NULL;          // for compressed content
            pdf_obj *stream = NULL, *fs = NULL;
            int64_t size = 0;
            fz_try(gctx)
            {
                pdf = $self->page->doc;     // the owning PDF
                int type = (int) pdf_annot_type(gctx, $self);
                if (type != PDF_ANNOT_FILEATTACHMENT)
                    THROWMSG("bad annot type");
                stream = pdf_dict_getl(gctx, $self->obj, PDF_NAME(FS),
                                   PDF_NAME(EF), PDF_NAME(F), NULL);
                // the object for file content
                if (!stream) THROWMSG("bad PDF: no /EF object");

                fs = pdf_dict_get(gctx, $self->obj, PDF_NAME(FS));

                // file content given
                res = JM_BufferFromBytes(gctx, buffer);
                if (buffer && !res) THROWMSG("bad type: 'buffer'");
                if (res)
                {
                    JM_update_stream(gctx, pdf, stream, res, 1);
                    // adjust /DL and /Size parameters
                    int64_t len = (int64_t) fz_buffer_storage(gctx, res, NULL);
                    pdf_obj *l = pdf_new_int(gctx, len);
                    pdf_dict_put(gctx, stream, PDF_NAME(DL), l);
                    pdf_dict_putl(gctx, stream, l, PDF_NAME(Params), PDF_NAME(Size), NULL);
                }

                if (filename)               // new filename given
                {
                    pdf_dict_put_text_string(gctx, stream, PDF_NAME(F), filename);
                    pdf_dict_put_text_string(gctx, fs, PDF_NAME(F), filename);
                    pdf_dict_put_text_string(gctx, stream, PDF_NAME(UF), filename);
                    pdf_dict_put_text_string(gctx, fs, PDF_NAME(UF), filename);
                    pdf_dict_put_text_string(gctx, $self->obj, PDF_NAME(Contents), filename);
                }

                if (ufilename)
                {
                    pdf_dict_put_text_string(gctx, stream, PDF_NAME(UF), ufilename);
                    pdf_dict_put_text_string(gctx, fs, PDF_NAME(UF), ufilename);
                }

                if (desc)                   // new description given
                {
                    pdf_dict_put_text_string(gctx, stream, PDF_NAME(Desc), desc);
                    pdf_dict_put_text_string(gctx, fs, PDF_NAME(Desc), desc);
                }
            }
            fz_always(gctx)
            {
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return_none;
        }

        //---------------------------------------------------------------------
        // annotation info
        //---------------------------------------------------------------------
        %pythoncode %{@property%}
        %feature("autodoc","Return various annotation properties.") info;
        PARENTCHECK(info)
        PyObject *info()
        {
            PyObject *res = PyDict_New();
            pdf_obj *o;

            DICT_SETITEM_DROP(res, dictkey_content,
                          JM_UNICODE(pdf_annot_contents(gctx, $self)));

            o = pdf_dict_get(gctx, $self->obj, PDF_NAME(Name));
            DICT_SETITEM_DROP(res, dictkey_name, JM_UNICODE(pdf_to_name(gctx, o)));

            // Title (= author)
            o = pdf_dict_get(gctx, $self->obj, PDF_NAME(T));
            DICT_SETITEM_DROP(res, dictkey_title, JM_UNICODE(pdf_to_text_string(gctx, o)));

            // CreationDate
            o = pdf_dict_gets(gctx, $self->obj, "CreationDate");
            DICT_SETITEM_DROP(res, dictkey_creationDate,
                          JM_UNICODE(pdf_to_text_string(gctx, o)));

            // ModDate
            o = pdf_dict_get(gctx, $self->obj, PDF_NAME(M));
            DICT_SETITEM_DROP(res, dictkey_modDate, JM_UNICODE(pdf_to_text_string(gctx, o)));

            // Subj
            o = pdf_dict_gets(gctx, $self->obj, "Subj");
            DICT_SETITEM_DROP(res, dictkey_subject,
                          JM_UNICODE(pdf_to_text_string(gctx, o)));

            // Identification (PDF key /NM)
            o = pdf_dict_gets(gctx, $self->obj, "NM");
            DICT_SETITEM_DROP(res, dictkey_id,
                          JM_UNICODE(pdf_to_text_string(gctx, o)));

            return res;
        }

        //---------------------------------------------------------------------
        // annotation set information
        //---------------------------------------------------------------------
        FITZEXCEPTION(setInfo, !result)
        %feature("autodoc","Set various annotation properties.") setInfo;
        %pythonprepend setInfo %{
        CheckParent(self)
        if type(info) is not dict:  # build a new dictionary from the other args
            info = {}
            if content is not None:
                info["content"] = content
            if title is not None:
                info["title"] = title
            if creationDate is not None:
                info["creationDate"] = creationDate
            if modDate is not None:
                info["modDate"] = modDate
            if subject is not None:
                info["subject"] = subject
        %}
        PyObject *setInfo(PyObject *info=NULL, char *content=NULL, char *title=NULL,
                          char *creationDate=NULL, char *modDate=NULL, char *subject=NULL)
        {
            char *uc = NULL;

            // use this to indicate a 'markup' annot type
            int is_markup = pdf_annot_has_author(gctx, $self);
            fz_try(gctx)
            {
                if (!PyDict_Check(info))
                    THROWMSG("info not a dict");

                // contents
                uc = JM_Python_str_AsChar(PyDict_GetItem(info, dictkey_content));
                if (uc)
                {
                    pdf_set_annot_contents(gctx, $self, uc);
                    JM_Python_str_DelForPy3(uc);
                }

                if (is_markup)
                {
                    // title (= author)
                    uc = JM_Python_str_AsChar(PyDict_GetItem(info, dictkey_title));
                    if (uc)
                    {
                        pdf_set_annot_author(gctx, $self, uc);
                        JM_Python_str_DelForPy3(uc);
                    }

                    // creation date
                    uc = JM_Python_str_AsChar(PyDict_GetItem(info, dictkey_creationDate));
                    if (uc)
                    {
                        pdf_dict_put_text_string(gctx, $self->obj,
                                                 PDF_NAME(CreationDate), uc);
                        JM_Python_str_DelForPy3(uc);
                    }

                    // mod date
                    uc = JM_Python_str_AsChar(PyDict_GetItem(info, dictkey_modDate));
                    if (uc)
                    {
                        pdf_dict_put_text_string(gctx, $self->obj,
                                                 PDF_NAME(M), uc);
                        JM_Python_str_DelForPy3(uc);
                    }

                    // subject
                    uc = JM_Python_str_AsChar(PyDict_GetItem(info, dictkey_subject));
                    if (uc)
                    {
                        pdf_dict_puts_drop(gctx, $self->obj, "Subj",
                                           pdf_new_text_string(gctx, uc));
                        JM_Python_str_DelForPy3(uc);
                    }
                }
            }
            fz_catch(gctx) return NULL;
            return_none;
        }

        //---------------------------------------------------------------------
        // annotation border
        //---------------------------------------------------------------------
        PARENTCHECK(border)
        %pythoncode %{@property%}
        PyObject *border()
        {
            return JM_annot_border(gctx, $self->obj);
        }

        //---------------------------------------------------------------------
        // set annotation border
        //---------------------------------------------------------------------
        %pythonprepend setBorder %{
        CheckParent(self)
        if type(border) is not dict:
            border = {"width": width, "style": style, "dashes": dashes}
        %}
        PyObject *setBorder(PyObject *border=NULL, float width=0, char *style=NULL, PyObject *dashes=NULL)
        {
            return JM_annot_set_border(gctx, border, $self->page->doc, $self->obj);
        }

        //---------------------------------------------------------------------
        // annotation flags
        //---------------------------------------------------------------------
        PARENTCHECK(flags)
        %pythoncode %{@property%}
        int flags()
        {
            return pdf_annot_flags(gctx, $self);
        }

        //---------------------------------------------------------------------
        // annotation clean contents
        //---------------------------------------------------------------------
        FITZEXCEPTION(_cleanContents, !result)
        PARENTCHECK(_cleanContents)
        PyObject *_cleanContents()
        {
            fz_try(gctx)
            {
                pdf_clean_annot_contents(gctx, $self->page->doc, $self,
                                         NULL, NULL, NULL, 1, 0);
            }
            fz_catch(gctx) return NULL;
            pdf_dirty_annot(gctx, $self);
            return_none;
        }

        //---------------------------------------------------------------------
        // set annotation flags
        //---------------------------------------------------------------------
        PARENTCHECK(setFlags)
        void setFlags(int flags)
        {
            pdf_set_annot_flags(gctx, $self, flags);
            pdf_dirty_annot(gctx, $self);
        }

        //---------------------------------------------------------------------
        // next annotation
        //---------------------------------------------------------------------
        PARENTCHECK(next)
        %pythonappend next
        %{
        if not val:
            return None
        val.thisown = True
        val.parent = self.parent  # copy owning page object from previous annot
        val.parent._annot_refs[id(val)] = val

        if val.type[0] != PDF_ANNOT_WIDGET:
            return val

        widget = Widget()
        TOOLS._fill_widget(val, widget)
        val = widget
        %}
        %pythoncode %{@property%}
        struct pdf_annot_s *next()
        {
            int type = pdf_annot_type(gctx, $self);
            pdf_annot *annot = NULL;

            if (type != PDF_ANNOT_WIDGET)
                annot = pdf_next_annot(gctx, $self);
            else
                annot = pdf_next_widget(gctx, $self);

            if (annot)
                pdf_keep_annot(gctx, annot);
            return annot;
        }


        %pythoncode %{
        def getPixmap(self, matrix=None, colorspace="rgb", alpha=False):
            """Return the Pixmap of the annotation.
            """
            page = self.parent
            if page is None:
                raise ValueError("orphaned object: parent is None")
            return page.getPixmap(
                matrix=matrix,
                colorspace=colorspace,
                alpha=alpha,
                clip=self.rect,
                annots=True,
            )


        def _erase(self):
            try:
                self.parent._forget_annot(self)
            except:
                pass
            if getattr(self, "thisown", True):
                self.__swig_destroy__(self)
            self.parent = None
            self.thisown = False

        def __str__(self):
            CheckParent(self)
            return "'%s' annotation on %s" % (self.type[1], str(self.parent))

        def __repr__(self):
            CheckParent(self)
            return "'%s' annotation on %s" % (self.type[1], str(self.parent))

        def __del__(self):
            self._erase()%}
    }
};
%clearnodefaultctor;

//-----------------------------------------------------------------------------
// fz_link
//-----------------------------------------------------------------------------
%rename(Link) fz_link_s;
%nodefaultctor;
struct fz_link_s
{
    %immutable;
    %extend {
        ~fz_link_s() {
            DEBUGMSG1("link");
            fz_drop_link(gctx, $self);
            DEBUGMSG2;
        }

        PyObject *_border(struct fz_document_s *doc, int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, doc);
            if (!pdf) return_none;
            pdf_obj *link_obj = pdf_new_indirect(gctx, pdf, xref, 0);
            if (!link_obj) return_none;
            PyObject *b = JM_annot_border(gctx, link_obj);
            pdf_drop_obj(gctx, link_obj);
            return b;
        }

        PyObject *_setBorder(PyObject *border, struct fz_document_s *doc, int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, doc);
            if (!pdf) return_none;
            pdf_obj *link_obj = pdf_new_indirect(gctx, pdf, xref, 0);
            if (!link_obj) return_none;
            PyObject *b = JM_annot_set_border(gctx, border, pdf, link_obj);
            pdf_drop_obj(gctx, link_obj);
            return b;
        }

        PyObject *_colors(struct fz_document_s *doc, int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, doc);
            if (!pdf) return_none;
            pdf_obj *link_obj = pdf_new_indirect(gctx, pdf, xref, 0);
            if (!link_obj) return_none;
            PyObject *b = JM_annot_colors(gctx, link_obj);
            pdf_drop_obj(gctx, link_obj);
            return b;
        }

        PyObject *_setColors(PyObject *colors, struct fz_document_s *doc, int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, doc);
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
        PARENTCHECK(uri)
        %pythoncode %{@property%}
        %pythonappend uri %{
        if not val:
            val = ""
        else:
            nval = "".join([c for c in val if 32 <= ord(c) <= 127])
            val = nval
        %}
        PyObject *uri()
        {
            return JM_UNICODE($self->uri);
        }

        PARENTCHECK(isExternal)
        %pythoncode %{@property%}
        PyObject *isExternal()
        {
            if (!$self->uri) Py_RETURN_FALSE;
            return JM_BOOL(fz_is_external_link(gctx, $self->uri));
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

        PARENTCHECK(rect)
        %pythoncode %{@property%}
        %pythonappend rect %{val = Rect(val)%}
        PyObject *rect()
        {
            return JM_py_from_rect($self->rect);
        }

        //---------------------------------------------------------------------
        // next link
        //---------------------------------------------------------------------
        // we need to increase the link refs number
        // so that it will not be freed when the head is dropped
        PARENTCHECK(next)
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
        struct fz_link_s *next()
        {
            fz_keep_link(gctx, $self->next);
            return $self->next;
        }

        %pythoncode %{
        def _erase(self):
            try:
                self.parent._forget_annot(self)
            except:
                pass
            if getattr(self, "thisown", True):
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
%rename(DisplayList) fz_display_list_s;
struct fz_display_list_s {
    %extend
    {
        ~fz_display_list_s() {
            DEBUGMSG1("display list");
            fz_drop_display_list(gctx, $self);
            DEBUGMSG2;
        }
        FITZEXCEPTION(fz_display_list_s, !result)
        fz_display_list_s(PyObject *mediabox)
        {
            struct fz_display_list_s *dl = NULL;
            fz_try(gctx)
                dl = fz_new_display_list(gctx, JM_rect_from_py(mediabox));
            fz_catch(gctx) return NULL;
            return dl;
        }

        FITZEXCEPTION(run, !result)
        PyObject *run(struct DeviceWrapper *dw, PyObject *m, PyObject *area) {
            fz_try(gctx)
            {
                fz_run_display_list(gctx, $self, dw->device,
                    JM_matrix_from_py(m), JM_rect_from_py(area), NULL);
            }
            fz_catch(gctx) return NULL;
            return_none;
        }

        //---------------------------------------------------------------------
        // DisplayList.rect
        //---------------------------------------------------------------------
        %pythoncode%{@property%}
        %pythonappend rect %{val = Rect(val)%}
        PyObject *rect()
        {
            return JM_py_from_rect(fz_bound_display_list(gctx, $self));
        }

        //---------------------------------------------------------------------
        // DisplayList.getPixmap
        //---------------------------------------------------------------------
        FITZEXCEPTION(getPixmap, !result)
        struct fz_pixmap_s *getPixmap(PyObject *matrix=NULL,
                                      struct fz_colorspace_s *colorspace=NULL,
                                      int alpha=1,
                                      PyObject *clip=NULL)
        {
            struct fz_colorspace_s *cs = NULL;
            fz_pixmap *pix = NULL;

            if (colorspace) cs = colorspace;
            else cs = fz_device_rgb(gctx);

            fz_try(gctx)
            {
                pix = JM_pixmap_from_display_list(gctx, $self, matrix, cs,
                                                  alpha, clip, NULL);
            }
            fz_catch(gctx) return NULL;
            return pix;
        }

        //---------------------------------------------------------------------
        // DisplayList.getTextPage
        //---------------------------------------------------------------------
        FITZEXCEPTION(getTextPage, !result)
        struct fz_stext_page_s *getTextPage(int flags = 3)
        {
            struct fz_stext_page_s *tp = NULL;
            fz_try(gctx)
            {
                fz_stext_options stext_options = { 0 };
                stext_options.flags = flags;
                tp = fz_new_stext_page_from_display_list(gctx, $self, &stext_options);
            }
            fz_catch(gctx) return NULL;
            return tp;
        }
        %pythoncode %{
        def __del__(self):
            if not type(self) is DisplayList: return
            self.__swig_destroy__(self)
        %}
    }
};

//-----------------------------------------------------------------------------
// fz_stext_page
//-----------------------------------------------------------------------------
%rename(TextPage) fz_stext_page_s;
struct fz_stext_page_s {
    %extend {
        FITZEXCEPTION(fz_stext_page_s, !result)
        fz_stext_page_s(PyObject *mediabox)
        {
            struct fz_stext_page_s *tp = NULL;
            fz_try(gctx)
                tp = fz_new_stext_page(gctx, JM_rect_from_py(mediabox));
            fz_catch(gctx) return NULL;
            return tp;
        }

        ~fz_stext_page_s()
        {
            DEBUGMSG1("text page");
            fz_drop_stext_page(gctx, $self);
            DEBUGMSG2;
        }
        //---------------------------------------------------------------------
        // method search()
        //---------------------------------------------------------------------
        %pythonappend search%{
        if len(val) == 0:
            return val
        nval = []
        for v in val:
            q = Quad(v)
            if not quads:
                nval.append(q.rect)
            else:
                nval.append(q)
        val = nval
        %}
        PyObject *search(const char *needle, int hit_max=16, int quads = 0)
        {
            fz_quad *result = NULL;
            PyObject *liste = PyList_New(0);
            int i, mymax = hit_max;
            if (mymax < 1) mymax = 16;
            result = JM_Alloc(fz_quad, (mymax+1));
            struct fz_quad_s *quad = (struct fz_quad_s *) result;
            int count = fz_search_stext_page(gctx, $self, needle, result, hit_max);
            for (i = 0; i < count; i++)
            {
                LIST_APPEND_DROP(liste, JM_py_from_quad(*quad));
                quad += 1;
            }
            JM_Free(result);
            return liste;
        }


        //---------------------------------------------------------------------
        // Get list of all blocks with block type and bbox as a Python list
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getNewBlockList, !result)
        PyObject *_getNewBlockList(PyObject *page_dict, int raw)
        {
            fz_try(gctx)
            {
                JM_make_textpage_dict(gctx, $self, page_dict, raw);
            }
            fz_catch(gctx)
            {
                return NULL;
            }
            return_none;
        }

        %pythoncode %{
        def _textpage_dict(self, raw = False):
            page_dict = {"width": self.rect.width, "height": self.rect.height}
            self._getNewBlockList(page_dict, raw)
            return page_dict
        %}


        //---------------------------------------------------------------------
        // Get text blocks with their bbox and concatenated lines
        // as a Python list
        //---------------------------------------------------------------------
        FITZEXCEPTION(extractBLOCKS, !result)
        %feature("autodoc","Fill a given list with text block information.") extractBLOCKS;
        PyObject *extractBLOCKS(PyObject *lines)
        {
            fz_stext_block *block;
            fz_stext_line *line;
            fz_stext_char *ch;
            int block_n = 0;
            PyObject *text = NULL, *litem;
            fz_buffer *res = NULL;
            fz_var(res);

            fz_try(gctx)
            {
                res = fz_new_buffer(gctx, 1024);
                for (block = $self->first_block; block; block = block->next)
                {
                    fz_rect blockrect = block->bbox;
                    if (block->type == FZ_STEXT_BLOCK_TEXT)
                    {
                        fz_clear_buffer(gctx, res);  // set text buffer to empty
                        int line_n = 0;
                        float last_y0 = 0.0;
                        for (line = block->u.t.first_line; line; line = line->next)
                        {
                            fz_rect linerect = line->bbox;
                            // append line no. 2 with new-line
                            if (line_n > 0)
                            {
                                if (linerect.y0 != last_y0)
                                    fz_append_string(gctx, res, "\n");
                                else
                                    fz_append_string(gctx, res, " ");
                            }
                            last_y0 = linerect.y0;
                            line_n++;
                            for (ch = line->first_char; ch; ch = ch->next)
                            {
                                JM_append_rune(gctx, res, ch->c);
                                linerect = fz_union_rect(linerect, JM_char_bbox(line, ch));
                            }
                            blockrect = fz_union_rect(blockrect, linerect);
                        }
                        text = JM_EscapeStrFromBuffer(gctx, res);
                    }
                    else
                    {
                        fz_image *img = block->u.i.image;
                        fz_colorspace *cs = img->colorspace;
                        text = PyUnicode_FromFormat("<image: %s, width %d, height %d, bpc %d>", fz_colorspace_name(gctx, cs), img->w, img->h, img->bpc);
                        blockrect = fz_union_rect(blockrect, block->bbox);
                    }
                    litem = PyTuple_New(7);
                    PyTuple_SET_ITEM(litem, 0, Py_BuildValue("f", blockrect.x0));
                    PyTuple_SET_ITEM(litem, 1, Py_BuildValue("f", blockrect.y0));
                    PyTuple_SET_ITEM(litem, 2, Py_BuildValue("f", blockrect.x1));
                    PyTuple_SET_ITEM(litem, 3, Py_BuildValue("f", blockrect.y1));
                    PyTuple_SET_ITEM(litem, 4, Py_BuildValue("O", text));
                    PyTuple_SET_ITEM(litem, 5, Py_BuildValue("i", block_n));
                    PyTuple_SET_ITEM(litem, 6, Py_BuildValue("i", block->type));
                    LIST_APPEND_DROP(lines, litem);
                    Py_DECREF(text);
                    block_n++;
                }
            }
            fz_always(gctx)
            {
                fz_drop_buffer(gctx, res);
                PyErr_Clear();
            }
            fz_catch(gctx) return NULL;
            return_none;
        }

        //---------------------------------------------------------------------
        // Get text words with their bbox
        //---------------------------------------------------------------------
        FITZEXCEPTION(extractWORDS, !result)
        %feature("autodoc","Fill a given list with text word information.") extractWORDS;
        PyObject *extractWORDS(PyObject *lines)
        {
            fz_stext_block *block;
            fz_stext_line *line;
            fz_stext_char *ch;
            fz_buffer *buff = NULL;
            fz_var(buff);
            size_t buflen = 0;
            int block_n = 0, line_n, word_n;
            fz_rect wbbox = {0,0,0,0};          // word bbox

            fz_try(gctx)
            {
                buff = fz_new_buffer(gctx, 64);
                for (block = $self->first_block; block; block = block->next)
                {
                    if (block->type != FZ_STEXT_BLOCK_TEXT)
                    {
                        block_n++;
                        continue;
                    }
                    line_n = 0;
                    for (line = block->u.t.first_line; line; line = line->next)
                    {
                        word_n = 0;                       // word counter per line
                        fz_clear_buffer(gctx, buff);      // reset word buffer
                        buflen = 0;                       // reset char counter
                        for (ch = line->first_char; ch; ch = ch->next)
                        {
                            if (ch->c == 32 && buflen == 0)
                                continue;                 // skip spaces at line start
                            if (ch->c == 32)
                            {   // --> finish the word
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
                            wbbox = fz_union_rect(wbbox, JM_char_bbox(line, ch));
                        }
                        if (buflen)                         // store any remaining word
                        {
                            word_n = JM_append_word(gctx, lines, buff, &wbbox,
                                                    block_n, line_n, word_n);
                            fz_clear_buffer(gctx, buff);
                            buflen = 0;
                        }
                        line_n++;
                    }
                    block_n++;
                }
            }
            fz_always(gctx)
            {
                fz_drop_buffer(gctx, buff);
                PyErr_Clear();
            }
            fz_catch(gctx)
            {
                return NULL;
            }
            return_none;
        }

        //---------------------------------------------------------------------
        // TextPage rectangle
        //---------------------------------------------------------------------
        %pythoncode %{@property%}
        %pythonappend rect %{
val = Rect(val)%}
        PyObject *rect()
        {
            fz_rect mediabox = $self->mediabox;
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
            fz_try(gctx)
            {
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                switch(format)
                {
                    case(1):
                        fz_print_stext_page_as_html(gctx, out, $self, 0);
                        break;
                    case(3):
                        fz_print_stext_page_as_xml(gctx, out, $self, 0);
                        break;
                    case(4):
                        fz_print_stext_page_as_xhtml(gctx, out, $self, 0);
                        break;
                    default:
                        JM_print_stext_page_as_text(gctx, out, $self);
                        text = JM_EscapeStrFromBuffer(gctx, res);
                        break;
                }
                if (!text) text = JM_EscapeStrFromBuffer(gctx, res);

            }
            fz_always(gctx)
            {
                fz_drop_buffer(gctx, res);
                fz_drop_output(gctx, out);
            }
            fz_catch(gctx) return NULL;

            return text;
        }
        %pythoncode %{
            def extractText(self):
                return self._extractText(0)

            def extractHTML(self):
                return self._extractText(1)

            def extractJSON(self):
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

            def extractXML(self):
                return self._extractText(3)

            def extractXHTML(self):
                return self._extractText(4)

            def extractDICT(self):
                return self._textpage_dict(raw=False)

            def extractRAWDICT(self):
                return self._textpage_dict(raw=True)
        %}
        %pythoncode %{
        def __del__(self):
            if self.this:
                self.__swig_destroy__(self)
                self.this = None
        %}
    }
};

//-----------------------------------------------------------------------------
// Graftmap - internally used for optimizing PDF object copy operations
//-----------------------------------------------------------------------------
%rename("Graftmap") pdf_graft_map_s;
struct pdf_graft_map_s
{
    %extend
    {
        ~pdf_graft_map_s()
        {
            DEBUGMSG1("graftmap");
            pdf_drop_graft_map(gctx, $self);
            DEBUGMSG2;
        }

        FITZEXCEPTION(pdf_graft_map_s, !result)
        pdf_graft_map_s(struct fz_document_s *doc)
        {
            pdf_graft_map *map = NULL;
            fz_try(gctx)
            {
                pdf_document *dst = pdf_specifics(gctx, doc);
                assert_PDF(dst);
                map = pdf_new_graft_map(gctx, dst);
            }
            fz_catch(gctx) return NULL;
            return map;
        }
        %pythoncode %{
            def __del__(self):
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
        %feature("autodoc","Return a unique positive integer.") gen_id;
        PyObject *gen_id()
        {
            JM_UNIQUE_ID += 1;
            if (JM_UNIQUE_ID < 0) JM_UNIQUE_ID = 1;
            return Py_BuildValue("i", JM_UNIQUE_ID);
        }

        %feature("autodoc","Free 'percent' of current store size.") store_shrink;
        PyObject *store_shrink(int percent)
        {
            if (percent >= 100)
            {
                fz_empty_store(gctx);
                return Py_BuildValue("i", 0);
            }
            if (percent > 0) fz_shrink_store(gctx, 100 - percent);
            return Py_BuildValue("i", (int) gctx->store->size);
        }

        %feature("autodoc","Determine dimension and other image data.") image_profile;
        PyObject *image_profile(PyObject *stream, int keep_image=0)
        {
            return JM_image_profile(gctx, stream, keep_image);
        }

        %feature("autodoc","Current store size.") store_size;
        %pythoncode%{@property%}
        PyObject *store_size()
        {
            return Py_BuildValue("i", (int) gctx->store->size);
        }

        %feature("autodoc","Maximum store size.") store_maxsize;
        %pythoncode%{@property%}
        PyObject *store_maxsize()
        {
            return Py_BuildValue("i", (int) gctx->store->max);
        }

        %feature("autodoc","Show configuration data.") fitz_config;
        %pythoncode%{@property%}
        PyObject *fitz_config()
        {
            return JM_fitz_config();
        }

        %feature("autodoc","Empty the glyph cache.") glyph_cache_empty;
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
        %}
        PyObject *_fill_widget(struct pdf_annot_s *annot, PyObject *widget)
        {
            fz_try(gctx)
            {
                JM_get_widget_properties(gctx, annot, widget);
            }
            fz_catch(gctx) return NULL;
            return_none;
        }

        FITZEXCEPTION(_save_widget, !result)
        PyObject *_save_widget(struct pdf_annot_s *annot, PyObject *widget)
        {
            fz_try(gctx)
            {
                JM_set_widget_properties(gctx, annot, widget);
            }
            fz_catch(gctx) return NULL;
            return_none;
        }


        FITZEXCEPTION(_parse_da, !result)
        %pythonappend _parse_da %{
        if not val or val == "":
            retun ((0,), "", 0)
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
        PyObject *_parse_da(struct pdf_annot_s *annot)
        {
            char *da_str = NULL;
            fz_try(gctx)
            {
                pdf_obj *da = pdf_dict_get_inheritable(gctx, annot->obj,
                                                       PDF_NAME(DA));
                if (!da)
                {
                    pdf_obj *trailer = pdf_trailer(gctx, annot->page->doc);
                    da = pdf_dict_getl(gctx, trailer, PDF_NAME(Root),
                                       PDF_NAME(AcroForm),
                                       PDF_NAME(DA),
                                       NULL);
                }
                da_str = (char *) pdf_to_text_string(gctx, da);
            }
            fz_catch(gctx) return NULL;
            return JM_UNICODE(da_str);
        }


        PyObject *_update_da(struct pdf_annot_s *annot, char *da_str)
        {
            fz_try(gctx)
            {
                pdf_dict_put_text_string(gctx, annot->obj, PDF_NAME(DA), da_str);
                pdf_dict_del(gctx, annot->obj, PDF_NAME(DS)); /* not supported */
                pdf_dict_del(gctx, annot->obj, PDF_NAME(RC)); /* not supported */
                pdf_dirty_annot(gctx, annot);
            }
            fz_catch(gctx) return NULL;
            return_none;
        }


        FITZEXCEPTION(_insert_contents, !result)
        %feature("autodoc","Make a new /Contents object for a page from bytes, and return its xref.") _insert_contents;
        PyObject *_insert_contents(struct fz_page_s *page, PyObject *newcont, int overlay=1)
        {
            fz_buffer *contbuf = NULL;
            int xref = 0;
            pdf_page *pdfpage = pdf_page_from_fz_page(gctx, page);
            fz_try(gctx)
            {
                assert_PDF(pdfpage);
                contbuf = JM_BufferFromBytes(gctx, newcont);
                xref = JM_insert_contents(gctx, pdfpage->doc, pdfpage->obj, contbuf, overlay);
                pdfpage->doc->dirty = 1;
            }
            fz_always(gctx) {fz_drop_buffer(gctx, contbuf);}
            fz_catch(gctx) {return NULL;}
            return Py_BuildValue("i", xref);
        }

        %feature("autodoc","Return compiled MuPDF version.") mupdf_version;
        PyObject *mupdf_version()
        {
            return PyUnicode_FromString(FZ_VERSION);
        }

        %feature("autodoc","Return the MuPDF warnings store.") mupdf_warnings;
        %pythonappend mupdf_warnings
        %{
        val = "\n".join(val)
        if reset:
            self.reset_mupdf_warnings()
        %}
        PyObject *mupdf_warnings(int reset=1)
        {
            Py_INCREF(JM_mupdf_warnings_store);
            return JM_mupdf_warnings_store;
        }

        %feature("autodoc","Reset MuPDF warnings.") reset_mupdf_warnings;
        void reset_mupdf_warnings()
        {
            Py_CLEAR(JM_mupdf_warnings_store);
            JM_mupdf_warnings_store = PyList_New(0);
        }

        %feature("autodoc","Set MuPDF error display to True or False.") mupdf_display_errors;
        PyObject *mupdf_display_errors(PyObject *value = NULL)
        {
            if (value == Py_True)
                JM_mupdf_show_errors = Py_True;
            else if (value == Py_False)
                JM_mupdf_show_errors = Py_False;
            Py_INCREF(JM_mupdf_show_errors);
            return JM_mupdf_show_errors;
        }

        %feature("autodoc","Transform rectangle with matrix.") _transform_rect;
        PyObject *_transform_rect(PyObject *rect, PyObject *matrix)
        {
            return JM_py_from_rect(fz_transform_rect(JM_rect_from_py(rect), JM_matrix_from_py(matrix)));
        }

        %feature("autodoc","Intersect two rectangles.") _intersect_rect;
        PyObject *_intersect_rect(PyObject *r1, PyObject *r2)
        {
            return JM_py_from_rect(fz_intersect_rect(JM_rect_from_py(r1),
                                                     JM_rect_from_py(r2)));
        }

        %feature("autodoc","Include point in a rect.") _include_point_in_rect;
        PyObject *_include_point_in_rect(PyObject *r, PyObject *p)
        {
            return JM_py_from_rect(fz_include_point_in_rect(JM_rect_from_py(r),
                                                     JM_point_from_py(p)));
        }

        %feature("autodoc","Transform point with matrix.") _transform_point;
        PyObject *_transform_point(PyObject *point, PyObject *matrix)
        {
            return JM_py_from_point(fz_transform_point(JM_point_from_py(point), JM_matrix_from_py(matrix)));
        }

        %feature("autodoc","Replace r1 with smallest rect containing both.") _union_rect;
        PyObject *_union_rect(PyObject *r1, PyObject *r2)
        {
            return JM_py_from_rect(fz_union_rect(JM_rect_from_py(r1),
                                                 JM_rect_from_py(r2)));
        }

        %feature("autodoc","Concatenate matrices m1, m2.") _concat_matrix;
        PyObject *_concat_matrix(PyObject *m1, PyObject *m2)
        {
            return JM_py_from_matrix(fz_concat(JM_matrix_from_py(m1),
                                                 JM_matrix_from_py(m2)));
        }

        %feature("autodoc","Invert a matrix.") _invert_matrix;
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

        %feature("autodoc","Measure length of a string for a Base14 font.") measure_string;
        float measure_string(const char *text, const char *fontname, float fontsize,
                             int encoding = 0)
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

        %pythoncode %{

def _hor_matrix(self, C, P):
    """Make a line horizontal.

    Args:
        C, P: points defining a line.
    Notes:
        Given two points C, P calculate matrix that rotates and translates the
        vector C -> P such that C is mapped to Point(0, 0), and P to some point
        on the x axis maintaining the distance between the points.
        If C == P, the null matrix will result.
    Returns:
        Matrix m such that C * m = (0, 0) and (P * m).y = 0.
    """

    S = (P - C).unit  # unit vector C -> P
    return Matrix(1, 0, 0, 1, -C.x, -C.y) * Matrix(S.x, -S.y, S.y, S.x, 0, 0)

def _angle_between(self, C, P, Q):
    """Compute the angle between two lines.

    Args:
        C, P, Q: points defining two lines which cross in P.
    Notes:
        Compute sine and cosine of the angle between two lines crossing in
        point P.
    Returns:
        (cos(alfa), sin(alfa)) of the angle alfa between the lines.
    """
    m = self._hor_matrix(P, Q)
    return (C * m).unit

def _le_annot_parms(self, annot, p1, p2):
    """Get common parameters for making line end symbols.
    """
    w = annot.border["width"]          # line width
    sc = annot.colors["stroke"]        # stroke color
    if not sc: sc = (0,0,0)
    scol = " ".join(map(str, sc)) + " RG\n"
    fc = annot.colors["fill"]          # fill color
    if not fc: fc = (0,0,0)
    fcol = " ".join(map(str, fc)) + " rg\n"
    nr = annot.rect
    np1 = p1                   # point coord relative to annot rect
    np2 = p2                   # point coord relative to annot rect
    m = self._hor_matrix(np1, np2)  # matrix makes the line horizontal
    im = ~m                            # inverted matrix
    L = np1 * m                        # converted start (left) point
    R = np2 * m                        # converted end (right) point
    if 0 <= annot.opacity < 1:
        opacity = "/Alp0 gs\n"
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

def _le_diamond(self, annot, p1, p2, lr):
    """Make stream commands for diamond line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2)
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

def _le_square(self, annot, p1, p2, lr):
    """Make stream commands for square line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2)
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

def _le_circle(self, annot, p1, p2, lr):
    """Make stream commands for circle line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2)
    shift = 2.5             # 2*shift*width = length of square edge
    d = shift * max(1, w)
    M = R - (d/2., 0) if lr else L + (d/2., 0)
    r = Rect(M, M) + (-d, -d, d, d)         # the square
    ap = "q\n" + opacity + self._oval_string(r.tl * im, r.tr * im, r.br * im, r.bl * im)
    ap += "%g w\n" % w
    ap += scol + fcol + "b\nQ\n"
    return ap

def _le_butt(self, annot, p1, p2, lr):
    """Make stream commands for butt line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2)
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

def _le_slash(self, annot, p1, p2, lr):
    """Make stream commands for slash line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2)
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

def _le_openarrow(self, annot, p1, p2, lr):
    """Make stream commands for open arrow line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2)
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

def _le_closedarrow(self, annot, p1, p2, lr):
    """Make stream commands for closed arrow line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2)
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

def _le_ropenarrow(self, annot, p1, p2, lr):
    """Make stream commands for right open arrow line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2)
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

def _le_rclosedarrow(self, annot, p1, p2, lr):
    """Make stream commands for right closed arrow line end symbol. "lr" denotes left (False) or right point.
    """
    m, im, L, R, w, scol, fcol, opacity = self._le_annot_parms(annot, p1, p2)
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
