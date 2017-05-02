%{
/*****************************************************************************/
// C helper functions for extractJSON
/*****************************************************************************/
void
fz_print_rect_json(fz_context *ctx, fz_output *out, fz_rect *bbox) {
    char buf[128];
    /* no buffer overflow! */
    snprintf(buf, sizeof(buf), "\"bbox\":[%g, %g, %g, %g],",
                        bbox->x0, bbox->y0, bbox->x1, bbox->y1);

    fz_write_printf(ctx, out, "%s", buf);
}

void
fz_print_utf8(fz_context *ctx, fz_output *out, int rune) {
    int i, n;
    char utf[10];
    n = fz_runetochar(utf, rune);
    for (i = 0; i < n; i++) {
        fz_write_printf(ctx, out, "%c", utf[i]);
    }
}

void
fz_print_span_stext_json(fz_context *ctx, fz_output *out, fz_stext_span *span) {
    fz_stext_char *ch;

    for (ch = span->text; ch < span->text + span->len; ch++)
    {
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
                    /*fz_print_utf8(ctx, out, ch->c);*/
                }
                break;
        }
    }
}

void
fz_send_data_base64(fz_context *ctx, fz_output *out, struct fz_buffer_s *buffer)
{
    size_t i;
    static const char set[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    unsigned char *buff;
    size_t bufflen = fz_buffer_storage(gctx, buffer, &buff);
    size_t len = bufflen/3;
    for (i = 0; i < len; i++)
    {
        int c = buff[3*i];
        int d = buff[3*i+1];
        int e = buff[3*i+2];
        /**************************************************/
        /* JSON decoders do not like "\n" in base64 data! */
        /* hence next 2 lines commented out               */
        /**************************************************/
        //if ((i & 15) == 0)
        //    fz_write_printf(ctx, out, "\n");
        fz_write_printf(ctx, out, "%c%c%c%c", set[c>>2], set[((c&3)<<4)|(d>>4)], set[((d&15)<<2)|(e>>6)], set[e & 63]);
    }
    i *= 3;
    switch (bufflen-i)
    {
        case 2:
        {
            int c = buff[i];
            int d = buff[i+1];
            fz_write_printf(ctx, out, "%c%c%c=", set[c>>2], set[((c&3)<<4)|(d>>4)], set[((d&15)<<2)]);
            break;
        }
    case 1:
        {
            int c = buff[i];
            fz_write_printf(ctx, out, "%c%c==", set[c>>2], set[(c&3)<<4]);
            break;
        }
    default:
    case 0:
        break;
    }
}

void
fz_print_stext_page_json(fz_context *ctx, fz_output *out, fz_stext_page *page)
{
    int block_n;

    fz_write_printf(ctx, out, "{\n \"len\":%d,\"width\":%g,\"height\":%g,\n \"blocks\":[\n",
              page->len,
              page->mediabox.x1 - page->mediabox.x0,
              page->mediabox.y1 - page->mediabox.y0);

    for (block_n = 0; block_n < page->len; block_n++)
    {
        fz_page_block * page_block = &(page->blocks[block_n]);

        fz_write_printf(ctx, out, "  {\"type\":%s,", page_block->type == FZ_PAGE_BLOCK_TEXT ? "\"text\"": "\"image\"");

        switch (page->blocks[block_n].type)
        {
            case FZ_PAGE_BLOCK_TEXT:
            {
                fz_stext_block *block = page->blocks[block_n].u.text;
                fz_stext_line *line;

                fz_print_rect_json(ctx, out, &(block->bbox));

                fz_write_printf(ctx, out, "\n   \"lines\":[\n");

                for (line = block->lines; line < block->lines + block->len; line++)
                {
                    fz_stext_span *span;
                    fz_write_printf(ctx, out, "      {");
                    fz_print_rect_json(ctx, out, &(line->bbox));

                    fz_write_printf(ctx, out, "\n       \"spans\":[\n");
                    for (span = line->first_span; span; span = span->next)
                    {
                        fz_write_printf(ctx, out, "         {");
                        fz_print_rect_json(ctx, out, &(span->bbox));
                        fz_write_printf(ctx, out, "\n          \"text\":\"");

                        fz_print_span_stext_json(ctx, out, span);

                        fz_write_printf(ctx, out, "\"\n         }");
                        if (span && (span->next)) {
                            fz_write_printf(ctx, out, ",\n");
                        }
                    }
                    fz_write_printf(ctx, out, "\n       ]");  /* spans end */

                    fz_write_printf(ctx, out, "\n      }");
                    if (line < (block->lines + block->len - 1)) {
                        fz_write_printf(ctx, out, ",\n");
                    }
                }
                fz_write_printf(ctx, out, "\n   ]");      /* lines end */
                break;
            }
            case FZ_PAGE_BLOCK_IMAGE:
            {
                fz_image_block *image = page->blocks[block_n].u.image;
                fz_compressed_buffer *buffer = fz_compressed_image_buffer(gctx, image->image);
                fz_print_rect_json(ctx, out, &(image->bbox));
                fz_write_printf(ctx, out, "\"imgtype\":%d,\"width\":%d,\"height\":%d,",
                                    buffer->params.type,
                                    image->image->w,
                                    image->image->h);
                fz_write_printf(ctx, out, "\"image\":\n");
                if (buffer == NULL) {
                    fz_write_printf(ctx, out, "null");
                } else {
                    fz_write_printf(ctx, out, "\"");
                    fz_send_data_base64(ctx, out, buffer->buffer);
                    fz_write_printf(ctx, out, "\"");
                }
                break;
            }
        }

        fz_write_printf(ctx, out, "\n  }");  /* blocks end */
        if (block_n < (page->len - 1)) {
            fz_write_printf(ctx, out, ",\n");
        }
    }
    fz_write_printf(ctx, out, "\n ]\n}");  /* page end */
}
%}