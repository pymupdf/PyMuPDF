%module fitz
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
%define CLOSECHECK(meth, cond)
%pythonprepend meth
%{if cond:
    raise ValueError("illegal operation on closed / encrypted document")%}
%enddef
/*
#define MEMDEBUG
*/
%feature("autodoc","1");
%{
#define SWIG_FILE_WITH_INIT
#define SWIG_PYTHON_2_UNICODE
#include <fitz.h>
#include <pdf.h>

void fz_print_stext_page_json(fz_context *ctx, fz_output *out, fz_stext_page *page);

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

/* include version information and several helpers */
%include version.i
%include helpers.i

/*******************************************************************************
out-typemap: convert a return fz_buffer to string, then drop it
*******************************************************************************/
%typemap(out) struct fz_buffer_s * {
    $result = SWIG_FromCharPtrAndSize((const char *)$1->data, $1->len);
    fz_drop_buffer(gctx, $1);
}

/* fz_document */
%rename(Document) fz_document_s;
struct fz_document_s
{
    %extend
    {
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
                self.thisown = False
        %}

        fz_document_s(const char *filename = NULL, PyObject *stream=NULL)
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
            if (PyBytes_Check(stream))
            {
                streamdata = PyBytes_AsString(stream);
                streamlen = (size_t) PyBytes_Size(stream);
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
            fz_catch(gctx)
                return NULL;
            return doc;
        }

        %pythonprepend close() %{
            if self.isClosed == 1:
                raise ValueError("operation on closed document")
            if hasattr(self, '_outline') and self._outline:
                self._dropOutline(self._outline)
                self._outline = None
            self.metadata    = None
            self.isClosed    = 1
            self.openErrCode = 0
            self.openErrMsg  = ''
        %}
        void close()
        {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free doc\n");
#endif
            while($self->refs > 1) {
                fz_drop_document(gctx, $self);
            }
            fz_drop_document(gctx, $self);
        }

        FITZEXCEPTION(loadPage, result==NULL)
        CLOSECHECK(loadPage, self.isClosed)
        %pythonappend loadPage %{
            if val:
                val.thisown = True
                val.number = number
                val.parent = self
        %}
        struct fz_page_s *loadPage(int number)
        {
            struct fz_page_s *page = NULL;
            fz_try(gctx)
                page = fz_load_page(gctx, $self, number);
            fz_catch(gctx)
                return NULL;
            return page;
        }

        CLOSECHECK(_loadOutline, self.isClosed)
        struct fz_outline_s *_loadOutline()
        {
            return fz_load_outline(gctx, $self);
        }

        void _dropOutline(struct fz_outline_s *ol) {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free outline\n");
#endif
            fz_drop_outline(gctx, ol);
        }

        CLOSECHECK(_getPageCount, self.isClosed)
        int _getPageCount() {
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

        CLOSECHECK(_needsPass, self.isClosed)
        int _needsPass() {
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
        %}
        int authenticate(const char *pass) {
            return fz_authenticate_password(gctx, $self, pass);
        }
        /****************************************************************/
        /* save(filename, ...)                                          */
        /****************************************************************/
        FITZEXCEPTION(save, result!=0)
        %pythonprepend save(char *filename, int garbage=0, int clean=0, int deflate=0, int incremental=0, int ascii=0, int expand=0, int linear=0) %{
            if self.isClosed == 1:
                raise ValueError("operation on closed document")
            if type(filename) == str:
                pass
            elif type(filename) == unicode:
                filename = filename.encode('utf8')
            else:
                raise TypeError("filename must be a string")
            if filename == self.name and incremental == 0:
                raise ValueError("cannot save to input file")
            if len(self.name) > 0 and not self.name.lower().endswith("pdf"):
                raise ValueError("can only save PDF files")
            if incremental and (self.name != filename or self.streamlen > 0):
                raise ValueError("incremental save to original file only")
            if incremental and (garbage > 0 or linear > 0):
                raise ValueError("incremental excludes garbage and linear")
            if incremental and self.openErrCode > 0:
                raise ValueError("open error '%s' - save to new file" % (self.openErrMsg,))
            if incremental and self.needsPass > 0:
                raise ValueError("decrypted - save to new file")
        %}

        int save(char *filename, int garbage=0, int clean=0, int deflate=0, int incremental=0, int ascii=0, int expand=0, int linear=0)
        {
            /* cast-down fz_document to a pdf_document */
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) return -2;                 /* not a valid pdf structure */
            int errors = 0;
            pdf_write_options opts;
            opts.do_incremental = incremental;
            opts.do_ascii = ascii;
            opts.do_deflate = deflate;
            opts.do_expand = expand;
            opts.do_garbage = garbage;
            opts.do_linear = linear;
            opts.do_clean = clean;
            opts.continue_on_error = 0;
            opts.errors = &errors;
            fz_try(gctx)
                pdf_save_document(gctx, pdf, filename, &opts);
            fz_catch(gctx) {
                return gctx->error->errcode;
            }
            return 0;
        }


        /***********************************************************************
        Insert pages from a source PDF into this PDF.
        For reconstructing the links (_do_links method), we must save the
        insertion point (start_at) if it was specified as -1.
        ***********************************************************************/
        FITZEXCEPTION(insertPDF, result<0)
        CLOSECHECK(insertPDF, self.isClosed)
        %pythonprepend insertPDF %{
            sa = start_at
            if sa < 0:
                sa = self.pageCount
        %}

        %pythonappend insertPDF %{
            if links:
                self._do_links(docsrc, from_page = from_page, to_page = to_page,
                               start_at = sa)
        %}

        %feature("autodoc","insertPDF(PDFsrc, from_page, to_page, start_at, rotate, links) -> int\nInsert page range [from, to] of source PDF, starting as page number start_at.") insertPDF;

        int insertPDF(struct fz_document_s *docsrc, int from_page=-1, int to_page=-1, int start_at=-1, int rotate=-1, int links = 1)
        {
            pdf_document *pdfout = pdf_specifics(gctx, $self);
            pdf_document *pdfsrc = pdf_specifics(gctx, docsrc);
            int outCount = fz_count_pages(gctx, $self);
            int srcCount = fz_count_pages(gctx, docsrc);
            int fp, tp, sa;
            /* local copy of page specifications */
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
                if (pdfout == NULL)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "target document not a PDF");
                if (pdfsrc == NULL)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "source document not a PDF");
                merge_range(pdfout, pdfsrc, fp, tp, sa, rotate);
            }
            fz_catch(gctx){
                return -1;
            }
            return 0;
        }

        /***********************************************************************
        Delete a page from a PDF given by its number
        ***********************************************************************/
        FITZEXCEPTION(deletePage, result<0)
        CLOSECHECK(deletePage, self.isClosed or self.isEncrypted)
        int deletePage(int pno)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                if (pdf == NULL)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "not a pdf document");
                int pageCount = fz_count_pages(gctx, $self);
                if ((pno < 0) | (pno >= pageCount))
                    fz_throw(gctx, FZ_ERROR_GENERIC, "page number out of range");
                pdf_delete_page(gctx, pdf, pno);
            }
            fz_catch(gctx) {
                return -1;
            }
            return 0;
        }

        /***********************************************************************
        Delete a page range from a PDF
        ***********************************************************************/
        FITZEXCEPTION(deletePageRange, result<0)
        CLOSECHECK(deletePageRange, self.isClosed or self.isEncrypted)
        int deletePageRange(int from_page = -1, int to_page = -1)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                if (pdf == NULL)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
                int pageCount = fz_count_pages(gctx, $self);
                int f = from_page;
                int t = to_page;
                if (f < 0) f = pageCount - 1;
                if (t < 0) t = pageCount - 1;
                if ((t >= pageCount) | (f > t))
                    fz_throw(gctx, FZ_ERROR_GENERIC, "invalid page range");
                int i = t + 1 - f;
                while (i > 0)
                {
                    pdf_delete_page(gctx, pdf, f);
                    i -= 1;
                }
            }
            fz_catch(gctx) {
                return -1;
            }
            return 0;
        }

        /***********************************************************************
        Copy a page from a PDF to another location of it
        ***********************************************************************/
        FITZEXCEPTION(copyPage, result<0)
        CLOSECHECK(copyPage, self.isClosed or self.isEncrypted)
        int copyPage(int pno, int to = -1)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                if (pdf == NULL)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
                int pageCount = fz_count_pages(gctx, $self);
                if ((pno < 0) | (pno >= pageCount))
                    fz_throw(gctx, FZ_ERROR_GENERIC, "source page out of range");
                pdf_obj *page = pdf_lookup_page_obj(gctx, pdf, pno);
                pdf_insert_page(gctx, pdf, to, page);
            }
            fz_catch(gctx) {
                return -1;
            }
            return 0;
        }

        /***********************************************************************
        Move a page from a PDF to another location of it
        ***********************************************************************/
        FITZEXCEPTION(movePage, result<0)
        CLOSECHECK(movePage, self.isClosed or self.isEncrypted)
        int movePage(int pno, int to = -1)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                if (pdf == NULL)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
                int pageCount = fz_count_pages(gctx, $self);
                if ((pno < 0) | (pno >= pageCount))
                    fz_throw(gctx, FZ_ERROR_GENERIC, "source page out of range");
                int t = to;
                if (t < 0) t = pageCount;
                if ((t == pno) | (pno == t - 1))
                    fz_throw(gctx, FZ_ERROR_GENERIC, "source and target too close");
                pdf_obj *page = pdf_lookup_page_obj(gctx, pdf, pno);
                pdf_insert_page(gctx, pdf, t, page);
                if (pno < t)
                    pdf_delete_page(gctx, pdf, pno);
                else
                    pdf_delete_page(gctx, pdf, pno+1);
            }
            fz_catch(gctx) {
                return -1;
            }
            return 0;
        }

        /***********************************************************************
        Create sub-document to keep only selected pages.
        Parameter is a Python list of the wanted page numbers.
        ***********************************************************************/
        FITZEXCEPTION(select, result<0)
        %feature("autodoc","select(list) -> int; build sub-pdf with listed pages") select;
        CLOSECHECK(select, self.isClosed or self.isEncrypted)
        %pythonappend select %{
            self.initData()
        %}
        int select(PyObject *pyliste)
        {
            /* preparatory stuff:
            (1) get underlying pdf document,
            (2) transform Python list into integer array
            */
            /* get underlying pdf_document, do some parm checks ***************/
            pdf_document *pdf = pdf_specifics(gctx, $self);
            int argc;
            fz_try(gctx)
            {
                if (pdf == NULL)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "not a pdf document");
                if (!PySequence_Check(pyliste))
                    fz_throw(gctx, FZ_ERROR_GENERIC, "expected a sequence");
                argc = (int) PySequence_Size(pyliste);
                if (argc < 1)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "sequence is empty");
            }
            fz_catch(gctx) {
                return -1;
            }
            /* transform Python list into int array ***********************/
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
                            fz_throw(gctx, FZ_ERROR_GENERIC, "page numbers not in range");
                    }
                    else
                        fz_throw(gctx, FZ_ERROR_GENERIC, "page numbers must be integers");
                }
            }
            fz_catch(gctx)
            {
                if (liste) free (liste);
                return -1;
            }
            /* finally we call retainpages                                    */
            /* code of retainpages copied from fz_clean_file.c                */
            globals glo = { 0 };
            glo.ctx = gctx;
            glo.doc = pdf;
            retainpages(gctx, &glo, argc, liste);
            free (liste);
            return 0;
        }

        /***********************************************************************
        Extract the text of a page given its number.
        ***********************************************************************/
        FITZEXCEPTION(_readPageText, result==NULL)
        CLOSECHECK(_readPageText, self.isClosed)
        struct fz_buffer_s *_readPageText(int pno, int output=0)
        {
            fz_page *page;
            fz_buffer *res;
            fz_try(gctx)
            {
                page = fz_load_page(gctx, $self, pno);
                res = readPageText(page, output);
                fz_drop_page(gctx, page);
            }
            fz_catch(gctx)
            {
                if (page) fz_drop_page(gctx, page);
                if (res) fz_drop_buffer(gctx, res);
                return NULL;
            }
            return res;
        }

        /***************************************/
        /* get document permissions            */
        /***************************************/
        %feature("autodoc","getPermits(self) -> dictionary containing permissions") getPermits;
        CLOSECHECK(getPermits, self.isClosed or self.isEncrypted)
        %pythonappend getPermits %{
            # transform bitfield response into dictionary
            d = {}
            if val % 2: # print permission?
                d["print"] = True
            else:
                d["print"] = False
            val = val >> 1
            if val % 2: # edit permission?
                d["edit"] = True
            else:
                d["edit"] = False
            val = val >> 1
            if val % 2: # copy permission?
                d["copy"] = True
            else:
                d["copy"] = False
            val = val >> 1
            if val % 2: # annotate permission?
                d["note"] = True
            else:
                d["note"] = False
            val = d
        %}
        int getPermits()
        {
            int permit = 0;
            if (fz_has_permission(gctx, $self, FZ_PERMISSION_PRINT))    permit += 4;
            if (fz_has_permission(gctx, $self, FZ_PERMISSION_EDIT))     permit += 8;
            if (fz_has_permission(gctx, $self, FZ_PERMISSION_COPY))     permit += 16;
            if (fz_has_permission(gctx, $self, FZ_PERMISSION_ANNOTATE)) permit += 32;
            return permit>>2;
        }

        FITZEXCEPTION(_getPageObjNumber, result==NULL)
        CLOSECHECK(_getPageObjNumber, self.isClosed)
        PyObject *_getPageObjNumber(int pno)
        {
            /* cast-down fz_document to a pdf_document */
            int pageCount = fz_count_pages(gctx, $self);
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx)
            {
                if ((pno < 0) | (pno >= pageCount))
                    fz_throw(gctx, FZ_ERROR_GENERIC, "page number out of range");
                if (!pdf)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
            }
            fz_catch(gctx) {
                return NULL;
            }
            pdf_obj *pageref = pdf_lookup_page_obj(gctx, pdf, pno);
            long objnum = (long) pdf_to_num(gctx, pageref);
            long objgen = (long) pdf_to_gen(gctx, pageref);
            PyObject *res, *xrefnum_o, *gennum_o;
            res = PyList_New(2);                        /* create Python list */
            xrefnum_o = PyInt_FromLong(objnum);
            gennum_o  = PyInt_FromLong(objgen);
            PyList_SetItem(res, 0, xrefnum_o);
            PyList_SetItem(res, 1, gennum_o);
            return res;
        }

        /***********************************************************************
        Returns the images used on a page as a nested list of lists.
        Each image entry contains
        [xref#, gen#, width, height, bpc, colorspace, altcs]
        ***********************************************************************/
        FITZEXCEPTION(getPageImageList, result==NULL)
        CLOSECHECK(getPageImageList, self.isClosed)
        PyObject *getPageImageList(int pno)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            int pageCount = fz_count_pages(gctx, $self);
            fz_try(gctx)
            {
                if ((pno < 0) | (pno >= pageCount))
                    fz_throw(gctx, FZ_ERROR_GENERIC, "page number out of range");
                if (!pdf)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
            }
            fz_catch(gctx)
            {
                return NULL;
            }
            PyObject *imglist = PyList_New(0);        /* returned Python list */
            pdf_obj *pageref = pdf_lookup_page_obj(gctx, pdf, pno);
            pdf_obj *pageobj = pdf_resolve_indirect(gctx, pageref);
            pdf_obj *rsrc = pdf_dict_get(gctx, pageobj, PDF_NAME_Resources);
            pdf_obj *dict = pdf_dict_get(gctx, rsrc, PDF_NAME_XObject);
            int n = pdf_dict_len(gctx, dict);
            int i;
            for (i = 0; i < n; i++)       /* do this for each img of the page */
            {
                pdf_obj *imagedict;
                pdf_obj *type;
                pdf_obj *cs = NULL;
                pdf_obj *altcs;
                pdf_obj *o;

                imagedict = pdf_dict_get_val(gctx, dict, i);
                if (!pdf_is_dict(gctx, imagedict)) continue;

                type = pdf_dict_get(gctx, imagedict, PDF_NAME_Subtype);
                if (!pdf_name_eq(gctx, type, PDF_NAME_Image)) continue;

                long xref = (long) pdf_to_num(gctx, imagedict);
                long gen  = (long) pdf_to_gen(gctx, imagedict);
                PyObject *xref_py = PyInt_FromLong(xref);      /* xref number */
                PyObject *gen_py  = PyInt_FromLong(gen);        /* gen number */

                o = pdf_dict_get(gctx, imagedict, PDF_NAME_Width);
                long width = (long) pdf_to_int(gctx, o);
                PyObject *width_py = PyInt_FromLong(width);

                o = pdf_dict_get(gctx, imagedict, PDF_NAME_Height);
                long height = (long) pdf_to_int(gctx, o);
                PyObject *height_py = PyInt_FromLong(height);

                o = pdf_dict_get(gctx, imagedict, PDF_NAME_BitsPerComponent);
                long bpc = (long) pdf_to_int(gctx, o);
                PyObject *bpc_py = PyInt_FromLong(bpc);

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

                PyObject *cs_py = PyString_FromString(pdf_to_name(gctx, cs));
                PyObject *altcs_py = PyString_FromString(pdf_to_name(gctx, altcs));

                PyObject *img = PyList_New(0);         /* Python list per img */
                PyList_Append(img, xref_py);
                PyList_Append(img, gen_py);
                PyList_Append(img, width_py);
                PyList_Append(img, height_py);
                PyList_Append(img, bpc_py);
                PyList_Append(img, cs_py);
                PyList_Append(img, altcs_py);
                PyList_Append(imglist, img);
            }
            return imglist;
        }

        /***********************************************************************
        Returns the fonts used on a page as a nested list of lists.
        Each font entry contains [xref#, gen#, type, basename, name]
        ***********************************************************************/
        FITZEXCEPTION(getPageFontList, result==NULL)
        CLOSECHECK(getPageFontList, self.isClosed)
        PyObject *getPageFontList(int pno)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self);
            int pageCount = fz_count_pages(gctx, $self);
            fz_try(gctx)
            {
                if ((pno < 0) | (pno >= pageCount))
                    fz_throw(gctx, FZ_ERROR_GENERIC, "page number out of range");
                if (!pdf)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
            }
            fz_catch(gctx)
            {
                return NULL;
            }
            PyObject *fontlist = PyList_New(0);       /* returned Python list */
            pdf_obj *pageref = pdf_lookup_page_obj(gctx, pdf, pno);
            pdf_obj *pageobj = pdf_resolve_indirect(gctx, pageref);
            pdf_obj *rsrc = pdf_dict_get(gctx, pageobj, PDF_NAME_Resources);
            pdf_obj *dict = pdf_dict_get(gctx, rsrc, PDF_NAME_Font);
            int n = pdf_dict_len(gctx, dict);
            int i;
            for (i = 0; i < n; i++)      /* do this for each font of the page */
            {
                pdf_obj *fontdict = NULL;
                pdf_obj *subtype = NULL;
                pdf_obj *basefont = NULL;
                pdf_obj *name = NULL;
                pdf_obj *bname = NULL;
                fontdict = pdf_dict_get_val(gctx, dict, i);
                if (!pdf_is_dict(gctx, fontdict)) continue;  /* no valid font */
                long xref = (long) pdf_to_num(gctx, fontdict);
                long gen  = (long) pdf_to_gen(gctx, fontdict);
                PyObject *xref_py = PyInt_FromLong(xref);      /* xref number */
                PyObject *gen_py  = PyInt_FromLong(gen);        /* gen number */
                subtype = pdf_dict_get(gctx, fontdict, PDF_NAME_Subtype);
                basefont = pdf_dict_get(gctx, fontdict, PDF_NAME_BaseFont);
                if (!basefont || pdf_is_null(gctx, basefont))
                    bname = pdf_dict_get(gctx, fontdict, PDF_NAME_Name);
                else
                    bname = basefont;
                name = pdf_dict_get(gctx, fontdict, PDF_NAME_Name);
                PyObject *type_py = PyString_FromString(pdf_to_name(gctx, subtype));
                PyObject *bname_py = PyString_FromString(pdf_to_name(gctx, bname));
                PyObject *name_py = PyString_FromString(pdf_to_name(gctx, name));
                PyObject *font = PyList_New(5);      /* Python list per font */
                PyList_SetItem(font, 0, xref_py);
                PyList_SetItem(font, 1, gen_py);
                PyList_SetItem(font, 2, type_py);
                PyList_SetItem(font, 3, bname_py);
                PyList_SetItem(font, 4, name_py);
                PyList_Append(fontlist, font);
            }
            return fontlist;
        }

        /***********************************************************************
        Delete all bookmarks (table of contents)
        returns a list of deleted xref outline entries
        ***********************************************************************/
        CLOSECHECK(_delToC, self.isClosed)
        %pythonappend _delToC %{
            self.initData()
        %}
        PyObject *_delToC()
        {
            PyObject *xrefs = PyList_New(0);         /* create Python list */

            pdf_document *pdf = pdf_specifics(gctx, $self); /* conv doc to pdf*/
            if (!pdf) return NULL;                          /* not a pdf      */
            pdf_obj *root, *olroot, *first;
            /* get main root */
            root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Root);
            /* get outline root */
            olroot = pdf_dict_get(gctx, root, PDF_NAME_Outlines);
            if (!olroot) return xrefs;                      /* no outlines    */
            int objcount, argc, i;
            int *res;
            objcount = 0;
            argc = 0;
            first = pdf_dict_get(gctx, olroot, PDF_NAME_First); /* first outl */
            if (!first) return xrefs;
            argc = countOutlines(first, argc);         /* get number outlines */
            if (argc < 1) return xrefs;
            res = malloc(argc * sizeof(int));          /* object number table */
            objcount = fillOLNumbers(res, first, objcount, argc);/* fill table*/
            pdf_dict_del(gctx, olroot, PDF_NAME_First);
            pdf_dict_del(gctx, olroot, PDF_NAME_Last);
            pdf_dict_del(gctx, olroot, PDF_NAME_Count);

            for (i = 0; i < objcount; i++)
                pdf_delete_object(gctx, pdf, res[i]);     /* del all OL items */

            for (i = 0; i < argc; i++)
            {
                PyObject *xref = PyInt_FromLong((long) res[i]);
                PyList_Append(xrefs, xref);
            }
            return xrefs;
        }

        /**********************************************************************
        Get Xref Number of Outline Root, create it if missing
        **********************************************************************/
        FITZEXCEPTION(_getOLRootNumber, result<0)
        CLOSECHECK(_getOLRootNumber, self.isClosed)
        int _getOLRootNumber()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); /* conv doc to pdf*/
            fz_try(gctx) {
                if (!pdf) fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
            }
            fz_catch(gctx) {
                return -2;
            }
            pdf_obj *root, *olroot, *ind_obj;
            /* get main root */
            root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Root);
            /* get outline root */
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

        /**********************************************************************
        Get a New Xref Number
        **********************************************************************/
        FITZEXCEPTION(_getNewXref, result<0)
        CLOSECHECK(_getNewXref, self.isClosed)
        int _getNewXref()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); /* conv doc to pdf*/
            fz_try(gctx) {
                if (!pdf) fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
            }
            fz_catch(gctx) {
                return -2;
            }
            return pdf_create_object(gctx, pdf);
        }

        /**********************************************************************
        Get Length of Xref
        **********************************************************************/
        FITZEXCEPTION(_getXrefLength, result<0)
        CLOSECHECK(_getXrefLength, self.isClosed)
        int _getXrefLength()
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); /* conv doc to pdf*/
            fz_try(gctx) {
                if (!pdf) fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
            }
            fz_catch(gctx) {
                return -2;
            }
            return pdf_xref_len(gctx, pdf);
        }

        /**********************************************************************
        Get Object String by Xref Number
        **********************************************************************/
        FITZEXCEPTION(_getObjectString, result==NULL)
        CLOSECHECK(_getObjectString, self.isClosed)
        struct fz_buffer_s *_getObjectString(int xnum)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); /* conv doc to pdf*/
            pdf_obj *obj;
            struct fz_buffer_s *res = NULL;
            fz_output *out;
            fz_try(gctx)
            {
                if (!pdf) fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
                int xreflen = pdf_xref_len(gctx, pdf);
                if ((xnum < 1) | (xnum >= xreflen))
                    fz_throw(gctx, FZ_ERROR_GENERIC, "xref number out of range");
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                obj = pdf_load_object(gctx, pdf, xnum, 0);
                pdf_print_obj(gctx, out, pdf_resolve_indirect(gctx, obj), 1);
            }
            fz_always(gctx)
            {
                if (obj) pdf_drop_obj(gctx, obj);
                if (out) fz_drop_output(gctx, out);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return res;
        }

        /**********************************************************************
        Update an Xref Number with a new Object given as a string
        **********************************************************************/
        FITZEXCEPTION(_updateObject, result!=0)
        CLOSECHECK(_updateObject, self.isClosed)
        int _updateObject(int xref, char *text)
        {
            pdf_obj *new_obj;
            pdf_document *pdf = pdf_specifics(gctx, $self); /* conv doc to pdf*/
            fz_try(gctx)
            {
                if (!pdf)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
                int xreflen = pdf_xref_len(gctx, pdf);
                if ((xref < 1) | (xref >= xreflen))
                    fz_throw(gctx, FZ_ERROR_GENERIC, "xref number out of range");
                /* create new object based on passed-in string          */
                new_obj = pdf_new_obj_from_str(gctx, pdf, text);
                pdf_update_object(gctx, pdf, xref, new_obj);
            }
            fz_catch(gctx) {
                return -1;
            }
            return 0;
        }

        /**********************************************************************
        Add or update metadata with provided raw string
        **********************************************************************/
        FITZEXCEPTION(_setMetadata, result>0)
        CLOSECHECK(_setMetadata, self.isClosed)
        int _setMetadata(char *text)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); /* conv doc to pdf*/
            fz_try(gctx) {
                if (!pdf) fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
            }
            fz_catch(gctx) {
                return 1;
            }
            pdf_obj *info, *new_info, *new_info_ind;
            int info_num;
            info_num = 0;              /* will contain xref no of info object */
            fz_try(gctx)
            {
                /* create new /Info object based on passed-in string          */
                new_info = pdf_new_obj_from_str(gctx, pdf, text);
            }
            fz_catch(gctx) {
                return gctx->error->errcode;
            }
            /* replace existing /Info object                                  */
            info = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Info);
            if (info)
            {
                info_num = pdf_to_num(gctx, info); /* get xref no of old info */
                pdf_update_object(gctx, pdf, info_num, new_info);/* put new in*/
                return 0;
            }
            /* create new indirect object from /Info object                   */
            new_info_ind = pdf_add_object(gctx, pdf, new_info);
            /* put this in the trailer dictionary                             */
            pdf_dict_put(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Info, new_info_ind);
            return 0;
        }

        /**********************************************************************
        Initialize document: set outline and metadata properties
        **********************************************************************/
        %pythoncode %{
            def initData(self):
                if self.isEncrypted:
                    raise ValueError("cannot initData - document still encrypted")
                self._outline = self._loadOutline()
                self.metadata = dict([(k,self._getMetadata(v)) for k,v in {'format':'format', 'title':'info:Title', 'author':'info:Author','subject':'info:Subject', 'keywords':'info:Keywords','creator':'info:Creator', 'producer':'info:Producer', 'creationDate':'info:CreationDate', 'modDate':'info:ModDate'}.items()])
                self.metadata['encryption'] = None if self._getMetadata('encryption')=='None' else self._getMetadata('encryption')

            outline = property(lambda self: self._outline)
            pageCount = property(lambda self: self._getPageCount())
            needsPass = property(lambda self: self._needsPass())

            def __repr__(self):
                if self.streamlen == 0:
                    return "fitz.Document('%s')" % (self.name,)
                return "fitz.Document('%s', bytearray)" % (self.name,)

            def __getitem__(self, i):
                if i >= 0:
                    return self.loadPage(i)
                else:
                    return self.loadPage(i + self.pageCount)                    

            def __len__(self):
                return self.pageCount

            %}
    }
};

