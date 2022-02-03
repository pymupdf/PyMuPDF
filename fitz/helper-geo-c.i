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
//-----------------------------------------------------------------------------
// Functions converting betwenn PySequences and fitz geometry objects
//-----------------------------------------------------------------------------
static int
JM_INT_ITEM(PyObject *obj, Py_ssize_t idx, int *result)
{
    PyObject *temp = PySequence_ITEM(obj, idx);
    if (!temp) return 1;
    if (PyLong_Check(temp)) {
        *result = (int) PyLong_AsLong(temp);
        Py_DECREF(temp);
    } else if (PyFloat_Check(temp)) {
        *result = (int) PyFloat_AsDouble(temp);
        Py_DECREF(temp);
    } else {
        Py_DECREF(temp);
        return 1;
    }
    if (PyErr_Occurred()) {
        PyErr_Clear();
        return 1;
    }
    return 0;
}

static int
JM_FLOAT_ITEM(PyObject *obj, Py_ssize_t idx, double *result)
{
    PyObject *temp = PySequence_ITEM(obj, idx);
    if (!temp) return 1;
    *result = PyFloat_AsDouble(temp);
    Py_DECREF(temp);
    if (PyErr_Occurred()) {
        PyErr_Clear();
        return 1;
    }
    return 0;
}


static fz_point
JM_normalize_vector(float x, float y)
{
    double px = x, py = y, len = (double) (x * x + y * y);

    if (len != 0) {
        len = sqrt(len);
        px /= len;
        py /= len;
    }
    return fz_make_point((float) px, (float) py);
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
    double f[4];

    for (i = 0; i < 4; i++) {
        if (JM_FLOAT_ITEM(r, i, &f[i]) == 1) return fz_infinite_rect;
        if (f[i] < FZ_MIN_INF_RECT) f[i] = FZ_MIN_INF_RECT;
        if (f[i] > FZ_MAX_INF_RECT) f[i] = FZ_MAX_INF_RECT;
    }

    return fz_make_rect((float) f[0], (float) f[1], (float) f[2], (float) f[3]);
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
    if (!r || !PySequence_Check(r) || PySequence_Size(r) != 4)
        return fz_infinite_irect;
    int x[4];
    Py_ssize_t i;

    for (i = 0; i < 4; i++) {
        if (JM_INT_ITEM(r, i, &x[i]) == 1) return fz_infinite_irect;
        if (x[i] < FZ_MIN_INF_RECT) x[i] = FZ_MIN_INF_RECT;
        if (x[i] > FZ_MAX_INF_RECT) x[i] = FZ_MAX_INF_RECT;
    }

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
// PySequence to fz_point. Default: (FZ_MIN_INF_RECT, FZ_MIN_INF_RECT)
//-----------------------------------------------------------------------------
static fz_point
JM_point_from_py(PyObject *p)
{
    fz_point p0 = fz_make_point(FZ_MIN_INF_RECT, FZ_MIN_INF_RECT);
    double x, y;

    if (!p || !PySequence_Check(p) || PySequence_Size(p) != 2)
        return p0;

    if (JM_FLOAT_ITEM(p, 0, &x) == 1) return p0;
    if (JM_FLOAT_ITEM(p, 1, &y) == 1) return p0;
    if (x < FZ_MIN_INF_RECT) x = FZ_MIN_INF_RECT;
    if (y < FZ_MIN_INF_RECT) y = FZ_MIN_INF_RECT;
    if (x > FZ_MAX_INF_RECT) x = FZ_MAX_INF_RECT;
    if (y > FZ_MAX_INF_RECT) y = FZ_MAX_INF_RECT;

    return fz_make_point((float) x, (float) y);
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
    double a[6];

    if (!m || !PySequence_Check(m) || PySequence_Size(m) != 6)
        return fz_identity;

    for (i = 0; i < 6; i++)
        if (JM_FLOAT_ITEM(m, i, &a[i]) == 1) return fz_identity;

    return fz_make_matrix((float) a[0], (float) a[1], (float) a[2], (float) a[3], (float) a[4], (float) a[5]);
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
    fz_quad q = fz_make_quad(FZ_MIN_INF_RECT, FZ_MIN_INF_RECT,
                             FZ_MAX_INF_RECT, FZ_MIN_INF_RECT,
                             FZ_MIN_INF_RECT, FZ_MAX_INF_RECT,
                             FZ_MAX_INF_RECT, FZ_MAX_INF_RECT);
    fz_point p[4];
    double test, x, y;
    Py_ssize_t i;
    PyObject *obj = NULL;

    if (!r || !PySequence_Check(r) || PySequence_Size(r) != 4)
        return q;

    if (JM_FLOAT_ITEM(r, 0, &test) == 0)
        return fz_quad_from_rect(JM_rect_from_py(r));

    for (i = 0; i < 4; i++) {
        obj = PySequence_ITEM(r, i);  // next point item
        if (!obj || !PySequence_Check(obj) || PySequence_Size(obj) != 2)
            goto exit_result;  // invalid: cancel the rest

        if (JM_FLOAT_ITEM(obj, 0, &x) == 1) goto exit_result;
        if (JM_FLOAT_ITEM(obj, 1, &y) == 1) goto exit_result;
        if (x < FZ_MIN_INF_RECT) x = FZ_MIN_INF_RECT;
        if (y < FZ_MIN_INF_RECT) y = FZ_MIN_INF_RECT;
        if (x > FZ_MAX_INF_RECT) x = FZ_MAX_INF_RECT;
        if (y > FZ_MAX_INF_RECT) y = FZ_MAX_INF_RECT;
        p[i] = fz_make_point((float) x, (float) y);

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
JM_py_from_quad(fz_quad q)
{
    return Py_BuildValue("((f,f),(f,f),(f,f),(f,f))",
                          q.ul.x, q.ul.y, q.ur.x, q.ur.y,
                          q.ll.x, q.ll.y, q.lr.x, q.lr.y);
}

%}
