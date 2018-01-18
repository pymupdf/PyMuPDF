%module fitz
//=============================================================================
// SWIG macro: generate fitz exceptions
//=============================================================================
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
//=============================================================================

//=============================================================================
// SWIG macro: check that a document is not closed
//=============================================================================
%define CLOSECHECK(meth)
%pythonprepend meth
%{if self.isClosed:
    raise ValueError("operation illegal for closed doc")%}
%enddef
//=============================================================================

//=============================================================================
// SWIG macro: check if object has valid parent
//=============================================================================
%define PARENTCHECK(meth)
%pythonprepend meth %{CheckParent(self)%}
%enddef
//=============================================================================

//=============================================================================
// SWIG macro: throw exceptions.
//=============================================================================
%define THROWMSG(msg)
fz_throw(gctx, FZ_ERROR_GENERIC, msg)
%enddef
//=============================================================================

// SWIG macro: ensure that document type is PDF
%define assert_PDF(cond)
if (!cond) THROWMSG("not a PDF")
%enddef
//=============================================================================
%feature("autodoc", "0");
// #define MEMDEBUG

%{
#define SWIG_FILE_WITH_INIT
#define SWIG_PYTHON_2_UNICODE
#include <fitz.h>
#include <pdf.h>
#include <zlib.h>
#include <time.h>
%}

/* global context */
%init %{
    gctx = fz_new_context(NULL, NULL, FZ_STORE_DEFAULT);
    if(!gctx) {
        fprintf(stderr, "[ERROR]gctx is NULL\n");
        exit(1);
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

/*****************************************************************************/
// include version information and several other helpers
/*****************************************************************************/
%pythoncode %{
import weakref
from binascii import hexlify
import sys
%}
%include version.i
%include helper-annot.i
%include helper-stext.i
%include helper-python.i
%include helper-other.i
%include helper-portfolio.i
%include helper-select.i
%include helper-xobject.i

/*****************************************************************************/
// fz_document
/*****************************************************************************/
%rename(Document) fz_document_s;
struct fz_document_s
{
    %extend
    {
        ~fz_document_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free document ...");
#endif
            fz_drop_document(gctx, $self);
#ifdef MEMDEBUG
            fprintf(stderr, " done!\n");
#endif
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
            if stream and not filename:
                raise ValueError("filetype missing with stream specified")
            if filename and stream and type(stream) not in (bytes, bytearray):
                raise ValueError("stream must be bytes or bytearray")
            self.isClosed    = False
            self.isEncrypted = 0
            self.metadata    = None
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
                self.isClosed    = False
                if self.needsPass:
                    self.isEncrypted = 1
                else: # we won't init until doc is decrypted
                    self.initData()
            else:
                self.thisown = False
        %}

        fz_document_s(const char *filename = NULL, PyObject *stream = NULL)
        {
            gctx->error->errcode = 0;
            gctx->error->message[0] = 0;
            struct fz_document_s *doc = NULL;
            fz_stream *data = NULL;
            char *streamdata = NULL;
            size_t streamlen = 0;
            if (PyBytes_Check(stream))
            {
                streamdata = PyBytes_AsString(stream);
                streamlen = (size_t) PyBytes_Size(stream);
            }
            else if (PyByteArray_Check(stream))
            {
                streamdata = PyByteArray_AsString(stream);
                streamlen = (size_t) PyByteArray_Size(stream);
            }

            fz_try(gctx)
            {
                if (streamlen > 0)
                {
                    data = fz_open_memory(gctx, streamdata, streamlen);
                    doc = fz_open_document_with_stream(gctx, filename, data);
                }
                else
                {
                    if (filename)
                        doc = fz_open_document(gctx, filename);
                    else
                        doc = (fz_document *) pdf_create_document(gctx);
                }
            }
            fz_catch(gctx) return NULL;
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
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free doc ...");
#endif
            while($self->refs > 1) {
                fz_drop_document(gctx, $self);
            }
            fz_drop_document(gctx, $self);
#ifdef MEMDEBUG
            fprintf(stderr, " done!\n");
#endif
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

        CLOSECHECK(_loadOutline)
        struct fz_outline_s *_loadOutline()
        {
            fz_outline *ol;
            fz_try(gctx) ol = fz_load_outline(gctx, $self);
            fz_catch(gctx) return NULL;
            return ol;
        }

        void _dropOutline(struct fz_outline_s *ol) {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free outline ...");
#endif
            fz_drop_outline(gctx, ol);
#ifdef MEMDEBUG
            fprintf(stderr, " done!\n");
#endif
        }

        CLOSECHECK(embeddedFileCount)
        %feature("autodoc","Return number of embedded files.") embeddedFileCount;
        %pythoncode%{@property%}
        int embeddedFileCount()
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            if (!pdf) return -1;
            return pdf_count_portfolio_entries(gctx, pdf);
        }

        FITZEXCEPTION(embeddedFileDel, result < 0)
        CLOSECHECK(embeddedFileDel)
        %feature("autodoc","Delete embedded file by name.") embeddedFileDel;
        int embeddedFileDel(char *name)
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            pdf_obj *names, *limits, *efiles, *v, *stream;
            char *limit1, *limit2, *tname;
            int i, len;
            fz_try(gctx)
            {
                assert_PDF(pdf);
                // get the EmbeddedFiles entry
                efiles = pdf_dict_getl(gctx, pdf_trailer(gctx, pdf),
                                      PDF_NAME_Root, PDF_NAME_Names,
                                      PDF_NAME_EmbeddedFiles, NULL);
                if (!efiles) THROWMSG("no embedded files");
                names = pdf_dict_get(gctx, efiles, PDF_NAME_Names);
                limits = pdf_dict_get(gctx, efiles, PDF_NAME_Limits);
                limit1 = NULL;
                limit2 = NULL;
                if (limits)                     // have name limits?
                    {
                        limit1 = pdf_to_utf8(gctx, pdf_array_get(gctx, limits, 0));
                        limit2 = pdf_to_utf8(gctx, pdf_array_get(gctx, limits, 1));
                    }
                len = pdf_array_len(gctx, names);     // embedded files count*2
                for (i=0; i < len; i+=2)              // search for the name
                    {
                        tname = pdf_to_utf8(gctx, pdf_array_get(gctx, names, i));
                        if (strcmp(tname, name) == 0) break;   // name found
                    }
                if (strcmp(tname, name) != 0) THROWMSG("name not found");
            }
            fz_catch(gctx) return -1;

            v = pdf_array_get(gctx, names, i+1);      // file descriptor
            
            // stream object containing file contents
            stream = pdf_dict_getl(gctx, v, PDF_NAME_EF, PDF_NAME_F, NULL);
            
            pdf_array_delete(gctx, names, i+1);  // delete file descriptor
            pdf_array_delete(gctx, names, i);    // delete name entry
            
            // delete stream object
            pdf_delete_object(gctx, pdf, pdf_to_num(gctx, stream));
            
            // adjust /Limits entry
            if (!limits) return 0;              // no Limits entry existed
            
            // no todo: deleted entry was not contained in Limits
            if ((strcmp(tname, limit1) != 0) && (strcmp(tname, limit2) != 0))
                return 0;

            // must re-calculate /Limits
            len = pdf_array_len(gctx, names);     // embedded files count*2
            if (len == 0)              // deleted last entry, also empty limits
                {
                pdf_array_delete(gctx, limits, 1);
                pdf_array_delete(gctx, limits, 0);
                return 0;
                }
            limit1[0] = 0xff;                    // initialize low entry
            limit2[0] = 0x00;                    // initialize high entry
            for (i=0; i < len; i+=2)              // search for low / hi names
                {
                tname = pdf_to_utf8(gctx, pdf_array_get(gctx, names, i));
                if (strcmp(tname, limit1) < 0) limit1 = tname;
                if (strcmp(tname, limit2) > 0) limit2 = tname;
                }

            pdf_array_put_drop(gctx, limits, 0,
                               pdf_new_string(gctx, pdf, limit1, strlen(limit1)));
            pdf_array_put_drop(gctx, limits, 1,
                               pdf_new_string(gctx, pdf, limit2, strlen(limit2)));
            return 0;
        }

        FITZEXCEPTION(embeddedFileInfo, !result)
        CLOSECHECK(embeddedFileInfo)
        %feature("autodoc","Retrieve embedded file information given its entry number or name.") embeddedFileInfo;
        PyObject *embeddedFileInfo(PyObject *id)
        {
            PyObject *infodict = PyDict_New();
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            Py_ssize_t name_len = 0;
            int n = -1;
            int count;
            char *name = NULL;
            char *sname = NULL;
            fz_try(gctx)
            {
                assert_PDF(pdf);
                count = pdf_count_portfolio_entries(gctx, pdf); // file count
                if (count < 1) THROWMSG("no embedded files");
                n = FindEmbedded(gctx, id, pdf);
            }
            fz_catch(gctx) return NULL;

            // name of file entry
            name = pdf_to_utf8(gctx, pdf_portfolio_entry_name(gctx, pdf, n));
            PyDict_SetItemString(infodict, "name", 
                   PyUnicode_DecodeUTF8(name, strlen(name), "strict"));
            pdf_obj *o = pdf_portfolio_entry_obj(gctx, pdf, n);
            name = pdf_to_utf8(gctx, pdf_dict_get(gctx, o, PDF_NAME_F));
            PyDict_SetItemString(infodict, "file", 
                   PyUnicode_DecodeUTF8(name, strlen(name), "strict"));
            name = pdf_to_utf8(gctx, pdf_dict_get(gctx, o, PDF_NAME_Desc));
            PyDict_SetItemString(infodict, "desc", 
                   PyUnicode_DecodeUTF8(name, strlen(name), "strict"));
            pdf_obj *olen = pdf_dict_getl(gctx, o, PDF_NAME_EF, PDF_NAME_F,
                                          PDF_NAME_Length, NULL);
            int len = -1;
            int DL = -1;
            if (olen) len = pdf_to_int(gctx, olen);
            pdf_obj *oDL = pdf_dict_getl(gctx, o, PDF_NAME_EF, PDF_NAME_F, PDF_NAME_DL, NULL);
            if (oDL) DL = pdf_to_int(gctx, oDL);
            PyDict_SetItemString(infodict, "size", PyInt_FromLong((long) DL));
            PyDict_SetItemString(infodict, "length", PyInt_FromLong((long) len));
            return infodict;
        }

        FITZEXCEPTION(embeddedFileSetInfo, result < 0)
        CLOSECHECK(embeddedFileSetInfo)
        %feature("autodoc","Change filename or description of embedded file given its entry number or name.") embeddedFileSetInfo;
        int embeddedFileSetInfo(PyObject *id, PyObject *filename=NULL, PyObject *desc=NULL)
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                Py_ssize_t name_len, file_len, desc_len;
                int n;
                char *f, *d, *name;
                name = getPDFstr(gctx, id, &name_len, "id");
                f = getPDFstr(gctx, filename, &file_len, "filename");
                d = getPDFstr(gctx, desc, &desc_len, "desc");
                if ((!f) && (!d)) THROWMSG("nothing to change");
                int count = pdf_count_portfolio_entries(gctx, pdf);
                if (count < 1) THROWMSG("no embedded files");
                n = FindEmbedded(gctx, id, pdf);
                pdf_obj *entry = pdf_portfolio_entry_obj(gctx, pdf, n);
                
                if (f != NULL)
                    {
                        pdf_dict_put_drop(gctx, entry, PDF_NAME_F,
                             pdf_new_string(gctx, pdf, f, (int) file_len));
                        pdf_dict_put_drop(gctx, entry, PDF_NAME_UF,
                             pdf_new_string(gctx, pdf, f, (int) file_len));
                    }

                if (d != NULL)
                    {
                        pdf_dict_put_drop(gctx, entry, PDF_NAME_Desc,
                             pdf_new_string(gctx, pdf, d, (int) desc_len));
                    }
            }
            fz_catch(gctx) return -1;
            return 0;
        }

        FITZEXCEPTION(embeddedFileGet, !result)
        CLOSECHECK(embeddedFileGet)
        %feature("autodoc","Retrieve embedded file content given its entry number or name.") embeddedFileGet;
        PyObject *embeddedFileGet(PyObject *id)
        {
            PyObject *cont = PyBytes_FromString("");
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            fz_buffer *buf = NULL;
            char *name = NULL;
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int count = pdf_count_portfolio_entries(gctx, pdf);
                if (count < 1) THROWMSG("no embedded files");
                int i = FindEmbedded(gctx, id, pdf);
                unsigned char *data;
                buf = pdf_portfolio_entry(gctx, pdf, i);
                Py_ssize_t len = (Py_ssize_t) fz_buffer_storage(gctx, buf, &data);
                cont = PyBytes_FromStringAndSize(data, len);
            }
            fz_always(gctx) if (buf) fz_drop_buffer(gctx, buf);
            fz_catch(gctx) return NULL;
            return cont;
        }

        FITZEXCEPTION(embeddedFileAdd, result < 0)
        CLOSECHECK(embeddedFileAdd)
        %feature("autodoc","Add new file from buffer.") embeddedFileAdd;
        int embeddedFileAdd(PyObject *buffer, char *name, PyObject *filename=NULL, PyObject *desc=NULL)
        {
            pdf_document *pdf = pdf_document_from_fz_document(gctx, $self);
            fz_buffer *data, *buf = NULL;
            int entry = 0;
            size_t size = 0;
            Py_ssize_t name_len, file_len, desc_len;
            char *f, *d;
            fz_try(gctx)
            {
                name_len = strlen(name);
                if (name_len < 1) THROWMSG("name not found");
                f = getPDFstr(gctx, filename, &file_len, "filename");
                d = getPDFstr(gctx, desc, &desc_len, "desc");
            }
            fz_catch(gctx) return -1;
            if (f == NULL)                  // no filename given
                {
                   f = name;                // take the name
                   file_len = name_len;
                }
            if (d == NULL)                  // no description given
                {
                    d = name;               // take the name
                    desc_len = name_len;
                }
                
            if (PyByteArray_Check(buffer))
            {
                size = (size_t) PyByteArray_Size(buffer);
                data = fz_new_buffer_from_shared_data(gctx,
                                PyByteArray_AsString(buffer), size);
            }
            else if (PyBytes_Check(buffer))
            {
                size = (size_t) PyBytes_Size(buffer);
                data = fz_new_buffer_from_shared_data(gctx,
                                PyBytes_AsString(buffer), size);
            }
            fz_try(gctx)
            {
                assert_PDF(pdf);       // must be PDF
                if (size == 0) THROWMSG("arg 1 not bytes or bytearray");
                int count = pdf_count_portfolio_entries(gctx, pdf);
                int i;
                char *tname;
                Py_ssize_t len = 0;
                for (i = 0; i < count; i++)      // check if name already exists
                {
                    tname = pdf_to_utf8(gctx, pdf_portfolio_entry_name(gctx, pdf, i));
                    if (strcmp(tname, name)==0) THROWMSG("name already exists");
                }
                buf = fz_new_buffer(gctx, size);
                fz_append_buffer(gctx, buf, data);
                entry = pdf_add_portfolio_entry(gctx, pdf,
                            name, name_len, /* name */
                            d, desc_len, /* desc */
                            f, file_len, /* filename */
                            f, file_len, /* unifile */
                            buf);
                
            }
            fz_always(gctx)
            {
                if (buf) fz_drop_buffer(gctx, buf);
            }
            fz_catch(gctx) return -1;
            return entry;
        }

        CLOSECHECK(pageCount)
        %pythoncode%{@property%}
        int pageCount() 
        {
            return fz_count_pages(gctx, $self);
        }

        CLOSECHECK(_getMetadata)
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

        CLOSECHECK(needsPass)
        %pythoncode%{@property%}
        int needsPass() {
            return fz_needs_password(gctx, $self);
        }

        CLOSECHECK(isPDF)
        %pythoncode%{@property%}
        PyObject *isPDF()
        {
            if (pdf_specifics(gctx, $self)) return Py_True;
            else return Py_False;
        }

        int _getGCTXerrcode() {
            return fz_caught(gctx);
        }

        const char *_getGCTXerrmsg() {
            return fz_caught_message(gctx);
        }

        CLOSECHECK(authenticate)
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
        //********************************************************************
        // save(filename, ...)
        //********************************************************************
        FITZEXCEPTION(save, result!=0)
        %pythonprepend save %{
            if self.isClosed:
                raise ValueError("operation illegal for closed doc")
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

        int save(char *filename, int garbage=0, int clean=0, int deflate=0, int incremental=0, int ascii=0, int expand=0, int linear=0)
        {
            int errors = 0;
            pdf_write_options opts;
            opts.do_incremental = incremental;
            opts.do_ascii = ascii;
            opts.do_compress = deflate;
            opts.do_compress_images = deflate;
            opts.do_compress_fonts = deflate;
            opts.do_decompress = expand;
            opts.do_garbage = garbage;
            opts.do_linear = linear;
            opts.do_clean = clean;
            opts.do_pretty = 0;
            opts.continue_on_error = 1;
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
                pdf_save_document(gctx, pdf, filename, &opts);
                }
            fz_catch(gctx) return -1;
            return 0;
        }

        //---------------------------------------------------------------------
        // write document to memory
        //---------------------------------------------------------------------
        FITZEXCEPTION(write, !result)
        %feature("autodoc", "Write document to a bytes object.") write;
        %pythonprepend write %{
            if self.isClosed:
                raise ValueError("operation illegal for closed doc")%}

        PyObject *write(int garbage=0, int clean=0, int deflate=0,
                        int ascii=0, int expand=0, int linear=0)
        {
            unsigned char *c;
            PyObject *r;
            size_t len;
            struct fz_buffer_s *res = NULL;
            fz_output *out;
            int errors = 0;
            pdf_write_options opts;
            opts.do_incremental = 0;
            opts.do_ascii = ascii;
            opts.do_compress = deflate;
            opts.do_compress_images = deflate;
            opts.do_compress_fonts = deflate;
            opts.do_decompress = expand;
            opts.do_garbage = garbage;
            opts.do_linear = linear;
            opts.do_clean = clean;
            opts.do_pretty = 0;
            opts.continue_on_error = 1;
            opts.errors = &errors;
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                if (fz_count_pages(gctx, $self) < 1)
                    THROWMSG("document has zero pages");
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                pdf_write_document(gctx, pdf, out, &opts);
                len = fz_buffer_storage(gctx, res, &c);
                r = PyBytes_FromStringAndSize(c, len);
            }
            fz_always(gctx)
            {
                if (out) fz_drop_output(gctx, out);
                if (res) fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) return NULL;
            return r;
        }

        //*********************************************************************
        // Insert pages from a source PDF into this PDF.
        // For reconstructing the links (_do_links method), we must save the
        // insertion point (start_at) if it was specified as -1.
        //*********************************************************************
        FITZEXCEPTION(insertPDF, result<0)
        %pythonprepend insertPDF
