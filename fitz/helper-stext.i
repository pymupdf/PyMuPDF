%{
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
    char utf[10];
    int i, n;

    for (block = page->first_block; block; block = block->next)
    {
        if (block->type == FZ_STEXT_BLOCK_TEXT)
        {
            int line_n = 0;
            for (line = block->u.t.first_line; line; line = line->next)
            {
                if (line_n > 0) fz_write_string(ctx, out, " ");
                line_n++;
                for (ch = line->first_char; ch; ch = ch->next)
                {
                    n = fz_runetochar(utf, ch->c);
                    for (i = 0; i < n; i++)
                        fz_write_byte(ctx, out, utf[i]);
                }
            }
            fz_write_string(ctx, out, "\n");
        }
    }
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

static const char *font_full_name(fz_context *ctx, fz_font *font)
{
    const char *name = fz_font_name(ctx, font);
    const char *s = strchr(name, '+');
    return s ? s + 1 : name;
}

static void font_family_name(fz_context *ctx, fz_font *font, char *buf, int size)
{
    const char *name = font_full_name(ctx, font);
    fz_strlcpy(buf, name, size);
}

void
JM_style_begin_dict(fz_context *ctx, PyObject *span, fz_font *font, float size, int sup)
{
    char family[80];
    font_family_name(ctx, font, family, sizeof family);
    int flags = sup;
    flags += fz_font_is_italic(ctx, font) * 2;
    flags += fz_font_is_serif(ctx, font) * 4;
    flags += fz_font_is_monospaced(ctx, font) * 8;
    flags += fz_font_is_bold(ctx, font) * 16;
    PyDict_SetItemString(span, "font", Py_BuildValue("s", family));
    PyDict_SetItemString(span, "size", Py_BuildValue("f", size));
    PyDict_SetItemString(span, "flags", Py_BuildValue("i", flags));
}

void
JM_style_end_dict(fz_context *ctx, fz_buffer *buff, PyObject *span, PyObject *spanlist)
{
    char *text;
    size_t len = fz_buffer_storage(ctx, buff, &text);
    PyDict_SetItemString(span, "text",  JM_UNICODE(text, len));
    PyList_Append(spanlist, span);
}

PyObject *
JM_extract_stext_textblock_as_dict(fz_context *ctx, fz_stext_block *block)
{
    fz_stext_line *line;
    fz_stext_char *ch;
    fz_font *font = NULL;
    fz_buffer *buff = NULL;
    float size = 0;
    int sup = 0;
    PyObject *span = NULL, *spanlist = NULL, *linelist = NULL, *linedict = NULL;
    linelist = PyList_New(0);
    PyObject *dict = PyDict_New();
    PyDict_SetItemString(dict, "type",  PyInt_FromLong(FZ_STEXT_BLOCK_TEXT));
    PyDict_SetItemString(dict, "bbox",   Py_BuildValue("[ffff]",
                                         block->bbox.x0, block->bbox.y0,
                                         block->bbox.x1, block->bbox.y1));

    for (line = block->u.t.first_line; line; line = line->next)
    {
        linedict = PyDict_New();
        PyDict_SetItemString(linedict, "bbox",   Py_BuildValue("ffff",
                                         line->bbox.x0, line->bbox.y0,
                                         line->bbox.x1, line->bbox.y1));
        PyDict_SetItemString(linedict, "wmode",  Py_BuildValue("i", line->wmode));
        PyDict_SetItemString(linedict, "dir",  Py_BuildValue("ff", line->dir.x, line->dir.y));
        spanlist = PyList_New(0);
        font = NULL;
        size = 0;

        for (ch = line->first_char; ch; ch = ch->next)
        {
            int ch_sup = detect_super_script(line, ch);
            if (ch->font != font || ch->size != size)
            {   // start new span
                if (font)    // must finish old span first
                {
                    JM_style_end_dict(ctx, buff, span, spanlist);
                    Py_DECREF(span);
                    span = NULL;
                    fz_drop_buffer(ctx, buff);
                    buff = NULL;
                    font = NULL;
                }
                font = ch->font;
                size = ch->size;
                sup = ch_sup;
                span = PyDict_New();
                buff = fz_new_buffer(ctx, 64);
                JM_style_begin_dict(ctx, span, font, size, sup);
            }
            fz_append_rune(ctx, buff, ch->c);
        }
        if (font)
        {
            JM_style_end_dict(ctx, buff, span, spanlist);
            Py_DECREF(span);
            font = NULL;
        }

        PyDict_SetItemString(linedict, "spans",  spanlist);
        Py_DECREF(spanlist);
        PyList_Append(linelist, linedict);
        Py_DECREF(linedict);
    }
    PyDict_SetItemString(dict, "lines",  linelist);
    Py_DECREF(linelist);
    return dict;
}

PyObject *
JM_extract_stext_imageblock_as_dict(fz_context *ctx, fz_stext_block *block)
{
    fz_image *image = block->u.i.image;
    fz_buffer *buf = NULL, *freebuf = NULL;
    fz_compressed_buffer *buffer = NULL;
    int n = fz_colorspace_n(ctx, image->colorspace);
    int w = image->w;
    int h = image->h;
    int type = 0;
    unsigned char ext[5];
    PyObject *bytes = JM_BinFromChar("");
    buffer = fz_compressed_image_buffer(ctx, image);
    if (buffer) type = buffer->params.type;
    PyObject *dict = PyDict_New();
    PyDict_SetItemString(dict, "type",  PyInt_FromLong(FZ_STEXT_BLOCK_IMAGE));
    PyDict_SetItemString(dict, "bbox",   Py_BuildValue("[ffff]",
                                         block->bbox.x0, block->bbox.y0,
                                         block->bbox.x1, block->bbox.y1));
    PyDict_SetItemString(dict, "width",  PyInt_FromLong((long) w));
    PyDict_SetItemString(dict, "height", PyInt_FromLong((long) h));
    fz_try(ctx)
    {
        if (image->use_colorkey) type = FZ_IMAGE_UNKNOWN;
        if (image->use_decode)   type = FZ_IMAGE_UNKNOWN;
        if (image->mask)         type = FZ_IMAGE_UNKNOWN;
        if (type < FZ_IMAGE_BMP) type = FZ_IMAGE_UNKNOWN;
        if (n != 1 && n != 3 && type == FZ_IMAGE_JPEG)
            type = FZ_IMAGE_UNKNOWN;
        if (type != FZ_IMAGE_UNKNOWN)
        {
            buf = buffer->buffer;
            switch(type)
            {
                case(FZ_IMAGE_BMP):  strcpy(ext, "bmp");  break;
                case(FZ_IMAGE_GIF):  strcpy(ext, "gif");  break;
                case(FZ_IMAGE_JPEG): strcpy(ext, "jpeg"); break;
                case(FZ_IMAGE_JPX):  strcpy(ext, "jpx");  break;
                case(FZ_IMAGE_JXR):  strcpy(ext, "jxr");  break;
                case(FZ_IMAGE_PNM):  strcpy(ext, "pnm");  break;
                case(FZ_IMAGE_TIFF): strcpy(ext, "tiff"); break;
                default:             strcpy(ext, "png");  break;
            }
        }
        else
        {
            buf = freebuf = fz_new_buffer_from_image_as_png(ctx, image, NULL);
            strcpy(ext, "png");
        }
        bytes = JM_BinFromBuffer(ctx, buf);
    }
    fz_always(ctx)
    {
        fz_drop_buffer(ctx, freebuf);
        PyDict_SetItemString(dict, "ext",  PyString_FromString(ext));
        PyDict_SetItemString(dict, "image",  bytes);
        Py_DECREF(bytes);
    }
    fz_catch(ctx) {;}
    return dict;
}

PyObject *
JM_stext_page_as_dict(fz_context *ctx, fz_stext_page *page)
{
    PyObject *dict = PyDict_New();
    PyObject *blocklist = PyList_New(0);
    fz_stext_block *block;
    float w = page->mediabox.x1 - page->mediabox.x0;
    float h = page->mediabox.y1 - page->mediabox.y0;
    PyDict_SetItemString(dict, "width", Py_BuildValue("f", w));
    PyDict_SetItemString(dict, "height", Py_BuildValue("f", h));
    for (block = page->first_block; block; block = block->next)
    {
        if (block->type == FZ_STEXT_BLOCK_IMAGE)
            PyList_Append(blocklist, JM_extract_stext_imageblock_as_dict(ctx, block));
        else
            PyList_Append(blocklist, JM_extract_stext_textblock_as_dict(ctx, block));
    }
    PyDict_SetItemString(dict, "blocks", blocklist);
    Py_DECREF(blocklist);
    return dict;
}
%}