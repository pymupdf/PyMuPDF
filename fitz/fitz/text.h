#ifndef MUPDF_FITZ_TEXT_H
#define MUPDF_FITZ_TEXT_H

#include "mupdf/fitz/system.h"
#include "mupdf/fitz/context.h"
#include "mupdf/fitz/font.h"
#include "mupdf/fitz/path.h"

/*
 * Text buffer.
 *
 * The trm field contains the a, b, c and d coefficients.
 * The e and f coefficients come from the individual elements,
 * together they form the transform matrix for the glyph.
 *
 * Glyphs are referenced by glyph ID.
 * The Unicode text equivalent is kept in a separate array
 * with indexes into the glyph array.
 */

typedef struct fz_text_s fz_text;
typedef struct fz_text_item_s fz_text_item;

struct fz_text_item_s
{
	float x, y;
	int gid; /* -1 for one gid to many ucs mappings */
	int ucs; /* -1 for one ucs to many gid mappings */
};

struct fz_text_s
{
	int refs;
	fz_font *font;
	fz_matrix trm;
	int wmode;
	int len, cap;
	fz_text_item *items;
};

fz_text *fz_new_text(fz_context *ctx, fz_font *face, const fz_matrix *trm, int wmode);
fz_text *fz_keep_text(fz_context *ctx, fz_text *text);
void fz_drop_text(fz_context *ctx, fz_text *text);

void fz_add_text(fz_context *ctx, fz_text *text, int gid, int ucs, float x, float y);
fz_rect *fz_bound_text(fz_context *ctx, fz_text *text, const fz_stroke_state *stroke, const fz_matrix *ctm, fz_rect *r);
void fz_print_text(fz_context *ctx, FILE *out, fz_text*);

#endif
