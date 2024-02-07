%{
/*
# ------------------------------------------------------------------------
# Copyright 2020-2022, Harald Lieder, mailto:harald.lieder@outlook.com
# License: GNU AFFERO GPL 3.0, https://www.gnu.org/licenses/agpl-3.0.html
#
# Part of "PyMuPDF", a Python binding for "MuPDF" (http://mupdf.com), a
# lightweight PDF, XPS, and E-book viewer, renderer and toolkit which is
# maintained and developed by Artifex Software, Inc. https://artifex.com.
# ------------------------------------------------------------------------
*/
// need own versions of ascender / descender
static const float
JM_font_ascender(fz_context *ctx, fz_font *font)
{
    if (skip_quad_corrections) {
        return 0.8f;
    }
    return fz_font_ascender(ctx, font);
}

static const float
JM_font_descender(fz_context *ctx, fz_font *font)
{
    if (skip_quad_corrections) {
        return -0.2f;
    }
    return fz_font_descender(ctx, font);
}


//----------------------------------------------------------------
// Return true if character is considered to be a word delimiter
//----------------------------------------------------------------
static const int 
JM_is_word_delimiter(int c, PyObject *delimiters)
{
    if (c <= 32 || c == 160) return 1;  // a standard delimiter

    // extra delimiters must be a non-empty sequence
    if (!delimiters || PyObject_Not(delimiters) || !PySequence_Check(delimiters)) {  
        return 0;
    }

    // convert to tuple for easier looping
    PyObject *delims = PySequence_Tuple(delimiters);
    if (!delims) {
        PyErr_Clear();
        return 0;
    }

    // Make 1-char PyObject from character given as integer
    PyObject *cchar = Py_BuildValue("C", c);  // single character PyObject
    Py_ssize_t i, len = PyTuple_Size(delims);
    for (i = 0; i < len; i++) {
        int rc = PyUnicode_Compare(cchar, PyTuple_GET_ITEM(delims, i));
        if (rc == 0) {  // equal to a delimiter character
            Py_DECREF(cchar);
            Py_DECREF(delims);
            PyErr_Clear();
            return 1;
        }
    }

    Py_DECREF(delims);
    PyErr_Clear();
    return 0;
}

/*  inactive
//-----------------------------------------------------------------------------
// Make OCR text page directly from an fz_page
//-----------------------------------------------------------------------------
fz_stext_page *
JM_new_stext_page_ocr_from_page(fz_context *ctx, fz_page *page, fz_rect rect, int flags,
        const char *lang, const char *tessdata)
{
    if (!page) return NULL;
    int with_list = 1;
    fz_stext_page *tp = NULL;
    fz_device *dev = NULL, *ocr_dev = NULL;
    fz_var(dev);
    fz_var(ocr_dev);
    fz_var(tp);
    fz_stext_options options;
    memset(&options, 0, sizeof options);
    options.flags = flags;
    //fz_matrix ctm = fz_identity;
    fz_matrix ctm1 = fz_make_matrix(100/72, 0, 0, 100/72, 0, 0);
    fz_matrix ctm2 = fz_make_matrix(400/72, 0, 0, 400/72, 0, 0);

    fz_try(ctx) {
        tp = fz_new_stext_page(ctx, rect);
        dev = fz_new_stext_device(ctx, tp, &options);
        ocr_dev = fz_new_ocr_device(ctx, dev, fz_identity, rect, with_list, lang, tessdata, NULL);
        fz_run_page(ctx, page, ocr_dev, fz_identity, NULL);
        fz_close_device(ctx, ocr_dev);
        fz_close_device(ctx, dev);
    }
    fz_always(ctx) {
        fz_drop_device(ctx, dev);
        fz_drop_device(ctx, ocr_dev);
    }
    fz_catch(ctx) {
        fz_drop_stext_page(ctx, tp);
        fz_rethrow(ctx);
    }
    return tp;
}
*/

//---------------------------------------------------------------------------
// APPEND non-ascii runes in unicode escape format to fz_buffer
//---------------------------------------------------------------------------
void JM_append_rune(fz_context *ctx, fz_buffer *buff, int ch)
{
    if (ch == 92) {  // prevent accidental "\u" etc.
        fz_append_string(ctx, buff, "\\u005c");
    } else if ((ch >= 32 && ch <= 255) || ch == 10) {
        fz_append_byte(ctx, buff, ch);
    } else if (ch >= 0xd800 && ch <= 0xdfff) {  // surrogate Unicode range
        fz_append_string(ctx, buff, "\\ufffd");
    } else if (ch <= 0xffff) {  // 4 hex digits
        fz_append_printf(ctx, buff, "\\u%04x", ch);
    } else {  // 8 hex digits
        fz_append_printf(ctx, buff, "\\U%08x", ch);
    }
}


// re-compute char quad if ascender/descender values make no sense
static fz_quad
JM_char_quad(fz_context *ctx, fz_stext_line *line, fz_stext_char *ch)
{
    if (skip_quad_corrections) {  // no special handling
        return ch->quad;
    }
    if (line->wmode) {  // never touch vertical write mode
        return ch->quad;
    }
    fz_font *font = ch->font;
    float asc = JM_font_ascender(ctx, font);
    float dsc = JM_font_descender(ctx, font);
    float c, s, fsize = ch->size;
    float asc_dsc = asc - dsc + FLT_EPSILON;
    if (asc_dsc >= 1 && small_glyph_heights == 0) {  // no problem
       return ch->quad;
    }
    if (asc < 1e-3) {  // probably Tesseract glyphless font
        dsc = -0.1f;
        asc = 0.9f;
        asc_dsc = 1.0f;
    }

    if (small_glyph_heights || asc_dsc < 1) {
        dsc = dsc / asc_dsc;
        asc = asc / asc_dsc;
    }
    asc_dsc = asc - dsc;
    asc = asc * fsize / asc_dsc;
    dsc = dsc * fsize / asc_dsc;

    /* ------------------------------
    Re-compute quad with the adjusted ascender / descender values:
    Move ch->origin to (0,0) and de-rotate quad, then adjust the corners,
    re-rotate and move back to ch->origin location.
    ------------------------------ */
    fz_matrix trm1, trm2, xlate1, xlate2;
    fz_quad quad;
    c = line->dir.x;  // cosine
    s = line->dir.y;  // sine
    trm1 = fz_make_matrix(c, -s, s, c, 0, 0);  // derotate
    trm2 = fz_make_matrix(c, s, -s, c, 0, 0);  // rotate
    if (c == -1) {  // left-right flip
        trm1.d = 1;
        trm2.d = 1;
    }
    xlate1 = fz_make_matrix(1, 0, 0, 1, -ch->origin.x, -ch->origin.y);
    xlate2 = fz_make_matrix(1, 0, 0, 1, ch->origin.x, ch->origin.y);

    quad = fz_transform_quad(ch->quad, xlate1);  // move origin to (0,0)
    quad = fz_transform_quad(quad, trm1);  // de-rotate corners

    // adjust vertical coordinates
    if (c == 1 && quad.ul.y > 0) {  // up-down flip
        quad.ul.y = asc;
        quad.ur.y = asc;
        quad.ll.y = dsc;
        quad.lr.y = dsc;
    } else {
        quad.ul.y = -asc;
        quad.ur.y = -asc;
        quad.ll.y = -dsc;
        quad.lr.y = -dsc;
    }

    // adjust horizontal coordinates that are too crazy:
    // (1) left x must be >= 0
    // (2) if bbox width is 0, lookup char advance in font.
    if (quad.ll.x < 0) {
        quad.ll.x = 0;
        quad.ul.x = 0;
    }
    float cwidth = quad.lr.x - quad.ll.x;
    if (cwidth < FLT_EPSILON) {
        int glyph = fz_encode_character(ctx, font, ch->c);
        if (glyph) {
            float fwidth = fz_advance_glyph(ctx, font, glyph, line->wmode);
            quad.lr.x = quad.ll.x + fwidth * fsize;
            quad.ur.x = quad.lr.x;
        }
    }

    quad = fz_transform_quad(quad, trm2);  // rotate back
    quad = fz_transform_quad(quad, xlate2);  // translate back
    return quad;
}


// return rect of char quad
static fz_rect
JM_char_bbox(fz_context *ctx, fz_stext_line *line, fz_stext_char *ch)
{
    fz_rect r = fz_rect_from_quad(JM_char_quad(ctx, line, ch));
    if (!line->wmode) {
        return r;
    }
    if (r.y1 < r.y0 + ch->size) {
        r.y0 = r.y1 - ch->size;
    }
    return r;
}


//-------------------------------------------
// make a buffer from an stext_page's text
//-------------------------------------------
fz_buffer *
JM_new_buffer_from_stext_page(fz_context *ctx, fz_stext_page *page)
{
    fz_stext_block *block;
    fz_stext_line *line;
    fz_stext_char *ch;
    fz_rect rect = page->mediabox;
    fz_buffer *buf = NULL;

    fz_try(ctx)
    {
        buf = fz_new_buffer(ctx, 256);
        for (block = page->first_block; block; block = block->next) {
            if (block->type == FZ_STEXT_BLOCK_TEXT) {
                for (line = block->u.t.first_line; line; line = line->next) {
                    for (ch = line->first_char; ch; ch = ch->next) {
                        if (!JM_rects_overlap(rect, JM_char_bbox(ctx, line, ch)) &&
                            !fz_is_infinite_rect(rect)) {
                            continue;
                        }
                        fz_append_rune(ctx, buf, ch->c);
                    }
                    fz_append_byte(ctx, buf, '\n');
                }
                fz_append_byte(ctx, buf, '\n');
            }
        }
    }
    fz_catch(ctx) {
        fz_drop_buffer(ctx, buf);
        fz_rethrow(ctx);
    }
    return buf;
}


static float hdist(fz_point *dir, fz_point *a, fz_point *b)
{
    float dx = b->x - a->x;
    float dy = b->y - a->y;
    return fz_abs(dx * dir->x + dy * dir->y);
}


static float vdist(fz_point *dir, fz_point *a, fz_point *b)
{
    float dx = b->x - a->x;
    float dy = b->y - a->y;
    return fz_abs(dx * dir->y + dy * dir->x);
}


struct highlight
{
    Py_ssize_t len;
    PyObject *quads;
    float hfuzz, vfuzz;
};


static void on_highlight_char(fz_context *ctx, void *arg, fz_stext_line *line, fz_stext_char *ch)
{
    struct highlight *hits = arg;
    float vfuzz = ch->size * hits->vfuzz;
    float hfuzz = ch->size * hits->hfuzz;
    fz_quad ch_quad = JM_char_quad(ctx, line, ch);
    if (hits->len > 0) {
        PyObject *quad = PySequence_ITEM(hits->quads, hits->len - 1);
        fz_quad end = JM_quad_from_py(quad);
        Py_DECREF(quad);
        if (hdist(&line->dir, &end.lr, &ch_quad.ll) < hfuzz
            && vdist(&line->dir, &end.lr, &ch_quad.ll) < vfuzz
            && hdist(&line->dir, &end.ur, &ch_quad.ul) < hfuzz
            && vdist(&line->dir, &end.ur, &ch_quad.ul) < vfuzz)
        {
            end.ur = ch_quad.ur;
            end.lr = ch_quad.lr;
            quad = JM_py_from_quad(end);
            PyList_SetItem(hits->quads, hits->len - 1, quad);
            return;
        }
    }
    LIST_APPEND_DROP(hits->quads, JM_py_from_quad(ch_quad));
    hits->len++;
}


static inline int canon(int c)
{
	/* TODO: proper unicode case folding */
	/* TODO: character equivalence (a matches ä, etc) */
	if (c == 0xA0 || c == 0x2028 || c == 0x2029)
		return ' ';
	if (c == '\r' || c == '\n' || c == '\t')
		return ' ';
	if (c >= 'A' && c <= 'Z')
		return c - 'A' + 'a';
	return c;
}


static inline int chartocanon(int *c, const char *s)
{
	int n = fz_chartorune(c, s);
	*c = canon(*c);
	return n;
}


static const char *match_string(const char *h, const char *n)
{
	int hc, nc;
	const char *e = h;
	h += chartocanon(&hc, h);
	n += chartocanon(&nc, n);
	while (hc == nc)
	{
		e = h;
		if (hc == ' ')
			do
				h += chartocanon(&hc, h);
			while (hc == ' ');
		else
			h += chartocanon(&hc, h);
		if (nc == ' ')
			do
				n += chartocanon(&nc, n);
			while (nc == ' ');
		else
			n += chartocanon(&nc, n);
	}
	return nc == 0 ? e : NULL;
}


static const char *find_string(const char *s, const char *needle, const char **endp)
{
    const char *end;
    while (*s)
    {
        end = match_string(s, needle);
        if (end)
            return *endp = end, s;
        ++s;
    }
    return *endp = NULL, NULL;
}


PyObject *
JM_search_stext_page(fz_context *ctx, fz_stext_page *page, const char *needle)
{
    struct highlight hits;
    fz_stext_block *block;
    fz_stext_line *line;
    fz_stext_char *ch;
    fz_buffer *buffer = NULL;
    const char *haystack, *begin, *end;
    fz_rect rect = page->mediabox;
    int c, inside;

    if (strlen(needle) == 0) Py_RETURN_NONE;
    PyObject *quads = PyList_New(0);
    hits.len = 0;
    hits.quads = quads;
    hits.hfuzz = 0.2f; /* merge kerns but not large gaps */
    hits.vfuzz = 0.1f;

    fz_try(ctx) {
        buffer = JM_new_buffer_from_stext_page(ctx, page);
        haystack = fz_string_from_buffer(ctx, buffer);
        begin = find_string(haystack, needle, &end);
        if (!begin) goto no_more_matches;

        inside = 0;
        for (block = page->first_block; block; block = block->next) {
            if (block->type != FZ_STEXT_BLOCK_TEXT) {
                continue;
            }
            for (line = block->u.t.first_line; line; line = line->next) {
                for (ch = line->first_char; ch; ch = ch->next) {
                    if (!fz_is_infinite_rect(rect) &&
                        !JM_rects_overlap(rect, JM_char_bbox(ctx, line, ch))) {
                            goto next_char;
                        }
try_new_match:
                    if (!inside) {
                        if (haystack >= begin) inside = 1;
                    }
                    if (inside) {
                        if (haystack < end) {
                            on_highlight_char(ctx, &hits, line, ch);
                        } else {
                            inside = 0;
                            begin = find_string(haystack, needle, &end);
                            if (!begin) goto no_more_matches;
                            else goto try_new_match;
                        }
                    }
                    haystack += fz_chartorune(&c, haystack);
next_char:;
                }
                assert(*haystack == '\n');
                ++haystack;
            }
            assert(*haystack == '\n');
            ++haystack;
        }
no_more_matches:;
    }
    fz_always(ctx)
        fz_drop_buffer(ctx, buffer);
    fz_catch(ctx)
        fz_rethrow(ctx);

    return quads;
}


//-----------------------------------------------------------------------------
// Plain text output. An identical copy of fz_print_stext_page_as_text,
// but lines within a block are concatenated by space instead a new-line
// character (which else leads to 2 new-lines).
//-----------------------------------------------------------------------------
void
JM_print_stext_page_as_text(fz_context *ctx, fz_buffer *buff, fz_stext_page *page)
{
    fz_stext_block *block;
    fz_stext_line *line;
    fz_stext_char *ch;
    fz_rect rect = page->mediabox;
    fz_rect chbbox;
    int last_char = 0;
    char utf[10];
    int i, n;

    for (block = page->first_block; block; block = block->next) {
        if (block->type == FZ_STEXT_BLOCK_TEXT) {
            for (line = block->u.t.first_line; line; line = line->next) {
                last_char = 0;
                for (ch = line->first_char; ch; ch = ch->next) {
                    chbbox = JM_char_bbox(ctx, line, ch);
                    if (fz_is_infinite_rect(rect) ||
                        JM_rects_overlap(rect, chbbox)) {
                        last_char = ch->c;
                        JM_append_rune(ctx, buff, ch->c);
                    }
                }
                if (last_char != 10 && last_char > 0) {
                    fz_append_string(ctx, buff, "\n");
                }
            }
        }
    }
}

//-----------------------------------------------------------------------------
// Functions for wordlist output
//-----------------------------------------------------------------------------
int JM_append_word(fz_context *ctx, PyObject *lines, fz_buffer *buff, fz_rect *wbbox,
                   int block_n, int line_n, int word_n)
{
    PyObject *s = JM_EscapeStrFromBuffer(ctx, buff);
    PyObject *litem = Py_BuildValue("ffffOiii",
                                    wbbox->x0,
                                    wbbox->y0,
                                    wbbox->x1,
                                    wbbox->y1,
                                    s,
                                    block_n, line_n, word_n);
    LIST_APPEND_DROP(lines, litem);
    Py_DECREF(s);
    *wbbox = fz_empty_rect;
    return word_n + 1;                 // word counter
}

//-----------------------------------------------------------------------------
// Functions for dictionary output
//-----------------------------------------------------------------------------

static int detect_super_script(fz_stext_line *line, fz_stext_char *ch)
{
    if (line->wmode == 0 && line->dir.x == 1 && line->dir.y == 0)
        return ch->origin.y < line->first_char->origin.y - ch->size * 0.1f;
    return 0;
}

static int JM_char_font_flags(fz_context *ctx, fz_font *font, fz_stext_line *line, fz_stext_char *ch)
{
    int flags = detect_super_script(line, ch);
    flags += fz_font_is_italic(ctx, font) * TEXT_FONT_ITALIC;
    flags += fz_font_is_serif(ctx, font) * TEXT_FONT_SERIFED;
    flags += fz_font_is_monospaced(ctx, font) * TEXT_FONT_MONOSPACED;
    flags += fz_font_is_bold(ctx, font) * TEXT_FONT_BOLD;
    return flags;
}

static const char *
JM_font_name(fz_context *ctx, fz_font *font)
{
    const char *name = fz_font_name(ctx, font);
    const char *s = strchr(name, '+');
    if (subset_fontnames || s == NULL || s-name != 6) {
        return name;
    }
    return s + 1;
}


static fz_rect
JM_make_spanlist(fz_context *ctx, PyObject *line_dict,
                 fz_stext_line *line, int raw, fz_buffer *buff,
                 fz_rect tp_rect)
{
    PyObject *span = NULL, *char_list = NULL, *char_dict;
    PyObject *span_list = PyList_New(0);
    fz_clear_buffer(ctx, buff);
    fz_stext_char *ch;
    fz_rect span_rect = fz_empty_rect;
    fz_rect line_rect = fz_empty_rect;
    fz_point span_origin = {0, 0};
    typedef struct style_s {
        float size; int flags; const char *font; int color;
        float asc; float desc;
    } char_style;
    char_style old_style = { -1, -1, "", -1, 0, 0 }, style;

    for (ch = line->first_char; ch; ch = ch->next) {
        fz_rect r = JM_char_bbox(ctx, line, ch);
        if (!JM_rects_overlap(tp_rect, r) &&
            !fz_is_infinite_rect(tp_rect)) {
            continue;
        }
        int flags = JM_char_font_flags(ctx, ch->font, line, ch);
        fz_point origin = ch->origin;
        style.size = ch->size;
        style.flags = flags;
        style.font = JM_font_name(ctx, ch->font);
        style.color = ch->color;
        style.asc = JM_font_ascender(ctx, ch->font);
        style.desc = JM_font_descender(ctx, ch->font);

        if (style.size != old_style.size ||
            style.flags != old_style.flags ||
            style.color != old_style.color ||
            strcmp(style.font, old_style.font) != 0) {

            if (old_style.size >= 0) {
                // not first one, output previous
                if (raw) {
                    // put character list in the span
                    DICT_SETITEM_DROP(span, dictkey_chars, char_list);
                    char_list = NULL;
                } else {
                    // put text string in the span
                    DICT_SETITEM_DROP(span, dictkey_text, JM_EscapeStrFromBuffer(ctx, buff));
                    fz_clear_buffer(ctx, buff);
                }

                DICT_SETITEM_DROP(span, dictkey_origin,
                    JM_py_from_point(span_origin));
                DICT_SETITEM_DROP(span, dictkey_bbox,
                    JM_py_from_rect(span_rect));
                line_rect = fz_union_rect(line_rect, span_rect);
                LIST_APPEND_DROP(span_list, span);
                span = NULL;
            }

            span = PyDict_New();
            float asc = style.asc, desc = style.desc;
            if (style.asc < 1e-3) {
                asc = 0.9f;
                desc = -0.1f;
            }

            DICT_SETITEM_DROP(span, dictkey_size, Py_BuildValue("f", style.size));
            DICT_SETITEM_DROP(span, dictkey_flags, Py_BuildValue("i", style.flags));
            DICT_SETITEM_DROP(span, dictkey_font, JM_EscapeStrFromStr(style.font));
            DICT_SETITEM_DROP(span, dictkey_color, Py_BuildValue("i", style.color));
            DICT_SETITEMSTR_DROP(span, "ascender", Py_BuildValue("f", asc));
            DICT_SETITEMSTR_DROP(span, "descender", Py_BuildValue("f", desc));

            old_style = style;
            span_rect = r;
            span_origin = origin;

        }
        span_rect = fz_union_rect(span_rect, r);

        if (raw) {  // make and append a char dict
            char_dict = PyDict_New();
            DICT_SETITEM_DROP(char_dict, dictkey_origin,
                          JM_py_from_point(ch->origin));

            DICT_SETITEM_DROP(char_dict, dictkey_bbox,
                          JM_py_from_rect(r));

            DICT_SETITEM_DROP(char_dict, dictkey_c,
                          Py_BuildValue("C", ch->c));

            if (!char_list) {
                char_list = PyList_New(0);
            }
            LIST_APPEND_DROP(char_list, char_dict);
        } else {  // add character byte to buffer
            JM_append_rune(ctx, buff, ch->c);
        }
    }
    // all characters processed, now flush remaining span
    if (span) {
        if (raw) {
            DICT_SETITEM_DROP(span, dictkey_chars, char_list);
            char_list = NULL;
        } else {
            DICT_SETITEM_DROP(span, dictkey_text, JM_EscapeStrFromBuffer(ctx, buff));
            fz_clear_buffer(ctx, buff);
        }
        DICT_SETITEM_DROP(span, dictkey_origin, JM_py_from_point(span_origin));
        DICT_SETITEM_DROP(span, dictkey_bbox, JM_py_from_rect(span_rect));

        if (!fz_is_empty_rect(span_rect)) {
            LIST_APPEND_DROP(span_list, span);
            line_rect = fz_union_rect(line_rect, span_rect);
        } else {
            Py_DECREF(span);
        }
        span = NULL;
    }
    if (!fz_is_empty_rect(line_rect)) {
        DICT_SETITEM_DROP(line_dict, dictkey_spans, span_list);
    } else {
        DICT_SETITEM_DROP(line_dict, dictkey_spans, span_list);
    }
    return line_rect;
}

static void JM_make_image_block(fz_context *ctx, fz_stext_block *block, PyObject *block_dict)
{
    fz_image *image = block->u.i.image;
    fz_buffer *buf = NULL, *freebuf = NULL;
    fz_compressed_buffer *buffer = fz_compressed_image_buffer(ctx, image);
    fz_var(buf);
    fz_var(freebuf);
    int n = fz_colorspace_n(ctx, image->colorspace);
    int w = image->w;
    int h = image->h;
    const char *ext = NULL;
    int type = FZ_IMAGE_UNKNOWN;
    if (buffer)
        type = buffer->params.type;
    if (type < FZ_IMAGE_BMP || type == FZ_IMAGE_JBIG2)
        type = FZ_IMAGE_UNKNOWN;
    PyObject *bytes = NULL;
    fz_var(bytes);
    fz_try(ctx) {
        if (buffer && type != FZ_IMAGE_UNKNOWN) {
            buf = buffer->buffer;
            ext = JM_image_extension(type);
        } else {
            buf = freebuf = fz_new_buffer_from_image_as_png(ctx, image, fz_default_color_params);
            ext = "png";
        }
        bytes = JM_BinFromBuffer(ctx, buf);
    }
    fz_always(ctx) {
        if (!bytes)
            bytes = JM_BinFromChar("");

        DICT_SETITEM_DROP(block_dict, dictkey_width,
                        Py_BuildValue("i", w));
        DICT_SETITEM_DROP(block_dict, dictkey_height,
                        Py_BuildValue("i", h));
        DICT_SETITEM_DROP(block_dict, dictkey_ext,
                        Py_BuildValue("s", ext));
        DICT_SETITEM_DROP(block_dict, dictkey_colorspace,
                        Py_BuildValue("i", n));
        DICT_SETITEM_DROP(block_dict, dictkey_xres,
                        Py_BuildValue("i", image->xres));
        DICT_SETITEM_DROP(block_dict, dictkey_yres,
                        Py_BuildValue("i", image->xres));
        DICT_SETITEM_DROP(block_dict, dictkey_bpc,
                        Py_BuildValue("i", (int) image->bpc));
        DICT_SETITEM_DROP(block_dict, dictkey_matrix,
                        JM_py_from_matrix(block->u.i.transform));
        DICT_SETITEM_DROP(block_dict, dictkey_size,
                        Py_BuildValue("n", PyBytes_Size(bytes)));
        DICT_SETITEM_DROP(block_dict, dictkey_image, bytes);

        fz_drop_buffer(ctx, freebuf);
    }
    fz_catch(ctx) {;}
    return;
}

static void JM_make_text_block(fz_context *ctx, fz_stext_block *block, PyObject *block_dict, int raw, fz_buffer *buff, fz_rect tp_rect)
{
    fz_stext_line *line;
    PyObject *line_list = PyList_New(0), *line_dict;
    fz_rect block_rect = fz_empty_rect;
    for (line = block->u.t.first_line; line; line = line->next) {
        if (fz_is_empty_rect(fz_intersect_rect(tp_rect, line->bbox)) &&
            !fz_is_infinite_rect(tp_rect)) {
            continue;
        }
        line_dict = PyDict_New();
        fz_rect line_rect = JM_make_spanlist(ctx, line_dict, line, raw, buff, tp_rect);
        block_rect = fz_union_rect(block_rect, line_rect);
        DICT_SETITEM_DROP(line_dict, dictkey_wmode,
                    Py_BuildValue("i", line->wmode));
        DICT_SETITEM_DROP(line_dict, dictkey_dir, JM_py_from_point(line->dir));
        DICT_SETITEM_DROP(line_dict, dictkey_bbox,
                    JM_py_from_rect(line_rect));
        LIST_APPEND_DROP(line_list, line_dict);
    }
    DICT_SETITEM_DROP(block_dict, dictkey_bbox, JM_py_from_rect(block_rect));
    DICT_SETITEM_DROP(block_dict, dictkey_lines, line_list);
    return;
}

void JM_make_textpage_dict(fz_context *ctx, fz_stext_page *tp, PyObject *page_dict, int raw)
{
    fz_stext_block *block;
    fz_buffer *text_buffer = fz_new_buffer(ctx, 128);
    PyObject *block_dict, *block_list = PyList_New(0);
    fz_rect tp_rect = tp->mediabox;
    int block_n = -1;
    for (block = tp->first_block; block; block = block->next) {
        block_n++;
        if (!fz_contains_rect(tp_rect, block->bbox) &&
            !fz_is_infinite_rect(tp_rect) &&
            block->type == FZ_STEXT_BLOCK_IMAGE) {
            continue;
        }
        if (!fz_is_infinite_rect(tp_rect) &&
            fz_is_empty_rect(fz_intersect_rect(tp_rect, block->bbox))) {
            continue;
        }

        block_dict = PyDict_New();
        DICT_SETITEM_DROP(block_dict, dictkey_number, Py_BuildValue("i", block_n));
        DICT_SETITEM_DROP(block_dict, dictkey_type, Py_BuildValue("i", block->type));
        if (block->type == FZ_STEXT_BLOCK_IMAGE) {
            DICT_SETITEM_DROP(block_dict, dictkey_bbox, JM_py_from_rect(block->bbox));
            JM_make_image_block(ctx, block, block_dict);
        } else {
            JM_make_text_block(ctx, block, block_dict, raw, text_buffer, tp_rect);
        }

        LIST_APPEND_DROP(block_list, block_dict);
    }
    DICT_SETITEM_DROP(page_dict, dictkey_blocks, block_list);
    fz_drop_buffer(ctx, text_buffer);
}



//---------------------------------------------------------------------
PyObject *
JM_copy_rectangle(fz_context *ctx, fz_stext_page *page, fz_rect area)
{
	fz_stext_block *block;
	fz_stext_line *line;
	fz_stext_char *ch;
	fz_buffer *buffer;
	int need_new_line = 0;
	PyObject *rc = NULL;
	fz_try(ctx) {
        buffer = fz_new_buffer(ctx, 1024);
		for (block = page->first_block; block; block = block->next) {
			if (block->type != FZ_STEXT_BLOCK_TEXT)
				continue;
			for (line = block->u.t.first_line; line; line = line->next) {
				int line_had_text = 0;
				for (ch = line->first_char; ch; ch = ch->next) {
					fz_rect r = JM_char_bbox(ctx, line, ch);
					if (JM_rects_overlap(area, r)) {
						line_had_text = 1;
						if (need_new_line) {
							fz_append_string(ctx, buffer, "\n");
							need_new_line = 0;
						}
						JM_append_rune(ctx, buffer, ch->c);
					}
				}
				if (line_had_text)
					need_new_line = 1;
			}
		}
		fz_terminate_buffer(ctx, buffer);
        rc = JM_EscapeStrFromBuffer(ctx, buffer);
        if (!rc) {
            rc = EMPTY_STRING;
            PyErr_Clear();
        }
	}
    fz_always(ctx) {
        fz_drop_buffer(ctx, buffer);
        }
	fz_catch(ctx) {
		fz_rethrow(ctx);
	}
	return rc;
}
//---------------------------------------------------------------------




fz_buffer *JM_object_to_buffer(fz_context *ctx, pdf_obj *what, int compress, int ascii)
{
    fz_buffer *res=NULL;
    fz_output *out=NULL;
    fz_try(ctx) {
        res = fz_new_buffer(ctx, 512);
        out = fz_new_output_with_buffer(ctx, res);
        pdf_print_obj(ctx, out, what, compress, ascii);
    }
    fz_always(ctx) {
        fz_drop_output(ctx, out);
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    fz_terminate_buffer(ctx, res);
    return res;
}

//-----------------------------------------------------------------------------
// Merge the /Resources object created by a text pdf device into the page.
// The device may have created multiple /ExtGState/Alp? and /Font/F? objects.
// These need to be renamed (renumbered) to not overwrite existing page
// objects from previous executions.
// Returns the next available numbers n, m for objects /Alp<n>, /F<m>.
//-----------------------------------------------------------------------------
PyObject *JM_merge_resources(fz_context *ctx, pdf_page *page, pdf_obj *temp_res)
{
    // page objects /Resources, /Resources/ExtGState, /Resources/Font
    pdf_obj *resources = pdf_dict_get(ctx, page->obj, PDF_NAME(Resources));
    pdf_obj *main_extg = pdf_dict_get(ctx, resources, PDF_NAME(ExtGState));
    pdf_obj *main_fonts = pdf_dict_get(ctx, resources, PDF_NAME(Font));

    // text pdf device objects /ExtGState, /Font
    pdf_obj *temp_extg = pdf_dict_get(ctx, temp_res, PDF_NAME(ExtGState));
    pdf_obj *temp_fonts = pdf_dict_get(ctx, temp_res, PDF_NAME(Font));


    int max_alp = -1, max_fonts = -1, i, n;
    char text[20];

    // Handle /Alp objects
    if (pdf_is_dict(ctx, temp_extg))  // any created at all?
    {
        n = pdf_dict_len(ctx, temp_extg);
        if (pdf_is_dict(ctx, main_extg)) {  // does page have /ExtGState yet?
            for (i = 0; i < pdf_dict_len(ctx, main_extg); i++) {
                // get highest number of objects named /Alpxxx
                char *alp = (char *) pdf_to_name(ctx, pdf_dict_get_key(ctx, main_extg, i));
                if (strncmp(alp, "Alp", 3) != 0) continue;
                int j = fz_atoi(alp + 3);
                if (j > max_alp) max_alp = j;
            }
        }
        else  // create a /ExtGState for the page
            main_extg = pdf_dict_put_dict(ctx, resources, PDF_NAME(ExtGState), n);

        max_alp += 1;
        for (i = 0; i < n; i++)  // copy over renumbered /Alp objects
        {
            char *alp = (char *) pdf_to_name(ctx, pdf_dict_get_key(ctx, temp_extg, i));
            int j = fz_atoi(alp + 3) + max_alp;
            fz_snprintf(text, sizeof(text), "Alp%d", j);  // new name
            pdf_obj *val = pdf_dict_get_val(ctx, temp_extg, i);
            pdf_dict_puts(ctx, main_extg, text, val);
        }
    }


    if (pdf_is_dict(ctx, main_fonts)) { // has page any fonts yet?
        for (i = 0; i < pdf_dict_len(ctx, main_fonts); i++) { // get max font number
            char *font = (char *) pdf_to_name(ctx, pdf_dict_get_key(ctx, main_fonts, i));
            if (strncmp(font, "F", 1) != 0) continue;
            int j = fz_atoi(font + 1);
            if (j > max_fonts) max_fonts = j;
        }
    }
    else  // create a Resources/Font for the page
        main_fonts = pdf_dict_put_dict(ctx, resources, PDF_NAME(Font), 2);

    max_fonts += 1;
    for (i = 0; i < pdf_dict_len(ctx, temp_fonts); i++) { // copy renumbered fonts
        char *font = (char *) pdf_to_name(ctx, pdf_dict_get_key(ctx, temp_fonts, i));
        int j = fz_atoi(font + 1) + max_fonts;
        fz_snprintf(text, sizeof(text), "F%d", j);
        pdf_obj *val = pdf_dict_get_val(ctx, temp_fonts, i);
        pdf_dict_puts(ctx, main_fonts, text, val);
    }
    return Py_BuildValue("ii", max_alp, max_fonts); // next available numbers
}


//-----------------------------------------------------------------------------
// version of fz_show_string, which covers SMALL CAPS
//-----------------------------------------------------------------------------
fz_matrix
JM_show_string_cs(fz_context *ctx, fz_text *text, fz_font *user_font, fz_matrix trm, const char *s,
	int wmode, int bidi_level, fz_bidi_direction markup_dir, fz_text_language language)
{
	fz_font *font=NULL;
	int gid, ucs;
	float adv;

	while (*s)
	{
		s += fz_chartorune(&ucs, s);
        gid = fz_encode_character_sc(ctx, user_font, ucs);
        if (gid == 0) {
		    gid = fz_encode_character_with_fallback(ctx, user_font, ucs, 0, language, &font);
        } else {
            font = user_font;
        }
		fz_show_glyph(ctx, text, font, trm, gid, ucs, wmode, bidi_level, markup_dir, language);
		adv = fz_advance_glyph(ctx, font, gid, wmode);
		if (wmode == 0)
			trm = fz_pre_translate(trm, adv, 0);
		else
			trm = fz_pre_translate(trm, 0, -adv);
	}

	return trm;
}


//-----------------------------------------------------------------------------
// version of fz_show_string, which also covers UCDN script
//-----------------------------------------------------------------------------
fz_matrix JM_show_string(fz_context *ctx, fz_text *text, fz_font *user_font, fz_matrix trm, const char *s, int wmode, int bidi_level, fz_bidi_direction markup_dir, fz_text_language language, int script)
{
    fz_font *font;
    int gid, ucs;
    float adv;

    while (*s) {
        s += fz_chartorune(&ucs, s);
        gid = fz_encode_character_with_fallback(ctx, user_font, ucs, script, language, &font);
        fz_show_glyph(ctx, text, font, trm, gid, ucs, wmode, bidi_level, markup_dir, language);
        adv = fz_advance_glyph(ctx, font, gid, wmode);
        if (wmode == 0)
            trm = fz_pre_translate(trm, adv, 0);
        else
            trm = fz_pre_translate(trm, 0, -adv);
    }
    return trm;
}


//-----------------------------------------------------------------------------
// return a fz_font from a number of parameters
//-----------------------------------------------------------------------------
fz_font *JM_get_font(fz_context *ctx,
    char *fontname,
    char *fontfile,
    PyObject *fontbuffer,
    int script,
    int lang,
    int ordering,
    int is_bold,
    int is_italic,
    int is_serif,
    int embed)
{
    const unsigned char *data = NULL;
    int size, index=0;
    fz_buffer *res = NULL;
    fz_font *font = NULL;
    fz_try(ctx) {
        if (fontfile) goto have_file;
        if (EXISTS(fontbuffer)) goto have_buffer;
        if (ordering > -1) goto have_cjk;
        if (fontname) goto have_base14;
        goto have_noto;

        // Base-14 or a MuPDF builtin font
        have_base14:;
        font = fz_new_base14_font(ctx, fontname);
        if (font) {
            goto fertig;
        }
        font = fz_new_builtin_font(ctx, fontname, is_bold, is_italic);
        goto fertig;

        // CJK font
        have_cjk:;
        font = fz_new_cjk_font(ctx, ordering);
        goto fertig;

        // fontfile
        have_file:;
        font = fz_new_font_from_file(ctx, NULL, fontfile, index, 0);
        goto fertig;

        // fontbuffer
        have_buffer:;
        res = JM_BufferFromBytes(ctx, fontbuffer);
        font = fz_new_font_from_buffer(ctx, NULL, res, index, 0);
        goto fertig;

        // Check for NOTO font
        have_noto:;
        data = fz_lookup_noto_font(ctx, script, lang, &size, &index);
        if (data) font = fz_new_font_from_memory(ctx, NULL, data, size, index, 0);
        if (font) goto fertig;
        font = fz_load_fallback_font(ctx, script, lang, is_serif, is_bold, is_italic);
        goto fertig;

        fertig:;
        if (!font) {
            RAISEPY(ctx, MSG_FONT_FAILED, PyExc_RuntimeError);
        }
        #if FZ_VERSION_MAJOR == 1 && FZ_VERSION_MINOR >= 22
        // if font allows this, set embedding
        if (!font->flags.never_embed) {
            fz_set_font_embedding(ctx, font, embed);
        }
        #endif
    }
    fz_always(ctx) {
        fz_drop_buffer(ctx, res);
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return font;
}

%}
