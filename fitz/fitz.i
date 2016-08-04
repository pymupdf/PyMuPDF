%module fitz
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
    gctx = fz_new_context(NULL, NULL, FZ_STORE_UNLIMITED);
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

/* include version information */
%include version.i

%include selecthelpers.i

/*******************************************************************************
out-typemap: convert return fz_buffers to strings and drop them
*******************************************************************************/
%typemap(out) struct fz_buffer_s * {
    $result = SWIG_FromCharPtrAndSize((const char *)$1->data, $1->len);
    fz_drop_buffer(gctx, $1);
}

/* fz_document */
%rename(Document) fz_document_s;
struct fz_document_s {
    %extend {
        %exception fz_document_s {
            $action
            if(!result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
        %pythonprepend fz_document_s %{
            if type(filename) == str:
                pass
            elif type(filename) == unicode:
                filename = filename.encode('utf8')
            else:
                raise TypeError("filename must be a string")
            self.name = filename
            if stream:
                self.streamlen = len(stream)
            else:
                self.streamlen = 0
            self.isClosed = 0
            self.isEncrypted = 0
            self.metadata = None

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

        fz_document_s(const char *filename, PyObject *stream=NULL) {
            struct fz_document_s *doc = NULL;
            fz_stream *data = NULL;
            char *streamdata;
            size_t streamlen = 0;
            if (PyByteArray_Check(stream)){
                streamdata = PyByteArray_AsString(stream);
                streamlen = (size_t) PyByteArray_Size(stream);
            }
            if (PyBytes_Check(stream)){
                streamdata = PyBytes_AsString(stream);
                streamlen = (size_t) PyBytes_Size(stream);
            }

            fz_try(gctx) {
                if (streamlen > 0){
                    data = fz_open_memory(gctx, streamdata, streamlen);
                    doc = fz_open_document_with_stream(gctx, filename, data);
                }
                else doc = fz_open_document(gctx, filename);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return doc;
        }

        %pythonprepend close() %{
            if self.isClosed == 1:
                raise ValueError("operation on closed document")
            if hasattr(self, '_outline') and self._outline:
                self._dropOutline(self._outline)
                self._outline = None
            self.metadata = None
            self.isClosed = 1
        %}
        void close() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free doc\n");
#endif
            while($self->refs > 1) {
                fz_drop_document(gctx, $self);
            }
            fz_drop_document(gctx, $self);
        }
        %exception loadPage {
            $action
            if(!result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
        %pythonprepend loadPage(int) %{
            if self.isClosed:
                raise ValueError("operation on closed document")
        %}
        %pythonappend loadPage(int) %{
            if val:
                val.thisown = True
                val.number = number
                val.parent = self
        %}
        struct fz_page_s *loadPage(int number) {
            struct fz_page_s *page = NULL;
            fz_try(gctx)
                page = fz_load_page(gctx, $self, number);
            fz_catch(gctx)
                ;
            return page;
        }

        %pythonprepend _loadOutline() %{
            if self.isClosed:
                raise ValueError("operation on closed document")
        %}
        struct fz_outline_s *_loadOutline() {
            return fz_load_outline(gctx, $self);
        }
        %pythonprepend _dropOutline(struct fz_outline_s *ol) %{
            if self.isClosed:
                raise ValueError("operation on closed document")
        %}
        void _dropOutline(struct fz_outline_s *ol) {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free outline\n");
#endif
            fz_drop_outline(gctx, ol);
        }
        %pythonprepend _getPageCount() %{
            if self.isClosed:
                raise ValueError("operation on closed document")
        %}
        int _getPageCount() {
            return fz_count_pages(gctx, $self);
        }

        %pythonprepend _getMetadata(const char *key) %{
            if self.isClosed:
                raise ValueError("operation on closed document")
        %}
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
        %pythonprepend _needsPass() %{
            if self.isClosed:
                raise ValueError("operation on closed document")
        %}
        int _needsPass() {
            return fz_needs_password(gctx, $self);
        }


        int _getGCTXerrcode() {
            return gctx->error->errcode;
        }

        char *_getGCTXerrmsg() {
            char *value;
            value = gctx->error->message;
            return value;
        }

        %pythonprepend authenticate(const char *pass) %{
            if self.isClosed:
                raise ValueError("operation on closed document")
        %}
        %pythonappend authenticate(const char *pass) %{
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
            if not self.name.lower().endswith("pdf"):
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
        %exception save {
            $action
            if(result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
        int save(char *filename, int garbage=0, int clean=0, int deflate=0, int incremental=0, int ascii=0, int expand=0, int linear=0) {
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


/*******************************************************************************
Insert pages from a source PDF to this PDF
*******************************************************************************/
        %pythonprepend insertPDF %{
            sa = start_at
            fp = from_page
            tp = to_page
            if sa < 0:
                sa = self.pageCount
            if fp <= 0:
                fp = 0
            if tp <= 0 or tp >= docsrc.pageCount:
                tp = docsrc.pageCount - 1

            newtoc = (0 == fp <= tp == docsrc.pageCount-1) and sa == self.pageCount
            
            if newtoc:
                toc1 = self.getToC(simple = False)
                toc2 = docsrc.getToC(simple = False)
                for t in toc2:
                    t[2] = t[2] + sa
                toc = toc1 + toc2
        %}
        
        %pythonappend insertPDF %{
            if links:
                self._do_links(docsrc, from_page=from_page, to_page = to_page,
                               start_at = sa)
            if newtoc:
                self.setToC(toc)
        %}

        %exception insertPDF {
            $action
            if(result < 0) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_ValueError, value);
                return NULL;
            }
        }
        %feature("autodoc","insertPDF(PDFsrc, from_page, to_page, start_at, rotate, links) -> int\nInsert page range [from, to] of source PDF, starting as page number start_at.") insertPDF;

        int insertPDF(struct fz_document_s *docsrc, int from_page=-1, int to_page=-1, int start_at=-1, int rotate=-1, int links = 1) {
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
            fz_try(gctx) {
                if (pdfout == NULL)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "target is not a PDF document");
                if (pdfsrc == NULL)
                    fz_throw(gctx, FZ_ERROR_GENERIC, "source is not a PDF document");
                merge_range(pdfout, pdfsrc, fp, tp, sa, rotate);
            }
            fz_catch(gctx){
                return -1;
            }
            return 0;
        }

/*******************************************************************************
Reduce document to keep only selected pages
Parameter is a Python list / tuple of integers (the wanted page numbers).
*******************************************************************************/
        %exception select {
            $action
            if(result < 0) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_ValueError, value);
                return NULL;
            }
        }
        %feature("autodoc","select(list) -> int; build sub pdf with the pages in list") select;
        %pythonprepend select %{
            if self.isClosed or self.isEncrypted:
                raise ValueError("operation on closed or encrypted document")
        %}
        %pythonappend select %{
            self.initData()
        %}
        int select(PyObject *pyliste) {
        /* preparatory stuff: (1) get underlying pdf document, (2) transform
           Python sequence into integer array
        */
            /* get underlying pdf_document, do some parm checks ***************/
            pdf_document *pdf = pdf_specifics(gctx, $self);
            int argc;
            fz_try(gctx) {
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
            /* transform Python sequence into int array ***********************/
            int pageCount = fz_count_pages(gctx, $self);
            int i;
            int *liste;
            liste = malloc(argc * sizeof(int));
            fz_try(gctx) {
                for (i = 0; i < argc; i++) {
                    PyObject *o = PySequence_GetItem(pyliste, i);
                    if (PyInt_Check(o)) {
                        liste[i] = (int) PyInt_AsLong(o);
                        if ((liste[i] < 0) | (liste[i] >= pageCount)) {
                            fz_throw(gctx, FZ_ERROR_GENERIC, "page numbers not in range");
                            }
                    }
                    else {
                        fz_throw(gctx, FZ_ERROR_GENERIC, "page numbers must be integers");
                    }
                }
            }
            fz_catch(gctx) {
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

        %exception _readPageText {
            $action
            if(!result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_ValueError, value);
                return NULL;
            }
        }

        struct fz_buffer_s *_readPageText(int pno, int output=0) {
            fz_page *page;
            fz_buffer *res;
            fz_try(gctx) {
                page = fz_load_page(gctx, $self, pno);
                res = readPageText(page, output);
                fz_drop_page(gctx, page);
            }
            fz_catch(gctx) {
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
        %pythonprepend getPermits() %{
            if self.isClosed or self.isEncrypted:
                raise ValueError("operation on closed or encrypted document")
        %}
        %pythonappend getPermits() %{
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
        int getPermits() {
            int permit = 0;
            if (fz_has_permission(gctx, $self, FZ_PERMISSION_PRINT))    permit += 4;
            if (fz_has_permission(gctx, $self, FZ_PERMISSION_EDIT))     permit += 8;
            if (fz_has_permission(gctx, $self, FZ_PERMISSION_COPY))     permit += 16;
            if (fz_has_permission(gctx, $self, FZ_PERMISSION_ANNOTATE)) permit += 32;
            return permit>>2;
        }

        %exception _getPageObjNumber {
            $action
            if(!result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_ValueError, value);
                return NULL;
            }
        }

        PyObject *_getPageObjNumber(int pno) {
            /* cast-down fz_document to a pdf_document */
            int pageCount = fz_count_pages(gctx, $self);
            fz_try(gctx) {
                if ((pno < 0) | (pno >= pageCount)) {
                    fz_throw(gctx, FZ_ERROR_GENERIC, "page number out of range");
                }
            }
            fz_catch(gctx) {
                return NULL;
            }
            pdf_document *pdf = pdf_specifics(gctx, $self);
            fz_try(gctx) {
                if (!pdf) {
                    fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
                }
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
/*******************************************************************************
Delete all bookmarks (table of contents)
returns number of outline entries deleted
*******************************************************************************/
        %pythonappend _delToC() %{
            self.initData()
        %}
        int _delToC() {
            pdf_document *pdf = pdf_specifics(gctx, $self); /* conv doc to pdf*/
            if (!pdf) return -2;                            /* not a pdf      */
            pdf_obj *root, *olroot, *first;
            /* get main root */
            root = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Root);
            /* get outline root */
            olroot = pdf_dict_get(gctx, root, PDF_NAME_Outlines);
            if (!olroot) return 0;                          /* no outlines    */
            int objcount, argc, i;
            int *res;
            objcount = 0;
            argc = 0;
            first = pdf_dict_get(gctx, olroot, PDF_NAME_First); /* first outl */
            if (!first) return 0;
            argc = countOutlines(first, argc);         /* get number outlines */
            if (argc < 1) return 0;
            res = malloc(argc * sizeof(int));          /* object number table */
            objcount = fillOLNumbers(res, first, objcount, argc);/* fill table*/
            pdf_dict_del(gctx, olroot, PDF_NAME_First);
            pdf_dict_del(gctx, olroot, PDF_NAME_Last);
            pdf_dict_del(gctx, olroot, PDF_NAME_Count);
            for (i = 0; i < objcount; i++) {
                pdf_delete_object(gctx, pdf, res[i]);     /* del all OL items */
            }
            return objcount;
        }

/*******************************************************************************
Get Xref Number of Outline Root
creates OL root if necessary
*******************************************************************************/
        %exception _getOLRootNumber {
            $action
            if(result < 0) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_ValueError, value);
                return NULL;
            }
        }

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

/*******************************************************************************
Get New Xref Number
*******************************************************************************/
        %exception _getNewXref {
            $action
            if(result < 0) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_ValueError, value);
                return NULL;
            }
        }

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

/*******************************************************************************
Get Length of Xref
*******************************************************************************/
        %exception _getXrefLength {
            $action
            if(result < 0) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_ValueError, value);
                return NULL;
            }
        }

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

/*******************************************************************************
Get Object String by Xref Number
*******************************************************************************/
        %exception _getObjectString {
            $action
            if(!result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_ValueError, value);
                return NULL;
            }
        }

        struct fz_buffer_s *_getObjectString(int xnum)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); /* conv doc to pdf*/
            pdf_obj *obj;
            struct fz_buffer_s *res = NULL;
            fz_output *out;
            fz_try(gctx) {
                if (!pdf) fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                obj = pdf_load_object(gctx, pdf, xnum, 0);
                pdf_print_obj(gctx, out, pdf_resolve_indirect(gctx, obj), 1);
            }
            fz_always(gctx) {
                if (obj) pdf_drop_obj(gctx, obj);
                if (out) fz_drop_output(gctx, out);
            }
            fz_catch(gctx) {
                return NULL;
            }
            return res;
        }

/*******************************************************************************
Delete Object by Xref Number
*******************************************************************************/
        %exception _delObject {
            $action
            if(result < 0) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_ValueError, value);
                return NULL;
            }
        }

        int _delObject(int num)
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

