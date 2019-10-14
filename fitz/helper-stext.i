%{
fz_stext_page *JM_new_stext_page_from_page(fz_context *ctx, fz_page *page, int flags)
{
    if (!page) return NULL;
    fz_stext_page *text = NULL;
    fz_device *dev = NULL;
    fz_var(dev);
    fz_var(text);
    fz_stext_options options;
    options.flags = flags;
    fz_try(ctx)
    {
        text = fz_new_stext_page(ctx, fz_bound_page(ctx, page));
        dev = fz_new_stext_device(ctx, text, &options);
        fz_run_page_contents(ctx, page, dev, fz_identity, NULL);
        fz_close_device(ctx, dev);
    }
    fz_always(ctx)
    {
        fz_drop_device(ctx, dev);
    }
    fz_catch(ctx)
    {
        fz_drop_stext_page(ctx, text);
        fz_rethrow(ctx);
    }
    return text;
}


// Replace MuPDF error rune with character 0xB7
PyObject *JM_repl_char()
{
    const unsigned char data[2] = {194, 183};
    return PyUnicode_FromStringAndSize(data, 2);
}

// append non-ascii runes in unicode escape format
void JM_append_rune(fz_context *ctx, fz_buffer *buff, int ch)
{
    if (ch >= 32 && ch <= 127)
    {
        fz_append_byte(ctx, buff, ch);
    }
    else if (ch <= 0xffff)
    {
        fz_append_printf(ctx, buff, "\\u%04x", ch);
    }
    else
    {
        fz_append_printf(ctx, buff, "\\U%08x", ch);
    }

}


// write non-ascii runes in unicode escape format
void JM_write_rune(fz_context *ctx, fz_output *out, int ch)
{
    if (ch >= 32 && ch <= 127)
    {
        fz_write_byte(ctx, out, ch);
    }
    else if (ch <= 0xffff)
    {
        fz_write_printf(ctx, out, "\\u%04x", ch);
    }
    else
    {
        fz_write_printf(ctx, out, "\\U%08x", ch);
    }
}


//-----------------------------------------------------------------------------
// Plain text output. An identical copy of fz_print_stext_page_as_text,
// but lines within a block are concatenated by space instead a new-line
// character (which else leads to 2 new-lines).
//-----------------------------------------------------------------------------
void
JM_print_stext_page_as_text(fz_context *ctx, fz_output *out, fz_stext_page *page)
{
    fz_stext_block *block;
    fz_stext_line *line;
    fz_stext_char *ch;
    int last_char;

    for (block = page->first_block; block; block = block->next)
    {
        if (block->type == FZ_STEXT_BLOCK_TEXT)
        {
            int line_n = 0;
            for (line = block->u.t.first_line; line; line = line->next)
            {
                if (line_n > 0 && last_char != 10)
                {
                    fz_write_string(ctx, out, "\n");
                }
                line_n++;
                for (ch = line->first_char; ch; ch = ch->next)
                {
                    JM_write_rune(ctx, out, ch->c);
                    last_char = ch->c;
                }
            }
            fz_write_string(ctx, out, "\n");
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
    PyList_Append(lines, litem);
    Py_DECREF(s);
    Py_DECREF(litem);
    wbbox->x0 = wbbox->y0 = wbbox->x1 = wbbox->y1 = 0;
    return word_n + 1;                 // word counter
}

//-----------------------------------------------------------------------------
// Functions for dictionary output
//-----------------------------------------------------------------------------

// create the char rect from its quad
fz_rect JM_char_bbox(fz_stext_line *line, fz_stext_char *ch)
{
    fz_rect r = fz_rect_from_quad(ch->quad);
    if (!fz_is_empty_rect(r)) return r;
    // we need to correct erroneous font!
    if ((r.y1 - r.y0) <= FLT_EPSILON) r.y0 = r.y1 - ch->size;
    if ((r.x1 - r.x0) <= FLT_EPSILON) r.x0 = r.x1 - ch->size;
    return r;
}

static int detect_super_script(fz_stext_line *line, fz_stext_char *ch)
{
    if (line->wmode == 0 && line->dir.x == 1 && line->dir.y == 0)
        return ch->origin.y < line->first_char->origin.y - ch->size * 0.1f;
    return 0;
}

static int JM_char_font_flags(fz_context *ctx, fz_font *font, fz_stext_line *line, fz_stext_char *ch)
{
    int flags = detect_super_script(line, ch);
    flags += fz_font_is_italic(ctx, font) * 2;
    flags += fz_font_is_serif(ctx, font) * 4;
    flags += fz_font_is_monospaced(ctx, font) * 8;
    flags += fz_font_is_bold(ctx, font) * 16;
    return flags;
}

//start-trace
static PyObject *JM_make_spanlist(fz_context *ctx, fz_stext_line *line, int raw, fz_buffer *buff)
{
    PyObject *span = NULL, *char_list = NULL, *char_dict, *val;
    PyObject *span_list = PyList_New(0);
    fz_clear_buffer(ctx, buff);
    fz_stext_char *ch;
    fz_rect span_rect;
    typedef struct style_s
    {float size; int flags; char *font; int color;} char_style;

    char_style old_style = { -1, -1, "", -1 }, style;

    for (ch = line->first_char; ch; ch = ch->next)
    {
        fz_rect r = JM_char_bbox(line, ch);
        int flags = JM_char_font_flags(ctx, ch->font, line, ch);
        style.size = ch->size;
        style.flags = flags;
        style.font = (char *) fz_font_name(ctx, ch->font);
        style.color = ch->color;

        if (style.size != old_style.size ||
            style.flags != old_style.flags ||
            style.color != old_style.color ||
            strcmp(style.font, old_style.font) != 0)  // changed -> new span
        {
            if (old_style.size >= 0)  // not 1st one, output previous span
            {
                if (raw)  // put character list in the span
                {
                    PyDict_SetItem(span, dictkey_chars, char_list);
                    Py_CLEAR(char_list);
                }
                else  // put text string in the span
                {
                    val = JM_EscapeStrFromBuffer(ctx, buff);
                    PyDict_SetItem(span, dictkey_text, val);
                    Py_DECREF(val);
                    fz_clear_buffer(ctx, buff);
                }

                val = JM_py_from_rect(span_rect);
                PyDict_SetItem(span, dictkey_bbox, val);
                Py_DECREF(val);

                PyList_Append(span_list, span);
                Py_CLEAR(span);
            }

            span = PyDict_New();

            val = Py_BuildValue("f", style.size);
            PyDict_SetItem(span, dictkey_size, val);
            Py_DECREF(val);

            val = Py_BuildValue("i", style.flags);
            PyDict_SetItem(span, dictkey_flags, val);
            Py_DECREF(val);

            val = JM_EscapeStrFromStr(style.font);
            PyDict_SetItem(span, dictkey_font, val);
            Py_DECREF(val);

            val = Py_BuildValue("i", style.color);
            PyDict_SetItem(span, dictkey_color, val);
            Py_DECREF(val);

            old_style = style;
            span_rect = r;
        }
        span_rect = fz_union_rect(span_rect, r);
        if (raw)  // make and append a char dict
        {
            char_dict = PyDict_New();

            val = Py_BuildValue("ff", ch->origin.x, ch->origin.y);
            PyDict_SetItem(char_dict, dictkey_origin, val);
            Py_DECREF(val);

            val = Py_BuildValue("ffff", r.x0, r.y0, r.x1, r.y1);
            PyDict_SetItem(char_dict, dictkey_bbox, val);
            Py_DECREF(val);

            val = PyUnicode_FromFormat("%c", ch->c);
            PyDict_SetItem(char_dict, dictkey_c, val);
            Py_DECREF(val);

            if (!char_list)
            {
                char_list = PyList_New(0);
            }
            PyList_Append(char_list, char_dict);
            Py_DECREF(char_dict);
        }
        else  // add character byte to buffer
        {
            JM_append_rune(ctx, buff, ch->c);
        }
    }
    // all characters processed, now flush remaining span
    if (span)
    {
        if (raw)
        {
            PyDict_SetItem(span, dictkey_chars, char_list);
            Py_CLEAR(char_list);
        }
        else
        {
            val = JM_EscapeStrFromBuffer(ctx, buff);
            PyDict_SetItem(span, dictkey_text, val);
            Py_DECREF(val);
            fz_clear_buffer(ctx, buff);
        }
        val = JM_py_from_rect(span_rect);
        PyDict_SetItem(span, dictkey_bbox, val);
        Py_DECREF(val);

        PyList_Append(span_list, span);
        Py_CLEAR(span);
    }
    return span_list;
}

static void JM_make_image_block(fz_context *ctx, fz_stext_block *block, PyObject *block_dict)
{
    fz_color_params color_params = {0};
    fz_image *image = block->u.i.image;
    fz_buffer *buf = NULL, *freebuf = NULL;
    fz_compressed_buffer *buffer = fz_compressed_image_buffer(ctx, image);
    fz_var(buf);
    fz_var(freebuf);
    int n = fz_colorspace_n(ctx, image->colorspace);
    int w = image->w;
    int h = image->h;
    int type = FZ_IMAGE_UNKNOWN;
    if (buffer) type = buffer->params.type;
    const char *ext = NULL;
    PyObject *bytes = JM_BinFromChar(""), *val;
    fz_var(bytes);
    fz_try(ctx)
    {
        if (type == FZ_IMAGE_JPX && !(image->mask))
            {;}
        else if (image->use_colorkey ||
                image->use_decode ||
                image->mask ||
                type < FZ_IMAGE_BMP ||
                type == FZ_IMAGE_JBIG2 ||
                (n != 1 && n != 3 && type == FZ_IMAGE_JPEG))
            type = FZ_IMAGE_UNKNOWN;

        if (type != FZ_IMAGE_UNKNOWN)
        {
            buf = buffer->buffer;
            ext = JM_image_extension(type);
        }
        else
        {
            buf = freebuf = fz_new_buffer_from_image_as_png(ctx, image, color_params);
            ext = "png";
        }
        if (PY_MAJOR_VERSION > 2)
        {
            bytes = JM_BinFromBuffer(ctx, buf);
        }
        else
        {
            bytes = JM_BArrayFromBuffer(ctx, buf);
        }
    }
    fz_always(ctx)
    {
        val = Py_BuildValue("i", w);
        PyDict_SetItem(block_dict, dictkey_width, val);
        Py_DECREF(val);

        val = Py_BuildValue("i", h);
        PyDict_SetItem(block_dict, dictkey_height, val);
        Py_DECREF(val);

        val = Py_BuildValue("s", ext);
        PyDict_SetItem(block_dict, dictkey_ext, val);
        Py_DECREF(val);

        PyDict_SetItem(block_dict, dictkey_image, bytes);
        Py_DECREF(bytes);

        fz_drop_buffer(ctx, freebuf);
    }
    fz_catch(ctx) {;}
    return;

}

static void JM_make_text_block(fz_context *ctx, fz_stext_block *block, PyObject *block_dict, int raw, fz_buffer *buff)
{
    fz_stext_line *line;
    PyObject *line_list = PyList_New(0), *line_dict, *val;

    for (line = block->u.t.first_line; line; line = line->next)
    {
        line_dict = PyDict_New();

        val = Py_BuildValue("i", line->wmode);
        PyDict_SetItem(line_dict, dictkey_wmode, val);
        Py_DECREF(val);

        val = Py_BuildValue("ff", line->dir.x, line->dir.y);
        PyDict_SetItem(line_dict, dictkey_dir, val);
        Py_DECREF(val);

        val = JM_py_from_rect(line->bbox);
        PyDict_SetItem(line_dict, dictkey_bbox, val);
        Py_DECREF(val);

        val = JM_make_spanlist(ctx, line, raw, buff);
        PyDict_SetItem(line_dict, dictkey_spans, val);
        Py_DECREF(val);

        PyList_Append(line_list, line_dict);
        Py_DECREF(line_dict);
    }
    PyDict_SetItem(block_dict, dictkey_lines, line_list);
    Py_DECREF(line_list);
    return;
}

void JM_make_textpage_dict(fz_context *ctx, fz_stext_page *tp, PyObject *page_dict, int raw)
{
    fz_stext_block *block;
    fz_buffer *text_buffer = fz_new_buffer(ctx, 64);
    PyObject *block_dict, *block_list = PyList_New(0), *val;
    for (block = tp->first_block; block; block = block->next)
    {
        block_dict = PyDict_New();

        val = Py_BuildValue("i", block->type);
        PyDict_SetItem(block_dict, dictkey_type, val);
        Py_DECREF(val);

        val = JM_py_from_rect(block->bbox);
        PyDict_SetItem(block_dict, dictkey_bbox, val);
        Py_DECREF(val);

        if (block->type == FZ_STEXT_BLOCK_IMAGE)
        {
            JM_make_image_block(ctx, block, block_dict);
        }
        else
        {
            JM_make_text_block(ctx, block, block_dict, raw, text_buffer);
        }

        PyList_Append(block_list, block_dict);
        Py_DECREF(block_dict);
    }
    PyDict_SetItem(page_dict, dictkey_blocks, block_list);
    Py_DECREF(block_list);
    fz_drop_buffer(ctx, text_buffer);
}
//end-trace

%}
