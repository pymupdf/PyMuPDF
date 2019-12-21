%inline %{
//----------------------------------------------------------------------------
// general
//----------------------------------------------------------------------------
#define EPSILON 1e-5
//----------------------------------------------------------------------------
// annotation types
//----------------------------------------------------------------------------
#define PDF_ANNOT_TEXT 0
#define PDF_ANNOT_LINK 1
#define PDF_ANNOT_FREE_TEXT 2
#define PDF_ANNOT_LINE 3
#define PDF_ANNOT_SQUARE 4
#define PDF_ANNOT_CIRCLE 5
#define PDF_ANNOT_POLYGON 6
#define PDF_ANNOT_POLYLINE 7
#define PDF_ANNOT_HIGHLIGHT 8
#define PDF_ANNOT_UNDERLINE 9
#define PDF_ANNOT_SQUIGGLY 10
#define PDF_ANNOT_STRIKEOUT 11
#define PDF_ANNOT_REDACT 12
#define PDF_ANNOT_STAMP 13
#define PDF_ANNOT_CARET 14
#define PDF_ANNOT_INK 15
#define PDF_ANNOT_POPUP 16
#define PDF_ANNOT_FILEATTACHMENT 17
#define PDF_ANNOT_SOUND 18
#define PDF_ANNOT_MOVIE 19
#define PDF_ANNOT_WIDGET 20
#define PDF_ANNOT_SCREEN 21
#define PDF_ANNOT_PRINTERMARK 22
#define PDF_ANNOT_TRAPNET 23
#define PDF_ANNOT_WATERMARK 24
#define PDF_ANNOT_3D 25
#define PDF_ANNOT_UNKNOWN -1

// deprecated aliases
#define ANNOT_TEXT PDF_ANNOT_TEXT
#define ANNOT_LINK PDF_ANNOT_LINK
#define ANNOT_FREETEXT PDF_ANNOT_FREE_TEXT
#define ANNOT_LINE PDF_ANNOT_LINE
#define ANNOT_SQUARE PDF_ANNOT_SQUARE
#define ANNOT_CIRCLE PDF_ANNOT_CIRCLE
#define ANNOT_POLYGON PDF_ANNOT_POLYGON
#define ANNOT_POLYLINE PDF_ANNOT_POLYLINE
#define ANNOT_HIGHLIGHT PDF_ANNOT_HIGHLIGHT
#define ANNOT_UNDERLINE PDF_ANNOT_UNDERLINE
#define ANNOT_SQUIGGLY PDF_ANNOT_SQUIGGLY
#define ANNOT_STRIKEOUT PDF_ANNOT_STRIKEOUT
#define ANNOT_STAMP PDF_ANNOT_STAMP
#define ANNOT_CARET PDF_ANNOT_CARET
#define ANNOT_INK PDF_ANNOT_INK
#define ANNOT_POPUP PDF_ANNOT_POPUP
#define ANNOT_FILEATTACHMENT PDF_ANNOT_FILEATTACHMENT
#define ANNOT_SOUND PDF_ANNOT_SOUND
#define ANNOT_MOVIE PDF_ANNOT_MOVIE
#define ANNOT_WIDGET PDF_ANNOT_WIDGET
#define ANNOT_SCREEN PDF_ANNOT_WIDGET
#define ANNOT_PRINTERMARK PDF_ANNOT_PRINTERMARK
#define ANNOT_TRAPNET PDF_ANNOT_TRAPNET
#define ANNOT_WATERMARK PDF_ANNOT_WATERMARK
#define ANNOT_3D PDF_ANNOT_3D

//----------------------------------------------------------------------------
// annotation flag bits
//----------------------------------------------------------------------------
#define PDF_ANNOT_IS_Invisible 1 << (1-1)
#define PDF_ANNOT_IS_Hidden 1 << (2-1)
#define PDF_ANNOT_IS_Print 1 << (3-1)
#define PDF_ANNOT_IS_NoZoom 1 << (4-1)
#define PDF_ANNOT_IS_NoRotate 1 << (5-1)
#define PDF_ANNOT_IS_NoView 1 << (6-1)
#define PDF_ANNOT_IS_ReadOnly 1 << (7-1)
#define PDF_ANNOT_IS_Locked 1 << (8-1)
#define PDF_ANNOT_IS_ToggleNoView 1 << (9-1)
#define PDF_ANNOT_IS_LockedContents 1 << (10-1)

// deprecated aliases
#define ANNOT_XF_Invisible PDF_ANNOT_IS_Invisible
#define ANNOT_XF_Hidden PDF_ANNOT_IS_Hidden
#define ANNOT_XF_Print PDF_ANNOT_IS_Print
#define ANNOT_XF_NoZoom PDF_ANNOT_IS_NoZoom
#define ANNOT_XF_NoRotate PDF_ANNOT_IS_NoRotate
#define ANNOT_XF_NoView PDF_ANNOT_IS_NoView
#define ANNOT_XF_ReadOnly PDF_ANNOT_IS_ReadOnly
#define ANNOT_XF_Locked PDF_ANNOT_IS_Locked
#define ANNOT_XF_ToggleNoView PDF_ANNOT_IS_ToggleNoView
#define ANNOT_XF_LockedContents PDF_ANNOT_IS_LockedContents

//----------------------------------------------------------------------------
// annotation line ending styles
//----------------------------------------------------------------------------
#define PDF_ANNOT_LE_NONE 0
#define PDF_ANNOT_LE_SQUARE 1
#define PDF_ANNOT_LE_CIRCLE 2
#define PDF_ANNOT_LE_DIAMOND 3
#define PDF_ANNOT_LE_OPEN_ARROW 4
#define PDF_ANNOT_LE_CLOSED_ARROW 5
#define PDF_ANNOT_LE_BUTT 6
#define PDF_ANNOT_LE_R_OPEN_ARROW 7
#define PDF_ANNOT_LE_R_CLOSED_ARROW 8
#define PDF_ANNOT_LE_SLASH 9

// deprecated aliases
#define ANNOT_LE_None PDF_ANNOT_LE_NONE
#define ANNOT_LE_Square PDF_ANNOT_LE_SQUARE
#define ANNOT_LE_Circle PDF_ANNOT_LE_CIRCLE
#define ANNOT_LE_Diamond PDF_ANNOT_LE_DIAMOND
#define ANNOT_LE_OpenArrow PDF_ANNOT_LE_OPEN_ARROW
#define ANNOT_LE_ClosedArrow PDF_ANNOT_LE_CLOSED_ARROW
#define ANNOT_LE_Butt PDF_ANNOT_LE_BUTT
#define ANNOT_LE_ROpenArrow PDF_ANNOT_LE_R_OPEN_ARROW
#define ANNOT_LE_RClosedArrow PDF_ANNOT_LE_R_CLOSED_ARROW
#define ANNOT_LE_Slash PDF_ANNOT_LE_SLASH

//----------------------------------------------------------------------------
// annotation field (widget) types
//----------------------------------------------------------------------------
#define PDF_WIDGET_TYPE_UNKNOWN 0
#define PDF_WIDGET_TYPE_BUTTON 1
#define PDF_WIDGET_TYPE_CHECKBOX 2
#define PDF_WIDGET_TYPE_COMBOBOX 3
#define PDF_WIDGET_TYPE_LISTBOX 4
#define PDF_WIDGET_TYPE_RADIOBUTTON 5
#define PDF_WIDGET_TYPE_SIGNATURE 6
#define PDF_WIDGET_TYPE_TEXT 7

// deprecated aliases
#define ANNOT_WG_NOT_WIDGET PDF_WIDGET_TYPE_UNKNOWN
#define ANNOT_WG_PUSHBUTTON PDF_WIDGET_TYPE_BUTTON
#define ANNOT_WG_CHECKBOX PDF_WIDGET_TYPE_CHECKBOX
#define ANNOT_WG_RADIOBUTTON PDF_WIDGET_TYPE_RADIOBUTTON
#define ANNOT_WG_TEXT PDF_WIDGET_TYPE_TEXT
#define ANNOT_WG_LISTBOX PDF_WIDGET_TYPE_LISTBOX
#define ANNOT_WG_COMBOBOX PDF_WIDGET_TYPE_COMBOBOX
#define ANNOT_WG_SIGNATURE PDF_WIDGET_TYPE_SIGNATURE

//----------------------------------------------------------------------------
// annotation text widget subtypes
//----------------------------------------------------------------------------
#define PDF_WIDGET_TX_FORMAT_NONE 0
#define PDF_WIDGET_TX_FORMAT_NUMBER 1
#define PDF_WIDGET_TX_FORMAT_SPECIAL 2
#define PDF_WIDGET_TX_FORMAT_DATE 3
#define PDF_WIDGET_TX_FORMAT_TIME 4

// deprecated aliases
#define ANNOT_WG_TEXT_UNRESTRAINED PDF_WIDGET_TX_FORMAT_NONE
#define ANNOT_WG_TEXT_NUMBER PDF_WIDGET_TX_FORMAT_NUMBER
#define ANNOT_WG_TEXT_SPECIAL PDF_WIDGET_TX_FORMAT_SPECIAL
#define ANNOT_WG_TEXT_DATE PDF_WIDGET_TX_FORMAT_DATE
#define ANNOT_WG_TEXT_TIME PDF_WIDGET_TX_FORMAT_TIME

//----------------------------------------------------------------------------
// annotation widget flags
//----------------------------------------------------------------------------
// Common to all field types
#define PDF_FIELD_IS_READ_ONLY 1
#define PDF_FIELD_IS_REQUIRED 1 << 1
#define PDF_FIELD_IS_NO_EXPORT 1 << 2

// deprecated aliases
#define WIDGET_Ff_ReadOnly PDF_FIELD_IS_READ_ONLY
#define WIDGET_Ff_Required PDF_FIELD_IS_REQUIRED
#define WIDGET_Ff_NoExport PDF_FIELD_IS_NO_EXPORT

// Text fields
#define PDF_TX_FIELD_IS_MULTILINE  1 << 12
#define PDF_TX_FIELD_IS_PASSWORD  1 << 13
#define PDF_TX_FIELD_IS_FILE_SELECT  1 << 20
#define PDF_TX_FIELD_IS_DO_NOT_SPELL_CHECK  1 << 22
#define PDF_TX_FIELD_IS_DO_NOT_SCROLL  1 << 23
#define PDF_TX_FIELD_IS_COMB  1 << 24
#define PDF_TX_FIELD_IS_RICH_TEXT  1 << 25

// deprecated aliases
#define WIDGET_Ff_Multiline PDF_TX_FIELD_IS_MULTILINE
#define WIDGET_Ff_Password PDF_TX_FIELD_IS_PASSWORD
#define WIDGET_Ff_FileSelect PDF_TX_FIELD_IS_FILE_SELECT
#define WIDGET_Ff_DoNotSpellCheck PDF_TX_FIELD_IS_DO_NOT_SPELL_CHECK
#define WIDGET_Ff_DoNotScroll PDF_TX_FIELD_IS_DO_NOT_SCROLL
#define WIDGET_Ff_Comb PDF_TX_FIELD_IS_COMB
#define WIDGET_Ff_RichText PDF_TX_FIELD_IS_RICH_TEXT

// Button fields
#define PDF_BTN_FIELD_IS_NO_TOGGLE_TO_OFF  1 << 14
#define PDF_BTN_FIELD_IS_RADIO  1 << 15
#define PDF_BTN_FIELD_IS_PUSHBUTTON  1 << 16
#define PDF_BTN_FIELD_IS_RADIOS_IN_UNISON  1 << 25

// deprecated aliases
#define WIDGET_Ff_NoToggleToOff PDF_BTN_FIELD_IS_NO_TOGGLE_TO_OFF
#define WIDGET_Ff_Radio PDF_BTN_FIELD_IS_RADIO
#define WIDGET_Ff_Pushbutton PDF_BTN_FIELD_IS_PUSHBUTTON
#define WIDGET_Ff_RadioInUnison PDF_BTN_FIELD_IS_RADIOS_IN_UNISON

// Choice fields
#define PDF_CH_FIELD_IS_COMBO  1 << 17
#define PDF_CH_FIELD_IS_EDIT  1 << 18
#define PDF_CH_FIELD_IS_SORT  1 << 19
#define PDF_CH_FIELD_IS_MULTI_SELECT  1 << 21
#define PDF_CH_FIELD_IS_DO_NOT_SPELL_CHECK  1 << 22
#define PDF_CH_FIELD_IS_COMMIT_ON_SEL_CHANGE  1 << 26

// deprecated aliases
#define WIDGET_Ff_Combo PDF_CH_FIELD_IS_COMBO
#define WIDGET_Ff_Edit PDF_CH_FIELD_IS_EDIT
#define WIDGET_Ff_Sort PDF_CH_FIELD_IS_SORT
#define WIDGET_Ff_MultiSelect PDF_CH_FIELD_IS_MULTI_SELECT
#define WIDGET_Ff_CommitOnSelCHange PDF_CH_FIELD_IS_COMMIT_ON_SEL_CHANGE

//----------------------------------------------------------------------------
// colorspace identifiers
//----------------------------------------------------------------------------
#define CS_RGB  1
#define CS_GRAY 2
#define CS_CMYK 3

//----------------------------------------------------------------------------
// PDF encryption algorithms
//----------------------------------------------------------------------------
#define PDF_ENCRYPT_KEEP 0
#define PDF_ENCRYPT_NONE 1
#define PDF_ENCRYPT_RC4_40 2
#define PDF_ENCRYPT_RC4_128 3
#define PDF_ENCRYPT_AES_128 4
#define PDF_ENCRYPT_AES_256 5
#define PDF_ENCRYPT_UNKNOWN 6

//----------------------------------------------------------------------------
// PDF permission codes
//----------------------------------------------------------------------------
#define PDF_PERM_PRINT 1 << 2
#define PDF_PERM_MODIFY 1 << 3
#define PDF_PERM_COPY 1 << 4
#define PDF_PERM_ANNOTATE 1 << 5
#define PDF_PERM_FORM 1 << 8
#define PDF_PERM_ACCESSIBILITY 1 << 9
#define PDF_PERM_ASSEMBLE 1 << 10
#define PDF_PERM_PRINT_HQ 1 << 11

// General text flags
#define TEXT_FONT_SUPERSCRIPT 1
#define TEXT_FONT_ITALIC 2
#define TEXT_FONT_SERIFED 4
#define TEXT_FONT_MONOSPACED 8
#define TEXT_FONT_BOLD 16

%}