/*******************************************************************************
Update an Xref Number with a new Object
Object given as a string
*******************************************************************************/
        %exception _updateObject {
            $action
            if(result < 0) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_ValueError, value);
                return NULL;
            }
        }

        int _updateObject(int xref, char *text)
        {
            pdf_document *pdf = pdf_specifics(gctx, $self); /* conv doc to pdf*/
            fz_try(gctx) {
                if (!pdf) fz_throw(gctx, FZ_ERROR_GENERIC, "not a PDF document");
            }
            fz_catch(gctx) {
                return -2;
            }
            pdf_obj *new_obj;
            fz_try(gctx) {
                /* create new object based on passed-in string          */
                new_obj = pdf_new_obj_from_str(gctx, pdf, text);
                pdf_update_object(gctx, pdf, xref, new_obj);
            }
            fz_catch(gctx) {
                return gctx->error->errcode;
            }
            return 0;
        }

/*******************************************************************************
Add or update metadata with provided raw string
*******************************************************************************/
        %exception _setMetadata {
            $action
            if(result > 0) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_ValueError, value);
                return NULL;
            }
        }

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
            fz_try(gctx) {
                /* create new /Info object based on passed-in string          */
                new_info = pdf_new_obj_from_str(gctx, pdf, text);
            }
            fz_catch(gctx) {
                return gctx->error->errcode;
            }
            /* replace existing /Info object                                  */
            info = pdf_dict_get(gctx, pdf_trailer(gctx, pdf), PDF_NAME_Info);
            if (info) {
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

/*******************************************************************************
Initialize document: set outline and metadata properties
*******************************************************************************/
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

            %}
    }
};