/******************************************************************************
fz_page
******************************************************************************/
%nodefaultctor;
%rename(Page) fz_page_s;
struct fz_page_s {
    %extend {
        ~fz_page_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free page\n");
#endif
            fz_drop_page(gctx, $self);
        }

        CLOSECHECK(bound, self.parent.isClosed)
        %pythonappend bound() %{
            if val:
                val.thisown = True
        %}
        struct fz_rect_s *bound() {
            fz_rect *rect = (fz_rect *)malloc(sizeof(fz_rect));
            fz_bound_page(gctx, $self, rect);
            return rect;
        }

        /***********************************************************/
        /* Page.run()                                              */
        /***********************************************************/
        FITZEXCEPTION(run, result)
        CLOSECHECK(run, self.parent.isClosed)
        int run(struct DeviceWrapper *dw, const struct fz_matrix_s *m) {
            fz_try(gctx) {
                fz_run_page(gctx, $self, dw->device, m, NULL);
            }
            fz_catch(gctx) {
                return 1;
            }
            return 0;
        }
        /***********************************************************/
        /* Page.loadLinks()                                        */
        /***********************************************************/
        CLOSECHECK(loadLinks, self.parent.isClosed)
        %pythonappend loadLinks() %{
            if val:
                val.thisown = True
        %}
        struct fz_link_s *loadLinks() {
            return fz_load_links(gctx, $self);
        }
        %pythoncode %{firstLink = property(loadLinks)%}

