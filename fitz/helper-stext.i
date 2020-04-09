%{
//-----------------------------------------------------------------------------
// Make a text page directly from an fz_page
//-----------------------------------------------------------------------------
fz_stext_page *JM_new_stext_page_from_page(fz_context *ctx, fz_page *page, int flags)
{
    if (!page) return NULL;
    fz_stext_page *text = NULL;
    fz_device *dev = NULL;
    fz_var(dev);
    fz_var(text);
    fz_stext_options options = { 0 };
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


//-----------------------------------------------------------------------------
// Replace MuPDF error rune with character 0xB7
//-----------------------------------------------------------------------------
PyObject *JM_repl_char()
{
    const unsigned char data[2] = {194, 183};
    return PyUnicode_FromStringAndSize(data, 2);
}

//-----------------------------------------------------------------------------
// APPEND non-ascii runes in unicode escape format to a fz_buffer
//-----------------------------------------------------------------------------
void JM_append_rune(fz_context *ctx, fz_buffer *buff, int ch)
{
    if (ch >= 32 && ch <= 127)
    {
        fz_append_byte(ctx, buff, ch);
    }
    else if (ch <= 0xffff)  // 4 hex digits
    {
        fz_append_printf(ctx, buff, "\\u%04x", ch);
    }
    else  // 8 hex digits
    {
        fz_append_printf(ctx, buff, "\\U%08x", ch);
    }
}


//-----------------------------------------------------------------------------
// WRITE non-ascii runes in unicode escape format to a fz_output
//-----------------------------------------------------------------------------
void JM_write_rune(fz_context *ctx, fz_output *out, int ch)
{
    if (ch >= 32 && ch <= 127)
    {
        fz_write_byte(ctx, out, ch);
    }
    else if (ch <= 0xffff)  // 4 hex digits
    {
        fz_write_printf(ctx, out, "\\u%04x", ch);
    }
    else  // 8 hex digits
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
    LIST_APPEND_DROP(lines, litem);
    Py_DECREF(s);
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
    flags += fz_font_is_italic(ctx, font) * TEXT_FONT_ITALIC;
    flags += fz_font_is_serif(ctx, font) * TEXT_FONT_SERIFED;
    flags += fz_font_is_monospaced(ctx, font) * TEXT_FONT_MONOSPACED;
    flags += fz_font_is_bold(ctx, font) * TEXT_FONT_BOLD;
    return flags;
}


static PyObject *JM_make_spanlist(fz_context *ctx, fz_stext_line *line, int raw, fz_buffer *buff)
{
    PyObject *span = NULL, *char_list = NULL, *char_dict;
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
                    DICT_SETITEM_DROP(span, dictkey_chars, char_list);
                    char_list = NULL;
                }
                else  // put text string in the span
                {
                    DICT_SETITEM_DROP(span, dictkey_text, JM_EscapeStrFromBuffer(ctx, buff));
                    fz_clear_buffer(ctx, buff);
                }

                DICT_SETITEM_DROP(span, dictkey_bbox, JM_py_from_rect(span_rect));

                LIST_APPEND_DROP(span_list, span);
                span = NULL;
            }

            span = PyDict_New();

            DICT_SETITEM_DROP(span, dictkey_size, Py_BuildValue("f", style.size));
            DICT_SETITEM_DROP(span, dictkey_flags, Py_BuildValue("i", style.flags));
            DICT_SETITEM_DROP(span, dictkey_font, JM_EscapeStrFromStr(style.font));
            DICT_SETITEM_DROP(span, dictkey_color, Py_BuildValue("i", style.color));

            old_style = style;
            span_rect = r;
        }
        span_rect = fz_union_rect(span_rect, r);
        if (raw)  // make and append a char dict
        {
            char_dict = PyDict_New();

            DICT_SETITEM_DROP(char_dict, dictkey_origin,
                          Py_BuildValue("ff", ch->origin.x, ch->origin.y));

            DICT_SETITEM_DROP(char_dict, dictkey_bbox,
                          Py_BuildValue("ffff", r.x0, r.y0, r.x1, r.y1));

            DICT_SETITEM_DROP(char_dict, dictkey_c,
                          PyUnicode_FromFormat("%c", ch->c));

            if (!char_list)
            {
                char_list = PyList_New(0);
            }
            LIST_APPEND_DROP(char_list, char_dict);
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
            DICT_SETITEM_DROP(span, dictkey_chars, char_list);
            char_list = NULL;
        }
        else
        {
            DICT_SETITEM_DROP(span, dictkey_text, JM_EscapeStrFromBuffer(ctx, buff));
            fz_clear_buffer(ctx, buff);
        }
        DICT_SETITEM_DROP(span, dictkey_bbox, JM_py_from_rect(span_rect));

        LIST_APPEND_DROP(span_list, span);
        span = NULL;
    }
    return span_list;
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
    fz_try(ctx)
    {
        if (buffer && type != FZ_IMAGE_UNKNOWN)
        {
            buf = buffer->buffer;
            ext = JM_image_extension(type);
        }
        else
        {
            buf = freebuf = fz_new_buffer_from_image_as_png(ctx, image, fz_default_color_params);
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
        DICT_SETITEM_DROP(block_dict, dictkey_image, bytes);

        fz_drop_buffer(ctx, freebuf);
    }
    fz_catch(ctx) {;}
    return;
}

