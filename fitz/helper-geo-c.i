%{

//-----------------------------------------------------------------------------
// Functions converting betwenn PySequences and fitz geometry objects
//-----------------------------------------------------------------------------
//-----------------------------------------------------------------------------
// Incomplete - not in use
//-----------------------------------------------------------------------------
/*
int JM_is_valid_quad(fz_quad q)
{
    fz_point b = fz_normalize_vector(fz_make_point(q.ur.x - q.ul.x, q.ur.y - q.ul.y));
    if ((fabs(b.x) + fabs(b.y)) <= JM_EPS) return 0;  // empty quad!

    fz_point c = fz_normalize_vector(fz_make_point(q.ll.x - q.ul.x, q.ll.y - q.ul.y));
    if ((fabs(c.x) + fabs(c.y)) <= JM_EPS) return 0;  // empty quad!

    if (fabs(b.x * c.x + b.y * c.y) > JM_EPS)
        return 0;                                // angle at UL != 90 deg

    b = fz_normalize_vector(fz_make_point(q.ur.x - q.lr.x, q.ur.y - q.lr.y));
    c = fz_normalize_vector(fz_make_point(q.ll.x - q.lr.x, q.ll.y - q.lr.y));
    if (fabs(b.x * c.x + b.y * c.y) > JM_EPS)
        return 0;                                // angle at LR != 90 deg

    b = fz_normalize_vector(fz_make_point(q.ul.x - q.ll.x, q.ul.y - q.ll.y));
    c = fz_normalize_vector(fz_make_point(q.lr.x - q.ll.x, q.lr.y - q.ll.y));
    if (fabs(b.x * c.x + b.y * c.y) > JM_EPS)
        return 0;                                // angle at LL != 90 deg
    return 1;
}
*/

//-----------------------------------------------------------------------------
// PySequence to quad. Default: quad of (0, 0) points.
// Four floats are treated as coordinates of a rect, and its corners will
// define the quad.
//-----------------------------------------------------------------------------
fz_quad JM_quad_from_py(PyObject *r)
{
    fz_quad q;
    fz_point p[4];
    size_t i;
    q.ul = q.ur = q.ll = q.lr = fz_make_point(0,0);

    if (!r || !PySequence_Check(r) || PySequence_Size(r) != 4)
        return q;

    double x0 = PyFloat_AsDouble(PySequence_GetItem(r, 0));
    if (!PyErr_Occurred())             // assume case 1: a rect is given
    {
        double y0 = PyFloat_AsDouble(PySequence_GetItem(r, 1));
        if (PyErr_Occurred()) goto return_simple;

        double x1 = PyFloat_AsDouble(PySequence_GetItem(r, 2));
        if (PyErr_Occurred()) goto return_simple;

        double y1 = PyFloat_AsDouble(PySequence_GetItem(r, 3));
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
        PyObject *o = PySequence_GetItem(r, i);
        p[i].x = p[i].y = 0;
        if (!PySequence_Check(o) || PySequence_Size(o) != 2)
            goto weiter;

        p[i].x = PyFloat_AsDouble(PySequence_GetItem(o, 0));
        if (PyErr_Occurred())
            p[i].x = 0;

        p[i].y = PyFloat_AsDouble(PySequence_GetItem(o, 1));
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
// PySequence to rect. Default: infinite rect
//-----------------------------------------------------------------------------
fz_rect JM_rect_from_py(PyObject *r)
{
    if (!r || !PySequence_Check(r) || PySequence_Size(r) != 4)
        return fz_infinite_rect;

    double x0 = PyFloat_AsDouble(PySequence_GetItem(r, 0));
    if (PyErr_Occurred()) goto return_empty;

    double y0 = PyFloat_AsDouble(PySequence_GetItem(r, 1));
    if (PyErr_Occurred()) goto return_empty;

    double x1 = PyFloat_AsDouble(PySequence_GetItem(r, 2));
    if (PyErr_Occurred()) goto return_empty;

    double y1 = PyFloat_AsDouble(PySequence_GetItem(r, 3));
    if (PyErr_Occurred()) goto return_empty;

    return fz_make_rect((float) x0, (float) y0, (float) x1, (float) y1);

    return_empty: ;
    PyErr_Clear();
    return fz_infinite_rect;
}

//-----------------------------------------------------------------------------
// fz_rect to PySequence
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
    if (!r || !PySequence_Check(r) || PySequence_Size(r) != 4)
        return fz_infinite_irect;

    long x0 = PyLong_AsLong(PySequence_GetItem(r, 0));
    if (PyErr_Occurred()) goto return_empty;

    long y0 = PyLong_AsLong(PySequence_GetItem(r, 1));
    if (PyErr_Occurred()) goto return_empty;

    long x1 = PyLong_AsLong(PySequence_GetItem(r, 2));
    if (PyErr_Occurred()) goto return_empty;

    long y1 = PyLong_AsLong(PySequence_GetItem(r, 3));
    if (PyErr_Occurred()) goto return_empty;

    return fz_make_irect((int) x0, (int) y0, (int) x1, (int) y1);

    return_empty: ;
    PyErr_Clear();
    return fz_infinite_irect;
}

//-----------------------------------------------------------------------------
// fz_irect to PySequence
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
    fz_point p0 = {0,0};
    if (!p || !PySequence_Check(p) || PySequence_Size(p) != 2)
        return p0;

    double x = PyFloat_AsDouble(PySequence_GetItem(p, 0));
    if (PyErr_Occurred()) goto zero_point;

    double y = PyFloat_AsDouble(PySequence_GetItem(p, 1));
    if (PyErr_Occurred()) goto zero_point;

    return fz_make_point((float) x, (float) y);

    zero_point: ;
    PyErr_Clear();
    return p0;
}

//-----------------------------------------------------------------------------
// fz_point to PySequence
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

    double a = PyFloat_AsDouble(PySequence_GetItem(m, 0));
    if (PyErr_Occurred()) goto fertig;

    double b = PyFloat_AsDouble(PySequence_GetItem(m, 1));
    if (PyErr_Occurred()) goto fertig;

    double c = PyFloat_AsDouble(PySequence_GetItem(m, 2));
    if (PyErr_Occurred()) goto fertig;

    double d = PyFloat_AsDouble(PySequence_GetItem(m, 3));
    if (PyErr_Occurred()) goto fertig;

    double e = PyFloat_AsDouble(PySequence_GetItem(m, 4));
    if (PyErr_Occurred()) goto fertig;

    double f = PyFloat_AsDouble(PySequence_GetItem(m, 5));
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
// fz_matrix to PySequence
//-----------------------------------------------------------------------------
PyObject *JM_py_from_matrix(fz_matrix m)
{
    return Py_BuildValue("ffffff", m.a, m.b, m.c, m.d, m.e, m.f);
}

%}