        /***********************************************************/
        /* Page.firstAnnot()                                       */
        /***********************************************************/
        CLOSECHECK(_firstAnnot, self.parent.isClosed)
        %pythonappend _firstAnnot
        %{
            if val:
                val.thisown = True
        %}
        struct pdf_annot_s *_firstAnnot()
        {   /* return a PDF annotation struct for ALL document types          */
            pdf_page *page = (pdf_page*)$self;      // treat page as PDF page
            /* see if we do have a PDF document ... */
            pdf_document *pdf = pdf_specifics(gctx, (fz_document*)page->doc);
            fz_annot *fannot;
            pdf_annot *pannot;
            if (pdf)
                {
                pannot = pdf_first_annot(gctx, page);
                if (pannot != NULL) pannot->page = page;
                }
            else
                {
                fannot = fz_first_annot(gctx, $self);
                if (fannot != NULL)
                    {
                    pannot = fz_new_annot(gctx, sizeof(pdf_annot));
                    pannot->super = *fannot;
                    pannot->page  = NULL;
                    pannot->annot_type = -1;
                    }
                else
                    pannot = NULL;
                }
            return pannot;
        }
        %pythoncode %{firstAnnot = property(_firstAnnot)%}

        /*********************************************************************/
        // Page.getRotate()
        /*********************************************************************/
        FITZEXCEPTION(getRotate, result<0)
        CLOSECHECK(getRotate, self.parent.isClosed)
        int getRotate()
        {
            pdf_page *page = (pdf_page*)$self;      // treat page as PDF page
            pdf_document *pdf = pdf_specifics(gctx, (fz_document*)page->doc);
            fz_try(gctx)
            {
                if (!pdf)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
            }
            fz_catch(gctx)
            {
                return -1;
            }
            return page->rotate;
        }

