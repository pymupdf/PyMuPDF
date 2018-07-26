%module fitz
//-----------------------------------------------------------------------------
// SWIG macro: generate fitz exceptions
//-----------------------------------------------------------------------------
%define FITZEXCEPTION(meth, cond)
        %exception meth
        {
            $action
            if(cond)
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

%define ANNOTWRAP2(meth, doc)
        FITZEXCEPTION(meth, !result)
        %pythonprepend meth %{CheckParent(self)%}
        %feature("autodoc", doc) meth;
        %pythonappend meth %{
        if not val: return
        val.thisown = True
        val.parent = weakref.proxy(self)
        self._annot_refs[id(val)] = val

        if val.type[0] == ANNOT_SQUARE:
            ap = _make_rect_AP(val)
        elif val.type[0] == ANNOT_CIRCLE:
            ap = _make_circle_AP(val)
        elif val.type[0] in (ANNOT_LINE, ANNOT_POLYLINE, ANNOT_POLYGON):
            ap = _make_line_AP(val)
        else:
            return val
        r = Rect(0, 0, val.rect.width, val.rect.height)
        val._checkAP(r, ap)
        %}
%enddef

%feature("autodoc", "0");

%{
//#define MEMDEBUG
#ifdef MEMDEBUG
#define DEBUGMSG1(x) fprintf(stderr, "[DEBUG] free %s ", x)
#define DEBUGMSG2 fprintf(stderr, "... done!\n")
#else
#define DEBUGMSG1(x)
#define DEBUGMSG2
#endif

#define SWIG_FILE_WITH_INIT
#define SWIG_PYTHON_2_UNICODE
#define THROWMSG(msg) fz_throw(gctx, FZ_ERROR_GENERIC, msg)
#define assert_PDF(cond) if (cond == NULL) THROWMSG("not a PDF")
#define INRANGE(v, low, high) ((low) <= v && v <= (high))
#define MAX(a, b) ((a) < (b)) ? (b) : (a)
#define MIN(a, b) ((a) < (b)) ? (a) : (b)
#define JM_BytesFromBuffer(ctx, x) PyBytes_FromStringAndSize(fz_string_from_buffer(ctx, x), (Py_ssize_t) fz_buffer_storage(ctx, x, NULL))
#define JM_StrFromBuffer(ctx, x) PyUnicode_DecodeUTF8(fz_string_from_buffer(ctx, x), (Py_ssize_t) fz_buffer_storage(ctx, x, NULL), "replace")
#define JM_PyErr_Clear if (PyErr_Occurred()) PyErr_Clear()

// binary output depending on Python major
# if PY_VERSION_HEX >= 0x03000000
#define JM_UNICODE(data) Py_BuildValue("s", data)
#define JM_BinFromChar(x) PyBytes_FromString(x)
#define JM_BinFromCharSize(x, y) PyBytes_FromStringAndSize(x, (Py_ssize_t) y)
#define JM_BinFromBuffer(ctx, x) PyBytes_FromStringAndSize(fz_string_from_buffer(ctx, x), (Py_ssize_t) fz_buffer_storage(ctx, x, NULL))
# else
#define JM_UNICODE(data) data ? PyUnicode_DecodeUTF8(data, strlen(data), "replace") : Py_BuildValue("s", NULL)
#define JM_BinFromChar(x) PyByteArray_FromStringAndSize(x, (Py_ssize_t) strlen(x))
#define JM_BinFromCharSize(x, y) PyByteArray_FromStringAndSize(x, (Py_ssize_t) y)
#define JM_BinFromBuffer(ctx, x) PyByteArray_FromStringAndSize(fz_string_from_buffer(ctx, x), (Py_ssize_t) fz_buffer_storage(ctx, x, NULL))
# endif
// define Python None object
#define NONE Py_BuildValue("s", NULL)
#include <fitz.h>
#include <pdf.h>
#include <zlib.h>
#include <time.h>
#include <fitz/config.h>
char *JM_Python_str_AsChar(PyObject *str);
%}

//-----------------------------------------------------------------------------
// global context
//-----------------------------------------------------------------------------
%init %{
    gctx = fz_new_context(NULL, NULL, FZ_STORE_DEFAULT);
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
%}

%header %{
    fz_context *gctx;

struct DeviceWrapper {
    fz_device *device;
    fz_display_list *list;
};
%}

//-----------------------------------------------------------------------------
// include version information and several other helpers
//-----------------------------------------------------------------------------
%pythoncode %{
import weakref
from binascii import hexlify
import math
%}
%include version.i
%include helper-other.i
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
            if not filename or type(filename) == str:
                pass
            elif type(filename) == unicode:
                filename = filename.encode('utf8')
            else:
                raise TypeError("filename must be string or None")
            self.name = filename if filename else ""
            self.streamlen = len(stream) if stream else 0
            if stream and not (filename or filetype):
                raise ValueError("filetype missing with stream specified")
            if stream and type(stream) not in (bytes, bytearray):
                raise ValueError("stream must be bytes or bytearray")
            self.isClosed    = False
            self.isEncrypted = 0
            self.metadata    = None
            self.stream      = stream       # do not garbage collect it
            self.openErrCode = 0
            self.openErrMsg  = ''
            self.FontInfos   = []
            self.Graftmaps   = {}
            self._page_refs  = weakref.WeakValueDictionary()%}

        %pythonappend fz_document_s %{
            if this:
                self.openErrCode = self._getGCTXerrcode()
                self.openErrMsg  = self._getGCTXerrmsg()
                self.thisown = True
                if self.needsPass:
                    self.isEncrypted = 1
                else: # we won't init until doc is decrypted
                    self.initData()
            else:
                self.thisown = False
        %}

        fz_document_s(const char *filename = NULL, PyObject *stream = NULL,
                      const char *filetype = NULL, struct fz_rect_s *rect = NULL,
                      float fontsize = 11)
        {
            gctx->error->errcode = 0;       // reset any error code
            gctx->error->message[0] = 0;    // reset any error message
            struct fz_document_s *doc = NULL;
            fz_stream *data = NULL;
            char *streamdata;
            size_t streamlen = JM_CharFromBytesOrArray(stream, &streamdata);
            fz_try(gctx)
            {
                if (rect)
                {
                    if (fz_is_empty_rect(rect) || fz_is_infinite_rect(rect))
                        THROWMSG("rect must be finite and not empty");
                    if (rect->x0 != 0.0 || rect->y0 != 0)
                        THROWMSG("rect must start at (0,0)");
                }
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
            if (rect)
                fz_layout_document(gctx, doc, rect->x1, rect->y1, fontsize);
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
        int embeddedFileCount()
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            if (!pdf) return 0;
            return pdf_count_portfolio_entries(gctx, pdf);
        }

        FITZEXCEPTION(embeddedFileDel, result < 1)
        CLOSECHECK(embeddedFileDel)
        %feature("autodoc","Delete embedded file by name.") embeddedFileDel;
        int embeddedFileDel(char *name)
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
                    char *test = pdf_to_utf8(gctx, pdf_array_get(gctx, names, i));
                    if (!strcmp(test, name))
                    {
                        pdf_array_delete(gctx, names, i + 1);
                        pdf_array_delete(gctx, names, i);
                    }
                }
                m = (n - pdf_array_len(gctx, names)) / 2;
            }
            fz_catch(gctx) return -1;
            return m;
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
            name = pdf_to_utf8(gctx, pdf_portfolio_entry_name(gctx, pdf, n));
            PyDict_SetItemString(infodict, "name", JM_UNICODE(name));

            pdf_obj *o = pdf_portfolio_entry_obj(gctx, pdf, n);

            name = pdf_to_utf8(gctx, pdf_dict_get(gctx, o, PDF_NAME_F));
            PyDict_SetItemString(infodict, "filename", JM_UNICODE(name));

            name = pdf_to_utf8(gctx, pdf_dict_get(gctx, o, PDF_NAME_UF));
            PyDict_SetItemString(infodict, "ufilename", JM_UNICODE(name));

            name = pdf_to_utf8(gctx, pdf_dict_get(gctx, o, PDF_NAME_Desc));
            PyDict_SetItemString(infodict, "desc", JM_UNICODE(name));

            int len = -1, DL = -1;
            pdf_obj *ef = pdf_dict_get(gctx, o, PDF_NAME_EF);
            o = pdf_dict_getl(gctx, ef, PDF_NAME_F,
                                          PDF_NAME_Length, NULL);
            if (o) len = pdf_to_int(gctx, o);

            o = pdf_dict_getl(gctx, ef, PDF_NAME_F, PDF_NAME_DL, NULL);
            if (o) DL = pdf_to_int(gctx, o);
            else
            {
                o = pdf_dict_getl(gctx, ef, PDF_NAME_F, PDF_NAME_Params,
                                   PDF_NAME_Size, NULL);
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
            fz_try(gctx)
            {
                assert_PDF(pdf);

                int n = JM_find_embedded(gctx, id, pdf);
                if (n < 0) THROWMSG("entry not found");

                pdf_obj *entry = pdf_portfolio_entry_obj(gctx, pdf, n);
                pdf_obj *filespec = pdf_dict_getl(gctx, entry, PDF_NAME_EF,
                                                  PDF_NAME_F, NULL);

                char *data = NULL;
                size_t len = JM_CharFromBytesOrArray(buffer, &data);
                if (len)
                {
                    if (!filespec) THROWMSG("/EF object not found");
                    fz_buffer *res = fz_new_buffer_from_shared_data(gctx, data, len);
                    JM_update_stream(gctx, pdf, filespec, res);
                    // adjust /DL and /Size parameters
                    pdf_obj *l = pdf_new_int(gctx, NULL, (int64_t) len);
                    pdf_dict_put(gctx, filespec, PDF_NAME_DL, l);
                    pdf_dict_putl(gctx, filespec, l, PDF_NAME_Params, PDF_NAME_Size, NULL);
                }
                if (filename)
                    pdf_dict_put_text_string(gctx, entry, PDF_NAME_F, filename);

                if (ufilename)
                    pdf_dict_put_text_string(gctx, entry, PDF_NAME_UF, ufilename);

                if (desc)
                    pdf_dict_put_text_string(gctx, entry, PDF_NAME_Desc, desc);
            }
            fz_catch(gctx) return NULL;
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
                cont = JM_BytesFromBuffer(gctx, buf);
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
            fz_buffer *data, *buf = NULL;
            char *buffdata;
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
                if (!size) THROWMSG("arg 1 not bytes or bytearray");

                // we do not allow duplicate names
                entry = JM_find_embedded(gctx, Py_BuildValue("s", name), pdf);
                if (entry >= 0) THROWMSG("name already exists");

                // first insert a dummy entry with no more than the name
                buf = fz_new_buffer(gctx, name_len + 1);   // has no real meaning
                fz_append_string(gctx, buf, name);         // fill something in
                fz_terminate_buffer(gctx, buf);            // to make it usable
                pdf_add_portfolio_entry(gctx, pdf,         // insert the entry
                        name, name_len,                    // except the name,
                        name, name_len,                    // everythinh will
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
                pdf_dict_put_text_string(gctx, o, PDF_NAME_F,    f);
                pdf_dict_put_text_string(gctx, o, PDF_NAME_UF,  uf);
                pdf_dict_put_text_string(gctx, o, PDF_NAME_Desc, d);
                // (2) insert the real file contents
                pdf_obj *filespec = pdf_dict_getl(gctx, o, PDF_NAME_EF,
                                                  PDF_NAME_F, NULL);
                data = fz_new_buffer_from_shared_data(gctx, buffdata, size);
                JM_update_stream(gctx, pdf, filespec, data);
                // finally update some size attributes
                pdf_obj *l = pdf_new_int(gctx, NULL, (int64_t) size);
                pdf_dict_put(gctx, filespec, PDF_NAME_DL, l);
                pdf_dict_putl(gctx, filespec, l, PDF_NAME_Params, PDF_NAME_Size, NULL);
            }
            fz_always(gctx) fz_drop_buffer(gctx, buf);
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return NONE;
        }

        FITZEXCEPTION(convertToPDF, !result)
        CLOSECHECK(convertToPDF)
        %feature("autodoc","Convert document to PDF selecting copy range and optional rotation. Output bytes object.") convertToPDF;
        PyObject *convertToPDF(int from_page=0, int to_page=-1, int rotate=0)
        {
            PyObject *doc = NULL;
            fz_try(gctx)
            {
                int fp = from_page, tp = to_page, srcCount = fz_count_pages(gctx, $self);
                if (pdf_specifics(gctx, $self))
                    THROWMSG("document is PDF already");
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
        int pageCount() 
        {
            return fz_count_pages(gctx, $self);
        }

        CLOSECHECK0(_getMetadata)
        char *_getMetadata(const char *key) {
            int vsize;
            char *value;
            vsize = fz_lookup_metadata(gctx, $self, key, NULL, 0)+1;
            if(vsize > 1) {
                value = (char *)malloc(sizeof(char)*vsize);
                fz_lookup_metadata(gctx, $self, key, value, vsize);
                return value;
            }
            else
                return NULL;
        }

        CLOSECHECK0(needsPass)
        %pythoncode%{@property%}
        int needsPass() {
            return fz_needs_password(gctx, $self);
        }

        PyObject *resolveLink(char *uri = NULL)
        {
            if (!uri) return NONE;
            float xp = 0.0, yp = 0.0;
            int pno = -1;
            fz_try(gctx)
                pno = fz_resolve_link(gctx, $self, uri, &xp, &yp);
            fz_catch(gctx)
                return NONE;
            if (pno < 0) return NONE;
            return Py_BuildValue("iff", pno, xp, yp);
        }

        FITZEXCEPTION(layout, !result)
        CLOSECHECK(layout)
        PyObject *layout(struct fz_rect_s *rect, float fontsize = 11)
        {
            if (!fz_is_document_reflowable(gctx, $self)) return NONE;
            fz_try(gctx)
            {
                if (fz_is_empty_rect(rect) || fz_is_infinite_rect(rect))
                    THROWMSG("rect must be finite and not empty");
                if (rect->x0 != 0.0 || rect->y0 != 0)
                    THROWMSG("rect must start at (0, 0)");
                fz_layout_document(gctx, $self, rect->x1, rect->y1, fontsize);
            }
            fz_catch(gctx) return NULL;
            return NONE;
        }

        CLOSECHECK0(isReflowable)
        %pythoncode%{@property%}
        PyObject *isReflowable()
        {
            return truth_value(fz_is_document_reflowable(gctx, $self));
        }

        CLOSECHECK0(_getPDFroot)
        %feature("autodoc", "PDF catalog xref number") _getPDFroot;
        int _getPDFroot()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            int xref = 0;
            if (!pdf) return xref;
            fz_try(gctx)
            {
                pdf_obj *root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf),
                                             PDF_NAME_Root);
                xref = pdf_to_num(gctx, root);
            }
            fz_catch(gctx) {;}
            return xref;
        }

        CLOSECHECK0(isPDF)
        %pythoncode%{@property%}
        PyObject *isPDF()
        {
            if (pdf_specifics(gctx, $self)) Py_RETURN_TRUE;
            else Py_RETURN_FALSE;
        }

        CLOSECHECK0(isDirty)
        %pythoncode%{@property%}
        PyObject *isDirty()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) Py_RETURN_FALSE;
            return truth_value(pdf_has_unsaved_changes(gctx, pdf));
        }

        int _getGCTXerrcode() {
            return fz_caught(gctx);
        }

        const char *_getGCTXerrmsg() {
            return fz_caught_message(gctx);
        }

        CLOSECHECK0(authenticate)
        %feature("autodoc", "Decrypt document with a password.") authenticate;
        %pythonappend authenticate %{
            if val: # the doc is decrypted successfully and we init the outline
                self.isEncrypted = 0
                self.initData()
                self.thisown = True
        %}
        int authenticate(const char *pass) {
            return fz_authenticate_password(gctx, $self, pass);
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
                raise ValueError("save to original requires incremental")
            if incremental and (self.name != filename or self.streamlen > 0):
                raise ValueError("incremental save needs original file")
        %}

        PyObject *save(char *filename, int garbage=0, int clean=0, int deflate=0, int incremental=0, int ascii=0, int expand=0, int linear=0, int pretty = 0)
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
                if (fz_count_pages(gctx, $self) < 1)
                    THROWMSG("document has no pages");
                if ((incremental) && (fz_needs_password(gctx, $self)))
                    THROWMSG("decrypted file - save to new");
                pdf_finish_edit(gctx, pdf);
                JM_embedded_clean(gctx, pdf);
                pdf_save_document(gctx, pdf, filename, &opts);
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
                raise ValueError("operation illegal for closed / encrypted doc")%}

        PyObject *write(int garbage=0, int clean=0, int deflate=0,
                        int ascii=0, int expand=0, int linear=0, int pretty = 0)
        {
            PyObject *r;
            struct fz_buffer_s *res = NULL;
            fz_output *out = NULL;
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
            fz_var(res);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                if (fz_count_pages(gctx, $self) < 1)
                    THROWMSG("document has zero pages");
                pdf_finish_edit(gctx, pdf);
                JM_embedded_clean(gctx, pdf);
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                pdf_write_document(gctx, pdf, out, &opts);
                pdf->dirty = 0;
                r = JM_BytesFromBuffer(gctx, res);
            }
            fz_always(gctx)
            {
                fz_drop_output(gctx, out);
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) return NULL;
            return r;
        }

        //*********************************************************************
        // Insert pages from a source PDF into this PDF.
        // For reconstructing the links (_do_links method), we must save the
        // insertion point (start_at) if it was specified as -1.
        //*********************************************************************
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
            int fp, tp, sa;
            // local copies of page numbers
            fp = from_page;
            tp = to_page;
            sa = start_at;
            /* normalize page specifications */
            if (fp < 0) fp = 0;
            if (fp > srcCount - 1) fp = srcCount - 1;
            if (tp < 0) tp = srcCount - 1;
            if (tp > srcCount - 1) tp = srcCount - 1;
            if (sa < 0) sa = outCount;
            if (sa > outCount) sa = outCount;
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
        FITZEXCEPTION(insertPage, result<0)
        %feature("autodoc","Insert a new page in front of 'pno'. Use arguments 'width', 'height' to specify a non-default page size, and optionally text insertion arguments.") insertPage;
        %pythonprepend insertPage %{
        if self.isClosed or self.isEncrypted:
            raise ValueError("operation illegal for closed / encrypted doc")
        if bool(text):
            CheckColor(color)
            if fontname and fontname[0] == "/":
                raise ValueError("invalid font reference")
        %}
        %pythonappend insertPage %{
        if val < 0: return val
        self._reset_page_refs()
        if not bool(text): return val
        page = self.loadPage(pno)
        val = page.insertText(Point(50, 72), text, fontsize = fontsize,
                              fontname = fontname, fontfile = fontfile,
                              color = color, idx = idx, set_simple = set_simple)
        %}
        int insertPage(int pno = -1, PyObject *text = NULL, float fontsize = 11,
                       float width = 595, float height = 842, int idx = 0, 
                       char *fontname = NULL, char *fontfile = NULL,
                       int set_simple = 0, PyObject *color = NULL)
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
                contents = fz_new_buffer(gctx, 10);
                fz_append_string(gctx, contents, "");
                fz_terminate_buffer(gctx, contents);
                page_obj = pdf_add_page(gctx, pdf, &mediabox, 0, resources, contents);
                pdf_insert_page(gctx, pdf, pno , page_obj);
                pdf_finish_edit(gctx, pdf);
            }
            fz_always(gctx)
            {
                fz_drop_buffer(gctx, contents);
                pdf_drop_obj(gctx, page_obj);
            }
            fz_catch(gctx) return -1;
            pdf->dirty = 1;
            return 0;
        }

        //---------------------------------------------------------------------
        // Create sub-document to keep only selected pages.
        // Parameter is a Python list of the wanted page numbers.
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
                    THROWMSG("expected a sequence");
                if (PySequence_Size(pyliste) < 1)
                    THROWMSG("len(sequence) invalid");        
                // now call retainpages (code copy of fz_clean_file.c)
                globals glo = {0};
                glo.ctx = gctx;
                glo.doc = pdf;
                retainpages(gctx, &glo, pyliste);
                pdf_finish_edit(gctx, pdf);
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
            PyObject *p = truth_value(fz_has_permission(gctx, $self, FZ_PERMISSION_PRINT));
            PyObject *e = truth_value(fz_has_permission(gctx, $self, FZ_PERMISSION_EDIT));
            PyObject *c = truth_value(fz_has_permission(gctx, $self, FZ_PERMISSION_COPY));
            PyObject *n = truth_value(fz_has_permission(gctx, $self, FZ_PERMISSION_ANNOTATE));
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
        PyObject *_getCharWidths(int xref, int limit, int idx = 0)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            PyObject *wlist = NULL;
            int i, glyph, mylimit;
            mylimit = limit;
            if (mylimit < 256) mylimit = 256;
            int cwlen = 0;
            const char *data;
            int size;
            fz_font *font = NULL;
            fz_buffer *buf = NULL;
            pdf_obj *basefont = NULL;
            const char *bfname = NULL;
            fz_try(gctx)
            {
                assert_PDF(pdf);
                if (xref < 1) THROWMSG("xref must at least 1");
                pdf_obj *o = pdf_load_object(gctx, pdf, xref);
                if (pdf_is_dict(gctx, o))
                {
                    basefont = pdf_dict_get(gctx, o, PDF_NAME_BaseFont);
                    if (pdf_is_name(gctx, basefont))
                    {
                        bfname = (char *) pdf_to_name(gctx, basefont);
                        data = fz_lookup_base14_font(gctx, bfname, &size);
                        if (data)
                        {
                            font = fz_new_font_from_memory(gctx, bfname, data, size, 0, 0);
                        }
                        else
                        {
                            buf = fontbuffer(gctx, pdf, xref);
                            if (!buf) THROWMSG("xref is not a supported font");
                            font = fz_new_font_from_buffer(gctx, NULL, buf, idx, 0);
                        }
                    }
                }
                else
                {
                    buf = fontbuffer(gctx, pdf, xref);
                    if (!buf) THROWMSG("xref is not a supported font");
                    font = fz_new_font_from_buffer(gctx, NULL, buf, idx, 0);
                }
                wlist = PyList_New(0);
                for (i = 0; i < mylimit; i++)
                {
                    glyph = fz_encode_character(gctx, font, i);
                    if (glyph > 0)
                    {
                        PyList_Append(wlist, Py_BuildValue("(i, f)", glyph, fz_advance_glyph(gctx, font, glyph, 0)));
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
            fz_try(gctx)
            {
                if (pno >= pageCount) THROWMSG("invalid page number(s)");
                assert_PDF(pdf);
            }
            fz_catch(gctx) return NULL;
            int n = pno;
            while (n < 0) n += pageCount;
            pdf_obj *pageref = pdf_lookup_page_obj(gctx, pdf, n);
            long objnum = (long) pdf_to_num(gctx, pageref);
            long objgen = (long) pdf_to_gen(gctx, pageref);
            return Py_BuildValue("(l, l)", objnum, objgen);
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
            fz_try(gctx)
            {
                if (n >= pageCount) THROWMSG("invalid page number(s)");
                assert_PDF(pdf);
                pageref = pdf_lookup_page_obj(gctx, pdf, n);
                rsrc = pdf_dict_get(gctx, pageref, PDF_NAME_Resources);
                if (!pageref || !rsrc) THROWMSG("cannot retrieve page info");
                liste = PyList_New(0);
                JM_ScanResources(gctx, pdf, rsrc, liste, what);
            }
            fz_catch(gctx)
            {
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
            const char *ext = "";
            const char *fontname = "";
            const char *stype = "";
            PyObject *nulltuple = Py_BuildValue("sssO", "", "", "", bytes);
            PyObject *tuple;
            Py_ssize_t len = 0;
            fz_try(gctx)
            {
                obj = pdf_load_object(gctx, pdf, xref);
                pdf_obj *type = pdf_dict_get(gctx, obj, PDF_NAME_Type);
                pdf_obj *subtype = pdf_dict_get(gctx, obj, PDF_NAME_Subtype);
                if(pdf_name_eq(gctx, type, PDF_NAME_Font) && 
                   strncmp(pdf_to_name(gctx, subtype), "CIDFontType", 11) != 0)
                {
                    basefont = pdf_dict_get(gctx, obj, PDF_NAME_BaseFont);
                    if (!basefont || pdf_is_null(gctx, basefont))
                        bname = pdf_dict_get(gctx, obj, PDF_NAME_Name);
                    else
                        bname = basefont;
                    fontname = (char *) pdf_to_name(gctx, bname);
                    ext = fontextension(gctx, pdf, xref);
                    stype = (char *) pdf_to_name(gctx, subtype);
                    if (strcmp(ext, "n/a") != 0 && !info_only)
                    {
                        buffer = fontbuffer(gctx, pdf, xref);
                        bytes = JM_BytesFromBuffer(gctx, buffer);
                        fz_drop_buffer(gctx, buffer);
                    }
                    tuple = Py_BuildValue("sssO", fontname, ext, stype, bytes);
                }
                else
                {
                    tuple = nulltuple;
                }
            }
            fz_catch(gctx)
            {
                tuple = Py_BuildValue("sssO", fontname, ext, stype, bytes);
            }
            return tuple;
        }

        FITZEXCEPTION(extractImage, !result)
        CLOSECHECK(extractImage)
        %feature("autodoc","Extract image an xref points to. Return dict of extension and image content") extractImage;
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
            pdf_obj *obj = NULL;
            PyObject *bytes = NULL;
            PyObject *rc = NULL;
            unsigned char ext[5];
            fz_image *image = NULL;
            fz_compressed_buffer *cbuf = NULL;
            int type = 0;
            int n = 0;
            fz_try(gctx)
            {
                obj = pdf_new_indirect(gctx, pdf, xref, 0);
                pdf_obj *subtype = pdf_dict_get(gctx, obj, PDF_NAME_Subtype);
                if (pdf_name_eq(gctx, subtype, PDF_NAME_Image))
                {
                    image = pdf_load_image(gctx, pdf, obj);
                    cbuf = fz_compressed_image_buffer(gctx, image);
                    type = cbuf == NULL ? FZ_IMAGE_UNKNOWN : cbuf->params.type;

                    // ensure returning a PNG for unsupported images ----------
                    if (image->use_colorkey) type = FZ_IMAGE_UNKNOWN;
                    if (image->use_decode)   type = FZ_IMAGE_UNKNOWN;
                    if (image->mask)         type = FZ_IMAGE_UNKNOWN;
                    if (type < FZ_IMAGE_BMP) type = FZ_IMAGE_UNKNOWN;
                    n = fz_colorspace_n(gctx, image->colorspace);
                    if (n != 1 && n != 3 && type == FZ_IMAGE_JPEG)
                        type = FZ_IMAGE_UNKNOWN;

                    if (type != FZ_IMAGE_UNKNOWN)
                    {
                        buffer = cbuf->buffer;
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
                    else
                    {
                        buffer = freebuf = fz_new_buffer_from_image_as_png(gctx, image, NULL);
                        strcpy(ext, "png");
                    }
                    bytes = JM_BinFromBuffer(gctx, buffer);
                    rc = Py_BuildValue("{s:s,s:O}", "ext", ext, "image", bytes);
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
            fz_catch(gctx) {;}
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

            pdf_document *pdf = pdf_specifics(gctx, $self); // conv doc to pdf
            if (!pdf) return xrefs;                   // not a pdf
            pdf_obj *root, *olroot, *first;
            // get the main root
            root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Root);
            // get the outline root
            olroot = pdf_dict_get(gctx, root, PDF_NAME_Outlines);
            if (!olroot) return xrefs;                // no outlines or some problem
            int objcount, argc, i;
            int *res;
            objcount = 0;
            argc = 0;
            first = pdf_dict_get(gctx, olroot, PDF_NAME_First); // first outline
            if (!first) return xrefs;
            argc = countOutlines(gctx, first, argc);  // get number of outlines
            if (argc < 1) return xrefs;
            res = malloc(argc * sizeof(int));         // object number table
            objcount = fillOLNumbers(gctx, res, first, objcount, argc); // fill table
            pdf_dict_del(gctx, olroot, PDF_NAME_First);
            pdf_dict_del(gctx, olroot, PDF_NAME_Last);
            pdf_dict_del(gctx, olroot, PDF_NAME_Count);

            for (i = 0; i < objcount; i++)
            {
                pdf_delete_object(gctx, pdf, res[i]);      // delete outline item
                PyList_Append(xrefs, PyInt_FromLong((long) res[i]));
            }
            free(res);
            pdf->dirty = 1;
            return xrefs;
        }

        //---------------------------------------------------------------------
        // Check: do we have an AcroForm & any field?
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
                form = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Root, PDF_NAME_AcroForm, NULL);
                if (form)                        // form obj exists
                {
                    fields = pdf_dict_get(gctx, form, PDF_NAME_Fields);
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
                fonts = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Root, PDF_NAME_AcroForm, PDF_NAME_DR, PDF_NAME_Font, NULL);
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
                fonts = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Root,
                             PDF_NAME_AcroForm, PDF_NAME_DR, PDF_NAME_Font, NULL);
                if (!fonts || !pdf_is_dict(gctx, fonts))
                    THROWMSG("PDF has no form fonts yet");
                pdf_obj *k = pdf_new_name(gctx, pdf, (const char *) name);
                pdf_obj *v = pdf_new_obj_from_str(gctx, pdf, font);
                pdf_dict_put(gctx, fonts, k, v);
            }
            fz_catch(gctx) NULL;
            return NONE;
        }

        //---------------------------------------------------------------------
        // Get Xref Number of Outline Root, create it if missing
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getOLRootNumber, result<0)
        CLOSECHECK(_getOLRootNumber)
        int _getOLRootNumber()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx) assert_PDF(pdf);
            fz_catch(gctx) return -1;
            
            pdf_obj *root, *olroot, *ind_obj;
            // get main root
            root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Root);
            // get outline root
            olroot = pdf_dict_get(gctx, root, PDF_NAME_Outlines);
            if (olroot == NULL)
            {
                olroot = pdf_new_dict(gctx, pdf, 4);
                pdf_dict_put(gctx, olroot, PDF_NAME_Type, PDF_NAME_Outlines);
                ind_obj = pdf_add_object(gctx, pdf, olroot);
                pdf_dict_put(gctx, root, PDF_NAME_Outlines, ind_obj);
                olroot = pdf_dict_get(gctx, root, PDF_NAME_Outlines);
                pdf_drop_obj(gctx, ind_obj);
                pdf->dirty = 1;
            }
            return pdf_to_num(gctx, olroot);
        }

        //---------------------------------------------------------------------
        // Get a new Xref number
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getNewXref, result<0)
        CLOSECHECK(_getNewXref)
        int _getNewXref()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); /* conv doc to pdf*/
            fz_try(gctx) assert_PDF(pdf);
            fz_catch(gctx) return -1;
            pdf->dirty = 1;
            return pdf_create_object(gctx, pdf);
        }

        //---------------------------------------------------------------------
        // Get Length of Xref
        //---------------------------------------------------------------------
        CLOSECHECK0(_getXrefLength)
        int _getXrefLength()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) return 0;
            return pdf_xref_len(gctx, pdf);
        }

        //---------------------------------------------------------------------
        // Get XML Metadata xref
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getXmlMetadataXref, result<0)
        CLOSECHECK0(_getXmlMetadataXref)
        int _getXmlMetadataXref()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); // get pdf document
            pdf_obj *xml;
            int xref = 0;
            fz_try(gctx)
            {
                assert_PDF(pdf);
                pdf_obj *root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Root);
                if (!root) THROWMSG("could not load root object");
                xml = pdf_dict_gets(gctx, root, "Metadata");
                if (xml) xref = pdf_to_num(gctx, xml);
            }
            fz_catch(gctx) return -1;
            return xref;
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
                pdf_obj *root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Root);
                if (root) pdf_dict_dels(gctx, root, "Metadata");
            }
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return NONE;
        }

        //---------------------------------------------------------------------
        // Get Object String of xref
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getObjectString, !result)
        CLOSECHECK0(_getObjectString)
        const char *_getObjectString(int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); // conv doc to pdf
            pdf_obj *obj = NULL;
            fz_buffer *res = NULL;
            fz_output *out = NULL;
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
            }
            fz_always(gctx)
            {
                pdf_drop_obj(gctx, obj);
                fz_drop_output(gctx, out);
            }
            fz_catch(gctx)
            {
                fz_drop_buffer(gctx, res);
                return NULL;
            }
            return fz_string_from_buffer(gctx, res);
        }
        %pythoncode %{_getXrefString = _getObjectString%}
        
        //---------------------------------------------------------------------
        // Get decompressed stream of an object by xref
        // Throws exception if not a stream.
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getXrefStream, !result)
        CLOSECHECK(_getXrefStream)
        PyObject *_getXrefStream(int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            PyObject *r;
            struct fz_buffer_s *res;
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if (!INRANGE(xref, 1, xreflen-1))
                    THROWMSG("xref out of range");
                res = pdf_load_stream_number(gctx, pdf, xref);
                r = JM_BytesFromBuffer(gctx, res);
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) return NULL;
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
                new_obj = pdf_new_obj_from_str(gctx, pdf, text);
                pdf_update_object(gctx, pdf, xref, new_obj);
                pdf_drop_obj(gctx, new_obj);
                if (page) refresh_link_table(gctx, pdf_page_from_fz_page(gctx, page));
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
            fz_buffer *res = NULL;
            size_t len = 0;
            char *c = NULL;
            pdf_document *pdf = pdf_specifics(gctx, $self);     // get pdf doc
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if (!INRANGE(xref, 1, xreflen-1))
                    THROWMSG("xref out of range");
                len = JM_CharFromBytesOrArray(stream, &c);
                if (len < 1) THROWMSG("stream must be bytes or bytearray");
                // get the object
                obj = pdf_new_indirect(gctx, pdf, xref, 0);
                if (!obj) THROWMSG("xref invalid");
                if (new == 0 && !pdf_is_stream(gctx, obj))
                    THROWMSG("xref not a stream object");

                res = fz_new_buffer_from_shared_data(gctx, c, len);
                JM_update_stream(gctx, pdf, obj, res);
                pdf_drop_obj(gctx, obj);
            }
            fz_catch(gctx) return NULL;
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
                new_info = pdf_new_obj_from_str(gctx, pdf, text);
            }
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            // replace existing /Info object
            info = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Info);
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
            pdf_dict_put_drop(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Info, new_info_ind);
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
        struct fz_rect_s *bound() {
            fz_rect *rect = (fz_rect *)malloc(sizeof(fz_rect));
            fz_bound_page(gctx, $self, rect);
            return rect;
        }
        %pythoncode %{rect = property(bound, doc="page rectangle")%}

        //---------------------------------------------------------------------
        // run()
        //---------------------------------------------------------------------
        FITZEXCEPTION(run, result)
        PARENTCHECK(run)
        int run(struct DeviceWrapper *dw, const struct fz_matrix_s *m)
        {
            fz_try(gctx) fz_run_page(gctx, $self, dw->device, m, NULL);
            fz_catch(gctx) return 1;
            return 0;
        }

        //---------------------------------------------------------------------
        // Page.getSVGimage
        //---------------------------------------------------------------------
        FITZEXCEPTION(getSVGimage, !result)
        %feature("autodoc","Create an SVG image from the page as a string.") getSVGimage;
        PARENTCHECK(getSVGimage)
        PyObject *getSVGimage(struct fz_matrix_s *matrix = NULL)
        {
            fz_rect mediabox;
            fz_bound_page(gctx, $self, &mediabox);
            fz_device *dev = NULL;
            fz_buffer *res = NULL;
            PyObject *text = NULL;
            fz_matrix *ctm = matrix;
            if (!matrix) ctm = (fz_matrix *) &fz_identity;
            fz_rect tbounds;
            fz_cookie *cookie = NULL;
            fz_output *out = NULL;
            fz_separations *seps = NULL;
            fz_var(out);
            fz_var(dev);
            fz_var(res);
            tbounds = mediabox;
            fz_transform_rect(&tbounds, ctm);

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
        ANNOTWRAP2(addLineAnnot, "Add 'Line' annot for points p1 and p2.")
        struct fz_annot_s *addLineAnnot(struct fz_point_s *p1, struct fz_point_s *p2)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_annot *annot = NULL;
            float col[3] = {0, 0, 0};
            float width  = 1.0f;
            fz_point a = {p1->x, p1->y};
            fz_point b = {p2->x, p2->y};
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
                fz_expand_rect(&r, 3 * width);
                pdf_set_annot_rect(gctx, annot, &r);
            }
            fz_catch(gctx) return NULL;
            fz_annot *fzannot = (fz_annot *) annot;
            return fz_keep_annot(gctx, fzannot);
        }

        //---------------------------------------------------------------------
        // page addTextAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addTextAnnot, "Add a 'sticky note' at position 'point'.")
        struct fz_annot_s *addTextAnnot(struct fz_point_s *point, char *text)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_annot *annot = NULL;
            char *name = "Note";
            fz_point pos = {point->x, point->y};
            fz_var(annot);
            fz_try(gctx)
            {
                assert_PDF(page);
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_TEXT);
                pdf_set_text_annot_position(gctx, annot, pos);
                pdf_set_annot_contents(gctx, annot, text);
                pdf_set_annot_icon_name(gctx, annot, name);
                pdf_update_appearance(gctx, annot);
                pdf_dirty_annot(gctx, annot);
                pdf_update_page(gctx, page);
            }
            fz_catch(gctx) return NULL;
            fz_annot *fzannot = (fz_annot *) annot;
            return fz_keep_annot(gctx, fzannot);
        }

        //---------------------------------------------------------------------
        // page addFileAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addFileAnnot, "Add a 'FileAttachment' annotation.")
        struct fz_annot_s *addFileAnnot(struct fz_point_s *point, PyObject *buffer, char *filename, char *ufilename = NULL, char *desc = NULL)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            fz_annot *fzannot = NULL;
            pdf_annot *annot = NULL;
            char *data = NULL, *uf, *d;
            if (!ufilename) uf = filename;
            if (!desc) d = filename;
            size_t len = 0;
            fz_buffer *filebuf = NULL;
            fz_rect r = {point->x, point->y, point->x + 20, point->y + 30};
            fz_var(annot);
            fz_try(gctx)
            {
                assert_PDF(page);
                annot = pdf_create_annot(gctx, page, ANNOT_FILEATTACHMENT);
                pdf_set_annot_rect(gctx, annot, &r);
                pdf_set_annot_icon_name(gctx, annot, "PushPin");
                len = JM_CharFromBytesOrArray(buffer, &data);
                filebuf = fz_new_buffer_from_shared_data(gctx, data, len);
                pdf_obj *val = JM_embed_file(gctx, page->doc, filebuf,
                                             filename, uf, d);
                pdf_dict_put(gctx, annot->obj, PDF_NAME_FS, val);
                pdf_dict_put_text_string(gctx, annot->obj, PDF_NAME_Contents, filename);
                JM_update_file_attachment_annot(gctx, page->doc, annot);
                pdf_dirty_annot(gctx, annot);
                pdf_update_page(gctx, page);
            }
            fz_catch(gctx) return NULL;
            fzannot = (fz_annot *) annot;
            return fz_keep_annot(gctx, fzannot);
        }

        //---------------------------------------------------------------------
        // page addStrikeoutAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addStrikeoutAnnot, "Strike out content in a rectangle.")
        struct fz_annot_s *addStrikeoutAnnot(struct fz_rect_s *rect)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            fz_annot *annot = NULL;
            fz_var(annot);
            fz_try(gctx)
            {
                assert_PDF(page);
                annot = JM_AnnotTextmarker(gctx, page, rect, PDF_ANNOT_STRIKE_OUT);
            }
            fz_catch(gctx) return NULL;
            return fz_keep_annot(gctx, annot);
        }

        //---------------------------------------------------------------------
        // page addUnderlineAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addUnderlineAnnot, "Underline content in a rectangle.")
        struct fz_annot_s *addUnderlineAnnot(struct fz_rect_s *rect)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            fz_annot *annot = NULL;
            fz_var(annot);
            fz_try(gctx)
            {
                assert_PDF(page);
                annot = JM_AnnotTextmarker(gctx, page, rect, PDF_ANNOT_UNDERLINE);
            }
            fz_catch(gctx) return NULL;
            return fz_keep_annot(gctx, annot);
        }

        //---------------------------------------------------------------------
        // page addHighlightAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP1(addHighlightAnnot, "Highlight content in a rectangle.")
        struct fz_annot_s *addHighlightAnnot(struct fz_rect_s *rect)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            fz_annot *annot = NULL;
            fz_var(annot);
            fz_try(gctx)
            {
                assert_PDF(page);
                annot = JM_AnnotTextmarker(gctx, page, rect, PDF_ANNOT_HIGHLIGHT);
            }
            fz_catch(gctx) return NULL;
            return fz_keep_annot(gctx, annot);
        }

        //---------------------------------------------------------------------
        // page addRectAnnot
        //---------------------------------------------------------------------
        ANNOTWRAP2(addRectAnnot, "Add a 'Rectangle' annotation.")
        struct fz_annot_s *addRectAnnot(struct fz_rect_s *rect)
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
        ANNOTWRAP2(addCircleAnnot, "Add a 'Circle' annotation.")
        struct fz_annot_s *addCircleAnnot(struct fz_rect_s *rect)
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
        ANNOTWRAP2(addPolylineAnnot, "Add a 'Polyline' annotation for a sequence of points.")
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
        ANNOTWRAP2(addPolygonAnnot, "Add a 'Polygon' annotation for a sequence of points.")
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
        ANNOTWRAP1(addFreetextAnnot, "Add a 'FreeText' annotation at position 'point'.")
        struct fz_annot_s *addFreetextAnnot(struct fz_point_s *pos, char *text, float fontsize = 11, PyObject *color = NULL)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            float col[3] = {0, 0, 0};
            if (color && PySequence_Check(color) && PySequence_Size(color) == 3)
            {
                col[0] = (float) PyFloat_AsDouble(PySequence_GetItem(color, 0));
                col[1] = (float) PyFloat_AsDouble(PySequence_GetItem(color, 1));
                col[2] = (float) PyFloat_AsDouble(PySequence_GetItem(color, 2));
            }
            char *fname = "Helvetica";
            pdf_annot *annot = NULL;
            char *ascii = JM_ASCIIFromChar(text);
            fz_var(ascii);
            fz_var(annot);
            fz_try(gctx)
            {
                assert_PDF(page);
                pdf_document *pdf = page->doc;
                annot = pdf_create_annot(gctx, page, PDF_ANNOT_FREE_TEXT);
                pdf_set_free_text_details(gctx, annot, pos,
                                          ascii, fname, fontsize, col);
                pdf_update_free_text_annot_appearance(gctx, pdf, annot);
                pdf_dirty_annot(gctx, annot);
                pdf_update_page(gctx, page);
            }
            fz_always(gctx) free(ascii);
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
            return fz_keep_display_list(gctx, dl);
        }

        //---------------------------------------------------------------------
        // Page.setCropBox
        // ATTENTION: This will alse change the value returned by Page.bound()
        //---------------------------------------------------------------------
        FITZEXCEPTION(setCropBox, !result)
        PARENTCHECK(setCropBox)
        PyObject *setCropBox(struct fz_rect_s *rect = NULL)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(page);
                if (!rect) THROWMSG("rect must be given");
                fz_rect mediabox = {0,0,0,0};
                fz_rect cropbox = {0,0,0,0};
                pdf_to_rect(gctx, pdf_dict_get(gctx, page->obj, PDF_NAME_MediaBox), &mediabox);
                cropbox.x0 = rect->x0;
                cropbox.y0 = mediabox.y1 - rect->y1;
                cropbox.x1 = rect->x1;
                cropbox.y1 = mediabox.y1 - rect->y0;
                pdf_dict_put_drop(gctx, page->obj, PDF_NAME_CropBox,
                                  pdf_new_rect(gctx, page->doc, &cropbox));                
            }
            fz_catch(gctx) return NULL;
            page->doc->dirty = 1;
            return NONE;
        }

        //---------------------------------------------------------------------
        // loadLinks()
        //---------------------------------------------------------------------
        PARENTCHECK(loadLinks)
        %pythonappend loadLinks