%{if self.isClosed:
    raise ValueError("operation illegal for closed doc")
if id(self) == id(docsrc):
    raise ValueError("source must not equal target PDF")
sa = start_at
if sa < 0:
    sa = self.pageCount%}

        %pythonappend insertPDF
%{if val == 0:
    self._reset_page_refs()
    if links:
        self._do_links(docsrc, from_page = from_page, to_page = to_page,
                   start_at = sa)%}

        %feature("autodoc","Copy page range ['from', 'to'] of source PDF, starting as page number 'start_at'.") insertPDF;

        int insertPDF(struct fz_document_s *docsrc, int from_page=-1, int to_page=-1, int start_at=-1, int rotate=-1, int links = 1)
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
            fz_catch(gctx) return -1;
            return 0;
        }

        //*********************************************************************
        // Delete a page from a PDF given by its number
        //*********************************************************************
        FITZEXCEPTION(deletePage, result<0)
        CLOSECHECK(deletePage)
        %feature("autodoc","Delete page 'pno'.") deletePage;
        %pythonappend deletePage %{if val == 0: self._reset_page_refs()%}
        int deletePage(int pno)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int pageCount = fz_count_pages(gctx, $self);
                if ((pno < 0) || (pno >= pageCount))
                    THROWMSG("invalid page number(s)");
                pdf_delete_page(gctx, pdf, pno);
                pdf_finish_edit(gctx, pdf);
            }
            fz_catch(gctx) return -1;
            return 0;
        }

        //*********************************************************************
        // Delete a page range from a PDF
        //*********************************************************************
        FITZEXCEPTION(deletePageRange, result<0)
        CLOSECHECK(deletePageRange)
        %feature("autodoc","Delete pages 'from' to 'to'.") deletePageRange;
        %pythonappend deletePageRange %{if val == 0: self._reset_page_refs()%}
        int deletePageRange(int from_page = -1, int to_page = -1)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int pageCount = fz_count_pages(gctx, $self);
                int f = from_page;
                int t = to_page;
                if (f < 0) f = pageCount - 1;
                if (t < 0) t = pageCount - 1;
                if ((t >= pageCount) | (f > t))
                    THROWMSG("invalid page number(s)");
                int i = t + 1 - f;
                while (i > 0)
                {
                    pdf_delete_page(gctx, pdf, f);
                    i -= 1;
                }
                pdf_finish_edit(gctx, pdf);
            }
            fz_catch(gctx) return -1;
            return 0;
        }

        //*********************************************************************
        // Copy a page within a PDF
        //*********************************************************************
        FITZEXCEPTION(copyPage, result<0)
        CLOSECHECK(copyPage)
        %feature("autodoc","Copy a page in front of 'to'.") copyPage;
        %pythonappend copyPage %{if val == 0: self._reset_page_refs()%}
        int copyPage(int pno, int to = -1)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int pageCount = fz_count_pages(gctx, $self);
                if ((pno < 0) | (pno >= pageCount))
                    THROWMSG("invalid page number(s)");
                pdf_obj *page = pdf_lookup_page_obj(gctx, pdf, pno);
                pdf_insert_page(gctx, pdf, to, page);
                pdf_finish_edit(gctx, pdf);
            }
            fz_catch(gctx) return -1;
            return 0;
        }

        //---------------------------------------------------------------------
        // Create and insert a new page (PDF)
        //---------------------------------------------------------------------
        FITZEXCEPTION(insertPage, result<0)
        %feature("autodoc","Insert a new page in front of 'pno'. Use arguments 'width', 'height' to specify a non-default page size, and optionally text insertion arguments.") insertPage;
        %pythonprepend insertPage %{
        if self.isClosed:
            raise ValueError("operation illegal for closed doc")
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
                if (contents) fz_drop_buffer(gctx, contents);
                if (page_obj) pdf_drop_obj(gctx, page_obj);
            }
            fz_catch(gctx) return -1;
            return (int) 0;
        }

        //*********************************************************************
        // Move a page within a PDF
        //*********************************************************************
        FITZEXCEPTION(movePage, result<0)
        CLOSECHECK(movePage)
        %feature("autodoc","Move page in front of 'to'.") movePage;
        %pythonappend movePage %{if val == 0: self._reset_page_refs()%}
        int movePage(int pno, int to = -1)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int pageCount = fz_count_pages(gctx, $self);
                if ((pno < 0) | (pno >= pageCount))
                    THROWMSG("invalid page number(s)");
                int t = to;
                if (t < 0) t = pageCount;
                if ((t == pno) || (pno == t - 1))
                    THROWMSG("source and target too close");
                pdf_obj *page = pdf_lookup_page_obj(gctx, pdf, pno);
                pdf_insert_page(gctx, pdf, t, page);
                if (pno < t)
                    pdf_delete_page(gctx, pdf, pno);
                else
                    pdf_delete_page(gctx, pdf, pno+1);
                pdf_finish_edit(gctx, pdf);
            }
            fz_catch(gctx) return -1;
            return 0;
        }

        //---------------------------------------------------------------------
        // Create sub-document to keep only selected pages.
        // Parameter is a Python list of the wanted page numbers.
        //---------------------------------------------------------------------
        FITZEXCEPTION(select, result<0)
        %feature("autodoc","Build sub-pdf with page numbers in 'list'.") select;
        CLOSECHECK(select)
        %pythonappend select
