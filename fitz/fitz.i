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
                PyErr_SetString(PyExc_Exception, gctx->error->message);
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
    raise RuntimeError("operation illegal for closed doc")%}
%enddef
//=============================================================================

//=============================================================================
// SWIG macro: check if object has valid parent
//=============================================================================
%define PARENTCHECK(meth)
%pythonprepend meth
%{if not hasattr(self, "parent") or self.parent is None:
    raise RuntimeError("orphaned object: has no parent")%}
%enddef
//=============================================================================

//=============================================================================
// SWIG macro: throw exceptions.
//=============================================================================
%define THROWMSG(msg)
fz_throw(gctx, FZ_ERROR_GENERIC, msg)
%enddef
//=============================================================================

// SWIG macro: check whether document type is PDF
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
void fz_print_stext_page_json(fz_context *ctx, fz_output *out, fz_stext_page *page);
void fz_print_rect_json(fz_context *ctx, fz_output *out, fz_rect *bbox);
void fz_print_utf8(fz_context *ctx, fz_output *out, int rune);
void fz_print_span_stext_json(fz_context *ctx, fz_output *out, fz_stext_span *span);
void fz_send_data_base64(fz_context *ctx, fz_output *out, fz_buffer *buffer);

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
%include helper-json.i
%include helper-python.i
%include helper-other.i
%include helper-portfolio.i
%include helper-select.i

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
        FITZEXCEPTION(fz_document_s, result==NULL)
        %pythonprepend fz_document_s %{
            if not filename or type(filename) == str:
                pass
            elif type(filename) == unicode:
                filename = filename.encode('utf8')
            else:
                raise TypeError("if specified, filename must be a string.")
            self.name = filename if filename else ""
            self.streamlen = len(stream) if stream else 0
            if stream and not filename:
                raise ValueError("filetype missing with stream specified")
            self.isClosed    = 0
            self.isEncrypted = 0
            self.metadata    = None
            self.openErrCode = 0
            self.openErrMsg  = ''
            self._page_refs  = weakref.WeakValueDictionary()

        %}
        %pythonappend fz_document_s %{
            if this:
                self.openErrCode = self._getGCTXerrcode()
                self.openErrMsg  = self._getGCTXerrmsg()
            if this and self.needsPass:
                self.isEncrypted = 1
            # we won't init encrypted doc until it is decrypted
            if this and not self.needsPass:
                self.initData()
                self.thisown = True
        %}

        fz_document_s(const char *filename = NULL, PyObject *stream = NULL)
        {
            struct fz_document_s *doc = NULL;
            fz_stream *data = NULL;
            char *streamdata;
            size_t streamlen = 0;
            if (PyByteArray_Check(stream))
            {
                streamdata = PyByteArray_AsString(stream);
                streamlen = (size_t) PyByteArray_Size(stream);
            }
            else if (PyBytes_Check(stream))
            {
                streamdata = PyBytes_AsString(stream);
                streamlen = (size_t) PyBytes_Size(stream);
            }

            fz_try(gctx)
            {
                gctx->error->errcode = 0;             // reset last error code
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
            fz_catch(gctx)
                return NULL;
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
            self.isClosed    = 1
            self.openErrCode = 0
            self.openErrMsg  = ''
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
        struct fz_page_s *loadPage(int number)
        {
            struct fz_page_s *page = NULL;
            int pageCount = fz_count_pages(gctx, $self);
            int n = number;
            while (n < 0) n += pageCount;
            fz_try(gctx) page = fz_load_page(gctx, $self, n);
            fz_catch(gctx) return NULL;
            return page;
        }

        CLOSECHECK(_loadOutline)
        struct fz_outline_s *_loadOutline()
        {
            return fz_load_outline(gctx, $self);
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
            limit1 = "�";                   // initialize low entry
            limit2 = " ";                   // initialize high entry
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
                n = FindEmbedded(id, pdf);
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
                name = getPDFstr(id, &name_len, "id");
                f = getPDFstr(filename, &file_len, "filename");
                d = getPDFstr(desc, &desc_len, "desc");
                if ((!f) && (!d)) THROWMSG("nothing to change");
                int count = pdf_count_portfolio_entries(gctx, pdf);
                if (count < 1) THROWMSG("no embedded files");
                n = FindEmbedded(id, pdf);
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
                int i = FindEmbedded(id, pdf);
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
            fz_buffer *data = NULL;
            int entry = 0;
            size_t size = 0;
            Py_ssize_t name_len, file_len, desc_len;
            char *f, *d;
            fz_try(gctx)
            {
                name_len = strlen(name);
                if (name_len < 1) THROWMSG("name not valid");
                f = getPDFstr(filename, &file_len, "filename");
                d = getPDFstr(desc, &desc_len, "desc");
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
                entry = pdf_add_portfolio_entry(gctx, pdf,
                            name, name_len, /* name */
                            d, desc_len, /* desc */
                            f, file_len, /* filename */
                            f, file_len, /* unifile */
                            data);
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

        int _getGCTXerrcode() {
            return gctx->error->errcode;
        }

        char *_getGCTXerrmsg() {
            return gctx->error->message;
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
                if ((incremental) && (garbage))
                    THROWMSG("incremental excludes garbage");
                if ((incremental) && (pdf->repair_attempted))
                    THROWMSG("repaired file - save to new");
                if ((incremental) && (fz_needs_password(gctx, $self)))
                    THROWMSG("encrypted file - save to new");
                if ((incremental) && (linear))
                    THROWMSG("incremental excludes linear");
                pdf_save_document(gctx, pdf, filename, &opts);
                }
            fz_catch(gctx) return -1;
            return 0;
        }

        /****************************************************************/
        // write document to memory
        /****************************************************************/
        FITZEXCEPTION(write, !result)
        %feature("autodoc", "Write document to bytearray.") write;
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
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                pdf_write_document(gctx, pdf, out, &opts);
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

        //*********************************************************************
        // Insert pages from a source PDF into this PDF.
        // For reconstructing the links (_do_links method), we must save the
        // insertion point (start_at) if it was specified as -1.
        //*********************************************************************
        FITZEXCEPTION(insertPDF, result<0)
        %pythonprepend insertPDF
%{if self.isClosed:
    raise RuntimeError("operation illegal for closed doc")
if id(self) == id(docsrc):
    raise RuntimeError("source must not equal target PDF")
sa = start_at
if sa < 0:
    sa = self.pageCount%}

        %pythonappend insertPDF
%{if links:
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
                if (!pdfout) THROWMSG("target not a PDF");
                if (!pdfsrc) THROWMSG("source not a PDF");
                merge_range(pdfout, pdfsrc, fp, tp, sa, rotate);
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
                if ((pno < 0) | (pno >= pageCount))
                    THROWMSG("page number out of range");
                pdf_delete_page(gctx, pdf, pno);
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
                    THROWMSG("invalid page range");
                int i = t + 1 - f;
                while (i > 0)
                {
                    pdf_delete_page(gctx, pdf, f);
                    i -= 1;
                }
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
                    THROWMSG("source page out of range");
                pdf_obj *page = pdf_lookup_page_obj(gctx, pdf, pno);
                pdf_insert_page(gctx, pdf, to, page);
            }
            fz_catch(gctx) return -1;
            return 0;
        }

        //---------------------------------------------------------------------
        // Create and insert a new page (PDF)
        //---------------------------------------------------------------------
        FITZEXCEPTION(insertPage, result<0)
        CLOSECHECK(insertPage)
        %feature("autodoc","Insert a new page in front of 'to'.") insertPage;
        %pythonprepend insertPage %{
        if self.isClosed:
            raise RuntimeError("operation illegal for closed doc")
        # ensure 'text' is a list of strings
        if text is not None:
            if type(text) not in (list, tuple):
                text = text.split("\n")
            tab = []
            for t in text:
                tab.append(getPDFstr(t, brackets = False))
            text = tab
        else:
            text = []
        # ensure 'fontname' is valid
        if not fontfile:
            if (not fontname) or fontname not in Base14_fontnames:
                fontname = "Helvetica"
        %}
        %pythonappend insertPage %{if val == 0: self._reset_page_refs()%}
        int insertPage(int to = -1, PyObject *text = NULL, float fontsize = 11,
                       float width = 595, float height = 842,
                       char *fontname = NULL, char *fontfile = NULL,
                       PyObject *color = NULL)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            const char *templ1 = "BT %g %g %g rg 1 0 0 1 50 %g Tm /%s %g Tf";
            const char *templ2 = "Tj 0 -%g TD\n";
            fz_rect mediabox = { 0, 0, 595, 842 };    // DIN-A4 portrait values
            mediabox.x1 = width;
            mediabox.y1 = height;
            float red, green, blue;
            red = green = blue = 0;
            char *itxt = NULL;
            size_t len, i, c_len, maxlen = 0;
            PyObject *t = NULL;
            float lheight = fontsize * 1.2;      // line height
            float top = height - 72 - fontsize;  // y of 1st line
            const char *data;
            int size;
            fz_font *font;
            pdf_obj *font_obj, *resources;
            pdf_obj *page_obj = NULL;
            // this will contain the /Contents stream:
            fz_buffer *contents = fz_new_buffer(gctx, 1024);
            fz_append_string(gctx, contents, "");
            maxlen = (height - 108) / lheight;   // max lines per page
            len = (size_t) PySequence_Size(text);
            if (len > maxlen) len = maxlen;
            char *font_str = fontname;

            fz_try(gctx)
            {
                assert_PDF(pdf);
                if (PySequence_Check(color))
                {
                    if (PySequence_Size(color) != 3) THROWMSG("need 3 color components");
                    red   = (float) PyFloat_AsDouble(PySequence_GetItem(color, 0));
                    green = (float) PyFloat_AsDouble(PySequence_GetItem(color, 1));
                    blue  = (float) PyFloat_AsDouble(PySequence_GetItem(color, 2));
                    if (red < 0 || red > 1 || green < 0 || green > 1 || blue < 0 || blue > 1)
                        THROWMSG("color components must in range [0, 1]");
                }
                if (len > 0)
                {
                    if (!fontname) THROWMSG("fontname must be supplied");
                    fz_append_printf(gctx, contents, templ1, red, green, blue, top,
                                     font_str, fontsize);
                    itxt = getPDFstr(PySequence_GetItem(text, 0), &c_len, "text0");
                    if ((strncmp(itxt, "<feff", 5) == 0) || (strncmp(itxt, "<FEFF", 5) == 0))
                        fz_append_string(gctx, contents, itxt);
                    else
                        fz_append_pdf_string(gctx, contents, itxt);
                    fz_append_printf(gctx, contents, templ2, lheight);
                    for (i = 1; i < len; i++)
                    {
                        if (i>1) fz_append_string(gctx, contents, "T* ");
                        itxt = getPDFstr(PySequence_GetItem(text, i), &c_len, "texti");
                        if ((strncmp(itxt, "<feff", 5) == 0) || (strncmp(itxt, "<FEFF", 5) == 0))
                            fz_append_string(gctx, contents, itxt);
                        else
                            fz_append_pdf_string(gctx, contents, itxt);
                        fz_append_string(gctx, contents, "Tj\n");
                    }
                    fz_append_string(gctx, contents, "ET\n");
                }
                // the new /Resources object:
                resources = pdf_add_object_drop(gctx, pdf, pdf_new_dict(gctx, pdf, 1));

                if (len > 0)           // only if there was some text:
                {
                    // content stream done, now insert the font
                    data = fz_lookup_base14_font(gctx, font_str, &size);
                    if (data)              // base 14 font found
                        font = fz_new_font_from_memory(gctx, font_str, data, size, 0, 0);
                    else
                    {
                        if (!fontfile) THROWMSG("unknown PDF Base 14 font");
                        font = fz_new_font_from_file(gctx, NULL, fontfile, 0, 0);
                    }

                    font_obj = pdf_add_simple_font(gctx, pdf, font);
                    fz_drop_font(gctx, font);
                    // resources obj will contain named reference to font
                    itxt = getPDFstr(PyUnicode_Concat(PyUnicode_FromString("Font/"), 
                                    PyUnicode_FromString(font_str)), &c_len, "font");
                    // itxt = "Font/font_str"
                    pdf_dict_putp_drop(gctx, resources, itxt, font_obj);
                }
                // ready to create and insert page
                fz_terminate_buffer(gctx, contents);
                page_obj = pdf_add_page(gctx, pdf, &mediabox, 0, resources, contents);
                pdf_insert_page(gctx, pdf, to , page_obj);
            }
            fz_always(gctx)
            {
                fz_drop_buffer(gctx, contents);
                if (page_obj) pdf_drop_obj(gctx, page_obj);
            }
            fz_catch(gctx) return -1;
            return (int) len;
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
                    THROWMSG("source page out of range");
                int t = to;
                if (t < 0) t = pageCount;
                if ((t == pno) | (pno == t - 1))
                    THROWMSG("source and target too close");
                pdf_obj *page = pdf_lookup_page_obj(gctx, pdf, pno);
                pdf_insert_page(gctx, pdf, t, page);
                if (pno < t)
                    pdf_delete_page(gctx, pdf, pno);
                else
                    pdf_delete_page(gctx, pdf, pno+1);
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
            int argc;
            fz_try(gctx)
            {
                assert_PDF(pdf);
                if (!PySequence_Check(pyliste))
                    THROWMSG("expected a sequence");
                argc = (int) PySequence_Size(pyliste);
                if (argc < 1)
                    THROWMSG("sequence is empty");
            }
            fz_catch(gctx) return -1;

            // transform Python list into int array
            int pageCount = fz_count_pages(gctx, $self);
            int i;
            int *liste;
            liste = malloc(argc * sizeof(int));
            fz_try(gctx)
            {
                for (i = 0; i < argc; i++)
                {
                    PyObject *o = PySequence_GetItem(pyliste, i);
                    if (PyInt_Check(o))
                    {
                        liste[i] = (int) PyInt_AsLong(o);
                        if ((liste[i] < 0) | (liste[i] >= pageCount))
                            THROWMSG("some page numbers not in range");
                    }
                    else
                        THROWMSG("page numbers must be integers");
                }
            }
            fz_catch(gctx)
            {
                if (liste) free (liste);
                return -1;
            }
            // now call retainpages (code copy of fz_clean_file.c)
            globals glo = { 0 };
            glo.ctx = gctx;
            glo.doc = pdf;
            fz_try(gctx) retainpages(gctx, &glo, argc, liste);
            fz_always(gctx) free (liste);
            fz_catch(gctx) return -5;
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

        FITZEXCEPTION(_getPageObjNumber, !result)
        CLOSECHECK(_getPageObjNumber)
        PyObject *_getPageObjNumber(int pno)
        {
            int pageCount = fz_count_pages(gctx, $self);
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                if ((pno < 0) | (pno >= pageCount))
                    THROWMSG("page number out of range");
                assert_PDF(pdf);
            }
            fz_catch(gctx) return NULL;
            pdf_obj *pageref = pdf_lookup_page_obj(gctx, pdf, pno);
            long objnum = (long) pdf_to_num(gctx, pageref);
            long objgen = (long) pdf_to_gen(gctx, pageref);
            return Py_BuildValue("(l, l)", objnum, objgen);
        }

        //*********************************************************************
        // Returns the images used on a page as a list of lists.
        // Each image entry contains
        // [xref#, gen#, width, height, bpc, colorspace, altcs]
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
                if (n >= pageCount) THROWMSG("page number out of range");
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
                pdf_obj *imagedict, *imagename, *type, *altcs, *o, *cs;
                PyObject *xref, *gen, *width, *height, *bpc, *cs_py, *altcs_py;
                PyObject *name_py;
                imagedict = pdf_dict_get_val(gctx, dict, i);
                imagename = pdf_dict_get_key(gctx, dict, i);
                if (!pdf_is_dict(gctx, imagedict)) continue;

                type = pdf_dict_get(gctx, imagedict, PDF_NAME_Subtype);
                if (!pdf_name_eq(gctx, type, PDF_NAME_Image)) continue;

                xref = PyInt_FromLong((long) pdf_to_num(gctx, imagedict));
                gen  = PyInt_FromLong((long) pdf_to_gen(gctx, imagedict));

                o = pdf_dict_get(gctx, imagedict, PDF_NAME_Width);
                width = PyInt_FromLong((long) pdf_to_int(gctx, o));

                o = pdf_dict_get(gctx, imagedict, PDF_NAME_Height);
                height = PyInt_FromLong((long) pdf_to_int(gctx, o));

                o = pdf_dict_get(gctx, imagedict, PDF_NAME_BitsPerComponent);
                bpc = PyInt_FromLong((long) pdf_to_int(gctx, o));

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

                cs_py = PyString_FromString(pdf_to_name(gctx, cs));
                altcs_py = PyString_FromString(pdf_to_name(gctx, altcs));
                name_py = PyString_FromString(pdf_to_name(gctx, imagename));
                PyObject *img = PyList_New(0);         /* Python list per img */
                PyList_Append(img, xref);
                PyList_Append(img, gen);
                PyList_Append(img, width);
                PyList_Append(img, height);
                PyList_Append(img, bpc);
                PyList_Append(img, cs_py);
                PyList_Append(img, altcs_py);
                PyList_Append(img, name_py);
                PyList_Append(imglist, img);
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
                if (n >= pageCount) THROWMSG("page number out of range");
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
                long xref = (long) pdf_to_num(gctx, fontdict);
                long gen  = (long) pdf_to_gen(gctx, fontdict);
                subtype = pdf_dict_get(gctx, fontdict, PDF_NAME_Subtype);
                basefont = pdf_dict_get(gctx, fontdict, PDF_NAME_BaseFont);
                if (!basefont || pdf_is_null(gctx, basefont))
                    bname = pdf_dict_get(gctx, fontdict, PDF_NAME_Name);
                else
                    bname = basefont;
                name = pdf_dict_get_key(gctx, dict, i);
                PyObject *font = PyList_New(0);       // Python list per font
                PyList_Append(font, PyInt_FromLong(xref));
                PyList_Append(font, PyInt_FromLong(gen));
                PyList_Append(font, PyString_FromString(pdf_to_name(gctx, subtype)));
                PyList_Append(font, PyString_FromString(pdf_to_name(gctx, bname)));
                PyList_Append(font, PyString_FromString(pdf_to_name(gctx, name)));
                PyList_Append(fontlist, font);
            }
            return fontlist;
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
            argc = countOutlines(first, argc);         // get number outlines
            if (argc < 1) return xrefs;
            res = malloc(argc * sizeof(int));          // object number table
            objcount = fillOLNumbers(res, first, objcount, argc); // fill table
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

        //*********************************************************************
        // Get bare text inside a rectangle of a page
        //*********************************************************************
        FITZEXCEPTION(_getPageRectText, !result)
        CLOSECHECK(_getPageRectText)
        const char *_getPageRectText(int pno, struct fz_rect_s *rect)
        {
            fz_buffer *res;
            fz_try(gctx)
            {
                res = fz_new_buffer_from_page_number(gctx, $self, pno, rect, 0, NULL);
            }
            fz_catch(gctx) return NULL;
            return fz_string_from_buffer(gctx, res);
        }

        //*********************************************************************
        // Delete XML-based Metadata
        //*********************************************************************
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
        // Get Object String by Xref Number
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
                if ((xref < 1) | (xref >= xreflen))
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
                if (page) refresh_link_table(pdf_page_from_fz_page(gctx, page));
            }
            fz_catch(gctx) return -1;
            return 0;
        }

        //---------------------------------------------------------------------
        // Update a stream identified by its xref
        //---------------------------------------------------------------------
        FITZEXCEPTION(_updateStream, result!=0)
        CLOSECHECK(_updateStream)
        int _updateStream(int xref, PyObject *stream)
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
                if ((xref < 1) | (xref >= xreflen))
                    THROWMSG("xref out of range");
                if (PyBytes_Check(stream))
                {
                    c = PyBytes_AsString(stream);
                    len = (size_t) PyBytes_Size(stream);
                }
                if (PyByteArray_Check(stream))
                {
                    c = PyByteArray_AsString(stream);
                    len = (size_t) PyByteArray_Size(stream);
                }
                if (c == NULL) THROWMSG("invalid stream");
                // get the object
                obj = pdf_new_indirect(gctx, pdf, xref, 0);
                if (!obj) THROWMSG("xref invalid");
                if (!pdf_is_stream(gctx, obj)) THROWMSG("xref is not a stream");
                
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
                if self.streamlen == 0:
                    return "fitz.Document('%s')" % (self.name,)
                return "fitz.Document('%s', bytearray)" % (self.name,)

            def __getitem__(self, i):
                if i >= len(self):
                    raise IndexError("page number out of range")
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
                for page in self._page_refs.values():
                    if page:
                        page._erase()
                self._page_refs.clear()
            
            def __del__(self):
                self._reset_page_refs()
                if getattr(self, "thisown", True):
                    self.__swig_destroy__(self)
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
        %pythoncode %{rect = property(bound, doc="Rect (mediabox) of the page")%}

        /***********************************************************/
        // run()
        /***********************************************************/
        FITZEXCEPTION(run, result)
        PARENTCHECK(run)
        int run(struct DeviceWrapper *dw, const struct fz_matrix_s *m)
        {
            fz_try(gctx) fz_run_page(gctx, $self, dw->device, m, NULL);
            fz_catch(gctx) return 1;
            return 0;
        }

        /***********************************************************/
        // loadLinks()
        /***********************************************************/
        PARENTCHECK(loadLinks)
        %pythonappend loadLinks
