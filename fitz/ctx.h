#include <Python.h>
#include <fitz.h>

typedef struct
{
    fz_context * ctx;
    PyObject * ctx_obj;
    fz_pixmap * pix;
}Pixmap;

typedef struct
{
    fz_context *ctx;
    PyObject *ctx_obj;
    fz_document *doc;
}Document;

typedef struct
{
    Document * doc;
    fz_page * page;
    PyObject * doc_obj;
}Page;

typedef struct
{
    fz_device *dev;
    PyObject *ctx_obj;
}Device;

typedef struct
{
    fz_text_sheet *text_sheet;
    PyObject *ctx_obj;
    fz_context *ctx;
}TextSheet;

typedef struct
{
    fz_display_list *display_list;
    fz_context *ctx;
    PyObject *ctx_obj;
}DisplayList;

typedef struct
{
    fz_text_page *text_page;
    fz_context *ctx;
    PyObject *ctx_obj;
}TextPage;

typedef struct
{
    fz_link *link;
    fz_context *ctx;
    PyObject *ctx_obj;
}Link;

typedef struct
{
    fz_outline *outline;
    fz_context *ctx;
    PyObject *ctx_obj;
}Outline;


void lock_mutex(void *user, int lock);
void unlock_mutex(void *user, int lock);


#define SET_CTX_OBJ(context, context_obj) result->ctx = context;\
result->ctx_obj=context_obj;Py_INCREF(context_obj);

#ifndef DEBUG
#define debug(s)
#else
#define debug(s) fprintf(stderr, s)
#endif

#define DELETE_FZ_PIXMAP_WITH_CTX(self) \
        debug("delete pixmap obj\n");\
        fz_drop_pixmap(self->ctx, self->pix);\
        Py_DECREF(self->ctx_obj);\
        free((void *)self);\
        debug("end delete pix obj\n")

#define DELETE_FZ_DOCUMENT_WITH_CTX(self) \
        debug("delete doc obj\n");\
        fz_close_document(self->doc);\
        Py_DECREF(self->ctx_obj);\
        free((void *)self);\
        debug("end delete doc obj\n")

#define DELETE_FZ_PAGE_WITH_DOC(self) \
        debug("free page obj\n");\
        fz_free_page(self->doc->doc, self->page);\
        Py_DECREF(self->doc_obj);\
        free((void*)self);\
        debug("end free page obj\n")

#define DELETE_FZ_DEVICE_WITH_CTX(self) \
        debug("close dev obj\n");\
        fz_free_device(self->dev);\
        Py_DECREF(self->ctx_obj);\
        free((void *)self);\
        debug("end close dev obj\n")

#define DELETE_FZ_TEXT_SHEET_WITH_CTX(self) \
        debug("free text sheet\n");\
        fz_free_text_sheet(self->ctx, self->text_sheet);\
        Py_DECREF(self->ctx_obj);\
        free((void *)self);\
        debug("end free text sheet\n")

#define DELETE_FZ_DISPLAY_LIST_WITH_CTX(self) \
        debug("free display list\n");\
        fz_free_display_list(self->ctx, self->display_list);\
        Py_DECREF(self->ctx_obj);\
        free((void *)self);\
        debug("end free display list\n")

#define DELETE_FZ_TEXT_PAGE_WITH_CTX(self) \
        debug("free text page\n");\
        fz_free_text_page(self->ctx, self->text_page);\
        Py_DECREF(self->ctx_obj);\
        free((void *)self);\
        debug("end free text page\n")

#define DELETE_FZ_LINK_WITH_CTX(self) \
        debug("free link\n");\
        fz_drop_link(self->ctx, self->link);\
        Py_DECREF(self->ctx_obj);\
        free((void *)self);\
        debug("end free link\n")

#define DELETE_FZ_OUTLINE_WITH_CTX(self) \
        debug("free outline\n");\
        fz_free_outline(self->ctx, self->outline);\
        Py_DECREF(self->ctx_obj);\
        free((void *)self);\
        debug("end free outline\n")

#define DELETE_FZ_CONTEXT_S(self) \
        debug("free ctx\n");\
        fz_free_context(self);\
        debug("end free ctx\n")