%{if val == 0:
    self._reset_page_refs()
    self.initData()%}
        int select(PyObject *pyliste)
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
            fz_catch(gctx) return -1;
            return 0;
        }

        //********************************************************************
        // get document permissions
        //********************************************************************
        %feature("autodoc","Get permissions dictionary.") permissions;
        CLOSECHECK(permissions)
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
                if (buf) fz_drop_buffer(gctx, buf);
                if (font) fz_drop_font(gctx, font);
            }
            fz_catch(gctx)
            {
                return NULL;
            }
            return wlist;
        }

        FITZEXCEPTION(_getPageObjNumber, !result)
        CLOSECHECK(_getPageObjNumber)
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

        //*********************************************************************
        // Returns the images used on a page as a list of lists.
        // Each image entry contains
        // [xref, smask, width, height, bpc, colorspace, altcs, name]
        //*********************************************************************
        FITZEXCEPTION(getPageImageList, result==NULL)
        CLOSECHECK(getPageImageList)
        %feature("autodoc","List images used on a page.") getPageImageList;
        PyObject *getPageImageList(int pno)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            int pageCount = fz_count_pages(gctx, $self);
            int n = pno;
            while (n < 0) n += pageCount;
            fz_try(gctx)
            {
                if (n >= pageCount) THROWMSG("invalid page number(s)");
                assert_PDF(pdf);
            }
            fz_catch(gctx) return NULL;
            PyObject *imglist = PyList_New(0);   // we will return this
            pdf_obj *pageref = pdf_lookup_page_obj(gctx, pdf, n);
            pdf_obj *pageobj = pdf_resolve_indirect(gctx, pageref);
            pdf_obj *rsrc = pdf_dict_get(gctx, pageobj, PDF_NAME_Resources);
            // XObject dictionary of page
            pdf_obj *dict = pdf_dict_get(gctx, rsrc, PDF_NAME_XObject);
            n = pdf_dict_len(gctx, dict);        // number of entries
            int i;
            for (i = 0; i < n; i++)       // do this for each img of the page
            {
                pdf_obj *imagedict, *imagename, *type, *altcs, *cs, *smask;
                int xref, gen;
                imagedict = pdf_dict_get_val(gctx, dict, i);
                imagename = pdf_dict_get_key(gctx, dict, i);
                if (!pdf_is_dict(gctx, imagedict)) continue;

                type = pdf_dict_get(gctx, imagedict, PDF_NAME_Subtype);
                if (!pdf_name_eq(gctx, type, PDF_NAME_Image)) continue;

                xref = pdf_to_num(gctx, imagedict);
                gen  = pdf_to_gen(gctx, imagedict);
                smask = pdf_dict_get(gctx, imagedict, PDF_NAME_SMask);
                if (smask)
                    gen = pdf_to_num(gctx, smask);
                int width = pdf_to_int(gctx, pdf_dict_get(gctx, imagedict,
                                       PDF_NAME_Width));

                int height = pdf_to_int(gctx, pdf_dict_get(gctx, imagedict,
                                        PDF_NAME_Height));

                int bpc = pdf_to_int(gctx, pdf_dict_get(gctx, imagedict,
                                     PDF_NAME_BitsPerComponent));

                cs = pdf_dict_get(gctx, imagedict, PDF_NAME_ColorSpace);
                altcs = NULL;
                if (pdf_is_array(gctx, cs))
                {
                    pdf_obj *cses = cs;
                    cs = pdf_array_get(gctx, cses, 0);
                    if (pdf_name_eq(gctx, cs, PDF_NAME_DeviceN) || pdf_name_eq(gctx, cs, PDF_NAME_Separation))
                    {
                        altcs = pdf_array_get(gctx, cses, 2);
                        if (pdf_is_array(gctx, altcs))
                            altcs = pdf_array_get(gctx, altcs, 0);
                    }
                }

                PyList_Append(imglist, Py_BuildValue("(i,i,i,i,i,s,s,s)",
                                       xref, gen, width, height, bpc,
                                       pdf_to_name(gctx, cs),
                                       pdf_to_name(gctx, altcs),
                                       pdf_to_name(gctx, imagename)));
            }
            return imglist;
        }

        //*********************************************************************
        // Returns the fonts used on a page as a nested list of lists.
        // Each font entry contains [xref#, gen#, type, basename, name]
        //*********************************************************************
        FITZEXCEPTION(getPageFontList, result==NULL)
        CLOSECHECK(getPageFontList)
        %feature("autodoc","List fonts used on a page.") getPageFontList;
        PyObject *getPageFontList(int pno)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            int pageCount = fz_count_pages(gctx, $self);
            int n = pno;          // pno might be < 0
            while (n < 0) n += pageCount;
            fz_try(gctx)
            {
                if (n >= pageCount) THROWMSG("invalid page number(s)");
                assert_PDF(pdf);
            }
            fz_catch(gctx) return NULL;

            pdf_obj *fontdict, *subtype, *basefont, *name, *bname;
            pdf_obj *pageref, *pageobj, *rsrc, *dict;
            PyObject *fontlist = PyList_New(0);  // we will return this
            pageref = pdf_lookup_page_obj(gctx, pdf, n);
            pageobj = pdf_resolve_indirect(gctx, pageref);
            rsrc = pdf_dict_get(gctx, pageobj, PDF_NAME_Resources);
            dict = pdf_dict_get(gctx, rsrc, PDF_NAME_Font);
            n = pdf_dict_len(gctx, dict);
            int i;
            for (i = 0; i < n; i++)      /* do this for each font of the page */
            {
                basefont = name = bname = NULL;
                fontdict = pdf_dict_get_val(gctx, dict, i);
                if (!pdf_is_dict(gctx, fontdict))
                    continue;  // not a valid font
                int xref = pdf_to_num(gctx, fontdict);
                char *ext = fontextension(gctx, pdf, xref);
                subtype = pdf_dict_get(gctx, fontdict, PDF_NAME_Subtype);
                basefont = pdf_dict_get(gctx, fontdict, PDF_NAME_BaseFont);
                if (!basefont || pdf_is_null(gctx, basefont))
                    bname = pdf_dict_get(gctx, fontdict, PDF_NAME_Name);
                else
                    bname = basefont;
                name = pdf_dict_get_key(gctx, dict, i);
                PyList_Append(fontlist, Py_BuildValue("(i,s,s,s,s)", xref, ext,
                                                      pdf_to_name(gctx, subtype),
                                                      pdf_to_name(gctx, bname),
                                                      pdf_to_name(gctx, name)));
            }
            return fontlist;
        }

        FITZEXCEPTION(extractFont, !result)
        CLOSECHECK(extractFont)
        PyObject *extractFont(int xref = 0, int info_only = 0)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(pdf);
            }
            fz_catch(gctx) return NULL;
            fz_buffer *buffer = NULL;
            pdf_obj *obj, *basefont, *bname;
            PyObject *bytes = PyBytes_FromString("");
            const char *ext = "";
            const char *fontname = "";
            const char *stype = "";
            PyObject *nulltuple = Py_BuildValue("(s,s,s,O)", "", "", "", bytes);
            PyObject *tuple;
            unsigned char *data;
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
                        len = (Py_ssize_t) fz_buffer_storage(gctx, buffer, &data);
                        bytes = PyBytes_FromStringAndSize(data, len);
                        fz_drop_buffer(gctx, buffer);
                    }
                    tuple = Py_BuildValue("(s,s,s,O)", fontname, ext, stype, bytes);
                }
                else
                {
                    tuple = nulltuple;
                }
            }
            fz_catch(gctx)
            {
                tuple = Py_BuildValue("(s,s,s,O)", fontname, ext, stype, bytes);
            }
            return tuple;
        }

        //*********************************************************************
        // Delete all bookmarks (table of contents)
        // returns the list of deleted (freed = now available) xref numbers
        //*********************************************************************
        CLOSECHECK(_delToC)
        %pythonappend _delToC %{self.initData()%}
        PyObject *_delToC()
        {
            PyObject *xrefs = PyList_New(0);         // create Python list

            pdf_document *pdf = pdf_specifics(gctx, $self); // conv doc to pdf
            if (!pdf) return NULL;                          // not a pdf
            pdf_obj *root, *olroot, *first;
            /* get main root */
            root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Root);
            /* get outline root */
            olroot = pdf_dict_get(gctx, root, PDF_NAME_Outlines);
            if (!olroot) return xrefs;                      // no outlines
            int objcount, argc, i;
            int *res;
            objcount = 0;
            argc = 0;
            first = pdf_dict_get(gctx, olroot, PDF_NAME_First); // first outline
            if (!first) return xrefs;
            argc = countOutlines(gctx, first, argc);         // get number outlines
            if (argc < 1) return xrefs;
            res = malloc(argc * sizeof(int));          // object number table
            objcount = fillOLNumbers(gctx, res, first, objcount, argc); // fill table
            pdf_dict_del(gctx, olroot, PDF_NAME_First);
            pdf_dict_del(gctx, olroot, PDF_NAME_Last);
            pdf_dict_del(gctx, olroot, PDF_NAME_Count);

            for (i = 0; i < objcount; i++)
                pdf_delete_object(gctx, pdf, res[i]);      // del all OL items

            for (i = 0; i < argc; i++)
                PyList_Append(xrefs, PyInt_FromLong((long) res[i]));
            return xrefs;
        }

        //*********************************************************************
        // Get Xref Number of Outline Root, create it if missing
        //*********************************************************************
        FITZEXCEPTION(_getOLRootNumber, result<0)
        CLOSECHECK(_getOLRootNumber)
        int _getOLRootNumber()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx) assert_PDF(pdf);
            fz_catch(gctx) return -2;
            
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
            }
            return pdf_to_num(gctx, olroot);
        }

        //*********************************************************************
        // Get a New Xref Number
        //*********************************************************************
        FITZEXCEPTION(_getNewXref, result<0)
        CLOSECHECK(_getNewXref)
        int _getNewXref()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); /* conv doc to pdf*/
            fz_try(gctx) assert_PDF(pdf);
            fz_catch(gctx) return -2;
            return pdf_create_object(gctx, pdf);
        }

        //*********************************************************************
        // Get Length of Xref
        //*********************************************************************
        CLOSECHECK(_getXrefLength)
        int _getXrefLength()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); // get pdf doc
            if (!pdf) return 0;
            return pdf_xref_len(gctx, pdf);
        }

        //---------------------------------------------------------------------
        // Get XML Metadata xref
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getXmlMetadataXref, result<0)
        CLOSECHECK(_getXmlMetadataXref)
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
        FITZEXCEPTION(_delXmlMetadata, result<0)
        CLOSECHECK(_delXmlMetadata)
        int _delXmlMetadata()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); // get pdf document
            fz_try(gctx)
            {
                assert_PDF(pdf);
                pdf_obj *root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Root);
                if (root) pdf_dict_dels(gctx, root, "Metadata");
                else THROWMSG("could not load root object");
            }
            fz_catch(gctx) return -1;
            return 0;
        }

        //*********************************************************************
        // Get Object String of xref
        //*********************************************************************
        FITZEXCEPTION(_getObjectString, !result)
        CLOSECHECK(_getObjectString)
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
                if ((xref < 1) | (xref >= xreflen))
                    THROWMSG("xref out of range");
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                obj = pdf_load_object(gctx, pdf, xref);
                pdf_print_obj(gctx, out, pdf_resolve_indirect(gctx, obj), 1);
            }
            fz_always(gctx)
            {
                if (obj) pdf_drop_obj(gctx, obj);
                if (out) fz_drop_output(gctx, out);
            }
            fz_catch(gctx)
            {
                if (res) fz_drop_buffer(gctx, res);
                return NULL;
            }
            return fz_string_from_buffer(gctx, res);
        }
        %pythoncode %{_getXrefString = _getObjectString%}
        
        /*********************************************************************/
        // Get decompressed stream of an object by xref
        // Throws exception if not a stream.
        /*********************************************************************/
        FITZEXCEPTION(_getXrefStream, !result)
        CLOSECHECK(_getXrefStream)
        PyObject *_getXrefStream(int xref)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            PyObject *r;
            size_t len;
            unsigned char *c;
            struct fz_buffer_s *res;
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if ((xref < 1) || (xref >= xreflen))
                    THROWMSG("xref out of range");
                res = pdf_load_stream_number(gctx, pdf, xref);
                len = fz_buffer_storage(gctx, res, &c);
                r = PyBytes_FromStringAndSize(c, len);
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) return NULL;
            return r;
        }

        /*********************************************************************/
        // Update an Xref Number with a new Object given as a string
        /*********************************************************************/
        FITZEXCEPTION(_updateObject, result!=0)
        CLOSECHECK(_updateObject)
        int _updateObject(int xref, char *text, struct fz_page_s *page = NULL)
        {
            pdf_obj *new_obj;
            pdf_document *pdf = pdf_specifics(gctx, $self);     // get pdf doc
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if ((xref < 1) | (xref >= xreflen))
                    THROWMSG("xref out of range");
                // create new object based on passed-in string
                new_obj = pdf_new_obj_from_str(gctx, pdf, text);
                pdf_update_object(gctx, pdf, xref, new_obj);
                pdf_drop_obj(gctx, new_obj);
                if (page) refresh_link_table(gctx, pdf_page_from_fz_page(gctx, page));
            }
            fz_catch(gctx) return -1;
            return 0;
        }

        //---------------------------------------------------------------------
        // Update a stream identified by its xref
        //---------------------------------------------------------------------
        FITZEXCEPTION(_updateStream, result!=0)
        CLOSECHECK(_updateStream)
        int _updateStream(int xref = 0, PyObject *stream = NULL)
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
                if ((xref < 1) || (xref >= xreflen))
                    THROWMSG("xref out of range");
                if (PyBytes_Check(stream))
                {
                    c = PyBytes_AsString(stream);
                    len = (size_t) PyBytes_Size(stream);
                }
                else
                {
                    if (PyByteArray_Check(stream))
                    {
                        c = PyByteArray_AsString(stream);
                        len = (size_t) PyByteArray_Size(stream);
                    }
                    else
                    {
                        THROWMSG("stream must be bytes or bytearray");
                    }
                }
                // get the object
                obj = pdf_new_indirect(gctx, pdf, xref, 0);
                if (!obj) THROWMSG("xref invalid");
                if (!pdf_is_stream(gctx, obj)) THROWMSG("xref not a stream object");
                
                pdf_dict_put(gctx, obj, PDF_NAME_Filter,
                                                   PDF_NAME_FlateDecode);
                res = deflatebuf(gctx, c, (size_t) len);
                pdf_update_stream(gctx, pdf, obj, res, 1);
                pdf_drop_obj(gctx, obj);
            }
            fz_catch(gctx) return -1;
            return 0;
        }

        //*********************************************************************
        // Add or update metadata based on provided raw string
        //*********************************************************************
        FITZEXCEPTION(_setMetadata, result>0)
        CLOSECHECK(_setMetadata)
        int _setMetadata(char *text)
        {
            pdf_obj *info, *new_info, *new_info_ind;
            int info_num = 0;               // will contain xref no of info object
            pdf_document *pdf = pdf_specifics(gctx, $self);     // get pdf doc
            fz_try(gctx) {
                assert_PDF(pdf);
                // create new /Info object based on passed-in string
                new_info = pdf_new_obj_from_str(gctx, pdf, text);
            }
            fz_catch(gctx) return 1;
            
            // replace existing /Info object
            info = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Info);
            if (info)
            {
                info_num = pdf_to_num(gctx, info);    // get xref no of old info
                pdf_update_object(gctx, pdf, info_num, new_info);  // insert new
                pdf_drop_obj(gctx, new_info);
                return 0;
            }
            // create new indirect object from /Info object
            new_info_ind = pdf_add_object(gctx, pdf, new_info);
            // put this in the trailer dictionary
            pdf_dict_put_drop(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Info, new_info_ind);
            return 0;
        }

        /*********************************************************************/
        // Initialize document: set outline and metadata properties
        /*********************************************************************/
        %pythoncode %{
            def initData(self):
                if self.isEncrypted:
                    raise ValueError("cannot initData - document still encrypted")
                self._outline = self._loadOutline()
                self.metadata = dict([(k,self._getMetadata(v)) for k,v in {'format':'format', 'title':'info:Title', 'author':'info:Author','subject':'info:Subject', 'keywords':'info:Keywords','creator':'info:Creator', 'producer':'info:Producer', 'creationDate':'info:CreationDate', 'modDate':'info:ModDate'}.items()])
                self.metadata['encryption'] = None if self._getMetadata('encryption')=='None' else self._getMetadata('encryption')

            outline = property(lambda self: self._outline)
            _getPageXref = _getPageObjNumber

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
                self._page_refs.clear()
            
            def __del__(self):
                self.isClosed = True
                if hasattr(self, "_reset_page_refs"):
                    self._reset_page_refs()
                if hasattr(self, "Graftmaps"):
                    for gmap in self.Graftmaps:
                        self.Graftmaps[gmap] = None
                if hasattr(self, "this") and self.thisown:
                    self.thisown = False
                    self.__swig_destroy__(self)
                self.Graftmaps = {}
                self._reset_page_refs = DUMMY
                self.__swig_destroy__ = DUMMY
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
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free page ...");
#endif
            fz_drop_page(gctx, $self);
#ifdef MEMDEBUG
            fprintf(stderr, " done!\n");
#endif
        }
        PARENTCHECK(bound)
        %pythonappend bound %{
            if val:
                val.thisown = True
        %}
        /***********************************************************/
        // bound()
        /***********************************************************/
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
        PARENTCHECK(getSVGimage)
        PyObject *getSVGimage(struct fz_matrix_s *matrix = NULL)
        {
            fz_rect mediabox;
            fz_bound_page(gctx, $self, &mediabox);
            fz_device *dev = NULL;
            fz_buffer *res = NULL;
            size_t res_len = 0;
            PyObject *text = NULL;
            fz_matrix *ctm = matrix;
            if (!matrix) ctm = (fz_matrix *) &fz_identity;
            fz_rect tbounds;
            fz_cookie *cookie = NULL;
            fz_output *out = NULL;
            fz_separations *seps = NULL;
            fz_var(out);
            tbounds = mediabox;
            fz_transform_rect(&tbounds, ctm);

            fz_try(gctx)
            {
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                unsigned char *data;
                dev = fz_new_svg_device(gctx, out, tbounds.x1-tbounds.x0, tbounds.y1-tbounds.y0, FZ_SVG_TEXT_AS_PATH, 1);
                fz_run_page(gctx, $self, dev, ctm, cookie);
                fz_close_device(gctx, dev);
                res_len = fz_buffer_storage(gctx, res, &data);
                text = PyUnicode_FromStringAndSize(data, (Py_ssize_t) res_len);
            }
            fz_always(gctx)
            {
                if (dev) fz_drop_device(gctx, dev);
                if (out) fz_drop_output(gctx, out);
                if (res) fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx)
            {
                if (res) fz_drop_buffer(gctx, res);
                return NULL;
            }
            return text;
        }

        //---------------------------------------------------------------------
        // getDisplayList()
        //---------------------------------------------------------------------
        FITZEXCEPTION(getDisplayList, !result)
        PARENTCHECK(getDisplayList)
        struct fz_display_list_s *getDisplayList()
        {
            fz_display_list *dl = NULL;
            fz_try(gctx)
            {
                dl = fz_new_display_list_from_page(gctx, $self);
            }
            fz_catch(gctx) return NULL;
            return dl;
        }

        //---------------------------------------------------------------------
        // Page.setCropBox
        //---------------------------------------------------------------------
        FITZEXCEPTION(setCropBox, result<0)
        PARENTCHECK(setCropBox)
        int setCropBox(struct fz_rect_s *rect)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_obj *o;
            fz_try(gctx)
            {
                assert_PDF(page);
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
            fz_catch(gctx) return -1;
            return 0;
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

        /***********************************************************/
        // firstAnnot
        /***********************************************************/
        PARENTCHECK(firstAnnot)
        %feature("autodoc","firstAnnot points to first annot on page") firstAnnot;
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
        FITZEXCEPTION(setRotation, result!=0)
        PARENTCHECK(setRotation)
        %feature("autodoc","Set page rotation to 'rot' degrees.") setRotation;
        int setRotation(int rot)
        {
            fz_try(gctx)
            {
                pdf_page *page = pdf_page_from_fz_page(gctx, $self);
                assert_PDF(page);
                if (rot % 90) THROWMSG("rotate not multiple of 90");
                pdf_obj *rot_o = pdf_new_int(gctx, page->doc, rot);
                pdf_dict_put_drop(gctx, page->obj, PDF_NAME_Rotate, rot_o);
            }
            fz_catch(gctx) return -1;
            return 0;
        }

        /*********************************************************************/
        // Page._addAnnot_FromString
        // Add new links provided as an array of string object definitions.
        /*********************************************************************/
        FITZEXCEPTION(_addAnnot_FromString, result!=0)
        PARENTCHECK(_addAnnot_FromString)
        int _addAnnot_FromString(PyObject *linklist)
        {
            pdf_obj *annots, *annots_arr, *annot, *ind_obj, *new_array;
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            PyObject *txtpy;
            char *text;
            int lcount = (int) PySequence_Size(linklist); // new object count
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
                int i;
                if (annots_arr)
                {   // copy existing annots to new array
                    for (i = 0; i < pdf_array_len(gctx, annots_arr); i++)
                            pdf_array_push(gctx, new_array, pdf_array_get(gctx, annots_arr, i));
                }
                for (i = 0; i < lcount; i++)
                    {   // extract object sources from Python list 
                        txtpy = PySequence_ITEM(linklist, (Py_ssize_t) i);
                        if (PyBytes_Check(txtpy))
                            text = PyBytes_AsString(txtpy);
                        else
                            text = PyBytes_AsString(PyUnicode_AsUTF8String(txtpy));
                        // create annot, insert its XREF into annot array
                        annot = pdf_new_obj_from_str(gctx, page->doc, text);
                        ind_obj = pdf_add_object(gctx, page->doc, annot);
                        pdf_array_push_drop(gctx, new_array, ind_obj);
                        pdf_drop_obj(gctx, annot);
                    }
                pdf_dict_put_drop(gctx, page->obj, PDF_NAME_Annots, new_array);
                refresh_link_table(gctx, page);
            }
            fz_catch(gctx) return -1;
            return 0;
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
        FITZEXCEPTION(_cleanContents, result!=0)
        PARENTCHECK(_cleanContents)
        int _cleanContents()
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_annot *annot;
            fz_try(gctx)
            {
                assert_PDF(page);
                pdf_clean_page_contents(gctx, page->doc, page, NULL, NULL, NULL, 0);
                for (annot = pdf_first_annot(gctx, page); annot != NULL; annot = pdf_next_annot(gctx, annot))
                {
                    pdf_clean_annot_contents(gctx, page->doc, annot, NULL, NULL, NULL, 0);
                }
            }
            fz_catch(gctx) return -1;
            return 0;
        }

        //---------------------------------------------------------------------
        // Show a PDF page
        //---------------------------------------------------------------------
        FITZEXCEPTION(showPDFpage, result<0)
        %feature("autodoc", "Display a PDF page in a rectangle.") showPDFpage;
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
                // make the XObject for source page
                xobj1 = JM_xobject_from_page(gctx, pdfout, pdfsrc, pno, &mediabox, &cropbox, xref, graftmap);
                // this is xref of spage as XObject
                xref = pdf_to_num(gctx, xobj1);

                //-------------------------------------------------------------
                // Calculate Matrix and BBox of the referencing XObject
                //-------------------------------------------------------------
                if (clip)
                {   // set cropbox if clip given
                    cropbox.x0 = clip->x0;
                    cropbox.y0 = mediabox.y1 - clip->y1;
                    cropbox.x1 = clip->x1;
                    cropbox.y1 = mediabox.y1 - clip->y0;
                }
                fz_matrix mat = {1,0,0,1,0,0};
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
                // create referencing XObject (actual display of page)
                //-------------------------------------------------------------
                xobj2 = pdf_new_xobject(gctx, pdfout, &cropbox, &mat);
                pdf_xobject *xobj2x = pdf_load_xobject(gctx, pdfout, xobj2);

                // fill the resources with the XObject reference to xobj1
                o = pdf_xobject_resources(gctx, xobj2x);
                pdf_obj *subres = pdf_new_dict(gctx, pdfout, 10);
                pdf_dict_put(gctx, o, PDF_NAME_XObject, subres);
                pdf_dict_puts(gctx, subres, "fullpage", xobj1);
                pdf_drop_obj(gctx, subres);

                // contents of xobj2 just invokes xobj1
                res = fz_new_buffer(gctx, 50);
                fz_append_string(gctx, res, "/fullpage Do");
                pdf_update_xobject_contents(gctx, pdfout, xobj2x, res);
                fz_drop_buffer(gctx, res);

                //-------------------------------------------------------------
                // update target page:
                //-------------------------------------------------------------
                // 1. resources object
                //-------------------------------------------------------------
                resources = pdf_dict_get(gctx, tpageref, PDF_NAME_Resources);
                subres = pdf_dict_get(gctx, resources, PDF_NAME_XObject);
                if (!subres)           // has no XObject yet: create one
                {
                    subres = pdf_new_dict(gctx, pdfout, 10);
                    pdf_dict_put(gctx, resources, PDF_NAME_XObject, subres);
                }

                // store *unique* reference name: xref & address of rect
                snprintf(data, 50, "fz-%d-%u", xref, rect);
                pdf_dict_puts(gctx, subres, data, xobj2);

                //-------------------------------------------------------------
                // 2. contents object
                //-------------------------------------------------------------
                nres = fz_new_buffer(gctx, 50);       // buffer for Do-command
                fz_append_string(gctx, nres, "/");    // Do-command
                fz_append_string(gctx, nres, data);
                fz_append_string(gctx, nres, " Do ");

                JM_extend_contents(gctx, pdfout, tpageref, nres, overlay);
            }
            fz_catch(gctx)
            {
                return -1;
            }
            return xref;
        }

        //---------------------------------------------------------------------
        // insert an image
        //---------------------------------------------------------------------
        FITZEXCEPTION(insertImage, result<0)
        PARENTCHECK(insertImage)
        %feature("autodoc", "Insert a new image in a rectangle.") insertImage;
        int insertImage(struct fz_rect_s *rect, const char *filename=NULL, struct fz_pixmap_s *pixmap = NULL, int overlay = 1)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_document *pdf;
            fz_pixmap *pm = NULL;
            fz_pixmap *pix = NULL;
            fz_image *mask = NULL;
            fz_separations *seps = NULL;
            pdf_obj *resources, *subres, *ref;
            fz_buffer *res = NULL, *nres = NULL;
            int i, j;
            unsigned char *s, *t;
            const char *template = "\nh q %g 0 0 %g %g %g cm /%s Do Q\n";
            Py_ssize_t c_len = 0;
            char name[50], md5hex[33];           // for image reference
            unsigned char md5[16];               // md5 of the image
            char *cont = NULL;
            const char *name_templ = "fz%s";   // template for image ref
            Py_ssize_t name_len = 0;
            fz_image *zimg, *image = NULL;
            fz_try(gctx)
            {
                assert_PDF(page);
                if ((pixmap) && (filename) || (!pixmap) && (!filename))
                    THROWMSG("need exactly one of filename or pixmap");
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

                // get objects "Resources" and "XObject"
                resources = pdf_dict_get(gctx, page->obj, PDF_NAME_Resources);
                subres = pdf_dict_get(gctx, resources, PDF_NAME_XObject);
                if (!subres)           // has no XObject yet, create one
                {
                    subres = pdf_new_dict(gctx, pdf, 10);
                    pdf_dict_put_drop(gctx, resources, PDF_NAME_XObject, subres);
                }

                // create the image
                // we always create a mask if the image contains an alpha
                if (filename)
                {
                    image = fz_new_image_from_file(gctx, filename);
                    pix = fz_get_pixmap_from_image(gctx, image, NULL, NULL, 0, 0);
                    if (pix->alpha == 1)
                    {
                        j = pix->n - 1;
                        pm = fz_new_pixmap(gctx, NULL, pix->w, pix->h, seps, 0);
                        s = pix->samples;
                        t = pm->samples;
                        for (i = 0; i < pix->w * pix->h; i++)
                            t[i] = s[j + i * pix->n];
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
                        j = pixmap->n - 1;       // j = # of pix bytes
                        // pm will consist of pixmap's alpha as 'samples'
                        pm = fz_new_pixmap(gctx, NULL, pixmap->w, pixmap->h, seps, 0);
                        s = pixmap->samples;
                        t = pm->samples;
                        for (i = 0; i < pixmap->w * pixmap->h; i++)
                            t[i] = s[j + i * pixmap->n];
                        mask = fz_new_image_from_pixmap(gctx, pm, NULL);
                        image = fz_new_image_from_pixmap(gctx, pixmap, mask);
                    }
                }
                // put image in the PDF and get its md5
                ref = JM_add_image(gctx, pdf, image, 0, md5);
                // we need a unique image name:
                // take md5 code of image
                hexlify(16, md5, md5hex);        // md5 as 32 hex bytes
                snprintf(name, 50, name_templ, md5hex);    // our img ref
                pdf_dict_puts(gctx, subres, name, ref);    // put in resources

                // retrieve and update contents stream
                nres = fz_new_buffer(gctx, 1024);
                fz_append_printf(gctx, nres, template, W, H, X, Y, name);
                JM_extend_contents(gctx, pdf, page->obj, nres, overlay);
            }
            fz_always(gctx)
            {
                if (image) fz_drop_image(gctx, image);
                if (mask) fz_drop_image(gctx, mask);
                if (pix) fz_drop_pixmap(gctx, pix);
                if (pm) fz_drop_pixmap(gctx, pm);
            }
            fz_catch(gctx) return -1;
            return 0;
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
                    font_obj = pdf_add_simple_font(gctx, pdf, font);
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
                        font_obj = pdf_add_simple_font(gctx, pdf, font);
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
            return self.rect + Rect(self.CropBoxPosition, self.CropBoxPosition)
        
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
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free rect ...");
#endif
            free($self);
