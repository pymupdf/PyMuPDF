%{
//-----------------------------------------------------------------------------
// Functions dealing with PDF form fields
//-----------------------------------------------------------------------------

// retrieve field value of PushButton
//-----------------------------------------------------------------------------
PyObject *JM_pushbtn_state(fz_context *ctx, pdf_annot *annot)
{   // pushed buttons do not reflect status changes in the PDF
    // always reflect them as untouched
    Py_RETURN_FALSE;
}

// retrieve field value of CheckBox
//-----------------------------------------------------------------------------
PyObject *JM_checkbox_state(fz_context *ctx, pdf_annot *annot)
{
    pdf_document *pdf = pdf_get_bound_document(ctx, annot->obj);
    pdf_obj *leafv  = pdf_get_inheritable(ctx, pdf, annot->obj, PDF_NAME_V);
    pdf_obj *leafas = pdf_get_inheritable(ctx, pdf, annot->obj, PDF_NAME_AS);
    if (!leafv) Py_RETURN_FALSE;
    if (leafv  == PDF_NAME_Off) Py_RETURN_FALSE;
    if (leafas && leafas == PDF_NAME_Off) Py_RETURN_FALSE;
    Py_RETURN_TRUE;
}

// retrieve field value of RadioBox
//-----------------------------------------------------------------------------
PyObject *JM_radiobtn_state(fz_context *ctx, pdf_annot *annot)
{   // MuPDF treats radio buttons like check boxes - hence so do we
    return JM_checkbox_state(ctx, annot);
}

// retrieve value of Text fields
//-----------------------------------------------------------------------------
PyObject *JM_text_value(fz_context *ctx, pdf_annot *annot)
{
    char *text = NULL;
    pdf_document *pdf = pdf_get_bound_document(ctx, annot->obj);
    fz_var(text);
    fz_try(ctx)
        text = pdf_field_value(ctx, pdf, annot->obj);
    fz_catch(ctx) return NONE;
    if (text) return JM_UNICODE(text, strlen(text));
    return NONE;
}

// retrieve value of ListBox fields
//-----------------------------------------------------------------------------
PyObject *JM_listbox_value(fz_context *ctx, pdf_annot *annot)
{
    int i = 0, n = 0;
    // may be single value or array
    pdf_obj *optarr = pdf_dict_get(ctx, annot->obj, PDF_NAME_V);
    if (pdf_is_string(ctx, optarr))         // a single string
        return PyString_FromString(pdf_to_utf8(ctx, optarr));

    n = pdf_array_len(ctx, optarr);
    PyObject *liste = PyList_New(0);

    // extract a list of strings
    // each entry may again be an array: take second entry then
    for (i = 0; i < n; i++)
    {
        pdf_obj *elem = pdf_array_get(ctx, optarr, i);
        if (pdf_is_array(ctx, elem))
            elem = pdf_array_get(ctx, elem, 1);
        PyList_Append(liste, PyString_FromString(pdf_to_utf8(ctx, elem)));
    }
    return liste;
}

// retrieve value of ComboBox fields
//-----------------------------------------------------------------------------
PyObject *JM_combobox_value(fz_context *ctx, pdf_annot *annot)
{   // combobox values are treated like listbox values
    return JM_listbox_value(ctx, annot);
}

// retrieve value of Signature fields
PyObject *JM_signature_value(fz_context *ctx, pdf_annot *annot)
{   // signatures are currently not supported
    return NONE;
}

// retrieve valid ListBox / ComboBox values
//-----------------------------------------------------------------------------
PyObject *JM_choice_options(fz_context *ctx, pdf_annot *annot)
{   // return list of choices for list or combo boxes
    pdf_document *pdf = pdf_get_bound_document(ctx, annot->obj);
    int n = pdf_choice_widget_options(ctx, pdf, (pdf_widget *) annot, 0, NULL);
    if (n == 0) return NONE;                     // wrong widget type

    pdf_obj *optarr = pdf_dict_get(ctx, annot->obj, PDF_NAME_Opt);
    int i, m;
    PyObject *liste = PyList_New(0);

    for (i = 0; i < n; i++)
    {
        m = pdf_array_len(ctx, pdf_array_get(ctx, optarr, i));
        if (m == 2)
        {
            PyList_Append(liste, Py_BuildValue("ss",
            pdf_to_utf8(ctx, pdf_array_get(ctx, pdf_array_get(ctx, optarr, i), 0)),
            pdf_to_utf8(ctx, pdf_array_get(ctx, pdf_array_get(ctx, optarr, i), 1))));
        }
        else
        {
            PyList_Append(liste, PyString_FromString(pdf_to_utf8(ctx, pdf_array_get(ctx, optarr, i))));
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
        opt = JM_Python_str_AsChar(PySequence_GetItem(liste, i));
        pdf_array_push_text_string(ctx, optarr, (const char *) opt);
        JM_Python_str_DelForPy3(opt);
    }

    pdf_dict_put(ctx, annot->obj, PDF_NAME_Opt, optarr);

    return;
}

%}

%pythoncode %{
#------------------------------------------------------------------------------
# Class describing a PDF form field ("widget")
#------------------------------------------------------------------------------
Widget_fontobjects = """<</CoBI <</Type/Font/Subtype/Type1/BaseFont/Courier-BoldOblique/Encoding/WinAnsiEncoding>>\n/CoBo <</Type/Font/Subtype/Type1/BaseFont/Courier-Bold/Encoding/WinAnsiEncoding>>\n/CoIt <</Type/Font/Subtype/Type1/BaseFont/Courier-Oblique/Encoding/WinAnsiEncoding>>\n/Cour <</Type/Font/Subtype/Type1/BaseFont/Courier/Encoding/WinAnsiEncoding>>\n/HeBI <</Type/Font/Subtype/Type1/BaseFont/Helvetica-BoldOblique/Encoding/WinAnsiEncoding>>\n/HeBo <</Type/Font/Subtype/Type1/BaseFont/Helvetica-Bold/Encoding/WinAnsiEncoding>>\n/HeIt <</Type/Font/Subtype/Type1/BaseFont/Helvetica-Oblique/Encoding/WinAnsiEncoding>>\n/Helv <</Type/Font/Subtype/Type1/BaseFont/Helvetica/Encoding/WinAnsiEncoding>>\n/Symb <</Type/Font/Subtype/Type1/BaseFont/Symbol/Encoding/WinAnsiEncoding>>\n/TiBI <</Type/Font/Subtype/Type1/BaseFont/Times-BoldItalic/Encoding/WinAnsiEncoding>>\n/TiBo <</Type/Font/Subtype/Type1/BaseFont/Times-Bold/Encoding/WinAnsiEncoding>>\n/TiIt <</Type/Font/Subtype/Type1/BaseFont/Times-Italic/Encoding/WinAnsiEncoding>>\n/TiRo <</Type/Font/Subtype/Type1/BaseFont/Times-Roman/Encoding/WinAnsiEncoding>>\n/ZaDb <</Type/Font/Subtype/Type1/BaseFont/ZapfDingbats/Encoding/WinAnsiEncoding>>>>"""

def _Widget_fontdict():
    flist = Widget_fontobjects[2:-2].splitlines()
    fdict = {}
    for f in flist:
        k, v = f.split(" ")
        fdict[k[1:]] = v
    return fdict

Widget_fontdict = _Widget_fontdict()

class Widget():
    def __init__(self):
        self.border_color       = None
        self.border_style       = "s"
        self.border_width       = 0
        self.list_values        = None           # choice fields
        self.field_name         = None           # field name
        self.field_value        = None
        self.field_flags        = None
        self.fill_color         = None
        self.button_caption     = None           # button caption
        self.rect               = None           # annot value
        self.text_color         = None           # text fields only
        self.text_font          = "Helv"
        self.text_fontsize      = None           # text fields only
        self.text_maxlen        = 0              # text fields only
        self.text_type          = 0              # text fields only
        self.text_da            = None           # /DA = default apparance
        self.field_type         = 3              # valid range 0 through 6
        self.field_type_string  = None           # field type as string
        self._dr_xref           = 0              # xref of /DR entry
    
    def _validate(self):
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
        if not self.border_width:
            self.border_width = 0

        if not self.text_color:
            self.text_color = (0, 0, 0)
        if not len(self.fill_color) == 3 or \
            type(self.fill_color) not in (list, tuple):
            raise ValueError("text_color must be 3 floats")

        if not self.text_fontsize:
            self.text_fontsize = 0

        bs = self.border_style
        if not bs:
            bs = "Solid"
        else:
            bs = bs.title()
            if bs[0] == "S":
                bs = "Solid"
            elif bs[0] == "B":
                bs = "Beveled"
            elif bs[0] == "D":
                bs = "Dashed"
            elif bs[0] == "U":
                bs = "Underline"
            elif bs[0] == "I":
                bs = "Inset"
            else:
                bs = "Solid"
        self.boder_style = bs

        checker[self.field_type]()

    def _adjust_font(self):
        fnames = [k for k in Widget_fontdict.keys()]
        fl = list(map(str.lower, fnames))
        if (not self.text_font) or self.text_font.lower() not in fl:
            self.text_font = "helv"
        i = fl.index(self.text_font.lower())
        self.text_font = fnames[i]
        return

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
        if type(self.list_values) not in (tuple, list):
            raise ValueError("field type requires a value list")
        if len(self.list_values) < 2:
            raise ValueError("too few values in list")
        return

    def _check5(self):
        if type(self.list_values) not in (tuple, list):
            raise ValueError("field type requires a value list")
        if len(self.list_values) < 2:
            raise ValueError("too few values in list")
        return

%}