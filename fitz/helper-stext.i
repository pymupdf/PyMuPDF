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
    int i, n, last_char;

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
                    n = fz_runetochar(utf, ch->c);
                    for (i = 0; i < n; i++)
                        fz_write_byte(ctx, out, utf[i]);
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

// for faling back to replacement character 0xB7
PyObject *JM_repl_char()
{
    char data[10];
    Py_ssize_t len = (Py_ssize_t) fz_runetochar(data, 0xb7);
    return PyUnicode_FromStringAndSize(data, len);
}

%}