#ifdef MEMDEBUG
            fprintf(stderr, " done!\n");
#endif
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
            fz_rect rect = {$self->x0, $self->y0,  $self->x1, $self->y1};
            if ($self->x1 < $self->x0)
            {
                rect.x0 = $self->x1;
                rect.x1 = $self->x0;
            }
            if ($self->y1 < $self->y0)
            {
                rect.y0 = $self->y1;
                rect.y1 = $self->y0;
            }
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
            if ($self->x1 <= $self->x0)
            {
                f = $self->x1;
                $self->x1 = $self->x0;
                $self->x0 = f;
            }
            if ($self->y1 <= $self->y0)
            {
                f = $self->y1;
                $self->y1 = $self->y0;
                $self->y0 = f;
            }
            return $self;
        }
        
        %feature("autodoc","contains") contains;
        PyObject *contains(struct fz_rect_s *rect)
        {
            if (fz_is_empty_rect(rect)) return truth_value(1);
            if (fz_is_empty_rect($self)) return truth_value(0);
            float l = $self->x0;
            float r = $self->x1;
            float t = $self->y0;
            float b = $self->y1;
            
            if ($self->x1 < $self->x0)
            {
                l = $self->x1;
                r = $self->x0;
            }
            if ($self->y1 < $self->y0)
            {
                t = $self->y1;
                b = $self->y0;
            }
            return truth_value(rect->x0 >= l && rect->x0 <= r &&
                               rect->x1 >= l && rect->x1 <= r &&
                               rect->y0 >= t && rect->y0 <= b &&
                               rect->y1 >= t && rect->y1 <= b);
        }

        PyObject *contains(struct fz_irect_s *rect)
        {
            if (fz_is_empty_irect(rect)) return truth_value(1);
            if (fz_is_empty_rect($self)) return truth_value(0);
            float l = $self->x0;
            float r = $self->x1;
            float t = $self->y0;
            float b = $self->y1;
            
            if ($self->x1 < $self->x0)
            {
                l = $self->x1;
                r = $self->x0;
            }
            if ($self->y1 < $self->y0)
            {
                t = $self->y1;
                b = $self->y0;
            }
            return truth_value(rect->x0 >= l && rect->x0 <= r &&
                               rect->x1 >= l && rect->x1 <= r &&
                               rect->y0 >= t && rect->y0 <= b &&
                               rect->y1 >= t && rect->y1 <= b);
        }

        PyObject *contains(struct fz_point_s *p)
        {
            if (fz_is_empty_rect($self)) return truth_value(0);
            float l = $self->x0;
            float t = $self->y0;
            float r = $self->x1;
            float b = $self->y1;
            if ($self->x1 <= $self->x0)
            {
                l = $self->x1;
                r = $self->x0;
            }
            if ($self->y1 <= $self->y0)
            {
                t = $self->y1;
                b = $self->y0;
            }
            if ((p->x < l) || (p->x > r) || (p->y < t) || (p->y > b))
                return truth_value(0);
            return truth_value(1);
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
                a = [self.x0, self.y0, self.x1, self.y1]
                return a[i]

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
        %pythoncode %{
        def __del__(self):
            if getattr(self, "thisown", True):
                try:
                    self.__swig_destroy__(self)
                except:
                    pass
                self.thisown = False
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
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free irect ... ");
#endif
            free($self);
#ifdef MEMDEBUG
            fprintf(stderr, "done!\n");
#endif
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

        %feature("autodoc","contains") contains;
        PyObject *contains(struct fz_irect_s *rect)
        {
            if (fz_is_empty_irect(rect)) return truth_value(1);
            if (fz_is_empty_irect($self)) return truth_value(0);
            int l = $self->x0;
            int r = $self->x1;
            int t = $self->y0;
            int b = $self->y1;
            
            if ($self->x1 < $self->x0)
            {
                l = $self->x1;
                r = $self->x0;
            }
            if ($self->y1 < $self->y0)
            {
                t = $self->y1;
                b = $self->y0;
            }
            return truth_value(rect->x0 >= l && rect->x0 <= r &&
                               rect->x1 >= l && rect->x1 <= r &&
                               rect->y0 >= t && rect->y0 <= b &&
                               rect->y1 >= t && rect->y1 <= b);
        }

        %feature("autodoc","Make rectangle finite") normalize;
        struct fz_irect_s *normalize()
        {
            int f;
            if ($self->x1 <= $self->x0)
            {
                f = $self->x1;
                $self->x1 = $self->x0;
                $self->x0 = f;
            }
            if ($self->y1 <= $self->y0)
            {
                f = $self->y1;
                $self->y1 = $self->y0;
                $self->y0 = f;
            }
            return $self;
        }
        
        PyObject *contains(struct fz_rect_s *rect)
        {
            if (fz_is_empty_rect(rect)) return truth_value(1);
            if (fz_is_empty_irect($self)) return truth_value(0);
            float l = $self->x0;
            float r = $self->x1;
            float t = $self->y0;
            float b = $self->y1;
            
            if ($self->x1 < $self->x0)
            {
                l = $self->x1;
                r = $self->x0;
            }
            if ($self->y1 < $self->y0)
            {
                t = $self->y1;
                b = $self->y0;
            }
            return truth_value(rect->x0 >= l && rect->x0 <= r &&
                               rect->x1 >= l && rect->x1 <= r &&
                               rect->y0 >= t && rect->y0 <= b &&
                               rect->y1 >= t && rect->y1 <= b);
        }

        PyObject *contains(struct fz_point_s *p)
        {
            if (fz_is_empty_irect($self)) return truth_value(0);
            float l = $self->x0;
            float t = $self->y0;
            float r = $self->x1;
            float b = $self->y1;
            if ($self->x1 <= $self->x0)
            {
                l = $self->x1;
                r = $self->x0;
            }
            if ($self->y1 <= $self->y0)
            {
                t = $self->y1;
                b = $self->y0;
            }
            if ((p->x < l) || (p->x > r) || (p->y < t) || (p->y > b))
                return truth_value(0);
            return truth_value(1);
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
                a = [self.x0, self.y0, self.x1, self.y1]
                return a[i]

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
                return "fitz.IRect" + str((self.x0, self.y0, self.x1, self.y1))

            width = property(lambda self: self.x1-self.x0)
            height = property(lambda self: self.y1-self.y0)
            tl = top_left
            tr = top_right
            br = bottom_right
            bl = bottom_left
        %}
        %pythoncode %{
        def __del__(self):
            if getattr(self, "thisown", True):
                try:
                    self.__swig_destroy__(self)
                except:
                    pass
                self.thisown = False
        %}
    }
};

