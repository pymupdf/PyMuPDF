#ifndef MUPDF_FITZ_DOCUMENT_H
#define MUPDF_FITZ_DOCUMENT_H

#include "mupdf/fitz/system.h"
#include "mupdf/fitz/context.h"
#include "mupdf/fitz/math.h"
#include "mupdf/fitz/device.h"
#include "mupdf/fitz/transition.h"
#include "mupdf/fitz/link.h"
#include "mupdf/fitz/outline.h"

/*
	Document interface
*/
typedef struct fz_document_s fz_document;
typedef struct fz_document_handler_s fz_document_handler;
typedef struct fz_page_s fz_page;
typedef struct fz_annot_s fz_annot;

typedef enum
{
	FZ_PERMISSION_PRINT = 'p',
	FZ_PERMISSION_COPY = 'c',
	FZ_PERMISSION_EDIT = 'e',
	FZ_PERMISSION_ANNOTATE = 'n',
}
fz_permission;

// TODO: move out of this interface (it's pdf specific)
typedef struct fz_write_options_s fz_write_options;

typedef void (fz_document_close_fn)(fz_context *ctx, fz_document *doc);
typedef int (fz_document_needs_password_fn)(fz_context *ctx, fz_document *doc);
typedef int (fz_document_authenticate_password_fn)(fz_context *ctx, fz_document *doc, const char *password);
typedef int (fz_document_has_permission_fn)(fz_context *ctx, fz_document *doc, fz_permission permission);
typedef fz_outline *(fz_document_load_outline_fn)(fz_context *ctx, fz_document *doc);
typedef void (fz_document_layout_fn)(fz_context *ctx, fz_document *doc, float w, float h, float em);
typedef int (fz_document_count_pages_fn)(fz_context *ctx, fz_document *doc);
typedef fz_page *(fz_document_load_page_fn)(fz_context *ctx, fz_document *doc, int number);
typedef int (fz_document_lookup_metadata_fn)(fz_context *ctx, fz_document *doc, const char *key, char *buf, int size);
typedef void (fz_document_write_fn)(fz_context *ctx, fz_document *doc, char *filename, fz_write_options *opts);

typedef fz_link *(fz_page_load_links_fn)(fz_context *ctx, fz_page *page);
typedef fz_rect *(fz_page_bound_page_fn)(fz_context *ctx, fz_page *page, fz_rect *);
typedef void (fz_page_run_page_contents_fn)(fz_context *ctx, fz_page *page, fz_device *dev, const fz_matrix *transform, fz_cookie *cookie);
typedef void (fz_page_drop_page_imp_fn)(fz_context *ctx, fz_page *page);
typedef fz_transition *(fz_page_page_presentation_fn)(fz_context *ctx, fz_page *page, float *duration);

typedef fz_annot *(fz_page_first_annot_fn)(fz_context *ctx, fz_page *page);
typedef fz_annot *(fz_page_next_annot_fn)(fz_context *ctx, fz_page *page, fz_annot *annot);
typedef fz_rect *(fz_page_bound_annot_fn)(fz_context *ctx, fz_page *page, fz_annot *annot, fz_rect *rect);
typedef void (fz_page_run_annot_fn)(fz_context *ctx, fz_page *page, fz_annot *annot, fz_device *dev, const fz_matrix *transform, fz_cookie *cookie);

struct fz_page_s
{
	int refs;
	fz_page_drop_page_imp_fn *drop_page_imp;
	fz_page_bound_page_fn *bound_page;
	fz_page_run_page_contents_fn *run_page_contents;
	fz_page_load_links_fn *load_links;
	fz_page_first_annot_fn *first_annot;
	fz_page_next_annot_fn *next_annot;
	fz_page_bound_annot_fn *bound_annot;
	fz_page_run_annot_fn *run_annot;
	fz_page_page_presentation_fn *page_presentation;
};

struct fz_document_s
{
	int refs;
	fz_document_close_fn *close;
	fz_document_needs_password_fn *needs_password;
	fz_document_authenticate_password_fn *authenticate_password;
	fz_document_has_permission_fn *has_permission;
	fz_document_load_outline_fn *load_outline;
	fz_document_layout_fn *layout;
	fz_document_count_pages_fn *count_pages;
	fz_document_load_page_fn *load_page;
	fz_document_lookup_metadata_fn *lookup_metadata;
	fz_document_write_fn *write;
	int did_layout;
};

