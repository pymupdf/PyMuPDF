#ifndef MUPDF_PDF_OBJECT_H
#define MUPDF_PDF_OBJECT_H

typedef struct pdf_document_s pdf_document;

/*
 * Dynamic objects.
 * The same type of objects as found in PDF and PostScript.
 * Used by the filters and the mupdf parser.
 */

typedef struct pdf_obj_s pdf_obj;

pdf_obj *pdf_new_null(fz_context *ctx, pdf_document *doc);
pdf_obj *pdf_new_bool(fz_context *ctx, pdf_document *doc, int b);
pdf_obj *pdf_new_int(fz_context *ctx, pdf_document *doc, int i);
pdf_obj *pdf_new_real(fz_context *ctx, pdf_document *doc, float f);
pdf_obj *pdf_new_name(fz_context *ctx, pdf_document *doc, const char *str);
pdf_obj *pdf_new_string(fz_context *ctx, pdf_document *doc, const char *str, int len);
pdf_obj *pdf_new_indirect(fz_context *ctx, pdf_document *doc, int num, int gen);
pdf_obj *pdf_new_array(fz_context *ctx, pdf_document *doc, int initialcap);
pdf_obj *pdf_new_dict(fz_context *ctx, pdf_document *doc, int initialcap);
pdf_obj *pdf_new_rect(fz_context *ctx, pdf_document *doc, const fz_rect *rect);
pdf_obj *pdf_new_matrix(fz_context *ctx, pdf_document *doc, const fz_matrix *mtx);
pdf_obj *pdf_copy_array(fz_context *ctx, pdf_obj *array);
pdf_obj *pdf_copy_dict(fz_context *ctx, pdf_obj *dict);

pdf_obj *pdf_new_obj_from_str(fz_context *ctx, pdf_document *doc, const char *src);

pdf_obj *pdf_keep_obj(fz_context *ctx, pdf_obj *obj);
void pdf_drop_obj(fz_context *ctx, pdf_obj *obj);

/* type queries */
int pdf_is_null(fz_context *ctx, pdf_obj *obj);
int pdf_is_bool(fz_context *ctx, pdf_obj *obj);
int pdf_is_int(fz_context *ctx, pdf_obj *obj);
int pdf_is_real(fz_context *ctx, pdf_obj *obj);
int pdf_is_number(fz_context *ctx, pdf_obj *obj);
int pdf_is_name(fz_context *ctx, pdf_obj *obj);
int pdf_is_string(fz_context *ctx, pdf_obj *obj);
int pdf_is_array(fz_context *ctx, pdf_obj *obj);
int pdf_is_dict(fz_context *ctx, pdf_obj *obj);
int pdf_is_indirect(fz_context *ctx, pdf_obj *obj);
int pdf_is_stream(fz_context *ctx, pdf_document *doc, int num, int gen);
pdf_obj *pdf_resolve_obj(fz_context *ctx, pdf_obj *a);
int pdf_objcmp(fz_context *ctx, pdf_obj *a, pdf_obj *b);
int pdf_objcmp_resolve(fz_context *ctx, pdf_obj *a, pdf_obj *b);

static inline int pdf_name_eq(fz_context *ctx, pdf_obj *a, pdf_obj *b)
{
	if (a == b)
		return 1;
	if (a < PDF_OBJ_NAME__LIMIT && b < PDF_OBJ_NAME__LIMIT)
		return 0;
	return !pdf_objcmp_resolve(ctx, a, b);
}

/* obj marking and unmarking functions - to avoid infinite recursions. */
int pdf_obj_marked(fz_context *ctx, pdf_obj *obj);
int pdf_mark_obj(fz_context *ctx, pdf_obj *obj);
void pdf_unmark_obj(fz_context *ctx, pdf_obj *obj);

/* obj memo functions - allows us to secretly remember "a memo" (a bool) in
 * an object, and to read back whether there was a memo, and if so, what it
 * was. */
void pdf_set_obj_memo(fz_context *ctx, pdf_obj *obj, int memo);
int pdf_obj_memo(fz_context *ctx, pdf_obj *obj, int *memo);

/* obj dirty bit support. */
int pdf_obj_is_dirty(fz_context *ctx, pdf_obj *obj);
void pdf_dirty_obj(fz_context *ctx, pdf_obj *obj);
void pdf_clean_obj(fz_context *ctx, pdf_obj *obj);

/* safe, silent failure, no error reporting on type mismatches */
int pdf_to_bool(fz_context *ctx, pdf_obj *obj);
int pdf_to_int(fz_context *ctx, pdf_obj *obj);
float pdf_to_real(fz_context *ctx, pdf_obj *obj);
char *pdf_to_name(fz_context *ctx, pdf_obj *obj);
char *pdf_to_str_buf(fz_context *ctx, pdf_obj *obj);
pdf_obj *pdf_to_dict(fz_context *ctx, pdf_obj *obj);
int pdf_to_str_len(fz_context *ctx, pdf_obj *obj);
int pdf_to_num(fz_context *ctx, pdf_obj *obj);
int pdf_to_gen(fz_context *ctx, pdf_obj *obj);

