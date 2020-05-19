%{

//-----------------------------------------------------------------------------
// Functions converting betwenn PySequences and fitz geometry objects
//-----------------------------------------------------------------------------
static int
JM_INT_ITEM(PyObject *obj, Py_ssize_t idx, int *result)
{
    PyObject *temp = PySequence_ITEM(obj, idx);
    if (!temp) return 1;
    *result = (int) PyLong_AsLong(temp);
    Py_DECREF(temp);
    if (PyErr_Occurred())
    {
        PyErr_Clear();
        return 1;
    }
    return 0;
}

static int
JM_FLOAT_ITEM(PyObject *obj, Py_ssize_t idx, float *result)
{
    PyObject *temp = PySequence_ITEM(obj, idx);
    if (!temp) return 1;
    *result = (float) PyFloat_AsDouble(temp);
    Py_DECREF(temp);
    if (PyErr_Occurred())
    {
        PyErr_Clear();
        return 1;
    }
    return 0;
}

//-----------------------------------------------------------------------------
// PySequence to fz_rect. Default: infinite rect
//-----------------------------------------------------------------------------
static fz_rect
JM_rect_from_py(PyObject *r)
{
    if (!r || !PySequence_Check(r) || PySequence_Size(r) != 4)
        return fz_infinite_rect;
    Py_ssize_t i;
    float f[4];

    for (i = 0; i < 4; i++)
        if (JM_FLOAT_ITEM(r, i, &f[i]) == 1) return fz_infinite_rect;

    return fz_make_rect(f[0], f[1], f[2], f[3]);
}

//-----------------------------------------------------------------------------
// PySequence from fz_rect
//-----------------------------------------------------------------------------
static PyObject *
JM_py_from_rect(fz_rect r)
{
    return Py_BuildValue("ffff", r.x0, r.y0, r.x1, r.y1);
}

//-----------------------------------------------------------------------------
// PySequence to fz_irect. Default: infinite irect
//-----------------------------------------------------------------------------
static fz_irect
JM_irect_from_py(PyObject *r)
{
    if (!PySequence_Check(r) || PySequence_Size(r) != 4)
        return fz_infinite_irect;
    int x[4];
    Py_ssize_t i;

    for (i = 0; i < 4; i++)
        if (JM_INT_ITEM(r, i, &x[i]) == 1) return fz_infinite_irect;

    return fz_make_irect(x[0], x[1], x[2], x[3]);
}

//-----------------------------------------------------------------------------
// PySequence from fz_irect
//-----------------------------------------------------------------------------
static PyObject *
JM_py_from_irect(fz_irect r)
{
    return Py_BuildValue("iiii", r.x0, r.y0, r.x1, r.y1);
}


//-----------------------------------------------------------------------------
// PySequence to fz_point. Default: (0, 0)
//-----------------------------------------------------------------------------
static fz_point
JM_point_from_py(PyObject *p)
{
    fz_point p0 = fz_make_point(0, 0);
    float x, y;

    if (!p || !PySequence_Check(p) || PySequence_Size(p) != 2)
        return p0;

    if (JM_FLOAT_ITEM(p, 0, &x) == 1) return p0;
    if (JM_FLOAT_ITEM(p, 1, &y) == 1) return p0;

    return fz_make_point(x, y);
}

//-----------------------------------------------------------------------------
// PySequence from fz_point
//-----------------------------------------------------------------------------
static PyObject *
JM_py_from_point(fz_point p)
{
    return Py_BuildValue("ff", p.x, p.y);
}


//-----------------------------------------------------------------------------
// PySequence to fz_matrix. Default: fz_identity
//-----------------------------------------------------------------------------
static fz_matrix
JM_matrix_from_py(PyObject *m)
{
    Py_ssize_t i;
    float a[6];

    if (!m || !PySequence_Check(m) || PySequence_Size(m) != 6)
        return fz_identity;

    for (i = 0; i < 6; i++)
        if (JM_FLOAT_ITEM(m, i, &a[i]) == 1) return fz_identity;

    return fz_make_matrix(a[0], a[1], a[2], a[3], a[4], a[5]);
}

//-----------------------------------------------------------------------------
// PySequence from fz_matrix
//-----------------------------------------------------------------------------
static PyObject *
JM_py_from_matrix(fz_matrix m)
{
    return Py_BuildValue("ffffff", m.a, m.b, m.c, m.d, m.e, m.f);
}

//-----------------------------------------------------------------------------
// fz_quad from PySequence. Four floats are treated as rect.
// Else must be four pairs of floats.
//-----------------------------------------------------------------------------
static fz_quad
JM_quad_from_py(PyObject *r)
{
    fz_quad q = fz_make_quad(0, 0, 0, 0, 0, 0, 0, 0);
    fz_point p[4];
    float test;
    Py_ssize_t i;
    PyObject *obj = NULL;

    if (!r || !PySequence_Check(r) || PySequence_Size(r) != 4)
        return q;

    if (JM_FLOAT_ITEM(r, 0, &test) == 0)
        return fz_quad_from_rect(JM_rect_from_py(r));

    for (i = 0; i < 4; i++)
    {
        obj = PySequence_ITEM(r, i);  // next point item
        if (!obj || !PySequence_Check(obj) || PySequence_Size(obj) != 2)
            goto exit_result;  // invalid: cancel the rest

        if (JM_FLOAT_ITEM(obj, 0, &p[i].x) == 1) goto exit_result;
        if (JM_FLOAT_ITEM(obj, 1, &p[i].y) == 1) goto exit_result;

        Py_CLEAR(obj);
    }
    q.ul = p[0];
    q.ur = p[1];
    q.ll = p[2];
    q.lr = p[3];
    return q;

    exit_result:;
    Py_CLEAR(obj);
    return q;
}

//-----------------------------------------------------------------------------
// PySequence from fz_quad.
//-----------------------------------------------------------------------------
static PyObject *
JM_py_from_quad(fz_quad quad)
{
    PyObject *pquad = PyTuple_New(4);
    PyTuple_SET_ITEM(pquad, 0, JM_py_from_point(quad.ul));
    PyTuple_SET_ITEM(pquad, 1, JM_py_from_point(quad.ur));
    PyTuple_SET_ITEM(pquad, 2, JM_py_from_point(quad.ll));
    PyTuple_SET_ITEM(pquad, 3, JM_py_from_point(quad.lr));
    return pquad;
}

%}