typedef fz_document *(fz_document_open_fn)(fz_context *ctx, const char *filename);
typedef fz_document *(fz_document_open_with_stream_fn)(fz_context *ctx, fz_stream *stream);
typedef int (fz_document_recognize_fn)(fz_context *ctx, const char *magic);

struct fz_document_handler_s
{
	fz_document_recognize_fn *recognize;
	fz_document_open_fn *open;
	fz_document_open_with_stream_fn *open_with_stream;
};

extern fz_document_handler pdf_document_handler;
extern fz_document_handler xps_document_handler;
extern fz_document_handler cbz_document_handler;
extern fz_document_handler img_document_handler;
extern fz_document_handler tiff_document_handler;
extern fz_document_handler html_document_handler;
extern fz_document_handler epub_document_handler;

void fz_register_document_handler(fz_context *ctx, const fz_document_handler *handler);

void fz_register_document_handlers(fz_context *ctx);

/*
	fz_open_document: Open a PDF, XPS or CBZ document.

	Open a document file and read its basic structure so pages and
	objects can be located. MuPDF will try to repair broken
	documents (without actually changing the file contents).

	The returned fz_document is used when calling most other
	document related functions. Note that it wraps the context, so
	those functions implicitly can access the global state in
	context.

	filename: a path to a file as it would be given to open(2).
*/
fz_document *fz_open_document(fz_context *ctx, const char *filename);

/*
	fz_open_document_with_stream: Open a PDF, XPS or CBZ document.

	Open a document using the specified stream object rather than
	opening a file on disk.

	magic: a string used to detect document type; either a file name or mime-type.
*/
fz_document *fz_open_document_with_stream(fz_context *ctx, const char *magic, fz_stream *stream);

/*
	fz_new_document: Create and initialize a document struct.
*/
void *fz_new_document(fz_context *ctx, int size);

/*
	fz_drop_document: Release an open document.

	The resource store in the context associated with fz_document
	is emptied, and any allocations for the document are freed when
	the last reference is dropped.

	Does not throw exceptions.
*/
void fz_drop_document(fz_context *ctx, fz_document *doc);

fz_document *fz_keep_document(fz_context *ctx, fz_document *doc);

/*
	fz_needs_password: Check if a document is encrypted with a
	non-blank password.

	Does not throw exceptions.
*/
int fz_needs_password(fz_context *ctx, fz_document *doc);

/*
	fz_authenticate_password: Test if the given password can
	decrypt the document.

	password: The password string to be checked. Some document
	specifications do not specify any particular text encoding, so
	neither do we.

	Does not throw exceptions.
*/
int fz_authenticate_password(fz_context *ctx, fz_document *doc, const char *password);

/*
	fz_load_outline: Load the hierarchical document outline.

	Should be freed by fz_drop_outline.
*/
fz_outline *fz_load_outline(fz_context *ctx, fz_document *doc);

/*
	fz_layout_document: Layout reflowable document types.

	w, h: Page size in points.
	em: Default font size in points.
*/
void fz_layout_document(fz_context *ctx, fz_document *doc, float w, float h, float em);

/*
	fz_count_pages: Return the number of pages in document

	May return 0 for documents with no pages.
*/
int fz_count_pages(fz_context *ctx, fz_document *doc);

/*
	fz_load_page: Load a page.

	After fz_load_page is it possible to retrieve the size of the
	page using fz_bound_page, or to render the page using
	fz_run_page_*. Free the page by calling fz_drop_page.

	number: page number, 0 is the first page of the document.
*/
fz_page *fz_load_page(fz_context *ctx, fz_document *doc, int number);

/*
	fz_load_links: Load the list of links for a page.

	Returns a linked list of all the links on the page, each with
	its clickable region and link destination. Each link is
	reference counted so drop and free the list of links by
	calling fz_drop_link on the pointer return from fz_load_links.

	page: Page obtained from fz_load_page.
*/
fz_link *fz_load_links(fz_context *ctx, fz_page *page);

/*
	fz_new_page: Create and initialize a page struct.
*/
void *fz_new_page(fz_context *ctx, int size);

