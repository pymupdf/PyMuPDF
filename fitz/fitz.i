%module fitz
//=============================================================================
// SWIG macro: generate fitz exceptions
//=============================================================================
%define FITZEXCEPTION(meth, cond)
        %exception meth
        {
            $action
            if(cond) {
                PyErr_SetString(PyExc_Exception, gctx->error->message);
                return NULL;
            }
        }
%enddef
//=============================================================================

//=============================================================================
// SWIG macro: check that a document is not closed
//=============================================================================
%define CLOSECHECK(meth, cond)
%pythonprepend meth
%{if hasattr(self, "parent") and self.parent is None:
    raise RuntimeError("orphaned object: parent is None")
if cond:
    raise RuntimeError("operation illegal for closed doc")%}
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
%pythoncode %{import weakref%}
%include version.i
%include linkDest.i
%include helpers.i

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
        CLOSECHECK(loadPage, self.isClosed)
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

        CLOSECHECK(_loadOutline, self.isClosed)
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

        CLOSECHECK(pageCount, self.isClosed)
        %pythoncode%{@property%}
        int pageCount() {
            return fz_count_pages(gctx, $self);
        }

        CLOSECHECK(_getMetadata, self.isClosed)
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

        CLOSECHECK(needsPass, self.isClosed)
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

        CLOSECHECK(authenticate, self.isClosed)
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
                raise ValueError("incremental save requires original file")
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

        %feature("autodoc","insertPDF(PDFsrc, from_page, to_page, start_at, rotate, links) -> int\nInsert page range [from, to] of source PDF, starting as page number start_at.") insertPDF;

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
        CLOSECHECK(deletePage, self.isClosed)
        %feature("autodoc","deletePage(pno) -> int\ndelete page pno from the PDF") deletePage;
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
        CLOSECHECK(deletePageRange, self.isClosed)
        %feature("autodoc","deletePageRange(from_page, to_page) -> int\ndelete page range from the PDF") deletePageRange;
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
        // Copy a page from a PDF to another location of it
        //*********************************************************************
        FITZEXCEPTION(copyPage, result<0)
        CLOSECHECK(copyPage, self.isClosed)
        %feature("autodoc","copyPage(pno, to=-1) -> int\ncopy a page within a PDF") copyPage;
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

        //*********************************************************************
        // Move a page from a PDF to another location of it
        //*********************************************************************
        FITZEXCEPTION(movePage, result<0)
        CLOSECHECK(movePage, self.isClosed)
        %feature("autodoc","movePage(pno, to=-1) -> int\nmove a page within a PDF") movePage;
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

        //*********************************************************************
        // Create sub-document to keep only selected pages.
        // Parameter is a Python list of the wanted page numbers.
        //*********************************************************************
        FITZEXCEPTION(select, result<0)
        %feature("autodoc","select(list) -> int; build sub-pdf with pages in list") select;
        CLOSECHECK(select, self.isClosed)
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
        %feature("autodoc","permissions -> dictionary containing permissions") permissions;
        CLOSECHECK(permissions, self.isClosed)
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
        CLOSECHECK(_getPageObjNumber, self.isClosed)
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
        CLOSECHECK(getPageImageList, self.isClosed)
        %feature("autodoc","getPageImageList(pno) -> int\nlist images used on a PDF page") getPageImageList;
        PyObject *getPageImageList(int pno)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            int pageCount = fz_count_pages(gctx, $self);
            int n = pno;
            while (n < 0) n += pageCount;
            fz_try(gctx)
            {
                if (n >= pageCount)
                    THROWMSG("page number out of range");
                assert_PDF(pdf);
            }
            fz_catch(gctx) return NULL;
            PyObject *imglist = PyList_New(0);        // resulting Python list
            pdf_obj *pageref = pdf_lookup_page_obj(gctx, pdf, n);
            pdf_obj *pageobj = pdf_resolve_indirect(gctx, pageref);
            pdf_obj *rsrc = pdf_dict_get(gctx, pageobj, PDF_NAME_Resources);
            pdf_obj *dict = pdf_dict_get(gctx, rsrc, PDF_NAME_XObject);
            n = pdf_dict_len(gctx, dict);
            int i;
            for (i = 0; i < n; i++)       // do this for each img of the page
            {
                pdf_obj *imagedict, *type, *altcs, *o, *cs;
                PyObject *xref, *gen, *width, *height, *bpc, *cs_py, *altcs_py;

                imagedict = pdf_dict_get_val(gctx, dict, i);
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

                PyObject *img = PyList_New(0);         /* Python list per img */
                PyList_Append(img, xref);
                PyList_Append(img, gen);
                PyList_Append(img, width);
                PyList_Append(img, height);
                PyList_Append(img, bpc);
                PyList_Append(img, cs_py);
                PyList_Append(img, altcs_py);
                PyList_Append(imglist, img);
            }
            return imglist;
        }

        //*********************************************************************
        // Returns the fonts used on a page as a nested list of lists.
        // Each font entry contains [xref#, gen#, type, basename, name]
        //*********************************************************************
        FITZEXCEPTION(getPageFontList, result==NULL)
        CLOSECHECK(getPageFontList, self.isClosed)
        %feature("autodoc","getPageFontList(pno) -> int\nlist fonts used on a PDF page") getPageFontList;
        PyObject *getPageFontList(int pno)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            int pageCount = fz_count_pages(gctx, $self);
            int n = pno;
            while (n < 0) n += pageCount;
            fz_try(gctx)
            {
                if (n >= pageCount)
                    THROWMSG("page number out of range");
                assert_PDF(pdf);
            }
            fz_catch(gctx) return NULL;

            PyObject *fontlist = PyList_New(0);  // Python list to be returned
            pdf_obj *pageref = pdf_lookup_page_obj(gctx, pdf, n);
            pdf_obj *pageobj = pdf_resolve_indirect(gctx, pageref);
            pdf_obj *rsrc = pdf_dict_get(gctx, pageobj, PDF_NAME_Resources);
            pdf_obj *dict = pdf_dict_get(gctx, rsrc, PDF_NAME_Font);
            n = pdf_dict_len(gctx, dict);
            int i;
            for (i = 0; i < n; i++)      /* do this for each font of the page */
            {
                pdf_obj *fontdict = NULL;
                pdf_obj *subtype = NULL;
                pdf_obj *basefont = NULL;
                pdf_obj *name = NULL;
                pdf_obj *bname = NULL;
                fontdict = pdf_dict_get_val(gctx, dict, i);
                if (!pdf_is_dict(gctx, fontdict)) continue;  // no valid font on page
                long xref = (long) pdf_to_num(gctx, fontdict);
                long gen  = (long) pdf_to_gen(gctx, fontdict);
                subtype = pdf_dict_get(gctx, fontdict, PDF_NAME_Subtype);
                basefont = pdf_dict_get(gctx, fontdict, PDF_NAME_BaseFont);
                if (!basefont || pdf_is_null(gctx, basefont))
                    bname = pdf_dict_get(gctx, fontdict, PDF_NAME_Name);
                else
                    bname = basefont;
                name = pdf_dict_get(gctx, fontdict, PDF_NAME_Name);
                PyObject *font = PyList_New(0);       // Python list per font
                PyList_Append(font, PyInt_FromLong(xref));
                PyList_Append(font, PyInt_FromLong(gen));
                PyList_Append(font, PyBytes_FromString(pdf_to_name(gctx, subtype)));
                PyList_Append(font, PyBytes_FromString(pdf_to_name(gctx, bname)));
                PyList_Append(font, PyBytes_FromString(pdf_to_name(gctx, name)));
                PyList_Append(fontlist, font);
            }
            return fontlist;
        }

        //*********************************************************************
        // Delete all bookmarks (table of contents)
        // returns the list of deleted (freed = now available) xref numbers
        //*********************************************************************
        CLOSECHECK(_delToC, self.isClosed)
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
        CLOSECHECK(_getOLRootNumber, self.isClosed)
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
        CLOSECHECK(_getNewXref, self.isClosed)
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
        FITZEXCEPTION(_getXrefLength, result<0)
        CLOSECHECK(_getXrefLength, self.isClosed)
        int _getXrefLength()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); // get pdf doc
            fz_try(gctx) assert_PDF(pdf);
            fz_catch(gctx) return -2;
            return pdf_xref_len(gctx, pdf);
        }

        //*********************************************************************
        // Get bare text inside a rectangle of a page
        //*********************************************************************
        FITZEXCEPTION(_getPageRectText, !result)
        CLOSECHECK(_getPageRectText, self.isClosed)
        char *_getPageRectText(int pno, struct fz_rect_s *rect)
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
        CLOSECHECK(_delXmlMetadata, self.isClosed)
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
        FITZEXCEPTION(_getObjectString, result==NULL)
        CLOSECHECK(_getObjectString, self.isClosed)
        const char *_getObjectString(int xnum)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); // conv doc to pdf
            pdf_obj *obj;
            struct fz_buffer_s *res = NULL;
            fz_output *out;
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if ((xnum < 1) | (xnum >= xreflen))
                    THROWMSG("xnum out of range");
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                obj = pdf_load_object(gctx, pdf, xnum);
                pdf_print_obj(gctx, out, pdf_resolve_indirect(gctx, obj), 1);
            }
            fz_always(gctx)
            {
                if (obj) pdf_drop_obj(gctx, obj);
                if (out) fz_drop_output(gctx, out);
            }
            fz_catch(gctx) return NULL;
            return fz_string_from_buffer(gctx, res);
        }

        /*********************************************************************/
        // Get decompressed stream of an object by xref
        // Throws exception if not a stream.
        /*********************************************************************/
        FITZEXCEPTION(_getXrefStream, !result)
        CLOSECHECK(_getXrefStream, self.isClosed)
        PyObject *_getXrefStream(int xnum)
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
                if ((xnum < 1) | (xnum >= xreflen))
                    THROWMSG("xnum out of range");
                res = pdf_load_stream_number(gctx, pdf, xnum);
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
        CLOSECHECK(_updateObject, self.isClosed)
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

        //*********************************************************************
        // Add or update metadata based on provided raw string
        //*********************************************************************
        FITZEXCEPTION(_setMetadata, result>0)
        CLOSECHECK(_setMetadata, self.isClosed)
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
                    raise IndexError
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

        CLOSECHECK(bound, self.parent.isClosed)
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
        CLOSECHECK(run, self.parent.isClosed)
        int run(struct DeviceWrapper *dw, const struct fz_matrix_s *m)
        {
            fz_try(gctx) fz_run_page(gctx, $self, dw->device, m, NULL);
            fz_catch(gctx) return 1;
            return 0;
        }

        /***********************************************************/
        // loadLinks()
        /***********************************************************/
        CLOSECHECK(loadLinks, self.parent.isClosed)
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
        CLOSECHECK(firstAnnot, self.parent.isClosed)
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
        CLOSECHECK(deleteLink, self.parent.isClosed)
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
        CLOSECHECK(deleteAnnot, self.parent.isClosed)
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
            // pdf_delete_annot(gctx, page, pannot);
            delete_annot(gctx, page, pannot);
            if (nextannot) fz_keep_annot(gctx, nextannot);
            return nextannot;
        }

        /*********************************************************************/
        // rotation - return page rotation
        /*********************************************************************/
        CLOSECHECK(rotation, self.parent.isClosed)
        %pythoncode %{@property%}
        %feature("autodoc","rotation -> int\nReturn rotation in degrees") rotation;
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
        CLOSECHECK(setRotation, self.parent.isClosed)
        %feature("autodoc","setRotation sets page rotation to 'rot' degrees") setRotation;
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
        CLOSECHECK(_addAnnot_FromString, self.parent.isClosed)
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

        //*********************************************************************
        // Get bare text inside a rectangle of a page
        //*********************************************************************
        FITZEXCEPTION(_getRectText, !result)
        CLOSECHECK(_getRectText, self.parent.isClosed)
        char *_getRectText(struct fz_rect_s *rect)
        {
            fz_buffer *res;
            fz_try(gctx)
            {
                res = fz_new_buffer_from_page(gctx, $self, rect, 0, NULL);
            }
            fz_catch(gctx) return NULL;
            return fz_string_from_buffer(gctx, res);
        }

        /*********************************************************************/
        // Page._readPageText()
        /*********************************************************************/
        FITZEXCEPTION(_readPageText, result==NULL)
        %newobject _readPageText;
        char *_readPageText(int output=0) {
            char *res;
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
                if (PySequence_Size(list) != 4) THROWMSG("sequence length must be 4");
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
        struct fz_irect_s *round() {
            fz_irect *irect = (fz_irect *)malloc(sizeof(fz_irect));
            fz_round_rect(irect, $self);
            return irect;
        }

        %feature("autodoc","Enlarge to include a 'Point' p") includePoint;
        struct fz_rect_s *includePoint(const struct fz_point_s *p) {
            fz_include_point_in_rect($self, p);
            return $self;
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
        void normalize()
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
            return;
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
        void normalize()
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
            return;
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
%feature("autodoc", "fitz.Pixmap(cs, width, height, samples, alpha)\nfitz.Pixmap(cs, fitz.Irect, alpha)\nfitz.Pixmap(cs, fitz.Pixmap)\nfitz.Pixmap(filename)\nfitz.Pixmap(bytearray)\nfitz.Pixmap(doc, xref)") fz_pixmap_s;struct fz_pixmap_s
{
    int x, y, w, h, n;
    int interpolate;
    int xres, yres;
    %extend {
        FITZEXCEPTION(fz_pixmap_s, !result)
        /***********************************************************/
        /* create empty pixmap with colorspace and IRect specified */
        /***********************************************************/
        fz_pixmap_s(struct fz_colorspace_s *cs, const struct fz_irect_s *bbox, int alpha = 0)
        {
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx)
                pm = fz_new_pixmap_with_bbox(gctx, cs, bbox, alpha);
            fz_catch(gctx) return NULL;
            return pm;
        }

        /***********************************************************/
        // create new pixmap as converted copy of another one
        /***********************************************************/
        fz_pixmap_s(struct fz_colorspace_s *cs, struct fz_pixmap_s *spix)
        {
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx)
            {
                pm = fz_new_pixmap(gctx, cs, spix->w, spix->h, spix->alpha);
                pm->x = 0;
                pm->y = 0;
                fz_convert_pixmap(gctx, pm, spix);
            }
            fz_catch(gctx) return NULL;
            return pm;
        }

        /***********************************************************/
        // create a pixmap from samples data
        /***********************************************************/
        fz_pixmap_s(struct fz_colorspace_s *cs, int w, int h, PyObject *samples, int alpha = 0)
        {
            char *data;
            size_t size = 0;
            int n = fz_colorspace_n(gctx, cs);
            int stride = (n + alpha)*w;
            if (PyByteArray_Check(samples)){
                data = PyByteArray_AsString(samples);
                size = (size_t) PyByteArray_Size(samples);
            }
            else if (PyBytes_Check(samples)){
                data = PyBytes_AsString(samples);
                size = (size_t) PyBytes_Size(samples);
            }
            fz_try(gctx) {
                if (size == 0)
                    THROWMSG("type(samples) invalid");
                if (stride * h != size) {
                    THROWMSG("len(samples) invalid");
                    }
                }
            fz_catch(gctx) return NULL;

            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx)
                pm = fz_new_pixmap_with_data(gctx, cs, w, h, alpha, stride, data);

            fz_catch(gctx) return NULL;

            return pm;
        }

        /******************************************/
        // create a pixmap from filename
        /******************************************/
        fz_pixmap_s(char *filename)
        {
            struct fz_image_s *img = NULL;
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx) {
                img = fz_new_image_from_file(gctx, filename);
                pm = fz_get_pixmap_from_image(gctx, img, NULL, NULL, NULL, NULL);
            }
            fz_catch(gctx) return NULL;
            fz_drop_image(gctx, img);
            return pm;
        }

        /*********************************************************************/
        // create a pixmap from bytes / bytearray
        /*********************************************************************/
        fz_pixmap_s(PyObject *imagedata)
        {
            size_t size;
            size = 0;
            char *data;
            if (PyByteArray_Check(imagedata))
            {
                data = PyByteArray_AsString(imagedata);
                size = (size_t) PyByteArray_Size(imagedata);
            }
            else if (PyBytes_Check(imagedata))
            {
                data = PyBytes_AsString(imagedata);
                size = (size_t) PyBytes_Size(imagedata);
            }
            struct fz_image_s *img = NULL;
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx)
            {
                if (size == 0)
                    THROWMSG("type(imagedata) invalid");
                img = fz_new_image_from_data(gctx, data, size);
                pm = fz_get_pixmap_from_image(gctx, img, NULL, NULL, NULL, NULL);
            }
            fz_always(gctx) if (img) fz_drop_image(gctx, img);
            fz_catch(gctx) return NULL;
            return pm;
        }

        /***********************************************************************
        Create pixmap from an image identified by XREF number
        ***********************************************************************/
        fz_pixmap_s(struct fz_document_s *doc, int xref)
        {
            struct fz_image_s *img = NULL;
            struct fz_pixmap_s *pix = NULL;
            pdf_obj *ref = NULL;
            pdf_document *pdf = pdf_specifics(gctx, doc);
            fz_try(gctx)
            {
                assert_PDF(pdf);
                int xreflen = pdf_xref_len(gctx, pdf);
                if ((xref < 1) | (xref >= xreflen))
                    THROWMSG("xref out of range");
                ref = pdf_new_indirect(gctx, pdf, xref, 0);
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

        /*********************************/
        /* clear total pixmap with value */
        /*********************************/
        void clearWith(int value)
        {
            fz_clear_pixmap_with_value(gctx, $self, value);
        }

        /*************************************/
        /* clear pixmap rectangle with value */
        /*************************************/
        void clearWith(int value, const struct fz_irect_s *bbox)
        {
            fz_clear_pixmap_rect_with_value(gctx, $self, value, bbox);
        }

        /***********************************/
        /* copy pixmaps                    */
        /***********************************/
        void copyPixmap(struct fz_pixmap_s *src, const struct fz_irect_s *bbox)
        {
            fz_copy_pixmap_rect(gctx, $self, src, bbox);
        }

        /*********************************************************************/
        // get length of one image row
        /*********************************************************************/
        %pythoncode %{@property%}
        int stride()
        {
            return fz_pixmap_stride(gctx, $self);
        }

        /*********************************************************************/
        // check alpha channel
        /*********************************************************************/
        %pythoncode %{@property%}
        int alpha()
        {
            return $self->alpha;
        }

        /*********************************************************************/
        // get colorspace of pixmap
        /*********************************************************************/
        %pythoncode %{@property%}
        struct fz_colorspace_s *colorspace()
        {
            return fz_pixmap_colorspace(gctx, $self);
        }

        /*********************************************************************/
        // get irect of pixmap
        /*********************************************************************/
        %pythoncode %{@property%}
        struct fz_irect_s *irect()
        {
            fz_irect *r = (fz_irect *)malloc(sizeof(fz_irect));
            r->x0 = 0;
            r->y0 = 0;
            r->x1 = 0;
            r->y1 = 0;
            return fz_pixmap_bbox(gctx, $self, r);
        }

        /**********************/
        /* get size of pixmap */
        /**********************/
        %pythoncode %{@property%}
        int size()
        {
            return (int) fz_pixmap_size(gctx, $self);
        }

        /**********************/
        /* writePNG           */
        /**********************/
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
            if (savealpha >= 0) fz_warn(gctx, "ignoring savealpha");
            fz_try(gctx) {
                fz_save_pixmap_as_png(gctx, $self, filename);
            }
            fz_catch(gctx) return 1;
            return 0;
        }

        /**********************/
        /* getPNGData         */
        /**********************/
        FITZEXCEPTION(getPNGData, !result)
        PyObject *getPNGData(int savealpha=-1)
        {
            struct fz_buffer_s *res = NULL;
            fz_output *out;
            unsigned char *c;
            PyObject *r;
            size_t len;
            if (savealpha >= 0) fz_warn(gctx, "ignoring savealpha");
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

        /************************/
        /* _writeIMG            */
        /************************/
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
            if (savealpha >= 0) fz_warn(gctx, "ignoring savealpha");
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

        /******************************/
        /* invertIRect (total pixmap) */
        /******************************/
        void invertIRect()
        {
            fz_invert_pixmap(gctx, $self);
        }
        /*************************/
        /* invertIRect           */
        /*************************/
        void invertIRect(const struct fz_irect_s *irect)
        {
            fz_invert_pixmap_rect(gctx, $self, irect);
        }

        PyObject *samples()
        {
            return PyByteArray_FromStringAndSize((const char *)$self->samples, ($self->w)*($self->h)*($self->n));
        }

        %pythoncode %{
            samples = property(samples)
            width  = w
            height = h

            def __len__(self):
                return self.size

            def __repr__(self):
                return "fitz.Pixmap(%s, %s, %s)" % (self.colorspace.name, self.irect, self.alpha)%}
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
/*****************************************************************************/
// number of bytes to define color of one pixel
/*****************************************************************************/
        %pythoncode %{@property%}
        int n()
        {
            return fz_colorspace_n(gctx, $self);
        }

/*****************************************************************************/
// name of colorspace
/*****************************************************************************/
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

/* fz_matrix */
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
                        return self.distance_to(r.bottom_right, unit = unit)
                    elif self.y <= r.y0:
                        return self.distance_to(r.top_right, unit = unit)
                    else:
                        return (self.x - r.x1) * f
                elif r.x0 <= self.x <= r.x1:
                    if self.y >= r.y1:
                        return (self.y - r.y1) * f
                    else:
                        return (r.y0 - self.y) * f
                else:
                    if self.y >= r.y1:
                        return self.distance_to(r.bottom_left, unit = unit)
                    elif self.y <= r.y0:
                        return self.distance_to(r.top_left, unit = unit)
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
        CLOSECHECK(rect, self.parent.parent.isClosed)
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
        CLOSECHECK(_getXref, self.parent.parent.isClosed)
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
        CLOSECHECK(_getAP, self.parent.parent.isClosed)
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
        CLOSECHECK(_setAP, self.parent.parent.isClosed)
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
        CLOSECHECK(setRect, self.parent.parent.isClosed)
        %feature("autodoc","setRect: changes the annot's rectangle") setRect;
        void setRect(struct fz_rect_s *r)
        {
            pdf_annot *annot = pdf_annot_from_fz_annot(gctx, $self);
            if (annot) pdf_set_annot_rect(gctx, annot, r);
        }

        /**********************************************************************/
        // annotation vertices (for "Line", "Polgon", "Ink", etc.
        /**********************************************************************/
        CLOSECHECK(vertices, self.parent.parent.isClosed)
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
        CLOSECHECK(colors, self.parent.parent.isClosed)
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
        CLOSECHECK(setColors, self.parent.parent.isClosed)
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
        CLOSECHECK(lineEnds, self.parent.parent.isClosed)
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
        CLOSECHECK(setLineEnds, self.parent.parent.isClosed)
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
        CLOSECHECK(type, self.parent.parent.isClosed)
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
        // annotation info
        /**********************************************************************/
        CLOSECHECK(info, self.parent.parent.isClosed)
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
        CLOSECHECK(setInfo, self.parent.parent.isClosed)
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
        CLOSECHECK(border, self.parent.parent.isClosed)
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
        CLOSECHECK(setBorder, self.parent.parent.isClosed)
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
        CLOSECHECK(flags, self.parent.parent.isClosed)
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
        CLOSECHECK(setFlags, self.parent.parent.isClosed)
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
        CLOSECHECK(next, self.parent.parent.isClosed)
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
        CLOSECHECK(getPixmap, self.parent.parent.isClosed)
        struct fz_pixmap_s *getPixmap(struct fz_matrix_s *matrix = NULL, struct fz_colorspace_s *colorspace = NULL, int alpha = 0)
        {
            struct fz_matrix_s *ctm;
            struct fz_colorspace_s *cs;
            fz_pixmap *pix;

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

        CLOSECHECK(uri, self.parent.parent.isClosed)
        %pythoncode %{@property%}
        char *uri()
        {
            return $self->uri;
        }

        CLOSECHECK(isExternal, self.parent.parent.isClosed)
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

        CLOSECHECK(rect, self.parent.parent.isClosed)
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
        CLOSECHECK(next, self.parent.parent.isClosed)
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
        /*******************************************/
        /* method extractJSON()                    */
        /*******************************************/
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
