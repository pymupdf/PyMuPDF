%module fitz
/*
#define MEMDEBUG
*/
%feature("autodoc","1");
%{
#define SWIG_FILE_WITH_INIT
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

/************************************/
/* our own version of fitz.Identity */
/************************************/
%immutable;
%inline %{
const struct fz_matrix_s Identity = { 1, 0, 0, 1, 0, 0 };
%}
%mutable;

/* include version information */
%include version.i

%include selecthelpers.i

/************************************************************************************/
/* typemap: make sure fz_buffers returned are converted to strings and then dropped */
/************************************************************************************/
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
                PyErr_SetString(PyExc_Exception, "cannot create Document");
                return NULL;
            }
        }
        %pythonprepend fz_document_s(const char *filename, char *stream=NULL, int streamlen=0) %{
            if type(filename) == str:
                pass
            elif type(filename) == unicode:
                filename = filename.encode('utf8')
            else:
                raise TypeError("filename must be a string")
            if not os.path.exists(filename) and streamlen == 0:
                raise IOError("no such file: '%s'" % (filename,))
            self.name = filename
            self.streamlen = streamlen
            self.isClosed = 0
            self.isEncrypted = 0
            self.metadata = None

        %}
        %pythonappend fz_document_s(const char *filename, char *stream=NULL, int streamlen=0) %{
            if this and self.needsPass:
                self.isEncrypted = 1
            # we won't init encrypted doc until it is decrypted
            if this and not self.needsPass:
                self.initData()
                self.thisown = False
        %}
        fz_document_s(const char *filename, char *stream=NULL, int streamlen=0) {
            struct fz_document_s *doc = NULL;
            fz_stream *data = NULL;
            if (streamlen > 0)
                data = fz_open_memory(gctx, stream, streamlen);
            fz_try(gctx)
                if (streamlen == 0)
                    doc = fz_open_document(gctx, filename);
                else
                    doc = fz_open_document_with_stream(gctx, filename, data);

            fz_catch(gctx)
                ;
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
                PyErr_SetString(PyExc_Exception, "cannot loadPage");
                return NULL;
            }
        }
        %pythonprepend loadPage(int) %{
            if self.isClosed == 1:
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
            if self.isClosed == 1:
                raise ValueError("operation on closed document")
        %}
        struct fz_outline_s *_loadOutline() {
            return fz_load_outline(gctx, $self);
        }
        %pythonprepend _dropOutline(struct fz_outline_s *ol) %{
            if self.isClosed == 1:
                raise ValueError("operation on closed document")
        %}
        void _dropOutline(struct fz_outline_s *ol) {
#ifdef MEMDEBUG
            fprintf(stderr, "[DEBUG]free outline\n");
#endif
            fz_drop_outline(gctx, ol);
        }
        %pythonprepend _getPageCount() %{
            if self.isClosed == 1:
                raise ValueError("operation on closed document")
        %}
        int _getPageCount() {
            return fz_count_pages(gctx, $self);
        }

        %pythonprepend _getMetadata(const char *key) %{
            if self.isClosed == 1:
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
            if self.isClosed == 1:
                raise ValueError("operation on closed document")
        %}
        int _needsPass() {
            return fz_needs_password(gctx, $self);
        }

        %pythonprepend authenticate(const char *pass) %{
            if self.isClosed == 1:
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
            if filename == self.name:
                raise ValueError("cannot save to input file")
            if not self.name.lower().endswith(("/pdf", ".pdf")):
                raise ValueError("can only save PDF files")
        %}
        %exception save {
            $action
            if(result) {
                PyErr_SetString(PyExc_Exception, "cannot save Document");
                return NULL;
            }
        }
        int save(char *filename, int garbage=0, int clean=0, int deflate=0, int incremental=0, int ascii=0, int expand=0, int linear=0) {
            /* cast-down fz_document to a pdf_document */
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) return -2;             // not a valid pdf structure, return
            int errors = 0;
            pdf_write_options opts;
            opts.do_incremental = incremental;
            opts.do_ascii = ascii;
            opts.do_deflate = deflate;
            opts.do_expand = expand;
            opts.do_garbage = garbage;
            opts.do_linear = linear;
            opts.do_clean = clean;
            opts.continue_on_error = 1;
            opts.errors = &errors;
            fz_try(gctx)
                pdf_save_document(gctx, pdf, filename, &opts);
            fz_catch(gctx)
                return -1;
            return errors;
        }

        /* typemap for Python list of integers */
        %typemap(in) (int *liste, int argc) {
            int i;
            if (!PySequence_Check($input)) {
                PyErr_SetString(PyExc_ValueError,"expected a sequence");
                return NULL;
            }
            $2 = PySequence_Size($input);
            if (!$2) {
                PyErr_SetString(PyExc_ValueError,"sequence is empty");
                return NULL;
            }
            $1 = (int *) malloc($2*sizeof(int));
            for (i = 0; i < $2; i++) {
                PyObject *o = PySequence_GetItem($input,i);
                if (PyInt_Check(o)) {
                    $1[i] = (int) PyInt_AsLong(o);
                    if ($1[i] < 0) {
                        PyErr_SetString(PyExc_ValueError,"sequence elements must be >= 0");
                        free($1);
                        return NULL;
                        }
                    if ($1[i] >= fz_count_pages(gctx, arg1)) {
                        PyErr_SetString(PyExc_ValueError,"sequence elements must be < pageCount");
                        free($1);
                        return NULL;
                        }
                    }
                else {
                    PyErr_SetString(PyExc_ValueError,"sequence elements must be integers");
                    free($1);
                    return NULL;
                    }
            }
        }
        %typemap(freearg) (int *liste, int argc) {
            if ($1) free($1);
        }

        /************************************************/
        /* reduce document to keep only selected pages  */
        /************************************************/
        int _select(int *liste, int argc) {
            /* cast-down fz_document to a pdf_document */
            pdf_document *pdf = pdf_specifics(gctx, $self);
            if (!pdf) {
                PyErr_SetString(PyExc_ValueError,"not a valid pdf document");
                free(liste);
                return -2;
                }
            globals glo = { 0 };
            glo.ctx = gctx;
            glo.doc = pdf;
            retainpages(gctx, &glo, argc, liste);
            return 0;
        }

        %exception _readPageText {
            $action
            if(!result) {
                PyErr_SetString(PyExc_Exception, "cannot do doc._readPageText");
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
                fz_drop_page(gctx, page);
            }
            return res;
        }

        /***************************************/
        /* get the permissions of the document */
        /***************************************/
        %feature("autodoc","getPermits(self) -> dictionary containing permissions") getPermits;
        %pythonprepend getPermits() %{
            if self.isClosed == 1:
                raise ValueError("operation on closed document")
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
            if (fz_has_permission(gctx, $self, FZ_PERMISSION_PRINT)) permit = permit + 4;
            if (fz_has_permission(gctx, $self, FZ_PERMISSION_EDIT)) permit = permit + 8;
            if (fz_has_permission(gctx, $self, FZ_PERMISSION_COPY)) permit = permit + 16;
            if (fz_has_permission(gctx, $self, FZ_PERMISSION_ANNOTATE)) permit = permit + 32;
            return permit>>2;
        }

        %pythoncode %{
            def initData(self):
                if self.isEncrypted:
                    raise ValueError("cannot initData - document is still encrypted")
                self._outline = self._loadOutline()
                self.metadata = dict([(k,self._getMetadata(v)) for k,v in {'format':'format','title':'info:Title',
                                                                           'author':'info:Author','subject':'info:Subject',
                                                                           'keywords':'info:Keywords','creator':'info:Creator',
                                                                           'producer':'info:Producer','creationDate':'info:CreationDate',
                                                                           'modDate':'info:ModDate'}.items()])
                self.metadata['encryption'] = None if self._getMetadata('encryption')=='None' else self._getMetadata('encryption')

            outline = property(lambda self: self._outline)
            pageCount = property(lambda self: self._getPageCount())
            needsPass = property(lambda self: self._needsPass())

            def __repr__(self):
                if self.streamlen == 0:
                    return "fitz.Document('%s')" % (self.name,)
                return "fitz.Document('%s', stream = <data>, streamlen = %s)" % (self.name, self.streamlen)

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
                PyErr_SetString(PyExc_Exception, "cannot run page");
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
                PyErr_SetString(PyExc_Exception, "cannot do page.readPageText");
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
        %pythoncode %{
            def transform(self, m):
                _fitz._fz_transform_rect(self, m)
                return self

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

        %pythoncode %{
            width = property(lambda self: self.x1-self.x0)
            height = property(lambda self: self.y1-self.y0)

            def getRect(self):
                return Rect(self.x0, self.y0, self.x1, self.y1)

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
                PyErr_SetString(PyExc_Exception, "cannot create Pixmap");
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
        fz_pixmap_s(struct fz_colorspace_s *cs, int w, int h, char *samples) {
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx)
                pm = fz_new_pixmap_with_data(gctx, cs, w, h, samples);
            fz_catch(gctx)
                ;
            return pm;
        }

        /******************************************/
        /* create a pixmap from filename          */
        /******************************************/
        fz_pixmap_s(char *filename) {
            struct fz_image_s *img = NULL;
            fz_try(gctx)
                img = fz_new_image_from_file(gctx, filename);
            fz_catch(gctx)
                ;
            struct fz_pixmap_s *pm = NULL;
            int w = -1;
            fz_try(gctx)
                pm = fz_get_pixmap_from_image(gctx, img, w, w);
            fz_catch(gctx)
                ;
            fz_drop_image(gctx, img);
            return pm;
        }

        /******************************************/
        /* create a pixmap from data area   */
        /******************************************/
        fz_pixmap_s(char *imagedata, int size) {
            struct fz_image_s *img = NULL;
            fz_try(gctx)
                img = fz_new_image_from_data(gctx, imagedata, size);
            fz_catch(gctx)
                ;
            struct fz_pixmap_s *pm = NULL;
            fz_try(gctx)
                pm = fz_get_pixmap_from_image(gctx, img, -1, -1);
            fz_catch(gctx)
                ;
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
                PyErr_SetString(PyExc_Exception, "cannot writePNG");
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

        /************************/
        /* _writeIMG           */
        /************************/
        %exception _writeIMG {
            $action
            if(result) {
                PyErr_SetString(PyExc_Exception, "cannot _writeIMG");
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
                PyErr_SetString(PyExc_Exception, "cannot create Device");
                return NULL;
            }
        }
        DeviceWrapper(struct fz_pixmap_s *pm) {
            struct DeviceWrapper *dw = NULL;
            fz_try(gctx) {
                dw = (struct DeviceWrapper *)calloc(1, sizeof(struct DeviceWrapper));
                dw->device = fz_new_draw_device(gctx, pm);
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
        %pythoncode %{
            def preScale(self, sx, sy):
                _fitz._fz_pre_scale(self, sx, sy)
                return self
            def preShear(self, sx, sy):
                _fitz._fz_pre_shear(self, sx, sy)
                return self
            def preRotate(self, degree):
                _fitz._fz_pre_rotate(self, degree)
                return self

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
                PyErr_SetString(PyExc_Exception, "saveXML failed");
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
                PyErr_SetString(PyExc_Exception, "saveText failed");
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
                PyErr_SetString(PyExc_Exception, "cannot create DisplayList");
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
                PyErr_SetString(PyExc_Exception, "cannot run display list");
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
                PyErr_SetString(PyExc_Exception, "cannot create TextSheet");
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
        /*************************************************/
        /* JSON decoders do not like interspersed "\n" ! */
        /*************************************************/
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
                PyErr_SetString(PyExc_Exception, "cannot create TextPage");
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
                PyErr_SetString(PyExc_Exception, "cannot extract text");
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
                PyErr_SetString(PyExc_Exception, "cannot extract XML text");
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
                PyErr_SetString(PyExc_Exception, "cannot extract HTML text");
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
                PyErr_SetString(PyExc_Exception, "cannot extract JSON text");
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