/* fz_page */
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

        %pythonprepend bound() %{
            if self.parent.isClosed == 1:
                raise ValueError("page operation on closed document")
        %}
        %pythonappend bound() %{
            if val:
                val.thisown = True
        %}
        struct fz_rect_s *bound() {
            fz_rect *rect = (fz_rect *)malloc(sizeof(fz_rect));
            fz_bound_page(gctx, $self, rect);
            return rect;
        }

        %exception run {
            $action
            if(result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
        /***********************************************************/
        /* Page.run()                                              */
        /***********************************************************/
        %pythonprepend run(struct DeviceWrapper *dw, const struct fz_matrix_s *m) %{
            if self.parent.isClosed == 1:
                raise ValueError("page operation on closed document")
        %}
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
        %pythonprepend loadLinks() %{
            if self.parent.isClosed == 1:
                raise ValueError("page operation on closed document")
        %}
        %pythonappend loadLinks() %{
            if val:
                val.thisown = True
        %}
        struct fz_link_s *loadLinks() {
            return fz_load_links(gctx, $self);
        }

        %exception _readPageText {
            $action
            if(!result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_ValueError, value);
                return NULL;
            }
        }

        struct fz_buffer_s *_readPageText(int output=0) {
            fz_buffer *res;
            fz_try(gctx) {
                res = readPageText($self, output);
            }
            fz_catch(gctx) {
                ;
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
        %exception fz_pixmap_s {
            $action
            if(!result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_ValueError, value);
                return NULL;
            }
        }
        /***********************************************************/
        /* create empty pixmap with colorspace and IRect specified */
        /***********************************************************/
        fz_pixmap_s(struct fz_colorspace_s *cs, const struct fz_irect_s *bbox) {
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx)
                pm = fz_new_pixmap_with_bbox(gctx, cs, bbox);
            fz_catch(gctx)
                ;
            return pm;
        }

        /***********************************************************/
        /* create a pixmap from samples data                       */
        /***********************************************************/
        fz_pixmap_s(struct fz_colorspace_s *cs, int w, int h, PyObject *samples) {
            char *data;
            size_t size;
            fz_try(gctx) {
                data = PyByteArray_AsString(samples);
                size = (size_t) PyByteArray_Size(samples);
                if ((cs->n+1) * w * h != size) {
                    fz_throw(gctx, FZ_ERROR_GENERIC,"invalid samples size");
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
        fz_pixmap_s(char *filename) {
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
        fz_pixmap_s(PyObject *imagedata) {
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
                    fz_throw(gctx, FZ_ERROR_GENERIC, "invalid argument type imagedata");
                img = fz_new_image_from_data(gctx, data, size);
                pm = fz_get_pixmap_from_image(gctx, img, -1, -1);
                }
            fz_catch(gctx) {
                if (img) fz_drop_image(gctx, img);
                return NULL;
                }
            fz_drop_image(gctx, img);
            return pm;
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
        void copyPixmap(struct fz_pixmap_s *src, const struct fz_irect_s *bbox) {
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
        %exception writePNG {
            $action
            if(result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
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
                fz_save_pixmap_as_png(gctx, $self, filename, savealpha);
            }
            fz_catch(gctx)
                return 1;
            return 0;
        }

        /**********************/
        /* getPNGData         */
        /**********************/
        PyObject *getPNGData(int savealpha=0) {
            struct fz_buffer_s *res = NULL;
            fz_output *out;
            fz_try(gctx) {
                res = fz_new_buffer(gctx, 1024);
                out = fz_new_output_with_buffer(gctx, res);
                fz_write_pixmap_as_png(gctx, out, $self, savealpha);
                fz_drop_output(gctx, out);
            }
            fz_catch(gctx)
                 ;
            return PyByteArray_FromStringAndSize((const char *)res->data, res->len);
        }

        /**************************************/
        /* samplesRGB                         */
        /* utility to extract samples data    */
        /* without the alpha bytes (RGB only) */
        /**************************************/

        PyObject *samplesRGB() {
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

        PyObject *samplesAlpha() {
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
        %exception _writeIMG {
            $action
            if(result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
        %pythonprepend _writeIMG(char *filename, char *format, int savealpha) %{
            if type(filename) == str:
                pass
            elif type(filename) == unicode:
                filename = filename.encode('utf8')
            else:
                raise TypeError("filename must be a string")
        %}
        int _writeIMG(char *filename, int format, int savealpha=0) {
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
        void invertIRect() {
            fz_invert_pixmap(gctx, $self);
        }
        /*************************/
        /* invertIRect           */
        /*************************/
        void invertIRect(const struct fz_irect_s *irect) {
            fz_invert_pixmap_rect(gctx, $self, irect);
        }

        PyObject *_getSamples() {
            return PyByteArray_FromStringAndSize((const char *)$self->samples, ($self->w)*($self->h)*($self->n));
        }
        %pythoncode %{
            samples = property(lambda self: self._getSamples())
            __len__ = getSize
            width  = w
            height = h

            def __repr__(self):
                cs = {2:"GRAY", 4:"RGB", 5:"CMYK"}
                return "fitz.Pixmap(fitz.cs%s, fitz.IRect(%s, %s, %s, %s))" % (cs[self.n], self.x, self.y, self.x + self.width, self.y + self.height)

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
        fz_colorspace_s(int type) {
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
        %exception DeviceWrapper {
            $action
            if(!result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
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
                ;
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
                ;
            return dw;
        }
        DeviceWrapper(struct fz_stext_sheet_s *ts, struct fz_stext_page_s *tp) {
            struct DeviceWrapper *dw = NULL;
            fz_try(gctx) {
                dw = (struct DeviceWrapper *)calloc(1, sizeof(struct DeviceWrapper));
                dw->device = fz_new_stext_device(gctx, ts, tp);
            }
            fz_catch(gctx)
                ;
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
        %exception saveXML {
            $action
            if(result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
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
                ;
            return res;
        }
        %exception saveText {
            $action
            if(result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
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
                ;
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

            def __len__(self):
                return 2

            def __repr__(self):
                return "fitz.Point" + str((self.x, self.y))
        %}
    }
};


/* fz_link */
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


/* fz_display_list */
%rename(DisplayList) fz_display_list_s;
struct fz_display_list_s {
    %extend {
        %exception fz_display_list_s {
            $action
            if(!result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
        fz_display_list_s() {
            struct fz_display_list_s *dl = NULL;
            fz_try(gctx)
                dl = fz_new_display_list(gctx);
            fz_catch(gctx)
                ;
            return dl;
        }

        ~fz_display_list_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free display list\n");
#endif
            fz_drop_display_list(gctx, $self);
        }
        %exception run {
            $action
            if(result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
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


/* fz_stext_sheet */
%rename(TextSheet) fz_stext_sheet_s;
struct fz_stext_sheet_s {
    %extend {
        %exception fz_stext_sheet_s {
            $action
            if(!result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
        fz_stext_sheet_s() {
            struct fz_stext_sheet_s *ts = NULL;
            fz_try(gctx)
                ts = fz_new_stext_sheet(gctx);
            fz_catch(gctx)
                ;
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

/* fz_stext_page */
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

/* C helper functions for extractJSON */
%{
void
fz_print_rect_json(fz_context *ctx, fz_output *out, fz_rect *bbox) {
    char buf[128];
    /* no buffer overflow! */
    snprintf(buf, sizeof(buf), "\"bbox\":[%g, %g, %g, %g],",
                        bbox->x0, bbox->y0, bbox->x1, bbox->y1);

    fz_printf(ctx, out, "%s", buf);
}

void
fz_print_utf8(fz_context *ctx, fz_output *out, int rune) {
    int i, n;
    char utf[10];
    n = fz_runetochar(utf, rune);
    for (i = 0; i < n; i++) {
        fz_printf(ctx, out, "%c", utf[i]);
    }
}

void
fz_print_span_stext_json(fz_context *ctx, fz_output *out, fz_stext_span *span) {
    fz_stext_char *ch;

    for (ch = span->text; ch < span->text + span->len; ch++)
    {
        switch (ch->c)
        {
            case '\\': fz_printf(ctx, out, "\\\\"); break;
            case '\'': fz_printf(ctx, out, "\\u0027"); break;
            case '"': fz_printf(ctx, out, "\\\""); break;
            case '\b': fz_printf(ctx, out, "\\b"); break;
            case '\f': fz_printf(ctx, out, "\\f"); break;
            case '\n': fz_printf(ctx, out, "\\n"); break;
            case '\r': fz_printf(ctx, out, "\\r"); break;
            case '\t': fz_printf(ctx, out, "\\t"); break;
            default:
                if (ch->c >= 32 && ch->c <= 127) {
                    fz_printf(ctx, out, "%c", ch->c);
                } else {
                    fz_printf(ctx, out, "\\u%04x", ch->c);
                    /*fz_print_utf8(ctx, out, ch->c);*/
                }
                break;
        }
    }
}

void
fz_send_data_base64(fz_context *ctx, fz_output *out, fz_buffer *buffer)
{
    int i, len;
    static const char set[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

    len = buffer->len/3;
    for (i = 0; i < len; i++)
    {
        int c = buffer->data[3*i];
        int d = buffer->data[3*i+1];
        int e = buffer->data[3*i+2];
        /**************************************************/
        /* JSON decoders do not like "\n" in base64 data! */
        /* ==> next 2 lines commented out                 */
        /**************************************************/
        //if ((i & 15) == 0)
        //    fz_printf(ctx, out, "\n");
        fz_printf(ctx, out, "%c%c%c%c", set[c>>2], set[((c&3)<<4)|(d>>4)], set[((d&15)<<2)|(e>>6)], set[e & 63]);
    }
    i *= 3;
    switch (buffer->len-i)
    {
        case 2:
        {
            int c = buffer->data[i];
            int d = buffer->data[i+1];
            fz_printf(ctx, out, "%c%c%c=", set[c>>2], set[((c&3)<<4)|(d>>4)], set[((d&15)<<2)]);
            break;
        }
    case 1:
        {
            int c = buffer->data[i];
            fz_printf(ctx, out, "%c%c==", set[c>>2], set[(c&3)<<4]);
            break;
        }
    default:
    case 0:
        break;
    }
}

void
fz_print_stext_page_json(fz_context *ctx, fz_output *out, fz_stext_page *page)
{
    int block_n;

    fz_printf(ctx, out, "{\n \"len\":%d,\"width\":%g,\"height\":%g,\n \"blocks\":[\n",
                        page->len,
                        page->mediabox.x1 - page->mediabox.x0,
                        page->mediabox.y1 - page->mediabox.y0);

    for (block_n = 0; block_n < page->len; block_n++)
    {
        fz_page_block * page_block = &(page->blocks[block_n]);

        fz_printf(ctx, out, "  {\"type\":%s,", page_block->type == FZ_PAGE_BLOCK_TEXT ? "\"text\"": "\"image\"");

        switch (page->blocks[block_n].type)
        {
            case FZ_PAGE_BLOCK_TEXT:
            {
                fz_stext_block *block = page->blocks[block_n].u.text;
                fz_stext_line *line;

                fz_print_rect_json(ctx, out, &(block->bbox));

                fz_printf(ctx, out, "\n   \"lines\":[\n");

                for (line = block->lines; line < block->lines + block->len; line++)
                {
                    fz_stext_span *span;
                    fz_printf(ctx, out, "      {");
                    fz_print_rect_json(ctx, out, &(line->bbox));

                    fz_printf(ctx, out, "\n       \"spans\":[\n");
                    for (span = line->first_span; span; span = span->next)
                    {
                        fz_printf(ctx, out, "         {");
                        fz_print_rect_json(ctx, out, &(span->bbox));
                        fz_printf(ctx, out, "\n          \"text\":\"");

                        fz_print_span_stext_json(ctx, out, span);

                        fz_printf(ctx, out, "\"\n         }");
                        if (span && (span->next)) {
                            fz_printf(ctx, out, ",\n");
                        }
                    }
                    fz_printf(ctx, out, "\n       ]");  /* spans end */

                    fz_printf(ctx, out, "\n      }");
                    if (line < (block->lines + block->len - 1)) {
                        fz_printf(ctx, out, ",\n");
                    }
                }
                fz_printf(ctx, out, "\n   ]");      /* lines end */
                break;
            }
            case FZ_PAGE_BLOCK_IMAGE:
            {
                fz_image_block *image = page->blocks[block_n].u.image;

                fz_print_rect_json(ctx, out, &(image->bbox));
                fz_printf(ctx, out, "\"imgtype\":%d,\"width\":%d,\"height\":%d,",
                                    image->image->buffer->params.type,
                                    image->image->w,
                                    image->image->h);
                fz_printf(ctx, out, "\"image\":\n");
                if (image->image->buffer == NULL) {
                    fz_printf(ctx, out, "null");
                } else {
                    fz_printf(ctx, out, "\"");
                    fz_send_data_base64(ctx, out, image->image->buffer->buffer);
                    fz_printf(ctx, out, "\"");
                }
                break;
            }
        }

        fz_printf(ctx, out, "\n  }");  /* blocks end */
        if (block_n < (page->len - 1)) {
            fz_printf(ctx, out, ",\n");
        }
    }
    fz_printf(ctx, out, "\n ]\n}");  /* page end */
}
%}

%rename(TextPage) fz_stext_page_s;
struct fz_stext_page_s {
    int len;
    %extend {
        %exception fz_stext_page_s {
            $action
            if(!result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
        fz_stext_page_s() {
            struct fz_stext_page_s *tp = NULL;
            fz_try(gctx)
                tp = fz_new_stext_page(gctx);
            fz_catch(gctx)
                ;
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
        %exception extractText {
            $action
            if(!result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
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
                ;
            }
            return res;
        }
        /*******************************************/
        /* method extractXML()                     */
        /*******************************************/
        %exception extractXML {
            $action
            if(!result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
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
                ;
            }
            return res;
        }
        /*******************************************/
        /* method extractHTML()                    */
        /*******************************************/
        %exception extractHTML {
            $action
            if(!result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
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
                ;
            }
            return res;
        }
        /*******************************************/
        /* method extractJSON()                    */
        /*******************************************/
        %exception extractJSON {
            $action
            if(!result) {
                char *value;
                value = gctx->error->message;
                PyErr_SetString(PyExc_Exception, value);
                return NULL;
            }
        }
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
                ;
            }
            return res;
        }
    }
};
