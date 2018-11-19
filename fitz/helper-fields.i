%{
//-----------------------------------------------------------------------------
// Functions dealing with PDF form fields
//-----------------------------------------------------------------------------

// PushButton get state
//-----------------------------------------------------------------------------
PyObject *JM_pushbtn_state(fz_context *ctx, pdf_annot *annot)
{   // pushed buttons do not reflect status changes in the PDF
    // always reflect them as untouched
    Py_RETURN_FALSE;
}

// CheckBox get state
//-----------------------------------------------------------------------------
PyObject *JM_checkbox_state(fz_context *ctx, pdf_annot *annot)
{
    pdf_obj *leafv  = pdf_dict_get_inheritable(ctx, annot->obj, PDF_NAME(V));
    pdf_obj *leafas = pdf_dict_get_inheritable(ctx, annot->obj, PDF_NAME(AS));
    if (!leafv) Py_RETURN_FALSE;
    if (leafv  == PDF_NAME(Off)) Py_RETURN_FALSE;
    if (leafv == pdf_new_name(ctx, "Yes"))
        Py_RETURN_TRUE;
    if (pdf_is_string(ctx, leafv) && !strcmp(pdf_to_str_buf(ctx, leafv), "Off"))
        Py_RETURN_FALSE;
    if (pdf_is_string(ctx, leafv) && !strcmp(pdf_to_str_buf(ctx, leafv), "Yes"))
        Py_RETURN_TRUE;
    if (leafas && leafas == PDF_NAME(Off)) Py_RETURN_FALSE;
    Py_RETURN_TRUE;
}

// RadioBox get state
//-----------------------------------------------------------------------------
PyObject *JM_radiobtn_state(fz_context *ctx, pdf_annot *annot)
{   // MuPDF treats radio buttons like check boxes - hence so do we
    return JM_checkbox_state(ctx, annot);
}

// Text field retrieve value
//-----------------------------------------------------------------------------
PyObject *JM_text_value(fz_context *ctx, pdf_annot *annot)
{
    char *text = NULL;
    pdf_document *pdf = pdf_get_bound_document(ctx, annot->obj);
    fz_var(text);
    fz_try(ctx)
        text = pdf_field_value(ctx, pdf, annot->obj);
    fz_catch(ctx) return NONE;
    return Py_BuildValue("s", text);
}

// ListBox retrieve value
//-----------------------------------------------------------------------------
PyObject *JM_listbox_value(fz_context *ctx, pdf_annot *annot)
{
    int i = 0, n = 0;
    // may be single value or array
    pdf_obj *optarr = pdf_dict_get(ctx, annot->obj, PDF_NAME(V));
    if (pdf_is_string(ctx, optarr))         // a single string
        return PyString_FromString(pdf_to_text_string(ctx, optarr));

    // value is an array (may have len 0)
    n = pdf_array_len(ctx, optarr);
    PyObject *liste = PyList_New(0);

    // extract a list of strings
    // each entry may again be an array: take second entry then
    for (i = 0; i < n; i++)
    {
        pdf_obj *elem = pdf_array_get(ctx, optarr, i);
        if (pdf_is_array(ctx, elem))
            elem = pdf_array_get(ctx, elem, 1);
        PyList_Append(liste, PyString_FromString(pdf_to_text_string(ctx, elem)));
    }
    return liste;
}

// ComboBox retrieve value
//-----------------------------------------------------------------------------
PyObject *JM_combobox_value(fz_context *ctx, pdf_annot *annot)
{   // combobox values are treated like listbox values
    return JM_listbox_value(ctx, annot);
}

// Signature field retrieve value
PyObject *JM_signature_value(fz_context *ctx, pdf_annot *annot)
{   // signatures are currently not supported
    return NONE;
}

// retrieve ListBox / ComboBox choice values
//-----------------------------------------------------------------------------
PyObject *JM_choice_options(fz_context *ctx, pdf_annot *annot)
{   // return list of choices for list or combo boxes
    pdf_document *pdf = pdf_get_bound_document(ctx, annot->obj);
    int n = pdf_choice_widget_options(ctx, pdf, (pdf_widget *) annot, 0, NULL);
    if (n == 0) return NONE;                     // wrong widget type

    pdf_obj *optarr = pdf_dict_get(ctx, annot->obj, PDF_NAME(Opt));
    int i, m;
    PyObject *liste = PyList_New(0);

    for (i = 0; i < n; i++)
    {
        m = pdf_array_len(ctx, pdf_array_get(ctx, optarr, i));
        if (m == 2)
        {
            PyList_Append(liste, Py_BuildValue("ss",
            pdf_to_text_string(ctx, pdf_array_get(ctx, pdf_array_get(ctx, optarr, i), 0)),
            pdf_to_text_string(ctx, pdf_array_get(ctx, pdf_array_get(ctx, optarr, i), 1))));
        }
        else
        {
            PyList_Append(liste, PyString_FromString(pdf_to_text_string(ctx, pdf_array_get(ctx, optarr, i))));
        }
    }
    return liste;
}

// set ListBox / ComboBox values
//-----------------------------------------------------------------------------
void JM_set_choice_options(fz_context *ctx, pdf_annot *annot, PyObject *liste)
{
    pdf_document *pdf = pdf_get_bound_document(ctx, annot->obj);
    Py_ssize_t i, n = PySequence_Size(liste);
    char *opt = NULL;
    pdf_obj *optarr = pdf_new_array(ctx, pdf, n);
    for (i = 0; i < n; i++)
    {
        opt = JM_Python_str_AsChar(PySequence_ITEM(liste, i));
        pdf_array_push_text_string(ctx, optarr, (const char *) opt);
        JM_Python_str_DelForPy3(opt);
    }

    pdf_dict_put(ctx, annot->obj, PDF_NAME(Opt), optarr);

    return;
}

//-----------------------------------------------------------------------------
// Called by "Page.addWidget" and "Annot.updateWidget".
// Set all properties of a new or updated widget, whether changed or not.
// Should be no performance issue, because verifying a change before updating
// is costly as well (and a code bloat). No problem on the PDF side, because
// any change will always lead to the complete new PDF object being stored.
//-----------------------------------------------------------------------------
void JM_set_widget_properties(fz_context *ctx, pdf_annot *annot, PyObject *Widget, int field_type)
{
    pdf_document *pdf = annot->page->doc;
    pdf_page *page = annot->page;
    fz_rect rect;
    pdf_obj *fill_col = NULL, *text_col = NULL, *border_col = NULL;
    pdf_obj *dashes = NULL;
    Py_ssize_t i, n = 0;
    PyObject *value;

    // ensure a font resources dict /DR --- -----------------------------------
    pdf_obj *dr = pdf_dict_getl(ctx, pdf_trailer(ctx, pdf),
                           PDF_NAME(Root), PDF_NAME(AcroForm), PDF_NAME(DR), NULL);
    // new /DR using the object prepared in xref
    if (!dr)
    {
        pdf_obj *form = pdf_dict_getl(ctx, pdf_trailer(ctx, pdf),
                                        PDF_NAME(Root), PDF_NAME(AcroForm), NULL);
        int xref = (int) PyInt_AsLong(PyObject_GetAttrString(Widget,
                                                                   "_dr_xref"));
        pdf_obj *f = pdf_new_indirect(ctx, pdf, xref, 0);
        dr = pdf_new_dict(ctx, pdf, 1);
        pdf_dict_put(ctx, dr, PDF_NAME(Font), f);
        pdf_dict_put_drop(ctx, form, PDF_NAME(DR), dr);
        JM_PyErr_Clear;
    }

    // rectangle --------------------------------------------------------------
    value = PyObject_GetAttrString(Widget, "rect");
    rect = JM_rect_from_py(value);
    Py_CLEAR(value);
    pdf_set_annot_rect(ctx, annot, rect);    // set the rect

    // fill color -------------------------------------------------------------
    value = PyObject_GetAttrString(Widget, "fill_color");
    if (value && PySequence_Check(value))
    {
        n = PySequence_Size(value);
        fill_col = pdf_new_array(ctx, pdf, n);
        for (i = 0; i < n; i++)
            pdf_array_push_real(ctx, fill_col,
                                PyFloat_AsDouble(PySequence_ITEM(value, i)));
        pdf_field_set_fill_color(ctx, pdf, annot->obj, fill_col);
        pdf_drop_obj(ctx, fill_col);
    }
    Py_CLEAR(value);
    JM_PyErr_Clear;

    // dashes -----------------------------------------------------------------
    value = PyObject_GetAttrString(Widget, "border_dashes");
    if (value && PySequence_Check(value))
    {
        n = PySequence_Size(value);
        dashes = pdf_new_array(ctx, pdf, n);
        for (i = 0; i < n; i++)
            pdf_array_push_int(ctx, dashes,
                                    PyInt_AsLong(PySequence_ITEM(value, i)));
        pdf_dict_putl_drop(ctx, annot->obj, dashes, PDF_NAME(BS),
                                                              PDF_NAME(D), NULL);
    }
    Py_CLEAR(value);
    JM_PyErr_Clear;

    // border color -----------------------------------------------------------
    value = PyObject_GetAttrString(Widget, "border_color");
    if (value && PySequence_Check(value))
    {
        n = PySequence_Size(value);
        border_col = pdf_new_array(ctx, pdf, n);
        for (i = 0; i < n; i++)
            pdf_array_push_real(ctx, border_col,
                                PyFloat_AsDouble(PySequence_ITEM(value, i)));
        pdf_dict_putl_drop(ctx, annot->obj, border_col, PDF_NAME(MK),
                                                             PDF_NAME(BC), NULL);
    }
    Py_CLEAR(value);
    JM_PyErr_Clear;

    // entry ignored - may be later use
    /*
    int text_type = (int) PyInt_AsLong(PyObject_GetAttrString(Widget,
                                                                  "text_type"));
    JM_PyErr_Clear;
    */

    // max text len -----------------------------------------------------------
    if (field_type == PDF_WIDGET_TYPE_TEXT)
    {
        int text_maxlen = (int) PyInt_AsLong(PyObject_GetAttrString(Widget,
                                                               "text_maxlen"));
        if (text_maxlen)
            pdf_dict_put_int(ctx, annot->obj, PDF_NAME(MaxLen), text_maxlen);
        JM_PyErr_Clear;
    }
    
    // choice values ----------------------------------------------------------
    if (field_type == PDF_WIDGET_TYPE_LISTBOX ||
        field_type == PDF_WIDGET_TYPE_COMBOBOX)
    {
        value = PyObject_GetAttrString(Widget, "choice_values");
        JM_set_choice_options(ctx, annot, value);
        Py_CLEAR(value);
    }
    JM_PyErr_Clear;

    // border style -----------------------------------------------------------
    pdf_obj *val = JM_get_border_style(ctx,
                                PyObject_GetAttrString(Widget, "border_style"));
    pdf_dict_putl_drop(ctx, annot->obj, val, PDF_NAME(BS), PDF_NAME(S), NULL);

    // border width -----------------------------------------------------------
    float border_width = (float) PyFloat_AsDouble(PyObject_GetAttrString(Widget,
                                                               "border_width"));
    pdf_dict_putl_drop(ctx, annot->obj, pdf_new_real(ctx, border_width),
                       PDF_NAME(BS), PDF_NAME(W), NULL);
    JM_PyErr_Clear;

    // /DA string -------------------------------------------------------------
    char *da = JM_Python_str_AsChar(PyObject_GetAttrString(Widget, "_text_da"));
    if (da)
    {
        pdf_dict_put_text_string(ctx, annot->obj, PDF_NAME(DA), da);
        JM_Python_str_DelForPy3(da);
        pdf_dict_dels(ctx, annot->obj, "DS");  // unsupported
        pdf_dict_dels(ctx, annot->obj, "RC");  // unsupported
    }
    JM_PyErr_Clear;

    // field flags ------------------------------------------------------------
    int field_flags = 0, Ff = 0;
    if (field_type != PDF_WIDGET_TYPE_CHECKBOX)
    {
        field_flags = (int) PyInt_AsLong(PyObject_GetAttrString(Widget,
                                                                "field_flags"));
        if (!PyErr_Occurred())
        {
            Ff = pdf_get_field_flags(ctx, pdf, annot->obj);
            Ff |= field_flags;
        }
        JM_PyErr_Clear;
    }
    pdf_dict_put_int(ctx, annot->obj, PDF_NAME(Ff), Ff);

    // button caption ---------------------------------------------------------
    if (field_type == PDF_WIDGET_TYPE_RADIOBUTTON ||
        field_type == PDF_WIDGET_TYPE_PUSHBUTTON ||
        field_type == PDF_WIDGET_TYPE_CHECKBOX)
    {
        char *ca = JM_Python_str_AsChar(PyObject_GetAttrString(Widget,
                                                             "button_caption"));
        if (ca)
        {
            pdf_dict_putl(ctx, annot->obj, pdf_new_text_string(ctx, ca),
                          PDF_NAME(MK), PDF_NAME(CA), NULL);
            JM_Python_str_DelForPy3(ca);
        }
        JM_PyErr_Clear;
    }

    // field value ------------------------------------------------------------
    // MuPDF function "pdf_field_set_value" always sets strings. For button
    // fields this may lead to an unrecognized state for some PDF viewers.
    //-------------------------------------------------------------------------
    value = PyObject_GetAttrString(Widget, "field_value");
    int result = 0;
    char *text = NULL;
    switch(field_type)
    {
    case PDF_WIDGET_TYPE_CHECKBOX:
    case PDF_WIDGET_TYPE_RADIOBUTTON:
        if (PyObject_RichCompareBool(value, Py_True, Py_EQ))
        {
            result = pdf_field_set_value(ctx, pdf, annot->obj, "Yes");
            pdf_dict_put_name(ctx, annot->obj, PDF_NAME(V), "Yes");
        }
        else
        {
            result = pdf_field_set_value(ctx, pdf, annot->obj, "Off");
            pdf_dict_put(ctx, annot->obj, PDF_NAME(V), PDF_NAME(Off));
        }
        break;
    default:
        text = JM_Python_str_AsChar(value);
        if (text)
        {
            result = pdf_field_set_value(ctx, pdf, annot->obj, (const char *)text);
            JM_Python_str_DelForPy3(text);
        }
    }
    Py_CLEAR(value);
    pdf_dirty_annot(ctx, annot);
    pdf_update_page(gctx, page);
}

%}

