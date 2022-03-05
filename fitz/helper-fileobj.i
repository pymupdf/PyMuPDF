%{
//-------------------------------------
// fz_output for Python file objects
//-------------------------------------
static void
JM_bytesio_write(fz_context *ctx, void *opaque, const void *data, size_t len)
{  // bio.write(bytes object)
    PyObject *bio = opaque, *b, *name, *rc;
    fz_try(ctx){
        b = PyBytes_FromStringAndSize((const char *) data, (Py_ssize_t) len);
        name = PyUnicode_FromString("write");
        PyObject_CallMethodObjArgs(bio, name, b, NULL);
        rc = PyErr_Occurred();
        if (rc) {
            RAISEPY(ctx, "could not write to Py file obj", rc);
        }
    }
    fz_always(ctx) {
        Py_XDECREF(b);
        Py_XDECREF(name);
        Py_XDECREF(rc);
        PyErr_Clear();
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
}

static void
JM_bytesio_truncate(fz_context *ctx, void *opaque)
{  // bio.truncate(bio.tell()) !!!
    PyObject *bio = opaque, *trunc = NULL, *tell = NULL, *rctell= NULL, *rc = NULL;
    fz_try(ctx) {
        trunc = PyUnicode_FromString("truncate");
        tell = PyUnicode_FromString("tell");
        rctell = PyObject_CallMethodObjArgs(bio, tell, NULL);
        PyObject_CallMethodObjArgs(bio, trunc, rctell, NULL);
        rc = PyErr_Occurred();
        if (rc) {
            RAISEPY(ctx, "could not truncate Py file obj", rc);
        }
    }
    fz_always(ctx) {
        Py_XDECREF(tell);
        Py_XDECREF(trunc);
        Py_XDECREF(rc);
        Py_XDECREF(rctell);
        PyErr_Clear();
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
}

static int64_t
JM_bytesio_tell(fz_context *ctx, void *opaque)
{  // returns bio.tell() -> int
    PyObject *bio = opaque, *rc = NULL, *name = NULL;
    int64_t pos = 0;
    fz_try(ctx) {
        name = PyUnicode_FromString("tell");
        rc = PyObject_CallMethodObjArgs(bio, name, NULL);
        if (!rc) {
            RAISEPY(ctx, "could not tell Py file obj", PyErr_Occurred());
        }
        pos = (int64_t) PyLong_AsUnsignedLongLong(rc);
    }
    fz_always(ctx) {
        Py_XDECREF(name);
        Py_XDECREF(rc);
        PyErr_Clear();
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
    return pos;
}


static void
JM_bytesio_seek(fz_context *ctx, void *opaque, int64_t off, int whence)
{  // bio.seek(off, whence=0)
    PyObject *bio = opaque, *rc = NULL, *name = NULL, *pos = NULL;
    fz_try(ctx) {
        name = PyUnicode_FromString("seek");
        pos = PyLong_FromUnsignedLongLong((unsigned long long) off);
        PyObject_CallMethodObjArgs(bio, name, pos, whence, NULL);
        rc = PyErr_Occurred();
        if (rc) {
            RAISEPY(ctx, "could not seek Py file obj", rc);
        }
    }
    fz_always(ctx) {
        Py_XDECREF(rc);
        Py_XDECREF(name);
        Py_XDECREF(pos);
        PyErr_Clear();
    }
    fz_catch(ctx) {
        fz_rethrow(ctx);
    }
}

fz_output *
JM_new_output_fileptr(fz_context *ctx, PyObject *bio)
{
    fz_output *out = fz_new_output(ctx, 0, bio, JM_bytesio_write, NULL, NULL);
    out->seek = JM_bytesio_seek;
    out->tell = JM_bytesio_tell;
    out->truncate = JM_bytesio_truncate;
    return out;
}
%}
