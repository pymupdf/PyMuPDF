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
#define PDF_ANNOT_POLY_LINE 7
#define PDF_ANNOT_HIGHLIGHT 8
#define PDF_ANNOT_UNDERLINE 9
#define PDF_ANNOT_SQUIGGLY 10
#define PDF_ANNOT_STRIKE_OUT 11
#define PDF_ANNOT_REDACT 12
#define PDF_ANNOT_STAMP 13
#define PDF_ANNOT_CARET 14
#define PDF_ANNOT_INK 15
#define PDF_ANNOT_POPUP 16
#define PDF_ANNOT_FILE_ATTACHMENT 17
#define PDF_ANNOT_SOUND 18
#define PDF_ANNOT_MOVIE 19
#define PDF_ANNOT_RICH_MEDIA 20
#define PDF_ANNOT_WIDGET 21
#define PDF_ANNOT_SCREEN 22
#define PDF_ANNOT_PRINTER_MARK 23
#define PDF_ANNOT_TRAP_NET 24
#define PDF_ANNOT_WATERMARK 25
#define PDF_ANNOT_3D 26
#define PDF_ANNOT_PROJECTION 27
#define PDF_ANNOT_UNKNOWN -1

//------------------------
// redaction annot options
//------------------------
#define PDF_REDACT_IMAGE_NONE 0
#define PDF_REDACT_IMAGE_REMOVE 1
#define PDF_REDACT_IMAGE_PIXELS 2

//----------------------------------------------------------------------------
// annotation flag bits
//----------------------------------------------------------------------------
#define PDF_ANNOT_IS_INVISIBLE 1 << (1-1)
#define PDF_ANNOT_IS_HIDDEN 1 << (2-1)
#define PDF_ANNOT_IS_PRINT 1 << (3-1)
#define PDF_ANNOT_IS_NO_ZOOM 1 << (4-1)
#define PDF_ANNOT_IS_NO_ROTATE 1 << (5-1)
#define PDF_ANNOT_IS_NO_VIEW 1 << (6-1)
#define PDF_ANNOT_IS_READ_ONLY 1 << (7-1)
#define PDF_ANNOT_IS_LOCKED 1 << (8-1)
#define PDF_ANNOT_IS_TOGGLE_NO_VIEW 1 << (9-1)
#define PDF_ANNOT_IS_LOCKED_CONTENTS 1 << (10-1)


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


//----------------------------------------------------------------------------
// annotation text widget subtypes
//----------------------------------------------------------------------------
#define PDF_WIDGET_TX_FORMAT_NONE 0
#define PDF_WIDGET_TX_FORMAT_NUMBER 1
#define PDF_WIDGET_TX_FORMAT_SPECIAL 2
#define PDF_WIDGET_TX_FORMAT_DATE 3
#define PDF_WIDGET_TX_FORMAT_TIME 4


//----------------------------------------------------------------------------
// annotation widget flags
//----------------------------------------------------------------------------
// Common to all field types
#define PDF_FIELD_IS_READ_ONLY 1
#define PDF_FIELD_IS_REQUIRED 1 << 1
#define PDF_FIELD_IS_NO_EXPORT 1 << 2


// Text fields
#define PDF_TX_FIELD_IS_MULTILINE  1 << 12
#define PDF_TX_FIELD_IS_PASSWORD  1 << 13
#define PDF_TX_FIELD_IS_FILE_SELECT  1 << 20
#define PDF_TX_FIELD_IS_DO_NOT_SPELL_CHECK  1 << 22
#define PDF_TX_FIELD_IS_DO_NOT_SCROLL  1 << 23
#define PDF_TX_FIELD_IS_COMB  1 << 24
#define PDF_TX_FIELD_IS_RICH_TEXT  1 << 25


// Button fields
#define PDF_BTN_FIELD_IS_NO_TOGGLE_TO_OFF  1 << 14
#define PDF_BTN_FIELD_IS_RADIO  1 << 15
#define PDF_BTN_FIELD_IS_PUSHBUTTON  1 << 16
#define PDF_BTN_FIELD_IS_RADIOS_IN_UNISON  1 << 25