        /*********************************************************************/
        // Page.setRotate()
        /*********************************************************************/
        FITZEXCEPTION(setRotate, result<0)
        CLOSECHECK(setRotate, self.parent.isClosed)
        int setRotate(int rot)
        {
            pdf_page *page = (pdf_page*)$self;      // treat page as PDF page
            pdf_document *pdf = pdf_specifics(gctx, (fz_document*)page->doc);
            fz_try(gctx)
            {
                if (!pdf)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
                pdf_obj *rot_o = pdf_new_int(gctx, pdf, rot);
                pdf_dict_put_drop(gctx, page->me, PDF_NAME_Rotate, rot_o);
            }
            fz_catch(gctx)
            {
                return -1;
            }
            return 0;
        }

        /*********************************************************************/
        // Page._readPageText()
        /*********************************************************************/
        FITZEXCEPTION(_readPageText, result==NULL)
        struct fz_buffer_s *_readPageText(int output=0) {
            fz_buffer *res;
            fz_try(gctx) {
                res = readPageText($self, output);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return res;
        }

        /***********************************************************/
        /* Page.__repr__()                                         */
        /***********************************************************/
        %pythoncode %{
        def __str__(self):
            return "page %s of %s" % (self.number, repr(self.parent))
        def __repr__(self):
            return repr(self.parent) + ".loadPage(" + str(self.number) + ")"
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

#ifdef MEMDEBUG
        ~fz_rect_s() {
            fprintf(stderr, "[DEBUG]free rect\n");
            free($self);
        }
#endif
        %pythonappend round() %{
            val.thisown = True
        %}
        struct fz_irect_s *round() {
            fz_irect *irect = (fz_irect *)malloc(sizeof(fz_irect));
            fz_round_rect(irect, $self);
            return irect;
        }

        struct fz_rect_s *includePoint(const struct fz_point_s *p) {
            fz_include_point_in_rect($self, p);
            return $self;
        }

        struct fz_rect_s *intersect(struct fz_rect_s *r) {
            fz_intersect_rect($self, r);
            return $self;
        }

        struct fz_rect_s *includeRect(struct fz_rect_s *r) {
            fz_union_rect($self, r);
            return $self;
        }

        %pythoncode %{
            def transform(self, m):
                _fitz._fz_transform_rect(self, m)
                return self

            def __getitem__(self, i):
                a = [self.x0, self.y0, self.x1, self.y1]
                return a[i]

            def __len__(self):
                return 4

            def __repr__(self):
                return "fitz.Rect" + str((self.x0, self.y0, self.x1, self.y1))

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
#ifdef MEMDEBUG
        ~fz_irect_s() {
            fprintf(stderr, "[DEBUG]free irect\n");
            free($self);
        }
#endif
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

            def __getitem__(self, i):
                a = [self.x0, self.y0, self.x1, self.y1]
                return a[i]

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
        /***********************************************************/
        /* create empty pixmap with colorspace and IRect specified */
        /***********************************************************/
        fz_pixmap_s(struct fz_colorspace_s *cs, const struct fz_irect_s *bbox)
        {
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx)
                pm = fz_new_pixmap_with_bbox(gctx, cs, bbox);
            fz_catch(gctx)
                return NULL;
            return pm;
        }

        /***********************************************************/
        /* create new pixmap as converted copy of another one      */
        /***********************************************************/
        fz_pixmap_s(struct fz_colorspace_s *cs, struct fz_pixmap_s *spix)
        {
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx)
            {
                if ((spix->n < 2) | (spix->n > 5))
                    fz_throw(gctx, FZ_ERROR_GENERIC, "unsupported source colorspace");
                pm = fz_new_pixmap(gctx, cs, spix->w, spix->h);
                pm->x = 0;
                pm->y = 0;
                fz_convert_pixmap(gctx, pm, spix);
            }
            fz_catch(gctx)
                return NULL;
            return pm;
        }