%{if val:
    val.thisown = True
    val.parent = weakref.proxy(self) # owning page object
    self._annot_refs[id(val)] = val%}
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
            pdf_obj *annots = pdf_dict_get(gctx, page->obj, PDF_NAME_Annots);
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
            pdf_dict_put(gctx, page->obj, PDF_NAME_Annots, annots);
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
        if val == Point(0,0):
            r = self.rect
            val = Point(r.width, r.height)
        %}
        struct fz_point_s *MediaBoxSize()
        {
            fz_point *p = (fz_point *)malloc(sizeof(fz_point));
            p->x = p->y = 0.0;
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            if (!page) return p;
            fz_rect r = {0,0,0,0};
            pdf_obj *o = pdf_dict_get(gctx, page->obj, PDF_NAME_MediaBox);
            if (!o) return p;
            pdf_to_rect(gctx, o, &r);
            p->x = r.x1 - r.x0;
            p->y = r.y1 - r.y0;
            return p;
        }

        //---------------------------------------------------------------------
        // CropBox position: top-left of /CropBox (PDF only)
        //---------------------------------------------------------------------
        PARENTCHECK(CropBoxPosition)
        %pythoncode %{@property%}
        %feature("autodoc","Retrieve position of /CropBox. Return (0,0) for non-PDF, or no /CropBox.") CropBoxPosition;
        struct fz_point_s *CropBoxPosition()
        {
            fz_point *p = (fz_point *)malloc(sizeof(fz_point));
            p->x = p->y = 0.0;
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            if (!page) return p;                 // not a PDF
            fz_rect cbox = {0,0,0,0};
            pdf_obj *o = pdf_dict_get(gctx, page->obj, PDF_NAME_CropBox);
            if (!o) return p;                    // no CropBox specified
            pdf_to_rect(gctx, o, &cbox);
            p->x = cbox.x0;
            p->y = cbox.y0;
            return p;
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
            pdf_obj *o = pdf_dict_get(gctx, page->obj, PDF_NAME_Rotate);
            if (!o) return 0;
            return pdf_to_int(gctx, o);
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
                if (rot % 90) THROWMSG("rotate not 90 * int");
                pdf_dict_put_int(gctx, page->obj, PDF_NAME_Rotate, (int64_t) rot);
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
                annots = pdf_dict_get(gctx, page->obj, PDF_NAME_Annots);
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
                    annot = pdf_new_obj_from_str(gctx, page->doc, text);
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
                pdf_dict_put_drop(gctx, page->obj, PDF_NAME_Annots, new_array);
                refresh_link_table(gctx, page);
            }
            fz_catch(gctx) return NULL;
            page->doc->dirty = 1;
            return NONE;
        }

        /*********************************************************************/
        // Page._getLinkXrefs - return list of link xref numbers.
        /*********************************************************************/

        PyObject *_getLinkXrefs()
        {
            pdf_obj *annots, *annots_arr, *link, *obj;
            int i, lcount;
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            PyObject *linkxrefs = PyList_New(0);
            if (!page) return linkxrefs;         // empty list if not PDF
            annots = pdf_dict_get(gctx, page->obj, PDF_NAME_Annots);
            if (!annots) return linkxrefs;
            if (pdf_is_indirect(gctx, annots))
                annots_arr = pdf_resolve_indirect(gctx, annots);
            else
                annots_arr = annots;
            lcount = pdf_array_len(gctx, annots_arr);
            for (i = 0; i < lcount; i++)
                {
                    link = pdf_array_get(gctx, annots_arr, i);
                    obj = pdf_dict_get(gctx, link, PDF_NAME_Subtype);
                    if (pdf_name_eq(gctx, obj, PDF_NAME_Link))
                    {
                        int xref = pdf_to_num(gctx, link);
                        PyList_Append(linkxrefs, PyInt_FromLong((long) xref));
                    }
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
        FITZEXCEPTION(_showPDFpage, result<0)
        int _showPDFpage(struct fz_rect_s *rect, struct fz_document_s *docsrc, int pno=0, int overlay=1, int keep_proportion=1, int reuse_xref=0, struct fz_rect_s *clip = NULL, struct pdf_graft_map_s *graftmap = NULL)
        {
            int xref;
            xref = reuse_xref;
            pdf_obj *xobj1, *xobj2, *resources, *o;
            fz_buffer *res, *nres;
            fz_rect mediabox = {0,0,0,0};
            fz_rect cropbox = {0,0,0,0};
            char data[50];
            fz_try(gctx)
            {
                pdf_page *tpage = pdf_page_from_fz_page(gctx, $self);
                assert_PDF(tpage);
                pdf_obj *tpageref = tpage->obj;
                pdf_document *pdfout = tpage->doc;    // target PDF
                pdf_document *pdfsrc = pdf_specifics(gctx, docsrc);
                assert_PDF(pdfsrc);

                //-------------------------------------------------------------
                // make XObject of source page and get its xref
                //-------------------------------------------------------------
                xobj1 = JM_xobject_from_page(gctx, pdfout, pdfsrc, pno,
                                             &mediabox, &cropbox, xref, graftmap);
                xref = pdf_to_num(gctx, xobj1);

                //-------------------------------------------------------------
                // Calculate /Matrix and /BBox of the referencing XObject
                //-------------------------------------------------------------
                if (clip)
                {   // set cropbox if clip given
                    cropbox.x0 = clip->x0;
                    cropbox.y0 = mediabox.y1 - clip->y1;
                    cropbox.x1 = clip->x1;
                    cropbox.y1 = mediabox.y1 - clip->y0;
                }
                fz_matrix mat = {1, 0, 0, 1, 0, 0};
                fz_rect prect = {0, 0, 0, 0};
                fz_rect r = {0, 0, 0, 0};
                fz_bound_page(gctx, $self, &prect);
                o = pdf_dict_get(gctx, tpageref, PDF_NAME_CropBox);
                pdf_to_rect(gctx, o, &r);
                if (o)
                {
                    prect.x0 = r.x0;
                    prect.y0 = r.y0;
                }
                o = pdf_dict_get(gctx, tpageref, PDF_NAME_MediaBox);
                pdf_to_rect(gctx, o, &r);
                if (o)
                {
                    prect.x1 = r.x1;
                    prect.y1 = r.y1;
                }
                float W = rect->x1 - rect->x0;
                float H = rect->y1 - rect->y0;
                float fw = W / (cropbox.x1 - cropbox.x0);
                float fh = H / (cropbox.y1 - cropbox.y0);
                if ((fw < fh) && keep_proportion)     // zoom factors in matrix
                    fh = fw;
                float X = rect->x0 + prect.x0 - fw*cropbox.x0;
                float Y = prect.y1 - (rect->y1 + prect.y0 + fh*cropbox.y0);
                mat.a = fw;
                mat.d = fh;
                mat.e = X;
                mat.f = Y;

                //-------------------------------------------------------------
                // create referencing XObject (controls actual display)
                //-------------------------------------------------------------
                xobj2 = pdf_new_xobject(gctx, pdfout, &cropbox, &mat);

                // fill reference to xobj1 into its /Resources
                o = pdf_xobject_resources(gctx, xobj2);
                pdf_obj *subres = pdf_new_dict(gctx, pdfout, 10);
                pdf_dict_put(gctx, o, PDF_NAME_XObject, subres);
                pdf_dict_puts(gctx, subres, "fullpage", xobj1);
                pdf_drop_obj(gctx, subres);

                // xobj2 invokes xobj1 via one statement
                res = fz_new_buffer(gctx, 50);
                fz_append_string(gctx, res, "/fullpage Do");
                pdf_update_xobject_contents(gctx, pdfout, xobj2, res);
                fz_drop_buffer(gctx, res);

                //-------------------------------------------------------------
                // update target page:
                //-------------------------------------------------------------
                // 1. resources object
                //-------------------------------------------------------------
                resources = pdf_dict_get(gctx, tpageref, PDF_NAME_Resources);
                subres = pdf_dict_get(gctx, resources, PDF_NAME_XObject);
                if (!subres)           // has no XObject dict yet: create one
                {
                    subres = pdf_new_dict(gctx, pdfout, 10);
                    pdf_dict_put(gctx, resources, PDF_NAME_XObject, subres);
                }

                // store *unique* reference name
                snprintf(data, 50, "fitz-%d-%d", xref, fz_gen_id(gctx));
                pdf_dict_puts(gctx, subres, data, xobj2);

                //-------------------------------------------------------------
                // 2. contents object
                //-------------------------------------------------------------
                nres = fz_new_buffer(gctx, 50);       // buffer for Do-command
                fz_append_string(gctx, nres, " q /");    // Do-command
                fz_append_string(gctx, nres, data);
                fz_append_string(gctx, nres, " Do Q ");

                JM_insert_contents(gctx, pdfout, tpageref, nres, overlay);
                fz_drop_buffer(gctx, nres);
            }
            fz_catch(gctx) return -1;
            return xref;
        }

        //---------------------------------------------------------------------
        // insert an image
        //---------------------------------------------------------------------
        FITZEXCEPTION(insertImage, !result)
        %pythonprepend insertImage %{
        CheckParent(self)
        imglst = self.parent.getPageImageList(self.number)
        ilst = [i[7] for i in imglst]
        n = "fitzImg"
        i = 0
        _imgname = n + "0"
        while _imgname in ilst:
            i += 1
            _imgname = n + str(i)%}
        %feature("autodoc", "Insert a new image into a rectangle.") insertImage;
        PyObject *insertImage(struct fz_rect_s *rect, const char *filename=NULL, struct fz_pixmap_s *pixmap = NULL, PyObject *stream = NULL, int overlay = 1,
        char *_imgname = NULL)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_document *pdf;
            fz_pixmap *pm = NULL;
            fz_pixmap *pix = NULL;
            fz_image *mask = NULL;
            fz_separations *seps = NULL;
            pdf_obj *resources, *subres, *ref;
            fz_buffer *res = NULL, *nres = NULL,  *imgbuf = NULL;

            unsigned char *streamdata = NULL;
            size_t streamlen = JM_CharFromBytesOrArray(stream, &streamdata);

            const char *template = " q %g 0 0 %g %g %g cm /%s Do Q ";
            char *cont = NULL;
            Py_ssize_t name_len = 0;
            fz_image *zimg = NULL, *image = NULL;
            int parm_count = 0;
            if (filename)      parm_count++;
            if (pixmap)        parm_count++;
            if (streamlen > 0) parm_count++;
            fz_try(gctx)
            {
                assert_PDF(page);
                if (parm_count != 1)
                    THROWMSG("need exactly one of filename, pixmap or stream");
                if (fz_is_empty_rect(rect) || fz_is_infinite_rect(rect))
                    THROWMSG("rect must be finite and not empty");
                // calculate coordinates for image matrix
                fz_rect prect = {0, 0, 0, 0};        // normal page rectangle
                fz_bound_page(gctx, $self, &prect);  // get page mediabox
                fz_rect r = {0, 0, 0, 0};            // modify where necessary
                pdf_obj *o = pdf_dict_get(gctx, page->obj, PDF_NAME_CropBox);
                if (o)
                {   // set top-left of page rect to new values
                    pdf_to_rect(gctx, o, &r);
                    prect.x0 = r.x0;
                    prect.y0 = r.y0;
                }
                o = pdf_dict_get(gctx, page->obj, PDF_NAME_MediaBox);
                if (o)
                {   // set bottom-right to new values
                    pdf_to_rect(gctx, o, &r);
                    prect.x1 = r.x1;
                    prect.y1 = r.y1;
                }
                // adjust rect.x0, rect.y0 by CropBox start
                float X = rect->x0 + prect.x0;
                float Y = prect.y1 - (rect->y1 + prect.y0);
                float W = rect->x1 - rect->x0;
                float H = rect->y1 - rect->y0;

                pdf = page->doc;

                // get objects "Resources" & "XObject"
                resources = pdf_dict_get(gctx, page->obj, PDF_NAME_Resources);
                subres = pdf_dict_get(gctx, resources, PDF_NAME_XObject);
                if (!subres)           // has no XObject yet, create one
                {
                    subres = pdf_new_dict(gctx, pdf, 10);
                    pdf_dict_put_drop(gctx, resources, PDF_NAME_XObject, subres);
                }

                // create the image
                if (filename || streamlen > 0)
                {
                    if (filename)
                        image = fz_new_image_from_file(gctx, filename);
                    else
                    {
                        imgbuf = fz_new_buffer_from_shared_data(gctx,
                                                   streamdata, streamlen);
                        image = fz_new_image_from_buffer(gctx, imgbuf);
                    }
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
                if (pixmap)
                {
                    if (pixmap->alpha == 0)
                        image = fz_new_image_from_pixmap(gctx, pixmap, NULL);
                    else
                    {   // pixmap has alpha, therefore create a mask
                        pm = fz_convert_pixmap(gctx, pixmap, NULL, NULL, NULL, NULL, 1);
                        pm->alpha = 0;
                        pm->colorspace = fz_keep_colorspace(gctx, fz_device_gray(gctx));
                        mask = fz_new_image_from_pixmap(gctx, pm, NULL);
                        image = fz_new_image_from_pixmap(gctx, pixmap, mask);
                    }
                }
                // put image in PDF
                ref = pdf_add_image(gctx, pdf, image, 0);
                pdf_dict_puts(gctx, subres, _imgname, ref);  // store ref-name

                // prep contents stream buffer with invoking command
                nres = fz_new_buffer(gctx, 50);
                fz_append_printf(gctx, nres, template, W, H, X, Y, _imgname);
                JM_insert_contents(gctx, pdf, page->obj, nres, overlay);
                fz_drop_buffer(gctx, nres);
            }
            fz_always(gctx)
            {
                fz_drop_image(gctx, image);
                fz_drop_image(gctx, mask);
                fz_drop_pixmap(gctx, pix);
                fz_drop_pixmap(gctx, pm);
            }
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return NONE;
        }

        //---------------------------------------------------------------------
        // insert font
        //---------------------------------------------------------------------
        FITZEXCEPTION(insertFont, !result)
        %pythonprepend insertFont %{
        if not self.parent:
            raise ValueError("orphaned object: parent is None")
        f = CheckFont(self, fontname)
        if f is not None:         # drop out if fontname already in page list
            return f[0]
        if not fontname:
            fontname = "Helvetica"
        if xref > 0:
            _, _, _, fontbuffer = self.parent.extractFont(xref)
            if not fontbuffer:
                raise ValueError("xref is no valid font")
        %}
        %pythonappend insertFont %{
        if val:
            xref = val[0]
            f = CheckFont(self, fontname)
            if f is not None:
                val[1]["type"] = f[2]       # put /Subtype in font info
                val[1]["glyphs"] = None
            doc = self.parent               # now add to document font info
            fi = CheckFontInfo(doc, xref)
            if fi is None:                  # look if we are already present
                doc.FontInfos.append(val)   # no: add me to document object
            return xref
        %}
        PyObject *insertFont(const char *fontname = NULL, const char *fontfile = NULL, PyObject *fontbuffer = NULL, int xref = 0, int set_simple = 0, int idx = 0)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_document *pdf;
            pdf_obj *resources, *fonts, *font_obj;
            fz_font *font;
            const char *data = NULL;
            int size, ixref = 0;
            PyObject *info;
            fz_try(gctx)
            {
                assert_PDF(page);
                pdf = page->doc;
                // get objects "Resources", "Resources/Font"
                resources = pdf_dict_get(gctx, page->obj, PDF_NAME_Resources);
                fonts = pdf_dict_get(gctx, resources, PDF_NAME_Font);
                int simple = 0;
                if (!fonts)       // page has no fonts yet
                    fonts = pdf_add_object_drop(gctx, pdf, pdf_new_dict(gctx, pdf, 1));
                
                data = fz_lookup_base14_font(gctx, fontname, &size);
                if (data)              // base 14 font found
                {
                    font = fz_new_font_from_memory(gctx, fontname, data, size, 0, 0);
                    font_obj = pdf_add_simple_font(gctx, pdf, font, PDF_SIMPLE_ENCODING_LATIN);
                    simple = 1;
                }
                else
                {
                    if (!fontfile && !fontbuffer) THROWMSG("unknown PDF Base 14 font");
                    if (fontfile)
                    {
                        font = fz_new_font_from_file(gctx, NULL, fontfile, idx, 0);
                    }
                    else
                    {
                        if (!PyBytes_Check(fontbuffer)) THROWMSG("fontbuffer must be bytes");
                        data = PyBytes_AsString(fontbuffer);
                        size = PyBytes_Size(fontbuffer);
                        font = fz_new_font_from_memory(gctx, NULL, data, size, idx, 0);
                    }
                    if (set_simple == 0)
                    {
                        font_obj = pdf_add_cid_font(gctx, pdf, font);
                        simple = 0;
                    }
                    else
                    {
                        font_obj = pdf_add_simple_font(gctx, pdf, font, PDF_SIMPLE_ENCODING_LATIN);
                        simple = 2;
                    }
                }
                ixref = pdf_to_num(gctx, font_obj);
                PyObject *name = PyString_FromString(fz_font_name(gctx, font));
                PyObject *exto;
                if (simple != 1)
                    exto = PyString_FromString(fontextension(gctx, pdf, ixref));
                else
                    exto = PyString_FromString("n/a");
                PyObject *simpleo = truth_value(simple);
                PyObject *idxo = PyInt_FromLong((long) idx);
                info = PyDict_New();
                PyDict_SetItemString(info, "name", name);
                PyDict_SetItemString(info, "simple", simpleo);
                PyDict_SetItemString(info, "ext", exto);
                fz_drop_font(gctx, font);
                // resources and fonts objects will contain named reference to font
                pdf_dict_puts(gctx, fonts, fontname, font_obj);
                pdf_dict_put(gctx, resources, PDF_NAME_Font, fonts);
            }
            fz_catch(gctx) return NULL;
            pdf->dirty = 1;
            return Py_BuildValue("[i, O]", ixref, info);
        }

        //---------------------------------------------------------------------
        // Get list of contents objects
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getContents, !result)
        PARENTCHECK(_getContents)
        PyObject *_getContents()
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            PyObject *list = NULL;
            pdf_obj *contents = NULL, *icont = NULL;
            int i, xref;
            fz_try(gctx)
            {
                assert_PDF(page);
                list = PyList_New(0);
                contents = pdf_dict_get(gctx, page->obj, PDF_NAME_Contents);
                if (pdf_is_array(gctx, contents))
                {   for (i=0; i < pdf_array_len(gctx, contents); i++)
                    {
                        icont = pdf_array_get(gctx, contents, i);
                        xref = pdf_to_num(gctx, icont);
                        PyList_Append(list, PyInt_FromLong((long) xref));
                    }
                }
                else
                {
                    xref = pdf_to_num(gctx, contents);
                    PyList_Append(list, PyInt_FromLong((long) xref));
                }
            }
            fz_catch(gctx) return NULL;
            return list;
        }

        //---------------------------------------------------------------------
        // Set /Contents of a page to object given by xref
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
                assert_PDF(page);
                if (!INRANGE(xref, 1, pdf_xref_len(gctx, page->doc) - 1))
                    THROWMSG("xref out of range");
                contents = pdf_new_indirect(gctx, page->doc, xref, 0);
                if (!pdf_is_stream(gctx, contents))
                    THROWMSG("xref is not a stream");
                pdf_dict_put_drop(gctx, page->obj, PDF_NAME_Contents, contents);
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

        def _getXref(self):
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


