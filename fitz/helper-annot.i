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
                                           pdf_to_num(ctx, page->obj), &page_ctm);
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
// annotation field (widget) types
//----------------------------------------------------------------------------
#define ANNOT_WG_NOT_WIDGET -1
#define ANNOT_WG_PUSHBUTTON 0
#define ANNOT_WG_CHECKBOX 1
#define ANNOT_WG_RADIOBUTTON 2
#define ANNOT_WG_TEXT 3
#define ANNOT_WG_LISTBOX 4
#define ANNOT_WG_COMBOBOX 5
#define ANNOT_WG_SIGNATURE 6

//----------------------------------------------------------------------------
// annotation text widget subtypes
//----------------------------------------------------------------------------
#define ANNOT_WG_TEXT_UNRESTRAINED 0
#define ANNOT_WG_TEXT_NUMBER 1
#define ANNOT_WG_TEXT_SPECIAL 2
#define ANNOT_WG_TEXT_DATE 3
#define ANNOT_WG_TEXT_TIME 4

//----------------------------------------------------------------------------
// return string for line end style
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
// return string name of annotation type
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

//-----------------------------------------------------------------------------
// create a strike-out / underline / highlight annotation
//-----------------------------------------------------------------------------
struct fz_annot_s *JM_AnnotTextmarker(fz_context *ctx, pdf_page *page, fz_rect *rect, int type)
{
    pdf_annot *annot = NULL;
    float line_thickness = 0.0f;
    float line_height = 0.0f;
    float alpha = 1.0f;
    float h  = rect->y1 - rect->y0;
    fz_rect bbox = {rect->x0, rect->y0, rect->x1, rect->y1};
    float color[3] = {0,0,0};
	switch (type)
	{
		case PDF_ANNOT_HIGHLIGHT:
			color[0] = 0.933333f;
			color[1] = 0.788235f;
			color[2] = 0.0f;
			alpha = 0.3f;
			line_thickness = 1.0f;
			line_height = 0.5f;
			break;
		case PDF_ANNOT_UNDERLINE:
			color[0] = 0.0f;
			color[1] = 0.0f;
			color[2] = 1.0f;
			alpha = 1.0f;
			line_thickness = 0.07f;
			line_height = 0.075f;
            bbox.y0 += 0.8f * h;
            bbox.y1 += 0.8f * h;
			break;
		case PDF_ANNOT_STRIKE_OUT:
			color[0] = 1.0f;
			color[1] = 0.0f;
			color[2] = 0.0f;
			alpha = 1.0f;
			line_thickness = 0.07f;
			line_height = 0.375f;
            bbox.y0 += 0.17f * h;
            bbox.y1 += 0.17f * h;
			break;
	}
    fz_try(ctx)
    {
        pdf_document *pdf = page->doc;
        annot = pdf_create_annot(ctx, page, type);
        pdf_set_annot_color(ctx, annot, 3, color);
        pdf_set_annot_border(ctx, annot, line_thickness);
        pdf_add_annot_quad_point(ctx, annot, bbox);
        pdf_set_annot_rect(ctx, annot, &bbox);
        pdf_set_markup_appearance(ctx, pdf, annot, color, alpha, line_thickness, line_height);
    }
    fz_catch(ctx) fz_rethrow(ctx);
    return (fz_annot *) annot;
}

//-----------------------------------------------------------------------------
// create a circle or rectangle annotation
//-----------------------------------------------------------------------------
struct fz_annot_s *JM_AnnotCircleOrRect(fz_context *ctx, pdf_page *page, fz_rect *rect, int type)
{
    pdf_annot *annot;
    float col[3] = {0,0,0};
    float width  = 1;
    fz_try(ctx)
    {
        pdf_document *pdf = page->doc;
        annot = pdf_create_annot(ctx, page, type);
        pdf_set_annot_border(ctx, annot, width);
        pdf_set_annot_color(ctx, annot, 3, col);
        pdf_set_annot_rect(ctx, annot, rect);
        pdf_obj *rd = pdf_new_array(ctx, pdf, 4);
        pdf_dict_puts_drop(ctx, annot->obj, "RD", rd);
        for (int i = 0; i < 4; i++)
            pdf_array_push_real(ctx, rd, width);
    }
    fz_catch(ctx) fz_rethrow(ctx);
    return (fz_annot *) annot;
}

//-----------------------------------------------------------------------------
// create a polyline or polygon annotation
//-----------------------------------------------------------------------------
struct fz_annot_s *JM_AnnotMultiline(fz_context *ctx, pdf_page *page, PyObject *points, int type)
{
    pdf_annot *annot;
    fz_try(ctx)
    {
        float col[3] = {0,0,0};
        float width  = 1;
        fz_point point = {0,0};
        fz_rect rect;
        
        int n = 0, i;
        if (PySequence_Check(points)) n = PySequence_Size(points);
        if (n < 2) THROWMSG("invalid points list");
        annot = pdf_create_annot(ctx, page, type);
        for (i = 0; i < n; i++)
        {
            PyObject *p = PySequence_ITEM(points, i);
            if (!PySequence_Check(p) || PySequence_Size(p) != 2)
                THROWMSG("invalid points list");
            // ===> treating a fitz.Point as a 2-tuple seems to work!
            point.x = (float) PyFloat_AsDouble(PySequence_GetItem(p, 0));
            point.y = (float) PyFloat_AsDouble(PySequence_GetItem(p, 1));
            Py_DECREF(p);
            pdf_add_annot_vertex(ctx, annot, point);
            if (i == 0)
            {
                rect.x0 = point.x;
                rect.y0 = point.y;
                rect.x1 = point.x;
                rect.y1 = point.y;
            }
            else
                fz_include_point_in_rect(&rect, &point);
        }
        pdf_set_annot_border(ctx, annot, width); // standard: width = 1
        pdf_set_annot_color(ctx, annot, 3, col); // standard: black
        pdf_set_annot_rect(ctx, annot, &rect);
    }
    fz_catch(ctx) fz_rethrow(ctx);
    return (fz_annot *) annot;
}

%}