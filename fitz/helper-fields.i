%{
#define SETATTR(a, v) PyObject_SetAttrString(Widget, a, v)
#define GETATTR(a) PyObject_GetAttrString(Widget, a)
#define CALLATTR(m, p) PyObject_CallMethod(Widget, m, p)
//-----------------------------------------------------------------------------
// Functions dealing with PDF form fields (widgets)
//-----------------------------------------------------------------------------
enum
{
	SigFlag_SignaturesExist = 1,
	SigFlag_AppendOnly = 2
};


// String from widget type
//-----------------------------------------------------------------------------
char *JM_field_type_text(int wtype)
{
    switch(wtype)
    {
        case(PDF_WIDGET_TYPE_BUTTON):
            return "Button";
        case(PDF_WIDGET_TYPE_CHECKBOX):
            return "CheckBox";
        case(PDF_WIDGET_TYPE_RADIOBUTTON):
            return "RadioButton";
        case(PDF_WIDGET_TYPE_TEXT):
            return "Text";
        case(PDF_WIDGET_TYPE_LISTBOX):
            return "ListBox";
        case(PDF_WIDGET_TYPE_COMBOBOX):
            return "ComboBox";
        case(PDF_WIDGET_TYPE_SIGNATURE):
            return "Signature";
        default:
            return "unknown";
    }
}

// Set the field type
//-----------------------------------------------------------------------------
void JM_set_field_type(fz_context *ctx, pdf_document *doc, pdf_obj *obj, int type)
{
	int setbits = 0;
	int clearbits = 0;
	pdf_obj *typename = NULL;

	switch(type)
	{
	case PDF_WIDGET_TYPE_BUTTON:
		typename = PDF_NAME(Btn);
		setbits = PDF_BTN_FIELD_IS_PUSHBUTTON;
		break;
	case PDF_WIDGET_TYPE_CHECKBOX:
		typename = PDF_NAME(Btn);
		clearbits = PDF_BTN_FIELD_IS_PUSHBUTTON;
		setbits = PDF_BTN_FIELD_IS_RADIO;
		break;
	case PDF_WIDGET_TYPE_RADIOBUTTON:
		typename = PDF_NAME(Btn);
		clearbits = (PDF_BTN_FIELD_IS_PUSHBUTTON|PDF_BTN_FIELD_IS_RADIO);
		break;
	case PDF_WIDGET_TYPE_TEXT:
		typename = PDF_NAME(Tx);
		break;
	case PDF_WIDGET_TYPE_LISTBOX:
		typename = PDF_NAME(Ch);
		clearbits = PDF_CH_FIELD_IS_COMBO;
		break;
	case PDF_WIDGET_TYPE_COMBOBOX:
		typename = PDF_NAME(Ch);
		setbits = PDF_CH_FIELD_IS_COMBO;
		break;
	case PDF_WIDGET_TYPE_SIGNATURE:
		typename = PDF_NAME(Sig);
		break;
	}

	if (typename)
		pdf_dict_put_drop(ctx, obj, PDF_NAME(FT), typename);

	if (setbits != 0 || clearbits != 0)
	{
		int bits = pdf_dict_get_int(ctx, obj, PDF_NAME(Ff));
		bits &= ~clearbits;
		bits |= setbits;
		pdf_dict_put_int(ctx, obj, PDF_NAME(Ff), bits);
	}
}

// Copied from MuPDF v1.14
// Create widget
//-----------------------------------------------------------------------------
pdf_widget *JM_create_widget(fz_context *ctx, pdf_document *doc, pdf_page *page, int type, char *fieldname)
{
	pdf_obj *form = NULL;
	int old_sigflags = pdf_to_int(ctx, pdf_dict_getp(ctx, pdf_trailer(ctx, doc), "Root/AcroForm/SigFlags"));
	pdf_annot *annot = pdf_create_annot_raw(ctx, page, PDF_ANNOT_WIDGET);

	fz_try(ctx)
	{
		JM_set_field_type(ctx, doc, annot->obj, type);
		pdf_dict_put_text_string(ctx, annot->obj, PDF_NAME(T), fieldname);

		if (type == PDF_WIDGET_TYPE_SIGNATURE)
		{
			int sigflags = (old_sigflags | (SigFlag_SignaturesExist|SigFlag_AppendOnly));
			pdf_dict_putl_drop(ctx, pdf_trailer(ctx, doc), pdf_new_int(ctx, sigflags), PDF_NAME(Root), PDF_NAME(AcroForm), PDF_NAME(SigFlags), NULL);
		}

		/*
		pdf_create_annot will have linked the new widget into the page's
		annot array. We also need it linked into the document's form
		*/
		form = pdf_dict_getp(ctx, pdf_trailer(ctx, doc), "Root/AcroForm/Fields");
		if (!form)
		{
			form = pdf_new_array(ctx, doc, 1);
			pdf_dict_putl_drop(ctx, pdf_trailer(ctx, doc),
                               form,
                               PDF_NAME(Root),
                               PDF_NAME(AcroForm),
                               PDF_NAME(Fields),
                               NULL);
		}

		pdf_array_push(ctx, form, annot->obj); /* Cleanup relies on this statement being last */
	}
	fz_catch(ctx)
	{
		pdf_delete_annot(ctx, page, annot);

		/* An empty Fields array may have been created, but that is harmless */

		if (type == PDF_WIDGET_TYPE_SIGNATURE)
			pdf_dict_putl_drop(ctx, pdf_trailer(ctx, doc), pdf_new_int(ctx, old_sigflags), PDF_NAME(Root), PDF_NAME(AcroForm), PDF_NAME(SigFlags), NULL);

		fz_rethrow(ctx);
	}

	return (pdf_widget *)annot;
}


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
    const char *text = NULL;
    fz_var(text);
    fz_try(ctx)
        text = pdf_field_value(ctx, annot->obj);
    fz_catch(ctx) Py_RETURN_NONE;
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
    Py_RETURN_NONE;
}