/* fz_rect */
%rename(_fz_transform_rect) fz_transform_rect;
struct fz_rect_s *fz_transform_rect(struct fz_rect_s *restrict rect, const struct fz_matrix_s *restrict transform);
%rename(Rect) fz_rect_s;

struct fz_rect_s
{
    float x0, y0, x1, y1;
    fz_rect_s();
    %extend {
        ~fz_rect_s() {
            DEBUGMSG1("rect");
            free($self);
            DEBUGMSG2;
        }
        FITZEXCEPTION(fz_rect_s, !result)
        fz_rect_s(const struct fz_rect_s *s) {
            fz_rect *r = (fz_rect *)malloc(sizeof(fz_rect));
            if (!s)
            {
                r->x0 = r->y0 = r->x1 = r->y1 = 0;
            }
            else *r = *s;
            return r;
        }

        fz_rect_s(const struct fz_point_s *lt, const struct fz_point_s *rb) {
            fz_rect *r = (fz_rect *)malloc(sizeof(fz_rect));
            r->x0 = lt->x;
            r->y0 = lt->y;
            r->x1 = rb->x;
            r->y1 = rb->y;
            return r;
        }

        fz_rect_s(float x0, float y0, const struct fz_point_s *rb) {
            fz_rect *r = (fz_rect *)malloc(sizeof(fz_rect));
            r->x0 = x0;
            r->y0 = y0;
            r->x1 = rb->x;
            r->y1 = rb->y;
            return r;
        }

        fz_rect_s(const struct fz_point_s *lt, float x1, float y1) {
            fz_rect *r = (fz_rect *)malloc(sizeof(fz_rect));
            r->x0 = lt->x;
            r->y0 = lt->y;
            r->x1 = x1;
            r->y1 = y1;
            return r;
        }

        fz_rect_s(float x0, float y0, float x1, float y1) {
            fz_rect *r = (fz_rect *)malloc(sizeof(fz_rect));
            r->x0 = x0;
            r->y0 = y0;
            r->x1 = x1;
            r->y1 = y1;
            return r;
        }

        //--------------------------------------------------------------------
        // create Rect from Python list
        //--------------------------------------------------------------------
        fz_rect_s(PyObject *list)
        {
            fz_rect *r = (fz_rect *)malloc(sizeof(fz_rect));
            fz_try(gctx)
            {
                if (!PySequence_Check(list)) THROWMSG("expected a sequence");
                if (PySequence_Size(list) != 4) THROWMSG("len(sequence) invalid");
                r->x0 = (float) PyFloat_AsDouble(PySequence_GetItem(list, 0));
                if (PyErr_Occurred()) THROWMSG("invalid sequ. item");
                r->y0 = (float) PyFloat_AsDouble(PySequence_GetItem(list, 1));
                if (PyErr_Occurred()) THROWMSG("invalid sequ. item");
                r->x1 = (float) PyFloat_AsDouble(PySequence_GetItem(list, 2));
                if (PyErr_Occurred()) THROWMSG("invalid sequ. item");
                r->y1 = (float) PyFloat_AsDouble(PySequence_GetItem(list, 3));
                if (PyErr_Occurred()) THROWMSG("invalid sequ. item");
            }
            fz_catch(gctx)
            {
                free(r);
                return NULL;
            }
            return r;
        }

        %pythonappend round() %{val.thisown = True%}
        %feature("autodoc","Create enclosing 'IRect'") round;
        struct fz_irect_s *round()
        {
            fz_irect *irect = (fz_irect *)malloc(sizeof(fz_irect));
            fz_rect rect = {MIN($self->x0, $self->x1),
                            MIN($self->y0, $self->y1),
                            MAX($self->x0, $self->x1),
                            MAX($self->y0, $self->y1)};
            fz_round_rect(irect, &rect);
            return irect;
        }

        %feature("autodoc","Enlarge to include a 'Point' p") includePoint;
        struct fz_rect_s *includePoint(const struct fz_point_s *p)
        {
            if (fz_is_infinite_rect($self)) return $self;
            return fz_include_point_in_rect($self, p);
        }

        %feature("autodoc","Shrink to intersection with another 'Rect' r") intersect;
        struct fz_rect_s *intersect(struct fz_rect_s *r) {
            fz_intersect_rect($self, r);
            return $self;
        }

        %feature("autodoc","Enlarge to include another 'Rect' r") includeRect;
        struct fz_rect_s *includeRect(struct fz_rect_s *r)
        {
            fz_union_rect($self, r);
            return $self;
        }
        
        %feature("autodoc","Make rectangle finite") normalize;
        struct fz_rect_s *normalize()
        {
            float f;
            if ($self->x1 < $self->x0)
            {
                f = $self->x1;
                $self->x1 = $self->x0;
                $self->x0 = f;
            }
            if ($self->y1 < $self->y0)
            {
                f = $self->y1;
                $self->y1 = $self->y0;
                $self->y0 = f;
            }
            return $self;
        }
        
        // check if Rect contains another Rect
        %feature("autodoc","contains") contains;
        PyObject *contains(struct fz_rect_s *rect)
        {
            if (fz_is_empty_rect(rect)) Py_RETURN_TRUE;
            if (fz_is_empty_rect($self)) Py_RETURN_FALSE;
            float l = MIN($self->x0, $self->x1);
            float r = MAX($self->x0, $self->x1);
            float t = MIN($self->y0, $self->y1);
            float b = MAX($self->y0, $self->y1);
                               
            return truth_value(INRANGE(rect->x0, l, r) &&
                               INRANGE(rect->x1, l, r) &&
                               INRANGE(rect->y0, t, b) &&
                               INRANGE(rect->y1, t, b));
        }

        // check if Rect contains another IRect
        PyObject *contains(struct fz_irect_s *rect)
        {
            if (fz_is_empty_irect(rect)) Py_RETURN_TRUE;
            if (fz_is_empty_rect($self)) Py_RETURN_FALSE;
            float l = MIN($self->x0, $self->x1);
            float r = MAX($self->x0, $self->x1);
            float t = MIN($self->y0, $self->y1);
            float b = MAX($self->y0, $self->y1);

            return truth_value(INRANGE(rect->x0, l, r) &&
                               INRANGE(rect->x1, l, r) &&
                               INRANGE(rect->y0, t, b) &&
                               INRANGE(rect->y1, t, b));
        }

        // check if Rect contains a Point
        PyObject *contains(struct fz_point_s *p)
        {
            if (fz_is_empty_rect($self)) Py_RETURN_FALSE;
            float l = MIN($self->x0, $self->x1);
            float r = MAX($self->x0, $self->x1);
            float t = MIN($self->y0, $self->y1);
            float b = MAX($self->y0, $self->y1);

            return truth_value(INRANGE(p->x, l, r) &&
                               INRANGE(p->y, t, b));
        }

        %pythoncode %{@property%}
        PyObject *isEmpty()
        {
            return truth_value(fz_is_empty_rect($self));
        }

        %pythoncode %{@property%}
        PyObject *isInfinite()
        {
            return truth_value(fz_is_infinite_rect($self));
        }

        %pythoncode %{
            def transform(self, m):
                """Transform rectangle with Matrix m."""
                _fitz._fz_transform_rect(self, m)
                return self

            @property
            def top_left(self):
                """Return the rectangle's top-left point."""
                return Point(self.x0, self.y0)
                
            @property
            def top_right(self):
                """Return the rectangle's top-right point."""
                return Point(self.x1, self.y0)
                
            @property
            def bottom_left(self):
                """Return the rectangle's bottom-left point."""
                return Point(self.x0, self.y1)
            
            @property
            def bottom_right(self):
                """Return the rectangle's bottom-right point."""
                return Point(self.x1, self.y1)
                
            def __getitem__(self, i):
                return (self.x0, self.y0, self.x1, self.y1)[i]

            def __setitem__(self, i, v):
                if   i == 0: self.x0 = v
                elif i == 1: self.y0 = v
                elif i == 2: self.x1 = v
                elif i == 3: self.y1 = v
                else:
                    raise IndexError("index out of range")
                return

            def __len__(self):
                return 4

            def __repr__(self):
                return "fitz.Rect" + str((self.x0, self.y0, self.x1, self.y1))

            irect = property(round)
            width = property(lambda self: self.x1-self.x0)
            height = property(lambda self: self.y1-self.y0)
            tl = top_left
            tr = top_right
            br = bottom_right
            bl = bottom_left
        %}
    }
};