        /***********************************************************/
        /* create a pixmap from samples data                       */
        /***********************************************************/
        fz_pixmap_s(struct fz_colorspace_s *cs, int w, int h, PyObject *samples)
        {
            char *data;
            size_t size;
            size = 0;
            if (PyByteArray_Check(samples)){
                data = PyByteArray_AsString(samples);
                size = (size_t) PyByteArray_Size(samples);
            }
            if (PyBytes_Check(samples)){
                data = PyBytes_AsString(samples);
                size = (size_t) PyBytes_Size(samples);
            }
            fz_try(gctx) {
                if (size == 0)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "type(samples) invalid");
                if ((cs->n+1) * w * h != size) {
                    fz_throw(gctx, FZ_ERROR_GENERIC, "len(samples) invalid");
                    }
                }
            fz_catch(gctx) {
                return NULL;
                }
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx)
                pm = fz_new_pixmap_with_data(gctx, cs, w, h, data);
            fz_catch(gctx)
                return NULL;
            return pm;
        }

        /******************************************/
        /* create a pixmap from filename          */
        /******************************************/
        fz_pixmap_s(char *filename)
        {
            struct fz_image_s *img = NULL;
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx) {
                img = fz_new_image_from_file(gctx, filename);
                pm = fz_get_pixmap_from_image(gctx, img, -1, 1);
            }
            fz_catch(gctx) {
                if (img) fz_drop_image(gctx, img);
                return NULL;
            }
            fz_drop_image(gctx, img);
            return pm;
        }

        /******************************************/
        /* create a pixmap from bytes / bytearray */
        /******************************************/
        fz_pixmap_s(PyObject *imagedata)
        {
            size_t size;
            size = 0;
            char *data;
            if (PyByteArray_Check(imagedata)){
                data = PyByteArray_AsString(imagedata);
                size = (size_t) PyByteArray_Size(imagedata);
            }
            if (PyBytes_Check(imagedata)){
                data = PyBytes_AsString(imagedata);
                size = (size_t) PyBytes_Size(imagedata);
            }
            struct fz_image_s *img = NULL;
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx) {
                if (size == 0)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "type(imagedata) invalid");
                img = fz_new_image_from_data(gctx, data, size);
                pm = fz_get_pixmap_from_image(gctx, img, -1, -1);
                fz_drop_image(gctx, img);
                }
            fz_catch(gctx) {
                if (img) fz_drop_image(gctx, img);
                return NULL;
                }

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
                if (!pdf)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
                int xreflen = pdf_xref_len(gctx, pdf);
                if ((xref < 1) | (xref >= xreflen))
                    fz_throw(gctx, FZ_ERROR_GENERIC, "xref number out of range");
                ref = pdf_new_indirect(gctx, pdf, xref, 0);
                img = pdf_load_image(gctx, pdf, ref);
                pdf_drop_obj(gctx, ref);
                pix = fz_get_pixmap_from_image(gctx, img, 0, 0);
                fz_drop_image(gctx,img);
            }
            fz_catch(gctx)
            {
                if (img) fz_drop_image(gctx, img);
                if (pix) fz_drop_pixmap(gctx, pix);
                if (ref) pdf_drop_obj(gctx, ref);
                return NULL;
            }
            return pix;
        }

        ~fz_pixmap_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free pixmap\n");
