%{
//----------------------------------------------------------------------------
// Return set(dict.keys()) <= set([vkeys, ...])
// keys of dict must be string or unicode in Py2 and string in Py3!
// Parameters:
// dict - the Python dictionary object to be checked
// vkeys - a null-terminated list of keys (char *)
//----------------------------------------------------------------------------
int checkDictKeys(PyObject *dict, const char *vkeys, ...)
{
    int i, j, rc;
    PyObject *dkeys = PyDict_Keys(dict);              // = dict.keys()
    if (!dkeys) return 0;                             // no valid dictionary
    j = PySequence_Size(dkeys);                       // len(dict.keys())
    PyObject *validkeys = PyList_New(0);            // make list of valid keys
    va_list ap;                                       // def var arg list
    va_start(ap, vkeys);                              // start of args
    while (vkeys != 0)                                // reached end yet?
        { // build list of valid keys to check against
#if PY_MAJOR_VERSION < 3
        PyList_Append(validkeys, PyBytes_FromString(vkeys));    // Python 2
#else
        PyList_Append(validkeys, PyUnicode_FromString(vkeys));  // python 3
#endif
        vkeys = va_arg(ap, const char *);             // get next char string
        }
    va_end(ap);                                       // end the var args loop
    rc = 1;                                           // prepare for success
    for (i = 0; i < j; i++)
    {   // loop through dictionary keys
        if (!PySequence_Contains(validkeys, PySequence_GetItem(dkeys, i)))
            {
            rc = 0;
            break;
            }
    }
    Py_DECREF(validkeys);
    Py_DECREF(dkeys);
    return rc;
}

//----------------------------------------------------------------------------
// returns Python True / False for an integer
//----------------------------------------------------------------------------
PyObject *truth_value(int v)
{
    if (v == 0) Py_RETURN_FALSE;
    Py_RETURN_TRUE;
}

//----------------------------------------------------------------------------
// refreshes the link and annotation tables of a page
//----------------------------------------------------------------------------
void refresh_link_table (pdf_page *page)
{
    pdf_obj *annots_arr = pdf_dict_get(gctx, page->obj, PDF_NAME_Annots);
    if (annots_arr)
    {
        fz_rect page_mediabox;
        fz_matrix page_ctm;
        pdf_page_transform(gctx, page, &page_mediabox, &page_ctm);
        page->links = pdf_load_link_annots(gctx, page->doc, annots_arr, &page_ctm);
        pdf_load_annots(gctx, page, annots_arr);
    }
    return;
}

//----------------------------------------------------------------------------
// deletes an annotation (revised version of the buggy pdf_delete_annot)
//----------------------------------------------------------------------------
void
delete_annot(fz_context *ctx, pdf_page *page, pdf_annot *annot)
{
    pdf_document *doc = annot->page->doc;
    pdf_annot **annotptr;
    pdf_obj *annot_arr;
    int i;

    if (annot == NULL)
        return;

    /* Remove annot from page's list */
    for (annotptr = &page->annots; *annotptr; annotptr = &(*annotptr)->next)
    {
        if (*annotptr == annot)
            break;
    }

    /* Check the passed annotation was of this page */
    if (*annotptr == NULL)
        return;

    *annotptr = annot->next;

    /* If the removed annotation was the last in the list adjust the end pointer */
    if (*annotptr == NULL)
        page->annot_tailp = annotptr;

    /* If the removed annotation has the focus, blur it. */
    if (doc->focus == annot)
    {
        doc->focus = NULL;
        doc->focus_obj = NULL;
    }

    /* Remove the annot from the "Annots" array. */
    pdf_obj *annot_entry = pdf_dict_get(ctx, page->obj, PDF_NAME_Annots);
    if (pdf_is_indirect(ctx, annot_entry))
        annot_arr = pdf_resolve_indirect(ctx, annot_entry);
    else
        annot_arr = annot_entry;
    i = pdf_array_find(ctx, annot_arr, annot->obj);
    if (i >= 0)
        pdf_array_delete(ctx, annot_arr, i);

    if (pdf_is_indirect(ctx, annot_entry))
        pdf_update_object(ctx, doc, pdf_to_num(ctx, annot_entry), annot_arr);
    else
        pdf_dict_put(ctx, page->obj, PDF_NAME_Annots, annot_arr);

    /* The garbage collection pass when saving will remove the annot object,
     * removing it here may break files if multiple pages use the same annot. */

    /* And free it. */
    fz_drop_annot(ctx, &annot->super);

    doc->dirty = 1;
}

fz_buffer *deflatebuf(fz_context *ctx, unsigned char *p, size_t n)
{
    fz_buffer *buf;
    uLongf csize;
    int t;
    uLong longN = (uLong)n;
    unsigned char *data;
    size_t cap;

    if (n != (size_t)longN)
        fz_throw(ctx, FZ_ERROR_GENERIC, "Buffer to large to deflate");

    cap = compressBound(longN);
    data = fz_malloc(ctx, cap);
    buf = fz_new_buffer_from_data(ctx, data, cap);
    csize = (uLongf)cap;
    t = compress(data, &csize, p, longN);
    if (t != Z_OK)
    {
        fz_drop_buffer(ctx, buf);
        fz_throw(ctx, FZ_ERROR_GENERIC, "cannot deflate buffer");
    }
    fz_resize_buffer(ctx, buf, csize);
    return buf;
}

//*****************************************************************************
// Return (char *) for PyBytes, PyString (Python 2) or PyUnicode object.
// For PyBytes, a conversion to PyUnicode is first performed, if Python 3.
// In Python 2, this is an alias for PyString and its (char *) is returned.
// PyUnicode objects are converted to UTF16BE bytes objects (all Python
// versions). Its (char *) version is returned.
// If only 1-byte code points are present, BOM and high-order bytes are
// deleted and the (compressed) rest is returned.
// Parameters:
// obj = PyBytes / PyString / PyUnicode object
// psize = pointer to a Py_ssize_t number for storing the returned length
// name = name of object to use in error messages
//*****************************************************************************
char *getPDFstr(PyObject *obj, Py_ssize_t* psize, const char *name)
{
    int ok;
    Py_ssize_t j, k;
    PyObject *me;
    unsigned char *nc;
    int have_uc = 0;    // indicates unicode beyond latin-1 code points
    me = obj;
    if (PyBytes_Check(me))
        {
        ok = PyBytes_AsStringAndSize(me, &nc, psize);
        if (ok != 0)
            {
            fz_throw(gctx, FZ_ERROR_GENERIC, "could not get string of '%s'", name);
            return NULL;
            }
#if PY_MAJOR_VERSION < 3
        return nc;                     // we are done when Python 2
#endif
        me = PyUnicode_FromStringAndSize(nc, *psize);      // assumes nc is UTF8
        }
    if (!PyUnicode_Check(me))
        {
        fz_throw(gctx, FZ_ERROR_GENERIC, "type(%s) is not unicode, bytes or str", name);
        return NULL;
        }
    PyObject *uc = PyUnicode_AsUTF16String(me);
    if (!uc)
        {
        fz_throw(gctx, FZ_ERROR_GENERIC, "could not create UTF16 for '%s'", name);
        return NULL;
        }
    ok = PyBytes_AsStringAndSize(uc, &nc, psize);
    if (ok != 0)
        {
        fz_throw(gctx, FZ_ERROR_GENERIC, "could not get UTF16 string of '%s'", name);
        return NULL;
        }
    // UTF16-BE (big endian) is required for PDF if code points > 0xff
    if (nc[0] == 255)                  // non-BE UTF16, so swap bytes
    {
        j = 2;
        nc[0] = 254;                   // set BOM to "BE"
        nc[1] = 255;
        while ((j+1) < *psize)
        {
            k = nc[j];                      // save 1st byte
            nc[j] = nc[j+1];                // copy 2nd byte
            nc[j+1] = k;                    // copy 1st byte
            if (nc[j] > 0) have_uc = 1;     // code point outside latin-1
            j = j + 2;
        }
    }
    else                               // have UTF16BE, just check code points
    {
        j = 2;
        while (j < *psize)
        {
            if (nc[j] > 0) have_uc = 1;     // code point outside latin-1
            j = j + 2;
        }
    }
    if (have_uc == 1) return nc;            // have large code points: done
    k=0; j=3;
    while (j < *psize)                      // kick out BOM & high order bytes
    {
        nc[k] = nc[j];
        k += 1;
        j += 2;
    }
    nc[k+1] = 0;                            // end of string delimiter
    *psize = (*psize - 2) / 2;              // reduced size
    return nc;
}

// annotation types
#define ANNOT_TEXT 0
#define ANNOT_LINK 1
#define ANNOT_FREETEXT 2
#define ANNOT_LINE 3
#define ANNOT_SQUARE 4
#define ANNOT_CIRCLE 5
#define ANNOT_POLYGON 6
#define ANNOT_POLYLINE 7
#define ANNOT_HIGHLIGHT 8
#define ANNOT_UNDERLINE 9
#define ANNOT_SQUIGGLY 10
#define ANNOT_STRIKEOUT 11
#define ANNOT_STAMP 12
#define ANNOT_CARET 13
#define ANNOT_INK 14
#define ANNOT_POPUP 15
#define ANNOT_FILEATTACHMENT 16
#define ANNOT_SOUND 17
#define ANNOT_MOVIE 18
#define ANNOT_WIDGET 19
#define ANNOT_SCREEN 20
#define ANNOT_PRINTERMARK 21
#define ANNOT_TRAPNET 22
#define ANNOT_WATERMARK 23
#define ANNOT_3D 24

// annotation flag bits
#define ANNOT_XF_Invisible 1 << (1-1)
#define ANNOT_XF_Hidden 1 << (2-1)
#define ANNOT_XF_Print 1 << (3-1)
#define ANNOT_XF_NoZoom 1 << (4-1)
#define ANNOT_XF_NoRotate 1 << (5-1)
#define ANNOT_XF_NoView 1 << (6-1)
#define ANNOT_XF_ReadOnly 1 << (7-1)
#define ANNOT_XF_Locked 1 << (8-1)
#define ANNOT_XF_ToggleNoView 1 << (9-1)
#define ANNOT_XF_LockedContents 1 << (10-1)

// line ending styles
#define ANNOT_LE_None 0
#define ANNOT_LE_Square 1
#define ANNOT_LE_Circle 2
#define ANNOT_LE_Diamond 3
#define ANNOT_LE_OpenArrow 4
#define ANNOT_LE_ClosedArrow 5
#define ANNOT_LE_Butt 6
#define ANNOT_LE_ROpenArrow 7
#define ANNOT_LE_RClosedArrow 8
#define ANNOT_LE_Slash 9

char *annot_le_style_str(int type)
{
    switch (type)
    {
    case ANNOT_LE_None: return "None";
    case ANNOT_LE_Square: return "Square";
    case ANNOT_LE_Circle: return "Circle";
    case ANNOT_LE_Diamond: return "Diamond";
    case ANNOT_LE_OpenArrow: return "OpenArrow";
    case ANNOT_LE_ClosedArrow: return "ClosedArrow";
    case ANNOT_LE_Butt: return "Butt";
    case ANNOT_LE_ROpenArrow: return "ROpenArrow";
    case ANNOT_LE_RClosedArrow: return "RClosedArrow";
    case ANNOT_LE_Slash: return "Slash";
    default: return "None";
    }
}

char *annot_type_str(int type)
{
    switch (type)
    {
    case ANNOT_TEXT: return "Text";
    case ANNOT_LINK: return "Link";
    case ANNOT_FREETEXT: return "FreeText";
    case ANNOT_LINE: return "Line";
    case ANNOT_SQUARE: return "Square";
    case ANNOT_CIRCLE: return "Circle";
    case ANNOT_POLYGON: return "Polygon";
    case ANNOT_POLYLINE: return "PolyLine";
    case ANNOT_HIGHLIGHT: return "Highlight";
    case ANNOT_UNDERLINE: return "Underline";
    case ANNOT_SQUIGGLY: return "Squiggly";
    case ANNOT_STRIKEOUT: return "StrikeOut";
    case ANNOT_STAMP: return "Stamp";
    case ANNOT_CARET: return "Caret";
    case ANNOT_INK: return "Ink";
    case ANNOT_POPUP: return "Popup";
    case ANNOT_FILEATTACHMENT: return "FileAttachment";
    case ANNOT_SOUND: return "Sound";
    case ANNOT_MOVIE: return "Movie";
    case ANNOT_WIDGET: return "Widget";
    case ANNOT_SCREEN: return "Screen";
    case ANNOT_PRINTERMARK: return "PrinterMark";
    case ANNOT_TRAPNET: return "TrapNet";
    case ANNOT_WATERMARK: return "Watermark";
    case ANNOT_3D: return "3D";
    default: return "";
    }
}

/*****************************************************************************/
// Deep-copies a specified source page to the target location.
/*****************************************************************************/
void page_merge(pdf_document* doc_des, pdf_document* doc_src, int page_from, int page_to, int rotate, pdf_graft_map *graft_map)
{
    pdf_obj *pageref = NULL;
    pdf_obj *page_dict;
    pdf_obj *obj = NULL, *ref = NULL, *subt = NULL;

    // list of object types (per page) we want to copy
    pdf_obj *known_page_objs[] = {PDF_NAME_Contents, PDF_NAME_Resources,
        PDF_NAME_MediaBox, PDF_NAME_CropBox, PDF_NAME_BleedBox, PDF_NAME_Annots,
        PDF_NAME_TrimBox, PDF_NAME_ArtBox, PDF_NAME_Rotate, PDF_NAME_UserUnit};
    int n = nelem(known_page_objs);                   // number of list elements
    int i;
    int num, j;
    fz_var(obj);
    fz_var(ref);

    fz_try(gctx)
    {
        pageref = pdf_lookup_page_obj(gctx, doc_src, page_from);
        pdf_flatten_inheritable_page_items(gctx, pageref);
        // make a new page
        page_dict = pdf_new_dict(gctx, doc_des, 4);
        pdf_dict_put_drop(gctx, page_dict, PDF_NAME_Type, PDF_NAME_Page);

        // copy objects of source page into it
        for (i = 0; i < n; i++)
            {
            obj = pdf_dict_get(gctx, pageref, known_page_objs[i]);
            if (obj != NULL)
                pdf_dict_put_drop(gctx, page_dict, known_page_objs[i], pdf_graft_object(gctx, doc_des, doc_src, obj, graft_map));
            }
        // remove any links from annots array
        pdf_obj *annots = pdf_dict_get(gctx, page_dict, PDF_NAME_Annots);
        int len = pdf_array_len(gctx, annots);
        for (j = 0; j < len; j++)
        {
            pdf_obj *o = pdf_array_get(gctx, annots, j);
            if (!pdf_name_eq(gctx, pdf_dict_get(gctx, o, PDF_NAME_Subtype), PDF_NAME_Link))
                continue;
            // remove the link annotation
            pdf_array_delete(gctx, annots, j);
            len--;
            j--;
        }
        // rotate the page as requested
        if (rotate != -1)
            {
            pdf_obj *rotateobj = pdf_new_int(gctx, doc_des, rotate);
            pdf_dict_put_drop(gctx, page_dict, PDF_NAME_Rotate, rotateobj);
            }
        // Now add the page dictionary to dest PDF
        obj = pdf_add_object_drop(gctx, doc_des, page_dict);

        // Get indirect ref of the page
        num = pdf_to_num(gctx, obj);
        ref = pdf_new_indirect(gctx, doc_des, num, 0);

        // Insert new page at specified location
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

/*****************************************************************************/
// Copy a range of pages (spage, epage) from a source PDF to a specified location
// (apage) of the target PDF.
// If spage > epage, the sequence of source pages is reversed.
/*****************************************************************************/
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

/******************************************************************************/
// Fills table 'res' with outline object numbers
// 'res' must be a correctly pre-allocated table of integers
// 'obj' must be the first OL item
// returns (int) number of filled-in outline item numbers.
/******************************************************************************/
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

/******************************************************************************/
// Returns (int) number of outlines
// 'obj' must be first OL item
/******************************************************************************/
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

/******************************************************************************/
// Read text from a document page - the short way.
// Main logic is contained in function fz_new_stext_page_from_page of file
// utils.c in the fitz directory.
// In essence, it creates an stext device, runs the stext page through it,
// deletes the device and returns the text buffer in the requested format.
// A display list is not used in the process.
/******************************************************************************/
const char *readPageText(fz_page *page, int output) {
    fz_buffer *res;
    fz_output *out;
    fz_stext_sheet *ts;
    fz_stext_page *tp;
    fz_try(gctx) {
        ts = fz_new_stext_sheet(gctx);
        tp = fz_new_stext_page_from_page(gctx, page, ts, NULL);
        res = fz_new_buffer(gctx, 1024);
        out = fz_new_output_with_buffer(gctx, res);
        if (output<=0) fz_print_stext_page(gctx, out, tp);
        if (output==1) fz_print_stext_page_html(gctx, out, tp);
        if (output==2) fz_print_stext_page_json(gctx, out, tp);
        if (output>=3) fz_print_stext_page_xml(gctx, out, tp);
    }
    fz_always(gctx)
    {
        fz_drop_output(gctx, out);
        fz_drop_stext_page(gctx, tp);
        fz_drop_stext_sheet(gctx, ts);
    }
    fz_catch(gctx) {
        if (res) fz_drop_buffer(gctx, res);
        fz_rethrow(gctx);
    }
    return fz_string_from_buffer(gctx, res);
}

/******************************************************************************/
// Helpers for document page selection - main logic was imported
// from pdf_clean_file.c. But instead of analyzing a string-based spefication of
// selected pages, we accept an integer array.
/******************************************************************************/
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

/******************************************************************************/
// Recreate page tree to only retain specified pages.
/******************************************************************************/

void retainpage(fz_context *ctx, pdf_document *doc, pdf_obj *parent, pdf_obj *kids, int page)
{
    pdf_obj *pageref = pdf_lookup_page_obj(ctx, doc, page);

    pdf_flatten_inheritable_page_items(ctx, pageref);

    pdf_dict_put(ctx, pageref, PDF_NAME_Parent, parent);

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

        /*********************************************************************/
        // Strip any children to start with. This takes care of
        // First / Last / Count for us.
        /*********************************************************************/
        nc = strip_outlines(ctx, doc, current, page_count, page_object_nums, names_list);

        if (!dest_is_valid(ctx, current, page_count, page_object_nums, names_list))
        {
            if (nc == 0)
            {
                /*************************************************************/
                // Outline with invalid dest and no children. Drop it by
                // pulling the next one in here.
                /*************************************************************/
                pdf_obj *next = pdf_dict_get(ctx, current, PDF_NAME_Next);
                if (next == NULL)
                {
                    // There is no next one to pull in
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
                // Outline with invalid dest, but children. Just drop the dest.
                pdf_dict_del(ctx, current, PDF_NAME_Dest);
                pdf_dict_del(ctx, current, PDF_NAME_A);
                current = pdf_dict_get(ctx, current, PDF_NAME_Next);
            }
        }
        else
        {
            // Keep this one
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

    if (outlines == NULL)
        return 0;

    first = pdf_dict_get(ctx, outlines, PDF_NAME_First);
    if (first == NULL)
        nc = 0;
    else
        nc = strip_outline(ctx, doc, first, page_count, page_object_nums,
                           names_list, &first, &last);

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

/******************************************************************************/
//   called by PyMuPDF:
//   argc  = length of "liste"
//   liste = (list of int) page numbers to retain
/******************************************************************************/
void retainpages(fz_context *ctx, globals *glo, int argc, int *liste)
{
    pdf_obj *oldroot, *root, *pages, *kids, *countobj, *olddests;
    pdf_document *doc = glo->doc;
    int argidx = 0;
    pdf_obj *names_list = NULL;
    pdf_obj *outlines;
    pdf_obj *ocproperties;
    int pagecount;
    int i;
    int *page_object_nums;

/******************************************************************************/
//    Keep only pages/type and (reduced) dest entries to avoid
//    references to dropped pages
/******************************************************************************/
    oldroot = pdf_dict_get(ctx, pdf_trailer(ctx, doc), PDF_NAME_Root);
    pages = pdf_dict_get(ctx, oldroot, PDF_NAME_Pages);
    olddests = pdf_load_name_tree(ctx, doc, PDF_NAME_Dests);
    outlines = pdf_dict_get(ctx, oldroot, PDF_NAME_Outlines);
    ocproperties = pdf_dict_get(ctx, oldroot, PDF_NAME_OCProperties);

    root = pdf_new_dict(ctx, doc, 3);
    pdf_dict_put(ctx, root, PDF_NAME_Type, pdf_dict_get(ctx, oldroot, PDF_NAME_Type));
    pdf_dict_put(ctx, root, PDF_NAME_Pages, pdf_dict_get(ctx, oldroot, PDF_NAME_Pages));
    if (outlines)
        pdf_dict_put(ctx, root, PDF_NAME_Outlines, outlines);
    if (ocproperties)
        pdf_dict_put(ctx, root, PDF_NAME_OCProperties, ocproperties);

    pdf_update_object(ctx, doc, pdf_to_num(ctx, oldroot), root);

    // Create a new kids array with only the pages we want to keep
    kids = pdf_new_array(ctx, doc, 1);

    // Retain pages specified
    int page;
    for (page = 0; page < argc; page++)
        {
            retainpage(ctx, doc, pages, kids, liste[page]);
        }

    // Update page count and kids array
    countobj = pdf_new_int(ctx, doc, pdf_array_len(ctx, kids));
    pdf_dict_put(ctx, pages, PDF_NAME_Count, countobj);
    pdf_drop_obj(ctx, countobj);
    pdf_dict_put(ctx, pages, PDF_NAME_Kids, kids);
    pdf_drop_obj(ctx, kids);

    // Force the next call to pdf_count_pages to recount
    glo->doc->page_count = 0;

    pagecount = pdf_count_pages(ctx, doc);
    page_object_nums = fz_calloc(ctx, pagecount, sizeof(*page_object_nums));
    for (i = 0; i < pagecount; i++)
    {
        pdf_obj *pageref = pdf_lookup_page_obj(ctx, doc, i);
        page_object_nums[i] = pdf_to_num(ctx, pageref);
    }

/******************************************************************************/
// If we had an old Dests tree (now reformed as an olddests dictionary),
// keep any entries in there that point to valid pages.
// This may mean we keep more than we need, but it is safe at least.
/******************************************************************************/
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
                pdf_array_push_drop(ctx, names_list, key_str);
                pdf_array_push(ctx, names_list, val);
            }
        }

        pdf_dict_put(ctx, dests, PDF_NAME_Names, names_list);
        pdf_dict_put(ctx, names, PDF_NAME_Dests, dests);
        pdf_dict_put(ctx, root, PDF_NAME_Names, names);

        pdf_drop_obj(ctx, names);
        pdf_drop_obj(ctx, dests);
        pdf_drop_obj(ctx, olddests);
    }

/*****************************************************************************/
// Edit each pages /Annot list to remove any links pointing to nowhere.
/*****************************************************************************/
    for (i = 0; i < pagecount; i++)
    {
        pdf_obj *pageref = pdf_lookup_page_obj(ctx, doc, i);

        pdf_obj *annots = pdf_dict_get(ctx, pageref, PDF_NAME_Annots);

        int len = pdf_array_len(ctx, annots);
        int j;

        for (j = 0; j < len; j++)
        {
            pdf_obj *o = pdf_array_get(ctx, annots, j);

            if (!pdf_name_eq(ctx, pdf_dict_get(ctx, o, PDF_NAME_Subtype), PDF_NAME_Link))
                continue;

            if (!dest_is_valid(ctx, o, pagecount, page_object_nums, names_list))
            {
                // Remove this annotation
                pdf_array_delete(ctx, annots, j);
                len--;
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
// C helper functions for extractJSON
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
        /* ==> next 2 lines commented out                 */
        /**************************************************/
        //if ((i & 15) == 0)
        //    fz_printf(ctx, out, "\n");
        fz_printf(ctx, out, "%c%c%c%c", set[c>>2], set[((c&3)<<4)|(d>>4)], set[((d&15)<<2)|(e>>6)], set[e & 63]);
    }
    i *= 3;
    switch (bufflen-i)
    {
        case 2:
        {
            int c = buff[i];
            int d = buff[i+1];
            fz_printf(ctx, out, "%c%c%c=", set[c>>2], set[((c&3)<<4)|(d>>4)], set[((d&15)<<2)]);
            break;
        }
    case 1:
        {
            int c = buff[i];
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
                fz_compressed_buffer *buffer = fz_compressed_image_buffer(gctx, image->image);
                fz_print_rect_json(ctx, out, &(image->bbox));
                fz_printf(ctx, out, "\"imgtype\":%d,\"width\":%d,\"height\":%d,",
                                    buffer->params.type,
                                    image->image->w,
                                    image->image->h);
                fz_printf(ctx, out, "\"image\":\n");
                if (buffer == NULL) {
                    fz_printf(ctx, out, "null");
                } else {
                    fz_printf(ctx, out, "\"");
                    fz_send_data_base64(ctx, out, buffer->buffer);
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