/* fz_irect */
%rename(IRect) fz_irect_s;
struct fz_irect_s
{
    int x0, y0;
    int x1, y1;
    fz_irect_s();
    %extend {
        ~fz_irect_s() {
            DEBUGMSG1("irect");
            free($self);
            DEBUGMSG2;
        }
        FITZEXCEPTION(fz_irect_s, !result)
        fz_irect_s(const struct fz_irect_s *s) {
            fz_irect *r = (fz_irect *)malloc(sizeof(fz_irect));
            if (!s)
            {
                r->x0 = r->y0 = r->x1 = r->y1 = 0;
            }
            else *r = *s;
            return r;
        }

        fz_irect_s(int x0, int y0, int x1, int y1) {
            fz_irect *r = (fz_irect *)malloc(sizeof(fz_irect));
            r->x0 = x0;
            r->y0 = y0;
            r->x1 = x1;
            r->y1 = y1;
            return r;
        }

        //--------------------------------------------------------------------
        // create IRect from Python list
        //--------------------------------------------------------------------
        fz_irect_s(PyObject *list)
        {
            fz_irect *r = (fz_irect *)malloc(sizeof(fz_irect));
            fz_try(gctx)
            {
                if (!PySequence_Check(list)) THROWMSG("expected a sequence");
                if (PySequence_Size(list) != 4) THROWMSG("len(sequence) invalid");
                r->x0 = (int) PyInt_AsLong(PySequence_GetItem(list, 0));
                if (PyErr_Occurred()) THROWMSG("invalid sequ. item");
                r->y0 = (int) PyInt_AsLong(PySequence_GetItem(list, 1));
                if (PyErr_Occurred()) THROWMSG("invalid sequ. item");
                r->x1 = (int) PyInt_AsLong(PySequence_GetItem(list, 2));
                if (PyErr_Occurred()) THROWMSG("invalid sequ. item");
                r->y1 = (int) PyInt_AsLong(PySequence_GetItem(list, 3));
                if (PyErr_Occurred()) THROWMSG("invalid sequ. item");
            }
            fz_catch(gctx) 
            {
                free(r);
                return NULL;
            }
            return r;
        }

        %pythoncode %{@property%}
        PyObject *isEmpty()
        {
            return truth_value(fz_is_empty_irect($self));
        }

        %pythoncode %{@property%}
        PyObject *isInfinite()
        {
            return truth_value(fz_is_infinite_irect($self));
        }

        %feature("autodoc","Make rectangle finite") normalize;
        struct fz_irect_s *normalize()
        {
            int f;
            if ($self->x1 < $self->x0)
            {
                f = $self->x1;
                $self->x1 = $self->x0;
                $self->x0 = f;
            }
            if ($self->y1 < $self->y0)
            {
                f = $self->y1;
                $self->y1 = $self->y0;
                $self->y0 = f;
            }
            return $self;
        }
        
        %feature("autodoc","contains") contains;
        PyObject *contains(struct fz_irect_s *rect)
        {
            if (fz_is_empty_irect(rect)) Py_RETURN_TRUE;
            if (fz_is_empty_irect($self)) Py_RETURN_FALSE;
            int l = MIN($self->x0, $self->x1);
            int r = MAX($self->x0, $self->x1);
            int t = MIN($self->y0, $self->y1);
            int b = MAX($self->y0, $self->y1);
            
            return truth_value(INRANGE(rect->x0, l, r) &&
                               INRANGE(rect->x1, l, r) &&
                               INRANGE(rect->y0, t, b) &&
                               INRANGE(rect->y1, t, b));
        }

        PyObject *contains(struct fz_rect_s *rect)
        {
            if (fz_is_empty_rect(rect)) Py_RETURN_TRUE;
            if (fz_is_empty_irect($self)) Py_RETURN_FALSE;
            float l = MIN($self->x0, $self->x1);
            float r = MAX($self->x0, $self->x1);
            float t = MIN($self->y0, $self->y1);
            float b = MAX($self->y0, $self->y1);

            return truth_value(INRANGE(rect->x0, l, r) &&
                               INRANGE(rect->x1, l, r) &&
                               INRANGE(rect->y0, t, b) &&
                               INRANGE(rect->y1, t, b));
        }

        PyObject *contains(struct fz_point_s *p)
        {
            if (fz_is_empty_irect($self)) Py_RETURN_FALSE;
            float l = MIN($self->x0, $self->x1);
            float r = MAX($self->x0, $self->x1);
            float t = MIN($self->y0, $self->y1);
            float b = MAX($self->y0, $self->y1);

            return truth_value(INRANGE(p->x, l, r) &&
                               INRANGE(p->y, t, b));
        }

        struct fz_irect_s *translate(int xoff, int yoff) {
            fz_translate_irect($self, xoff, yoff);
            return $self;
        }

        struct fz_irect_s *intersect(struct fz_irect_s *ir) {
            fz_intersect_irect($self, ir);
            return $self;
        }

        %pythoncode %{
            def getRect(self):
                return Rect(self.x0, self.y0, self.x1, self.y1)
            
            rect = property(getRect)

            @property
            def top_left(self):
                return Point(self.x0, self.y0)
                
            @property
            def top_right(self):
                return Point(self.x1, self.y0)
                
            @property
            def bottom_left(self):
                return Point(self.x0, self.y1)
            
            @property
            def bottom_right(self):
                return Point(self.x1, self.y1)
                
            def __getitem__(self, i):
                return (self.x0, self.y0, self.x1, self.y1)[i]

            def __setitem__(self, i, v):
                if   i == 0: self.x0 = v
                elif i == 1: self.y0 = v
                elif i == 2: self.x1 = v
                elif i == 3: self.y1 = v
                else:
                    raise IndexError("index out of range")
                return

            def __len__(self):
                return 4

            def __repr__(self):
                if not type(self) is IRect: return
                return "fitz.IRect" + str((self.x0, self.y0, self.x1, self.y1))

            width = property(lambda self: self.x1-self.x0)
            height = property(lambda self: self.y1-self.y0)
            tl = top_left
            tr = top_right
            br = bottom_right
            bl = bottom_left

        %}
    }
};

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
        fz_pixmap_s(struct fz_colorspace_s *cs, const struct fz_irect_s *bbox, int alpha = 0)
        {
            fz_pixmap *pm = NULL;
            fz_separations *seps = NULL;
            fz_try(gctx)
                pm = fz_new_pixmap_with_bbox(gctx, cs, bbox, seps, alpha);
            fz_catch(gctx) return NULL;
            return pm;
        }

        //---------------------------------------------------------------------
        // copy pixmap, converting colorspace
        // New in v1.11: option to remove alpha
        // Changed in 1.13: alpha = 0 does not work since at least 1.12
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
        fz_pixmap_s(struct fz_pixmap_s *spix, float w, float h, struct fz_irect_s *clip = NULL)
        {
            fz_pixmap *pm = NULL;
            fz_try(gctx)
            {
                pm = fz_scale_pixmap(gctx, spix, spix->x, spix->y, w, h, clip);
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
                if (size < 1) THROWMSG("invalid argument type");
                data = fz_new_buffer_from_shared_data(gctx,
                              streamdata, size);
                img = fz_new_image_from_buffer(gctx, data);
                pm = fz_get_pixmap_from_image(gctx, img, NULL, NULL, NULL, NULL);
            }
            fz_always(gctx)
            {
                fz_drop_image(gctx, img);
                fz_drop_buffer(gctx, data);
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
                type = pdf_dict_get(gctx, ref, PDF_NAME_Subtype);
                if (!pdf_name_eq(gctx, type, PDF_NAME_Image))
                    THROWMSG("xref not an image");
                if (!pdf_is_stream(gctx, ref))
                    THROWMSG("xref is not a stream");
                img = pdf_load_image(gctx, pdf, ref);
                pdf_drop_obj(gctx, ref);
                pix = fz_get_pixmap_from_image(gctx, img, NULL, NULL, NULL, NULL);
            }
            fz_always(gctx)
            {
                fz_drop_image(gctx, img);
            }
            fz_catch(gctx)
            {
                fz_drop_pixmap(gctx, pix);
                pdf_drop_obj(gctx, ref);
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
                PySys_WriteStdout("warning: ignoring shrink factor < 1\n");
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
                PySys_WriteStdout("warning: colorspace invalid for function\n");
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
        // Pixmap.setResolution
        //----------------------------------------------------------------------
        void setResolution(int xres, int yres)
        {
            $self->xres = xres;
            $self->yres = yres;
        }

        //----------------------------------------------------------------------
        // clear total pixmap with 0x00 */
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
        void clearWith(int value, const struct fz_irect_s *bbox)
        {
            fz_clear_pixmap_rect_with_value(gctx, $self, value, bbox);
        }

        //----------------------------------------------------------------------
        // copy pixmaps 
        //----------------------------------------------------------------------
        FITZEXCEPTION(copyPixmap, !result)
        PyObject *copyPixmap(struct fz_pixmap_s *src, const struct fz_irect_s *bbox)
        {
            fz_try(gctx)
            {
                if (!fz_pixmap_colorspace(gctx, src))
                    THROWMSG("cannot copy pixmap with NULL colorspace");
                fz_copy_pixmap_rect(gctx, $self, src, bbox, NULL);
            }
            fz_catch(gctx) return NULL;
            return NONE;
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
        struct fz_irect_s *irect()
        {
            fz_irect *r = (fz_irect *)malloc(sizeof(fz_irect));
            r->x0 = r->y0 = r->x1 = r->y1 = 0;
            return fz_pixmap_bbox(gctx, $self, r);
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
                size_t data_len = 0;
                if (alphavalues)
                {
                    data_len = JM_CharFromBytesOrArray(alphavalues, &data);
                    if (data_len > 0 && data_len < w * h)
                        THROWMSG("not enough alpha values");
                }
                int i = 0, k = 0;
                while (i < balen)
                {
                    if (data_len > 0) $self->samples[i+n] = data[k];
                    else              $self->samples[i+n] = 255;
                    i += n+1;
                    k += 1;
                }
            }
            fz_catch(gctx) return NULL;
            return NONE;
        }

        //----------------------------------------------------------------------
        // getPNGData
        //----------------------------------------------------------------------
        FITZEXCEPTION(getPNGData, !result)
        PyObject *getPNGData(int savealpha=-1)
        {
            struct fz_buffer_s *res = NULL;
            fz_output *out = NULL;
            PyObject *r;
            if (savealpha != -1) PySys_WriteStdout("warning: ignoring savealpha\n");
            fz_try(gctx) {
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                fz_write_pixmap_as_png(gctx, out, $self);
                r = JM_BinFromBuffer(gctx, res);
            }
            fz_always(gctx)
            {
                fz_drop_output(gctx, out);
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) return NULL;
            return r;
        }

        //----------------------------------------------------------------------
        // _writeIMG
        //----------------------------------------------------------------------
        FITZEXCEPTION(_writeIMG, !result)
        PyObject *_writeIMG(char *filename, int format, int savealpha=-1)
        {
            if (savealpha != -1) PySys_WriteStdout("warning: ignoring savealpha\n");
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
                }
            }
            fz_catch(gctx) return NULL;
            return NONE;
        }
        %pythoncode %{
        def writePNG(self, filename, savealpha = -1):
            return self._writeIMG(filename, 1, savealpha)
        %}
        //----------------------------------------------------------------------
        // invertIRect
        //----------------------------------------------------------------------
        void invertIRect(const struct fz_irect_s *irect = NULL)
        {
            if (!fz_pixmap_colorspace(gctx, $self))
                {
                    PySys_WriteStdout("warning: ignored for stencil pixmap\n");
                    return;
                }
                    
            if (irect) fz_invert_pixmap_rect(gctx, $self, irect);
            else       fz_invert_pixmap(gctx, $self);
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
        int n()
        {
            return fz_colorspace_n(gctx, $self);
        }

        //----------------------------------------------------------------------
        // name of colorspace
        //----------------------------------------------------------------------
        const char *_name()
        {
            return fz_colorspace_name(gctx, $self);
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
        DeviceWrapper(struct fz_pixmap_s *pm, struct fz_irect_s *clip) {
            struct DeviceWrapper *dw = NULL;
            fz_try(gctx) {
                dw = (struct DeviceWrapper *)calloc(1, sizeof(struct DeviceWrapper));
                if (!clip)
                    dw->device = fz_new_draw_device(gctx, &fz_identity, pm);
                else
                    dw->device = fz_new_draw_device_with_bbox(gctx, &fz_identity, pm, clip);
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

//------------------------------------------------------------------------------
// fz_matrix
//------------------------------------------------------------------------------
%rename(_fz_pre_scale) fz_pre_scale;
%rename(_fz_pre_shear) fz_pre_shear;
%rename(_fz_pre_rotate) fz_pre_rotate;
struct fz_matrix_s *fz_pre_scale(struct fz_matrix_s *m, float sx, float sy);
struct fz_matrix_s *fz_pre_shear(struct fz_matrix_s *m, float sx, float sy);
struct fz_matrix_s *fz_pre_rotate(struct fz_matrix_s *m, float degree);
%rename(Matrix) fz_matrix_s;
struct fz_matrix_s
{
    float a, b, c, d, e, f;
    fz_matrix_s();
    %extend {
        FITZEXCEPTION(fz_matrix_s, !result)
        ~fz_matrix_s()
        {
            DEBUGMSG1("matrix");
            free($self);
            DEBUGMSG2;
        }
        
        //--------------------------------------------------------------------
        // copy constructor
        //--------------------------------------------------------------------
        fz_matrix_s(const struct fz_matrix_s* n)
        {
            fz_matrix *m = (fz_matrix *)malloc(sizeof(fz_matrix));
            if (!n)
            {
                m->a = m->b = m->c = m->d = m->e = m->f = 0;
            }
            else
            {
                *m = *n;
            }
            return m;
        }
        
        //--------------------------------------------------------------------
        // create a scale/shear matrix, scale matrix by default
        //--------------------------------------------------------------------
        fz_matrix_s(float sx, float sy, int shear=0)
        {
            fz_matrix *m = (fz_matrix *)malloc(sizeof(fz_matrix));
            if(shear) return fz_shear(m, sx, sy);
            return fz_scale(m, sx, sy);
        }
        
        //--------------------------------------------------------------------
        // create a matrix by its 6 components
        //--------------------------------------------------------------------
        fz_matrix_s(float r, float s, float t, float u, float v, float w)
        {
            fz_matrix *m = (fz_matrix *)malloc(sizeof(fz_matrix));
            m->a = r;
            m->b = s;
            m->c = t;
            m->d = u;
            m->e = v;
            m->f = w;
            return m;
        }

        //--------------------------------------------------------------------
        // create a rotation matrix
        //--------------------------------------------------------------------
        fz_matrix_s(float degree)
        {
            fz_matrix *m = (fz_matrix *)malloc(sizeof(fz_matrix));
            return fz_rotate(m, degree);
        }

        //--------------------------------------------------------------------
        // create matrix from Python sequence
        //--------------------------------------------------------------------
        fz_matrix_s(PyObject *list)
        {
            fz_matrix *m = (fz_matrix *)malloc(sizeof(fz_matrix));
            fz_try(gctx)
            {
                if (!PySequence_Check(list)) THROWMSG("expected a sequence");
                if (PySequence_Size(list) != 6) THROWMSG("len(sequence) invalid");
                m->a = (float) PyFloat_AsDouble(PySequence_GetItem(list, 0));
                if (PyErr_Occurred()) THROWMSG("invalid sequ. item");
                m->b = (float) PyFloat_AsDouble(PySequence_GetItem(list, 1));
                if (PyErr_Occurred()) THROWMSG("invalid sequ. item");
                m->c = (float) PyFloat_AsDouble(PySequence_GetItem(list, 2));
                if (PyErr_Occurred()) THROWMSG("invalid sequ. item");
                m->d = (float) PyFloat_AsDouble(PySequence_GetItem(list, 3));
                if (PyErr_Occurred()) THROWMSG("invalid sequ. item");
                m->e = (float) PyFloat_AsDouble(PySequence_GetItem(list, 4));
                if (PyErr_Occurred()) THROWMSG("invalid sequ. item");
                m->f = (float) PyFloat_AsDouble(PySequence_GetItem(list, 5));
                if (PyErr_Occurred()) THROWMSG("invalid sequ. item");
            }
            fz_catch(gctx)
            {
                free(m);
                return NULL;
            }
            return m;
        }

        //--------------------------------------------------------------------
        // invert a matrix
        //--------------------------------------------------------------------
        int invert(const struct fz_matrix_s *m)
        {
            int rc = fz_try_invert_matrix($self, m);
            return rc;
        }

        struct fz_matrix_s *preTranslate(float sx, float sy)
        {
            fz_pre_translate($self, sx, sy);
            return $self;
        }

        //--------------------------------------------------------------------
        // multiply matrices
        //--------------------------------------------------------------------
        struct fz_matrix_s *concat(struct fz_matrix_s *m1, struct fz_matrix_s *m2) {
            fz_concat($self, m1, m2);
            return $self;
        }

        %pythoncode %{
            def preScale(self, sx, sy):
                """preScale(Matrix self, float sx, float sy) -> Matrix self updated"""
                _fitz._fz_pre_scale(self, sx, sy)
                return self
            def preShear(self, sx, sy):
                """preShear(Matrix self, float sx, float sy) -> Matrix self updated"""
                _fitz._fz_pre_shear(self, sx, sy)
                return self
            def preRotate(self, degree):
                """preRotate(Matrix self, float degree) -> Matrix self updated"""
                _fitz._fz_pre_rotate(self, degree)
                return self
            def __getitem__(self, i):
                return (self.a, self.b, self.c, self.d, self.e, self.f)[i]

            def __setitem__(self, i, v):
                if   i == 0: self.a = v
                elif i == 1: self.b = v
                elif i == 2: self.c = v
                elif i == 3: self.d = v
                elif i == 4: self.e = v
                elif i == 5: self.f = v
                else:
                    raise IndexError("index out of range")
                return

            def __len__(self):
                return 6
            def __repr__(self):
                return "fitz.Matrix(%s, %s, %s, %s, %s, %s)" % (self.a, self.b, self.c, self.d, self.e, self.f)

        %}
    }
};


/* fz_outline */
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
        if not val:
            return ""
        if val.isprintable():
            return val
        nval = ""
        for c in val:
            if c.isprintable():
                nval += c
            else:
                break
        val = nval
        %}
        char *uri()
            {
            return $self->uri;
            }

        %pythoncode %{@property%}
        int isExternal()
            {
            if (!$self->uri) return 0;
            return fz_is_external_link(gctx, $self->uri);
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

/* fz_point */
%rename(_fz_transform_point) fz_transform_point;
struct fz_point_s *fz_transform_point(struct fz_point_s *restrict point, const struct fz_matrix_s *restrict transform);
%rename(Point) fz_point_s;
struct fz_point_s
{
    float x, y;
    fz_point_s();
    %extend
    {
        FITZEXCEPTION(fz_point_s, !result)
        fz_point_s(const struct fz_point_s *q) {
            fz_point *p = (fz_point *)malloc(sizeof(fz_point));
            if (!q)
            {
                p->x = p->y = 0;
            }
            else *p = *q;
            return p;
        }

        fz_point_s(float x, float y) {
            fz_point *p = (fz_point *)malloc(sizeof(fz_point));
            p->x = x;
            p->y = y;
            return p;
        }

        //--------------------------------------------------------------------
        // create Point from Python list
        //--------------------------------------------------------------------
        fz_point_s(PyObject *list)
        {
            fz_point *p = (fz_point *)malloc(sizeof(fz_point));
            fz_try(gctx)
            {
                if (!PySequence_Check(list)) THROWMSG("expected a sequence");
                if (PySequence_Size(list) != 2) THROWMSG("len(sequence) invalid");
                p->x = (float) PyFloat_AsDouble(PySequence_GetItem(list, 0));
                if (PyErr_Occurred()) THROWMSG("invalid sequ. item");
                p->y = (float) PyFloat_AsDouble(PySequence_GetItem(list, 1));
                if (PyErr_Occurred()) THROWMSG("invalid sequ. item");
            }
            fz_catch(gctx)
            {
                free(p);
                return NULL;
            }
            return p;
        }

        %pythoncode %{
            def distance_to(self, *args):
                """Return the distance to a rectangle or another point."""
                assert len(args) > 0, "at least one parameter must be given"
                x = args[0]
                if len(args) > 1:
                    unit = args[1]
                else:
                    unit = "px"
                u = {"px": (1.,1.), "in": (1.,72.), "cm": (2.54, 72.), "mm": (25.4, 72.)}
                f = u[unit][0] / u[unit][1]
                if type(x) is Point:
                    return abs(self - x) * f
            
                # from here on, x is a rectangle
                # as a safeguard, make a finite copy of it
                r = Rect(x.top_left, x.top_left)
                r = r | x.bottom_right
                if self in r:
                    return 0.0
                if self.x > r.x1:
                    if self.y >= r.y1:
                        return self.distance_to(r.bottom_right, unit)
                    elif self.y <= r.y0:
                        return self.distance_to(r.top_right, unit)
                    else:
                        return (self.x - r.x1) * f
                elif r.x0 <= self.x <= r.x1:
                    if self.y >= r.y1:
                        return (self.y - r.y1) * f
                    else:
                        return (r.y0 - self.y) * f
                else:
                    if self.y >= r.y1:
                        return self.distance_to(r.bottom_left, unit)
                    elif self.y <= r.y0:
                        return self.distance_to(r.top_left, unit)
                    else:
                        return (r.x0 - self.x) * f
        
            def transform(self, m):
                _fitz._fz_transform_point(self, m)
                return self

            def __setitem__(self, i, v):
                if i == 0:
                    self.x = v
                elif i == 1:
                    self.y = v
                else:
                    raise IndexError("index out of range")
                return

            def __getitem__(self, i):
                return (self.x, self.y)[i]

            def __len__(self):
                return 2

            def __repr__(self):
                return "fitz.Point" + str((self.x, self.y))
        %}
        ~fz_point_s()
        {
            DEBUGMSG1("point");
            free($self);
            DEBUGMSG2;
        }
    }
};

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
        struct fz_rect_s *rect()
        {
            fz_rect *r = (fz_rect *)malloc(sizeof(fz_rect));
            return fz_bound_annot(gctx, $self, r);
        }

        //---------------------------------------------------------------------
        // annotation get xref number
        //---------------------------------------------------------------------
        PARENTCHECK(_getXref)
        %feature("autodoc","Xref number of annotation") _getXref;
        int _getXref()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if(!annot) return 0;
            return pdf_to_num(gctx, annot->obj);
        }

        //---------------------------------------------------------------------
        // annotation get decompressed appearance stream source
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getAP, !result)
        PARENTCHECK(_getAP)
        %feature("autodoc","Get contents source of a PDF annot") _getAP;
        PyObject *_getAP()
        {
            PyObject *r = NONE;
            fz_buffer *res = NULL;
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;
            fz_try(gctx)
            {
                res = pdf_load_stream(gctx, annot->ap);
                if (res) r = JM_BytesFromBuffer(gctx, res);
            }
            fz_always(gctx) fz_drop_buffer(gctx, res);
            fz_catch(gctx) return NONE;
            return r;
        }

        //---------------------------------------------------------------------
        // annotation update /AP stream
        //---------------------------------------------------------------------
        FITZEXCEPTION(_setAP, !result)
        PARENTCHECK(_setAP)
        %feature("autodoc","Update contents source of a PDF annot") _setAP;
        PyObject *_setAP(PyObject *ap)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            fz_buffer *res = NULL;
            fz_try(gctx)
            {
                assert_PDF(annot);
                if (!annot->ap) THROWMSG("annot has no /AP object");
                char *c = NULL;
                size_t len = JM_CharFromBytesOrArray(ap, &c);
                if (len < 1) THROWMSG("invalid content argument");
                res = fz_new_buffer_from_shared_data(gctx, c, len);
                JM_update_stream(gctx, annot->page->doc, annot->ap, res);
                pdf_dirty_annot(gctx, annot);
                pdf_update_page(gctx, annot->page);
            }
            fz_catch(gctx) return NULL;
            return NONE;
        }

        //---------------------------------------------------------------------
        // annotation create or update /AP object
        //---------------------------------------------------------------------
        FITZEXCEPTION(_checkAP, !result)
        PARENTCHECK(_checkAP)
        %feature("autodoc","Check and update /AP object of annot") _checkAP;
        PyObject *_checkAP(struct fz_rect_s *rect, char *c)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(annot);
                JM_make_ap_object(gctx, $self, rect, c);
                pdf_dirty_annot(gctx, annot);
                pdf_update_page(gctx, annot->page);
            }
            fz_catch(gctx) return NULL;
            return NONE;
        }

        //---------------------------------------------------------------------
        // annotation set rectangle
        //---------------------------------------------------------------------
        void _setRect(struct fz_rect_s *rect)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return;
            fz_try(gctx)
            {
                pdf_set_annot_rect(gctx, annot, rect);
            }
            fz_catch(gctx) {;}
            return;
        }
        %pythoncode %{
        def setRect(self, rect):
            """Change the annot's rectangle."""
            CheckParent(self)
            if rect.isEmpty or rect.isInfinite:
                raise ValueError("Rect must be finite and not empty.")
            # only handle Circle, Square, Line, PolyLine and Polygon here
            if self.type[0] not in range(2, 8):
                self._setRect(rect)
                return

            if self.type[0] == ANNOT_CIRCLE:
                self._setRect(rect)
                ap = _make_circle_AP(self)
                self._checkAP(Rect(0, 0, rect.width, rect.height), ap)
                return

            if self.type[0] == ANNOT_SQUARE:
                self._setRect(rect)
                ap = _make_rect_AP(self)
                self._checkAP(Rect(0, 0, rect.width, rect.height), ap)
                return

            orect = self.rect
            m = Matrix(rect.width / orect.width, rect.height / orect.height)
            
            # now transform the points of the annot
            ov = self.vertices
            nv = [(Point(v) - orect.tl) * m + rect.tl for v in ov] # new points
            r0 = Rect(nv[0], nv[0])              # recalculate new rectangle
            for v in nv[1:]:
                r0 |= v                          # enveloping all points
            w = self.border["width"] * 3         # allow for add'l space
            r0 += (-w, -w, w, w)                 # for line end symbols
            self._setRect(r0)                    # this is the final rect
            self._setVertices(nv)                # put the points in annot
            ap = _make_line_AP(self, nv, r0)
            self._checkAP(Rect(0, 0, r0.width, r0.height), ap)
        %}

        //---------------------------------------------------------------------
        // annotation vertices (for "Line", "Polgon", "Ink", etc.
        //---------------------------------------------------------------------
        PARENTCHECK(vertices)
        %feature("autodoc","Point coordinates for various annot types") vertices;
        %pythoncode %{@property%}
        PyObject *vertices()
        {
            PyObject *res, *list;
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;                  // not a PDF!

            //----------------------------------------------------------------
            // The following objects occur in different annotation types.
            // So we are sure that o != NULL occurs at most once.
            // Every pair of floats is one point, that needs to be separately
            // transformed with the page's transformation matrix.
            //----------------------------------------------------------------
            pdf_obj *o = pdf_dict_get(gctx, annot->obj, PDF_NAME_Vertices);
            if (!o) o = pdf_dict_get(gctx, annot->obj, PDF_NAME_L);
            if (!o) o = pdf_dict_get(gctx, annot->obj, PDF_NAME_QuadPoints);
            if (!o) o = pdf_dict_gets(gctx, annot->obj, "CL");
            int i, j, n;
            fz_point point;            // point object to work with
            fz_matrix page_ctm;        // page transformation matrix
            pdf_page_transform(gctx, annot->page, NULL, &page_ctm);

            if (o)                     // anything found yet?
            {
                res = PyList_New(0);   // create Python list
                n = pdf_array_len(gctx, o);
                for (i = 0; i < n; i += 2)
                {
                    point.x = pdf_to_real(gctx, pdf_array_get(gctx, o, i));
                    point.y = pdf_to_real(gctx, pdf_array_get(gctx, o, i+1));
                    fz_transform_point(&point, &page_ctm);
                    PyList_Append(res, Py_BuildValue("ff", point.x, point.y));
                }
                return res;
            }
            // nothing found so far - maybe an Ink annotation?
            pdf_obj *il_o = pdf_dict_get(gctx, annot->obj, PDF_NAME_InkList);
            if (!il_o) return NONE;                   // no inkList
            res = PyList_New(0);                      // create result list
            n = pdf_array_len(gctx, il_o);
            for (i = 0; i < n; i++)
            {
                list = PyList_New(0);
                o = pdf_array_get(gctx, il_o, i);
                int m = pdf_array_len(gctx, o);
                for (j = 0; j < m; j += 2)
                {
                    point.x = pdf_to_real(gctx, pdf_array_get(gctx, o, j));
                    point.y = pdf_to_real(gctx, pdf_array_get(gctx, o, j+1));
                    fz_transform_point(&point, &page_ctm);
                    PyList_Append(list, Py_BuildValue("ff", point.x, point.y));
                }
                PyList_Append(res, list);
                Py_DECREF(list);
            }
            return res;
        }

        //---------------------------------------------------------------------
        // annotation set vertices
        //---------------------------------------------------------------------
        FITZEXCEPTION(_setVertices, !result)
        PARENTCHECK(_setVertices)
        %feature("autodoc","Change the annot's vertices. Only for 'Line', 'PolyLine' and 'Polygon' types.") _setVertices;
        PyObject *_setVertices(PyObject *vertices)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;
            int type = pdf_annot_type(gctx, annot);
            if (!INRANGE(type, 3, 7)) return NONE;
            if (INRANGE(type, 4, 5)) return NONE; // only handling 3 types
            fz_try(gctx)
            {
                fz_point a, b;
                PyObject *p = NULL;
                if (type == PDF_ANNOT_LINE)
                {
                    p = PySequence_ITEM(vertices, 0);
                    a.x = (float) PyFloat_AsDouble(PySequence_ITEM(p, 0));
                    a.y = (float) PyFloat_AsDouble(PySequence_ITEM(p, 1));
                    Py_DECREF(p);
                    p = PySequence_ITEM(vertices, 1);
                    b.x = (float) PyFloat_AsDouble(PySequence_ITEM(p, 0));
                    b.y = (float) PyFloat_AsDouble(PySequence_ITEM(p, 1));
                    Py_DECREF(p);
                    pdf_set_annot_line(gctx, annot, a, b);
                }
                else
                {
                    int i, n = PySequence_Size(vertices);
                    for (i = 0; i < n; i++)
                    {
                        p = PySequence_ITEM(vertices, i);
                        a.x = (float) PyFloat_AsDouble(PySequence_ITEM(p, 0));
                        a.y = (float) PyFloat_AsDouble(PySequence_ITEM(p, 1));
                        Py_DECREF(p);
                        pdf_set_annot_vertex(gctx, annot, i, a);
                    }
                }

            }
            fz_catch(gctx) return NULL;
            return NONE;
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
             
            PyObject *res = PyDict_New();
            PyObject *bc = PyList_New(0);        // stroke colors
            PyObject *fc = PyList_New(0);        // fill colors

            int i;
            float col;
            pdf_obj *o = pdf_dict_get(gctx, annot->obj, PDF_NAME_C);
            if (pdf_is_array(gctx, o))
            {
                int n = pdf_array_len(gctx, o);
                for (i = 0; i < n; i++)
                {
                    col = pdf_to_real(gctx, pdf_array_get(gctx, o, i));
                    PyList_Append(bc, Py_BuildValue("f", col));
                }
            }
            PyDict_SetItemString(res, "stroke", bc);

            o = pdf_dict_gets(gctx, annot->obj, "IC");
            if (pdf_is_array(gctx, o))
            {
                int n = pdf_array_len(gctx, o);
                for (i = 0; i < n; i++)
                {
                    col = pdf_to_real(gctx, pdf_array_get(gctx, o, i));
                    PyList_Append(fc, Py_BuildValue("f", col));
                }
            }
            PyDict_SetItemString(res, "fill", fc);

            Py_DECREF(bc);
            Py_DECREF(fc);
            return res;
        }

        //---------------------------------------------------------------------
        // annotation update appearance
        //---------------------------------------------------------------------
        PARENTCHECK(updateAppearance)
        %feature("autodoc","Update the appearance of an annotation.") updateAppearance;
        PyObject *updateAppearance()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;
            fz_try(gctx)
            {
                pdf_update_appearance(gctx, annot);
            }
            fz_catch(gctx)
            {
                PySys_WriteStderr("cannot update annot: '%s'\n", fz_caught_message(gctx));
                Py_RETURN_FALSE;
            }
            Py_RETURN_TRUE;
        }

        //---------------------------------------------------------------------
        // annotation set colors
        //---------------------------------------------------------------------
        PARENTCHECK(setColors)
        %feature("autodoc","setColors(dict)\nChanges the 'stroke' and 'fill' colors of an annotation. If provided, values must be lists of up to 4 floats.") setColors;
        %pythonappend setColors %{
        if self.type[0] not in range(2, 8):
            return
        r = Rect(0, 0, self.rect.width, self.rect.height)
        if self.type[0] == ANNOT_CIRCLE:
            ap = _make_circle_AP(self)
        elif self.type[0] == ANNOT_SQUARE:
            ap = _make_rect_AP(self)
        else:
            ap = _make_line_AP(self)
        self._checkAP(r, ap)
        %}
        void setColors(PyObject *colors)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return;
            if (!PyDict_Check(colors)) return;
            if (pdf_annot_type(gctx, annot) == PDF_ANNOT_WIDGET)
            {
                PySys_WriteStdout("use 'updateWidget' to change form fields\n");
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
                    col[i] = (float) PyFloat_AsDouble(PySequence_GetItem(ccol, i));
                fz_try(gctx)
                    pdf_set_annot_color(gctx, annot, n, col);
                fz_catch(gctx)
                    PySys_WriteStdout("cannot set stroke color for this annot type\n");
            }
            n = 0;
            if (icol)
                if (PySequence_Check(icol))
                    n = (int) PySequence_Size(icol);
            if (n>0)
            {
                if (!pdf_annot_has_interior_color(gctx, annot))
                {
                    PySys_WriteStdout("annot type has no fill color\n");
                    return;
                }
                for (i=0; i<n; i++)
                    col[i] = (float) PyFloat_AsDouble(PySequence_GetItem(icol, i));
                fz_try(gctx)
                    pdf_set_annot_interior_color(gctx, annot, n, col);
                fz_catch(gctx)
                    PySys_WriteStdout("cannot set fill color for this annot type\n");
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
        %pythonappend setLineEnds %{
        if self.type[0] not in range(2, 8):
            return
        if self.type[0] in (ANNOT_CIRCLE, ANNOT_SQUARE):
            return
        r = Rect(0, 0, self.rect.width, self.rect.height)
        ap = _make_line_AP(self)
        self._checkAP(r, ap)
        %}
        void setLineEnds(int start, int end)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return;
            if (pdf_annot_has_line_ending_styles(gctx, annot))
                pdf_set_annot_line_ending_styles(gctx, annot, start, end);
            else
                PySys_WriteStdout("annot type has no line ends\n");
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
        float opacity()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return 1;                // not a PDF
            return pdf_annot_opacity(gctx, annot);
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
                pdf_set_annot_opacity(gctx, annot, 1);
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
                stream = pdf_dict_getl(gctx, annot->obj, PDF_NAME_FS,
                                   PDF_NAME_EF, PDF_NAME_F, NULL);
                if (!stream) THROWMSG("bad PDF: file entry not found");
            }
            fz_catch(gctx) return NULL;

            fs = pdf_dict_get(gctx, annot->obj, PDF_NAME_FS);

            o = pdf_dict_get(gctx, fs, PDF_NAME_UF);
            if (o) filename = pdf_to_utf8(gctx, o);
            else
            {
                o = pdf_dict_get(gctx, fs, PDF_NAME_F);
                if (o) filename = pdf_to_utf8(gctx, o);
            }

            o = pdf_dict_get(gctx, fs, PDF_NAME_Desc);
            if (o) desc = pdf_to_utf8(gctx, o);

            o = pdf_dict_get(gctx, stream, PDF_NAME_Length);
            if (o) length = pdf_to_int(gctx, o);

            o = pdf_dict_getl(gctx, stream, PDF_NAME_Params,
                                PDF_NAME_Size, NULL);
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
                stream = pdf_dict_getl(gctx, annot->obj, PDF_NAME_FS,
                                   PDF_NAME_EF, PDF_NAME_F, NULL);
                if (!stream) THROWMSG("bad PDF: file entry not found");
                buf = pdf_load_stream(gctx, stream);
                res = JM_BytesFromBuffer(gctx, buf);
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
                stream = pdf_dict_getl(gctx, annot->obj, PDF_NAME_FS,
                                   PDF_NAME_EF, PDF_NAME_F, NULL);
                // the object for file content
                if (!stream) THROWMSG("bad PDF: file entry not found");
                
                fs = pdf_dict_get(gctx, annot->obj, PDF_NAME_FS);

                // file content is ignored if not bytes / bytearray
                size = (int64_t) JM_CharFromBytesOrArray(buffer, &data);
                if (size > 0)
                {
                    pdf_obj *s = pdf_new_int(gctx, NULL, size);
                    pdf_dict_put(gctx, stream, PDF_NAME_Filter,
                                 PDF_NAME_FlateDecode);

                    pdf_dict_putl_drop(gctx, stream, s,
                                       PDF_NAME_Params, PDF_NAME_Size, NULL);
                    res = JM_deflatebuf(gctx, data, size);
                    pdf_update_stream(gctx, pdf, stream, res, 1);
                }

                if (filename)               // new filename given
                {
                    pdf_dict_put_text_string(gctx, stream, PDF_NAME_F, filename);
                    pdf_dict_put_text_string(gctx, fs, PDF_NAME_F, filename);
                }

                if (ufilename)
                {
                    pdf_dict_put_text_string(gctx, stream, PDF_NAME_UF, filename);
                    pdf_dict_put_text_string(gctx, fs, PDF_NAME_UF, filename);
                }

                if (desc)                   // new description given
                {
                    pdf_dict_put_text_string(gctx, stream, PDF_NAME_Desc, desc);
                    pdf_dict_put_text_string(gctx, fs, PDF_NAME_Desc, desc);
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
            c = pdf_copy_annot_contents(gctx, annot);
            PyDict_SetItemString(res, "content", JM_UNICODE(c));

            o = pdf_dict_get(gctx, annot->obj, PDF_NAME_Name);
            c = (char *) pdf_to_name(gctx, o);
            PyDict_SetItemString(res, "name", JM_UNICODE(c));

            // Title, author
            o = pdf_dict_get(gctx, annot->obj, PDF_NAME_T);
            c = pdf_to_utf8(gctx, o);
            PyDict_SetItemString(res, "title", JM_UNICODE(c));

            // CreationDate
            o = pdf_dict_gets(gctx, annot->obj, "CreationDate");
            c = pdf_to_utf8(gctx, o);
            PyDict_SetItemString(res, "creationDate", JM_UNICODE(c));

            // ModDate
            o = pdf_dict_get(gctx, annot->obj, PDF_NAME_M);
            c = pdf_to_utf8(gctx, o);
            PyDict_SetItemString(res, "modDate", JM_UNICODE(c));

            // Subj
            o = pdf_dict_gets(gctx, annot->obj, "Subj");
            c = pdf_to_utf8(gctx, o);
            PyDict_SetItemString(res, "subject", JM_UNICODE(c));

            return res;
        }

        /**********************************************************************/
        // annotation set information
        /**********************************************************************/
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
                                                 PDF_NAME_CreationDate, uc);
                        JM_Python_str_DelForPy3(uc);
                    }

                    // mod date
                    uc = JM_Python_str_AsChar(PyDict_GetItemString(info, "modDate"));
                    if (uc)
                    {
                        pdf_dict_put_text_string(gctx, annot->obj,
                                                 PDF_NAME_M, uc);
                        JM_Python_str_DelForPy3(uc);
                    }

                    // subject
                    uc = JM_Python_str_AsChar(PyDict_GetItemString(info, "subject"));
                    if (uc)
                    {
                        pdf_dict_puts_drop(gctx, annot->obj, "Subj",
                                           pdf_new_text_string(gctx, NULL, uc));
                        JM_Python_str_DelForPy3(uc);
                    }
                }
            }
            fz_catch(gctx) return NULL;
            return NONE;
        }

        /**********************************************************************/
        // annotation border
        // PDF dictionaries checked are /Border, /BS, and /BE
        // return a dictionary
        /**********************************************************************/
        PARENTCHECK(border)
        %pythoncode %{@property%}
        PyObject *border()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;                   // not a PDF
            PyObject *res = PyDict_New();
            PyObject *dash_py   = PyList_New(0);
            PyObject *effect_py = PyList_New(0);
            int i;
            char *effect2 = NULL, *style = NULL;
            float width = 0;
            int effect1 = -1;

            pdf_obj *o = pdf_dict_get(gctx, annot->obj, PDF_NAME_Border);
            if (pdf_is_array(gctx, o))
            {
                width = pdf_to_real(gctx, pdf_array_get(gctx, o, 2));
                if (pdf_array_len(gctx, o) == 4)
                {
                    pdf_obj *dash = pdf_array_get(gctx, o, 3);
                    for (i = 0; i < pdf_array_len(gctx, dash); i++)
                        PyList_Append(dash_py, Py_BuildValue("i",
                                      pdf_to_int(gctx, pdf_array_get(gctx, dash, i))));
                }
            }

            pdf_obj *bs_o = pdf_dict_get(gctx, annot->obj, PDF_NAME_BS);
            if (bs_o)
            {
                o = pdf_dict_get(gctx, bs_o, PDF_NAME_W);
                if (o) width = pdf_to_real(gctx, o);
                o = pdf_dict_get(gctx, bs_o, PDF_NAME_S);
                if (o)
                {
                    style = (char *) pdf_to_name(gctx, o);
                }
                o = pdf_dict_get(gctx, bs_o, PDF_NAME_D);
                if (o)
                {
                    for (i = 0; i < pdf_array_len(gctx, o); i++)
                        PyList_Append(dash_py, Py_BuildValue("i",
                                      pdf_to_int(gctx, pdf_array_get(gctx, o, i))));
                }
            }

            pdf_obj *be_o = pdf_dict_gets(gctx, annot->obj, "BE");
            if (be_o)
            {
                o = pdf_dict_get(gctx, be_o, PDF_NAME_S);
                if (o) effect2 = (char *) pdf_to_name(gctx, o);
                o = pdf_dict_get(gctx, be_o, PDF_NAME_I);
                if (o) effect1 = pdf_to_int(gctx, o);
            }

            PyList_Append(effect_py, Py_BuildValue("i", effect1));
            PyList_Append(effect_py, Py_BuildValue("s", effect2));

            PyDict_SetItemString(res, "width", Py_BuildValue("f", width));

            PyDict_SetItemString(res, "dashes", dash_py);

            PyDict_SetItemString(res, "style", Py_BuildValue("s", style));

            if (effect1 > -1) PyDict_SetItemString(res, "effect", effect_py);
            Py_DECREF(effect_py);
            Py_DECREF(dash_py);
            return res;
        }

        //---------------------------------------------------------------------
        // set annotation border
        //---------------------------------------------------------------------
        PARENTCHECK(setBorder)
        %pythonappend setBorder %{_upd_my_AP(self)%}
        PyObject *setBorder(PyObject *border)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return NONE;                   // not a PDF
            if (!PyDict_Check(border))
            {
                PySys_WriteStdout("arg must be a dict");
                return NONE;     // not a dict
            }

            pdf_document *doc = annot->page->doc;     // PDF document
            float nwidth = -1;                        // new width
            PyObject *ndashes = NULL;                 // new dashes
            PyObject *nstyle = NULL;                  // new style
            float owidth = -1;                        // old width
            PyObject *odashes = NULL;                 // old dashes
            PyObject *ostyle  = NULL;                 // old style

            nwidth = (float) PyFloat_AsDouble(PyDict_GetItemString(border, "width"));
            PyErr_Clear();
            ndashes = PyDict_GetItemString(border, "dashes");
            nstyle  = PyDict_GetItemString(border, "style");

            // first get old border properties
            PyObject *oborder = fz_annot_s_border($self);
            owidth = (float) PyFloat_AsDouble(PyDict_GetItemString(oborder, "width"));
            PyErr_Clear();
            odashes = PyDict_GetItemString(oborder, "dashes");
            ostyle = PyDict_GetItemString(oborder, "style");

            // then delete current annot entries
            pdf_dict_del(gctx, annot->obj, PDF_NAME_BS);
            pdf_dict_del(gctx, annot->obj, PDF_NAME_BE);
            pdf_dict_del(gctx, annot->obj, PDF_NAME_Border);
            
            Py_ssize_t i, n;
            int d;
            // populate new border array
            if (nwidth < 0) nwidth = owidth;     // no new width: take current
            if (nwidth < 0) nwidth = 0;          // default if no width given
            
            if (!ndashes) ndashes = odashes;     // no new dashes: take old

            if (!nstyle)  nstyle  = ostyle;      // no new style: take old

            if (ndashes && PySequence_Check(ndashes) && PySequence_Size(ndashes))
            {
                n = PySequence_Size(ndashes);
                pdf_obj *darr = pdf_new_array(gctx, doc, n);
                for (i = 0; i < n; i++)
                {
                    d = (int) PyInt_AsLong(PySequence_GetItem(ndashes, i));
                    pdf_array_push_int(gctx, darr, (int64_t) d);
                }
                pdf_dict_putl_drop(gctx, annot->obj, darr, PDF_NAME_BS, PDF_NAME_D, NULL);
            }

            pdf_dict_putl_drop(gctx, annot->obj, pdf_new_real(gctx, doc, nwidth),
                               PDF_NAME_BS, PDF_NAME_W, NULL);

            pdf_obj *val = JM_get_border_style(gctx, nstyle);

            pdf_dict_putl_drop(gctx, annot->obj, val,
                               PDF_NAME_BS, PDF_NAME_S, NULL);

            pdf_dirty_annot(gctx, annot);
            PyErr_Clear();
            return NONE;
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
        struct fz_pixmap_s *getPixmap(struct fz_matrix_s *matrix = NULL, struct fz_colorspace_s *colorspace = NULL, int alpha = 0)
        {
            struct fz_matrix_s *ctm = (fz_matrix *) &fz_identity;
            struct fz_colorspace_s *cs = fz_device_rgb(gctx);
            fz_pixmap *pix = NULL;
            if (matrix) ctm = matrix;
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
                                      PDF_NAME_BS, PDF_NAME_W, NULL));
                if (border_width == 0.0f) border_width = 1.0f;
                PyObject_SetAttrString(Widget, "border_width",
                                       Py_BuildValue("f", border_width));

                pdf_obj *dashes = pdf_dict_getl(gctx, annot->obj,
                                      PDF_NAME_BS, PDF_NAME_D, NULL);
                if (pdf_is_array(gctx, dashes))
                {
                    n = (Py_ssize_t) pdf_array_len(gctx, dashes);
                    PyObject *d = PyList_New(n);
                    for (i = 0; i < n; i++)
                        PyList_SetItem(d, i, Py_BuildValue("i", pdf_to_int(gctx,
                                      pdf_array_get(gctx, dashes, (int) i))));

                    PyObject_SetAttrString(Widget, "border_dashes", d);
                    Py_DECREF(d);
                }

                int text_maxlen = pdf_to_int(gctx, pdf_get_inheritable(gctx, pdf, annot->obj, PDF_NAME_MaxLen));
                PyObject_SetAttrString(Widget, "text_maxlen",
                                       Py_BuildValue("i", text_maxlen));

                // entry ignored for new / updated widgets
                int text_type = pdf_text_widget_content_type(gctx, pdf, tw);
                PyObject_SetAttrString(Widget, "text_type",
                                       Py_BuildValue("i", text_type));

                pdf_obj *bgcol = pdf_dict_getl(gctx, annot->obj,
                                               PDF_NAME_MK, PDF_NAME_BG, NULL);
                if (pdf_is_array(gctx, bgcol))
                {
                    n = (Py_ssize_t) pdf_array_len(gctx, bgcol);
                    PyObject *col = PyList_New(n);
                    for (i = 0; i < n; i++)
                        PyList_SetItem(col, i, Py_BuildValue("f",
                        pdf_to_real(gctx, pdf_array_get(gctx, bgcol, (int) i))));

                    PyObject_SetAttrString(Widget, "fill_color", col);
                    Py_DECREF(col);
                }

                pdf_obj *bccol = pdf_dict_getl(gctx, annot->obj, PDF_NAME_MK, PDF_NAME_BC, NULL);

                if (pdf_is_array(gctx, bccol))
                {
                    n = (Py_ssize_t) pdf_array_len(gctx, bccol);
                    PyObject *col = PyList_New(n);
                    for (i = 0; i < n; i++)
                        PyList_SetItem(col, i, Py_BuildValue("f",
                        pdf_to_real(gctx, pdf_array_get(gctx, bccol, (int) i))));

                    PyObject_SetAttrString(Widget, "border_color", col);
                    Py_DECREF(col);
                }

                char *da = pdf_to_str_buf(gctx, pdf_get_inheritable(gctx,
                                                pdf, annot->obj, PDF_NAME_DA));
                PyObject_SetAttrString(Widget, "_text_da", Py_BuildValue("s", da));

                pdf_obj *ca = pdf_dict_getl(gctx, annot->obj,
                                            PDF_NAME_MK, PDF_NAME_CA, NULL);
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