// Choice fields
#define PDF_CH_FIELD_IS_COMBO  1 << 17
#define PDF_CH_FIELD_IS_EDIT  1 << 18
#define PDF_CH_FIELD_IS_SORT  1 << 19
#define PDF_CH_FIELD_IS_MULTI_SELECT  1 << 21
#define PDF_CH_FIELD_IS_DO_NOT_SPELL_CHECK  1 << 22
#define PDF_CH_FIELD_IS_COMMIT_ON_SEL_CHANGE  1 << 26


// Signature fields errors
#define PDF_SIGNATURE_ERROR_OKAY 0
#define PDF_SIGNATURE_ERROR_NO_SIGNATURES 1
#define PDF_SIGNATURE_ERROR_NO_CERTIFICATE 2
#define PDF_SIGNATURE_ERROR_DIGEST_FAILURE 3
#define PDF_SIGNATURE_ERROR_SELF_SIGNED 4
#define PDF_SIGNATURE_ERROR_SELF_SIGNED_IN_CHAIN 5
#define PDF_SIGNATURE_ERROR_NOT_TRUSTED 6
#define PDF_SIGNATURE_ERROR_UNKNOWN 7


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

//----------------------------------------------------------------------------
// PDF Blend Modes
//----------------------------------------------------------------------------
#define PDF_BM_Color "Color"
#define PDF_BM_ColorBurn "ColorBurn"
#define PDF_BM_ColorDodge "ColorDodge"
#define PDF_BM_Darken "Darken"
#define PDF_BM_Difference "Difference"
#define PDF_BM_Exclusion "Exclusion"
#define PDF_BM_HardLight "HardLight"
#define PDF_BM_Hue "Hue"
#define PDF_BM_Lighten "Lighten"
#define PDF_BM_Luminosity "Luminosity"
#define PDF_BM_Multiply "Multiply"
#define PDF_BM_Normal "Normal"
#define PDF_BM_Overlay "Overlay"
#define PDF_BM_Saturation "Saturation"
#define PDF_BM_Screen "Screen"
#define PDF_BM_SoftLight "Softlight"


// General text flags
#define TEXT_FONT_SUPERSCRIPT 1
#define TEXT_FONT_ITALIC 2
#define TEXT_FONT_SERIFED 4
#define TEXT_FONT_MONOSPACED 8
#define TEXT_FONT_BOLD 16

