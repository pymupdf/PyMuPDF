%module fitz

%{
#define SWIG_FILE_WITH_INIT
#include <fitz.h>
#include "aux.h"
%}

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

typedef struct {
    %immutable;
    fz_document doc;
}Document;

%extend Document {
    Document(const char *filename) {
        return (Document *)fz_open_document(gctx, filename);
    }
    ~Document() {
        fz_drop_document(gctx, (fz_document *)$self);
    }
    int pageCount_get() {
        return fz_count_pages(gctx, (fz_document *)$self);
    }
    %pythoncode %{
        __swig_getmethods__["pageCount"] = _fitz.Document_pageCount_get
        if _newclass:
            pageCount = _swig_property(_fitz.Document_pageCount_get)
    %}
};

void initContext();
void dropContext();
