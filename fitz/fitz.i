%module fitz

%{
#define SWIG_FILE_WITH_INIT
#include <fitz.h>
%}

#define FZ_STORE_UNLIMITED 0

#define FZ_VERSION "1.7a"

fz_context *fz_new_context_imp(fz_alloc_context *alloc, fz_locks_context *locks, unsigned int max_store, const char *versio);

void fz_register_document_handlers(fz_context *ctx);

fz_document *fz_open_document(fz_context *ctx, const char *filename);

int fz_count_pages(fz_context *ctx, fz_document *doc);
