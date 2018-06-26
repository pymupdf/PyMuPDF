%{
PyObject *JM_UnicodeFromASCII(const char *in);
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
// Functions for wordlist output
//-----------------------------------------------------------------------------
int JM_append_word(fz_context *ctx, PyObject *lines, fz_buffer *buff, fz_rect *wbbox,
                   int block_n, int line_n, int word_n)
{
    PyObject *litem = Py_BuildValue("ffffOiii", wbbox->x0, wbbox->y0, wbbox->x1, wbbox->y1,
                                    JM_StrFromBuffer(ctx, buff),
                                    block_n, line_n, word_n);
    PyList_Append(lines, litem);
    Py_DECREF(litem);
    wbbox->x0 = wbbox->y0 = wbbox->x1 = wbbox->y1 = 0;
    return word_n + 1;                 // word counter
}

//-----------------------------------------------------------------------------
// Functions for dictionary output
//-----------------------------------------------------------------------------

// create an empty rectangle --------------------------------------------------
fz_rect *JM_empty_rect()
{
    fz_rect *r = (fz_rect *)malloc(sizeof(fz_rect));
    r->x0 = r->y0 = r->x1 = r->y1 = 0;
    return r;
}

// enlarge rect r1 by r2. modify r2-height by size
void JM_join_rect(fz_rect *r1, fz_rect *r2, float size)
{
    if (fz_is_empty_rect(r1))
    {
        r1->x0 = r2->x0;
        r1->y0 = r2->y0;
        r1->x1 = r2->x1;
        r1->y1 = MAX(r2->y1, r2->y0 + size);
    }
    else
    {
        r1->x0 = MIN(r1->x0, r2->x0);
        r1->y0 = MIN(r1->y0, r2->y0);
        r1->x1 = MAX(r1->x1, r2->x1);
        r1->y1 = MAX(r1->y1, MAX(r2->y1, r2->y0 + size));
    }
}

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
    PyDict_SetItemString(span, "font", JM_UnicodeFromASCII(family));
    PyDict_SetItemString(span, "size", Py_BuildValue("f", size));
    PyDict_SetItemString(span, "flags", Py_BuildValue("i", flags));
}

void
JM_style_end_dict(fz_context *ctx, fz_buffer *buff, PyObject *span, PyObject *spanlist)
{
    PyDict_SetItemString(span, "text",  JM_StrFromBuffer(ctx, buff));
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
    fz_rect *blockrect = JM_empty_rect();
    PyDict_SetItemString(dict, "type",  PyInt_FromLong(FZ_STEXT_BLOCK_TEXT));

    for (line = block->u.t.first_line; line; line = line->next)
    {
        linedict = PyDict_New();
        fz_rect *linerect = JM_empty_rect();
        PyDict_SetItemString(linedict, "wmode",  Py_BuildValue("i", line->wmode));
        PyDict_SetItemString(linedict, "dir",  Py_BuildValue("ff", line->dir.x, line->dir.y));
        spanlist = PyList_New(0);
        font = NULL;
        size = 0;

        for (ch = line->first_char; ch; ch = ch->next)
        {
            JM_join_rect(linerect, &ch->bbox, ch->size);

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
        PyDict_SetItemString(linedict, "bbox",   Py_BuildValue("ffff",
                                         linerect->x0, linerect->y0,
                                         linerect->x1, linerect->y1));

        JM_join_rect(blockrect, linerect, 0);

        free(linerect);
        PyList_Append(linelist, linedict);
        Py_DECREF(linedict);
    }
    PyDict_SetItemString(dict, "lines",  linelist);
    Py_DECREF(linelist);
    PyDict_SetItemString(dict, "bbox",   Py_BuildValue("ffff",
                                         blockrect->x0, blockrect->y0,
                                         blockrect->x1, blockrect->y1));
    free(blockrect);
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