#endif
            fz_drop_pixmap(gctx, $self);
        }
        /***************************/
        /* apply gamma correction  */
        /***************************/
        void gammaWith(float gamma) {
            fz_gamma_pixmap(gctx, $self, gamma);
        }

        /***************************/
        /* tint pixmap with color  */
        /***************************/
        %pythonprepend tintWith(int red, int green, int blue) %{
            # only GRAY and RGB pixmaps allowed
            if self.n not in (2, 4):
                raise TypeError("only gray and rgb pixmaps can be tinted")
        %}
        void tintWith(int red, int green, int blue) {
            fz_tint_pixmap(gctx, $self, red, green, blue);
        }

        /*********************************/
        /* clear total pixmap with value */
        /*********************************/
        void clearWith(int value) {
            fz_clear_pixmap_with_value(gctx, $self, value);
        }

        /*************************************/
        /* clear pixmap rectangle with value */
        /*************************************/
        void clearWith(int value, const struct fz_irect_s *bbox) {
            fz_clear_pixmap_rect_with_value(gctx, $self, value, bbox);
        }

        /***********************************/
        /* copy pixmaps                    */
        /***********************************/
        void copyPixmap(struct fz_pixmap_s *src, const struct fz_irect_s *bbox)
        {
            fz_copy_pixmap_rect(gctx, $self, src, bbox);
        }

        /**********************/
        /* get size of pixmap */
        /**********************/
        int getSize() {
            return fz_pixmap_size(gctx, $self);
        }

        /**********************/
        /* writePNG           */
        /**********************/
        FITZEXCEPTION(writePNG, result)
        %pythonprepend writePNG(char *filename, int savealpha) %{
            if type(filename) == str:
                pass
            elif type(filename) == unicode:
                filename = filename.encode('utf8')
            else:
                raise TypeError("filename must be a string")
            if not filename.lower().endswith(".png"):
                raise ValueError("filename must end with '.png'")
        %}
        int writePNG(char *filename, int savealpha=0) {
            fz_try(gctx) {
                if ($self->n > 4)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "PNG not supported for CMYK");
                fz_save_pixmap_as_png(gctx, $self, filename, savealpha);
            }
            fz_catch(gctx)
                return 1;
            return 0;
        }

        /**********************/
        /* getPNGData         */
        /**********************/
        FITZEXCEPTION(getPNGData, !result)
        PyObject *getPNGData(int savealpha=0)
        {
            struct fz_buffer_s *res = NULL;
            fz_output *out;
            fz_try(gctx) {
                if ($self->n > 4)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "PNG not supported for CMYK");
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                fz_write_pixmap_as_png(gctx, out, $self, savealpha);
                fz_drop_output(gctx, out);
            }
            fz_catch(gctx)
                 return NULL;
            return PyByteArray_FromStringAndSize((const char *)res->data, res->len);
        }

        /**************************************/
        /* samplesRGB                         */
        /* utility to extract samples data    */
        /* without the alpha bytes (RGB only) */
        /**************************************/

        PyObject *samplesRGB()
        {
            if ($self->n != 4) return NULL;  /* RGB colorspaces onbly */
            char *t;
            char *s;
            char *out;
            int i;
            int j;
            int size;
            PyObject *res;                   /* feedback bytearrarray */
            s = (char *)$self->samples;      // point to samples
            size = $self->w * $self->h * 3;  // new area is 3/4 of samples
            out = (char *)malloc(size);      // allocate it
            if (!out) {                      // got it?
                PyErr_SetString(PyExc_Exception, "cannot allocate samplesRGB");
                return NULL;
            }
            t = (char *)out;                 // point to it
            for (i=0; i<$self->w; i++) {
                for (j=0; j<$self->h; j++) {
                    t[0] = s[0];
                    t[1] = s[1];
                    t[2] = s[2];
                    t = t + 3;
                    s = s + 4;
                }
            }
            res = (PyObject *)PyByteArray_FromStringAndSize((const char *)out, size);
            free(out);
            return res;
        }

        /**************************************/
        /* samplesAlpha                       */
        /* utility to extract the alpha bytes */
        /* out of the samples area            */
        /**************************************/

        PyObject *samplesAlpha()
        {
            char *t;
            char *s;
            char *out;
            int i;
            int j;
            int size;
            PyObject *res;                   /* feedback bytearrarray */
            s = (char *)$self->samples;      // point to samples
            size = $self->w * $self->h;      // new area is 1/4 of samples
            out = (char *)malloc(size);      // allocate it
            if (!out) {                      // got it?
                PyErr_SetString(PyExc_Exception, "cannot allocate samplesAlpha");
                return NULL;
            }
            t = (char *)out;                 // point to it
            for (i=0; i<$self->w; i++) {
                for (j=0; j<$self->h; j++) {
                    t[0] = s[$self->n - 1];
                    t = t + 1;
                    s = s + $self->n;
                }
            }
            res = (PyObject *)PyByteArray_FromStringAndSize((const char *)out, size);
            free(out);
            return res;
        }

        /************************/
        /* _writeIMG            */
        /************************/
        FITZEXCEPTION(_writeIMG, result)
        %pythonprepend _writeIMG(char *filename, char *format, int savealpha) %{
            if type(filename) == str:
                pass
            elif type(filename) == unicode:
                filename = filename.encode('utf8')
            else:
                raise TypeError("filename must be a string")
        %}
        int _writeIMG(char *filename, int format, int savealpha=0)
        {
            fz_try(gctx) {
                switch(format)
                {
                    case(1):
                        fz_save_pixmap_as_png(gctx, $self, filename, savealpha);
                        break;
                    case(2):
                        fz_save_pixmap_as_pnm(gctx, $self, filename);
                        break;
                    case(3):
                        fz_save_pixmap_as_pam(gctx, $self, filename, savealpha);
                        break;
                    case(4):
                        fz_save_pixmap_as_tga(gctx, $self, filename, savealpha);
                        break;
                }
            }
            fz_catch(gctx)
                return 1;
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

        PyObject *_getSamples()
        {
            return PyByteArray_FromStringAndSize((const char *)$self->samples, ($self->w)*($self->h)*($self->n));
        }

        %pythoncode %{
            samples = property(lambda self: self._getSamples())
            __len__ = getSize
            width  = w
            height = h

            def __repr__(self):
                cs = {2:"fitz.csGRAY", 4:"fitz.csRGB", 5:"fitz.csCMYK"}
                cspace = "unsupp:" + str(self.n) if not cs.get(self.n) else cs[self.n]
                return "fitz.Pixmap(%s, fitz.IRect(%s, %s, %s, %s))" % (cspace, self.x, self.y, self.x + self.width, self.y + self.height)

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
        ~fz_colorspace_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free colorspace\n");
#endif
            fz_drop_colorspace(gctx, $self);
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
                    dw->device = fz_new_draw_device(gctx, pm);
                else
                    dw->device = fz_new_draw_device_with_bbox(gctx, pm, clip);
            }
            fz_catch(gctx)
                return NULL;
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
            fz_catch(gctx)
                return NULL;
            return dw;
        }
        DeviceWrapper(struct fz_stext_sheet_s *ts, struct fz_stext_page_s *tp) {
            struct DeviceWrapper *dw = NULL;
            fz_try(gctx) {
                dw = (struct DeviceWrapper *)calloc(1, sizeof(struct DeviceWrapper));
                dw->device = fz_new_stext_device(gctx, ts, tp);
            }
            fz_catch(gctx)
                return NULL;
            return dw;
        }
        ~DeviceWrapper() {
            fz_display_list *list = $self->list;
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free device\n");
#endif
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
#ifdef MEMDEBUG
        ~fz_matrix_s() {
            fprintf(stderr, "[DEBUG]free matrix\n");
            free($self);
        }
#endif
        /* copy constructor */
        fz_matrix_s(const struct fz_matrix_s* n) {
            fz_matrix *m = (fz_matrix *)malloc(sizeof(fz_matrix));
            return fz_copy_matrix(m, n);
        }
        /* create a scale/shear matrix, scale matrix by default */
        fz_matrix_s(float sx, float sy, int shear=0) {
            if(shear) {
                fz_matrix *m = (fz_matrix *)malloc(sizeof(fz_matrix));
                return fz_shear(m, sx, sy);
            }
            else {
                fz_matrix *m = (fz_matrix *)malloc(sizeof(fz_matrix));
                return fz_scale(m, sx, sy);
            }
        }
        /* create a rotate matrix */
        fz_matrix_s(float degree) {
            fz_matrix *m = (fz_matrix *)malloc(sizeof(fz_matrix));
            return fz_rotate(m, degree);
        }

        int invert(const struct fz_matrix_s *m) {
            int rc = fz_try_invert_matrix($self, m);
            return rc;
        }

        struct fz_matrix_s *preTranslate(float sx, float sy) {
            fz_pre_translate($self, sx, sy);
            return $self;
        }

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
    struct fz_link_dest_s dest;
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
            fprintf(stderr, "[DEBUG]free outline\n");
#endif
            fz_drop_outline(gctx, $self);
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
            int res = 1;
            struct fz_output_s *xml;
            fz_try(gctx) {
                xml = fz_new_output_with_path(gctx, filename, 0);
                fz_print_outline_xml(gctx, xml, $self);
                fz_drop_output(gctx, xml);
                res = 0;
            }
            fz_catch(gctx)
                return 1;
            return res;
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
            fz_catch(gctx)
                return 1;
            return res;
        }
    }
};
%clearnodefaultctor;


