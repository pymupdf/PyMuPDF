#ifndef MUPDF_PDF_PAGE_H
#define MUPDF_PDF_PAGE_H

int pdf_lookup_page_number(fz_context *ctx, pdf_document *doc, pdf_obj *pageobj);
int pdf_count_pages(fz_context *ctx, pdf_document *doc);
pdf_obj *pdf_lookup_page_obj(fz_context *ctx, pdf_document *doc, int needle);

/*
	pdf_load_page: Load a page and its resources.

	Locates the page in the PDF document and loads the page and its
	resources. After pdf_load_page is it possible to retrieve the size
	of the page using pdf_bound_page, or to render the page using
	pdf_run_page_*.

	number: page number, where 0 is the first page of the document.
*/
pdf_page *pdf_load_page(fz_context *ctx, pdf_document *doc, int number);

void pdf_drop_page(fz_context *ctx, pdf_page *page);

fz_link *pdf_load_links(fz_context *ctx, pdf_page *page);

/*
	pdf_bound_page: Determine the size of a page.

	Determine the page size in user space units, taking page rotation
	into account. The page size is taken to be the crop box if it
	exists (visible area after cropping), otherwise the media box will
	be used (possibly including printing marks).

	Does not throw exceptions.
*/
fz_rect *pdf_bound_page(fz_context *ctx, pdf_page *page, fz_rect *);

/*
	pdf_run_page: Interpret a loaded page and render it on a device.

	page: A page loaded by pdf_load_page.

	dev: Device used for rendering, obtained from fz_new_*_device.

	ctm: A transformation matrix applied to the objects on the page,
	e.g. to scale or rotate the page contents as desired.
*/
void pdf_run_page(fz_context *ctx, pdf_page *page, fz_device *dev, const fz_matrix *ctm, fz_cookie *cookie);

/*
	pdf_run_page: Interpret a loaded page and render it on a device.

	page: A page loaded by pdf_load_page.

	dev: Device used for rendering, obtained from fz_new_*_device.

	ctm: A transformation matrix applied to the objects on the page,
	e.g. to scale or rotate the page contents as desired.

	cookie: A pointer to an optional fz_cookie structure that can be used
	to track progress, collect errors etc.
*/
void pdf_run_page_with_usage(fz_context *ctx, pdf_document *doc, pdf_page *page, fz_device *dev, const fz_matrix *ctm, char *event, fz_cookie *cookie);

/*
	pdf_run_page_contents: Interpret a loaded page and render it on a device.
	Just the main page contents without the annotations

	page: A page loaded by pdf_load_page.

	dev: Device used for rendering, obtained from fz_new_*_device.

	ctm: A transformation matrix applied to the objects on the page,
	e.g. to scale or rotate the page contents as desired.
*/
void pdf_run_page_contents(fz_context *ctx, pdf_page *page, fz_device *dev, const fz_matrix *ctm, fz_cookie *cookie);

/*
	pdf_page_contents_process_fn: A function used for processing the
	cleaned page contents/resources gathered as part of
	pdf_clean_page_contents.

	buffer: A buffer holding the page contents.

	res: A pdf_obj holding the page resources.

	arg: An opaque arg specific to the particular function.
*/
typedef void (pdf_page_contents_process_fn)(fz_context *ctx, fz_buffer *buffer, pdf_obj *res, void *arg);

/*
	pdf_clean_page_contents: Clean a loaded pages rendering operations,
	with an optional post processing step.

	Firstly, this filters the PDF operators used to avoid (some cases
	of) repetition, and leaves the page in a balanced state with an
	unchanged top level matrix etc. At the same time, the resources
	used by the page contents are collected.

	Next, the resources themselves are cleaned (as appropriate) in the
	same way.

	Next, an optional post processing stage is called.

	Finally, the page contents and resources in the documents page tree
	are replaced by these processed versions.

	Annotations remain unaffected.

	page: A page loaded by pdf_load_page.

	cookie: A pointer to an optional fz_cookie structure that can be used
	to track progress, collect errors etc.
*/
void pdf_clean_page_contents(fz_context *ctx, pdf_document *doc, pdf_page *page, fz_cookie *cookie,
	pdf_page_contents_process_fn *proc, void *proc_arg, int ascii);

/*
	Presentation interface.
*/
fz_transition *pdf_page_presentation(fz_context *ctx, pdf_page *page, float *duration);

/*
 * Page tree, pages and related objects
 */

struct pdf_page_s
{
	fz_page super;
	pdf_document *doc;

	fz_matrix ctm; /* calculated from mediabox and rotate */
	fz_rect mediabox;
	int rotate;
	int transparency;
	pdf_obj *resources;
	pdf_obj *contents;
	fz_link *links;
	pdf_annot *annots;
	pdf_annot **annot_tailp;
	pdf_annot *changed_annots;
	pdf_annot *deleted_annots;
	pdf_annot *tmp_annots;
	pdf_obj *me;
	float duration;
	int transition_present;
	fz_transition transition;
	int incomplete;
};

enum
{
	PDF_PAGE_INCOMPLETE_CONTENTS = 1,
	PDF_PAGE_INCOMPLETE_ANNOTS = 2
};

#endif
