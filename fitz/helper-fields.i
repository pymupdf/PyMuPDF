%{
//-----------------------------------------------------------------------------
// Functions dealing with PDF form fields
//-----------------------------------------------------------------------------
PyObject *JM_pushbtn_state(fz_context *ctx, pdf_annot *annot)
{   // pushed buttons do not reflect status changes in the PDF
    // always reflect them as untouched
    Py_RETURN_FALSE;
}

PyObject *JM_checkbox_state(fz_context *ctx, pdf_annot *annot)
{
    pdf_document *pdf = pdf_get_bound_document(ctx, annot->obj);
    pdf_obj *leafv  = pdf_get_inheritable(ctx, pdf, annot->obj, PDF_NAME_V);
    pdf_obj *leafas = pdf_get_inheritable(ctx, pdf, annot->obj, PDF_NAME_AS);
    if (leafv)
        if (leafv  == PDF_NAME_Off) Py_RETURN_FALSE;
    if (leafas)
        if (leafas == PDF_NAME_Off) Py_RETURN_FALSE;
    Py_RETURN_TRUE;
}

PyObject *JM_radiobtn_state(fz_context *ctx, pdf_annot *annot)
{   // MuPDF treats radio buttons like check boxes - hence so do we
    return JM_checkbox_state(ctx, annot);
}

PyObject *JM_text_value(fz_context *ctx, pdf_annot *annot)
{
    char *text = NULL;
    pdf_document *pdf = pdf_get_bound_document(ctx, annot->obj);
    fz_var(text);
    fz_try(ctx)
        text = pdf_field_value(ctx, pdf, annot->obj);
    fz_catch(ctx) return NONE;
    if (text) return PyString_FromString(text);
    return NONE;
}

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

PyObject *JM_combobox_value(fz_context *ctx, pdf_annot *annot)
{   // combobox values are treated like listbox values
    return JM_listbox_value(ctx, annot);
}

PyObject *JM_signature_value(fz_context *ctx, pdf_annot *annot)
{   // signatures are currently not covered
    return NONE;
}

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

%}