static void JM_make_text_block(fz_context *ctx, fz_stext_block *block, PyObject *block_dict, int raw, fz_buffer *buff)
{
    fz_stext_line *line;
    PyObject *line_list = PyList_New(0), *line_dict;

    for (line = block->u.t.first_line; line; line = line->next)
    {
        line_dict = PyDict_New();

        DICT_SETITEM_DROP(line_dict, dictkey_wmode,
                      Py_BuildValue("i", line->wmode));
        DICT_SETITEM_DROP(line_dict, dictkey_dir,
                      Py_BuildValue("ff", line->dir.x, line->dir.y));
        DICT_SETITEM_DROP(line_dict, dictkey_bbox,
                      JM_py_from_rect(line->bbox));
        DICT_SETITEM_DROP(line_dict, dictkey_spans,
                       JM_make_spanlist(ctx, line, raw, buff));

        LIST_APPEND_DROP(line_list, line_dict);
    }
    DICT_SETITEM_DROP(block_dict, dictkey_lines, line_list);
    return;
}

void JM_make_textpage_dict(fz_context *ctx, fz_stext_page *tp, PyObject *page_dict, int raw)
{
    fz_stext_block *block;
    fz_buffer *text_buffer = fz_new_buffer(ctx, 64);
    PyObject *block_dict, *block_list = PyList_New(0);
    for (block = tp->first_block; block; block = block->next)
    {
        block_dict = PyDict_New();

        DICT_SETITEM_DROP(block_dict, dictkey_type, Py_BuildValue("i", block->type));
        DICT_SETITEM_DROP(block_dict, dictkey_bbox, JM_py_from_rect(block->bbox));

        if (block->type == FZ_STEXT_BLOCK_IMAGE)
        {
            JM_make_image_block(ctx, block, block_dict);
        }
        else
        {
            JM_make_text_block(ctx, block, block_dict, raw, text_buffer);
        }

        LIST_APPEND_DROP(block_list, block_dict);
    }
    DICT_SETITEM_DROP(page_dict, dictkey_blocks, block_list);
    fz_drop_buffer(ctx, text_buffer);
}

PyObject *JM_object_to_string(fz_context *ctx, pdf_obj *what, int compress, int ascii)
{
    fz_buffer *res=NULL;
    fz_output *out=NULL;
    PyObject *text=NULL;
    fz_try(ctx)
    {
        res = fz_new_buffer(ctx, 1024);
        out = fz_new_output_with_buffer(ctx, res);
        pdf_print_obj(ctx, out, what, compress, ascii);
        text = JM_EscapeStrFromBuffer(ctx, res);
    }
    fz_always(ctx)
    {
        fz_drop_output(ctx, out);
        fz_drop_buffer(ctx, res);
    }
    fz_catch(ctx)
    {
        text = PyUnicode_FromString("");
        return text;
    }
    return text;
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

    int max_alp = 0, max_fonts = 0, i, n;
    char start_str[32] = {0};  // string for comparison
    char text[32] = {0};  // string for comparison

    // Handle /Alp objects
    if (pdf_is_dict(ctx, temp_extg))  // any created at all?
    {
        n = pdf_dict_len(ctx, temp_extg);
        if (pdf_is_dict(ctx, main_extg))  // does page have /ExtGState yet?
        {
            for (i = 0; i < pdf_dict_len(ctx, main_extg); i++)
            {   // get highest number of objects named /Alp?
                char *alp = (char *) pdf_to_name(ctx, pdf_dict_get_key(ctx, main_extg, i));
                if (strncmp(alp, "Alp", 3) != 0) continue;
                if (strcmp(start_str, alp) < 0) strcpy(start_str, alp);
            }
            while (strcmp(text, start_str) < 0)
            {   // compute next available number
                fz_snprintf(text, sizeof(text), "Alp%d", max_alp);
                max_alp++;
            }
        }
        else  // create a /ExtGState for the page
            main_extg = pdf_dict_put_dict(ctx, resources, PDF_NAME(ExtGState), n);

        for (i = 0; i < n; i++)  // copy over renumbered /Alp objects
        {
            fz_snprintf(text, sizeof(text), "Alp%d", i + max_alp);  // new name
            pdf_obj *val = pdf_dict_get_val(ctx, temp_extg, i);
            pdf_dict_puts(ctx, main_extg, text, val);
        }
    }

    text[0] = 0;  // empty comparison string
    start_str[0] = 0;  // empty comparison string

    if (pdf_is_dict(ctx, main_fonts))  // has page any fonts yet?
    {
        for (i = 0; i < pdf_dict_len(ctx, main_fonts); i++)
        {   // get highest number of fonts named /F?
            char *font = (char *) pdf_to_name(ctx, pdf_dict_get_key(ctx, main_fonts, i));
            if (strncmp(font, "F", 1) != 0) continue;
            if (strcmp(start_str, font) < 0) strcpy(start_str, font);
        }
        while (strcmp(text, start_str) < 0)
        {   // compute next available number
            fz_snprintf(text, sizeof(text), "F%d", max_fonts);
            max_fonts++;
        }
    }
    else  // create a Resources/Font for the page
        main_fonts = pdf_dict_put_dict(ctx, resources, PDF_NAME(Font), 2);

    for (i = 0; i < pdf_dict_len(ctx, temp_fonts); i++)
    {   // copy over renumbered font objects
        fz_snprintf(text, sizeof(text), "F%d", i + max_fonts);
        pdf_obj *val = pdf_dict_get_val(ctx, temp_fonts, i);
        pdf_dict_puts_drop(ctx, main_fonts, text, val);
    }
    return Py_BuildValue("ii", max_alp, max_fonts); // next available numbers
}
%}