/*fz_link_kind */
%rename("%(strip:[FZ_])s") "";
typedef enum fz_link_kind_e
{
    FZ_LINK_NONE = 0,
    FZ_LINK_GOTO,
    FZ_LINK_URI,
    FZ_LINK_LAUNCH,
    FZ_LINK_NAMED,
    FZ_LINK_GOTOR
} fz_link_kind;


/* fz_link_dest */
%rename(linkDest) fz_link_dest_s;
%nodefaultctor;
struct fz_link_dest_s {
    %immutable;
    fz_link_kind kind;
    %extend {
        int _getPage() {
            return ($self->kind == FZ_LINK_GOTO || $self->kind == FZ_LINK_GOTOR) ? $self->ld.gotor.page : 0;
        }
        char *_getDest() {
            return ($self->kind == FZ_LINK_GOTO || $self->kind == FZ_LINK_GOTOR) ? $self->ld.gotor.dest : NULL;
        }
        int _getFlags() {
            return ($self->kind == FZ_LINK_GOTO || $self->kind == FZ_LINK_GOTOR) ? $self->ld.gotor.flags : 0;
        }
        struct fz_point_s *_getLt() {
            return ($self->kind == FZ_LINK_GOTO || $self->kind == FZ_LINK_GOTOR) ? &($self->ld.gotor.lt) : NULL;
        }
        struct fz_point_s *_getRb() {
            return ($self->kind == FZ_LINK_GOTO || $self->kind == FZ_LINK_GOTOR) ? &($self->ld.gotor.rb) : NULL;
        }
        char *_getFileSpec() {
            return ($self->kind == FZ_LINK_GOTO || $self->kind == FZ_LINK_GOTOR) ? $self->ld.gotor.file_spec : ($self->kind==FZ_LINK_LAUNCH ? $self->ld.launch.file_spec : NULL);
        }
        int _getNewWindow() {
            return ($self->kind == FZ_LINK_GOTO || $self->kind == FZ_LINK_GOTOR) ? $self->ld.gotor.new_window : ($self->kind==FZ_LINK_LAUNCH ? $self->ld.launch.new_window : 0);
        }
        char *_getUri() {
            return ($self->kind == FZ_LINK_URI) ? $self->ld.uri.uri : NULL;
        }
        int _getIsMap() {
            return ($self->kind == FZ_LINK_URI) ? $self->ld.uri.is_map : 0;
        }
        int _getIsUri() {
            return $self->kind == FZ_LINK_LAUNCH ? $self->ld.launch.is_uri : 0;
        }
        char *_getNamed() {
            return $self->kind == FZ_LINK_NAMED ? $self->ld.named.named : NULL;
        }
        ~fz_link_dest_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free link_dest\n");
#endif
            fz_drop_link_dest(gctx, $self);
        }
    }
    %pythoncode %{
        page = property(_getPage)
        dest = property(_getDest)
        flags = property(_getFlags)
        lt = property(_getLt)
        rb = property(_getRb)
        fileSpec = property(_getFileSpec)
        newWindow = property(_getNewWindow)
        uri = property(_getUri)
        isMap = property(_getIsMap)
        isUri = property(_getIsUri)
        named = property(_getNamed)
    %}
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
#ifdef MEMDEBUG
        ~fz_point_s() {
            fprintf(stderr, "[DEBUG]free point\n");
            free($self);
        }
#endif
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

        %pythoncode %{
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
/* Annotation */
/*****************************************************************************/
typedef enum {
    FZ_ANNOT_TEXT,
    FZ_ANNOT_LINK,
    FZ_ANNOT_FREETEXT,
    FZ_ANNOT_LINE,
    FZ_ANNOT_SQUARE,
    FZ_ANNOT_CIRCLE,
    FZ_ANNOT_POLYGON,
    FZ_ANNOT_POLYLINE,
    FZ_ANNOT_HIGHLIGHT,
    FZ_ANNOT_UNDERLINE,
    FZ_ANNOT_SQUIGGLY,
    FZ_ANNOT_STRIKEOUT,
    FZ_ANNOT_STAMP,
    FZ_ANNOT_CARET,
    FZ_ANNOT_INK,
    FZ_ANNOT_POPUP,
    FZ_ANNOT_FILEATTACHMENT,
    FZ_ANNOT_SOUND,
    FZ_ANNOT_MOVIE,
    FZ_ANNOT_WIDGET,
    FZ_ANNOT_SCREEN,
    FZ_ANNOT_PRINTERMARK,
    FZ_ANNOT_TRAPNET,
    FZ_ANNOT_WATERMARK,
    FZ_ANNOT_3D
} fz_annot_type;

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

%rename(Annot) pdf_annot_s;
%nodefaultctor;
struct pdf_annot_s
{
    fz_annot super;
    pdf_page *page;

    %extend
    {
        ~pdf_annot_s()
        {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free annot\n");
#endif
            fz_drop_annot(gctx, (fz_annot*)$self);
        }
        /**********************************************************************/
        // annotation rectangle
        /**********************************************************************/
        struct fz_rect_s *_getRect()
        {   // use the fz_annot for this ...
            fz_rect *r = (fz_rect *)malloc(sizeof(fz_rect));
            r = fz_bound_annot(gctx, &$self->super, r);
            return r;
        }
        %pythoncode %{rect = property(_getRect)%}

        /**********************************************************************/
        // annotation vertices
        /**********************************************************************/
        PyObject *_getVertices()
        {
            PyObject *res, *coord_o;
            res = PyList_New(0);                      // create Python list
            if ($self->page == NULL) return res;      // not a PDF!
            float coord = 0.0;
            pdf_obj *vert_o;
            const char *vert_str = "Vertices";
            vert_o = pdf_dict_gets(gctx, $self->obj, vert_str);
            if (!vert_o) return res;                  // no Vertices entry there
            int n = pdf_array_len(gctx, vert_o);
            int i;
            if (n < 1) return res;                    // no Vertices entry there
            for (i = 0; i < n; i++)
                {
                    coord = pdf_to_real(gctx, pdf_array_get(gctx, vert_o, i));
                    coord_o = PyFloat_FromDouble((double) coord);
                    PyList_Append(res, coord_o);
                }
            return res;
        }
        %pythoncode %{vertices = property(_getVertices)%}

        /**********************************************************************/
        // annotation lineEnds
        /**********************************************************************/
        PyObject *_getLineEnds()
        {
            PyObject *res, *lstart_o, *lend_o;
            res = PyList_New(0);                      // create Python list
            if ($self->page == NULL) return res;      // not a PDF!
            char *lstart = "";
            char *lend = "";
            pdf_obj *LE_o;
            const char *LE_str = "LE";
            LE_o = pdf_dict_gets(gctx, $self->obj, LE_str);
            if (!LE_o) return res;                    // no LE entry there

            if (pdf_is_name(gctx, LE_o))
                {
                lstart = pdf_to_name(gctx, LE_o);
                }
            else
                {
                if (pdf_is_array(gctx, LE_o))
                    {
                    lstart = pdf_to_name(gctx, pdf_array_get(gctx, LE_o, 0));
                    if (pdf_array_len(gctx, LE_o) > 1)
                        lend   = pdf_to_name(gctx, pdf_array_get(gctx, LE_o, 1));
                    }
                }
            lstart_o = PyString_FromString(lstart);
            lend_o   = PyString_FromString(lend);
            PyList_Append(res, lstart_o);
            PyList_Append(res, lend_o);
            return res;
        }
        %pythoncode %{lineEnds = property(_getLineEnds)%}

        /**********************************************************************/
        // annotation type
        /**********************************************************************/
        PyObject *_getType()
        {
            int type;
            PyObject *res, *type_o, *type_str_o;
            res = PyList_New(0);                        /* create Python list */
            if ($self->page == NULL) return res;      // not a PDF!
            type = (int) pdf_annot_type(gctx, $self);
            $self->annot_type = type;

            char *type_str = annot_type_str(type);

            type_o = PyInt_FromLong((long) type);
            type_str_o  = PyString_FromString(type_str);
            PyList_Append(res, type_o);
            PyList_Append(res, type_str_o);
            return res;
        }
        %pythoncode %{type = property(_getType)%}

        /**********************************************************************/
        // annotation name
        /**********************************************************************/
        char *_getName()
        {
            char *name;
            name = "";
            if ($self->page == NULL) return name;   // not a PDF!

            pdf_obj *name_o;
            name_o = pdf_dict_get(gctx, $self->obj, PDF_NAME_Name);
            if (name_o == NULL) return name;

            if (pdf_is_string(gctx, name_o))
                return pdf_to_str_buf(gctx, name_o);

            if (!pdf_is_name(gctx, name_o)) return name;
            name = pdf_to_name(gctx, name_o);
            return name;
        }
        %pythoncode %{name = property(_getName)%}

        /**********************************************************************/
        // annotation title
        /**********************************************************************/
        char *_getTitle()
        {
            char *title = "";
            if ($self->page == NULL) return title;   // not a PDF!
            pdf_obj *title_o;
            title_o = pdf_dict_get(gctx, $self->obj, PDF_NAME_T);
            if (title_o == NULL) return title;
            title = pdf_to_str_buf(gctx, title_o);
            return title;
        }
        %pythoncode %{title = property(_getTitle)%}

        /**********************************************************************/
        // annotation date
        /**********************************************************************/
        char *_getDate()
        {
            char *date = "";
            if ($self->page == NULL) return date;   // not a PDF!
            pdf_obj *date_o;
            date_o = pdf_dict_get(gctx, $self->obj, PDF_NAME_M);
            if (date_o == NULL) return date;
            date = pdf_to_str_buf(gctx, date_o);
            return date;
        }
        %pythoncode %{date = property(_getDate)%}

        /**********************************************************************/
        // annotation flags
        /**********************************************************************/
        int _getFlags()
        {
            int flag = 0;
            if ($self->page == NULL) return flag;   // not a PDF!
            pdf_obj *flag_o;
            flag_o = pdf_dict_get(gctx, $self->obj, PDF_NAME_F);
            if (flag_o == NULL) return flag;
            flag = pdf_to_int(gctx, flag_o);
            return flag;
        }
        %pythoncode %{flags = property(_getFlags)%}

        /**********************************************************************/
        // annotation contents
        /**********************************************************************/
        char *_getContents()
        {
            char *content;
            if ($self->page == NULL)    // not a PDF!
                content = "";
            else
                content = pdf_annot_contents(gctx, $self->page->doc, $self);
            return content;
        }
        %pythoncode %{content = property(_getContents)%}

        /**********************************************************************/
        // next annotation
        /**********************************************************************/
        %pythonappend _getNext
        %{
            if val:
                val.thisown = True
        %}
        struct pdf_annot_s *_getNext()
        {
            fz_annot *fannot;
            pdf_annot *pannot;
            if ($self->page)
                {
                pannot = pdf_next_annot(gctx, $self);
                if (pannot != NULL) pannot->page = $self->page;
                }
            else    // not a PDF!
                {
                fannot = fz_next_annot(gctx, &$self->super);
                if (fannot != NULL)
                    {
                    pannot = fz_new_annot(gctx, sizeof(pdf_annot));
                    pannot->super = *fannot;
                    pannot->page  = NULL;
                    pannot->annot_type = -1;
                    }
                else
                    pannot = NULL;
                }
            return pannot;

        }
        %pythoncode %{next = property(_getNext)%}

        /**********************************************************************/
        // annotation pixmap
        /**********************************************************************/
        FITZEXCEPTION(getPixmap, !result)
        %pythonprepend getPixmap
        %{
            if not matrix: matrix = Matrix(0)
            if not colorspace: colorspace = Colorspace(CS_RGB)%}

        struct fz_pixmap_s *getPixmap(struct fz_matrix_s *matrix = NULL, struct fz_colorspace_s *colorspace = NULL)
        {
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx)
            {
                pm = fz_new_pixmap_from_annot(gctx, &$self->super, matrix, colorspace);
            }
            fz_catch(gctx)
            {
                return NULL;
            }
            return pm;
        }

    }
};
%clearnodefaultctor;