// retrieve ListBox / ComboBox choice values
//-----------------------------------------------------------------------------
PyObject *JM_choice_options(fz_context *ctx, pdf_annot *annot)
{   // return list of choices for list or combo boxes
    pdf_document *pdf = pdf_get_bound_document(ctx, annot->obj);
    int n = pdf_choice_widget_options(ctx, pdf, (pdf_widget *) annot, 0, NULL);
    if (n == 0) Py_RETURN_NONE;                     // wrong widget type

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
// Populate a Python Widget object with the values from a PDF form field.
// Called by "Page.firstWidget" and "Widget.next".
//-----------------------------------------------------------------------------
void JM_get_widget_properties(fz_context *ctx, pdf_annot *annot, PyObject *Widget)
{
    pdf_document *pdf = annot->page->doc;
    pdf_widget *tw = (pdf_widget *) annot;
    pdf_obj *obj = NULL;
    Py_ssize_t i = 0, n = 0;
    fz_try(ctx)
    {
        int field_type = pdf_widget_type(gctx, tw);
        //JM_TRACE("trace 01");
        SETATTR("field_type", Py_BuildValue("i", field_type));
        //JM_TRACE("trace 02");
        if (field_type == PDF_WIDGET_TYPE_SIGNATURE)
        {
            if (pdf_signature_is_signed(ctx, pdf, annot->obj))
            {
                SETATTR("is_signed", Py_True);
            }
            else
            {
                SETATTR("is_signed", Py_False);
            }
        }
        else
        {
            SETATTR("is_signed", Py_None);
            //JM_TRACE("trace 03");
        }
        SETATTR("border_style",
                Py_BuildValue("s", pdf_field_border_style(ctx, annot->obj)));
        //JM_TRACE("trace 04");
        SETATTR("field_type_string",
                Py_BuildValue("s", JM_field_type_text(field_type)));
        //JM_TRACE("trace 05");
        char *field_name = pdf_field_name(ctx, annot->obj);
        SETATTR("field_name",
                Py_BuildValue("s", field_name));
        JM_Free(field_name);
        //JM_TRACE("trace 06");

        const char *label = NULL;
        obj = pdf_dict_get(ctx, annot->obj, PDF_NAME(TU));
        if (obj) label = pdf_to_text_string(ctx, obj);
        SETATTR("field_label", Py_BuildValue("s", label));

        //JM_TRACE("trace 07");
        SETATTR("field_value",
                Py_BuildValue("s", pdf_field_value(ctx, annot->obj)));
        //JM_TRACE("trace 08");
        SETATTR("field_display",
                Py_BuildValue("i", pdf_field_display(ctx, annot->obj)));
        //JM_TRACE("trace 09");
        float border_width = pdf_to_real(ctx, pdf_dict_getl(ctx, annot->obj,
                                PDF_NAME(BS), PDF_NAME(W), NULL));
        if (border_width == 0.0f) border_width = 1.0f;
        SETATTR("border_width",
                Py_BuildValue("f", border_width));
        //JM_TRACE("trace 10");
        obj = pdf_dict_getl(ctx, annot->obj,
                                PDF_NAME(BS), PDF_NAME(D), NULL);
        if (pdf_is_array(ctx, obj))
        {
            n = (Py_ssize_t) pdf_array_len(ctx, obj);
            PyObject *d = PyList_New(n);
            for (i = 0; i < n; i++)
                PyList_SetItem(d, i, Py_BuildValue("i", pdf_to_int(ctx,
                                pdf_array_get(ctx, obj, (int) i))));

            SETATTR("border_dashes", d);
            Py_CLEAR(d);
        }
        //JM_TRACE("trace 11");
        SETATTR("text_maxlen",
                Py_BuildValue("i", pdf_text_widget_max_len(ctx, pdf, tw)));
        //JM_TRACE("trace 12");
        SETATTR("text_format",
                Py_BuildValue("i", pdf_text_widget_format(ctx, pdf, tw)));
        //JM_TRACE("trace 13");
        obj = pdf_dict_getl(ctx, annot->obj,
                                        PDF_NAME(MK), PDF_NAME(BG), NULL);
        if (pdf_is_array(ctx, obj))
        {
            n = (Py_ssize_t) pdf_array_len(ctx, obj);
            PyObject *col = PyList_New(n);
            for (i = 0; i < n; i++)
                PyList_SetItem(col, i, Py_BuildValue("f",
                pdf_to_real(ctx, pdf_array_get(ctx, obj, (int) i))));

            SETATTR("fill_color", col);
            Py_CLEAR(col);
        }
        //JM_TRACE("trace 14");
        obj = pdf_dict_getl(ctx, annot->obj, PDF_NAME(MK), PDF_NAME(BC), NULL);

        if (pdf_is_array(ctx, obj))
        {
            n = (Py_ssize_t) pdf_array_len(ctx, obj);
            PyObject *col = PyList_New(n);
            for (i = 0; i < n; i++)
                PyList_SetItem(col, i, Py_BuildValue("f",
                pdf_to_real(ctx, pdf_array_get(ctx, obj, (int) i))));

            SETATTR("border_color", col);
            Py_CLEAR(col);
        }
        //JM_TRACE("trace 15");
        SETATTR("choice_values", JM_choice_options(ctx, annot));
        //JM_TRACE("trace 16");
        char *da = pdf_to_str_buf(ctx, pdf_dict_get_inheritable(ctx,
                                        annot->obj, PDF_NAME(DA)));
        SETATTR("_text_da", Py_BuildValue("s", da));
        //JM_TRACE("trace 16");
        obj = pdf_dict_getl(ctx, annot->obj,
                                    PDF_NAME(MK), PDF_NAME(CA), NULL);
        if (obj)
            SETATTR("button_caption",
                    JM_UNICODE(pdf_to_str_buf(ctx, obj)));
        //JM_TRACE("trace 17");
        SETATTR("field_flags",
                Py_BuildValue("i", pdf_field_flags(ctx, annot->obj)));
        //JM_TRACE("trace 18");
        // call Py method to reconstruct text color, font name, size
        PyObject *call = CALLATTR("_parse_da", NULL);
        Py_XDECREF(call);
        //JM_TRACE("trace 19");
    }
    fz_always(ctx) PyErr_Clear();
    fz_catch(ctx) fz_rethrow(ctx);
    return;
}


//-----------------------------------------------------------------------------
// Update a PDF form field with the properties from a Python Widget object.
// Called by "Page.addWidget" and "Annot.updateWidget".
//-----------------------------------------------------------------------------
void JM_set_widget_properties(fz_context *ctx, pdf_annot *annot, PyObject *Widget)
{
    pdf_document *pdf = annot->page->doc;
    pdf_page *page = annot->page;
    fz_rect rect;
    pdf_obj *fill_col = NULL, *border_col = NULL;
    pdf_obj *dashes = NULL;
    Py_ssize_t i, n = 0;
    int d;
    int field_type = (int) PyInt_AsLong(GETATTR("field_type"));
    PyObject *value;

    // rectangle --------------------------------------------------------------
    value = GETATTR("rect");
    rect = JM_rect_from_py(value);
    Py_CLEAR(value);
    pdf_set_annot_rect(ctx, annot, rect);    // set the rect

    // fill color -------------------------------------------------------------
    value = GETATTR("fill_color");
    if (value && PySequence_Check(value))
    {
        n = PySequence_Size(value);
        fill_col = pdf_new_array(ctx, pdf, n);
        for (i = 0; i < n; i++)
            pdf_array_push_real(ctx, fill_col,
                                PyFloat_AsDouble(PySequence_ITEM(value, i)));
        pdf_field_set_fill_color(ctx, annot->obj, fill_col);
        pdf_drop_obj(ctx, fill_col);
    }
    Py_CLEAR(value);

    // dashes -----------------------------------------------------------------
    value = GETATTR("border_dashes");
    if (value && PySequence_Check(value))
    {
        n = PySequence_Size(value);
        dashes = pdf_new_array(ctx, pdf, n);
        for (i = 0; i < n; i++)
            pdf_array_push_int(ctx, dashes,
                                    PyInt_AsLong(PySequence_ITEM(value, i)));
        pdf_dict_putl_drop(ctx, annot->obj, dashes,
                                PDF_NAME(BS),
                                PDF_NAME(D),
                                NULL);
    }
    Py_CLEAR(value);

    // border color -----------------------------------------------------------
    value = GETATTR("border_color");
    if (value && PySequence_Check(value))
    {
        n = PySequence_Size(value);
        border_col = pdf_new_array(ctx, pdf, n);
        for (i = 0; i < n; i++)
            pdf_array_push_real(ctx, border_col,
                                PyFloat_AsDouble(PySequence_ITEM(value, i)));
        pdf_dict_putl_drop(ctx, annot->obj, border_col,
                                PDF_NAME(MK),
                                PDF_NAME(BC),
                                NULL);
    }
    Py_CLEAR(value);

    // entry ignored - may be used later
    /*
    int text_format = (int) PyInt_AsLong(GETATTR("text_format"));
    */

    // field label -----------------------------------------------------------
    value = GETATTR("field_label");
    if (value != Py_None)
    {
        char *label = JM_Python_str_AsChar(value);
        pdf_dict_put_text_string(ctx, annot->obj, PDF_NAME(TU), label);
        JM_Python_str_DelForPy3(label);
    }
    Py_CLEAR(value);

    // max text len -----------------------------------------------------------
    if (field_type == PDF_WIDGET_TYPE_TEXT)
    {
        int text_maxlen = (int) PyInt_AsLong(GETATTR("text_maxlen"));
        if (text_maxlen)
            pdf_dict_put_int(ctx, annot->obj, PDF_NAME(MaxLen), text_maxlen);
    }
    d = (int) PyInt_AsLong(GETATTR("field_display"));
    pdf_field_set_display(ctx, annot->obj, d);

    // choice values ----------------------------------------------------------
    if (field_type == PDF_WIDGET_TYPE_LISTBOX ||
        field_type == PDF_WIDGET_TYPE_COMBOBOX)
    {
        value = GETATTR("choice_values");
        JM_set_choice_options(ctx, annot, value);
        Py_CLEAR(value);
    }

    // border style -----------------------------------------------------------
    pdf_obj *val = JM_get_border_style(ctx,
                                GETATTR("border_style"));
    pdf_dict_putl_drop(ctx, annot->obj, val,
                            PDF_NAME(BS),
                            PDF_NAME(S),
                            NULL);

    // border width -----------------------------------------------------------
    float border_width = (float) PyFloat_AsDouble(GETATTR("border_width"));
    pdf_dict_putl_drop(ctx, annot->obj, pdf_new_real(ctx, border_width),
                            PDF_NAME(BS),
                            PDF_NAME(W),
                            NULL);

    // /DA string -------------------------------------------------------------
    char *da = JM_Python_str_AsChar(GETATTR("_text_da"));
    pdf_dict_put_text_string(ctx, annot->obj, PDF_NAME(DA), da);
    JM_Python_str_DelForPy3(da);
    pdf_dict_del(ctx, annot->obj, PDF_NAME(DS)); /* not supported */
    pdf_dict_del(ctx, annot->obj, PDF_NAME(RC)); /* not supported */

    // field flags ------------------------------------------------------------
    int field_flags = 0, Ff = 0;
    if (field_type != PDF_WIDGET_TYPE_CHECKBOX)
    {
        field_flags = (int) PyInt_AsLong(GETATTR("field_flags"));
        if (!PyErr_Occurred())
        {
            Ff = pdf_field_flags(ctx, annot->obj);
            Ff |= field_flags;
        }
    }
    pdf_dict_put_int(ctx, annot->obj, PDF_NAME(Ff), Ff);

    // button caption ---------------------------------------------------------
    char *ca = JM_Python_str_AsChar(GETATTR("button_caption"));
    if (ca)
    {
        pdf_field_set_button_caption(ctx, annot->obj, ca);
        JM_Python_str_DelForPy3(ca);
    }

    // field value ------------------------------------------------------------
    // MuPDF function "pdf_set_field_value" always sets strings. For button
    // fields this may lead to an unrecognized state for some PDF viewers.
    //-------------------------------------------------------------------------
    value = GETATTR("field_value");
    int result = 0;
    char *text = NULL;
    switch(field_type)
    {
    case PDF_WIDGET_TYPE_CHECKBOX:
    case PDF_WIDGET_TYPE_RADIOBUTTON:
        if (PyObject_RichCompareBool(value, Py_True, Py_EQ))
        {
            result = pdf_set_field_value(ctx, pdf, annot->obj, "Yes", 1);
            pdf_dict_put_name(ctx, annot->obj, PDF_NAME(V), "Yes");
        }
        else
        {
            result = pdf_set_field_value(ctx, pdf, annot->obj, "Off", 1);
            pdf_dict_put(ctx, annot->obj, PDF_NAME(V), PDF_NAME(Off));
        }
        break;
    default:
        text = JM_Python_str_AsChar(value);
        if (text)
        {
            result = pdf_set_field_value(ctx, pdf, annot->obj, (const char *)text, 1);
            JM_Python_str_DelForPy3(text);
        }
    }
    Py_CLEAR(value);
    PyErr_Clear();
    pdf_dirty_annot(ctx, annot);
    annot->is_hot = 1;
    annot->is_active = 1;
    pdf_update_appearance(ctx, annot);
    pdf_update_page(ctx, page);
}
#undef SETATTR
#undef GETATTR
#undef CALLATTR
%}

