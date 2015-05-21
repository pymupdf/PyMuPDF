%module fitz

#define MEMDEBUG

%{
#define SWIG_FILE_WITH_INIT
#include <fitz.h>
%}

/* global context */
%init %{
    gctx = fz_new_context(NULL, NULL, FZ_STORE_UNLIMITED);
    fz_register_document_handlers(gctx);
%}
%header %{
    fz_context *gctx;
%}
    

/* fz_document */
%rename(Document) fz_document_s;
struct fz_document_s {
    %extend {
        fz_document_s(const char *filename) {
            return fz_open_document(gctx, filename);
        }
        ~fz_document_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "free doc\n");
#endif
            fz_drop_document(gctx, $self);
        }
        %pythonappend loadPage(int) %{
            val.thisown = True
        %}
        struct fz_page_s *loadPage(int number) {
            return fz_load_page(gctx, $self, number);
        }
        %pythonappend loadOutline() %{
            val.thisown = True
        %}
        struct fz_outline_s *loadOutline() {
            return fz_load_outline(gctx, $self);
        }
        int _getPageCount() {
            return fz_count_pages(gctx, $self);
        }
        %pythoncode %{
            pageCount = property(_getPageCount)
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
            fprintf(stderr, "free page\n");
#endif
            fz_drop_page(gctx, $self);
        }
        %pythonappend bound() %{
            val.thisown = True
        %}
        struct fz_rect_s *bound() {
            fz_rect *rect = (fz_rect *)malloc(sizeof(fz_rect));
            fz_bound_page(gctx, $self, rect);
            return rect;
        }
        void run(struct fz_device_s *dev, const struct fz_matrix_s *m) {
            fz_run_page(gctx, $self, dev, m, NULL);
        }
        %pythonappend loadLinks() %{
            val.thisown = True
        %}
        struct fz_link_s *loadLinks() {
            return fz_load_links(gctx, $self);
        }
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
#ifdef MEMDEBUG
        ~fz_rect_s() {
            fprintf(stderr, "free rect\n");
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
            fprintf(stderr, "free irect\n");
            free($self);
        }
#endif
        fz_irect_s(const struct fz_irect_s *s) {
            fz_irect *r = (fz_irect *)malloc(sizeof(fz_irect));
            *r = *s;
            return r;
        }
        %pythoncode %{
            width = property(lambda self: self.x1-self.x0)
            height = property(lambda self: self.y1-self.y0)
        %}
    }
};


/* fz_pixmap */
%typemap(out) unsigned char * {
    $result = PyString_FromString((char *)$1);
}
%rename(Pixmap) fz_pixmap_s;
struct fz_pixmap_s
{
    int x, y, w, h, n;
    int interpolate;
    int xres, yres;
    unsigned char *samples;
    %extend {
        fz_pixmap_s(struct fz_colorspace_s *cs, const struct fz_irect_s *bbox) {
            return fz_new_pixmap_with_bbox(gctx, cs, bbox);
        }
        ~fz_pixmap_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "free pixmap\n");
#endif
            fz_drop_pixmap(gctx, $self);
        }
        void clearWith(int value) {
            fz_clear_pixmap_with_value(gctx, $self, value);
        }
        void writePNG(char *filename, int savealpha) {
            fz_write_png(gctx, $self, filename, savealpha);
        }
    }
};


/* fz_colorspace */
#define CS_RGB 1
%inline %{
    #define CS_RGB 1
%}
%rename(Colorspace) fz_colorspace_s;
struct fz_colorspace_s
{
    %extend {
        fz_colorspace_s(int type) {
            switch(type) {
                case CS_RGB:
                default:
                    return fz_device_rgb(gctx);
                    break;
            }
        }
        ~fz_colorspace_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "free colorspace\n");
#endif
            fz_drop_colorspace(gctx, $self);
        }
    } 
};


/* fz_device */
%rename(Device) fz_device_s;
struct fz_device_s
{
    %extend {
        fz_device_s(struct fz_pixmap_s *pm) {
            return fz_new_draw_device(gctx, pm);
        }
        ~fz_device_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "free device\n");
#endif
            fz_drop_device(gctx, $self);
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
            fprintf(stderr, "free matrix\n");
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
        %}
    }
};
%rename(Identity) fz_identity;
%inline %{
    extern const struct fz_matrix_s fz_identity;
%}


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
    %extend {
        ~fz_outline_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "free outline\n");
#endif
            fz_drop_outline(gctx, $self);
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
            fprintf(stderr, "free link_dest\n");
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
            fprintf(stderr, "free point\n");
            free($self);
        }
#endif
        fz_point_s(const struct fz_point_s *q) {
            fz_point *p = (fz_point *)malloc(sizeof(fz_point));
            *p = *q;
            return p;
        }
        %pythoncode %{
            def transform(self, m):
                _fitz._fz_transform_point(self, m)
                return self
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
    int refs;
    struct fz_rect_s rect;
    struct fz_link_dest_s dest;
    struct fz_link_s *next;
    %extend {
        ~fz_link_s() {
#ifdef MEMDEBUG
            fprintf(stderr, "free link\n");
#endif
            fz_drop_link(gctx, $self);
        }
    }
};
%clearnodefaultctor;


