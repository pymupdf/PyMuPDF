%{

//-----------------------------------------------------------------------------
// Functions converting betwenn PySequences and fitz geometry objects
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
// fz_quad from PySequence. Four-floats-seq is treated as rect.
// Else must be four pairs of floats.
//-----------------------------------------------------------------------------
fz_quad JM_quad_from_py(PyObject *r)
{
    fz_quad q;
    fz_point p[4];
    size_t i;
    q.ul = q.ur = q.ll = q.lr = fz_make_point(0, 0);

    if (!PySequence_Check(r) || PySequence_Size(r) != 4)
        return q;

    float x0 = (float) PyFloat_AsDouble(PySequence_ITEM(r, 0));
    if (!PyErr_Occurred())             // assume case 1: a rect is given
    {
        float y0 = (float) PyFloat_AsDouble(PySequence_ITEM(r, 1));
        if (PyErr_Occurred()) goto return_simple;

        float x1 = (float) PyFloat_AsDouble(PySequence_ITEM(r, 2));
        if (PyErr_Occurred()) goto return_simple;

        float y1 = (float) PyFloat_AsDouble(PySequence_ITEM(r, 3));
        if (PyErr_Occurred()) goto return_simple;

        q.ul = fz_make_point(x0, y0);
        q.ur = fz_make_point(x1, y0);
        q.ll = fz_make_point(x0, y1);
        q.lr = fz_make_point(x1, y1);

        return_simple: ;
        PyErr_Clear();
        return q;
    }

    PyErr_Clear();
    for (i = 0; i < 4; i++)
    {
        PyObject *o = PySequence_ITEM(r, i);
        p[i].x = p[i].y = 0;
        if (!PySequence_Check(o) || PySequence_Size(o) != 2)
            goto weiter;

        p[i].x = (float) PyFloat_AsDouble(PySequence_ITEM(o, 0));
        if (PyErr_Occurred())
            p[i].x = 0;

        p[i].y = (float) PyFloat_AsDouble(PySequence_ITEM(o, 1));
        if (PyErr_Occurred())
            p[i].y = 0;

        PyErr_Clear();
        weiter: ;
        Py_CLEAR(o);
    }
    q.ul = p[0];
    q.ur = p[1];
    q.ll = p[2];
    q.lr = p[3];
    return q;
}

//-----------------------------------------------------------------------------
// PySequence from fz_quad.
//-----------------------------------------------------------------------------
PyObject *JM_py_from_quad(fz_quad quad)
{
    PyObject *pquad = PyTuple_New(4);
    PyTuple_SET_ITEM(pquad, 0, Py_BuildValue("ff", quad.ul.x, quad.ul.y));
    PyTuple_SET_ITEM(pquad, 1, Py_BuildValue("ff", quad.ur.x, quad.ur.y));
    PyTuple_SET_ITEM(pquad, 2, Py_BuildValue("ff", quad.ll.x, quad.ll.y));
    PyTuple_SET_ITEM(pquad, 3, Py_BuildValue("ff", quad.lr.x, quad.lr.y));
    return pquad;
}

//-----------------------------------------------------------------------------
// PySequence to fz_rect. Default: infinite rect
//-----------------------------------------------------------------------------
fz_rect JM_rect_from_py(PyObject *r)
{
    if (!PySequence_Check(r) || PySequence_Size(r) != 4)
        return fz_infinite_rect;

    float x0 = (float) PyFloat_AsDouble(PySequence_ITEM(r, 0));
    if (PyErr_Occurred()) goto return_empty;

    float y0 = (float) PyFloat_AsDouble(PySequence_ITEM(r, 1));
    if (PyErr_Occurred()) goto return_empty;

    float x1 = (float) PyFloat_AsDouble(PySequence_ITEM(r, 2));
    if (PyErr_Occurred()) goto return_empty;

    float y1 = (float) PyFloat_AsDouble(PySequence_ITEM(r, 3));
    if (PyErr_Occurred()) goto return_empty;

    return fz_make_rect(x0, y0, x1, y1);

    return_empty: ;
    PyErr_Clear();
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

    int x0 = (int) PyLong_AsLong(PySequence_ITEM(r, 0));
    if (PyErr_Occurred()) goto return_empty;

    int y0 = (int) PyLong_AsLong(PySequence_ITEM(r, 1));
    if (PyErr_Occurred()) goto return_empty;

    int x1 = (int) PyLong_AsLong(PySequence_ITEM(r, 2));
    if (PyErr_Occurred()) goto return_empty;

    int y1 = (int) PyLong_AsLong(PySequence_ITEM(r, 3));
    if (PyErr_Occurred()) goto return_empty;

    return fz_make_irect(x0, y0, x1, y1);

    return_empty: ;
    PyErr_Clear();
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

    float x = (float) PyFloat_AsDouble(PySequence_ITEM(p, 0));
    if (PyErr_Occurred()) goto zero_point;

    float y = (float) PyFloat_AsDouble(PySequence_ITEM(p, 1));
    if (PyErr_Occurred()) goto zero_point;

    return fz_make_point(x, y);

    zero_point: ;
    PyErr_Clear();
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
    if (!PySequence_Check(m) || PySequence_Size(m) != 6)
        return m0;

    float a = (float) PyFloat_AsDouble(PySequence_ITEM(m, 0));
    if (PyErr_Occurred()) goto fertig;

    float b = (float) PyFloat_AsDouble(PySequence_ITEM(m, 1));
    if (PyErr_Occurred()) goto fertig;

    float c = (float) PyFloat_AsDouble(PySequence_ITEM(m, 2));
    if (PyErr_Occurred()) goto fertig;

    float d = (float) PyFloat_AsDouble(PySequence_ITEM(m, 3));
    if (PyErr_Occurred()) goto fertig;

    float e = (float) PyFloat_AsDouble(PySequence_ITEM(m, 4));
    if (PyErr_Occurred()) goto fertig;

    float f = (float) PyFloat_AsDouble(PySequence_ITEM(m, 5));
    if (PyErr_Occurred()) goto fertig;

    m0.a = a;
    m0.b = b;
    m0.c = c;
    m0.d = d;
    m0.e = e;
    m0.f = f;

    fertig: ;
    PyErr_Clear();
    return m0;
}

//-----------------------------------------------------------------------------
// PySequence from fz_matrix
//-----------------------------------------------------------------------------
PyObject *JM_py_from_matrix(fz_matrix m)
{
    return Py_BuildValue("ffffff", m.a, m.b, m.c, m.d, m.e, m.f);
}

%}