int pdf_array_len(fz_context *ctx, pdf_obj *array);
pdf_obj *pdf_array_get(fz_context *ctx, pdf_obj *array, int i);
void pdf_array_put(fz_context *ctx, pdf_obj *array, int i, pdf_obj *obj);
void pdf_array_put_drop(fz_context *ctx, pdf_obj *array, int i, pdf_obj *obj);
void pdf_array_push(fz_context *ctx, pdf_obj *array, pdf_obj *obj);
void pdf_array_push_drop(fz_context *ctx, pdf_obj *array, pdf_obj *obj);
void pdf_array_insert(fz_context *ctx, pdf_obj *array, pdf_obj *obj, int index);
void pdf_array_insert_drop(fz_context *ctx, pdf_obj *array, pdf_obj *obj, int index);
void pdf_array_delete(fz_context *ctx, pdf_obj *array, int index);
int pdf_array_contains(fz_context *ctx, pdf_obj *array, pdf_obj *obj);

int pdf_dict_len(fz_context *ctx, pdf_obj *dict);
pdf_obj *pdf_dict_get_key(fz_context *ctx, pdf_obj *dict, int idx);
pdf_obj *pdf_dict_get_val(fz_context *ctx, pdf_obj *dict, int idx);
void pdf_dict_put_val_drop(fz_context *ctx, pdf_obj *obj, int i, pdf_obj *new_obj);
pdf_obj *pdf_dict_get(fz_context *ctx, pdf_obj *dict, pdf_obj *key);
pdf_obj *pdf_dict_getp(fz_context *ctx, pdf_obj *dict, const char *path);
pdf_obj *pdf_dict_getl(fz_context *ctx, pdf_obj *dict, ...);
pdf_obj *pdf_dict_geta(fz_context *ctx, pdf_obj *dict, pdf_obj *key, pdf_obj *abbrev);
pdf_obj *pdf_dict_gets(fz_context *ctx, pdf_obj *dict, const char *key);
pdf_obj *pdf_dict_getsa(fz_context *ctx, pdf_obj *dict, const char *key, const char *abbrev);
void pdf_dict_put(fz_context *ctx, pdf_obj *dict, pdf_obj *key, pdf_obj *val);
void pdf_dict_put_drop(fz_context *ctx, pdf_obj *dict, pdf_obj *key, pdf_obj *val);
void pdf_dict_puts(fz_context *ctx, pdf_obj *dict, const char *key, pdf_obj *val);
void pdf_dict_puts_drop(fz_context *ctx, pdf_obj *dict, const char *key, pdf_obj *val);
void pdf_dict_putp(fz_context *ctx, pdf_obj *dict, const char *path, pdf_obj *val);
void pdf_dict_putp_drop(fz_context *ctx, pdf_obj *dict, const char *path, pdf_obj *val);
void pdf_dict_putl(fz_context *ctx, pdf_obj *dict, pdf_obj *val, ...);
void pdf_dict_putl_drop(fz_context *ctx, pdf_obj *dict, pdf_obj *val, ...);
void pdf_dict_del(fz_context *ctx, pdf_obj *dict, pdf_obj *key);
void pdf_dict_dels(fz_context *ctx, pdf_obj *dict, const char *key);
void pdf_sort_dict(fz_context *ctx, pdf_obj *dict);

/*
	Recurse through the object structure setting the node's parent_num to num.
	parent_num is used when a subobject is to be changed during a document edit.
	The whole containing hierarchy is moved to the incremental xref section, so
	to be later written out as an incremental file update.
*/
void pdf_set_obj_parent(fz_context *ctx, pdf_obj *obj, int num);

int pdf_obj_refs(fz_context *ctx, pdf_obj *ref);

int pdf_obj_parent_num(fz_context *ctx, pdf_obj *obj);

int pdf_sprint_obj(fz_context *ctx, char *s, int n, pdf_obj *obj, int tight);
int pdf_fprint_obj(fz_context *ctx, FILE *fp, pdf_obj *obj, int tight);
int pdf_output_obj(fz_context *ctx, fz_output *out, pdf_obj *obj, int tight);

#ifndef NDEBUG
void pdf_print_obj(fz_context *ctx, pdf_obj *obj);
void pdf_print_ref(fz_context *ctx, pdf_obj *obj);
#endif

char *pdf_to_utf8(fz_context *ctx, pdf_document *doc, pdf_obj *src);
unsigned short *pdf_to_ucs2(fz_context *ctx, pdf_document *doc, pdf_obj *src);
pdf_obj *pdf_to_utf8_name(fz_context *ctx, pdf_document *doc, pdf_obj *src);
char *pdf_from_ucs2(fz_context *ctx, pdf_document *doc, unsigned short *str);
void pdf_to_ucs2_buf(fz_context *ctx, unsigned short *buffer, pdf_obj *src);

fz_rect *pdf_to_rect(fz_context *ctx, pdf_obj *array, fz_rect *rect);
fz_matrix *pdf_to_matrix(fz_context *ctx, pdf_obj *array, fz_matrix *mat);

pdf_document *pdf_get_indirect_document(fz_context *ctx, pdf_obj *obj);
void pdf_set_str_len(fz_context *ctx, pdf_obj *obj, int newlen);
void pdf_set_int(fz_context *ctx, pdf_obj *obj, int i);

#endif
