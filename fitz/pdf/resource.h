#ifndef MUPDF_PDF_RESOURCE_H
#define MUPDF_PDF_RESOURCE_H

/*
 * PDF interface to store
 */
void pdf_store_item(fz_context *ctx, pdf_obj *key, void *val, unsigned int itemsize);
void *pdf_find_item(fz_context *ctx, fz_store_drop_fn *drop, pdf_obj *key);
void pdf_remove_item(fz_context *ctx, fz_store_drop_fn *drop, pdf_obj *key);

/*
 * Functions, Colorspaces, Shadings and Images
 */

fz_function *pdf_load_function(fz_context *ctx, pdf_document *doc, pdf_obj *ref, int in, int out);

fz_colorspace *pdf_load_colorspace(fz_context *ctx, pdf_document *doc, pdf_obj *obj);
int pdf_is_tint_colorspace(fz_context *ctx, fz_colorspace *cs);

fz_shade *pdf_load_shading(fz_context *ctx, pdf_document *doc, pdf_obj *obj);

fz_image *pdf_load_inline_image(fz_context *ctx, pdf_document *doc, pdf_obj *rdb, pdf_obj *dict, fz_stream *file);
int pdf_is_jpx_image(fz_context *ctx, pdf_obj *dict);

fz_image *pdf_load_image(fz_context *ctx, pdf_document *doc, pdf_obj *obj);

/*
 * Pattern
 */

typedef struct pdf_pattern_s pdf_pattern;

struct pdf_pattern_s
{
	fz_storable storable;
	int ismask;
	float xstep;
	float ystep;
	fz_matrix matrix;
	fz_rect bbox;
	pdf_document *document;
	pdf_obj *resources;
	pdf_obj *contents;
};

pdf_pattern *pdf_load_pattern(fz_context *ctx, pdf_document *doc, pdf_obj *obj);
pdf_pattern *pdf_keep_pattern(fz_context *ctx, pdf_pattern *pat);
void pdf_drop_pattern(fz_context *ctx, pdf_pattern *pat);

/*
 * XObject
 */

typedef struct pdf_xobject_s pdf_xobject;

struct pdf_xobject_s
{
	fz_storable storable;
	fz_matrix matrix;
	fz_rect bbox;
	int isolated;
	int knockout;
	int transparency;
	fz_colorspace *colorspace;
	pdf_document *document;
	pdf_obj *resources;
	pdf_obj *contents;
	pdf_obj *me;
	int iteration;
};

pdf_xobject *pdf_load_xobject(fz_context *ctx, pdf_document *doc, pdf_obj *obj);
pdf_obj *pdf_new_xobject(fz_context *ctx, pdf_document *doc, const fz_rect *bbox, const fz_matrix *mat);
pdf_xobject *pdf_keep_xobject(fz_context *ctx, pdf_xobject *xobj);
void pdf_drop_xobject(fz_context *ctx, pdf_xobject *xobj);
void pdf_update_xobject_contents(fz_context *ctx, pdf_document *doc, pdf_xobject *form, fz_buffer *buffer);

void pdf_update_appearance(fz_context *ctx, pdf_document *doc, pdf_annot *annot);

#endif