%pythoncode %{
#------------------------------------------------------------------------------
# Font definitions for new PyMuPDF widgets.
# IMPORTANT: do not change anything here! Line breaks are required, as well
# as are the spaces after the font ref names.
#------------------------------------------------------------------------------
Widget_fontobjects = """<</CoBI <</Type/Font/Subtype/Type1/BaseFont/Courier-BoldOblique/Encoding/WinAnsiEncoding>>\n/CoBo <</Type/Font/Subtype/Type1/BaseFont/Courier-Bold/Encoding/WinAnsiEncoding>>\n/CoIt <</Type/Font/Subtype/Type1/BaseFont/Courier-Oblique/Encoding/WinAnsiEncoding>>\n/Cour <</Type/Font/Subtype/Type1/BaseFont/Courier/Encoding/WinAnsiEncoding>>\n/HeBI <</Type/Font/Subtype/Type1/BaseFont/Helvetica-BoldOblique/Encoding/WinAnsiEncoding>>\n/HeBo <</Type/Font/Subtype/Type1/BaseFont/Helvetica-Bold/Encoding/WinAnsiEncoding>>\n/HeIt <</Type/Font/Subtype/Type1/BaseFont/Helvetica-Oblique/Encoding/WinAnsiEncoding>>\n/Helv <</Type/Font/Subtype/Type1/BaseFont/Helvetica/Encoding/WinAnsiEncoding>>\n/Symb <</Type/Font/Subtype/Type1/BaseFont/Symbol/Encoding/WinAnsiEncoding>>\n/TiBI <</Type/Font/Subtype/Type1/BaseFont/Times-BoldItalic/Encoding/WinAnsiEncoding>>\n/TiBo <</Type/Font/Subtype/Type1/BaseFont/Times-Bold/Encoding/WinAnsiEncoding>>\n/TiIt <</Type/Font/Subtype/Type1/BaseFont/Times-Italic/Encoding/WinAnsiEncoding>>\n/TiRo <</Type/Font/Subtype/Type1/BaseFont/Times-Roman/Encoding/WinAnsiEncoding>>\n/ZaDb <</Type/Font/Subtype/Type1/BaseFont/ZapfDingbats/Encoding/WinAnsiEncoding>>>>"""

def _Widget_fontdict():
    """Turns the above font definitions into a dictionary. Assumes certain line breaks and spaces.
    """
    flist = Widget_fontobjects[2:-2].splitlines()
    fdict = {}
    for f in flist:
        k, v = f.split(" ")
        fdict[k[1:]] = v
    return fdict

Widget_fontdict = _Widget_fontdict()   # needed so we can use it as a property

#------------------------------------------------------------------------------
# Class describing a PDF form field ("widget")
#------------------------------------------------------------------------------
class Widget():
    def __init__(self):
        self.border_color       = None
        self.border_style       = "S"
        self.border_width       = 0
        self.border_dashes      = None
        self.choice_values      = None           # choice fields only
        self.field_name         = None           # field name
        self.field_value        = None
        self.field_flags        = None
        self.fill_color         = None
        self.button_caption     = None           # button caption
        self.rect               = None           # annot value
        self.text_color         = (0, 0, 0)
        self.text_font          = "Helv"
        self.text_fontsize      = 0
        self.text_maxlen        = 0              # text fields only
        self.text_type          = 0              # text fields only
        self._text_da           = ""             # /DA = default apparance
        self.field_type         = 3              # valid range 0 through 6
        self.field_type_string  = None           # field type as string
        self._text_da           = ""             # /DA = default apparance
        self._dr_xref           = 0              # xref of /DR entry
    
    def _validate(self):
        """Validate the class entries.
        """
        checker = (self._check0, self._check1, self._check2, self._check3,
                   self._check4, self._check5)
        if not 0 <= self.field_type <= 5:
            raise NotImplementedError("unsupported widget type")
        if type(self.rect) is not Rect:
            raise ValueError("invalid rect")
        if self.rect.isInfinite or self.rect.isEmpty:
            raise ValueError("rect must be finite and not empty")
        if not self.field_name:
            raise ValueError("field name missing")
        
        if self.border_color:
            if not len(self.border_color) in range(1,5) or \
               type(self.border_color) not in (list, tuple):
               raise ValueError("border_color must be 1 - 4 floats")
        
        if self.fill_color:
            if not len(self.fill_color) in range(1,5) or \
               type(self.fill_color) not in (list, tuple):
               raise ValueError("fill_color must be 1 - 4 floats")
        
        if not self.text_color:
            self.text_color = (0, 0, 0)
        if not len(self.text_color) in range(1,5) or \
            type(self.text_color) not in (list, tuple):
            raise ValueError("text_color must be 1 - 4 floats")

        if not self.border_width:
            self.border_width = 0

        if not self.text_fontsize:
            self.text_fontsize = 0

        checker[self.field_type]()

    def _adjust_font(self):
        """Ensure the font name is from our list and correctly spelled.
        """
        fnames = [k for k in Widget_fontdict.keys()]
        fl = list(map(str.lower, fnames))
        if (not self.text_font) or self.text_font.lower() not in fl:
            self.text_font = "helv"
        i = fl.index(self.text_font.lower())
        self.text_font = fnames[i]
        return

    def _parse_da(self):
        """Extract font name, size and color from default appearance string (/DA object). Equivalent to 'pdf_parse_default_appearance' function in MuPDF's 'pdf-annot.c'.
        """
        if not self._text_da:
            return
        font = "Helv"
        fsize = 0
        col = (0, 0, 0)
        dat = self._text_da.split()              # split on any whitespace
        for i, item in enumerate(dat):
            if item == "Tf":
                font = dat[i - 2][1:]
                fsize = float(dat[i - 1])
                dat[i] = dat[i-1] = dat[i-2] = ""
                continue
            if item == "g":            # unicolor text
                col = [(float(dat[i - 1]))]
                dat[i] = dat[i-1] = ""
                continue
            if item == "rg":           # RGB colored text
                col = [float(f) for f in dat[i - 3:i]]
                dat[i] = dat[i-1] = dat[i-2] = dat[i-3] = ""
                continue
        self.text_font     = font
        self.text_fontsize = fsize
        self.text_color    = col
        self._text_da = " ".join([c for c in dat if c != ""])
        return

    # any widget type specific checks
    def _check0(self):
        return
    
    def _check1(self):
        return

    def _check2(self):
        return

    def _check3(self):
        if not 0 <= self.text_type <= 4:
            raise ValueError("text subtype not in range 0 - 4")
        return

    def _check4(self):
        if type(self.choice_values) not in (tuple, list):
            raise ValueError("field type requires a value list")
        if len(self.choice_values) < 2:
            raise ValueError("too few choice values")
        return

    def _check5(self):
        if type(self.choice_values) not in (tuple, list):
            raise ValueError("field type requires a value list")
        if len(self.choice_values) < 2:
            raise ValueError("too few choice values")
        return

%}