/*****************************************************************************/
// fz_link
/*****************************************************************************/
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

        PARENTCHECK(uri)
        %pythoncode %{@property%}
        %pythonappend uri %{
        if not val:
            return ""
        if val.isprintable():
            return val
        nval = ""
        for c in val:
            if c.isprintable():
                nval += c
            else:
                break
        val = nval
        %}
        char *uri()
        {
            return $self->uri;
        }

        PARENTCHECK(isExternal)
        %pythoncode %{@property%}
        int isExternal()
        {
            if (!$self->uri) return 0;
            return fz_is_external_link(gctx, $self->uri);
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
        struct fz_rect_s *rect()
        {
            fz_rect *r = (fz_rect *)malloc(sizeof(fz_rect));
            r->x0 = $self->rect.x0;
            r->y0 = $self->rect.y0;
            r->x1 = $self->rect.x1;
            r->y1 = $self->rect.y1;
            return r;
        }

        /*********************************************************************/
        // next link
        /*********************************************************************/
        // we need to increase the link refs number
        // so that it will not be freed when the head is dropped
        PARENTCHECK(next)
        %pythonappend next
%{if val:
    val.thisown = True
    val.parent = self.parent # copy owning page object from previous annot
    val.parent._annot_refs[id(val)] = val%}
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

/*****************************************************************************/
/* fz_display_list */
/*****************************************************************************/
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
        fz_display_list_s(struct fz_rect_s *mediabox)
        {
            struct fz_display_list_s *dl = NULL;
            fz_try(gctx)
                dl = fz_new_display_list(gctx, mediabox);
            fz_catch(gctx) return NULL;
            return dl;
        }

        FITZEXCEPTION(run, result)
        int run(struct DeviceWrapper *dw, const struct fz_matrix_s *m, const struct fz_rect_s *area) {
            fz_try(gctx)
            {
                fz_run_display_list(gctx, $self, dw->device, m, area, NULL);
            }
            fz_catch(gctx) return 1;
            return 0;
        }

        //---------------------------------------------------------------------
        // DisplayList.rect
        //---------------------------------------------------------------------
        %pythoncode%{@property%}
        struct fz_rect_s *rect()
        {
            fz_rect *mediabox = (fz_rect *)malloc(sizeof(fz_rect));
            fz_bound_display_list(gctx, $self, mediabox);
            return mediabox;
        }

        //---------------------------------------------------------------------
        // DisplayList.getPixmap
        //---------------------------------------------------------------------
        FITZEXCEPTION(getPixmap, !result)
        struct fz_pixmap_s *getPixmap(const struct fz_matrix_s *matrix = NULL, struct fz_colorspace_s *colorspace = NULL, int alpha = 0, struct fz_rect_s *clip = NULL)
        {
            struct fz_matrix_s *m = NULL;
            struct fz_colorspace_s *cs = NULL;
            fz_pixmap *pix = NULL;
            if (matrix) m = (fz_matrix *) matrix;
            else m = (fz_matrix *) &fz_identity;

            if (colorspace) cs = colorspace;
            else cs = fz_device_rgb(gctx);

            fz_try(gctx)
            {
                pix = JM_pixmap_from_display_list(gctx, $self, m, cs, alpha, clip);
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
    }
};

//-----------------------------------------------------------------------------
// fz_stext_page
//-----------------------------------------------------------------------------
%rename(TextPage) fz_stext_page_s;
struct fz_stext_page_s {
    %extend {
        FITZEXCEPTION(fz_stext_page_s, !result)
        fz_stext_page_s(struct fz_rect_s *mediabox) {
            struct fz_stext_page_s *tp = NULL;
            fz_try(gctx)
                tp = fz_new_stext_page(gctx, mediabox);
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
        %pythonappend search %{
        if val:
            nval = []
            for r in val:
                nval.append(Rect(r))
            val = nval
        %}
        PyObject *search(const char *needle, int hit_max=16)
        {
            fz_rect *result = NULL;
            PyObject *liste = PyList_New(0);
            int i, mymax = hit_max;
            if (mymax < 1) mymax = 16;
            result = (fz_rect *)malloc(sizeof(fz_rect)*(mymax+1));
            struct fz_rect_s *rect = (struct fz_rect_s *) result;
            int count = fz_search_stext_page(gctx, $self, needle, result, hit_max);
            for (i = 0; i < count; i++)
            {
                PyList_Append(liste,
                              Py_BuildValue("ffff", rect->x0, rect->y0,
                                            rect->x1,rect->y1));
                rect += 1;
            }
            free(result);
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
                fz_rect *blockrect = JM_empty_rect();
                if (block->type == FZ_STEXT_BLOCK_TEXT)
                {
                    fz_try(gctx)
                    {
                        res = fz_new_buffer(gctx, 1024);
                        int line_n = 0;
                        float last_y0 = 0.0;
                        for (line = block->u.t.first_line; line; line = line->next)
                        {
                            fz_rect *linerect = JM_empty_rect();
                            // append line no. 2 with new-line 
                            if (line_n > 0)
                            {
                                if (linerect->y0 != last_y0)
                                    fz_append_string(gctx, res, "\n");
                                else
                                    fz_append_string(gctx, res, " ");
                            }
                            last_y0 = linerect->y0;
                            line_n++;
                            for (ch = line->first_char; ch; ch = ch->next)
                            {
                                fz_append_rune(gctx, res, ch->c);
                                JM_join_rect(linerect, &ch->bbox, ch->size);
                            }
                            JM_join_rect(blockrect, linerect, 0.0f);
                            free(linerect);
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
                    JM_join_rect(blockrect, &block->bbox, 0.0f);
                }
                litem = Py_BuildValue("ffffOii", blockrect->x0, blockrect->y0,
                                      blockrect->x1, blockrect->y1,
                                      text, block_n, block->type);
                PyList_Append(lines, litem);
                Py_DECREF(litem);
                Py_DECREF(text);
                free(blockrect);
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
            fz_rect *wbbox = JM_empty_rect();         // word bbox
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
                            word_n = JM_append_word(gctx, lines, buff, wbbox,
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
                        JM_join_rect(wbbox, &ch->bbox, ch->size);
                    }
                    if (buff)                         // store any remaining word
                    {
                        word_n = JM_append_word(gctx, lines, buff, wbbox,
                                                block_n, line_n, word_n);
                        fz_drop_buffer(gctx, buff);
                        buff = NULL;
                        buflen = 0;
                    }
                    line_n++;
                }
                block_n++;
            }
            free(wbbox);
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
            
            def convertb64(s):
                if str is bytes:
                    return base64.b64encode(s)
                return base64.b64encode(s).decode()
            
            val = json.dumps(val, separators=(",", ":"), default=convertb64)
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
                        text = JM_stext_page_as_dict(gctx, $self);
                        break;
                    case(3):
                        fz_print_stext_page_as_xml(gctx, out, $self);
                        break;
                    case(4):
                        fz_print_stext_page_as_xhtml(gctx, out, $self);
                        break;
                    case(5):
                        text = JM_stext_page_as_dict(gctx, $self);
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
        %feature("autodoc","Return a globally unique integer.") gen_id;
        int gen_id()
        {
            return fz_gen_id(gctx);
        }
        
        %feature("autodoc","Free 'percent' of current store size.") store_shrink;
        size_t store_shrink(unsigned int percent)
        {
            if (percent >= 100)
            {
                fz_empty_store(gctx);
                return 0;
            }
            if (percent > 0) fz_shrink_store(gctx, 100 - percent);
            return gctx->store->size;            
        }

        %feature("autodoc","Current store size.") store_size;
        %pythoncode%{@property%}
        size_t store_size()
        {
            return gctx->store->size;
        }

        %feature("autodoc","Maximum store size.") store_maxsize;
        %pythoncode%{@property%}
        size_t store_maxsize()
        {
            return gctx->store->max;
        }

        void _store_debug()
        {
            fz_debug_store(gctx);
        }

        %feature("autodoc","Empty the glyph cache.") glyph_cache_empty;
        void glyph_cache_empty()
        {
            fz_purge_glyph_cache(gctx);
        }

    }
};
