%{
/*
# ------------------------------------------------------------------------
# Copyright 2020-2022, Harald Lieder, mailto:harald.lieder@outlook.com
# License: GNU AFFERO GPL 3.0, https://www.gnu.org/licenses/agpl-3.0.html
#
# Part of "PyMuPDF", a Python binding for "MuPDF" (http://mupdf.com), a
# lightweight PDF, XPS, and E-book viewer, renderer and toolkit which is
# maintained and developed by Artifex Software, Inc. https://artifex.com.
# ------------------------------------------------------------------------
*/
#define SETATTR(a, v) PyObject_SetAttrString(Widget, a, v)
#define GETATTR(a) PyObject_GetAttrString(Widget, a)
#define CALLATTR(m, p) PyObject_CallMethod(Widget, m, p)

static void
SETATTR_DROP(PyObject *mod, const char *attr, PyObject *value)
{
    if (!value)
        PyObject_DelAttrString(mod, attr);
    else
    {
        PyObject_SetAttrString(mod, attr, value);
        Py_DECREF(value);
    }
}

//-----------------------------------------------------------------------------
// Functions dealing with PDF form fields (widgets)
//-----------------------------------------------------------------------------
enum
{
	SigFlag_SignaturesExist = 1,
	SigFlag_AppendOnly = 2
};


// make new PDF action object from JavaScript source
// Parameters are a PDF document and a Python string.
// Returns a PDF action object.
//-----------------------------------------------------------------------------
pdf_obj *
JM_new_javascript(fz_context *ctx, pdf_document *pdf, PyObject *value)
{
    fz_buffer *res = NULL;
    if (!PyObject_IsTrue(value))  // no argument given
        return NULL;

    char *data = JM_StrAsChar(value);
    if (!data)  // not convertible to char*
        return NULL;

    res = fz_new_buffer_from_copied_data(ctx, data, strlen(data));
    pdf_obj *source = pdf_add_stream(ctx, pdf, res, NULL, 0);
    pdf_obj *newaction = pdf_add_new_dict(ctx, pdf, 4);
    pdf_dict_put(ctx, newaction, PDF_NAME(S), pdf_new_name(ctx, "JavaScript"));
    pdf_dict_put(ctx, newaction, PDF_NAME(JS), source);
    fz_drop_buffer(ctx, res);
    return pdf_keep_obj(ctx, newaction);
}


// JavaScript extractor
// Returns either the script source or None. Parameter is a PDF action
// dictionary, which must have keys /S and /JS. The value of /S must be
// '/JavaScript'. The value of /JS is returned.
//-----------------------------------------------------------------------------
PyObject *
JM_get_script(fz_context *ctx, pdf_obj *key)
{
    pdf_obj *js = NULL;
    fz_buffer *res = NULL;
    PyObject *script = NULL;
    if (!key) Py_RETURN_NONE;

    if (!strcmp(pdf_to_name(ctx,
                pdf_dict_get(ctx, key, PDF_NAME(S))), "JavaScript")) {
        js = pdf_dict_get(ctx, key, PDF_NAME(JS));
    }
    if (!js) Py_RETURN_NONE;

    if (pdf_is_string(ctx, js)) {
        script = JM_UnicodeFromStr(pdf_to_text_string(ctx, js));
    } else if (pdf_is_stream(ctx, js)) {
        res = pdf_load_stream(ctx, js);
        script = JM_EscapeStrFromBuffer(ctx, res);
        fz_drop_buffer(ctx, res);
    } else {
        Py_RETURN_NONE;
    }
    if (PyObject_IsTrue(script)) { // do not return an empty script
        return script;
    }
    Py_CLEAR(script);
    Py_RETURN_NONE;
}


// Create a JavaScript PDF action.
// Usable for all object types which support PDF actions, even if the
// argument name suggests annotations. Up to 2 key values can be specified, so
// JavaScript actions can be stored for '/A' and '/AA/?' keys.
//-----------------------------------------------------------------------------
void JM_put_script(fz_context *ctx, pdf_obj *annot_obj, pdf_obj *key1, pdf_obj *key2, PyObject *value)
{
    PyObject *script = NULL;
    pdf_obj *key1_obj = pdf_dict_get(ctx, annot_obj, key1);
    pdf_document *pdf = pdf_get_bound_document(ctx, annot_obj);  // owning PDF

    // if no new script given, just delete corresponding key
    if (!value || !PyObject_IsTrue(value)) {
        if (!key2) {
            pdf_dict_del(ctx, annot_obj, key1);
        } else if (key1_obj) {
            pdf_dict_del(ctx, key1_obj, key2);
        }
        return;
    }

    // read any existing script as a PyUnicode string
    if (!key2 || !key1_obj) {
        script = JM_get_script(ctx, key1_obj);
    } else {
        script = JM_get_script(ctx, pdf_dict_get(ctx, key1_obj, key2));
    }

    // replace old script, if different from new one
    if (!PyObject_RichCompareBool(value, script, Py_EQ)) {
        pdf_obj *newaction = JM_new_javascript(ctx, pdf, value);
        if (!key2) {
            pdf_dict_put_drop(ctx, annot_obj, key1, newaction);
        } else {
            pdf_dict_putl_drop(ctx, annot_obj, newaction, key1, key2, NULL);
        }
    }
    Py_XDECREF(script);
    return;
}

/*
// Execute a JavaScript action for annot or field.
//-----------------------------------------------------------------------------
PyObject *
JM_exec_script(fz_context *ctx, pdf_obj *annot_obj, pdf_obj *key1, pdf_obj *key2)
{
    PyObject *script = NULL;
    char *code = NULL;
    fz_try(ctx) {
        pdf_document *pdf = pdf_get_bound_document(ctx, annot_obj);
        char buf[100];
        if (!key2) {
            script = JM_get_script(ctx, key1_obj);
        } else {
            script = JM_get_script(ctx, pdf_dict_get(ctx, key1_obj, key2));
        }
        code = JM_StrAsChar(script);
        fz_snprintf(buf, sizeof buf, "%d/A", pdf_to_num(ctx, annot_obj));
        pdf_js_execute(pdf->js, buf, code);
    }
    fz_always(ctx) {
        Py_XDECREF(string);
    }
    fz_catch(ctx) {
        Py_RETURN_FALSE;
    }
    Py_RETURN_TRUE;
}
*/

// String from widget type
//-----------------------------------------------------------------------------
char *JM_field_type_text(int wtype)
{
    switch(wtype) {
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

	switch(type) {
	case PDF_WIDGET_TYPE_BUTTON:
		typename = PDF_NAME(Btn);
		setbits = PDF_BTN_FIELD_IS_PUSHBUTTON;
		break;
	case PDF_WIDGET_TYPE_RADIOBUTTON:
		typename = PDF_NAME(Btn);
		clearbits = PDF_BTN_FIELD_IS_PUSHBUTTON;
		setbits = PDF_BTN_FIELD_IS_RADIO;
		break;
	case PDF_WIDGET_TYPE_CHECKBOX:
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

	if (setbits != 0 || clearbits != 0) {
		int bits = pdf_dict_get_int(ctx, obj, PDF_NAME(Ff));
		bits &= ~clearbits;
		bits |= setbits;
		pdf_dict_put_int(ctx, obj, PDF_NAME(Ff), bits);
	}
}

// Copied from MuPDF v1.14
// Create widget.
// Returns a kept reference to a pdf_annot - caller must drop it.
//-----------------------------------------------------------------------------
pdf_annot *JM_create_widget(fz_context *ctx, pdf_document *doc, pdf_page *page, int type, char *fieldname)
{
	pdf_obj *form = NULL;
	int old_sigflags = pdf_to_int(ctx, pdf_dict_getp(ctx, pdf_trailer(ctx, doc), "Root/AcroForm/SigFlags"));
	pdf_annot *annot = pdf_create_annot_raw(ctx, page, PDF_ANNOT_WIDGET);   // returns a kept reference.
    pdf_obj *annot_obj = pdf_annot_obj(ctx, annot);
	fz_try(ctx) {
		JM_set_field_type(ctx, doc, annot_obj, type);
		pdf_dict_put_text_string(ctx, annot_obj, PDF_NAME(T), fieldname);

		if (type == PDF_WIDGET_TYPE_SIGNATURE) {
			int sigflags = (old_sigflags | (SigFlag_SignaturesExist|SigFlag_AppendOnly));
			pdf_dict_putl_drop(ctx, pdf_trailer(ctx, doc), pdf_new_int(ctx, sigflags), PDF_NAME(Root), PDF_NAME(AcroForm), PDF_NAME(SigFlags), NULL);
		}

		/*
		pdf_create_annot will have linked the new widget into the page's
		annot array. We also need it linked into the document's form
		*/
		form = pdf_dict_getp(ctx, pdf_trailer(ctx, doc), "Root/AcroForm/Fields");
		if (!form) {
			form = pdf_new_array(ctx, doc, 1);
			pdf_dict_putl_drop(ctx, pdf_trailer(ctx, doc),
                               form,
                               PDF_NAME(Root),
                               PDF_NAME(AcroForm),
                               PDF_NAME(Fields),
                               NULL);
		}

		pdf_array_push(ctx, form, annot_obj); // Cleanup relies on this statement being last
	}
	fz_catch(ctx) {
		pdf_delete_annot(ctx, page, annot);

		if (type == PDF_WIDGET_TYPE_SIGNATURE) {
			pdf_dict_putl_drop(ctx, pdf_trailer(ctx, doc), pdf_new_int(ctx, old_sigflags), PDF_NAME(Root), PDF_NAME(AcroForm), PDF_NAME(SigFlags), NULL);
        }

		fz_rethrow(ctx);
	}

	return annot;
}



// PushButton get state
//-----------------------------------------------------------------------------
PyObject *JM_pushbtn_state(fz_context *ctx, pdf_annot *annot)
{   // pushed buttons do not reflect status changes in the PDF
    // always reflect them as untouched
    Py_RETURN_FALSE;
}


// Text field retrieve value
//-----------------------------------------------------------------------------
PyObject *JM_text_value(fz_context *ctx, pdf_annot *annot)
{
    const char *text = NULL;
    fz_var(text);
    fz_try(ctx) {
        pdf_obj *annot_obj = pdf_annot_obj(ctx, annot);
        text = pdf_field_value(ctx, annot_obj);
    }
    fz_catch(ctx) Py_RETURN_NONE;
    return JM_UnicodeFromStr(text);
}

// ListBox retrieve value
//-----------------------------------------------------------------------------
PyObject *JM_listbox_value(fz_context *ctx, pdf_annot *annot)
{
    int i = 0, n = 0;
    // may be single value or array
    pdf_obj *annot_obj = pdf_annot_obj(ctx, annot);
    pdf_obj *optarr = pdf_dict_get(ctx, annot_obj, PDF_NAME(V));
    if (pdf_is_string(ctx, optarr))         // a single string
        return PyString_FromString(pdf_to_text_string(ctx, optarr));

    // value is an array (may have len 0)
    n = pdf_array_len(ctx, optarr);
    PyObject *liste = PyList_New(0);

    // extract a list of strings
    // each entry may again be an array: take second entry then
    for (i = 0; i < n; i++) {
        pdf_obj *elem = pdf_array_get(ctx, optarr, i);
        if (pdf_is_array(ctx, elem))
            elem = pdf_array_get(ctx, elem, 1);
        LIST_APPEND_DROP(liste, JM_UnicodeFromStr(pdf_to_text_string(ctx, elem)));
    }
    return liste;
}

// ComboBox retrieve value
//-----------------------------------------------------------------------------
PyObject *JM_combobox_value(fz_context *ctx, pdf_annot *annot)
{   // combobox treated like listbox
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
    pdf_obj *annot_obj = pdf_annot_obj(ctx, annot);
    PyObject *val;
    int n = pdf_choice_widget_options(ctx, annot, 0, NULL);
    if (n == 0) Py_RETURN_NONE;                     // wrong widget type

    pdf_obj *optarr = pdf_dict_get(ctx, annot_obj, PDF_NAME(Opt));
    int i, m;
    PyObject *liste = PyList_New(0);

    for (i = 0; i < n; i++) {
        m = pdf_array_len(ctx, pdf_array_get(ctx, optarr, i));
        if (m == 2) {
            val = Py_BuildValue("ss",
            pdf_to_text_string(ctx, pdf_array_get(ctx, pdf_array_get(ctx, optarr, i), 0)),
            pdf_to_text_string(ctx, pdf_array_get(ctx, pdf_array_get(ctx, optarr, i), 1)));
            LIST_APPEND_DROP(liste, val);
        } else {
            val = JM_UnicodeFromStr(pdf_to_text_string(ctx, pdf_array_get(ctx, optarr, i)));
            LIST_APPEND_DROP(liste, val);
        }
    }
    return liste;
}


// set ListBox / ComboBox values
//-----------------------------------------------------------------------------
void JM_set_choice_options(fz_context *ctx, pdf_annot *annot, PyObject *liste)
{
    if (!liste) return;
    if (!PySequence_Check(liste)) return;
    Py_ssize_t i, n = PySequence_Size(liste);
    if (n < 1) return;
    PyObject *tuple = PySequence_Tuple(liste);
    PyObject *val = NULL, *val1 = NULL, *val2 = NULL;
    pdf_obj *optarrsub = NULL, *optarr = NULL, *annot_obj = NULL;
    pdf_document *pdf = NULL;
    const char *opt = NULL, *opt1 = NULL, *opt2 = NULL;
    fz_try(ctx) {
        annot_obj = pdf_annot_obj(ctx, annot);
        pdf = pdf_get_bound_document(ctx, annot_obj);
        optarr = pdf_new_array(ctx, pdf, (int) n);
    for (i = 0; i < n; i++) {
        val = PyTuple_GET_ITEM(tuple, i);
        opt = PyUnicode_AsUTF8(val);
        if (opt) {
            pdf_array_push_text_string(ctx, optarr, opt);
        } else {
                if (!PySequence_Check(val) || PySequence_Size(val) != 2) {
                    RAISEPY(ctx, "bad choice field list", PyExc_ValueError);
                }
                val1 = PySequence_GetItem(val, 0);
                opt1 = PyUnicode_AsUTF8(val1);
                if (!opt1) {
                    RAISEPY(ctx, "bad choice field list", PyExc_ValueError);
                }
                val2 = PySequence_GetItem(val, 1);
                opt2 = PyUnicode_AsUTF8(val2);
                if (!opt2) {
                    RAISEPY(ctx, "bad choice field list", PyExc_ValueError);
                };
                Py_CLEAR(val1);
                Py_CLEAR(val2);
            optarrsub = pdf_array_push_array(ctx, optarr, 2);
            pdf_array_push_text_string(ctx, optarrsub, opt1);
            pdf_array_push_text_string(ctx, optarrsub, opt2);
        }
    }
    pdf_dict_put_drop(ctx, annot_obj, PDF_NAME(Opt), optarr);
    }
    fz_always(ctx) {
        Py_CLEAR(tuple);
        Py_CLEAR(val1);
        Py_CLEAR(val2);
        PyErr_Clear();
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return;
}


//-----------------------------------------------------------------------------
// Populate a Python Widget object with the values from a PDF form field.
// Called by "Page.firstWidget" and "Widget.next".
//-----------------------------------------------------------------------------
void JM_get_widget_properties(fz_context *ctx, pdf_annot *annot, PyObject *Widget)
{
    pdf_obj *annot_obj = pdf_annot_obj(ctx, annot);
    pdf_page *page = pdf_annot_page(ctx, annot);
    pdf_document *pdf = page->doc;
    pdf_annot *tw = annot;
    pdf_obj *obj = NULL;
    Py_ssize_t i = 0, n = 0;
    fz_try(ctx) {
        int field_type = pdf_widget_type(ctx, tw);
        SETATTR_DROP(Widget, "field_type", Py_BuildValue("i", field_type));
        if (field_type == PDF_WIDGET_TYPE_SIGNATURE) {
            if (pdf_signature_is_signed(ctx, pdf, annot_obj)) {
                SETATTR("is_signed", Py_True);
            } else {
                SETATTR("is_signed", Py_False);
            }
        } else {
            SETATTR("is_signed", Py_None);
        }
        SETATTR_DROP(Widget, "border_style",
                JM_UnicodeFromStr(pdf_field_border_style(ctx, annot_obj)));
        SETATTR_DROP(Widget, "field_type_string",
                JM_UnicodeFromStr(JM_field_type_text(field_type)));

        #if FZ_VERSION_MAJOR == 1 && FZ_VERSION_MINOR <= 22
            char *field_name = pdf_field_name(ctx, annot_obj);
        #else
            char *field_name = pdf_load_field_name(ctx, annot_obj);
        #endif
        SETATTR_DROP(Widget, "field_name", JM_UnicodeFromStr(field_name));
        JM_Free(field_name);

        const char *label = NULL;
        obj = pdf_dict_get(ctx, annot_obj, PDF_NAME(TU));
        if (obj) label = pdf_to_text_string(ctx, obj);
        SETATTR_DROP(Widget, "field_label", JM_UnicodeFromStr(label));

        const char *fvalue = NULL;
        if (field_type == PDF_WIDGET_TYPE_RADIOBUTTON) {
            obj = pdf_dict_get(ctx, annot_obj, PDF_NAME(Parent));  // owning RB group
            if (obj) {
                SETATTR_DROP(Widget, "rb_parent", Py_BuildValue("i", pdf_to_num(ctx, obj)));
            }
            obj = pdf_dict_get(ctx, annot_obj, PDF_NAME(AS));
            if (obj) {
                fvalue = pdf_to_name(ctx, obj);
            }
        }
        if (!fvalue) {
            fvalue = pdf_field_value(ctx, annot_obj);
        }
        SETATTR_DROP(Widget, "field_value", JM_UnicodeFromStr(fvalue));

        SETATTR_DROP(Widget, "field_display",
                Py_BuildValue("i", pdf_field_display(ctx, annot_obj)));

        float border_width = pdf_to_real(ctx, pdf_dict_getl(ctx, annot_obj,
                                PDF_NAME(BS), PDF_NAME(W), NULL));
        if (border_width == 0) border_width = 1;
        SETATTR_DROP(Widget, "border_width",
                Py_BuildValue("f", border_width));

        obj = pdf_dict_getl(ctx, annot_obj,
                                PDF_NAME(BS), PDF_NAME(D), NULL);
        if (pdf_is_array(ctx, obj)) {
            n = (Py_ssize_t) pdf_array_len(ctx, obj);
            PyObject *d = PyList_New(n);
            for (i = 0; i < n; i++) {
                PyList_SET_ITEM(d, i, Py_BuildValue("i", pdf_to_int(ctx,
                                pdf_array_get(ctx, obj, (int) i))));
            }
            SETATTR_DROP(Widget, "border_dashes", d);
        }

        SETATTR_DROP(Widget, "text_maxlen",
                Py_BuildValue("i", pdf_text_widget_max_len(ctx, tw)));

        SETATTR_DROP(Widget, "text_format",
                Py_BuildValue("i", pdf_text_widget_format(ctx, tw)));

        obj = pdf_dict_getl(ctx, annot_obj, PDF_NAME(MK), PDF_NAME(BG), NULL);
        if (pdf_is_array(ctx, obj)) {
            n = (Py_ssize_t) pdf_array_len(ctx, obj);
            PyObject *col = PyList_New(n);
            for (i = 0; i < n; i++) {
                PyList_SET_ITEM(col, i, Py_BuildValue("f",
                pdf_to_real(ctx, pdf_array_get(ctx, obj, (int) i))));
            }
            SETATTR_DROP(Widget, "fill_color", col);
        }

        obj = pdf_dict_getl(ctx, annot_obj, PDF_NAME(MK), PDF_NAME(BC), NULL);
        if (pdf_is_array(ctx, obj)) {
            n = (Py_ssize_t) pdf_array_len(ctx, obj);
            PyObject *col = PyList_New(n);
            for (i = 0; i < n; i++) {
                PyList_SET_ITEM(col, i, Py_BuildValue("f",
                pdf_to_real(ctx, pdf_array_get(ctx, obj, (int) i))));
            }
            SETATTR_DROP(Widget, "border_color", col);
        }

        SETATTR_DROP(Widget, "choice_values", JM_choice_options(ctx, annot));

        const char *da = pdf_to_text_string(ctx, pdf_dict_get_inheritable(ctx,
                                        annot_obj, PDF_NAME(DA)));
        SETATTR_DROP(Widget, "_text_da", JM_UnicodeFromStr(da));

        obj = pdf_dict_getl(ctx, annot_obj, PDF_NAME(MK), PDF_NAME(CA), NULL);
        if (obj) {
            SETATTR_DROP(Widget, "button_caption",
                    JM_UnicodeFromStr((char *)pdf_to_text_string(ctx, obj)));
        }

        SETATTR_DROP(Widget, "field_flags",
                Py_BuildValue("i", pdf_field_flags(ctx, annot_obj)));

        // call Py method to reconstruct text color, font name, size
        PyObject *call = CALLATTR("_parse_da", NULL);
        Py_XDECREF(call);

        // extract JavaScript action texts
        SETATTR_DROP(Widget, "script",
            JM_get_script(ctx, pdf_dict_get(ctx, annot_obj, PDF_NAME(A))));

        SETATTR_DROP(Widget, "script_stroke",
            JM_get_script(ctx, pdf_dict_getl(ctx, annot_obj, PDF_NAME(AA), PDF_NAME(K), NULL)));

        SETATTR_DROP(Widget, "script_format",
            JM_get_script(ctx, pdf_dict_getl(ctx, annot_obj, PDF_NAME(AA), PDF_NAME(F), NULL)));

        SETATTR_DROP(Widget, "script_change",
            JM_get_script(ctx, pdf_dict_getl(ctx, annot_obj, PDF_NAME(AA), PDF_NAME(V), NULL)));

        SETATTR_DROP(Widget, "script_calc",
            JM_get_script(ctx, pdf_dict_getl(ctx, annot_obj, PDF_NAME(AA), PDF_NAME(C), NULL)));

        SETATTR_DROP(Widget, "script_blur",
            JM_get_script(ctx, pdf_dict_getl(ctx, annot_obj, PDF_NAME(AA), pdf_new_name(ctx, "Bl"), NULL)));

        SETATTR_DROP(Widget, "script_focus",
            JM_get_script(ctx, pdf_dict_getl(ctx, annot_obj, PDF_NAME(AA), pdf_new_name(ctx, "Fo"), NULL)));
    }
    fz_always(ctx) PyErr_Clear();
    fz_catch(ctx) fz_rethrow(ctx);
    return;
}


//-----------------------------------------------------------------------------
// Update the PDF form field with the properties from a Python Widget object.
// Called by "Page.addWidget" and "Annot.updateWidget".
//-----------------------------------------------------------------------------
void JM_set_widget_properties(fz_context *ctx, pdf_annot *annot, PyObject *Widget)
{
    pdf_page *page = pdf_annot_page(ctx, annot);
    pdf_obj *annot_obj = pdf_annot_obj(ctx, annot);
    pdf_document *pdf = page->doc;
    fz_rect rect;
    pdf_obj *fill_col = NULL, *border_col = NULL;
    pdf_obj *dashes = NULL;
    Py_ssize_t i, n = 0;
    int d;
    PyObject *value = GETATTR("field_type");
    int field_type = (int) PyInt_AsLong(value);
    Py_DECREF(value);

    // rectangle --------------------------------------------------------------
    value = GETATTR("rect");
    rect = JM_rect_from_py(value);
    Py_XDECREF(value);
    fz_matrix rot_mat = JM_rotate_page_matrix(ctx, page);
    rect = fz_transform_rect(rect, rot_mat);
    pdf_set_annot_rect(ctx, annot, rect);

    // fill color -------------------------------------------------------------
    value = GETATTR("fill_color");
    if (value && PySequence_Check(value)) {
        n = PySequence_Size(value);
        fill_col = pdf_new_array(ctx, pdf, n);
        double col = 0;
        for (i = 0; i < n; i++) {
            JM_FLOAT_ITEM(value, i, &col);
            pdf_array_push_real(ctx, fill_col, col);
        }
        pdf_field_set_fill_color(ctx, annot_obj, fill_col);
        pdf_drop_obj(ctx, fill_col);
    }
    Py_XDECREF(value);

    // dashes -----------------------------------------------------------------
    value = GETATTR("border_dashes");
    if (value && PySequence_Check(value)) {
        n = PySequence_Size(value);
        dashes = pdf_new_array(ctx, pdf, n);
        for (i = 0; i < n; i++) {
            pdf_array_push_int(ctx, dashes,
                               (int64_t) PyInt_AsLong(PySequence_ITEM(value, i)));
        }
        pdf_dict_putl_drop(ctx, annot_obj, dashes,
                                PDF_NAME(BS),
                                PDF_NAME(D),
                                NULL);
    }
    Py_XDECREF(value);

    // border color -----------------------------------------------------------
    value = GETATTR("border_color");
    if (value && PySequence_Check(value)) {
        n = PySequence_Size(value);
        border_col = pdf_new_array(ctx, pdf, n);
        double col = 0;
        for (i = 0; i < n; i++) {
            JM_FLOAT_ITEM(value, i, &col);
            pdf_array_push_real(ctx, border_col, col);
        }
        pdf_dict_putl_drop(ctx, annot_obj, border_col,
                                PDF_NAME(MK),
                                PDF_NAME(BC),
                                NULL);
    }
    Py_XDECREF(value);

    // entry ignored - may be used later
    /*
    int text_format = (int) PyInt_AsLong(GETATTR("text_format"));
    */

    // field label -----------------------------------------------------------
    value = GETATTR("field_label");
    if (value != Py_None) {
        char *label = JM_StrAsChar(value);
        pdf_dict_put_text_string(ctx, annot_obj, PDF_NAME(TU), label);
    }
    Py_XDECREF(value);

    // field name -------------------------------------------------------------
    value = GETATTR("field_name");
    if (value != Py_None) {
        char *name = JM_StrAsChar(value);
        #if FZ_VERSION_MAJOR == 1 && FZ_VERSION_MINOR <= 22
            char *old_name = pdf_field_name(ctx, annot_obj);
        #else
            char *old_name = pdf_load_field_name(ctx, annot_obj);
        #endif
        if (strcmp(name, old_name) != 0) {
            pdf_dict_put_text_string(ctx, annot_obj, PDF_NAME(T), name);
        }
        JM_Free(old_name);
    }
    Py_XDECREF(value);

    // max text len -----------------------------------------------------------
    if (field_type == PDF_WIDGET_TYPE_TEXT)
    {
        value = GETATTR("text_maxlen");
        int text_maxlen = (int) PyInt_AsLong(value);
        if (text_maxlen) {
            pdf_dict_put_int(ctx, annot_obj, PDF_NAME(MaxLen), text_maxlen);
        }
        Py_XDECREF(value);
    }
    value = GETATTR("field_display");
    d = (int) PyInt_AsLong(value);
    Py_XDECREF(value);
    pdf_field_set_display(ctx, annot_obj, d);

    // choice values ----------------------------------------------------------
    if (field_type == PDF_WIDGET_TYPE_LISTBOX ||
        field_type == PDF_WIDGET_TYPE_COMBOBOX) {
        value = GETATTR("choice_values");
        JM_set_choice_options(ctx, annot, value);
        Py_XDECREF(value);
    }

    // border style -----------------------------------------------------------
    value = GETATTR("border_style");
    pdf_obj *val = JM_get_border_style(ctx, value);
    Py_XDECREF(value);
    pdf_dict_putl_drop(ctx, annot_obj, val,
                            PDF_NAME(BS),
                            PDF_NAME(S),
                            NULL);

    // border width -----------------------------------------------------------
    value = GETATTR("border_width");
    float border_width = (float) PyFloat_AsDouble(value);
    Py_XDECREF(value);
    pdf_dict_putl_drop(ctx, annot_obj, pdf_new_real(ctx, border_width),
                            PDF_NAME(BS),
                            PDF_NAME(W),
                            NULL);

    // /DA string -------------------------------------------------------------
    value = GETATTR("_text_da");
    char *da = JM_StrAsChar(value);
    Py_XDECREF(value);
    pdf_dict_put_text_string(ctx, annot_obj, PDF_NAME(DA), da);
    pdf_dict_del(ctx, annot_obj, PDF_NAME(DS)); /* not supported by MuPDF */
    pdf_dict_del(ctx, annot_obj, PDF_NAME(RC)); /* not supported by MuPDF */

    // field flags ------------------------------------------------------------
    value = GETATTR("field_flags");
    int field_flags = (int) PyInt_AsLong(value);
    Py_XDECREF(value);
    if (!PyErr_Occurred()) {
        if (field_type == PDF_WIDGET_TYPE_COMBOBOX) {
            field_flags |= PDF_CH_FIELD_IS_COMBO;
        } else if (field_type == PDF_WIDGET_TYPE_RADIOBUTTON) {
            field_flags |= PDF_BTN_FIELD_IS_RADIO;
        } else if (field_type == PDF_WIDGET_TYPE_BUTTON) {
            field_flags |= PDF_BTN_FIELD_IS_PUSHBUTTON;
        }
        pdf_dict_put_int(ctx, annot_obj, PDF_NAME(Ff), field_flags);
    }

    // button caption ---------------------------------------------------------
    value = GETATTR("button_caption");
    char *ca = JM_StrAsChar(value);
    if (ca) {
        pdf_field_set_button_caption(ctx, annot_obj, ca);
    }
    Py_XDECREF(value);

    // script (/A) -------------------------------------------------------
    value = GETATTR("script");
    JM_put_script(ctx, annot_obj, PDF_NAME(A), NULL, value);
    Py_CLEAR(value);

    // script (/AA/K) -------------------------------------------------------
    value = GETATTR("script_stroke");
    JM_put_script(ctx, annot_obj, PDF_NAME(AA), PDF_NAME(K), value);
    Py_CLEAR(value);

    // script (/AA/F) -------------------------------------------------------
    value = GETATTR("script_format");
    JM_put_script(ctx, annot_obj, PDF_NAME(AA), PDF_NAME(F), value);
    Py_CLEAR(value);

    // script (/AA/V) -------------------------------------------------------
    value = GETATTR("script_change");
    JM_put_script(ctx, annot_obj, PDF_NAME(AA), PDF_NAME(V), value);
    Py_CLEAR(value);

    // script (/AA/C) -------------------------------------------------------
    value = GETATTR("script_calc");
    JM_put_script(ctx, annot_obj, PDF_NAME(AA), PDF_NAME(C), value);
    Py_CLEAR(value);

    // script (/AA/Bl) ------------------------------------------------------
    value = GETATTR("script_blur");
    JM_put_script(ctx, annot_obj, PDF_NAME(AA), pdf_new_name(ctx, "Bl"), value);
    Py_CLEAR(value);

    // script (/AA/Fo) ------------------------------------------------------
    value = GETATTR("script_focus");
    JM_put_script(ctx, annot_obj, PDF_NAME(AA), pdf_new_name(ctx, "Fo"), value);
    Py_CLEAR(value);

    // field value ------------------------------------------------------------
    value = GETATTR("field_value");  // field value
    char *text = JM_StrAsChar(value);  // convert to text (may fail!)

    switch(field_type)
    {
    case PDF_WIDGET_TYPE_RADIOBUTTON:
        if (PyObject_RichCompareBool(value, Py_False, Py_EQ)) {
            pdf_set_field_value(ctx, pdf, annot_obj, "Off", 1);
            pdf_dict_put_name(gctx, annot_obj, PDF_NAME(AS), "Off");
        } else {
            pdf_obj *onstate = pdf_button_field_on_state(ctx, annot_obj);
            if (onstate) {
                const char *on = pdf_to_name(ctx, onstate);
                pdf_set_field_value(ctx, pdf, annot_obj, on, 1);
                pdf_dict_put_name(gctx, annot_obj, PDF_NAME(AS), on);
            } else  if (text) {
                pdf_dict_put_name(gctx, annot_obj, PDF_NAME(AS), text);
            }
        }
        break;

    case PDF_WIDGET_TYPE_CHECKBOX:  // will always be "Yes" or "Off"
        if (PyObject_RichCompareBool(value, Py_True, Py_EQ) || text && strcmp(text, "Yes")==0) {
            pdf_dict_put_name(gctx, annot_obj, PDF_NAME(AS), "Yes");
            pdf_dict_put_name(gctx, annot_obj, PDF_NAME(V), "Yes");
        } else {
            pdf_dict_put_name(gctx, annot_obj, PDF_NAME(AS), "Off");
            pdf_dict_put_name(gctx, annot_obj, PDF_NAME(V), "Off");
        }
        break;

    default:
        if (text) {
            pdf_set_field_value(ctx, pdf, annot_obj, (const char *)text, 1);
            if (field_type == PDF_WIDGET_TYPE_COMBOBOX || field_type == PDF_WIDGET_TYPE_LISTBOX) {
                pdf_dict_del(ctx, annot_obj, PDF_NAME(I));
            }
        }
    }
    Py_CLEAR(value);
    PyErr_Clear();
    pdf_dirty_annot(ctx, annot);
    pdf_set_annot_hot(ctx, annot, 1);
    pdf_set_annot_active(ctx, annot, 1);
    pdf_update_annot(ctx, annot);
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
        self.thisown = True
        self.border_color = None
        self.border_style = "S"
        self.border_width = 0
        self.border_dashes = None
        self.choice_values = None  # choice fields only
        self.rb_parent = None  # radio buttons only: xref of owning parent

        self.field_name = None  # field name
        self.field_label = None  # field label
        self.field_value = None
        self.field_flags = 0
        self.field_display = 0
        self.field_type = 0  # valid range 1 through 7
        self.field_type_string = None  # field type as string

        self.fill_color = None
        self.button_caption = None  # button caption
        self.is_signed = None  # True / False if signature
        self.text_color = (0, 0, 0)
        self.text_font = "Helv"
        self.text_fontsize = 0
        self.text_maxlen = 0  # text fields only
        self.text_format = 0  # text fields only
        self._text_da = ""  # /DA = default apparance

        self.script = None  # JavaScript (/A)
        self.script_stroke = None  # JavaScript (/AA/K)
        self.script_format = None  # JavaScript (/AA/F)
        self.script_change = None  # JavaScript (/AA/V)
        self.script_calc = None  # JavaScript (/AA/C)
        self.script_blur = None  # JavaScript (/AA/Bl)
        self.script_focus = None  # JavaScript (/AA/Fo)

        self.rect = None  # annot value
        self.xref = 0  # annot value


    def _validate(self):
        """Validate the class entries.
        """
        if (self.rect.is_infinite
            or self.rect.is_empty
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

        # standardize content of JavaScript entries
        btn_type = self.field_type in (
            PDF_WIDGET_TYPE_BUTTON,
            PDF_WIDGET_TYPE_CHECKBOX,
            PDF_WIDGET_TYPE_RADIOBUTTON
        )
        if not self.script:
            self.script = None
        elif type(self.script) is not str:
            raise ValueError("script content must be a string")

        # buttons cannot have the following script actions
        if btn_type or not self.script_calc:
            self.script_calc = None
        elif type(self.script_calc) is not str:
            raise ValueError("script_calc content must be a string")

        if btn_type or not self.script_change:
            self.script_change = None
        elif type(self.script_change) is not str:
            raise ValueError("script_change content must be a string")

        if btn_type or not self.script_format:
            self.script_format = None
        elif type(self.script_format) is not str:
            raise ValueError("script_format content must be a string")

        if btn_type or not self.script_stroke:
            self.script_stroke = None
        elif type(self.script_stroke) is not str:
            raise ValueError("script_stroke content must be a string")

        if btn_type or not self.script_blur:
            self.script_blur = None
        elif type(self.script_blur) is not str:
            raise ValueError("script_blur content must be a string")

        if btn_type or not self.script_focus:
            self.script_focus = None
        elif type(self.script_focus) is not str:
            raise ValueError("script_focus content must be a string")

        self._checker()  # any field_type specific checks


    def _adjust_font(self):
        """Ensure text_font is correctly spelled if empty or from our list.

        Otherwise assume the font is in an existing field.
        """
        if not self.text_font:
            self.text_font = "Helv"
            return
        doc = self.parent.parent
        for f in doc.FormFonts + ["Cour", "TiRo", "Helv", "ZaDb"]:
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
            if item == "g":  # unicolor text
                col = [(float(dat[i - 1]))]
                dat[i] = dat[i-1] = ""
                continue
            if item == "rg":  # RGB colored text
                col = [float(f) for f in dat[i - 3:i]]
                dat[i] = dat[i-1] = dat[i-2] = dat[i-3] = ""
                continue
        self.text_font = font
        self.text_fontsize = fsize
        self.text_color = col
        self._text_da = ""
        return


    def _checker(self):
        """Any widget type checks.
        """
        if self.field_type not in range(1, 8):
            raise ValueError("bad field type")


        # if setting a radio button to ON, first set Off all buttons
        # in the group - this is not done by MuPDF:
        if self.field_type == PDF_WIDGET_TYPE_RADIOBUTTON and self.field_value not in (False, "Off") and hasattr(self, "parent"):
            # so we are about setting this button to ON/True
            # check other buttons in same group and set them to 'Off'
            doc = self.parent.parent
            kids_type, kids_value = doc.xref_get_key(self.xref, "Parent/Kids")
            if kids_type == "array":
                xrefs = tuple(map(int, kids_value[1:-1].replace("0 R","").split()))
                for xref in xrefs:
                    if xref != self.xref:
                        doc.xref_set_key(xref, "AS", "/Off")
        # the calling method will now set the intended button to on and
        # will find everything prepared for correct functioning.


    def update(self):
        """Reflect Python object in the PDF.
        """
        doc = self.parent.parent
        self._validate()

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

        # if widget has a '/AA/C' script, make sure it is in the '/CO'
        # array of the '/AcroForm' dictionary.
        if self.script_calc:  # there is a "calculation" script:
            # make sure we are in the /CO array
            util_ensure_widget_calc(self._annot)

        # finally update the widget
        TOOLS._save_widget(self._annot, self)
        self._text_da = ""


    def button_states(self):
        """Return the on/off state names for button widgets.

        A button may have 'normal' or 'pressed down' appearances. While the 'Off'
        state is usually called like this, the 'On' state is often given a name
        relating to the functional context.
        """
        if self.field_type not in (2, 5):
            return None  # no button type
        if hasattr(self, "parent"):  # field already exists on page
            doc = self.parent.parent
        else:
            return None
        xref = self.xref
        states = {"normal": None, "down": None}
        APN = doc.xref_get_key(xref, "AP/N")
        if APN[0] == "dict":
            nstates = []
            APN = APN[1][2:-2]
            apnt = APN.split("/")[1:]
            for x in apnt:
                nstates.append(x.split()[0])
            states["normal"] = nstates
        if APN[0] == "xref":
            nstates = []
            nxref = int(APN[1].split(" ")[0])
            APN = doc.xref_object(nxref)
            apnt = APN.split("/")[1:]
            for x in apnt:
                nstates.append(x.split()[0])
            states["normal"] = nstates
        APD = doc.xref_get_key(xref, "AP/D")
        if APD[0] == "dict":
            dstates = []
            APD = APD[1][2:-2]
            apdt = APD.split("/")[1:]
            for x in apdt:
                dstates.append(x.split()[0])
            states["down"] = dstates
        if APD[0] == "xref":
            dstates = []
            dxref = int(APD[1].split(" ")[0])
            APD = doc.xref_object(dxref)
            apdt = APD.split("/")[1:]
            for x in apdt:
                dstates.append(x.split()[0])
            states["down"] = dstates
        return states

    def on_state(self):
        """Return the "On" value for button widgets.

        This is useful for radio buttons mainly. Checkboxes will always return
        "Yes". Radio buttons will return the string that is unequal to "Off"
        as returned by method button_states().
        If the radio button is new / being created, it does not yet have an
        "On" value. In this case, a warning is shown and True is returned.
        """
        if self.field_type not in (2, 5):
            return None  # no checkbox or radio button
        if self.field_type == 2:
            return "Yes"
        bstate = self.button_states()
        if bstate==None:
            bstate = {}
        for k in bstate.keys():
            for v in bstate[k]:
                if v != "Off":
                    return v
        print("warning: radio button has no 'On' value.")
        return True

    def reset(self):
        """Reset the field value to its default.
        """
        TOOLS._reset_widget(self._annot)

    def __repr__(self):
        return "'%s' widget on %s" % (self.field_type_string, str(self.parent))

    def __del__(self):
        if hasattr(self, "_annot"):
            del self._annot

    @property
    def next(self):
        return self._annot.next
%}
