%module fitz

%{
#define SWIG_FILE_WITH_INIT
#include <fitz.h>
%}

/* global context */
%inline %{
    fz_context *gctx = NULL;
    
    void initContext() {
        gctx = fz_new_context(NULL, NULL, FZ_STORE_UNLIMITED);
        fz_register_document_handlers(gctx);
    }
    
    void dropContext() {
        if(!gctx) return;
        fz_drop_context(gctx);
        gctx = NULL;
    }
%}
void initContext();
void dropContext();

/* fz_document */
%rename(Document) fz_document_s;
struct fz_document_s {
    %extend {
        fz_document_s(const char *filename) {
            return fz_open_document(gctx, filename);
        }
        ~fz_document_s() {
            fz_drop_document(gctx, $self);
        }
        int pageCount_get() {
            return fz_count_pages(gctx, $self);
        }
        struct fz_page_s *loadPage(int number) {
            return fz_load_page(gctx, $self, number);
        }
        %pythoncode %{
            __swig_getmethods__["pageCount"] = _fitz.Document_pageCount_get
            if _newclass:
                pageCount = _swig_property(_fitz.Document_pageCount_get)
        %}
    }
};


/* fz_page */
%nodefaultctor;
%rename(Page) fz_page_s;
struct fz_page_s {
    %extend {
        ~fz_page_s() {
            fz_drop_page(gctx, $self);
        }
        struct fz_rect_s *bound() {
            fz_rect *rect = (fz_rect *)malloc(sizeof(fz_rect));
            fz_bound_page(gctx, $self, rect);
            return rect;
        }
        void run(struct fz_device_s *dev, const struct fz_matrix_s *m) {
            fz_run_page(gctx, $self, dev, m, NULL);
        }
    }
};
%clearnodefaultctor;


/* fz_rect */
%rename(Rect) fz_rect_s;
struct fz_rect_s
{
    float x0, y0;
    float x1, y1;
    %extend {
        struct fz_irect_s *round() {
            fz_irect *irect = (fz_irect *)malloc(sizeof(fz_irect));
            fz_round_rect(irect, $self);
            return irect;
        }
        struct fz_rect_s *transform(const struct fz_matrix_s *m) {
            return fz_transform_rect($self, m);
        }
    }
};


/* fz_irect */
%rename(IRect) fz_irect_s;
struct fz_irect_s
{
    int x0, y0;
    int x1, y1;
};


/* fz_pixmap */
%rename(Pixmap) fz_pixmap_s;
struct fz_pixmap_s
{
    int x, y, w, h, n;
    int interpolate;
    int xres, yres;
    %extend {
        fz_pixmap_s(struct fz_colorspace_s *cs, const struct fz_irect_s *bbox) {
            return fz_new_pixmap_with_bbox(gctx, cs, bbox);
        }
        ~fz_pixmap_s() {
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
            fz_drop_device(gctx, $self);
        }
    }
};


/* fz_matrix */
%rename(Matrix) fz_matrix_s;
struct fz_matrix_s
{
    float a, b, c, d, e, f;
    %extend {
        static struct fz_matrix_s *scale(float sx, float sy) {
            fz_matrix *m = (fz_matrix *)malloc(sizeof(fz_matrix));
            return fz_scale(m, sx, sy);
        }
        struct fz_matrix_s *preScale(float sx, float sy) {
            return fz_pre_scale($self, sx, sy);
        }
        static struct fz_matrix_s *shear(float sx, float sy) {
            fz_matrix *m = (fz_matrix *)malloc(sizeof(fz_matrix));
            return fz_shear(m, sx, sy);
        }
        struct fz_matrix_s *preShear(float sx, float sy) {
            return fz_pre_shear($self, sx, sy);
        }
        static struct fz_matrix_s *rotate(float degree) {
            fz_matrix *m = (fz_matrix *)malloc(sizeof(fz_matrix));
            return fz_rotate(m, degree);
        }
        struct fz_matrix_s *preRotate(float degree) {
            return fz_pre_rotate($self, degree);
        }
    }
};
%rename (Identity) fz_identity;
%inline %{
    extern const struct fz_matrix_s fz_identity;
%}