/*
	fz_bound_page: Determine the size of a page at 72 dpi.

	Does not throw exceptions.
*/
fz_rect *fz_bound_page(fz_context *ctx, fz_page *page, fz_rect *rect);

/*
	fz_run_page: Run a page through a device.

	page: Page obtained from fz_load_page.

	dev: Device obtained from fz_new_*_device.

	transform: Transform to apply to page. May include for example
	scaling and rotation, see fz_scale, fz_rotate and fz_concat.
	Set to fz_identity if no transformation is desired.

	cookie: Communication mechanism between caller and library
	rendering the page. Intended for multi-threaded applications,
	while single-threaded applications set cookie to NULL. The
	caller may abort an ongoing rendering of a page. Cookie also
	communicates progress information back to the caller. The
	fields inside cookie are continually updated while the page is
	rendering.
*/
void fz_run_page(fz_context *ctx, fz_page *page, fz_device *dev, const fz_matrix *transform, fz_cookie *cookie);

/*
	fz_run_page_contents: Run a page through a device. Just the main
	page content, without the annotations, if any.

	page: Page obtained from fz_load_page.

	dev: Device obtained from fz_new_*_device.

	transform: Transform to apply to page. May include for example
	scaling and rotation, see fz_scale, fz_rotate and fz_concat.
	Set to fz_identity if no transformation is desired.

	cookie: Communication mechanism between caller and library
	rendering the page. Intended for multi-threaded applications,
	while single-threaded applications set cookie to NULL. The
	caller may abort an ongoing rendering of a page. Cookie also
	communicates progress information back to the caller. The
	fields inside cookie are continually updated while the page is
	rendering.
*/
void fz_run_page_contents(fz_context *ctx, fz_page *page, fz_device *dev, const fz_matrix *transform, fz_cookie *cookie);

/*
	fz_run_annot: Run an annotation through a device.

	page: Page obtained from fz_load_page.

	annot: an annotation.

	dev: Device obtained from fz_new_*_device.

	transform: Transform to apply to page. May include for example
	scaling and rotation, see fz_scale, fz_rotate and fz_concat.
	Set to fz_identity if no transformation is desired.

	cookie: Communication mechanism between caller and library
	rendering the page. Intended for multi-threaded applications,
	while single-threaded applications set cookie to NULL. The
	caller may abort an ongoing rendering of a page. Cookie also
	communicates progress information back to the caller. The
	fields inside cookie are continually updated while the page is
	rendering.
*/
void fz_run_annot(fz_context *ctx, fz_page *page, fz_annot *annot, fz_device *dev, const fz_matrix *transform, fz_cookie *cookie);

/*
	fz_drop_page: Free a loaded page.

	Does not throw exceptions.
*/
void fz_drop_page(fz_context *ctx, fz_page *page);

/*
	fz_page_presentation: Get the presentation details for a given page.

	duration: NULL, or a pointer to a place to set the page duration in
	seconds. (Will be set to 0 if unspecified).

	Returns: a pointer to a transition structure, or NULL if there isn't
	one.

	Does not throw exceptions.
*/
fz_transition *fz_page_presentation(fz_context *ctx, fz_page *page, float *duration);

/*
	fz_has_permission: Check permission flags on document.
*/
int fz_has_permission(fz_context *ctx, fz_document *doc, fz_permission p);

/*
	fz_lookup_metadata: Retrieve document meta data strings.

	doc: The document to query.

	key: Which meta data key to retrieve...

	Basic information:
		'format'	-- Document format and version.
		'encryption'	-- Description of the encryption used.

	From the document information dictionary:
		'info:Title'
		'info:Author'
		'info:Subject'
		'info:Keywords'
		'info:Creator'
		'info:Producer'
		'info:CreationDate'
		'info:ModDate'

	buf: The buffer to hold the results (a nul-terminated UTF-8 string).

	size: Size of 'buf'.

	Returns the size of the output string (may be larger than 'size' if
	the output was truncated), or -1 if the key is not recognized or found.
*/
int fz_lookup_metadata(fz_context *ctx, fz_document *doc, const char *key, char *buf, int size);

#define FZ_META_FORMAT "format"
#define FZ_META_ENCRYPTION "encryption"

#define FZ_META_INFO_AUTHOR "info:Author"
#define FZ_META_INFO_TITLE "info:Title"

#endif
