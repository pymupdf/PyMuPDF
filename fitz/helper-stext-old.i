%{
PyObject *JM_UnicodeFromASCII(const char *in);

// for falling back to replacement character 0xB7
PyObject *JM_repl_char()
{
    char data[10];
    Py_ssize_t len = (Py_ssize_t) fz_runetochar(data, 0xb7);
    return PyUnicode_FromStringAndSize(data, len);
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
                if (line_n > 0 && last_char != 10) fz_write_string(ctx, out, "\n");
                line_n++;
                for (ch = line->first_char; ch; ch = ch->next)
                {
                    fz_write_rune(ctx, out, ch->c);
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
    PyObject *s = JM_StrFromBuffer(ctx, buff);
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

// create the char rectangle from the char quad
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

int JM_char_font_flags(fz_context *ctx, fz_font *font, fz_stext_line *line, fz_stext_char *ch)
{
    int flags = detect_super_script(line, ch);
    flags += fz_font_is_italic(ctx, font) * 2;
    flags += fz_font_is_serif(ctx, font) * 4;
    flags += fz_font_is_monospaced(ctx, font) * 8;
    flags += fz_font_is_bold(ctx, font) * 16;
    return flags;
}

int JM_textpage_charlist(fz_context *ctx, fz_stext_page *tp, int blockno, int lineno, PyObject *list)
{
    fz_stext_block *block;
    fz_stext_line *line;
    fz_stext_char *ch;
    PyObject *uchar;
    int i = -1, j = -1, n = 0;
    for (block = tp->first_block; block; block = block->next)
    {
        i++;
        if (i == blockno) break;
    }
    if (i != blockno || !block)  // wrong block number
        return -1;
    if (block->type != FZ_STEXT_BLOCK_TEXT)  // wrong block type
        return -2;

    for (line = block->u.t.first_line; line; line = line->next)
    {
        j++;
        if (j == lineno) break;
    }
    if (j != lineno || !line)  // wrong line number
        return -3;

    for (ch = line->first_char; ch; ch = ch->next)
    {
        fz_rect r = JM_char_bbox(line, ch);
        int flags = JM_char_font_flags(ctx, ch->font, line, ch);
        PyObject *ufont = JM_UnicodeFromASCII(fz_font_name(ctx, ch->font));
        uchar = PyUnicode_FromFormat("%c", ch->c);
        if (!uchar) uchar = JM_repl_char();
        PyObject *item = PyTuple_New(11);
        PyTuple_SET_ITEM(item, 0, Py_BuildValue("f", ch->origin.x));
        PyTuple_SET_ITEM(item, 1, Py_BuildValue("f", ch->origin.y));
        PyTuple_SET_ITEM(item, 2, Py_BuildValue("f", r.x0));
        PyTuple_SET_ITEM(item, 3, Py_BuildValue("f", r.y0));
        PyTuple_SET_ITEM(item, 4, Py_BuildValue("f", r.x1));
        PyTuple_SET_ITEM(item, 5, Py_BuildValue("f", r.y1));
        PyTuple_SET_ITEM(item, 6, Py_BuildValue("f", ch->size));
        PyTuple_SET_ITEM(item, 7, Py_BuildValue("i", flags));
        PyTuple_SET_ITEM(item, 8, Py_BuildValue("O", ufont));
        PyTuple_SET_ITEM(item, 9, Py_BuildValue("i", ch->color));
        PyTuple_SET_ITEM(item, 10, Py_BuildValue("O", uchar));
        PyList_Append(list, item);
        Py_DECREF(uchar);
        Py_DECREF(ufont);
        Py_DECREF(item);
        PyErr_Clear();
        n++;
    }
    return n;
}

int JM_textpage_linelist(fz_context *ctx, fz_stext_page *tp, int blockno, PyObject *list)
{
    fz_stext_block *block;
    fz_stext_line *line;
    int i = -1, n = 0;
    for (block = tp->first_block; block; block = block->next)
    {
        i++;
        if (i == blockno) break;
    }

    if (i != blockno || !block)  // wrong block number
        return -1;
    if (block->type != FZ_STEXT_BLOCK_TEXT)  // wrong block type
        return -2;

    for (line = block->u.t.first_line; line; line = line->next)
    {
        PyObject *item = PyTuple_New(7);
        PyTuple_SET_ITEM(item, 0, Py_BuildValue("i", line->wmode));
        PyTuple_SET_ITEM(item, 1, Py_BuildValue("f", line->dir.x));
        PyTuple_SET_ITEM(item, 2, Py_BuildValue("f", line->dir.y));
        PyTuple_SET_ITEM(item, 3, Py_BuildValue("f", line->bbox.x0));
        PyTuple_SET_ITEM(item, 4, Py_BuildValue("f", line->bbox.y0));
        PyTuple_SET_ITEM(item, 5, Py_BuildValue("f", line->bbox.x1));
        PyTuple_SET_ITEM(item, 6, Py_BuildValue("f", line->bbox.y1));
        PyList_Append(list, item);
        Py_DECREF(item);
        n++;
    }
    return n;
}

int JM_textpage_blocklist(fz_context *ctx, fz_stext_page *tp, PyObject *list)
{
    fz_stext_block *block;
    int n = 0;
    for (block = tp->first_block; block; block = block->next)
    {
        fz_rect r = block->bbox;
        PyObject *item = PyTuple_New(5);
        PyTuple_SET_ITEM(item, 0, Py_BuildValue("i", block->type));
        PyTuple_SET_ITEM(item, 1, Py_BuildValue("f", r.x0));
        PyTuple_SET_ITEM(item, 2, Py_BuildValue("f", r.y0));
        PyTuple_SET_ITEM(item, 3, Py_BuildValue("f", r.x1));
        PyTuple_SET_ITEM(item, 4, Py_BuildValue("f", r.y1));
        PyList_Append(list, item);
        Py_DECREF(item);
        n++;
    }
    return n;

}

int JM_textpage_imageblock(fz_context *ctx, fz_stext_page *tp, int blockno, PyObject *list)
{
    fz_stext_block *block;
    int i = -1;
    for (block = tp->first_block; block; block = block->next)
    {
        i++;
        if (i == blockno) break;
    }

    if (i != blockno || !block)  // wrong block number
        return -1;
    if (block->type != FZ_STEXT_BLOCK_IMAGE)  // wrong block type
        return -2;
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
    PyObject *bytes = JM_BinFromChar("");
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
            bytes = JM_BinFromBuffer(ctx, buf);
        else
            bytes = JM_BArrayFromBuffer(ctx, buf);
    }
    fz_always(ctx)
    {
        PyObject *item = PyTuple_New(5);
        PyTuple_SET_ITEM(item, 0, Py_BuildValue("i", FZ_STEXT_BLOCK_IMAGE));
        PyTuple_SET_ITEM(item, 1, Py_BuildValue("i", w));
        PyTuple_SET_ITEM(item, 2, Py_BuildValue("i", h));
        PyTuple_SET_ITEM(item, 3, Py_BuildValue("s", ext));
        PyTuple_SET_ITEM(item, 4, Py_BuildValue("O", bytes));
        PyList_Append(list, item);
        Py_DECREF(bytes);
        Py_DECREF(item);
        fz_drop_buffer(ctx, freebuf);
    }
    fz_catch(ctx) {;}
    return 0;
}

//-----------------------------------------------------------------------------
// Fill a dictionary from TextPage content 
//-----------------------------------------------------------------------------
int JM_make_textpage_dict(fz_context *ctx, fz_stext_page *tp, PyObject *page_dict, int raw)
{
    PyObject *blocks = PyList_New(0);
    Py_ssize_t num_blocks = JM_textpage_blocklist(ctx, tp, blocks);
    PyObject *block_list = PyList_New(0);
    PyObject *val;
    Py_ssize_t i;
    for (i = 0; i < num_blocks; i++)
    {
        PyObject *block = PySequence_ITEM(blocks, i);
        PyObject *block_dict = PyDict_New();
        val = PySequence_ITEM(block, 0);
        int block_type = (int) PyLong_AsLong(val);
        PyDict_SetItemString(block_dict, "type", val);
        Py_DECREF(val);
        val = PySequence_GetSlice(block, 1, 5);
        PyDict_SetItemString(block_dict, "bbox", val);
        Py_DECREF(val);
        PyObject *lines = PyList_New(0);
        if (block_type == 1)
        {
            int n = JM_textpage_imageblock(ctx, tp, (int) i, lines);
            if (n != 0) THROWMSG("could not extract image block");
            PyObject *ilist = PySequence_ITEM(lines, 0);
            val = PySequence_ITEM(ilist, 1);
            PyDict_SetItemString(block_dict, "width", val);
            Py_DECREF(val);
            val = PySequence_ITEM(ilist, 2);
            PyDict_SetItemString(block_dict, "height", val);
            Py_DECREF(val);
            val = PySequence_ITEM(ilist, 3);
            PyDict_SetItemString(block_dict, "ext", val);
            Py_DECREF(val);
            val = PySequence_ITEM(ilist, 4);
            PyDict_SetItemString(block_dict, "image", val);
            Py_DECREF(val);
            PyList_Append(block_list, block_dict);
            Py_DECREF(ilist);
            Py_DECREF(block_dict);
            Py_DECREF(lines);
            continue;
        }
        Py_ssize_t num_lines = JM_textpage_linelist(ctx, tp, (int) i, lines);
        PyObject *line_list = PyList_New(0);
        Py_ssize_t j;
        for (j = 0; j < num_lines; j++)
        {
            PyObject *line = PySequence_ITEM(lines, j);
            PyObject *line_dict = PyDict_New();
            val = PySequence_ITEM(line, 0);
            PyDict_SetItemString(line_dict, "wmode", val);
            Py_DECREF(val);
            val = PySequence_GetSlice(line, 1, 3);
            PyDict_SetItemString(line_dict, "dir", val);
            Py_DECREF(val);
            val = PySequence_GetSlice(line, 3, 7);
            PyDict_SetItemString(line_dict, "bbox", val);
            Py_DECREF(val);
            PyObject *span_list = PyList_New(0);
            PyObject *characters = PyList_New(0);
            PyObject *old_style = NULL;
            PyObject *style = NULL;
            PyObject *span = NULL;
            PyObject *char_list = NULL;
            PyObject *span_bbox = NULL;
            PyObject *char_dict = NULL;
            PyObject *text = NULL;
            int num_chars = JM_textpage_charlist(ctx, tp, (int) i, (int) j, characters);
            int k;
            for (k = 0; k < num_chars; k++)
            {
                PyObject *ch = PySequence_ITEM(characters, (Py_ssize_t) k);
                PyObject *char_bbox = PySequence_GetSlice(ch, 2, 6);
                PyObject *fsize = PySequence_ITEM(ch, 6);
                PyObject *flags = PySequence_ITEM(ch, 7);
                PyObject *font = PySequence_ITEM(ch, 8);
                PyObject *color = PySequence_ITEM(ch, 9);
                PyObject *char_text = PySequence_ITEM(ch, 10);
                val = PyUnicode_FromString("+");
                PyObject *splits = PyUnicode_Split(font, val, 1);
                Py_DECREF(font);
                Py_DECREF(val);
                if (PyList_GET_SIZE(splits) == 1)
                {
                    font = PySequence_ITEM(splits, 0);
                }
                else
                {
                    font = PySequence_ITEM(splits, 1);
                }
                Py_DECREF(splits);

                style = PyList_New(0);
                PyList_Append(style, font);
                PyList_Append(style, fsize);
                PyList_Append(style, flags);
                PyList_Append(style, color);

                if (PyObject_RichCompareBool(old_style, style, Py_EQ) != 1)
                {
                    if (old_style)
                    {
                        if (raw)
                        {
                            PyDict_SetItemString(span, "chars", char_list);
                            Py_CLEAR(char_list);
                        }
                        else
                        {
                            PyDict_SetItemString(span, "text", text);
                            Py_CLEAR(text);
                        }
                        PyDict_SetItemString(span, "bbox", span_bbox);
                        Py_CLEAR(span_bbox);
                        PyList_Append(span_list, span);
                        Py_CLEAR(span);
                    }
                    span = PyDict_New();
                    PyDict_SetItemString(span, "font", font);
                    PyDict_SetItemString(span, "size", fsize);
                    PyDict_SetItemString(span, "flags", flags);
                    PyDict_SetItemString(span, "color", color);
                    Py_DECREF(font);
                    Py_DECREF(fsize);
                    Py_DECREF(flags);
                    Py_DECREF(color);
                    old_style = style;
                    span_bbox = char_bbox;
                }

                fz_rect r = fz_union_rect(JM_rect_from_py(span_bbox),
                                          JM_rect_from_py(char_bbox));
                Py_CLEAR(span_bbox);
                span_bbox = JM_py_from_rect(r);
                if (raw)
                {
                    char_dict = PyDict_New();
                    val = PySequence_GetSlice(ch, 0, 2);
                    PyDict_SetItemString(char_dict, "origin", val);
                    Py_DECREF(val);
                    PyDict_SetItemString(char_dict, "bbox", char_bbox);
                    PyDict_SetItemString(char_dict, "c", char_text);
                    Py_CLEAR(char_text);
                    if (!char_list)
                    {
                        char_list = PyList_New(0);
                    }
                    PyList_Append(char_list, char_dict);
                    Py_DECREF(char_dict);
                }
                else
                {
                    if (text)
                    {
                        val = PyUnicode_Concat(text, char_text);
                        if (!val)
                        {
                            JM_TRACE("concat result is NULL!");
                        }
                        Py_CLEAR(text);
                        Py_CLEAR(char_text);
                        text = val;
                    }
                    else
                    {
                        text = char_text;
                        Py_CLEAR(char_text);
                    }
                }
                Py_CLEAR(char_bbox);
            }

            if (raw)
            {
                if (char_list && PySequence_Size(char_list) > 0)
                {
                    PyDict_SetItemString(span, "chars", char_list);
                    Py_CLEAR(char_list);
                }
            }
            else
            {
                if (text && PyUnicode_GetSize(text) > 0)
                {
                    PyDict_SetItemString(span, "text", text);
                    Py_CLEAR(text);
                }
            }

            PyDict_SetItemString(span, "bbox", span_bbox);
            Py_CLEAR(span_bbox);
            PyList_Append(span_list, span);
            Py_CLEAR(span);

            PyDict_SetItemString(line_dict, "spans", span_list);
            Py_CLEAR(span_list);
            PyList_Append(line_list, line_dict);
            Py_DECREF(line_dict);
        }
        PyDict_SetItemString(block_dict, "lines", line_list);
        Py_DECREF(lines);
        Py_DECREF(line_list);
        PyList_Append(block_list, block_dict);
        Py_DECREF(block_dict);
    }
    PyDict_SetItemString(page_dict, "blocks", block_list);
    Py_DECREF(block_list);
    Py_DECREF(blocks);
    return 0;
}
%}
