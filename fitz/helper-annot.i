%{
//----------------------------------------------------------------------------
// refreshes the link and annotation tables of a page
//----------------------------------------------------------------------------
void refresh_link_table(fz_context *ctx, pdf_page *page)
{
    pdf_obj *annots_arr = pdf_dict_get(ctx, page->obj, PDF_NAME_Annots);
    if (annots_arr)
    {
        fz_rect page_mediabox;
        fz_matrix page_ctm;
        pdf_page_transform(ctx, page, &page_mediabox, &page_ctm);
        page->links = pdf_load_link_annots(ctx, page->doc, annots_arr,
                                           pdf_to_num(gctx, page->obj), &page_ctm);
        pdf_load_annots(ctx, page, annots_arr);
    }
    return;
}

//----------------------------------------------------------------------------
// annotation types
//----------------------------------------------------------------------------
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

//----------------------------------------------------------------------------
// annotation flag bits
//----------------------------------------------------------------------------
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

//----------------------------------------------------------------------------
// annotation line ending styles
//----------------------------------------------------------------------------
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

//----------------------------------------------------------------------------
// return character string for line end style
//----------------------------------------------------------------------------
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

//----------------------------------------------------------------------------
// return character name of annotation type
//----------------------------------------------------------------------------
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
%}