/*************/
/* fz_pixmap */
/*************/
%rename(Pixmap) fz_pixmap_s;
struct fz_pixmap_s
{
    int x, y, w, h, n;
    int xres, yres;
    %extend {
        ~fz_pixmap_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free pixmap ... ");
#endif
            fz_drop_pixmap(gctx, $self);
#ifdef MEMDEBUG
            fprintf(stderr, "done!\n");
#endif
        }
        FITZEXCEPTION(fz_pixmap_s, !result)
        %pythonappend fz_pixmap_s %{
        if this:
            self.thisown = True
        else:
            self.thisown = False%}
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
        // create pixmap as converted copy of another one
        // New in v1.11: option to remove alpha
        //---------------------------------------------------------------------
        fz_pixmap_s(struct fz_colorspace_s *cs, struct fz_pixmap_s *spix, int alpha = 1)
        {
            fz_pixmap *pm = NULL;
            fz_try(gctx)
            {
                pm = fz_convert_pixmap(gctx, spix, cs, NULL, NULL, NULL, alpha);
            }
            fz_catch(gctx) return NULL;
            return pm;
        }

        //---------------------------------------------------------------------
        // create pixmap as scaled copy of another one
        //---------------------------------------------------------------------
        fz_pixmap_s(fz_pixmap *spix, float w, float h, struct fz_irect_s *clip = NULL)
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
        // create a pixmap with alpha channel added
        //---------------------------------------------------------------------
        fz_pixmap_s(struct fz_pixmap_s *spix)
        {
            fz_pixmap *pm = NULL;
            int n, w, h, balen, i, j, l;
            fz_separations *seps = NULL;
            fz_try(gctx)
            {
                if (spix->alpha == 1) THROWMSG("source pixmap already has alpha");
                n = fz_pixmap_colorants(gctx, spix);
                w = fz_pixmap_width(gctx, spix);
                h = fz_pixmap_height(gctx, spix);
                fz_colorspace *cs = fz_pixmap_colorspace(gctx, spix);
                pm = fz_new_pixmap(gctx, cs, w, h, seps, 1);
                // fill pixmap with spix and alpha values
                balen = w * h * (n+1);
                i = j = 0;
                while (i < balen)
                {
                    for (l=0; l < n; l++)
                    {
                        pm->samples[i+l] = spix->samples[j+l];
                    }
                    pm->samples[i+n] = 255;
                    i += n+1;
                    j += n;
                }
                pm->x = spix->x;
                pm->y = spix->y;
                pm->xres = spix->xres;
                pm->yres = spix->yres;
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
            size_t size = 0;
            int n = fz_colorspace_n(gctx, cs);
            int stride = (n + alpha)*w;
            fz_separations *seps = NULL;
            fz_pixmap *pm = NULL;
            if (PyByteArray_Check(samples)){
                data = PyByteArray_AsString(samples);
                size = (size_t) PyByteArray_Size(samples);
            }
            else if (PyBytes_Check(samples)){
                data = PyBytes_AsString(samples);
                size = (size_t) PyBytes_Size(samples);
            }
            fz_try(gctx)
            {
                if (size == 0) THROWMSG("invalid argument type");
                if (stride * h != size) THROWMSG("len(samples) invalid");
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
            fz_always(gctx) if (img) fz_drop_image(gctx, img);
            fz_catch(gctx) return NULL;
            return pm;
        }

        //---------------------------------------------------------------------
        // create pixmap from in-memory image
        //---------------------------------------------------------------------
        fz_pixmap_s(PyObject *imagedata)
        {
            size_t size = 0;
            fz_buffer *data = NULL;
            fz_image *img = NULL;
            fz_pixmap *pm = NULL;
            fz_try(gctx)
            {
                if (!imagedata) THROWMSG("invalid argument type");
                if (PyByteArray_Check(imagedata))
                {
                    size = (size_t) PyByteArray_Size(imagedata);
                    data = fz_new_buffer_from_shared_data(gctx,
                              PyByteArray_AsString(imagedata), size);
                }
                else if (PyBytes_Check(imagedata))
                {
                    size = (size_t) PyBytes_Size(imagedata);
                    data = fz_new_buffer_from_shared_data(gctx,
                              PyBytes_AsString(imagedata), size);
                }
                if (size == 0) THROWMSG("invalid argument type");
                img = fz_new_image_from_buffer(gctx, data);
                pm = fz_get_pixmap_from_image(gctx, img, NULL, NULL, NULL, NULL);
            }
            fz_always(gctx)
            {
                if (img) fz_drop_image(gctx, img);
                if (data) fz_drop_buffer(gctx, data);
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
                if ((xref < 1) | (xref >= xreflen))
                    THROWMSG("xref out of range");
                ref = pdf_new_indirect(gctx, pdf, xref, 0);
                type = pdf_dict_get(gctx, ref, PDF_NAME_Subtype);
                if (!pdf_name_eq(gctx, type, PDF_NAME_Image))
                    THROWMSG("xref not an image");
                if (!pdf_is_stream(gctx, ref))
                    THROWMSG("broken PDF: xref is not a stream");
                img = pdf_load_image(gctx, pdf, ref);
                pdf_drop_obj(gctx, ref);
                pix = fz_get_pixmap_from_image(gctx, img, NULL, NULL, NULL, NULL);
            }
            fz_always(gctx)
            {
                if (img) fz_drop_image(gctx, img);
            }
            fz_catch(gctx)
            {
                if (pix) fz_drop_pixmap(gctx, pix);
                if (ref) pdf_drop_obj(gctx, ref);
                return NULL;
            }
            return pix;
        }

        //---------------------------------------------------------------------
        // shrink
        //---------------------------------------------------------------------
        void shrink(int factor)
        {
            if (factor < 0) return;
            fz_try(gctx)
            {
                fz_subsample_pixmap(gctx, $self, factor);
            }
            fz_catch(gctx) return;
        }

        /***************************/
        /* apply gamma correction  */
        /***************************/
        void gammaWith(float gamma)
        {
            fz_gamma_pixmap(gctx, $self, gamma);
        }

        /***************************/
        /* tint pixmap with color  */
        /***************************/
        %pythonprepend tintWith%{
            if self.colorspace.n > 3:
                raise TypeError("CMYK colorspace cannot be tinted")%}
        void tintWith(int red, int green, int blue)
        {
            fz_tint_pixmap(gctx, $self, red, green, blue);
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
        void copyPixmap(struct fz_pixmap_s *src, const struct fz_irect_s *bbox)
        {
            fz_copy_pixmap_rect(gctx, $self, src, bbox, NULL);
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
        FITZEXCEPTION(setAlpha, result<0)
        int setAlpha(PyObject *alphavalues=NULL)
        {
            fz_try(gctx)
            {
                if ($self->alpha == 0) THROWMSG("pixmap has no alpha channel");
                int n = fz_pixmap_colorants(gctx, $self);
                int w = fz_pixmap_width(gctx, $self);
                int h = fz_pixmap_height(gctx, $self);
                int balen = w * h * (n+1);
                unsigned char *data = NULL;
                int data_len = 0;
                if (alphavalues)
                {
                    if (PyBytes_Check(alphavalues))
                    {
                        data_len = PyBytes_Size(alphavalues);
                        data     = PyBytes_AsString(alphavalues);
                    }
                    if (PyByteArray_Check(alphavalues))
                    {
                        data_len = PyByteArray_Size(alphavalues);
                        data     = PyByteArray_AsString(alphavalues);
                    }
                    if (data_len > 0 && data_len < w * h)
                        THROWMSG("too few alpha values");
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
            fz_catch(gctx) return -1;
            return 0;
        }

        //----------------------------------------------------------------------
        // getPNGData
        //----------------------------------------------------------------------
        FITZEXCEPTION(getPNGData, !result)
        PyObject *getPNGData(int savealpha=-1)
        {
            struct fz_buffer_s *res = NULL;
            fz_output *out = NULL;
            unsigned char *c;
            PyObject *r;
            size_t len;
            if (savealpha != -1) fz_warn(gctx, "ignoring savealpha");
            fz_try(gctx) {
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                fz_write_pixmap_as_png(gctx, out, $self);
                len = fz_buffer_storage(gctx, res, &c);
                r = PyByteArray_FromStringAndSize(c, len);
            }
            fz_always(gctx)
            {
                if (out) fz_drop_output(gctx, out);
                if (res) fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) return NULL;
            return r;
        }

        //----------------------------------------------------------------------
        // _writeIMG
        //----------------------------------------------------------------------
        FITZEXCEPTION(_writeIMG, result)
        %pythonprepend _writeIMG
        %{
            if type(filename) == str:
                pass
            elif type(filename) == unicode:
                filename = filename.encode('utf8')
            else:
                raise TypeError("filename must be a string")
        %}
        int _writeIMG(char *filename, int format, int savealpha=-1)
        {
            if (savealpha != -1) fz_warn(gctx, "ignoring savealpha");
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
            fz_catch(gctx) return 1;
            return 0;
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
                if self.colorspace:
                    return "fitz.Pixmap(%s, %s, %s)" % (self.colorspace.name, self.irect, self.alpha)
                else:
                    return "fitz.Pixmap(%s, %s, %s)" % ('None', self.irect, self.alpha)%}
        %pythoncode %{
        def __del__(self):
            if hasattr(self, "this") and self.thisown:
                self.thisown = False
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
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free colorspace ... ");
#endif
            fz_drop_colorspace(gctx, $self);
#ifdef MEMDEBUG
            fprintf(stderr, "done!\n");
#endif
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
        %pythoncode %{@property%}
        const char *name()
        {
            return fz_colorspace_name(gctx, $self);
        }

        %pythoncode %{
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
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free device\n");
#endif
            fz_close_device(gctx, $self->device);
            fz_drop_device(gctx, $self->device);
            if(list) {
#ifdef MEMDEBUG
                fprintf(stderr, "[DEBUG]free display list after freeing device\n");
#endif
                fz_drop_display_list(gctx, list);
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
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free matrix ... ");
#endif
            free($self);
#ifdef MEMDEBUG
            fprintf(stderr, "done!\n");
#endif
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
        // create a rotate matrix
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
                m = [self.a, self.b, self.c, self.d, self.e, self.f]
                return m[i]

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
        %pythoncode %{
        def __del__(self):
            if getattr(self, "thisown", True):
                try:
                    self.__swig_destroy__(self)
                except:
                    pass
                self.thisown = False
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
        ~fz_outline_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free outline ... ");
#endif
            fz_drop_outline(gctx, $self);
#ifdef MEMDEBUG
            fprintf(stderr, "done!\n");
#endif
        }
    }
*/
    %extend {
        %pythoncode %{@property%}
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
            return linkDest(self)
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
    %extend {
        FITZEXCEPTION(fz_point_s, !result)
        ~fz_point_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free point ... ");
#endif
            free($self);
#ifdef MEMDEBUG
            fprintf(stderr, "done!\n");
#endif
        }
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

            def __getitem__(self, i):
                a = [self.x, self.y]
                return a[i]

            def __len__(self):
                return 2

            def __repr__(self):
                return "fitz.Point" + str((self.x, self.y))
        %}
        %pythoncode %{
        def __del__(self):
            if getattr(self, "thisown", True):
                try:
                    self.__swig_destroy__(self)
                except:
                    pass
                self.thisown = False
        %}
    }
};

/*****************************************************************************/
// Annotation
/*****************************************************************************/
// annotation types
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
// annotation flags
#define ANNOT_XF_Invisible  1 << (1-1)
#define ANNOT_XF_Hidden  1 << (2-1)
#define ANNOT_XF_Print  1 << (3-1)
#define ANNOT_XF_NoZoom  1 << (4-1)
#define ANNOT_XF_NoRotate  1 << (5-1)
#define ANNOT_XF_NoView  1 << (6-1)
#define ANNOT_XF_ReadOnly  1 << (7-1)
#define ANNOT_XF_Locked  1 << (8-1)
#define ANNOT_XF_ToggleNoView  1 << (9-1)
#define ANNOT_XF_LockedContents  1 << (10-1)
// annotation line end styles
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

%rename(Annot) fz_annot_s;
%nodefaultctor;
struct fz_annot_s
{
    %extend
    {
        ~fz_annot_s()
        {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free annot ... ");
#endif
            fz_drop_annot(gctx, $self);
#ifdef MEMDEBUG
            fprintf(stderr, "done!\n");
#endif
        }
        /**********************************************************************/
        // annotation rectangle
        /**********************************************************************/
        PARENTCHECK(rect)
        %feature("autodoc","rect: rectangle containing the annot") rect;
        %pythoncode %{@property%}
        struct fz_rect_s *rect()
        {
            fz_rect *r = (fz_rect *)malloc(sizeof(fz_rect));
            return fz_bound_annot(gctx, $self, r);
        }

        /**********************************************************************/
        // annotation get xref number
        /**********************************************************************/
        PARENTCHECK(_getXref)
        %feature("autodoc","return xref number of annotation") _getXref;
        int _getXref()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if(!annot) return 0;
            return pdf_to_num(gctx, annot->obj);
        }

        /**********************************************************************/
        // annotation get decompressed appearance stream source
        /**********************************************************************/
        FITZEXCEPTION(_getAP, !result)
        PARENTCHECK(_getAP)
        %feature("autodoc","_getAP: provides operator source of the /AP") _getAP;
        PyObject *_getAP()
        {
            PyObject *r=NULL;
            size_t len;
            unsigned char *c;
            struct fz_buffer_s *res;
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(annot);
                if (!annot->ap) THROWMSG("annot has no /AP");
                res = pdf_load_stream(gctx, annot->ap->obj);
                len = fz_buffer_storage(gctx, res, &c);
                r = PyBytes_FromStringAndSize(c, (Py_ssize_t) len);
                fz_drop_buffer(gctx, res);
            }
            fz_catch(gctx) return NULL;
            return r;
        }

        /**********************************************************************/
        // annotation update appearance stream source
        /**********************************************************************/
        FITZEXCEPTION(_setAP, result!=0)
        PARENTCHECK(_setAP)
        %feature("autodoc","_setAP: updates operator source of the /AP") _setAP;
        int _setAP(PyObject *ap)
        {
            Py_ssize_t len = 0;
            char *c = NULL;
            if (PyByteArray_Check(ap))
            {
                c = PyByteArray_AsString(ap);
                len = PyByteArray_Size(ap);
            }
            else if (PyBytes_Check(ap))
            {
                c = PyBytes_AsString(ap);
                len = PyBytes_Size(ap);
            }
            struct fz_buffer_s *res;
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(annot);
                if (!annot->ap) THROWMSG("annot has no /AP");
                if (!c) THROWMSG("invalid argument type");
                pdf_dict_put(gctx, annot->ap->obj, PDF_NAME_Filter,
                                                   PDF_NAME_FlateDecode);
                res = deflatebuf(gctx, c, (size_t) len);
                pdf_update_stream(gctx, annot->page->doc, annot->ap->obj, res, 1);
            }
            fz_catch(gctx) return -1;
            return 0;
        }

        /**********************************************************************/
        // annotation set rectangle
        /**********************************************************************/
        PARENTCHECK(setRect)
        %feature("autodoc","setRect: changes the annot's rectangle") setRect;
        void setRect(struct fz_rect_s *r)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (annot) pdf_set_annot_rect(gctx, annot, r);
        }

        /**********************************************************************/
        // annotation vertices (for "Line", "Polgon", "Ink", etc.
        /**********************************************************************/
        PARENTCHECK(vertices)
        %feature("autodoc","vertices: point coordinates for various annot types") vertices;
        %pythoncode %{@property%}
        PyObject *vertices()
        {
            PyObject *res, *list;
            res = PyList_New(0);                      // create Python list
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return res;                   // not a PDF!
            //----------------------------------------------------------------
            // The following objects occur in different annotation types.
            // So we are sure that o != NULL occurs at most once.
            // Every pair of floats is one point, that needs to be separately
            // transformed with the page's transformation matrix.
            //----------------------------------------------------------------
            pdf_obj *o = pdf_dict_gets(gctx, annot->obj, "Vertices");
            if (!o) o = pdf_dict_get(gctx, annot->obj, PDF_NAME_L);
            if (!o) o = pdf_dict_get(gctx, annot->obj, PDF_NAME_QuadPoints);
            if (!o) o = pdf_dict_gets(gctx, annot->obj, "CL");
            int i, j, n;
            fz_point point;            // point object to work with
            fz_matrix page_ctm;        // page transformation matrix
            pdf_page_transform(gctx, annot->page, NULL, &page_ctm);
            
            if (o)                     // anything found yet?
                {
                n = pdf_array_len(gctx, o);
                for (i = 0; i < n; i += 2)
                    {
                        point.x = pdf_to_real(gctx, pdf_array_get(gctx, o, i));
                        point.y = pdf_to_real(gctx, pdf_array_get(gctx, o, i+1));
                        fz_transform_point(&point, &page_ctm);
                        PyList_Append(res, PyFloat_FromDouble((double) point.x));
                        PyList_Append(res, PyFloat_FromDouble((double) point.y));
                    }
                return res;
                }
            // nothing found so far - maybe an Ink annotation?
            pdf_obj *il_o = pdf_dict_get(gctx, annot->obj, PDF_NAME_InkList);
            if (!il_o) return res;                    // no inkList
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
                        PyList_Append(list, PyFloat_FromDouble((double) point.x));
                        PyList_Append(list, PyFloat_FromDouble((double) point.y));
                        }
                    PyList_Append(res, list);
                    Py_DECREF(list);
                }
            return res;
        }

        /**********************************************************************/
        // annotation colors
        /**********************************************************************/
        PARENTCHECK(colors)
        %feature("autodoc","dictionary of the annot's colors") colors;
        %pythoncode %{@property%}
        PyObject *colors()
        {
            PyObject *res = PyDict_New();
            PyObject *bc = PyList_New(0);        // fill colors
            PyObject *fc = PyList_New(0);        // stroke colors
            // default: '{"common": [], "fill": []}'
            PyDict_SetItemString(res, "common", bc);
            PyDict_SetItemString(res, "fill", fc);

            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot)
            {
                Py_DECREF(bc);
                Py_DECREF(fc);
                return res;                   // not a PDF
            }
             
            PyObject *col_o;
            int i;
            float col;
            pdf_obj *o = pdf_dict_get(gctx, annot->obj, PDF_NAME_C);
            if ((o != NULL) & (pdf_is_array(gctx, o)))
                {
                int n = pdf_array_len(gctx, o);
                for (i = 0; i < n; i++)
                    {
                    col = pdf_to_real(gctx, pdf_array_get(gctx, o, i));
                    col_o = PyFloat_FromDouble((double) col);
                    PyList_Append(bc, col_o);
                    }
                }
            PyDict_SetItemString(res, "common", bc);
            o = pdf_dict_gets(gctx, annot->obj, "IC");
            if ((o != NULL) & (pdf_is_array(gctx, o)))
                {
                int n = pdf_array_len(gctx, o);
                for (i = 0; i < n; i++)
                    {
                    col = pdf_to_real(gctx, pdf_array_get(gctx, o, i));
                    col_o = PyFloat_FromDouble((double) col);
                    PyList_Append(fc, col_o);
                    }
                }
            PyDict_SetItemString(res, "fill", fc);
            Py_DECREF(bc);
            Py_DECREF(fc);
            return res;
        }

        /**********************************************************************/
        // annotation set colors
        /**********************************************************************/
        PARENTCHECK(setColors)
        %feature("autodoc","setColors(dict)\nChanges the 'common' and 'fill' colors of an annotation. If provided, values must be lists of up to 4 floats.") setColors;
        void setColors(PyObject *colors)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return;
            if (!PyDict_Check(colors)) return;
            PyObject *ccol, *icol;
            ccol = PyDict_GetItemString(colors, "common");
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
                pdf_set_annot_color(gctx, annot, n, col);
            }
            n = 0;
            if (icol)
                if (PySequence_Check(icol))
                    n = (int) PySequence_Size(icol);
            if (n>0)
            {
                for (i=0; i<n; i++)
                    col[i] = (float) PyFloat_AsDouble(PySequence_GetItem(icol, i));
                pdf_set_annot_interior_color(gctx, annot, n, col);
            }
            return;
        }

        /**********************************************************************/
        // annotation lineEnds
        /**********************************************************************/
        PARENTCHECK(lineEnds)
        %pythoncode %{@property%}
        PyObject *lineEnds()
        {
            PyObject *res;
            res = PyDict_New();                       // create Python Dict
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return res;                   // no a PDF: empty dict
            pdf_obj *o = pdf_dict_gets(gctx, annot->obj, "LE");
            if (!o) return res;                       // no LE: empty dict
            char *lstart = "";
            char *lend = "";
            if (pdf_is_name(gctx, o)) lstart = (char *) pdf_to_name(gctx, o);
            else if (pdf_is_array(gctx, o))
                {
                lstart = (char *) pdf_to_name(gctx, pdf_array_get(gctx, o, 0));
                if (pdf_array_len(gctx, o) > 1)
                    lend   = (char *) pdf_to_name(gctx, pdf_array_get(gctx, o, 1));
                }
            PyObject *cpy;
            cpy = PyUnicode_DecodeUTF8(lstart, strlen(lstart), "strict");
            PyDict_SetItemString(res, "start", cpy);
            cpy = PyUnicode_DecodeUTF8(lend, strlen(lend), "strict");
            PyDict_SetItemString(res, "end", cpy);
            return res;
        }

        /**********************************************************************/
        // annotation set line ends
        /**********************************************************************/
        PARENTCHECK(setLineEnds)
        void setLineEnds(int start, int end)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (annot)
                {
                pdf_document *pdf = annot->page->doc;
                pdf_obj *o_s = pdf_new_name(gctx, pdf, annot_le_style_str(start));
                pdf_obj *o_e = pdf_new_name(gctx, pdf, annot_le_style_str(end));
                pdf_obj *o_arr = pdf_new_array(gctx, pdf, 2);
                pdf_array_push_drop(gctx, o_arr, o_s);
                pdf_array_push_drop(gctx, o_arr, o_e);
                pdf_dict_puts_drop(gctx, annot->obj, "LE", o_arr);
                pdf_update_appearance(gctx, pdf, annot);
                }
        }

        /**********************************************************************/
        // annotation type
        /**********************************************************************/
        PARENTCHECK(type)
        %pythoncode %{@property%}
        PyObject *type()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return Py_BuildValue("()");             // not a PDF
            int type = (int) pdf_annot_type(gctx, annot);
            char *c = annot_type_str(type);
            pdf_obj *o = pdf_dict_gets(gctx, annot->obj, "IT");
            if (!o || !pdf_is_name(gctx, o))
                return Py_BuildValue("(is)", type, c);         // no IT entry
            const char *it = pdf_to_name(gctx, o);
            return Py_BuildValue("(iss)", type, c, it);
        }

        /**********************************************************************/
        // annotation get attached file info
        /**********************************************************************/
        FITZEXCEPTION(fileInfo, !result)
        PARENTCHECK(fileInfo)
        %feature("autodoc","Retrieve attached file information.") fileInfo;
        PyObject *fileInfo()
        {
            PyObject *res = PyDict_New();             // create Python dict
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            char *filename = NULL;
            int length, size;
            pdf_obj *f_o, *l_o, *s_o, *stream;

            fz_try(gctx)
            {
                assert_PDF(annot);
                int type = (int) pdf_annot_type(gctx, annot);
                if (type != ANNOT_FILEATTACHMENT)
                    THROWMSG("not a file attachment annot");
                stream = pdf_dict_getl(gctx, annot->obj, PDF_NAME_FS,
                                   PDF_NAME_EF, PDF_NAME_F, NULL);
                if (!stream) THROWMSG("bad PDF: file has no stream");
            }
            fz_catch(gctx) return NULL;

            f_o = pdf_dict_get(gctx, stream, PDF_NAME_F);
            l_o = pdf_dict_get(gctx, stream, PDF_NAME_Length);
            s_o = pdf_dict_getl(gctx, stream, PDF_NAME_Params,
                                PDF_NAME_Size, NULL);

            if (l_o) length = pdf_to_int(gctx, l_o);
            else     length = -1;

            if (s_o) size = pdf_to_int(gctx, s_o);
            else     size = -1;

            if (f_o) filename = pdf_to_utf8(gctx, f_o);
            else     filename = "<undefined>";

            PyDict_SetItemString(res, "filename",
                   PyUnicode_DecodeUTF8(filename, strlen(filename), "strict"));
            PyDict_SetItemString(res, "length", PyInt_FromLong((long) length));
            PyDict_SetItemString(res, "size", PyInt_FromLong((long) size));
            return res;
        }

        /**********************************************************************/
        // annotation get attached file content
        /**********************************************************************/
        FITZEXCEPTION(fileGet, !result)
        PARENTCHECK(fileGet)
        %feature("autodoc","Retrieve annotation attached file content.") fileGet;
        PyObject *fileGet()
        {
            PyObject *res = NULL;
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            pdf_obj *stream = NULL;
            fz_buffer *buf = NULL;
            unsigned char *data = NULL;
            Py_ssize_t len;
            fz_try(gctx)
            {
                assert_PDF(annot);
                int type = (int) pdf_annot_type(gctx, annot);
                if (type != ANNOT_FILEATTACHMENT)
                    THROWMSG("not a file attachment annot");
                stream = pdf_dict_getl(gctx, annot->obj, PDF_NAME_FS,
                                   PDF_NAME_EF, PDF_NAME_F, NULL);
                if (!stream) THROWMSG("bad PDF: file has no stream");
                buf = pdf_load_stream(gctx, stream);
                len = (Py_ssize_t) fz_buffer_storage(gctx, buf, &data);
                res = PyBytes_FromStringAndSize(data, len);
            }
            fz_always(gctx) if (buf) fz_drop_buffer(gctx, buf);
            fz_catch(gctx) return NULL;
            return res;
        }

        //---------------------------------------------------------------------
        // annotation update attached file content
        //---------------------------------------------------------------------
        FITZEXCEPTION(fileUpd, result < 0)
        PARENTCHECK(fileUpd)
        %feature("autodoc","Update annotation attached file content.") fileUpd;
        int fileUpd(PyObject *buffer, PyObject *filename=NULL)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            pdf_document *pdf = NULL;       // to be filled in
            char *data = NULL;              // for new file content
            fz_buffer *res = NULL;          // for compressed content
            pdf_obj *stream = NULL;
            size_t size = 0;
            Py_ssize_t file_len;
            char *f;                        // filename
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
                if (!stream) THROWMSG("bad PDF: file has no stream");
                f = getPDFstr(gctx, filename, &file_len, "filename");
                // new file content must by bytes / bytearray
                if (PyByteArray_Check(buffer))
                {
                    size = (size_t) PyByteArray_Size(buffer);
                    data = PyByteArray_AsString(buffer);
                }
                else if (PyBytes_Check(buffer))
                {
                    size = (size_t) PyBytes_Size(buffer);
                    data = PyBytes_AsString(buffer);
                }
                if (size == 0) THROWMSG("arg 1 not bytes or bytearray");
                if (f != NULL)              // new filename given
                {
                    pdf_dict_put_drop(gctx, stream, PDF_NAME_F,
                         pdf_new_string(gctx, pdf, f, (int) file_len));
                    pdf_dict_put_drop(gctx, stream, PDF_NAME_UF,
                         pdf_new_string(gctx, pdf, f, (int) file_len));
                }
                // show that we provide a deflated stream
                pdf_dict_put(gctx, stream, PDF_NAME_Filter,
                                           PDF_NAME_FlateDecode);
                pdf_obj *p_o = pdf_dict_get(gctx, stream, PDF_NAME_Params);
                pdf_dict_put_drop(gctx, p_o, PDF_NAME_Size,
                                  pdf_new_int(gctx, pdf, (int) size));
                res = deflatebuf(gctx, data, size);
                pdf_update_stream(gctx, pdf, stream, res, 1);
            }
            fz_always(gctx) ;
            fz_catch(gctx) return -1;
            return 0;
        }

        /**********************************************************************/
        // annotation info
        /**********************************************************************/
        PARENTCHECK(info)
        %pythoncode %{@property%}
        PyObject *info()
        {
            PyObject *res = PyDict_New();
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return res;                   // not a PDF
            pdf_obj *o;
            PyObject *cpy;
            char *c;
            c = "";                                   // Contents
            o = pdf_dict_gets(gctx, annot->obj, "Contents");
            if (o) c = pdf_to_utf8(gctx, o);
            cpy = PyUnicode_DecodeUTF8(c, strlen(c), "strict");
            PyDict_SetItemString(res, "content", cpy);

            c = "";                                   // Name
            o = pdf_dict_get(gctx, annot->obj, PDF_NAME_Name);
            if (o) c = (char *) pdf_to_name(gctx, o);
            cpy = PyUnicode_DecodeUTF8(c, strlen(c), "strict");
            PyDict_SetItemString(res, "name", cpy);

            c = "";                                   // Title
            o = pdf_dict_get(gctx, annot->obj, PDF_NAME_T);
            if (o) c = pdf_to_utf8(gctx, o);
            cpy = PyUnicode_DecodeUTF8(c, strlen(c), "strict");
            PyDict_SetItemString(res, "title", cpy);

            c = "";                                   // CreationDate
            o = pdf_dict_gets(gctx, annot->obj, "CreationDate");
            if (o) c = pdf_to_utf8(gctx, o);
            cpy = PyUnicode_DecodeUTF8(c, strlen(c), "strict");
            PyDict_SetItemString(res, "creationDate", cpy);

            c = "";                                   // ModDate
            o = pdf_dict_get(gctx, annot->obj, PDF_NAME_M);
            if (o) c = pdf_to_utf8(gctx, o);
            cpy = PyUnicode_DecodeUTF8(c, strlen(c), "strict");
            PyDict_SetItemString(res, "modDate", cpy);

            c = "";                                   // Subj
            o = pdf_dict_gets(gctx, annot->obj, "Subj");
            if (o) c = pdf_to_utf8(gctx, o);
            cpy = PyUnicode_DecodeUTF8(c, strlen(c), "strict");
            PyDict_SetItemString(res, "subject", cpy);

            return res;
        }

        /**********************************************************************/
        // annotation set information
        /**********************************************************************/
        FITZEXCEPTION(setInfo, result<0)
        PARENTCHECK(setInfo)
        int setInfo(PyObject *info)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            pdf_document *pdf;
            if (annot) pdf = annot->page->doc;
            PyObject *value;
            unsigned char *uc;
            Py_ssize_t i;
            // ensure we have valid dictionary keys ...
            int dictvalid = checkDictKeys(info, "content", "title", "modDate", "creationDate", "subject", "name", 0);
            fz_try(gctx)
            {
                assert_PDF(annot);
                if (!PyDict_Check(info))
                    THROWMSG("info not a dict");
                if (!dictvalid)
                    THROWMSG("invalid key in info dict");

                // contents
                value = PyDict_GetItemString(info, "content");
                if (value)
                    {
                    uc = getPDFstr(gctx, value, &i, "content");
                    if (!uc) return -1;
                    pdf_dict_put_drop(gctx, annot->obj, PDF_NAME_Contents,
                                      pdf_new_string(gctx, pdf, uc, i));
                    }

                // title (= author)
                value = PyDict_GetItemString(info, "title");
                if (value)
                    {
                    uc = getPDFstr(gctx, value, &i, "title");
                    if (!uc) return -1;
                    pdf_dict_put_drop(gctx, annot->obj, PDF_NAME_T,
                                      pdf_new_string(gctx, pdf, uc, i));
                    }

                // creation date
                value = PyDict_GetItemString(info, "creationDate");
                if (value)
                    {
                    uc = getPDFstr(gctx, value, &i, "creationDate");
                    if (!uc) return -1;
                    pdf_dict_puts_drop(gctx, annot->obj, "CreationDate",
                                       pdf_new_string(gctx, pdf, uc, i));
                    }

                // mod date
                value = PyDict_GetItemString(info, "modDate");
                if (value)
                    {
                    uc = getPDFstr(gctx, value, &i, "modDate");
                    if (!uc) return -1;
                    pdf_dict_put_drop(gctx, annot->obj, PDF_NAME_M,
                                      pdf_new_string(gctx, pdf, uc, i));
                    }

                // subject
                value = PyDict_GetItemString(info, "subject");
                if (value)
                    {
                    uc = getPDFstr(gctx, value, &i, "subject");
                    if (!uc) return -1;
                    pdf_dict_puts_drop(gctx, annot->obj, "Subj",
                                       pdf_new_string(gctx, pdf, uc, i));
                    }
            }
            fz_catch(gctx) return -1;
            pdf_update_appearance(gctx, pdf, annot);
            return 0;
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
            PyObject *res = PyDict_New();
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return res;                   // not a PDF -> empty dict
            PyObject *emptylst_py = PyList_New(0);
            PyObject *blank_py = PyString_FromString("");
            PyObject *dash_py   = PyList_New(0);
            PyObject *effect_py = PyList_New(0);
            int i;
            char *effect2, *style;
            effect2 = style = "";
            double width = -1.0;
            int effect1 = -1;
            long dashes[10];
            int dashlen = 10;
            for (i = 0; i < dashlen; i++) dashes[i] = 0;
            int dash_ind, style_ind;
            dash_ind = style_ind = 0;

            pdf_obj *o = pdf_dict_get(gctx, annot->obj, PDF_NAME_Border);
            if (pdf_is_array(gctx, o))
                {
                width = (double) pdf_to_real(gctx, pdf_array_get(gctx, o, 2));
                if (pdf_array_len(gctx, o) == 4)
                    {
                    dash_ind = 1;
                    pdf_obj *dash = pdf_array_get(gctx, o, 3);
                    for (i = 0; i < pdf_array_len(gctx, dash); i++)
                        if (i < dashlen)
                            dashes[i] = (long) pdf_to_int(gctx,
                                             pdf_array_get(gctx, dash, i));
                    }
                }

            pdf_obj *bs_o = pdf_dict_get(gctx, annot->obj, PDF_NAME_BS);
            if (bs_o)
                {
                o = pdf_dict_get(gctx, bs_o, PDF_NAME_W);
                if (o) width = (double) pdf_to_real(gctx, o);
                o = pdf_dict_get(gctx, bs_o, PDF_NAME_S);
                if (o)
                    {
                    style_ind = 1;
                    style = (char *) pdf_to_name(gctx, o);
                    }
                o = pdf_dict_get(gctx, bs_o, PDF_NAME_D);
                if (o)
                    {
                    dash_ind = 1;
                    for (i = 0; i < pdf_array_len(gctx, o); i++)
                        if (i < dashlen)
                            dashes[i] = (long) pdf_to_int(gctx,
                                             pdf_array_get(gctx, o, i));
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

            for (i = 0; i < dashlen; i++)
                if (dashes[i] > 0)
                    PyList_Append(dash_py, PyInt_FromLong(dashes[i]));

            PyList_Append(effect_py, PyInt_FromLong((long) effect1));
            PyList_Append(effect_py, PyString_FromString(effect2));

            if (width >=0)
                PyDict_SetItemString(res, "width", PyFloat_FromDouble(width));

            if (dash_ind > 0)
                PyDict_SetItemString(res, "dashes", dash_py);

            if (style_ind > 0)
                PyDict_SetItemString(res, "style", PyString_FromString(style));

            if (effect1 > -1) PyDict_SetItemString(res, "effect", effect_py);

            return res;
        }

        //---------------------------------------------------------------------
        // set annotation border (destroys any /BE or /BS entries)
        // Argument 'border' must be number or dict.
        // Width and dashes may both be modified.
        //---------------------------------------------------------------------
        PARENTCHECK(setBorder)
        int setBorder(PyObject *border)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if(!annot) return -1;                     // not a PDF
            pdf_document *doc = annot->page->doc;     // PDF document
            float width = -1;                         // new width
            float cur_width = -1;                     // current width
            PyObject *pyo;
            PyObject *pydashes = NULL;                // new dashes
            PyObject *pycur_dashes = NULL;            // current dashes
            if (PyFloat_Check(border) || PyInt_Check(border))
                width = (float) PyFloat_AsDouble(border);
            else
            {
                if (!PyDict_Check(border)) return -2;     // not a dict
                if (PyDict_Size(border) == 0) return -3;  // ignore empty dict
                pyo = PyDict_GetItemString(border, "width");
                if (pyo) width = (float) PyFloat_AsDouble(pyo);
                pydashes = PyDict_GetItemString(border, "dashes");
            }
            // first get current width and dash entries of annot
            PyObject *cur_border = fz_annot_s_border($self);
            pyo = PyDict_GetItemString(cur_border, "width");
            if (pyo) cur_width = (float) PyFloat_AsDouble(pyo);
            pycur_dashes = PyDict_GetItemString(cur_border, "dashes");
            // then delete what might be in annot dictionary
            pdf_dict_del(gctx, annot->obj, PDF_NAME_BS);
            pdf_dict_del(gctx, annot->obj, PDF_NAME_BE);
            pdf_dict_del(gctx, annot->obj, PDF_NAME_Border);
            
            int i, d;
            // populate new border array
            if (width < 0) width = cur_width;    // no new width: take current
            if (width < 0) width = 0;            // default if no width given
            pdf_obj *bdr = pdf_new_array(gctx, doc, 3);
            pdf_array_push_drop(gctx, bdr, pdf_new_real(gctx, doc, 0));
            pdf_array_push_drop(gctx, bdr, pdf_new_real(gctx, doc, 0));
            pdf_array_push_drop(gctx, bdr, pdf_new_real(gctx, doc, width));
            
            if (!pydashes) pydashes = pycur_dashes;   // no new dashes: current
            if (!pydashes)
                {}
            else if (PyList_Check(pydashes))
                {
                // dashes specified: create another array
                pdf_obj *darr = pdf_new_array(gctx, doc, 1);
                for (i = 0; i < (int) PyList_Size(pydashes); i++)
                    {
                    d = (int) PyInt_AsLong(PyList_GetItem(pydashes, i));
                    pdf_array_push_drop(gctx, darr, pdf_new_int(gctx, doc, d));
                    }
                pdf_array_push_drop(gctx, bdr, darr);
                }
            pdf_dict_put_drop(gctx, annot->obj, PDF_NAME_Border, bdr);
            return 0;
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
        FITZEXCEPTION(_cleanContents, result!=0)
        PARENTCHECK(_cleanContents)
        int _cleanContents()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            fz_try(gctx)
            {
                assert_PDF(annot);
                pdf_clean_annot_contents(gctx, annot->page->doc, annot,
                                         NULL, NULL, NULL, 0);
            }
            fz_catch(gctx) return -1;
            return 0;
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
            struct fz_matrix_s *ctm = NULL;
            struct fz_colorspace_s *cs = NULL;
            fz_pixmap *pix = NULL;
            fz_separations *seps = NULL;

            if (matrix) ctm = matrix;
            else ctm = (fz_matrix *) &fz_identity;

            if (colorspace) cs = colorspace;
            else cs = fz_device_rgb(gctx);

            fz_try(gctx)
            {
                pix = fz_new_pixmap_from_annot(gctx, $self, ctm, cs, alpha);
            }
            fz_catch(gctx) return NULL;
            return pix;
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
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free link ...");
#endif
            fz_drop_link(gctx, $self);
#ifdef MEMDEBUG
            fprintf(stderr, " done!\n");
#endif
        }

        PARENTCHECK(uri)
        %pythoncode %{@property%}
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
            if self.parent.parent.isClosed:
                raise ValueError("operation illegal for closed doc")
            return linkDest(self)        
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
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free display list\n");
#endif
            fz_drop_display_list(gctx, $self);
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
            fz_try(gctx) {
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
            struct fz_stext_page_s *tp;
            fz_try(gctx)
            {
                fz_stext_options stext_options;
                stext_options.flags = flags;
                tp = fz_new_stext_page_from_display_list(gctx, $self, &stext_options);
            }
            fz_catch(gctx) return NULL;
            return tp;
        }
        %pythoncode %{
        def __del__(self):
            if getattr(self, "thisown", True):
                try:
                    self.__swig_destroy__(self)
                except:
                    pass
                self.thisown = False
        %}

    }
};