%{if val:
    val.thisown = True
    val.parent = weakref.proxy(self) # owning page object
    self._annot_refs[id(val)] = val%}
        struct fz_link_s *loadLinks()
        {
            return fz_load_links(gctx, $self);
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
            fz_annot *annot = fz_first_annot(gctx, $self);
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
            refresh_link_table(page);            // reload link / annot tables
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

        /*********************************************************************/
        // rotation - return page rotation
        /*********************************************************************/
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
        PARENTCHECK(setRotation)
        %feature("autodoc","Set page rotation to 'rot' degrees.") setRotation;
        int setRotation(int rot)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            if (!page) return -1;
            pdf_obj *rot_o = pdf_new_int(gctx, page->doc, rot);
            pdf_dict_put_drop(gctx, page->obj, PDF_NAME_Rotate, rot_o);
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
                refresh_link_table(page);
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
            pdf_obj *resources, *subres, *contents, *ref;
            fz_buffer *res = NULL;
            fz_buffer *nres = NULL;
            int i, j;
            unsigned char *s, *t;
            char *content_str;
            const char *template = " q %s 0 0 %s %s %s cm /%s Do Q\n";
            Py_ssize_t c_len = 0;
            fz_rect prect = { 0, 0, 0, 0};
            fz_bound_page(gctx, $self, &prect);  // get page mediabox
            char X[15], Y[15], W[15], H[15];     // rect coord as strings
            char name[50], md5hex[33];           // image ref
            unsigned char md5[16];               // md5 of the image
            char *cont = NULL;
            const char *name_templ = "FITZ%s";   // template for image ref
            Py_ssize_t name_len = 0;
            fz_image *zimg, *image = NULL;
            fz_try(gctx)
            {
                assert_PDF(page);
                pdf = page->doc;
                if ((pixmap) && (filename) || (!pixmap) && (!filename))
                    THROWMSG("exactly one of filename, pixmap must be given");
                if (!fz_contains_rect(&prect, rect))
                    THROWMSG("rect must be contained in page rect");
                if (fz_is_empty_rect(rect) || fz_is_infinite_rect(rect))
                    THROWMSG("rect must be finite and not empty");

                // create strings for rect coordinates
                snprintf(X, 15, "%g", (double) rect->x0);
                snprintf(Y, 15, "%g", (double) (prect.y1 - rect->y1));
                snprintf(W, 15, "%g", (double) (rect->x1 - rect->x0));
                snprintf(H, 15, "%g", (double) (rect->y1 - rect->y0));

                // get objects "Resources" and "XObject"
                contents = pdf_dict_get(gctx, page->obj, PDF_NAME_Contents);
                resources = pdf_dict_get(gctx, page->obj, PDF_NAME_Resources);
                subres = pdf_dict_get(gctx, resources, PDF_NAME_XObject);
                if (!subres)           // has no XObject (yet)
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
                        pm = fz_new_pixmap(gctx, NULL, pix->w, pix->h, 0);
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
                        pm = fz_new_pixmap(gctx, NULL, pixmap->w, pixmap->h, 0);
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
                if (pdf_is_array(gctx, contents))     // multiple contents obj
                {   // choose the correct one (1st or last)
                    if (overlay == 1) i = pdf_array_len(gctx, contents) - 1;
                    else              i = 0;
                    contents = pdf_array_get(gctx, contents, i);
                }
                res = pdf_load_stream(gctx, contents); // decompressed stream
                if (!res) THROWMSG("bad PDF: Contents is no stream object");
                nres = fz_new_buffer(gctx, 1024);
                // insert our string into contents buffer
                fz_append_printf(gctx, nres, template, W, H, X, Y, name);
                if (overlay == 1)      // append our string
                {
                    fz_append_buffer(gctx, res, nres);
                    fz_drop_buffer(gctx, nres);
                    nres = NULL;
                }
                else                   // prepend our string
                {
                    fz_append_buffer(gctx, nres, res);
                    fz_drop_buffer(gctx, res);
                    res = nres;
                }
                fz_terminate_buffer(gctx, res);
                // now compress and put back contents stream
                pdf_dict_put(gctx, contents, PDF_NAME_Filter,
                             PDF_NAME_FlateDecode);
                c_len = (Py_ssize_t) fz_buffer_storage(gctx, res, &content_str);
                nres = deflatebuf(gctx, content_str, (size_t) c_len);
                pdf_update_stream(gctx, pdf, contents, nres, 1);
            }
            fz_always(gctx)
            {
                if (image) fz_drop_image(gctx, image);
                if (res) fz_drop_buffer(gctx, res);
                if (nres) fz_drop_buffer(gctx, nres);
                if (mask) fz_drop_image(gctx, mask);
                if (pix) fz_drop_pixmap(gctx, pix);
                if (pm) fz_drop_pixmap(gctx, pm);
            }
            fz_catch(gctx) return -1;
            return 0;
        }

        //---------------------------------------------------------------------
        // insert text
        //---------------------------------------------------------------------
        FITZEXCEPTION(insertText, result<0)
        %pythonprepend insertText %{
        if not self.parent:
            raise RuntimeError("orphaned object: no parent exists")
        # ensure 'text' is a list of strings
        if text is not None:
            if type(text) not in (list, tuple):
                text = text.split("\n")
            tab = []
            for t in text:
                tab.append(getPDFstr(t, brackets = False))
            text = tab
        else:
            text = []
        # ensure valid 'fontname'
        if not fontfile:
            if not fontname:
                fontname = "Helvetica"
            else:
                if fontname.startswith("/"):
                    fontlist = self.parent.getPageFontList(self.number)
                    fontrefs = [fontlist[i][4] for i in range(len(fontlist))]
                    assert fontname[1:] in fontrefs, "invalid font name reference: " + fontname
                elif fontname not in Base14_fontnames:
                    fontname = "Helvetica"%}
        %feature("autodoc", "Insert new text on a page.") insertText;
        int insertText(struct fz_point_s *point, PyObject *text = NULL,
                       float fontsize = 11, const char *fontname = NULL,
                       const char *fontfile = NULL, PyObject *color = NULL)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_document *pdf;
            pdf_obj *resources, *contents, *fonts;
            fz_buffer *cont_buf, *cont_buf_compr;
            cont_buf = cont_buf_compr = NULL;
            char *content_str;              // updated content string
            const char *templ1 = " BT %g %g %g rg 1 0 0 1 %g %g Tm %s%s %g Tf";
            const char *templ2 = "Tj 0 -%g TD\n";
            Py_ssize_t c_len, len;
            int i, nlines;
            char *itxt;
            fz_rect prect = { 0, 0, 0, 0};
            fz_bound_page(gctx, $self, &prect);
            float top = prect.y1 - point->y;
            float left = point->x;
            float red, green, blue;
            red = green = blue = 0;
            float lheight = fontsize * 1.2; // line height
            float pheight = prect.y1;       // page height
            const char *data;
            int size;
            fz_font *font;
            pdf_obj *font_obj;
            fz_try(gctx)
            {
                assert_PDF(page);
                pdf = page->doc;
                if (top < lheight || point->y < lheight)
                    THROWMSG("text position outside vertical page range");
                if (!fontname) THROWMSG("fontname must be supplied");
                if (PySequence_Check(color))
                {
                    if (PySequence_Size(color) != 3) THROWMSG("need 3 color components");
                    red   = (float) PyFloat_AsDouble(PySequence_GetItem(color, 0));
                    green = (float) PyFloat_AsDouble(PySequence_GetItem(color, 1));
                    blue  = (float) PyFloat_AsDouble(PySequence_GetItem(color, 2));
                    if (red < 0 || red > 1 || green < 0 || green > 1 || blue < 0 || blue > 1)
                        THROWMSG("color components must in range [0, 1]");
                }
                if (!PySequence_Check(text)) THROWMSG("text must be specified");
                else
                {
                    len = PySequence_Size(text);
                    if (len < 1) THROWMSG("some text is needed");
                }
                // get objects "Resources", "Contents", "Resources/Font"
                resources = pdf_dict_get(gctx, page->obj, PDF_NAME_Resources);
                fonts = pdf_dict_get(gctx, resources, PDF_NAME_Font);
                if (!fonts)
                    fonts = pdf_add_object_drop(gctx, pdf, pdf_new_dict(gctx, pdf, 1));
                contents = pdf_dict_get(gctx, page->obj, PDF_NAME_Contents);
                if (pdf_is_array(gctx, contents))
                {   // take last if more than one contents object
                    i = pdf_array_len(gctx, contents) - 1;
                    contents = pdf_array_get(gctx, contents, i);
                }
                // extract decompressed contents string in a buffer
                cont_buf = pdf_load_stream(gctx, contents);
                if (!cont_buf) THROWMSG("bad PDF: Contents is no stream object");

                // append our stuff to contents
                char *font_pref = "/";
                if (strncmp(fontname, "/", 1) == 0) font_pref = " ";
                fz_append_printf(gctx, cont_buf, templ1, red, green, blue,
                                 left, top, font_pref, fontname, fontsize);
                itxt = getPDFstr(PySequence_GetItem(text, 0), &c_len, "text0");
                // append as string if UTF-16BE encoded, else as PDF string
                if ((strncmp(itxt, "<feff", 5) == 0) || (strncmp(itxt, "<FEFF", 5) == 0))
                    fz_append_string(gctx, cont_buf, itxt);
                else
                    fz_append_pdf_string(gctx, cont_buf, itxt);
                top -= lheight;
                nlines = 1;
                fz_append_printf(gctx, cont_buf, templ2, lheight);   // line 1
                for (i = 1; i < len; i++)
                {
                    if (top < lheight) break;    // no space left on page
                    if (i > 1) fz_append_string(gctx, cont_buf, "T* ");
                    itxt = getPDFstr(PySequence_GetItem(text, i), &c_len, "texti");
                    if ((strncmp(itxt, "<feff", 5) == 0) || (strncmp(itxt, "<FEFF", 5) == 0))
                        fz_append_string(gctx, cont_buf, itxt);
                    else
                        fz_append_pdf_string(gctx, cont_buf, itxt);
                    fz_append_string(gctx, cont_buf, "Tj\n");
                    top -= lheight;
                    nlines++;
                }
                fz_append_string(gctx, cont_buf, "ET\n");
                fz_terminate_buffer(gctx, cont_buf);

                // indicate we will turn in compressed contents
                pdf_dict_put(gctx, contents, PDF_NAME_Filter,
                             PDF_NAME_FlateDecode);
                c_len = (Py_ssize_t) fz_buffer_storage(gctx, cont_buf, &content_str);
                cont_buf_compr = deflatebuf(gctx, content_str, (size_t) c_len);
                pdf_update_stream(gctx, pdf, contents, cont_buf_compr, 1);

                if (strncmp(fontname, "/", 1) != 0)   // new font given
                {   // insert new font
                    data = fz_lookup_base14_font(gctx, fontname, &size);
                    if (data)              // base 14 font found
                        font = fz_new_font_from_memory(gctx, fontname, data, size, 0, 0);
                    else
                    {
                        if (!fontfile) THROWMSG("unknown PDF Base 14 font");
                        font = fz_new_font_from_file(gctx, NULL, fontfile, 0, 0);
                    }

                    font_obj = pdf_add_simple_font(gctx, pdf, font);
                    fz_drop_font(gctx, font);
                    // resources obj will contain named reference to font
                    pdf_dict_puts(gctx, fonts, fontname, font_obj);
                    pdf_dict_put(gctx, resources, PDF_NAME_Font, fonts);
                }
            }
            fz_always(gctx)
            {
                if (cont_buf) fz_drop_buffer(gctx, cont_buf);
                if (cont_buf_compr) fz_drop_buffer(gctx, cont_buf_compr);
            }
            fz_catch(gctx) return -1;
            return nlines;
        }

        //---------------------------------------------------------------------
        // draw line
        //---------------------------------------------------------------------
        FITZEXCEPTION(drawLine, result<0)
        %feature("autodoc", "Draw a line from point 'p1' to 'p2'.") drawLine;
        int drawLine(struct fz_point_s *p1, struct fz_point_s *p2,
                     PyObject *color = NULL, float width = 1, char *dashes = NULL)
        {
            pdf_page *page = pdf_page_from_fz_page(gctx, $self);
            pdf_document *pdf;
            pdf_obj *resources, *contents;
            fz_buffer *cont_buf, *cont_buf_compr;
            cont_buf = cont_buf_compr = NULL;
            char *content_str;              // updated content string
            const char *templ1 = "\nq 1 J %s d %g %g %g RG %g w %g %g m %g %g l S Q\n";
            char *dash_str = "[]0";
            Py_ssize_t c_len;
            int i;
            fz_rect prect = { 0, 0, 0, 0};
            fz_bound_page(gctx, $self, &prect);
            float red, green, blue, from_y, to_y;
            red = green = blue = 0;
            from_y = prect.y1 - p1->y;
            to_y = prect.y1 - p2->y;
            fz_try(gctx)
            {
                assert_PDF(page);
                pdf = page->doc;
                if (p1->y < prect.y0 || p1->y > prect.y1 ||
                    p2->y < prect.y0 || to_y > prect.y1 || 
                    p1->x < prect.x0 || p1->x > prect.x1 ||
                    p2->x < prect.x0 || p2->x > prect.x1)
                    THROWMSG("line endpoints must be within page rect");
                if (PySequence_Check(color))
                {
                    if (PySequence_Size(color) != 3) THROWMSG("need 3 color components");
                    red   = (float) PyFloat_AsDouble(PySequence_GetItem(color, 0));
                    green = (float) PyFloat_AsDouble(PySequence_GetItem(color, 1));
                    blue  = (float) PyFloat_AsDouble(PySequence_GetItem(color, 2));
                    if (red < 0 || red > 1 || green < 0 || green > 1 || blue < 0 || blue > 1)
                        THROWMSG("color components must in range 0 to 1");
                }
                if (dashes) dash_str = dashes;
                // get objects "Resources", "Contents", "Resources/Font"
                resources = pdf_dict_get(gctx, page->obj, PDF_NAME_Resources);
                contents = pdf_dict_get(gctx, page->obj, PDF_NAME_Contents);
                if (pdf_is_array(gctx, contents))
                {   // take last if more than one contents object
                    i = pdf_array_len(gctx, contents) - 1;
                    contents = pdf_array_get(gctx, contents, i);
                }
                // extract decompressed contents string in a buffer
                cont_buf = pdf_load_stream(gctx, contents);
                if (!cont_buf) THROWMSG("bad PDF: Contents is no stream object");

                // append our stuff to contents
                fz_append_printf(gctx, cont_buf, templ1, dash_str, red, green,
                                 blue, width, p1->x, from_y, p2->x, to_y);
                fz_terminate_buffer(gctx, cont_buf);

                // indicate we will turn in compressed contents
                pdf_dict_put(gctx, contents, PDF_NAME_Filter,
                             PDF_NAME_FlateDecode);
                c_len = (Py_ssize_t) fz_buffer_storage(gctx, cont_buf, &content_str);
                cont_buf_compr = deflatebuf(gctx, content_str, (size_t) c_len);
                pdf_update_stream(gctx, pdf, contents, cont_buf_compr, 1);

            }
            fz_always(gctx)
            {
                if (cont_buf) fz_drop_buffer(gctx, cont_buf);
                if (cont_buf_compr) fz_drop_buffer(gctx, cont_buf_compr);
            }
            fz_catch(gctx) return -1;
            return 0;
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
        // Get raw text contained in a rectangle
        //---------------------------------------------------------------------
        FITZEXCEPTION(_getRectText, !result)
        PARENTCHECK(_getRectText)
        const char *_getRectText(struct fz_rect_s *rect)
        {
            fz_buffer *res;
            fz_try(gctx)
            {
                res = fz_new_buffer_from_page(gctx, $self, rect, 0, NULL);
            }
            fz_catch(gctx) return NULL;
            return fz_string_from_buffer(gctx, res);
        }

        //---------------------------------------------------------------------
        // Page._readPageText()
        //---------------------------------------------------------------------
        FITZEXCEPTION(_readPageText, result==NULL)
        %newobject _readPageText;
        const char *_readPageText(int output=0) {
            const char *res = NULL;
            fz_try(gctx) res = readPageText($self, output);
            fz_catch(gctx) return NULL;
            return res;
        }

        %pythoncode %{
        def __str__(self):
            if self.parent:
                return "page %s of %s" % (self.number, repr(self.parent))
            else:
                return "orphaned page"

        def __repr__(self):
            if self.parent:
                return repr(self.parent) + "[" + str(self.number) + "]"
            else:
                return "orphaned page"

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
            
        def __del__(self):
            self._erase()

        def getFontList(self):
            return self.parent.getPageFontList(self.number)

        def getImageList(self):
            return self.parent.getPageImageList(self.number)

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
    float x0, y0;
    float x1, y1;
    fz_rect_s();
    %extend {
        FITZEXCEPTION(fz_rect_s, !result)
        fz_rect_s(const struct fz_rect_s *s) {
            fz_rect *r = (fz_rect *)malloc(sizeof(fz_rect));
            *r = *s;
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
                if (PySequence_Size(list) != 4) THROWMSG("len(sequence) must be 4");
                r->x0 = (float) PyFloat_AsDouble(PySequence_GetItem(list, 0));
                r->y0 = (float) PyFloat_AsDouble(PySequence_GetItem(list, 1));
                r->x1 = (float) PyFloat_AsDouble(PySequence_GetItem(list, 2));
                r->y1 = (float) PyFloat_AsDouble(PySequence_GetItem(list, 3));
            }
            fz_catch(gctx)
            {
                free(r);
                return NULL;
            }
            return r;
        }

        ~fz_rect_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free rect ...");
#endif
            free($self);
#ifdef MEMDEBUG
            fprintf(stderr, " done!\n");
#endif
        }
        %pythonappend round() %{
            val.thisown = True
        %}
        %feature("autodoc","Create enclosing 'IRect'") round;
        struct fz_irect_s *round()
        {
            fz_irect *irect = (fz_irect *)malloc(sizeof(fz_irect));
            fz_rect *rect = (fz_rect *)malloc(sizeof(fz_rect));
            rect->x0 = $self->x0;
            rect->y0 = $self->y0;
            rect->x1 = $self->x1;
            rect->y1 = $self->y1;
            if ($self->x1 < $self->x0)
            {
                rect->x0 = $self->x1;
                rect->x1 = $self->x0;
            }
            if ($self->y1 < $self->y0)
            {
                rect->y0 = $self->y1;
                rect->y1 = $self->y0;
            }
            fz_round_rect(irect, rect);
            free(rect);
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
        PyObject *contains(struct fz_rect_s *r)
        {
            return truth_value(fz_contains_rect($self, r));
        }

        PyObject *contains(struct fz_irect_s *ir)
        {
            fz_rect *r = (fz_rect *)malloc(sizeof(fz_rect));
            r->x0 = ir->x0;
            r->y0 = ir->y0;
            r->x1 = ir->x1;
            r->y1 = ir->y1;
            int rc = fz_contains_rect($self, r);
            free(r);
            return truth_value(rc);
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
                
            def __contains__(self, x):
                if type(x) in (int, float):
                    return x in tuple(self)
                return self.contains(x)

            def __getitem__(self, i):
                a = [self.x0, self.y0, self.x1, self.y1]
                return a[i]

            def __setitem__(self, i, v):
                if   i == 0: self.x0 = v
                elif i == 1: self.y0 = v
                elif i == 2: self.x1 = v
                elif i == 3: self.y1 = v
                else:
                    raise IndexError("list index out of range")
                return

            def __len__(self):
                return 4

            def __repr__(self):
                return "fitz.Rect" + str((self.x0, self.y0, self.x1, self.y1))

            irect = property(round)
            width = property(lambda self: self.x1-self.x0)
            height = property(lambda self: self.y1-self.y0)
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
        FITZEXCEPTION(fz_irect_s, !result)
        ~fz_irect_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free irect ... ");
#endif
            free($self);
#ifdef MEMDEBUG
            fprintf(stderr, "done!\n");
#endif
        }
        fz_irect_s(const struct fz_irect_s *s) {
            fz_irect *r = (fz_irect *)malloc(sizeof(fz_irect));
            *r = *s;
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
                if (PySequence_Size(list) != 4) THROWMSG("sequence length must be 4");
                r->x0 = (int) PyInt_AsLong(PySequence_GetItem(list, 0));
                r->y0 = (int) PyInt_AsLong(PySequence_GetItem(list, 1));
                r->x1 = (int) PyInt_AsLong(PySequence_GetItem(list, 2));
                r->y1 = (int) PyInt_AsLong(PySequence_GetItem(list, 3));
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
        PyObject *contains(struct fz_irect_s *ir)
        {
            fz_rect *s = (fz_rect *)malloc(sizeof(fz_rect));
            s->x0 = $self->x0;
            s->y0 = $self->y0;
            s->x1 = $self->x1;
            s->y1 = $self->y1;
            fz_rect *r = (fz_rect *)malloc(sizeof(fz_rect));
            r->x0 = ir->x0;
            r->y0 = ir->y0;
            r->x1 = ir->x1;
            r->y1 = ir->y1;
            int rc = fz_contains_rect(s, r);
            free(s);
            free(r);
            return truth_value(rc);
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
        
        PyObject *contains(struct fz_rect_s *r)
        {
            fz_rect *s = (fz_rect *)malloc(sizeof(fz_rect));
            s->x0 = $self->x0;
            s->y0 = $self->y0;
            s->x1 = $self->x1;
            s->y1 = $self->y1;
            int rc = fz_contains_rect(s, r);
            free(s);
            return truth_value(rc);
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
            width = property(lambda self: self.x1-self.x0)
            height = property(lambda self: self.y1-self.y0)

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
                
            def __contains__(self, x):
                if type(x) in (int, float):
                    return x in tuple(self)
                return self.contains(x)

            def __getitem__(self, i):
                a = [self.x0, self.y0, self.x1, self.y1]
                return a[i]

            def __setitem__(self, i, v):
                if   i == 0: self.x0 = v
                elif i == 1: self.y0 = v
                elif i == 2: self.x1 = v
                elif i == 3: self.y1 = v
                else:
                    raise IndexError("list index out of range")
                return

            def __len__(self):
                return 4

            def __repr__(self):
                return "fitz.IRect" + str((self.x0, self.y0, self.x1, self.y1))
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
    int interpolate;
    int xres, yres;
    %extend {
        FITZEXCEPTION(fz_pixmap_s, !result)
        //---------------------------------------------------------------------
        // create empty pixmap with colorspace and IRect
        //---------------------------------------------------------------------
        fz_pixmap_s(struct fz_colorspace_s *cs, const struct fz_irect_s *bbox, int alpha = 0)
        {
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx)
                pm = fz_new_pixmap_with_bbox(gctx, cs, bbox, alpha);
            fz_catch(gctx) return NULL;
            return pm;
        }

        //---------------------------------------------------------------------
        // create pixmap as converted copy of another one
        // New in v1.11: option to remove alpha
        //---------------------------------------------------------------------
        fz_pixmap_s(struct fz_colorspace_s *cs, struct fz_pixmap_s *spix, int alpha = 1)
        {
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx)
            {
                pm = fz_convert_pixmap(gctx, spix, cs, alpha);
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
            struct fz_pixmap_s *pm = NULL;
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
                if (size == 0) THROWMSG("type(samples) invalid");
                if (stride * h != size) THROWMSG("len(samples) invalid");
                pm = fz_new_pixmap_with_data(gctx, cs, w, h, alpha, stride, data);
            }
            fz_catch(gctx) return NULL;
            return pm;
        }

        //---------------------------------------------------------------------
        // create pixmap from filename
        //---------------------------------------------------------------------
        fz_pixmap_s(char *filename)
        {
            struct fz_image_s *img = NULL;
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx) {
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
            struct fz_image_s *img = NULL;
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx)
            {
                if (size == 0)
                    THROWMSG("type(imagedata) invalid");
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
            struct fz_image_s *img = NULL;
            struct fz_pixmap_s *pix = NULL;
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
                    THROWMSG("xref entry is not an image");
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

        ~fz_pixmap_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free pixmap ... ");
#endif
            fz_drop_pixmap(gctx, $self);
#ifdef MEMDEBUG
            fprintf(stderr, "done!\n");
#endif
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
            fz_copy_pixmap_rect(gctx, $self, src, bbox);
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
        // writePNG
        //----------------------------------------------------------------------
        FITZEXCEPTION(writePNG, result)
        %pythonprepend writePNG %{
            if type(filename) == str:
                pass
            elif type(filename) == unicode:
                filename = filename.encode('utf8')
            else:
                raise TypeError("filename must be a string")
            if not filename.lower().endswith(".png"):
                raise ValueError("filename must end with '.png'")
        %}
        int writePNG(char *filename, int savealpha=-1)
        {
            if (savealpha != -1) fz_warn(gctx, "ignoring savealpha");
            fz_try(gctx) {
                fz_save_pixmap_as_png(gctx, $self, filename);
            }
            fz_catch(gctx) return 1;
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

        ~fz_colorspace_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free colorspace ... ");
#endif
            fz_drop_colorspace(gctx, $self);
#ifdef MEMDEBUG
            fprintf(stderr, "done!\n");
#endif
        }
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
        DeviceWrapper(struct fz_stext_sheet_s *ts, struct fz_stext_page_s *tp) {
            struct DeviceWrapper *dw = NULL;
            fz_try(gctx) {
                dw = (struct DeviceWrapper *)calloc(1, sizeof(struct DeviceWrapper));
                dw->device = fz_new_stext_device(gctx, ts, tp, 0);
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
            return fz_copy_matrix(m, n);
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
        // create matrix from Python list
        //--------------------------------------------------------------------
        fz_matrix_s(PyObject *list)
        {
            fz_matrix *m = (fz_matrix *)malloc(sizeof(fz_matrix));
            fz_try(gctx)
            {
                if (!PySequence_Check(list)) THROWMSG("expected a sequence");
                if (PySequence_Size(list) != 6) THROWMSG("sequence length must be 6");
                m->a = (float) PyFloat_AsDouble(PySequence_GetItem(list, 0));
                m->b = (float) PyFloat_AsDouble(PySequence_GetItem(list, 1));
                m->c = (float) PyFloat_AsDouble(PySequence_GetItem(list, 2));
                m->d = (float) PyFloat_AsDouble(PySequence_GetItem(list, 3));
                m->e = (float) PyFloat_AsDouble(PySequence_GetItem(list, 4));
                m->f = (float) PyFloat_AsDouble(PySequence_GetItem(list, 5));
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
                    raise IndexError("list index out of range")
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
        FITZEXCEPTION(saveXML, result)
        %pythonprepend saveXML(const char *filename) %{
            if type(filename) == str:
                pass
            elif type(filename) == unicode:
                filename = filename.encode('utf8')
            else:
                raise TypeError("filename must be a string")
        %}
        int saveXML(const char *filename) {
            struct fz_output_s *xml;
            fz_try(gctx) {
                xml = fz_new_output_with_path(gctx, filename, 0);
                fz_print_outline_xml(gctx, xml, $self);
                fz_drop_output(gctx, xml);
            }
            fz_catch(gctx) return 1;
            return 0;
        }
        FITZEXCEPTION(saveText, result)
        %pythonprepend saveText(const char *filename) %{
            if type(filename) == str:
                pass
            elif type(filename) == unicode:
                filename = filename.encode('utf8')
            else:
                raise TypeError("filename must be a string")
        %}
        int saveText(const char *filename) {
            int res = 1;
            struct fz_output_s *text;
            fz_try(gctx) {
                text = fz_new_output_with_path(gctx, filename, 0);
                fz_print_outline(gctx, text, $self);
                fz_drop_output(gctx, text);
                res = 0;
            }
            fz_catch(gctx) return 1;
            return res;
        }
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
            *p = *q;
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
                if (PySequence_Size(list) != 2) THROWMSG("sequence length must be 2");
                p->x = (float) PyFloat_AsDouble(PySequence_GetItem(list, 0));
                p->y = (float) PyFloat_AsDouble(PySequence_GetItem(list, 1));
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
                if (!c) THROWMSG("type(ap) invalid");
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
                annot->changed = 1;
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
                annot->changed = 1;
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
            if (pdf_is_name(gctx, o)) lstart = pdf_to_name(gctx, o);
            else if (pdf_is_array(gctx, o))
                {
                lstart = pdf_to_name(gctx, pdf_array_get(gctx, o, 0));
                if (pdf_array_len(gctx, o) > 1)
                    lend   = pdf_to_name(gctx, pdf_array_get(gctx, o, 1));
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
                annot->changed = 1;
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
            PyObject *res = PyList_New(0);            // create Python list
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (!annot) return res;                   // not a PDF
            int type = (int) pdf_annot_type(gctx, annot);
            PyList_Append(res, PyInt_FromLong((long) type));
            char *c = annot_type_str(type);
            PyObject *cpy = PyUnicode_DecodeUTF8(c, strlen(c), "strict");
            PyList_Append(res, cpy);
            pdf_obj *o = pdf_dict_gets(gctx, annot->obj, "IT");
            if (!o) return res;                       // no IT entry
            if (pdf_is_name(gctx, o))
                {
                c = pdf_to_name(gctx, o);
                cpy = PyUnicode_DecodeUTF8(c, strlen(c), "strict");
                PyList_Append(res, cpy);
                }
            return res;
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
                if (!stream) THROWMSG("bad PDF: attached file has no stream");
                f = getPDFstr(filename, &file_len, "filename");
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
            if (o) c = pdf_to_name(gctx, o);
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
                    THROWMSG("info not a Python dict");
                if (!dictvalid)
                    THROWMSG("invalid key in info dict");

                // contents
                value = PyDict_GetItemString(info, "content");
                if (value)
                    {
                    uc = getPDFstr(value, &i, "content");
                    if (!uc) return -1;
                    pdf_dict_put_drop(gctx, annot->obj, PDF_NAME_Contents,
                                      pdf_new_string(gctx, pdf, uc, i));
                    }

                // title (= author)
                value = PyDict_GetItemString(info, "title");
                if (value)
                    {
                    uc = getPDFstr(value, &i, "title");
                    if (!uc) return -1;
                    pdf_dict_put_drop(gctx, annot->obj, PDF_NAME_T,
                                      pdf_new_string(gctx, pdf, uc, i));
                    }

                // creation date
                value = PyDict_GetItemString(info, "creationDate");
                if (value)
                    {
                    uc = getPDFstr(value, &i, "creationDate");
                    if (!uc) return -1;
                    pdf_dict_puts_drop(gctx, annot->obj, "CreationDate",
                                       pdf_new_string(gctx, pdf, uc, i));
                    }

                // mod date
                value = PyDict_GetItemString(info, "modDate");
                if (value)
                    {
                    uc = getPDFstr(value, &i, "modDate");
                    if (!uc) return -1;
                    pdf_dict_put_drop(gctx, annot->obj, PDF_NAME_M,
                                      pdf_new_string(gctx, pdf, uc, i));
                    }

                // subject
                value = PyDict_GetItemString(info, "subject");
                if (value)
                    {
                    uc = getPDFstr(value, &i, "subject");
                    if (!uc) return -1;
                    pdf_dict_puts_drop(gctx, annot->obj, "Subj",
                                       pdf_new_string(gctx, pdf, uc, i));
                    }
            }
            fz_catch(gctx) return -1;
            annot->changed = 1;
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
                    style = pdf_to_name(gctx, o);
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
                if (o) effect2 = pdf_to_name(gctx, o);
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

        /**********************************************************************/
        // set annotation border (destroys any /BE or /BS entries)
        // Argument 'border' must be number or dict.
        // Width and dashes may both be modified.
        /**********************************************************************/
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
            annot->changed = 1;
            return 0;
        }

        /**********************************************************************/
        // annotation flags
        /**********************************************************************/
        PARENTCHECK(flags)
        %pythoncode %{@property%}
        int flags()
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (annot) return pdf_annot_flags(gctx, annot);
            return -1;
        }

        /**********************************************************************/
        // set annotation flags
        /**********************************************************************/
        PARENTCHECK(setFlags)
        void setFlags(int flags)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (annot)
                {
                pdf_set_annot_flags(gctx, annot, flags);
                annot->changed = 1;
                }
        }

        /**********************************************************************/
        // next annotation
        /**********************************************************************/
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

        /**********************************************************************/
        // annotation pixmap
        /**********************************************************************/
        FITZEXCEPTION(getPixmap, !result)
        PARENTCHECK(getPixmap)
        struct fz_pixmap_s *getPixmap(struct fz_matrix_s *matrix = NULL, struct fz_colorspace_s *colorspace = NULL, int alpha = 0)
        {
            struct fz_matrix_s *ctm = NULL;
            struct fz_colorspace_s *cs = NULL;
            fz_pixmap *pix = NULL;

            if (matrix) ctm = matrix;
            else ctm = &fz_identity;

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
                raise RuntimeError("orphaned object: parent is None")
            if self.parent.parent.isClosed:
                raise RuntimeError("operation illegal for closed doc")
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
    %extend {
        FITZEXCEPTION(fz_display_list_s, !result)
        fz_display_list_s(struct fz_rect_s *mediabox)
        {
            struct fz_display_list_s *dl = NULL;
            fz_try(gctx)
                dl = fz_new_display_list(gctx, mediabox);
            fz_catch(gctx) return NULL;
            return dl;
        }

        ~fz_display_list_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free display list\n");
#endif
            fz_drop_display_list(gctx, $self);
        }
        FITZEXCEPTION(run, result)
        int run(struct DeviceWrapper *dw, const struct fz_matrix_s *m, const struct fz_rect_s *area) {
            fz_try(gctx) {
                fz_run_display_list(gctx, $self, dw->device, m, area, NULL);
            }
            fz_catch(gctx) return 1;
            return 0;
        }
    }
};

/*****************************************************************************/
// fz_stext_sheet
/*****************************************************************************/
%rename(TextSheet) fz_stext_sheet_s;
struct fz_stext_sheet_s {
    %extend {
        FITZEXCEPTION(fz_stext_sheet_s, !result)
        fz_stext_sheet_s() {
            struct fz_stext_sheet_s *ts = NULL;
            fz_try(gctx)
                ts = fz_new_stext_sheet(gctx);
            fz_catch(gctx) return NULL;
            return ts;
        }

        ~fz_stext_sheet_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free text sheet\n");
#endif
            fz_drop_stext_sheet(gctx, $self);
        }
    }
};

/*****************************************************************************/
// fz_stext_page
/*****************************************************************************/
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
    int len;
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
        /*******************************************/
        // method search()
        /*******************************************/
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
        /*******************************************/
        /* method extractText()                    */
        /*******************************************/
        FITZEXCEPTION(extractText, !result)
        %newobject extractText;
        const char *extractText() {
            struct fz_buffer_s *res = NULL;
            fz_output *out;
            fz_try(gctx) {
                /* inital size for text */
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                fz_print_stext_page(gctx, out, $self);
            }
            fz_always(gctx) fz_drop_output(gctx, out);
            fz_catch(gctx) return NULL;
            return fz_string_from_buffer(gctx, res);
        }
        /*******************************************/
        /* method extractXML()                     */
        /*******************************************/
        FITZEXCEPTION(extractXML, !result)
        %newobject extractXML;
        const char *extractXML() {
            struct fz_buffer_s *res = NULL;
            fz_output *out;
            fz_try(gctx) {
                /* inital size for text */
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                fz_print_stext_page_xml(gctx, out, $self);
            }
            fz_always(gctx) fz_drop_output(gctx, out);
            fz_catch(gctx) return NULL;
            return fz_string_from_buffer(gctx, res);
        }
        /*******************************************/
        /* method extractHTML()                    */
        /*******************************************/
        FITZEXCEPTION(extractHTML, !result)
        %newobject extractHTML;
        const char *extractHTML() {
            struct fz_buffer_s *res = NULL;
            fz_output *out;
            fz_try(gctx) {
                /* inital size for text */
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                fz_print_stext_page_html(gctx, out, $self);
            }
            fz_always(gctx) fz_drop_output(gctx, out);
            fz_catch(gctx) return NULL;
            return fz_string_from_buffer(gctx, res);
        }
        //---------------------------------------------------------------------
        // method extractJSON()
        //---------------------------------------------------------------------
        FITZEXCEPTION(extractJSON, !result)
        %newobject extractJSON;
        const char *extractJSON() {
            struct fz_buffer_s *res = NULL;
            fz_output *out;
            fz_try(gctx) {
                /* inital size for text */
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                fz_print_stext_page_json(gctx, out, $self);
            }
            fz_always(gctx) fz_drop_output(gctx, out);
            fz_catch(gctx) return NULL;
            return fz_string_from_buffer(gctx, res);
        }
    }
};