/*****************************************************************************/
// fz_link
/*****************************************************************************/
%rename("%(regex:/fz_(.*)/\\U\\1/)s") "";
enum {
    fz_link_flag_l_valid = 1, /* lt.x is valid */
    fz_link_flag_t_valid = 2, /* lt.y is valid */
    fz_link_flag_r_valid = 4, /* rb.x is valid */
    fz_link_flag_b_valid = 8, /* rb.y is valid */
    fz_link_flag_fit_h = 16, /* Fit horizontally */
    fz_link_flag_fit_v = 32, /* Fit vertically */
    fz_link_flag_r_is_zoom = 64 /* rb.x is actually a zoom figure */
};
%rename(Link) fz_link_s;
%nodefaultctor;
struct fz_link_s
{
    %immutable;
    struct fz_rect_s rect;
    struct fz_link_dest_s dest;
    %extend {
        ~fz_link_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free link\n");
#endif
            fz_drop_link(gctx, $self);
        }
        /* we need to increase the link refs number so that it won't be freed when the head is dropped */
        %pythonappend _getNext() %{
            if val:
                val.thisown = True
        %}
        struct fz_link_s *_getNext() {
            fz_keep_link(gctx, $self->next);
            return $self->next;
        }
        %pythoncode %{
            next = property(_getNext)
        %}
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
        fz_display_list_s()
        {
            struct fz_display_list_s *dl = NULL;
            fz_try(gctx)
                dl = fz_new_display_list(gctx);
            fz_catch(gctx)
                return NULL;
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
            fz_catch(gctx)
                return 1;
            return 0;
        }
    }
};

/*****************************************************************************/
/* fz_stext_sheet */
/*****************************************************************************/
%rename(TextSheet) fz_stext_sheet_s;
struct fz_stext_sheet_s {
    %extend {
        FITZEXCEPTION(fz_stext_sheet_s, !result)
        fz_stext_sheet_s() {
            struct fz_stext_sheet_s *ts = NULL;
            fz_try(gctx)
                ts = fz_new_stext_sheet(gctx);
            fz_catch(gctx)
                return NULL;
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
/* fz_stext_page */
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
        fz_stext_page_s() {
            struct fz_stext_page_s *tp = NULL;
            fz_try(gctx)
                tp = fz_new_stext_page(gctx);
            fz_catch(gctx)
                return NULL;
            return tp;
        }

        ~fz_stext_page_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free text page\n");
#endif
            fz_drop_stext_page(gctx, $self);
        }
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
        struct fz_buffer_s *extractText() {
            struct fz_buffer_s *res = NULL;
            fz_output *out;
            fz_try(gctx) {
                /* inital size for text */
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                fz_print_stext_page(gctx, out, $self);
                fz_drop_output(gctx, out);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return res;
        }
        /*******************************************/
        /* method extractXML()                     */
        /*******************************************/
        FITZEXCEPTION(extractXML, !result)
        struct fz_buffer_s *extractXML() {
            struct fz_buffer_s *res = NULL;
            fz_output *out;
            fz_try(gctx) {
                /* inital size for text */
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                fz_print_stext_page_xml(gctx, out, $self);
                fz_drop_output(gctx, out);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return res;
        }
        /*******************************************/
        /* method extractHTML()                    */
        /*******************************************/
        FITZEXCEPTION(extractHTML, !result)
        struct fz_buffer_s *extractHTML() {
            struct fz_buffer_s *res = NULL;
            fz_output *out;
            fz_try(gctx) {
                /* inital size for text */
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                fz_print_stext_page_html(gctx, out, $self);
                fz_drop_output(gctx, out);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return res;
        }
        /*******************************************/
        /* method extractJSON()                    */
        /*******************************************/
        FITZEXCEPTION(extractJSON, !result)
        struct fz_buffer_s *extractJSON() {
            struct fz_buffer_s *res = NULL;
            fz_output *out;
            fz_try(gctx) {
                /* inital size for text */
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                fz_print_stext_page_json(gctx, out, $self);
                fz_drop_output(gctx, out);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return res;
        }
    }
};