// UCDN Script codes
#define UCDN_SCRIPT_COMMON 0
#define UCDN_SCRIPT_LATIN 1
#define UCDN_SCRIPT_GREEK 2
#define UCDN_SCRIPT_CYRILLIC 3
#define UCDN_SCRIPT_ARMENIAN 4
#define UCDN_SCRIPT_HEBREW 5
#define UCDN_SCRIPT_ARABIC 6
#define UCDN_SCRIPT_SYRIAC 7
#define UCDN_SCRIPT_THAANA 8
#define UCDN_SCRIPT_DEVANAGARI 9
#define UCDN_SCRIPT_BENGALI 10
#define UCDN_SCRIPT_GURMUKHI 11
#define UCDN_SCRIPT_GUJARATI 12
#define UCDN_SCRIPT_ORIYA 13
#define UCDN_SCRIPT_TAMIL 14
#define UCDN_SCRIPT_TELUGU 15
#define UCDN_SCRIPT_KANNADA 16
#define UCDN_SCRIPT_MALAYALAM 17
#define UCDN_SCRIPT_SINHALA 18
#define UCDN_SCRIPT_THAI 19
#define UCDN_SCRIPT_LAO 20
#define UCDN_SCRIPT_TIBETAN 21
#define UCDN_SCRIPT_MYANMAR 22
#define UCDN_SCRIPT_GEORGIAN 23
#define UCDN_SCRIPT_HANGUL 24
#define UCDN_SCRIPT_ETHIOPIC 25
#define UCDN_SCRIPT_CHEROKEE 26
#define UCDN_SCRIPT_CANADIAN_ABORIGINAL 27
#define UCDN_SCRIPT_OGHAM 28
#define UCDN_SCRIPT_RUNIC 29
#define UCDN_SCRIPT_KHMER 30
#define UCDN_SCRIPT_MONGOLIAN 31
#define UCDN_SCRIPT_HIRAGANA 32
#define UCDN_SCRIPT_KATAKANA 33
#define UCDN_SCRIPT_BOPOMOFO 34
#define UCDN_SCRIPT_HAN 35
#define UCDN_SCRIPT_YI 36
#define UCDN_SCRIPT_OLD_ITALIC 37
#define UCDN_SCRIPT_GOTHIC 38
#define UCDN_SCRIPT_DESERET 39
#define UCDN_SCRIPT_INHERITED 40
#define UCDN_SCRIPT_TAGALOG 41
#define UCDN_SCRIPT_HANUNOO 42
#define UCDN_SCRIPT_BUHID 43
#define UCDN_SCRIPT_TAGBANWA 44
#define UCDN_SCRIPT_LIMBU 45
#define UCDN_SCRIPT_TAI_LE 46
#define UCDN_SCRIPT_LINEAR_B 47
#define UCDN_SCRIPT_UGARITIC 48
#define UCDN_SCRIPT_SHAVIAN 49
#define UCDN_SCRIPT_OSMANYA 50
#define UCDN_SCRIPT_CYPRIOT 51
#define UCDN_SCRIPT_BRAILLE 52
#define UCDN_SCRIPT_BUGINESE 53
#define UCDN_SCRIPT_COPTIC 54
#define UCDN_SCRIPT_NEW_TAI_LUE 55
#define UCDN_SCRIPT_GLAGOLITIC 56
#define UCDN_SCRIPT_TIFINAGH 57
#define UCDN_SCRIPT_SYLOTI_NAGRI 58
#define UCDN_SCRIPT_OLD_PERSIAN 59
#define UCDN_SCRIPT_KHAROSHTHI 60
#define UCDN_SCRIPT_BALINESE 61
#define UCDN_SCRIPT_CUNEIFORM 62
#define UCDN_SCRIPT_PHOENICIAN 63
#define UCDN_SCRIPT_PHAGS_PA 64
#define UCDN_SCRIPT_NKO 65
#define UCDN_SCRIPT_SUNDANESE 66
#define UCDN_SCRIPT_LEPCHA 67
#define UCDN_SCRIPT_OL_CHIKI 68
#define UCDN_SCRIPT_VAI 69
#define UCDN_SCRIPT_SAURASHTRA 70
#define UCDN_SCRIPT_KAYAH_LI 71
#define UCDN_SCRIPT_REJANG 72
#define UCDN_SCRIPT_LYCIAN 73
#define UCDN_SCRIPT_CARIAN 74
#define UCDN_SCRIPT_LYDIAN 75
#define UCDN_SCRIPT_CHAM 76
#define UCDN_SCRIPT_TAI_THAM 77
#define UCDN_SCRIPT_TAI_VIET 78
#define UCDN_SCRIPT_AVESTAN 79
#define UCDN_SCRIPT_EGYPTIAN_HIEROGLYPHS 80
#define UCDN_SCRIPT_SAMARITAN 81
#define UCDN_SCRIPT_LISU 82
#define UCDN_SCRIPT_BAMUM 83
#define UCDN_SCRIPT_JAVANESE 84
#define UCDN_SCRIPT_MEETEI_MAYEK 85
#define UCDN_SCRIPT_IMPERIAL_ARAMAIC 86
#define UCDN_SCRIPT_OLD_SOUTH_ARABIAN 87
#define UCDN_SCRIPT_INSCRIPTIONAL_PARTHIAN 88
#define UCDN_SCRIPT_INSCRIPTIONAL_PAHLAVI 89
#define UCDN_SCRIPT_OLD_TURKIC 90
#define UCDN_SCRIPT_KAITHI 91
#define UCDN_SCRIPT_BATAK 92
#define UCDN_SCRIPT_BRAHMI 93
#define UCDN_SCRIPT_MANDAIC 94
#define UCDN_SCRIPT_CHAKMA 95
#define UCDN_SCRIPT_MEROITIC_CURSIVE 96
#define UCDN_SCRIPT_MEROITIC_HIEROGLYPHS 97
#define UCDN_SCRIPT_MIAO 98
#define UCDN_SCRIPT_SHARADA 99
#define UCDN_SCRIPT_SORA_SOMPENG 100
#define UCDN_SCRIPT_TAKRI 101
#define UCDN_SCRIPT_UNKNOWN 102
#define UCDN_SCRIPT_BASSA_VAH 103
#define UCDN_SCRIPT_CAUCASIAN_ALBANIAN 104
#define UCDN_SCRIPT_DUPLOYAN 105
#define UCDN_SCRIPT_ELBASAN 106
#define UCDN_SCRIPT_GRANTHA 107
#define UCDN_SCRIPT_KHOJKI 108
#define UCDN_SCRIPT_KHUDAWADI 109
#define UCDN_SCRIPT_LINEAR_A 110
#define UCDN_SCRIPT_MAHAJANI 111
#define UCDN_SCRIPT_MANICHAEAN 112
#define UCDN_SCRIPT_MENDE_KIKAKUI 113
#define UCDN_SCRIPT_MODI 114
#define UCDN_SCRIPT_MRO 115
#define UCDN_SCRIPT_NABATAEAN 116
#define UCDN_SCRIPT_OLD_NORTH_ARABIAN 117
#define UCDN_SCRIPT_OLD_PERMIC 118
#define UCDN_SCRIPT_PAHAWH_HMONG 119
#define UCDN_SCRIPT_PALMYRENE 120
#define UCDN_SCRIPT_PAU_CIN_HAU 121
#define UCDN_SCRIPT_PSALTER_PAHLAVI 122
#define UCDN_SCRIPT_SIDDHAM 123
#define UCDN_SCRIPT_TIRHUTA 124
#define UCDN_SCRIPT_WARANG_CITI 125
#define UCDN_SCRIPT_AHOM 126
#define UCDN_SCRIPT_ANATOLIAN_HIEROGLYPHS 127
#define UCDN_SCRIPT_HATRAN 128
#define UCDN_SCRIPT_MULTANI 129
#define UCDN_SCRIPT_OLD_HUNGARIAN 130
#define UCDN_SCRIPT_SIGNWRITING 131
#define UCDN_SCRIPT_ADLAM 132
#define UCDN_SCRIPT_BHAIKSUKI 133
#define UCDN_SCRIPT_MARCHEN 134
#define UCDN_SCRIPT_NEWA 135
#define UCDN_SCRIPT_OSAGE 136
#define UCDN_SCRIPT_TANGUT 137
#define UCDN_SCRIPT_MASARAM_GONDI 138
#define UCDN_SCRIPT_NUSHU 139
#define UCDN_SCRIPT_SOYOMBO 140
#define UCDN_SCRIPT_ZANABAZAR_SQUARE 141
#define UCDN_SCRIPT_DOGRA 142
#define UCDN_SCRIPT_GUNJALA_GONDI 143
#define UCDN_SCRIPT_HANIFI_ROHINGYA 144
#define UCDN_SCRIPT_MAKASAR 145
#define UCDN_SCRIPT_MEDEFAIDRIN 146
#define UCDN_SCRIPT_OLD_SOGDIAN 147
#define UCDN_SCRIPT_SOGDIAN 148
#define UCDN_SCRIPT_ELYMAIC 149
#define UCDN_SCRIPT_NANDINAGARI 150
#define UCDN_SCRIPT_NYIAKENG_PUACHUE_HMONG 151
#define UCDN_SCRIPT_WANCHO 152

%}

%{
// Global Constants - Python dictionary keys
PyObject *dictkey_align;
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
PyObject *dictkey_da;
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
PyObject *dictkey_number;
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
