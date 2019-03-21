%module fitz
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
// SWIG macro: check that a document is not closed
//-----------------------------------------------------------------------------
%define CLOSECHECK(meth)
%pythonprepend meth
%{if self.isClosed or self.isEncrypted:
    raise ValueError("operation illegal for closed / encrypted doc")%}
%enddef

%define CLOSECHECK0(meth)
%pythonprepend meth
%{if self.isClosed:
    raise ValueError("operation illegal for closed doc")%}
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
        %pythonprepend meth %{CheckParent(self)%}
        %feature("autodoc", doc) meth;
        %pythonappend meth %{
        if not val: return
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

#define SWIG_FILE_WITH_INIT
#define SWIG_PYTHON_2_UNICODE
#define JM_EPS 1E-5

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

#define THROWMSG(msg) fz_throw(gctx, FZ_ERROR_GENERIC, msg)
#define assert_PDF(cond) if (cond == NULL) THROWMSG("not a PDF")
#define INRANGE(v, low, high) ((low) <= v && v <= (high))
#define MAX(a, b) ((a) < (b)) ? (b) : (a)
#define MIN(a, b) ((a) < (b)) ? (a) : (b)
#define JM_StrFromBuffer(ctx, x) PyUnicode_DecodeUTF8(fz_string_from_buffer(ctx, x), (Py_ssize_t) fz_buffer_storage(ctx, x, NULL), "replace")
#define JM_PyErr_Clear if (PyErr_Occurred()) PyErr_Clear()

// binary output depending on Python major
# if PY_VERSION_HEX >= 0x03000000
#define JM_UNICODE(data) Py_BuildValue("s", data)
#define JM_BinFromChar(x) PyBytes_FromString(x)
#define JM_BinFromCharSize(x, y) PyBytes_FromStringAndSize(x, (Py_ssize_t) y)
# else
#define JM_UNICODE(data) data ? PyUnicode_DecodeUTF8(data, strlen(data), "replace") : Py_BuildValue("s", NULL)
#define JM_BinFromChar(x) PyByteArray_FromStringAndSize(x, (Py_ssize_t) strlen(x))
#define JM_BinFromCharSize(x, y) PyByteArray_FromStringAndSize(x, (Py_ssize_t) y)
# endif

// define Python None object
#define NONE Py_BuildValue("", NULL)

#include <fitz.h>
#include <pdf.h>
#include <zlib.h>
#include <time.h>
char *JM_Python_str_AsChar(PyObject *str);
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

JM_output_log = PyByteArray_FromStringAndSize("", 0);
fz_output *JM_fitz_stdout = JM_OutFromBarray(gctx, JM_output_log);
fz_set_stdout(gctx, JM_fitz_stdout);

JM_error_log  = PyByteArray_FromStringAndSize("", 0);
fz_output *JM_fitz_stderr = JM_OutFromBarray(gctx, JM_error_log);
fz_set_stderr(gctx, JM_fitz_stderr);

if (JM_fitz_stderr && JM_fitz_stdout)
    {;}
else
    PySys_WriteStderr("error redirecting stdout/stderr!\n");

//-----------------------------------------------------------------------------
// STOP redirect stdout/stderr
//-----------------------------------------------------------------------------
%}

%header %{
fz_context *gctx;
int JM_UNIQUE_ID = 0;

PyObject *fitz_stdout = NULL;
PyObject *fitz_stderr = NULL;

struct DeviceWrapper {
    fz_device *device;
    fz_display_list *list;
};
%}

