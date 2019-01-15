%{
//-----------------------------------------------------------------------------
// Create an fz_output which writes to a Python ByteArray
//-----------------------------------------------------------------------------
PyObject *JM_output_log;
PyObject *JM_error_log;

static void
JM_WriteBarray(fz_context *ctx, PyObject *barray, const void *buffer, size_t count)
{
    if (!buffer || count < 1) return;
    PyObject *c = PyByteArray_FromStringAndSize((const char *)buffer, (Py_ssize_t) count);
    if (!c || c == NONE) return;
    PyObject *old = barray;                 // save for Py_DECREFing
    barray = PySequence_InPlaceConcat(barray, c);
    Py_DECREF(c);
    Py_DECREF(old);
    return;
}

static void
JM_SeekDummy(fz_context *ctx, void *opaque, int64_t off, int whence)
{   // ignore seeks
    return;
}

static int64_t
JM_TellBarray(fz_context *ctx, PyObject *barray)
{
    return (int64_t) PyByteArray_Size(barray);
}

fz_output *JM_OutFromBarray(fz_context *ctx, PyObject *barray)
{
    fz_output *out = fz_new_output(ctx, 0, barray, JM_WriteBarray, NULL, NULL);
    out->seek = JM_SeekDummy;
    out->tell = JM_TellBarray;
    return out;
}
%}