//-----------------------------------------------------------------------------
// fz_stext_page
//-----------------------------------------------------------------------------
%typemap(out) struct fz_rect_s * {
    PyObject *pyRect;
    struct fz_rect_s *rect;
    $result = PyList_New(0);
    rect = (struct fz_rect_s *)$1;
    while(!fz_is_empty_rect(rect)) {
        pyRect = SWIG_NewPointerObj(memcpy(malloc(sizeof(struct fz_rect_s)), rect, sizeof(struct fz_rect_s)), SWIGTYPE_p_fz_rect_s, SWIG_POINTER_OWN);
        PyList_Append($result, pyRect);
        Py_DECREF(pyRect);
        rect += 1;
    }
    free($1);
}

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

        ~fz_stext_page_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free text page\n");
#endif
            fz_drop_stext_page(gctx, $self);
        }
        //---------------------------------------------------------------------
        // method search()
        //---------------------------------------------------------------------
        struct fz_rect_s *search(const char *needle, int hit_max=16) {
            fz_rect *result;
            int count;
            if(hit_max < 0) {
                fprintf(stderr, "[DEBUG]invalid hit max number %d\n", hit_max);
                return NULL;
            }
            result = (fz_rect *)malloc(sizeof(fz_rect)*(hit_max+1));
            count = fz_search_stext_page(gctx, $self, needle, result, hit_max);
            result[count] = fz_empty_rect;
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]count is %d, last one is (%g %g), (%g %g)\n", count, result[count].x0, result[count].y0, result[count].x1, result[count].y1);
#endif
            return result;
        }

        //---------------------------------------------------------------------
        // Get text blocks with their bbox and concatenated lines 
        // as a Python list
        //---------------------------------------------------------------------
        FITZEXCEPTION(_extractTextLines_AsList, !result)
        PyObject *_extractTextLines_AsList()
        {
            fz_stext_block *block;
            fz_stext_line *line;
            fz_stext_char *ch;
            int last_char = 0;
            char utf[10];
            int i, n;
            long block_n = 0;
            PyObject *lines = PyList_New(0);
            PyObject *text = NULL;
            fz_buffer *res = NULL;
            fz_output *out = NULL;
            size_t res_len = 0;
            unsigned char *data;
            for (block = $self->first_block; block; block = block->next)
            {
                PyObject *litem = PyList_New(0);
                PyList_Append(litem, PyFloat_FromDouble((double) block->bbox.x0));
                PyList_Append(litem, PyFloat_FromDouble((double) block->bbox.y0));
                PyList_Append(litem, PyFloat_FromDouble((double) block->bbox.x1));
                PyList_Append(litem, PyFloat_FromDouble((double) block->bbox.y1));
                if (block->type == FZ_STEXT_BLOCK_TEXT)
                {
                    fz_try(gctx)
                    {
                        res = fz_new_buffer(gctx, 1024);
                        out = fz_new_output_with_buffer(gctx, res);
                    }
                    fz_catch(gctx)
                    {
                        if (res) fz_drop_buffer(gctx, res);
                        if (out) fz_drop_output(gctx, out);
                        return NULL;
                    }
                    int line_n = 0;
                    for (line = block->u.t.first_line; line; line = line->next)
                    {
                        // add new line after a chr(32)
                        if (line_n > 0)
                            fz_write_string(gctx, out, " ");
                        line_n += 1;
                        for (ch = line->first_char; ch; ch = ch->next)
                        {
                            last_char = ch->c;
                            n = fz_runetochar(utf, ch->c);
                            for (i = 0; i < n; i++)
                                fz_write_byte(gctx, out, utf[i]);
                        }
                    }
                    res_len = fz_buffer_storage(gctx, res, &data);
                    text = PyUnicode_FromStringAndSize(data, (Py_ssize_t) res_len);
                    PyList_Append(litem, text);
                    fz_drop_buffer(gctx, res);
                    fz_drop_output(gctx,out);
                }
                else
                {
                    fz_image *img = block->u.i.image;
                    fz_colorspace *cs = img->colorspace;
                    PyList_Append(litem, PyUnicode_FromFormat("<image: %s, width %d, height %d, bpc %d>",
                                         fz_colorspace_name(gctx, cs), img->w, img->h, img->bpc));
                }
                PyList_Append(litem, PyInt_FromLong(block_n));
                PyList_Append(litem, PyInt_FromLong((long) block->type));
                PyList_Append(lines, litem);
                Py_DECREF(litem);
                block_n += 1;
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
            char word[128];
            char utf[10];
            int i, n;
            long block_n, line_n, word_n;
            block_n = line_n = word_n = 0;
            Py_ssize_t char_n;
            PyObject *lines = PyList_New(0);
            PyObject *litem;
            float c_x0, c_y0, c_x1, c_y1;
            for (block = $self->first_block; block; block = block->next)
            {
                if (block->type == FZ_STEXT_BLOCK_TEXT)
                {
                    line_n = 0;
                    for (line = block->u.t.first_line; line; line = line->next)
                    {
                        word_n = 0;           // word counter per line
                        c_x0 = line->bbox.x0; // start of 1st word of line
                        c_x1 = c_x0;          // initialize word end
                        c_y0 = line->bbox.y0; // line baseline - never changes
                        c_y1 = c_y0;          // initialize word height
                        char_n = 0;           // reset char counter
                        for (ch = line->first_char; ch; ch = ch->next)
                        {
                            if ((ch->c == 32 && char_n > 0) || char_n >= 127)
                            // if space char or word too long, store what we have so far
                            {
                                litem = PyList_New(0);
                                PyList_Append(litem, PyFloat_FromDouble((double) c_x0));
                                PyList_Append(litem, PyFloat_FromDouble((double) c_y0));
                                PyList_Append(litem, PyFloat_FromDouble((double) c_x1));
                                PyList_Append(litem, PyFloat_FromDouble((double) c_y1));
                                PyList_Append(litem, PyUnicode_FromStringAndSize(word, char_n));
                                PyList_Append(litem, PyInt_FromLong(block_n));
                                PyList_Append(litem, PyInt_FromLong(line_n));
                                PyList_Append(litem, PyInt_FromLong(word_n));
                                PyList_Append(lines, litem);
                                Py_DECREF(litem);
                                word_n += 1;        // word counter
                                c_x0 = ch->bbox.x1; // start pos. of next word
                                c_y1 = c_y0;        // initialize word height
                                char_n = 0;         // reset char counter
                                continue;
                            }
                            // append one unicode character to the word
                            if (ch->bbox.y1 > c_y1)
                                c_y1 = ch->bbox.y1; // adjust word height
                            c_x1 = ch->bbox.x1;     // adjust end of word
                            n = fz_runetochar(utf, ch->c);
                            for (i = 0; i < n; i++)
                            {
                                word[char_n] = utf[i];
                                char_n += 1;
                                word[char_n] = 0;     // indicate end-of-string
                            }
                        }
                        if (char_n > 0) // store any remaining stuff in word
                        {
                            litem = PyList_New(0);
                            PyList_Append(litem, PyFloat_FromDouble((double) c_x0));
                            PyList_Append(litem, PyFloat_FromDouble((double) c_y0));
                            PyList_Append(litem, PyFloat_FromDouble((double) c_x1));
                            PyList_Append(litem, PyFloat_FromDouble((double) c_y1));
                            PyList_Append(litem, PyUnicode_FromStringAndSize(word, char_n));
                            PyList_Append(litem, PyInt_FromLong(block_n));
                            PyList_Append(litem, PyInt_FromLong(line_n));
                            PyList_Append(litem, PyInt_FromLong(word_n));
                            PyList_Append(lines, litem);
                            Py_DECREF(litem);
                        }
                        line_n += 1;
                    }
                    block_n += 1;
                }
            }
            return lines;
        }

        //---------------------------------------------------------------------
        // Get raw text between two points on a text page
        //---------------------------------------------------------------------
        FITZEXCEPTION(_extractTextLines, !result)
        const char *_extractTextLines(struct fz_point_s *p1, struct fz_point_s *p2)
        {
            char *c = NULL;
            fz_point a = {p1->x, p1->y};
            fz_point b = {p2->x, p2->y};
            fz_try(gctx)
            {
                c = fz_copy_selection(gctx, $self, a, b, 0);
            }
            fz_catch(gctx) return NULL;
            return c;
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
            size_t res_len = 0;
            PyObject *text = NULL;
            fz_try(gctx)
            {
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                unsigned char *data;
                switch(format)
                {
                    case(1):
                        fz_print_stext_page_as_html(gctx, out, $self);
                        break;
                    case(2):
                        DG_print_stext_page_as_json(gctx, out, $self);
                        break;
                    case(3):
                        fz_print_stext_page_as_xml(gctx, out, $self);
                        break;
                    case(4):
                        fz_print_stext_page_as_xhtml(gctx, out, $self);
                        break;
                    default:
                        JM_print_stext_page_as_text(gctx, out, $self);
                }
                res_len = fz_buffer_storage(gctx, res, &data);
                text = PyUnicode_FromStringAndSize(data, (Py_ssize_t) res_len);
                fz_drop_buffer(gctx, res);
            }
            fz_always(gctx) if (out) fz_drop_output(gctx, out);
            fz_catch(gctx)
            {
                if (res) fz_drop_buffer(gctx, res);
                return NULL;
            }
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
                
        %}
    }
};

%rename("Graftmap") pdf_graft_map_s;
struct pdf_graft_map_s {
    %extend {
        ~pdf_graft_map_s()
        {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free graftmap ...");
#endif
            pdf_drop_graft_map(gctx, $self);
#ifdef MEMDEBUG
            fprintf(stderr, " done!\n");
#endif
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
    }
};