//-----------------------------------------------------------------------------
// include version information and several other helpers
//-----------------------------------------------------------------------------
%pythoncode %{
import os
import weakref
from binascii import hexlify
import math

fitz_py2 = str is bytes           # if true, this is Python 2
%}
%include version.i
%include helper-geo-c.i
%include helper-other.i
%include helper-out-barray.i
%include helper-write-c.i
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
                if fitz_py2:                 # Python 2
                    if type(filename) is unicode:
                        filename = filename.encode("utf8")
                else:
                    filename = str(filename)     # should take care of pathlib

            self.streamlen = len(stream) if stream else 0

            self.name = ""
            if filename and self.streamlen == 0:
                self.name = filename

            if self.streamlen > 0:
                if not (filename or filetype):
                    raise ValueError("filetype missing with stream specified")
                if type(stream) not in (bytes, bytearray):
                    raise ValueError("stream must be bytes or bytearray")

            self.isClosed    = False
            self.isEncrypted = 0
            self.metadata    = None
            self.stream      = stream       # prevent garbage collecting this
            self.openErrCode = 0
            self.openErrMsg  = ''
            self.FontInfos   = []
            self.Graftmaps   = {}
            self.ShownPages  = {}
            self._page_refs  = weakref.WeakValueDictionary()%}

        %pythonappend fz_document_s %{
            if this:
                self.openErrCode = self._getGCTXerrcode()
                self.openErrMsg  = self._getGCTXerrmsg()
                self.thisown = True
                self._graft_id = TOOLS.gen_id()
                if self.needsPass:
                    self.isEncrypted = 1
                else: # we won't init until doc is decrypted
                    self.initData()
            else:
                self.thisown = False
        %}

        fz_document_s(const char *filename = NULL, PyObject *stream = NULL,
                      const char *filetype = NULL, PyObject *rect = NULL,
                      float width = 0, float height = 0,
                      float fontsize = 11)
        {
            gctx->error->errcode = 0;       // reset any error code
            gctx->error->message[0] = 0;    // reset any error message
            struct fz_document_s *doc = NULL;
            fz_stream *data = NULL;
            char *streamdata;
            float w = width, h = height;
            fz_rect r = JM_rect_from_py(rect);
            if (!(fz_is_empty_rect(r) && !fz_is_infinite_rect(r)))
            {
                w = r.x1 - r.x0;
                h = r.y1 - r.y0;
            }

            size_t streamlen = JM_CharFromBytesOrArray(stream, &streamdata);
            fz_try(gctx)
            {
                if (streamlen > 0)
                {
                    data = fz_open_memory(gctx, streamdata, streamlen);
                    char *magic = (char *)filename;
                    if (!magic) magic = (char *)filetype;
                    doc = fz_open_document_with_stream(gctx, magic, data);
                }
                else
                {
                    if (filename)
                    {
                        if (!filetype || strlen(filetype) == 0) doc = fz_open_document(gctx, filename);
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
                raise ValueError("operation illegal for closed doc")
            if hasattr(self, '_outline') and self._outline:
                self._dropOutline(self._outline)
                self._outline = None
            self._reset_page_refs()
            self.metadata    = None
            self.stream      = None
            self.isClosed    = True
            self.openErrCode = 0
            self.openErrMsg  = ''
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

        CLOSECHECK(embeddedFileCount)
        %feature("autodoc","Return number of embedded files.") embeddedFileCount;
        %pythoncode%{@property%}
        PyObject *embeddedFileCount()
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            int i = -1;
            if (pdf) i = pdf_count_portfolio_entries(gctx, pdf);
            return Py_BuildValue("i", i);
        }

        FITZEXCEPTION(embeddedFileDel, !result)
        CLOSECHECK(embeddedFileDel)
        %feature("autodoc","Delete embedded file by name.") embeddedFileDel;
        PyObject *embeddedFileDel(char *name)
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            pdf_obj *names;
            int i, n, m;
            fz_var(names);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                // check presence of name
                if (JM_find_embedded(gctx, Py_BuildValue("s", name), pdf) < 0)
                    THROWMSG("name not found");

                names = JM_embedded_names(gctx, pdf);
                if (!pdf_is_array(gctx, names))
                    THROWMSG("could not find names array");
                n = pdf_array_len(gctx, names);

                //-------------------------------------------------------------
                // Every file has 2 entries: name and file descriptor.
                // First delete file descriptor, then the name entry.
                // Because it might be referenced elsewhere, we leave deletion
                // of stream object to garbage collection.
                //-------------------------------------------------------------
                for (i = 0; i < n; i += 2)
                {
                    char *test = (char *) pdf_to_text_string(gctx, pdf_array_get(gctx, names, i));
                    if (!strcmp(test, name))
                    {
                        pdf_array_delete(gctx, names, i + 1);
                        pdf_array_delete(gctx, names, i);
                    }
                }
                m = (n - pdf_array_len(gctx, names)) / 2;
            }
            fz_catch(gctx) return NULL;
            return Py_BuildValue("i", m);
        }

        FITZEXCEPTION(embeddedFileInfo, !result)
        CLOSECHECK(embeddedFileInfo)
        %feature("autodoc","Retrieve embedded file information given its entry number or name.") embeddedFileInfo;
        PyObject *embeddedFileInfo(PyObject *id)
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            Py_ssize_t name_len = 0;
            int n = -1;
            char *name = NULL;
            char *sname = NULL;
            fz_try(gctx)
            {
                assert_PDF(pdf);
                n = JM_find_embedded(gctx, id, pdf);
                if (n < 0) THROWMSG("entry not found");
            }
            fz_catch(gctx) return NULL;

            PyObject *infodict = PyDict_New();
            // name of file entry
            name = (char *) pdf_to_text_string(gctx, pdf_portfolio_entry_name(gctx, pdf, n));
            PyDict_SetItemString(infodict, "name", JM_UNICODE(name));

            pdf_obj *o = pdf_portfolio_entry_obj(gctx, pdf, n);

            name = (char *) pdf_to_text_string(gctx, pdf_dict_get(gctx, o, PDF_NAME(F)));
            PyDict_SetItemString(infodict, "filename", JM_UNICODE(name));

            name = (char *) pdf_to_text_string(gctx, pdf_dict_get(gctx, o, PDF_NAME(UF)));
            PyDict_SetItemString(infodict, "ufilename", JM_UNICODE(name));

            name = (char *) pdf_to_text_string(gctx, pdf_dict_get(gctx, o, PDF_NAME(Desc)));
            PyDict_SetItemString(infodict, "desc", JM_UNICODE(name));

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

            PyDict_SetItemString(infodict, "size", Py_BuildValue("i", DL));
            PyDict_SetItemString(infodict, "length", Py_BuildValue("i", len));
            return infodict;
        }

        FITZEXCEPTION(embeddedFileUpd, !result)
        CLOSECHECK(embeddedFileUpd)
        %feature("autodoc","Change an embedded file given its entry number or name.") embeddedFileUpd;
        PyObject *embeddedFileUpd(PyObject *id, PyObject *buffer = NULL, char *filename = NULL, char *ufilename = NULL, char *desc = NULL)
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            fz_buffer *res = NULL;
            fz_var(res);
            fz_try(gctx)
            {
                assert_PDF(pdf);

                int n = JM_find_embedded(gctx, id, pdf);
                if (n < 0) THROWMSG("entry not found");

                pdf_obj *entry = pdf_portfolio_entry_obj(gctx, pdf, n);
                pdf_obj *filespec = pdf_dict_getl(gctx, entry, PDF_NAME(EF),
                                                  PDF_NAME(F), NULL);

                char *data = NULL;
                size_t len = JM_CharFromBytesOrArray(buffer, &data);
                if (len > 0)
                {
                    if (!filespec) THROWMSG("/EF object not found");
                    res = fz_new_buffer_from_copied_data(gctx, data, len);
                    JM_update_stream(gctx, pdf, filespec, res);
                    // adjust /DL and /Size parameters
                    pdf_obj *l = pdf_new_int(gctx, (int64_t) len);
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
            return NONE;
        }

        %pythoncode %{
        def embeddedFileSetInfo(self, id, filename=None, ufilename=None, desc=None):
            self.embeddedFileUpd(id, filename=filename, ufilename=ufilename, desc=desc)
            return
        %}

        FITZEXCEPTION(embeddedFileGet, !result)
        CLOSECHECK(embeddedFileGet)
        %feature("autodoc","Retrieve embedded file content by name or by number.") embeddedFileGet;
        PyObject *embeddedFileGet(PyObject *id)
        {
            PyObject *cont = NULL;
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            fz_buffer *buf = NULL;
            fz_var(buf);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int i = JM_find_embedded(gctx, id, pdf);
                if (i < 0) THROWMSG("entry not found");
                buf = pdf_portfolio_entry(gctx, pdf, i);
                cont = JM_BinFromBuffer(gctx, buf);
            }
            fz_always(gctx) fz_drop_buffer(gctx, buf);
            fz_catch(gctx) return NULL;
            return cont;
        }

        FITZEXCEPTION(embeddedFileAdd, !result)
        CLOSECHECK(embeddedFileAdd)
        %feature("autodoc","Embed a new file.") embeddedFileAdd;
        PyObject *embeddedFileAdd(PyObject *buffer, const char *name, char *filename=NULL, char *ufilename=NULL, char *desc=NULL)
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            fz_buffer *data = NULL, *buf = NULL;
            char *buffdata;
            fz_var(data);
            fz_var(buf);
            int entry = 0;
            size_t size = 0;
            char *f = filename, *uf = ufilename, *d = desc;
            int name_len = (int) strlen(name);
            // make adjustments for omitted arguments
            if (!f) f = (char *)name;
            if (!uf) uf = f;
            if (!d) d = f;

            fz_try(gctx)
            {
                assert_PDF(pdf);
                size = JM_CharFromBytesOrArray(buffer, &buffdata);
                if (size < 1) THROWMSG("buffer not bytes / bytearray");

                // we do not allow duplicate names
                entry = JM_find_embedded(gctx, Py_BuildValue("s", name), pdf);
                if (entry >= 0) THROWMSG("name already exists");

                // first insert a dummy entry with no more than the name
                buf = fz_new_buffer(gctx, name_len + 1);   // has no real meaning
                fz_append_string(gctx, buf, name);         // fill something in
                fz_terminate_buffer(gctx, buf);            // to make it usable
                pdf_add_portfolio_entry(gctx, pdf,         // insert the entry.
                        name, name_len,                    // Except the name,
                        name, name_len,                    // everything will
                        name, name_len,                    // be overwritten
                        name, name_len,
                        buf);
                fz_drop_buffer(gctx, buf);                 // kick stupid buffer
                buf = NULL;
                //-------------------------------------------------------------
                // now modify the entry just created:
                // (1) allow unicode values for filenames and description
                // (2) deflate the file content
                //-------------------------------------------------------------
                // locate the entry again
                entry = JM_find_embedded(gctx, Py_BuildValue("s", name), pdf);
                // (1) insert the real metadata
                pdf_obj *o = pdf_portfolio_entry_obj(gctx, pdf, entry);
                pdf_dict_put_text_string(gctx, o, PDF_NAME(F),    f);
                pdf_dict_put_text_string(gctx, o, PDF_NAME(UF),  uf);
                pdf_dict_put_text_string(gctx, o, PDF_NAME(Desc), d);
                // (2) insert the real file contents
                pdf_obj *filespec = pdf_dict_getl(gctx, o, PDF_NAME(EF),
                                                  PDF_NAME(F), NULL);
                data = fz_new_buffer_from_copied_data(gctx, buffdata, size);
                JM_update_stream(gctx, pdf, filespec, data);
                // finally update some size attributes
                pdf_obj *l = pdf_new_int(gctx, (int64_t) size);
                pdf_dict_put(gctx, filespec, PDF_NAME(DL), l);
                pdf_dict_putl(gctx, filespec, l, PDF_NAME(Params), PDF_NAME(Size), NULL);
            }
            fz_always(gctx)
            {
                fz_drop_buffer(gctx, buf);
                fz_drop_buffer(gctx, data);
            }
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return NONE;
        }

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
            return Py_BuildValue("i", fz_needs_password(gctx, $self));
        }

        %feature("autodoc", "Calculate internal link destination.") resolveLink;
        PyObject *resolveLink(char *uri = NULL)
        {
            if (!uri) return NONE;
            float xp = 0.0f, yp = 0.0f;
            int pno = -1;
            fz_try(gctx)
                pno = fz_resolve_link(gctx, $self, uri, &xp, &yp);
            fz_catch(gctx)
                return NONE;
            if (pno < 0) return NONE;
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
            if (!fz_is_document_reflowable(gctx, $self)) return NONE;
            fz_try(gctx)
            {
                float w = width, h = height;
                fz_rect r = JM_rect_from_py(rect);
                if (!fz_is_empty_rect(r) && !fz_is_infinite_rect(r))
                {
                    w = r.x1 - r.x0;
                    h = r.y1 - r.y0;
                }
                if (w <= 0.0f || h <= 0.0f)
                        THROWMSG("invalid page size");
                fz_layout_document(gctx, $self, w, h, fontsize);
            }
            fz_catch(gctx) return NULL;
            return NONE;
        }

        CLOSECHECK(makeBookmark)
        %feature("autodoc", "Make page bookmark in a reflowable document.") makeBookmark;
        PyObject *makeBookmark(int pno = 0)
        {
            if (!fz_is_document_reflowable(gctx, $self)) return NONE;
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
            return NONE;
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
            if (!pdf) return NONE;
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
                        hexlify(len, (unsigned char *) pdf_to_str_buf(gctx, o), (unsigned char *) hex);
                        PyList_Append(idlist, Py_BuildValue("s", hex));
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

        %feature("autodoc", "Retrieve last MuPDF error code.") _getGCTXerrcode;
        PyObject *_getGCTXerrcode() {
            return Py_BuildValue("i", fz_caught(gctx));
        }

        %feature("autodoc", "Retrieve last MuPDF error message.") _getGCTXerrmsg;
        PyObject *_getGCTXerrmsg() {
            return Py_BuildValue("s", fz_caught_message(gctx));
        }

        CLOSECHECK0(authenticate)
        %feature("autodoc", "Decrypt document with a password.") authenticate;
        %pythonappend authenticate %{
            if val: # the doc is decrypted successfully and we init the outline
                self.isEncrypted = 0
                self.initData()
                self.thisown = True
        %}
        PyObject *authenticate(char *password)
        {
            return Py_BuildValue("i", fz_authenticate_password(gctx, $self, (const char *) password));
        }

        //---------------------------------------------------------------------
        // save(filename, ...)
        //---------------------------------------------------------------------
        FITZEXCEPTION(save, !result)
        %pythonprepend save %{
            if self.isClosed or self.isEncrypted:
                raise ValueError("operation illegal for closed / encrypted doc")
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
                if self.name != filename or self.streamlen > 0:
                    raise ValueError("incremental needs original file")
        %}

        PyObject *save(char *filename, int garbage=0, int clean=0, int deflate=0, int incremental=0, int ascii=0, int expand=0, int linear=0, int pretty = 0, int decrypt = 1)
        {
            int errors = 0;
            pdf_write_options opts = { 0 };
            opts.do_incremental     = incremental;
            opts.do_ascii           = ascii;
            opts.do_compress        = deflate;
            opts.do_compress_images = deflate;
            opts.do_compress_fonts  = deflate;
            opts.do_decompress      = expand;
            opts.do_garbage         = garbage;
            opts.do_linear          = linear;
            opts.do_clean           = clean;
            opts.do_pretty          = pretty;
            opts.do_sanitize        = clean;
            opts.continue_on_error  = 1;
            opts.errors = &errors;
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                JM_embedded_clean(gctx, pdf);
                JM_save_document(gctx, pdf, filename, &opts, decrypt);
                pdf->dirty = 0;
            }
            fz_catch(gctx) return NULL;
            return NONE;
        }

        //---------------------------------------------------------------------
        // write document to memory
        //---------------------------------------------------------------------
        FITZEXCEPTION(write, !result)
        %feature("autodoc", "Write document to a bytes object.") write;
        %pythonprepend write %{
            if self.isClosed or self.isEncrypted:
                raise ValueError("operation illegal for closed / encrypted doc")
            if self.pageCount < 1:
                raise ValueError("cannot write with zero pages")
        %}

        PyObject *write(int garbage=0, int clean=0, int deflate=0,
                        int ascii=0, int expand=0, int linear=0, int pretty = 0, int decrypt = 1)
        {
            PyObject *r = NULL;
            fz_output *out = NULL;
            fz_buffer *res = NULL;
            int errors = 0;
            pdf_write_options opts = { 0 };
            opts.do_incremental     = 0;
            opts.do_ascii           = ascii;
            opts.do_compress        = deflate;
            opts.do_compress_images = deflate;
            opts.do_compress_fonts  = deflate;
            opts.do_decompress      = expand;
            opts.do_garbage         = garbage;
            opts.do_linear          = linear;
            opts.do_clean           = clean;
            opts.do_pretty          = pretty;
            opts.do_sanitize        = clean;
            opts.continue_on_error  = 1;
            opts.errors = &errors;
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
                JM_write_document(gctx, pdf, out, &opts, decrypt);
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
    raise ValueError("operation illegal for closed / encrypted doc")
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

        PyObject *insertPDF(struct fz_document_s *docsrc, int from_page=-1, int to_page=-1, int start_at=-1, int rotate=-1, int links = 1)
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
                merge_range(gctx, pdfout, pdfsrc, fp, tp, sa, rotate);
            }
            fz_catch(gctx) return NULL;
            pdfout->dirty = 1;
            return NONE;
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
            fz_rect mediabox = { 0, 0, 595, 842 };    // ISO-A4 portrait values
            mediabox.x1 = width;
            mediabox.y1 = height;
            pdf_obj *resources = NULL, *page_obj = NULL;
            fz_buffer *contents = NULL;
            fz_try(gctx)
            {
                assert_PDF(pdf);
                if (pno < -1) THROWMSG("invalid page number(s)");
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
            return NONE;
        }

        //---------------------------------------------------------------------
        // Create sub-document to keep only selected pages.
        // Parameter is a Python sequence of the wanted page numbers.
        //---------------------------------------------------------------------
        FITZEXCEPTION(select, !result)
        %feature("autodoc","Build sub-pdf with page numbers in 'list'.") select;
        CLOSECHECK(select)
        %pythonappend select %{
            self._reset_page_refs()
            self.initData()%}
        PyObject *select(PyObject *pyliste)
        {
            // preparatory stuff:
            // (1) get underlying pdf document,
            // (2) transform Python list into integer array
            
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                if (!PySequence_Check(pyliste))
                    THROWMSG("sequence required");
                if (PySequence_Size(pyliste) < 1)
                    THROWMSG("invalid sequ. length");        
                // now call retainpages (code copy of fz_clean_file.c)
                globals glo = {0};
                glo.ctx = gctx;
                glo.doc = pdf;
                retainpages(gctx, &glo, pyliste);
            }
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return NONE;
        }

        //********************************************************************
        // get document permissions
        //********************************************************************
        %feature("autodoc","Get permissions dictionary.") permissions;
        CLOSECHECK0(permissions)
        %pythoncode%{@property%}
        PyObject *permissions()
        {
            PyObject *p = JM_BOOL(fz_has_permission(gctx, $self, FZ_PERMISSION_PRINT));
            PyObject *e = JM_BOOL(fz_has_permission(gctx, $self, FZ_PERMISSION_EDIT));
            PyObject *c = JM_BOOL(fz_has_permission(gctx, $self, FZ_PERMISSION_COPY));
            PyObject *n = JM_BOOL(fz_has_permission(gctx, $self, FZ_PERMISSION_ANNOTATE));
            PyObject *res = PyDict_New();
            PyDict_SetItemString(res, "print", p);
            PyDict_SetItemString(res, "edit", e);
            PyDict_SetItemString(res, "copy", c);
            PyDict_SetItemString(res, "note", n);
            return res;
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
                        PyList_Append(wlist, Py_BuildValue("(i, f)", glyph, adv));
                    }
                    else
                    {
                        PyList_Append(wlist, Py_BuildValue("(i, f)", glyph, 0.0));
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
                if (n >= pageCount) THROWMSG("invalid page number(s)");
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
        x = []
        for v in val:
            if v not in x:
                x.append(v)
        val = x%}
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
                if (n >= pageCount) THROWMSG("invalid page number(s)");
                assert_PDF(pdf);
                pageref = pdf_lookup_page_obj(gctx, pdf, n);
                rsrc = pdf_dict_get(gctx, pageref, PDF_NAME(Resources));
                if (!pageref || !rsrc) THROWMSG("cannot retrieve page info");
                liste = PyList_New(0);
                JM_scan_resources(gctx, pdf, rsrc, liste, what);
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
                    fontname = (char *) JM_ASCIIFromChar((char *) pdf_to_name(gctx, bname));
                    tuple = Py_BuildValue("sssO",
                                fontname,
                                ext,
                                pdf_to_name(gctx, subtype),
                                bytes);
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
            fz_pixmap *pix = NULL;
            fz_var(pix);
            pdf_obj *obj = NULL;
            PyObject *rc = NULL;
            unsigned char ext[5];
            fz_image *image = NULL;
            fz_var(image);
            fz_output *out = NULL;
            fz_var(out);
            fz_compressed_buffer *cbuf = NULL;
            int type = FZ_IMAGE_UNKNOWN, n = 0, xres = 0, yres = 0, is_jpx = 0;
            int smask = 0, width = 0, height = 0;
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
                    }

                    // ensure returning a PNG for unsupported images ----------
                    if (type < FZ_IMAGE_BMP ||
                        type == FZ_IMAGE_JBIG2)
                        type = FZ_IMAGE_UNKNOWN;

                    if (type != FZ_IMAGE_UNKNOWN)
                    {
                        switch(type)
                        {
                            case(FZ_IMAGE_BMP):  strcpy(ext, "bmp");  break;
                            case(FZ_IMAGE_GIF):  strcpy(ext, "gif");  break;
                            case(FZ_IMAGE_JPEG): strcpy(ext, "jpeg"); break;
                            case(FZ_IMAGE_JPX):  strcpy(ext, "jpx");  break;
                            case(FZ_IMAGE_JXR):  strcpy(ext, "jxr");  break;
                            case(FZ_IMAGE_PNM):  strcpy(ext, "pnm");  break;
                            case(FZ_IMAGE_TIFF): strcpy(ext, "tiff"); break;
                            default:             strcpy(ext, "png");  break;
                        }
                    }
                    else  // need a pixmap to make a PNG buffer
                    {
                        pix = fz_get_pixmap_from_image(gctx, image,
                                                       NULL, NULL, NULL, NULL);
                        n = pix->n;
                        // only gray & rgb pixmaps support PNG!
                        if (pix->colorspace &&
                            pix->colorspace != fz_device_gray(gctx) &&
                            pix->colorspace != fz_device_rgb(gctx))
                        {
                            fz_pixmap *pix2 = fz_convert_pixmap(gctx, pix,
                                     fz_device_rgb(gctx), NULL, NULL, NULL, 1);
                            fz_drop_pixmap(gctx, pix);
                            pix = pix2;
                        }

                        freebuf = fz_new_buffer(gctx, 2048);
                        out = fz_new_output_with_buffer(gctx, freebuf);
                        fz_write_pixmap_as_png(gctx, out, pix);
                        buffer = freebuf;
                        strcpy(ext, "png");
                    }
                    PyObject *bytes = JM_BinFromBuffer(gctx, buffer);
                    rc = Py_BuildValue("{s:s,s:i,s:i,s:i,s:i,s:i,s:i,s:s,s:O}",
                                       "ext", ext,
                                       "smask", smask,
                                       "width", width,
                                       "height", height,
                                       "colorspace", n,
                                       "xres", xres,
                                       "yres", yres,
                                       "cs-name", cs_name,
                                       "image", bytes);
                    Py_CLEAR(bytes);
                }
                else
                    rc = PyDict_New();
            }
            fz_always(gctx)
            {
                fz_drop_image(gctx, image);
                fz_drop_buffer(gctx, freebuf);
                fz_drop_output(gctx, out);
                fz_drop_pixmap(gctx, pix);
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
            PyList_Append(xrefs, Py_BuildValue("i", olroot_xref));
            pdf->dirty = 1;
            return xrefs;
        }

        //---------------------------------------------------------------------
        // Check: is this an AcroForm with at least one field?
        //---------------------------------------------------------------------
        CLOSECHECK0(isFormPDF)
        %pythoncode%{@property%}
        PyObject *isFormPDF()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) Py_RETURN_FALSE;           // not a PDF
            pdf_obj *form = NULL;
            pdf_obj *fields = NULL;
            int have_form = 0;                   // preset indicator
            fz_try(gctx)
            {
                form = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Root), PDF_NAME(AcroForm), NULL);
                if (form)                        // form obj exists
                {
                    fields = pdf_dict_get(gctx, form, PDF_NAME(Fields));
                    if (fields && pdf_array_len(gctx, fields) > 0) have_form = 1;
                }
            }
            fz_catch(gctx) Py_RETURN_FALSE;      // any problem yields false
            if (!have_form) Py_RETURN_FALSE;     // no form / no fields
            Py_RETURN_TRUE;
        }

        //---------------------------------------------------------------------
        // Return the list of field font resource names
        //---------------------------------------------------------------------
        CLOSECHECK0(FormFonts)
        %pythoncode%{@property%}
        PyObject *FormFonts()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) return NONE;           // not a PDF
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
                        PyList_Append(liste, Py_BuildValue("s", pdf_to_name(gctx, f)));
                    }
                }
            }
            fz_catch(gctx) NONE;       // any problem yields None
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
            if (!pdf) NONE;           // not a PDF
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
            return NONE;
        }

        //---------------------------------------------------------------------
        // Get Xref Number of Outline Root, create it if missing
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getOLRootNumber, !result)
        CLOSECHECK(_getOLRootNumber)
        PyObject *_getOLRootNumber()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx) assert_PDF(pdf);
            fz_catch(gctx) return NULL;
            
            pdf_obj *root, *olroot, *ind_obj;
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
            return NONE;
        }

        //---------------------------------------------------------------------
        // Get Object String of xref
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getXrefString, !result)
        CLOSECHECK0(_getXrefString)
        PyObject *_getXrefString(int xref)
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
                pdf_print_obj(gctx, out, pdf_resolve_indirect(gctx, obj), 1);
                text = JM_StrFromBuffer(gctx, res);
            }
            fz_always(gctx)
            {
                pdf_drop_obj(gctx, obj);
                fz_drop_output(gctx, out);
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) return NULL;
            return text;
        }

        //---------------------------------------------------------------------
        // Get String of PDF trailer
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getTrailerString, !result)
        CLOSECHECK0(_getTrailerString)
        PyObject *_getTrailerString()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); // conv doc to pdf
            if (!pdf) return NONE;
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
                    pdf_print_obj(gctx, out, obj, 1);
                    text = JM_StrFromBuffer(gctx, res);
                }
                else text = NONE;
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
        // Get decompressed stream of an object by xref
        // Return NONE if not stream
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getXrefStream, !result)
        CLOSECHECK(_getXrefStream)
        PyObject *_getXrefStream(int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            PyObject *r = NONE;
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
                    refresh_link_table(gctx, pdf_page_from_fz_page(gctx, page));
            }
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return NONE;
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
                if (!res) THROWMSG("stream must be bytes or bytearray");
                JM_update_stream(gctx, pdf, obj, res);
                
            }
            fz_always(gctx)
            {
                fz_drop_buffer(gctx, res);
                pdf_drop_obj(gctx, obj);
            }
            fz_catch(gctx)
                return NULL;
            pdf->dirty = 1;
            return NONE;
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
                return NONE;
            }
            // create new indirect object from /Info object
            new_info_ind = pdf_add_object(gctx, pdf, new_info);
            // put this in the trailer dictionary
            pdf_dict_put_drop(gctx, pdf_trailer(gctx, pdf), PDF_NAME(Info), new_info_ind);
            return NONE;
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

            def getPageFontList(self, pno):
                """Retrieve a list of fonts used on a page.
                """
                if self.isClosed or self.isEncrypted:
                    raise ValueError("operation illegal for closed / encrypted doc")
                if self.isPDF:
                    return self._getPageInfo(pno, 1)
                return []

            def getPageImageList(self, pno):
                """Retrieve a list of images used on a page.
                """
                if self.isClosed or self.isEncrypted:
                    raise ValueError("operation illegal for closed / encrypted doc")
                if self.isPDF:
                    return self._getPageInfo(pno, 2)
                return []

            def copyPage(self, pno, to=-1):
                """Copy a page to before some other page of the document. Specify 'to = -1' to copy after last page.
                """
                pl = list(range(len(self)))
                if pno < 0 or pno > pl[-1]:
                    raise ValueError("'from' page number out of range")
                if to < -1 or to > pl[-1]:
                    raise ValueError("'to' page number out of range")
                if to == -1:
                    pl.append(pno)
                else:
                    pl.insert(to, pno)
                return self.select(pl)
            
            def movePage(self, pno, to = -1):
                """Move a page to before some other page of the document. Specify 'to = -1' to move after last page.
                """
                pl = list(range(len(self)))
                if pno < 0 or pno > pl[-1]:
                    raise ValueError("'from' page number out of range")
                if to < -1 or to > pl[-1]:
                    raise ValueError("'to' page number out of range")
                pl.remove(pno)
                if to == -1:
                    pl.append(pno)
                else:
                    pl.insert(to-1, pno)
                return self.select(pl)
            
            def deletePage(self, pno = -1):
                """Delete a page from the document. First page is '0', last page is '-1'.
                """
                pl = list(range(len(self)))
                if pno < -1 or pno > pl[-1]:
                    raise ValueError("page number out of range")
                if pno >= 0:
                    pl.remove(pno)
                else:
                    pl.remove(pl[-1])
                return self.select(pl)
            
            def deletePageRange(self, from_page = -1, to_page = -1):
                """Delete pages from the document. First page is '0', last page is '-1'.
                """
                pl = list(range(len(self)))
                f = from_page
                t = to_page
                if f == -1:
                    f = pl[-1]
                if t == -1:
                    t = pl[-1]
                if not 0 <= f <= t <= pl[-1]:
                    raise ValueError("page number(s) out of range")
                for i in range(f, t+1):
                    pl.remove(i)
                return self.select(pl)

            def saveIncr(self):
                """ Save PDF incrementally"""
                return self.save(self.name, incremental = True)

            def __repr__(self):
                m = "closed " if self.isClosed else ""
                if self.streamlen == 0:
                    if self.name == "":
                        return m + "fitz.Document(<new PDF>)"
                    return m + "fitz.Document('%s')" % (self.name,)
                return m + "fitz.Document('%s', <memory>)" % (self.name,)

            def __getitem__(self, i=0):
                if type(i) is not int:
                    raise ValueError("invalid page number(s)")
                if i >= len(self):
                    raise IndexError("invalid page number(s)")
                return self.loadPage(i)

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
                    self.thisown = False
                    self.__swig_destroy__(self)
                self.Graftmaps = {}
                self.ShownPages = {}
                self.stream    = None
                self._reset_page_refs = DUMMY
                self.__swig_destroy__ = DUMMY
                self.isClosed = True
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
            return NONE;
        }

        //---------------------------------------------------------------------
        // Page.getSVGimage
        //---------------------------------------------------------------------
        FITZEXCEPTION(getSVGimage, !result)
        %feature("autodoc","Create an SVG image from the page as a string.") getSVGimage;
        PARENTCHECK(getSVGimage)
        PyObject *getSVGimage(PyObject *matrix = NULL)
        {
            fz_rect mediabox = fz_bound_page(gctx, $self);
            fz_device *dev = NULL;
            fz_buffer *res = NULL;
            PyObject *text = NULL;
            fz_matrix ctm = JM_matrix_from_py(matrix);
            fz_cookie *cookie = NULL;
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
                dev = fz_new_svg_device(gctx, out, tbounds.x1-tbounds.x0, tbounds.y1-tbounds.y0, FZ_SVG_TEXT_AS_PATH, 1);
                fz_run_page(gctx, $self, dev, ctm, cookie);
                fz_close_device(gctx, dev);
                text = JM_StrFromBuffer(gctx, res);
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
        // page addLineAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addLineAnnot, "Add 'Line' annot for points p1 and p2.")
        struct fz_annot_s *addLineAnnot(PyObject *p1, PyObject *p2)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_annot *annot = NULL;
            float col[3] = {0, 0, 0};
            float width  = 1.0f;
            fz_point a = JM_point_from_py(p1);
            fz_point b = JM_point_from_py(p2);
            fz_rect r  = {MIN(a.x, b.x), MIN(a.y, b.y), MAX(a.x, b.x), MAX(a.y, b.y)};
            fz_var(annot);
            fz_try(gctx)
            {
                assert_PDF(page);
                pdf_document *pdf = page->doc;
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_LINE);
                pdf_set_annot_line(gctx, annot, a, b);
                pdf_set_annot_border(gctx, annot, width);
                pdf_set_annot_color(gctx, annot, 3, col);
                r = fz_expand_rect(r, 3 * width);
                pdf_set_annot_rect(gctx, annot, r);
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) return NULL;
            fz_annot *fzannot = (fz_annot *) annot;
            return fz_keep_annot(gctx, fzannot);
        }

        //---------------------------------------------------------------------
        // page addTextAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addTextAnnot, "Add a 'sticky note' at position 'point'.")
        struct fz_annot_s *addTextAnnot(PyObject *point, char *text)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_annot *annot = NULL;
            fz_point pos = JM_point_from_py(point);
            fz_var(annot);
            fz_try(gctx)
            {
                assert_PDF(page);
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_TEXT);
                pdf_set_text_annot_position(gctx, annot, pos);
                pdf_set_annot_contents(gctx, annot, text);
                pdf_set_annot_icon_name(gctx, annot, "Note");
                float col[3] = {0.9f, 0.9f, 0.0f};
                pdf_set_annot_color(gctx, annot, 3, col);
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) return NULL;
            fz_annot *fzannot = (fz_annot *) annot;
            return fz_keep_annot(gctx, fzannot);
        }

        //---------------------------------------------------------------------
        // page addInkAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addInkAnnot, "Add a 'handwriting' as a list of list of point-likes. Each sublist forms an independent stroke.")
        struct fz_annot_s *addInkAnnot(PyObject *list)
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
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx)
            {
                Py_CLEAR(p);
                Py_CLEAR(sublist);
                return NULL;
            }

            fz_annot *fzannot = (fz_annot *) annot;
            return fz_keep_annot(gctx, fzannot);
        }

        //---------------------------------------------------------------------
        // page addStampAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addStampAnnot, "Add a 'rubber stamp' in a rectangle.")
        struct fz_annot_s *addStampAnnot(PyObject *rect, int stamp = 0)
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
            fz_var(annot);
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
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) return NULL;
            fz_annot *fzannot = (fz_annot *) annot;
            return fz_keep_annot(gctx, fzannot);
        }

        //---------------------------------------------------------------------
        // page addFileAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addFileAnnot, "Add a 'FileAttachment' annotation at location 'point'.")
        struct fz_annot_s *addFileAnnot(PyObject *point, PyObject *buffer, char *filename, char *ufilename = NULL, char *desc = NULL)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            fz_annot *fzannot = NULL;
            pdf_annot *annot = NULL;
            char *data = NULL, *uf = ufilename, *d = desc;
            if (!ufilename) uf = filename;
            if (!desc) d = filename;
            size_t len = 0;
            fz_buffer *filebuf = NULL;
            fz_point p = JM_point_from_py(point);
            fz_rect r = {p.x, p.y, p.x + 20, p.y + 30};
            fz_var(annot);
            fz_try(gctx)
            {
                assert_PDF(page);
                annot = pdf_create_annot(gctx, page, ANNOT_FILEATTACHMENT);
                pdf_set_annot_rect(gctx, annot, r);
                pdf_set_annot_icon_name(gctx, annot, "PushPin");
                len = JM_CharFromBytesOrArray(buffer, &data);
                filebuf = fz_new_buffer_from_shared_data(gctx, data, len);
                pdf_obj *val = JM_embed_file(gctx, page->doc, filebuf,
                                             filename, uf, d);
                pdf_dict_put(gctx, annot->obj, PDF_NAME(FS), val);
                pdf_dict_put_text_string(gctx, annot->obj, PDF_NAME(Contents), filename);
                float col[3] = {0.9f, 0.9f, 0.0f};
                pdf_set_annot_color(gctx, annot, 3, col);
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx) return NULL;
            fzannot = (fz_annot *) annot;
            return fz_keep_annot(gctx, fzannot);
        }

        //---------------------------------------------------------------------
        // page addStrikeoutAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addStrikeoutAnnot, "Strike out content in a rectangle or quadrilateral.")
        struct fz_annot_s *addStrikeoutAnnot(PyObject *rect)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            fz_annot *annot = NULL;
            fz_var(annot);
            fz_quad quad = JM_quad_from_py(rect);
            fz_try(gctx)
            {
                assert_PDF(page);
                annot = JM_AnnotTextmarker(gctx, page, quad, PDF_ANNOT_STRIKE_OUT);
            }
            fz_catch(gctx) return NULL;
            return fz_keep_annot(gctx, annot);
        }

        //---------------------------------------------------------------------
        // page addUnderlineAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addUnderlineAnnot, "Underline content in a rectangle or quadrilateral.")
        struct fz_annot_s *addUnderlineAnnot(PyObject *rect)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            fz_annot *annot = NULL;
            fz_var(annot);
            fz_quad quad = JM_quad_from_py(rect);
            fz_try(gctx)
            {
                assert_PDF(page);
                annot = JM_AnnotTextmarker(gctx, page, quad, PDF_ANNOT_UNDERLINE);
            }
            fz_catch(gctx) return NULL;
            return fz_keep_annot(gctx, annot);
        }

        //---------------------------------------------------------------------
        // page addSquigglyAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addSquigglyAnnot, "Wavy underline content in a rectangle or quadrilateral.")
        struct fz_annot_s *addSquigglyAnnot(PyObject *rect)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            fz_annot *annot = NULL;
            fz_var(annot);
            fz_quad quad = JM_quad_from_py(rect);
            fz_try(gctx)
            {
                assert_PDF(page);
                annot = JM_AnnotTextmarker(gctx, page, quad, PDF_ANNOT_SQUIGGLY);
            }
            fz_catch(gctx) return NULL;
            return fz_keep_annot(gctx, annot);
        }

        //---------------------------------------------------------------------
        // page addHighlightAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addHighlightAnnot, "Highlight content in a rectangle or quadrilateral.")
        struct fz_annot_s *addHighlightAnnot(PyObject *rect)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            fz_annot *annot = NULL;
            fz_var(annot);
            fz_quad quad = JM_quad_from_py(rect);
            fz_try(gctx)
            {
                assert_PDF(page);
                annot = JM_AnnotTextmarker(gctx, page, quad, PDF_ANNOT_HIGHLIGHT);
            }
            fz_catch(gctx) return NULL;
            return fz_keep_annot(gctx, annot);
        }

        //---------------------------------------------------------------------
        // page addRectAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addRectAnnot, "Add a 'Rectangle' annotation.")
        struct fz_annot_s *addRectAnnot(PyObject *rect)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            fz_annot *fzannot = NULL;
            fz_var(fzannot);
            fz_try(gctx)
            {
                assert_PDF(page);
                fzannot = JM_AnnotCircleOrRect(gctx, page, rect, PDF_ANNOT_SQUARE);
            }
            fz_catch(gctx) return NULL;
            return fz_keep_annot(gctx, fzannot);
        }

        //---------------------------------------------------------------------
        // page addCircleAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addCircleAnnot, "Add a 'Circle' annotation.")
        struct fz_annot_s *addCircleAnnot(PyObject *rect)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            fz_annot *fzannot = NULL;
            fz_var(fzannot);
            fz_try(gctx)
            {
                assert_PDF(page);
                fzannot = JM_AnnotCircleOrRect(gctx, page, rect, PDF_ANNOT_CIRCLE);
            }
            fz_catch(gctx) return NULL;
            return fz_keep_annot(gctx, fzannot);
        }

        //---------------------------------------------------------------------
        // page addPolylineAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addPolylineAnnot, "Add a 'Polyline' annotation for a sequence of points.")
        struct fz_annot_s *addPolylineAnnot(PyObject *points)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            fz_annot *fzannot = NULL;
            fz_var(fzannot);
            fz_try(gctx)
            {
                assert_PDF(page);
                fzannot = JM_AnnotMultiline(gctx, page, points, PDF_ANNOT_POLY_LINE);
            }
            fz_catch(gctx) return NULL;
            return fz_keep_annot(gctx, fzannot);
        }

        //---------------------------------------------------------------------
        // page addPolygonAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addPolygonAnnot, "Add a 'Polygon' annotation for a sequence of points.")
        struct fz_annot_s *addPolygonAnnot(PyObject *points)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            fz_annot *fzannot = NULL;
            fz_var(fzannot);
            fz_try(gctx)
            {
                assert_PDF(page);
                fzannot = JM_AnnotMultiline(gctx, page, points, PDF_ANNOT_POLYGON);
            }
            fz_catch(gctx) return NULL;
            return fz_keep_annot(gctx, fzannot);
        }

        //---------------------------------------------------------------------
        // page addFreetextAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addFreetextAnnot, "Add a 'FreeText' annotation in rectangle 'rect'.")
        struct fz_annot_s *addFreetextAnnot(PyObject *rect, char *text, float fontsize = 12, char *fontname = NULL, PyObject *color = NULL, int rotate = 0)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            float bcol[3] = {1.0f, 1.0f, 1.0f};    // border, box color: white
            float col[4] = {0.0f, 0.0f, 0.0f, 0.0f}; // std. text color: black
            int ncol = 3;
            JM_color_FromSequence(color, &ncol,  col);
            fz_rect r = JM_rect_from_py(rect);
            pdf_annot *annot = NULL;
            fz_var(annot);
            fz_try(gctx)
            {
                assert_PDF(page);
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_FREE_TEXT);
                pdf_set_annot_contents(gctx, annot, text);
                pdf_set_annot_color(gctx, annot, 3, bcol); // set rect colors
                pdf_dict_put_int(gctx, annot->obj, PDF_NAME(Rotate), rotate);

                pdf_set_text_annot_position(gctx, annot, fz_make_point(r.x0, r.y0));
                pdf_set_annot_rect(gctx, annot, r);
                // insert the default appearance string
                JM_make_annot_DA(gctx, annot, ncol, col, fontname, fontsize);
                pdf_update_annot(gctx, annot);
            }
            fz_always(gctx) {;}
            fz_catch(gctx) return NULL;
            fz_annot *fzannot = (fz_annot *) annot;
            return fz_keep_annot(gctx, fzannot);
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

                # Check if PDF already has our fonts.
                # If none insert all of them in a new object and store the xref.
                # Else only add any missing fonts.
                # To determine the situation, /DR object is checked.
                xref = 0
                ff = doc.FormFonts               # /DR object: existing fonts
                if not widget.text_font:         # ensure default
                    widget.text_font = "Helv"
                if not widget.text_font in ff:   # if no existent font ...
                    if not doc.isFormPDF or not ff:   # a fresh /AcroForm PDF!
                        xref = doc._getNewXref()      # insert all our fonts
                        doc._updateObject(xref, Widget_fontobjects)
                    else:                        # add any missing fonts
                        for k in Widget_fontdict.keys():
                            if not k in ff:      # add our font if missing
                                doc._addFormFont(k, Widget_fontdict[k])
                    widget._adjust_font()        # ensure correct font spelling
                widget._dr_xref = xref           # non-zero causes /DR creation

                # now create the /DA string
                if   len(widget.text_color) == 3:
                    fmt = "{:g} {:g} {:g} rg /{f:s} {s:g} Tf " + widget._text_da
                elif len(widget.text_color) == 1:
                    fmt = "{:g} g /{f:s} {s:g} Tf " + widget._text_da
                elif len(widget.text_color) == 4:
                    fmt = "{:g} {:g} {:g} {:g} k /{f:s} {s:g} Tf " + widget._text_da
                widget._text_da = fmt.format(*widget.text_color, f=widget.text_font,
                                             s=widget.text_fontsize)
                # create the widget at last
                annot = self._addWidget(widget)
                if annot:
                    annot.thisown = True
                    annot.parent = weakref.proxy(self) # owning page object
                    self._annot_refs[id(annot)] = annot
                return annot
        %}
        FITZEXCEPTION(_addWidget, !result)
        struct fz_annot_s *_addWidget(PyObject *Widget)
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
                JM_PyErr_Clear;

                char *field_name = JM_Python_str_AsChar(PyObject_GetAttrString(Widget,
                                                        "field_name"));
                JM_PyErr_Clear;

                widget = pdf_create_widget(gctx, pdf, page, field_type, field_name);
                JM_Python_str_DelForPy3(field_name);
                JM_PyErr_Clear;
                annot = (pdf_annot *) widget;

                //-------------------------------------------------------------
                // now field exists, adjust its properties
                //-------------------------------------------------------------
                JM_set_widget_properties(gctx, annot, Widget, field_type);
            }
            fz_always(gctx) JM_PyErr_Clear;
            fz_catch(gctx) return NULL;
            fz_annot *fzannot = (fz_annot *) annot;
            return fz_keep_annot(gctx, fzannot);
        }

        //---------------------------------------------------------------------
        // getDisplayList()
        //---------------------------------------------------------------------
        FITZEXCEPTION(getDisplayList, !result)
        PARENTCHECK(getDisplayList)
        struct fz_display_list_s *getDisplayList()
        {
            fz_display_list *dl = NULL;
            fz_try(gctx) dl = fz_new_display_list_from_page(gctx, $self);
            fz_catch(gctx) return NULL;
            return dl;
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
            return NONE;
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
        %pythoncode %{firstLink = property(loadLinks)%}

        //---------------------------------------------------------------------
        // firstAnnot
        //---------------------------------------------------------------------
        PARENTCHECK(firstAnnot)
        %feature("autodoc","Points to first annotation on page") firstAnnot;
        %pythonappend firstAnnot
%{if val:
    val.thisown = True
    val.parent = weakref.proxy(self) # owning page object
    self._annot_refs[id(val)] = val%}
        %pythoncode %{@property%}
        struct fz_annot_s *firstAnnot()
        {
            fz_annot *annot;
            fz_try(gctx) annot = fz_first_annot(gctx, $self);
            fz_catch(gctx) annot = NULL;
            if (annot) fz_keep_annot(gctx, annot);
            return annot;
        }

        /*********************************************************************/
        // Page.deleteLink() - delete link
        /*********************************************************************/
        PARENTCHECK(deleteLink)
        %feature("autodoc","Delete link if PDF") deleteLink;
        %pythonappend deleteLink
%{if linkdict["xref"] == 0: return
linkid = linkdict["id"]
try:
    linkobj = self._annot_refs[linkid]
    linkobj._erase()
except:
    pass
%}
        void deleteLink(PyObject *linkdict)
        {
            if (!linkdict) return;               // have no parameter
            if (!PyDict_Check(linkdict)) return; // have no dictionary
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            if (!page) return;                   // have no PDF
            int xref = (int) PyInt_AsLong(PyDict_GetItemString(linkdict, "xref"));
            if (xref < 1) return;                // invalid xref
            pdf_obj *annots = pdf_dict_get(gctx, page->obj, PDF_NAME(Annots));
            if (!annots) return;                 // have no annotations
            int len = pdf_array_len(gctx, annots);
            int i, oxref = 0;
            for (i = 0; i < len; i++)
            {
                oxref = pdf_to_num(gctx, pdf_array_get(gctx, annots, i));
                if (xref == oxref) break;        // found xref in annotations
            }
            if (xref != oxref) return;           // xref not in annotations
            pdf_array_delete(gctx, annots, i);   // delete entry in annotations
            pdf_delete_object(gctx, page->doc, xref);      // delete link object
            pdf_dict_put(gctx, page->obj, PDF_NAME(Annots), annots);
            refresh_link_table(gctx, page);            // reload link / annot tables
            page->doc->dirty = 1;
            return;
        }

        /*********************************************************************/
        // Page.deleteAnnot() - delete annotation and return the next one
        /*********************************************************************/
        PARENTCHECK(deleteAnnot)
        %feature("autodoc","Delete annot if PDF and return next one") deleteAnnot;
        %pythonappend deleteAnnot
%{if val:
    val.thisown = True
    val.parent = weakref.proxy(self) # owning page object
    val.parent._annot_refs[id(val)] = val
fannot._erase()
%}
        struct fz_annot_s *deleteAnnot(struct fz_annot_s *fannot)
        {
            if (!fannot) return NULL;
            fz_annot *nextannot = fz_next_annot(gctx, fannot);  // store next
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            if (!page)                 // no PDF, just return next annotation
                {
                if (nextannot) fz_keep_annot(gctx, nextannot);
                return nextannot;
                }
            pdf_annot *pannot = pdf_annot_from_fz_annot(gctx, fannot);
            pdf_delete_annot(gctx, page, pannot);
            if (nextannot) fz_keep_annot(gctx, nextannot);
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
            return NONE;
        }

        /*********************************************************************/
        // Page._addAnnot_FromString
        // Add new links provided as an array of string object definitions.
        /*********************************************************************/
        FITZEXCEPTION(_addAnnot_FromString, !result)
        PARENTCHECK(_addAnnot_FromString)
        PyObject *_addAnnot_FromString(PyObject *linklist)
        {
            pdf_obj *annots, *annots_arr, *annot, *ind_obj, *new_array;
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            PyObject *txtpy;
            char *text;
            int lcount = (int) PySequence_Size(linklist); // new object count
            if (lcount < 1) return NONE;
            int i;
            fz_try(gctx)
            {
                assert_PDF(page);                // make sure we have a PDF
                // get existing annots array
                annots = pdf_dict_get(gctx, page->obj, PDF_NAME(Annots));
                if (annots)
                    {
                        if (pdf_is_indirect(gctx, annots))
                            annots_arr = pdf_resolve_indirect(gctx, annots);
                        else annots_arr = annots;
                    }
                else
                    annots_arr = NULL;
                int new_len = lcount;
                if (annots_arr) new_len += pdf_array_len(gctx, annots_arr);
                // allocate new array of old plus new size
                new_array = pdf_new_array(gctx, page->doc, new_len);
                if (annots_arr)
                {   // copy existing annots to new array
                    for (i = 0; i < pdf_array_len(gctx, annots_arr); i++)
                            pdf_array_push(gctx, new_array, pdf_array_get(gctx, annots_arr, i));
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
                pdf_dict_put_drop(gctx, page->obj, PDF_NAME(Annots), new_array);
                refresh_link_table(gctx, page);
            }
            fz_catch(gctx) return NULL;
            page->doc->dirty = 1;
            return NONE;
        }

        //---------------------------------------------------------------------
        // Page._getLinkXrefs - get list of link xref numbers.
        // Return None for non-PDF
        //---------------------------------------------------------------------
        PyObject *_getLinkXrefs()
        {
            pdf_obj *annots, *annots_arr, *link, *obj;
            int i, lcount;
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            PyObject *linkxrefs = PyList_New(0);
            if (!page) return linkxrefs;         // empty list for non-PDF
            annots = pdf_dict_get(gctx, page->obj, PDF_NAME(Annots));
            if (!annots) return linkxrefs;
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
                    PyList_Append(linkxrefs, Py_BuildValue("i", pdf_to_num(gctx, link)));
            }
            return linkxrefs;
        }

        //---------------------------------------------------------------------
        // clean contents stream
        //---------------------------------------------------------------------
        FITZEXCEPTION(_cleanContents, !result)
        PARENTCHECK(_cleanContents)
        PyObject *_cleanContents()
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_annot *annot;
            fz_try(gctx)
            {
                assert_PDF(page);
                pdf_clean_page_contents(gctx, page->doc, page, NULL, NULL, NULL, 1, 0);
                for (annot = pdf_first_annot(gctx, page); annot != NULL; annot = pdf_next_annot(gctx, annot))
                {
                    pdf_clean_annot_contents(gctx, page->doc, annot, NULL, NULL, NULL, 1, 0);
                }
            }
            fz_catch(gctx) return NULL;
            page->doc->dirty = 1;
            return NONE;
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
                resources = pdf_dict_get(gctx, tpageref, PDF_NAME(Resources));
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
        const char *_imgname=NULL)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_document *pdf;
            fz_pixmap *pm = NULL;
            fz_pixmap *pix = NULL;
            fz_image *mask = NULL;
            fz_separations *seps = NULL;
            pdf_obj *resources, *subres, *ref;
            fz_buffer *res = NULL, *nres = NULL,  *imgbuf = NULL;
            fz_matrix mat = JM_matrix_from_py(matrix); // pre-calculated
            char *streamdata = NULL;
            size_t streamlen = JM_CharFromBytesOrArray(stream, &streamdata);

            const char *template = " q %g %g %g %g %g %g cm /%s Do Q ";
            char *cont = NULL;
            
            fz_image *zimg = NULL, *image = NULL;
            fz_try(gctx)
            {
                pdf = page->doc;

                // get objects "Resources" & "XObject"
                resources = pdf_dict_get(gctx, page->obj, PDF_NAME(Resources));
                subres = pdf_dict_get(gctx, resources, PDF_NAME(XObject));
                if (!subres)           // has no XObject yet, create one
                {
                    subres = pdf_new_dict(gctx, pdf, 10);
                    pdf_dict_putl_drop(gctx, page->obj, subres, PDF_NAME(Resources), PDF_NAME(XObject), NULL);
                }

                // create the image
                if (filename || streamlen > 0)
                {
                    if (!streamlen)
                        image = fz_new_image_from_file(gctx, filename);
                    else
                    {
                        imgbuf = fz_new_buffer_from_copied_data(gctx,
                                                   streamdata, streamlen);
                        image = fz_new_image_from_buffer(gctx, imgbuf);
                    }

                    // test alpha channel (would require SMask creation)
                    pix = fz_get_pixmap_from_image(gctx, image, NULL, NULL, 0, 0);
                    if (pix->alpha == 1)
                    {   // have alpha, therefore create a mask
                        pm = fz_convert_pixmap(gctx, pix, NULL, NULL, NULL, NULL, 1);
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
                    {   // pixmap has alpha, therefore create an SMask
                        pm = fz_convert_pixmap(gctx, pixmap, NULL, NULL, NULL, NULL, 1);
                        pm->alpha = 0;
                        pm->colorspace = fz_keep_colorspace(gctx, fz_device_gray(gctx));
                        mask = fz_new_image_from_pixmap(gctx, pm, NULL);
                        image = fz_new_image_from_pixmap(gctx, pixmap, mask);
                    }
                }
                // image created - now put it in the PDF
                ref = pdf_add_image(gctx, pdf, image, 0);
                pdf_dict_puts(gctx, subres, _imgname, ref);  // store ref-name

                // prep contents stream buffer with invoking command
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
            return NONE;
        }

        //---------------------------------------------------------------------
        // insert font
        //---------------------------------------------------------------------
        %pythoncode
%{
def insertFont(self, fontname="helv", fontfile=None, fontbuffer=None,
               set_simple=False, wmode=0, encoding=0):
    doc = self.parent
    if not doc:
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
            char *data = NULL;
            int size, ixref = 0, index = 0, simple = 0;
            PyObject *value;
            PyObject *exto = NULL;
            fz_try(gctx)
            {
                assert_PDF(page);
                pdf = page->doc;
                // get the objects /Resources, /Resources/Font
                resources = pdf_dict_get(gctx, page->obj, PDF_NAME(Resources));
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
                    exto = Py_BuildValue("s", "n/a");
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
                    exto = Py_BuildValue("s", "n/a");
                    simple = 1;
                    goto weiter;
                }

                if (fontfile)
                    font = fz_new_font_from_file(gctx, NULL, fontfile, idx, 0);
                else
                {
                    size = (int) JM_CharFromBytesOrArray(fontbuffer, &data);
                    if (!size) THROWMSG("one of fontfile, fontbuffer must be given");
                    font = fz_new_font_from_memory(gctx, NULL, data, size, idx, 0);
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

                PyObject *name = Py_BuildValue("s", pdf_to_name(gctx,
                            pdf_dict_get(gctx, font_obj, PDF_NAME(BaseFont))));

                PyObject *subt = Py_BuildValue("s", pdf_to_name(gctx,
                            pdf_dict_get(gctx, font_obj, PDF_NAME(Subtype))));

                if (!exto)
                    exto = Py_BuildValue("s", fontextension(gctx, pdf, ixref));

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
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return value;
        }

        //---------------------------------------------------------------------
        // Get page transformation matrix
        //---------------------------------------------------------------------
        PARENTCHECK(_getTransformation)
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
            fz_try(gctx)
            {
                assert_PDF(page);           // only works for PDF
                contents = pdf_dict_get(gctx, page->obj, PDF_NAME(Contents));
                list = PyList_New(0);       // init an empty list
                if (pdf_is_array(gctx, contents))     // may be several
                {   for (i=0; i < pdf_array_len(gctx, contents); i++)
                    {
                        icont = pdf_array_get(gctx, contents, i);
                        xref = pdf_to_num(gctx, icont);
                        PyList_Append(list,  Py_BuildValue("i", xref));
                    }
                }
                else if (contents)          // at most 1 object there
                {
                    xref = pdf_to_num(gctx, contents);
                    PyList_Append(list, Py_BuildValue("i", xref));
                }
            }
            fz_catch(gctx) return NULL;
            return list;
        }

        //---------------------------------------------------------------------
        // Set given object to be the /Contents of a page
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
            return NONE;
        }

        %pythoncode %{
        def __str__(self):
            CheckParent(self)
            x = self.parent.name
            if self.parent.streamlen > 0:
                x += " (memory)"
            if x == "":
                x = "<new PDF>"
            return "page %s of %s" % (self.number, x)

        def __repr__(self):
            CheckParent(self)
            x = self.parent.name
            if self.parent.streamlen > 0:
                x += " (memory)"
            if x == "":
                x = "<new PDF>"
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

        def getFontList(self):
            CheckParent(self)
            return self.parent.getPageFontList(self.number)

        def getImageList(self):
            CheckParent(self)
            return self.parent.getPageImageList(self.number)

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
                pm = fz_convert_pixmap(gctx, spix, cs, NULL, NULL, NULL, 1);
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
            char *data = NULL;
            int n = fz_colorspace_n(gctx, cs);
            int stride = (n + alpha)*w;
            fz_separations *seps = NULL;
            fz_pixmap *pm = NULL;
            size_t size = JM_CharFromBytesOrArray(samples, &data);
            fz_try(gctx)
            {
                if (size < 1) THROWMSG("invalid arg type samples");
                if (stride * h != size) THROWMSG("invalid arg len samples");
                pm = fz_new_pixmap_with_data(gctx, cs, w, h, seps, alpha, stride, data);
            }
            fz_catch(gctx) return NULL;
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
                if (!filename) THROWMSG("invalid argument type");
                img = fz_new_image_from_file(gctx, filename);
                pm = fz_get_pixmap_from_image(gctx, img, NULL, NULL, NULL, NULL);
            }
            fz_always(gctx) fz_drop_image(gctx, img);
            fz_catch(gctx) return NULL;
            return pm;
        }

        //---------------------------------------------------------------------
        // create pixmap from in-memory image
        //---------------------------------------------------------------------
        fz_pixmap_s(PyObject *imagedata)
        {
            size_t size = 0;
            char *streamdata;
            fz_buffer *data = NULL;
            fz_image *img = NULL;
            fz_pixmap *pm = NULL;
            fz_try(gctx)
            {
                size = JM_CharFromBytesOrArray(imagedata, &streamdata);
                if (size < 1) THROWMSG("bad image data");
                data = fz_new_buffer_from_shared_data(gctx,
                              streamdata, size);
                img = fz_new_image_from_buffer(gctx, data);
                pm = fz_get_pixmap_from_image(gctx, img, NULL, NULL, NULL, NULL);
            }
            fz_always(gctx)
            {
                fz_drop_image(gctx, img);
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
        void tintWith(int red, int green, int blue)
        {
            fz_tint_pixmap(gctx, $self, red, green, blue);
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
            return NONE;
        }

        //----------------------------------------------------------------------
        // set alpha values
        //----------------------------------------------------------------------
        FITZEXCEPTION(setAlpha, !result)
        PyObject *setAlpha(PyObject *alphavalues=NULL)
        {
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
                    data_len = (int) JM_CharFromBytesOrArray(alphavalues, &data);
                    if (data_len && data_len < w * h)
                        THROWMSG("not enough alpha values");
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
            fz_catch(gctx) return NULL;
            return NONE;
        }

        //----------------------------------------------------------------------
        // Pixmap._getImageData
        //----------------------------------------------------------------------
        FITZEXCEPTION(_getImageData, !result)
        PyObject *_getImageData(int format)
        {
            fz_output *out = NULL;
            fz_buffer *res = NULL;
            // the following will be returned:
            PyObject *barray = NULL;
            fz_try(gctx)
            {
                size_t size = fz_pixmap_stride(gctx, $self) * $self->h;
                res = fz_new_buffer(gctx, size);
                out = fz_new_output_with_buffer(gctx, res);
                out->seek = JM_SeekDummy;        // ignore seek calls
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
                    case(4):
                        fz_write_pixmap_as_tga(gctx, out, $self);
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
    return self._getImageData(idx)

def getPNGdata(self):
    return self._getImageData(1)

def getPNGData(self):
    return self._getImageData(1)
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
                    case(4):
                        fz_save_pixmap_as_tga(gctx, $self, filename);
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
            return NONE;
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
                for (j=0; j < n; j++)
                {
                    PyList_SetItem(p, j, Py_BuildValue("i", $self->samples[i + j]));
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
            return NONE;
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
#define CS_RGB  1
#define CS_GRAY 2
#define CS_CMYK 3
%inline %{
    #define CS_RGB  1
    #define CS_GRAY 2
    #define CS_CMYK 3
%}
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
            return Py_BuildValue("s", fz_colorspace_name(gctx, $self));
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
                fz_stext_options opts;
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
            return Py_BuildValue("s", $self->uri);
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
//----------------------------------------------------------------------------
// annotation types
//----------------------------------------------------------------------------
#define ANNOT_TEXT 0
#define ANNOT_LINK 1
#define ANNOT_FREETEXT 2
#define ANNOT_LINE 3
#define ANNOT_SQUARE 4
#define ANNOT_CIRCLE 5
#define ANNOT_POLYGON 6
#define ANNOT_POLYLINE 7
#define ANNOT_HIGHLIGHT 8
#define ANNOT_UNDERLINE 9
#define ANNOT_SQUIGGLY 10
#define ANNOT_STRIKEOUT 11
#define ANNOT_STAMP 12
#define ANNOT_CARET 13
#define ANNOT_INK 14
#define ANNOT_POPUP 15
#define ANNOT_FILEATTACHMENT 16
#define ANNOT_SOUND 17
#define ANNOT_MOVIE 18
#define ANNOT_WIDGET 19
#define ANNOT_SCREEN 20
#define ANNOT_PRINTERMARK 21
#define ANNOT_TRAPNET 22
#define ANNOT_WATERMARK 23
#define ANNOT_3D 24

//----------------------------------------------------------------------------
// annotation flag bits
//----------------------------------------------------------------------------
#define ANNOT_XF_Invisible 1 << (1-1)
#define ANNOT_XF_Hidden 1 << (2-1)
#define ANNOT_XF_Print 1 << (3-1)
#define ANNOT_XF_NoZoom 1 << (4-1)
#define ANNOT_XF_NoRotate 1 << (5-1)
#define ANNOT_XF_NoView 1 << (6-1)
#define ANNOT_XF_ReadOnly 1 << (7-1)
#define ANNOT_XF_Locked 1 << (8-1)
#define ANNOT_XF_ToggleNoView 1 << (9-1)
#define ANNOT_XF_LockedContents 1 << (10-1)

//----------------------------------------------------------------------------
// annotation line ending styles
//----------------------------------------------------------------------------
#define ANNOT_LE_None 0
#define ANNOT_LE_Square 1
#define ANNOT_LE_Circle 2
#define ANNOT_LE_Diamond 3
#define ANNOT_LE_OpenArrow 4
#define ANNOT_LE_ClosedArrow 5
#define ANNOT_LE_Butt 6
#define ANNOT_LE_ROpenArrow 7
#define ANNOT_LE_RClosedArrow 8
#define ANNOT_LE_Slash 9

//----------------------------------------------------------------------------
// annotation field (widget) types
//----------------------------------------------------------------------------
#define ANNOT_WG_NOT_WIDGET -1
#define ANNOT_WG_PUSHBUTTON 0
#define ANNOT_WG_CHECKBOX 1
#define ANNOT_WG_RADIOBUTTON 2
#define ANNOT_WG_TEXT 3
#define ANNOT_WG_LISTBOX 4
#define ANNOT_WG_COMBOBOX 5
#define ANNOT_WG_SIGNATURE 6

//----------------------------------------------------------------------------
// annotation text widget subtypes
//----------------------------------------------------------------------------
#define ANNOT_WG_TEXT_UNRESTRAINED 0
#define ANNOT_WG_TEXT_NUMBER 1
#define ANNOT_WG_TEXT_SPECIAL 2
#define ANNOT_WG_TEXT_DATE 3
#define ANNOT_WG_TEXT_TIME 4

//----------------------------------------------------------------------------
// annotation widget flags
//----------------------------------------------------------------------------
// Common to all field types
#define WIDGET_Ff_ReadOnly 1
#define WIDGET_Ff_Required 2
#define WIDGET_Ff_NoExport 4

// Text fields
#define WIDGET_Ff_Multiline 4096
#define WIDGET_Ff_Password 8192

#define WIDGET_Ff_FileSelect 1048576
#define WIDGET_Ff_DoNotSpellCheck 4194304
#define WIDGET_Ff_DoNotScroll 8388608
#define WIDGET_Ff_Comb 16777216
#define WIDGET_Ff_RichText 33554432

// Button fields
#define WIDGET_Ff_NoToggleToOff 16384
#define WIDGET_Ff_Radio 32768
#define WIDGET_Ff_Pushbutton 65536
#define WIDGET_Ff_RadioInUnison 33554432

// Choice fields
#define WIDGET_Ff_Combo 131072
#define WIDGET_Ff_Edit 262144
#define WIDGET_Ff_Sort 524288
#define WIDGET_Ff_MultiSelect 2097152
#define WIDGET_Ff_CommitOnSelCHange 67108864

%rename(Annot) fz_annot_s;
%nodefaultctor;
struct fz_annot_s
{
    %extend
    {
        ~fz_annot_s()
        {
            DEBUGMSG1("annot");
            fz_drop_annot(gctx, $self);
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
            fz_rect r = fz_bound_annot(gctx, $self);
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
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            int i = 0;
            if(annot) i = pdf_to_num(gctx, annot->obj);
            return Py_BuildValue("i", i);
        }

        //---------------------------------------------------------------------
        // annotation get decompressed appearance stream source
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getAP, !result)
        %feature("autodoc","Get contents source of a PDF annot") _getAP;
        PyObject *_getAP()
        {
            PyObject *r = NONE;
            fz_buffer *res = NULL;
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;
            fz_try(gctx)
            {
                pdf_obj *ap = pdf_dict_getl(gctx, annot->obj, PDF_NAME(AP),
                                              PDF_NAME(N), NULL);
                
                if (pdf_is_stream(gctx, ap))  res = pdf_load_stream(gctx, ap);
                if (res) r = JM_BinFromBuffer(gctx, res);
            }
            fz_always(gctx) fz_drop_buffer(gctx, res);
            fz_catch(gctx) return NONE;
            return r;
        }

        //---------------------------------------------------------------------
        // annotation update /AP stream
        //---------------------------------------------------------------------
        FITZEXCEPTION(_setAP, !result)
        %feature("autodoc","Update contents source of a PDF annot") _setAP;
        PyObject *_setAP(PyObject *ap, int rect = 0)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            fz_buffer *res = NULL;
            fz_var(res);
            fz_try(gctx)
            {
                assert_PDF(annot);
                pdf_obj *apobj = pdf_dict_getl(gctx, annot->obj, PDF_NAME(AP),
                                              PDF_NAME(N), NULL);
                if (!apobj) THROWMSG("annot has no /AP/N object");
                if (!pdf_is_stream(gctx, apobj))
                    THROWMSG("/AP/N object is no stream");
                char *c = NULL;
                size_t len = JM_CharFromBytesOrArray(ap, &c);
                if (!c) THROWMSG("invalid /AP stream argument");
                res = fz_new_buffer_from_copied_data(gctx, c, strlen(c));
                JM_update_stream(gctx, annot->page->doc, apobj, res);
                if (rect)
                {
                    fz_rect bbox = pdf_dict_get_rect(gctx, annot->obj, PDF_NAME(Rect));
                    pdf_dict_put_rect(gctx, apobj, PDF_NAME(BBox), bbox);
                    annot->ap = NULL;
                }
            }
            fz_always(gctx)
                fz_drop_buffer(gctx, res);
            fz_catch(gctx) return NULL;
            return NONE;
        }

        //---------------------------------------------------------------------
        // annotation set rectangle
        //---------------------------------------------------------------------
        void setRect(PyObject *rect)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return;
            fz_try(gctx)
            {
                pdf_set_annot_rect(gctx, annot, JM_rect_from_py(rect));
            }
            fz_catch(gctx) {;}
            return;
        }

        //---------------------------------------------------------------------
        // annotation vertices (for "Line", "Polgon", "Ink", etc.
        //---------------------------------------------------------------------
        PARENTCHECK(vertices)
        %feature("autodoc","Point coordinates for various annot types") vertices;
        %pythoncode %{@property%}
        PyObject *vertices()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;                  // not a PDF!
            PyObject *res = NONE;
            pdf_obj *o;
            //----------------------------------------------------------------
            // The following objects occur in different annotation types.
            // So we are sure that o != NULL occurs at most once.
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
            if (o) goto weiter;
            return res;

            weiter:;
            int i, n;
            fz_point point;             // point object to work with
            fz_matrix page_ctm;         // page transformation matrix
            pdf_page_transform(gctx, annot->page, NULL, &page_ctm);
            res = PyList_New(0);        // create Python list
            n = pdf_array_len(gctx, o);
            for (i = 0; i < n; i += 2)
            {
                point.x = pdf_to_real(gctx, pdf_array_get(gctx, o, i));
                point.y = pdf_to_real(gctx, pdf_array_get(gctx, o, i+1));
                point = fz_transform_point(point, page_ctm);
                PyList_Append(res, Py_BuildValue("ff", point.x, point.y));
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
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;
            return JM_annot_colors(gctx, annot->obj);
        }

        //---------------------------------------------------------------------
        // annotation update appearance
        //---------------------------------------------------------------------
        PARENTCHECK(update)
        %feature("autodoc","Update the appearance of an annotation.") update;
        %pythonprepend update %{
        if self.type[0] == ANNOT_WIDGET:
            print("Use updateWidget method for form fields.")
            return False%}
        %pythonappend update %{
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
           enclose their syntax in a string pair "q ... Q", which may cause
           Adobe and other readers not to display the annot.

        """
        if not val is True:  # skip if something went wrong
            return val
        
        def color_string(cs, code):
            """Return valid PDF color operator for a given color sequence.
            """
            if cs is None: return ""
            if hasattr(cs, "__float__") or len(cs) == 1:
                app = " g\n" if code == "f" else " G\n"
            elif len(cs) == 3:
                app = " rg\n" if code == "f" else " RG\n"
            else:
                app = " k\n" if code == "f" else " K\n"
            if hasattr(cs, "__len__"):
                col = " ".join(map(str, cs)) + app
            else:
                col = "%g" % cs + app
            return bytes(col, "utf8") if not fitz_py2 else col

        type   = self.type[0]               # get the annot type
        dt     = self.border["dashes"]      # get the dashes spec
        bwidth = self.border["width"]       # get border line width
        stroke = self.colors["stroke"]      # get the stroke color
        fill   = self.colors["fill"]        # get the fill color
        rect   = None                       # used if we change the rect here
        bfill  = color_string(fill, "f")
        p_ctm  = self.parent._getTransformation() # page transformation matrix
        imat   = ~p_ctm                     # inverse page transf. matrix
        
        line_end_le, line_end_ri = 0, 0     # line end codes
        if self.lineEnds:
            line_end_le, line_end_ri = self.lineEnds

        ap     = self._getAP()              # get the annot operator source
        ap_updated = False                  # assume we did nothing

        if type == ANNOT_FREETEXT:
            CheckColor(fill_color)
            CheckColor(border_color)
            CheckColor(text_color)

            ap_tab = ap.splitlines()        # split AP stream into lines
            idx_BT = ap_tab.index(b"BT")    # line no. of text start
            # to avoid effort, we rely on a fixed format generated by MuPDF for
            # this annot type: line 0 = fill color, line 5 border color, etc.
            if fill_color is not None:
                ap_tab[0] = color_string(fill_color, "f")
                ap_updated = True
            else:
                ap_tab[0] = ap_tab[1] = ap_tab[2] = b""
                ap_updated = True

            if idx_BT == 7:
                if bwidth > 0:
                    if border_color is not None:
                        ap_tab[4] = color_string(border_color, "s")
                        ap_updated = True
                else: # for zero border width suppress border
                    ap_tab[3] = b"0 w"
                    ap_tab[4] = ap_tab[5] = ap_tab[6] = b""
                    ap_updated = True

            if text_color is not None:
                ap_tab[idx_BT + 1] = color_string(text_color, "f")
                ap_updated = True

            if fontsize > 0.0:
                x = ap_tab[idx_BT + 2].split()
                x[1] = b"%g" % fontsize
                ap_tab[idx_BT + 2] = b" ".join(x)
                ap_updated = True

            if ap_updated:
                ap = b"\n".join(ap_tab)         # updated AP stream

        if bfill != "":
            if type == ANNOT_POLYGON:
                ap = ap[:-1] + bfill + b"b" # close, fill, and stroke
                ap_updated = True
            elif type == ANNOT_POLYLINE:
                ap = ap[:-1] + bfill + b"B" # fill and stroke
                ap_updated = True

        # Dashes not handled by MuPDF, so we do it here.
        if dt:
            dash = "[" + " ".join(map(str, dt)) + "] d\n"
            ap = dash.encode("utf-8") + ap
            # reset dashing - only applies for LINE annots with line ends given
            ap = ap.replace(b"\nS\n", b"\nS\n[] d\n", 1)
            ap_updated = True

        # Opacity not handled by MuPDF, so we do it here. The /ExtGState object
        # "Alp0" referenced here has already been added by our C code.
        if 0 <= self.opacity < 1:
            ap = b"/Alp0 gs\n" + ap
            ap_updated = True

        #----------------------------------------------------------------------
        # the following handles line end symbols for 'Polygon' and 'Polyline
        #----------------------------------------------------------------------
        if max(line_end_le, line_end_ri) > 0 and type in (ANNOT_POLYGON, ANNOT_POLYLINE):

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
        self._cleanContents()%}

        PyObject *update(float fontsize = 0.0f,
                         PyObject *text_color = NULL,
                         PyObject *border_color=NULL,
                         PyObject *fill_color = NULL,
                         int rotate = -1)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;
            int type = pdf_annot_type(gctx, annot);
            fz_try(gctx)
            {
                pdf_dirty_annot(gctx, annot); // enforce MuPDF /AP formatting
                if (type == PDF_ANNOT_FREE_TEXT && rotate >= 0)
                    pdf_dict_put_int(gctx, annot->obj, PDF_NAME(Rotate), rotate);
                pdf_update_annot(gctx, annot);
            }
            fz_catch(gctx)
            {
                PySys_WriteStderr("cannot update annot: '%s'\n", fz_caught_message(gctx));
                Py_RETURN_FALSE;
            }

            // check /AP object
            pdf_obj *ap = pdf_dict_getl(gctx, annot->obj, PDF_NAME(AP),
                                        PDF_NAME(N), NULL);
            if (!ap)
            {
                PySys_WriteStderr("annot has no /AP onject!\n");
                Py_RETURN_FALSE;
            }

            // get opacity
            pdf_obj *ca = pdf_dict_get(gctx, annot->obj, PDF_NAME(CA));
            if (!ca)              // no opacity given
                Py_RETURN_TRUE;

            pdf_obj *alp0 = pdf_new_dict(gctx, annot->page->doc, 2);
            pdf_dict_put(gctx, alp0, PDF_NAME(CA), ca);
            pdf_dict_put(gctx, alp0, PDF_NAME(ca), ca);
            pdf_obj *extg = pdf_new_dict(gctx, annot->page->doc, 1);
            pdf_dict_puts_drop(gctx, extg, "Alp0", alp0);
            pdf_dict_putl_drop(gctx, ap, extg, PDF_NAME(Resources),
                               PDF_NAME(ExtGState), NULL);
            pdf_dict_putl_drop(gctx, annot->obj, ap, PDF_NAME(AP), PDF_NAME(N), NULL);
            annot->ap = NULL;

            Py_RETURN_TRUE;
        }

        //---------------------------------------------------------------------
        // annotation set colors
        //---------------------------------------------------------------------
        PARENTCHECK(setColors)
        %feature("autodoc","setColors(dict)\nChanges the 'stroke' and 'fill' colors of an annotation. If provided, values must be lists of up to 4 floats.") setColors;
        void setColors(PyObject *colors)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return;
            if (!PyDict_Check(colors)) return;
            if (pdf_annot_type(gctx, annot) == PDF_ANNOT_WIDGET)
            {
                JM_Warning("use 'updateWidget' to change form fields");
                return;
            }
            PyObject *ccol, *icol;
            ccol = PyDict_GetItemString(colors, "stroke");
            icol = PyDict_GetItemString(colors, "fill");
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
                    pdf_set_annot_color(gctx, annot, n, col);
                fz_catch(gctx)
                    JM_Warning("cannot set stroke color for this annot type");
            }
            n = 0;
            if (icol)
                if (PySequence_Check(icol))
                    n = (int) PySequence_Size(icol);
            if (n>0)
            {
                if (!pdf_annot_has_interior_color(gctx, annot))
                {
                    JM_Warning("annot type has no fill color");
                    return;
                }
                for (i=0; i<n; i++)
                    col[i] = (float) PyFloat_AsDouble(PySequence_ITEM(icol, i));
                fz_try(gctx)
                    pdf_set_annot_interior_color(gctx, annot, n, col);
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
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;                   // no a PDF
            int i = pdf_annot_type(gctx, annot);
            // return nothing for invalid annot types
            if (!INRANGE(i, 2, 7)) return NONE;
            if (INRANGE(i, 4, 5)) return NONE;
            PyObject *res = Py_BuildValue("[ii]", 0, 0); // stanard
            pdf_obj *o = pdf_dict_gets(gctx, annot->obj, "LE");
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
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return;
            if (pdf_annot_has_line_ending_styles(gctx, annot))
                pdf_set_annot_line_ending_styles(gctx, annot, start, end);
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
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;             // not a PDF
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
        PARENTCHECK(opacity)
        %pythoncode %{@property%}
        PyObject *opacity()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            double opy = -1.0f;
            if (annot)
            {
                pdf_obj *ca = pdf_dict_get(gctx, annot->obj, PDF_NAME(CA));
                if (pdf_is_number(gctx, ca))
                    opy = pdf_to_real(gctx, ca);
            }
            return Py_BuildValue("f", opy);
        }

        //---------------------------------------------------------------------
        // annotation set opacity
        //---------------------------------------------------------------------
        PARENTCHECK(setOpacity)
        void setOpacity(float opacity)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return;             // not a PDF
            if (INRANGE(opacity, 0.0f, 1.0f))
                pdf_set_annot_opacity(gctx, annot, opacity);
            else
                pdf_set_annot_opacity(gctx, annot, 1.0f);
        }

        //---------------------------------------------------------------------
        // widget type
        //---------------------------------------------------------------------
        PARENTCHECK(widget_type)
        %pythoncode %{@property%}
        PyObject *widget_type()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            int wtype;
            if (!annot) return NONE;             // not a PDF

            wtype = pdf_field_type(gctx, pdf_get_bound_document(gctx, annot->obj), annot->obj);
            switch(wtype)
            {
                case(PDF_WIDGET_TYPE_PUSHBUTTON):
                    return Py_BuildValue("is", wtype, "PushButton");
                case(PDF_WIDGET_TYPE_CHECKBOX):
                    return Py_BuildValue("is", wtype, "CheckBox");
                case(PDF_WIDGET_TYPE_RADIOBUTTON):
                    return Py_BuildValue("is", wtype, "RadioButton");
                case(PDF_WIDGET_TYPE_TEXT):
                    return Py_BuildValue("is", wtype, "Text");
                case(PDF_WIDGET_TYPE_LISTBOX):
                    return Py_BuildValue("is", wtype, "ListBox");
                case(PDF_WIDGET_TYPE_COMBOBOX):
                    return Py_BuildValue("is", wtype, "ComboBox");
                case(PDF_WIDGET_TYPE_SIGNATURE):
                    return Py_BuildValue("is", wtype, "Signature");
                default:
                    return NONE;
            }
        }

        //---------------------------------------------------------------------
        // widget value
        //---------------------------------------------------------------------
        PARENTCHECK(widget_value)
        %pythoncode %{@property%}
        PyObject *widget_value()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;             // not a PDF
            if (pdf_annot_type(gctx, annot) != PDF_ANNOT_WIDGET)
                return NONE;
            int wtype = pdf_field_type(gctx, pdf_get_bound_document(gctx, annot->obj), annot->obj);
            switch(wtype)
            {
                case(PDF_WIDGET_TYPE_PUSHBUTTON):
                    return JM_pushbtn_state(gctx, annot);
                case(PDF_WIDGET_TYPE_CHECKBOX):
                    return JM_checkbox_state(gctx, annot);
                case(PDF_WIDGET_TYPE_RADIOBUTTON):
                    return JM_radiobtn_state(gctx, annot);
                case(PDF_WIDGET_TYPE_TEXT):
                    return JM_text_value(gctx, annot);
                case(PDF_WIDGET_TYPE_LISTBOX):
                    return JM_listbox_value(gctx, annot);
                case(PDF_WIDGET_TYPE_COMBOBOX):
                    return JM_combobox_value(gctx, annot);
                case(PDF_WIDGET_TYPE_SIGNATURE):
                    return JM_signature_value(gctx, annot);
                default:
                    return NONE;
            }
        }

        //---------------------------------------------------------------------
        // widget name
        //---------------------------------------------------------------------
        PARENTCHECK(widget_name)
        %pythoncode %{@property%}
        PyObject *widget_name()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;
            if (pdf_annot_type(gctx, annot) != PDF_ANNOT_WIDGET)
                return NONE;
            return PyString_FromString(pdf_field_name(gctx,
                                       pdf_get_bound_document(gctx, annot->obj),
                                       annot->obj));
        }

        //---------------------------------------------------------------------
        // widget list box / combo box choices
        //---------------------------------------------------------------------
        PARENTCHECK(widget_choices)
        %pythoncode %{@property%}
        PyObject *widget_choices()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;
            if (pdf_annot_type(gctx, annot) != PDF_ANNOT_WIDGET)
                return NONE;
            return JM_choice_options(gctx, annot);
        }

        //---------------------------------------------------------------------
        // annotation get attached file info
        //---------------------------------------------------------------------
        FITZEXCEPTION(fileInfo, !result)
        PARENTCHECK(fileInfo)
        %feature("autodoc","Retrieve attached file information.") fileInfo;
        PyObject *fileInfo()
        {
            PyObject *res = PyDict_New();             // create Python dict
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            char *filename = NULL;
            char *desc = NULL;
            int length = -1, size = -1;
            pdf_obj *stream = NULL, *o = NULL, *fs = NULL;

            fz_try(gctx)
            {
                assert_PDF(annot);
                int type = (int) pdf_annot_type(gctx, annot);
                if (type != ANNOT_FILEATTACHMENT)
                    THROWMSG("not a file attachment annot");
                stream = pdf_dict_getl(gctx, annot->obj, PDF_NAME(FS),
                                   PDF_NAME(EF), PDF_NAME(F), NULL);
                if (!stream) THROWMSG("bad PDF: file entry not found");
            }
            fz_catch(gctx) return NULL;

            fs = pdf_dict_get(gctx, annot->obj, PDF_NAME(FS));

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

            PyDict_SetItemString(res, "filename", JM_UNICODE(filename));
            PyDict_SetItemString(res, "desc", JM_UNICODE(desc));
            PyDict_SetItemString(res, "length", Py_BuildValue("i", length));
            PyDict_SetItemString(res, "size", Py_BuildValue("i", size));
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
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            pdf_obj *stream = NULL;
            fz_buffer *buf = NULL;
            fz_var(buf);
            fz_try(gctx)
            {
                assert_PDF(annot);
                int type = (int) pdf_annot_type(gctx, annot);
                if (type != ANNOT_FILEATTACHMENT)
                    THROWMSG("not a file attachment annot");
                stream = pdf_dict_getl(gctx, annot->obj, PDF_NAME(FS),
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
        // annotation update attached file content
        //---------------------------------------------------------------------
        FITZEXCEPTION(fileUpd, !result)
        PARENTCHECK(fileUpd)
        %feature("autodoc","Update annotation attached file content.") fileUpd;
        PyObject *fileUpd(PyObject *buffer=NULL, char *filename=NULL, char *ufilename=NULL, char *desc=NULL)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            pdf_document *pdf = NULL;       // to be filled in
            char *data = NULL;              // for new file content
            fz_buffer *res = NULL;          // for compressed content
            pdf_obj *stream = NULL, *fs = NULL;
            int64_t size = 0;
            fz_try(gctx)
            {
                assert_PDF(annot);          // must be a PDF
                pdf = annot->page->doc;     // this is the PDF
                int type = (int) pdf_annot_type(gctx, annot);
                if (type != ANNOT_FILEATTACHMENT)
                    THROWMSG("not a file attachment annot");
                stream = pdf_dict_getl(gctx, annot->obj, PDF_NAME(FS),
                                   PDF_NAME(EF), PDF_NAME(F), NULL);
                // the object for file content
                if (!stream) THROWMSG("bad PDF: file entry not found");
                
                fs = pdf_dict_get(gctx, annot->obj, PDF_NAME(FS));

                // file content is ignored if not bytes / bytearray
                size = (int64_t) JM_CharFromBytesOrArray(buffer, &data);
                if (size > 0)
                {
                    pdf_obj *s = pdf_new_int(gctx, size);
                    pdf_dict_put(gctx, stream, PDF_NAME(Filter),
                                 PDF_NAME(FlateDecode));

                    pdf_dict_putl_drop(gctx, stream, s,
                                       PDF_NAME(Params), PDF_NAME(Size), NULL);
                    res = JM_deflatebuf(gctx, data, size);
                    pdf_update_stream(gctx, pdf, stream, res, 1);
                }

                if (filename)               // new filename given
                {
                    pdf_dict_put_text_string(gctx, stream, PDF_NAME(F), filename);
                    pdf_dict_put_text_string(gctx, fs, PDF_NAME(F), filename);
                }

                if (ufilename)
                {
                    pdf_dict_put_text_string(gctx, stream, PDF_NAME(UF), filename);
                    pdf_dict_put_text_string(gctx, fs, PDF_NAME(UF), filename);
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
            return NONE;
        }

        //---------------------------------------------------------------------
        // annotation info
        //---------------------------------------------------------------------
        PARENTCHECK(info)
        %pythoncode %{@property%}
        PyObject *info()
        {
            PyObject *res = PyDict_New();
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return res;                   // not a PDF
            pdf_obj *o;
            char *c;
            c = (char *) pdf_annot_contents(gctx, annot);
            PyDict_SetItemString(res, "content", JM_UNICODE(c));

            o = pdf_dict_get(gctx, annot->obj, PDF_NAME(Name));
            c = (char *) pdf_to_name(gctx, o);
            PyDict_SetItemString(res, "name", JM_UNICODE(c));

            // Title, author
            o = pdf_dict_get(gctx, annot->obj, PDF_NAME(T));
            c = (char *) pdf_to_text_string(gctx, o);
            PyDict_SetItemString(res, "title", JM_UNICODE(c));

            // CreationDate
            o = pdf_dict_gets(gctx, annot->obj, "CreationDate");
            c = (char *) pdf_to_text_string(gctx, o);
            PyDict_SetItemString(res, "creationDate", JM_UNICODE(c));

            // ModDate
            o = pdf_dict_get(gctx, annot->obj, PDF_NAME(M));
            c = (char *) pdf_to_text_string(gctx, o);
            PyDict_SetItemString(res, "modDate", JM_UNICODE(c));

            // Subj
            o = pdf_dict_gets(gctx, annot->obj, "Subj");
            c = (char *) pdf_to_text_string(gctx, o);
            PyDict_SetItemString(res, "subject", JM_UNICODE(c));

            return res;
        }

        //---------------------------------------------------------------------
        // annotation set information
        //---------------------------------------------------------------------
        FITZEXCEPTION(setInfo, !result)
        PARENTCHECK(setInfo)
        PyObject *setInfo(PyObject *info)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            char *uc = NULL;

            // use this to indicate a 'markup' annot type
            int is_markup = pdf_annot_has_author(gctx, annot);
            fz_var(is_markup);
            fz_var(annot);
            fz_try(gctx)
            {
                assert_PDF(annot);
                if (!PyDict_Check(info))
                    THROWMSG("info not a dict");

                // contents
                uc = JM_Python_str_AsChar(PyDict_GetItemString(info, "content"));
                if (uc)
                {
                    pdf_set_annot_contents(gctx, annot, uc);
                    JM_Python_str_DelForPy3(uc);
                }

                if (is_markup)
                {
                    // title (= author)
                    uc = JM_Python_str_AsChar(PyDict_GetItemString(info, "title"));
                    if (uc)
                    {
                        pdf_set_annot_author(gctx, annot, uc);
                        JM_Python_str_DelForPy3(uc);
                    }

                    // creation date
                    uc = JM_Python_str_AsChar(PyDict_GetItemString(info,
                                              "creationDate"));
                    if (uc)
                    {
                        pdf_dict_put_text_string(gctx, annot->obj,
                                                 PDF_NAME(CreationDate), uc);
                        JM_Python_str_DelForPy3(uc);
                    }

                    // mod date
                    uc = JM_Python_str_AsChar(PyDict_GetItemString(info, "modDate"));
                    if (uc)
                    {
                        pdf_dict_put_text_string(gctx, annot->obj,
                                                 PDF_NAME(M), uc);
                        JM_Python_str_DelForPy3(uc);
                    }

                    // subject
                    uc = JM_Python_str_AsChar(PyDict_GetItemString(info, "subject"));
                    if (uc)
                    {
                        pdf_dict_puts_drop(gctx, annot->obj, "Subj",
                                           pdf_new_text_string(gctx, uc));
                        JM_Python_str_DelForPy3(uc);
                    }
                }
            }
            fz_catch(gctx) return NULL;
            return NONE;
        }

        //---------------------------------------------------------------------
        // annotation border
        //---------------------------------------------------------------------
        PARENTCHECK(border)
        %pythoncode %{@property%}
        PyObject *border()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;                   // not a PDF
            return JM_annot_border(gctx, annot->obj);
        }

        //---------------------------------------------------------------------
        // set annotation border
        //---------------------------------------------------------------------
        PARENTCHECK(setBorder)
        PyObject *setBorder(PyObject *border)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;                   // not a PDF
            return JM_annot_set_border(gctx, border, annot->page->doc, annot->obj);
        }

        //---------------------------------------------------------------------
        // annotation flags
        //---------------------------------------------------------------------
        PARENTCHECK(flags)
        %pythoncode %{@property%}
        int flags()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (annot) return pdf_annot_flags(gctx, annot);
            return -1;
        }

        //---------------------------------------------------------------------
        // annotation clean contents
        //---------------------------------------------------------------------
        FITZEXCEPTION(_cleanContents, !result)
        PARENTCHECK(_cleanContents)
        PyObject *_cleanContents()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(annot);
                pdf_clean_annot_contents(gctx, annot->page->doc, annot,
                                         NULL, NULL, NULL, 1, 0);
            }
            fz_catch(gctx) return NULL;
            pdf_dirty_annot(gctx, annot);
            return NONE;
        }

        //---------------------------------------------------------------------
        // set annotation flags
        //---------------------------------------------------------------------
        PARENTCHECK(setFlags)
        void setFlags(int flags)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (annot)
            {
                pdf_set_annot_flags(gctx, annot, flags);
                pdf_dirty_annot(gctx, annot);
            }
        }

        //---------------------------------------------------------------------
        // next annotation
        //---------------------------------------------------------------------
        PARENTCHECK(next)
        %pythonappend next
%{if val:
    val.thisown = True
    val.parent = self.parent # copy owning page object from previous annot
    val.parent._annot_refs[id(val)] = val%}
        %pythoncode %{@property%}
        struct fz_annot_s *next()
        {
            fz_annot *annot = fz_next_annot(gctx, $self);
            if (annot)
                fz_keep_annot(gctx, annot);
            return annot;
        }

        //---------------------------------------------------------------------
        // annotation pixmap
        //---------------------------------------------------------------------
        FITZEXCEPTION(getPixmap, !result)
        PARENTCHECK(getPixmap)
        struct fz_pixmap_s *getPixmap(PyObject *matrix = NULL, struct fz_colorspace_s *colorspace = NULL, int alpha = 0)
        {
            fz_matrix ctm = JM_matrix_from_py(matrix);
            struct fz_colorspace_s *cs = fz_device_rgb(gctx);
            fz_pixmap *pix = NULL;
            if (colorspace) cs = colorspace;

            fz_try(gctx)
                pix = fz_new_pixmap_from_annot(gctx, $self, ctm, cs, alpha);
            fz_catch(gctx) return NULL;
            return pix;
        }

        //---------------------------------------------------------------------
        // annotation _updateWidget - change PDF field information
        //---------------------------------------------------------------------
        FITZEXCEPTION(_updateWidget, !result)
        PARENTCHECK(_updateWidget)
        PyObject *_updateWidget(PyObject *Widget)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            pdf_document *pdf = pdf_get_bound_document(gctx, annot->obj);
            fz_try(gctx)
            {
                int field_type = (int) PyInt_AsLong(PyObject_GetAttrString(Widget,
                                                    "field_type"));
                JM_set_widget_properties(gctx, annot, Widget, field_type);
            }
            fz_always(gctx)
            {
                JM_PyErr_Clear;
            }
            fz_catch(gctx) return NULL;
            return NONE;
        }

        //---------------------------------------------------------------------
        // annotation _getWidget - PDF field information
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getWidget, !result)
        PARENTCHECK(_getWidget)
        PyObject *_getWidget(PyObject *Widget)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            pdf_document *pdf = annot->page->doc;
            pdf_widget *tw = (pdf_widget *) annot;
            Py_ssize_t i = 0, n = 0;
            fz_try(gctx)
            {
                char *border_style = pdf_field_border_style(gctx, pdf, annot->obj);
                PyObject_SetAttrString(Widget, "border_style",
                                       Py_BuildValue("s", border_style));

                float border_width = pdf_to_real(gctx, pdf_dict_getl(gctx, annot->obj,
                                      PDF_NAME(BS), PDF_NAME(W), NULL));
                if (border_width == 0.0f) border_width = 1.0f;
                PyObject_SetAttrString(Widget, "border_width",
                                       Py_BuildValue("f", border_width));

                pdf_obj *dashes = pdf_dict_getl(gctx, annot->obj,
                                      PDF_NAME(BS), PDF_NAME(D), NULL);
                if (pdf_is_array(gctx, dashes))
                {
                    n = (Py_ssize_t) pdf_array_len(gctx, dashes);
                    PyObject *d = PyList_New(n);
                    for (i = 0; i < n; i++)
                        PyList_SetItem(d, i, Py_BuildValue("i", pdf_to_int(gctx,
                                      pdf_array_get(gctx, dashes, (int) i))));

                    PyObject_SetAttrString(Widget, "border_dashes", d);
                    Py_CLEAR(d);
                }

                int text_maxlen = pdf_to_int(gctx, pdf_dict_get_inheritable(gctx, annot->obj, PDF_NAME(MaxLen)));
                PyObject_SetAttrString(Widget, "text_maxlen",
                                       Py_BuildValue("i", text_maxlen));

                // entry ignored for new / updated widgets
                int text_type = pdf_text_widget_content_type(gctx, pdf, tw);
                PyObject_SetAttrString(Widget, "text_type",
                                       Py_BuildValue("i", text_type));

                pdf_obj *bgcol = pdf_dict_getl(gctx, annot->obj,
                                               PDF_NAME(MK), PDF_NAME(BG), NULL);
                if (pdf_is_array(gctx, bgcol))
                {
                    n = (Py_ssize_t) pdf_array_len(gctx, bgcol);
                    PyObject *col = PyList_New(n);
                    for (i = 0; i < n; i++)
                        PyList_SetItem(col, i, Py_BuildValue("f",
                        pdf_to_real(gctx, pdf_array_get(gctx, bgcol, (int) i))));

                    PyObject_SetAttrString(Widget, "fill_color", col);
                    Py_CLEAR(col);
                }

                pdf_obj *bccol = pdf_dict_getl(gctx, annot->obj, PDF_NAME(MK), PDF_NAME(BC), NULL);

                if (pdf_is_array(gctx, bccol))
                {
                    n = (Py_ssize_t) pdf_array_len(gctx, bccol);
                    PyObject *col = PyList_New(n);
                    for (i = 0; i < n; i++)
                        PyList_SetItem(col, i, Py_BuildValue("f",
                        pdf_to_real(gctx, pdf_array_get(gctx, bccol, (int) i))));

                    PyObject_SetAttrString(Widget, "border_color", col);
                    Py_CLEAR(col);
                }

                char *da = pdf_to_str_buf(gctx, pdf_dict_get_inheritable(gctx,
                                                annot->obj, PDF_NAME(DA)));
                PyObject_SetAttrString(Widget, "_text_da", Py_BuildValue("s", da));

                pdf_obj *ca = pdf_dict_getl(gctx, annot->obj,
                                            PDF_NAME(MK), PDF_NAME(CA), NULL);
                if (ca)
                    PyObject_SetAttrString(Widget, "button_caption",
                                 JM_UNICODE(pdf_to_str_buf(gctx, ca)));

                int field_flags = pdf_get_field_flags(gctx, pdf, annot->obj);
                PyObject_SetAttrString(Widget, "field_flags",
                                       Py_BuildValue("i", field_flags));
                
                // call Py method to reconstruct text color, font name, size
                PyObject *call = PyObject_CallMethod(Widget,
                                                     "_parse_da", NULL);
                Py_XDECREF(call);

            }
            fz_always(gctx) PyErr_Clear();
            fz_catch(gctx) return NULL;
            return NONE;
        }

        %pythoncode %{
        @property
        def widget(self):
            annot_type = self.type[0]
            if annot_type != ANNOT_WIDGET:
                return None
            w = Widget()
            w.field_type        = self.widget_type[0]
            w.field_type_string = self.widget_type[1]
            w.field_value       = self.widget_value
            w.field_name        = self.widget_name
            w.choice_values     = self.widget_choices
            w.rect              = self.rect
            w.text_font         = None
            self._getWidget(w)
            return w

        def updateWidget(self, widget):
            if self.widget_type[0] != widget.field_type:
                raise ValueError("cannot change widget type")
            widget._validate()
            doc = self.parent.parent
            xref = 0
            ff = doc.FormFonts
            if not widget.text_font:         # ensure default
                widget.text_font = "Helv"
            if not widget.text_font in ff:   # if no existent font ...
                if not doc.isFormPDF or not ff:   # a fresh /AcroForm PDF!
                    xref = doc._getNewXref()      # insert all our fonts
                    doc._updateObject(xref, Widget_fontobjects)
                else:                        # add any missing fonts
                    for k in Widget_fontdict.keys():
                        if not k in ff:      # add our font if missing
                            doc._addFormFont(k, Widget_fontdict[k])
                widget._adjust_font()        # ensure correct font spelling
            widget._dr_xref = xref           # non-zero causes /DR creation
            # now create the /DA string
            if   len(widget.text_color) == 3:
                fmt = "{:g} {:g} {:g} rg /{f:s} {s:g} Tf " + widget._text_da
            elif len(widget.text_color) == 1:
                fmt = "{:g} g /{f:s} {s:g} Tf " + widget._text_da
            elif len(widget.text_color) == 4:
                fmt = "{:g} {:g} {:g} {:g} k /{f:s} {s:g} Tf " + widget._text_da
            widget._text_da = fmt.format(*widget.text_color, f=widget.text_font,
                                        s=widget.text_fontsize)
            # update the widget at last
            self._updateWidget(widget)

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
            if (!pdf) return NONE;
            pdf_obj *link_obj = pdf_new_indirect(gctx, pdf, xref, 0);
            if (!link_obj) return NONE;
            PyObject *b = JM_annot_border(gctx, link_obj);
            pdf_drop_obj(gctx, link_obj);
            return b;
        }

        PyObject *_setBorder(PyObject *border, struct fz_document_s *doc, int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, doc);
            if (!pdf) return NONE;
            pdf_obj *link_obj = pdf_new_indirect(gctx, pdf, xref, 0);
            if (!link_obj) return NONE;
            PyObject *b = JM_annot_set_border(gctx, border, pdf, link_obj);
            pdf_drop_obj(gctx, link_obj);
            return b;
        }

        PyObject *_colors(struct fz_document_s *doc, int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, doc);
            if (!pdf) return NONE;
            pdf_obj *link_obj = pdf_new_indirect(gctx, pdf, xref, 0);
            if (!link_obj) return NONE;
            PyObject *b = JM_annot_colors(gctx, link_obj);
            pdf_drop_obj(gctx, link_obj);
            return b;
        }

        PyObject *_setColors(PyObject *colors, struct fz_document_s *doc, int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, doc);
            pdf_obj *arr = NULL;
            int i;
            if (!pdf) return NONE;
            if (!PyDict_Check(colors)) return NONE;
            float scol[4] = {0.0f, 0.0f, 0.0f, 0.0f};
            int nscol = 0;
            float fcol[4] = {0.0f, 0.0f, 0.0f, 0.0f};
            int nfcol = 0;
            PyObject *stroke = PyDict_GetItemString(colors, "stroke");
            PyObject *fill = PyDict_GetItemString(colors, "fill");
            JM_color_FromSequence(stroke, &nscol, scol);
            JM_color_FromSequence(fill, &nfcol, fcol);
            if (!nscol && !nfcol) return NONE;
            pdf_obj *link_obj = pdf_new_indirect(gctx, pdf, xref, 0);
            if (!link_obj) return NONE;
            if (nscol > 0)
            {
                arr = pdf_new_array(gctx, pdf, nscol);
                for (i = 0; i < nscol; i++)
                    pdf_array_push_real(gctx, arr, scol[i]);
                pdf_dict_put_drop(gctx, link_obj, PDF_NAME(C), arr);
            }
            if (nfcol > 0) JM_Warning("this annot type has no fill color)");
            pdf_drop_obj(gctx, link_obj);
            return NONE;
        }

        %pythoncode %{
            @property
            def border(self):
                return self._border(self.parent.parent.this, self.xref)

            def setBorder(self, border):
                return self._setBorder(border, self.parent.parent.this, self.xref)

            @property
            def colors(self):
                return self._colors(self.parent.parent.this, self.xref)

            def setColors(self, colors):
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
            return Py_BuildValue("s", $self->uri);
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
                raise ValueError("operation illegal for closed / encrypted doc")
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
                val.parent = self.parent # copy owning page from prev link
                val.parent._annot_refs[id(val)] = val
                if self.xref > 0: # prev link has an xref
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
            return NONE;
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
        struct fz_pixmap_s *getPixmap(PyObject *matrix = NULL, struct fz_colorspace_s *colorspace = NULL, int alpha = 0, PyObject *clip = NULL)
        {
            struct fz_colorspace_s *cs = NULL;
            fz_pixmap *pix = NULL;

            if (colorspace) cs = colorspace;
            else cs = fz_device_rgb(gctx);

            fz_try(gctx)
            {
                pix = JM_pixmap_from_display_list(gctx, $self, matrix, cs, alpha, clip);
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
        fz_stext_page_s(PyObject *mediabox) {
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
                PyList_Append(liste,
                              Py_BuildValue("(ff),(ff),(ff),(ff)",
                                            quad->ul.x, quad->ul.y,
                                            quad->ur.x, quad->ur.y,
                                            quad->ll.x, quad->ll.y,
                                            quad->lr.x, quad->lr.y));
                quad += 1;
            }
            JM_Free(result);
            return liste;
        }

        //---------------------------------------------------------------------
        // Get text blocks with their bbox and concatenated lines 
        // as a Python list
        //---------------------------------------------------------------------
        FITZEXCEPTION(_extractTextBlocks_AsList, !result)
        PyObject *_extractTextBlocks_AsList()
        {
            fz_stext_block *block;
            fz_stext_line *line;
            fz_stext_char *ch;
            int block_n = 0;
            PyObject *lines = PyList_New(0);
            PyObject *text = NULL, *litem;
            fz_buffer *res = NULL;
            for (block = $self->first_block; block; block = block->next)
            {
                fz_rect blockrect = block->bbox;
                if (block->type == FZ_STEXT_BLOCK_TEXT)
                {
                    fz_try(gctx)
                    {
                        res = fz_new_buffer(gctx, 1024);
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
                                fz_append_rune(gctx, res, ch->c);
                                linerect = fz_union_rect(linerect, JM_char_bbox(line, ch));
                            }
                            blockrect = fz_union_rect(blockrect, linerect);
                        }
                        text = JM_StrFromBuffer(gctx, res);
                    }
                    fz_always(gctx)
                    {
                        fz_drop_buffer(gctx, res);
                        res = NULL;
                    }
                    fz_catch(gctx) return NULL;
                }
                else
                {
                    fz_image *img = block->u.i.image;
                    fz_colorspace *cs = img->colorspace;
                    text = PyUnicode_FromFormat("<image: %s, width %d, height %d, bpc %d>", fz_colorspace_name(gctx, cs), img->w, img->h, img->bpc);
                    blockrect = fz_union_rect(blockrect, block->bbox);
                }
                litem = Py_BuildValue("ffffOii", blockrect.x0, blockrect.y0,
                                      blockrect.x1, blockrect.y1,
                                      text, block_n, block->type);
                PyList_Append(lines, litem);
                Py_CLEAR(litem);
                Py_CLEAR(text);
                block_n++;
            }
            return lines;
        }

        //---------------------------------------------------------------------
        // Get text words with their bbox
        //---------------------------------------------------------------------
        FITZEXCEPTION(_extractTextWords_AsList, !result)
        PyObject *_extractTextWords_AsList()
        {
            fz_stext_block *block;
            fz_stext_line *line;
            fz_stext_char *ch;
            fz_buffer *buff = NULL;
            size_t buflen = 0;
            int block_n = 0, line_n, word_n;
            fz_rect wbbox = {0,0,0,0};          // word bbox
            PyObject *lines = PyList_New(0);
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
                    buff = NULL;                      // reset word buffer
                    buflen = 0;                       // reset char counter
                    for (ch = line->first_char; ch; ch = ch->next)
                    {
                        if (ch->c == 32 && buflen == 0)
                            continue;                 // skip spaces at line start
                        if (ch->c == 32)
                        {   // --> finish the word
                            word_n = JM_append_word(gctx, lines, buff, &wbbox,
                                                    block_n, line_n, word_n);
                            fz_drop_buffer(gctx, buff);
                            buff = NULL;
                            buflen = 0;               // reset char counter
                            continue;
                        }
                        // append one unicode character to the word
                        if (!buff) buff = fz_new_buffer(gctx, 64);
                        fz_append_rune(gctx, buff, ch->c);
                        buflen++;
                        // enlarge word bbox
                        wbbox = fz_union_rect(wbbox, JM_char_bbox(line, ch));
                    }
                    if (buff)                         // store any remaining word
                    {
                        word_n = JM_append_word(gctx, lines, buff, &wbbox,
                                                block_n, line_n, word_n);
                        fz_drop_buffer(gctx, buff);
                        buff = NULL;
                        buflen = 0;
                    }
                    line_n++;
                }
                block_n++;
            }
            return lines;
        }

        //---------------------------------------------------------------------
        // method _extractText()
        //---------------------------------------------------------------------
        FITZEXCEPTION(_extractText, !result)
        %newobject _extractText;
        %pythonappend _extractText %{
            if format != 2:
                return val
            import base64, json

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
        %}
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
                        fz_print_stext_page_as_html(gctx, out, $self);
                        break;
                    case(2):
                        text = JM_stext_page_as_dict(gctx, $self, 0);
                        break;
                    case(3):
                        fz_print_stext_page_as_xml(gctx, out, $self);
                        break;
                    case(4):
                        fz_print_stext_page_as_xhtml(gctx, out, $self);
                        break;
                    case(5):
                        text = JM_stext_page_as_dict(gctx, $self, 0);
                        break;
                    case(6):
                        text = JM_stext_page_as_dict(gctx, $self, 1);
                        break;
                    default:
                        JM_print_stext_page_as_text(gctx, out, $self);
                        break;
                }
                if (!text) text = JM_StrFromBuffer(gctx, res);
                
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
                return self._extractText(2)

            def extractXML(self):
                return self._extractText(3)

            def extractXHTML(self):
                return self._extractText(4)

            def extractDICT(self):
                return self._extractText(5)

            def extractRAWDICT(self):
                return self._extractText(6)
        %}
        %pythoncode %{
        def __del__(self):
            if not type(self) is TextPage: return
            self.__swig_destroy__(self)
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

        FITZEXCEPTION(_insert_contents, !result)
        PyObject *_insert_contents(struct fz_page_s *fzpage, PyObject *newcont, int overlay)
        {
            fz_buffer *contbuf = NULL;
            int xref = 0;
            pdf_page *page = pdf_page_from_fz_page(gctx, fzpage);
            fz_try(gctx)
            {
                assert_PDF(page);
                contbuf = JM_BufferFromBytes(gctx, newcont);
                xref = JM_insert_contents(gctx, page->doc, page->obj, contbuf, overlay);
                page->doc->dirty = 1;
            }
            fz_always(gctx) fz_drop_buffer(gctx, contbuf);
            fz_catch(gctx) return NULL;
            return Py_BuildValue("i", xref);
        }

        %pythoncode%{@property%}
        PyObject *fitz_stdout()
        {
            return Py_BuildValue("s", PyByteArray_AS_STRING(JM_output_log));
        }

        %feature("autodoc","Empty fitz output log.") fitz_stdout_reset;
        void fitz_stdout_reset()
        {
            Py_CLEAR(JM_output_log);
            JM_output_log = PyByteArray_FromStringAndSize("", 0);
        }

        %pythoncode%{@property%}
        PyObject *fitz_stderr()
        {
            return Py_BuildValue("s", PyByteArray_AS_STRING(JM_error_log));
        }

        %feature("autodoc","Empty fitz error log.") fitz_stderr_reset;
        void fitz_stderr_reset()
        {
            Py_CLEAR(JM_error_log);
            JM_error_log  = PyByteArray_FromStringAndSize("", 0);
        }

        %feature("autodoc","Return compiled MuPDF version.") mupdf_version;
        PyObject *mupdf_version()
        {
            return Py_BuildValue("s", FZ_VERSION);
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
            if (det < -JM_EPS || det > JM_EPS)
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
                        c = pdf_greek_from_unicode(c); break;
                    case PDF_SIMPLE_ENCODING_CYRILLIC:
                        c = pdf_cyrillic_from_unicode(c); break;
                    default:
                        c = pdf_winansi_from_unicode(c); break;
                }
                if (c < 0) c = 0xB7;
                g = fz_encode_character(gctx, font, c);
                w += fz_advance_glyph(gctx, font, g, 0);
            }
            return w * fontsize;
        }

        %pythoncode %{

def _hor_matrix(self, C, P):
    """Given two points C, P calculate matrix that rotates and translates the vector C -> P such that C is mapped to Point(0, 0), and P to some point on the x axis
    """
    S = (P - C).unit                        # unit vector C -> P
    return Matrix(1, 0, 0, 1, -C.x, -C.y) * Matrix(S.x, -S.y, S.y, S.x, 0, 0)

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
    m = self._hor_matrix(np1, np2)        # matrix makes the line horizontal
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
