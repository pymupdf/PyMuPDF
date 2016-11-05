%{
char *annot_type_str(int type)
{
	switch (type)
	{
	case FZ_ANNOT_TEXT: return "Text";
	case FZ_ANNOT_LINK: return "Link";
	case FZ_ANNOT_FREETEXT: return "FreeText";
	case FZ_ANNOT_LINE: return "Line";
	case FZ_ANNOT_SQUARE: return "Square";
	case FZ_ANNOT_CIRCLE: return "Circle";
	case FZ_ANNOT_POLYGON: return "Polygon";
	case FZ_ANNOT_POLYLINE: return "PolyLine";
	case FZ_ANNOT_HIGHLIGHT: return "Highlight";
	case FZ_ANNOT_UNDERLINE: return "Underline";
	case FZ_ANNOT_SQUIGGLY: return "Squiggly";
	case FZ_ANNOT_STRIKEOUT: return "StrikeOut";
	case FZ_ANNOT_STAMP: return "Stamp";
	case FZ_ANNOT_CARET: return "Caret";
	case FZ_ANNOT_INK: return "Ink";
	case FZ_ANNOT_POPUP: return "Popup";
	case FZ_ANNOT_FILEATTACHMENT: return "FileAttachment";
	case FZ_ANNOT_SOUND: return "Sound";
	case FZ_ANNOT_MOVIE: return "Movie";
	case FZ_ANNOT_WIDGET: return "Widget";
	case FZ_ANNOT_SCREEN: return "Screen";
	case FZ_ANNOT_PRINTERMARK: return "PrinterMark";
	case FZ_ANNOT_TRAPNET: return "TrapNet";
	case FZ_ANNOT_WATERMARK: return "Watermark";
	case FZ_ANNOT_3D: return "3D";
	default: return "";
	}
}

/*******************************************************************************
Deep-copies a specified source page to the target location.
*******************************************************************************/
void page_merge(pdf_document* doc_des, pdf_document* doc_src, int page_from, int page_to, int rotate, pdf_graft_map *graft_map)
{
    pdf_obj *pageref = NULL;
    pdf_obj *page_dict;
    pdf_obj *obj = NULL, *ref = NULL;
    /***************************************************************************
    Include minimal number of objects for page.  Do not include items that
    reference other pages.
    ***************************************************************************/
    pdf_obj *known_page_objs[] = {PDF_NAME_Contents, PDF_NAME_Resources,
        PDF_NAME_MediaBox, PDF_NAME_CropBox, PDF_NAME_BleedBox,
        PDF_NAME_TrimBox, PDF_NAME_ArtBox, PDF_NAME_Rotate, PDF_NAME_UserUnit};
    int n = nelem(known_page_objs);
    int i;
    int num;
    fz_var(obj);
    fz_var(ref);

    fz_try(gctx)
    {
        pageref = pdf_lookup_page_obj(gctx, doc_src, page_from);

        /* Make a new dictionary and copy over the items from the source object to
        * the new dict that we want to deep copy. */
        page_dict = pdf_new_dict(gctx, doc_des, 4);

        pdf_dict_put_drop(gctx, page_dict, PDF_NAME_Type, PDF_NAME_Page);

        for (i = 0; i < n; i++)
        {
            obj = pdf_dict_get(gctx, pageref, known_page_objs[i]);
            if (obj != NULL)
                pdf_dict_put_drop(gctx, page_dict, known_page_objs[i], pdf_graft_object(gctx, doc_des, doc_src, obj, graft_map));
        }
        /***********************************************************************
        Make page rotate as specified
        ***********************************************************************/
        if (rotate != -1) {
            pdf_obj *rotateobj = pdf_new_int(gctx, doc_des, rotate);
            pdf_dict_put_drop(gctx, page_dict, PDF_NAME_Rotate, rotateobj);
        }
        /***********************************************************************
        Now add the page dictionary to dest PDF
        ***********************************************************************/
        obj = pdf_add_object_drop(gctx, doc_des, page_dict);

        /***********************************************************************
        Get indirect ref of the page
        ***********************************************************************/
        num = pdf_to_num(gctx, obj);
        ref = pdf_new_indirect(gctx, doc_des, num, 0);

        /***********************************************************************
        Insert new page at specified location
        ***********************************************************************/
        pdf_insert_page(gctx, doc_des, page_to, ref);

    }
    fz_always(gctx)
    {
        pdf_drop_obj(gctx, obj);
        pdf_drop_obj(gctx, ref);
    }
    fz_catch(gctx)
    {
        fz_rethrow(gctx);
    }
}

/*******************************************************************************
Copy a range of pages (spage, epage) from a source PDF to a specified location
(apage) of the target PDF.
If spage > epage, the sequence of source pages is reversed.
*******************************************************************************/
void merge_range(pdf_document* doc_des, pdf_document* doc_src, int spage, int epage, int apage, int rotate)
{
    int page, afterpage;
    pdf_graft_map *graft_map;
    afterpage = apage;

    graft_map = pdf_new_graft_map(gctx, doc_src);

    fz_try(gctx)
    {
        if (spage < epage)
            for (page = spage; page <= epage; page++, afterpage++)
                page_merge(doc_des, doc_src, page, afterpage, rotate, graft_map);
        else
            for (page = spage; page >= epage; page--, afterpage++)
                page_merge(doc_des, doc_src, page, afterpage, rotate, graft_map);
    }

    fz_always(gctx)
    {
        pdf_drop_graft_map(gctx, graft_map);
    }
    fz_catch(gctx)
    {
        fz_rethrow(gctx);
    }
}

/*******************************************************************************
Fills table 'res' with outline object numbers
'res' must be a correctly pre-allocated table of integers
'obj' must be the first OL item
returns (int) number of filled-in outline item numbers.
*******************************************************************************/
int fillOLNumbers(int *res, pdf_obj *obj, int oc, int argc)
{
    int onum;
    pdf_obj *first, *parent, *thisobj;
    if (!obj) return oc;
    if (oc >= argc) return oc;
    thisobj = obj;
    while (thisobj) {
        onum = pdf_to_num(gctx, thisobj);
        res[oc] = onum;
        oc += 1;
        first = pdf_dict_get(gctx, thisobj, PDF_NAME_First);   /* try go down */
        if (first) oc = fillOLNumbers(res, first, oc, argc);   /* recurse     */
        thisobj = pdf_dict_get(gctx, thisobj, PDF_NAME_Next);  /* try go next */
        parent = pdf_dict_get(gctx, thisobj, PDF_NAME_Parent); /* get parent  */
        if (!thisobj) thisobj = parent;         /* goto parent if no next obj */
    }
    return oc;
}

/*******************************************************************************
Returns (int) number of outlines
'obj' must be first OL item
*******************************************************************************/
int countOutlines(pdf_obj *obj, int oc)
{
    pdf_obj *first, *parent, *thisobj;
    if (!obj) return oc;
    thisobj = obj;
    while (thisobj) {
        oc += 1;
        first = pdf_dict_get(gctx, thisobj, PDF_NAME_First);   /* try go down */
        if (first) oc = countOutlines(first, oc);
        thisobj = pdf_dict_get(gctx, thisobj, PDF_NAME_Next);  /* try go next */
        parent = pdf_dict_get(gctx, thisobj, PDF_NAME_Parent); /* get parent  */
        if (!thisobj) thisobj = parent;      /* goto parent if no next exists */
    }
    return oc;
}

/*******************************************************************************
Read text from a document page - the short way.
Main logic is contained in function fz_new_stext_page_from_page of file
utils.c in the fitz directory.
In essence, it creates an stext device, runs the stext page through it,
deletes the device and returns the text buffer in the requested format.
A display list is not used in the process.
*******************************************************************************/
struct fz_buffer_s *readPageText(fz_page *page, int output) {
    fz_buffer *res;
    fz_output *out;
    fz_stext_sheet *ts;
    fz_stext_page *tp;
    fz_try(gctx) {
        ts = fz_new_stext_sheet(gctx);
        tp = fz_new_stext_page_from_page(gctx, page, ts);
        res = fz_new_buffer(gctx, 1024);
        out = fz_new_output_with_buffer(gctx, res);
        if (output<=0) fz_print_stext_page(gctx, out, tp);
        if (output==1) fz_print_stext_page_html(gctx, out, tp);
        if (output==2) fz_print_stext_page_json(gctx, out, tp);
        if (output>=3) fz_print_stext_page_xml(gctx, out, tp);
        fz_drop_output(gctx, out);
        fz_drop_stext_page(gctx, tp);
        fz_drop_stext_sheet(gctx, ts);
    }
    fz_catch(gctx) {
        if (out) fz_drop_output(gctx, out);
        if (tp)  fz_drop_stext_page(gctx, tp);
        if (ts)  fz_drop_stext_sheet(gctx, ts);
        if (res) fz_drop_buffer(gctx, res);
        fz_rethrow(gctx);
    }
    return res;
}

/*******************************************************************************
Helpers for document page selection - main logic was imported
from pdf_clean_file.c. But instead of analyzing a string-based spefication of
selected pages, we accept an integer array.
*******************************************************************************/
typedef struct globals_s
{
    pdf_document *doc;
    fz_context *ctx;
} globals;

int string_in_names_list(fz_context *ctx, pdf_obj *p, pdf_obj *names_list)
{
    int n = pdf_array_len(ctx, names_list);
    int i;
    char *str = pdf_to_str_buf(ctx, p);

    for (i = 0; i < n ; i += 2)
    {
        if (!strcmp(pdf_to_str_buf(ctx, pdf_array_get(ctx, names_list, i)), str))
            return 1;
    }
    return 0;
}

/*******************************************************************************
Recreate page tree to only retain specified pages.
*******************************************************************************/

void retainpage(fz_context *ctx, pdf_document *doc, pdf_obj *parent, pdf_obj *kids, int page)
{
    pdf_obj *pageref = pdf_lookup_page_obj(ctx, doc, page);
    pdf_obj *pageobj = pdf_resolve_indirect(ctx, pageref);

    pdf_dict_put(ctx, pageobj, PDF_NAME_Parent, parent);

    /* Store page object in new kids array */
    pdf_array_push(ctx, kids, pageref);
}

int dest_is_valid_page(fz_context *ctx, pdf_obj *obj, int *page_object_nums, int pagecount)
{
    int i;
    int num = pdf_to_num(ctx, obj);

    if (num == 0)
        return 0;
    for (i = 0; i < pagecount; i++)
    {
        if (page_object_nums[i] == num)
            return 1;
    }
    return 0;
}

int dest_is_valid(fz_context *ctx, pdf_obj *o, int page_count, int *page_object_nums, pdf_obj *names_list)
{
    pdf_obj *p;

    p = pdf_dict_get(ctx, o, PDF_NAME_A);
    if (pdf_name_eq(ctx, pdf_dict_get(ctx, p, PDF_NAME_S), PDF_NAME_GoTo) &&
        !string_in_names_list(ctx, pdf_dict_get(ctx, p, PDF_NAME_D), names_list))
        return 0;

    p = pdf_dict_get(ctx, o, PDF_NAME_Dest);
    if (p == NULL)
    {}
    else if (pdf_is_string(ctx, p))
    {
        return string_in_names_list(ctx, p, names_list);
    }
    else if (!dest_is_valid_page(ctx, pdf_array_get(ctx, p, 0), page_object_nums, page_count))
        return 0;

    return 1;
}

int strip_outlines(fz_context *ctx, pdf_document *doc, pdf_obj *outlines, int page_count, int *page_object_nums, pdf_obj *names_list);

int strip_outline(fz_context *ctx, pdf_document *doc, pdf_obj *outlines, int page_count, int *page_object_nums, pdf_obj *names_list, pdf_obj **pfirst, pdf_obj **plast)
{
    pdf_obj *prev = NULL;
    pdf_obj *first = NULL;
    pdf_obj *current;
    int count = 0;

    for (current = outlines; current != NULL; )
    {
        int nc;

/*******************************************************************************
        Strip any children to start with. This takes care of
        First / Last / Count for us.
*******************************************************************************/
        nc = strip_outlines(ctx, doc, current, page_count, page_object_nums, names_list);

        if (!dest_is_valid(ctx, current, page_count, page_object_nums, names_list))
        {
            if (nc == 0)
            {
/*******************************************************************************
                Outline with invalid dest and no children. Drop it by
                pulling the next one in here.
*******************************************************************************/
                pdf_obj *next = pdf_dict_get(ctx, current, PDF_NAME_Next);
                if (next == NULL)
                {
                    /* There is no next one to pull in */
                    if (prev != NULL)
                        pdf_dict_del(ctx, prev, PDF_NAME_Next);
                }
                else if (prev != NULL)
                {
                    pdf_dict_put(ctx, prev, PDF_NAME_Next, next);
                    pdf_dict_put(ctx, next, PDF_NAME_Prev, prev);
                }
                else
                {
                    pdf_dict_del(ctx, next, PDF_NAME_Prev);
                }
                current = next;
            }
            else
            {
                /* Outline with invalid dest, but children. Just drop the dest. */
                pdf_dict_del(ctx, current, PDF_NAME_Dest);
                pdf_dict_del(ctx, current, PDF_NAME_A);
                current = pdf_dict_get(ctx, current, PDF_NAME_Next);
            }
        }
        else
        {
            /* Keep this one */
            if (first == NULL)
                first = current;
            prev = current;
            current = pdf_dict_get(ctx, current, PDF_NAME_Next);
            count++;
        }
    }

    *pfirst = first;
    *plast = prev;

    return count;
}

int strip_outlines(fz_context *ctx, pdf_document *doc, pdf_obj *outlines, int page_count, int *page_object_nums, pdf_obj *names_list)
{
    int nc;
    pdf_obj *first;
    pdf_obj *last;

    first = pdf_dict_get(ctx, outlines, PDF_NAME_First);
    if (first == NULL)
        nc = 0;
    else
        nc = strip_outline(ctx, doc, first, page_count, page_object_nums, names_list, &first, &last);

    if (nc == 0)
    {
        pdf_dict_del(ctx, outlines, PDF_NAME_First);
        pdf_dict_del(ctx, outlines, PDF_NAME_Last);
        pdf_dict_del(ctx, outlines, PDF_NAME_Count);
    }
    else
    {
        int old_count = pdf_to_int(ctx, pdf_dict_get(ctx, outlines, PDF_NAME_Count));
        pdf_dict_put(ctx, outlines, PDF_NAME_First, first);
        pdf_dict_put(ctx, outlines, PDF_NAME_Last, last);
        pdf_dict_put_drop(ctx, outlines, PDF_NAME_Count, pdf_new_int(ctx, doc, old_count > 0 ? nc : -nc));
    }

    return nc;
}

/*******************************************************************************
   called by PyMuPDF:
   argc  = length of "liste"
   liste = (list of int) page numbers to retain
*******************************************************************************/
void retainpages(fz_context *ctx, globals *glo, int argc, int *liste)
{
    pdf_obj *oldroot, *root, *pages, *kids, *countobj, *parent, *olddests;
    pdf_document *doc = glo->doc;
    int argidx = 0;
    pdf_obj *names_list = NULL;
    pdf_obj *outlines;
    int pagecount;
    int i;
    int *page_object_nums;

/*******************************************************************************
    Keep only pages/type and (reduced) dest entries to avoid
    references to dropped pages
*******************************************************************************/
    oldroot = pdf_dict_get(ctx, pdf_trailer(ctx, doc), PDF_NAME_Root);
    pages = pdf_dict_get(ctx, oldroot, PDF_NAME_Pages);
    olddests = pdf_load_name_tree(ctx, doc, PDF_NAME_Dests);
    outlines = pdf_dict_get(ctx, oldroot, PDF_NAME_Outlines);

    root = pdf_new_dict(ctx, doc, 3);
    pdf_dict_put(ctx, root, PDF_NAME_Type, pdf_dict_get(ctx, oldroot, PDF_NAME_Type));
    pdf_dict_put(ctx, root, PDF_NAME_Pages, pdf_dict_get(ctx, oldroot, PDF_NAME_Pages));
    pdf_dict_put(ctx, root, PDF_NAME_Outlines, outlines);

    pdf_update_object(ctx, doc, pdf_to_num(ctx, oldroot), root);

    /* Create a new kids array with only the pages we want to keep */
    parent = pdf_new_indirect(ctx, doc, pdf_to_num(ctx, pages), pdf_to_gen(ctx, pages));
    kids = pdf_new_array(ctx, doc, 1);

    /* Retain pages specified */
    int page;
    for (page = 0; page < argc; page++)
        {
            retainpage(ctx, doc, parent, kids, liste[page]);
        }

    pdf_drop_obj(ctx, parent);

    /* Update page count and kids array */
    countobj = pdf_new_int(ctx, doc, pdf_array_len(ctx, kids));
    pdf_dict_put(ctx, pages, PDF_NAME_Count, countobj);
    pdf_drop_obj(ctx, countobj);
    pdf_dict_put(ctx, pages, PDF_NAME_Kids, kids);
    pdf_drop_obj(ctx, kids);

    /* Force the next call to pdf_count_pages to recount */
    glo->doc->page_count = 0;

    pagecount = pdf_count_pages(ctx, doc);
    page_object_nums = fz_calloc(ctx, pagecount, sizeof(*page_object_nums));
    for (i = 0; i < pagecount; i++)
    {
        pdf_obj *pageref = pdf_lookup_page_obj(ctx, doc, i);
        page_object_nums[i] = pdf_to_num(ctx, pageref);
    }

/*******************************************************************************    If we had an old Dests tree (now reformed as an olddests dictionary),
    keep any entries in there that point to valid pages.
    This may mean we keep more than we need, but it is safe at least.
*******************************************************************************/
    if (olddests)
    {
        pdf_obj *names = pdf_new_dict(ctx, doc, 1);
        pdf_obj *dests = pdf_new_dict(ctx, doc, 1);
        int len = pdf_dict_len(ctx, olddests);

        names_list = pdf_new_array(ctx, doc, 32);

        for (i = 0; i < len; i++)
        {
            pdf_obj *key = pdf_dict_get_key(ctx, olddests, i);
            pdf_obj *val = pdf_dict_get_val(ctx, olddests, i);
            pdf_obj *dest = pdf_dict_get(ctx, val, PDF_NAME_D);

            dest = pdf_array_get(ctx, dest ? dest : val, 0);
            if (dest_is_valid_page(ctx, dest, page_object_nums, pagecount))
            {
                pdf_obj *key_str = pdf_new_string(ctx, doc, pdf_to_name(ctx, key), strlen(pdf_to_name(ctx, key)));
                pdf_array_push(ctx, names_list, key_str);
                pdf_array_push(ctx, names_list, val);
                pdf_drop_obj(ctx, key_str);
            }
        }

        pdf_dict_put(ctx, dests, PDF_NAME_Names, names_list);
        pdf_dict_put(ctx, names, PDF_NAME_Dests, dests);
        pdf_dict_put(ctx, root, PDF_NAME_Names, names);

        pdf_drop_obj(ctx, names);
        pdf_drop_obj(ctx, dests);
        pdf_drop_obj(ctx, olddests);
    }

/*******************************************************************************
    Edit each pages /Annot list to remove any links pointing to nowhere.
*******************************************************************************/
    for (i = 0; i < pagecount; i++)
    {
        pdf_obj *pageref = pdf_lookup_page_obj(ctx, doc, i);
        pdf_obj *pageobj = pdf_resolve_indirect(ctx, pageref);

        pdf_obj *annots = pdf_dict_get(ctx, pageobj, PDF_NAME_Annots);

        int len = pdf_array_len(ctx, annots);
        int j;

        for (j = 0; j < len; j++)
        {
            pdf_obj *o = pdf_array_get(ctx, annots, j);

            if (!pdf_name_eq(ctx, pdf_dict_get(ctx, o, PDF_NAME_Subtype), PDF_NAME_Link))
                continue;

            if (!dest_is_valid(ctx, o, pagecount, page_object_nums, names_list))
            {
                /* Remove this annotation */
                pdf_array_delete(ctx, annots, j);
                j--;
            }
        }
    }

    if (strip_outlines(ctx, doc, outlines, pagecount, page_object_nums, names_list) == 0)
    {
        pdf_dict_del(ctx, root, PDF_NAME_Outlines);
    }

    fz_free(ctx, page_object_nums);
    pdf_drop_obj(ctx, names_list);
    pdf_drop_obj(ctx, root);
}

/*****************************************************************************/
/* C helper functions for extractJSON */
/*****************************************************************************/

void
fz_print_rect_json(fz_context *ctx, fz_output *out, fz_rect *bbox) {
    char buf[128];
    /* no buffer overflow! */
    snprintf(buf, sizeof(buf), "\"bbox\":[%g, %g, %g, %g],",
                        bbox->x0, bbox->y0, bbox->x1, bbox->y1);

    fz_printf(ctx, out, "%s", buf);
}

void
fz_print_utf8(fz_context *ctx, fz_output *out, int rune) {
    int i, n;
    char utf[10];
    n = fz_runetochar(utf, rune);
    for (i = 0; i < n; i++) {
        fz_printf(ctx, out, "%c", utf[i]);
    }
}

void
fz_print_span_stext_json(fz_context *ctx, fz_output *out, fz_stext_span *span) {
    fz_stext_char *ch;

    for (ch = span->text; ch < span->text + span->len; ch++)
    {
        switch (ch->c)
        {
            case '\\': fz_printf(ctx, out, "\\\\"); break;
            case '\'': fz_printf(ctx, out, "\\u0027"); break;
            case '"': fz_printf(ctx, out, "\\\""); break;
            case '\b': fz_printf(ctx, out, "\\b"); break;
            case '\f': fz_printf(ctx, out, "\\f"); break;
            case '\n': fz_printf(ctx, out, "\\n"); break;
            case '\r': fz_printf(ctx, out, "\\r"); break;
            case '\t': fz_printf(ctx, out, "\\t"); break;
            default:
                if (ch->c >= 32 && ch->c <= 127) {
                    fz_printf(ctx, out, "%c", ch->c);
                } else {
                    fz_printf(ctx, out, "\\u%04x", ch->c);
                    /*fz_print_utf8(ctx, out, ch->c);*/
                }
                break;
        }
    }
}

void
fz_send_data_base64(fz_context *ctx, fz_output *out, fz_buffer *buffer)
{
    int i, len;
    static const char set[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

    len = buffer->len/3;
    for (i = 0; i < len; i++)
    {
        int c = buffer->data[3*i];
        int d = buffer->data[3*i+1];
        int e = buffer->data[3*i+2];
        /**************************************************/
        /* JSON decoders do not like "\n" in base64 data! */
        /* ==> next 2 lines commented out                 */
        /**************************************************/
        //if ((i & 15) == 0)
        //    fz_printf(ctx, out, "\n");
        fz_printf(ctx, out, "%c%c%c%c", set[c>>2], set[((c&3)<<4)|(d>>4)], set[((d&15)<<2)|(e>>6)], set[e & 63]);
    }
    i *= 3;
    switch (buffer->len-i)
    {
        case 2:
        {
            int c = buffer->data[i];
            int d = buffer->data[i+1];
            fz_printf(ctx, out, "%c%c%c=", set[c>>2], set[((c&3)<<4)|(d>>4)], set[((d&15)<<2)]);
            break;
        }
    case 1:
        {
            int c = buffer->data[i];
            fz_printf(ctx, out, "%c%c==", set[c>>2], set[(c&3)<<4]);
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

    fz_printf(ctx, out, "{\n \"len\":%d,\"width\":%g,\"height\":%g,\n \"blocks\":[\n",
                        page->len,
                        page->mediabox.x1 - page->mediabox.x0,
                        page->mediabox.y1 - page->mediabox.y0);

    for (block_n = 0; block_n < page->len; block_n++)
    {
        fz_page_block * page_block = &(page->blocks[block_n]);

        fz_printf(ctx, out, "  {\"type\":%s,", page_block->type == FZ_PAGE_BLOCK_TEXT ? "\"text\"": "\"image\"");

        switch (page->blocks[block_n].type)
        {
            case FZ_PAGE_BLOCK_TEXT:
            {
                fz_stext_block *block = page->blocks[block_n].u.text;
                fz_stext_line *line;

                fz_print_rect_json(ctx, out, &(block->bbox));

                fz_printf(ctx, out, "\n   \"lines\":[\n");

                for (line = block->lines; line < block->lines + block->len; line++)
                {
                    fz_stext_span *span;
                    fz_printf(ctx, out, "      {");
                    fz_print_rect_json(ctx, out, &(line->bbox));

                    fz_printf(ctx, out, "\n       \"spans\":[\n");
                    for (span = line->first_span; span; span = span->next)
                    {
                        fz_printf(ctx, out, "         {");
                        fz_print_rect_json(ctx, out, &(span->bbox));
                        fz_printf(ctx, out, "\n          \"text\":\"");

                        fz_print_span_stext_json(ctx, out, span);

                        fz_printf(ctx, out, "\"\n         }");
                        if (span && (span->next)) {
                            fz_printf(ctx, out, ",\n");
                        }
                    }
                    fz_printf(ctx, out, "\n       ]");  /* spans end */

                    fz_printf(ctx, out, "\n      }");
                    if (line < (block->lines + block->len - 1)) {
                        fz_printf(ctx, out, ",\n");
                    }
                }
                fz_printf(ctx, out, "\n   ]");      /* lines end */
                break;
            }
            case FZ_PAGE_BLOCK_IMAGE:
            {
                fz_image_block *image = page->blocks[block_n].u.image;

                fz_print_rect_json(ctx, out, &(image->bbox));
                fz_printf(ctx, out, "\"imgtype\":%d,\"width\":%d,\"height\":%d,",
                                    image->image->buffer->params.type,
                                    image->image->w,
                                    image->image->h);
                fz_printf(ctx, out, "\"image\":\n");
                if (image->image->buffer == NULL) {
                    fz_printf(ctx, out, "null");
                } else {
                    fz_printf(ctx, out, "\"");
                    fz_send_data_base64(ctx, out, image->image->buffer->buffer);
                    fz_printf(ctx, out, "\"");
                }
                break;
            }
        }

        fz_printf(ctx, out, "\n  }");  /* blocks end */
        if (block_n < (page->len - 1)) {
            fz_printf(ctx, out, ",\n");
        }
    }
    fz_printf(ctx, out, "\n ]\n}");  /* page end */
}
%}
