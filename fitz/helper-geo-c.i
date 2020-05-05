%{

//-----------------------------------------------------------------------------
// Functions converting betwenn PySequences and fitz geometry objects
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
// PySequence to fz_rect. Default: infinite rect
//-----------------------------------------------------------------------------
fz_rect JM_rect_from_py(PyObject *r)
{
    if (!PySequence_Check(r) || PySequence_Size(r) != 4)
        return fz_infinite_rect;
    PyObject *o;

    o = PySequence_ITEM(r, 0);
    if (!o) goto return_empty;
    float x0 = (float) PyFloat_AsDouble(o);
    if (PyErr_Occurred()) goto return_empty;
    Py_DECREF(o);

    o = PySequence_ITEM(r, 1);
    if (!o) goto return_empty;
    float y0 = (float) PyFloat_AsDouble(o);
    if (PyErr_Occurred()) goto return_empty;
    Py_DECREF(o);

    o = PySequence_ITEM(r, 2);
    if (!o) goto return_empty;
    float x1 = (float) PyFloat_AsDouble(o);
    if (PyErr_Occurred()) goto return_empty;
    Py_DECREF(o);

    o = PySequence_ITEM(r, 3);
    if (!o) goto return_empty;
    float y1 = (float) PyFloat_AsDouble(o);
    if (PyErr_Occurred()) goto return_empty;
    Py_DECREF(o);

    return fz_make_rect(x0, y0, x1, y1);

    return_empty: ;
    PyErr_Clear();
    Py_CLEAR(o);
    return fz_infinite_rect;
}

//-----------------------------------------------------------------------------
// PySequence from fz_rect
//-----------------------------------------------------------------------------
PyObject *JM_py_from_rect(fz_rect r)
{
    return Py_BuildValue("ffff", r.x0, r.y0, r.x1, r.y1);
}

//-----------------------------------------------------------------------------
// PySequence to fz_irect. Default: infinite irect
//-----------------------------------------------------------------------------
fz_irect JM_irect_from_py(PyObject *r)
{
    if (!PySequence_Check(r) || PySequence_Size(r) != 4)
        return fz_infinite_irect;

    PyObject *o;

    o = PySequence_ITEM(r, 0);
    if (!o) goto return_empty;
    int x0 = (int) PyLong_AsLong(o);
    if (PyErr_Occurred()) goto return_empty;
    Py_DECREF(o);

    o = PySequence_ITEM(r, 1);
    if (!o) goto return_empty;
    int y0 = (int) PyLong_AsLong(o);
    if (PyErr_Occurred()) goto return_empty;
    Py_DECREF(o);

    o = PySequence_ITEM(r, 2);
    if (!o) goto return_empty;
    int x1 = (int) PyLong_AsLong(o);
    if (PyErr_Occurred()) goto return_empty;
    Py_DECREF(o);

    o = PySequence_ITEM(r, 3);
    if (!o) goto return_empty;
    int y1 = (int) PyLong_AsLong(o);
    if (PyErr_Occurred()) goto return_empty;
    Py_DECREF(o);

    return fz_make_irect(x0, y0, x1, y1);

    return_empty: ;
    PyErr_Clear();
    Py_CLEAR(o);
    return fz_infinite_irect;
}

//-----------------------------------------------------------------------------
// PySequence from fz_irect
//-----------------------------------------------------------------------------
PyObject *JM_py_from_irect(fz_irect r)
{
    return Py_BuildValue("iiii", r.x0, r.y0, r.x1, r.y1);
}


//-----------------------------------------------------------------------------
// PySequence to fz_point. Default: (0, 0)
//-----------------------------------------------------------------------------
fz_point JM_point_from_py(PyObject *p)
{
    fz_point p0 = fz_make_point(0, 0);
    if (!PySequence_Check(p) || PySequence_Size(p) != 2)
        return p0;
    PyObject *o;
    o = PySequence_ITEM(p, 0);
    if (!o) goto zero_point;
    float x = (float) PyFloat_AsDouble(o);
    if (PyErr_Occurred()) goto zero_point;
    Py_DECREF(o);

    o = PySequence_ITEM(p, 1);
    if (!o) goto zero_point;
    float y = (float) PyFloat_AsDouble(o);
    if (PyErr_Occurred()) goto zero_point;

    return fz_make_point(x, y);

    zero_point: ;
    PyErr_Clear();
    Py_CLEAR(o);
    return p0;
}

//-----------------------------------------------------------------------------
// PySequence from fz_point
//-----------------------------------------------------------------------------
PyObject *JM_py_from_point(fz_point p)
{
    return Py_BuildValue("ff", p.x, p.y);
}


//-----------------------------------------------------------------------------
// PySequence to fz_matrix. Default: fz_identity
//-----------------------------------------------------------------------------
fz_matrix JM_matrix_from_py(PyObject *m)
{
    fz_matrix m0 = fz_identity;
    if (!m || !PySequence_Check(m) || PySequence_Size(m) != 6)
        return m0;

    PyObject *o;

    o = PySequence_ITEM(m, 0);
    if (!o) goto fertig;
    float a = (float) PyFloat_AsDouble(o);
    if (PyErr_Occurred()) goto fertig;
    Py_DECREF(o);

    o = PySequence_ITEM(m, 1);
    if (!o) goto fertig;
    float b = (float) PyFloat_AsDouble(o);
    if (PyErr_Occurred()) goto fertig;

    o = PySequence_ITEM(m, 2);
    if (!o) goto fertig;
    float c = (float) PyFloat_AsDouble(o);
    if (PyErr_Occurred()) goto fertig;
    Py_DECREF(o);

    o = PySequence_ITEM(m, 3);
    if (!o) goto fertig;
    float d = (float) PyFloat_AsDouble(o);
    if (PyErr_Occurred()) goto fertig;
    Py_DECREF(o);

    o = PySequence_ITEM(m, 4);
    if (!o) goto fertig;
    float e = (float) PyFloat_AsDouble(o);
    if (PyErr_Occurred()) goto fertig;
    Py_DECREF(o);

    o = PySequence_ITEM(m, 5);
    if (!o) goto fertig;
    float f = (float) PyFloat_AsDouble(o);
    if (PyErr_Occurred()) goto fertig;
    Py_DECREF(o);

    return fz_make_matrix(a, b, c, d, e, f);

    fertig: ;
    PyErr_Clear();
    Py_CLEAR(o);
    return m0;
}

//-----------------------------------------------------------------------------
// PySequence from fz_matrix
//-----------------------------------------------------------------------------
PyObject *JM_py_from_matrix(fz_matrix m)
{
    return Py_BuildValue("ffffff", m.a, m.b, m.c, m.d, m.e, m.f);
}

//-----------------------------------------------------------------------------
// fz_quad from PySequence. Four-floats-seq is treated as rect.
// Else must be four pairs of floats.
//-----------------------------------------------------------------------------
fz_quad JM_quad_from_py(PyObject *r)
{
    fz_quad q = fz_make_quad(0, 0, 0, 0, 0, 0, 0, 0);
    fz_point p[4];
    size_t i;
    PyObject *o, *o1;

    if (!PySequence_Check(r) || PySequence_Size(r) != 4)
        return q;

    o = PySequence_ITEM(r, 0);
    float x0 = (float) PyFloat_AsDouble(o);  // 1st item a float?
    Py_XDECREF(o);
    if (!PyErr_Occurred())  // assume: a rect is given
    {
        return fz_quad_from_rect(JM_rect_from_py(r));
    }

    PyErr_Clear();
    for (i = 0; i < 4; i++)
    {
        o = PySequence_ITEM(r, i);  // next point item
        if (!o || !PySequence_Check(o) || PySequence_Size(o) != 2)
            goto exit_result;  // invalid: cancel the rest

        o1 = PySequence_ITEM(o, 0);
        if (o1) p[i].x = (float) PyFloat_AsDouble(o1);
        else goto exit_result;
        Py_CLEAR(o1);
        if (PyErr_Occurred()) goto exit_result;

        o1 = PySequence_ITEM(o, 1);
        if (o1) p[i].y = (float) PyFloat_AsDouble(o1);
        else goto exit_result;
        Py_CLEAR(o1);
        if (PyErr_Occurred()) goto exit_result;

        Py_DECREF(o);
    }
    q.ul = p[0];
    q.ur = p[1];
    q.ll = p[2];
    q.lr = p[3];

    exit_result:;
    PyErr_Clear();
    Py_CLEAR(o);
    return q;
}

//-----------------------------------------------------------------------------
// PySequence from fz_quad.
//-----------------------------------------------------------------------------
PyObject *JM_py_from_quad(fz_quad quad)
{
    PyObject *pquad = PyTuple_New(4);
    PyTuple_SET_ITEM(pquad, 0, JM_py_from_point(quad.ul));
    PyTuple_SET_ITEM(pquad, 1, JM_py_from_point(quad.ur));
    PyTuple_SET_ITEM(pquad, 2, JM_py_from_point(quad.ll));
    PyTuple_SET_ITEM(pquad, 3, JM_py_from_point(quad.lr));
    return pquad;
}

%}
