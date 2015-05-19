#ifndef MUPDF_PDF_XREF_H
#define MUPDF_PDF_XREF_H

/*
	pdf_create_object: Allocate a slot in the xref table and return a fresh unused object number.
*/
int pdf_create_object(fz_context *ctx, pdf_document *doc);

/*
	pdf_delete_object: Remove object from xref table, marking the slot as free.
*/
void pdf_delete_object(fz_context *ctx, pdf_document *doc, int num);

/*
	pdf_update_object: Replace object in xref table with the passed in object.
*/
void pdf_update_object(fz_context *ctx, pdf_document *doc, int num, pdf_obj *obj);

/*
	pdf_update_stream: Replace stream contents for object in xref table with the passed in buffer.

	The buffer contents must match the /Filter setting if 'compressed' is true.
	If 'compressed' is false, the /Filter and /DecodeParms entries are deleted.
	The /Length entry is updated.
*/
void pdf_update_stream(fz_context *ctx, pdf_document *doc, pdf_obj *ref, fz_buffer *buf, int compressed);

/*
 * xref and object / stream api
 */

typedef struct pdf_xref_entry_s pdf_xref_entry;

struct pdf_xref_entry_s
{
	char type;	/* 0=unset (f)ree i(n)use (o)bjstm */
	unsigned char flags; /* bit 0 = marked */
	unsigned short gen;	/* generation / objstm index */
	int ofs;	/* file offset / objstm object number */
	int stm_ofs;	/* on-disk stream */
	fz_buffer *stm_buf; /* in-memory stream (for updated objects) */
	pdf_obj *obj;	/* stored/cached object */
};

enum
{
	PDF_OBJ_FLAG_MARK = 1,
};

typedef struct pdf_xref_subsec_s pdf_xref_subsec;

struct pdf_xref_subsec_s
{
	pdf_xref_subsec *next;
	int len;
	int start;
	pdf_xref_entry *table;
};

struct pdf_xref_s
{
	int num_objects;
	pdf_xref_subsec *subsec;
	pdf_obj *trailer;
	pdf_obj *pre_repair_trailer;
};

pdf_xref_entry *pdf_cache_object(fz_context *ctx, pdf_document *doc, int num, int gen);

int pdf_count_objects(fz_context *ctx, pdf_document *doc);
pdf_obj *pdf_resolve_indirect(fz_context *ctx, pdf_obj *ref);
pdf_obj *pdf_load_object(fz_context *ctx, pdf_document *doc, int num, int gen);

fz_buffer *pdf_load_raw_stream(fz_context *ctx, pdf_document *doc, int num, int gen);
fz_buffer *pdf_load_stream(fz_context *ctx, pdf_document *doc, int num, int gen);
fz_stream *pdf_open_raw_stream(fz_context *ctx, pdf_document *doc, int num, int gen);
fz_stream *pdf_open_stream(fz_context *ctx, pdf_document *doc, int num, int gen);

fz_stream *pdf_open_inline_stream(fz_context *ctx, pdf_document *doc, pdf_obj *stmobj, int length, fz_stream *chain, fz_compression_params *params);
fz_compressed_buffer *pdf_load_compressed_stream(fz_context *ctx, pdf_document *doc, int num, int gen);
void pdf_load_compressed_inline_image(fz_context *ctx, pdf_document *doc, pdf_obj *dict, int length, fz_stream *cstm, int indexed, fz_image *image);
fz_stream *pdf_open_stream_with_offset(fz_context *ctx, pdf_document *doc, int num, int gen, pdf_obj *dict, int stm_ofs);
fz_stream *pdf_open_compressed_stream(fz_context *ctx, fz_compressed_buffer *);
fz_stream *pdf_open_contents_stream(fz_context *ctx, pdf_document *doc, pdf_obj *obj);
fz_buffer *pdf_load_raw_renumbered_stream(fz_context *ctx, pdf_document *doc, int num, int gen, int orig_num, int orig_gen);
fz_buffer *pdf_load_renumbered_stream(fz_context *ctx, pdf_document *doc, int num, int gen, int orig_num, int orig_gen, int *truncated);
fz_stream *pdf_open_raw_renumbered_stream(fz_context *ctx, pdf_document *doc, int num, int gen, int orig_num, int orig_gen);

pdf_obj *pdf_trailer(fz_context *ctx, pdf_document *doc);
void pdf_set_populating_xref_trailer(fz_context *ctx, pdf_document *doc, pdf_obj *trailer);
int pdf_xref_len(fz_context *ctx, pdf_document *doc);
pdf_xref_entry *pdf_get_populating_xref_entry(fz_context *ctx, pdf_document *doc, int i);
pdf_xref_entry *pdf_get_xref_entry(fz_context *ctx, pdf_document *doc, int i);
void pdf_replace_xref(fz_context *ctx, pdf_document *doc, pdf_xref_entry *entries, int n);
void pdf_xref_ensure_incremental_object(fz_context *ctx, pdf_document *doc, int num);
int pdf_xref_is_incremental(fz_context *ctx, pdf_document *doc, int num);

void pdf_repair_xref(fz_context *ctx, pdf_document *doc);
void pdf_repair_obj_stms(fz_context *ctx, pdf_document *doc);
pdf_obj *pdf_new_ref(fz_context *ctx, pdf_document *doc, pdf_obj *obj);
void pdf_ensure_solid_xref(fz_context *ctx, pdf_document *doc, int num);
void pdf_mark_xref(fz_context *ctx, pdf_document *doc);
void pdf_clear_xref(fz_context *ctx, pdf_document *doc);
void pdf_clear_xref_to_mark(fz_context *ctx, pdf_document *doc);

int pdf_repair_obj(fz_context *ctx, pdf_document *doc, pdf_lexbuf *buf, int *stmofsp, int *stmlenp, pdf_obj **encrypt, pdf_obj **id, pdf_obj **page, int *tmpofs);

pdf_obj *pdf_progressive_advance(fz_context *ctx, pdf_document *doc, int pagenum);

void pdf_print_xref(fz_context *ctx, pdf_document *);

#endif
