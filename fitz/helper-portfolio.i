%{
//----------------------------------------------------------------------------
// portfolio schema types
//----------------------------------------------------------------------------
#define PDF_SCHEMA_NUMBER 0
#define PDF_SCHEMA_SIZE 1
#define PDF_SCHEMA_TEXT 2
#define PDF_SCHEMA_DATE 3
#define PDF_SCHEMA_DESC 4
#define PDF_SCHEMA_MODDATE 5
#define PDF_SCHEMA_CREATIONDATE 6
#define PDF_SCHEMA_FILENAME 7
#define PDF_SCHEMA_UNKNOWN 8

void portfolio_out_string(fz_output *out, unsigned char *str, int len)
{
    int c;

    if (len > 1 && str[0] == 0xFE && str[1] == 0xFF)
    {
        str += 2;
        len -= 2;
        while (len)
        {
            c = (*str++<<8);
            c += *str++;
            if (c >= 32 && c != 127 && c < 256)
                fz_write_printf(gctx, out, "%c", c);
            else
                fz_write_printf(gctx, out, "<%04x>", c);
            len -= 2;
        };
    }
    else
    {
        while (len)
        {
            c = *str++;
            if (c >= 32 && c != 127 && c < 256)
                fz_write_printf(gctx, out, "%c", c);
            else
                fz_write_printf(gctx, out, "<%02x>", c);
            len--;
        };
    }
}

void portfolio_out_obj(fz_output *out, pdf_obj *obj, const char *dflt)
{
    if (obj == NULL) fz_write_printf(gctx, out, dflt);
    else if (pdf_is_string(gctx, obj))
        portfolio_out_string(out, (unsigned char *)pdf_to_str_buf(gctx, obj),
                                     pdf_to_str_len(gctx, obj));
    else
        pdf_print_obj(gctx, out, obj, 1);
}

%}