%pythoncode %{
#------------------------------------------------------------------------------
# Class describing a PDF form field ("widget")
#------------------------------------------------------------------------------
class Widget(object):
    def __init__(self):
        self.border_color       = None
        self.border_style       = "S"
        self.border_width       = 0
        self.border_dashes      = None
        self.choice_values      = None           # choice fields only
        self.field_name         = None           # field name
        self.field_label        = None           # field label
        self.field_value        = None
        self.field_flags        = None
        self.field_display      = 0
        self.fill_color         = None
        self.button_caption     = None           # button caption
        self.rect               = None           # annot value
        self.is_signed          = None           # True / False if signature
        self.text_color         = (0, 0, 0)
        self.text_font          = "Helv"
        self.text_fontsize      = 0
        self.text_maxlen        = 0              # text fields only
        self.text_format        = 0              # text fields only
        self._text_da           = ""             # /DA = default apparance
        self.field_type         = 0              # valid range 1 through 7
        self.field_type_string  = None           # field type as string
        self._text_da           = ""             # /DA = default apparance
        self.xref               = 0              # annot value


    def _validate(self):
        """Validate the class entries.
        """
        if (self.rect.isInfinite
            or self.rect.isEmpty
           ):
            raise ValueError("bad rect")

        if not self.field_name:
            raise ValueError("field name missing")

        if self.field_label == "Unnamed":
            self.field_label = None
        CheckColor(self.border_color)
        CheckColor(self.fill_color)
        if not self.text_color:
            self.text_color = (0, 0, 0)
        CheckColor(self.text_color)

        if not self.border_width:
            self.border_width = 0

        if not self.text_fontsize:
            self.text_fontsize = 0

        self.border_style = self.border_style.upper()[0:1]

        self._checker()  # any field_type specific checks


    def _adjust_font(self):
        """Ensure text_font is from our list and correctly spelled.
        """
        if not self.text_font:
            self.text_font = "Helv"
            return
        valid_fonts = ("Cour", "TiRo", "Helv", "ZaDb")
        for f in valid_fonts:
            if self.text_font.lower() == f.lower():
                self.text_font = f
                return
        self.text_font = "Helv"
        return


    def _parse_da(self):
        """Extract font name, size and color from default appearance string (/DA object).

        Equivalent to 'pdf_parse_default_appearance' function in MuPDF's 'pdf-annot.c'.
        """
        if not self._text_da:
            return
        font = "Helv"
        fsize = 0
        col = (0, 0, 0)
        dat = self._text_da.split()  # split on any whitespace
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
        self._text_da = ""
        return


    def _checker(self):
        """Any widget type checks.
        """
        if self.field_type not in range(1, 8):
            raise ValueError("bad field type")


    def update(self):
        """Reflect Python object in the PDF.
        """
        self._validate()
        doc = self.parent.parent

        self._adjust_font()  # ensure valid text_font name

        # now create the /DA string
        self._text_da = ""
        if   len(self.text_color) == 3:
            fmt = "{:g} {:g} {:g} rg /{f:s} {s:g} Tf" + self._text_da
        elif len(self.text_color) == 1:
            fmt = "{:g} g /{f:s} {s:g} Tf" + self._text_da
        elif len(self.text_color) == 4:
            fmt = "{:g} {:g} {:g} {:g} k /{f:s} {s:g} Tf" + self._text_da
        self._text_da = fmt.format(*self.text_color, f=self.text_font,
                                    s=self.text_fontsize)
        # finally update the widget

        TOOLS._save_widget(self._annot, self)
        self._text_da = ""


    def __repr__(self):
        return "'%s' widget on %s" % (self.field_type_string, str(self.parent))

    def __del__(self):
        self._annot.__del__()

    @property
    def next(self):
        return self._annot.next
%}
