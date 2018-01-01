%{
//-----------------------------------------------------------------------------
// C helper functions for extractJSON, and other structured text output
// functions.
// Renamed JSON functions to prefix them with "DG", to indicate they were
// contributed by our GitHub user @deepgully.
// Functions contributed by Jorj McKie are prefixed by "JM"
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
// JSON requirement: must have a digit before the decimal point
//-----------------------------------------------------------------------------
void DG_print_rect_json(fz_context *ctx, fz_output *out, fz_rect *bbox)
{
    char buf[128];
    snprintf(buf, sizeof(buf), "\"bbox\": [%g, %g, %g, %g],",
                        bbox->x0, bbox->y0, bbox->x1, bbox->y1);
    fz_write_printf(ctx, out, "%s", buf);
}

//-----------------------------------------------------------------------------
// JSON requirement: must have a digit before the decimal point
//-----------------------------------------------------------------------------
void DG_print_float_json(fz_context *ctx, fz_output *out, float g)
{
    char buf[15];
    snprintf(buf, sizeof(buf), "%g", g);
    fz_write_printf(ctx, out, "%s", buf);
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
DG_print_stext_image_as_json(fz_context *ctx, fz_output *out, fz_stext_block *block)
{
    fz_write_printf(ctx, out, "\n  {\"type\": 1, ");
    DG_print_rect_json(ctx, out, &(block->bbox));
    fz_image *image = block->u.i.image;
    fz_buffer *buf = NULL;
    int w = image->w;
    int h = image->h;
    int bparams = 0;
    fz_compressed_buffer *buffer = fz_compressed_image_buffer(ctx, image);
    if (buffer) bparams = buffer->params.type;
    fz_write_printf(ctx, out, "\n   \"imgtype\": %d, \"width\": %d, \"height\": %d, ",
                                    bparams, w, h);
    fz_write_printf(ctx, out, "\"image\":\n");

    if (!buffer)
    {
        fz_try(ctx)
        {
            buf = fz_new_buffer_from_image_as_png(ctx, image, NULL);
            fz_write_printf(ctx, out, "\"");
            fz_write_base64_buffer(ctx, out, buf, 0);
            fz_write_printf(ctx, out, "\"");
        }
        fz_always(ctx) fz_drop_buffer(ctx, buf);
        fz_catch(ctx)
        {
            fz_write_printf(ctx, out, "null");
        }
    }
    if (buffer)
    {
        fz_write_printf(ctx, out, "\"");
        fz_write_base64_buffer(ctx, out, buffer->buffer, 0);
        fz_write_printf(ctx, out, "\"");
    }
    fz_write_printf(ctx, out, "\n  }");
}

static void
DG_print_style_begin_json(fz_context *ctx, fz_output *out, fz_font *font, float size, int sup)
{
    char family[80];
    int flags = sup;
    flags += fz_font_is_italic(ctx, font) * 2;
    flags += fz_font_is_serif(ctx, font) * 4;
    flags += fz_font_is_monospaced(ctx, font) * 8;
    flags += fz_font_is_bold(ctx, font) * 16;
    font_family_name(ctx, font, family, sizeof family);

    fz_write_printf(ctx, out, "\n      {\"font\": \"%s\", \"size\": ", family);
    DG_print_float_json(ctx, out, size);
    fz_write_printf(ctx, out, ", \"flags\": %d", flags);
    fz_write_string(ctx, out, ", \"text\": \"");
}

static void
DG_print_style_end_json(fz_context *ctx, fz_output *out, fz_font *font, float size, int sup)
{
    fz_write_string(ctx, out, "\"}");
}

void
DG_print_stext_block_as_json(fz_context *ctx, fz_output *out, fz_stext_block *block)
{
    fz_stext_line *line;
    fz_stext_char *ch;
    fz_font *font = NULL;
    float size = 0;
    int sup = 0;
    fz_write_printf(ctx, out, "\n  {\"type\": 0, ");
    DG_print_rect_json(ctx, out, &(block->bbox));
    fz_write_printf(ctx, out, "\n   \"lines\": [\n");
    int line_n = 0;
    int span_n = 0;
    for (line = block->u.t.first_line; line; line = line->next)
    {
        if (line_n > 0) fz_write_printf(ctx, out, ",\n");
        fz_write_printf(ctx, out, "    {");        // begin line
        DG_print_rect_json(ctx, out, &(line->bbox));
        fz_write_printf(ctx, out, " \"wmode\": %d, \"dir\": [", line->wmode);
        DG_print_float_json(ctx, out, line->dir.x);
        fz_write_printf(ctx, out, ", ");
        DG_print_float_json(ctx, out, line->dir.y);
        fz_write_printf(ctx, out, "],\n     \"spans\": [");
        font = NULL;

        for (ch = line->first_char; ch; ch = ch->next)
        {
            int ch_sup = detect_super_script(line, ch);
            if (ch->font != font || ch->size != size)
            {
                if (font)
                {
                    DG_print_style_end_json(ctx, out, font, size, sup);
                    fz_write_printf(ctx, out, ",");
                }
                font = ch->font;
                size = ch->size;
                sup = ch_sup;
                DG_print_style_begin_json(ctx, out, font, size, sup);
            }

            switch (ch->c)
            {
                case '\\': fz_write_printf(ctx, out, "\\\\"); break;
                case '\'': fz_write_printf(ctx, out, "\\u0027"); break;
                case '"': fz_write_printf(ctx, out, "\\\""); break;
                case '\b': fz_write_printf(ctx, out, "\\b"); break;
                case '\f': fz_write_printf(ctx, out, "\\f"); break;
                case '\n': fz_write_printf(ctx, out, "\\n"); break;
                case '\r': fz_write_printf(ctx, out, "\\r"); break;
                case '\t': fz_write_printf(ctx, out, "\\t"); break;
                default:
                    if (ch->c >= 32 && ch->c <= 127) {
                        fz_write_printf(ctx, out, "%c", ch->c);
                    } else {
                        fz_write_printf(ctx, out, "\\u%04x", ch->c);
                    }
                    break;
            }
            line_n += 1;
        }
        if (font)
            DG_print_style_end_json(ctx, out, font, size, sup);
        fz_write_printf(ctx, out, " \n     ]\n"); // end of spans
        fz_write_printf(ctx, out, "    }"); // end line
    }
    fz_write_printf(ctx, out, "\n   ]"); // end of lines
    fz_write_printf(ctx, out, "\n  }"); // end a block
}

void
DG_print_stext_page_as_json(fz_context *ctx, fz_output *out, fz_stext_page *page)
{
    int block_n = 0;
    fz_stext_block *block;
    float w = page->mediabox.x1 - page->mediabox.x0;
    float h = page->mediabox.y1 - page->mediabox.y0;

    fz_write_printf(ctx, out, "{\"width\": %g, \"height\": %g,\n \"blocks\": [", w, h);

    for (block = page->first_block; block; block = block->next)
    {
        if (block_n > 0)
            fz_write_printf(ctx, out, ",");
        if (block->type == FZ_STEXT_BLOCK_IMAGE)
            DG_print_stext_image_as_json(ctx, out, block);
        else if (block->type == FZ_STEXT_BLOCK_TEXT)
        {
            DG_print_stext_block_as_json(ctx, out, block);
        }
        block_n += 1;
    }
    fz_write_printf(ctx, out, "\n ]");  /* blocks end */
    fz_write_printf(ctx, out, "\n}");  /* page end */
}

//-----------------------------------------------------------------------------
// Plain text output. An identical copy of fz_print_stext_page_as_text
// except that lines within a block are concatenated with a space instead
// a new-line.
//-----------------------------------------------------------------------------
void
JM_print_stext_page_as_text(fz_context *ctx, fz_output *out, fz_stext_page *page)
{
    fz_stext_block *block;
    fz_stext_line *line;
    fz_stext_char *ch;
    char utf[10];
    int last_char = 0;
    int i, n;

    for (block = page->first_block; block; block = block->next)
    {
        if (block->type == FZ_STEXT_BLOCK_TEXT)
        {
            int line_n = 0;
            for (line = block->u.t.first_line; line; line = line->next)
            {
                // append next line with a space if prev did not end with "-"
                if (line_n > 0) fz_write_string(ctx, out, " ");
                line_n += 1;
                for (ch = line->first_char; ch; ch = ch->next)
                {
                    last_char = ch->c;      // save char value
                    n = fz_runetochar(utf, ch->c);
                    for (i = 0; i < n; i++)
                        fz_write_byte(ctx, out, utf[i]);
                }
            }
            fz_write_string(ctx, out, "\n");
        }
    }
}

%}