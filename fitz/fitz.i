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
        fz_page *loadPage(int number) {
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
        fz_rect *bound() {
            return NULL;
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
};