%{
// Global Constants - Python dictionary keys
PyObject *dictkey_bbox;
PyObject *dictkey_blocks;
PyObject *dictkey_bpc;
PyObject *dictkey_c;
PyObject *dictkey_chars;
PyObject *dictkey_color;
PyObject *dictkey_colorspace;
PyObject *dictkey_content;
PyObject *dictkey_creationDate;
PyObject *dictkey_cs_name;
PyObject *dictkey_dashes;
PyObject *dictkey_desc;
PyObject *dictkey_dir;
PyObject *dictkey_effect;
PyObject *dictkey_ext;
PyObject *dictkey_filename;
PyObject *dictkey_fill;
PyObject *dictkey_flags;
PyObject *dictkey_font;
PyObject *dictkey_height;
PyObject *dictkey_id;
PyObject *dictkey_image;
PyObject *dictkey_length;
PyObject *dictkey_lines;
PyObject *dictkey_modDate;
PyObject *dictkey_name;
PyObject *dictkey_origin;
PyObject *dictkey_size;
PyObject *dictkey_smask;
PyObject *dictkey_spans;
PyObject *dictkey_stroke;
PyObject *dictkey_style;
PyObject *dictkey_subject;
PyObject *dictkey_text;
PyObject *dictkey_title;
PyObject *dictkey_type;
PyObject *dictkey_ufilename;
PyObject *dictkey_width;
PyObject *dictkey_wmode;
PyObject *dictkey_xref;
PyObject *dictkey_xres;
PyObject *dictkey_yres;

%}
