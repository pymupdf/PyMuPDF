'''
PyMuPDF implemented on top of MuPDF Python bindings.

License:

    SPDX-License-Identifier: GPL-3.0-only
'''

# To reduce startup times, we don't import everything we require here.
#
import atexit
import binascii
import collections
import inspect
import io
import math
import os
import pathlib
import glob
import re
import string
import sys
import tarfile
import time
import typing
import warnings
import weakref
import zipfile

from . import extra


# Set up g_out_log and g_out_message from environment variables.
#
# PYMUPDF_MESSAGE controls the destination of user messages (from function
# `pymupdf.message()`).
#
# PYMUPDF_LOG controls the destination of internal development logging (from
# function `pymupdf.log()`).
#
# For syntax, see _make_output()'s `text` arg.
#

def _make_output(
        *,
        text=None,
        fd=None,
        stream=None,
        path=None,
        path_append=None,
        pylogging=None,
        pylogging_logger=None,
        pylogging_level=None,
        pylogging_name=None,
        default=None,
        ):
    '''
    Returns a stream that writes to a specified destination, which can be a
    file descriptor, a file, an existing stream or Python's `logging' system.
    
    Args:
        text: text specification of destination.
            fd:<int> - write to file descriptor.
            path:<str> - write to file.
            path+:<str> - append to file.
            logging:<items> - write to Python `logging` module.
                items: comma-separated <name=value> pairs.
                    level=<int>
                    name=<str>.
                Other names are ignored.
        
        fd: an int file descriptor.
        stream: something with methods .write(text) and .flush().
            If specified we simply return <stream>.
        path: a file path.
            If specified we return a stream that writes to this file.
        path_append: a file path.
            If specified we return a stream that appends to this file.
        pylogging*:
            if any of these args is not None, we return a stream that writes to
            Python's `logging` module.
            
            pylogging:
                Unused other than to activate use of logging module.
            pylogging_logger:
                A logging.Logger; If None, set from <pylogging_name>.
            pylogging_level:
                An int log level, if None we use
                pylogging_logger.getEffectiveLevel().
            pylogging_name:
                Only used if <pylogging_logger> is None:
                    If <pylogging_name> is None, we set it to 'pymupdf'.
                    Then we do: pylogging_logger = logging.getLogger(pylogging_name)
    '''
    if text is not None:
        # Textual specification, for example from from environment variable.
        if text.startswith('fd:'):
            fd = int(text[3:])
        elif text.startswith('path:'):
            path = text[5:]
        elif text.startswith('path+'):
            path_append = text[5:]
        elif text.startswith('logging:'):
            pylogging = True
            items_d = dict()
            items = text[8:].split(',')
            #items_d = {n: v for (n, v) in [item.split('=', 1) for item in items]}
            for item in items:
                if not item:
                    continue
                nv = item.split('=', 1)
                assert len(nv) == 2, f'Need `=` in {item=}.'
                n, v = nv
                items_d[n] = v
            pylogging_level = items_d.get('level')
            if pylogging_level is not None:
                pylogging_level = int(pylogging_level)
            pylogging_name = items_d.get('name', 'pymupdf')
        else:
            assert 0, f'Expected prefix `fd:`, `path:`. `path+:` or `logging:` in {text=}.'
    
    if fd is not None:
        ret = open(fd, mode='w', closefd=False)
    elif stream is not None:
        assert hasattr(stream, 'write')
        assert hasattr(stream, 'flush')
        ret = stream
    elif path is not None:
        ret = open(path, 'w')
    elif path_append is not None:
        ret = open(path_append, 'a')
    elif (0
            or pylogging is not None
            or pylogging_logger is not None
            or pylogging_level is not None
            or pylogging_name is not None
            ):
        import logging
        if pylogging_logger is None:
            if pylogging_name is None:
                pylogging_name = 'pymupdf'
            pylogging_logger = logging.getLogger(pylogging_name)
        assert isinstance(pylogging_logger, logging.Logger)
        if pylogging_level is None:
            pylogging_level = pylogging_logger.getEffectiveLevel()
        class Out:
            def write(self, text):
                # `logging` module appends newlines, but so does the `print()`
                # functions in our caller message() and log() fns, so we need to
                # remove them here.
                text = text.rstrip('\n')
                if text:
                    pylogging_logger.log(pylogging_level, text)
            def flush(self):
                pass
        ret = Out()
    else:
        ret = default
    return ret

# Set steam used by PyMuPDF messaging.
_g_out_message = _make_output(text=os.environ.get('PYMUPDF_MESSAGE'), default=sys.stdout)

# Set steam used by PyMuPDF development/debugging logging.
_g_out_log = _make_output(text=os.environ.get('PYMUPDF_LOG'), default=sys.stdout)

# Things for testing logging.
_g_log_items = list()
_g_log_items_active = False

def _log_items():
    return _g_log_items

def _log_items_active(active):
    global _g_log_items_active
    _g_log_items_active = active
        
def _log_items_clear():
    del _g_log_items[:]


def set_messages(
        *,
        text=None,
        fd=None,
        stream=None,
        path=None,
        path_append=None,
        pylogging=None,
        pylogging_logger=None,
        pylogging_level=None,
        pylogging_name=None,
        ):
    '''
    Sets destination of PyMuPDF messages. See _make_output() for details.
    '''
    global _g_out_message
    _g_out_message = _make_output(
            text=text,
            fd=fd,
            stream=stream,
            path=path,
            path_append=path_append,
            pylogging=pylogging,
            pylogging_logger=pylogging_logger,
            pylogging_level=pylogging_level,
            pylogging_name=pylogging_name,
            default=_g_out_message,
            )

def set_log(
        *,
        text=None,
        fd=None,
        stream=None,
        path=None,
        path_append=None,
        pylogging=None,
        pylogging_logger=None,
        pylogging_level=None,
        pylogging_name=None,
        ):
    '''
    Sets destination of PyMuPDF development/debugging logging. See
    _make_output() for details.
    '''
    global _g_out_log
    _g_out_log = _make_output(
            text=text,
            fd=fd,
            stream=stream,
            path=path,
            path_append=path_append,
            pylogging=pylogging,
            pylogging_logger=pylogging_logger,
            pylogging_level=pylogging_level,
            pylogging_name=pylogging_name,
            default=_g_out_log,
            )

def log( text='', caller=1):
    '''
    For development/debugging diagnostics.
    '''
    try:
        stack = inspect.stack(context=0)
    except StopIteration:
        pass
    else:
        frame_record = stack[caller]
        try:
            filename = os.path.relpath(frame_record.filename)
        except Exception:   # Can fail on windows.
            filename = frame_record.filename
        line = frame_record.lineno
        function = frame_record.function
        text = f'{filename}:{line}:{function}(): {text}'
    if _g_log_items_active:
        _g_log_items.append(text)
    if _g_out_log:
        print(text, file=_g_out_log, flush=1)


def message(text=''):
    '''
    For user messages.
    '''
    # It looks like `print()` does nothing if sys.stdout is None (without
    # raising an exception), but we don't rely on this.
    if _g_out_message:
        print(text, file=_g_out_message, flush=1)


def exception_info():
    import traceback
    log(f'exception_info:')
    log(traceback.format_exc())


# PDF names must not contain these characters:
INVALID_NAME_CHARS = set(string.whitespace + "()<>[]{}/%" + chr(0))

def get_env_bool( name, default):
    '''
    Returns `True`, `False` or `default` depending on whether $<name> is '1',
    '0' or unset. Otherwise assert-fails.
    '''
    v = os.environ.get( name)
    if v is None:
        ret = default
    elif v == '1':
        ret = True
    elif v == '0':
        ret = False
    else:
        assert 0, f'Unrecognised value for {name}: {v!r}'
    if ret != default:
        log(f'Using non-default setting from {name}: {v!r}')
    return ret

def get_env_int( name, default):
    '''
    Returns `True`, `False` or `default` depending on whether $<name> is '1',
    '0' or unset. Otherwise assert-fails.
    '''
    v = os.environ.get( name)
    if v is None:
        ret = default
    else:
        ret = int(v)
    if ret != default:
        log(f'Using non-default setting from {name}: {v}')
    return ret

# All our `except ...` blocks output diagnostics if `g_exceptions_verbose` is
# true.
g_exceptions_verbose = get_env_int( 'PYMUPDF_EXCEPTIONS_VERBOSE', 1)

# $PYMUPDF_USE_EXTRA overrides whether to use optimised C fns in `extra`.
#
g_use_extra = get_env_bool( 'PYMUPDF_USE_EXTRA', True)


# Global switches
#

class _Globals:
    def __init__(self):
        self.no_device_caching = 0
        self.small_glyph_heights = 0
        self.subset_fontnames = 0
        self.skip_quad_corrections = 0

_globals = _Globals()


# Optionally use MuPDF via cppyy bindings; experimental and not tested recently
# as of 2023-01-20 11:51:40
#
mupdf_cppyy = os.environ.get( 'MUPDF_CPPYY')
if mupdf_cppyy is not None:
    # pylint: disable=all
    log( f'{__file__}: $MUPDF_CPPYY={mupdf_cppyy!r} so attempting to import mupdf_cppyy.')
    log( f'{__file__}: $PYTHONPATH={os.environ["PYTHONPATH"]}')
    if mupdf_cppyy == '':
        import mupdf_cppyy
    else:
        import importlib
        mupdf_cppyy = importlib.machinery.SourceFileLoader(
                'mupdf_cppyy',
                mupdf_cppyy
                ).load_module()
    mupdf = mupdf_cppyy.cppyy.gbl.mupdf
else:
    # Use MuPDF Python SWIG bindings. We allow import from either our own
    # directory for conventional wheel installs, or from separate place in case
    # we are using a separately-installed system installation of mupdf.
    #
    try:
        from . import mupdf
    except Exception:
        import mupdf
    mupdf.reinit_singlethreaded()

def _int_rc(text):
    '''
    Converts string to int, ignoring trailing 'rc...'.
    '''
    rc = text.find('rc')
    if rc >= 0:
        text = text[:rc]
    return int(text)

# Basic version information.
#
pymupdf_version = "1.25.2"
mupdf_version = mupdf.FZ_VERSION
pymupdf_date = "2025-01-17 00:00:01"

# Versions as tuples; useful when comparing versions.
#
pymupdf_version_tuple = tuple( [_int_rc(i) for i in pymupdf_version.split('.')])
mupdf_version_tuple = tuple( [_int_rc(i) for i in mupdf_version.split('.')])

assert mupdf_version_tuple == (mupdf.FZ_VERSION_MAJOR, mupdf.FZ_VERSION_MINOR, mupdf.FZ_VERSION_PATCH), \
        f'Inconsistent MuPDF version numbers: {mupdf_version_tuple=} != {(mupdf.FZ_VERSION_MAJOR, mupdf.FZ_VERSION_MINOR, mupdf.FZ_VERSION_PATCH)=}'

# Legacy version information.
#
pymupdf_date2 = pymupdf_date.replace('-', '').replace(' ', '').replace(':', '')
version = (pymupdf_version, mupdf_version, pymupdf_date2)
VersionFitz = mupdf_version
VersionBind = pymupdf_version
VersionDate = pymupdf_date


# String formatting.

def _format_g(value, *, fmt='%g'):
    '''
    Returns `value` formatted with mupdf.fz_format_double() if available,
    otherwise with Python's `%`.

    If `value` is a list or tuple, we return a space-separated string of
    formatted values.
    '''
    if isinstance(value, (list, tuple)):
        ret = ''
        for v in value:
            if ret:
                ret += ' '
            ret += _format_g(v, fmt=fmt)
        return ret
    else:
        if mupdf_version_tuple >= (1, 24, 2):
            return mupdf.fz_format_double(fmt, value)
        else:
            return fmt % value
        
format_g = _format_g

# Names required by class method typing annotations.
OptBytes = typing.Optional[typing.ByteString]
OptDict = typing.Optional[dict]
OptFloat = typing.Optional[float]
OptInt = typing.Union[int, None]
OptSeq = typing.Optional[typing.Sequence]
OptStr = typing.Optional[str]

Page = 'Page_forward_decl'
Point = 'Point_forward_decl'

matrix_like = 'matrix_like'
point_like = 'point_like'
quad_like = 'quad_like'
rect_like = 'rect_like'


def _as_fz_document(document):
    '''
    Returns document as a mupdf.FzDocument, upcasting as required. Raises
    'document closed' exception if closed.
    '''
    if isinstance(document, Document):
        if document.is_closed:
            raise ValueError('document closed')
        document = document.this
    if isinstance(document, mupdf.FzDocument):
        return document
    elif isinstance(document, mupdf.PdfDocument):
        return document.super()
    elif document is None:
        assert 0, f'document is None'
    else:
        assert 0, f'Unrecognised {type(document)=}'

def _as_pdf_document(document, required=True):
    '''
    Returns `document` downcast to a mupdf.PdfDocument. If downcast fails (i.e.
    `document` is not actually a `PdfDocument`) then we assert-fail if `required`
    is true (the default) else return a `mupdf.PdfDocument` with `.m_internal`
    false.
    '''
    if isinstance(document, Document):
        if document.is_closed:
            raise ValueError('document closed')
        document = document.this
    if isinstance(document, mupdf.PdfDocument):
        return document
    elif isinstance(document, mupdf.FzDocument):
        ret = mupdf.PdfDocument(document)
        if required:
            assert ret.m_internal
        return ret
    elif document is None:
        assert 0, f'document is None'
    else:
        assert 0, f'Unrecognised {type(document)=}'

def _as_fz_page(page):
    '''
    Returns page as a mupdf.FzPage, upcasting as required.
    '''
    if isinstance(page, Page):
        page = page.this
    if isinstance(page, mupdf.PdfPage):
        return page.super()
    elif isinstance(page, mupdf.FzPage):
        return page
    elif page is None:
        assert 0, f'page is None'
    else:
        assert 0, f'Unrecognised {type(page)=}'

def _as_pdf_page(page, required=True):
    '''
    Returns `page` downcast to a mupdf.PdfPage. If downcast fails (i.e. `page`
    is not actually a `PdfPage`) then we assert-fail if `required` is true (the
    default) else return a `mupdf.PdfPage` with `.m_internal` false.
    '''
    if isinstance(page, Page):
        page = page.this
    if isinstance(page, mupdf.PdfPage):
        return page
    elif isinstance(page, mupdf.FzPage):
        ret = mupdf.pdf_page_from_fz_page(page)
        if required:
            assert ret.m_internal
        return ret
    elif page is None:
        assert 0, f'page is None'
    else:
        assert 0, f'Unrecognised {type(page)=}'


def _pdf_annot_page(annot):
    '''
    Wrapper for mupdf.pdf_annot_page() which raises an exception if <annot>
    is not bound to a page instead of returning a mupdf.PdfPage with
    `.m_internal=None`.

    [Some other MuPDF functions such as pdf_update_annot()` already raise a
    similar exception if a pdf_annot's .page field is null.]
    '''
    page = mupdf.pdf_annot_page(annot)
    if not page.m_internal:
        raise RuntimeError('Annot is not bound to a page')
    return page


# Fixme: we don't support JM_MEMORY=1.
JM_MEMORY = 0

# Classes
#

class Annot:

    def __init__(self, annot):
        assert isinstance( annot, mupdf.PdfAnnot)
        self.this = annot

    def __repr__(self):
        parent = getattr(self, 'parent', '<>')
        return "'%s' annotation on %s" % (self.type[1], str(parent))

    def __str__(self):
        return self.__repr__()

    def _erase(self):
        if getattr(self, "thisown", False):
            self.thisown = False

    def _get_redact_values(self):
        annot = self.this
        if mupdf.pdf_annot_type(annot) != mupdf.PDF_ANNOT_REDACT:
            return

        values = dict()
        try:
            obj = mupdf.pdf_dict_gets(mupdf.pdf_annot_obj(annot), "RO")
            if obj.m_internal:
                message_warning("Ignoring redaction key '/RO'.")
                xref = mupdf.pdf_to_num(obj)
                values[dictkey_xref] = xref
            obj = mupdf.pdf_dict_gets(mupdf.pdf_annot_obj(annot), "OverlayText")
            if obj.m_internal:
                text = mupdf.pdf_to_text_string(obj)
                values[dictkey_text] = JM_UnicodeFromStr(text)
            else:
                values[dictkey_text] = ''
            obj = mupdf.pdf_dict_get(mupdf.pdf_annot_obj(annot), PDF_NAME('Q'))
            align = 0
            if obj.m_internal:
                align = mupdf.pdf_to_int(obj)
            values[dictkey_align] = align
        except Exception:
            if g_exceptions_verbose:    exception_info()
            return
        val = values

        if not val:
            return val
        val["rect"] = self.rect
        text_color, fontname, fontsize = TOOLS._parse_da(self)
        val["text_color"] = text_color
        val["fontname"] = fontname
        val["fontsize"] = fontsize
        fill = self.colors["fill"]
        val["fill"] = fill
        return val

    def _getAP(self):
        if g_use_extra:
            assert isinstance( self.this, mupdf.PdfAnnot)
            ret = extra.Annot_getAP(self.this)
            assert isinstance( ret, bytes)
            return ret
        else:
            r = None
            res = None
            annot = self.this
            assert isinstance( annot, mupdf.PdfAnnot)
            annot_obj = mupdf.pdf_annot_obj( annot)
            ap = mupdf.pdf_dict_getl( annot_obj, PDF_NAME('AP'), PDF_NAME('N'))
            if mupdf.pdf_is_stream( ap):
                res = mupdf.pdf_load_stream( ap)
            if res and res.m_internal:
                r = JM_BinFromBuffer(res)
            return r

    def _setAP(self, buffer_, rect=0):
        try:
            annot = self.this
            annot_obj = mupdf.pdf_annot_obj( annot)
            page = _pdf_annot_page(annot)
            apobj = mupdf.pdf_dict_getl( annot_obj, PDF_NAME('AP'), PDF_NAME('N'))
            if not apobj.m_internal:
                raise RuntimeError( MSG_BAD_APN)
            if not mupdf.pdf_is_stream( apobj):
                raise RuntimeError( MSG_BAD_APN)
            res = JM_BufferFromBytes( buffer_)
            if not res.m_internal:
                raise ValueError( MSG_BAD_BUFFER)
            JM_update_stream( page.doc(), apobj, res, 1)
            if rect:
                bbox = mupdf.pdf_dict_get_rect( annot_obj, PDF_NAME('Rect'))
                mupdf.pdf_dict_put_rect( apobj, PDF_NAME('BBox'), bbox)
        except Exception:
            if g_exceptions_verbose:    exception_info()

    def _update_appearance(self, opacity=-1, blend_mode=None, fill_color=None, rotate=-1):
        annot = self.this
        assert annot.m_internal
        annot_obj = mupdf.pdf_annot_obj( annot)
        page = _pdf_annot_page(annot)
        pdf = page.doc()
        type_ = mupdf.pdf_annot_type( annot)
        nfcol, fcol = JM_color_FromSequence(fill_color)

        try:
            # remove fill color from unsupported annots
            # or if so requested
            if nfcol == 0 or type_ not in (
                    mupdf.PDF_ANNOT_SQUARE,
                    mupdf.PDF_ANNOT_CIRCLE,
                    mupdf.PDF_ANNOT_LINE,
                    mupdf.PDF_ANNOT_POLY_LINE,
                    mupdf.PDF_ANNOT_POLYGON
                    ):
                mupdf.pdf_dict_del( annot_obj, PDF_NAME('IC'))
            elif nfcol > 0:
                mupdf.pdf_set_annot_interior_color( annot, fcol[:nfcol])

            insert_rot = 1 if rotate >= 0 else 0
            if type_ not in (
                    mupdf.PDF_ANNOT_CARET,
                    mupdf.PDF_ANNOT_CIRCLE,
                    mupdf.PDF_ANNOT_FREE_TEXT,
                    mupdf.PDF_ANNOT_FILE_ATTACHMENT,
                    mupdf.PDF_ANNOT_INK,
                    mupdf.PDF_ANNOT_LINE,
                    mupdf.PDF_ANNOT_POLY_LINE,
                    mupdf.PDF_ANNOT_POLYGON,
                    mupdf.PDF_ANNOT_SQUARE,
                    mupdf.PDF_ANNOT_STAMP,
                    mupdf.PDF_ANNOT_TEXT,
                    ):
                insert_rot = 0

            if insert_rot:
                mupdf.pdf_dict_put_int( annot_obj, PDF_NAME('Rotate'), rotate)

            mupdf.pdf_dirty_annot( annot)
            mupdf.pdf_update_annot( annot) # let MuPDF update
            pdf.resynth_required = 0
            # insert fill color
            if type_ == mupdf.PDF_ANNOT_FREE_TEXT:
                if nfcol > 0:
                    mupdf.pdf_set_annot_color( annot, fcol[:nfcol])
            elif nfcol > 0:
                col = mupdf.pdf_new_array( page.doc(), nfcol)
                for i in range( nfcol):
                    mupdf.pdf_array_push_real( col, fcol[i])
                mupdf.pdf_dict_put( annot_obj, PDF_NAME('IC'), col)
        except Exception as e:
            if g_exceptions_verbose:    exception_info()
            message( f'cannot update annot: {e}')
            raise
        
        if (opacity < 0 or opacity >= 1) and not blend_mode:    # no opacity, no blend_mode
            return True

        try:    # create or update /ExtGState
            ap = mupdf.pdf_dict_getl(
                    mupdf.pdf_annot_obj(annot),
                    PDF_NAME('AP'),
                    PDF_NAME('N')
                    )
            if not ap.m_internal:   # should never happen
                raise RuntimeError( MSG_BAD_APN)

            resources = mupdf.pdf_dict_get( ap, PDF_NAME('Resources'))
            if not resources.m_internal:    # no Resources yet: make one
                resources = mupdf.pdf_dict_put_dict( ap, PDF_NAME('Resources'), 2)
            
            alp0 = mupdf.pdf_new_dict( page.doc(), 3)
            if opacity >= 0 and opacity < 1:
                mupdf.pdf_dict_put_real( alp0, PDF_NAME('CA'), opacity)
                mupdf.pdf_dict_put_real( alp0, PDF_NAME('ca'), opacity)
                mupdf.pdf_dict_put_real( annot_obj, PDF_NAME('CA'), opacity)

            if blend_mode:
                mupdf.pdf_dict_put_name( alp0, PDF_NAME('BM'), blend_mode)
                mupdf.pdf_dict_put_name( annot_obj, PDF_NAME('BM'), blend_mode)

            extg = mupdf.pdf_dict_get( resources, PDF_NAME('ExtGState'))
            if not extg.m_internal: # no ExtGState yet: make one
                extg = mupdf.pdf_dict_put_dict( resources, PDF_NAME('ExtGState'), 2)

            mupdf.pdf_dict_put( extg, PDF_NAME('H'), alp0)

        except Exception as e:
            if g_exceptions_verbose:    exception_info()
            message( f'cannot set opacity or blend mode\n: {e}')
            raise

        return True

    @property
    def apn_bbox(self):
        """annotation appearance bbox"""
        CheckParent(self)
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj(annot)
        ap = mupdf.pdf_dict_getl(annot_obj, PDF_NAME('AP'), PDF_NAME('N'))
        if not ap.m_internal:
            val = JM_py_from_rect(mupdf.FzRect(mupdf.FzRect.Fixed_INFINITE))
        else:
            rect = mupdf.pdf_dict_get_rect(ap, PDF_NAME('BBox'))
            val = JM_py_from_rect(rect)

        val = Rect(val) * self.get_parent().transformation_matrix
        val *= self.get_parent().derotation_matrix
        return val

    @property
    def apn_matrix(self):
        """annotation appearance matrix"""
        try:
            CheckParent(self)
            annot = self.this
            assert isinstance(annot, mupdf.PdfAnnot)
            ap = mupdf.pdf_dict_getl(
                    mupdf.pdf_annot_obj(annot),
                    mupdf.PDF_ENUM_NAME_AP,
                    mupdf.PDF_ENUM_NAME_N
                    )
            if not ap.m_internal:
                return JM_py_from_matrix(mupdf.FzMatrix())
            mat = mupdf.pdf_dict_get_matrix(ap, mupdf.PDF_ENUM_NAME_Matrix)
            val = JM_py_from_matrix(mat)

            val = Matrix(val)

            return val
        except Exception:
            if g_exceptions_verbose:    exception_info()
            raise

    @property
    def blendmode(self):
        """annotation BlendMode"""
        CheckParent(self)
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj(annot)
        obj = mupdf.pdf_dict_get(annot_obj, PDF_NAME('BM'))
        blend_mode = None
        if obj.m_internal:
            blend_mode = JM_UnicodeFromStr(mupdf.pdf_to_name(obj))
            return blend_mode
        # loop through the /AP/N/Resources/ExtGState objects
        obj = mupdf.pdf_dict_getl(
                annot_obj,
                PDF_NAME('AP'),
                PDF_NAME('N'),
                PDF_NAME('Resources'),
                PDF_NAME('ExtGState'),
                )
        if mupdf.pdf_is_dict(obj):
            n = mupdf.pdf_dict_len(obj)
            for i in range(n):
                obj1 = mupdf.pdf_dict_get_val(obj, i)
                if mupdf.pdf_is_dict(obj1):
                    m = mupdf.pdf_dict_len(obj1)
                    for j in range(m):
                        obj2 = mupdf.pdf_dict_get_key(obj1, j)
                        if mupdf.pdf_objcmp(obj2, PDF_NAME('BM')) == 0:
                            blend_mode = JM_UnicodeFromStr(mupdf.pdf_to_name(mupdf.pdf_dict_get_val(obj1, j)))
                            return blend_mode
        return blend_mode

    @property
    def border(self):
        """Border information."""
        CheckParent(self)
        atype = self.type[0]
        if atype not in (
                mupdf.PDF_ANNOT_CIRCLE,
                mupdf.PDF_ANNOT_FREE_TEXT,
                mupdf.PDF_ANNOT_INK,
                mupdf.PDF_ANNOT_LINE,
                mupdf.PDF_ANNOT_POLY_LINE,
                mupdf.PDF_ANNOT_POLYGON,
                mupdf.PDF_ANNOT_SQUARE,
                ):
            return dict()
        ao = mupdf.pdf_annot_obj(self.this)
        ret = JM_annot_border(ao)
        return ret

    def clean_contents(self, sanitize=1):
        """Clean appearance contents stream."""
        CheckParent(self)
        annot = self.this
        pdf = mupdf.pdf_get_bound_document(mupdf.pdf_annot_obj(annot))
        filter_ = _make_PdfFilterOptions(recurse=1, instance_forms=0, ascii=0, sanitize=sanitize)
        mupdf.pdf_filter_annot_contents(pdf, annot, filter_)

    @property
    def colors(self):
        """Color definitions."""
        try:
            CheckParent(self)
            annot = self.this
            assert isinstance(annot, mupdf.PdfAnnot)
            return JM_annot_colors(mupdf.pdf_annot_obj(annot))
        except Exception:
            if g_exceptions_verbose:    exception_info()
            raise

    def delete_responses(self):
        """Delete 'Popup' and responding annotations."""
        CheckParent(self)
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj(annot)
        page = _pdf_annot_page(annot)
        while 1:
            irt_annot = JM_find_annot_irt(annot)
            if not irt_annot.m_internal:
                break
            mupdf.pdf_delete_annot(page, irt_annot)
        mupdf.pdf_dict_del(annot_obj, PDF_NAME('Popup'))

        annots = mupdf.pdf_dict_get(page.obj(), PDF_NAME('Annots'))
        n = mupdf.pdf_array_len(annots)
        found = 0
        for i in range(n-1, -1, -1):
            o = mupdf.pdf_array_get(annots, i)
            p = mupdf.pdf_dict_get(o, PDF_NAME('Parent'))
            if not o.m_internal:
                continue
            if not mupdf.pdf_objcmp(p, annot_obj):
                mupdf.pdf_array_delete(annots, i)
                found = 1
        if found:
            mupdf.pdf_dict_put(page.obj(), PDF_NAME('Annots'), annots)

    @property
    def file_info(self):
        """Attached file information."""
        CheckParent(self)
        res = dict()
        length = -1
        size = -1
        desc = None
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj(annot)
        type_ = mupdf.pdf_annot_type(annot)
        if type_ != mupdf.PDF_ANNOT_FILE_ATTACHMENT:
            raise TypeError( MSG_BAD_ANNOT_TYPE)
        stream = mupdf.pdf_dict_getl(
                annot_obj,
                PDF_NAME('FS'),
                PDF_NAME('EF'),
                PDF_NAME('F'),
                )
        if not stream.m_internal:
            RAISEPY( "bad PDF: file entry not found", JM_Exc_FileDataError)

        fs = mupdf.pdf_dict_get(annot_obj, PDF_NAME('FS'))

        o = mupdf.pdf_dict_get(fs, PDF_NAME('UF'))
        if o.m_internal:
            filename = mupdf.pdf_to_text_string(o)
        else:
            o = mupdf.pdf_dict_get(fs, PDF_NAME('F'))
            if o.m_internal:
                filename = mupdf.pdf_to_text_string(o)

        o = mupdf.pdf_dict_get(fs, PDF_NAME('Desc'))
        if o.m_internal:
            desc = mupdf.pdf_to_text_string(o)

        o = mupdf.pdf_dict_get(stream, PDF_NAME('Length'))
        if o.m_internal:
            length = mupdf.pdf_to_int(o)

        o = mupdf.pdf_dict_getl(stream, PDF_NAME('Params'), PDF_NAME('Size'))
        if o.m_internal:
            size = mupdf.pdf_to_int(o)

        res[ dictkey_filename] = JM_EscapeStrFromStr(filename)
        res[ dictkey_descr] = JM_UnicodeFromStr(desc)
        res[ dictkey_length] = length
        res[ dictkey_size] = size
        return res

    @property
    def flags(self):
        """Flags field."""
        CheckParent(self)
        annot = self.this
        return mupdf.pdf_annot_flags(annot)

    def get_file(self):
        """Retrieve attached file content."""
        CheckParent(self)
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj(annot)
        type = mupdf.pdf_annot_type(annot)
        if type != mupdf.PDF_ANNOT_FILE_ATTACHMENT:
            raise TypeError( MSG_BAD_ANNOT_TYPE)
        stream = mupdf.pdf_dict_getl(annot_obj, PDF_NAME('FS'), PDF_NAME('EF'), PDF_NAME('F'))
        if not stream.m_internal:
            RAISEPY( "bad PDF: file entry not found", JM_Exc_FileDataError)
        buf = mupdf.pdf_load_stream(stream)
        res = JM_BinFromBuffer(buf)
        return res

    def get_oc(self):
        """Get annotation optional content reference."""
        CheckParent(self)
        oc = 0
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj(annot)
        obj = mupdf.pdf_dict_get(annot_obj, PDF_NAME('OC'))
        if obj.m_internal:
            oc = mupdf.pdf_to_num(obj)
        return oc

    # PyMuPDF doesn't seem to have this .parent member, but removing it breaks
    # 11 tests...?
    #@property
    def get_parent(self):
        try:
            ret = getattr( self, 'parent')
        except AttributeError:
            page = _pdf_annot_page(self.this)
            assert isinstance( page, mupdf.PdfPage)
            document = Document( page.doc()) if page.m_internal else None
            ret = Page(page, document)
            #self.parent = weakref.proxy( ret)
            self.parent = ret
            #log(f'No attribute .parent: {type(self)=} {id(self)=}: have set {id(self.parent)=}.')
            #log( f'Have set self.parent')
        return ret

    def get_pixmap(self, matrix=None, dpi=None, colorspace=None, alpha=0):
        """annotation Pixmap"""

        CheckParent(self)
        cspaces = {"gray": csGRAY, "rgb": csRGB, "cmyk": csCMYK}
        if type(colorspace) is str:
            colorspace = cspaces.get(colorspace.lower(), None)
        if dpi:
            matrix = Matrix(dpi / 72, dpi / 72)
        ctm = JM_matrix_from_py(matrix)
        cs = colorspace
        if not cs:
            cs = mupdf.fz_device_rgb()

        pix = mupdf.pdf_new_pixmap_from_annot(self.this, ctm, cs, mupdf.FzSeparations(0), alpha)
        ret = Pixmap(pix)
        if dpi:
            ret.set_dpi(dpi, dpi)
        return ret

    def get_sound(self):
        """Retrieve sound stream."""
        CheckParent(self)
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj(annot)
        type = mupdf.pdf_annot_type(annot)
        sound = mupdf.pdf_dict_get(annot_obj, PDF_NAME('Sound'))
        if type != mupdf.PDF_ANNOT_SOUND or not sound.m_internal:
            raise TypeError( MSG_BAD_ANNOT_TYPE)
        if mupdf.pdf_dict_get(sound, PDF_NAME('F')).m_internal:
            RAISEPY( "unsupported sound stream", JM_Exc_FileDataError)
        res = dict()
        obj = mupdf.pdf_dict_get(sound, PDF_NAME('R'))
        if obj.m_internal:
            res['rate'] = mupdf.pdf_to_real(obj)
        obj = mupdf.pdf_dict_get(sound, PDF_NAME('C'))
        if obj.m_internal:
            res['channels'] = mupdf.pdf_to_int(obj)
        obj = mupdf.pdf_dict_get(sound, PDF_NAME('B'))
        if obj.m_internal:
            res['bps'] = mupdf.pdf_to_int(obj)
        obj = mupdf.pdf_dict_get(sound, PDF_NAME('E'))
        if obj.m_internal:
            res['encoding'] = mupdf.pdf_to_name(obj)
        obj = mupdf.pdf_dict_gets(sound, "CO")
        if obj.m_internal:
            res['compression'] = mupdf.pdf_to_name(obj)
        buf = mupdf.pdf_load_stream(sound)
        stream = JM_BinFromBuffer(buf)
        res['stream'] = stream
        return res

    def get_textpage(self, clip=None, flags=0):
        """Make annotation TextPage."""
        CheckParent(self)
        options = mupdf.FzStextOptions()
        options.flags = flags
        annot = self.this
        stextpage = mupdf.FzStextPage(annot, options)
        ret = TextPage(stextpage)
        p = self.get_parent()
        if isinstance(p, weakref.ProxyType):
            ret.parent = p
        else:
            ret.parent = weakref.proxy(p)
        return ret

    @property
    def has_popup(self):
        """Check if annotation has a Popup."""
        CheckParent(self)
        annot = self.this
        obj = mupdf.pdf_dict_get(mupdf.pdf_annot_obj(annot), PDF_NAME('Popup'))
        return True if obj.m_internal else False

    @property
    def info(self):
        """Various information details."""
        CheckParent(self)
        annot = self.this
        res = dict()

        res[dictkey_content] = JM_UnicodeFromStr(mupdf.pdf_annot_contents(annot))

        o = mupdf.pdf_dict_get(mupdf.pdf_annot_obj(annot), PDF_NAME('Name'))
        res[dictkey_name] = JM_UnicodeFromStr(mupdf.pdf_to_name(o))

        # Title (= author)
        o = mupdf.pdf_dict_get(mupdf.pdf_annot_obj(annot), PDF_NAME('T'))
        res[dictkey_title] = JM_UnicodeFromStr(mupdf.pdf_to_text_string(o))

        # CreationDate
        o = mupdf.pdf_dict_gets(mupdf.pdf_annot_obj(annot), "CreationDate")
        res[dictkey_creationDate] = JM_UnicodeFromStr(mupdf.pdf_to_text_string(o))

        # ModDate
        o = mupdf.pdf_dict_get(mupdf.pdf_annot_obj(annot), PDF_NAME('M'))
        res[dictkey_modDate] = JM_UnicodeFromStr(mupdf.pdf_to_text_string(o))

        # Subj
        o = mupdf.pdf_dict_gets(mupdf.pdf_annot_obj(annot), "Subj")
        res[dictkey_subject] = mupdf.pdf_to_text_string(o)

        # Identification (PDF key /NM)
        o = mupdf.pdf_dict_gets(mupdf.pdf_annot_obj(annot), "NM")
        res[dictkey_id] = JM_UnicodeFromStr(mupdf.pdf_to_text_string(o))

        return res

    @property
    def irt_xref(self):
        '''
        annotation IRT xref
        '''
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj( annot)
        irt = mupdf.pdf_dict_get( annot_obj, PDF_NAME('IRT'))
        if not irt.m_internal:
            return 0
        return mupdf.pdf_to_num( irt)

    @property
    def is_open(self):
        """Get 'open' status of annotation or its Popup."""
        CheckParent(self)
        return mupdf.pdf_annot_is_open(self.this)

    @property
    def language(self):
        """annotation language"""
        this_annot = self.this
        lang = mupdf.pdf_annot_language(this_annot)
        if lang == mupdf.FZ_LANG_UNSET:
            return
        assert hasattr(mupdf, 'fz_string_from_text_language2')
        return mupdf.fz_string_from_text_language2(lang)

    @property
    def line_ends(self):
        """Line end codes."""
        CheckParent(self)
        annot = self.this
        # return nothing for invalid annot types
        if not mupdf.pdf_annot_has_line_ending_styles(annot):
            return
        lstart = mupdf.pdf_annot_line_start_style(annot)
        lend = mupdf.pdf_annot_line_end_style(annot)
        return lstart, lend

    @property
    def next(self):
        """Next annotation."""
        CheckParent(self)
        this_annot = self.this
        assert isinstance(this_annot, mupdf.PdfAnnot)
        assert this_annot.m_internal
        type_ = mupdf.pdf_annot_type(this_annot)
        if type_ != mupdf.PDF_ANNOT_WIDGET:
            annot = mupdf.pdf_next_annot(this_annot)
        else:
            annot = mupdf.pdf_next_widget(this_annot)

        val = Annot(annot) if annot.m_internal else None
        if not val:
            return None
        val.thisown = True
        assert val.get_parent().this.m_internal_value() == self.get_parent().this.m_internal_value()
        val.parent._annot_refs[id(val)] = val

        if val.type[0] == mupdf.PDF_ANNOT_WIDGET:
            widget = Widget()
            TOOLS._fill_widget(val, widget)
            val = widget
        return val

    @property
    def opacity(self):
        """Opacity."""
        CheckParent(self)
        annot = self.this
        opy = -1
        ca = mupdf.pdf_dict_get( mupdf.pdf_annot_obj(annot), mupdf.PDF_ENUM_NAME_CA)
        if mupdf.pdf_is_number(ca):
            opy = mupdf.pdf_to_real(ca)
        return opy

    @property
    def popup_rect(self):
        """annotation 'Popup' rectangle"""
        CheckParent(self)
        rect = mupdf.FzRect(mupdf.FzRect.Fixed_INFINITE)
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj( annot)
        obj = mupdf.pdf_dict_get( annot_obj, PDF_NAME('Popup'))
        if obj.m_internal:
            rect = mupdf.pdf_dict_get_rect(obj, PDF_NAME('Rect'))
            #log( '{rect=}')
        val = JM_py_from_rect(rect)
        #log( '{val=}')
        
        val = Rect(val) * self.get_parent().transformation_matrix
        val *= self.get_parent().derotation_matrix
        
        return val

    @property
    def popup_xref(self):
        """annotation 'Popup' xref"""
        CheckParent(self)
        xref = 0
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj(annot)
        obj = mupdf.pdf_dict_get(annot_obj, PDF_NAME('Popup'))
        if obj.m_internal:
            xref = mupdf.pdf_to_num(obj)
        return xref

    @property
    def rect(self):
        """annotation rectangle"""
        if g_use_extra:
            val = extra.Annot_rect3( self.this)
        else:
            val = mupdf.pdf_bound_annot(self.this)
        val = Rect(val)
        
        # Caching self.parent_() reduces 1000x from 0.07 to 0.04.
        #
        p = self.get_parent()
        #p = getattr( self, 'parent', None)
        #if p is None:
        #    p = self.parent
        #    self.parent = p
        #p = self.parent_()
        val *= p.derotation_matrix
        return val

    @property
    def rect_delta(self):
        '''
        annotation delta values to rectangle
        '''
        annot_obj = mupdf.pdf_annot_obj(self.this)
        arr = mupdf.pdf_dict_get( annot_obj, PDF_NAME('RD'))
        if mupdf.pdf_array_len( arr) == 4:
            return (
                    mupdf.pdf_to_real( mupdf.pdf_array_get( arr, 0)),
                    mupdf.pdf_to_real( mupdf.pdf_array_get( arr, 1)),
                    -mupdf.pdf_to_real( mupdf.pdf_array_get( arr, 2)),
                    -mupdf.pdf_to_real( mupdf.pdf_array_get( arr, 3)),
                    )

    @property
    def rotation(self):
        """annotation rotation"""
        CheckParent(self)
        annot = self.this
        rotation = mupdf.pdf_dict_get( mupdf.pdf_annot_obj(annot), mupdf.PDF_ENUM_NAME_Rotate)
        if not rotation.m_internal:
            return -1
        return mupdf.pdf_to_int( rotation)

    def set_apn_bbox(self, bbox):
        """
        Set annotation appearance bbox.
        """
        CheckParent(self)
        page = self.get_parent()
        rot = page.rotation_matrix
        mat = page.transformation_matrix
        bbox *= rot * ~mat
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj(annot)
        ap = mupdf.pdf_dict_getl(annot_obj, PDF_NAME('AP'), PDF_NAME('N'))
        if not ap.m_internal:
            raise RuntimeError( MSG_BAD_APN)
        rect = JM_rect_from_py(bbox)
        mupdf.pdf_dict_put_rect(ap, PDF_NAME('BBox'), rect)

    def set_apn_matrix(self, matrix):
        """Set annotation appearance matrix."""
        CheckParent(self)
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj(annot)
        ap = mupdf.pdf_dict_getl(annot_obj, PDF_NAME('AP'), PDF_NAME('N'))
        if not ap.m_internal:
            raise RuntimeError( MSG_BAD_APN)
        mat = JM_matrix_from_py(matrix)
        mupdf.pdf_dict_put_matrix(ap, PDF_NAME('Matrix'), mat)

    def set_blendmode(self, blend_mode):
        """Set annotation BlendMode."""
        CheckParent(self)
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj(annot)
        mupdf.pdf_dict_put_name(annot_obj, PDF_NAME('BM'), blend_mode)

    def set_border(self, border=None, width=-1, style=None, dashes=None, clouds=-1):
        """Set border properties.

        Either a dict, or direct arguments width, style, dashes or clouds."""
        CheckParent(self)
        atype, atname = self.type[:2]  # annotation type
        if atype not in (
                mupdf.PDF_ANNOT_CIRCLE,
                mupdf.PDF_ANNOT_FREE_TEXT,
                mupdf.PDF_ANNOT_INK,
                mupdf.PDF_ANNOT_LINE,
                mupdf.PDF_ANNOT_POLY_LINE,
                mupdf.PDF_ANNOT_POLYGON,
                mupdf.PDF_ANNOT_SQUARE,
                ):
            message(f"Cannot set border for '{atname}'.")
            return None
        if atype not in (
                mupdf.PDF_ANNOT_CIRCLE,
                mupdf.PDF_ANNOT_FREE_TEXT,
                mupdf.PDF_ANNOT_POLYGON,
                mupdf.PDF_ANNOT_SQUARE,
                ):
            if clouds > 0:
                message(f"Cannot set cloudy border for '{atname}'.")
                clouds = -1  # do not set border effect
        if type(border) is not dict:
            border = {"width": width, "style": style, "dashes": dashes, "clouds": clouds}
        border.setdefault("width", -1)
        border.setdefault("style", None)
        border.setdefault("dashes", None)
        border.setdefault("clouds", -1)
        if border["width"] is None:
            border["width"] = -1
        if border["clouds"] is None:
            border["clouds"] = -1
        if hasattr(border["dashes"], "__getitem__"):  # ensure sequence items are integers
            border["dashes"] = tuple(border["dashes"])
            for item in border["dashes"]:
                if not isinstance(item, int):
                    border["dashes"] = None
                    break
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj( annot)
        pdf = mupdf.pdf_get_bound_document( annot_obj)
        return JM_annot_set_border( border, pdf, annot_obj)

    def set_colors(self, colors=None, stroke=None, fill=None):
        """Set 'stroke' and 'fill' colors.

        Use either a dict or the direct arguments.
        """
        CheckParent(self)
        doc = self.get_parent().parent
        if type(colors) is not dict:
            colors = {"fill": fill, "stroke": stroke}
        fill = colors.get("fill")
        stroke = colors.get("stroke")
        fill_annots = (mupdf.PDF_ANNOT_CIRCLE, mupdf.PDF_ANNOT_SQUARE, mupdf.PDF_ANNOT_LINE, mupdf.PDF_ANNOT_POLY_LINE, mupdf.PDF_ANNOT_POLYGON,
                       mupdf.PDF_ANNOT_REDACT,)
        if stroke in ([], ()):
            doc.xref_set_key(self.xref, "C", "[]")
        elif stroke is not None:
            if hasattr(stroke, "__float__"):
                stroke = [float(stroke)]
            CheckColor(stroke)
            assert len(stroke) in (1, 3, 4)
            s = f"[{_format_g(stroke)}]"
            doc.xref_set_key(self.xref, "C", s)

        if fill and self.type[0] not in fill_annots:
            message("Warning: fill color ignored for annot type '%s'." % self.type[1])
            return
        if fill in ([], ()):
            doc.xref_set_key(self.xref, "IC", "[]")
        elif fill is not None:
            if hasattr(fill, "__float__"):
                fill = [float(fill)]
            CheckColor(fill)
            assert len(fill) in (1, 3, 4)
            s = f"[{_format_g(fill)}]"
            doc.xref_set_key(self.xref, "IC", s)

    def set_flags(self, flags):
        """Set annotation flags."""
        CheckParent(self)
        annot = self.this
        mupdf.pdf_set_annot_flags(annot, flags)

    def set_info(self, info=None, content=None, title=None, creationDate=None, modDate=None, subject=None):
        """Set various properties."""
        CheckParent(self)
        if type(info) is dict:  # build the args from the dictionary
            content = info.get("content", None)
            title = info.get("title", None)
            creationDate = info.get("creationDate", None)
            modDate = info.get("modDate", None)
            subject = info.get("subject", None)
            info = None
        annot = self.this
        # use this to indicate a 'markup' annot type
        is_markup = mupdf.pdf_annot_has_author(annot)
        # contents
        if content:
            mupdf.pdf_set_annot_contents(annot, content)
        if is_markup:
            # title (= author)
            if title:
                mupdf.pdf_set_annot_author(annot, title)
            # creation date
            if creationDate:
                mupdf.pdf_dict_put_text_string(mupdf.pdf_annot_obj(annot), PDF_NAME('CreationDate'), creationDate)
            # mod date
            if modDate:
                mupdf.pdf_dict_put_text_string(mupdf.pdf_annot_obj(annot), PDF_NAME('M'), modDate)
            # subject
            if subject:
                mupdf.pdf_dict_puts(mupdf.pdf_annot_obj(annot), "Subj", mupdf.pdf_new_text_string(subject))

    def set_irt_xref(self, xref):
        '''
        Set annotation IRT xref
        '''
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj( annot)
        page = _pdf_annot_page(annot)
        if xref < 1 or xref >= mupdf.pdf_xref_len( page.doc()):
            raise ValueError( MSG_BAD_XREF)
        irt = mupdf.pdf_new_indirect( page.doc(), xref, 0)
        subt = mupdf.pdf_dict_get( irt, PDF_NAME('Subtype'))
        irt_subt = mupdf.pdf_annot_type_from_string( mupdf.pdf_to_name( subt))
        if irt_subt < 0:
            raise ValueError( MSG_IS_NO_ANNOT)
        mupdf.pdf_dict_put( annot_obj, PDF_NAME('IRT'), irt)

    def set_language(self, language=None):
        """Set annotation language."""
        CheckParent(self)
        this_annot = self.this
        if not language:
            lang = mupdf.FZ_LANG_UNSET
        else:
            lang = mupdf.fz_text_language_from_string(language)
        mupdf.pdf_set_annot_language(this_annot, lang)

    def set_line_ends(self, start, end):
        """Set line end codes."""
        CheckParent(self)
        annot = self.this
        if mupdf.pdf_annot_has_line_ending_styles(annot):
            mupdf.pdf_set_annot_line_ending_styles(annot, start, end)
        else:
            message_warning("bad annot type for line ends")

    def set_name(self, name):
        """Set /Name (icon) of annotation."""
        CheckParent(self)
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj(annot)
        mupdf.pdf_dict_put_name(annot_obj, PDF_NAME('Name'), name)

    def set_oc(self, oc=0):
        """Set / remove annotation OC xref."""
        CheckParent(self)
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj(annot)
        if not oc:
            mupdf.pdf_dict_del(annot_obj, PDF_NAME('OC'))
        else:
            JM_add_oc_object(mupdf.pdf_get_bound_document(annot_obj), annot_obj, oc)

    def set_opacity(self, opacity):
        """Set opacity."""
        CheckParent(self)
        annot = self.this
        if not _INRANGE(opacity, 0.0, 1.0):
            mupdf.pdf_set_annot_opacity(annot, 1)
            return
        mupdf.pdf_set_annot_opacity(annot, opacity)
        if opacity < 1.0:
            page = _pdf_annot_page(annot)
            page.transparency = 1

    def set_open(self, is_open):
        """Set 'open' status of annotation or its Popup."""
        CheckParent(self)
        annot = self.this
        mupdf.pdf_set_annot_is_open(annot, is_open)

    def set_popup(self, rect):
        '''
        Create annotation 'Popup' or update rectangle.
        '''
        CheckParent(self)
        annot = self.this
        pdfpage = _pdf_annot_page(annot)
        rot = JM_rotate_page_matrix(pdfpage)
        r = mupdf.fz_transform_rect(JM_rect_from_py(rect), rot)
        mupdf.pdf_set_annot_popup(annot, r)

    def set_rect(self, rect):
        """Set annotation rectangle."""
        CheckParent(self)
        annot = self.this
        
        pdfpage = _pdf_annot_page(annot)
        rot = JM_rotate_page_matrix(pdfpage)
        r = mupdf.fz_transform_rect(JM_rect_from_py(rect), rot)
        if mupdf.fz_is_empty_rect(r) or mupdf.fz_is_infinite_rect(r):
            raise ValueError( MSG_BAD_RECT)
        try:
            mupdf.pdf_set_annot_rect(annot, r)
        except Exception as e:
            message(f'cannot set rect: {e}')
            return False

    def set_rotation(self, rotate=0):
        """Set annotation rotation."""
        CheckParent(self)
        
        annot = self.this
        type = mupdf.pdf_annot_type(annot)
        if type not in (
                mupdf.PDF_ANNOT_CARET,
                mupdf.PDF_ANNOT_CIRCLE,
                mupdf.PDF_ANNOT_FREE_TEXT,
                mupdf.PDF_ANNOT_FILE_ATTACHMENT,
                mupdf.PDF_ANNOT_INK,
                mupdf.PDF_ANNOT_LINE,
                mupdf.PDF_ANNOT_POLY_LINE,
                mupdf.PDF_ANNOT_POLYGON,
                mupdf.PDF_ANNOT_SQUARE,
                mupdf.PDF_ANNOT_STAMP,
                mupdf.PDF_ANNOT_TEXT,
                ):
            return
        rot = rotate
        while rot < 0:
            rot += 360
        while rot >= 360:
            rot -= 360
        if type == mupdf.PDF_ANNOT_FREE_TEXT and rot % 90 != 0:
            rot = 0
        annot_obj = mupdf.pdf_annot_obj(annot)
        mupdf.pdf_dict_put_int(annot_obj, PDF_NAME('Rotate'), rot)

    @property
    def type(self):
        """annotation type"""
        CheckParent(self)
        if not self.this.m_internal:
            return 'null'
        type_ = mupdf.pdf_annot_type(self.this)
        c = mupdf.pdf_string_from_annot_type(type_)
        o = mupdf.pdf_dict_gets( mupdf.pdf_annot_obj(self.this), 'IT')
        if not o.m_internal or mupdf.pdf_is_name(o):
            return (type_, c)
        it = mupdf.pdf_to_name(o)
        return (type_, c, it)

    def update(self,
            blend_mode: OptStr =None,
            opacity: OptFloat =None,
            fontsize: float =0,
            fontname: OptStr =None,
            text_color: OptSeq =None,
            border_color: OptSeq =None,
            fill_color: OptSeq =None,
            cross_out: bool =True,
            rotate: int =-1,
            ):
        """Update annot appearance.

        Notes:
            Depending on the annot type, some parameters make no sense,
            while others are only available in this method to achieve the
            desired result. This is especially true for 'FreeText' annots.
        Args:
            blend_mode: set the blend mode, all annotations.
            opacity: set the opacity, all annotations.
            fontsize: set fontsize, 'FreeText' only.
            fontname: set the font, 'FreeText' only.
            border_color: set border color, 'FreeText' only.
            text_color: set text color, 'FreeText' only.
            fill_color: set fill color, all annotations.
            cross_out: draw diagonal lines, 'Redact' only.
            rotate: set rotation, 'FreeText' and some others.
        """
        Annot.update_timing_test()
        CheckParent(self)
        def color_string(cs, code):
            """Return valid PDF color operator for a given color sequence.
            """
            cc = ColorCode(cs, code)
            if not cc:
                return b""
            return (cc + "\n").encode()

        annot_type = self.type[0]  # get the annot type
        dt = self.border.get("dashes", None)  # get the dashes spec
        bwidth = self.border.get("width", -1)  # get border line width
        stroke = self.colors["stroke"]  # get the stroke color
        if fill_color is not None:
            fill = fill_color
        else:
            fill = self.colors["fill"]
        rect = None  # self.rect  # prevent MuPDF fiddling with it
        apnmat = self.apn_matrix  # prevent MuPDF fiddling with it
        if rotate != -1:  # sanitize rotation value
            while rotate < 0:
                rotate += 360
            while rotate >= 360:
                rotate -= 360
            if annot_type == mupdf.PDF_ANNOT_FREE_TEXT and rotate % 90 != 0:
                rotate = 0

        #------------------------------------------------------------------
        # handle opacity and blend mode
        #------------------------------------------------------------------
        if blend_mode is None:
            blend_mode = self.blendmode
        if not hasattr(opacity, "__float__"):
            opacity = self.opacity

        if 0 <= opacity < 1 or blend_mode is not None:
            opa_code = "/H gs\n"  # then we must reference this 'gs'
        else:
            opa_code = ""

        if annot_type == mupdf.PDF_ANNOT_FREE_TEXT:
            CheckColor(border_color)
            CheckColor(text_color)
            CheckColor(fill_color)
            tcol, fname, fsize = TOOLS._parse_da(self)

            # read and update default appearance as necessary
            update_default_appearance = False
            if fsize <= 0:
                fsize = 12
                update_default_appearance = True
            if text_color is not None:
                tcol = text_color
                update_default_appearance = True
            if fontname is not None:
                fname = fontname
                update_default_appearance = True
            if fontsize > 0:
                fsize = fontsize
                update_default_appearance = True

            if update_default_appearance:
                da_str = ""
                if len(tcol) == 3:
                    fmt = "{:g} {:g} {:g} rg /{f:s} {s:g} Tf"
                elif len(tcol) == 1:
                    fmt = "{:g} g /{f:s} {s:g} Tf"
                elif len(tcol) == 4:
                    fmt = "{:g} {:g} {:g} {:g} k /{f:s} {s:g} Tf"
                da_str = fmt.format(*tcol, f=fname, s=fsize)
                TOOLS._update_da(self, da_str)

        #------------------------------------------------------------------
        # now invoke MuPDF to update the annot appearance
        #------------------------------------------------------------------
        val = self._update_appearance(
            opacity=opacity,
            blend_mode=blend_mode,
            fill_color=fill,
            rotate=rotate,
        )
        if val is False:
            raise RuntimeError("Error updating annotation.")

        bfill = color_string(fill, "f")
        bstroke = color_string(stroke, "c")

        p_ctm = self.get_parent().transformation_matrix
        imat = ~p_ctm  # inverse page transf. matrix

        if dt:
            dashes = "[" + " ".join(map(str, dt)) + "] 0 d\n"
            dashes = dashes.encode("utf-8")
        else:
            dashes = None

        if self.line_ends:
            line_end_le, line_end_ri = self.line_ends
        else:
            line_end_le, line_end_ri = 0, 0  # init line end codes

        # read contents as created by MuPDF
        ap = self._getAP()
        ap_tab = ap.splitlines()  # split in single lines
        ap_updated = False  # assume we did nothing

        if annot_type == mupdf.PDF_ANNOT_REDACT:
            if cross_out:  # create crossed-out rect
                ap_updated = True
                ap_tab = ap_tab[:-1]
                _, LL, LR, UR, UL = ap_tab
                ap_tab.append(LR)
                ap_tab.append(LL)
                ap_tab.append(UR)
                ap_tab.append(LL)
                ap_tab.append(UL)
                ap_tab.append(b"S")

            if bwidth > 0 or bstroke != b"":
                ap_updated = True
                ntab = [_format_g(bwidth).encode() + b" w"] if bwidth > 0 else []
                for line in ap_tab:
                    if line.endswith(b"w"):
                        continue
                    if line.endswith(b"RG") and bstroke != b"":
                        line = bstroke[:-1]
                    ntab.append(line)
                ap_tab = ntab

            ap = b"\n".join(ap_tab)

        if annot_type == mupdf.PDF_ANNOT_FREE_TEXT:
            BT = ap.find(b"BT")
            ET = ap.rfind(b"ET") + 2
            ap = ap[BT:ET]
            w, h = self.rect.width, self.rect.height
            if rotate in (90, 270) or not (apnmat.b == apnmat.c == 0):
                w, h = h, w
            re = b"0 0 " + _format_g((w, h)).encode() + b" re"
            ap = re + b"\nW\nn\n" + ap
            ope = None
            fill_string = color_string(fill, "f")
            if fill_string:
                ope = b"f"
            stroke_string = color_string(border_color, "c")
            if stroke_string and bwidth > 0:
                ope = b"S"
                bwidth = _format_g(bwidth).encode() + b" w\n"
            else:
                bwidth = stroke_string = b""
            if fill_string and stroke_string:
                ope = b"B"
            if ope is not None:
                ap = bwidth + fill_string + stroke_string + re + b"\n" + ope + b"\n" + ap

            if dashes is not None:  # handle dashes
                ap = dashes + b"\n" + ap
                dashes = None

            ap_updated = True

        if annot_type in (mupdf.PDF_ANNOT_POLYGON, mupdf.PDF_ANNOT_POLY_LINE):
            ap = b"\n".join(ap_tab[:-1]) + b"\n"
            ap_updated = True
            if bfill != b"":
                if annot_type == mupdf.PDF_ANNOT_POLYGON:
                    ap = ap + bfill + b"b"  # close, fill, and stroke
                elif annot_type == mupdf.PDF_ANNOT_POLY_LINE:
                    ap = ap + b"S"  # stroke
            else:
                if annot_type == mupdf.PDF_ANNOT_POLYGON:
                    ap = ap + b"s"  # close and stroke
                elif annot_type == mupdf.PDF_ANNOT_POLY_LINE:
                    ap = ap + b"S"  # stroke

        if dashes is not None:  # handle dashes
            ap = dashes + ap
            # reset dashing - only applies for LINE annots with line ends given
            ap = ap.replace(b"\nS\n", b"\nS\n[] 0 d\n", 1)
            ap_updated = True

        if opa_code:
            ap = opa_code.encode("utf-8") + ap
            ap_updated = True

        ap = b"q\n" + ap + b"\nQ\n"
        #----------------------------------------------------------------------
        # the following handles line end symbols for 'Polygon' and 'Polyline'
        #----------------------------------------------------------------------
        if line_end_le + line_end_ri > 0 and annot_type in (mupdf.PDF_ANNOT_POLYGON, mupdf.PDF_ANNOT_POLY_LINE):

            le_funcs = (None, TOOLS._le_square, TOOLS._le_circle,
                        TOOLS._le_diamond, TOOLS._le_openarrow,
                        TOOLS._le_closedarrow, TOOLS._le_butt,
                        TOOLS._le_ropenarrow, TOOLS._le_rclosedarrow,
                        TOOLS._le_slash)
            le_funcs_range = range(1, len(le_funcs))
            d = 2 * max(1, self.border["width"])
            rect = self.rect + (-d, -d, d, d)
            ap_updated = True
            points = self.vertices
            if line_end_le in le_funcs_range:
                p1 = Point(points[0]) * imat
                p2 = Point(points[1]) * imat
                left = le_funcs[line_end_le](self, p1, p2, False, fill_color)
                ap += left.encode()
            if line_end_ri in le_funcs_range:
                p1 = Point(points[-2]) * imat
                p2 = Point(points[-1]) * imat
                left = le_funcs[line_end_ri](self, p1, p2, True, fill_color)
                ap += left.encode()

        if ap_updated:
            if rect:                        # rect modified here?
                self.set_rect(rect)
                self._setAP(ap, rect=1)
            else:
                self._setAP(ap, rect=0)

        #-------------------------------
        # handle annotation rotations
        #-------------------------------
        if annot_type not in (  # only these types are supported
                mupdf.PDF_ANNOT_CARET,
                mupdf.PDF_ANNOT_CIRCLE,
                mupdf.PDF_ANNOT_FILE_ATTACHMENT,
                mupdf.PDF_ANNOT_INK,
                mupdf.PDF_ANNOT_LINE,
                mupdf.PDF_ANNOT_POLY_LINE,
                mupdf.PDF_ANNOT_POLYGON,
                mupdf.PDF_ANNOT_SQUARE,
                mupdf.PDF_ANNOT_STAMP,
                mupdf.PDF_ANNOT_TEXT,
                ):
            return

        rot = self.rotation  # get value from annot object
        if rot == -1:  # nothing to change
            return

        M = (self.rect.tl + self.rect.br) / 2  # center of annot rect

        if rot == 0:  # undo rotations
            if abs(apnmat - Matrix(1, 1)) < 1e-5:
                return  # matrix already is a no-op
            quad = self.rect.morph(M, ~apnmat)  # derotate rect
            self.setRect(quad.rect)
            self.set_apn_matrix(Matrix(1, 1))  # appearance matrix = no-op
            return

        mat = Matrix(rot)
        quad = self.rect.morph(M, mat)
        self.set_rect(quad.rect)
        self.set_apn_matrix(apnmat * mat)

    def update_file(self, buffer_=None, filename=None, ufilename=None, desc=None):
        """Update attached file."""
        CheckParent(self)
        annot = self.this
        annot_obj = mupdf.pdf_annot_obj(annot)
        pdf = mupdf.pdf_get_bound_document(annot_obj)  # the owning PDF
        type = mupdf.pdf_annot_type(annot)
        if type != mupdf.PDF_ANNOT_FILE_ATTACHMENT:
            raise TypeError( MSG_BAD_ANNOT_TYPE)
        stream = mupdf.pdf_dict_getl(annot_obj, PDF_NAME('FS'), PDF_NAME('EF'), PDF_NAME('F'))
        # the object for file content
        if not stream.m_internal:
            RAISEPY( "bad PDF: no /EF object", JM_Exc_FileDataError)

        fs = mupdf.pdf_dict_get(annot_obj, PDF_NAME('FS'))

        # file content given
        res = JM_BufferFromBytes(buffer_)
        if buffer_ and not res.m_internal:
            raise ValueError( MSG_BAD_BUFFER)
        if res:
            JM_update_stream(pdf, stream, res, 1)
            # adjust /DL and /Size parameters
            len, _ = mupdf.fz_buffer_storage(res)
            l = mupdf.pdf_new_int(len)
            mupdf.pdf_dict_put(stream, PDF_NAME('DL'), l)
            mupdf.pdf_dict_putl(stream, l, PDF_NAME('Params'), PDF_NAME('Size'))

        if filename:
            mupdf.pdf_dict_put_text_string(stream, PDF_NAME('F'), filename)
            mupdf.pdf_dict_put_text_string(fs, PDF_NAME('F'), filename)
            mupdf.pdf_dict_put_text_string(stream, PDF_NAME('UF'), filename)
            mupdf.pdf_dict_put_text_string(fs, PDF_NAME('UF'), filename)
            mupdf.pdf_dict_put_text_string(annot_obj, PDF_NAME('Contents'), filename)

        if ufilename:
            mupdf.pdf_dict_put_text_string(stream, PDF_NAME('UF'), ufilename)
            mupdf.pdf_dict_put_text_string(fs, PDF_NAME('UF'), ufilename)

        if desc:
            mupdf.pdf_dict_put_text_string(stream, PDF_NAME('Desc'), desc)
            mupdf.pdf_dict_put_text_string(fs, PDF_NAME('Desc'), desc)

    @staticmethod
    def update_timing_test():
        total = 0
        for i in range( 30*1000):
            total += i
        return total
    
    @property
    def vertices(self):
        """annotation vertex points"""
        CheckParent(self)
        annot = self.this
        assert isinstance(annot, mupdf.PdfAnnot)
        annot_obj = mupdf.pdf_annot_obj(annot)
        page = _pdf_annot_page(annot)
        page_ctm = mupdf.FzMatrix()   # page transformation matrix
        dummy = mupdf.FzRect()  # Out-param for mupdf.pdf_page_transform().
        mupdf.pdf_page_transform(page, dummy, page_ctm)
        derot = JM_derotate_page_matrix(page)
        page_ctm = mupdf.fz_concat(page_ctm, derot)

        #----------------------------------------------------------------
        # The following objects occur in different annotation types.
        # So we are sure that (!o) occurs at most once.
        # Every pair of floats is one point, that needs to be separately
        # transformed with the page transformation matrix.
        #----------------------------------------------------------------
        o = mupdf.pdf_dict_get(annot_obj, PDF_NAME('Vertices'))
        if not o.m_internal:    o = mupdf.pdf_dict_get(annot_obj, PDF_NAME('L'))
        if not o.m_internal:    o = mupdf.pdf_dict_get(annot_obj, PDF_NAME('QuadPoints'))
        if not o.m_internal:    o = mupdf.pdf_dict_gets(annot_obj, 'CL')
        
        if o.m_internal:
            # handle lists with 1-level depth
            # weiter
            res = []
            for i in range(0, mupdf.pdf_array_len(o), 2):
                x = mupdf.pdf_to_real(mupdf.pdf_array_get(o, i))
                y = mupdf.pdf_to_real(mupdf.pdf_array_get(o, i+1))
                point = mupdf.FzPoint(x, y)
                point = mupdf.fz_transform_point(point, page_ctm)
                res.append( (point.x, point.y))
            return res
            
        o = mupdf.pdf_dict_gets(annot_obj, 'InkList')
        if o.m_internal:
            # InkList has 2-level lists
            #inklist:
            res = []
            for i in range(mupdf.pdf_array_len(o)):
                res1 = []
                o1 = mupdf.pdf_array_get(o, i)
                for j in range(0, mupdf.pdf_array_len(o1), 2):
                    x = mupdf.pdf_to_real(mupdf.pdf_array_get(o1, j))
                    y = mupdf.pdf_to_real(mupdf.pdf_array_get(o1, j+1))
                    point = mupdf.FzPoint(x, y)
                    point = mupdf.fz_transform_point(point, page_ctm)
                    res1.append( (point.x, point.y))
                res.append(res1)
            return res

    @property
    def xref(self):
        """annotation xref number"""
        CheckParent(self)
        annot = self.this
        return mupdf.pdf_to_num(mupdf.pdf_annot_obj(annot))


class Archive:
    def __init__( self, *args):
        '''
        Archive(dirname [, path]) - from folder
        Archive(file [, path]) - from file name or object
        Archive(data, name) - from memory item
        Archive() - empty archive
        Archive(archive [, path]) - from archive
        '''
        self._subarchives = list()
        self.this = mupdf.fz_new_multi_archive()
        if args:
            self.add( *args)
    
    def __repr__( self):
        return f'Archive, sub-archives: {len(self._subarchives)}'

    def _add_arch( self, subarch, path=None):
        mupdf.fz_mount_multi_archive( self.this, subarch, path)
    
    def _add_dir( self, folder, path=None):
        sub = mupdf.fz_open_directory( folder)
        mupdf.fz_mount_multi_archive( self.this, sub, path)
    
    def _add_treeitem( self, memory, name, path=None):
        buff = JM_BufferFromBytes( memory)
        sub = mupdf.fz_new_tree_archive( mupdf.FzTree())
        mupdf.fz_tree_archive_add_buffer( sub, name, buff)
        mupdf.fz_mount_multi_archive( self.this, sub, path)
    
    def _add_ziptarfile( self, filepath, type_, path=None):
        if type_ == 1:
            sub = mupdf.fz_open_zip_archive( filepath)
        else:
            sub = mupdf.fz_open_tar_archive( filepath)
        mupdf.fz_mount_multi_archive( self.this, sub, path)
    
    def _add_ziptarmemory( self, memory, type_, path=None):
        buff = JM_BufferFromBytes( memory)
        stream = mupdf.fz_open_buffer( buff)
        if type_==1:
            sub = mupdf.fz_open_zip_archive_with_stream( stream)
        else:
            sub = mupdf.fz_open_tar_archive_with_stream( stream)
        mupdf.fz_mount_multi_archive( self.this, sub, path)
    
    def add( self, content, path=None):
        '''
        Add a sub-archive.

        Args:
            content:
                The content to be added. May be one of:
                    `str` - must be path of directory or file.
                    `bytes`, `bytearray`, `io.BytesIO` - raw data.
                    `zipfile.Zipfile`.
                    `tarfile.TarFile`.
                    `pymupdf.Archive`.
                    A two-item tuple `(data, name)`.
                    List or tuple (but not tuple with length 2) of the above.
            path: (str) a "virtual" path name, under which the elements
                of content can be retrieved. Use it to e.g. cope with
                duplicate element names.
        '''
        def is_binary_data(x):
            return isinstance(x, (bytes, bytearray, io.BytesIO))

        def make_subarch(entries, mount, fmt):
            subarch = dict(fmt=fmt, entries=entries, path=mount)
            if fmt != "tree" or self._subarchives == []:
                self._subarchives.append(subarch)
            else:
                ltree = self._subarchives[-1]
                if ltree["fmt"] != "tree" or ltree["path"] != subarch["path"]:
                    self._subarchives.append(subarch)
                else:
                    ltree["entries"].extend(subarch["entries"])
                    self._subarchives[-1] = ltree

        if isinstance(content, pathlib.Path):
            content = str(content)
        
        if isinstance(content, str):
            if os.path.isdir(content):
                self._add_dir(content, path)
                return make_subarch(os.listdir(content), path, 'dir')
            elif os.path.isfile(content):
                assert isinstance(path, str) and path != '', \
                        f'Need name for binary content, but {path=}.'
                with open(content) as f:
                    ff = f.read()
                self._add_treeitem(ff, path)
                return make_subarch([path], None, 'tree')
            else:
                raise ValueError(f'Not a file or directory: {content!r}')

        elif is_binary_data(content):
            assert isinstance(path, str) and path != '' \
                    f'Need name for binary content, but {path=}.'
            self._add_treeitem(content, path)
            return make_subarch([path], None, 'tree')

        elif isinstance(content, zipfile.ZipFile):
            filename = getattr(content, "filename", None)
            if filename is None:
                fp = content.fp.getvalue()
                self._add_ziptarmemory(fp, 1, path)
            else:
                self._add_ziptarfile(filename, 1, path)
            return make_subarch(content.namelist(), path, 'zip')

        elif isinstance(content, tarfile.TarFile):
            filename = getattr(content.fileobj, "name", None)
            if filename is None:
                fp = content.fileobj
                if not isinstance(fp, io.BytesIO):
                    fp = fp.fileobj
                self._add_ziptarmemory(fp.getvalue(), 0, path)
            else:
                self._add_ziptarfile(filename, 0, path)
            return make_subarch(content.getnames(), path, 'tar')

        elif isinstance(content, Archive):
            self._add_arch(content, path)
            return make_subarch([], path, 'multi')
        
        if isinstance(content, tuple) and len(content) == 2:
            # covers the tree item plus path
            data, name = content
            assert isinstance(name, str), f'Unexpected {type(name)=}'
            if is_binary_data(data):
                self._add_treeitem(data, name, path=path)
            elif isinstance(data, str):
                if os.path.isfile(data):
                    with open(data, 'rb') as f:
                        ff = f.read()
                    self._add_treeitem(ff, name, path=path)
            else:
                assert 0, f'Unexpected {type(data)=}.'
            return make_subarch([name], path, 'tree')
        
        elif hasattr(content, '__getitem__'):
            # Deal with sequence of disparate items.
            for item in content:
                self.add(item, path)
            return
        
        else:
            raise TypeError(f'Unrecognised type {type(content)}.')
        assert 0

    @property
    def entry_list( self):
        '''
        List of sub archives.
        '''
        return self._subarchives
    
    def has_entry( self, name):
        return mupdf.fz_has_archive_entry( self.this, name)
    
    def read_entry( self, name):
        buff = mupdf.fz_read_archive_entry( self.this, name)
        return JM_BinFromBuffer( buff)


class Xml:

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __init__( self, rhs):
        if isinstance( rhs, mupdf.FzXml):
            self.this = rhs
        elif isinstance( str):
            buff = mupdf.fz_new_buffer_from_copied_data( rhs)
            self.this = mupdf.fz_parse_xml_from_html5( buff)
        else:
            assert 0, f'Unsupported type for rhs: {type(rhs)}'
    
    def _get_node_tree( self):
        def show_node(node, items, shift):
            while node is not None:
                if node.is_text:
                    items.append((shift, f'"{node.text}"'))
                    node = node.next
                    continue
                items.append((shift, f"({node.tagname}"))
                for k, v in node.get_attributes().items():
                    items.append((shift, f"={k} '{v}'"))
                child = node.first_child
                if child:
                    items = show_node(child, items, shift + 1)
                items.append((shift, f"){node.tagname}"))
                node = node.next
            return items

        shift = 0
        items = []
        items = show_node(self, items, shift)
        return items
    
    def add_bullet_list(self):
        """Add bulleted list ("ul" tag)"""
        child = self.create_element("ul")
        self.append_child(child)
        return child

    def add_class(self, text):
        """Set some class via CSS. Replaces complete class spec."""
        cls = self.get_attribute_value("class")
        if cls is not None and text in cls:
            return self
        self.remove_attribute("class")
        if cls is None:
            cls = text
        else:
            cls += " " + text
        self.set_attribute("class", cls)
        return self

    def add_code(self, text=None):
        """Add a "code" tag"""
        child = self.create_element("code")
        if type(text) is str:
            child.append_child(self.create_text_node(text))
        prev = self.span_bottom()
        if prev is None:
            prev = self
        prev.append_child(child)
        return self

    def add_codeblock(self):
        """Add monospaced lines ("pre" node)"""
        child = self.create_element("pre")
        self.append_child(child)
        return child

    def add_description_list(self):
        """Add description list ("dl" tag)"""
        child = self.create_element("dl")
        self.append_child(child)
        return child

    def add_division(self):
        """Add "div" tag"""
        child = self.create_element("div")
        self.append_child(child)
        return child

    def add_header(self, level=1):
        """Add header tag"""
        if level not in range(1, 7):
            raise ValueError("Header level must be in [1, 6]")
        this_tag = self.tagname
        new_tag = f"h{level}"
        child = self.create_element(new_tag)
        if this_tag not in ("h1", "h2", "h3", "h4", "h5", "h6", "p"):
            self.append_child(child)
            return child
        self.parent.append_child(child)
        return child

    def add_horizontal_line(self):
        """Add horizontal line ("hr" tag)"""
        child = self.create_element("hr")
        self.append_child(child)
        return child

    def add_image(self, name, width=None, height=None, imgfloat=None, align=None):
        """Add image node (tag "img")."""
        child = self.create_element("img")
        if width is not None:
            child.set_attribute("width", f"{width}")
        if height is not None:
            child.set_attribute("height", f"{height}")
        if imgfloat is not None:
            child.set_attribute("style", f"float: {imgfloat}")
        if align is not None:
            child.set_attribute("align", f"{align}")
        child.set_attribute("src", f"{name}")
        self.append_child(child)
        return child

    def add_link(self, href, text=None):
        """Add a hyperlink ("a" tag)"""
        child = self.create_element("a")
        if not isinstance(text, str):
            text = href
        child.set_attribute("href", href)
        child.append_child(self.create_text_node(text))
        prev = self.span_bottom()
        if prev is None:
            prev = self
        prev.append_child(child)
        return self

    def add_list_item(self):
        """Add item ("li" tag) under a (numbered or bulleted) list."""
        if self.tagname not in ("ol", "ul"):
            raise ValueError("cannot add list item to", self.tagname)
        child = self.create_element("li")
        self.append_child(child)
        return child

    def add_number_list(self, start=1, numtype=None):
        """Add numbered list ("ol" tag)"""
        child = self.create_element("ol")
        if start > 1:
            child.set_attribute("start", str(start))
        if numtype is not None:
            child.set_attribute("type", numtype)
        self.append_child(child)
        return child

    def add_paragraph(self):
        """Add "p" tag"""
        child = self.create_element("p")
        if self.tagname != "p":
            self.append_child(child)
        else:
            self.parent.append_child(child)
        return child

    def add_span(self):
        child = self.create_element("span")
        self.append_child(child)
        return child

    def add_style(self, text):
        """Set some style via CSS style. Replaces complete style spec."""
        style = self.get_attribute_value("style")
        if style is not None and text in style:
            return self
        self.remove_attribute("style")
        if style is None:
            style = text
        else:
            style += ";" + text
        self.set_attribute("style", style)
        return self

    def add_subscript(self, text=None):
        """Add a subscript ("sub" tag)"""
        child = self.create_element("sub")
        if type(text) is str:
            child.append_child(self.create_text_node(text))
        prev = self.span_bottom()
        if prev is None:
            prev = self
        prev.append_child(child)
        return self

    def add_superscript(self, text=None):
        """Add a superscript ("sup" tag)"""
        child = self.create_element("sup")
        if type(text) is str:
            child.append_child(self.create_text_node(text))
        prev = self.span_bottom()
        if prev is None:
            prev = self
        prev.append_child(child)
        return self

    def add_text(self, text):
        """Add text. Line breaks are honored."""
        lines = text.splitlines()
        line_count = len(lines)
        prev = self.span_bottom()
        if prev is None:
            prev = self

        for i, line in enumerate(lines):
            prev.append_child(self.create_text_node(line))
            if i < line_count - 1:
                prev.append_child(self.create_element("br"))
        return self

    def append_child( self, child):
        mupdf.fz_dom_append_child( self.this, child.this)
    
    def append_styled_span(self, style):
        span = self.create_element("span")
        span.add_style(style)
        prev = self.span_bottom()
        if prev is None:
            prev = self
        prev.append_child(span)
        return prev

    def bodytag( self):
        return Xml( mupdf.fz_dom_body( self.this))
    
    def clone( self):
        ret = mupdf.fz_dom_clone( self.this)
        return Xml( ret)
    
    @staticmethod
    def color_text(color):
        if type(color) is str:
            return color
        if type(color) is int:
            return f"rgb({sRGB_to_rgb(color)})"
        if type(color) in (tuple, list):
            return f"rgb{tuple(color)}"
        return color

    def create_element( self, tag):
        return Xml( mupdf.fz_dom_create_element( self.this, tag))
    
    def create_text_node( self, text):
        return Xml( mupdf.fz_dom_create_text_node( self.this, text))
    
    def debug(self):
        """Print a list of the node tree below self."""
        items = self._get_node_tree()
        for item in items:
            message("  " * item[0] + item[1].replace("\n", "\\n"))

    def find( self, tag, att, match):
        ret = mupdf.fz_dom_find( self.this, tag, att, match)
        if ret.m_internal:
            return Xml( ret)
    
    def find_next( self, tag, att, match):
        ret = mupdf.fz_dom_find_next( self.this, tag, att, match)
        if ret.m_internal:
            return Xml( ret)
    
    @property
    def first_child( self):
        if mupdf.fz_xml_text( self.this):
            # text node, has no child.
            return
        ret = mupdf.fz_dom_first_child( self)
        if ret.m_internal:
            return Xml( ret)
    
    def get_attribute_value( self, key):
        assert key
        return mupdf.fz_dom_attribute( self.this, key)
    
    def get_attributes( self):
        if mupdf.fz_xml_text( self.this):
            # text node, has no attributes.
            return
        result = dict()
        i = 0
        while 1:
            val, key = mupdf.fz_dom_get_attribute( self.this, i)
            if not val or not key:
                break
            result[ key] = val
            i += 1
        return result
    
    def insert_after( self, node):
        mupdf.fz_dom_insert_after( self.this, node.this)
    
    def insert_before( self, node):
        mupdf.fz_dom_insert_before( self.this, node.this)
    
    def insert_text(self, text):
        lines = text.splitlines()
        line_count = len(lines)
        for i, line in enumerate(lines):
            self.append_child(self.create_text_node(line))
            if i < line_count - 1:
                self.append_child(self.create_element("br"))
        return self

    @property
    def is_text(self):
        """Check if this is a text node."""
        return self.text is not None

    @property
    def last_child(self):
        """Return last child node."""
        child = self.first_child
        if child is None:
            return None
        while True:
            next = child.next
            if not next:
                return child
            child = next

    @property
    def next( self):
        ret = mupdf.fz_dom_next( self.this)
        if ret.m_internal:
            return Xml( ret)
            
    @property
    def parent( self):
        ret = mupdf.fz_dom_parent( self.this)
        if ret.m_internal:
            return Xml( ret)
    
    @property
    def previous( self):
        ret = mupdf.fz_dom_previous( self.this)
        if ret.m_internal:
            return Xml( ret)
    
    def remove( self):
        mupdf.fz_dom_remove( self.this)
    
    def remove_attribute( self, key):
        assert key
        mupdf.fz_dom_remove_attribute( self.this, key)
    
    @property
    def root( self):
        return Xml( mupdf.fz_xml_root( self.this))
    
    def set_align(self, align):
        """Set text alignment via CSS style"""
        text = "text-align: %s"
        if isinstance( align, str):
            t = align
        elif align == TEXT_ALIGN_LEFT:
            t = "left"
        elif align == TEXT_ALIGN_CENTER:
            t = "center"
        elif align == TEXT_ALIGN_RIGHT:
            t = "right"
        elif align == TEXT_ALIGN_JUSTIFY:
            t = "justify"
        else:
            raise ValueError(f"Unrecognised {align=}")
        text = text % t
        self.add_style(text)
        return self

    def set_attribute( self, key, value):
        assert key
        mupdf.fz_dom_add_attribute( self.this, key, value)
    
    def set_bgcolor(self, color):
        """Set background color via CSS style"""
        text = f"background-color: %s" % self.color_text(color)
        self.add_style(text)  # does not work on span level
        return self

    def set_bold(self, val=True):
        """Set bold on / off via CSS style"""
        if val:
            val="bold"
        else:
            val="normal"
        text = "font-weight: %s" % val
        self.append_styled_span(text)
        return self

    def set_color(self, color):
        """Set text color via CSS style"""
        text = f"color: %s" % self.color_text(color)
        self.append_styled_span(text)
        return self

    def set_columns(self, cols):
        """Set number of text columns via CSS style"""
        text = f"columns: {cols}"
        self.append_styled_span(text)
        return self

    def set_font(self, font):
        """Set font-family name via CSS style"""
        text = "font-family: %s" % font
        self.append_styled_span(text)
        return self

    def set_fontsize(self, fontsize):
        """Set font size name via CSS style"""
        if type(fontsize) is str:
            px=""
        else:
            px="px"
        text = f"font-size: {fontsize}{px}"
        self.append_styled_span(text)
        return self

    def set_id(self, unique):
        """Set a unique id."""
        # check uniqueness
        root = self.root
        if root.find(None, "id", unique):
            raise ValueError(f"id '{unique}' already exists")
        self.set_attribute("id", unique)
        return self

    def set_italic(self, val=True):
        """Set italic on / off via CSS style"""
        if val:
            val="italic"
        else:
            val="normal"
        text = "font-style: %s" % val
        self.append_styled_span(text)
        return self

    def set_leading(self, leading):
        """Set inter-line spacing value via CSS style - block-level only."""
        text = f"-mupdf-leading: {leading}"
        self.add_style(text)
        return self

    def set_letter_spacing(self, spacing):
        """Set inter-letter spacing value via CSS style"""
        text = f"letter-spacing: {spacing}"
        self.append_styled_span(text)
        return self

    def set_lineheight(self, lineheight):
        """Set line height name via CSS style - block-level only."""
        text = f"line-height: {lineheight}"
        self.add_style(text)
        return self

    def set_margins(self, val):
        """Set margin values via CSS style"""
        text = "margins: %s" % val
        self.append_styled_span(text)
        return self

    def set_opacity(self, opacity):
        """Set opacity via CSS style"""
        text = f"opacity: {opacity}"
        self.append_styled_span(text)
        return self

    def set_pagebreak_after(self):
        """Insert a page break after this node."""
        text = "page-break-after: always"
        self.add_style(text)
        return self

    def set_pagebreak_before(self):
        """Insert a page break before this node."""
        text = "page-break-before: always"
        self.add_style(text)
        return self

    def set_properties(
            self,
            align=None,
            bgcolor=None,
            bold=None,
            color=None,
            columns=None,
            font=None,
            fontsize=None,
            indent=None,
            italic=None,
            leading=None,
            letter_spacing=None,
            lineheight=None,
            margins=None,
            pagebreak_after=None,
            pagebreak_before=None,
            word_spacing=None,
            unqid=None,
            cls=None,
            ):
        """Set any or all properties of a node.

        To be used for existing nodes preferably.
        """
        root = self.root
        temp = root.add_division()
        if align is not None:
            temp.set_align(align)
        if bgcolor is not None:
            temp.set_bgcolor(bgcolor)
        if bold is not None:
            temp.set_bold(bold)
        if color is not None:
            temp.set_color(color)
        if columns is not None:
            temp.set_columns(columns)
        if font is not None:
            temp.set_font(font)
        if fontsize is not None:
            temp.set_fontsize(fontsize)
        if indent is not None:
            temp.set_text_indent(indent)
        if italic is not None:
            temp.set_italic(italic)
        if leading is not None:
            temp.set_leading(leading)
        if letter_spacing is not None:
            temp.set_letter_spacing(letter_spacing)
        if lineheight is not None:
            temp.set_lineheight(lineheight)
        if margins is not None:
            temp.set_margins(margins)
        if pagebreak_after is not None:
            temp.set_pagebreak_after()
        if pagebreak_before is not None:
            temp.set_pagebreak_before()
        if word_spacing is not None:
            temp.set_word_spacing(word_spacing)
        if unqid is not None:
            self.set_id(unqid)
        if cls is not None:
            self.add_class(cls)

        styles = []
        top_style = temp.get_attribute_value("style")
        if top_style is not None:
            styles.append(top_style)
        child = temp.first_child
        while child:
            styles.append(child.get_attribute_value("style"))
            child = child.first_child
        self.set_attribute("style", ";".join(styles))
        temp.remove()
        return self

    def set_text_indent(self, indent):
        """Set text indentation name via CSS style - block-level only."""
        text = f"text-indent: {indent}"
        self.add_style(text)
        return self

    def set_underline(self, val="underline"):
        text = "text-decoration: %s" % val
        self.append_styled_span(text)
        return self

    def set_word_spacing(self, spacing):
        """Set inter-word spacing value via CSS style"""
        text = f"word-spacing: {spacing}"
        self.append_styled_span(text)
        return self

    def span_bottom(self):
        """Find deepest level in stacked spans."""
        parent = self
        child = self.last_child
        if child is None:
            return None
        while child.is_text:
            child = child.previous
            if child is None:
                break
        if child is None or child.tagname != "span":
            return None

        while True:
            if child is None:
                return parent
            if child.tagname in ("a", "sub","sup","body") or child.is_text:
                child = child.next
                continue
            if child.tagname == "span":
                parent = child
                child = child.first_child
            else:
                return parent

    @property
    def tagname( self):
        return mupdf.fz_xml_tag( self.this)
    
    @property
    def text( self):
        return mupdf.fz_xml_text( self.this)
    
    add_var = add_code
    add_samp = add_code
    add_kbd = add_code


class Colorspace:

    def __init__(self, type_):
        """Supported are GRAY, RGB and CMYK."""
        if isinstance( type_, mupdf.FzColorspace):
            self.this = type_
        elif type_ == CS_GRAY:
            self.this = mupdf.FzColorspace(mupdf.FzColorspace.Fixed_GRAY)
        elif type_ == CS_CMYK:
            self.this = mupdf.FzColorspace(mupdf.FzColorspace.Fixed_CMYK)
        elif type_ == CS_RGB:
            self.this = mupdf.FzColorspace(mupdf.FzColorspace.Fixed_RGB)
        else:
            self.this = mupdf.FzColorspace(mupdf.FzColorspace.Fixed_RGB)

    def __repr__(self):
        x = ("", "GRAY", "", "RGB", "CMYK")[self.n]
        return "Colorspace(CS_%s) - %s" % (x, self.name)

    def _name(self):
        return mupdf.fz_colorspace_name(self.this)

    @property
    def n(self):
        """Size of one pixel."""
        return mupdf.fz_colorspace_n(self.this)

    @property
    def name(self):
        """Name of the Colorspace."""
        return self._name()


class DeviceWrapper:
    def __init__(self, *args):
        if args_match( args, mupdf.FzDevice):
            device, = args
            self.this = device
        elif args_match( args, Pixmap, None):
            pm, clip = args
            bbox = JM_irect_from_py( clip)
            if mupdf.fz_is_infinite_irect( bbox):
                self.this = mupdf.fz_new_draw_device( mupdf.FzMatrix(), pm)
            else:
                self.this = mupdf.fz_new_draw_device_with_bbox( mupdf.FzMatrix(), pm, bbox)
        elif args_match( args, mupdf.FzDisplayList):
            dl, = args
            self.this = mupdf.fz_new_list_device( dl)
        elif args_match( args, mupdf.FzStextPage, None):
            tp, flags = args
            opts = mupdf.FzStextOptions( flags)
            self.this = mupdf.fz_new_stext_device( tp, opts)
        else:
            raise Exception( f'Unrecognised args for DeviceWrapper: {args!r}')


class DisplayList:
    def __del__(self):
        if not type(self) is DisplayList: return
        self.thisown = False

    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], mupdf.FzRect):
            self.this = mupdf.FzDisplayList(args[0])
        elif len(args) == 1 and isinstance(args[0], mupdf.FzDisplayList):
            self.this = args[0]
        else:
            assert 0, f'Unrecognised {args=}'

    def get_pixmap(self, matrix=None, colorspace=None, alpha=0, clip=None):
        if isinstance(colorspace, Colorspace):
            colorspace = colorspace.this
        else:
            colorspace = mupdf.FzColorspace(mupdf.FzColorspace.Fixed_RGB)
        val = JM_pixmap_from_display_list(self.this, matrix, colorspace, alpha, clip, None)
        val.thisown = True
        return val

    def get_textpage(self, flags=3):
        """Make a TextPage from a DisplayList."""
        stext_options = mupdf.FzStextOptions()
        stext_options.flags = flags
        val = mupdf.FzStextPage(self.this, stext_options)
        val.thisown = True
        return val

    @property
    def rect(self):
        val = JM_py_from_rect(mupdf.fz_bound_display_list(self.this))
        val = Rect(val)
        return val

    def run(self, dw, m, area):
        mupdf.fz_run_display_list(
                self.this,
                dw.device,
                JM_matrix_from_py(m),
                JM_rect_from_py(area),
                mupdf.FzCookie(),
                )

if g_use_extra:
    extra_FzDocument_insert_pdf = extra.FzDocument_insert_pdf


class Document:

    def __contains__(self, loc) -> bool:
        if type(loc) is int:
            if loc < self.page_count:
                return True
            return False
        if type(loc) not in (tuple, list) or len(loc) != 2:
            return False
        chapter, pno = loc
        if (0
                or not isinstance(chapter, int)
                or chapter < 0
                or chapter >= self.chapter_count
                ):
            return False
        if (0
                or not isinstance(pno, int)
                or pno < 0
                or pno >= self.chapter_page_count(chapter)
                ):
            return False
        return True

    def __delitem__(self, i)->None:
        if not self.is_pdf:
            raise ValueError("is no PDF")
        if type(i) is int:
            return self.delete_page(i)
        if type(i) in (list, tuple, range):
            return self.delete_pages(i)
        if type(i) is not slice:
            raise ValueError("bad argument type")
        pc = self.page_count
        start = i.start if i.start else 0
        stop = i.stop if i.stop else pc
        step = i.step if i.step else 1
        while start < 0:
            start += pc
        if start >= pc:
            raise ValueError("bad page number(s)")
        while stop < 0:
            stop += pc
        if stop > pc:
            raise ValueError("bad page number(s)")
        return self.delete_pages(range(start, stop, step))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @typing.overload
    def __getitem__(self, i: int = 0) -> Page:
        ...
    
    if sys.version_info >= (3, 9):
        @typing.overload
        def __getitem__(self, i: slice) -> list[Page]:
            ...
        
        @typing.overload
        def __getitem__(self, i: tuple[int, int]) -> Page:
            ...
    
    def __getitem__(self, i=0):
        if isinstance(i, slice):
            return [self[j] for j in range(*i.indices(len(self)))]
        assert isinstance(i, int) or (isinstance(i, tuple) and len(i) == 2 and all(isinstance(x, int) for x in i)), \
                f'Invalid item number: {i=}.'
        if i not in self:
            raise IndexError(f"page {i} not in document")
        return self.load_page(i)

    def __init__(self, filename=None, stream=None, filetype=None, rect=None, width=0, height=0, fontsize=11):
        """Creates a document. Use 'open' as a synonym.

        Notes:
            Basic usages:
            open() - new PDF document
            open(filename) - string or pathlib.Path, must have supported
                    file extension.
            open(type, buffer) - type: valid extension, buffer: bytes object.
            open(stream=buffer, filetype=type) - keyword version of previous.
            open(filename, fileype=type) - filename with unrecognized extension.
            rect, width, height, fontsize: layout reflowable document
            on open (e.g. EPUB). Ignored if n/a.
        """
        # We temporarily set JM_mupdf_show_errors=0 while we are constructing,
        # then restore its original value in a `finally:` block.
        #
        global JM_mupdf_show_errors
        JM_mupdf_show_errors_old = JM_mupdf_show_errors
        JM_mupdf_show_errors = 0
        try:
            self.is_closed    = False
            self.is_encrypted = False
            self.is_encrypted = False
            self.metadata    = None
            self.FontInfos   = []
            self.Graftmaps   = {}
            self.ShownPages  = {}
            self.InsertedImages  = {}
            self._page_refs  = weakref.WeakValueDictionary()
            if isinstance(filename, mupdf.PdfDocument):
                pdf_document = filename
                self.this = pdf_document
                self.this_is_pdf = True
                return
        
            # Classic implementation temporarily sets JM_mupdf_show_errors=0 then
            # restores the previous value in `fz_always() {...}` before returning.
            #
        
            if not filename or type(filename) is str:
                pass
            elif hasattr(filename, "absolute"):
                filename = str(filename)
            elif hasattr(filename, "name"):
                filename = filename.name
            else:
                raise TypeError(f"bad filename: {type(filename)=} {filename=}.")
        
            if stream is not None:
                if type(stream) is bytes:
                    self.stream = stream
                elif type(stream) is bytearray:
                    self.stream = bytes(stream)
                elif type(stream) is io.BytesIO:
                    self.stream = stream.getvalue()
                else:
                    raise TypeError(f"bad stream: {type(stream)=}.")
                stream = self.stream
                if not (filename or filetype):
                    filename = 'pdf'
            else:
                self.stream = None

            if filename and self.stream is None:
                from_file = True
                self._name = filename
            else:
                from_file = False
                self._name = ""

            if from_file:
                if not os.path.exists(filename):
                    msg = f"no such file: '{filename}'"
                    raise FileNotFoundError(msg)
                elif not os.path.isfile(filename):
                    msg = f"'{filename}' is no file"
                    raise FileDataError(msg)
                    
            if from_file and os.path.getsize(filename) == 0:
                raise EmptyFileError(f'Cannot open empty file: {filename=}.')
            if type(self.stream) is bytes and len(self.stream) == 0:
                raise EmptyFileError(f'Cannot open empty stream.')
            w = width
            h = height
            r = JM_rect_from_py(rect)
            if not mupdf.fz_is_infinite_rect(r):
                w = r.x1 - r.x0
                h = r.y1 - r.y0

            if stream:  # stream given, **MUST** be bytes!
                assert isinstance(stream, bytes)
                c = stream
                #len = (size_t) PyBytes_Size(stream);

                if mupdf_cppyy:
                    buffer_ = mupdf.fz_new_buffer_from_copied_data( c)
                    data = mupdf.fz_open_buffer( buffer_)
                else:
                    # Pass raw bytes data to mupdf.fz_open_memory(). This assumes
                    # that the bytes string will not be modified; i think the
                    # original PyMuPDF code makes the same assumption. Presumably
                    # setting self.stream above ensures that the bytes will not be
                    # garbage collected?
                    data = mupdf.fz_open_memory(mupdf.python_buffer_data(c), len(c))
                magic = filename
                if not magic:
                    magic = filetype
                # fixme: pymupdf does:
                #   handler = fz_recognize_document(gctx, filetype);
                #   if (!handler) raise ValueError( MSG_BAD_FILETYPE)
                # but prefer to leave fz_open_document_with_stream() to raise.
                try:
                    doc = mupdf.fz_open_document_with_stream(magic, data)
                except Exception as e:
                    if g_exceptions_verbose > 1:    exception_info()
                    raise FileDataError(f'Failed to open stream') from e
            else:
                if filename:
                    if not filetype:
                        try:
                            doc = mupdf.fz_open_document(filename)
                        except Exception as e:
                            if g_exceptions_verbose > 1:    exception_info()
                            raise FileDataError(f'Failed to open file {filename!r}.') from e
                    else:
                        handler = mupdf.ll_fz_recognize_document(filetype)
                        if handler:
                            if handler.open:
                                #log( f'{handler.open=}')
                                #log( f'{dir(handler.open)=}')
                                try:
                                    stream = mupdf.FzStream(filename)
                                    accel = mupdf.FzStream()
                                    archive = mupdf.FzArchive(None)
                                    if mupdf_version_tuple >= (1, 24, 8):
                                        doc = mupdf.ll_fz_document_handler_open(
                                                handler,
                                                stream.m_internal,
                                                accel.m_internal,
                                                archive.m_internal,
                                                None,   # recognize_state
                                                )
                                    else:
                                        doc = mupdf.ll_fz_document_open_fn_call(
                                                handler.open,
                                                stream.m_internal,
                                                accel.m_internal,
                                                archive.m_internal,
                                                )
                                except Exception as e:
                                    if g_exceptions_verbose > 1:    exception_info()
                                    raise FileDataError(f'Failed to open file {filename!r} as type {filetype!r}.') from e
                                doc = mupdf.FzDocument( doc)
                            else:
                                assert 0
                        else:
                            raise ValueError( MSG_BAD_FILETYPE)
                else:
                    pdf = mupdf.PdfDocument()
                    doc = mupdf.FzDocument(pdf)
            if w > 0 and h > 0:
                mupdf.fz_layout_document(doc, w, h, fontsize)
            elif mupdf.fz_is_document_reflowable(doc):
                mupdf.fz_layout_document(doc, 400, 600, 11)
            this = doc

            self.this = this

            # fixme: not sure where self.thisown gets initialised in PyMuPDF.
            #
            self.thisown = True

            if self.thisown:
                self._graft_id = TOOLS.gen_id()
                if self.needs_pass:
                    self.is_encrypted = True
                else: # we won't init until doc is decrypted
                    self.init_doc()
                # the following hack detects invalid/empty SVG files, which else may lead
                # to interpreter crashes
                if filename and filename.lower().endswith("svg") or filetype and "svg" in filetype.lower():
                    try:
                        _ = self.convert_to_pdf()  # this seems to always work
                    except Exception as e:
                        if g_exceptions_verbose > 1:    exception_info()
                        raise FileDataError("cannot open broken document") from e

            if g_use_extra:
                self.this_is_pdf = isinstance( self.this, mupdf.PdfDocument)
                if self.this_is_pdf:
                    self.page_count2 = extra.page_count_pdf
                else:
                    self.page_count2 = extra.page_count_fz
        finally:
            JM_mupdf_show_errors = JM_mupdf_show_errors_old
    
    def __len__(self) -> int:
        return self.page_count

    def __repr__(self) -> str:
        m = "closed " if self.is_closed else ""
        if self.stream is None:
            if self.name == "":
                return m + "Document(<new PDF, doc# %i>)" % self._graft_id
            return m + "Document('%s')" % (self.name,)
        return m + "Document('%s', <memory, doc# %i>)" % (self.name, self._graft_id)

    def _addFormFont(self, name, font):
        """Add new form font."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self, required=0)
        if not pdf.m_internal:
            return
        fonts = mupdf.pdf_dict_getl(
                mupdf.pdf_trailer( pdf),
                PDF_NAME('Root'),
                PDF_NAME('AcroForm'),
                PDF_NAME('DR'),
                PDF_NAME('Font'),
                )
        if not fonts.m_internal or not mupdf.pdf_is_dict( fonts):
            raise RuntimeError( "PDF has no form fonts yet")
        k = mupdf.pdf_new_name( name)
        v = JM_pdf_obj_from_str( pdf, font)
        mupdf.pdf_dict_put( fonts, k, v)

    def _delToC(self):
        """Delete the TOC."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        xrefs = []  # create Python list
        pdf = _as_pdf_document(self, required=0)
        if not pdf.m_internal:
            return xrefs    # not a pdf
        # get the main root
        root = mupdf.pdf_dict_get(mupdf.pdf_trailer(pdf), PDF_NAME('Root'))
        # get the outline root
        olroot = mupdf.pdf_dict_get(root, PDF_NAME('Outlines'))
        if not olroot.m_internal:
            return xrefs    # no outlines or some problem

        first = mupdf.pdf_dict_get(olroot, PDF_NAME('First'))  # first outline

        xrefs = JM_outline_xrefs(first, xrefs)
        xref_count = len(xrefs)

        olroot_xref = mupdf.pdf_to_num(olroot) # delete OL root
        mupdf.pdf_delete_object(pdf, olroot_xref)  # delete OL root
        mupdf.pdf_dict_del(root, PDF_NAME('Outlines')) # delete OL root

        for i in range(xref_count):
            _, xref = JM_INT_ITEM(xrefs, i)
            mupdf.pdf_delete_object(pdf, xref) # delete outline item
        xrefs.append(olroot_xref)
        val = xrefs
        self.init_doc()
        return val

    def _delete_page(self, pno):
        pdf = _as_pdf_document(self)
        mupdf.pdf_delete_page( pdf, pno)
        if pdf.m_internal.rev_page_map:
            mupdf.ll_pdf_drop_page_tree( pdf.m_internal)

    def _deleteObject(self, xref):
        """Delete object."""
        pdf = _as_pdf_document(self)
        if not _INRANGE(xref, 1, mupdf.pdf_xref_len(pdf)-1):
            raise ValueError( MSG_BAD_XREF)
        mupdf.pdf_delete_object(pdf, xref)

    def _embeddedFileGet(self, idx):
        pdf = _as_pdf_document(self)
        names = mupdf.pdf_dict_getl(
                mupdf.pdf_trailer(pdf),
                PDF_NAME('Root'),
                PDF_NAME('Names'),
                PDF_NAME('EmbeddedFiles'),
                PDF_NAME('Names'),
                )
        entry = mupdf.pdf_array_get(names, 2*idx+1)
        filespec = mupdf.pdf_dict_getl(entry, PDF_NAME('EF'), PDF_NAME('F'))
        buf = mupdf.pdf_load_stream(filespec)
        cont = JM_BinFromBuffer(buf)
        return cont

    def _embeddedFileIndex(self, item: typing.Union[int, str]) -> int:
        filenames = self.embfile_names()
        msg = "'%s' not in EmbeddedFiles array." % str(item)
        if item in filenames:
            idx = filenames.index(item)
        elif item in range(len(filenames)):
            idx = item
        else:
            raise ValueError(msg)
        return idx

    def _embfile_add(self, name, buffer_, filename=None, ufilename=None, desc=None):
        pdf = _as_pdf_document(self)
        data = JM_BufferFromBytes(buffer_)
        if not data.m_internal:
            raise TypeError( MSG_BAD_BUFFER)

        names = mupdf.pdf_dict_getl(
                mupdf.pdf_trailer(pdf),
                PDF_NAME('Root'),
                PDF_NAME('Names'),
                PDF_NAME('EmbeddedFiles'),
                PDF_NAME('Names'),
                )
        if not mupdf.pdf_is_array(names):
            root = mupdf.pdf_dict_get(mupdf.pdf_trailer(pdf), PDF_NAME('Root'))
            names = mupdf.pdf_new_array(pdf, 6)    # an even number!
            mupdf.pdf_dict_putl(
                    root,
                    names,
                    PDF_NAME('Names'),
                    PDF_NAME('EmbeddedFiles'),
                    PDF_NAME('Names'),
                    )
        fileentry = JM_embed_file(pdf, data, filename, ufilename, desc, 1)
        xref = mupdf.pdf_to_num(
                mupdf.pdf_dict_getl(fileentry, PDF_NAME('EF'), PDF_NAME('F'))
                )
        mupdf.pdf_array_push(names, mupdf.pdf_new_text_string(name))
        mupdf.pdf_array_push(names, fileentry)
        return xref

    def _embfile_del(self, idx):
        pdf = _as_pdf_document(self)
        names = mupdf.pdf_dict_getl(
                mupdf.pdf_trailer(pdf),
                PDF_NAME('Root'),
                PDF_NAME('Names'),
                PDF_NAME('EmbeddedFiles'),
                PDF_NAME('Names'),
                )
        mupdf.pdf_array_delete(names, idx + 1)
        mupdf.pdf_array_delete(names, idx)

    def _embfile_info(self, idx, infodict):
        pdf = _as_pdf_document(self)
        xref = 0
        ci_xref=0

        trailer = mupdf.pdf_trailer(pdf)

        names = mupdf.pdf_dict_getl(
                trailer,
                PDF_NAME('Root'),
                PDF_NAME('Names'),
                PDF_NAME('EmbeddedFiles'),
                PDF_NAME('Names'),
                )
        o = mupdf.pdf_array_get(names, 2*idx+1)
        ci = mupdf.pdf_dict_get(o, PDF_NAME('CI'))
        if ci.m_internal:
            ci_xref = mupdf.pdf_to_num(ci)
        infodict["collection"] = ci_xref
        name = mupdf.pdf_to_text_string(mupdf.pdf_dict_get(o, PDF_NAME('F')))
        infodict[dictkey_filename] = JM_EscapeStrFromStr(name)

        name = mupdf.pdf_to_text_string(mupdf.pdf_dict_get(o, PDF_NAME('UF')))
        infodict[dictkey_ufilename] = JM_EscapeStrFromStr(name)

        name = mupdf.pdf_to_text_string(mupdf.pdf_dict_get(o, PDF_NAME('Desc')))
        infodict[dictkey_descr] = JM_UnicodeFromStr(name)

        len_ = -1
        DL = -1
        fileentry = mupdf.pdf_dict_getl(o, PDF_NAME('EF'), PDF_NAME('F'))
        xref = mupdf.pdf_to_num(fileentry)
        o = mupdf.pdf_dict_get(fileentry, PDF_NAME('Length'))
        if o.m_internal:
            len_ = mupdf.pdf_to_int(o)

        o = mupdf.pdf_dict_get(fileentry, PDF_NAME('DL'))
        if o.m_internal:
            DL = mupdf.pdf_to_int(o)
        else:
            o = mupdf.pdf_dict_getl(fileentry, PDF_NAME('Params'), PDF_NAME('Size'))
            if o.m_internal:
                DL = mupdf.pdf_to_int(o)
        infodict[dictkey_size] = DL
        infodict[dictkey_length] = len_
        return xref

    def _embfile_names(self, namelist):
        """Get list of embedded file names."""
        pdf = _as_pdf_document(self)
        names = mupdf.pdf_dict_getl(
                mupdf.pdf_trailer(pdf),
                PDF_NAME('Root'),
                PDF_NAME('Names'),
                PDF_NAME('EmbeddedFiles'),
                PDF_NAME('Names'),
                )
        if mupdf.pdf_is_array(names):
            n = mupdf.pdf_array_len(names)
            for i in range(0, n, 2):
                val = JM_EscapeStrFromStr(
                        mupdf.pdf_to_text_string(
                            mupdf.pdf_array_get(names, i)
                            )
                        )
                namelist.append(val)

    def _embfile_upd(self, idx, buffer_=None, filename=None, ufilename=None, desc=None):
        pdf = _as_pdf_document(self)
        xref = 0
        names = mupdf.pdf_dict_getl(
                mupdf.pdf_trailer(pdf),
                PDF_NAME('Root'),
                PDF_NAME('Names'),
                PDF_NAME('EmbeddedFiles'),
                PDF_NAME('Names'),
                )
        entry = mupdf.pdf_array_get(names, 2*idx+1)

        filespec = mupdf.pdf_dict_getl(entry, PDF_NAME('EF'), PDF_NAME('F'))
        if not filespec.m_internal:
            RAISEPY( "bad PDF: no /EF object", JM_Exc_FileDataError)
        res = JM_BufferFromBytes(buffer_)
        if buffer_ and buffer_.m_internal and not res.m_internal:
            raise TypeError( MSG_BAD_BUFFER)
        if res.m_internal and buffer_ and buffer_.m_internal:
            JM_update_stream(pdf, filespec, res, 1)
            # adjust /DL and /Size parameters
            len, _ = mupdf.fz_buffer_storage(res)
            l = mupdf.pdf_new_int(len)
            mupdf.pdf_dict_put(filespec, PDF_NAME('DL'), l)
            mupdf.pdf_dict_putl(filespec, l, PDF_NAME('Params'), PDF_NAME('Size'))
        xref = mupdf.pdf_to_num(filespec)
        if filename:
            mupdf.pdf_dict_put_text_string(entry, PDF_NAME('F'), filename)

        if ufilename:
            mupdf.pdf_dict_put_text_string(entry, PDF_NAME('UF'), ufilename)

        if desc:
            mupdf.pdf_dict_put_text_string(entry, PDF_NAME('Desc'), desc)
        return xref

    def _extend_toc_items(self, items):
        """Add color info to all items of an extended TOC list."""
        if self.is_closed:
            raise ValueError("document closed")
        if g_use_extra:
            return extra.Document_extend_toc_items( self.this, items)
        pdf = _as_pdf_document(self)
        zoom = "zoom"
        bold = "bold"
        italic = "italic"
        collapse = "collapse"

        root = mupdf.pdf_dict_get(mupdf.pdf_trailer(pdf), PDF_NAME('Root'))
        if not root.m_internal:
            return
        olroot = mupdf.pdf_dict_get(root, PDF_NAME('Outlines'))
        if not olroot.m_internal:
            return
        first = mupdf.pdf_dict_get(olroot, PDF_NAME('First'))
        if not first.m_internal:
            return
        xrefs = []
        xrefs = JM_outline_xrefs(first, xrefs)
        n = len(xrefs)
        m = len(items)
        if not n:
            return
        if n != m:
            raise IndexError( "internal error finding outline xrefs")

        # update all TOC item dictionaries
        for i in range(n):
            xref = int(xrefs[i])
            item = items[i]
            itemdict = item[3]
            if not isinstance(itemdict, dict):
                raise ValueError( "need non-simple TOC format")
            itemdict[dictkey_xref] = xrefs[i]
            bm = mupdf.pdf_load_object(pdf, xref)
            flags = mupdf.pdf_to_int( mupdf.pdf_dict_get(bm, PDF_NAME('F')))
            if flags == 1:
                itemdict[italic] = True
            elif flags == 2:
                itemdict[bold] = True
            elif flags == 3:
                itemdict[italic] = True
                itemdict[bold] = True
            count = mupdf.pdf_to_int( mupdf.pdf_dict_get(bm, PDF_NAME('Count')))
            if count < 0:
                itemdict[collapse] = True
            elif count > 0:
                itemdict[collapse] = False
            col = mupdf.pdf_dict_get(bm, PDF_NAME('C'))
            if mupdf.pdf_is_array(col) and mupdf.pdf_array_len(col) == 3:
                color = (
                        mupdf.pdf_to_real(mupdf.pdf_array_get(col, 0)),
                        mupdf.pdf_to_real(mupdf.pdf_array_get(col, 1)),
                        mupdf.pdf_to_real(mupdf.pdf_array_get(col, 2)),
                        )
                itemdict[dictkey_color] = color
            z=0
            obj = mupdf.pdf_dict_get(bm, PDF_NAME('Dest'))
            if not obj.m_internal or not mupdf.pdf_is_array(obj):
                obj = mupdf.pdf_dict_getl(bm, PDF_NAME('A'), PDF_NAME('D'))
            if mupdf.pdf_is_array(obj) and mupdf.pdf_array_len(obj) == 5:
                z = mupdf.pdf_to_real(mupdf.pdf_array_get(obj, 4))
            itemdict[zoom] = float(z)
            item[3] = itemdict
            items[i] = item

    def _forget_page(self, page: Page):
        """Remove a page from document page dict."""
        pid = id(page)
        if pid in self._page_refs:
            #self._page_refs[pid] = None
            del self._page_refs[pid]

    def _get_char_widths(self, xref: int, bfname: str, ext: str, ordering: int, limit: int, idx: int = 0):
        pdf = _as_pdf_document(self)
        mylimit = limit
        if mylimit < 256:
            mylimit = 256
        if ordering >= 0:
            data, size, index = mupdf.fz_lookup_cjk_font(ordering)
            font = mupdf.fz_new_font_from_memory(None, data, size, index, 0)
        else:
            data, size = mupdf.fz_lookup_base14_font(bfname)
            if data:
                font = mupdf.fz_new_font_from_memory(bfname, data, size, 0, 0)
            else:
                buf = JM_get_fontbuffer(pdf, xref)
                if not buf.m_internal:
                    raise Exception("font at xref %d is not supported" % xref)

                font = mupdf.fz_new_font_from_buffer(None, buf, idx, 0)
        wlist = []
        for i in range(mylimit):
            glyph = mupdf.fz_encode_character(font, i)
            adv = mupdf.fz_advance_glyph(font, glyph, 0)
            if ordering >= 0:
                glyph = i
            if glyph > 0:
                wlist.append( (glyph, adv))
            else:
                wlist.append( (glyph, 0.0))
        return wlist

    def _get_page_labels(self):
        pdf = _as_pdf_document(self)
        rc = []
        pagelabels = mupdf.pdf_new_name("PageLabels")
        obj = mupdf.pdf_dict_getl( mupdf.pdf_trailer(pdf), PDF_NAME('Root'), pagelabels)
        if not obj.m_internal:
            return rc
        # simple case: direct /Nums object
        nums = mupdf.pdf_resolve_indirect( mupdf.pdf_dict_get( obj, PDF_NAME('Nums')))
        if nums.m_internal:
            JM_get_page_labels(rc, nums)
            return rc
        # case: /Kids/Nums
        nums = mupdf.pdf_resolve_indirect( mupdf.pdf_dict_getl(obj, PDF_NAME('Kids'), PDF_NAME('Nums')))
        if nums.m_internal:
            JM_get_page_labels(rc, nums)
            return rc
        # case: /Kids is an array of multiple /Nums
        kids = mupdf.pdf_resolve_indirect( mupdf.pdf_dict_get( obj, PDF_NAME('Kids')))
        if not kids.m_internal or not mupdf.pdf_is_array(kids):
            return rc
        n = mupdf.pdf_array_len(kids)
        for i in range(n):
            nums = mupdf.pdf_resolve_indirect(
                    mupdf.pdf_dict_get( mupdf.pdf_array_get(kids, i)),
                    PDF_NAME('Nums'),
                    )
            JM_get_page_labels(rc, nums)
        return rc

    def _getMetadata(self, key):
        """Get metadata."""
        try:
            return mupdf.fz_lookup_metadata2( self.this, key)
        except Exception:
            if g_exceptions_verbose > 2:    exception_info()
            return ''

    def _getOLRootNumber(self):
        """Get xref of Outline Root, create it if missing."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        # get main root
        root = mupdf.pdf_dict_get( mupdf.pdf_trailer( pdf), PDF_NAME('Root'))
        # get outline root
        olroot = mupdf.pdf_dict_get( root, PDF_NAME('Outlines'))
        if not olroot.m_internal:
            olroot = mupdf.pdf_new_dict( pdf, 4)
            mupdf.pdf_dict_put( olroot, PDF_NAME('Type'), PDF_NAME('Outlines'))
            ind_obj = mupdf.pdf_add_object( pdf, olroot)
            mupdf.pdf_dict_put( root, PDF_NAME('Outlines'), ind_obj)
            olroot = mupdf.pdf_dict_get( root, PDF_NAME('Outlines'))
        return mupdf.pdf_to_num( olroot)

    def _getPDFfileid(self):
        """Get PDF file id."""
        pdf = _as_pdf_document(self, required=0)
        if not pdf.m_internal:
            return
        idlist = []
        identity = mupdf.pdf_dict_get(mupdf.pdf_trailer(pdf), PDF_NAME('ID'))
        if identity.m_internal:
            n = mupdf.pdf_array_len(identity)
            for i in range(n):
                o = mupdf.pdf_array_get(identity, i)
                text = mupdf.pdf_to_text_string(o)
                hex_ = binascii.hexlify(text)
                idlist.append(hex_)
        return idlist

    def _getPageInfo(self, pno, what):
        """List fonts, images, XObjects used on a page."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        doc = self.this
        pageCount = mupdf.pdf_count_pages(doc) if isinstance(doc, mupdf.PdfDocument) else mupdf.fz_count_pages(doc)
        n = pno  # pno < 0 is allowed
        while n < 0:
            n += pageCount  # make it non-negative
        if n >= pageCount:
            raise ValueError( MSG_BAD_PAGENO)
        pdf = _as_pdf_document(self)
        pageref = mupdf.pdf_lookup_page_obj(pdf, n)
        rsrc = mupdf.pdf_dict_get_inheritable(pageref, mupdf.PDF_ENUM_NAME_Resources)
        liste = []
        tracer = []
        if rsrc.m_internal:
            JM_scan_resources(pdf, rsrc, liste, what, 0, tracer)
        return liste

    def _insert_font(self, fontfile=None, fontbuffer=None):
        '''
        Utility: insert font from file or binary.
        '''
        pdf = _as_pdf_document(self)
        if not fontfile and not fontbuffer:
            raise ValueError( MSG_FILE_OR_BUFFER)
        value = JM_insert_font(pdf, None, fontfile, fontbuffer, 0, 0, 0, 0, 0, -1)
        return value

    def _loadOutline(self):
        """Load first outline."""
        doc = self.this
        assert isinstance( doc, mupdf.FzDocument)
        try:
            ol = mupdf.fz_load_outline( doc)
        except Exception:
            if g_exceptions_verbose > 1:    exception_info()
            return
        return Outline( ol)

    def _make_page_map(self):
        """Make an array page number -> page object."""
        if self.is_closed:
            raise ValueError("document closed")
        assert 0, f'_make_page_map() is no-op'

    def _move_copy_page(self, pno, nb, before, copy):
        """Move or copy a PDF page reference."""
        pdf = _as_pdf_document(self)
        same = 0
        # get the two page objects -----------------------------------
        # locate the /Kids arrays and indices in each

        page1, parent1, i1 = pdf_lookup_page_loc( pdf, pno)

        kids1 = mupdf.pdf_dict_get( parent1, PDF_NAME('Kids'))

        page2, parent2, i2 = pdf_lookup_page_loc( pdf, nb)
        kids2 = mupdf.pdf_dict_get( parent2, PDF_NAME('Kids'))
        if before:  # calc index of source page in target /Kids
            pos = i2
        else:
            pos = i2 + 1

        # same /Kids array? ------------------------------------------
        same = mupdf.pdf_objcmp( kids1, kids2)

        # put source page in target /Kids array ----------------------
        if not copy and same != 0:  # update parent in page object
            mupdf.pdf_dict_put( page1, PDF_NAME('Parent'), parent2)
        mupdf.pdf_array_insert( kids2, page1, pos)

        if same != 0:   # different /Kids arrays ----------------------
            parent = parent2
            while parent.m_internal:    # increase /Count objects in parents
                count = mupdf.pdf_dict_get_int( parent, PDF_NAME('Count'))
                mupdf.pdf_dict_put_int( parent, PDF_NAME('Count'), count + 1)
                parent = mupdf.pdf_dict_get( parent, PDF_NAME('Parent'))
            if not copy:    # delete original item
                mupdf.pdf_array_delete( kids1, i1)
                parent = parent1
                while parent.m_internal:    # decrease /Count objects in parents
                    count = mupdf.pdf_dict_get_int( parent, PDF_NAME('Count'))
                    mupdf.pdf_dict_put_int( parent, PDF_NAME('Count'), count - 1)
                    parent = mupdf.pdf_dict_get( parent, PDF_NAME('Parent'))
        else:   # same /Kids array
            if copy:    # source page is copied
                parent = parent2
                while parent.m_internal:    # increase /Count object in parents
                    count = mupdf.pdf_dict_get_int( parent, PDF_NAME('Count'))
                    mupdf.pdf_dict_put_int( parent, PDF_NAME('Count'), count + 1)
                    parent = mupdf.pdf_dict_get( parent, PDF_NAME('Parent'))
            else:
                if i1 < pos:
                    mupdf.pdf_array_delete( kids1, i1)
                else:
                    mupdf.pdf_array_delete( kids1, i1 + 1)
        if pdf.m_internal.rev_page_map: # page map no longer valid: drop it
            mupdf.ll_pdf_drop_page_tree( pdf.m_internal)

        self._reset_page_refs()

    def _newPage(self, pno=-1, width=595, height=842):
        """Make a new PDF page."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        if g_use_extra:
            extra._newPage( self.this, pno, width, height)
        else:
            pdf = _as_pdf_document(self)
            mediabox = mupdf.FzRect(mupdf.FzRect.Fixed_UNIT)
            mediabox.x1 = width
            mediabox.y1 = height
            contents = mupdf.FzBuffer()
            if pno < -1:
                raise ValueError( MSG_BAD_PAGENO)
            # create /Resources and /Contents objects
            #resources = pdf.add_object(pdf.new_dict(1))
            resources = mupdf.pdf_add_new_dict(pdf, 1)
            page_obj = mupdf.pdf_add_page( pdf, mediabox, 0, resources, contents)
            mupdf.pdf_insert_page( pdf, pno, page_obj)
        # fixme: pdf->dirty = 1;

        self._reset_page_refs()
        return self[pno]

    def _remove_links_to(self, numbers):
        pdf = _as_pdf_document(self)
        _remove_dest_range(pdf, numbers)

    def _remove_toc_item(self, xref):
        # "remove" bookmark by letting it point to nowhere
        pdf = _as_pdf_document(self)
        item = mupdf.pdf_new_indirect(pdf, xref, 0)
        mupdf.pdf_dict_del( item, PDF_NAME('Dest'))
        mupdf.pdf_dict_del( item, PDF_NAME('A'))
        color = mupdf.pdf_new_array( pdf, 3)
        for i in range(3):
            mupdf.pdf_array_push_real( color, 0.8)
        mupdf.pdf_dict_put( item, PDF_NAME('C'), color)

    def _reset_page_refs(self):
        """Invalidate all pages in document dictionary."""
        if getattr(self, "is_closed", True):
            return
        pages = [p for p in self._page_refs.values()]
        for page in pages:
            if page:
                page._erase()
                page = None
        self._page_refs.clear()

    def _set_page_labels(self, labels):
        pdf = _as_pdf_document(self)
        pagelabels = mupdf.pdf_new_name("PageLabels")
        root = mupdf.pdf_dict_get(mupdf.pdf_trailer(pdf), PDF_NAME('Root'))
        mupdf.pdf_dict_del(root, pagelabels)
        mupdf.pdf_dict_putl(root, mupdf.pdf_new_array(pdf, 0), pagelabels, PDF_NAME('Nums'))

        xref = self.pdf_catalog()
        text = self.xref_object(xref, compressed=True)
        text = text.replace("/Nums[]", "/Nums[%s]" % labels)
        self.update_object(xref, text)

    def _update_toc_item(self, xref, action=None, title=None, flags=0, collapse=None, color=None):
        '''
        "update" bookmark by letting it point to nowhere
        '''
        pdf = _as_pdf_document(self)
        item = mupdf.pdf_new_indirect( pdf, xref, 0)
        if title:
            mupdf.pdf_dict_put_text_string( item, PDF_NAME('Title'), title)
        if action:
            mupdf.pdf_dict_del( item, PDF_NAME('Dest'))
            obj = JM_pdf_obj_from_str( pdf, action)
            mupdf.pdf_dict_put( item, PDF_NAME('A'), obj)
        mupdf.pdf_dict_put_int( item, PDF_NAME('F'), flags)
        if color:
            c = mupdf.pdf_new_array( pdf, 3)
            for i in range(3):
                f = color[i]
                mupdf.pdf_array_push_real( c, f)
            mupdf.pdf_dict_put( item, PDF_NAME('C'), c)
        elif color is not None:
            mupdf.pdf_dict_del( item, PDF_NAME('C'))
        if collapse is not None:
            if mupdf.pdf_dict_get( item, PDF_NAME('Count')).m_internal:
                i = mupdf.pdf_dict_get_int( item, PDF_NAME('Count'))
                if (i < 0 and collapse is False) or (i > 0 and collapse is True):
                    i = i * (-1)
                    mupdf.pdf_dict_put_int( item, PDF_NAME('Count'), i)

    @property
    def FormFonts(self):
        """Get list of field font resource names."""
        pdf = _as_pdf_document(self, required=0)
        if not pdf.m_internal:
            return
        fonts = mupdf.pdf_dict_getl(
                mupdf.pdf_trailer(pdf),
                PDF_NAME('Root'),
                PDF_NAME('AcroForm'),
                PDF_NAME('DR'),
                PDF_NAME('Font'),
                )
        liste = list()
        if fonts.m_internal and mupdf.pdf_is_dict(fonts):   # fonts exist
            n = mupdf.pdf_dict_len(fonts)
            for i in range(n):
                f = mupdf.pdf_dict_get_key(fonts, i)
                liste.append(JM_UnicodeFromStr(mupdf.pdf_to_name(f)))
        return liste

    def add_layer(self, name, creator=None, on=None):
        """Add a new OC layer."""
        pdf = _as_pdf_document(self)
        JM_add_layer_config( pdf, name, creator, on)
        mupdf.ll_pdf_read_ocg( pdf.m_internal)

    def add_ocg(self, name, config=-1, on=1, intent=None, usage=None):
        """Add new optional content group."""
        xref = 0
        pdf = _as_pdf_document(self)

        # make the OCG
        ocg = mupdf.pdf_add_new_dict(pdf, 3)
        mupdf.pdf_dict_put(ocg, PDF_NAME('Type'), PDF_NAME('OCG'))
        mupdf.pdf_dict_put_text_string(ocg, PDF_NAME('Name'), name)
        intents = mupdf.pdf_dict_put_array(ocg, PDF_NAME('Intent'), 2)
        if not intent:
            mupdf.pdf_array_push(intents, PDF_NAME('View'))
        elif not isinstance(intent, str):
            assert 0, f'fixme: intent is not a str. {type(intent)=} {type=}'
            #n = len(intent)
            #for i in range(n):
            #    item = intent[i]
            #    c = JM_StrAsChar(item);
            #    if (c) {
            #        pdf_array_push(gctx, intents, pdf_new_name(gctx, c));
            #    }
            #    Py_DECREF(item);
            #}
        else:
            mupdf.pdf_array_push(intents, mupdf.pdf_new_name(intent))
        use_for = mupdf.pdf_dict_put_dict(ocg, PDF_NAME('Usage'), 3)
        ci_name = mupdf.pdf_new_name("CreatorInfo")
        cre_info = mupdf.pdf_dict_put_dict(use_for, ci_name, 2)
        mupdf.pdf_dict_put_text_string(cre_info, PDF_NAME('Creator'), "PyMuPDF")
        if usage:
            mupdf.pdf_dict_put_name(cre_info, PDF_NAME('Subtype'), usage)
        else:
            mupdf.pdf_dict_put_name(cre_info, PDF_NAME('Subtype'), "Artwork")
        indocg = mupdf.pdf_add_object(pdf, ocg)

        # Insert OCG in the right config
        ocp = JM_ensure_ocproperties(pdf)
        obj = mupdf.pdf_dict_get(ocp, PDF_NAME('OCGs'))
        mupdf.pdf_array_push(obj, indocg)

        if config > -1:
            obj = mupdf.pdf_dict_get(ocp, PDF_NAME('Configs'))
            if not mupdf.pdf_is_array(obj):
                raise ValueError( MSG_BAD_OC_CONFIG)
            cfg = mupdf.pdf_array_get(obj, config)
            if not cfg.m_internal:
                raise ValueError( MSG_BAD_OC_CONFIG)
        else:
            cfg = mupdf.pdf_dict_get(ocp, PDF_NAME('D'))

        obj = mupdf.pdf_dict_get(cfg, PDF_NAME('Order'))
        if not obj.m_internal:
            obj = mupdf.pdf_dict_put_array(cfg, PDF_NAME('Order'), 1)
        mupdf.pdf_array_push(obj, indocg)
        if on:
            obj = mupdf.pdf_dict_get(cfg, PDF_NAME('ON'))
            if not obj.m_internal:
                obj = mupdf.pdf_dict_put_array(cfg, PDF_NAME('ON'), 1)
        else:
            obj =mupdf.pdf_dict_get(cfg, PDF_NAME('OFF'))
            if not obj.m_internal:
                obj =mupdf.pdf_dict_put_array(cfg, PDF_NAME('OFF'), 1)
        mupdf.pdf_array_push(obj, indocg)

        # let MuPDF take note: re-read OCProperties
        mupdf.ll_pdf_read_ocg(pdf.m_internal)

        xref = mupdf.pdf_to_num(indocg)
        return xref

    def authenticate(self, password):
        """Decrypt document."""
        if self.is_closed:
            raise ValueError("document closed")
        val = mupdf.fz_authenticate_password(self.this, password)
        if val:  # the doc is decrypted successfully and we init the outline
            self.is_encrypted = False
            self.is_encrypted = False
            self.init_doc()
            self.thisown = True
        return val

    def can_save_incrementally(self):
        """Check whether incremental saves are possible."""
        pdf = _as_pdf_document(self, required=0)
        if not pdf.m_internal:
            return False
        return mupdf.pdf_can_be_saved_incrementally(pdf)

    def bake(self, *, annots: bool = True, widgets: bool = True) -> None:
        """Convert annotations or fields to permanent content.

        Notes:
            Converts annotations or widgets to permanent page content, like
            text and vector graphics, as appropriate.
            After execution, pages will still look the same, but no longer
            have annotations, respectively no fields.
            If widgets are selected the PDF will no longer be a Form PDF.

        Args:
            annots: convert annotations
            widgets: convert form fields

        """
        pdf = _as_pdf_document(self)
        mupdf.pdf_bake_document(pdf, int(annots), int(widgets))

    @property
    def chapter_count(self):
        """Number of chapters."""
        if self.is_closed:
            raise ValueError("document closed")
        return mupdf.fz_count_chapters( self.this)

    def chapter_page_count(self, chapter):
        """Page count of chapter."""
        if self.is_closed:
            raise ValueError("document closed")
        chapters = mupdf.fz_count_chapters( self.this)
        if chapter < 0 or chapter >= chapters:
            raise ValueError( "bad chapter number")
        pages = mupdf.fz_count_chapter_pages( self.this, chapter)
        return pages

    def close(self):
        """Close document."""
        if getattr(self, "is_closed", True):
            raise ValueError("document closed")
        # self._cleanup()
        if hasattr(self, "_outline") and self._outline:
            self._outline = None
        self._reset_page_refs()
        #self.metadata    = None
        #self.stream      = None
        self.is_closed    = True
        #self.FontInfos   = []
        self.Graftmaps = {} # Fixes test_3140().
        #self.ShownPages = {}
        #self.InsertedImages  = {}
        #self.this = None
        self.this = None

    def convert_to_pdf(self, from_page=0, to_page=-1, rotate=0):
        """Convert document to a PDF, selecting page range and optional rotation. Output bytes object."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        fz_doc = self.this
        fp = from_page
        tp = to_page
        srcCount = mupdf.fz_count_pages(fz_doc)
        if fp < 0:
            fp = 0
        if fp > srcCount - 1:
            fp = srcCount - 1
        if tp < 0:
            tp = srcCount - 1
        if tp > srcCount - 1:
            tp = srcCount - 1
        len0 = len(JM_mupdf_warnings_store)
        doc = JM_convert_to_pdf(fz_doc, fp, tp, rotate)
        len1 = len(JM_mupdf_warnings_store)
        for i in range(len0, len1):
            message(f'{JM_mupdf_warnings_store[i]}')
        return doc

    def copy_page(self, pno: int, to: int =-1):
        """Copy a page within a PDF document.

        This will only create another reference of the same page object.
        Args:
            pno: source page number
            to: put before this page, '-1' means after last page.
        """
        if self.is_closed:
            raise ValueError("document closed")

        page_count = len(self)
        if (
                pno not in range(page_count)
                or to not in range(-1, page_count)
                ):
            raise ValueError("bad page number(s)")
        before = 1
        copy = 1
        if to == -1:
            to = page_count - 1
            before = 0

        return self._move_copy_page(pno, to, before, copy)

    def del_xml_metadata(self):
        """Delete XML metadata."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        root = mupdf.pdf_dict_get( mupdf.pdf_trailer( pdf), PDF_NAME('Root'))
        if root.m_internal:
            mupdf.pdf_dict_del( root, PDF_NAME('Metadata'))

    def delete_page(self, pno: int =-1):
        """ Delete one page from a PDF.
        """
        if not self.is_pdf:
            raise ValueError("is no PDF")
        if self.is_closed:
            raise ValueError("document closed")

        page_count = self.page_count
        while pno < 0:
            pno += page_count

        if pno >= page_count:
            raise ValueError("bad page number(s)")

        # remove TOC bookmarks pointing to deleted page
        toc = self.get_toc()
        ol_xrefs = self.get_outline_xrefs()
        for i, item in enumerate(toc):
            if item[2] == pno + 1:
                self._remove_toc_item(ol_xrefs[i])

        self._remove_links_to(frozenset((pno,)))
        self._delete_page(pno)
        self._reset_page_refs()

    def delete_pages(self, *args, **kw):
        """Delete pages from a PDF.

        Args:
            Either keywords 'from_page'/'to_page', or two integers to
            specify the first/last page to delete.
            Or a list/tuple/range object, which can contain arbitrary
            page numbers.
        """
        if not self.is_pdf:
            raise ValueError("is no PDF")
        if self.is_closed:
            raise ValueError("document closed")

        page_count = self.page_count  # page count of document
        f = t = -1
        if kw:  # check if keywords were used
            if args:  # then no positional args are allowed
                raise ValueError("cannot mix keyword and positional argument")
            f = kw.get("from_page", -1)  # first page to delete
            t = kw.get("to_page", -1)  # last page to delete
            while f < 0:
                f += page_count
            while t < 0:
                t += page_count
            if not f <= t < page_count:
                raise ValueError("bad page number(s)")
            numbers = tuple(range(f, t + 1))
        else:
            if len(args) > 2 or args == []:
                raise ValueError("need 1 or 2 positional arguments")
            if len(args) == 2:
                f, t = args
                if not (type(f) is int and type(t) is int):
                    raise ValueError("both arguments must be int")
                if f > t:
                    f, t = t, f
                if not f <= t < page_count:
                    raise ValueError("bad page number(s)")
                numbers = tuple(range(f, t + 1))
            else:
                r = args[0]
                if type(r) not in (int, range, list, tuple):
                    raise ValueError("need int or sequence if one argument")
                numbers = tuple(r)

        numbers = list(map(int, set(numbers)))  # ensure unique integers
        if numbers == []:
            message("nothing to delete")
            return
        numbers.sort()
        if numbers[0] < 0 or numbers[-1] >= page_count:
            raise ValueError("bad page number(s)")
        frozen_numbers = frozenset(numbers)
        toc = self.get_toc()
        for i, xref in enumerate(self.get_outline_xrefs()):
            if toc[i][2] - 1 in frozen_numbers:
                self._remove_toc_item(xref)  # remove target in PDF object

        self._remove_links_to(frozen_numbers)

        for i in reversed(numbers):  # delete pages, last to first
            self._delete_page(i)

        self._reset_page_refs()

    def embfile_add(self,
            name: str,
            buffer_: typing.ByteString,
            filename: OptStr =None,
            ufilename: OptStr =None,
            desc: OptStr =None,
            ) -> None:
        """Add an item to the EmbeddedFiles array.

        Args:
            name: name of the new item, must not already exist.
            buffer_: (binary data) the file content.
            filename: (str) the file name, default: the name
            ufilename: (unicode) the file name, default: filename
            desc: (str) the description.
        """
        filenames = self.embfile_names()
        msg = "Name '%s' already exists." % str(name)
        if name in filenames:
            raise ValueError(msg)

        if filename is None:
            filename = name
        if ufilename is None:
            ufilename = filename
        if desc is None:
            desc = name
        xref = self._embfile_add(
                name,
                buffer_=buffer_,
                filename=filename,
                ufilename=ufilename,
                desc=desc,
                )
        date = get_pdf_now()
        self.xref_set_key(xref, "Type", "/EmbeddedFile")
        self.xref_set_key(xref, "Params/CreationDate", get_pdf_str(date))
        self.xref_set_key(xref, "Params/ModDate", get_pdf_str(date))
        return xref

    def embfile_count(self) -> int:
        """Get number of EmbeddedFiles."""
        return len(self.embfile_names())

    def embfile_del(self, item: typing.Union[int, str]):
        """Delete an entry from EmbeddedFiles.

        Notes:
            The argument must be name or index of an EmbeddedFiles item.
            Physical deletion of data will happen on save to a new
            file with appropriate garbage option.
        Args:
            item: name or number of item.
        Returns:
            None
        """
        idx = self._embeddedFileIndex(item)
        return self._embfile_del(idx)

    def embfile_get(self, item: typing.Union[int, str]) -> bytes:
        """Get the content of an item in the EmbeddedFiles array.

        Args:
            item: number or name of item.
        Returns:
            (bytes) The file content.
        """
        idx = self._embeddedFileIndex(item)
        return self._embeddedFileGet(idx)

    def embfile_info(self, item: typing.Union[int, str]) -> dict:
        """Get information of an item in the EmbeddedFiles array.

        Args:
            item: number or name of item.
        Returns:
            Information dictionary.
        """
        idx = self._embeddedFileIndex(item)
        infodict = {"name": self.embfile_names()[idx]}
        xref = self._embfile_info(idx, infodict)
        t, date = self.xref_get_key(xref, "Params/CreationDate")
        if t != "null":
            infodict["creationDate"] = date
        t, date = self.xref_get_key(xref, "Params/ModDate")
        if t != "null":
            infodict["modDate"] = date
        t, md5 = self.xref_get_key(xref, "Params/CheckSum")
        if t != "null":
            infodict["checksum"] = binascii.hexlify(md5.encode()).decode()
        return infodict

    def embfile_names(self) -> list:
        """Get list of names of EmbeddedFiles."""
        filenames = []
        self._embfile_names(filenames)
        return filenames

    def embfile_upd(self,
            item: typing.Union[int, str],
            buffer_: OptBytes =None,
            filename: OptStr =None,
            ufilename: OptStr =None,
            desc: OptStr =None,
            ) -> None:
        """Change an item of the EmbeddedFiles array.

        Notes:
            Only provided parameters are changed. If all are omitted,
            the method is a no-op.
        Args:
            item: number or name of item.
            buffer_: (binary data) the new file content.
            filename: (str) the new file name.
            ufilename: (unicode) the new filen ame.
            desc: (str) the new description.
        """
        idx = self._embeddedFileIndex(item)
        xref = self._embfile_upd(
                idx,
                buffer_=buffer_,
                filename=filename,
                ufilename=ufilename,
                desc=desc,
                )
        date = get_pdf_now()
        self.xref_set_key(xref, "Params/ModDate", get_pdf_str(date))
        return xref

    def extract_font(self, xref=0, info_only=0, named=None):
        '''
        Get a font by xref. Returns a tuple or dictionary.
        '''
        #log( '{=xref info_only}')
        pdf = _as_pdf_document(self)
        obj = mupdf.pdf_load_object(pdf, xref)
        type_ = mupdf.pdf_dict_get(obj, PDF_NAME('Type'))
        subtype = mupdf.pdf_dict_get(obj, PDF_NAME('Subtype'))
        if (mupdf.pdf_name_eq(type_, PDF_NAME('Font'))
                and not mupdf.pdf_to_name( subtype).startswith('CIDFontType')
                ):
            basefont = mupdf.pdf_dict_get(obj, PDF_NAME('BaseFont'))
            if not basefont.m_internal or mupdf.pdf_is_null(basefont):
                bname = mupdf.pdf_dict_get(obj, PDF_NAME('Name'))
            else:
                bname = basefont
            ext = JM_get_fontextension(pdf, xref)
            if ext != 'n/a' and not info_only:
                buffer_ = JM_get_fontbuffer(pdf, xref)
                bytes_ = JM_BinFromBuffer(buffer_)
            else:
                bytes_ = b''
            if not named:
                rc = (
                        JM_EscapeStrFromStr(mupdf.pdf_to_name(bname)),
                        JM_UnicodeFromStr(ext),
                        JM_UnicodeFromStr(mupdf.pdf_to_name(subtype)),
                        bytes_,
                        )
            else:
                rc = {
                        dictkey_name: JM_EscapeStrFromStr(mupdf.pdf_to_name(bname)),
                        dictkey_ext: JM_UnicodeFromStr(ext),
                        dictkey_type: JM_UnicodeFromStr(mupdf.pdf_to_name(subtype)),
                        dictkey_content: bytes_,
                        }
        else:
            if not named:
                rc = '', '', '', b''
            else:
                rc = {
                        dictkey_name: '',
                        dictkey_ext: '',
                        dictkey_type: '',
                        dictkey_content: b'',
                        }
        return rc

    def extract_image(self, xref):
        """Get image by xref. Returns a dictionary."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")

        pdf = _as_pdf_document(self)

        if not _INRANGE(xref, 1, mupdf.pdf_xref_len(pdf)-1):
            raise ValueError( MSG_BAD_XREF)

        obj = mupdf.pdf_new_indirect(pdf, xref, 0)
        subtype = mupdf.pdf_dict_get(obj, PDF_NAME('Subtype'))

        if not mupdf.pdf_name_eq(subtype, PDF_NAME('Image')):
            raise ValueError( "not an image")

        o = mupdf.pdf_dict_geta(obj, PDF_NAME('SMask'), PDF_NAME('Mask'))
        if o.m_internal:
            smask = mupdf.pdf_to_num(o)
        else:
            smask = 0

        # load the image
        img = mupdf.pdf_load_image(pdf, obj)
        rc = dict()
        _make_image_dict(img, rc)
        rc[dictkey_smask] = smask
        rc[dictkey_cs_name] = mupdf.fz_colorspace_name(img.colorspace())
        return rc

    def ez_save(
            self,
            filename,
            garbage=3,
            clean=False,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            incremental=False,
            ascii=False,
            expand=False,
            linear=False,
            pretty=False,
            encryption=1,
            permissions=4095,
            owner_pw=None,
            user_pw=None,
            no_new_id=True,
            preserve_metadata=1,
            use_objstms=1,
            compression_effort=0,
            ):
        '''
        Save PDF using some different defaults
        '''
        return self.save(
                filename,
                garbage=garbage,
                clean=clean,
                deflate=deflate,
                deflate_images=deflate_images,
                deflate_fonts=deflate_fonts,
                incremental=incremental,
                ascii=ascii,
                expand=expand,
                linear=linear,
                pretty=pretty,
                encryption=encryption,
                permissions=permissions,
                owner_pw=owner_pw,
                user_pw=user_pw,
                no_new_id=no_new_id,
                preserve_metadata=preserve_metadata,
                use_objstms=use_objstms,
                compression_effort=compression_effort,
                )

    def find_bookmark(self, bm):
        """Find new location after layouting a document."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        location = mupdf.fz_lookup_bookmark2( self.this, bm)
        return location.chapter, location.page

    def fullcopy_page(self, pno, to=-1):
        """Make a full page duplicate."""
        pdf = _as_pdf_document(self)
        page_count = mupdf.pdf_count_pages( pdf)
        try:
            if (not _INRANGE(pno, 0, page_count - 1)
                    or not _INRANGE(to, -1, page_count - 1)
                    ):
                raise ValueError( MSG_BAD_PAGENO)

            page1 = mupdf.pdf_resolve_indirect( mupdf.pdf_lookup_page_obj( pdf, pno))

            page2 = mupdf.pdf_deep_copy_obj( page1)
            old_annots = mupdf.pdf_dict_get( page2, PDF_NAME('Annots'))

            # copy annotations, but remove Popup and IRT types
            if old_annots.m_internal:
                n = mupdf.pdf_array_len( old_annots)
                new_annots = mupdf.pdf_new_array( pdf, n)
                for i in range(n):
                    o = mupdf.pdf_array_get( old_annots, i)
                    subtype = mupdf.pdf_dict_get( o, PDF_NAME('Subtype'))
                    if mupdf.pdf_name_eq( subtype, PDF_NAME('Popup')):
                        continue
                    if mupdf.pdf_dict_gets( o, "IRT").m_internal:
                        continue
                    copy_o = mupdf.pdf_deep_copy_obj( mupdf.pdf_resolve_indirect( o))
                    xref = mupdf.pdf_create_object( pdf)
                    mupdf.pdf_update_object( pdf, xref, copy_o)
                    copy_o = mupdf.pdf_new_indirect( pdf, xref, 0)
                    mupdf.pdf_dict_del( copy_o, PDF_NAME('Popup'))
                    mupdf.pdf_dict_del( copy_o, PDF_NAME('P'))
                    mupdf.pdf_array_push( new_annots, copy_o)
                mupdf.pdf_dict_put( page2, PDF_NAME('Annots'), new_annots)

            # copy the old contents stream(s)
            res = JM_read_contents( page1)

            # create new /Contents object for page2
            if res and res.m_internal:
                #contents = mupdf.pdf_add_stream( pdf, mupdf.fz_new_buffer_from_copied_data( b"  ", 1), NULL, 0)
                contents = mupdf.pdf_add_stream( pdf, mupdf.fz_new_buffer_from_copied_data( b" "), mupdf.PdfObj(), 0)
                JM_update_stream( pdf, contents, res, 1)
                mupdf.pdf_dict_put( page2, PDF_NAME('Contents'), contents)

            # now insert target page, making sure it is an indirect object
            xref = mupdf.pdf_create_object( pdf)   # get new xref
            mupdf.pdf_update_object( pdf, xref, page2) # store new page

            page2 = mupdf.pdf_new_indirect( pdf, xref, 0)  # reread object
            mupdf.pdf_insert_page( pdf, to, page2) # and store the page
        finally:
            mupdf.ll_pdf_drop_page_tree( pdf.m_internal)

        self._reset_page_refs()

    def get_layer(self, config=-1):
        """Content of ON, OFF, RBGroups of an OC layer."""
        pdf = _as_pdf_document(self)
        ocp = mupdf.pdf_dict_getl(
                mupdf.pdf_trailer( pdf),
                PDF_NAME('Root'),
                PDF_NAME('OCProperties'),
                )
        if not ocp.m_internal:
            return
        if config == -1:
            obj = mupdf.pdf_dict_get( ocp, PDF_NAME('D'))
        else:
            obj = mupdf.pdf_array_get(
                    mupdf.pdf_dict_get( ocp, PDF_NAME('Configs')),
                    config,
                    )
        if not obj.m_internal:
            raise ValueError( MSG_BAD_OC_CONFIG)
        rc = JM_get_ocg_arrays( obj)
        return rc

    def get_layers(self):
        """Show optional OC layers."""
        pdf = _as_pdf_document(self)
        n = mupdf.pdf_count_layer_configs( pdf)
        if n == 1:
            obj = mupdf.pdf_dict_getl(
                    mupdf.pdf_trailer( pdf),
                    PDF_NAME('Root'),
                    PDF_NAME('OCProperties'),
                    PDF_NAME('Configs'),
                    )
            if not mupdf.pdf_is_array( obj):
                n = 0
        rc = []
        info = mupdf.PdfLayerConfig()
        for i in range(n):
            mupdf.pdf_layer_config_info( pdf, i, info)
            item = {
                    "number": i,
                    "name": info.name,
                    "creator": info.creator,
                    }
            rc.append( item)
        return rc

    def get_new_xref(self):
        """Make new xref."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        xref = 0
        ENSURE_OPERATION(pdf)
        xref = mupdf.pdf_create_object(pdf)
        return xref

    def get_ocgs(self):
        """Show existing optional content groups."""
        ci = mupdf.pdf_new_name( "CreatorInfo")
        pdf = _as_pdf_document(self)
        ocgs = mupdf.pdf_dict_getl(
                mupdf.pdf_dict_get( mupdf.pdf_trailer( pdf), PDF_NAME('Root')),
                PDF_NAME('OCProperties'),
                PDF_NAME('OCGs'),
                )
        rc = dict()
        if not mupdf.pdf_is_array( ocgs):
            return rc
        n = mupdf.pdf_array_len( ocgs)
        for i in range(n):
            ocg = mupdf.pdf_array_get( ocgs, i)
            xref = mupdf.pdf_to_num( ocg)
            name = mupdf.pdf_to_text_string( mupdf.pdf_dict_get( ocg, PDF_NAME('Name')))
            obj = mupdf.pdf_dict_getl( ocg, PDF_NAME('Usage'), ci, PDF_NAME('Subtype'))
            usage = None
            if obj.m_internal:
                usage = mupdf.pdf_to_name( obj)
            intents = list()
            intent = mupdf.pdf_dict_get( ocg, PDF_NAME('Intent'))
            if intent.m_internal:
                if mupdf.pdf_is_name( intent):
                    intents.append( mupdf.pdf_to_name( intent))
                elif mupdf.pdf_is_array( intent):
                    m = mupdf.pdf_array_len( intent)
                    for j in range(m):
                        o = mupdf.pdf_array_get( intent, j)
                        if mupdf.pdf_is_name( o):
                            intents.append( mupdf.pdf_to_name( o))
            hidden = mupdf.pdf_is_ocg_hidden( pdf, mupdf.PdfObj(), usage, ocg)
            item = {
                    "name": name,
                    "intent": intents,
                    "on": not hidden,
                    "usage": usage,
                    }
            temp = xref
            rc[ temp] = item
        return rc

    def get_outline_xrefs(self):
        """Get list of outline xref numbers."""
        xrefs = []
        pdf = _as_pdf_document(self, required=0)
        if not pdf.m_internal:
            return xrefs
        root = mupdf.pdf_dict_get(mupdf.pdf_trailer(pdf), PDF_NAME('Root'))
        if not root.m_internal:
            return xrefs
        olroot = mupdf.pdf_dict_get(root, PDF_NAME('Outlines'))
        if not olroot.m_internal:
            return xrefs
        first = mupdf.pdf_dict_get(olroot, PDF_NAME('First'))
        if not first.m_internal:
            return xrefs
        xrefs = JM_outline_xrefs(first, xrefs)
        return xrefs

    def get_page_fonts(self, pno: int, full: bool =False) -> list:
        """Retrieve a list of fonts used on a page.
        """
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        if not self.is_pdf:
            return ()
        if type(pno) is not int:
            try:
                pno = pno.number
            except Exception:
                exception_info()
                raise ValueError("need a Page or page number")
        val = self._getPageInfo(pno, 1)
        if not full:
            return [v[:-1] for v in val]
        return val

    def get_page_images(self, pno: int, full: bool =False) -> list:
        """Retrieve a list of images used on a page.
        """
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        if not self.is_pdf:
            return ()
        val = self._getPageInfo(pno, 2)
        if not full:
            return [v[:-1] for v in val]
        return val

    def get_page_xobjects(self, pno: int) -> list:
        """Retrieve a list of XObjects used on a page.
        """
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        if not self.is_pdf:
            return ()
        val = self._getPageInfo(pno, 3)
        return val

    def get_sigflags(self):
        """Get the /SigFlags value."""
        pdf = _as_pdf_document(self, required=0)
        if not pdf.m_internal:
            return -1   # not a PDF
        sigflags = mupdf.pdf_dict_getl(
                mupdf.pdf_trailer(pdf),
                PDF_NAME('Root'),
                PDF_NAME('AcroForm'),
                PDF_NAME('SigFlags'),
                )
        sigflag = -1
        if sigflags.m_internal:
            sigflag = mupdf.pdf_to_int(sigflags)
        return sigflag

    def get_xml_metadata(self):
        """Get document XML metadata."""
        xml = None
        pdf = _as_pdf_document(self, required=0)
        if pdf.m_internal:
            xml = mupdf.pdf_dict_getl(
                    mupdf.pdf_trailer(pdf),
                    PDF_NAME('Root'),
                    PDF_NAME('Metadata'),
                    )
        if xml is not None and xml.m_internal:
            buff = mupdf.pdf_load_stream(xml)
            rc = JM_UnicodeFromBuffer(buff)
        else:
            rc = ''
        return rc

    def init_doc(self):
        if self.is_encrypted:
            raise ValueError("cannot initialize - document still encrypted")
        self._outline = self._loadOutline()
        self.metadata = dict(
                    [
                        (k,self._getMetadata(v)) for k,v in {
                            'format':'format',
                            'title':'info:Title',
                            'author':'info:Author',
                            'subject':'info:Subject',
                            'keywords':'info:Keywords',
                            'creator':'info:Creator',
                            'producer':'info:Producer',
                            'creationDate':'info:CreationDate',
                            'modDate':'info:ModDate',
                            'trapped':'info:Trapped'
                            }.items()
                    ]
                )
        self.metadata['encryption'] = None if self._getMetadata('encryption')=='None' else self._getMetadata('encryption')

    def insert_file(self,
            infile,
            from_page=-1,
            to_page=-1,
            start_at=-1,
            rotate=-1,
            links=True,
            annots=True,
            show_progress=0,
            final=1,
            ):
        '''
        Insert an arbitrary supported document to an existing PDF.

        The infile may be given as a filename, a Document or a Pixmap. Other
        parameters - where applicable - equal those of insert_pdf().
        '''
        src = None
        if isinstance(infile, Pixmap):
            if infile.colorspace.n > 3:
                infile = Pixmap(csRGB, infile)
            src = Document("png", infile.tobytes())
        elif isinstance(infile, Document):
            src = infile
        else:
            src = Document(infile)
        if not src:
            raise ValueError("bad infile parameter")
        if not src.is_pdf:
            pdfbytes = src.convert_to_pdf()
            src = Document("pdf", pdfbytes)
        return self.insert_pdf(
                src,
                from_page=from_page,
                to_page=to_page,
                start_at=start_at,
                rotate=rotate,
                links=links,
                annots=annots,
                show_progress=show_progress,
                final=final,
                )

    def insert_pdf(
            self,
            docsrc,
            from_page=-1,
            to_page=-1,
            start_at=-1,
            rotate=-1,
            links=1,
            annots=1,
            show_progress=0,
            final=1,
            _gmap=None,
            ):
        """Insert a page range from another PDF.

        Args:
            docsrc: PDF to copy from. Must be different object, but may be same file.
            from_page: (int) first source page to copy, 0-based, default 0.
            to_page: (int) last source page to copy, 0-based, default last page.
            start_at: (int) from_page will become this page number in target.
            rotate: (int) rotate copied pages, default -1 is no change.
            links: (int/bool) whether to also copy links.
            annots: (int/bool) whether to also copy annotations.
            show_progress: (int) progress message interval, 0 is no messages.
            final: (bool) indicates last insertion from this source PDF.
            _gmap: internal use only

        Copy sequence reversed if from_page > to_page."""

        # Insert pages from a source PDF into this PDF.
        # For reconstructing the links (_do_links method), we must save the
        # insertion point (start_at) if it was specified as -1.
        #log( 'insert_pdf(): start')
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        if self._graft_id == docsrc._graft_id:
            raise ValueError("source and target cannot be same object")
        sa = start_at
        if sa < 0:
            sa = self.page_count
        if len(docsrc) > show_progress > 0:
            inname = os.path.basename(docsrc.name)
            if not inname:
                inname = "memory PDF"
            outname = os.path.basename(self.name)
            if not outname:
                outname = "memory PDF"
            message("Inserting '%s' at '%s'" % (inname, outname))

        # retrieve / make a Graftmap to avoid duplicate objects
        #log( 'insert_pdf(): Graftmaps')
        isrt = docsrc._graft_id
        _gmap = self.Graftmaps.get(isrt, None)
        if _gmap is None:
            #log( 'insert_pdf(): Graftmaps2')
            _gmap = Graftmap(self)
            self.Graftmaps[isrt] = _gmap

        if g_use_extra:
            #log( 'insert_pdf(): calling extra_FzDocument_insert_pdf()')
            extra_FzDocument_insert_pdf(
                    self.this,
                    docsrc.this,
                    from_page,
                    to_page,
                    start_at,
                    rotate,
                    links,
                    annots,
                    show_progress,
                    final,
                    _gmap,
                    )
            #log( 'insert_pdf(): extra_FzDocument_insert_pdf() returned.')
        else:
            pdfout = _as_pdf_document(self)
            pdfsrc = _as_pdf_document(docsrc)
            outCount = mupdf.fz_count_pages(self)
            srcCount = mupdf.fz_count_pages(docsrc.this)

            # local copies of page numbers
            fp = from_page
            tp = to_page
            sa = start_at

            # normalize page numbers
            fp = max(fp, 0) # -1 = first page
            fp = min(fp, srcCount - 1)  # but do not exceed last page

            if tp < 0:
                tp = srcCount - 1   # -1 = last page
            tp = min(tp, srcCount - 1)  # but do not exceed last page

            if sa < 0:
                sa = outCount   # -1 = behind last page
            sa = min(sa, outCount)  # but that is also the limit

            if not pdfout.m_internal or not pdfsrc.m_internal:
                raise TypeError( "source or target not a PDF")
            ENSURE_OPERATION(pdfout)
            JM_merge_range(pdfout, pdfsrc, fp, tp, sa, rotate, links, annots, show_progress, _gmap)
        
        #log( 'insert_pdf(): calling self._reset_page_refs()')
        self._reset_page_refs()
        if links:
            #log( 'insert_pdf(): calling self._do_links()')
            self._do_links(docsrc, from_page = from_page, to_page = to_page, start_at = sa)
        if final == 1:
            self.Graftmaps[isrt] = None
        #log( 'insert_pdf(): returning')

    @property
    def is_dirty(self):
        pdf = _as_pdf_document(self, required=0)
        if not pdf.m_internal:
            return False
        r = mupdf.pdf_has_unsaved_changes(pdf)
        return True if r else False

    @property
    def is_fast_webaccess(self):
        '''
        Check whether we have a linearized PDF.
        '''
        pdf = _as_pdf_document(self, required=0)
        if pdf.m_internal:
            return mupdf.pdf_doc_was_linearized(pdf)
        return False    # gracefully handle non-PDF

    @property
    def is_form_pdf(self):
        """Either False or PDF field count."""
        pdf = _as_pdf_document(self, required=0)
        if not pdf.m_internal:
            return False
        count = -1
        try:
            fields = mupdf.pdf_dict_getl(
                    mupdf.pdf_trailer(pdf),
                    mupdf.PDF_ENUM_NAME_Root,
                    mupdf.PDF_ENUM_NAME_AcroForm,
                    mupdf.PDF_ENUM_NAME_Fields,
                    )
            if mupdf.pdf_is_array(fields):
                count = mupdf.pdf_array_len(fields)
        except Exception:
            if g_exceptions_verbose:    exception_info()
            return False
        if count >= 0:
            return count
        return False

    @property
    def is_pdf(self):
        """Check for PDF."""
        if isinstance(self.this, mupdf.PdfDocument):
            return True
        # Avoid calling smupdf.pdf_specifics because it will end up creating
        # a new PdfDocument which will call pdf_create_document(), which is ok
        # but a little unnecessary.
        #
        if mupdf.ll_pdf_specifics(self.this.m_internal):
            ret = True
        else:
            ret = False
        return ret

    @property
    def is_reflowable(self):
        """Check if document is layoutable."""
        if self.is_closed:
            raise ValueError("document closed")
        return bool(mupdf.fz_is_document_reflowable(self))

    @property
    def is_repaired(self):
        """Check whether PDF was repaired."""
        pdf = _as_pdf_document(self, required=0)
        if not pdf.m_internal:
            return False
        r = mupdf.pdf_was_repaired(pdf)
        if r:
            return True
        return False

    def journal_can_do(self):
        """Show if undo and / or redo are possible."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        undo=0
        redo=0
        pdf = _as_pdf_document(self)
        undo = mupdf.pdf_can_undo(pdf)
        redo = mupdf.pdf_can_redo(pdf)
        return {'undo': bool(undo), 'redo': bool(redo)}

    def journal_enable(self):
        """Activate document journalling."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        mupdf.pdf_enable_journal(pdf)

    def journal_is_enabled(self):
        """Check if journalling is enabled."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        enabled = pdf.m_internal and pdf.m_internal.journal
        return enabled

    def journal_load(self, filename):
        """Load a journal from a file."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        if isinstance(filename, str):
            mupdf.pdf_load_journal(pdf, filename)
        else:
            res = JM_BufferFromBytes(filename)
            stm = mupdf.fz_open_buffer(res)
            mupdf.pdf_deserialise_journal(pdf, stm)
        if not pdf.m_internal.journal:
            RAISEPY( "Journal and document do not match", JM_Exc_FileDataError)

    def journal_op_name(self, step):
        """Show operation name for given step."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        name = mupdf.pdf_undoredo_step(pdf, step)
        return name

    def journal_position(self):
        """Show journalling state."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        steps=0
        pdf = _as_pdf_document(self)
        rc, steps = mupdf.pdf_undoredo_state(pdf)
        return rc, steps

    def journal_redo(self):
        """Move forward in the journal."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        mupdf.pdf_redo(pdf)
        return True

    def journal_save(self, filename):
        """Save journal to a file."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        if isinstance(filename, str):
            mupdf.pdf_save_journal(pdf, filename)
        else:
            out = JM_new_output_fileptr(filename)
            mupdf.pdf_write_journal(pdf, out)
            out.fz_close_output()

    def journal_start_op(self, name=None):
        """Begin a journalling operation."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        if not pdf.m_internal.journal:
            raise RuntimeError( "Journalling not enabled")
        if name:
            mupdf.pdf_begin_operation(pdf, name)
        else:
            mupdf.pdf_begin_implicit_operation(pdf)

    def journal_stop_op(self):
        """End a journalling operation."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        mupdf.pdf_end_operation(pdf)

    def journal_undo(self):
        """Move backwards in the journal."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        mupdf.pdf_undo(pdf)
        return True

    @property
    def language(self):
        """Document language."""
        pdf = _as_pdf_document(self, required=0)
        if not pdf.m_internal:
            return
        lang = mupdf.pdf_document_language(pdf)
        if lang == mupdf.FZ_LANG_UNSET:
            return
        return mupdf.fz_string_from_text_language2(lang)

    @property
    def last_location(self):
        """Id (chapter, page) of last page."""
        if self.is_closed:
            raise ValueError("document closed")
        last_loc = mupdf.fz_last_page(self.this)
        return last_loc.chapter, last_loc.page

    def layer_ui_configs(self):
        """Show OC visibility status modifiable by user."""
        pdf = _as_pdf_document(self)
        info = mupdf.PdfLayerConfigUi()
        n = mupdf.pdf_count_layer_config_ui( pdf)
        rc = []
        for i in range(n):
            mupdf.pdf_layer_config_ui_info( pdf, i, info)
            if info.type == 1:
                type_ = "checkbox"
            elif info.type == 2:
                type_ = "radiobox"
            else:
                type_ = "label"
            item = {
                    "number": i,
                    "text": info.text,
                    "depth": info.depth,
                    "type": type_,
                    "on": info.selected,
                    "locked": info.locked,
                    }
            rc.append(item)
        return rc

    def layout(self, rect=None, width=0, height=0, fontsize=11):
        """Re-layout a reflowable document."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        doc = self.this
        if not mupdf.fz_is_document_reflowable( doc):
            return
        w = width
        h = height
        r = JM_rect_from_py(rect)
        if not mupdf.fz_is_infinite_rect(r):
            w = r.x1 - r.x0
            h = r.y1 - r.y0
        if w <= 0.0 or h <= 0.0:
            raise ValueError( "bad page size")
        mupdf.fz_layout_document( doc, w, h, fontsize)

        self._reset_page_refs()
        self.init_doc()

    def load_page(self, page_id):
        """Load a page.

        'page_id' is either a 0-based page number or a tuple (chapter, pno),
        with chapter number and page number within that chapter.
        """
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        if page_id is None:
            page_id = 0
        if page_id not in self:
            raise ValueError("page not in document")
        if type(page_id) is int and page_id < 0:
            np = self.page_count
            while page_id < 0:
                page_id += np
        if isinstance(page_id, int):
            page = mupdf.fz_load_page(self.this, page_id)
        else:
            chapter, pagenum = page_id
            page = mupdf.fz_load_chapter_page(self.this, chapter, pagenum)
        val = Page(page, self)

        val.thisown = True
        val.parent = self
        self._page_refs[id(val)] = val
        val._annot_refs = weakref.WeakValueDictionary()
        val.number = page_id
        return val

    def location_from_page_number(self, pno):
        """Convert pno to (chapter, page)."""
        if self.is_closed:
            raise ValueError("document closed")
        this_doc = self.this
        loc = mupdf.fz_make_location(-1, -1)
        page_count = mupdf.fz_count_pages(this_doc)
        while pno < 0:
            pno += page_count
        if pno >= page_count:
            raise ValueError( MSG_BAD_PAGENO)
        loc = mupdf.fz_location_from_page_number(this_doc, pno)
        return loc.chapter, loc.page

    def make_bookmark(self, loc):
        """Make a page pointer before layouting document."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        loc = mupdf.FzLocation(*loc)
        mark = mupdf.ll_fz_make_bookmark2( self.this.m_internal, loc.internal())
        return mark

    @property
    def markinfo(self) -> dict:
        """Return the PDF MarkInfo value."""
        xref = self.pdf_catalog()
        if xref == 0:
            return None
        rc = self.xref_get_key(xref, "MarkInfo")
        if rc[0] == "null":
            return {}
        if rc[0] == "xref":
            xref = int(rc[1].split()[0])
            val = self.xref_object(xref, compressed=True)
        elif rc[0] == "dict":
            val = rc[1]
        else:
            val = None
        if val is None or not (val[:2] == "<<" and val[-2:] == ">>"):
            return {}
        valid = {"Marked": False, "UserProperties": False, "Suspects": False}
        val = val[2:-2].split("/")
        for v in val[1:]:
            try:
                key, value = v.split()
            except Exception:
                if g_exceptions_verbose > 1:    exception_info()
                return valid
            if value == "true":
                valid[key] = True
        return valid

    def move_page(self, pno: int, to: int =-1):
        """Move a page within a PDF document.

        Args:
            pno: source page number.
            to: put before this page, '-1' means after last page.
        """
        if self.is_closed:
            raise ValueError("document closed")
        page_count = len(self)
        if (pno not in range(page_count) or to not in range(-1, page_count)):
            raise ValueError("bad page number(s)")
        before = 1
        copy = 0
        if to == -1:
            to = page_count - 1
            before = 0

        return self._move_copy_page(pno, to, before, copy)

    @property
    def name(self):
        return self._name
    
    def need_appearances(self, value=None):
        """Get/set the NeedAppearances value."""
        if not self.is_form_pdf:
            return None
        
        pdf = _as_pdf_document(self)
        oldval = -1
        appkey = "NeedAppearances"
        
        form = mupdf.pdf_dict_getp(
                mupdf.pdf_trailer(pdf),
                "Root/AcroForm",
                )
        app = mupdf.pdf_dict_gets(form, appkey)
        if mupdf.pdf_is_bool(app):
            oldval = mupdf.pdf_to_bool(app)
        if value:
            mupdf.pdf_dict_puts(form, appkey, mupdf.PDF_TRUE)
        else:
            mupdf.pdf_dict_puts(form, appkey, mupdf.PDF_FALSE)
        if value is None:
            return oldval >= 0
        return value

    @property
    def needs_pass(self):
        """Indicate password required."""
        if self.is_closed:
            raise ValueError("document closed")
        document = self.this if isinstance(self.this, mupdf.FzDocument) else self.this.super()
        ret = mupdf.fz_needs_password( document)
        return ret

    def next_location(self, page_id):
        """Get (chapter, page) of next page."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        if type(page_id) is int:
            page_id = (0, page_id)
        if page_id not in self:
            raise ValueError("page id not in document")
        if tuple(page_id) == self.last_location:
            return ()
        this_doc = _as_fz_document(self)
        val = page_id[ 0]
        if not isinstance(val, int):
            RAISEPY(MSG_BAD_PAGEID, PyExc_ValueError)
        chapter = val
        val = page_id[ 1]
        pno = val
        loc = mupdf.fz_make_location(chapter, pno)
        next_loc = mupdf.fz_next_page( this_doc, loc)
        return next_loc.chapter, next_loc.page

    def page_annot_xrefs(self, n):
        if g_use_extra:
            return extra.page_annot_xrefs( self.this, n)
        
        if isinstance(self.this, mupdf.PdfDocument):
            page_count = mupdf.pdf_count_pages(self.this)
            pdf_document = self.this
        else:
            page_count = mupdf.fz_count_pages(self.this)
            pdf_document = _as_pdf_document(self)
        while n < 0:
            n += page_count
        if n > page_count:
            raise ValueError( MSG_BAD_PAGENO)
        page_obj = mupdf.pdf_lookup_page_obj(pdf_document, n)
        annots = JM_get_annot_xref_list(page_obj)
        return annots

    @property
    def page_count(self):
        """Number of pages."""
        if self.is_closed:
            raise ValueError('document closed')
        if g_use_extra:
            return self.page_count2(self)
        if isinstance( self.this, mupdf.FzDocument):
            return mupdf.fz_count_pages( self.this)
        else:
            return mupdf.pdf_count_pages( self.this)

    def page_cropbox(self, pno):
        """Get CropBox of page number (without loading page)."""
        if self.is_closed:
            raise ValueError("document closed")
        this_doc = self.this
        page_count = mupdf.fz_count_pages( this_doc)
        n = pno
        while n < 0:
            n += page_count
        pdf = _as_pdf_document(self)
        if n >= page_count:
            raise ValueError( MSG_BAD_PAGENO)
        pageref = mupdf.pdf_lookup_page_obj( pdf, n)
        cropbox = JM_cropbox(pageref)
        val = JM_py_from_rect(cropbox)

        val = Rect(val)

        return val

    def page_number_from_location(self, page_id):
        """Convert (chapter, pno) to page number."""
        if type(page_id) is int:
            np = self.page_count
            while page_id < 0:
                page_id += np
            page_id = (0, page_id)
        if page_id not in self:
            raise ValueError("page id not in document")
        chapter, pno = page_id
        loc = mupdf.fz_make_location( chapter, pno)
        page_n = mupdf.fz_page_number_from_location( self.this, loc)
        return page_n

    def page_xref(self, pno):
        """Get xref of page number."""
        if g_use_extra:
            return extra.page_xref( self.this, pno)
        if self.is_closed:
            raise ValueError("document closed")
        page_count = mupdf.fz_count_pages(self.this)
        n = pno
        while n < 0:
            n += page_count
        pdf = _as_pdf_document(self)
        xref = 0
        if n >= page_count:
            raise ValueError( MSG_BAD_PAGENO)
        xref = mupdf.pdf_to_num(mupdf.pdf_lookup_page_obj(pdf, n))
        return xref

    @property
    def pagelayout(self) -> str:
        """Return the PDF PageLayout value.
        """
        xref = self.pdf_catalog()
        if xref == 0:
            return None
        rc = self.xref_get_key(xref, "PageLayout")
        if rc[0] == "null":
            return "SinglePage"
        if rc[0] == "name":
            return rc[1][1:]
        return "SinglePage"

    @property
    def pagemode(self) -> str:
        """Return the PDF PageMode value.
        """
        xref = self.pdf_catalog()
        if xref == 0:
            return None
        rc = self.xref_get_key(xref, "PageMode")
        if rc[0] == "null":
            return "UseNone"
        if rc[0] == "name":
            return rc[1][1:]
        return "UseNone"

    if sys.implementation.version < (3, 9):
        # Appending `[Page]` causes `TypeError: 'ABCMeta' object is not subscriptable`.
        _pages_ret = collections.abc.Iterable
    else:
        _pages_ret = collections.abc.Iterable[Page]

    def pages(self, start: OptInt =None, stop: OptInt =None, step: OptInt =None) -> _pages_ret:
        """Return a generator iterator over a page range.

        Arguments have the same meaning as for the range() built-in.
        """
        if not self.page_count:
            return
        # set the start value
        start = start or 0
        while start < 0:
            start += self.page_count
        if start not in range(self.page_count):
            raise ValueError("bad start page number")

        # set the stop value
        stop = stop if stop is not None and stop <= self.page_count else self.page_count

        # set the step value
        if step == 0:
            raise ValueError("arg 3 must not be zero")
        if step is None:
            if start > stop:
                step = -1
            else:
                step = 1

        for pno in range(start, stop, step):
            yield (self.load_page(pno))

    def pdf_catalog(self):
        """Get xref of PDF catalog."""
        pdf = _as_pdf_document(self, required=0)
        xref = 0
        if not pdf.m_internal:
            return xref
        root = mupdf.pdf_dict_get(mupdf.pdf_trailer(pdf), PDF_NAME('Root'))
        xref = mupdf.pdf_to_num(root)
        return xref

    def pdf_trailer(self, compressed=0, ascii=0):
        """Get PDF trailer as a string."""
        return self.xref_object(-1, compressed=compressed, ascii=ascii)

    @property
    def permissions(self):
        """Document permissions."""
        if self.is_encrypted:
            return 0
        doc =self.this
        pdf = mupdf.pdf_document_from_fz_document(doc)

        # for PDF return result of standard function
        if pdf.m_internal:
            return mupdf.pdf_document_permissions(pdf)

        # otherwise simulate the PDF return value
        perm = 0xFFFFFFFC   # all permissions granted
        # now switch off where needed
        if not mupdf.fz_has_permission(doc, mupdf.FZ_PERMISSION_PRINT):
            perm = perm ^ mupdf.PDF_PERM_PRINT
        if not mupdf.fz_has_permission(doc, mupdf.FZ_PERMISSION_EDIT):
            perm = perm ^ mupdf.PDF_PERM_MODIFY
        if not mupdf.fz_has_permission(doc, mupdf.FZ_PERMISSION_COPY):
            perm = perm ^ mupdf.PDF_PERM_COPY
        if not mupdf.fz_has_permission(doc, mupdf.FZ_PERMISSION_ANNOTATE):
            perm = perm ^ mupdf.PDF_PERM_ANNOTATE
        return perm

    def prev_location(self, page_id):

        """Get (chapter, page) of previous page."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        if type(page_id) is int:
            page_id = (0, page_id)
        if page_id not in self:
            raise ValueError("page id not in document")
        if page_id  == (0, 0):
            return ()
        chapter, pno = page_id
        loc = mupdf.fz_make_location(chapter, pno)
        prev_loc = mupdf.fz_previous_page(self.this, loc)
        return prev_loc.chapter, prev_loc.page

    def reload_page(self, page: Page) -> Page:
        """Make a fresh copy of a page."""
        old_annots = {}  # copy annot references to here
        pno = page.number  # save the page number
        for k, v in page._annot_refs.items():  # save the annot dictionary
            old_annots[k] = v
        
        # When we call `self.load_page()` below, it will end up in
        # fz_load_chapter_page(), which will return any matching page in the
        # document's list of non-ref-counted loaded pages, instead of actually
        # reloading the page.
        #
        # We want to assert that we have actually reloaded the fz_page, and not
        # simply returned the same `fz_page*` pointer from the document's list
        # of non-ref-counted loaded pages.
        #
        # So we first remove our reference to the `fz_page*`. This will
        # decrement .refs, and if .refs was 1, this is guaranteed to free the
        # `fz_page*` and remove it from the document's list if it was there. So
        # we are guaranteed that our returned `fz_page*` is from a genuine
        # reload, even if it happens to reuse the original block of memory.
        #
        # However if the original .refs is greater than one, there must be
        # other references to the `fz_page` somewhere, and we require that
        # these other references are not keeping the page in the document's
        # list.  We check that we are returning a newly loaded page by
        # asserting that our returned `fz_page*` is different from the original
        # `fz_page*` - the original was not freed, so a new `fz_page` cannot
        # reuse the same block of memory.
        #
        
        refs_old = page.this.m_internal.refs
        m_internal_old = page.this.m_internal_value()
        
        page.this = None
        page._erase()  # remove the page
        page = None
        TOOLS.store_shrink(100)
        page = self.load_page(pno)  # reload the page

        # copy annot refs over to the new dictionary
        #page_proxy = weakref.proxy(page)
        for k, v in old_annots.items():
            annot = old_annots[k]
            #annot.parent = page_proxy  # refresh parent to new page
            page._annot_refs[k] = annot
        if refs_old == 1:
            # We know that `page.this = None` will have decremented the ref
            # count to zero so we are guaranteed that the new `fz_page` is a
            # new page even if it happens to have reused the same block of
            # memory.
            pass
        else:
            # Check that the new `fz_page*` is different from the original.
            m_internal_new = page.this.m_internal_value()
            assert m_internal_new != m_internal_old, \
                    f'{refs_old=} {m_internal_old=:#x} {m_internal_new=:#x}'
        return page

    def resolve_link(self, uri=None, chapters=0):
        """Calculate internal link destination.

        Args:
            uri: (str) some Link.uri
            chapters: (bool) whether to use (chapter, page) format
        Returns:
            (page_id, x, y) where x, y are point coordinates on the page.
            page_id is either page number (if chapters=0), or (chapter, pno).
        """
        if not uri:
            if chapters:
                return (-1, -1), 0, 0
            return -1, 0, 0
        try:
            loc, xp, yp = mupdf.fz_resolve_link(self.this, uri)
        except Exception:
            if g_exceptions_verbose:    exception_info()
            if chapters:
                return (-1, -1), 0, 0
            return -1, 0, 0
        if chapters:
            return (loc.chapter, loc.page), xp, yp
        pno = mupdf.fz_page_number_from_location(self.this, loc)
        return pno, xp, yp

    def resolve_names(self):
        """Convert the PDF's destination names into a Python dict.

        The only parameter is the pymupdf.Document.
        All names found in the catalog under keys "/Dests" and "/Names/Dests" are
        being included.

        Returns:
            A dcitionary with the following layout:
            - key: (str) the name
            - value: (dict) with the following layout:
                * "page":  target page number (0-based). If no page number found -1.
                * "to": (x, y) target point on page - currently in PDF coordinates,
                        i.e. point (0,0) is the bottom-left of the page.
                * "zoom": (float) the zoom factor
                * "dest": (str) only occurs if the target location on the page has
                        not been provided as "/XYZ" or if no page number was found.
            Examples:
            {'__bookmark_1': {'page': 0, 'to': (0.0, 541.0), 'zoom': 0.0},
            '__bookmark_2': {'page': 0, 'to': (0.0, 481.45), 'zoom': 0.0}}

            or

            '21154a7c20684ceb91f9c9adc3b677c40': {'page': -1, 'dest': '/XYZ 15.75 1486 0'}, ...
        """
        if hasattr(self, "_resolved_names"):  # do not execute multiple times!
            return self._resolved_names
        # this is a backward listing of page xref to page number
        page_xrefs = {self.page_xref(i): i for i in range(self.page_count)}

        def obj_string(obj):
            """Return string version of a PDF object definition."""
            buffer = mupdf.fz_new_buffer(512)
            output = mupdf.FzOutput(buffer)
            mupdf.pdf_print_obj(output, obj, 1, 0)
            output.fz_close_output()
            return JM_UnicodeFromBuffer(buffer)

        def get_array(val):
            """Generate value of one item of the names dictionary."""
            templ_dict = {"page": -1, "dest": ""}  # value template
            if val.pdf_is_indirect():
                val = mupdf.pdf_resolve_indirect(val)
            if val.pdf_is_array():
                array = obj_string(val)
            elif val.pdf_is_dict():
                array = obj_string(mupdf.pdf_dict_gets(val, "D"))
            else:  # if all fails return the empty template
                return templ_dict

            # replace PDF "null" by zero, omit the square brackets
            array = array.replace("null", "0")[1:-1]

            # find stuff before first "/"
            idx = array.find("/")
            if idx < 1:  # this has no target page spec
                templ_dict["dest"] = array  # return the orig. string
                return templ_dict

            subval = array[:idx]  # stuff before "/"
            array = array[idx:]  # stuff from "/" onwards
            templ_dict["dest"] = array

            # if we start with /XYZ: extract x, y, zoom
            # 1, 2 or 3 of these values may actually be supplied
            if array.startswith("/XYZ"):
                del templ_dict["dest"]  # don't return orig string in this case

                t = [0, 0, 0]  # the resulting x, y, z values

                # need to replace any "null" item by "0", then split at
                # white spaces, omitting "/XYZ" from the result
                for i, v in enumerate(array.replace("null", "0").split()[1:]):
                    t[i] = float(v)
                templ_dict["to"] = (t[0], t[1])
                templ_dict["zoom"] = t[2]

            # extract page number
            if "0 R" in subval:  # page xref given?
                templ_dict["page"] = page_xrefs.get(int(subval.split()[0]),-1)
            else:  # naked page number given
                templ_dict["page"] = int(subval)
            return templ_dict

        def fill_dict(dest_dict, pdf_dict):
            """Generate name resolution items for pdf_dict.

            This may be either "/Names/Dests" or just "/Dests"
            """
            # length of the PDF dictionary
            name_count = mupdf.pdf_dict_len(pdf_dict)

            # extract key-val of each dict item
            for i in range(name_count):
                key = mupdf.pdf_dict_get_key(pdf_dict, i)
                val = mupdf.pdf_dict_get_val(pdf_dict, i)
                if key.pdf_is_name():  # this should always be true!
                    dict_key = key.pdf_to_name()
                else:
                    message(f"key {i} is no /Name")
                    dict_key = None

                if dict_key:
                    dest_dict[dict_key] = get_array(val)  # store key/value in dict

        # access underlying PDF document of fz Document
        pdf = mupdf.pdf_document_from_fz_document(self)

        # access PDF catalog
        catalog = mupdf.pdf_dict_gets(mupdf.pdf_trailer(pdf), "Root")

        dest_dict = {}

        # make PDF_NAME(Dests)
        dests = mupdf.pdf_new_name("Dests")

        # extract destinations old style (PDF 1.1)
        old_dests = mupdf.pdf_dict_get(catalog, dests)
        if old_dests.pdf_is_dict():
            fill_dict(dest_dict, old_dests)

        # extract destinations new style (PDF 1.2+)
        tree = mupdf.pdf_load_name_tree(pdf, dests)
        if tree.pdf_is_dict():
            fill_dict(dest_dict, tree)

        self._resolved_names = dest_dict  # store result or reuse
        return dest_dict

    def save(
            self,
            filename,
            garbage=0,
            clean=0,
            deflate=0,
            deflate_images=0,
            deflate_fonts=0,
            incremental=0,
            ascii=0,
            expand=0,
            linear=0,
            no_new_id=0,
            appearance=0,
            pretty=0,
            encryption=1,
            permissions=4095,
            owner_pw=None,
            user_pw=None,
            preserve_metadata=1,
            use_objstms=0,
            compression_effort=0,
            ):
        # From %pythonprepend save
        #
        """Save PDF to file, pathlib.Path or file pointer."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        if type(filename) is str:
            pass
        elif hasattr(filename, "open"):  # assume: pathlib.Path
            filename = str(filename)
        elif hasattr(filename, "name"):  # assume: file object
            filename = filename.name
        elif not hasattr(filename, "seek"):  # assume file object
            raise ValueError("filename must be str, Path or file object")
        if filename == self.name and not incremental:
            raise ValueError("save to original must be incremental")
        if linear and use_objstms:
            raise ValueError("'linear' and 'use_objstms' cannot both be requested")
        if self.page_count < 1:
            raise ValueError("cannot save with zero pages")
        if incremental:
            if self.name != filename or self.stream:
                raise ValueError("incremental needs original file")
        if user_pw and len(user_pw) > 40 or owner_pw and len(owner_pw) > 40:
            raise ValueError("password length must not exceed 40")
        
        pdf = _as_pdf_document(self)
        opts = mupdf.PdfWriteOptions()
        opts.do_incremental = incremental
        opts.do_ascii = ascii
        opts.do_compress = deflate
        opts.do_compress_images = deflate_images
        opts.do_compress_fonts = deflate_fonts
        opts.do_decompress = expand
        opts.do_garbage = garbage
        opts.do_pretty = pretty
        opts.do_linear = linear
        opts.do_clean = clean
        opts.do_sanitize = clean
        opts.dont_regenerate_id = no_new_id
        opts.do_appearance = appearance
        opts.do_encrypt = encryption
        opts.permissions = permissions
        if owner_pw is not None:
            opts.opwd_utf8_set_value(owner_pw)
        elif user_pw is not None:
            opts.opwd_utf8_set_value(user_pw)
        if user_pw is not None:
            opts.upwd_utf8_set_value(user_pw)
        opts.do_preserve_metadata = preserve_metadata
        opts.do_use_objstms = use_objstms
        opts.compression_effort = compression_effort

        out = None
        pdf.m_internal.resynth_required = 0
        JM_embedded_clean(pdf)
        if no_new_id == 0:
            JM_ensure_identity(pdf)
        if isinstance(filename, str):
            #log( 'calling mupdf.pdf_save_document()')
            mupdf.pdf_save_document(pdf, filename, opts)
        else:
            out = JM_new_output_fileptr(filename)
            #log( f'{type(out)=} {type(out.this)=}')
            mupdf.pdf_write_document(pdf, out, opts)
            out.fz_close_output()

    def save_snapshot(self, filename):
        """Save a file snapshot suitable for journalling."""
        if self.is_closed:
            raise ValueError("doc is closed")
        if type(filename) is str:
            pass
        elif hasattr(filename, "open"):  # assume: pathlib.Path
            filename = str(filename)
        elif hasattr(filename, "name"):  # assume: file object
            filename = filename.name
        else:
            raise ValueError("filename must be str, Path or file object")
        if filename == self.name:
            raise ValueError("cannot snapshot to original")
        pdf = _as_pdf_document(self)
        mupdf.pdf_save_snapshot(pdf, filename)

    def saveIncr(self):
        """ Save PDF incrementally"""
        return self.save(self.name, incremental=True, encryption=mupdf.PDF_ENCRYPT_KEEP)

    def select(self, pyliste):
        """Build sub-pdf with page numbers in the list."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        if not self.is_pdf:
            raise ValueError("is no PDF")
        if not hasattr(pyliste, "__getitem__"):
            raise ValueError("sequence required")

        valid_range = range(len(self))
        if (len(pyliste) == 0
            or min(pyliste) not in valid_range
            or max(pyliste) not in valid_range
        ):
            raise ValueError("bad page number(s)")

        # get underlying pdf document,
        pdf = _as_pdf_document(self)
        # create page sub-pdf via pdf_rearrange_pages2().
        #
        mupdf.pdf_rearrange_pages2(pdf, pyliste)

        # remove any existing pages with their kids
        self._reset_page_refs()

    def set_language(self, language=None):
        pdf = _as_pdf_document(self)
        if not language:
            lang = mupdf.FZ_LANG_UNSET
        else:
            lang = mupdf.fz_text_language_from_string(language)
        mupdf.pdf_set_document_language(pdf, lang)
        return True

    def set_layer(self, config, basestate=None, on=None, off=None, rbgroups=None, locked=None):
        """Set the PDF keys /ON, /OFF, /RBGroups of an OC layer."""
        if self.is_closed:
            raise ValueError("document closed")
        ocgs = set(self.get_ocgs().keys())
        if ocgs == set():
            raise ValueError("document has no optional content")

        if on:
            if type(on) not in (list, tuple):
                raise ValueError("bad type: 'on'")
            s = set(on).difference(ocgs)
            if s != set():
                raise ValueError("bad OCGs in 'on': %s" % s)

        if off:
            if type(off) not in (list, tuple):
                raise ValueError("bad type: 'off'")
            s = set(off).difference(ocgs)
            if s != set():
                raise ValueError("bad OCGs in 'off': %s" % s)

        if locked:
            if type(locked) not in (list, tuple):
                raise ValueError("bad type: 'locked'")
            s = set(locked).difference(ocgs)
            if s != set():
                raise ValueError("bad OCGs in 'locked': %s" % s)

        if rbgroups:
            if type(rbgroups) not in (list, tuple):
                raise ValueError("bad type: 'rbgroups'")
            for x in rbgroups:
                if not type(x) in (list, tuple):
                    raise ValueError("bad RBGroup '%s'" % x)
                s = set(x).difference(ocgs)
                if s != set():
                    raise ValueError("bad OCGs in RBGroup: %s" % s)

        if basestate:
            basestate = str(basestate).upper()
            if basestate == "UNCHANGED":
                basestate = "Unchanged"
            if basestate not in ("ON", "OFF", "Unchanged"):
                raise ValueError("bad 'basestate'")
        pdf = _as_pdf_document(self)
        ocp = mupdf.pdf_dict_getl(
                mupdf.pdf_trailer( pdf),
                PDF_NAME('Root'),
                PDF_NAME('OCProperties'),
                )
        if not ocp.m_internal:
            return
        if config == -1:
            obj = mupdf.pdf_dict_get( ocp, PDF_NAME('D'))
        else:
            obj = mupdf.pdf_array_get(
                    mupdf.pdf_dict_get( ocp, PDF_NAME('Configs')),
                    config,
                    )
        if not obj.m_internal:
            raise ValueError( MSG_BAD_OC_CONFIG)
        JM_set_ocg_arrays( obj, basestate, on, off, rbgroups, locked)
        mupdf.ll_pdf_read_ocg( pdf.m_internal)

    def set_layer_ui_config(self, number, action=0):
        """Set / unset OC intent configuration."""
        # The user might have given the name instead of sequence number,
        # so select by that name and continue with corresp. number
        if isinstance(number, str):
            select = [ui["number"] for ui in self.layer_ui_configs() if ui["text"] == number]
            if select == []:
                raise ValueError(f"bad OCG '{number}'.")
            number = select[0]  # this is the number for the name
        pdf = _as_pdf_document(self)
        if action == 1:
            mupdf.pdf_toggle_layer_config_ui(pdf, number)
        elif action == 2:
            mupdf.pdf_deselect_layer_config_ui(pdf, number)
        else:
            mupdf.pdf_select_layer_config_ui(pdf, number)

    def set_markinfo(self, markinfo: dict) -> bool:
        """Set the PDF MarkInfo values."""
        xref = self.pdf_catalog()
        if xref == 0:
            raise ValueError("not a PDF")
        if not markinfo or not isinstance(markinfo, dict):
            return False
        valid = {"Marked": False, "UserProperties": False, "Suspects": False}

        if not set(valid.keys()).issuperset(markinfo.keys()):
            badkeys = f"bad MarkInfo key(s): {set(markinfo.keys()).difference(valid.keys())}"
            raise ValueError(badkeys)
        pdfdict = "<<"
        valid.update(markinfo)
        for key, value in valid.items():
            value=str(value).lower()
            if value not in ("true", "false"):
                raise ValueError(f"bad key value '{key}': '{value}'")
            pdfdict += f"/{key} {value}"
        pdfdict += ">>"
        self.xref_set_key(xref, "MarkInfo", pdfdict)
        return True

    def set_pagelayout(self, pagelayout: str):
        """Set the PDF PageLayout value."""
        valid = ("SinglePage", "OneColumn", "TwoColumnLeft", "TwoColumnRight", "TwoPageLeft", "TwoPageRight")
        xref = self.pdf_catalog()
        if xref == 0:
            raise ValueError("not a PDF")
        if not pagelayout:
            raise ValueError("bad PageLayout value")
        if pagelayout[0] == "/":
            pagelayout = pagelayout[1:]
        for v in valid:
            if pagelayout.lower() == v.lower():
                self.xref_set_key(xref, "PageLayout", f"/{v}")
                return True
        raise ValueError("bad PageLayout value")

    def set_pagemode(self, pagemode: str):
        """Set the PDF PageMode value."""
        valid = ("UseNone", "UseOutlines", "UseThumbs", "FullScreen", "UseOC", "UseAttachments")
        xref = self.pdf_catalog()
        if xref == 0:
            raise ValueError("not a PDF")
        if not pagemode:
            raise ValueError("bad PageMode value")
        if pagemode[0] == "/":
            pagemode = pagemode[1:]
        for v in valid:
            if pagemode.lower() == v.lower():
                self.xref_set_key(xref, "PageMode", f"/{v}")
                return True
        raise ValueError("bad PageMode value")

    def set_xml_metadata(self, metadata):
        """Store XML document level metadata."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        root = mupdf.pdf_dict_get( mupdf.pdf_trailer( pdf), PDF_NAME('Root'))
        if not root.m_internal:
            RAISEPY( MSG_BAD_PDFROOT, JM_Exc_FileDataError)
        res = mupdf.fz_new_buffer_from_copied_data( metadata.encode('utf-8'))
        xml = mupdf.pdf_dict_get( root, PDF_NAME('Metadata'))
        if xml.m_internal:
            JM_update_stream( pdf, xml, res, 0)
        else:
            xml = mupdf.pdf_add_stream( pdf, res, mupdf.PdfObj(), 0)
            mupdf.pdf_dict_put( xml, PDF_NAME('Type'), PDF_NAME('Metadata'))
            mupdf.pdf_dict_put( xml, PDF_NAME('Subtype'), PDF_NAME('XML'))
            mupdf.pdf_dict_put( root, PDF_NAME('Metadata'), xml)

    def switch_layer(self, config, as_default=0):
        """Activate an OC layer."""
        pdf = _as_pdf_document(self)
        cfgs = mupdf.pdf_dict_getl(
                mupdf.pdf_trailer( pdf),
                PDF_NAME('Root'),
                PDF_NAME('OCProperties'),
                PDF_NAME('Configs')
                )
        if not mupdf.pdf_is_array( cfgs) or not mupdf.pdf_array_len( cfgs):
            if config < 1:
                return
            raise ValueError( MSG_BAD_OC_LAYER)
        if config < 0:
            return
        mupdf.pdf_select_layer_config( pdf, config)
        if as_default:
            mupdf.pdf_set_layer_config_as_default( pdf)
            mupdf.ll_pdf_read_ocg( pdf.m_internal)

    def update_object(self, xref, text, page=None):
        """Replace object definition source."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        xreflen = mupdf.pdf_xref_len(pdf)
        if not _INRANGE(xref, 1, xreflen-1):
            RAISEPY("bad xref", MSG_BAD_XREF, PyExc_ValueError)
        ENSURE_OPERATION(pdf)
        # create new object with passed-in string
        new_obj = JM_pdf_obj_from_str(pdf, text)
        mupdf.pdf_update_object(pdf, xref, new_obj)
        if page:
            JM_refresh_links( _as_pdf_page(page))

    def update_stream(self, xref=0, stream=None, new=1, compress=1):
        """Replace xref stream part."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        xreflen = mupdf.pdf_xref_len(pdf)
        if xref < 1 or xref > xreflen:
            raise ValueError( MSG_BAD_XREF)
        # get the object
        obj = mupdf.pdf_new_indirect(pdf, xref, 0)
        if not mupdf.pdf_is_dict(obj):
            raise ValueError( MSG_IS_NO_DICT)
        res = JM_BufferFromBytes(stream)
        if not res.m_internal:
            raise TypeError( MSG_BAD_BUFFER)
        JM_update_stream(pdf, obj, res, compress)
        pdf.dirty = 1

    @property
    def version_count(self):
        '''
        Count versions of PDF document.
        '''
        pdf = _as_pdf_document(self, required=0)
        if pdf.m_internal:
            return mupdf.pdf_count_versions(pdf)
        return 0

    def write(
            self,
            garbage=False,
            clean=False,
            deflate=False,
            deflate_images=False,
            deflate_fonts=False,
            incremental=False,
            ascii=False,
            expand=False,
            linear=False,
            no_new_id=False,
            appearance=False,
            pretty=False,
            encryption=1,
            permissions=4095,
            owner_pw=None,
            user_pw=None,
            preserve_metadata=1,
            use_objstms=0,
            compression_effort=0,
    ):
        from io import BytesIO
        bio = BytesIO()
        self.save(
                bio,
                garbage=garbage,
                clean=clean,
                no_new_id=no_new_id,
                appearance=appearance,
                deflate=deflate,
                deflate_images=deflate_images,
                deflate_fonts=deflate_fonts,
                incremental=incremental,
                ascii=ascii,
                expand=expand,
                linear=linear,
                pretty=pretty,
                encryption=encryption,
                permissions=permissions,
                owner_pw=owner_pw,
                user_pw=user_pw,
                preserve_metadata=preserve_metadata,
                use_objstms=use_objstms,
                compression_effort=compression_effort,
        )
        return bio.getvalue()

    @property
    def xref(self):
        """PDF xref number of page."""
        CheckParent(self)
        return self.parent.page_xref(self.number)

    def xref_get_key(self, xref, key):
        """Get PDF dict key value of object at 'xref'."""
        pdf = _as_pdf_document(self)
        xreflen = mupdf.pdf_xref_len(pdf)
        if not _INRANGE(xref, 1, xreflen-1) and xref != -1:
            raise ValueError( MSG_BAD_XREF)
        if xref > 0:
            obj = mupdf.pdf_load_object(pdf, xref)
        else:
            obj = mupdf.pdf_trailer(pdf)
        if not obj.m_internal:
            return ("null", "null")
        subobj = mupdf.pdf_dict_getp(obj, key)
        if not subobj.m_internal:
            return ("null", "null")
        text = None
        if mupdf.pdf_is_indirect(subobj):
            type = "xref"
            text = "%i 0 R" % mupdf.pdf_to_num(subobj)
        elif mupdf.pdf_is_array(subobj):
            type = "array"
        elif mupdf.pdf_is_dict(subobj):
            type = "dict"
        elif mupdf.pdf_is_int(subobj):
            type = "int"
            text = "%i" % mupdf.pdf_to_int(subobj)
        elif mupdf.pdf_is_real(subobj):
            type = "float"
        elif mupdf.pdf_is_null(subobj):
            type = "null"
            text = "null"
        elif mupdf.pdf_is_bool(subobj):
            type = "bool"
            if mupdf.pdf_to_bool(subobj):
                text = "true"
            else:
                text = "false"
        elif mupdf.pdf_is_name(subobj):
            type = "name"
            text = "/%s" % mupdf.pdf_to_name(subobj)
        elif mupdf.pdf_is_string(subobj):
            type = "string"
            text = JM_UnicodeFromStr(mupdf.pdf_to_text_string(subobj))
        else:
            type = "unknown"
        if text is None:
            res = JM_object_to_buffer(subobj, 1, 0)
            text = JM_UnicodeFromBuffer(res)
        return (type, text)

    def xref_get_keys(self, xref):
        """Get the keys of PDF dict object at 'xref'. Use -1 for the PDF trailer."""
        pdf = _as_pdf_document(self)
        xreflen = mupdf.pdf_xref_len( pdf)
        if not _INRANGE(xref, 1, xreflen-1) and xref != -1:
            raise ValueError( MSG_BAD_XREF)
        if xref > 0:
            obj = mupdf.pdf_load_object( pdf, xref)
        else:
            obj = mupdf.pdf_trailer( pdf)
        n = mupdf.pdf_dict_len( obj)
        rc = []
        if n == 0:
            return rc
        for i in range(n):
            key = mupdf.pdf_to_name( mupdf.pdf_dict_get_key( obj, i))
            rc.append(key)
        return rc

    def xref_is_font(self, xref):
        """Check if xref is a font object."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        if self.xref_get_key(xref, "Type")[1] == "/Font":
            return True
        return False

    def xref_is_image(self, xref):
        """Check if xref is an image object."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        if self.xref_get_key(xref, "Subtype")[1] == "/Image":
            return True
        return False

    def xref_is_stream(self, xref=0):
        """Check if xref is a stream object."""
        pdf = _as_pdf_document(self, required=0)
        if not pdf.m_internal:
            return False    # not a PDF
        return bool(mupdf.pdf_obj_num_is_stream(pdf, xref))

    def xref_is_xobject(self, xref):
        """Check if xref is a form xobject."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        if self.xref_get_key(xref, "Subtype")[1] == "/Form":
            return True
        return False

    def xref_length(self):
        """Get length of xref table."""
        xreflen = 0
        pdf = _as_pdf_document(self, required=0)
        if pdf.m_internal:
            xreflen = mupdf.pdf_xref_len(pdf)
        return xreflen

    def xref_object(self, xref, compressed=0, ascii=0):
        """Get xref object source as a string."""
        if self.is_closed:
            raise ValueError("document closed")
        if g_use_extra:
            ret = extra.xref_object( self.this, xref, compressed, ascii)
            return ret
        pdf = _as_pdf_document(self)
        xreflen = mupdf.pdf_xref_len(pdf)
        if not _INRANGE(xref, 1, xreflen-1) and xref != -1:
            raise ValueError( MSG_BAD_XREF)
        if xref > 0:
            obj = mupdf.pdf_load_object(pdf, xref)
        else:
            obj = mupdf.pdf_trailer(pdf)
        res = JM_object_to_buffer(mupdf.pdf_resolve_indirect(obj), compressed, ascii)
        text = JM_EscapeStrFromBuffer(res)
        return text

    def xref_set_key(self, xref, key, value):
        """Set the value of a PDF dictionary key."""
        if self.is_closed:
            raise ValueError("document closed")

        if not key or not isinstance(key, str) or INVALID_NAME_CHARS.intersection(key) not in (set(), {"/"}):
            raise ValueError("bad 'key'")
        if not isinstance(value, str) or not value or value[0] == "/" and INVALID_NAME_CHARS.intersection(value[1:]) != set():
            raise ValueError("bad 'value'")

        pdf = _as_pdf_document(self)
        xreflen = mupdf.pdf_xref_len(pdf)
        #if not _INRANGE(xref, 1, xreflen-1) and xref != -1:
        #    THROWMSG("bad xref")
        #if len(value) == 0:
        #    THROWMSG("bad 'value'")
        #if len(key) == 0:
        #    THROWMSG("bad 'key'")
        if not _INRANGE(xref, 1, xreflen-1) and xref != -1:
            raise ValueError( MSG_BAD_XREF)
        if xref != -1:
            obj = mupdf.pdf_load_object(pdf, xref)
        else:
            obj = mupdf.pdf_trailer(pdf)
        new_obj = JM_set_object_value(obj, key, value)
        if not new_obj.m_internal:
            return  # did not work: skip update
        if xref != -1:
            mupdf.pdf_update_object(pdf, xref, new_obj)
        else:
            n = mupdf.pdf_dict_len(new_obj)
            for i in range(n):
                mupdf.pdf_dict_put(
                        obj,
                        mupdf.pdf_dict_get_key(new_obj, i),
                        mupdf.pdf_dict_get_val(new_obj, i),
                        )

    def xref_stream(self, xref):
        """Get decompressed xref stream."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        xreflen = mupdf.pdf_xref_len( pdf)
        if not _INRANGE(xref, 1, xreflen-1) and xref != -1:
            raise ValueError( MSG_BAD_XREF)
        if xref >= 0:
            obj = mupdf.pdf_new_indirect( pdf, xref, 0)
        else:
            obj = mupdf.pdf_trailer( pdf)
        r = None
        if mupdf.pdf_is_stream( obj):
            res = mupdf.pdf_load_stream_number( pdf, xref)
            r = JM_BinFromBuffer( res)
        return r

    def xref_stream_raw(self, xref):
        """Get xref stream without decompression."""
        if self.is_closed or self.is_encrypted:
            raise ValueError("document closed or encrypted")
        pdf = _as_pdf_document(self)
        xreflen = mupdf.pdf_xref_len( pdf)
        if not _INRANGE(xref, 1, xreflen-1) and xref != -1:
            raise ValueError( MSG_BAD_XREF)
        if xref >= 0:
            obj = mupdf.pdf_new_indirect( pdf, xref, 0)
        else:
            obj = mupdf.pdf_trailer( pdf)
        r = None
        if mupdf.pdf_is_stream( obj):
            res = mupdf.pdf_load_raw_stream_number( pdf, xref)
            r = JM_BinFromBuffer( res)
        return r

    def xref_xml_metadata(self):
        """Get xref of document XML metadata."""
        pdf = _as_pdf_document(self)
        root = mupdf.pdf_dict_get( mupdf.pdf_trailer( pdf), PDF_NAME('Root'))
        if not root.m_internal:
            RAISEPY( MSG_BAD_PDFROOT, JM_Exc_FileDataError)
        xml = mupdf.pdf_dict_get( root, PDF_NAME('Metadata'))
        xref = 0
        if xml.m_internal:
            xref = mupdf.pdf_to_num( xml)
        return xref
    
    __slots__ = ('this', 'page_count2', 'this_is_pdf', '__dict__')
    
    outline = property(lambda self: self._outline)
    tobytes = write
    is_stream = xref_is_stream

open = Document


class DocumentWriter:

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __init__(self, path, options=''):
        if isinstance( path, str):
            pass
        elif hasattr( path, 'absolute'):
            path = str( path)
        elif hasattr( path, 'name'):
            path = path.name
        if isinstance( path, str):
            self.this = mupdf.FzDocumentWriter( path, options, mupdf.FzDocumentWriter.PathType_PDF)
        else:
            # Need to keep the Python JM_new_output_fileptr_Output instance
            # alive for the lifetime of this DocumentWriter, otherwise calls
            # to virtual methods implemented in Python fail. So we make it a
            # member of this DocumentWriter.
            #
            # Unrelated to this, mupdf.FzDocumentWriter will set
            # self._out.m_internal to null because ownership is passed in.
            #
            out = JM_new_output_fileptr( path)
            self.this = mupdf.FzDocumentWriter( out, options, mupdf.FzDocumentWriter.OutputType_PDF)
            assert out.m_internal_value() == 0
            assert hasattr( self.this, '_out')
    
    def begin_page( self, mediabox):
        mediabox2 = JM_rect_from_py(mediabox)
        device = mupdf.fz_begin_page( self.this, mediabox2)
        device_wrapper = DeviceWrapper( device)
        return device_wrapper
    
    def close( self):
        mupdf.fz_close_document_writer( self.this)
        
    def end_page( self):
        mupdf.fz_end_page( self.this)


class Font:

    def __del__(self):
        if type(self) is not Font:
            return None

    def __init__(
            self,
            fontname=None,
            fontfile=None,
            fontbuffer=None,
            script=0,
            language=None,
            ordering=-1,
            is_bold=0,
            is_italic=0,
            is_serif=0,
            embed=1,
            ):
        
        if fontbuffer:
            if hasattr(fontbuffer, "getvalue"):
                fontbuffer = fontbuffer.getvalue()
            elif isinstance(fontbuffer, bytearray):
                fontbuffer = bytes(fontbuffer)
            if not isinstance(fontbuffer, bytes):
                raise ValueError("bad type: 'fontbuffer'")
        
        if isinstance(fontname, str):
            fname_lower = fontname.lower()
            if "/" in fname_lower or "\\" in fname_lower or "." in fname_lower:
                message("Warning: did you mean a fontfile?")

            if fname_lower in ("cjk", "china-t", "china-ts"):
                ordering = 0

            elif fname_lower.startswith("china-s"):
                ordering = 1
            elif fname_lower.startswith("korea"):
                ordering = 3
            elif fname_lower.startswith("japan"):
                ordering = 2
            elif fname_lower in fitz_fontdescriptors.keys():
                import pymupdf_fonts  # optional fonts
                fontbuffer = pymupdf_fonts.myfont(fname_lower)  # make a copy
                fontname = None  # ensure using fontbuffer only
                del pymupdf_fonts  # remove package again

            elif ordering < 0:
                fontname = Base14_fontdict.get(fontname, fontname)

        lang = mupdf.fz_text_language_from_string(language)
        font = JM_get_font(fontname, fontfile,
                   fontbuffer, script, lang, ordering,
                   is_bold, is_italic, is_serif, embed)
        self.this = font

    def __repr__(self):
        return "Font('%s')" % self.name

    @property
    def ascender(self):
        """Return the glyph ascender value."""
        return mupdf.fz_font_ascender(self.this)

    @property
    def bbox(self):
        return self.this.fz_font_bbox()
    
    @property
    def buffer(self):
        buffer_ = mupdf.FzBuffer( mupdf.ll_fz_keep_buffer( self.this.m_internal.buffer))
        return mupdf.fz_buffer_extract_copy( buffer_)

    def char_lengths(self, text, fontsize=11, language=None, script=0, wmode=0, small_caps=0):
        """Return tuple of char lengths of unicode 'text' under a fontsize."""
        lang = mupdf.fz_text_language_from_string(language)
        rc = []
        for ch in text:
            c = ord(ch)
            if small_caps:
                gid = mupdf.fz_encode_character_sc(self.this, c)
                if gid >= 0:
                    font = self.this
            else:
                gid, font = mupdf.fz_encode_character_with_fallback(self.this, c, script, lang)
            rc.append(fontsize * mupdf.fz_advance_glyph(font, gid, wmode))
        return rc

    @property
    def descender(self):
        """Return the glyph descender value."""
        return mupdf.fz_font_descender(self.this)

    @property
    def flags(self):
        f = mupdf.ll_fz_font_flags(self.this.m_internal)
        if not f:
            return
        assert isinstance( f, mupdf.fz_font_flags_t)
        #log( '{=f}')
        if mupdf_cppyy:
            # cppyy includes remaining higher bits.
            v = [f.is_mono]
            def b(bits):
                ret = v[0] & ((1 << bits)-1)
                v[0] = v[0] >> bits
                return ret
            is_mono = b(1)
            is_serif = b(1)
            is_bold = b(1)
            is_italic = b(1)
            ft_substitute = b(1)
            ft_stretch = b(1)
            fake_bold = b(1)
            fake_italic = b(1)
            has_opentype = b(1)
            invalid_bbox = b(1)
            cjk_lang = b(1)
            embed = b(1)
            never_embed = b(1)
        return {
                "mono":         is_mono if mupdf_cppyy else f.is_mono,
                "serif":        is_serif if mupdf_cppyy else f.is_serif,
                "bold":         is_bold if mupdf_cppyy else f.is_bold,
                "italic":       is_italic if mupdf_cppyy else f.is_italic,
                "substitute":   ft_substitute if mupdf_cppyy else f.ft_substitute,
                "stretch":      ft_stretch if mupdf_cppyy else f.ft_stretch,
                "fake-bold":    fake_bold if mupdf_cppyy else f.fake_bold,
                "fake-italic":  fake_italic if mupdf_cppyy else f.fake_italic,
                "opentype":     has_opentype if mupdf_cppyy else f.has_opentype,
                "invalid-bbox": invalid_bbox if mupdf_cppyy else f.invalid_bbox,
                'cjk':          cjk_lang if mupdf_cppyy else f.cjk,
                'cjk-lang':     cjk_lang if mupdf_cppyy else f.cjk_lang,
                'embed':        embed if mupdf_cppyy else f.embed,
                'never-embed':  never_embed if mupdf_cppyy else f.never_embed,
                }

    def glyph_advance(self, chr_, language=None, script=0, wmode=0, small_caps=0):
        """Return the glyph width of a unicode (font size 1)."""
        lang = mupdf.fz_text_language_from_string(language)
        if small_caps:
            gid = mupdf.fz_encode_character_sc(self.this, chr_)
            if gid >= 0:
                font = self.this
        else:
            gid, font = mupdf.fz_encode_character_with_fallback(self.this, chr_, script, lang)
        return mupdf.fz_advance_glyph(font, gid, wmode)

    def glyph_bbox(self, char, language=None, script=0, small_caps=0):
        """Return the glyph bbox of a unicode (font size 1)."""
        lang = mupdf.fz_text_language_from_string(language)
        if small_caps:
            gid = mupdf.fz_encode_character_sc( self.this, char)
            if gid >= 0:
                font = self.this
        else:
            gid, font = mupdf.fz_encode_character_with_fallback( self.this, char, script, lang)
        return Rect(mupdf.fz_bound_glyph( font, gid, mupdf.FzMatrix()))

    @property
    def glyph_count(self):
        return self.this.m_internal.glyph_count

    def glyph_name_to_unicode(self, name):
        """Return the unicode for a glyph name."""
        return glyph_name_to_unicode(name)

    def has_glyph(self, chr, language=None, script=0, fallback=0, small_caps=0):
        """Check whether font has a glyph for this unicode."""
        if fallback:
            lang = mupdf.fz_text_language_from_string(language)
            gid, font = mupdf.fz_encode_character_with_fallback(self.this, chr, script, lang)
        else:
            if small_caps:
                gid = mupdf.fz_encode_character_sc(self.this, chr)
            else:
                gid = mupdf.fz_encode_character(self.this, chr)
        return gid

    @property
    def is_bold(self):
        return mupdf.fz_font_is_bold( self.this)

    @property
    def is_italic(self):
        return mupdf.fz_font_is_italic( self.this)

    @property
    def is_monospaced(self):
        return mupdf.fz_font_is_monospaced( self.this)

    @property
    def is_serif(self):
        return mupdf.fz_font_is_serif( self.this)

    @property
    def is_writable(self):
        return True # see pymupdf commit ef4056ee4da2
        font = self.this
        flags = mupdf.ll_fz_font_flags(font.m_internal)
        if mupdf_cppyy:
            # cppyy doesn't handle bitfields correctly.
            import cppyy
            ft_substitute = cppyy.gbl.mupdf_mfz_font_flags_ft_substitute( flags)
        else:
            ft_substitute = flags.ft_substitute
        
        if ( mupdf.ll_fz_font_t3_procs(font.m_internal)
                or ft_substitute
                or not mupdf.pdf_font_writing_supported(font)
                ):
            return False
        return True

    @property
    def name(self):
        ret = mupdf.fz_font_name(self.this)
        #log( '{ret=}')
        return ret

    def text_length(self, text, fontsize=11, language=None, script=0, wmode=0, small_caps=0):
        """Return length of unicode 'text' under a fontsize."""
        thisfont = self.this
        lang = mupdf.fz_text_language_from_string(language)
        rc = 0
        if not isinstance(text, str):
            raise TypeError( MSG_BAD_TEXT)
        for ch in text:
            c = ord(ch)
            if small_caps:
                gid = mupdf.fz_encode_character_sc(thisfont, c)
                if gid >= 0:
                    font = thisfont
            else:
                gid, font = mupdf.fz_encode_character_with_fallback(thisfont, c, script, lang)
            rc += mupdf.fz_advance_glyph(font, gid, wmode)
        rc *= fontsize
        return rc

    def unicode_to_glyph_name(self, ch):
        """Return the glyph name for a unicode."""
        return unicode_to_glyph_name(ch)

    def valid_codepoints(self):
        '''
        Returns sorted list of valid unicodes of a fz_font.
        '''
        if mupdf_version_tuple < (1, 24, 11):
            # mupdf.fz_enumerate_font_cmap2() not available.
            return []
        ucs_gids = mupdf.fz_enumerate_font_cmap2(self.this)
        ucss = [i.ucs for i in ucs_gids]
        ucss_unique = set(ucss)
        ucss_unique_sorted = sorted(ucss_unique)
        return ucss_unique_sorted


class Graftmap:

    def __del__(self):
        if not type(self) is Graftmap:
            return
        self.thisown = False

    def __init__(self, doc):
        dst = _as_pdf_document(doc)
        map_ = mupdf.pdf_new_graft_map(dst)
        self.this = map_
        self.thisown = True


class Link:
    def __del__(self):
        self._erase()

    def __init__( self, this):
        assert isinstance( this, mupdf.FzLink)
        self.this = this

    def __repr__(self):
        CheckParent(self)
        return "link on " + str(self.parent)

    def __str__(self):
        CheckParent(self)
        return "link on " + str(self.parent)

    def _border(self, doc, xref):
        pdf = _as_pdf_document(doc, required=0)
        if not pdf.m_internal:
            return
        link_obj = mupdf.pdf_new_indirect(pdf, xref, 0)
        if not link_obj.m_internal:
            return
        b = JM_annot_border(link_obj)
        return b

    def _colors(self, doc, xref):
        pdf = _as_pdf_document(doc, required=0)
        if not pdf.m_internal:
            return
        link_obj = mupdf.pdf_new_indirect( pdf, xref, 0)
        if not link_obj.m_internal:
            raise ValueError( MSG_BAD_XREF)
        b = JM_annot_colors( link_obj)
        return b

    def _erase(self):
        self.parent = None
        self.thisown = False

    def _setBorder(self, border, doc, xref):
        pdf = _as_pdf_document(doc, required=0)
        if not pdf.m_internal:
            return
        link_obj = mupdf.pdf_new_indirect(pdf, xref, 0)
        if not link_obj.m_internal:
            return
        b = JM_annot_set_border(border, pdf, link_obj)
        return b
        
    @property
    def border(self):
        return self._border(self.parent.parent.this, self.xref)

    @property
    def colors(self):
        return self._colors(self.parent.parent.this, self.xref)

    @property
    def dest(self):
        """Create link destination details."""
        if hasattr(self, "parent") and self.parent is None:
            raise ValueError("orphaned object: parent is None")
        if self.parent.parent.is_closed or self.parent.parent.is_encrypted:
            raise ValueError("document closed or encrypted")
        doc = self.parent.parent

        if self.is_external or self.uri.startswith("#"):
            uri = None
        else:
            uri = doc.resolve_link(self.uri)

        return linkDest(self, uri, doc)

    @property
    def flags(self)->int:
        CheckParent(self)
        doc = self.parent.parent
        if not doc.is_pdf:
            return 0
        f = doc.xref_get_key(self.xref, "F")
        if f[1] != "null":
            return int(f[1])
        return 0

    @property
    def is_external(self):
        """Flag the link as external."""
        CheckParent(self)
        if g_use_extra:
            return extra.Link_is_external( self.this)
        this_link = self.this
        if not this_link.m_internal or not this_link.m_internal.uri:
            return False
        return bool( mupdf.fz_is_external_link( this_link.m_internal.uri))

    @property
    def next(self):
        """Next link."""
        if not self.this.m_internal:
            return None
        CheckParent(self)
        if 0 and g_use_extra:
            val = extra.Link_next( self.this)
        else:
            val = self.this.next()
        if not val.m_internal:
            return None
        val = Link( val)
        if val:
            val.thisown = True
            val.parent = self.parent  # copy owning page from prev link
            val.parent._annot_refs[id(val)] = val
            if self.xref > 0:  # prev link has an xref
                link_xrefs = [x[0] for x in self.parent.annot_xrefs() if x[1] == mupdf.PDF_ANNOT_LINK]
                link_ids = [x[2] for x in self.parent.annot_xrefs() if x[1] == mupdf.PDF_ANNOT_LINK]
                idx = link_xrefs.index(self.xref)
                val.xref = link_xrefs[idx + 1]
                val.id = link_ids[idx + 1]
            else:
                val.xref = 0
                val.id = ""
        return val

    @property
    def rect(self):
        """Rectangle ('hot area')."""
        CheckParent(self)
        # utils.py:getLinkDict() appears to expect exceptions from us, so we
        # ensure that we raise on error.
        if self.this is None or not self.this.m_internal:
            raise Exception( 'self.this.m_internal not available')
        val = JM_py_from_rect( self.this.rect())
        val = Rect(val)
        return val

    def set_border(self, border=None, width=0, dashes=None, style=None):
        if type(border) is not dict:
            border = {"width": width, "style": style, "dashes": dashes}
        return self._setBorder(border, self.parent.parent.this, self.xref)

    def set_colors(self, colors=None, stroke=None, fill=None):
        """Set border colors."""
        CheckParent(self)
        doc = self.parent.parent
        if type(colors) is not dict:
            colors = {"fill": fill, "stroke": stroke}
        fill = colors.get("fill")
        stroke = colors.get("stroke")
        if fill is not None:
            message("warning: links have no fill color")
        if stroke in ([], ()):
            doc.xref_set_key(self.xref, "C", "[]")
            return
        if hasattr(stroke, "__float__"):
            stroke = [float(stroke)]
        CheckColor(stroke)
        assert len(stroke) in (1, 3, 4)
        s = f"[{_format_g(stroke)}]"
        doc.xref_set_key(self.xref, "C", s)

    def set_flags(self, flags):
        CheckParent(self)
        doc = self.parent.parent
        if not doc.is_pdf:
            raise ValueError("is no PDF")
        if not type(flags) is int:
            raise ValueError("bad 'flags' value")
        doc.xref_set_key(self.xref, "F", str(flags))
        return None

    @property
    def uri(self):
        """Uri string."""
        #CheckParent(self)
        if g_use_extra:
            return extra.link_uri(self.this)
        this_link = self.this
        return this_link.m_internal.uri if this_link.m_internal else ''

    page = -1


class Matrix:

    def __abs__(self):
        return math.sqrt(sum([c*c for c in self]))

    def __add__(self, m):
        if hasattr(m, "__float__"):
            return Matrix(self.a + m, self.b + m, self.c + m,
                          self.d + m, self.e + m, self.f + m)
        if len(m) != 6:
            raise ValueError("Matrix: bad seq len")
        return Matrix(self.a + m[0], self.b + m[1], self.c + m[2],
                          self.d + m[3], self.e + m[4], self.f + m[5])

    def __bool__(self):
        return not (max(self) == min(self) == 0)

    def __eq__(self, mat):
        if not hasattr(mat, "__len__"):
            return False
        return len(mat) == 6 and not (self - mat)

    def __getitem__(self, i):
        return (self.a, self.b, self.c, self.d, self.e, self.f)[i]

    def __init__(self, *args, a=None, b=None, c=None, d=None, e=None, f=None):
        """
        Matrix() - all zeros
        Matrix(a, b, c, d, e, f)
        Matrix(zoom-x, zoom-y) - zoom
        Matrix(shear-x, shear-y, 1) - shear
        Matrix(degree) - rotate
        Matrix(Matrix) - new copy
        Matrix(sequence) - from 'sequence'
        Matrix(mupdf.FzMatrix) - from MuPDF class wrapper for fz_matrix.
        
        Explicit keyword args a, b, c, d, e, f override any earlier settings if
        not None.
        """
        if not args:
            self.a = self.b = self.c = self.d = self.e = self.f = 0.0
        elif len(args) > 6:
            raise ValueError("Matrix: bad seq len")
        elif len(args) == 6:  # 6 numbers
            self.a, self.b, self.c, self.d, self.e, self.f = map(float, args)
        elif len(args) == 1:  # either an angle or a sequ
            if isinstance(args[0], mupdf.FzMatrix):
                self.a = args[0].a
                self.b = args[0].b
                self.c = args[0].c
                self.d = args[0].d
                self.e = args[0].e
                self.f = args[0].f
            elif hasattr(args[0], "__float__"):
                theta = math.radians(args[0])
                c_ = round(math.cos(theta), 8)
                s_ = round(math.sin(theta), 8)
                self.a = self.d = c_
                self.b = s_
                self.c = -s_
                self.e = self.f = 0.0
            else:
                self.a, self.b, self.c, self.d, self.e, self.f = map(float, args[0])
        elif len(args) == 2 or len(args) == 3 and args[2] == 0:
            self.a, self.b, self.c, self.d, self.e, self.f = float(args[0]), \
                0.0, 0.0, float(args[1]), 0.0, 0.0
        elif len(args) == 3 and args[2] == 1:
            self.a, self.b, self.c, self.d, self.e, self.f = 1.0, \
                float(args[1]), float(args[0]), 1.0, 0.0, 0.0
        else:
            raise ValueError("Matrix: bad args")
        
        # Override with explicit args if specified.
        if a is not None:   self.a = a
        if b is not None:   self.b = b
        if c is not None:   self.c = c
        if d is not None:   self.d = d
        if e is not None:   self.e = e
        if f is not None:   self.f = f

    def __invert__(self):
        """Calculate inverted matrix."""
        m1 = Matrix()
        m1.invert(self)
        return m1

    def __len__(self):
        return 6

    def __mul__(self, m):
        if hasattr(m, "__float__"):
            return Matrix(self.a * m, self.b * m, self.c * m,
                          self.d * m, self.e * m, self.f * m)
        m1 = Matrix(1,1)
        return m1.concat(self, m)

    def __neg__(self):
        return Matrix(-self.a, -self.b, -self.c, -self.d, -self.e, -self.f)

    def __nonzero__(self):
        return not (max(self) == min(self) == 0)

    def __pos__(self):
        return Matrix(self)

    def __repr__(self):
        return "Matrix" + str(tuple(self))

    def __setitem__(self, i, v):
        v = float(v)
        if   i == 0: self.a = v
        elif i == 1: self.b = v
        elif i == 2: self.c = v
        elif i == 3: self.d = v
        elif i == 4: self.e = v
        elif i == 5: self.f = v
        else:
            raise IndexError("index out of range")
        return

    def __sub__(self, m):
        if hasattr(m, "__float__"):
            return Matrix(self.a - m, self.b - m, self.c - m,
                          self.d - m, self.e - m, self.f - m)
        if len(m) != 6:
            raise ValueError("Matrix: bad seq len")
        return Matrix(self.a - m[0], self.b - m[1], self.c - m[2],
                          self.d - m[3], self.e - m[4], self.f - m[5])

    def __truediv__(self, m):
        if hasattr(m, "__float__"):
            return Matrix(self.a * 1./m, self.b * 1./m, self.c * 1./m,
                          self.d * 1./m, self.e * 1./m, self.f * 1./m)
        m1 = util_invert_matrix(m)[1]
        if not m1:
            raise ZeroDivisionError("matrix not invertible")
        m2 = Matrix(1,1)
        return m2.concat(self, m1)

    def concat(self, one, two):
        """Multiply two matrices and replace current one."""
        if not len(one) == len(two) == 6:
            raise ValueError("Matrix: bad seq len")
        self.a, self.b, self.c, self.d, self.e, self.f = util_concat_matrix(one, two)
        return self

    def invert(self, src=None):
        """Calculate the inverted matrix. Return 0 if successful and replace
        current one. Else return 1 and do nothing.
        """
        if src is None:
            dst = util_invert_matrix(self)
        else:
            dst = util_invert_matrix(src)
        if dst[0] == 1:
            return 1
        self.a, self.b, self.c, self.d, self.e, self.f = dst[1]
        return 0

    @property
    def is_rectilinear(self):
        """True if rectangles are mapped to rectangles."""
        return (abs(self.b) < EPSILON and abs(self.c) < EPSILON) or \
            (abs(self.a) < EPSILON and abs(self.d) < EPSILON)

    def prerotate(self, theta):
        """Calculate pre rotation and replace current matrix."""
        theta = float(theta)
        while theta < 0: theta += 360
        while theta >= 360: theta -= 360
        if abs(0 - theta) < EPSILON:
            pass

        elif abs(90.0 - theta) < EPSILON:
            a = self.a
            b = self.b
            self.a = self.c
            self.b = self.d
            self.c = -a
            self.d = -b

        elif abs(180.0 - theta) < EPSILON:
            self.a = -self.a
            self.b = -self.b
            self.c = -self.c
            self.d = -self.d

        elif abs(270.0 - theta) < EPSILON:
            a = self.a
            b = self.b
            self.a = -self.c
            self.b = -self.d
            self.c = a
            self.d = b

        else:
            rad = math.radians(theta)
            s = math.sin(rad)
            c = math.cos(rad)
            a = self.a
            b = self.b
            self.a = c * a + s * self.c
            self.b = c * b + s * self.d
            self.c =-s * a + c * self.c
            self.d =-s * b + c * self.d

        return self

    def prescale(self, sx, sy):
        """Calculate pre scaling and replace current matrix."""
        sx = float(sx)
        sy = float(sy)
        self.a *= sx
        self.b *= sx
        self.c *= sy
        self.d *= sy
        return self

    def preshear(self, h, v):
        """Calculate pre shearing and replace current matrix."""
        h = float(h)
        v = float(v)
        a, b = self.a, self.b
        self.a += v * self.c
        self.b += v * self.d
        self.c += h * a
        self.d += h * b
        return self

    def pretranslate(self, tx, ty):
        """Calculate pre translation and replace current matrix."""
        tx = float(tx)
        ty = float(ty)
        self.e += tx * self.a + ty * self.c
        self.f += tx * self.b + ty * self.d
        return self

    __inv__ = __invert__
    __div__ = __truediv__
    norm = __abs__


class IdentityMatrix(Matrix):
    """Identity matrix [1, 0, 0, 1, 0, 0]"""

    def __hash__(self):
        return hash((1,0,0,1,0,0))

    def __init__(self):
        Matrix.__init__(self, 1.0, 1.0)

    def __repr__(self):
        return "IdentityMatrix(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)"

    def __setattr__(self, name, value):
        if name in "ad":
            self.__dict__[name] = 1.0
        elif name in "bcef":
            self.__dict__[name] = 0.0
        else:
            self.__dict__[name] = value

    def checkargs(*args):
        raise NotImplementedError("Identity is readonly")

Identity = IdentityMatrix()


class linkDest:
    """link or outline destination details"""

    def __init__(self, obj, rlink, document=None):
        isExt = obj.is_external
        isInt = not isExt
        self.dest = ""
        self.file_spec = ""
        self.flags = 0
        self.is_map = False
        self.is_uri = False
        self.kind = LINK_NONE
        self.lt = Point(0, 0)
        self.named = dict()
        self.new_window = ""
        self.page = obj.page
        self.rb = Point(0, 0)
        self.uri = obj.uri
        
        def uri_to_dict(uri):
            items = self.uri[1:].split('&')
            ret = dict()
            for item in items:
                eq = item.find('=')
                if eq >= 0:
                    ret[item[:eq]] = item[eq+1:]
                else:
                    ret[item] = None
            return ret

        def unescape(name):
            """Unescape '%AB' substrings to chr(0xAB)."""
            split = name.replace("%%", "%25")  # take care of escaped '%'
            split = split.split("%")
            newname = split[0]
            for item in split[1:]:
                piece = item[:2]
                newname += chr(int(piece, base=16))
                newname += item[2:]
            return newname
        
        if rlink and not self.uri.startswith("#"):
            self.uri = f"#page={rlink[0] + 1}&zoom=0,{_format_g(rlink[1])},{_format_g(rlink[2])}"
        if obj.is_external:
            self.page = -1
            self.kind = LINK_URI
        if not self.uri:
            self.page = -1
            self.kind = LINK_NONE
        if isInt and self.uri:
            self.uri = self.uri.replace("&zoom=nan", "&zoom=0")
            if self.uri.startswith("#"):
                self.kind = LINK_GOTO
                m = re.match('^#page=([0-9]+)&zoom=([0-9.]+),(-?[0-9.]+),(-?[0-9.]+)$', self.uri)
                if m:
                    self.page = int(m.group(1)) - 1
                    self.lt = Point(float((m.group(3))), float(m.group(4)))
                    self.flags = self.flags | LINK_FLAG_L_VALID | LINK_FLAG_T_VALID
                else:
                    m = re.match('^#page=([0-9]+)$', self.uri)
                    if m:
                        self.page = int(m.group(1)) - 1
                    else:
                        self.kind = LINK_NAMED
                        m = re.match('^#nameddest=(.*)', self.uri)
                        assert document
                        if document and m:
                            named = unescape(m.group(1))
                            self.named = document.resolve_names().get(named)
                            if self.named is None:
                                # document.resolve_names() does not contain an
                                # entry for `named` so use an empty dict.
                                self.named = dict()
                            self.named['nameddest'] = named
                        else:
                            self.named = uri_to_dict(self.uri[1:])
            else:
                self.kind = LINK_NAMED
                self.named = uri_to_dict(self.uri)
        if obj.is_external:
            if not self.uri:
                pass
            elif self.uri.startswith("file:"):
                self.file_spec = self.uri[5:]
                if self.file_spec.startswith("//"):
                    self.file_spec = self.file_spec[2:]
                self.is_uri = False
                self.uri = ""
                self.kind = LINK_LAUNCH
                ftab = self.file_spec.split("#")
                if len(ftab) == 2:
                    if ftab[1].startswith("page="):
                        self.kind = LINK_GOTOR
                        self.file_spec = ftab[0]
                        self.page = int(ftab[1].split("&")[0][5:]) - 1
            elif ":" in self.uri:
                self.is_uri = True
                self.kind = LINK_URI
            else:
                self.is_uri = True
                self.kind = LINK_LAUNCH
        assert isinstance(self.named, dict)

class Widget:
    '''
    Class describing a PDF form field ("widget")
    '''

    def __init__(self):
        self.border_color = None
        self.border_style = "S"
        self.border_width = 0
        self.border_dashes = None
        self.choice_values = None  # choice fields only
        self.rb_parent = None   # radio buttons only: xref of owning parent

        self.field_name = None  # field name
        self.field_label = None # field label
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
        self._text_da = ""  # /DA = default appearance

        self.script = None  # JavaScript (/A)
        self.script_stroke = None  # JavaScript (/AA/K)
        self.script_format = None  # JavaScript (/AA/F)
        self.script_change = None  # JavaScript (/AA/V)
        self.script_calc = None  # JavaScript (/AA/C)
        self.script_blur = None  # JavaScript (/AA/Bl)
        self.script_focus = None  # JavaScript (/AA/Fo) codespell:ignore

        self.rect = None  # annot value
        self.xref = 0  # annot value

    def __repr__(self):
        #return "'%s' widget on %s" % (self.field_type_string, str(self.parent))
        # No self.parent.
        return f'Widget:(field_type={self.field_type_string} script={self.script})'
        return "'%s' widget" % (self.field_type_string)

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

    def _checker(self):
        """Any widget type checks.
        """
        if self.field_type not in range(1, 8):
            raise ValueError("bad field type")

        # if setting a radio button to ON, first set Off all buttons
        # in the group - this is not done by MuPDF:
        if self.field_type == mupdf.PDF_WIDGET_TYPE_RADIOBUTTON and self.field_value not in (False, "Off") and hasattr(self, "parent"):
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
                mupdf.PDF_WIDGET_TYPE_BUTTON,
                mupdf.PDF_WIDGET_TYPE_CHECKBOX,
                mupdf.PDF_WIDGET_TYPE_RADIOBUTTON,
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
            return
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

    @property
    def next(self):
        return self._annot.next

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
        bstate = self.button_states()
        if bstate is None:
            bstate = dict()
        for k in bstate.keys():
            for v in bstate[k]:
                if v != "Off":
                    return v
        message("warning: radio button has no 'On' value.")
        return True

    def reset(self):
        """Reset the field value to its default.
        """
        TOOLS._reset_widget(self._annot)

    def update(self):
        """Reflect Python object in the PDF.
        """
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
        # finally update the widget

        # if widget has a '/AA/C' script, make sure it is in the '/CO'
        # array of the '/AcroForm' dictionary.
        if self.script_calc:  # there is a "calculation" script:
            # make sure we are in the /CO array
            util_ensure_widget_calc(self._annot)

        # finally update the widget
        TOOLS._save_widget(self._annot, self)
        self._text_da = ""


from . import _extra


class Outline:

    def __init__(self, ol):
        self.this = ol

    @property
    def dest(self):
        '''outline destination details'''
        return linkDest(self, None, None)

    def destination(self, document):
        '''
        Like `dest` property but uses `document` to resolve destinations for
        kind=LINK_NAMED.
        '''
        return linkDest(self, None, document)
        
    @property
    def down(self):
        ol = self.this
        down_ol = ol.down()
        if not down_ol.m_internal:
            return
        return Outline(down_ol)

    @property
    def is_external(self):
        if g_use_extra:
            # calling _extra.* here appears to save significant time in
            # test_toc.py:test_full_toc, 1.2s=>0.94s.
            #
            return _extra.Outline_is_external( self.this)
        ol = self.this
        if not ol.m_internal:
            return False
        uri = ol.m_internal.uri if 1 else ol.uri()
        if uri is None:
            return False
        return mupdf.fz_is_external_link(uri)

    @property
    def is_open(self):
        if 1:
            return self.this.m_internal.is_open
        return self.this.is_open()

    @property
    def next(self):
        ol = self.this
        next_ol = ol.next()
        if not next_ol.m_internal:
            return
        return Outline(next_ol)

    @property
    def page(self):
        if 1:
            return self.this.m_internal.page.page
        return self.this.page().page

    @property
    def title(self):
        return self.this.m_internal.title

    @property
    def uri(self):
        ol = self.this
        if not ol.m_internal:
            return None
        return ol.m_internal.uri

    @property
    def x(self):
        return self.this.m_internal.x

    @property
    def y(self):
        return self.this.m_internal.y

    __slots__ = [ 'this']


def _make_PdfFilterOptions(
        recurse=0,
        instance_forms=0,
        ascii=0,
        no_update=0,
        sanitize=0,
        sopts=None,
        ):
    '''
    Returns a mupdf.PdfFilterOptions instance.
    '''

    filter_ = mupdf.PdfFilterOptions()
    filter_.recurse = recurse
    filter_.instance_forms = instance_forms
    filter_.ascii = ascii
    
    filter_.no_update = no_update
    if sanitize:
        # We want to use a PdfFilterFactory whose `.filter` fn pointer is
        # set to MuPDF's `pdf_new_sanitize_filter()`. But not sure how to
        # get access to this raw fn in Python; and on Windows raw MuPDF
        # functions are not even available to C++.
        #
        # So we use SWIG Director to implement our own
        # PdfFilterFactory whose `filter()` method calls
        # `mupdf.ll_pdf_new_sanitize_filter()`.
        if sopts:
            assert isinstance(sopts, mupdf.PdfSanitizeFilterOptions)
        else:
            sopts = mupdf.PdfSanitizeFilterOptions()
        class Factory(mupdf.PdfFilterFactory2):
            def __init__(self):
                super().__init__()
                self.use_virtual_filter()
                self.sopts = sopts
            def filter(self, ctx, doc, chain, struct_parents, transform, options):
                if 0:
                    log(f'sanitize filter.filter():')
                    log(f'    {self=}')
                    log(f'    {ctx=}')
                    log(f'    {doc=}')
                    log(f'    {chain=}')
                    log(f'    {struct_parents=}')
                    log(f'    {transform=}')
                    log(f'    {options=}')
                    log(f'    {self.sopts.internal()=}')
                return mupdf.ll_pdf_new_sanitize_filter(
                        doc,
                        chain,
                        struct_parents,
                        transform,
                        options,
                        self.sopts.internal(),
                        )

        factory = Factory()
        filter_.add_factory(factory.internal())
        filter_._factory = factory
    return filter_


class Page:

    def __init__(self, page, document):
        assert isinstance(page, (mupdf.FzPage, mupdf.PdfPage)), f'page is: {page}'
        self.this = page
        self.thisown = True
        self.last_point = None
        self.draw_cont = ''
        self._annot_refs = dict()
        self.parent = document
        if page.m_internal:
            if isinstance( page, mupdf.PdfPage):
                self.number = page.m_internal.super.number
            else:
                self.number = page.m_internal.number
        else:
            self.number = None

    def __repr__(self):
        return self.__str__()
        CheckParent(self)
        x = self.parent.name
        if self.parent.stream is not None:
            x = "<memory, doc# %i>" % (self.parent._graft_id,)
        if x == "":
            x = "<new PDF, doc# %i>" % self.parent._graft_id
        return "page %s of %s" % (self.number, x)

    def __str__(self):
        #CheckParent(self)
        parent = getattr(self, 'parent', None)
        if isinstance(self.this.m_internal, mupdf.pdf_page):
            number = self.this.m_internal.super.number
        else:
            number = self.this.m_internal.number
        ret = f'page {number}'
        if parent:
            x = self.parent.name
            if self.parent.stream is not None:
                x = "<memory, doc# %i>" % (self.parent._graft_id,)
            if x == "":
                x = "<new PDF, doc# %i>" % self.parent._graft_id
            ret += f' of {x}'
        return ret

    def _add_caret_annot(self, point):
        if g_use_extra:
            annot = extra._add_caret_annot( self.this, JM_point_from_py(point))
        else:
            page = self._pdf_page()
            annot = mupdf.pdf_create_annot(page, mupdf.PDF_ANNOT_CARET)
            if point:
                p = JM_point_from_py(point)
                r = mupdf.pdf_annot_rect(annot)
                r = mupdf.FzRect(p.x, p.y, p.x + r.x1 - r.x0, p.y + r.y1 - r.y0)
                mupdf.pdf_set_annot_rect(annot, r)
            mupdf.pdf_update_annot(annot)
            JM_add_annot_id(annot, "A")
        return annot

    def _add_file_annot(self, point, buffer_, filename, ufilename=None, desc=None, icon=None):
        page = self._pdf_page()
        uf = ufilename if ufilename else filename
        d = desc if desc else filename
        p = JM_point_from_py(point)
        filebuf = JM_BufferFromBytes(buffer_)
        if not filebuf.m_internal:
            raise TypeError( MSG_BAD_BUFFER)
        annot = mupdf.pdf_create_annot(page, mupdf.PDF_ANNOT_FILE_ATTACHMENT)
        r = mupdf.pdf_annot_rect(annot)
        r = mupdf.fz_make_rect(p.x, p.y, p.x + r.x1 - r.x0, p.y + r.y1 - r.y0)
        mupdf.pdf_set_annot_rect(annot, r)
        flags = mupdf.PDF_ANNOT_IS_PRINT
        mupdf.pdf_set_annot_flags(annot, flags)

        if icon:
            mupdf.pdf_set_annot_icon_name(annot, icon)

        val = JM_embed_file(page.doc(), filebuf, filename, uf, d, 1)
        mupdf.pdf_dict_put(mupdf.pdf_annot_obj(annot), PDF_NAME('FS'), val)
        mupdf.pdf_dict_put_text_string(mupdf.pdf_annot_obj(annot), PDF_NAME('Contents'), filename)
        mupdf.pdf_update_annot(annot)
        mupdf.pdf_set_annot_rect(annot, r)
        mupdf.pdf_set_annot_flags(annot, flags)
        JM_add_annot_id(annot, "A")
        return Annot(annot)

    def _add_freetext_annot(
            self, rect,
            text,
            fontsize=11,
            fontname=None,
            text_color=None,
            fill_color=None,
            border_color=None,
            align=0,
            rotate=0,
            ):
        page = self._pdf_page()
        nfcol, fcol = JM_color_FromSequence(fill_color)
        ntcol, tcol = JM_color_FromSequence(text_color)
        r = JM_rect_from_py(rect)
        if mupdf.fz_is_infinite_rect(r) or mupdf.fz_is_empty_rect(r):
            raise ValueError( MSG_BAD_RECT)
        annot = mupdf.pdf_create_annot( page, mupdf.PDF_ANNOT_FREE_TEXT)
        annot_obj = mupdf.pdf_annot_obj( annot)
        mupdf.pdf_set_annot_contents( annot, text)
        mupdf.pdf_set_annot_rect( annot, r)
        mupdf.pdf_dict_put_int( annot_obj, PDF_NAME('Rotate'), rotate)
        mupdf.pdf_dict_put_int( annot_obj, PDF_NAME('Q'), align)

        if nfcol > 0:
            mupdf.pdf_set_annot_color( annot, fcol[:nfcol])

        # insert the default appearance string
        JM_make_annot_DA(annot, ntcol, tcol, fontname, fontsize)
        mupdf.pdf_update_annot( annot)
        JM_add_annot_id(annot, "A")
        val = Annot(annot)

        #%pythonappend _add_freetext_annot
        ap = val._getAP()
        BT = ap.find(b"BT")
        ET = ap.rfind(b"ET") + 2
        ap = ap[BT:ET]
        w = rect[2]-rect[0]
        h = rect[3]-rect[1]
        if rotate in (90, -90, 270):
            w, h = h, w
        re = f"0 0 {_format_g((w, h))} re".encode()
        ap = re + b"\nW\nn\n" + ap
        ope = None
        bwidth = b""
        fill_string = ColorCode(fill_color, "f").encode()
        if fill_string:
            fill_string += b"\n"
            ope = b"f"
        stroke_string = ColorCode(border_color, "c").encode()
        if stroke_string:
            stroke_string += b"\n"
            bwidth = b"1 w\n"
            ope = b"S"
        if fill_string and stroke_string:
            ope = b"B"
        if ope is not None:
            ap = bwidth + fill_string + stroke_string + re + b"\n" + ope + b"\n" + ap
        val._setAP(ap)
        return val

    def _add_ink_annot(self, list):
        page = _as_pdf_page(self.this)
        if not PySequence_Check(list):
            raise ValueError( MSG_BAD_ARG_INK_ANNOT)
        ctm = mupdf.FzMatrix()
        mupdf.pdf_page_transform(page, mupdf.FzRect(0), ctm)
        inv_ctm = mupdf.fz_invert_matrix(ctm)
        annot = mupdf.pdf_create_annot(page, mupdf.PDF_ANNOT_INK)
        annot_obj = mupdf.pdf_annot_obj(annot)
        n0 = len(list)
        inklist = mupdf.pdf_new_array(page.doc(), n0)

        for j in range(n0):
            sublist = list[j]
            n1 = len(sublist)
            stroke = mupdf.pdf_new_array(page.doc(), 2 * n1)

            for i in range(n1):
                p = sublist[i]
                if not PySequence_Check(p) or PySequence_Size(p) != 2:
                    raise ValueError( MSG_BAD_ARG_INK_ANNOT)
                point = mupdf.fz_transform_point(JM_point_from_py(p), inv_ctm)
                mupdf.pdf_array_push_real(stroke, point.x)
                mupdf.pdf_array_push_real(stroke, point.y)

            mupdf.pdf_array_push(inklist, stroke)

        mupdf.pdf_dict_put(annot_obj, PDF_NAME('InkList'), inklist)
        mupdf.pdf_update_annot(annot)
        JM_add_annot_id(annot, "A")
        return Annot(annot)

    def _add_line_annot(self, p1, p2):
        page = self._pdf_page()
        annot = mupdf.pdf_create_annot(page, mupdf.PDF_ANNOT_LINE)
        a = JM_point_from_py(p1)
        b = JM_point_from_py(p2)
        mupdf.pdf_set_annot_line(annot, a, b)
        mupdf.pdf_update_annot(annot)
        JM_add_annot_id(annot, "A")
        assert annot.m_internal
        return Annot(annot)

    def _add_multiline(self, points, annot_type):
        page = self._pdf_page()
        if len(points) < 2:
            raise ValueError( MSG_BAD_ARG_POINTS)
        annot = mupdf.pdf_create_annot(page, annot_type)
        for p in points:
            if (PySequence_Size(p) != 2):
                raise ValueError( MSG_BAD_ARG_POINTS)
            point = JM_point_from_py(p)
            mupdf.pdf_add_annot_vertex(annot, point)

        mupdf.pdf_update_annot(annot)
        JM_add_annot_id(annot, "A")
        return Annot(annot)

    def _add_redact_annot(self, quad, text=None, da_str=None, align=0, fill=None, text_color=None):
        page = self._pdf_page()
        fcol = [ 1, 1, 1, 0]
        nfcol = 0
        annot = mupdf.pdf_create_annot(page, mupdf.PDF_ANNOT_REDACT)
        q = JM_quad_from_py(quad)
        r = mupdf.fz_rect_from_quad(q)
        # TODO calculate de-rotated rect
        mupdf.pdf_set_annot_rect(annot, r)
        if fill:
            nfcol, fcol = JM_color_FromSequence(fill)
            arr = mupdf.pdf_new_array(page.doc(), nfcol)
            for i in range(nfcol):
                mupdf.pdf_array_push_real(arr, fcol[i])
            mupdf.pdf_dict_put(mupdf.pdf_annot_obj(annot), PDF_NAME('IC'), arr)
        if text:
            assert da_str
            mupdf.pdf_dict_puts(
                    mupdf.pdf_annot_obj(annot),
                    "OverlayText",
                    mupdf.pdf_new_text_string(text),
                    )
            mupdf.pdf_dict_put_text_string(mupdf.pdf_annot_obj(annot), PDF_NAME('DA'), da_str)
            mupdf.pdf_dict_put_int(mupdf.pdf_annot_obj(annot), PDF_NAME('Q'), align)
        mupdf.pdf_update_annot(annot)
        JM_add_annot_id(annot, "A")
        annot = mupdf.ll_pdf_keep_annot(annot.m_internal)
        annot = mupdf.PdfAnnot( annot)
        return Annot(annot)

    def _add_square_or_circle(self, rect, annot_type):
        page = self._pdf_page()
        r = JM_rect_from_py(rect)
        if mupdf.fz_is_infinite_rect(r) or mupdf.fz_is_empty_rect(r):
            raise ValueError( MSG_BAD_RECT)
        annot = mupdf.pdf_create_annot(page, annot_type)
        mupdf.pdf_set_annot_rect(annot, r)
        mupdf.pdf_update_annot(annot)
        JM_add_annot_id(annot, "A")
        assert annot.m_internal
        return Annot(annot)

    def _add_stamp_annot(self, rect, stamp=0):
        page = self._pdf_page()
        stamp_id = [
                PDF_NAME('Approved'),
                PDF_NAME('AsIs'),
                PDF_NAME('Confidential'),
                PDF_NAME('Departmental'),
                PDF_NAME('Experimental'),
                PDF_NAME('Expired'),
                PDF_NAME('Final'),
                PDF_NAME('ForComment'),
                PDF_NAME('ForPublicRelease'),
                PDF_NAME('NotApproved'),
                PDF_NAME('NotForPublicRelease'),
                PDF_NAME('Sold'),
                PDF_NAME('TopSecret'),
                PDF_NAME('Draft'),
                ]
        n = len(stamp_id)
        name = stamp_id[0]
        r = JM_rect_from_py(rect)
        if mupdf.fz_is_infinite_rect(r) or mupdf.fz_is_empty_rect(r):
            raise ValueError( MSG_BAD_RECT)
        if _INRANGE(stamp, 0, n-1):
            name = stamp_id[stamp]
        annot = mupdf.pdf_create_annot(page, mupdf.PDF_ANNOT_STAMP)
        mupdf.pdf_set_annot_rect(annot, r)
        try:
            n = PDF_NAME('Name')
            mupdf.pdf_dict_put(mupdf.pdf_annot_obj(annot), PDF_NAME('Name'), name)
        except Exception:
            if g_exceptions_verbose:    exception_info()
            raise
        mupdf.pdf_set_annot_contents(
                annot,
                mupdf.pdf_dict_get_name(mupdf.pdf_annot_obj(annot), PDF_NAME('Name')),
                )
        mupdf.pdf_update_annot(annot)
        JM_add_annot_id(annot, "A")
        return Annot(annot)

    def _add_text_annot(self, point, text, icon=None):
        page = self._pdf_page()
        p = JM_point_from_py( point)
        annot = mupdf.pdf_create_annot(page, mupdf.PDF_ANNOT_TEXT)
        r = mupdf.pdf_annot_rect(annot)
        r = mupdf.fz_make_rect(p.x, p.y, p.x + r.x1 - r.x0, p.y + r.y1 - r.y0)
        mupdf.pdf_set_annot_rect(annot, r)
        mupdf.pdf_set_annot_contents(annot, text)
        if icon:
            mupdf.pdf_set_annot_icon_name(annot, icon)
        mupdf.pdf_update_annot(annot)
        JM_add_annot_id(annot, "A")
        return Annot(annot)

    def _add_text_marker(self, quads, annot_type):

        CheckParent(self)
        if not self.parent.is_pdf:
            raise ValueError("is no PDF")

        val = Page__add_text_marker(self, quads, annot_type)
        if not val:
            return None
        val.parent = weakref.proxy(self)
        self._annot_refs[id(val)] = val

        return val

    def _addAnnot_FromString(self, linklist):
        """Add links from list of object sources."""
        CheckParent(self)
        if g_use_extra:
            self.__class__._addAnnot_FromString = extra.Page_addAnnot_FromString
            #log('Page._addAnnot_FromString() deferring to extra.Page_addAnnot_FromString().')
            return extra.Page_addAnnot_FromString( self.this, linklist)
        page = _as_pdf_page(self.this)
        lcount = len(linklist)  # link count
        if lcount < 1:
            return
        i = -1

        # insert links from the provided sources
        if not isinstance(linklist, tuple):
            raise ValueError( "bad 'linklist' argument")
        if not mupdf.pdf_dict_get( page.obj(), PDF_NAME('Annots')).m_internal:
            mupdf.pdf_dict_put_array( page.obj(), PDF_NAME('Annots'), lcount)
        annots = mupdf.pdf_dict_get( page.obj(), PDF_NAME('Annots'))
        assert annots.m_internal, f'{lcount=} {annots.m_internal=}'
        for i in range(lcount):
            txtpy = linklist[i]
            text = JM_StrAsChar(txtpy)
            if not text:
                message("skipping bad link / annot item %i.", i)
                continue
            try:
                annot = mupdf.pdf_add_object( page.doc(), JM_pdf_obj_from_str( page.doc(), text))
                ind_obj = mupdf.pdf_new_indirect( page.doc(), mupdf.pdf_to_num( annot), 0)
                mupdf.pdf_array_push( annots, ind_obj)
            except Exception:
                if g_exceptions_verbose:    exception_info()
                message("skipping bad link / annot item %i.\n" % i)

    def _addWidget(self, field_type, field_name):
        page = self._pdf_page()
        pdf = page.doc()
        annot = JM_create_widget(pdf, page, field_type, field_name)
        if not annot.m_internal:
            raise RuntimeError( "cannot create widget")
        JM_add_annot_id(annot, "W")
        return Annot(annot)

    def _apply_redactions(self, text, images, graphics):
        page = self._pdf_page()
        opts = mupdf.PdfRedactOptions()
        opts.black_boxes = 0  # no black boxes
        opts.text = text  # how to treat text
        opts.image_method = images  # how to treat images
        opts.line_art = graphics  # how to treat vector graphics
        success = mupdf.pdf_redact_page(page.doc(), page, opts)
        return success

    def _erase(self):
        self._reset_annot_refs()
        try:
            self.parent._forget_page(self)
        except Exception:
            exception_info()
            pass
        self.parent = None
        self.thisown = False
        self.number = None
        self.this = None

    def _count_q_balance(self):
        """Count missing graphic state pushs and pops.

        Returns:
            A pair of integers (push, pop). Push is the number of missing
            PDF "q" commands, pop is the number of "Q" commands.
            A balanced graphics state for the page will be reached if its
            /Contents is prepended with 'push' copies of string "q\n"
            and appended with 'pop' copies of "\nQ".
        """
        page = _as_pdf_page(self)  # need the underlying PDF page
        res = mupdf.pdf_dict_get(  # access /Resources
            page.obj(),
            mupdf.PDF_ENUM_NAME_Resources,
        )
        cont = mupdf.pdf_dict_get(  # access /Contents
            page.obj(),
            mupdf.PDF_ENUM_NAME_Contents,
        )
        pdf = _as_pdf_document(self.parent)  # need underlying PDF document

        # return value of MuPDF function
        return mupdf.pdf_count_q_balance_outparams_fn(pdf, res, cont)

    def _get_optional_content(self, oc: OptInt) -> OptStr:
        if oc is None or oc == 0:
            return None
        doc = self.parent
        check = doc.xref_object(oc, compressed=True)
        if not ("/Type/OCG" in check or "/Type/OCMD" in check):
            #log( 'raising "bad optional content"')
            raise ValueError("bad optional content: 'oc'")
        #log( 'Looking at self._get_resource_properties()')
        props = {}
        for p, x in self._get_resource_properties():
            props[x] = p
        if oc in props.keys():
            return props[oc]
        i = 0
        mc = "MC%i" % i
        while mc in props.values():
            i += 1
            mc = "MC%i" % i
        self._set_resource_property(mc, oc)
        #log( 'returning {mc=}')
        return mc

    def _get_resource_properties(self):
        '''
        page list Resource/Properties
        '''
        page = self._pdf_page()
        rc = JM_get_resource_properties(page.obj())
        return rc

    def _get_textpage(self, clip=None, flags=0, matrix=None):
        if g_use_extra:
            ll_tpage = extra.page_get_textpage(self.this, clip, flags, matrix)
            tpage = mupdf.FzStextPage(ll_tpage)
            return tpage
        page = self.this
        options = mupdf.FzStextOptions(flags)
        rect = JM_rect_from_py(clip)
        # Default to page's rect if `clip` not specified, for #2048.
        rect = mupdf.fz_bound_page(page) if clip is None else JM_rect_from_py(clip)
        ctm = JM_matrix_from_py(matrix)
        tpage = mupdf.FzStextPage(rect)
        dev = mupdf.fz_new_stext_device(tpage, options)
        if _globals.no_device_caching:
            mupdf.fz_enable_device_hints( dev, mupdf.FZ_NO_CACHE)
        if isinstance(page, mupdf.FzPage):
            pass
        elif isinstance(page, mupdf.PdfPage):
            page = page.super()
        else:
            assert 0, f'Unrecognised {type(page)=}'
        mupdf.fz_run_page(page, dev, ctm, mupdf.FzCookie())
        mupdf.fz_close_device(dev)
        return tpage

    def _insert_image(self,
            filename=None, pixmap=None, stream=None, imask=None, clip=None,
            overlay=1, rotate=0, keep_proportion=1, oc=0, width=0, height=0,
            xref=0, alpha=-1, _imgname=None, digests=None
            ):
        maskbuf = mupdf.FzBuffer()
        page = self._pdf_page()
        # This will create an empty PdfDocument with a call to
        # pdf_new_document() then assign page.doc()'s return value to it (which
        # drop the original empty pdf_document).
        pdf = page.doc()
        w = width
        h = height
        img_xref = xref
        rc_digest = 0

        do_process_pixmap = 1
        do_process_stream = 1
        do_have_imask = 1
        do_have_image = 1
        do_have_xref = 1

        if xref > 0:
            ref = mupdf.pdf_new_indirect(pdf, xref, 0)
            w = mupdf.pdf_to_int( mupdf.pdf_dict_geta( ref, PDF_NAME('Width'), PDF_NAME('W')))
            h = mupdf.pdf_to_int( mupdf.pdf_dict_geta( ref, PDF_NAME('Height'), PDF_NAME('H')))
            if w + h == 0:
                raise ValueError( MSG_IS_NO_IMAGE)
            #goto have_xref()
            do_process_pixmap = 0
            do_process_stream = 0
            do_have_imask = 0
            do_have_image = 0

        else:
            if stream:
                imgbuf = JM_BufferFromBytes(stream)
                do_process_pixmap = 0
            else:
                if filename:
                    imgbuf = mupdf.fz_read_file(filename)
                    #goto have_stream()
                    do_process_pixmap = 0

        if do_process_pixmap:
            #log( 'do_process_pixmap')
            # process pixmap ---------------------------------
            arg_pix = pixmap.this
            w = arg_pix.w()
            h = arg_pix.h()
            digest = mupdf.fz_md5_pixmap2(arg_pix)
            md5_py = digest
            temp = digests.get(md5_py, None)
            if temp is not None:
                img_xref = temp
                ref = mupdf.pdf_new_indirect(page.doc(), img_xref, 0)
                #goto have_xref()
                do_process_stream = 0
                do_have_imask = 0
                do_have_image = 0
            else:
                if arg_pix.alpha() == 0:
                    image = mupdf.fz_new_image_from_pixmap(arg_pix, mupdf.FzImage())
                else:
                    pm = mupdf.fz_convert_pixmap(
                            arg_pix,
                            mupdf.FzColorspace(),
                            mupdf.FzColorspace(),
                            mupdf.FzDefaultColorspaces(None),
                            mupdf.FzColorParams(),
                            1,
                            )
                    pm.alpha = 0
                    pm.colorspace = None
                    mask = mupdf.fz_new_image_from_pixmap(pm, mupdf.FzImage())
                    image = mupdf.fz_new_image_from_pixmap(arg_pix, mask)
                #goto have_image()
                do_process_stream = 0
                do_have_imask = 0

        if do_process_stream:
            #log( 'do_process_stream')
            # process stream ---------------------------------
            state = mupdf.FzMd5()
            if mupdf_cppyy:
                mupdf.fz_md5_update_buffer( state, imgbuf)
            else:
                mupdf.fz_md5_update(state, imgbuf.m_internal.data, imgbuf.m_internal.len)
            if imask:
                maskbuf = JM_BufferFromBytes(imask)
                if mupdf_cppyy:
                    mupdf.fz_md5_update_buffer( state, maskbuf)
                else:
                    mupdf.fz_md5_update(state, maskbuf.m_internal.data, maskbuf.m_internal.len)
            digest = mupdf.fz_md5_final2(state)
            md5_py = bytes(digest)
            temp = digests.get(md5_py, None)
            if temp is not None:
                img_xref = temp
                ref = mupdf.pdf_new_indirect(page.doc(), img_xref, 0)
                w = mupdf.pdf_to_int( mupdf.pdf_dict_geta( ref, PDF_NAME('Width'), PDF_NAME('W')))
                h = mupdf.pdf_to_int( mupdf.pdf_dict_geta( ref, PDF_NAME('Height'), PDF_NAME('H')))
                #goto have_xref()
                do_have_imask = 0
                do_have_image = 0
            else:
                image = mupdf.fz_new_image_from_buffer(imgbuf)
                w = image.w()
                h = image.h()
                if not imask:
                    #goto have_image()
                    do_have_imask = 0

        if do_have_imask:
            # `fz_compressed_buffer` is reference counted and
            # `mupdf.fz_new_image_from_compressed_buffer2()`
            # is povided as a Swig-friendly wrapper for
            # `fz_new_image_from_compressed_buffer()`, so we can do things
            # straightfowardly.
            #
            cbuf1 = mupdf.fz_compressed_image_buffer( image)
            if not cbuf1.m_internal:
                raise ValueError( "uncompressed image cannot have mask")
            bpc = image.bpc()
            colorspace = image.colorspace()
            xres, yres = mupdf.fz_image_resolution(image)
            mask = mupdf.fz_new_image_from_buffer(maskbuf)
            image = mupdf.fz_new_image_from_compressed_buffer2(
                    w,
                    h,
                    bpc,
                    colorspace,
                    xres,
                    yres,
                    1,  # interpolate
                    0,  # imagemask,
                    list(), # decode
                    list(), # colorkey
                    cbuf1,
                    mask,
                    )
            
        if do_have_image:
            #log( 'do_have_image')
            ref = mupdf.pdf_add_image(pdf, image)
            if oc:
                JM_add_oc_object(pdf, ref, oc)
            img_xref = mupdf.pdf_to_num(ref)
            digests[md5_py] = img_xref
            rc_digest = 1

        if do_have_xref:
            #log( 'do_have_xref')
            resources = mupdf.pdf_dict_get_inheritable(page.obj(), PDF_NAME('Resources'))
            if not resources.m_internal:
                resources = mupdf.pdf_dict_put_dict(page.obj(), PDF_NAME('Resources'), 2)
            xobject = mupdf.pdf_dict_get(resources, PDF_NAME('XObject'))
            if not xobject.m_internal:
                xobject = mupdf.pdf_dict_put_dict(resources, PDF_NAME('XObject'), 2)
            mat = calc_image_matrix(w, h, clip, rotate, keep_proportion)
            mupdf.pdf_dict_puts(xobject, _imgname, ref)
            nres = mupdf.fz_new_buffer(50)
            s = f"\nq\n{_format_g((mat.a, mat.b, mat.c, mat.d, mat.e, mat.f))} cm\n/{_imgname} Do\nQ\n"
            #s = s.replace('\n', '\r\n')
            mupdf.fz_append_string(nres, s)
            JM_insert_contents(pdf, page.obj(), nres, overlay)

        if rc_digest:
            return img_xref, digests
        else:
            return img_xref, None

    def _insertFont(self, fontname, bfname, fontfile, fontbuffer, set_simple, idx, wmode, serif, encoding, ordering):
        page = self._pdf_page()
        pdf = page.doc()

        value = JM_insert_font(pdf, bfname, fontfile,fontbuffer, set_simple, idx, wmode, serif, encoding, ordering)
        # get the objects /Resources, /Resources/Font
        resources = mupdf.pdf_dict_get_inheritable( page.obj(), PDF_NAME('Resources'))
        fonts = mupdf.pdf_dict_get(resources, PDF_NAME('Font'))
        if not fonts.m_internal:    # page has no fonts yet
            fonts = mupdf.pdf_new_dict(pdf, 5)
            mupdf.pdf_dict_putl(page.obj(), fonts, PDF_NAME('Resources'), PDF_NAME('Font'))
        # store font in resources and fonts objects will contain named reference to font
        _, xref = JM_INT_ITEM(value, 0)
        if not xref:
            raise RuntimeError( "cannot insert font")
        font_obj = mupdf.pdf_new_indirect(pdf, xref, 0)
        mupdf.pdf_dict_puts(fonts, fontname, font_obj)
        return value

    def _load_annot(self, name, xref):
        page = self._pdf_page()
        if xref == 0:
            annot = JM_get_annot_by_name(page, name)
        else:
            annot = JM_get_annot_by_xref(page, xref)
        if annot.m_internal:
            return Annot(annot)

    def _makePixmap(self, doc, ctm, cs, alpha=0, annots=1, clip=None):
        pix = JM_pixmap_from_page(doc, self.this, ctm, cs, alpha, annots, clip)
        return Pixmap(pix)

    def _other_box(self, boxtype):
        rect = mupdf.FzRect( mupdf.FzRect.Fixed_INFINITE)
        page = _as_pdf_page(self.this, required=False)
        if page.m_internal:
            obj = mupdf.pdf_dict_gets( page.obj(), boxtype)
            if mupdf.pdf_is_array(obj):
                rect = mupdf.pdf_to_rect(obj)
        if mupdf.fz_is_infinite_rect( rect):
            return
        return JM_py_from_rect(rect)

    def _pdf_page(self, required=True):
        return _as_pdf_page(self.this, required=required)

    def _reset_annot_refs(self):
        """Invalidate / delete all annots of this page."""
        self._annot_refs.clear()

    def _set_opacity(self, gstate=None, CA=1, ca=1, blendmode=None):

        if CA >= 1 and ca >= 1 and blendmode is None:
            return
        tCA = int(round(max(CA , 0) * 100))
        if tCA >= 100:
            tCA = 99
        tca = int(round(max(ca, 0) * 100))
        if tca >= 100:
            tca = 99
        gstate = "fitzca%02i%02i" % (tCA, tca)

        if not gstate:
            return
        page = _as_pdf_page(self.this)
        resources = mupdf.pdf_dict_get(page.obj(), PDF_NAME('Resources'))
        if not resources.m_internal:
            resources = mupdf.pdf_dict_put_dict(page.obj(), PDF_NAME('Resources'), 2)
        extg = mupdf.pdf_dict_get(resources, PDF_NAME('ExtGState'))
        if not extg.m_internal:
            extg = mupdf.pdf_dict_put_dict(resources, PDF_NAME('ExtGState'), 2)
        n = mupdf.pdf_dict_len(extg)
        for i in range(n):
            o1 = mupdf.pdf_dict_get_key(extg, i)
            name = mupdf.pdf_to_name(o1)
            if name == gstate:
                return gstate
        opa = mupdf.pdf_new_dict(page.doc(), 3)
        mupdf.pdf_dict_put_real(opa, PDF_NAME('CA'), CA)
        mupdf.pdf_dict_put_real(opa, PDF_NAME('ca'), ca)
        mupdf.pdf_dict_puts(extg, gstate, opa)
        return gstate

    def _set_pagebox(self, boxtype, rect):
        doc = self.parent
        if doc is None:
            raise ValueError("orphaned object: parent is None")

        if not doc.is_pdf:
            raise ValueError("is no PDF")

        valid_boxes = ("CropBox", "BleedBox", "TrimBox", "ArtBox")

        if boxtype not in valid_boxes:
            raise ValueError("bad boxtype")

        rect = Rect(rect)
        mb = self.mediabox
        rect = Rect(rect[0], mb.y1 - rect[3], rect[2], mb.y1 - rect[1])
        if not (mb.x0 <= rect.x0 < rect.x1 <= mb.x1 and mb.y0 <= rect.y0 < rect.y1 <= mb.y1):
            raise ValueError(f"{boxtype} not in MediaBox")

        doc.xref_set_key(self.xref, boxtype, f"[{_format_g(tuple(rect))}]")

    def _set_resource_property(self, name, xref):
        page = self._pdf_page()
        JM_set_resource_property(page.obj(), name, xref)

    def _show_pdf_page(self, fz_srcpage, overlay=1, matrix=None, xref=0, oc=0, clip=None, graftmap=None, _imgname=None):
        cropbox = JM_rect_from_py(clip)
        mat = JM_matrix_from_py(matrix)
        rc_xref = xref
        tpage = _as_pdf_page(self.this)
        tpageref = tpage.obj()
        pdfout = tpage.doc()    # target PDF
        ENSURE_OPERATION(pdfout)
        #-------------------------------------------------------------
        # convert the source page to a Form XObject
        #-------------------------------------------------------------
        xobj1 = JM_xobject_from_page(pdfout, fz_srcpage, xref, graftmap.this)
        if not rc_xref:
            rc_xref = mupdf.pdf_to_num(xobj1)

        #-------------------------------------------------------------
        # create referencing XObject (controls display on target page)
        #-------------------------------------------------------------
        # fill reference to xobj1 into the /Resources
        #-------------------------------------------------------------
        subres1 = mupdf.pdf_new_dict(pdfout, 5)
        mupdf.pdf_dict_puts(subres1, "fullpage", xobj1)
        subres = mupdf.pdf_new_dict(pdfout, 5)
        mupdf.pdf_dict_put(subres, PDF_NAME('XObject'), subres1)

        res = mupdf.fz_new_buffer(20)
        mupdf.fz_append_string(res, "/fullpage Do")

        xobj2 = mupdf.pdf_new_xobject(pdfout, cropbox, mat, subres, res)
        if oc > 0:
            JM_add_oc_object(pdfout, mupdf.pdf_resolve_indirect(xobj2), oc)

        #-------------------------------------------------------------
        # update target page with xobj2:
        #-------------------------------------------------------------
        # 1. insert Xobject in Resources
        #-------------------------------------------------------------
        resources = mupdf.pdf_dict_get_inheritable(tpageref, PDF_NAME('Resources'))
        subres = mupdf.pdf_dict_get(resources, PDF_NAME('XObject'))
        if not subres.m_internal:
            subres = mupdf.pdf_dict_put_dict(resources, PDF_NAME('XObject'), 5)

        mupdf.pdf_dict_puts(subres, _imgname, xobj2)

        #-------------------------------------------------------------
        # 2. make and insert new Contents object
        #-------------------------------------------------------------
        nres = mupdf.fz_new_buffer(50) # buffer for Do-command
        mupdf.fz_append_string(nres, " q /")   # Do-command
        mupdf.fz_append_string(nres, _imgname)
        mupdf.fz_append_string(nres, " Do Q ")

        JM_insert_contents(pdfout, tpageref, nres, overlay)
        return rc_xref

    def add_caret_annot(self, point: point_like) -> Annot:
        """Add a 'Caret' annotation."""
        old_rotation = annot_preprocess(self)
        try:
            annot = self._add_caret_annot(point)
        finally:
            if old_rotation != 0:
                self.set_rotation(old_rotation)
        annot = Annot( annot)
        annot_postprocess(self, annot)
        assert hasattr( annot, 'parent')
        return annot

    def add_circle_annot(self, rect: rect_like) -> Annot:
        """Add a 'Circle' (ellipse, oval) annotation."""
        old_rotation = annot_preprocess(self)
        try:
            annot = self._add_square_or_circle(rect, mupdf.PDF_ANNOT_CIRCLE)
        finally:
            if old_rotation != 0:
                self.set_rotation(old_rotation)
        annot_postprocess(self, annot)
        return annot

    def add_file_annot(
            self,
            point: point_like,
            buffer_: typing.ByteString,
            filename: str,
            ufilename: OptStr =None,
            desc: OptStr =None,
            icon: OptStr =None
            ) -> Annot:
        """Add a 'FileAttachment' annotation."""
        old_rotation = annot_preprocess(self)
        try:
            annot = self._add_file_annot(point,
                    buffer_,
                    filename,
                    ufilename=ufilename,
                    desc=desc,
                    icon=icon,
                    )
        finally:
            if old_rotation != 0:
                self.set_rotation(old_rotation)
        annot_postprocess(self, annot)
        return annot

    def add_freetext_annot(
            self,
            rect: rect_like,
            text: str,
            fontsize: float =11,
            fontname: OptStr =None,
            border_color: OptSeq =None,
            text_color: OptSeq =None,
            fill_color: OptSeq =None,
            align: int =0,
            rotate: int =0
            ) -> Annot:
        """Add a 'FreeText' annotation."""

        old_rotation = annot_preprocess(self)
        try:
            annot = self._add_freetext_annot(
                    rect,
                    text,
                    fontsize=fontsize,
                    fontname=fontname,
                    border_color=border_color,
                    text_color=text_color,
                    fill_color=fill_color,
                    align=align,
                    rotate=rotate,
                    )
        finally:
            if old_rotation != 0:
                self.set_rotation(old_rotation)
        annot_postprocess(self, annot)
        return annot

    def add_highlight_annot(self, quads=None, start=None,
                          stop=None, clip=None) -> Annot:
        """Add a 'Highlight' annotation."""
        if quads is None:
            q = get_highlight_selection(self, start=start, stop=stop, clip=clip)
        else:
            q = CheckMarkerArg(quads)
        ret = self._add_text_marker(q, mupdf.PDF_ANNOT_HIGHLIGHT)
        return ret

    def add_ink_annot(self, handwriting: list) -> Annot:
        """Add a 'Ink' ('handwriting') annotation.

        The argument must be a list of lists of point_likes.
        """
        old_rotation = annot_preprocess(self)
        try:
            annot = self._add_ink_annot(handwriting)
        finally:
            if old_rotation != 0:
                self.set_rotation(old_rotation)
        annot_postprocess(self, annot)
        return annot

    def add_line_annot(self, p1: point_like, p2: point_like) -> Annot:
        """Add a 'Line' annotation."""
        old_rotation = annot_preprocess(self)
        try:
            annot = self._add_line_annot(p1, p2)
        finally:
            if old_rotation != 0:
                self.set_rotation(old_rotation)
        annot_postprocess(self, annot)
        return annot

    def add_polygon_annot(self, points: list) -> Annot:
        """Add a 'Polygon' annotation."""
        old_rotation = annot_preprocess(self)
        try:
            annot = self._add_multiline(points, mupdf.PDF_ANNOT_POLYGON)
        finally:
            if old_rotation != 0:
                self.set_rotation(old_rotation)
        annot_postprocess(self, annot)
        return annot

    def add_polyline_annot(self, points: list) -> Annot:
        """Add a 'PolyLine' annotation."""
        old_rotation = annot_preprocess(self)
        try:
            annot = self._add_multiline(points, mupdf.PDF_ANNOT_POLY_LINE)
        finally:
            if old_rotation != 0:
                self.set_rotation(old_rotation)
        annot_postprocess(self, annot)
        return annot

    def add_rect_annot(self, rect: rect_like) -> Annot:
        """Add a 'Square' (rectangle) annotation."""
        old_rotation = annot_preprocess(self)
        try:
            annot = self._add_square_or_circle(rect, mupdf.PDF_ANNOT_SQUARE)
        finally:
            if old_rotation != 0:
                self.set_rotation(old_rotation)
        annot_postprocess(self, annot)
        return annot

    def add_redact_annot(
            self,
            quad,
            text: OptStr =None,
            fontname: OptStr =None,
            fontsize: float =11,
            align: int =0,
            fill: OptSeq =None,
            text_color: OptSeq =None,
            cross_out: bool =True,
            ) -> Annot:
        """Add a 'Redact' annotation."""
        da_str = None
        if text and not set(string.whitespace).issuperset(text):
            CheckColor(fill)
            CheckColor(text_color)
            if not fontname:
                fontname = "Helv"
            if not fontsize:
                fontsize = 11
            if not text_color:
                text_color = (0, 0, 0)
            if hasattr(text_color, "__float__"):
                text_color = (text_color, text_color, text_color)
            if len(text_color) > 3:
                text_color = text_color[:3]
            fmt = "{:g} {:g} {:g} rg /{f:s} {s:g} Tf"
            da_str = fmt.format(*text_color, f=fontname, s=fontsize)
            if fill is None:
                fill = (1, 1, 1)
            if fill:
                if hasattr(fill, "__float__"):
                    fill = (fill, fill, fill)
                if len(fill) > 3:
                    fill = fill[:3]
        else:
            text = None

        old_rotation = annot_preprocess(self)
        try:
            annot = self._add_redact_annot(quad, text=text, da_str=da_str,
                       align=align, fill=fill)
        finally:
            if old_rotation != 0:
                self.set_rotation(old_rotation)
        annot_postprocess(self, annot)
        #-------------------------------------------------------------
        # change appearance to show a crossed-out rectangle
        #-------------------------------------------------------------
        if cross_out:
            ap_tab = annot._getAP().splitlines()[:-1]  # get the 4 commands only
            _, LL, LR, UR, UL = ap_tab
            ap_tab.append(LR)
            ap_tab.append(LL)
            ap_tab.append(UR)
            ap_tab.append(LL)
            ap_tab.append(UL)
            ap_tab.append(b"S")
            ap = b"\n".join(ap_tab)
            annot._setAP(ap, 0)
        return annot

    def add_squiggly_annot(
            self,
            quads=None,
            start=None,
            stop=None,
            clip=None,
            ) -> Annot:
        """Add a 'Squiggly' annotation."""
        if quads is None:
            q = get_highlight_selection(self, start=start, stop=stop, clip=clip)
        else:
            q = CheckMarkerArg(quads)
        return self._add_text_marker(q, mupdf.PDF_ANNOT_SQUIGGLY)

    def add_stamp_annot(self, rect: rect_like, stamp: int =0) -> Annot:
        """Add a ('rubber') 'Stamp' annotation."""
        old_rotation = annot_preprocess(self)
        try:
            annot = self._add_stamp_annot(rect, stamp)
        finally:
            if old_rotation != 0:
                self.set_rotation(old_rotation)
        annot_postprocess(self, annot)
        return annot

    def add_strikeout_annot(self, quads=None, start=None, stop=None, clip=None) -> Annot:
        """Add a 'StrikeOut' annotation."""
        if quads is None:
            q = get_highlight_selection(self, start=start, stop=stop, clip=clip)
        else:
            q = CheckMarkerArg(quads)
        return self._add_text_marker(q, mupdf.PDF_ANNOT_STRIKE_OUT)

    def add_text_annot(self, point: point_like, text: str, icon: str ="Note") -> Annot:
        """Add a 'Text' (sticky note) annotation."""
        old_rotation = annot_preprocess(self)
        try:
            annot = self._add_text_annot(point, text, icon=icon)
        finally:
            if old_rotation != 0:
                self.set_rotation(old_rotation)
        annot_postprocess(self, annot)
        return annot

    def add_underline_annot(self, quads=None, start=None, stop=None, clip=None) -> Annot:
        """Add a 'Underline' annotation."""
        if quads is None:
            q = get_highlight_selection(self, start=start, stop=stop, clip=clip)
        else:
            q = CheckMarkerArg(quads)
        return self._add_text_marker(q, mupdf.PDF_ANNOT_UNDERLINE)

    def add_widget(self, widget: Widget) -> Annot:
        """Add a 'Widget' (form field)."""
        CheckParent(self)
        doc = self.parent
        if not doc.is_pdf:
            raise ValueError("is no PDF")
        widget._validate()
        annot = self._addWidget(widget.field_type, widget.field_name)
        if not annot:
            return None
        annot.thisown = True
        annot.parent = weakref.proxy(self) # owning page object
        self._annot_refs[id(annot)] = annot
        widget.parent = annot.parent
        widget._annot = annot
        widget.update()
        return annot

    def annot_names(self):
        '''
        page get list of annot names
        '''
        """List of names of annotations, fields and links."""
        CheckParent(self)
        page = self._pdf_page(required=False)
        if not page.m_internal:
            return []
        return JM_get_annot_id_list(page)

    def annot_xrefs(self):
        '''
        List of xref numbers of annotations, fields and links.
        '''
        return JM_get_annot_xref_list2(self)
    
    def annots(self, types=None):
        """ Generator over the annotations of a page.

        Args:
            types: (list) annotation types to subselect from. If none,
                   all annotations are returned. E.g. types=[PDF_ANNOT_LINE]
                   will only yield line annotations.
        """
        skip_types = (mupdf.PDF_ANNOT_LINK, mupdf.PDF_ANNOT_POPUP, mupdf.PDF_ANNOT_WIDGET)
        if not hasattr(types, "__getitem__"):
            annot_xrefs = [a[0] for a in self.annot_xrefs() if a[1] not in skip_types]
        else:
            annot_xrefs = [a[0] for a in self.annot_xrefs() if a[1] in types and a[1] not in skip_types]
        for xref in annot_xrefs:
            annot = self.load_annot(xref)
            annot._yielded=True
            yield annot

    @property
    def artbox(self):
        """The ArtBox"""
        rect = self._other_box("ArtBox")
        if rect is None:
            return self.cropbox
        mb = self.mediabox
        return Rect(rect[0], mb.y1 - rect[3], rect[2], mb.y1 - rect[1])

    @property
    def bleedbox(self):
        """The BleedBox"""
        rect = self._other_box("BleedBox")
        if rect is None:
            return self.cropbox
        mb = self.mediabox
        return Rect(rect[0], mb.y1 - rect[3], rect[2], mb.y1 - rect[1])

    def bound(self):
        """Get page rectangle."""
        CheckParent(self)
        page = _as_fz_page(self.this)
        val = mupdf.fz_bound_page(page)
        val = Rect(val)
        
        if val.is_infinite and self.parent.is_pdf:
            cb = self.cropbox
            w, h = cb.width, cb.height
            if self.rotation not in (0, 180):
                w, h = h, w
            val = Rect(0, 0, w, h)
            msg = TOOLS.mupdf_warnings(reset=False).splitlines()[-1]
            message(msg)
        
        return val

    def clean_contents(self, sanitize=1):
        if not sanitize and not self.is_wrapped:
            self.wrap_contents()
        page = _as_pdf_page( self.this, required=False)
        if not page.m_internal:
            return
        filter_ = _make_PdfFilterOptions(recurse=1, sanitize=sanitize)
        mupdf.pdf_filter_page_contents( page.doc(), page, filter_)
    
    @property
    def cropbox(self):
        """The CropBox."""
        CheckParent(self)
        page = self._pdf_page(required=False)
        if not page.m_internal:
            val = mupdf.fz_bound_page(self.this)
        else:
            val = JM_cropbox(page.obj())
        val = Rect(val)

        return val

    @property
    def cropbox_position(self):
        return self.cropbox.tl

    def delete_annot(self, annot):
        """Delete annot and return next one."""
        CheckParent(self)
        CheckParent(annot)

        page = self._pdf_page()
        while 1:
            # first loop through all /IRT annots and remove them
            irt_annot = JM_find_annot_irt(annot.this)
            if not irt_annot:    # no more there
                break
            mupdf.pdf_delete_annot(page, irt_annot.this)
        nextannot = mupdf.pdf_next_annot(annot.this)   # store next
        mupdf.pdf_delete_annot(page, annot.this)
        val = Annot(nextannot)

        if val:
            val.thisown = True
            val.parent = weakref.proxy(self) # owning page object
            val.parent._annot_refs[id(val)] = val
        annot._erase()
        return val

    def delete_link(self, linkdict):
        """Delete a Link."""
        CheckParent(self)
        if not isinstance( linkdict, dict):
            return  # have no dictionary

        def finished():
            if linkdict["xref"] == 0: return
            try:
                linkid = linkdict["id"]
                linkobj = self._annot_refs[linkid]
                linkobj._erase()
            except Exception:
                # Don't print this exception, to match classic. Issue #2841.
                if g_exceptions_verbose > 1:    exception_info()
                pass

        page = _as_pdf_page(self.this, required=False)
        if not page.m_internal:
            return finished()   # have no PDF
        xref = linkdict[dictkey_xref]
        if xref < 1:
            return finished()   # invalid xref
        annots = mupdf.pdf_dict_get( page.obj(), PDF_NAME('Annots'))
        if not annots.m_internal:
            return finished()   # have no annotations
        len_ = mupdf.pdf_array_len( annots)
        if len_ == 0:
            return finished()
        oxref = 0
        for i in range( len_):
            oxref = mupdf.pdf_to_num( mupdf.pdf_array_get( annots, i))
            if xref == oxref:
                break   # found xref in annotations

        if xref != oxref:
            return finished()   # xref not in annotations
        mupdf.pdf_array_delete( annots, i) # delete entry in annotations
        mupdf.pdf_delete_object( page.doc(), xref) # delete link object
        mupdf.pdf_dict_put( page.obj(), PDF_NAME('Annots'), annots)
        JM_refresh_links( page)

        return finished()

    @property
    def derotation_matrix(self) -> Matrix:
        """Reflects page de-rotation."""
        if g_use_extra:
            return Matrix(extra.Page_derotate_matrix( self.this))
        pdfpage = self._pdf_page(required=False)
        if not pdfpage.m_internal:
            return Matrix(mupdf.FzRect(mupdf.FzRect.UNIT))
        return Matrix(JM_derotate_page_matrix(pdfpage))

    def extend_textpage(self, tpage, flags=0, matrix=None):
        page = self.this
        tp = tpage.this
        assert isinstance( tp, mupdf.FzStextPage)
        options = mupdf.FzStextOptions()
        options.flags = flags
        ctm = JM_matrix_from_py(matrix)
        dev = mupdf.FzDevice(tp, options)
        mupdf.fz_run_page( page, dev, ctm, mupdf.FzCookie())
        mupdf.fz_close_device( dev)

    @property
    def first_annot(self):
        """First annotation."""
        CheckParent(self)
        page = self._pdf_page(required=False)
        if not page.m_internal:
            return
        annot = mupdf.pdf_first_annot(page)
        if not annot.m_internal:
            return
        val = Annot(annot)
        val.thisown = True
        val.parent = weakref.proxy(self) # owning page object
        self._annot_refs[id(val)] = val
        return val

    @property
    def first_link(self):
        '''
        First link on page
        '''
        return self.load_links()

    @property
    def first_widget(self):
        """First widget/field."""
        CheckParent(self)
        annot = 0
        page = self._pdf_page(required=False)
        if not page.m_internal:
            return
        annot = mupdf.pdf_first_widget(page)
        if not annot.m_internal:
            return
        val = Annot(annot)
        val.thisown = True
        val.parent = weakref.proxy(self) # owning page object
        self._annot_refs[id(val)] = val
        widget = Widget()
        TOOLS._fill_widget(val, widget)
        val = widget
        return val

    def get_bboxlog(self, layers=None):
        CheckParent(self)
        old_rotation = self.rotation
        if old_rotation != 0:
            self.set_rotation(0)
        page = self.this
        rc = []
        inc_layers = True if layers else False
        dev = JM_new_bbox_device( rc, inc_layers)
        mupdf.fz_run_page( page, dev, mupdf.FzMatrix(), mupdf.FzCookie())
        mupdf.fz_close_device( dev)

        if old_rotation != 0:
            self.set_rotation(old_rotation)
        return rc

    def get_cdrawings(self, extended=None, callback=None, method=None):
        """Extract vector graphics ("line art") from the page."""
        CheckParent(self)
        old_rotation = self.rotation
        if old_rotation != 0:
            self.set_rotation(0)
        page = self.this
        if isinstance(page, mupdf.PdfPage):
            # Downcast pdf_page to fz_page.
            page = mupdf.FzPage(page)
        assert isinstance(page, mupdf.FzPage), f'{self.this=}'
        clips = True if extended else False
        prect = mupdf.fz_bound_page(page)
        if g_use_extra:
            rc = extra.get_cdrawings(page, extended, callback, method)
        else:
            rc = list()
            if callable(callback) or method is not None:
                dev = JM_new_lineart_device_Device(callback, clips, method)
            else:
                dev = JM_new_lineart_device_Device(rc, clips, method)
            dev.ptm = mupdf.FzMatrix(1, 0, 0, -1, 0, prect.y1)
            mupdf.fz_run_page(page, dev, mupdf.FzMatrix(), mupdf.FzCookie())
            mupdf.fz_close_device(dev)

        if old_rotation != 0:
            self.set_rotation(old_rotation)
        if callable(callback) or method is not None:
            return
        return rc

    def get_contents(self):
        """Get xrefs of /Contents objects."""
        CheckParent(self)
        ret = []
        page = _as_pdf_page(self.this)
        obj = page.obj()
        contents = mupdf.pdf_dict_get(obj, mupdf.PDF_ENUM_NAME_Contents)
        if mupdf.pdf_is_array(contents):
            n = mupdf.pdf_array_len(contents)
            for i in range(n):
                icont = mupdf.pdf_array_get(contents, i)
                xref = mupdf.pdf_to_num(icont)
                ret.append(xref)
        elif contents.m_internal:
            xref = mupdf.pdf_to_num(contents)
            ret.append( xref)
        return ret

    def get_displaylist(self, annots=1):
        '''
        Make a DisplayList from the page for Pixmap generation.

        Include (default) or exclude annotations.
        '''
        CheckParent(self)
        if annots:
            dl = mupdf.fz_new_display_list_from_page(self.this)
        else:
            dl = mupdf.fz_new_display_list_from_page_contents(self.this)
        return DisplayList(dl)

    def get_drawings(self, extended: bool=False) -> list:
        """Retrieve vector graphics. The extended version includes clips.

        Note:
        For greater comfort, this method converts point-likes, rect-likes, quad-likes
        of the C version to respective Point / Rect / Quad objects.
        It also adds default items that are missing in original path types.
        """
        allkeys = (
                'closePath',
                'fill',
                'color',
                'width',
                'lineCap',
                'lineJoin',
                'dashes',
                'stroke_opacity',
                'fill_opacity',
                'even_odd',
                )
        val = self.get_cdrawings(extended=extended)
        for i in range(len(val)):
            npath = val[i]
            if not npath["type"].startswith("clip"):
                npath["rect"] = Rect(npath["rect"])
            else:
                npath["scissor"] = Rect(npath["scissor"])
            if npath["type"]!="group":
                items = npath["items"]
                newitems = []
                for item in items:
                    cmd = item[0]
                    rest = item[1:]
                    if  cmd == "re":
                        item = ("re", Rect(rest[0]).normalize(), rest[1])
                    elif cmd == "qu":
                        item = ("qu", Quad(rest[0]))
                    else:
                        item = tuple([cmd] + [Point(i) for i in rest])
                    newitems.append(item)
                npath["items"] = newitems
            if npath['type'] in ('f', 's'):
                for k in allkeys:
                    npath[k] = npath.get(k)

            val[i] = npath
        return val

        class Drawpath(object):
            """Reflects a path dictionary from get_cdrawings()."""
            def __init__(self, **args):
                self.__dict__.update(args)
        
        class Drawpathlist(object):
            """List of Path objects representing get_cdrawings() output."""
            def __getitem__(self, item):
                return self.paths.__getitem__(item)

            def __init__(self):
                self.paths = []
                self.path_count = 0
                self.group_count = 0
                self.clip_count = 0
                self.fill_count = 0
                self.stroke_count = 0
                self.fillstroke_count = 0

            def __len__(self):
                return self.paths.__len__()

            def append(self, path):
                self.paths.append(path)
                self.path_count += 1
                if path.type == "clip":
                    self.clip_count += 1
                elif path.type == "group":
                    self.group_count += 1
                elif path.type == "f":
                    self.fill_count += 1
                elif path.type == "s":
                    self.stroke_count += 1
                elif path.type == "fs":
                    self.fillstroke_count += 1

            def clip_parents(self, i):
                """Return list of parent clip paths.

                Args:
                    i: (int) return parents of this path.
                Returns:
                    List of the clip parents."""
                if i >= self.path_count:
                    raise IndexError("bad path index")
                while i < 0:
                    i += self.path_count
                lvl = self.paths[i].level
                clips = list(  # clip paths before identified one
                    reversed(
                        [
                            p
                            for p in self.paths[:i]
                            if p.type == "clip" and p.level < lvl
                        ]
                    )
                )
                if clips == []:  # none found: empty list
                    return []
                nclips = [clips[0]]  # init return list
                for p in clips[1:]:
                    if p.level >= nclips[-1].level:
                        continue  # only accept smaller clip levels
                    nclips.append(p)
                return nclips

            def group_parents(self, i):
                """Return list of parent group paths.

                Args:
                    i: (int) return parents of this path.
                Returns:
                    List of the group parents."""
                if i >= self.path_count:
                    raise IndexError("bad path index")
                while i < 0:
                    i += self.path_count
                lvl = self.paths[i].level
                groups = list(  # group paths before identified one
                    reversed(
                        [
                            p
                            for p in self.paths[:i]
                            if p.type == "group" and p.level < lvl
                        ]
                    )
                )
                if groups == []:  # none found: empty list
                    return []
                ngroups = [groups[0]]  # init return list
                for p in groups[1:]:
                    if p.level >= ngroups[-1].level:
                        continue  # only accept smaller group levels
                    ngroups.append(p)
                return ngroups

        def get_lineart(self) -> object:
            """Get page drawings paths.

            Note:
            For greater comfort, this method converts point-like, rect-like, quad-like
            tuples of the C version to respective Point / Rect / Quad objects.
            Also adds default items that are missing in original path types.
            In contrast to get_drawings(), this output is an object.
            """

            val = self.get_cdrawings(extended=True)
            paths = self.Drawpathlist()
            for path in val:
                npath = self.Drawpath(**path)
                if npath.type != "clip":
                    npath.rect = Rect(path["rect"])
                else:
                    npath.scissor = Rect(path["scissor"])
                if npath.type != "group":
                    items = path["items"]
                    newitems = []
                    for item in items:
                        cmd = item[0]
                        rest = item[1:]
                        if  cmd == "re":
                            item = ("re", Rect(rest[0]).normalize(), rest[1])
                        elif cmd == "qu":
                            item = ("qu", Quad(rest[0]))
                        else:
                            item = tuple([cmd] + [Point(i) for i in rest])
                        newitems.append(item)
                    npath.items = newitems
                
                if npath.type == "f":
                    npath.stroke_opacity = None
                    npath.dashes = None
                    npath.line_join = None
                    npath.line_cap = None
                    npath.color = None
                    npath.width = None

                paths.append(npath)

            val = None
            return paths

    def remove_rotation(self):
        """Set page rotation to 0 while maintaining visual appearance."""
        rot = self.rotation  # normalized rotation value
        if rot == 0:
            return  Identity # nothing to do

        # need to derotate the page's content
        mb = self.mediabox  # current mediabox

        if rot == 90:
            # before derotation, shift content horizontally
            mat0 = Matrix(1, 0, 0, 1, mb.y1 - mb.x1 - mb.x0 - mb.y0, 0)
        elif rot == 270:
            # before derotation, shift content vertically
            mat0 = Matrix(1, 0, 0, 1, 0, mb.x1 - mb.y1 - mb.y0 - mb.x0)
        else:  # rot = 180
            mat0 = Matrix(1, 0, 0, 1, -2 * mb.x0, -2 * mb.y0)

        # prefix with derotation matrix
        mat = mat0 * self.derotation_matrix
        cmd = _format_g(tuple(mat)) + ' cm '
        cmd = cmd.encode('utf8')
        _ = TOOLS._insert_contents(self, cmd, False)  # prepend to page contents

        # swap x- and y-coordinates
        if rot in (90, 270):
            x0, y0, x1, y1 = mb
            mb.x0 = y0
            mb.y0 = x0
            mb.x1 = y1
            mb.y1 = x1
            self.set_mediabox(mb)

        self.set_rotation(0)
        rot = ~mat  # inverse of the derotation matrix

        for annot in self.annots():  # modify rectangles of annotations
            r = annot.rect * rot
            # TODO: only try to set rectangle for applicable annot types
            annot.set_rect(r)
        for link in self.get_links():  # modify 'from' rectangles of links
            r = link["from"] * rot
            self.delete_link(link)
            link["from"] = r
            try:  # invalid links remain deleted
                self.insert_link(link)
            except Exception:
                pass
        for widget in self.widgets():  # modify field rectangles
            r = widget.rect * rot
            widget.rect = r
            widget.update()
        return rot  # the inverse of the generated derotation matrix

    def cluster_drawings(
        self, clip=None, drawings=None, x_tolerance: float = 3, y_tolerance: float = 3
    ) -> list:
        """Join rectangles of neighboring vector graphic items.

        Args:
            clip: optional rect-like to restrict the page area to consider.
            drawings: (optional) output of a previous "get_drawings()".
            x_tolerance: horizontal neighborhood threshold.
            y_tolerance: vertical neighborhood threshold.

        Notes:
            Vector graphics (also called line-art or drawings) usually consist
            of independent items like rectangles, lines or curves to jointly
            form table grid lines or bar, line, pie charts and similar.
            This method identifies rectangles wrapping these disparate items.

        Returns:
            A list of Rect items, each wrapping line-art items that are close
            enough to be considered forming a common vector graphic.
            Only "significant" rectangles will be returned, i.e. having both,
            width and height larger than the tolerance values.
        """
        CheckParent(self)
        parea = self.rect  # the default clipping area
        if clip is not None:
            parea = Rect(clip)
        delta_x = x_tolerance  # shorter local name
        delta_y = y_tolerance  # shorter local name
        if drawings is None:  # if we cannot re-use a previous output
            drawings = self.get_drawings()

        def are_neighbors(r1, r2):
            """Detect whether r1, r2 are "neighbors".

            Items r1, r2 are called neighbors if the minimum distance between
            their points is less-equal delta.

            Both parameters must be (potentially invalid) rectangles.
            """
            # normalize rectangles as needed
            rr1_x0, rr1_x1 = (r1.x0, r1.x1) if r1.x1 > r1.x0 else (r1.x1, r1.x0)
            rr1_y0, rr1_y1 = (r1.y0, r1.y1) if r1.y1 > r1.y0 else (r1.y1, r1.y0)
            rr2_x0, rr2_x1 = (r2.x0, r2.x1) if r2.x1 > r2.x0 else (r2.x1, r2.x0)
            rr2_y0, rr2_y1 = (r2.y0, r2.y1) if r2.y1 > r2.y0 else (r2.y1, r2.y0)
            if (
                0
                or rr1_x1 < rr2_x0 - delta_x
                or rr1_x0 > rr2_x1 + delta_x
                or rr1_y1 < rr2_y0 - delta_y
                or rr1_y0 > rr2_y1 + delta_y
            ):
                # Rects do not overlap.
                return False
            else:
                # Rects overlap.
                return True

        # exclude graphics not contained in the clip
        paths = [
            p
            for p in drawings
            if 1
            and p["rect"].x0 >= parea.x0
            and p["rect"].x1 <= parea.x1
            and p["rect"].y0 >= parea.y0
            and p["rect"].y1 <= parea.y1
        ]

        # list of all vector graphic rectangles
        prects = sorted([p["rect"] for p in paths], key=lambda r: (r.y1, r.x0))

        new_rects = []  # the final list of the joined rectangles

        # -------------------------------------------------------------------------
        # The strategy is to identify and join all rects that are neighbors
        # -------------------------------------------------------------------------
        while prects:  # the algorithm will empty this list
            r = +prects[0]  # copy of first rectangle
            repeat = True
            while repeat:
                repeat = False
                for i in range(len(prects) - 1, 0, -1):  # from back to front
                    if are_neighbors(prects[i], r):
                        r |= prects[i].tl  # include in first rect
                        r |= prects[i].br  # include in first rect
                        del prects[i]  # delete this rect
                        repeat = True

            new_rects.append(r)
            del prects[0]
            prects = sorted(set(prects), key=lambda r: (r.y1, r.x0))

        new_rects = sorted(set(new_rects), key=lambda r: (r.y1, r.x0))
        return [r for r in new_rects if r.width > delta_x and r.height > delta_y]

    def get_fonts(self, full=False):
        """List of fonts defined in the page object."""
        CheckParent(self)
        return self.parent.get_page_fonts(self.number, full=full)

    def get_image_bbox(self, name, transform=0):
        """Get rectangle occupied by image 'name'.

        'name' is either an item of the image list, or the referencing
        name string - elem[7] of the resp. item.
        Option 'transform' also returns the image transformation matrix.
        """
        CheckParent(self)
        doc = self.parent
        if doc.is_closed or doc.is_encrypted:
            raise ValueError('document closed or encrypted')

        inf_rect = Rect(1, 1, -1, -1)
        null_mat = Matrix()
        if transform:
            rc = (inf_rect, null_mat)
        else:
            rc = inf_rect

        if type(name) in (list, tuple):
            if not type(name[-1]) is int:
                raise ValueError('need item of full page image list')
            item = name
        else:
            imglist = [i for i in doc.get_page_images(self.number, True) if name == i[7]]
            if len(imglist) == 1:
                item = imglist[0]
            elif imglist == []:
                raise ValueError('bad image name')
            else:
                raise ValueError("found multiple images named '%s'." % name)
        xref = item[-1]
        if xref != 0 or transform:
            try:
                return self.get_image_rects(item, transform=transform)[0]
            except Exception:
                exception_info()
                return inf_rect
        pdf_page = self._pdf_page()
        val = JM_image_reporter(pdf_page)

        if not bool(val):
            return rc

        for v in val:
            if v[0] != item[-3]:
                continue
            q = Quad(v[1])
            bbox = q.rect
            if transform == 0:
                rc = bbox
                break

            hm = Matrix(util_hor_matrix(q.ll, q.lr))
            h = abs(q.ll - q.ul)
            w = abs(q.ur - q.ul)
            m0 = Matrix(1 / w, 0, 0, 1 / h, 0, 0)
            m = ~(hm * m0)
            rc = (bbox, m)
            break
        val = rc

        return val

    def get_images(self, full=False):
        """List of images defined in the page object."""
        CheckParent(self)
        return self.parent.get_page_images(self.number, full=full)

    def get_oc_items(self) -> list:
        """Get OCGs and OCMDs used in the page's contents.

        Returns:
            List of items (name, xref, type), where type is one of "ocg" / "ocmd",
            and name is the property name.
        """
        rc = []
        for pname, xref in self._get_resource_properties():
            text = self.parent.xref_object(xref, compressed=True)
            if "/Type/OCG" in text:
                octype = "ocg"
            elif "/Type/OCMD" in text:
                octype = "ocmd"
            else:
                continue
            rc.append((pname, xref, octype))
        return rc

    def get_svg_image(self, matrix=None, text_as_path=1):
        """Make SVG image from page."""
        CheckParent(self)
        mediabox = mupdf.fz_bound_page(self.this)
        ctm = JM_matrix_from_py(matrix)
        tbounds = mediabox
        text_option = mupdf.FZ_SVG_TEXT_AS_PATH if text_as_path == 1 else mupdf.FZ_SVG_TEXT_AS_TEXT
        tbounds = mupdf.fz_transform_rect(tbounds, ctm)

        res = mupdf.fz_new_buffer(1024)
        out = mupdf.FzOutput(res)
        dev = mupdf.fz_new_svg_device(
                out,
                tbounds.x1-tbounds.x0,  # width
                tbounds.y1-tbounds.y0,  # height
                text_option,
                1,
                )
        mupdf.fz_run_page(self.this, dev, ctm, mupdf.FzCookie())
        mupdf.fz_close_device(dev)
        out.fz_close_output()
        text = JM_EscapeStrFromBuffer(res)
        return text

    def get_textbox(
            page: Page,
            rect: rect_like,
            textpage=None,  #: TextPage = None,
            ) -> str:
        tp = textpage
        if tp is None:
            tp = page.get_textpage()
        elif getattr(tp, "parent") != page:
            raise ValueError("not a textpage of this page")
        rc = tp.extractTextbox(rect)
        if textpage is None:
            del tp
        return rc

    def get_textpage(self, clip: rect_like = None, flags: int = 0, matrix=None) -> "TextPage":
        CheckParent(self)
        if matrix is None:
            matrix = Matrix(1, 1)
        old_rotation = self.rotation
        if old_rotation != 0:
            self.set_rotation(0)
        try:
            textpage = self._get_textpage(clip, flags=flags, matrix=matrix)
        finally:
            if old_rotation != 0:
                self.set_rotation(old_rotation)
        textpage = TextPage(textpage)
        textpage.parent = weakref.proxy(self)
        return textpage

    def get_texttrace(self):

        CheckParent(self)
        old_rotation = self.rotation
        if old_rotation != 0:
            self.set_rotation(0)
        page = self.this
        rc = []
        if g_use_extra:
            dev = extra.JM_new_texttrace_device(rc)
        else:
            dev = JM_new_texttrace_device(rc)
        prect = mupdf.fz_bound_page(page)
        dev.ptm = mupdf.FzMatrix(1, 0, 0, -1, 0, prect.y1)
        mupdf.fz_run_page(page, dev, mupdf.FzMatrix(), mupdf.FzCookie())
        mupdf.fz_close_device(dev)

        if old_rotation != 0:
            self.set_rotation(old_rotation)
        return rc

    def get_xobjects(self):
        """List of xobjects defined in the page object."""
        CheckParent(self)
        return self.parent.get_page_xobjects(self.number)

    def insert_font(self, fontname="helv", fontfile=None, fontbuffer=None,
                   set_simple=False, wmode=0, encoding=0):
        doc = self.parent
        if doc is None:
            raise ValueError("orphaned object: parent is None")
        idx = 0

        if fontname.startswith("/"):
            fontname = fontname[1:]
        inv_chars = INVALID_NAME_CHARS.intersection(fontname)
        if inv_chars != set():
            raise ValueError(f"bad fontname chars {inv_chars}")

        font = CheckFont(self, fontname)
        if font is not None:                    # font already in font list of page
            xref = font[0]                      # this is the xref
            if CheckFontInfo(doc, xref):        # also in our document font list?
                return xref                     # yes: we are done
            # need to build the doc FontInfo entry - done via get_char_widths
            doc.get_char_widths(xref)
            return xref

        #--------------------------------------------------------------------------
        # the font is not present for this page
        #--------------------------------------------------------------------------

        bfname = Base14_fontdict.get(fontname.lower(), None) # BaseFont if Base-14 font

        serif = 0
        CJK_number = -1
        CJK_list_n = ["china-t", "china-s", "japan", "korea"]
        CJK_list_s = ["china-ts", "china-ss", "japan-s", "korea-s"]

        try:
            CJK_number = CJK_list_n.index(fontname)
            serif = 0
        except Exception:
            # Verbose in PyMuPDF/tests.
            if g_exceptions_verbose > 1:    exception_info()
            pass

        if CJK_number < 0:
            try:
                CJK_number = CJK_list_s.index(fontname)
                serif = 1
            except Exception:
                # Verbose in PyMuPDF/tests.
                if g_exceptions_verbose > 1:    exception_info()
                pass

        if fontname.lower() in fitz_fontdescriptors.keys():
            import pymupdf_fonts
            fontbuffer = pymupdf_fonts.myfont(fontname)  # make a copy
            del pymupdf_fonts

        # install the font for the page
        if fontfile is not None:
            if type(fontfile) is str:
                fontfile_str = fontfile
            elif hasattr(fontfile, "absolute"):
                fontfile_str = str(fontfile)
            elif hasattr(fontfile, "name"):
                fontfile_str = fontfile.name
            else:
                raise ValueError("bad fontfile")
        else:
            fontfile_str = None
        val = self._insertFont(fontname, bfname, fontfile_str, fontbuffer, set_simple, idx,
                               wmode, serif, encoding, CJK_number)

        if not val:                   # did not work, error return
            return val

        xref = val[0]                 # xref of installed font
        fontdict = val[1]

        if CheckFontInfo(doc, xref):  # check again: document already has this font
            return xref               # we are done

        # need to create document font info
        doc.get_char_widths(xref, fontdict=fontdict)
        return xref

    @property
    def is_wrapped(self):
        """Check if /Contents is in a balanced graphics state."""
        return self._count_q_balance() == (0, 0)

    @property
    def language(self):
        """Page language."""
        pdfpage = _as_pdf_page(self.this, required=False)
        if not pdfpage.m_internal:
            return
        lang = mupdf.pdf_dict_get_inheritable(pdfpage.obj(), PDF_NAME('Lang'))
        if not lang.m_internal:
            return
        return mupdf.pdf_to_str_buf(lang)

    def links(self, kinds=None):
        """ Generator over the links of a page.

        Args:
            kinds: (list) link kinds to subselect from. If none,
                   all links are returned. E.g. kinds=[LINK_URI]
                   will only yield URI links.
        """
        all_links = self.get_links()
        for link in all_links:
            if kinds is None or link["kind"] in kinds:
                yield (link)

    def load_annot(self, ident: typing.Union[str, int]) -> Annot:
        """Load an annot by name (/NM key) or xref.

        Args:
            ident: identifier, either name (str) or xref (int).
        """
        CheckParent(self)
        if type(ident) is str:
            xref = 0
            name = ident
        elif type(ident) is int:
            xref = ident
            name = None
        else:
            raise ValueError("identifier must be a string or integer")
        val = self._load_annot(name, xref)
        if not val:
            return val
        val.thisown = True
        val.parent = weakref.proxy(self)
        self._annot_refs[id(val)] = val
        return val

    def load_links(self):
        """Get first Link."""
        CheckParent(self)
        val = mupdf.fz_load_links( self.this)
        if not val.m_internal:
            return
        val = Link( val)
        val.thisown = True
        val.parent = weakref.proxy(self) # owning page object
        self._annot_refs[id(val)] = val
        val.xref = 0
        val.id = ""
        if self.parent.is_pdf:
            xrefs = self.annot_xrefs()
            xrefs = [x for x in xrefs if x[1] == mupdf.PDF_ANNOT_LINK]
            if xrefs:
                link_id = xrefs[0]
                val.xref = link_id[0]
                val.id = link_id[2]
        else:
            val.xref = 0
            val.id = ""
        return val

    #----------------------------------------------------------------
    # page load widget by xref
    #----------------------------------------------------------------
    def load_widget( self, xref):
        """Load a widget by its xref."""
        CheckParent(self)

        page = _as_pdf_page(self.this)
        annot = JM_get_widget_by_xref( page, xref)
        #log( '{=type(annot)}')
        val = annot
        if not val:
            return val
        val.thisown = True
        val.parent = weakref.proxy(self)
        self._annot_refs[id(val)] = val
        widget = Widget()
        TOOLS._fill_widget(val, widget)
        val = widget
        return val

    @property
    def mediabox(self):
        """The MediaBox."""
        CheckParent(self)
        page = self._pdf_page(required=False)
        if not page.m_internal:
            rect = mupdf.fz_bound_page( self.this)
        else:
            rect = JM_mediabox( page.obj())
        return Rect(rect)

    @property
    def mediabox_size(self):
        return Point(self.mediabox.x1, self.mediabox.y1)

    #@property
    #def parent( self):
    #    assert self._parent
    #    if self._parent:
    #        return self._parent
    #    return Document( self.this.document())

    def read_contents(self):
        """All /Contents streams concatenated to one bytes object."""
        return TOOLS._get_all_contents(self)

    def refresh(self):
        """Refresh page after link/annot/widget updates."""
        CheckParent(self)
        doc = self.parent
        page = doc.reload_page(self)
        # fixme this looks wrong.
        self.this = page

    @property
    def rotation(self):
        """Page rotation."""
        CheckParent(self)
        page = _as_pdf_page(self.this, required=0)
        if not page.m_internal:
            return 0
        return JM_page_rotation(page)

    @property
    def rotation_matrix(self) -> Matrix:
        """Reflects page rotation."""
        return Matrix(TOOLS._rotate_matrix(self))

    def run(self, dw, m):
        """Run page through a device.
        dw: DeviceWrapper
        """
        CheckParent(self)
        mupdf.fz_run_page(self.this, dw.device, JM_matrix_from_py(m), mupdf.FzCookie())

    def set_artbox(self, rect):
        """Set the ArtBox."""
        return self._set_pagebox("ArtBox", rect)

    def set_bleedbox(self, rect):
        """Set the BleedBox."""
        return self._set_pagebox("BleedBox", rect)

    def set_contents(self, xref):
        """Set object at 'xref' as the page's /Contents."""
        CheckParent(self)
        doc = self.parent
        if doc.is_closed:
            raise ValueError("document closed")
        if not doc.is_pdf:
            raise ValueError("is no PDF")
        if xref not in range(1, doc.xref_length()):
            raise ValueError("bad xref")
        if not doc.xref_is_stream(xref):
            raise ValueError("xref is no stream")
        doc.xref_set_key(self.xref, "Contents", "%i 0 R" % xref)

    def set_cropbox(self, rect):
        """Set the CropBox. Will also change Page.rect."""
        return self._set_pagebox("CropBox", rect)

    def set_language(self, language=None):
        """Set PDF page default language."""
        CheckParent(self)
        pdfpage = _as_pdf_page(self.this)
        if not language:
            mupdf.pdf_dict_del(pdfpage.obj(), PDF_NAME('Lang'))
        else:
            lang = mupdf.fz_text_language_from_string(language)
            assert hasattr(mupdf, 'fz_string_from_text_language2')
            mupdf.pdf_dict_put_text_string(
                    pdfpage.obj,
                    PDF_NAME('Lang'),
                    mupdf.fz_string_from_text_language2(lang)
                    )

    def set_mediabox(self, rect):
        """Set the MediaBox."""
        CheckParent(self)
        page = self._pdf_page()
        mediabox = JM_rect_from_py(rect)
        if (mupdf.fz_is_empty_rect(mediabox)
                or mupdf.fz_is_infinite_rect(mediabox)
                ):
            raise ValueError( MSG_BAD_RECT)
        mupdf.pdf_dict_put_rect( page.obj(), PDF_NAME('MediaBox'), mediabox)
        mupdf.pdf_dict_del( page.obj(), PDF_NAME('CropBox'))
        mupdf.pdf_dict_del( page.obj(), PDF_NAME('ArtBox'))
        mupdf.pdf_dict_del( page.obj(), PDF_NAME('BleedBox'))
        mupdf.pdf_dict_del( page.obj(), PDF_NAME('TrimBox'))

    def set_rotation(self, rotation):
        """Set page rotation."""
        CheckParent(self)
        page = _as_pdf_page(self.this)
        rot = JM_norm_rotation(rotation)
        mupdf.pdf_dict_put_int( page.obj(), PDF_NAME('Rotate'), rot)

    def set_trimbox(self, rect):
        """Set the TrimBox."""
        return self._set_pagebox("TrimBox", rect)

    @property
    def transformation_matrix(self):
        """Page transformation matrix."""
        CheckParent(self)

        ctm = mupdf.FzMatrix()
        page = self._pdf_page(required=False)
        if not page.m_internal:
            return JM_py_from_matrix(ctm)
        mediabox = mupdf.FzRect(mupdf.FzRect.Fixed_UNIT)    # fixme: original code passed mediabox=NULL.
        mupdf.pdf_page_transform(page, mediabox, ctm)
        val = JM_py_from_matrix(ctm)

        if self.rotation % 360 == 0:
            val = Matrix(val)
        else:
            val = Matrix(1, 0, 0, -1, 0, self.cropbox.height)
        return val

    @property
    def trimbox(self):
        """The TrimBox"""
        rect = self._other_box("TrimBox")
        if rect is None:
            return self.cropbox
        mb = self.mediabox
        return Rect(rect[0], mb.y1 - rect[3], rect[2], mb.y1 - rect[1])

    def widgets(self, types=None):
        """ Generator over the widgets of a page.

        Args:
            types: (list) field types to subselect from. If none,
                    all fields are returned. E.g. types=[PDF_WIDGET_TYPE_TEXT]
                    will only yield text fields.
        """
        #for a in self.annot_xrefs():
        #    log( '{a=}')
        widget_xrefs = [a[0] for a in self.annot_xrefs() if a[1] == mupdf.PDF_ANNOT_WIDGET]
        #log(f'widgets(): {widget_xrefs=}')
        for xref in widget_xrefs:
            widget = self.load_widget(xref)
            if types is None or widget.field_type in types:
                yield (widget)

    def wrap_contents(self):
        """Ensure page is in a balanced graphics state."""
        push, pop = self._count_q_balance()  # count missing "q"/"Q" commands
        if push > 0:  # prepend required push commands
            prepend = b"q\n" * push
            TOOLS._insert_contents(self, prepend, False)
        if pop > 0:  # append required pop commands
            append = b"\nQ" * pop + b"\n"
            TOOLS._insert_contents(self, append, True)

    @property
    def xref(self):
        """PDF xref number of page."""
        CheckParent(self)
        return self.parent.page_xref(self.number)

    rect = property(bound, doc="page rectangle")


class Pixmap:

    def __init__(self, *args):
        """
        Pixmap(colorspace, irect, alpha) - empty pixmap.
        Pixmap(colorspace, src) - copy changing colorspace.
        Pixmap(src, width, height,[clip]) - scaled copy, float dimensions.
        Pixmap(src, alpha=1) - copy and add or drop alpha channel.
        Pixmap(filename) - from an image in a file.
        Pixmap(image) - from an image in memory (bytes).
        Pixmap(colorspace, width, height, samples, alpha) - from samples data.
        Pixmap(PDFdoc, xref) - from an image at xref in a PDF document.
        """
        # Cache for property `self.samples_mv`. Set here so __del_() sees it if
        # we raise.
        #
        self._samples_mv = None

        # 2024-01-16: Experimental support for a memory-view of the underlying
        # data.  Doesn't seem to make much difference to Pixmap.set_pixel() so
        # not currently used.
        self._memory_view = None
        
        if 0:
            pass

        elif args_match(args,
                (Colorspace, mupdf.FzColorspace),
                (mupdf.FzRect, mupdf.FzIrect, IRect, Rect, tuple)
                ):
            # create empty pixmap with colorspace and IRect
            cs, rect = args
            alpha = 0
            pm = mupdf.fz_new_pixmap_with_bbox(cs, JM_irect_from_py(rect), mupdf.FzSeparations(0), alpha)
            self.this = pm

        elif args_match(args,
                (Colorspace, mupdf.FzColorspace),
                (mupdf.FzRect, mupdf.FzIrect, IRect, Rect, tuple),
                (int, bool)
                ):
            # create empty pixmap with colorspace and IRect
            cs, rect, alpha = args
            pm = mupdf.fz_new_pixmap_with_bbox(cs, JM_irect_from_py(rect), mupdf.FzSeparations(0), alpha)
            self.this = pm

        elif args_match(args, (Colorspace, mupdf.FzColorspace, type(None)), (Pixmap, mupdf.FzPixmap)):
            # copy pixmap, converting colorspace
            cs, spix = args
            if isinstance(cs, Colorspace):
                cs = cs.this
            elif cs is None:
                cs = mupdf.FzColorspace(None)
            if isinstance(spix, Pixmap):
                spix = spix.this
            if not mupdf.fz_pixmap_colorspace(spix).m_internal:
                raise ValueError( "source colorspace must not be None")
            
            if cs.m_internal:
                self.this = mupdf.fz_convert_pixmap(
                        spix,
                        cs,
                        mupdf.FzColorspace(),
                        mupdf.FzDefaultColorspaces(None),
                        mupdf.FzColorParams(),
                        1
                        )
            else:
                self.this = mupdf.fz_new_pixmap_from_alpha_channel( spix)
                if not self.this.m_internal:
                    raise RuntimeError( MSG_PIX_NOALPHA)

        elif args_match(args, (Pixmap, mupdf.FzPixmap), (Pixmap, mupdf.FzPixmap)):
            # add mask to a pixmap w/o alpha channel
            spix, mpix = args
            if isinstance(spix, Pixmap):
                spix = spix.this
            if isinstance(mpix, Pixmap):
                mpix = mpix.this
            spm = spix
            mpm = mpix
            if not spix.m_internal: # intercept NULL for spix: make alpha only pix
                dst = mupdf.fz_new_pixmap_from_alpha_channel(mpm)
                if not dst.m_internal:
                    raise RuntimeError( MSG_PIX_NOALPHA)
            else:
                dst = mupdf.fz_new_pixmap_from_color_and_mask(spm, mpm)
            self.this = dst

        elif (args_match(args, (Pixmap, mupdf.FzPixmap), (float, int), (float, int), None) or
             args_match(args, (Pixmap, mupdf.FzPixmap), (float, int), (float, int))):
            # create pixmap as scaled copy of another one
            if len(args) == 3:
                spix, w, h = args
                bbox = mupdf.FzIrect(mupdf.fz_infinite_irect)
            else:
                spix, w, h, clip = args
                bbox = JM_irect_from_py(clip)
        
            spix, w, h, clip = args
            src_pix = spix.this if isinstance(spix, Pixmap) else spix
            bbox = JM_irect_from_py(clip)
            if not mupdf.fz_is_infinite_irect(bbox):
                pm = mupdf.fz_scale_pixmap(src_pix, src_pix.x(), src_pix.y(), w, h, bbox)
            else:
                pm = mupdf.fz_scale_pixmap(src_pix, src_pix.x(), src_pix.y(), w, h, mupdf.FzIrect(mupdf.fz_infinite_irect))
            self.this = pm

        elif args_match(args, str, (Pixmap, mupdf.FzPixmap)) and args[0] == 'raw':
            # Special raw construction where we set .this directly.
            _, pm = args
            if isinstance(pm, Pixmap):
                pm = pm.this
            self.this = pm

        elif args_match(args, (Pixmap, mupdf.FzPixmap), (int, None)):
            # Pixmap(struct Pixmap *spix, int alpha=1)
            # copy pixmap & add / drop the alpha channel
            spix = args[0]
            alpha = args[1] if len(args) == 2 else 1
            src_pix = spix.this if isinstance(spix, Pixmap) else spix
            if not _INRANGE(alpha, 0, 1):
                raise ValueError( "bad alpha value")
            cs = mupdf.fz_pixmap_colorspace(src_pix)
            if not cs.m_internal and not alpha:
                raise ValueError( "cannot drop alpha for 'NULL' colorspace")
            seps = mupdf.FzSeparations()
            n = mupdf.fz_pixmap_colorants(src_pix)
            w = mupdf.fz_pixmap_width(src_pix)
            h = mupdf.fz_pixmap_height(src_pix)
            pm = mupdf.fz_new_pixmap(cs, w, h, seps, alpha)
            pm.m_internal.x = src_pix.m_internal.x
            pm.m_internal.y = src_pix.m_internal.y
            pm.m_internal.xres = src_pix.m_internal.xres
            pm.m_internal.yres = src_pix.m_internal.yres

            # copy samples data ------------------------------------------
            if 1:
                # We use specially-provided (by MuPDF Python bindings)
                # ll_fz_pixmap_copy() to get best performance.
                # test_pixmap.py:test_setalpha(): 3.9s t=0.0062
                mupdf.ll_fz_pixmap_copy( pm.m_internal, src_pix.m_internal, n)
            elif 1:
                # Use memoryview.
                # test_pixmap.py:test_setalpha(): 4.6 t=0.51
                src_view = mupdf.fz_pixmap_samples_memoryview( src_pix)
                pm_view = mupdf.fz_pixmap_samples_memoryview( pm)
                if src_pix.alpha() == pm.alpha():   # identical samples
                    #memcpy(tptr, sptr, w * h * (n + alpha));
                    size = w * h * (n + alpha)
                    pm_view[ 0 : size] = src_view[ 0 : size]
                else:
                    tptr = 0
                    sptr = 0
                    # This is a little faster than calling
                    # pm.fz_samples_set(), but still quite slow. E.g. reduces
                    # test_pixmap.py:test_setalpha() from 6.7s to 4.5s.
                    #
                    # t=0.53
                    pm_stride = pm.stride()
                    pm_n = pm.n()
                    pm_alpha = pm.alpha()
                    src_stride = src_pix.stride()
                    src_n = src_pix.n()
                    #log( '{=pm_stride pm_n src_stride src_n}')
                    for y in range( h):
                        for x in range( w):
                            pm_i = pm_stride * y + pm_n * x
                            src_i = src_stride * y + src_n * x
                            pm_view[ pm_i : pm_i + n] = src_view[ src_i : src_i + n]
                            if pm_alpha:
                                pm_view[ pm_i + n] = 255
            else:
                # Copy individual bytes from Python. Very slow.
                # test_pixmap.py:test_setalpha(): 6.89 t=2.601
                if src_pix.alpha() == pm.alpha():   # identical samples
                    #memcpy(tptr, sptr, w * h * (n + alpha));
                    for i in range(w * h * (n + alpha)):
                        mupdf.fz_samples_set(pm, i, mupdf.fz_samples_get(src_pix, i))
                else:
                    # t=2.56
                    tptr = 0
                    sptr = 0
                    src_pix_alpha = src_pix.alpha()
                    for i in range(w * h):
                        #memcpy(tptr, sptr, n);
                        for j in range(n):
                            mupdf.fz_samples_set(pm, tptr + j, mupdf.fz_samples_get(src_pix, sptr + j))
                        tptr += n
                        if pm.alpha():
                            mupdf.fz_samples_set(pm, tptr, 255)
                            tptr += 1
                        sptr += n + src_pix_alpha
            self.this = pm

        elif args_match(args, (mupdf.FzColorspace, Colorspace), int, int, None, (int, bool)):
            # create pixmap from samples data
            cs, w, h, samples, alpha = args
            if isinstance(cs, Colorspace):
                cs = cs.this
                assert isinstance(cs, mupdf.FzColorspace)
            n = mupdf.fz_colorspace_n(cs)
            stride = (n + alpha) * w
            seps = mupdf.FzSeparations()
            pm = mupdf.fz_new_pixmap(cs, w, h, seps, alpha)

            if isinstance( samples, (bytes, bytearray)):
                #log('using mupdf.python_buffer_data()')
                samples2 = mupdf.python_buffer_data(samples)
                size = len(samples)
            else:
                res = JM_BufferFromBytes(samples)
                if not res.m_internal:
                    raise ValueError( "bad samples data")
                size, c = mupdf.fz_buffer_storage(res)
                samples2 = mupdf.python_buffer_data(samples) # raw swig proxy for `const unsigned char*`.
            if stride * h != size:
                raise ValueError( f"bad samples length {w=} {h=} {alpha=} {n=} {stride=} {size=}")
            mupdf.ll_fz_pixmap_copy_raw( pm.m_internal, samples2)
            self.this = pm

        elif args_match(args, None):
            # create pixmap from filename, file object, pathlib.Path or memory
            imagedata, = args
            name = 'name'
            if hasattr(imagedata, "resolve"):
                fname = imagedata.__str__()
                if fname:
                    img = mupdf.fz_new_image_from_file(fname)
            elif hasattr(imagedata, name):
                fname = imagedata.name
                if fname:
                    img = mupdf.fz_new_image_from_file(fname)
            elif isinstance(imagedata, str):
                img = mupdf.fz_new_image_from_file(imagedata)
            else:
                res = JM_BufferFromBytes(imagedata)
                if not res.m_internal or not res.m_internal.len:
                    raise ValueError( "bad image data")
                img = mupdf.fz_new_image_from_buffer(res)

            # Original code passed null for subarea and ctm, but that's not
            # possible with MuPDF's python bindings. The equivalent is an
            # infinite rect and identify matrix scaled by img.w() and img.h().
            pm, w, h = mupdf.fz_get_pixmap_from_image(
                    img,
                    mupdf.FzIrect(FZ_MIN_INF_RECT, FZ_MIN_INF_RECT, FZ_MAX_INF_RECT, FZ_MAX_INF_RECT),
                    mupdf.FzMatrix( img.w(), 0, 0, img.h(), 0, 0),
                    )
            xres, yres = mupdf.fz_image_resolution(img)
            pm.m_internal.xres = xres
            pm.m_internal.yres = yres
            self.this = pm

        elif args_match(args, (Document, mupdf.FzDocument), int):
            # Create pixmap from PDF image identified by XREF number
            doc, xref = args
            pdf = _as_pdf_document(doc)
            xreflen = mupdf.pdf_xref_len(pdf)
            if not _INRANGE(xref, 1, xreflen-1):
                raise ValueError( MSG_BAD_XREF)
            ref = mupdf.pdf_new_indirect(pdf, xref, 0)
            type_ = mupdf.pdf_dict_get(ref, PDF_NAME('Subtype'))
            if (not mupdf.pdf_name_eq(type_, PDF_NAME('Image'))
                    and not mupdf.pdf_name_eq(type_, PDF_NAME('Alpha'))
                    and not mupdf.pdf_name_eq(type_, PDF_NAME('Luminosity'))
                    ):
                raise ValueError( MSG_IS_NO_IMAGE)
            img = mupdf.pdf_load_image(pdf, ref)
            # Original code passed null for subarea and ctm, but that's not
            # possible with MuPDF's python bindings. The equivalent is an
            # infinite rect and identify matrix scaled by img.w() and img.h().
            pix, w, h = mupdf.fz_get_pixmap_from_image(
                    img,
                    mupdf.FzIrect(FZ_MIN_INF_RECT, FZ_MIN_INF_RECT, FZ_MAX_INF_RECT, FZ_MAX_INF_RECT),
                    mupdf.FzMatrix(img.w(), 0, 0, img.h(), 0, 0),
                    )
            self.this = pix

        else:
            text = 'Unrecognised args for constructing Pixmap:\n'
            for arg in args:
                text += f'    {type(arg)}: {arg}\n'
            raise Exception( text)

    def __len__(self):
        return self.size

    def __repr__(self):
        if not type(self) is Pixmap: return
        if self.colorspace:
            return "Pixmap(%s, %s, %s)" % (self.colorspace.this.m_internal.name, self.irect, self.alpha)
        else:
            return "Pixmap(%s, %s, %s)" % ('None', self.irect, self.alpha)

    def _tobytes(self, format_, jpg_quality):
        '''
        Pixmap._tobytes
        '''
        pm = self.this
        size = mupdf.fz_pixmap_stride(pm) * pm.h()
        res = mupdf.fz_new_buffer(size)
        out = mupdf.FzOutput(res)
        if   format_ == 1:  mupdf.fz_write_pixmap_as_png(out, pm)
        elif format_ == 2:  mupdf.fz_write_pixmap_as_pnm(out, pm)
        elif format_ == 3:  mupdf.fz_write_pixmap_as_pam(out, pm)
        elif format_ == 5:  mupdf.fz_write_pixmap_as_psd(out, pm)
        elif format_ == 6:  mupdf.fz_write_pixmap_as_ps(out, pm)
        elif format_ == 7:
            mupdf.fz_write_pixmap_as_jpeg(out, pm, jpg_quality, 0)
        else:
            mupdf.fz_write_pixmap_as_png(out, pm)
        out.fz_close_output()
        barray = JM_BinFromBuffer(res)
        return barray

    def _writeIMG(self, filename, format_, jpg_quality):
        pm = self.this
        if   format_ == 1:  mupdf.fz_save_pixmap_as_png(pm, filename)
        elif format_ == 2:  mupdf.fz_save_pixmap_as_pnm(pm, filename)
        elif format_ == 3:  mupdf.fz_save_pixmap_as_pam(pm, filename)
        elif format_ == 5:  mupdf.fz_save_pixmap_as_psd(pm, filename)
        elif format_ == 6:  mupdf.fz_save_pixmap_as_ps(pm, filename)
        elif format_ == 7:  mupdf.fz_save_pixmap_as_jpeg(pm, filename, jpg_quality)
        else:               mupdf.fz_save_pixmap_as_png(pm, filename)

    @property
    def alpha(self):
        """Indicates presence of alpha channel."""
        return mupdf.fz_pixmap_alpha(self.this)

    def clear_with(self, value=None, bbox=None):
        """Fill all color components with same value."""
        if value is None:
            mupdf.fz_clear_pixmap(self.this)
        elif bbox is None:
            mupdf.fz_clear_pixmap_with_value(self.this, value)
        else:
            JM_clear_pixmap_rect_with_value(self.this, value, JM_irect_from_py(bbox))

    def color_count(self, colors=0, clip=None):
        '''
        Return count of each color.
        '''
        pm = self.this
        rc = JM_color_count( pm, clip)
        if not colors:
            return len( rc)
        return rc

    def color_topusage(self, clip=None):
        """Return most frequent color and its usage ratio."""
        allpixels = 0
        cnt = 0
        if clip is not None and self.irect in Rect(clip):
            clip = self.irect
        for pixel, count in self.color_count(colors=True,clip=clip).items():
            allpixels += count
            if count > cnt:
                cnt = count
                maxpixel = pixel
        if not allpixels:
            return (1, bytes([255] * self.n))
        return (cnt / allpixels, maxpixel)

    @property
    def colorspace(self):
        """Pixmap Colorspace."""
        cs = Colorspace(mupdf.fz_pixmap_colorspace(self.this))
        if cs.name == "None":
            return None
        return cs

    def copy(self, src, bbox):
        """Copy bbox from another Pixmap."""
        pm = self.this
        src_pix = src.this
        if not mupdf.fz_pixmap_colorspace(src_pix):
            raise ValueError( "cannot copy pixmap with NULL colorspace")
        if pm.alpha() != src_pix.alpha():
            raise ValueError( "source and target alpha must be equal")
        mupdf.fz_copy_pixmap_rect(pm, src_pix, JM_irect_from_py(bbox), mupdf.FzDefaultColorspaces(None))

    @property
    def digest(self):
        """MD5 digest of pixmap (bytes)."""
        ret = mupdf.fz_md5_pixmap2(self.this)
        return bytes(ret)

    def gamma_with(self, gamma):
        """Apply correction with some float.
        gamma=1 is a no-op."""
        if not mupdf.fz_pixmap_colorspace( self.this):
            message_warning("colorspace invalid for function")
            return
        mupdf.fz_gamma_pixmap( self.this, gamma)

    @property
    def h(self):
        """The height."""
        return mupdf.fz_pixmap_height(self.this)

    def invert_irect(self, bbox=None):
        """Invert the colors inside a bbox."""
        pm = self.this
        if not mupdf.fz_pixmap_colorspace(pm).m_internal:
            message_warning("ignored for stencil pixmap")
            return False
        r = JM_irect_from_py(bbox)
        if mupdf.fz_is_infinite_irect(r):
            mupdf.fz_invert_pixmap(pm)
            return True
        mupdf.fz_invert_pixmap_rect(pm, r)
        return True

    @property
    def irect(self):
        """Pixmap bbox - an IRect object."""
        val = mupdf.fz_pixmap_bbox(self.this)
        return JM_py_from_irect( val)

    @property
    def is_monochrome(self):
        """Check if pixmap is monochrome."""
        return mupdf.fz_is_pixmap_monochrome( self.this)

    @property
    def is_unicolor(self):
        '''
        Check if pixmap has only one color.
        '''
        pm = self.this
        n = pm.n()
        count = pm.w() * pm.h() * n
        def _pixmap_read_samples(pm, offset, n):
            ret = list()
            for i in range(n):
                ret.append(mupdf.fz_samples_get(pm, offset+i))
            return ret
        sample0 = _pixmap_read_samples( pm, 0, n)
        for offset in range( n, count, n):
            sample = _pixmap_read_samples( pm, offset, n)
            if sample != sample0:
                return False
        return True

    @property
    def n(self):
        """The size of one pixel."""
        if g_use_extra:
            # Setting self.__class__.n gives a small reduction in overhead of
            # test_general.py:test_2093, e.g. 1.4x -> 1.3x.
            #return extra.pixmap_n(self.this)
            def n2(self):
                return extra.pixmap_n(self.this)
            self.__class__.n = property(n2)
            return self.n
        return mupdf.fz_pixmap_components(self.this)

    def pdfocr_save(self, filename, compress=1, language=None, tessdata=None):
        '''
        Save pixmap as an OCR-ed PDF page.
        '''
        tessdata = get_tessdata(tessdata)
        opts = mupdf.FzPdfocrOptions()
        opts.compress = compress
        if language:
            opts.language_set2( language)
        if tessdata:
            opts.datadir_set2( tessdata)
        pix = self.this
        if isinstance(filename, str):
            mupdf.fz_save_pixmap_as_pdfocr( pix, filename, 0, opts)
        else:
            out = JM_new_output_fileptr( filename)
            try:
                mupdf.fz_write_pixmap_as_pdfocr( out, pix, opts)
            finally:
                out.fz_close_output()   # Avoid MuPDF warning.

    def pdfocr_tobytes(self, compress=True, language="eng", tessdata=None):
        """Save pixmap as an OCR-ed PDF page.

        Args:
            compress: (bool) compress, default 1 (True).
            language: (str) language(s) occurring on page, default "eng" (English),
                    multiples like "eng+ger" for English and German.
            tessdata: (str) folder name of Tesseract's language support. If None
                    we use environment variable TESSDATA_PREFIX or search for
                    Tesseract installation.
        Notes:
            On failure, make sure Tesseract is installed and you have set
            <tessdata> or environment variable "TESSDATA_PREFIX" to the folder
            containing your Tesseract's language support data.
        """
        tessdata = get_tessdata(tessdata)
        from io import BytesIO
        bio = BytesIO()
        self.pdfocr_save(bio, compress=compress, language=language, tessdata=tessdata)
        return bio.getvalue()

    def pil_image(self):
        """Create a Pillow Image from the Pixmap."""
        try:
            from PIL import Image
        except ImportError:
            message("PIL/Pillow not installed")
            raise

        cspace = self.colorspace
        if not cspace:
            mode = "L"
        elif cspace.n == 1:
            mode = "L" if not self.alpha else "LA"
        elif cspace.n == 3:
            mode = "RGB" if not self.alpha else "RGBA"
        else:
            mode = "CMYK"

        img = Image.frombytes(mode, (self.width, self.height), self.samples)
        return img

    def pil_save(self, *args, **kwargs):
        """Write to image file using Pillow.

        An intermediate PIL Image is created, and its "save" method is used
        to store the image. See Pillow documentation to learn about the
        meaning of possible positional and keyword parameters.
        Use this when other output formats are desired.
        """
        img = self.pil_image()

        if "dpi" not in kwargs.keys():
            kwargs["dpi"] = (self.xres, self.yres)

        img.save(*args, **kwargs)

    def pil_tobytes(self, *args, **kwargs):
        """Convert to an image in memory using Pillow.

        An intermediate PIL Image is created, and its "save" method is used
        to store the image. See Pillow documentation to learn about the
        meaning of possible positional or keyword parameters.
        Use this when other output formats are desired.
        """
        bytes_out = io.BytesIO()
        img = self.pil_image()

        if "dpi" not in kwargs.keys():
            kwargs["dpi"] = (self.xres, self.yres)

        img.save(bytes_out, *args, **kwargs)
        return bytes_out.getvalue()

    def pixel(self, x, y):
        """Get color tuple of pixel (x, y).
        Last item is the alpha if Pixmap.alpha is true."""
        if g_use_extra:
            return extra.pixmap_pixel(self.this.m_internal, x, y)
        if (0
                or x < 0
                or x >= self.this.m_internal.w
                or y < 0
                or y >= self.this.m_internal.h
                ):
            RAISEPY(MSG_PIXEL_OUTSIDE, PyExc_ValueError)
        n = self.this.m_internal.n
        stride = self.this.m_internal.stride
        i = stride * y + n * x
        ret = tuple( self.samples_mv[ i: i+n])
        return ret

    @property
    def samples(self)->bytes:
        mv = self.samples_mv
        return bytes( mv)

    @property
    def samples_mv(self):
        '''
        Pixmap samples memoryview.
        '''
        # We remember the returned memoryview so that our `__del__()` can
        # release it; otherwise accessing it after we have been destructed will
        # fail, possibly crashing Python; this is #4155.
        #
        if self._samples_mv is None:
            self._samples_mv = mupdf.fz_pixmap_samples_memoryview(self.this)
        return self._samples_mv
    
    def _samples_mv_release(self):
        if self._samples_mv:
            self._samples_mv.release()

    @property
    def samples_ptr(self):
        return mupdf.fz_pixmap_samples_int(self.this)

    def save(self, filename, output=None, jpg_quality=95):
        """Output as image in format determined by filename extension.

        Args:
            output: (str) only use to overrule filename extension. Default is PNG.
                    Others are JPEG, JPG, PNM, PGM, PPM, PBM, PAM, PSD, PS.
        """
        valid_formats = {
                "png": 1,
                "pnm": 2,
                "pgm": 2,
                "ppm": 2,
                "pbm": 2,
                "pam": 3,
                "psd": 5,
                "ps": 6,
                "jpg": 7,
                "jpeg": 7,
                }
        
        if type(filename) is str:
            pass
        elif hasattr(filename, "absolute"):
            filename = str(filename)
        elif hasattr(filename, "name"):
            filename = filename.name
        if output is None:
            _, ext = os.path.splitext(filename)
            output = ext[1:]

        idx = valid_formats.get(output.lower(), None)
        if idx is None:
            raise ValueError(f"Image format {output} not in {tuple(valid_formats.keys())}")
        if self.alpha and idx in (2, 6, 7):
            raise ValueError("'%s' cannot have alpha" % output)
        if self.colorspace and self.colorspace.n > 3 and idx in (1, 2, 4):
            raise ValueError(f"unsupported colorspace for '{output}'")
        if idx == 7:
            self.set_dpi(self.xres, self.yres)
        return self._writeIMG(filename, idx, jpg_quality)

    def set_alpha(self, alphavalues=None, premultiply=1, opaque=None, matte=None):
        """Set alpha channel to values contained in a byte array.
        If omitted, set alphas to 255.

        Args:
            alphavalues: (bytes) with length (width * height) or 'None'.
            premultiply: (bool, True) premultiply colors with alpha values.
            opaque: (tuple, length colorspace.n) this color receives opacity 0.
            matte: (tuple, length colorspace.n)) preblending background color.
        """
        pix = self.this
        alpha = 0
        m = 0
        if pix.alpha() == 0:
            raise ValueError( MSG_PIX_NOALPHA)
        n = mupdf.fz_pixmap_colorants(pix)
        w = mupdf.fz_pixmap_width(pix)
        h = mupdf.fz_pixmap_height(pix)
        balen = w * h * (n+1)
        colors = [0, 0, 0, 0]   # make this color opaque
        bgcolor = [0, 0, 0, 0]  # preblending background color
        zero_out = 0
        bground = 0
        if opaque and isinstance(opaque, (list, tuple)) and len(opaque) == n:
            for i in range(n):
                colors[i] = opaque[i]
            zero_out = 1
        if matte and isinstance( matte, (tuple, list)) and len(matte) == n:
            for i in range(n):
                bgcolor[i] = matte[i]
            bground = 1
        data = bytes()
        data_len = 0
        if alphavalues:
            #res = JM_BufferFromBytes(alphavalues)
            #data_len, data = mupdf.fz_buffer_storage(res)
            #if data_len < w * h:
            #    THROWMSG("bad alpha values")
            # fixme: don't seem to need to create an fz_buffer - can
            # use <alphavalues> directly?
            if isinstance(alphavalues, (bytes, bytearray)):
                data = alphavalues
                data_len = len(alphavalues)
            else:
                assert 0, f'unexpected type for alphavalues: {type(alphavalues)}'
            if data_len < w * h:
                raise ValueError( "bad alpha values")
        if 1:
            # Use C implementation for speed.
            mupdf.Pixmap_set_alpha_helper(
                    balen,
                    n,
                    data_len,
                    zero_out,
                    mupdf.python_buffer_data( data),
                    pix.m_internal,
                    premultiply,
                    bground,
                    colors,
                    bgcolor,
                    )
        else:
            i = k = j = 0
            data_fix = 255
            while i < balen:
                alpha = data[k]
                if zero_out:
                    for j in range(i, i+n):
                        if mupdf.fz_samples_get(pix, j) != colors[j - i]:
                            data_fix = 255
                            break
                        else:
                            data_fix = 0
                if data_len:
                    def fz_mul255( a, b):
                        x = a * b + 128
                        x += x // 256
                        return x // 256

                    if data_fix == 0:
                        mupdf.fz_samples_set(pix, i+n, 0)
                    else:
                        mupdf.fz_samples_set(pix, i+n, alpha)
                    if premultiply and not bground:
                        for j in range(i, i+n):
                            mupdf.fz_samples_set(pix, j, fz_mul255( mupdf.fz_samples_get(pix, j), alpha))
                    elif bground:
                        for j in range( i, i+n):
                            m = bgcolor[j - i]
                            mupdf.fz_samples_set(pix, j, fz_mul255( mupdf.fz_samples_get(pix, j) - m, alpha))
                else:
                    mupdf.fz_samples_set(pix, i+n, data_fix)
                i += n+1
                k += 1

    def tobytes(self, output="png", jpg_quality=95):
        '''
        Convert to binary image stream of desired type.
        '''
        valid_formats = {
                "png": 1,
                "pnm": 2,
                "pgm": 2,
                "ppm": 2,
                "pbm": 2,
                "pam": 3,
                "tga": 4,
                "tpic": 4,
                "psd": 5,
                "ps": 6,
                'jpg': 7,
                'jpeg': 7,
                }
        idx = valid_formats.get(output.lower(), None)
        if idx is None:
            raise ValueError(f"Image format {output} not in {tuple(valid_formats.keys())}")
        if self.alpha and idx in (2, 6, 7):
            raise ValueError("'{output}' cannot have alpha")
        if self.colorspace and self.colorspace.n > 3 and idx in (1, 2, 4):
            raise ValueError(f"unsupported colorspace for '{output}'")
        if idx == 7:
            self.set_dpi(self.xres, self.yres)
        barray = self._tobytes(idx, jpg_quality)
        return barray

    def set_dpi(self, xres, yres):
        """Set resolution in both dimensions."""
        pm = self.this
        pm.m_internal.xres = xres
        pm.m_internal.yres = yres

    def set_origin(self, x, y):
        """Set top-left coordinates."""
        pm = self.this
        pm.m_internal.x = x
        pm.m_internal.y = y

    def set_pixel(self, x, y, color):
        """Set color of pixel (x, y)."""
        if g_use_extra:
            return extra.set_pixel(self.this.m_internal, x, y, color)
        pm = self.this
        if not _INRANGE(x, 0, pm.w() - 1) or not _INRANGE(y, 0, pm.h() - 1):
            raise ValueError( MSG_PIXEL_OUTSIDE)
        n = pm.n()
        for j in range(n):
            i = color[j]
            if not _INRANGE(i, 0, 255):
                raise ValueError( MSG_BAD_COLOR_SEQ)
        stride = mupdf.fz_pixmap_stride( pm)
        i = stride * y + n * x
        if 0:
            # Using a cached self._memory_view doesn't actually make much
            # difference to speed.
            if not self._memory_view:
                self._memory_view = self.samples_mv
            for j in range(n):
                self._memory_view[i + j] = color[j]
        else:
            for j in range(n):
                pm.fz_samples_set(i + j, color[j])

    def set_rect(self, bbox, color):
        """Set color of all pixels in bbox."""
        pm = self.this
        n = pm.n()
        c = []
        for j in range(n):
            i = color[j]
            if not _INRANGE(i, 0, 255):
                raise ValueError( MSG_BAD_COLOR_SEQ)
            c.append(i)
        bbox = JM_irect_from_py(bbox)
        i = JM_fill_pixmap_rect_with_color(pm, c, bbox)
        rc = bool(i)
        return rc

    def shrink(self, factor):
        """Divide width and height by 2**factor.
        E.g. factor=1 shrinks to 25% of original size (in place)."""
        if factor < 1:
            message_warning("ignoring shrink factor < 1")
            return
        mupdf.fz_subsample_pixmap( self.this, factor)
        # Pixmap has changed so clear our memory view.
        self._memory_view = None
        self._samples_mv_release()

    @property
    def size(self):
        """Pixmap size."""
        return  mupdf.fz_pixmap_size( self.this)

    @property
    def stride(self):
        """Length of one image line (width * n)."""
        return self.this.stride()

    def tint_with(self, black, white):
        """Tint colors with modifiers for black and white."""
        if not self.colorspace or self.colorspace.n > 3:
            message("warning: colorspace invalid for function")
            return
        return mupdf.fz_tint_pixmap( self.this, black, white)

    @property
    def w(self):
        """The width."""
        return mupdf.fz_pixmap_width(self.this)
    
    def warp(self, quad, width, height):
        """Return pixmap from a warped quad."""
        if not quad.is_convex: raise ValueError("quad must be convex")
        q = JM_quad_from_py(quad)
        points = [ q.ul, q.ur, q.lr, q.ll]
        dst = mupdf.fz_warp_pixmap( self.this, points, width, height)
        return Pixmap( dst)

    @property
    def x(self):
        """x component of Pixmap origin."""
        return mupdf.fz_pixmap_x(self.this)

    @property
    def xres(self):
        """Resolution in x direction."""
        return self.this.xres()

    @property
    def y(self):
        """y component of Pixmap origin."""
        return mupdf.fz_pixmap_y(self.this)

    @property
    def yres(self):
        """Resolution in y direction."""
        return self.this.yres()

    width  = w
    height = h
    
    def __del__(self):
        if self._samples_mv:
            self._samples_mv.release()


del Point
class Point:

    def __abs__(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def __add__(self, p):
        if hasattr(p, "__float__"):
            return Point(self.x + p, self.y + p)
        if len(p) != 2:
            raise ValueError("Point: bad seq len")
        return Point(self.x + p[0], self.y + p[1])

    def __bool__(self):
        return not (max(self) == min(self) == 0)

    def __eq__(self, p):
        if not hasattr(p, "__len__"):
            return False
        return len(p) == 2 and not (self - p)

    def __getitem__(self, i):
        return (self.x, self.y)[i]

    def __hash__(self):
        return hash(tuple(self))

    def __init__(self, *args, x=None, y=None):
        '''
        Point() - all zeros
        Point(x, y)
        Point(Point) - new copy
        Point(sequence) - from 'sequence'

        Explicit keyword args x, y override earlier settings if not None.
        '''
        if not args:
            self.x = 0.0
            self.y = 0.0
        elif len(args) > 2:
            raise ValueError("Point: bad seq len")
        elif len(args) == 2:
            self.x = float(args[0])
            self.y = float(args[1])
        elif len(args) == 1:
            l = args[0]
            if isinstance(l, (mupdf.FzPoint, mupdf.fz_point)):
                self.x = l.x
                self.y = l.y
            else:
                if not hasattr(l, "__getitem__"):
                    raise ValueError("Point: bad args")
                if len(l) != 2:
                    raise ValueError("Point: bad seq len")
                self.x = float(l[0])
                self.y = float(l[1])
        else:
            raise ValueError("Point: bad seq len")
        if x is not None:   self.x = x
        if y is not None:   self.y = y

    def __len__(self):
        return 2

    def __mul__(self, m):
        if hasattr(m, "__float__"):
            return Point(self.x * m, self.y * m)
        if hasattr(m, "__getitem__") and len(m) == 2:
            # dot product
            return self.x * m[0] + self.y * m[1]
        p = Point(self)
        return p.transform(m)

    def __neg__(self):
        return Point(-self.x, -self.y)

    def __nonzero__(self):
        return not (max(self) == min(self) == 0)

    def __pos__(self):
        return Point(self)

    def __repr__(self):
        return "Point" + str(tuple(self))

    def __setitem__(self, i, v):
        v = float(v)
        if   i == 0: self.x = v
        elif i == 1: self.y = v
        else:
            raise IndexError("index out of range")
        return None

    def __sub__(self, p):
        if hasattr(p, "__float__"):
            return Point(self.x - p, self.y - p)
        if len(p) != 2:
            raise ValueError("Point: bad seq len")
        return Point(self.x - p[0], self.y - p[1])

    def __truediv__(self, m):
        if hasattr(m, "__float__"):
            return Point(self.x * 1./m, self.y * 1./m)
        m1 = util_invert_matrix(m)[1]
        if not m1:
            raise ZeroDivisionError("matrix not invertible")
        p = Point(self)
        return p.transform(m1)

    @property
    def abs_unit(self):
        """Unit vector with positive coordinates."""
        s = self.x * self.x + self.y * self.y
        if s < EPSILON:
            return Point(0,0)
        s = math.sqrt(s)
        return Point(abs(self.x) / s, abs(self.y) / s)

    def distance_to(self, *args):
        """Return distance to rectangle or another point."""
        if not len(args) > 0:
            raise ValueError("at least one parameter must be given")

        x = args[0]
        if len(x) == 2:
            x = Point(x)
        elif len(x) == 4:
            x = Rect(x)
        else:
            raise ValueError("arg1 must be point-like or rect-like")

        if len(args) > 1:
            unit = args[1]
        else:
            unit = "px"
        u = {"px": (1.,1.), "in": (1.,72.), "cm": (2.54, 72.),
             "mm": (25.4, 72.)}
        f = u[unit][0] / u[unit][1]

        if type(x) is Point:
            return abs(self - x) * f

        # from here on, x is a rectangle
        # as a safeguard, make a finite copy of it
        r = Rect(x.top_left, x.top_left)
        r = r | x.bottom_right
        if self in r:
            return 0.0
        if self.x > r.x1:
            if self.y >= r.y1:
                return self.distance_to(r.bottom_right, unit)
            elif self.y <= r.y0:
                return self.distance_to(r.top_right, unit)
            else:
                return (self.x - r.x1) * f
        elif r.x0 <= self.x <= r.x1:
            if self.y >= r.y1:
                return (self.y - r.y1) * f
            else:
                return (r.y0 - self.y) * f
        else:
            if self.y >= r.y1:
                return self.distance_to(r.bottom_left, unit)
            elif self.y <= r.y0:
                return self.distance_to(r.top_left, unit)
            else:
                return (r.x0 - self.x) * f

    def transform(self, m):
        """Replace point by its transformation with matrix-like m."""
        if len(m) != 6:
            raise ValueError("Matrix: bad seq len")
        self.x, self.y = util_transform_point(self, m)
        return self

    @property
    def unit(self):
        """Unit vector of the point."""
        s = self.x * self.x + self.y * self.y
        if s < EPSILON:
            return Point(0,0)
        s = math.sqrt(s)
        return Point(self.x / s, self.y / s)

    __div__ = __truediv__
    norm = __abs__


class Quad:

    def __abs__(self):
        if self.is_empty:
            return 0.0
        return abs(self.ul - self.ur) * abs(self.ul - self.ll)

    def __add__(self, q):
        if hasattr(q, "__float__"):
            return Quad(self.ul + q, self.ur + q, self.ll + q, self.lr + q)
        if len(q) != 4:
            raise ValueError("Quad: bad seq len")
        return Quad(self.ul + q[0], self.ur + q[1], self.ll + q[2], self.lr + q[3])

    def __bool__(self):
        return not self.is_empty

    def __contains__(self, x):
        try:
            l = x.__len__()
        except Exception:
            if g_exceptions_verbose > 1:    exception_info()
            return False
        if l == 2:
            return util_point_in_quad(x, self)
        if l != 4:
            return False
        if CheckRect(x):
            if Rect(x).is_empty:
                return True
            return util_point_in_quad(x[:2], self) and util_point_in_quad(x[2:], self)
        if CheckQuad(x):
            for i in range(4):
                if not util_point_in_quad(x[i], self):
                    return False
            return True
        return False

    def __eq__(self, quad):
        if not hasattr(quad, "__len__"):
            return False
        return len(quad) == 4 and (
            self.ul == quad[0] and
            self.ur == quad[1] and
            self.ll == quad[2] and
            self.lr == quad[3]
        )

    def __getitem__(self, i):
        return (self.ul, self.ur, self.ll, self.lr)[i]

    def __hash__(self):
        return hash(tuple(self))

    def __init__(self, *args, ul=None, ur=None, ll=None, lr=None):
        '''
        Quad() - all zero points
        Quad(ul, ur, ll, lr)
        Quad(quad) - new copy
        Quad(sequence) - from 'sequence'

        Explicit keyword args ul, ur, ll, lr override earlier settings if not
        None.
    
        '''
        if not args:
            self.ul = self.ur = self.ll = self.lr = Point()
        elif len(args) > 4:
            raise ValueError("Quad: bad seq len")
        elif len(args) == 4:
            self.ul, self.ur, self.ll, self.lr = map(Point, args)
        elif len(args) == 1:
            l = args[0]
            if isinstance(l, mupdf.FzQuad):
                self.this = l
                self.ul, self.ur, self.ll, self.lr = Point(l.ul), Point(l.ur), Point(l.ll), Point(l.lr)
            elif not hasattr(l, "__getitem__"):
                raise ValueError("Quad: bad args")
            elif len(l) != 4:
                raise ValueError("Quad: bad seq len")
            else:
                self.ul, self.ur, self.ll, self.lr = map(Point, l)
        else:
            raise ValueError("Quad: bad args")
        if ul is not None:  self.ul = Point(ul)
        if ur is not None:  self.ur = Point(ur)
        if ll is not None:  self.ll = Point(ll)
        if lr is not None:  self.lr = Point(lr)

    def __len__(self):
        return 4

    def __mul__(self, m):
        q = Quad(self)
        q = q.transform(m)
        return q

    def __neg__(self):
        return Quad(-self.ul, -self.ur, -self.ll, -self.lr)

    def __nonzero__(self):
        return not self.is_empty

    def __pos__(self):
        return Quad(self)

    def __repr__(self):
        return "Quad" + str(tuple(self))

    def __setitem__(self, i, v):
        if   i == 0: self.ul = Point(v)
        elif i == 1: self.ur = Point(v)
        elif i == 2: self.ll = Point(v)
        elif i == 3: self.lr = Point(v)
        else:
            raise IndexError("index out of range")
        return None

    def __sub__(self, q):
        if hasattr(q, "__float__"):
            return Quad(self.ul - q, self.ur - q, self.ll - q, self.lr - q)
        if len(q) != 4:
            raise ValueError("Quad: bad seq len")
        return Quad(self.ul - q[0], self.ur - q[1], self.ll - q[2], self.lr - q[3])

    def __truediv__(self, m):
        if hasattr(m, "__float__"):
            im = 1. / m
        else:
            im = util_invert_matrix(m)[1]
            if not im:
                raise ZeroDivisionError("Matrix not invertible")
        q = Quad(self)
        q = q.transform(im)
        return q

    @property
    def is_convex(self):
        """Check if quad is convex and not degenerate.

        Notes:
            Check that for the two diagonals, the other two corners are not
            on the same side of the diagonal.
        Returns:
            True or False.
        """
        m = planish_line(self.ul, self.lr)  # puts this diagonal on x-axis
        p1 = self.ll * m  # transform the
        p2 = self.ur * m  # other two points
        if p1.y * p2.y > 0:
            return False
        m = planish_line(self.ll, self.ur)  # puts other diagonal on x-axis
        p1 = self.lr * m  # transform the
        p2 = self.ul * m  # remaining points
        if p1.y * p2.y > 0:
            return False
        return True

    @property
    def is_empty(self):
        """Check whether all quad corners are on the same line.

        This is the case if width or height is zero.
        """
        return self.width < EPSILON or self.height < EPSILON

    @property
    def is_infinite(self):
        """Check whether this is the infinite quad."""
        return self.rect.is_infinite

    @property
    def is_rectangular(self):
        """Check if quad is rectangular.

        Notes:
            Some rotation matrix can thus transform it into a rectangle.
            This is equivalent to three corners enclose 90 degrees.
        Returns:
            True or False.
        """

        sine = util_sine_between(self.ul, self.ur, self.lr)
        if abs(sine - 1) > EPSILON:  # the sine of the angle
            return False

        sine = util_sine_between(self.ur, self.lr, self.ll)
        if abs(sine - 1) > EPSILON:
            return False

        sine = util_sine_between(self.lr, self.ll, self.ul)
        if abs(sine - 1) > EPSILON:
            return False

        return True

    def morph(self, p, m):
        """Morph the quad with matrix-like 'm' and point-like 'p'.

        Return a new quad."""
        if self.is_infinite:
            return INFINITE_QUAD()
        delta = Matrix(1, 1).pretranslate(p.x, p.y)
        q = self * ~delta * m * delta
        return q

    @property
    def rect(self):
        r = Rect()
        r.x0 = min(self.ul.x, self.ur.x, self.lr.x, self.ll.x)
        r.y0 = min(self.ul.y, self.ur.y, self.lr.y, self.ll.y)
        r.x1 = max(self.ul.x, self.ur.x, self.lr.x, self.ll.x)
        r.y1 = max(self.ul.y, self.ur.y, self.lr.y, self.ll.y)
        return r

    def transform(self, m):
        """Replace quad by its transformation with matrix m."""
        if hasattr(m, "__float__"):
            pass
        elif len(m) != 6:
            raise ValueError("Matrix: bad seq len")
        self.ul *= m
        self.ur *= m
        self.ll *= m
        self.lr *= m
        return self

    __div__ = __truediv__
    width  = property(lambda self: max(abs(self.ul - self.ur), abs(self.ll - self.lr)))
    height = property(lambda self: max(abs(self.ul - self.ll), abs(self.ur - self.lr)))


class Rect:
    
    def __abs__(self):
        if self.is_empty or self.is_infinite:
            return 0.0
        return (self.x1 - self.x0) * (self.y1 - self.y0)

    def __add__(self, p):
        if hasattr(p, "__float__"):
            return Rect(self.x0 + p, self.y0 + p, self.x1 + p, self.y1 + p)
        if len(p) != 4:
            raise ValueError("Rect: bad seq len")
        return Rect(self.x0 + p[0], self.y0 + p[1], self.x1 + p[2], self.y1 + p[3])

    def __and__(self, x):
        if not hasattr(x, "__len__"):
            raise ValueError("bad operand 2")

        r1 = Rect(x)
        r = Rect(self)
        return r.intersect(r1)

    def __bool__(self):
        return not (max(self) == min(self) == 0)

    def __contains__(self, x):
        if hasattr(x, "__float__"):
            return x in tuple(self)
        l = len(x)
        if l == 2:
            return util_is_point_in_rect(x, self)
        if l == 4:
            r = INFINITE_RECT()
            try:
                r = Rect(x)
            except Exception:
                if g_exceptions_verbose > 1:    exception_info()
                r = Quad(x).rect
            return (self.x0 <= r.x0 <= r.x1 <= self.x1 and
                    self.y0 <= r.y0 <= r.y1 <= self.y1)
        return False

    def __eq__(self, rect):
        if not hasattr(rect, "__len__"):
            return False
        return len(rect) == 4 and not (self - rect)

    def __getitem__(self, i):
        return (self.x0, self.y0, self.x1, self.y1)[i]

    def __hash__(self):
        return hash(tuple(self))

    def __init__(self, *args, p0=None, p1=None, x0=None, y0=None, x1=None, y1=None):
        """
        Rect() - all zeros
        Rect(x0, y0, x1, y1)
        Rect(top-left, x1, y1)
        Rect(x0, y0, bottom-right)
        Rect(top-left, bottom-right)
        Rect(Rect or IRect) - new copy
        Rect(sequence) - from 'sequence'
    
        Explicit keyword args p0, p1, x0, y0, x1, y1 override earlier settings
        if not None.
        """
        x0, y0, x1, y1 = util_make_rect( *args, p0=p0, p1=p1, x0=x0, y0=y0, x1=x1, y1=y1)
        self.x0 = float( x0)
        self.y0 = float( y0)
        self.x1 = float( x1)
        self.y1 = float( y1)

    def __len__(self):
        return 4

    def __mul__(self, m):
        if hasattr(m, "__float__"):
            return Rect(self.x0 * m, self.y0 * m, self.x1 * m, self.y1 * m)
        r = Rect(self)
        r = r.transform(m)
        return r

    def __neg__(self):
        return Rect(-self.x0, -self.y0, -self.x1, -self.y1)

    def __nonzero__(self):
        return not (max(self) == min(self) == 0)

    def __or__(self, x):
        if not hasattr(x, "__len__"):
            raise ValueError("bad operand 2")
        r = Rect(self)
        if len(x) == 2:
            return r.include_point(x)
        if len(x) == 4:
            return r.include_rect(x)
        raise ValueError("bad operand 2")

    def __pos__(self):
        return Rect(self)

    def __repr__(self):
        return "Rect" + str(tuple(self))

    def __setitem__(self, i, v):
        v = float(v)
        if   i == 0: self.x0 = v
        elif i == 1: self.y0 = v
        elif i == 2: self.x1 = v
        elif i == 3: self.y1 = v
        else:
            raise IndexError("index out of range")
        return None

    def __sub__(self, p):
        if hasattr(p, "__float__"):
            return Rect(self.x0 - p, self.y0 - p, self.x1 - p, self.y1 - p)
        if len(p) != 4:
            raise ValueError("Rect: bad seq len")
        return Rect(self.x0 - p[0], self.y0 - p[1], self.x1 - p[2], self.y1 - p[3])

    def __truediv__(self, m):
        if hasattr(m, "__float__"):
            return Rect(self.x0 * 1./m, self.y0 * 1./m, self.x1 * 1./m, self.y1 * 1./m)
        im = util_invert_matrix(m)[1]
        if not im:
            raise ZeroDivisionError(f"Matrix not invertible: {m}")
        r = Rect(self)
        r = r.transform(im)
        return r

    @property
    def bottom_left(self):
        """Bottom-left corner."""
        return Point(self.x0, self.y1)

    @property
    def bottom_right(self):
        """Bottom-right corner."""
        return Point(self.x1, self.y1)

    def contains(self, x):
        """Check if containing point-like or rect-like x."""
        return self.__contains__(x)

    @property
    def height(self):
        return max(0, self.y1 - self.y0)

    def include_point(self, p):
        """Extend to include point-like p."""
        if len(p) != 2:
            raise ValueError("Point: bad seq len")
        self.x0, self.y0, self.x1, self.y1 = util_include_point_in_rect(self, p)
        return self

    def include_rect(self, r):
        """Extend to include rect-like r."""
        if len(r) != 4:
            raise ValueError("Rect: bad seq len")
        r = Rect(r)
        if r.is_infinite or self.is_infinite:
            self.x0, self.y0, self.x1, self.y1 = FZ_MIN_INF_RECT, FZ_MIN_INF_RECT, FZ_MAX_INF_RECT, FZ_MAX_INF_RECT
        elif r.is_empty:
            return self
        elif self.is_empty:
            self.x0, self.y0, self.x1, self.y1 = r.x0, r.y0, r.x1, r.y1
        else:
            self.x0, self.y0, self.x1, self.y1 = util_union_rect(self, r)
        return self

    def intersect(self, r):
        """Restrict to common rect with rect-like r."""
        if not len(r) == 4:
            raise ValueError("Rect: bad seq len")
        r = Rect(r)
        if r.is_infinite:
            return self
        elif self.is_infinite:
            self.x0, self.y0, self.x1, self.y1 = r.x0, r.y0, r.x1, r.y1
        elif r.is_empty:
            self.x0, self.y0, self.x1, self.y1 = r.x0, r.y0, r.x1, r.y1
        elif self.is_empty:
            return self
        else:
            self.x0, self.y0, self.x1, self.y1 = util_intersect_rect(self, r)
        return self

    def intersects(self, x):
        """Check if intersection with rectangle x is not empty."""
        r1 = Rect(x)
        if self.is_empty or self.is_infinite or r1.is_empty or r1.is_infinite:
            return False
        r = Rect(self)
        if r.intersect(r1).is_empty:
            return False
        return True

    @property
    def is_empty(self):
        """True if rectangle area is empty."""
        return self.x0 >= self.x1 or self.y0 >= self.y1

    @property
    def is_infinite(self):
        """True if this is the infinite rectangle."""
        return self.x0 == self.y0 == FZ_MIN_INF_RECT and self.x1 == self.y1 == FZ_MAX_INF_RECT

    @property
    def is_valid(self):
        """True if rectangle is valid."""
        return self.x0 <= self.x1 and self.y0 <= self.y1

    def morph(self, p, m):
        """Morph with matrix-like m and point-like p.

        Returns a new quad."""
        if self.is_infinite:
            return INFINITE_QUAD()
        return self.quad.morph(p, m)

    def norm(self):
        return math.sqrt(sum([c*c for c in self]))

    def normalize(self):
        """Replace rectangle with its finite version."""
        if self.x1 < self.x0:
            self.x0, self.x1 = self.x1, self.x0
        if self.y1 < self.y0:
            self.y0, self.y1 = self.y1, self.y0
        return self

    @property
    def quad(self):
        """Return Quad version of rectangle."""
        return Quad(self.tl, self.tr, self.bl, self.br)

    def round(self):
        """Return the IRect."""
        return IRect(util_round_rect(self))

    @property
    def top_left(self):
        """Top-left corner."""
        return Point(self.x0, self.y0)

    @property
    def top_right(self):
        """Top-right corner."""
        return Point(self.x1, self.y0)
    
    def torect(self, r):
        """Return matrix that converts to target rect."""

        r = Rect(r)
        if self.is_infinite or self.is_empty or r.is_infinite or r.is_empty:
            raise ValueError("rectangles must be finite and not empty")
        return (
            Matrix(1, 0, 0, 1, -self.x0, -self.y0)
            * Matrix(r.width / self.width, r.height / self.height)
            * Matrix(1, 0, 0, 1, r.x0, r.y0)
        )

    def transform(self, m):
        """Replace with the transformation by matrix-like m."""
        if not len(m) == 6:
            raise ValueError("Matrix: bad seq len")
        self.x0, self.y0, self.x1, self.y1 = util_transform_rect(self, m)
        return self

    @property
    def width(self):
        return max(0, self.x1 - self.x0)

    __div__ = __truediv__

    bl = bottom_left
    br = bottom_right
    irect = property(round)
    tl = top_left
    tr = top_right


class Shape:
    """Create a new shape."""

    def __init__(self, page: Page):
        CheckParent(page)
        self.page = page
        self.doc = page.parent
        if not self.doc.is_pdf:
            raise ValueError("not a PDF")
        self.height = page.mediabox_size.y
        self.width = page.mediabox_size.x
        self.x = page.cropbox_position.x
        self.y = page.cropbox_position.y

        self.pctm = page.transformation_matrix  # page transf. matrix
        self.ipctm = ~self.pctm  # inverted transf. matrix

        self.draw_cont = ""
        self.text_cont = ""
        self.totalcont = ""
        self.last_point = None
        self.rect = None

    def commit(self, overlay: bool = True) -> None:
        """
        Update the page's /Contents object with Shape data. The argument
        controls whether data appear in foreground (default) or background.
        """
        CheckParent(self.page)  # doc may have died meanwhile
        self.totalcont += self.text_cont

        self.totalcont = self.totalcont.encode()

        if self.totalcont != b"":
            # make /Contents object with dummy stream
            xref = TOOLS._insert_contents(self.page, b" ", overlay)
            # update it with potential compression
            mupdf.pdf_update_stream(self.doc, xref, self.totalcont)

        self.last_point = None  # clean up ...
        self.rect = None  #
        self.draw_cont = ""  # for potential ...
        self.text_cont = ""  # ...
        self.totalcont = ""  # re-use
        return

    def draw_bezier(
            self,
            p1: point_like,
            p2: point_like,
            p3: point_like,
            p4: point_like,
            ):# -> Point:
        """Draw a standard cubic Bezier curve."""
        p1 = Point(p1)
        p2 = Point(p2)
        p3 = Point(p3)
        p4 = Point(p4)
        if not (self.last_point == p1):
            args = JM_TUPLE(p1 * self.ipctm)
            self.draw_cont += f"{_format_g(args)} m\n"
        args = JM_TUPLE(list(p2 * self.ipctm) + list(p3 * self.ipctm) + list(p4 * self.ipctm))
        self.draw_cont += f"{_format_g(args)} c\n"
        self.updateRect(p1)
        self.updateRect(p2)
        self.updateRect(p3)
        self.updateRect(p4)
        self.last_point = p4
        return self.last_point

    def draw_circle(self, center: point_like, radius: float):# -> Point:
        """Draw a circle given its center and radius."""
        if not radius > EPSILON:
            raise ValueError("radius must be positive")
        center = Point(center)
        p1 = center - (radius, 0)
        return self.draw_sector(center, p1, 360, fullSector=False)

    def draw_curve(
            self,
            p1: point_like,
            p2: point_like,
            p3: point_like,
            ):# -> Point:
        """Draw a curve between points using one control point."""
        kappa = 0.55228474983
        p1 = Point(p1)
        p2 = Point(p2)
        p3 = Point(p3)
        k1 = p1 + (p2 - p1) * kappa
        k2 = p3 + (p2 - p3) * kappa
        return self.draw_bezier(p1, k1, k2, p3)

    def draw_line(self, p1: point_like, p2: point_like):# -> Point:
        """Draw a line between two points."""
        p1 = Point(p1)
        p2 = Point(p2)
        if not (self.last_point == p1):
            self.draw_cont += _format_g(JM_TUPLE(p1 * self.ipctm)) + " m\n"
            self.last_point = p1
            self.updateRect(p1)

        self.draw_cont += _format_g(JM_TUPLE(p2 * self.ipctm)) + " l\n"
        self.updateRect(p2)
        self.last_point = p2
        return self.last_point

    def draw_oval(self, tetra: typing.Union[quad_like, rect_like]):# -> Point:
        """Draw an ellipse inside a tetrapod."""
        if len(tetra) != 4:
            raise ValueError("invalid arg length")
        if hasattr(tetra[0], "__float__"):
            q = Rect(tetra).quad
        else:
            q = Quad(tetra)

        mt = q.ul + (q.ur - q.ul) * 0.5
        mr = q.ur + (q.lr - q.ur) * 0.5
        mb = q.ll + (q.lr - q.ll) * 0.5
        ml = q.ul + (q.ll - q.ul) * 0.5
        if not (self.last_point == ml):
            self.draw_cont += _format_g(JM_TUPLE(ml * self.ipctm)) + " m\n"
            self.last_point = ml
        self.draw_curve(ml, q.ll, mb)
        self.draw_curve(mb, q.lr, mr)
        self.draw_curve(mr, q.ur, mt)
        self.draw_curve(mt, q.ul, ml)
        self.updateRect(q.rect)
        self.last_point = ml
        return self.last_point

    def draw_polyline(self, points: list):# -> Point:
        """Draw several connected line segments."""
        for i, p in enumerate(points):
            if i == 0:
                if not (self.last_point == Point(p)):
                    self.draw_cont += _format_g(JM_TUPLE(Point(p) * self.ipctm)) + " m\n"
                    self.last_point = Point(p)
            else:
                self.draw_cont += _format_g(JM_TUPLE(Point(p) * self.ipctm)) + " l\n"
            self.updateRect(p)

        self.last_point = Point(points[-1])
        return self.last_point

    def draw_quad(self, quad: quad_like):# -> Point:
        """Draw a Quad."""
        q = Quad(quad)
        return self.draw_polyline([q.ul, q.ll, q.lr, q.ur, q.ul])

    def draw_rect(self, rect: rect_like):# -> Point:
        """Draw a rectangle."""
        r = Rect(rect)
        args = JM_TUPLE(list(r.bl * self.ipctm) + [r.width, r.height])
        self.draw_cont += _format_g(args) + " re\n"
            
        self.updateRect(r)
        self.last_point = r.tl
        return self.last_point

    def draw_sector(
            self,
            center: point_like,
            point: point_like,
            beta: float,
            fullSector: bool = True,
            ):# -> Point:
        """Draw a circle sector."""
        center = Point(center)
        point = Point(point)
        def l3(a, b):
            return _format_g((a, b)) + " m\n"
        def l4(a, b, c, d, e, f):
            return _format_g((a, b, c, d, e, f)) + " c\n"
        def l5(a, b):
            return _format_g((a, b)) + " l\n"
        betar = math.radians(-beta)
        w360 = math.radians(math.copysign(360, betar)) * (-1)
        w90 = math.radians(math.copysign(90, betar))
        w45 = w90 / 2
        while abs(betar) > 2 * math.pi:
            betar += w360  # bring angle below 360 degrees
        if not (self.last_point == point):
            self.draw_cont += l3(JM_TUPLE(point * self.ipctm))
            self.last_point = point
        Q = Point(0, 0)  # just make sure it exists
        C = center
        P = point
        S = P - C  # vector 'center' -> 'point'
        rad = abs(S)  # circle radius

        if not rad > EPSILON:
            raise ValueError("radius must be positive")

        alfa = self.horizontal_angle(center, point)
        while abs(betar) > abs(w90):  # draw 90 degree arcs
            q1 = C.x + math.cos(alfa + w90) * rad
            q2 = C.y + math.sin(alfa + w90) * rad
            Q = Point(q1, q2)  # the arc's end point
            r1 = C.x + math.cos(alfa + w45) * rad / math.cos(w45)
            r2 = C.y + math.sin(alfa + w45) * rad / math.cos(w45)
            R = Point(r1, r2)  # crossing point of tangents
            kappah = (1 - math.cos(w45)) * 4 / 3 / abs(R - Q)
            kappa = kappah * abs(P - Q)
            cp1 = P + (R - P) * kappa  # control point 1
            cp2 = Q + (R - Q) * kappa  # control point 2
            self.draw_cont += l4(JM_TUPLE(
                list(cp1 * self.ipctm) + list(cp2 * self.ipctm) + list(Q * self.ipctm)
            ))

            betar -= w90  # reduce param angle by 90 deg
            alfa += w90  # advance start angle by 90 deg
            P = Q  # advance to arc end point
        # draw (remaining) arc
        if abs(betar) > 1e-3:  # significant degrees left?
            beta2 = betar / 2
            q1 = C.x + math.cos(alfa + betar) * rad
            q2 = C.y + math.sin(alfa + betar) * rad
            Q = Point(q1, q2)  # the arc's end point
            r1 = C.x + math.cos(alfa + beta2) * rad / math.cos(beta2)
            r2 = C.y + math.sin(alfa + beta2) * rad / math.cos(beta2)
            R = Point(r1, r2)  # crossing point of tangents
            # kappa height is 4/3 of segment height
            kappah = (1 - math.cos(beta2)) * 4 / 3 / abs(R - Q)  # kappa height
            kappa = kappah * abs(P - Q) / (1 - math.cos(betar))
            cp1 = P + (R - P) * kappa  # control point 1
            cp2 = Q + (R - Q) * kappa  # control point 2
            self.draw_cont += l4(JM_TUPLE(
                list(cp1 * self.ipctm) + list(cp2 * self.ipctm) + list(Q * self.ipctm)
            ))
        if fullSector:
            self.draw_cont += l3(JM_TUPLE(point * self.ipctm))
            self.draw_cont += l5(JM_TUPLE(center * self.ipctm))
            self.draw_cont += l5(JM_TUPLE(Q * self.ipctm))
        self.last_point = Q
        return self.last_point

    def draw_squiggle(
            self,
            p1: point_like,
            p2: point_like,
            breadth=2,
            ):# -> Point:
        """Draw a squiggly line from p1 to p2."""
        p1 = Point(p1)
        p2 = Point(p2)
        S = p2 - p1  # vector start - end
        rad = abs(S)  # distance of points
        cnt = 4 * int(round(rad / (4 * breadth), 0))  # always take full phases
        if cnt < 4:
            raise ValueError("points too close")
        mb = rad / cnt  # revised breadth
        matrix = Matrix(TOOLS._hor_matrix(p1, p2))  # normalize line to x-axis
        i_mat = ~matrix  # get original position
        k = 2.4142135623765633  # y of draw_curve helper point

        points = []  # stores edges
        for i in range(1, cnt):
            if i % 4 == 1:  # point "above" connection
                p = Point(i, -k) * mb
            elif i % 4 == 3:  # point "below" connection
                p = Point(i, k) * mb
            else:  # else on connection line
                p = Point(i, 0) * mb
            points.append(p * i_mat)

        points = [p1] + points + [p2]
        cnt = len(points)
        i = 0
        while i + 2 < cnt:
            self.draw_curve(points[i], points[i + 1], points[i + 2])
            i += 2
        return p2

    def draw_zigzag(
            self,
            p1: point_like,
            p2: point_like,
            breadth: float = 2,
            ):# -> Point:
        """Draw a zig-zagged line from p1 to p2."""
        p1 = Point(p1)
        p2 = Point(p2)
        S = p2 - p1  # vector start - end
        rad = abs(S)  # distance of points
        cnt = 4 * int(round(rad / (4 * breadth), 0))  # always take full phases
        if cnt < 4:
            raise ValueError("points too close")
        mb = rad / cnt  # revised breadth
        matrix = Matrix(TOOLS._hor_matrix(p1, p2))  # normalize line to x-axis
        i_mat = ~matrix  # get original position
        points = []  # stores edges
        for i in range(1, cnt):
            if i % 4 == 1:  # point "above" connection
                p = Point(i, -1) * mb
            elif i % 4 == 3:  # point "below" connection
                p = Point(i, 1) * mb
            else:  # ignore others
                continue
            points.append(p * i_mat)
        self.draw_polyline([p1] + points + [p2])  # add start and end points
        return p2

    def finish(
            self,
            width: float = 1,
            color: OptSeq = (0,),
            fill: OptSeq = None,
            lineCap: int = 0,
            lineJoin: int = 0,
            dashes: OptStr = None,
            even_odd: bool = False,
            morph: OptSeq = None,
            closePath: bool = True,
            fill_opacity: float = 1,
            stroke_opacity: float = 1,
            oc: int = 0,
            ) -> None:
        """Finish the current drawing segment.

        Notes:
            Apply colors, opacity, dashes, line style and width, or
            morphing. Also whether to close the path
            by connecting last to first point.
        """
        if self.draw_cont == "":  # treat empty contents as no-op
            return

        if width == 0:  # border color makes no sense then
            color = None
        elif color is None:  # vice versa
            width = 0
        # if color == None and fill == None:
        #     raise ValueError("at least one of 'color' or 'fill' must be given")
        color_str = ColorCode(color, "c")  # ensure proper color string
        fill_str = ColorCode(fill, "f")  # ensure proper fill string

        optcont = self.page._get_optional_content(oc)
        if optcont is not None:
            self.draw_cont = "/OC /%s BDC\n" % optcont + self.draw_cont
            emc = "EMC\n"
        else:
            emc = ""

        alpha = self.page._set_opacity(CA=stroke_opacity, ca=fill_opacity)
        if alpha is not None:
            self.draw_cont = "/%s gs\n" % alpha + self.draw_cont

        if width != 1 and width != 0:
            self.draw_cont += _format_g(width) + " w\n"

        if lineCap != 0:
            self.draw_cont = "%i J\n" % lineCap + self.draw_cont
        if lineJoin != 0:
            self.draw_cont = "%i j\n" % lineJoin + self.draw_cont

        if dashes not in (None, "", "[] 0"):
            self.draw_cont = "%s d\n" % dashes + self.draw_cont

        if closePath:
            self.draw_cont += "h\n"
            self.last_point = None

        if color is not None:
            self.draw_cont += color_str

        if fill is not None:
            self.draw_cont += fill_str
            if color is not None:
                if not even_odd:
                    self.draw_cont += "B\n"
                else:
                    self.draw_cont += "B*\n"
            else:
                if not even_odd:
                    self.draw_cont += "f\n"
                else:
                    self.draw_cont += "f*\n"
        else:
            self.draw_cont += "S\n"

        self.draw_cont += emc
        if CheckMorph(morph):
            m1 = Matrix(
                1, 0, 0, 1, morph[0].x + self.x, self.height - morph[0].y - self.y
            )
            mat = ~m1 * morph[1] * m1
            self.draw_cont = _format_g(JM_TUPLE(mat) + self.draw_cont) + " cm\n"

        self.totalcont += "\nq\n" + self.draw_cont + "Q\n"
        self.draw_cont = ""
        self.last_point = None
        return

    @staticmethod
    def horizontal_angle(C, P):
        """Return the angle to the horizontal for the connection from C to P.
        This uses the arcus sine function and resolves its inherent ambiguity by
        looking up in which quadrant vector S = P - C is located.
        """
        S = Point(P - C).unit  # unit vector 'C' -> 'P'
        alfa = math.asin(abs(S.y))  # absolute angle from horizontal
        if S.x < 0:  # make arcsin result unique
            if S.y <= 0:  # bottom-left
                alfa = -(math.pi - alfa)
            else:  # top-left
                alfa = math.pi - alfa
        else:
            if S.y >= 0:  # top-right
                pass
            else:  # bottom-right
                alfa = -alfa
        return alfa

    def insert_text(
            self,
            point: point_like,
            buffer_: typing.Union[str, list],
            fontsize: float = 11,
            lineheight: OptFloat = None,
            fontname: str = "helv",
            fontfile: OptStr = None,
            set_simple: bool = 0,
            encoding: int = 0,
            color: OptSeq = None,
            fill: OptSeq = None,
            render_mode: int = 0,
            border_width: float = 1,
            rotate: int = 0,
            morph: OptSeq = None,
            stroke_opacity: float = 1,
            fill_opacity: float = 1,
            oc: int = 0,
            ) -> int:
        # ensure 'text' is a list of strings, worth dealing with
        if not bool(buffer_):
            return 0

        if type(buffer_) not in (list, tuple):
            text = buffer_.splitlines()
        else:
            text = buffer_

        if not len(text) > 0:
            return 0

        point = Point(point)
        try:
            maxcode = max([ord(c) for c in " ".join(text)])
        except Exception:
            exception_info()
            return 0

        # ensure valid 'fontname'
        fname = fontname
        if fname.startswith("/"):
            fname = fname[1:]

        xref = self.page.insert_font(
                fontname=fname,
                fontfile=fontfile,
                encoding=encoding,
                set_simple=set_simple,
                )
        fontinfo = CheckFontInfo(self.doc, xref)

        fontdict = fontinfo[1]
        ordering = fontdict["ordering"]
        simple = fontdict["simple"]
        bfname = fontdict["name"]
        ascender = fontdict["ascender"]
        descender = fontdict["descender"]
        if lineheight:
            lheight = fontsize * lineheight
        elif ascender - descender <= 1:
            lheight = fontsize * 1.2
        else:
            lheight = fontsize * (ascender - descender)

        if maxcode > 255:
            glyphs = self.doc.get_char_widths(xref, maxcode + 1)
        else:
            glyphs = fontdict["glyphs"]

        tab = []
        for t in text:
            if simple and bfname not in ("Symbol", "ZapfDingbats"):
                g = None
            else:
                g = glyphs
            tab.append(getTJstr(t, g, simple, ordering))
        text = tab

        color_str = ColorCode(color, "c")
        fill_str = ColorCode(fill, "f")
        if not fill and render_mode == 0:  # ensure fill color when 0 Tr
            fill = color
            fill_str = ColorCode(color, "f")

        morphing = CheckMorph(morph)
        rot = rotate
        if rot % 90 != 0:
            raise ValueError("bad rotate value")

        while rot < 0:
            rot += 360
        rot = rot % 360  # text rotate = 0, 90, 270, 180

        templ1 = lambda a, b, c, d, e, f, g: f"\nq\n{a}{b}BT\n%{c}1 0 0 1 {_format_g((d, e))} Tm\n/{f} {g} Tf "
        templ2 = lambda a: f"TJ\n0 -{_format_g(a)} TD\n"
        cmp90 = "0 1 -1 0 0 0 cm\n"  # rotates 90 deg counter-clockwise
        cmm90 = "0 -1 1 0 0 0 cm\n"  # rotates 90 deg clockwise
        cm180 = "-1 0 0 -1 0 0 cm\n"  # rotates by 180 deg.
        height = self.height
        width = self.width

        # setting up for standard rotation directions
        # case rotate = 0
        if morphing:
            m1 = Matrix(1, 0, 0, 1, morph[0].x + self.x, height - morph[0].y - self.y)
            mat = ~m1 * morph[1] * m1
            cm = _format_g(JM_TUPLE(mat)) + " cm\n"
        else:
            cm = ""
        top = height - point.y - self.y  # start of 1st char
        left = point.x + self.x  # start of 1. char
        space = top  # space available
        if rot == 90:
            left = height - point.y - self.y
            top = -point.x - self.x
            cm += cmp90
            space = width - abs(top)

        elif rot == 270:
            left = -height + point.y + self.y
            top = point.x + self.x
            cm += cmm90
            space = abs(top)

        elif rot == 180:
            left = -point.x - self.x
            top = -height + point.y + self.y
            cm += cm180
            space = abs(point.y + self.y)

        optcont = self.page._get_optional_content(oc)
        if optcont is not None:
            bdc = "/OC /%s BDC\n" % optcont
            emc = "EMC\n"
        else:
            bdc = emc = ""

        alpha = self.page._set_opacity(CA=stroke_opacity, ca=fill_opacity)
        if alpha is None:
            alpha = ""
        else:
            alpha = "/%s gs\n" % alpha
        nres = templ1(bdc, alpha, cm, left, top, fname, fontsize)
        if render_mode > 0:
            nres += "%i Tr " % render_mode
        if border_width != 1:
            nres += _format_g(border_width) + " w "
        if color is not None:
            nres += color_str
        if fill is not None:
            nres += fill_str

        # =========================================================================
        #   start text insertion
        # =========================================================================
        nres += text[0]
        nlines = 1  # set output line counter
        if len(text) > 1:
            nres += templ2(lheight)  # line 1
        else:
            nres += 'TJ'
        for i in range(1, len(text)):
            if space < lheight:
                break  # no space left on page
            if i > 1:
                nres += "\nT* "
            nres += text[i] + 'TJ'
            space -= lheight
            nlines += 1

        nres += "\nET\n%sQ\n" % emc

        # =========================================================================
        #   end of text insertion
        # =========================================================================
        # update the /Contents object
        self.text_cont += nres
        return nlines

    def update_rect(self, x):
        if self.rect is None:
            if len(x) == 2:
                self.rect = Rect(x, x)
            else:
                self.rect = Rect(x)
        else:
            if len(x) == 2:
                x = Point(x)
                self.rect.x0 = min(self.rect.x0, x.x)
                self.rect.y0 = min(self.rect.y0, x.y)
                self.rect.x1 = max(self.rect.x1, x.x)
                self.rect.y1 = max(self.rect.y1, x.y)
            else:
                x = Rect(x)
                self.rect.x0 = min(self.rect.x0, x.x0)
                self.rect.y0 = min(self.rect.y0, x.y0)
                self.rect.x1 = max(self.rect.x1, x.x1)
                self.rect.y1 = max(self.rect.y1, x.y1)


class Story:

    def __init__( self, html='', user_css=None, em=12, archive=None):
        buffer_ = mupdf.fz_new_buffer_from_copied_data( html.encode('utf-8'))
        if archive and not isinstance(archive, Archive):
            archive = Archive(archive)
        arch = archive.this if archive else mupdf.FzArchive( None)
        if hasattr(mupdf, 'FzStoryS'):
            self.this = mupdf.FzStoryS( buffer_, user_css, em, arch)
        else:
            self.this = mupdf.FzStory( buffer_, user_css, em, arch)
    
    def add_header_ids(self):
        '''
        Look for `<h1..6>` items in `self` and adds unique `id`
        attributes if not already present.
        '''
        dom = self.body
        i = 0
        x = dom.find(None, None, None)
        while x:
            name = x.tagname
            if len(name) == 2 and name[0]=="h" and name[1] in "123456":
                attr = x.get_attribute_value("id")
                if not attr:
                    id_ = f"h_id_{i}"
                    #log(f"{name=}: setting {id_=}")
                    x.set_attribute("id", id_)
                    i += 1
            x = x.find_next(None, None, None)

    @staticmethod
    def add_pdf_links(document_or_stream, positions):
        """
        Adds links to PDF document.
        Args:
            document_or_stream:
                A PDF `Document` or raw PDF content, for example an
                `io.BytesIO` instance.
            positions:
                List of `ElementPosition`'s for `document_or_stream`,
                typically from Story.element_positions(). We raise an
                exception if two or more positions have same id.
        Returns:
            `document_or_stream` if a `Document` instance, otherwise a
            new `Document` instance.
        We raise an exception if an `href` in `positions` refers to an
        internal position `#<name>` but no item in `positions` has `id =
        name`.
        """
        if isinstance(document_or_stream, Document):
            document = document_or_stream
        else:
            document = Document("pdf", document_or_stream)

        # Create dict from id to position, which we will use to find
        # link destinations.
        #
        id_to_position = dict()
        #log(f"positions: {positions}")
        for position in positions:
            #log(f"add_pdf_links(): position: {position}")
            if (position.open_close & 1) and position.id:
                #log(f"add_pdf_links(): position with id: {position}")
                if position.id in id_to_position:
                    #log(f"Ignoring duplicate positions with id={position.id!r}")
                    pass
                else:
                    id_to_position[ position.id] = position

        # Insert links for all positions that have an `href`.
        #
        for position_from in positions:
        
            if (position_from.open_close & 1) and position_from.href:
            
                #log(f"add_pdf_links(): position with href: {position}")
                link = dict()
                link['from'] = Rect(position_from.rect)
                
                if position_from.href.startswith("#"):
                    #`<a href="#...">...</a>` internal link.
                    target_id = position_from.href[1:]
                    try:
                        position_to = id_to_position[ target_id]
                    except Exception as e:
                        if g_exceptions_verbose > 1:    exception_info()
                        raise RuntimeError(f"No destination with id={target_id}, required by position_from: {position_from}") from e
                    # Make link from `position_from`'s rect to top-left of
                    # `position_to`'s rect.
                    if 0:
                        log(f"add_pdf_links(): making link from:")
                        log(f"add_pdf_links():    {position_from}")
                        log(f"add_pdf_links(): to:")
                        log(f"add_pdf_links():    {position_to}")
                    link["kind"] = LINK_GOTO
                    x0, y0, x1, y1 = position_to.rect
                    # This appears to work well with viewers which scroll
                    # to make destination point top-left of window.
                    link["to"] = Point(x0, y0)
                    link["page"] = position_to.page_num - 1
                    
                else:
                    # `<a href="...">...</a>` external link.
                    if position_from.href.startswith('name:'):
                        link['kind'] = LINK_NAMED
                        link['name'] = position_from.href[5:]
                    else:
                        link['kind'] = LINK_URI
                        link['uri'] = position_from.href
                
                #log(f'Adding link: {position_from.page_num=} {link=}.')
                document[position_from.page_num - 1].insert_link(link)
        
        return document

    @property
    def body(self):
        dom = self.document()
        return dom.bodytag()
        
    def document( self):
        dom = mupdf.fz_story_document( self.this)
        return Xml( dom)

    def draw( self, device, matrix=None):
        ctm2 = JM_matrix_from_py( matrix)
        dev = device.this if device else mupdf.FzDevice( None)
        mupdf.fz_draw_story( self.this, dev, ctm2)

    def element_positions( self, function, args=None):
        '''
        Trigger a callback function to record where items have been placed.
        '''
        if type(args) is dict:
            for k in args.keys():
                if not (type(k) is str and k.isidentifier()):
                    raise ValueError(f"invalid key '{k}'")
        else:
            args = {}
        if not callable(function) or function.__code__.co_argcount != 1:
            raise ValueError("callback 'function' must be a callable with exactly one argument")
        
        def function2( position):
            class Position2:
                pass
            position2 = Position2()
            position2.depth = position.depth
            position2.heading = position.heading
            position2.id = position.id
            position2.rect = JM_py_from_rect(position.rect)
            position2.text = position.text
            position2.open_close = position.open_close
            position2.rect_num = position.rectangle_num
            position2.href = position.href
            if args:
                for k, v in args.items():
                    setattr( position2, k, v)
            function( position2)
        mupdf.fz_story_positions( self.this, function2)

    def place( self, where):
        where = JM_rect_from_py( where)
        filled = mupdf.FzRect()
        more = mupdf.fz_place_story( self.this, where, filled)
        return more, JM_py_from_rect( filled)

    def reset( self):
        mupdf.fz_reset_story( self.this)
    
    def write(self, writer, rectfn, positionfn=None, pagefn=None):
        dev = None
        page_num = 0
        rect_num = 0
        filled = Rect(0, 0, 0, 0)
        while 1:
            mediabox, rect, ctm = rectfn(rect_num, filled)
            rect_num += 1
            if mediabox:
                # new page.
                page_num += 1
            more, filled = self.place( rect)
            if positionfn:
                def positionfn2(position):
                    # We add a `.page_num` member to the
                    # `ElementPosition` instance.
                    position.page_num = page_num
                    positionfn(position)
                self.element_positions(positionfn2)
            if writer:
                if mediabox:
                    # new page.
                    if dev:
                        if pagefn:
                            pagefn(page_num, mediabox, dev, 1)
                        writer.end_page()
                    dev = writer.begin_page( mediabox)
                    if pagefn:
                        pagefn(page_num, mediabox, dev, 0)
                self.draw( dev, ctm)
                if not more:
                    if pagefn:
                        pagefn( page_num, mediabox, dev, 1)
                    writer.end_page()
            else:
                self.draw(None, ctm)
            if not more:
                break

    @staticmethod
    def write_stabilized(writer, contentfn, rectfn, user_css=None, em=12, positionfn=None, pagefn=None, archive=None, add_header_ids=True):
        positions = list()
        content = None
        # Iterate until stable.
        while 1:
            content_prev = content
            content = contentfn( positions)
            stable = False
            if content == content_prev:
                stable = True
            content2 = content
            story = Story(content2, user_css, em, archive)

            if add_header_ids:
                story.add_header_ids()

            positions = list()
            def positionfn2(position):
                #log(f"write_stabilized(): {stable=} {positionfn=} {position=}")
                positions.append(position)
                if stable and positionfn:
                    positionfn(position)
            story.write(
                    writer if stable else None,
                    rectfn,
                    positionfn2,
                    pagefn,
                    )
            if stable:
                break

    @staticmethod
    def write_stabilized_with_links(contentfn, rectfn, user_css=None, em=12, positionfn=None, pagefn=None, archive=None, add_header_ids=True):
        #log("write_stabilized_with_links()")
        stream = io.BytesIO()
        writer = DocumentWriter(stream)
        positions = []
        def positionfn2(position):
            #log(f"write_stabilized_with_links(): {position=}")
            positions.append(position)
            if positionfn:
                positionfn(position)
        Story.write_stabilized(writer, contentfn, rectfn, user_css, em, positionfn2, pagefn, archive, add_header_ids)
        writer.close()
        stream.seek(0)
        return Story.add_pdf_links(stream, positions)

    def write_with_links(self, rectfn, positionfn=None, pagefn=None):
        #log("write_with_links()")
        stream = io.BytesIO()
        writer = DocumentWriter(stream)
        positions = []
        def positionfn2(position):
            #log(f"write_with_links(): {position=}")
            positions.append(position)
            if positionfn:
                positionfn(position)
        self.write(writer, rectfn, positionfn=positionfn2, pagefn=pagefn)
        writer.close()
        stream.seek(0)
        return Story.add_pdf_links(stream, positions)

    class FitResult:
        '''
        The result from a `Story.fit*()` method.
        
        Members:
        
        `big_enough`:
            `True` if the fit succeeded.
        `filled`:
            From the last call to `Story.place()`.
        `more`:
            `False` if the fit succeeded.
        `numcalls`:
            Number of calls made to `self.place()`.
        `parameter`:
            The successful parameter value, or the largest failing value.
        `rect`:
            The rect created from `parameter`.
        '''
        def __init__(self, big_enough=None, filled=None, more=None, numcalls=None, parameter=None, rect=None):
            self.big_enough = big_enough
            self.filled = filled
            self.more = more
            self.numcalls = numcalls
            self.parameter = parameter
            self.rect = rect
        
        def __repr__(self):
            return (
                    f' big_enough={self.big_enough}'
                    f' filled={self.filled}'
                    f' more={self.more}'
                    f' numcalls={self.numcalls}'
                    f' parameter={self.parameter}'
                    f' rect={self.rect}'
                    )

    def fit(self, fn, pmin=None, pmax=None, delta=0.001, verbose=False):
        '''
        Finds optimal rect that contains the story `self`.
        
        Returns a `Story.FitResult` instance.
            
        On success, the last call to `self.place()` will have been with the
        returned rectangle, so `self.draw()` can be used directly.
        
        Args:
        :arg fn:
            A callable taking a floating point `parameter` and returning a
            `pymupdf.Rect()`. If the rect is empty, we assume the story will
            not fit and do not call `self.place()`.

            Must guarantee that `self.place()` behaves monotonically when
            given rect `fn(parameter`) as `parameter` increases. This
            usually means that both width and height increase or stay
            unchanged as `parameter` increases.
        :arg pmin:
            Minimum parameter to consider; `None` for -infinity.
        :arg pmax:
            Maximum parameter to consider; `None` for +infinity.
        :arg delta:
            Maximum error in returned `parameter`.
        :arg verbose:
            If true we output diagnostics.
        '''
        def log(text):
            assert verbose
            message(f'fit(): {text}')
        
        assert isinstance(pmin, (int, float)) or pmin is None
        assert isinstance(pmax, (int, float)) or pmax is None
        
        class State:
            def __init__(self):
                self.pmin = pmin
                self.pmax = pmax
                self.pmin_result = None
                self.pmax_result = None
                self.result = None
                self.numcalls = 0
                if verbose:
                    self.pmin0 = pmin
                    self.pmax0 = pmax
        state = State()
        
        if verbose:
            log(f'starting. {state.pmin=} {state.pmax=}.')
        
        self.reset()

        def ret():
            if state.pmax is not None:
                if state.last_p != state.pmax:
                    if verbose:
                        log(f'Calling update() with pmax, because was overwritten by later calls.')
                    big_enough = update(state.pmax)
                    assert big_enough
                result = state.pmax_result
            else:
                result = state.pmin_result if state.pmin_result else Story.FitResult(numcalls=state.numcalls)
            if verbose:
                log(f'finished. {state.pmin0=} {state.pmax0=} {state.pmax=}: returning {result=}')
            return result
        
        def update(parameter):
            '''
            Evaluates `more, _ = self.place(fn(parameter))`. If `more` is
            false, then `rect` is big enough to contain `self` and we
            set `state.pmax=parameter` and return True. Otherwise we set
            `state.pmin=parameter` and return False.
            '''
            rect = fn(parameter)
            assert isinstance(rect, Rect), f'{type(rect)=} {rect=}'
            if rect.is_empty:
                big_enough = False
                result = Story.FitResult(parameter=parameter, numcalls=state.numcalls)
                if verbose:
                    log(f'update(): not calling self.place() because rect is empty.')
            else:
                more, filled = self.place(rect)
                state.numcalls += 1
                big_enough = not more
                result = Story.FitResult(
                        filled=filled,
                        more=more,
                        numcalls=state.numcalls,
                        parameter=parameter,
                        rect=rect,
                        big_enough=big_enough,
                        )
                if verbose:
                    log(f'update(): called self.place(): {state.numcalls:>2d}: {more=} {parameter=} {rect=}.')
            if big_enough:
                state.pmax = parameter
                state.pmax_result = result
            else:
                state.pmin = parameter
                state.pmin_result = result
            state.last_p = parameter
            return big_enough

        def opposite(p, direction):
            '''
            Returns same sign as `direction`, larger or smaller than `p` if
            direction is positive or negative respectively.
            '''
            if p is None or p==0:
                return direction
            if direction * p > 0:
                return 2 * p
            return -p
            
        if state.pmin is None:
            # Find an initial finite pmin value.
            if verbose: log(f'finding pmin.')
            parameter = opposite(state.pmax, -1)
            while 1:
                if not update(parameter):
                    break
                parameter *= 2
        else:
            if update(state.pmin):
                if verbose: log(f'{state.pmin=} is big enough.')
                return ret()
        
        if state.pmax is None:
            # Find an initial finite pmax value.
            if verbose: log(f'finding pmax.')
            parameter = opposite(state.pmin, +1)
            while 1:
                if update(parameter):
                    break
                parameter *= 2
        else:
            if not update(state.pmax):
                # No solution possible.
                state.pmax = None
                if verbose: log(f'No solution possible {state.pmax=}.')
                return ret()
        
        # Do binary search in pmin..pmax.
        if verbose: log(f'doing binary search with {state.pmin=} {state.pmax=}.')
        while 1:
            if state.pmax - state.pmin < delta:
                return ret()
            parameter = (state.pmin + state.pmax) / 2
            update(parameter)

    def fit_scale(self, rect, scale_min=0, scale_max=None, delta=0.001, verbose=False):
        '''
        Finds smallest value `scale` in range `scale_min..scale_max` where
        `scale * rect` is large enough to contain the story `self`.

        Returns a `Story.FitResult` instance.

        :arg width:
            width of rect.
        :arg height:
            height of rect.
        :arg scale_min:
            Minimum scale to consider; must be >= 0.
        :arg scale_max:
            Maximum scale to consider, must be >= scale_min or `None` for
            infinite.
        :arg delta:
            Maximum error in returned scale.
        :arg verbose:
            If true we output diagnostics.
        '''
        x0, y0, x1, y1 = rect
        width = x1 - x0
        height = y1 - y0
        def fn(scale):
            return Rect(x0, y0, x0 + scale*width, y0 + scale*height)
        return self.fit(fn, scale_min, scale_max, delta, verbose)

    def fit_height(self, width, height_min=0, height_max=None, origin=(0, 0), delta=0.001, verbose=False):
        '''
        Finds smallest height in range `height_min..height_max` where a rect
        with size `(width, height)` is large enough to contain the story
        `self`.

        Returns a `Story.FitResult` instance.

        :arg width:
            width of rect.
        :arg height_min:
            Minimum height to consider; must be >= 0.
        :arg height_max:
            Maximum height to consider, must be >= height_min or `None` for
            infinite.
        :arg origin:
            `(x0, y0)` of rect.
        :arg delta:
            Maximum error in returned height.
        :arg verbose:
            If true we output diagnostics.
        '''
        x0, y0 = origin
        x1 = x0 + width
        def fn(height):
            return Rect(x0, y0, x1, y0+height)
        return self.fit(fn, height_min, height_max, delta, verbose)

    def fit_width(self, height, width_min=0, width_max=None, origin=(0, 0), delta=0.001, verbose=False):
        '''
        Finds smallest width in range `width_min..width_max` where a rect with size
        `(width, height)` is large enough to contain the story `self`.

        Returns a `Story.FitResult` instance.
        Returns a `FitResult` instance.

        :arg height:
            height of rect.
        :arg width_min:
            Minimum width to consider; must be >= 0.
        :arg width_max:
            Maximum width to consider, must be >= width_min or `None` for
            infinite.
        :arg origin:
            `(x0, y0)` of rect.
        :arg delta:
            Maximum error in returned width.
        :arg verbose:
            If true we output diagnostics.
        '''
        x0, y0 = origin
        y1 = y0 + height
        def fn(width):
            return Rect(x0, y0, x0+width, y1)
        return self.fit(fn, width_min, width_max, delta, verbose)


class TextPage:

    def __init__(self, *args):
        if args_match(args, mupdf.FzRect):
            mediabox = args[0]
            self.this = mupdf.FzStextPage( mediabox)
        elif args_match(args, mupdf.FzStextPage):
            self.this = args[0]
        else:
            raise Exception(f'Unrecognised args: {args}')
        self.thisown = True
        self.parent = None

    def _extractText(self, format_):
        this_tpage = self.this
        res = mupdf.fz_new_buffer(1024)
        out = mupdf.FzOutput( res)
        # fixme: mupdfwrap.py thinks fz_output is not copyable, possibly
        # because there is no .refs member visible and no fz_keep_output() fn,
        # although there is an fz_drop_output(). So mupdf.fz_new_output_with_buffer()
        # doesn't convert the returned fz_output* into a mupdf.FzOutput.
        #out = mupdf.FzOutput(out)
        if format_ == 1:
            mupdf.fz_print_stext_page_as_html(out, this_tpage, 0)
        elif format_ == 3:
            mupdf.fz_print_stext_page_as_xml(out, this_tpage, 0)
        elif format_ == 4:
            mupdf.fz_print_stext_page_as_xhtml(out, this_tpage, 0)
        else:
            JM_print_stext_page_as_text(res, this_tpage)
        out.fz_close_output()
        text = JM_EscapeStrFromBuffer(res)
        return text

    def _getNewBlockList(self, page_dict, raw):
        JM_make_textpage_dict(self.this, page_dict, raw)

    def _textpage_dict(self, raw=False):
        page_dict = {"width": self.rect.width, "height": self.rect.height}
        self._getNewBlockList(page_dict, raw)
        return page_dict

    def extractBLOCKS(self):
        """Return a list with text block information."""
        if g_use_extra:
            return extra.extractBLOCKS(self.this)
        block_n = -1
        this_tpage = self.this
        tp_rect = mupdf.FzRect(this_tpage.m_internal.mediabox)
        res = mupdf.fz_new_buffer(1024)
        lines = []
        for block in this_tpage:
            block_n += 1
            blockrect = mupdf.FzRect(mupdf.FzRect.Fixed_EMPTY)
            if block.m_internal.type == mupdf.FZ_STEXT_BLOCK_TEXT:
                mupdf.fz_clear_buffer(res) # set text buffer to empty
                line_n = -1
                last_char = 0
                for line in block:
                    line_n += 1
                    linerect = mupdf.FzRect(mupdf.FzRect.Fixed_EMPTY)
                    for ch in line:
                        cbbox = JM_char_bbox(line, ch)
                        if (not JM_rects_overlap(tp_rect, cbbox)
                                and not mupdf.fz_is_infinite_rect(tp_rect)
                                ):
                            continue
                        JM_append_rune(res, ch.m_internal.c)
                        last_char = ch.m_internal.c
                        linerect = mupdf.fz_union_rect(linerect, cbbox)
                    if last_char != 10 and not mupdf.fz_is_empty_rect(linerect):
                        mupdf.fz_append_byte(res, 10)
                    blockrect = mupdf.fz_union_rect(blockrect, linerect)
                text = JM_EscapeStrFromBuffer(res)
            elif (JM_rects_overlap(tp_rect, block.m_internal.bbox)
                    or mupdf.fz_is_infinite_rect(tp_rect)
                    ):
                img = block.i_image()
                cs = img.colorspace()
                text = "<image: %s, width: %d, height: %d, bpc: %d>" % (
                        mupdf.fz_colorspace_name(cs),
                        img.w(), img.h(), img.bpc()
                        )
                blockrect = mupdf.fz_union_rect(blockrect, mupdf.FzRect(block.m_internal.bbox))
            if not mupdf.fz_is_empty_rect(blockrect):
                litem = (
                        blockrect.x0,
                        blockrect.y0,
                        blockrect.x1,
                        blockrect.y1,
                        text,
                        block_n,
                        block.m_internal.type,
                        )
                lines.append(litem)
        return lines

    def extractDICT(self, cb=None, sort=False) -> dict:
        """Return page content as a Python dict of images and text spans."""
        val = self._textpage_dict(raw=False)
        if cb is not None:
            val["width"] = cb.width
            val["height"] = cb.height
        if sort:
            blocks = val["blocks"]
            blocks.sort(key=lambda b: (b["bbox"][3], b["bbox"][0]))
            val["blocks"] = blocks
        return val

    def extractHTML(self) -> str:
        """Return page content as a HTML string."""
        return self._extractText(1)

    def extractIMGINFO(self, hashes=0):
        """Return a list with image meta information."""
        block_n = -1
        this_tpage = self.this
        rc = []
        for block in this_tpage:
            block_n += 1
            if block.m_internal.type == mupdf.FZ_STEXT_BLOCK_TEXT:
                continue
            img = block.i_image()
            img_size = 0
            mask = img.mask()
            if mask.m_internal:
                has_mask = True
            else:
                has_mask = False
            compr_buff = mupdf.fz_compressed_image_buffer(img)
            if compr_buff.m_internal:
                img_size = compr_buff.fz_compressed_buffer_size()
                compr_buff = None
            if hashes:
                r = mupdf.FzIrect(FZ_MIN_INF_RECT, FZ_MIN_INF_RECT, FZ_MAX_INF_RECT, FZ_MAX_INF_RECT)
                assert mupdf.fz_is_infinite_irect(r)
                m = mupdf.FzMatrix(img.w(), 0, 0, img.h(), 0, 0)
                pix, w, h = mupdf.fz_get_pixmap_from_image(img, r, m)
                digest = mupdf.fz_md5_pixmap2(pix)
                digest = bytes(digest)
                if img_size == 0:
                    img_size = img.w() * img.h() * img.n()
            cs = mupdf.FzColorspace(mupdf.ll_fz_keep_colorspace(img.m_internal.colorspace))
            block_dict = dict()
            block_dict[dictkey_number] = block_n
            block_dict[dictkey_bbox] = JM_py_from_rect(block.m_internal.bbox)
            block_dict[dictkey_matrix] = JM_py_from_matrix(block.i_transform())
            block_dict[dictkey_width] = img.w()
            block_dict[dictkey_height] = img.h()
            block_dict[dictkey_colorspace] = mupdf.fz_colorspace_n(cs)
            block_dict[dictkey_cs_name] = mupdf.fz_colorspace_name(cs)
            block_dict[dictkey_xres] = img.xres()
            block_dict[dictkey_yres] = img.yres()
            block_dict[dictkey_bpc] = img.bpc()
            block_dict[dictkey_size] = img_size
            if hashes:
                block_dict["digest"] = digest
            block_dict["has-mask"] = has_mask
            rc.append(block_dict)
        return rc

    def extractJSON(self, cb=None, sort=False) -> str:
        """Return 'extractDICT' converted to JSON format."""
        import base64
        import json
        val = self._textpage_dict(raw=False)

        class b64encode(json.JSONEncoder):
            def default(self, s):
                if type(s) in (bytes, bytearray):
                    return base64.b64encode(s).decode()

        if cb is not None:
            val["width"] = cb.width
            val["height"] = cb.height
        if sort:
            blocks = val["blocks"]
            blocks.sort(key=lambda b: (b["bbox"][3], b["bbox"][0]))
            val["blocks"] = blocks
        
        val = json.dumps(val, separators=(",", ":"), cls=b64encode, indent=1)
        return val

    def extractRAWDICT(self, cb=None, sort=False) -> dict:
        """Return page content as a Python dict of images and text characters."""
        val = self._textpage_dict(raw=True)
        if cb is not None:
            val["width"] = cb.width
            val["height"] = cb.height
        if sort:
            blocks = val["blocks"]
            blocks.sort(key=lambda b: (b["bbox"][3], b["bbox"][0]))
            val["blocks"] = blocks
        return val

    def extractRAWJSON(self, cb=None, sort=False) -> str:
        """Return 'extractRAWDICT' converted to JSON format."""
        import base64
        import json
        val = self._textpage_dict(raw=True)

        class b64encode(json.JSONEncoder):
            def default(self,s):
                if type(s) in (bytes, bytearray):
                    return base64.b64encode(s).decode()

        if cb is not None:
            val["width"] = cb.width
            val["height"] = cb.height
        if sort:
            blocks = val["blocks"]
            blocks.sort(key=lambda b: (b["bbox"][3], b["bbox"][0]))
            val["blocks"] = blocks
        val = json.dumps(val, separators=(",", ":"), cls=b64encode, indent=1)
        return val

    def extractSelection(self, pointa, pointb):
        a = JM_point_from_py(pointa)
        b = JM_point_from_py(pointb)
        found = mupdf.fz_copy_selection(self.this, a, b, 0)
        return found

    def extractText(self, sort=False) -> str:
        """Return simple, bare text on the page."""
        if not sort:
            return self._extractText(0)
        blocks = self.extractBLOCKS()[:]
        blocks.sort(key=lambda b: (b[3], b[0]))
        return "".join([b[4] for b in blocks])

    def extractTextbox(self, rect):
        this_tpage = self.this
        assert isinstance(this_tpage, mupdf.FzStextPage)
        area = JM_rect_from_py(rect)
        found = JM_copy_rectangle(this_tpage, area)
        rc = PyUnicode_DecodeRawUnicodeEscape(found)
        return rc

    def extractWORDS(self, delimiters=None):
        """Return a list with text word information."""
        if g_use_extra:
            return extra.extractWORDS(self.this, delimiters)
        buflen = 0
        last_char_rtl = 0
        block_n = -1
        wbbox = mupdf.FzRect(mupdf.FzRect.Fixed_EMPTY)  # word bbox
        this_tpage = self.this
        tp_rect = mupdf.FzRect(this_tpage.m_internal.mediabox)

        lines = None
        buff = mupdf.fz_new_buffer(64)
        lines = []
        for block in this_tpage:
            block_n += 1
            if block.m_internal.type != mupdf.FZ_STEXT_BLOCK_TEXT:
                continue
            line_n = -1
            for line in block:
                line_n += 1
                word_n = 0                  # word counter per line
                mupdf.fz_clear_buffer(buff) # reset word buffer
                buflen = 0                  # reset char counter
                for ch in line:
                    cbbox = JM_char_bbox(line, ch)
                    if (not JM_rects_overlap(tp_rect, cbbox)
                            and not mupdf.fz_is_infinite_rect(tp_rect)
                            ):
                        continue
                    word_delimiter = JM_is_word_delimiter(ch.m_internal.c, delimiters)
                    this_char_rtl = JM_is_rtl_char(ch.m_internal.c)
                    if word_delimiter or this_char_rtl != last_char_rtl:
                        if buflen == 0 and word_delimiter:
                            continue    # skip delimiters at line start
                        if not mupdf.fz_is_empty_rect(wbbox):
                            word_n, wbbox = JM_append_word(lines, buff, wbbox, block_n, line_n, word_n)
                        mupdf.fz_clear_buffer(buff)
                        buflen = 0  # reset char counter
                        if word_delimiter:
                            continue
                    # append one unicode character to the word
                    JM_append_rune(buff, ch.m_internal.c)
                    last_char_rtl = this_char_rtl
                    buflen += 1
                    # enlarge word bbox
                    wbbox = mupdf.fz_union_rect(wbbox, JM_char_bbox(line, ch))
                if buflen and not mupdf.fz_is_empty_rect(wbbox):
                    word_n, wbbox = JM_append_word(lines, buff, wbbox, block_n, line_n, word_n)
                buflen = 0
        return lines

    def extractXHTML(self) -> str:
        """Return page content as a XHTML string."""
        return self._extractText(4)

    def extractXML(self) -> str:
        """Return page content as a XML string."""
        return self._extractText(3)

    def poolsize(self):
        """TextPage current poolsize."""
        tpage = self.this
        pool = mupdf.Pool(tpage.m_internal.pool)
        size = mupdf.fz_pool_size( pool)
        pool.m_internal = None  # Ensure that pool's destructor does not free the pool.
        return size

    @property
    def rect(self):
        """Page rectangle."""
        this_tpage = self.this
        mediabox = this_tpage.m_internal.mediabox
        val = JM_py_from_rect(mediabox)
        val = Rect(val)

        return val

    def search(self, needle, hit_max=0, quads=1):
        """Locate 'needle' returning rects or quads."""
        val = JM_search_stext_page(self.this, needle)
        if not val:
            return val
        items = len(val)
        for i in range(items):  # change entries to quads or rects
            q = Quad(val[i])
            if quads:
                val[i] = q
            else:
                val[i] = q.rect
        if quads:
            return val
        i = 0  # join overlapping rects on the same line
        while i < items - 1:
            v1 = val[i]
            v2 = val[i + 1]
            if v1.y1 != v2.y1 or (v1 & v2).is_empty:
                i += 1
                continue  # no overlap on same line
            val[i] = v1 | v2  # join rectangles
            del val[i + 1]  # remove v2
            items -= 1  # reduce item count
        return val

    extractTEXT = extractText


class TextWriter:

    def __init__(self, page_rect, opacity=1, color=None):
        """Stores text spans for later output on compatible PDF pages."""
        self.this = mupdf.fz_new_text()

        self.opacity = opacity
        self.color = color
        self.rect = Rect(page_rect)
        self.ctm = Matrix(1, 0, 0, -1, 0, self.rect.height)
        self.ictm = ~self.ctm
        self.last_point = Point()
        self.last_point.__doc__ = "Position following last text insertion."
        self.text_rect = Rect()
        
        self.text_rect.__doc__ = "Accumulated area of text spans."
        self.used_fonts = set()
        self.thisown = True

    @property
    def _bbox(self):
        val = JM_py_from_rect( mupdf.fz_bound_text( self.this, mupdf.FzStrokeState(None), mupdf.FzMatrix()))
        val = Rect(val)
        return val

    def append(self, pos, text, font=None, fontsize=11, language=None, right_to_left=0, small_caps=0):
        """Store 'text' at point 'pos' using 'font' and 'fontsize'."""
        pos = Point(pos) * self.ictm
        #log( '{font=}')
        if font is None:
            font = Font("helv")
        if not font.is_writable:
            if 0:
                log( '{font.this.m_internal.name=}')
                log( '{font.this.m_internal.t3matrix=}')
                log( '{font.this.m_internal.bbox=}')
                log( '{font.this.m_internal.glyph_count=}')
                log( '{font.this.m_internal.use_glyph_bbox=}')
                log( '{font.this.m_internal.width_count=}')
                log( '{font.this.m_internal.width_default=}')
                log( '{font.this.m_internal.has_digest=}')
                log( 'Unsupported font {font.name=}')
                if mupdf_cppyy:
                    import cppyy
                    log( f'Unsupported font {cppyy.gbl.mupdf_font_name(font.this.m_internal)=}')
            raise ValueError("Unsupported font '%s'." % font.name)
        if right_to_left:
            text = self.clean_rtl(text)
            text = "".join(reversed(text))
            right_to_left = 0

        lang = mupdf.fz_text_language_from_string(language)
        p = JM_point_from_py(pos)
        trm = mupdf.fz_make_matrix(fontsize, 0, 0, fontsize, p.x, p.y)
        markup_dir = 0
        wmode = 0
        if small_caps == 0:
            trm = mupdf.fz_show_string( self.this, font.this, trm, text, wmode, right_to_left, markup_dir, lang)
        else:
            trm = JM_show_string_cs( self.this, font.this, trm, text, wmode, right_to_left, markup_dir, lang)
        val = JM_py_from_matrix(trm)

        self.last_point = Point(val[-2:]) * self.ctm
        self.text_rect = self._bbox * self.ctm
        val = self.text_rect, self.last_point
        if font.flags["mono"] == 1:
            self.used_fonts.add(font)
        return val

    def appendv(self, pos, text, font=None, fontsize=11, language=None, small_caps=False):
        lheight = fontsize * 1.2
        for c in text:
            self.append(pos, c, font=font, fontsize=fontsize,
                language=language, small_caps=small_caps)
            pos.y += lheight
        return self.text_rect, self.last_point

    def clean_rtl(self, text):
        """Revert the sequence of Latin text parts.

        Text with right-to-left writing direction (Arabic, Hebrew) often
        contains Latin parts, which are written in left-to-right: numbers, names,
        etc. For output as PDF text we need *everything* in right-to-left.
        E.g. an input like "<arabic> ABCDE FG HIJ <arabic> KL <arabic>" will be
        converted to "<arabic> JIH GF EDCBA <arabic> LK <arabic>". The Arabic
        parts remain untouched.

        Args:
            text: str
        Returns:
            Massaged string.
        """
        if not text:
            return text
        # split into words at space boundaries
        words = text.split(" ")
        idx = []
        for i in range(len(words)):
            w = words[i]
        # revert character sequence for Latin only words
            if not (len(w) < 2 or max([ord(c) for c in w]) > 255):
                words[i] = "".join(reversed(w))
                idx.append(i)  # stored index of Latin word

        # adjacent Latin words must revert their sequence, too
        idx2 = []  # store indices of adjacent Latin words
        for i in range(len(idx)):
            if idx2 == []:  # empty yet?
                idx2.append(idx[i]) # store Latin word number

            elif idx[i] > idx2[-1] + 1:  # large gap to last?
                if len(idx2) > 1:  # at least two consecutives?
                    words[idx2[0] : idx2[-1] + 1] = reversed(
                        words[idx2[0] : idx2[-1] + 1]
                    )  # revert their sequence
                idx2 = [idx[i]]  # re-initialize

            elif idx[i] == idx2[-1] + 1:  # new adjacent Latin word
                idx2.append(idx[i])

        text = " ".join(words)
        return text

    def write_text(self, page, color=None, opacity=-1, overlay=1, morph=None, matrix=None, render_mode=0, oc=0):
        """Write the text to a PDF page having the TextWriter's page size.

        Args:
            page: a PDF page having same size.
            color: override text color.
            opacity: override transparency.
            overlay: put in foreground or background.
            morph: tuple(Point, Matrix), apply a matrix with a fixpoint.
            matrix: Matrix to be used instead of 'morph' argument.
            render_mode: (int) PDF render mode operator 'Tr'.
        """
        CheckParent(page)
        if abs(self.rect - page.rect) > 1e-3:
            raise ValueError("incompatible page rect")
        if morph is not None:
            if (type(morph) not in (tuple, list)
                    or type(morph[0]) is not Point
                    or type(morph[1]) is not Matrix
                    ):
                raise ValueError("morph must be (Point, Matrix) or None")
        if matrix is not None and morph is not None:
            raise ValueError("only one of matrix, morph is allowed")
        if getattr(opacity, "__float__", None) is None or opacity == -1:
            opacity = self.opacity
        if color is None:
            color = self.color

        if 1:
            pdfpage = page._pdf_page()
            alpha = 1
            if opacity >= 0 and opacity < 1:
                alpha = opacity
            ncol = 1
            dev_color = [0, 0, 0, 0]
            if color:
                ncol, dev_color = JM_color_FromSequence(color)
            if ncol == 3:
                colorspace = mupdf.fz_device_rgb()
            elif ncol == 4:
                colorspace = mupdf.fz_device_cmyk()
            else:
                colorspace = mupdf.fz_device_gray()

            resources = mupdf.pdf_new_dict(pdfpage.doc(), 5)
            contents = mupdf.fz_new_buffer(1024)
            dev = mupdf.pdf_new_pdf_device( pdfpage.doc(), mupdf.FzMatrix(), resources, contents)
            #log( '=== {dev_color!r=}')
            mupdf.fz_fill_text(
                    dev,
                    self.this,
                    mupdf.FzMatrix(),
                    colorspace,
                    dev_color,
                    alpha,
                    mupdf.FzColorParams(mupdf.fz_default_color_params),
                    )
            mupdf.fz_close_device( dev)

            # copy generated resources into the one of the page
            max_nums = JM_merge_resources( pdfpage, resources)
            cont_string = JM_EscapeStrFromBuffer( contents)
            result = (max_nums, cont_string)
            val = result

        max_nums = val[0]
        content = val[1]
        max_alp, max_font = max_nums
        old_cont_lines = content.splitlines()

        optcont = page._get_optional_content(oc)
        if optcont is not None:
            bdc = "/OC /%s BDC" % optcont
            emc = "EMC"
        else:
            bdc = emc = ""

        new_cont_lines = ["q"]
        if bdc:
            new_cont_lines.append(bdc)

        cb = page.cropbox_position
        if page.rotation in (90, 270):
            delta = page.rect.height - page.rect.width
        else:
            delta = 0
        mb = page.mediabox
        if bool(cb) or mb.y0 != 0 or delta != 0:
            new_cont_lines.append(f"1 0 0 1 {_format_g((cb.x, cb.y + mb.y0 - delta))} cm")

        if morph:
            p = morph[0] * self.ictm
            delta = Matrix(1, 1).pretranslate(p.x, p.y)
            matrix = ~delta * morph[1] * delta
        if morph or matrix:
            new_cont_lines.append(_format_g(JM_TUPLE(matrix)) + " cm")

        for line in old_cont_lines:
            if line.endswith(" cm"):
                continue
            if line == "BT":
                new_cont_lines.append(line)
                new_cont_lines.append("%i Tr" % render_mode)
                continue
            if line.endswith(" gs"):
                alp = int(line.split()[0][4:]) + max_alp
                line = "/Alp%i gs" % alp
            elif line.endswith(" Tf"):
                temp = line.split()
                fsize = float(temp[1])
                if render_mode != 0:
                    w = fsize * 0.05
                else:
                    w = 1
                new_cont_lines.append(_format_g(w) + " w")
                font = int(temp[0][2:]) + max_font
                line = " ".join(["/F%i" % font] + temp[1:])
            elif line.endswith(" rg"):
                new_cont_lines.append(line.replace("rg", "RG"))
            elif line.endswith(" g"):
                new_cont_lines.append(line.replace(" g", " G"))
            elif line.endswith(" k"):
                new_cont_lines.append(line.replace(" k", " K"))
            new_cont_lines.append(line)
        if emc:
            new_cont_lines.append(emc)
        new_cont_lines.append("Q\n")
        content = "\n".join(new_cont_lines).encode("utf-8")
        TOOLS._insert_contents(page, content, overlay=overlay)
        val = None
        for font in self.used_fonts:
            repair_mono_font(page, font)
        return val


class IRect:
    """
    IRect() - all zeros
    IRect(x0, y0, x1, y1) - 4 coordinates
    IRect(top-left, x1, y1) - point and 2 coordinates
    IRect(x0, y0, bottom-right) - 2 coordinates and point
    IRect(top-left, bottom-right) - 2 points
    IRect(sequ) - new from sequence or rect-like
    """

    def __add__(self, p):
        return Rect.__add__(self, p).round()

    def __and__(self, x):
        return Rect.__and__(self, x).round()

    def __contains__(self, x):
        return Rect.__contains__(self, x)

    def __eq__(self, r):
        if not hasattr(r, "__len__"):
            return False
        return len(r) == 4 and self.x0 == r[0] and self.y0 == r[1] and self.x1 == r[2] and self.y1 == r[3]

    def __getitem__(self, i):
        return (self.x0, self.y0, self.x1, self.y1)[i]

    def __hash__(self):
        return hash(tuple(self))

    def __init__(self, *args, p0=None, p1=None, x0=None, y0=None, x1=None, y1=None):
        self.x0, self.y0, self.x1, self.y1 = util_make_irect( *args, p0=p0, p1=p1, x0=x0, y0=y0, x1=x1, y1=y1)

    def __len__(self):
        return 4

    def __mul__(self, m):
        return Rect.__mul__(self, m).round()

    def __neg__(self):
        return IRect(-self.x0, -self.y0, -self.x1, -self.y1)

    def __or__(self, x):
        return Rect.__or__(self, x).round()

    def __pos__(self):
        return IRect(self)

    def __repr__(self):
        return "IRect" + str(tuple(self))

    def __setitem__(self, i, v):
        v = int(v)
        if   i == 0: self.x0 = v
        elif i == 1: self.y0 = v
        elif i == 2: self.x1 = v
        elif i == 3: self.y1 = v
        else:
            raise IndexError("index out of range")
        return None

    def __sub__(self, p):
        return Rect.__sub__(self, p).round()

    def __truediv__(self, m):
        return Rect.__truediv__(self, m).round()

    @property
    def bottom_left(self):
        """Bottom-left corner."""
        return Point(self.x0, self.y1)

    @property
    def bottom_right(self):
        """Bottom-right corner."""
        return Point(self.x1, self.y1)

    @property
    def height(self):
        return max(0, self.y1 - self.y0)

    def include_point(self, p):
        """Extend rectangle to include point p."""
        rect = self.rect.include_point(p)
        return rect.irect

    def include_rect(self, r):
        """Extend rectangle to include rectangle r."""
        rect = self.rect.include_rect(r)
        return rect.irect

    def intersect(self, r):
        """Restrict rectangle to intersection with rectangle r."""
        return Rect.intersect(self, r).round()

    def intersects(self, x):
        return Rect.intersects(self, x)

    @property
    def is_empty(self):
        """True if rectangle area is empty."""
        return self.x0 >= self.x1 or self.y0 >= self.y1

    @property
    def is_infinite(self):
        """True if rectangle is infinite."""
        return self.x0 == self.y0 == FZ_MIN_INF_RECT and self.x1 == self.y1 == FZ_MAX_INF_RECT

    @property
    def is_valid(self):
        """True if rectangle is valid."""
        return self.x0 <= self.x1 and self.y0 <= self.y1

    def morph(self, p, m):
        """Morph with matrix-like m and point-like p.

        Returns a new quad."""
        if self.is_infinite:
            return INFINITE_QUAD()
        return self.quad.morph(p, m)

    def norm(self):
        return math.sqrt(sum([c*c for c in self]))

    def normalize(self):
        """Replace rectangle with its valid version."""
        if self.x1 < self.x0:
            self.x0, self.x1 = self.x1, self.x0
        if self.y1 < self.y0:
            self.y0, self.y1 = self.y1, self.y0
        return self

    @property
    def quad(self):
        """Return Quad version of rectangle."""
        return Quad(self.tl, self.tr, self.bl, self.br)

    @property
    def rect(self):
        return Rect(self)

    @property
    def top_left(self):
        """Top-left corner."""
        return Point(self.x0, self.y0)

    @property
    def top_right(self):
        """Top-right corner."""
        return Point(self.x1, self.y0)

    def torect(self, r):
        """Return matrix that converts to target rect."""
        r = Rect(r)
        if self.is_infinite or self.is_empty or r.is_infinite or r.is_empty:
            raise ValueError("rectangles must be finite and not empty")
        return (
                Matrix(1, 0, 0, 1, -self.x0, -self.y0)
                * Matrix(r.width / self.width, r.height / self.height)
                * Matrix(1, 0, 0, 1, r.x0, r.y0)
                )

    def transform(self, m):
        return Rect.transform(self, m).round()

    @property
    def width(self):
        return max(0, self.x1 - self.x0)

    br = bottom_right
    bl = bottom_left
    tl = top_left
    tr = top_right


# Data
#

if 1:
    _self = sys.modules[__name__]
    if 1:
        for _name, _value in mupdf.__dict__.items():
            if _name.startswith(('PDF_', 'UCDN_SCRIPT_')):
                if _name.startswith('PDF_ENUM_NAME_'):
                    # Not a simple enum.
                    pass
                else:
                    #assert not inspect.isroutine(value)
                    #log(f'importing {_name=} {_value=}.')
                    setattr(_self, _name, _value)
                    #log(f'{getattr( self, name, None)=}')
    else:
        # This is slow due to importing inspect, e.g. 0.019 instead of 0.004.
        for _name, _value in inspect.getmembers(mupdf):
            if _name.startswith(('PDF_', 'UCDN_SCRIPT_')):
                if _name.startswith('PDF_ENUM_NAME_'):
                    # Not a simple enum.
                    pass
                else:
                    #assert not inspect.isroutine(value)
                    #log(f'importing {name}')
                    setattr(_self, _name, _value)
                    #log(f'{getattr( self, name, None)=}')
    
    # This is a macro so not preserved in mupdf C++/Python bindings.
    #
    PDF_SIGNATURE_DEFAULT_APPEARANCE = (0
            | mupdf.PDF_SIGNATURE_SHOW_LABELS
            | mupdf.PDF_SIGNATURE_SHOW_DN
            | mupdf.PDF_SIGNATURE_SHOW_DATE
            | mupdf.PDF_SIGNATURE_SHOW_TEXT_NAME
            | mupdf.PDF_SIGNATURE_SHOW_GRAPHIC_NAME
            | mupdf.PDF_SIGNATURE_SHOW_LOGO
            )

    #UCDN_SCRIPT_ADLAM = mupdf.UCDN_SCRIPT_ADLAM
    #setattr(self, 'UCDN_SCRIPT_ADLAM', mupdf.UCDN_SCRIPT_ADLAM)
    
    assert mupdf.UCDN_EAST_ASIAN_H == 1
    
    # Flake8 incorrectly fails next two lines because we've dynamically added
    # items to self.
    assert PDF_TX_FIELD_IS_MULTILINE == mupdf.PDF_TX_FIELD_IS_MULTILINE # noqa: F821
    assert UCDN_SCRIPT_ADLAM == mupdf.UCDN_SCRIPT_ADLAM # noqa: F821
    del _self, _name, _value

AnyType = typing.Any

Base14_fontnames = (
    "Courier",
    "Courier-Oblique",
    "Courier-Bold",
    "Courier-BoldOblique",
    "Helvetica",
    "Helvetica-Oblique",
    "Helvetica-Bold",
    "Helvetica-BoldOblique",
    "Times-Roman",
    "Times-Italic",
    "Times-Bold",
    "Times-BoldItalic",
    "Symbol",
    "ZapfDingbats",
    )

Base14_fontdict = {}
for f in Base14_fontnames:
    Base14_fontdict[f.lower()] = f
Base14_fontdict["helv"] = "Helvetica"
Base14_fontdict["heit"] = "Helvetica-Oblique"
Base14_fontdict["hebo"] = "Helvetica-Bold"
Base14_fontdict["hebi"] = "Helvetica-BoldOblique"
Base14_fontdict["cour"] = "Courier"
Base14_fontdict["coit"] = "Courier-Oblique"
Base14_fontdict["cobo"] = "Courier-Bold"
Base14_fontdict["cobi"] = "Courier-BoldOblique"
Base14_fontdict["tiro"] = "Times-Roman"
Base14_fontdict["tibo"] = "Times-Bold"
Base14_fontdict["tiit"] = "Times-Italic"
Base14_fontdict["tibi"] = "Times-BoldItalic"
Base14_fontdict["symb"] = "Symbol"
Base14_fontdict["zadb"] = "ZapfDingbats"

EPSILON = 1e-5
FLT_EPSILON = 1e-5

# largest 32bit integers surviving C float conversion roundtrips
# used by MuPDF to define infinite rectangles
FZ_MIN_INF_RECT = -0x80000000
FZ_MAX_INF_RECT = 0x7fffff80

JM_annot_id_stem = "fitz"
JM_mupdf_warnings_store = []
JM_mupdf_show_errors = 1
JM_mupdf_show_warnings = 0


# ------------------------------------------------------------------------------
# Various PDF Optional Content Flags
# ------------------------------------------------------------------------------
PDF_OC_ON = 0
PDF_OC_TOGGLE = 1
PDF_OC_OFF = 2

# ------------------------------------------------------------------------------
# link kinds and link flags
# ------------------------------------------------------------------------------
LINK_NONE = 0
LINK_GOTO = 1
LINK_URI = 2
LINK_LAUNCH = 3
LINK_NAMED = 4
LINK_GOTOR = 5
LINK_FLAG_L_VALID = 1
LINK_FLAG_T_VALID = 2
LINK_FLAG_R_VALID = 4
LINK_FLAG_B_VALID = 8
LINK_FLAG_FIT_H = 16
LINK_FLAG_FIT_V = 32
LINK_FLAG_R_IS_ZOOM = 64

SigFlag_SignaturesExist = 1
SigFlag_AppendOnly = 2

STAMP_Approved = 0
STAMP_AsIs = 1
STAMP_Confidential = 2
STAMP_Departmental = 3
STAMP_Experimental = 4
STAMP_Expired = 5
STAMP_Final = 6
STAMP_ForComment = 7
STAMP_ForPublicRelease = 8
STAMP_NotApproved = 9
STAMP_NotForPublicRelease = 10
STAMP_Sold = 11
STAMP_TopSecret = 12
STAMP_Draft = 13

TEXT_ALIGN_LEFT = 0
TEXT_ALIGN_CENTER = 1
TEXT_ALIGN_RIGHT = 2
TEXT_ALIGN_JUSTIFY = 3

TEXT_FONT_SUPERSCRIPT = 1
TEXT_FONT_ITALIC = 2
TEXT_FONT_SERIFED = 4
TEXT_FONT_MONOSPACED = 8
TEXT_FONT_BOLD = 16

TEXT_OUTPUT_TEXT = 0
TEXT_OUTPUT_HTML = 1
TEXT_OUTPUT_JSON = 2
TEXT_OUTPUT_XML = 3
TEXT_OUTPUT_XHTML = 4

TEXT_PRESERVE_LIGATURES = mupdf.FZ_STEXT_PRESERVE_LIGATURES
TEXT_PRESERVE_WHITESPACE = mupdf.FZ_STEXT_PRESERVE_WHITESPACE
TEXT_PRESERVE_IMAGES = mupdf.FZ_STEXT_PRESERVE_IMAGES
TEXT_INHIBIT_SPACES = mupdf.FZ_STEXT_INHIBIT_SPACES
TEXT_DEHYPHENATE = mupdf.FZ_STEXT_DEHYPHENATE
TEXT_PRESERVE_SPANS = mupdf.FZ_STEXT_PRESERVE_SPANS
TEXT_MEDIABOX_CLIP = mupdf.FZ_STEXT_MEDIABOX_CLIP
TEXT_CID_FOR_UNKNOWN_UNICODE = mupdf.FZ_STEXT_USE_CID_FOR_UNKNOWN_UNICODE
if mupdf_version_tuple >= (1, 25):
    TEXT_COLLECT_STRUCTURE = mupdf.FZ_STEXT_COLLECT_STRUCTURE
    TEXT_ACCURATE_BBOXES = mupdf.FZ_STEXT_ACCURATE_BBOXES
    TEXT_COLLECT_VECTORS = mupdf.FZ_STEXT_COLLECT_VECTORS
    TEXT_IGNORE_ACTUALTEXT = mupdf.FZ_STEXT_IGNORE_ACTUALTEXT
    TEXT_STEXT_SEGMENT = mupdf.FZ_STEXT_SEGMENT
else:
    TEXT_COLLECT_STRUCTURE = 256
    TEXT_ACCURATE_BBOXES = 512
    TEXT_COLLECT_VECTORS = 1024
    TEXT_IGNORE_ACTUALTEXT = 2048
    TEXT_STEXT_SEGMENT = 4096

TEXTFLAGS_WORDS = (0
        | TEXT_PRESERVE_LIGATURES
        | TEXT_PRESERVE_WHITESPACE
        | TEXT_MEDIABOX_CLIP
        | TEXT_CID_FOR_UNKNOWN_UNICODE
        )

TEXTFLAGS_BLOCKS = (0
        | TEXT_PRESERVE_LIGATURES
        | TEXT_PRESERVE_WHITESPACE
        | TEXT_MEDIABOX_CLIP
        | TEXT_CID_FOR_UNKNOWN_UNICODE
        )

TEXTFLAGS_DICT = (0
        | TEXT_PRESERVE_LIGATURES
        | TEXT_PRESERVE_WHITESPACE
        | TEXT_MEDIABOX_CLIP
        | TEXT_PRESERVE_IMAGES
        | TEXT_CID_FOR_UNKNOWN_UNICODE
        )

TEXTFLAGS_RAWDICT = TEXTFLAGS_DICT

TEXTFLAGS_SEARCH = (0
        | TEXT_PRESERVE_WHITESPACE
        | TEXT_MEDIABOX_CLIP
        | TEXT_DEHYPHENATE
        | TEXT_CID_FOR_UNKNOWN_UNICODE
        )

TEXTFLAGS_HTML = (0
        | TEXT_PRESERVE_LIGATURES
        | TEXT_PRESERVE_WHITESPACE
        | TEXT_MEDIABOX_CLIP
        | TEXT_PRESERVE_IMAGES
        | TEXT_CID_FOR_UNKNOWN_UNICODE
        )

TEXTFLAGS_XHTML = (0
        | TEXT_PRESERVE_LIGATURES
        | TEXT_PRESERVE_WHITESPACE
        | TEXT_MEDIABOX_CLIP
        | TEXT_PRESERVE_IMAGES
        | TEXT_CID_FOR_UNKNOWN_UNICODE
        )

TEXTFLAGS_XML = (0
        | TEXT_PRESERVE_LIGATURES
        | TEXT_PRESERVE_WHITESPACE
        | TEXT_MEDIABOX_CLIP
        | TEXT_CID_FOR_UNKNOWN_UNICODE
        )

TEXTFLAGS_TEXT = (0
        | TEXT_PRESERVE_LIGATURES
        | TEXT_PRESERVE_WHITESPACE
        | TEXT_MEDIABOX_CLIP
        | TEXT_CID_FOR_UNKNOWN_UNICODE
        )

# Simple text encoding options
TEXT_ENCODING_LATIN = 0
TEXT_ENCODING_GREEK = 1
TEXT_ENCODING_CYRILLIC = 2

TOOLS_JM_UNIQUE_ID = 0

# colorspace identifiers
CS_RGB = 1
CS_GRAY = 2
CS_CMYK = 3

# PDF Blend Modes
PDF_BM_Color = "Color"
PDF_BM_ColorBurn = "ColorBurn"
PDF_BM_ColorDodge = "ColorDodge"
PDF_BM_Darken = "Darken"
PDF_BM_Difference = "Difference"
PDF_BM_Exclusion = "Exclusion"
PDF_BM_HardLight = "HardLight"
PDF_BM_Hue = "Hue"
PDF_BM_Lighten = "Lighten"
PDF_BM_Luminosity = "Luminosity"
PDF_BM_Multiply = "Multiply"
PDF_BM_Normal = "Normal"
PDF_BM_Overlay = "Overlay"
PDF_BM_Saturation = "Saturation"
PDF_BM_Screen = "Screen"
PDF_BM_SoftLight = "Softlight"

# General text flags
TEXT_FONT_SUPERSCRIPT = 1
TEXT_FONT_ITALIC = 2
TEXT_FONT_SERIFED = 4
TEXT_FONT_MONOSPACED = 8
TEXT_FONT_BOLD = 16


annot_skel = {
        "goto1": lambda a, b, c, d, e: f"<</A<</S/GoTo/D[{a} 0 R/XYZ {_format_g((b, c, d))}]>>/Rect[{e}]/BS<</W 0>>/Subtype/Link>>",
        "goto2": lambda a, b: f"<</A<</S/GoTo/D{a}>>/Rect[{b}]/BS<</W 0>>/Subtype/Link>>",
        "gotor1": lambda a, b, c, d, e, f, g: f"<</A<</S/GoToR/D[{a} /XYZ {_format_g((b, c, d))}]/F<</F({e})/UF({f})/Type/Filespec>>>>/Rect[{g}]/BS<</W 0>>/Subtype/Link>>",
        "gotor2": lambda a, b, c: f"<</A<</S/GoToR/D{a}/F({b})>>/Rect[{c}]/BS<</W 0>>/Subtype/Link>>",
        "launch": lambda a, b, c: f"<</A<</S/Launch/F<</F({a})/UF({b})/Type/Filespec>>>>/Rect[{c}]/BS<</W 0>>/Subtype/Link>>",
        "uri": lambda a, b: f"<</A<</S/URI/URI({a})>>/Rect[{b}]/BS<</W 0>>/Subtype/Link>>",
        "named": lambda a, b: f"<</A<</S/GoTo/D({a})/Type/Action>>/Rect[{b}]/BS<</W 0>>/Subtype/Link>>",
        }

class FileDataError(RuntimeError):
    """Raised for documents with file structure issues."""
    pass

class FileNotFoundError(RuntimeError):
    """Raised if file does not exist."""
    pass

class EmptyFileError(FileDataError):
    """Raised when creating documents from zero-length data."""
    pass

# propagate exception class to C-level code
#_set_FileDataError(FileDataError)
 
csRGB = Colorspace(CS_RGB)
csGRAY = Colorspace(CS_GRAY)
csCMYK = Colorspace(CS_CMYK)

# These don't appear to be visible in classic, but are used
# internally.
#
dictkey_align = "align"
dictkey_asc = "ascender"
dictkey_bbox = "bbox"
dictkey_blocks = "blocks"
dictkey_bpc = "bpc"
dictkey_c = "c"
dictkey_chars = "chars"
dictkey_color = "color"
dictkey_colorspace = "colorspace"
dictkey_content = "content"
dictkey_creationDate = "creationDate"
dictkey_cs_name = "cs-name"
dictkey_da = "da"
dictkey_dashes = "dashes"
dictkey_descr = "description"
dictkey_desc = "descender"
dictkey_dir = "dir"
dictkey_effect = "effect"
dictkey_ext = "ext"
dictkey_filename = "filename"
dictkey_fill = "fill"
dictkey_flags = "flags"
dictkey_char_flags = "char_flags"
dictkey_font = "font"
dictkey_glyph = "glyph"
dictkey_height = "height"
dictkey_id = "id"
dictkey_image = "image"
dictkey_items = "items"
dictkey_length = "length"
dictkey_lines = "lines"
dictkey_matrix = "transform"
dictkey_modDate = "modDate"
dictkey_name = "name"
dictkey_number = "number"
dictkey_origin = "origin"
dictkey_rect = "rect"
dictkey_size = "size"
dictkey_smask = "smask"
dictkey_spans = "spans"
dictkey_stroke = "stroke"
dictkey_style = "style"
dictkey_subject = "subject"
dictkey_text = "text"
dictkey_title = "title"
dictkey_type = "type"
dictkey_ufilename = "ufilename"
dictkey_width = "width"
dictkey_wmode = "wmode"
dictkey_xref = "xref"
dictkey_xres = "xres"
dictkey_yres = "yres"


try:
    from pymupdf_fonts import fontdescriptors, fontbuffers

    fitz_fontdescriptors = fontdescriptors.copy()
    for k in fitz_fontdescriptors.keys():
        fitz_fontdescriptors[k]["loader"] = fontbuffers[k]
    del fontdescriptors, fontbuffers
except ImportError:
    fitz_fontdescriptors = {}

symbol_glyphs = (   # Glyph list for the built-in font 'Symbol'
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (32, 0.25),
        (33, 0.333),
        (34, 0.713),
        (35, 0.5),
        (36, 0.549),
        (37, 0.833),
        (38, 0.778),
        (39, 0.439),
        (40, 0.333),
        (41, 0.333),
        (42, 0.5),
        (43, 0.549),
        (44, 0.25),
        (45, 0.549),
        (46, 0.25),
        (47, 0.278),
        (48, 0.5),
        (49, 0.5),
        (50, 0.5),
        (51, 0.5),
        (52, 0.5),
        (53, 0.5),
        (54, 0.5),
        (55, 0.5),
        (56, 0.5),
        (57, 0.5),
        (58, 0.278),
        (59, 0.278),
        (60, 0.549),
        (61, 0.549),
        (62, 0.549),
        (63, 0.444),
        (64, 0.549),
        (65, 0.722),
        (66, 0.667),
        (67, 0.722),
        (68, 0.612),
        (69, 0.611),
        (70, 0.763),
        (71, 0.603),
        (72, 0.722),
        (73, 0.333),
        (74, 0.631),
        (75, 0.722),
        (76, 0.686),
        (77, 0.889),
        (78, 0.722),
        (79, 0.722),
        (80, 0.768),
        (81, 0.741),
        (82, 0.556),
        (83, 0.592),
        (84, 0.611),
        (85, 0.69),
        (86, 0.439),
        (87, 0.768),
        (88, 0.645),
        (89, 0.795),
        (90, 0.611),
        (91, 0.333),
        (92, 0.863),
        (93, 0.333),
        (94, 0.658),
        (95, 0.5),
        (96, 0.5),
        (97, 0.631),
        (98, 0.549),
        (99, 0.549),
        (100, 0.494),
        (101, 0.439),
        (102, 0.521),
        (103, 0.411),
        (104, 0.603),
        (105, 0.329),
        (106, 0.603),
        (107, 0.549),
        (108, 0.549),
        (109, 0.576),
        (110, 0.521),
        (111, 0.549),
        (112, 0.549),
        (113, 0.521),
        (114, 0.549),
        (115, 0.603),
        (116, 0.439),
        (117, 0.576),
        (118, 0.713),
        (119, 0.686),
        (120, 0.493),
        (121, 0.686),
        (122, 0.494),
        (123, 0.48),
        (124, 0.2),
        (125, 0.48),
        (126, 0.549),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (183, 0.46),
        (160, 0.25),
        (161, 0.62),
        (162, 0.247),
        (163, 0.549),
        (164, 0.167),
        (165, 0.713),
        (166, 0.5),
        (167, 0.753),
        (168, 0.753),
        (169, 0.753),
        (170, 0.753),
        (171, 1.042),
        (172, 0.713),
        (173, 0.603),
        (174, 0.987),
        (175, 0.603),
        (176, 0.4),
        (177, 0.549),
        (178, 0.411),
        (179, 0.549),
        (180, 0.549),
        (181, 0.576),
        (182, 0.494),
        (183, 0.46),
        (184, 0.549),
        (185, 0.549),
        (186, 0.549),
        (187, 0.549),
        (188, 1),
        (189, 0.603),
        (190, 1),
        (191, 0.658),
        (192, 0.823),
        (193, 0.686),
        (194, 0.795),
        (195, 0.987),
        (196, 0.768),
        (197, 0.768),
        (198, 0.823),
        (199, 0.768),
        (200, 0.768),
        (201, 0.713),
        (202, 0.713),
        (203, 0.713),
        (204, 0.713),
        (205, 0.713),
        (206, 0.713),
        (207, 0.713),
        (208, 0.768),
        (209, 0.713),
        (210, 0.79),
        (211, 0.79),
        (212, 0.89),
        (213, 0.823),
        (214, 0.549),
        (215, 0.549),
        (216, 0.713),
        (217, 0.603),
        (218, 0.603),
        (219, 1.042),
        (220, 0.987),
        (221, 0.603),
        (222, 0.987),
        (223, 0.603),
        (224, 0.494),
        (225, 0.329),
        (226, 0.79),
        (227, 0.79),
        (228, 0.786),
        (229, 0.713),
        (230, 0.384),
        (231, 0.384),
        (232, 0.384),
        (233, 0.384),
        (234, 0.384),
        (235, 0.384),
        (236, 0.494),
        (237, 0.494),
        (238, 0.494),
        (239, 0.494),
        (183, 0.46),
        (241, 0.329),
        (242, 0.274),
        (243, 0.686),
        (244, 0.686),
        (245, 0.686),
        (246, 0.384),
        (247, 0.549),
        (248, 0.384),
        (249, 0.384),
        (250, 0.384),
        (251, 0.384),
        (252, 0.494),
        (253, 0.494),
        (254, 0.494),
        (183, 0.46),
        )


zapf_glyphs = ( # Glyph list for the built-in font 'ZapfDingbats'
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (32, 0.278),
        (33, 0.974),
        (34, 0.961),
        (35, 0.974),
        (36, 0.98),
        (37, 0.719),
        (38, 0.789),
        (39, 0.79),
        (40, 0.791),
        (41, 0.69),
        (42, 0.96),
        (43, 0.939),
        (44, 0.549),
        (45, 0.855),
        (46, 0.911),
        (47, 0.933),
        (48, 0.911),
        (49, 0.945),
        (50, 0.974),
        (51, 0.755),
        (52, 0.846),
        (53, 0.762),
        (54, 0.761),
        (55, 0.571),
        (56, 0.677),
        (57, 0.763),
        (58, 0.76),
        (59, 0.759),
        (60, 0.754),
        (61, 0.494),
        (62, 0.552),
        (63, 0.537),
        (64, 0.577),
        (65, 0.692),
        (66, 0.786),
        (67, 0.788),
        (68, 0.788),
        (69, 0.79),
        (70, 0.793),
        (71, 0.794),
        (72, 0.816),
        (73, 0.823),
        (74, 0.789),
        (75, 0.841),
        (76, 0.823),
        (77, 0.833),
        (78, 0.816),
        (79, 0.831),
        (80, 0.923),
        (81, 0.744),
        (82, 0.723),
        (83, 0.749),
        (84, 0.79),
        (85, 0.792),
        (86, 0.695),
        (87, 0.776),
        (88, 0.768),
        (89, 0.792),
        (90, 0.759),
        (91, 0.707),
        (92, 0.708),
        (93, 0.682),
        (94, 0.701),
        (95, 0.826),
        (96, 0.815),
        (97, 0.789),
        (98, 0.789),
        (99, 0.707),
        (100, 0.687),
        (101, 0.696),
        (102, 0.689),
        (103, 0.786),
        (104, 0.787),
        (105, 0.713),
        (106, 0.791),
        (107, 0.785),
        (108, 0.791),
        (109, 0.873),
        (110, 0.761),
        (111, 0.762),
        (112, 0.762),
        (113, 0.759),
        (114, 0.759),
        (115, 0.892),
        (116, 0.892),
        (117, 0.788),
        (118, 0.784),
        (119, 0.438),
        (120, 0.138),
        (121, 0.277),
        (122, 0.415),
        (123, 0.392),
        (124, 0.392),
        (125, 0.668),
        (126, 0.668),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (183, 0.788),
        (161, 0.732),
        (162, 0.544),
        (163, 0.544),
        (164, 0.91),
        (165, 0.667),
        (166, 0.76),
        (167, 0.76),
        (168, 0.776),
        (169, 0.595),
        (170, 0.694),
        (171, 0.626),
        (172, 0.788),
        (173, 0.788),
        (174, 0.788),
        (175, 0.788),
        (176, 0.788),
        (177, 0.788),
        (178, 0.788),
        (179, 0.788),
        (180, 0.788),
        (181, 0.788),
        (182, 0.788),
        (183, 0.788),
        (184, 0.788),
        (185, 0.788),
        (186, 0.788),
        (187, 0.788),
        (188, 0.788),
        (189, 0.788),
        (190, 0.788),
        (191, 0.788),
        (192, 0.788),
        (193, 0.788),
        (194, 0.788),
        (195, 0.788),
        (196, 0.788),
        (197, 0.788),
        (198, 0.788),
        (199, 0.788),
        (200, 0.788),
        (201, 0.788),
        (202, 0.788),
        (203, 0.788),
        (204, 0.788),
        (205, 0.788),
        (206, 0.788),
        (207, 0.788),
        (208, 0.788),
        (209, 0.788),
        (210, 0.788),
        (211, 0.788),
        (212, 0.894),
        (213, 0.838),
        (214, 1.016),
        (215, 0.458),
        (216, 0.748),
        (217, 0.924),
        (218, 0.748),
        (219, 0.918),
        (220, 0.927),
        (221, 0.928),
        (222, 0.928),
        (223, 0.834),
        (224, 0.873),
        (225, 0.828),
        (226, 0.924),
        (227, 0.924),
        (228, 0.917),
        (229, 0.93),
        (230, 0.931),
        (231, 0.463),
        (232, 0.883),
        (233, 0.836),
        (234, 0.836),
        (235, 0.867),
        (236, 0.867),
        (237, 0.696),
        (238, 0.696),
        (239, 0.874),
        (183, 0.788),
        (241, 0.874),
        (242, 0.76),
        (243, 0.946),
        (244, 0.771),
        (245, 0.865),
        (246, 0.771),
        (247, 0.888),
        (248, 0.967),
        (249, 0.888),
        (250, 0.831),
        (251, 0.873),
        (252, 0.927),
        (253, 0.97),
        (183, 0.788),
        (183, 0.788),
        )


# Functions
#

def _read_samples( pixmap, offset, n):
    # fixme: need to be able to get a sample in one call, as a Python
    # bytes or similar.
    ret = []
    if not pixmap.samples():
        # mupdf.fz_samples_get() gives a segv if pixmap->samples is null.
        return ret
    for i in range( n):
        ret.append( mupdf.fz_samples_get( pixmap, offset + i))
    return bytes( ret)


def _INRANGE(v, low, high):
    return low <= v and v <= high


def _remove_dest_range(pdf, numbers):
    pagecount = mupdf.pdf_count_pages(pdf)
    for i in range(pagecount):
        n1 = i
        if n1 in numbers:
            continue

        pageref = mupdf.pdf_lookup_page_obj( pdf, i)
        annots = mupdf.pdf_dict_get( pageref, PDF_NAME('Annots'))
        if not annots.m_internal:
            continue
        len_ = mupdf.pdf_array_len(annots)
        for j in range(len_ - 1, -1, -1):
            o = mupdf.pdf_array_get( annots, j)
            if not mupdf.pdf_name_eq( mupdf.pdf_dict_get( o, PDF_NAME('Subtype')), PDF_NAME('Link')):
                continue
            action = mupdf.pdf_dict_get( o, PDF_NAME('A'))
            dest = mupdf.pdf_dict_get( o, PDF_NAME('Dest'))
            if action.m_internal:
                if not mupdf.pdf_name_eq( mupdf.pdf_dict_get( action, PDF_NAME('S')), PDF_NAME('GoTo')):
                    continue
                dest = mupdf.pdf_dict_get( action, PDF_NAME('D'))
            pno = -1
            if mupdf.pdf_is_array( dest):
                target = mupdf.pdf_array_get( dest, 0)
                pno = mupdf.pdf_lookup_page_number( pdf, target)
            elif mupdf.pdf_is_string( dest):
                location, _, _ = mupdf.fz_resolve_link( pdf.super(), mupdf.pdf_to_text_string( dest))
                pno = location.page
            if pno < 0: # page number lookup did not work
                continue
            n1 = pno
            if n1 in numbers:
                mupdf.pdf_array_delete( annots, j)


def ASSERT_PDF(cond):
    assert isinstance(cond, (mupdf.PdfPage, mupdf.PdfDocument)), f'{type(cond)=} {cond=}'
    if not cond.m_internal:
        raise Exception(MSG_IS_NO_PDF)


def EMPTY_IRECT():
    return IRect(FZ_MAX_INF_RECT, FZ_MAX_INF_RECT, FZ_MIN_INF_RECT, FZ_MIN_INF_RECT)


def EMPTY_QUAD():
    return EMPTY_RECT().quad


def EMPTY_RECT():
    return Rect(FZ_MAX_INF_RECT, FZ_MAX_INF_RECT, FZ_MIN_INF_RECT, FZ_MIN_INF_RECT)


def ENSURE_OPERATION(pdf):
    if not JM_have_operation(pdf):
        raise Exception("No journalling operation started")


def INFINITE_IRECT():
    return IRect(FZ_MIN_INF_RECT, FZ_MIN_INF_RECT, FZ_MAX_INF_RECT, FZ_MAX_INF_RECT)


def INFINITE_QUAD():
    return INFINITE_RECT().quad


def INFINITE_RECT():
    return Rect(FZ_MIN_INF_RECT, FZ_MIN_INF_RECT, FZ_MAX_INF_RECT, FZ_MAX_INF_RECT)


def JM_BinFromBuffer(buffer_):
    '''
    Turn fz_buffer into a Python bytes object
    '''
    assert isinstance(buffer_, mupdf.FzBuffer)
    ret = mupdf.fz_buffer_extract_copy(buffer_)
    return ret


def JM_EscapeStrFromStr(c):
    # `c` is typically from SWIG which will have converted a `const char*` from
    # C into a Python `str` using `PyUnicode_DecodeUTF8(carray, static_cast<
    # Py_ssize_t >(size), "surrogateescape")`.  This gives us a Python `str`
    # with some characters encoded as a \0xdcXY sequence, where `XY` are hex
    # digits for an invalid byte in the original `const char*`.
    #
    # This is actually a reasonable way of representing arbitrary
    # strings from C, but we want to mimic what PyMuPDF does. It uses
    # `PyUnicode_DecodeRawUnicodeEscape(c, (Py_ssize_t) strlen(c), "replace")`
    # which gives a string containing actual unicode characters for any invalid
    # bytes.
    #
    # We mimic this by converting the `str` to a `bytes` with 'surrogateescape'
    # to recognise \0xdcXY sequences, then convert the individual bytes into a
    # `str` using `chr()`.
    #
    # Would be good to have a more efficient way to do this.
    #
    if c is None:
        return ''
    assert isinstance(c, str), f'{type(c)=}'
    b = c.encode('utf8', 'surrogateescape')
    ret = ''
    for bb in b:
        ret += chr(bb)
    return ret


def JM_BufferFromBytes(stream):
    '''
    Make fz_buffer from a PyBytes, PyByteArray or io.BytesIO object. If a text
    io.BytesIO, we convert to binary by encoding as utf8.
    '''
    if isinstance(stream, (bytes, bytearray)):
        data = stream
    elif hasattr(stream, 'getvalue'):
        data = stream.getvalue()
        if isinstance(data, str):
            data = data.encode('utf-8')
        if not isinstance(data, (bytes, bytearray)):
            raise Exception(f'.getvalue() returned unexpected type: {type(data)}')
    else:
        return mupdf.FzBuffer()
    return mupdf.fz_new_buffer_from_copied_data(data)


def JM_FLOAT_ITEM(obj, idx):
    if not PySequence_Check(obj):
        return None
    return float(obj[idx])

def JM_INT_ITEM(obj, idx):
    if idx < len(obj):
        temp = obj[idx]
        if isinstance(temp, (int, float)):
            return 0, temp
    return 1, None


def JM_pixmap_from_page(doc, page, ctm, cs, alpha, annots, clip):
    '''
    Pixmap creation directly using a short-lived displaylist, so we can support
    separations.
    '''
    SPOTS_NONE = 0
    SPOTS_OVERPRINT_SIM = 1
    SPOTS_FULL = 2
    
    FZ_ENABLE_SPOT_RENDERING = True # fixme: this is a build-time setting in MuPDF's config.h.
    if FZ_ENABLE_SPOT_RENDERING:
        spots = SPOTS_OVERPRINT_SIM
    else:
        spots = SPOTS_NONE

    seps = None
    colorspace = cs
    
    matrix = JM_matrix_from_py(ctm)
    rect = mupdf.fz_bound_page(page)
    rclip = JM_rect_from_py(clip)
    rect = mupdf.fz_intersect_rect(rect, rclip) # no-op if clip is not given
    rect = mupdf.fz_transform_rect(rect, matrix)
    bbox = mupdf.fz_round_rect(rect)

    # Pixmap of the document's /OutputIntents ("output intents")
    oi = mupdf.fz_document_output_intent(doc)
    # if present and compatible, use it instead of the parameter
    if oi.m_internal:
        if mupdf.fz_colorspace_n(oi) == mupdf.fz_colorspace_n(cs):
            colorspace = mupdf.fz_keep_colorspace(oi)

    # check if spots rendering is available and if so use separations
    if spots != SPOTS_NONE:
        seps = mupdf.fz_page_separations(page)
        if seps.m_internal:
            n = mupdf.fz_count_separations(seps)
            if spots == SPOTS_FULL:
                for i in range(n):
                    mupdf.fz_set_separation_behavior(seps, i, mupdf.FZ_SEPARATION_SPOT)
            else:
                for i in range(n):
                    mupdf.fz_set_separation_behavior(seps, i, mupdf.FZ_SEPARATION_COMPOSITE)
        elif mupdf.fz_page_uses_overprint(page):
            # This page uses overprint, so we need an empty
            # sep object to force the overprint simulation on.
            seps = mupdf.fz_new_separations(0)
        elif oi.m_internal and mupdf.fz_colorspace_n(oi) != mupdf.fz_colorspace_n(colorspace):
            # We have an output intent, and it's incompatible
            # with the colorspace our device needs. Force the
            # overprint simulation on, because this ensures that
            # we 'simulate' the output intent too.
            seps = mupdf.fz_new_separations(0)

    pix = mupdf.fz_new_pixmap_with_bbox(colorspace, bbox, seps, alpha)

    if alpha:
        mupdf.fz_clear_pixmap(pix)
    else:
        mupdf.fz_clear_pixmap_with_value(pix, 0xFF)

    dev = mupdf.fz_new_draw_device(matrix, pix)
    if annots:
        mupdf.fz_run_page(page, dev, mupdf.FzMatrix(), mupdf.FzCookie())
    else:
        mupdf.fz_run_page_contents(page, dev, mupdf.FzMatrix(), mupdf.FzCookie())
    mupdf.fz_close_device(dev)
    return pix


def JM_StrAsChar(x):
    # fixme: should encode, but swig doesn't pass bytes to C as const char*.
    return x
    #return x.encode('utf8')


def JM_TUPLE(o: typing.Sequence) -> tuple:
    return tuple(map(lambda x: round(x, 5) if abs(x) >= 1e-4 else 0, o))


def JM_TUPLE3(o: typing.Sequence) -> tuple:
    return tuple(map(lambda x: round(x, 3) if abs(x) >= 1e-3 else 0, o))


def JM_UnicodeFromStr(s):
    if s is None:
        return ''
    if isinstance(s, bytes):
        s = s.decode('utf8')
    assert isinstance(s, str), f'{type(s)=} {s=}'
    return s


def JM_add_annot_id(annot, stem):
    '''
    Add a unique /NM key to an annotation or widget.
    Append a number to 'stem' such that the result is a unique name.
    '''
    assert isinstance(annot, mupdf.PdfAnnot)
    page = _pdf_annot_page(annot)
    annot_obj = mupdf.pdf_annot_obj( annot)
    names = JM_get_annot_id_list(page)
    i = 0
    while 1:
        stem_id = f'{JM_annot_id_stem}-{stem}{i}'
        if stem_id not in names:
            break
        i += 1
    response = JM_StrAsChar(stem_id)
    name = mupdf.pdf_new_string( response, len(response))
    mupdf.pdf_dict_puts(annot_obj, "NM", name)
    page.doc().m_internal.resynth_required = 0


def JM_add_oc_object(pdf, ref, xref):
    '''
    Add OC object reference to a dictionary
    '''
    indobj = mupdf.pdf_new_indirect(pdf, xref, 0)
    if not mupdf.pdf_is_dict(indobj):
        RAISEPY(MSG_BAD_OC_REF, PyExc_ValueError)
    type_ = mupdf.pdf_dict_get(indobj, PDF_NAME('Type'))
    if (mupdf.pdf_objcmp(type_, PDF_NAME('OCG')) == 0
            or mupdf.pdf_objcmp(type_, PDF_NAME('OCMD')) == 0
            ):
        mupdf.pdf_dict_put(ref, PDF_NAME('OC'), indobj)
    else:
        RAISEPY(MSG_BAD_OC_REF, PyExc_ValueError)


def JM_annot_border(annot_obj):
    dash_py = list()
    style = None
    width = -1
    clouds = -1
    obj = None

    obj = mupdf.pdf_dict_get( annot_obj, PDF_NAME('Border'))
    if mupdf.pdf_is_array( obj):
        width = mupdf.pdf_to_real( mupdf.pdf_array_get( obj, 2))
        if mupdf.pdf_array_len( obj) == 4:
            dash = mupdf.pdf_array_get( obj, 3)
            for i in range( mupdf.pdf_array_len( dash)):
                val = mupdf.pdf_to_int( mupdf.pdf_array_get( dash, i))
                dash_py.append( val)

    bs_o = mupdf.pdf_dict_get( annot_obj, PDF_NAME('BS'))
    if bs_o.m_internal:
        width = mupdf.pdf_to_real( mupdf.pdf_dict_get( bs_o, PDF_NAME('W')))
        style = mupdf.pdf_to_name( mupdf.pdf_dict_get( bs_o, PDF_NAME('S')))
        if style == '':
            style = None
        obj = mupdf.pdf_dict_get( bs_o, PDF_NAME('D'))
        if obj.m_internal:
            for i in range( mupdf.pdf_array_len( obj)):
                val = mupdf.pdf_to_int( mupdf.pdf_array_get( obj, i))
                dash_py.append( val)

    obj = mupdf.pdf_dict_get( annot_obj, PDF_NAME('BE'))
    if obj.m_internal:
        clouds = mupdf.pdf_to_int( mupdf.pdf_dict_get( obj, PDF_NAME('I')))

    res = dict()
    res[ dictkey_width] = width
    res[ dictkey_dashes] = tuple( dash_py)
    res[ dictkey_style] = style
    res[ 'clouds'] = clouds
    return res


def JM_annot_colors(annot_obj):
    res = dict()
    bc = list() # stroke colors
    fc =list()  # fill colors
    o = mupdf.pdf_dict_get(annot_obj, mupdf.PDF_ENUM_NAME_C)
    if mupdf.pdf_is_array(o):
        n = mupdf.pdf_array_len(o)
        for i in range(n):
            col = mupdf.pdf_to_real( mupdf.pdf_array_get(o, i))
            bc.append(col)
    res[dictkey_stroke] = bc

    o = mupdf.pdf_dict_gets(annot_obj, "IC")
    if mupdf.pdf_is_array(o):
        n = mupdf.pdf_array_len(o)
        for i in range(n):
            col = mupdf.pdf_to_real( mupdf.pdf_array_get(o, i))
            fc.append(col)

    res[dictkey_fill] = fc
    return res


def JM_annot_set_border( border, doc, annot_obj):
    assert isinstance(border, dict)
    obj = None
    dashlen = 0
    nwidth = border.get( dictkey_width)     # new width
    ndashes = border.get( dictkey_dashes)   # new dashes
    nstyle = border.get( dictkey_style)     # new style
    nclouds  = border.get( 'clouds', -1)    # new clouds value

    # get old border properties
    oborder = JM_annot_border( annot_obj)

    # delete border-related entries
    mupdf.pdf_dict_del( annot_obj, PDF_NAME('BS'))
    mupdf.pdf_dict_del( annot_obj, PDF_NAME('BE'))
    mupdf.pdf_dict_del( annot_obj, PDF_NAME('Border'))

    # populate border items: keep old values for any omitted new ones
    if nwidth < 0:
        nwidth = oborder.get( dictkey_width)    # no new width: keep current
    if ndashes is None:
        ndashes = oborder.get( dictkey_dashes)  # no new dashes: keep old
    if nstyle is None:
        nstyle  = oborder.get( dictkey_style)   # no new style: keep old
    if nclouds < 0:
        nclouds  = oborder.get( "clouds", -1)   # no new clouds: keep old

    if isinstance( ndashes, tuple) and len( ndashes) > 0:
        dashlen = len( ndashes)
        darr = mupdf.pdf_new_array( doc, dashlen)
        for d in ndashes:
            mupdf.pdf_array_push_int( darr, d)
        mupdf.pdf_dict_putl( annot_obj, darr, PDF_NAME('BS'), PDF_NAME('D'))

    mupdf.pdf_dict_putl(
            annot_obj,
            mupdf.pdf_new_real( nwidth),
            PDF_NAME('BS'),
            PDF_NAME('W'),
            )

    if dashlen == 0:
        obj = JM_get_border_style( nstyle)
    else:
        obj = PDF_NAME('D')
    mupdf.pdf_dict_putl( annot_obj, obj, PDF_NAME('BS'), PDF_NAME('S'))

    if nclouds > 0:
        mupdf.pdf_dict_put_dict( annot_obj, PDF_NAME('BE'), 2)
        obj = mupdf.pdf_dict_get( annot_obj, PDF_NAME('BE'))
        mupdf.pdf_dict_put( obj, PDF_NAME('S'), PDF_NAME('C'))
        mupdf.pdf_dict_put_int( obj, PDF_NAME('I'), nclouds)


def make_escape(ch):
    if ch == 92:
        return "\\u005c"
    elif 32 <= ch <= 127 or ch == 10:
        return chr(ch)
    elif 0xd800 <= ch <= 0xdfff:  # orphaned surrogate
        return "\\ufffd"
    elif ch <= 0xffff:
        return "\\u%04x" % ch
    else:
        return "\\U%08x" % ch


def JM_append_rune(buff, ch):
    """
    APPEND non-ascii runes in unicode escape format to fz_buffer.
    """
    mupdf.fz_append_string(buff, make_escape(ch))


def JM_append_word(lines, buff, wbbox, block_n, line_n, word_n):
    '''
    Functions for wordlist output
    '''
    s = JM_EscapeStrFromBuffer(buff)
    litem = (
            wbbox.x0,
            wbbox.y0,
            wbbox.x1,
            wbbox.y1,
            s,
            block_n,
            line_n,
            word_n,
            )
    lines.append(litem)
    return word_n + 1, mupdf.FzRect(mupdf.FzRect.Fixed_EMPTY)   # word counter


def JM_add_layer_config( pdf, name, creator, ON):
    '''
    Add OC configuration to the PDF catalog
    '''
    ocp = JM_ensure_ocproperties( pdf)
    configs = mupdf.pdf_dict_get( ocp, PDF_NAME('Configs'))
    if not mupdf.pdf_is_array( configs):
        configs = mupdf.pdf_dict_put_array( ocp, PDF_NAME('Configs'), 1)
    D = mupdf.pdf_new_dict( pdf, 5)
    mupdf.pdf_dict_put_text_string( D, PDF_NAME('Name'), name)
    if creator is not None:
        mupdf.pdf_dict_put_text_string( D, PDF_NAME('Creator'), creator)
    mupdf.pdf_dict_put( D, PDF_NAME('BaseState'), PDF_NAME('OFF'))
    onarray = mupdf.pdf_dict_put_array( D, PDF_NAME('ON'), 5)
    if not ON:
        pass
    else:
        ocgs = mupdf.pdf_dict_get( ocp, PDF_NAME('OCGs'))
        n = len(ON)
        for i in range(n):
            xref = 0
            e, xref = JM_INT_ITEM(ON, i)
            if e == 1:
                continue
            ind = mupdf.pdf_new_indirect( pdf, xref, 0)
            if mupdf.pdf_array_contains( ocgs, ind):
                mupdf.pdf_array_push( onarray, ind)
    mupdf.pdf_array_push( configs, D)


def JM_char_bbox(line, ch):
    '''
    return rect of char quad
    '''
    q = JM_char_quad(line, ch)
    r = mupdf.fz_rect_from_quad(q)
    if not line.m_internal.wmode:
        return r
    if r.y1 < r.y0 + ch.m_internal.size:
        r.y0 = r.y1 - ch.m_internal.size
    return r


def JM_char_font_flags(font, line, ch):
    flags = 0
    if line and ch:
        flags += detect_super_script(line, ch)
    flags += mupdf.fz_font_is_italic(font) * TEXT_FONT_ITALIC
    flags += mupdf.fz_font_is_serif(font) * TEXT_FONT_SERIFED
    flags += mupdf.fz_font_is_monospaced(font) * TEXT_FONT_MONOSPACED
    flags += mupdf.fz_font_is_bold(font) * TEXT_FONT_BOLD
    return flags


def JM_char_quad(line, ch):
    '''
    re-compute char quad if ascender/descender values make no sense
    '''
    if 1 and g_use_extra:
        # This reduces time taken to extract text from PyMuPDF.pdf from 20s to
        # 15s.
        return mupdf.FzQuad(extra.JM_char_quad( line.m_internal, ch.m_internal))
        
    assert isinstance(line, mupdf.FzStextLine)
    assert isinstance(ch, mupdf.FzStextChar)
    if _globals.skip_quad_corrections:   # no special handling
        return ch.quad
    if line.m_internal.wmode:  # never touch vertical write mode
        return ch.quad
    font = mupdf.FzFont(mupdf.ll_fz_keep_font(ch.m_internal.font))
    asc = JM_font_ascender(font)
    dsc = JM_font_descender(font)
    fsize = ch.m_internal.size
    asc_dsc = asc - dsc + FLT_EPSILON
    if asc_dsc >= 1 and _globals.small_glyph_heights == 0:   # no problem
        return mupdf.FzQuad(ch.m_internal.quad)

    # Re-compute quad with adjusted ascender / descender values:
    # Move ch->origin to (0,0) and de-rotate quad, then adjust the corners,
    # re-rotate and move back to ch->origin location.
    fsize = ch.m_internal.size
    bbox = mupdf.fz_font_bbox(font)
    fwidth = bbox.x1 - bbox.x0
    if asc < 1e-3:  # probably Tesseract glyphless font
        dsc = -0.1
        asc = 0.9
        asc_dsc = 1.0
    
    if _globals.small_glyph_heights or asc_dsc < 1:
        dsc = dsc / asc_dsc
        asc = asc / asc_dsc
    asc_dsc = asc - dsc
    asc = asc * fsize / asc_dsc
    dsc = dsc * fsize / asc_dsc
    
    # Re-compute quad with the adjusted ascender / descender values:
    # Move ch->origin to (0,0) and de-rotate quad, then adjust the corners,
    # re-rotate and move back to ch->origin location.
    c = line.m_internal.dir.x  # cosine
    s = line.m_internal.dir.y  # sine
    trm1 = mupdf.fz_make_matrix(c, -s, s, c, 0, 0) # derotate
    trm2 = mupdf.fz_make_matrix(c, s, -s, c, 0, 0) # rotate
    if (c == -1):   # left-right flip
        trm1.d = 1
        trm2.d = 1
    xlate1 = mupdf.fz_make_matrix(1, 0, 0, 1, -ch.m_internal.origin.x, -ch.m_internal.origin.y)
    xlate2 = mupdf.fz_make_matrix(1, 0, 0, 1, ch.m_internal.origin.x, ch.m_internal.origin.y)

    quad = mupdf.fz_transform_quad(mupdf.FzQuad(ch.m_internal.quad), xlate1)    # move origin to (0,0)
    quad = mupdf.fz_transform_quad(quad, trm1) # de-rotate corners
    
    # adjust vertical coordinates
    if c == 1 and quad.ul.y > 0:    # up-down flip
        quad.ul.y = asc
        quad.ur.y = asc
        quad.ll.y = dsc
        quad.lr.y = dsc
    else:
        quad.ul.y = -asc
        quad.ur.y = -asc
        quad.ll.y = -dsc
        quad.lr.y = -dsc

    # adjust horizontal coordinates that are too crazy:
    # (1) left x must be >= 0
    # (2) if bbox width is 0, lookup char advance in font.
    if quad.ll.x < 0:
        quad.ll.x = 0
        quad.ul.x = 0
    
    cwidth = quad.lr.x - quad.ll.x
    if cwidth < FLT_EPSILON:
        glyph = mupdf.fz_encode_character( font, ch.m_internal.c)
        if glyph:
            fwidth = mupdf.fz_advance_glyph( font, glyph, line.m_internal.wmode)
            quad.lr.x = quad.ll.x + fwidth * fsize
            quad.ur.x = quad.lr.x

    quad = mupdf.fz_transform_quad(quad, trm2) # rotate back
    quad = mupdf.fz_transform_quad(quad, xlate2)   # translate back
    return quad


def JM_choice_options(annot):
    '''
    return list of choices for list or combo boxes
    '''
    annot_obj = mupdf.pdf_annot_obj( annot.this)
    
    opts = mupdf.pdf_choice_widget_options2( annot, 0)
    n = len( opts)
    if n == 0:
        return  # wrong widget type

    optarr = mupdf.pdf_dict_get( annot_obj, PDF_NAME('Opt'))
    liste = []

    for i in range( n):
        m = mupdf.pdf_array_len( mupdf.pdf_array_get( optarr, i))
        if m == 2:
            val = (
                    mupdf.pdf_to_text_string( mupdf.pdf_array_get( mupdf.pdf_array_get( optarr, i), 0)),
                    mupdf.pdf_to_text_string( mupdf.pdf_array_get( mupdf.pdf_array_get( optarr, i), 1)),
                    )
            liste.append( val)
        else:
            val = mupdf.pdf_to_text_string( mupdf.pdf_array_get( optarr, i))
            liste.append( val)
    return liste


def JM_clear_pixmap_rect_with_value(dest, value, b):
    '''
    Clear a pixmap rectangle - my version also supports non-alpha pixmaps
    '''
    b = mupdf.fz_intersect_irect(b, mupdf.fz_pixmap_bbox(dest))
    w = b.x1 - b.x0
    y = b.y1 - b.y0
    if w <= 0 or y <= 0:
        return 0

    destspan = dest.stride()
    destp = destspan * (b.y0 - dest.y()) + dest.n() * (b.x0 - dest.x())

    # CMYK needs special handling (and potentially any other subtractive colorspaces)
    if mupdf.fz_colorspace_n(dest.colorspace()) == 4:
        value = 255 - value
        while 1:
            s = destp
            for x in range(0, w):
                mupdf.fz_samples_set(dest, s, 0)
                s += 1
                mupdf.fz_samples_set(dest, s, 0)
                s += 1
                mupdf.fz_samples_set(dest, s, 0)
                s += 1
                mupdf.fz_samples_set(dest, s, value)
                s += 1
                if dest.alpha():
                    mupdf.fz_samples_set(dest, s, 255)
                    s += 1
            destp += destspan
            if y == 0:
                break
            y -= 1
        return 1

    while 1:
        s = destp
        for x in range(w):
            for k in range(dest.n()-1):
                mupdf.fz_samples_set(dest, s, value)
                s += 1
            if dest.alpha():
                mupdf.fz_samples_set(dest, s, 255)
                s += 1
            else:
                mupdf.fz_samples_set(dest, s, value)
                s += 1
        destp += destspan
        if y == 0:
            break
        y -= 1
    return 1


def JM_color_FromSequence(color):
    
    if isinstance(color, (int, float)):    # maybe just a single float
        color = color[0]
    
    if not isinstance( color, (list, tuple)):
        return -1, []
    
    if len(color) not in (0, 1, 3, 4):
        return -1, []
    
    ret = color[:]
    for i in range(len(ret)):
        if ret[i] < 0 or ret[i] > 1:
            ret[i] = 1
    return len(ret), ret


def JM_color_count( pm, clip):
    rc = dict()
    cnt = 0
    irect = mupdf.fz_pixmap_bbox( pm)
    irect = mupdf.fz_intersect_irect(irect, mupdf.fz_round_rect(JM_rect_from_py(clip)))
    stride = pm.stride()
    width = irect.x1 - irect.x0
    height = irect.y1 - irect.y0
    n = pm.n()
    substride = width * n
    s = stride * (irect.y0 - pm.y()) + (irect.x0 - pm.x()) * n
    oldpix = _read_samples( pm, s, n)
    cnt = 0
    if mupdf.fz_is_empty_irect(irect):
        return rc
    for i in range( height):
        for j in range( 0, substride, n):
            newpix = _read_samples( pm, s + j, n)
            if newpix != oldpix:
                pixel = oldpix
                c = rc.get( pixel, None)
                if c is not None:
                    cnt += c
                rc[ pixel] = cnt
                cnt = 1
                oldpix = newpix
            else:
                cnt += 1
        s += stride
    pixel = oldpix
    c = rc.get( pixel)
    if c is not None:
        cnt += c
    rc[ pixel] = cnt
    return rc


def JM_compress_buffer(inbuffer):
    '''
    compress char* into a new buffer
    '''
    data, compressed_length = mupdf.fz_new_deflated_data_from_buffer(
            inbuffer,
            mupdf.FZ_DEFLATE_BEST,
            )
    #log( '{=data compressed_length}')
    if not data or compressed_length == 0:
        return None
    buf = mupdf.FzBuffer(mupdf.fz_new_buffer_from_data(data, compressed_length))
    mupdf.fz_resize_buffer(buf, compressed_length)
    return buf


def JM_copy_rectangle(page, area):
    need_new_line = 0
    buffer = io.StringIO()
    for block in page:
        if block.m_internal.type != mupdf.FZ_STEXT_BLOCK_TEXT:
            continue
        for line in block:
            line_had_text = 0
            for ch in line:
                r = JM_char_bbox(line, ch)
                if JM_rects_overlap(area, r):
                    line_had_text = 1
                    if need_new_line:
                        buffer.write("\n")
                        need_new_line = 0
                    buffer.write(make_escape(ch.m_internal.c))
            if line_had_text:
                need_new_line = 1

    s = buffer.getvalue()   # take over the data
    return s


def JM_convert_to_pdf(doc, fp, tp, rotate):
    '''
    Convert any MuPDF document to a PDF
    Returns bytes object containing the PDF, created via 'write' function.
    '''
    pdfout = mupdf.PdfDocument()
    incr = 1
    s = fp
    e = tp
    if fp > tp:
        incr = -1   # count backwards
        s = tp      # adjust ...
        e = fp      # ... range
    rot = JM_norm_rotation(rotate)
    i = fp
    while 1:    # interpret & write document pages as PDF pages
        if not _INRANGE(i, s, e):
            break
        page = mupdf.fz_load_page(doc, i)
        mediabox = mupdf.fz_bound_page(page)
        dev, resources, contents = mupdf.pdf_page_write(pdfout, mediabox)
        mupdf.fz_run_page(page, dev, mupdf.FzMatrix(), mupdf.FzCookie())
        mupdf.fz_close_device(dev)
        dev = None
        page_obj = mupdf.pdf_add_page(pdfout, mediabox, rot, resources, contents)
        mupdf.pdf_insert_page(pdfout, -1, page_obj)
        i += incr
    # PDF created - now write it to Python bytearray
    # prepare write options structure
    opts = mupdf.PdfWriteOptions()
    opts.do_garbage         = 4
    opts.do_compress        = 1
    opts.do_compress_images = 1
    opts.do_compress_fonts  = 1
    opts.do_sanitize        = 1
    opts.do_incremental     = 0
    opts.do_ascii           = 0
    opts.do_decompress      = 0
    opts.do_linear          = 0
    opts.do_clean           = 1
    opts.do_pretty          = 0

    res = mupdf.fz_new_buffer(8192)
    out = mupdf.FzOutput(res)
    mupdf.pdf_write_document(pdfout, out, opts)
    out.fz_close_output()
    c = mupdf.fz_buffer_extract_copy(res)
    assert isinstance(c, bytes)
    return c


# Copied from MuPDF v1.14
# Create widget
def JM_create_widget(doc, page, type, fieldname):
    old_sigflags = mupdf.pdf_to_int(mupdf.pdf_dict_getp(mupdf.pdf_trailer(doc), "Root/AcroForm/SigFlags"))
    #log( '*** JM_create_widget()')
    #log( f'{mupdf.pdf_create_annot_raw=}')
    #log( f'{page=}')
    #log( f'{mupdf.PDF_ANNOT_WIDGET=}')
    annot = mupdf.pdf_create_annot_raw(page, mupdf.PDF_ANNOT_WIDGET)
    annot_obj = mupdf.pdf_annot_obj(annot)
    try:
        JM_set_field_type(doc, annot_obj, type)
        mupdf.pdf_dict_put_text_string(annot_obj, PDF_NAME('T'), fieldname)

        if type == mupdf.PDF_WIDGET_TYPE_SIGNATURE:
            sigflags = old_sigflags | (SigFlag_SignaturesExist | SigFlag_AppendOnly)
            mupdf.pdf_dict_putl(
                    mupdf.pdf_trailer(doc),
                    mupdf.pdf_new_int(sigflags),
                    PDF_NAME('Root'),
                    PDF_NAME('AcroForm'),
                    PDF_NAME('SigFlags'),
                    )
        # pdf_create_annot will have linked the new widget into the page's
        # annot array. We also need it linked into the document's form
        form = mupdf.pdf_dict_getp(mupdf.pdf_trailer(doc), "Root/AcroForm/Fields")
        if not form.m_internal:
            form = mupdf.pdf_new_array(doc, 1)
            mupdf.pdf_dict_putl(
                    mupdf.pdf_trailer(doc),
                    form,
                    PDF_NAME('Root'),
                    PDF_NAME('AcroForm'),
                    PDF_NAME('Fields'),
                    )
        mupdf.pdf_array_push(form, annot_obj)  # Cleanup relies on this statement being last
    except Exception:
        if g_exceptions_verbose:    exception_info()
        mupdf.pdf_delete_annot(page, annot)

        if type == mupdf.PDF_WIDGET_TYPE_SIGNATURE:
            mupdf.pdf_dict_putl(
                    mupdf.pdf_trailer(doc),
                    mupdf.pdf_new_int(old_sigflags),
                    PDF_NAME('Root'),
                    PDF_NAME('AcroForm'),
                    PDF_NAME('SigFlags'),
                    )
        raise
    return annot


def JM_cropbox(page_obj):
    '''
    return a PDF page's CropBox
    '''
    if g_use_extra:
        return extra.JM_cropbox(page_obj)
    
    mediabox = JM_mediabox(page_obj)
    cropbox = mupdf.pdf_to_rect(
                mupdf.pdf_dict_get_inheritable(page_obj, PDF_NAME('CropBox'))
                )
    if mupdf.fz_is_infinite_rect(cropbox) or mupdf.fz_is_empty_rect(cropbox):
        cropbox = mediabox
    y0 = mediabox.y1 - cropbox.y1
    y1 = mediabox.y1 - cropbox.y0
    cropbox.y0 = y0
    cropbox.y1 = y1
    return cropbox


def JM_cropbox_size(page_obj):
    rect = JM_cropbox(page_obj)
    w = abs(rect.x1 - rect.x0)
    h = abs(rect.y1 - rect.y0)
    size = mupdf.fz_make_point(w, h)
    return size


def JM_derotate_page_matrix(page):
    '''
    just the inverse of rotation
    '''
    mp = JM_rotate_page_matrix(page)
    return mupdf.fz_invert_matrix(mp)


def JM_embed_file(
        pdf,
        buf,
        filename,
        ufilename,
        desc,
        compress,
        ):
    '''
    embed a new file in a PDF (not only /EmbeddedFiles entries)
    '''
    len_ = 0
    val = mupdf.pdf_new_dict(pdf, 6)
    mupdf.pdf_dict_put_dict(val, PDF_NAME('CI'), 4)
    ef = mupdf.pdf_dict_put_dict(val, PDF_NAME('EF'), 4)
    mupdf.pdf_dict_put_text_string(val, PDF_NAME('F'), filename)
    mupdf.pdf_dict_put_text_string(val, PDF_NAME('UF'), ufilename)
    mupdf.pdf_dict_put_text_string(val, PDF_NAME('Desc'), desc)
    mupdf.pdf_dict_put(val, PDF_NAME('Type'), PDF_NAME('Filespec'))
    bs = b'  '
    f = mupdf.pdf_add_stream(
            pdf,
            #mupdf.fz_fz_new_buffer_from_copied_data(bs),
            mupdf.fz_new_buffer_from_copied_data(bs),
            mupdf.PdfObj(),
            0,
            )
    mupdf.pdf_dict_put(ef, PDF_NAME('F'), f)
    JM_update_stream(pdf, f, buf, compress)
    len_, _ = mupdf.fz_buffer_storage(buf)
    mupdf.pdf_dict_put_int(f, PDF_NAME('DL'), len_)
    mupdf.pdf_dict_put_int(f, PDF_NAME('Length'), len_)
    params = mupdf.pdf_dict_put_dict(f, PDF_NAME('Params'), 4)
    mupdf.pdf_dict_put_int(params, PDF_NAME('Size'), len_)
    return val


def JM_embedded_clean(pdf):
    '''
    perform some cleaning if we have /EmbeddedFiles:
    (1) remove any /Limits if /Names exists
    (2) remove any empty /Collection
    (3) set /PageMode/UseAttachments
    '''
    root = mupdf.pdf_dict_get( mupdf.pdf_trailer( pdf), PDF_NAME('Root'))

    # remove any empty /Collection entry
    coll = mupdf.pdf_dict_get(root, PDF_NAME('Collection'))
    if coll.m_internal and mupdf.pdf_dict_len(coll) == 0:
        mupdf.pdf_dict_del(root, PDF_NAME('Collection'))

    efiles = mupdf.pdf_dict_getl(
            root,
            PDF_NAME('Names'),
            PDF_NAME('EmbeddedFiles'),
            PDF_NAME('Names'),
            )
    if efiles.m_internal:
        mupdf.pdf_dict_put_name(root, PDF_NAME('PageMode'), "UseAttachments")


def JM_EscapeStrFromBuffer(buff):
    if not buff.m_internal:
        return ''
    s = mupdf.fz_buffer_extract_copy(buff)
    val = PyUnicode_DecodeRawUnicodeEscape(s, errors='replace')
    return val


def JM_ensure_identity(pdf):
    '''
    Store ID in PDF trailer
    '''
    id_ = mupdf.pdf_dict_get( mupdf.pdf_trailer(pdf), PDF_NAME('ID'))
    if not id_.m_internal:
        rnd0 = mupdf.fz_memrnd2(16)
        # Need to convert raw bytes into a str to send to
        # mupdf.pdf_new_string(). chr() seems to work for this.
        rnd = ''
        for i in rnd0:
            rnd += chr(i)
        id_ = mupdf.pdf_dict_put_array( mupdf.pdf_trailer( pdf), PDF_NAME('ID'), 2)
        mupdf.pdf_array_push( id_, mupdf.pdf_new_string( rnd, len(rnd)))
        mupdf.pdf_array_push( id_, mupdf.pdf_new_string( rnd, len(rnd)))

def JM_ensure_ocproperties(pdf):
    '''
    Ensure OCProperties, return /OCProperties key
    '''
    ocp = mupdf.pdf_dict_get(mupdf.pdf_dict_get(mupdf.pdf_trailer(pdf), PDF_NAME('Root')), PDF_NAME('OCProperties'))
    if ocp.m_internal:
        return ocp
    root = mupdf.pdf_dict_get(mupdf.pdf_trailer(pdf), PDF_NAME('Root'))
    ocp = mupdf.pdf_dict_put_dict(root, PDF_NAME('OCProperties'), 2)
    mupdf.pdf_dict_put_array(ocp, PDF_NAME('OCGs'), 0)
    D = mupdf.pdf_dict_put_dict(ocp, PDF_NAME('D'), 5)
    mupdf.pdf_dict_put_array(D, PDF_NAME('ON'), 0)
    mupdf.pdf_dict_put_array(D, PDF_NAME('OFF'), 0)
    mupdf.pdf_dict_put_array(D, PDF_NAME('Order'), 0)
    mupdf.pdf_dict_put_array(D, PDF_NAME('RBGroups'), 0)
    return ocp


def JM_expand_fname(name):
    '''
    Make /DA string of annotation
    '''
    if not name:    return "Helv"
    if name.startswith("Co"):   return "Cour"
    if name.startswith("co"):   return "Cour"
    if name.startswith("Ti"):   return "TiRo"
    if name.startswith("ti"):   return "TiRo"
    if name.startswith("Sy"):   return "Symb"
    if name.startswith("sy"):   return "Symb"
    if name.startswith("Za"):   return "ZaDb"
    if name.startswith("za"):   return "ZaDb"
    return "Helv"


def JM_field_type_text(wtype):
    '''
    String from widget type
    '''
    if wtype == mupdf.PDF_WIDGET_TYPE_BUTTON:
        return "Button"
    if wtype == mupdf.PDF_WIDGET_TYPE_CHECKBOX:
        return "CheckBox"
    if wtype == mupdf.PDF_WIDGET_TYPE_RADIOBUTTON:
        return "RadioButton"
    if wtype == mupdf.PDF_WIDGET_TYPE_TEXT:
        return "Text"
    if wtype == mupdf.PDF_WIDGET_TYPE_LISTBOX:
        return "ListBox"
    if wtype == mupdf.PDF_WIDGET_TYPE_COMBOBOX:
        return "ComboBox"
    if wtype == mupdf.PDF_WIDGET_TYPE_SIGNATURE:
        return "Signature"
    return "unknown"


def JM_fill_pixmap_rect_with_color(dest, col, b):
    assert isinstance(dest, mupdf.FzPixmap)
    # fill a rect with a color tuple
    b = mupdf.fz_intersect_irect(b, mupdf.fz_pixmap_bbox( dest))
    w = b.x1 - b.x0
    y = b.y1 - b.y0
    if w <= 0 or y <= 0:
        return 0
    destspan = dest.stride()
    destp = destspan * (b.y0 - dest.y()) + dest.n() * (b.x0 - dest.x())
    while 1:
        s = destp
        for x in range(w):
            for i in range( dest.n()):
                mupdf.fz_samples_set(dest, s, col[i])
                s += 1
        destp += destspan
        y -= 1
        if y == 0:
            break
    return 1


def JM_find_annot_irt(annot):
    '''
    Return the first annotation whose /IRT key ("In Response To") points to
    annot. Used to remove the response chain of a given annotation.
    '''
    assert isinstance(annot, mupdf.PdfAnnot)
    irt_annot = None    # returning this
    annot_obj = mupdf.pdf_annot_obj(annot)
    found = 0
    # loop thru MuPDF's internal annots array
    page = _pdf_annot_page(annot)
    irt_annot = mupdf.pdf_first_annot(page)
    while 1:
        assert isinstance(irt_annot, mupdf.PdfAnnot)
        if not irt_annot.m_internal:
            break
        irt_annot_obj = mupdf.pdf_annot_obj(irt_annot)
        o = mupdf.pdf_dict_gets(irt_annot_obj, 'IRT')
        if o.m_internal:
            if not mupdf.pdf_objcmp(o, annot_obj):
                found = 1
                break
        irt_annot = mupdf.pdf_next_annot(irt_annot)
    if found:
        return irt_annot


def JM_font_ascender(font):
    '''
    need own versions of ascender / descender
    '''
    assert isinstance(font, mupdf.FzFont)
    if _globals.skip_quad_corrections:
        return 0.8
    return mupdf.fz_font_ascender(font)


def JM_font_descender(font):
    '''
    need own versions of ascender / descender
    '''
    assert isinstance(font, mupdf.FzFont)
    if _globals.skip_quad_corrections:
        return -0.2
    ret = mupdf.fz_font_descender(font)
    return ret


def JM_is_word_delimiter(ch, delimiters):
    """Check if ch is an extra word delimiting character.
    """
    if (0
        or ch <= 32
        or ch == 160
        or 0x202a <= ch <= 0x202e
    ):
        # covers any whitespace plus unicodes that switch between
        # right-to-left and left-to-right languages
        return True
    if not delimiters:  # no extra delimiters provided
        return False
    char = chr(ch)
    for d in delimiters:
        if d == char:
            return True
    return False
    

def JM_is_rtl_char(ch):
    if ch < 0x590 or ch > 0x900:
        return False
    return True


def JM_font_name(font):
    assert isinstance(font, mupdf.FzFont)
    name = mupdf.fz_font_name(font)
    s = name.find('+')
    if _globals.subset_fontnames or s == -1 or s != 6:
        return name
    return name[s + 1:]


def JM_gather_fonts(pdf, dict_, fontlist, stream_xref):
    rc = 1
    n = mupdf.pdf_dict_len(dict_)
    for i in range(n):

        refname = mupdf.pdf_dict_get_key(dict_, i)
        fontdict = mupdf.pdf_dict_get_val(dict_, i)
        if not mupdf.pdf_is_dict(fontdict):
            mupdf.fz_warn( f"'{mupdf.pdf_to_name(refname)}' is no font dict ({mupdf.pdf_to_num(fontdict)} 0 R)")
            continue

        subtype = mupdf.pdf_dict_get(fontdict, mupdf.PDF_ENUM_NAME_Subtype)
        basefont = mupdf.pdf_dict_get(fontdict, mupdf.PDF_ENUM_NAME_BaseFont)
        if not basefont.m_internal or mupdf.pdf_is_null(basefont):
            name = mupdf.pdf_dict_get(fontdict, mupdf.PDF_ENUM_NAME_Name)
        else:
            name = basefont
        encoding = mupdf.pdf_dict_get(fontdict, mupdf.PDF_ENUM_NAME_Encoding)
        if mupdf.pdf_is_dict(encoding):
            encoding = mupdf.pdf_dict_get(encoding, mupdf.PDF_ENUM_NAME_BaseEncoding)
        xref = mupdf.pdf_to_num(fontdict)
        ext = "n/a"
        if xref:
            ext = JM_get_fontextension(pdf, xref)
        entry = (
                xref,
                ext,
                mupdf.pdf_to_name(subtype),
                JM_EscapeStrFromStr(mupdf.pdf_to_name(name)),
                mupdf.pdf_to_name(refname),
                mupdf.pdf_to_name(encoding),
                stream_xref,
                )
        fontlist.append(entry)
    return rc


def JM_gather_forms(doc, dict_: mupdf.PdfObj, imagelist, stream_xref: int):
    '''
    Store info of a /Form xobject in Python list
    '''
    assert isinstance(doc, mupdf.PdfDocument)
    rc = 1
    n = mupdf.pdf_dict_len(dict_)
    for i in range(n):
        refname = mupdf.pdf_dict_get_key( dict_, i)
        imagedict = mupdf.pdf_dict_get_val(dict_, i)
        if not mupdf.pdf_is_dict(imagedict):
            mupdf.fz_warn( f"'{mupdf.pdf_to_name(refname)}' is no form dict ({mupdf.pdf_to_num(imagedict)} 0 R)")
            continue

        type_ = mupdf.pdf_dict_get(imagedict, PDF_NAME('Subtype'))
        if not mupdf.pdf_name_eq(type_, PDF_NAME('Form')):
            continue

        o = mupdf.pdf_dict_get(imagedict, PDF_NAME('BBox'))
        m = mupdf.pdf_dict_get(imagedict, PDF_NAME('Matrix'))
        if m.m_internal:
            mat = mupdf.pdf_to_matrix(m)
        else:
            mat = mupdf.FzMatrix()
        if o.m_internal:
            bbox = mupdf.fz_transform_rect( mupdf.pdf_to_rect(o), mat)
        else:
            bbox = mupdf.FzRect(mupdf.FzRect.Fixed_INFINITE)
        xref = mupdf.pdf_to_num(imagedict)

        entry = (
                xref,
                mupdf.pdf_to_name( refname),
                stream_xref,
                JM_py_from_rect(bbox),
                )
        imagelist.append(entry)
    return rc


def JM_gather_images(doc: mupdf.PdfDocument, dict_: mupdf.PdfObj, imagelist, stream_xref: int):
    '''
    Store info of an image in Python list
    '''
    rc = 1
    n = mupdf.pdf_dict_len( dict_)
    for i in range(n):
        refname = mupdf.pdf_dict_get_key(dict_, i)
        imagedict = mupdf.pdf_dict_get_val(dict_, i)
        if not mupdf.pdf_is_dict(imagedict):
            mupdf.fz_warn(f"'{mupdf.pdf_to_name(refname)}' is no image dict ({mupdf.pdf_to_num(imagedict)} 0 R)")
            continue

        type_ = mupdf.pdf_dict_get(imagedict, PDF_NAME('Subtype'))
        if not mupdf.pdf_name_eq(type_, PDF_NAME('Image')):
            continue

        xref = mupdf.pdf_to_num(imagedict)
        gen = 0
        smask = mupdf.pdf_dict_geta(imagedict, PDF_NAME('SMask'), PDF_NAME('Mask'))
        if smask.m_internal:
            gen = mupdf.pdf_to_num(smask)

        filter_ = mupdf.pdf_dict_geta(imagedict, PDF_NAME('Filter'), PDF_NAME('F'))
        if mupdf.pdf_is_array(filter_):
            filter_ = mupdf.pdf_array_get(filter_, 0)

        altcs = mupdf.PdfObj(0)
        cs = mupdf.pdf_dict_geta(imagedict, PDF_NAME('ColorSpace'), PDF_NAME('CS'))
        if mupdf.pdf_is_array(cs):
            cses = cs
            cs = mupdf.pdf_array_get(cses, 0)
            if (mupdf.pdf_name_eq(cs, PDF_NAME('DeviceN'))
                    or mupdf.pdf_name_eq(cs, PDF_NAME('Separation'))
                    ):
                altcs = mupdf.pdf_array_get(cses, 2)
                if mupdf.pdf_is_array(altcs):
                    altcs = mupdf.pdf_array_get(altcs, 0)
        width = mupdf.pdf_dict_geta(imagedict, PDF_NAME('Width'), PDF_NAME('W'))
        height = mupdf.pdf_dict_geta(imagedict, PDF_NAME('Height'), PDF_NAME('H'))
        bpc = mupdf.pdf_dict_geta(imagedict, PDF_NAME('BitsPerComponent'), PDF_NAME('BPC'))

        entry = (
                xref,
                gen,
                mupdf.pdf_to_int(width),
                mupdf.pdf_to_int(height),
                mupdf.pdf_to_int(bpc),
                JM_EscapeStrFromStr(mupdf.pdf_to_name(cs)),
                JM_EscapeStrFromStr(mupdf.pdf_to_name(altcs)),
                JM_EscapeStrFromStr(mupdf.pdf_to_name(refname)),
                JM_EscapeStrFromStr(mupdf.pdf_to_name(filter_)),
                stream_xref,
                )
        imagelist.append(entry)
    return rc


def JM_get_annot_by_xref(page, xref):
    '''
    retrieve annot by its xref
    '''
    assert isinstance(page, mupdf.PdfPage)
    found = 0
    # loop thru MuPDF's internal annots array
    annot = mupdf.pdf_first_annot(page)
    while 1:
        if not annot.m_internal:
            break
        if xref == mupdf.pdf_to_num(mupdf.pdf_annot_obj(annot)):
            found = 1
            break
        annot = mupdf.pdf_next_annot( annot)
    if not found:
        raise Exception("xref %d is not an annot of this page" % xref)
    return annot


def JM_get_annot_by_name(page, name):
    '''
    retrieve annot by name (/NM key)
    '''
    assert isinstance(page, mupdf.PdfPage)
    if not name:
        return
    found = 0
    # loop thru MuPDF's internal annots and widget arrays
    annot = mupdf.pdf_first_annot(page)
    while 1:
        if not annot.m_internal:
            break

        response, len_ = mupdf.pdf_to_string(mupdf.pdf_dict_gets(mupdf.pdf_annot_obj(annot), "NM"))
        if name == response:
            found = 1
            break
        annot = mupdf.pdf_next_annot(annot)
    if not found:
        raise Exception("'%s' is not an annot of this page" % name)
    return annot


def JM_get_annot_id_list(page):
    names = []
    annots = mupdf.pdf_dict_get( page.obj(), mupdf.PDF_ENUM_NAME_Annots)
    if not annots.m_internal:
        return names
    for i in range( mupdf.pdf_array_len(annots)):
        annot_obj = mupdf.pdf_array_get(annots, i)
        name = mupdf.pdf_dict_gets(annot_obj, "NM")
        if name.m_internal:
            names.append(
                mupdf.pdf_to_text_string(name)
                )
    return names

def JM_get_annot_xref_list( page_obj):
    '''
    return the xrefs and /NM ids of a page's annots, links and fields
    '''
    if g_use_extra:
        names = extra.JM_get_annot_xref_list( page_obj)
        return names
    
    names = []
    annots = mupdf.pdf_dict_get( page_obj, PDF_NAME('Annots'))
    n = mupdf.pdf_array_len( annots)
    for i in range( n):
        annot_obj = mupdf.pdf_array_get( annots, i)
        xref = mupdf.pdf_to_num( annot_obj)
        subtype = mupdf.pdf_dict_get( annot_obj, PDF_NAME('Subtype'))
        if not subtype.m_internal:
            continue    # subtype is required
        type_ = mupdf.pdf_annot_type_from_string( mupdf.pdf_to_name( subtype))
        if type_ == mupdf.PDF_ANNOT_UNKNOWN:
            continue    # only accept valid annot types
        id_ = mupdf.pdf_dict_gets( annot_obj, "NM")
        names.append( (xref, type_, mupdf.pdf_to_text_string( id_)))
    return names


def JM_get_annot_xref_list2(page):
    page = page._pdf_page(required=False)
    if not page.m_internal:
        return list()
    return JM_get_annot_xref_list( page.obj())


def JM_get_border_style(style):
    '''
    return pdf_obj "border style" from Python str
    '''
    val = mupdf.PDF_ENUM_NAME_S
    if style is None:
        return val
    s = style
    if   s.startswith("b") or s.startswith("B"):    val = mupdf.PDF_ENUM_NAME_B
    elif s.startswith("d") or s.startswith("D"):    val = mupdf.PDF_ENUM_NAME_D
    elif s.startswith("i") or s.startswith("I"):    val = mupdf.PDF_ENUM_NAME_I
    elif s.startswith("u") or s.startswith("U"):    val = mupdf.PDF_ENUM_NAME_U
    elif s.startswith("s") or s.startswith("S"):    val = mupdf.PDF_ENUM_NAME_S
    return val


def JM_get_font(
        fontname,
        fontfile,
        fontbuffer,
        script,
        lang,
        ordering,
        is_bold,
        is_italic,
        is_serif,
        embed,
        ):
    '''
    return a fz_font from a number of parameters
    '''
    def fertig(font):
        if not font.m_internal:
            raise RuntimeError(MSG_FONT_FAILED)
        # if font allows this, set embedding
        if not font.m_internal.flags.never_embed:
            mupdf.fz_set_font_embedding(font, embed)
        return font
    
    index = 0
    font = None
    if fontfile:
        #goto have_file;
        font = mupdf.fz_new_font_from_file( None, fontfile, index, 0)
        return fertig(font)

    if fontbuffer:
        #goto have_buffer;
        res = JM_BufferFromBytes(fontbuffer)
        font = mupdf.fz_new_font_from_buffer( None, res, index, 0)
        return fertig(font)

    if ordering > -1:
        # goto have_cjk;
        font = mupdf.fz_new_cjk_font(ordering)
        return fertig(font)

    if fontname:
        # goto have_base14;
        # Base-14 or a MuPDF builtin font
        font = mupdf.fz_new_base14_font(fontname)
        if font.m_internal:
            return fertig(font)
        font = mupdf.fz_new_builtin_font(fontname, is_bold, is_italic)
        return fertig(font)
    
    # Check for NOTO font
    #have_noto:;
    data, size, index = mupdf.fz_lookup_noto_font( script, lang)
    font = None
    if data:
        font = mupdf.fz_new_font_from_memory( None, data, size, index, 0)
    if font.m_internal:
        return fertig(font)
    font = mupdf.fz_load_fallback_font( script, lang, is_serif, is_bold, is_italic)
    return fertig(font)
    

def JM_get_fontbuffer(doc, xref):
    '''
    Return the contents of a font file, identified by xref
    '''
    if xref < 1:
        return
    o = mupdf.pdf_load_object(doc, xref)
    desft = mupdf.pdf_dict_get(o, PDF_NAME('DescendantFonts'))
    if desft.m_internal:
        obj = mupdf.pdf_resolve_indirect(mupdf.pdf_array_get(desft, 0))
        obj = mupdf.pdf_dict_get(obj, PDF_NAME('FontDescriptor'))
    else:
        obj = mupdf.pdf_dict_get(o, PDF_NAME('FontDescriptor'))

    if not obj.m_internal:
        message(f"invalid font - FontDescriptor missing")
        return

    o = obj

    stream = None

    obj = mupdf.pdf_dict_get(o, PDF_NAME('FontFile'))
    if obj.m_internal:
        stream = obj    # ext = "pfa"

    obj = mupdf.pdf_dict_get(o, PDF_NAME('FontFile2'))
    if obj.m_internal:
        stream = obj    # ext = "ttf"

    obj = mupdf.pdf_dict_get(o, PDF_NAME('FontFile3'))
    if obj.m_internal:
        stream = obj

        obj = mupdf.pdf_dict_get(obj, PDF_NAME('Subtype'))
        if obj.m_internal and not mupdf.pdf_is_name(obj):
            message("invalid font descriptor subtype")
            return

        if mupdf.pdf_name_eq(obj, PDF_NAME('Type1C')):
            pass    # Prev code did: ext = "cff", but this has no effect.
        elif mupdf.pdf_name_eq(obj, PDF_NAME('CIDFontType0C')):
            pass    # Prev code did: ext = "cid", but this has no effect.
        elif mupdf.pdf_name_eq(obj, PDF_NAME('OpenType')):
            pass    # Prev code did: ext = "otf", but this has no effect. */
        else:
            message('warning: unhandled font type {pdf_to_name(ctx, obj)!r}')

    if not stream:
        message('warning: unhandled font type')
        return

    return mupdf.pdf_load_stream(stream)


def JM_get_resource_properties(ref):
    '''
    Return the items of Resources/Properties (used for Marked Content)
    Argument may be e.g. a page object or a Form XObject
    '''
    properties = mupdf.pdf_dict_getl(ref, PDF_NAME('Resources'), PDF_NAME('Properties'))
    if not properties.m_internal:
        return ()
    else:
        n = mupdf.pdf_dict_len(properties)
        if n < 1:
            return ()
        rc = []
        for i in range(n):
            key = mupdf.pdf_dict_get_key(properties, i)
            val = mupdf.pdf_dict_get_val(properties, i)
            c = mupdf.pdf_to_name(key)
            xref = mupdf.pdf_to_num(val)
            rc.append((c, xref))
    return rc


def JM_get_widget_by_xref( page, xref):
    '''
    retrieve widget by its xref
    '''
    found = False
    annot = mupdf.pdf_first_widget( page)
    while annot.m_internal:
        annot_obj = mupdf.pdf_annot_obj( annot)
        if xref == mupdf.pdf_to_num( annot_obj):
            found = True
            break
        annot = mupdf.pdf_next_widget( annot)
    if not found:
        raise Exception( f"xref {xref} is not a widget of this page")
    return Annot( annot)


def JM_get_widget_properties(annot, Widget):
    '''
    Populate a Python Widget object with the values from a PDF form field.
    Called by "Page.first_widget" and "Widget.next".
    '''
    #log( '{type(annot)=}')
    annot_obj = mupdf.pdf_annot_obj(annot.this)
    #log( 'Have called mupdf.pdf_annot_obj()')
    page = _pdf_annot_page(annot.this)
    pdf = page.doc()
    tw = annot

    def SETATTR(key, value):
        setattr(Widget, key, value)

    def SETATTR_DROP(mod, key, value):
        # Original C code for this function deletes if PyObject* is NULL. We
        # don't have a representation for that in Python - e.g. None is not
        # represented by NULL.
        setattr(mod, key, value)

    #log( '=== + mupdf.pdf_widget_type(tw)')
    field_type = mupdf.pdf_widget_type(tw.this)
    #log( '=== - mupdf.pdf_widget_type(tw)')
    Widget.field_type = field_type
    if field_type == mupdf.PDF_WIDGET_TYPE_SIGNATURE:
        if mupdf.pdf_signature_is_signed(pdf, annot_obj):
            SETATTR("is_signed", True)
        else:
            SETATTR("is_signed",False)
    else:
        SETATTR("is_signed", None)
    SETATTR_DROP(Widget, "border_style", JM_UnicodeFromStr(mupdf.pdf_field_border_style(annot_obj)))
    SETATTR_DROP(Widget, "field_type_string", JM_UnicodeFromStr(JM_field_type_text(field_type)))

    field_name = mupdf.pdf_load_field_name(annot_obj)
    SETATTR_DROP(Widget, "field_name", field_name)

    def pdf_dict_get_inheritable_nonempty_label(node, key):
        '''
        This is a modified version of MuPDF's pdf_dict_get_inheritable(), with
        some changes:
        * Returns string from pdf_to_text_string() or None if not found.
        * Recurses to parent if current node exists but with empty string
          value.
        '''
        slow = node
        halfbeat = 11   # Don't start moving slow pointer for a while.
        while 1:
            if not node.m_internal:
                return
            val = mupdf.pdf_dict_get(node, key)
            if val.m_internal:
                label = mupdf.pdf_to_text_string(val)
                if label:
                    return label
            node = mupdf.pdf_dict_get(node, PDF_NAME('Parent'))
            if node.m_internal == slow.m_internal:
                raise Exception("cycle in resources")
            halfbeat -= 1
            if halfbeat == 0:
                slow = mupdf.pdf_dict_get(slow, PDF_NAME('Parent'))
                halfbeat = 2
    
    # In order to address #3950, we use our modified pdf_dict_get_inheritable()
    # to ignore empty-string child values.
    label = pdf_dict_get_inheritable_nonempty_label(annot_obj, PDF_NAME('TU'))
    if label is not None:
        SETATTR_DROP(Widget, "field_label", label)

    fvalue = None
    if field_type == mupdf.PDF_WIDGET_TYPE_RADIOBUTTON:
        obj = mupdf.pdf_dict_get( annot_obj, PDF_NAME('Parent'))    # owning RB group
        if obj.m_internal:
            SETATTR_DROP(Widget, "rb_parent", mupdf.pdf_to_num( obj))
        obj = mupdf.pdf_dict_get(annot_obj, PDF_NAME('AS'))
        if obj.m_internal:
            fvalue = mupdf.pdf_to_name(obj)
    if not fvalue:
        fvalue = mupdf.pdf_field_value(annot_obj)
    SETATTR_DROP(Widget, "field_value", JM_UnicodeFromStr(fvalue))

    SETATTR_DROP(Widget, "field_display", mupdf.pdf_field_display(annot_obj))

    border_width = mupdf.pdf_to_real(mupdf.pdf_dict_getl(annot_obj, PDF_NAME('BS'), PDF_NAME('W')))
    if border_width == 0:
        border_width = 1
    SETATTR_DROP(Widget, "border_width", border_width)

    obj = mupdf.pdf_dict_getl(annot_obj, PDF_NAME('BS'), PDF_NAME('D'))
    if mupdf.pdf_is_array(obj):
        n = mupdf.pdf_array_len(obj)
        d = [0] * n
        for i in range(n):
            d[i] = mupdf.pdf_to_int(mupdf.pdf_array_get(obj, i))
        SETATTR_DROP(Widget, "border_dashes", d)

    SETATTR_DROP(Widget, "text_maxlen", mupdf.pdf_text_widget_max_len(tw.this))

    SETATTR_DROP(Widget, "text_format", mupdf.pdf_text_widget_format(tw.this))

    obj = mupdf.pdf_dict_getl(annot_obj, PDF_NAME('MK'), PDF_NAME('BG'))
    if mupdf.pdf_is_array(obj):
        n = mupdf.pdf_array_len(obj)
        col = [0] * n
        for i in range(n):
            col[i] = mupdf.pdf_to_real(mupdf.pdf_array_get(obj, i))
        SETATTR_DROP(Widget, "fill_color", col)

    obj = mupdf.pdf_dict_getl(annot_obj, PDF_NAME('MK'), PDF_NAME('BC'))
    if mupdf.pdf_is_array(obj):
        n = mupdf.pdf_array_len(obj)
        col = [0] * n
        for i in range(n):
            col[i] = mupdf.pdf_to_real(mupdf.pdf_array_get(obj, i))
        SETATTR_DROP(Widget, "border_color", col)

    SETATTR_DROP(Widget, "choice_values", JM_choice_options(annot))

    da = mupdf.pdf_to_text_string(mupdf.pdf_dict_get_inheritable(annot_obj, PDF_NAME('DA')))
    SETATTR_DROP(Widget, "_text_da", JM_UnicodeFromStr(da))

    obj = mupdf.pdf_dict_getl(annot_obj, PDF_NAME('MK'), PDF_NAME('CA'))
    if obj.m_internal:
        SETATTR_DROP(Widget, "button_caption", JM_UnicodeFromStr(mupdf.pdf_to_text_string(obj)))

    SETATTR_DROP(Widget, "field_flags", mupdf.pdf_field_flags(annot_obj))

    # call Py method to reconstruct text color, font name, size
    Widget._parse_da()

    # extract JavaScript action texts
    s = mupdf.pdf_dict_get(annot_obj, PDF_NAME('A'))
    ss = JM_get_script(s)
    SETATTR_DROP(Widget, "script", ss)

    SETATTR_DROP(Widget, "script_stroke",
            JM_get_script(mupdf.pdf_dict_getl(annot_obj, PDF_NAME('AA'), PDF_NAME('K')))
            )

    SETATTR_DROP(Widget, "script_format",
            JM_get_script(mupdf.pdf_dict_getl(annot_obj, PDF_NAME('AA'), PDF_NAME('F')))
            )

    SETATTR_DROP(Widget, "script_change",
            JM_get_script(mupdf.pdf_dict_getl(annot_obj, PDF_NAME('AA'), PDF_NAME('V')))
            )

    SETATTR_DROP(Widget, "script_calc",
            JM_get_script(mupdf.pdf_dict_getl(annot_obj, PDF_NAME('AA'), PDF_NAME('C')))
            )

    SETATTR_DROP(Widget, "script_blur",
            JM_get_script(mupdf.pdf_dict_getl(annot_obj, PDF_NAME('AA'), mupdf.pdf_new_name('Bl')))
            )

    SETATTR_DROP(Widget, "script_focus",
            JM_get_script(mupdf.pdf_dict_getl(annot_obj, PDF_NAME('AA'), mupdf.pdf_new_name('Fo')))
            )


def JM_get_fontextension(doc, xref):
    '''
    Return the file extension of a font file, identified by xref
    '''
    if xref < 1:
        return "n/a"
    o = mupdf.pdf_load_object(doc, xref)
    desft = mupdf.pdf_dict_get(o, PDF_NAME('DescendantFonts'))
    if desft.m_internal:
        obj = mupdf.pdf_resolve_indirect(mupdf.pdf_array_get(desft, 0))
        obj = mupdf.pdf_dict_get(obj, PDF_NAME('FontDescriptor'))
    else:
        obj = mupdf.pdf_dict_get(o, PDF_NAME('FontDescriptor'))
    if not obj.m_internal:
        return "n/a"    # this is a base-14 font

    o = obj # we have the FontDescriptor

    obj = mupdf.pdf_dict_get(o, PDF_NAME('FontFile'))
    if obj.m_internal:
        return "pfa"

    obj = mupdf.pdf_dict_get(o, PDF_NAME('FontFile2'))
    if obj.m_internal:
        return "ttf"

    obj = mupdf.pdf_dict_get(o, PDF_NAME('FontFile3'))
    if obj.m_internal:
        obj = mupdf.pdf_dict_get(obj, PDF_NAME('Subtype'))
        if obj.m_internal and not mupdf.pdf_is_name(obj):
            message("invalid font descriptor subtype")
            return "n/a"
        if mupdf.pdf_name_eq(obj, PDF_NAME('Type1C')):
            return "cff"
        elif mupdf.pdf_name_eq(obj, PDF_NAME('CIDFontType0C')):
            return "cid"
        elif mupdf.pdf_name_eq(obj, PDF_NAME('OpenType')):
            return "otf"
        else:
            message("unhandled font type '%s'", mupdf.pdf_to_name(obj))

    return "n/a"


def JM_get_ocg_arrays_imp(arr):
    '''
    Get OCG arrays from OC configuration
    Returns dict {"basestate":name, "on":list, "off":list, "rbg":list, "locked":list}
    '''
    list_ = list()
    if mupdf.pdf_is_array( arr):
        n = mupdf.pdf_array_len( arr)
        for i in range(n):
            obj = mupdf.pdf_array_get( arr, i)
            item = mupdf.pdf_to_num( obj)
            if item not in list_:
                list_.append(item)
    return list_


def JM_get_ocg_arrays(conf):

    rc = dict()
    arr = mupdf.pdf_dict_get( conf, PDF_NAME('ON'))
    list_ = JM_get_ocg_arrays_imp( arr)
    if list_:
        rc["on"] = list_
    arr = mupdf.pdf_dict_get( conf, PDF_NAME('OFF'))
    list_ = JM_get_ocg_arrays_imp( arr)
    if list_:
        rc["off"] = list_
    arr = mupdf.pdf_dict_get( conf, PDF_NAME('Locked'))
    list_ = JM_get_ocg_arrays_imp( arr)
    if list_:
        rc['locked'] = list_
    list_ = list()
    arr = mupdf.pdf_dict_get( conf, PDF_NAME('RBGroups'))
    if mupdf.pdf_is_array( arr):
        n = mupdf.pdf_array_len( arr)
        for i in range(n):
            obj = mupdf.pdf_array_get( arr, i)
            list1 = JM_get_ocg_arrays_imp( obj)
            list_.append(list1)
    if list_:
        rc["rbgroups"] = list_
    obj = mupdf.pdf_dict_get( conf, PDF_NAME('BaseState'))

    if obj.m_internal:
        state = mupdf.pdf_to_name( obj)
        rc["basestate"] = state
    return rc


def JM_get_page_labels(liste, nums):
    n = mupdf.pdf_array_len(nums)
    for i in range(0, n, 2):
        key = mupdf.pdf_resolve_indirect( mupdf.pdf_array_get(nums, i))
        pno = mupdf.pdf_to_int(key)
        val = mupdf.pdf_resolve_indirect( mupdf.pdf_array_get(nums, i + 1))
        res = JM_object_to_buffer(val, 1, 0)
        c = mupdf.fz_buffer_extract(res)
        assert isinstance(c, bytes)
        c = c.decode('utf-8')
        liste.append( (pno, c))


def JM_get_script(key):
    '''
    JavaScript extractor
    Returns either the script source or None. Parameter is a PDF action
    dictionary, which must have keys /S and /JS. The value of /S must be
    '/JavaScript'. The value of /JS is returned.
    '''
    if not key.m_internal:
        return

    j = mupdf.pdf_dict_get(key, PDF_NAME('S'))
    jj = mupdf.pdf_to_name(j)
    if jj == "JavaScript":
        js = mupdf.pdf_dict_get(key, PDF_NAME('JS'))
        if not js.m_internal:
            return
    else:
        return

    if mupdf.pdf_is_string(js):
        script = JM_UnicodeFromStr(mupdf.pdf_to_text_string(js))
    elif mupdf.pdf_is_stream(js):
        res = mupdf.pdf_load_stream(js)
        script = JM_EscapeStrFromBuffer(res)
    else:
        return
    if script:  # do not return an empty script
        return script
    return


def JM_have_operation(pdf):
    '''
    Ensure valid journalling state
    '''
    if pdf.m_internal.journal and not mupdf.pdf_undoredo_step(pdf, 0):
        return 0
    return 1


def JM_image_extension(type_):
    '''
    return extension for MuPDF image type
    '''
    if type_ == mupdf.FZ_IMAGE_FAX:     return "fax"
    if type_ == mupdf.FZ_IMAGE_RAW:     return "raw"
    if type_ == mupdf.FZ_IMAGE_FLATE:   return "flate"
    if type_ == mupdf.FZ_IMAGE_LZW:     return "lzw"
    if type_ == mupdf.FZ_IMAGE_RLD:     return "rld"
    if type_ == mupdf.FZ_IMAGE_BMP:     return "bmp"
    if type_ == mupdf.FZ_IMAGE_GIF:     return "gif"
    if type_ == mupdf.FZ_IMAGE_JBIG2:   return "jb2"
    if type_ == mupdf.FZ_IMAGE_JPEG:    return "jpeg"
    if type_ == mupdf.FZ_IMAGE_JPX:     return "jpx"
    if type_ == mupdf.FZ_IMAGE_JXR:     return "jxr"
    if type_ == mupdf.FZ_IMAGE_PNG:     return "png"
    if type_ == mupdf.FZ_IMAGE_PNM:     return "pnm"
    if type_ == mupdf.FZ_IMAGE_TIFF:    return "tiff"
    #if type_ == mupdf.FZ_IMAGE_PSD:     return "psd"
    return "n/a"


# fixme: need to avoid using a global for this.
g_img_info = None


def JM_image_filter(opaque, ctm, name, image):
    assert isinstance(ctm, mupdf.FzMatrix)
    r = mupdf.FzRect(mupdf.FzRect.Fixed_UNIT)
    q = mupdf.fz_transform_quad( mupdf.fz_quad_from_rect(r), ctm)
    q = mupdf.fz_transform_quad( q, g_img_info_matrix)
    temp = name, JM_py_from_quad(q)
    g_img_info.append(temp)


def JM_image_profile( imagedata, keep_image):
    '''
    Return basic properties of an image provided as bytes or bytearray
    The function creates an fz_image and optionally returns it.
    '''
    if not imagedata:
        return None # nothing given
    
    len_ = len( imagedata)
    if len_ < 8:
        message( "bad image data")
        return None
    c = imagedata
    #log( 'calling mfz_recognize_image_format with {c!r=}')
    type_ = mupdf.fz_recognize_image_format( c)
    if type_ == mupdf.FZ_IMAGE_UNKNOWN:
        return None

    if keep_image:
        res = mupdf.fz_new_buffer_from_copied_data( c, len_)
    else:
        res = mupdf.fz_new_buffer_from_shared_data( c, len_)
    image = mupdf.fz_new_image_from_buffer( res)
    ctm = mupdf.fz_image_orientation_matrix( image)
    xres, yres = mupdf.fz_image_resolution(image)
    orientation = mupdf.fz_image_orientation( image)
    cs_name = mupdf.fz_colorspace_name( image.colorspace())
    result = dict()
    result[ dictkey_width] = image.w()
    result[ dictkey_height] = image.h()
    result[ "orientation"] = orientation
    result[ dictkey_matrix] = JM_py_from_matrix(ctm)
    result[ dictkey_xres] = xres
    result[ dictkey_yres] = yres
    result[ dictkey_colorspace] = image.n()
    result[ dictkey_bpc] = image.bpc()
    result[ dictkey_ext] = JM_image_extension(type_)
    result[ dictkey_cs_name] = cs_name

    if keep_image:
        result[ dictkey_image] = image
    return result


def JM_image_reporter(page):
    doc = page.doc()
    global g_img_info_matrix
    g_img_info_matrix = mupdf.FzMatrix()
    mediabox = mupdf.FzRect()
    mupdf.pdf_page_transform(page, mediabox, g_img_info_matrix)

    class SanitizeFilterOptions(mupdf.PdfSanitizeFilterOptions2):
        def __init__(self):
            super().__init__()
            self.use_virtual_image_filter()
        def image_filter(self, ctx, ctm, name, image, scissor):
            JM_image_filter(None, mupdf.FzMatrix(ctm), name, image)

    sanitize_filter_options = SanitizeFilterOptions()

    filter_options = _make_PdfFilterOptions(
            instance_forms=1,
            ascii=1,
            no_update=1,
            sanitize=1,
            sopts=sanitize_filter_options,
            )

    global g_img_info
    g_img_info = []

    mupdf.pdf_filter_page_contents( doc, page, filter_options)

    rc = tuple(g_img_info)
    g_img_info = []
    return rc


def JM_fitz_config():
    have_TOFU           = not hasattr(mupdf, 'TOFU')
    have_TOFU_BASE14    = not hasattr(mupdf, 'TOFU_BASE14')
    have_TOFU_CJK       = not hasattr(mupdf, 'TOFU_CJK')
    have_TOFU_CJK_EXT   = not hasattr(mupdf, 'TOFU_CJK_EXT')
    have_TOFU_CJK_LANG  = not hasattr(mupdf, 'TOFU_CJK_LANG')
    have_TOFU_EMOJI     = not hasattr(mupdf, 'TOFU_EMOJI')
    have_TOFU_HISTORIC  = not hasattr(mupdf, 'TOFU_HISTORIC')
    have_TOFU_SIL       = not hasattr(mupdf, 'TOFU_SIL')
    have_TOFU_SYMBOL    = not hasattr(mupdf, 'TOFU_SYMBOL')
    
    ret = dict()
    ret["base14"]           = have_TOFU_BASE14
    ret["cbz"]              = bool(mupdf.FZ_ENABLE_CBZ)
    ret["epub"]             = bool(mupdf.FZ_ENABLE_EPUB)
    ret["html"]             = bool(mupdf.FZ_ENABLE_HTML)
    ret["icc"]              = bool(mupdf.FZ_ENABLE_ICC)
    ret["img"]              = bool(mupdf.FZ_ENABLE_IMG)
    ret["jpx"]              = bool(mupdf.FZ_ENABLE_JPX)
    ret["js"]               = bool(mupdf.FZ_ENABLE_JS)
    ret["pdf"]              = bool(mupdf.FZ_ENABLE_PDF)
    ret["plotter-cmyk"]     = bool(mupdf.FZ_PLOTTERS_CMYK)
    ret["plotter-g"]        = bool(mupdf.FZ_PLOTTERS_G)
    ret["plotter-n"]        = bool(mupdf.FZ_PLOTTERS_N)
    ret["plotter-rgb"]      = bool(mupdf.FZ_PLOTTERS_RGB)
    ret["py-memory"]        = bool(JM_MEMORY)
    ret["svg"]              = bool(mupdf.FZ_ENABLE_SVG)
    ret["tofu"]             = have_TOFU
    ret["tofu-cjk"]         = have_TOFU_CJK
    ret["tofu-cjk-ext"]     = have_TOFU_CJK_EXT
    ret["tofu-cjk-lang"]    = have_TOFU_CJK_LANG
    ret["tofu-emoji"]       = have_TOFU_EMOJI
    ret["tofu-historic"]    = have_TOFU_HISTORIC
    ret["tofu-sil"]         = have_TOFU_SIL
    ret["tofu-symbol"]      = have_TOFU_SYMBOL
    ret["xps"]              = bool(mupdf.FZ_ENABLE_XPS)
    return ret


def JM_insert_contents(pdf, pageref, newcont, overlay):
    '''
    Insert a buffer as a new separate /Contents object of a page.
    1. Create a new stream object from buffer 'newcont'
    2. If /Contents already is an array, then just prepend or append this object
    3. Else, create new array and put old content obj and this object into it.
       If the page had no /Contents before, just create a 1-item array.
    '''
    contents = mupdf.pdf_dict_get(pageref, PDF_NAME('Contents'))
    newconts = mupdf.pdf_add_stream(pdf, newcont, mupdf.PdfObj(), 0)
    xref = mupdf.pdf_to_num(newconts)
    if mupdf.pdf_is_array(contents):
        if overlay:  # append new object
            mupdf.pdf_array_push(contents, newconts)
        else:   # prepend new object
            mupdf.pdf_array_insert(contents, newconts, 0)
    else:
        carr = mupdf.pdf_new_array(pdf, 5)
        if overlay:
            if contents.m_internal:
                mupdf.pdf_array_push(carr, contents)
            mupdf.pdf_array_push(carr, newconts)
        else:
            mupdf.pdf_array_push(carr, newconts)
            if contents.m_internal:
                mupdf.pdf_array_push(carr, contents)
        mupdf.pdf_dict_put(pageref, PDF_NAME('Contents'), carr)
    return xref


def JM_insert_font(pdf, bfname, fontfile, fontbuffer, set_simple, idx, wmode, serif, encoding, ordering):
    '''
    Insert a font in a PDF
    '''
    font = None
    res = None
    data = None
    ixref = 0
    index = 0
    simple = 0
    value=None
    name=None
    subt=None
    exto = None

    ENSURE_OPERATION(pdf)
    # check for CJK font
    if ordering > -1:
        data, size, index = mupdf.fz_lookup_cjk_font(ordering)
    if data:
        font = mupdf.fz_new_font_from_memory(None, data, size, index, 0)
        font_obj = mupdf.pdf_add_cjk_font(pdf, font, ordering, wmode, serif)
        exto = "n/a"
        simple = 0
        #goto weiter;
    else:

        # check for PDF Base-14 font
        if bfname:
            data, size = mupdf.fz_lookup_base14_font(bfname)
        if data:
            font = mupdf.fz_new_font_from_memory(bfname, data, size, 0, 0)
            font_obj = mupdf.pdf_add_simple_font(pdf, font, encoding)
            exto = "n/a"
            simple = 1
            #goto weiter;

        else:
            if fontfile:
                font = mupdf.fz_new_font_from_file(None, fontfile, idx, 0)
            else:
                res = JM_BufferFromBytes(fontbuffer)
                if not res.m_internal:
                    RAISEPY(MSG_FILE_OR_BUFFER, PyExc_ValueError)
                font = mupdf.fz_new_font_from_buffer(None, res, idx, 0)

            if not set_simple:
                font_obj = mupdf.pdf_add_cid_font(pdf, font)
                simple = 0
            else:
                font_obj = mupdf.pdf_add_simple_font(pdf, font, encoding)
                simple = 2
    #weiter: ;
    ixref = mupdf.pdf_to_num(font_obj)
    name = JM_EscapeStrFromStr( mupdf.pdf_to_name( mupdf.pdf_dict_get(font_obj, PDF_NAME('BaseFont'))))

    subt = JM_UnicodeFromStr( mupdf.pdf_to_name( mupdf.pdf_dict_get( font_obj, PDF_NAME('Subtype'))))

    if not exto:
        exto = JM_UnicodeFromStr(JM_get_fontextension(pdf, ixref))

    asc = mupdf.fz_font_ascender(font)
    dsc = mupdf.fz_font_descender(font)
    value = [
            ixref,
            {
                "name": name,        # base font name
                "type": subt,        # subtype
                "ext": exto,         # file extension
                "simple": bool(simple), # simple font?
                "ordering": ordering, # CJK font?
                "ascender": asc,
                "descender": dsc,
            },
            ]
    return value

def JM_irect_from_py(r):
    '''
    PySequence to mupdf.FzIrect. Default: infinite irect
    '''
    if isinstance(r, mupdf.FzIrect):
        return r
    if isinstance(r, IRect):
        r = mupdf.FzIrect( r.x0, r.y0, r.x1, r.y1)
        return r
    if isinstance(r, Rect):
        ret = mupdf.FzRect(r.x0, r.y0, r.x1, r.y1)
        ret = mupdf.FzIrect(ret)  # Uses fz_irect_from_rect().
        return ret
    if isinstance(r, mupdf.FzRect):
        ret = mupdf.FzIrect(r)  # Uses fz_irect_from_rect().
        return ret
    if not r or not PySequence_Check(r) or PySequence_Size(r) != 4:
        return mupdf.FzIrect(mupdf.fz_infinite_irect)
    f = [0, 0, 0, 0]
    for i in range(4):
        f[i] = r[i]
        if f[i] is None:
            return mupdf.FzIrect(mupdf.fz_infinite_irect)
        if f[i] < FZ_MIN_INF_RECT:
            f[i] = FZ_MIN_INF_RECT
        if f[i] > FZ_MAX_INF_RECT:
            f[i] = FZ_MAX_INF_RECT
    return mupdf.fz_make_irect(f[0], f[1], f[2], f[3])

def JM_listbox_value( annot):
    '''
    ListBox retrieve value
    '''
    # may be single value or array
    annot_obj = mupdf.pdf_annot_obj( annot)
    optarr = mupdf.pdf_dict_get( annot_obj, PDF_NAME('V'))
    if mupdf.pdf_is_string( optarr):   # a single string
        return mupdf.pdf_to_text_string( optarr)

    # value is an array (may have len 0)
    n = mupdf.pdf_array_len( optarr)
    liste = []

    # extract a list of strings
    # each entry may again be an array: take second entry then
    for i in range( n):
        elem = mupdf.pdf_array_get( optarr, i)
        if mupdf.pdf_is_array( elem):
            elem = mupdf.pdf_array_get( elem, 1)
        liste.append( JM_UnicodeFromStr( mupdf.pdf_to_text_string( elem)))
    return liste


def JM_make_annot_DA(annot, ncol, col, fontname, fontsize):
    # PyMuPDF uses a fz_buffer to build up the string, but it's non-trivial to
    # convert the fz_buffer's `unsigned char*` into a `const char*` suitable
    # for passing to pdf_dict_put_text_string(). So instead we build up the
    # string directly in Python.
    buf = ''
    if ncol < 1:
        buf += f'0 g '
    elif ncol == 1:
        buf += f'{col[0]:g} g '
    elif ncol == 2:
        assert 0
    elif ncol == 3:
        buf += f'{col[0]:g} {col[1]:g} {col[2]:g} rg '
    else:
        buf += f'{col[0]:g} {col[1]:g} {col[2]:g} {col[3]:g} k '
    buf += f'/{JM_expand_fname(fontname)} {fontsize} Tf'
    mupdf.pdf_dict_put_text_string(mupdf.pdf_annot_obj(annot), mupdf.PDF_ENUM_NAME_DA, buf)


def JM_make_spanlist(line_dict, line, raw, buff, tp_rect):
    if g_use_extra:
        return extra.JM_make_spanlist(line_dict, line, raw, buff, tp_rect)
    char_list = None
    span_list = []
    mupdf.fz_clear_buffer(buff)
    span_rect = mupdf.FzRect(mupdf.FzRect.Fixed_EMPTY)
    line_rect = mupdf.FzRect(mupdf.FzRect.Fixed_EMPTY)

    class char_style:
        def __init__(self, rhs=None):
            if rhs:
                self.size = rhs.size
                self.flags = rhs.flags
                if mupdf_version_tuple >= (1, 25, 2):
                    self.char_flags = rhs.char_flags
                self.font = rhs.font
                self.color = rhs.color
                self.asc = rhs.asc
                self.desc = rhs.desc
            else:
                self.size = -1
                self.flags = -1
                if mupdf_version_tuple >= (1, 25, 2):
                    self.char_flags = -1
                self.font = ''
                self.color = -1
                self.asc = 0
                self.desc = 0
        def __str__(self):
            ret = f'{self.size} {self.flags}'
            if mupdf_version_tuple >= (1, 25, 2):
                ret += f' {self.char_flags}'
            ret += f' {self.font} {self.color} {self.asc} {self.desc}'
            return ret

    old_style = char_style()
    style = char_style()
    span = None
    span_origin = None

    for ch in line:
        # start-trace
        r = JM_char_bbox(line, ch)
        if (not JM_rects_overlap(tp_rect, r)
                and not mupdf.fz_is_infinite_rect(tp_rect)
                ):
            continue

        # Info from:
        # detect_super_script()
        # fz_font_is_italic()
        # fz_font_is_serif()
        # fz_font_is_monospaced()
        # fz_font_is_bold()
        
        flags = JM_char_font_flags(mupdf.FzFont(mupdf.ll_fz_keep_font(ch.m_internal.font)), line, ch)
        origin = mupdf.FzPoint(ch.m_internal.origin)
        style.size = ch.m_internal.size
        style.flags = flags
        if mupdf_version_tuple >= (1, 25, 2):
            style.char_flags = ch.m_internal.flags
        style.font = JM_font_name(mupdf.FzFont(mupdf.ll_fz_keep_font(ch.m_internal.font)))
        if mupdf_version_tuple >= (1, 25):
            style.color = ch.m_internal.argb
        else:
            style.color = ch.m_internal.color
        style.asc = JM_font_ascender(mupdf.FzFont(mupdf.ll_fz_keep_font(ch.m_internal.font)))
        style.desc = JM_font_descender(mupdf.FzFont(mupdf.ll_fz_keep_font(ch.m_internal.font)))

        if (style.size != old_style.size
                or style.flags != old_style.flags
                or (mupdf_version_tuple >= (1, 25, 2)
                    and (style.char_flags & ~mupdf.FZ_STEXT_SYNTHETIC)
                        != (old_style.char_flags & ~mupdf.FZ_STEXT_SYNTHETIC)
                    )
                or style.color != old_style.color
                or style.font != old_style.font
                ):
            if old_style.size >= 0:
                # not first one, output previous
                if raw:
                    # put character list in the span
                    span[dictkey_chars] = char_list
                    char_list = None
                else:
                    # put text string in the span
                    span[dictkey_text] = JM_EscapeStrFromBuffer( buff)
                    mupdf.fz_clear_buffer(buff)

                span[dictkey_origin] = JM_py_from_point(span_origin)
                span[dictkey_bbox] = JM_py_from_rect(span_rect)
                line_rect = mupdf.fz_union_rect(line_rect, span_rect)
                span_list.append( span)
                span = None

            span = dict()
            asc = style.asc
            desc = style.desc
            if style.asc < 1e-3:
                asc = 0.9
                desc = -0.1

            span[dictkey_size] = style.size
            span[dictkey_flags] = style.flags
            if mupdf_version_tuple >= (1, 25, 2):
                span[dictkey_char_flags] = style.char_flags
            span[dictkey_font] = JM_EscapeStrFromStr(style.font)
            span[dictkey_color] = style.color
            span["ascender"] = asc
            span["descender"] = desc

            # Need to be careful here - doing 'old_style=style' does a shallow
            # copy, but we need to keep old_style as a distinct instance.
            old_style = char_style(style)
            span_rect = r
            span_origin = origin

        span_rect = mupdf.fz_union_rect(span_rect, r)

        if raw: # make and append a char dict
            char_dict = dict()
            char_dict[dictkey_origin] = JM_py_from_point( ch.m_internal.origin)
            char_dict[dictkey_bbox] = JM_py_from_rect(r)
            char_dict[dictkey_c] = chr(ch.m_internal.c)

            if char_list is None:
                char_list = []
            char_list.append(char_dict)
        else:   # add character byte to buffer
            JM_append_rune(buff, ch.m_internal.c)

    # all characters processed, now flush remaining span
    if span:
        if raw:
            span[dictkey_chars] = char_list
            char_list = None
        else:
            span[dictkey_text] = JM_EscapeStrFromBuffer(buff)
            mupdf.fz_clear_buffer(buff)
        span[dictkey_origin] = JM_py_from_point(span_origin)
        span[dictkey_bbox] = JM_py_from_rect(span_rect)

        if not mupdf.fz_is_empty_rect(span_rect):
            span_list.append(span)
            line_rect = mupdf.fz_union_rect(line_rect, span_rect)
        span = None
    if not mupdf.fz_is_empty_rect(line_rect):
        line_dict[dictkey_spans] = span_list
    else:
        line_dict[dictkey_spans] = span_list
    return line_rect

def _make_image_dict(img, img_dict):
    """Populate a dictionary with information extracted from a given image.

    Used by 'Document.extract_image' and by 'JM_make_image_block'.
    Both of these functions will add some more specific information.
    """
    img_type = img.fz_compressed_image_type()
    ext = JM_image_extension(img_type)

    # compressed image buffer if present, else None
    ll_cbuf = mupdf.ll_fz_compressed_image_buffer(img.m_internal)

    if (0
        or not ll_cbuf
        or img_type in (mupdf.FZ_IMAGE_JBIG2, mupdf.FZ_IMAGE_UNKNOWN)
        or img_type < mupdf.FZ_IMAGE_BMP
    ):
        # not an image with a compressed buffer: convert to PNG
        res = mupdf.fz_new_buffer_from_image_as_png(
                    img,
                    mupdf.FzColorParams(mupdf.fz_default_color_params),
              )
        ext = "png"
    elif ext == "jpeg" and img.n() == 4:
        # JPEG with CMYK: invert colors
        res = mupdf.fz_new_buffer_from_image_as_jpeg(
                    img, mupdf.FzColorParams(mupdf.fz_default_color_params), 95, 1)
    else:
        # copy the compressed buffer
        res = mupdf.FzBuffer(mupdf.ll_fz_keep_buffer(ll_cbuf.buffer))

    bytes_ = JM_BinFromBuffer(res)
    img_dict[dictkey_width] = img.w()
    img_dict[dictkey_height] = img.h()
    img_dict[dictkey_ext] = ext
    img_dict[dictkey_colorspace] = img.n()
    img_dict[dictkey_xres] = img.xres()
    img_dict[dictkey_yres] = img.yres()
    img_dict[dictkey_bpc] = img.bpc()
    img_dict[dictkey_size] = len(bytes_)
    img_dict[dictkey_image] = bytes_

def JM_make_image_block(block, block_dict):
    img = block.i_image()
    _make_image_dict(img, block_dict)
    # if the image has a mask, store it as a PNG buffer
    mask = img.mask()
    if mask.m_internal:
        buff = mask.fz_new_buffer_from_image_as_png(mupdf.FzColorParams(mupdf.fz_default_color_params))
        block_dict["mask"] = buff.fz_buffer_extract()
    else:
        block_dict["mask"] = None
    block_dict[dictkey_matrix] = JM_py_from_matrix(block.i_transform())


def JM_make_text_block(block, block_dict, raw, buff, tp_rect):
    if g_use_extra:
        return extra.JM_make_text_block(block.m_internal, block_dict, raw, buff.m_internal, tp_rect.m_internal)
    line_list = []
    block_rect = mupdf.FzRect(mupdf.FzRect.Fixed_EMPTY)
    #log(f'{block=}')
    for line in block:
        #log(f'{line=}')
        if (mupdf.fz_is_empty_rect(mupdf.fz_intersect_rect(tp_rect, mupdf.FzRect(line.m_internal.bbox)))
                and not mupdf.fz_is_infinite_rect(tp_rect)
                ):
            continue
        line_dict = dict()
        line_rect = JM_make_spanlist(line_dict, line, raw, buff, tp_rect)
        block_rect = mupdf.fz_union_rect(block_rect, line_rect)
        line_dict[dictkey_wmode] = line.m_internal.wmode
        line_dict[dictkey_dir] = JM_py_from_point(line.m_internal.dir)
        line_dict[dictkey_bbox] = JM_py_from_rect(line_rect)
        line_list.append(line_dict)
    block_dict[dictkey_bbox] = JM_py_from_rect(block_rect)
    block_dict[dictkey_lines] = line_list


def JM_make_textpage_dict(tp, page_dict, raw):
    if g_use_extra:
        return extra.JM_make_textpage_dict(tp.m_internal, page_dict, raw)
    text_buffer = mupdf.fz_new_buffer(128)
    block_list = []
    tp_rect = mupdf.FzRect(tp.m_internal.mediabox)
    block_n = -1
    #log( 'JM_make_textpage_dict {=tp}')
    for block in tp:
        block_n += 1
        if (not mupdf.fz_contains_rect(tp_rect, mupdf.FzRect(block.m_internal.bbox))
                and not mupdf.fz_is_infinite_rect(tp_rect)
                and block.m_internal.type == mupdf.FZ_STEXT_BLOCK_IMAGE
                ):
            continue
        if (not mupdf.fz_is_infinite_rect(tp_rect)
                and mupdf.fz_is_empty_rect(mupdf.fz_intersect_rect(tp_rect, mupdf.FzRect(block.m_internal.bbox)))
                ):
            continue

        block_dict = dict()
        block_dict[dictkey_number] = block_n
        block_dict[dictkey_type] = block.m_internal.type
        if block.m_internal.type == mupdf.FZ_STEXT_BLOCK_IMAGE:
            block_dict[dictkey_bbox] = JM_py_from_rect(block.m_internal.bbox)
            JM_make_image_block(block, block_dict)
        else:
            JM_make_text_block(block, block_dict, raw, text_buffer, tp_rect)

        block_list.append(block_dict)
    page_dict[dictkey_blocks] = block_list


def JM_matrix_from_py(m):
    a = [0, 0, 0, 0, 0, 0]
    if isinstance(m, mupdf.FzMatrix):
        return m
    if isinstance(m, Matrix):
        return mupdf.FzMatrix(m.a, m.b, m.c, m.d, m.e, m.f)
    if not m or not PySequence_Check(m) or PySequence_Size(m) != 6:
        return mupdf.FzMatrix()
    for i in range(6):
        a[i] = JM_FLOAT_ITEM(m, i)
        if a[i] is None:
            return mupdf.FzRect()
    return mupdf.FzMatrix(a[0], a[1], a[2], a[3], a[4], a[5])


def JM_mediabox(page_obj):
    '''
    return a PDF page's MediaBox
    '''
    page_mediabox = mupdf.FzRect(mupdf.FzRect.Fixed_UNIT)
    mediabox = mupdf.pdf_to_rect(
            mupdf.pdf_dict_get_inheritable(page_obj, PDF_NAME('MediaBox'))
            )
    if mupdf.fz_is_empty_rect(mediabox) or mupdf.fz_is_infinite_rect(mediabox):
        mediabox.x0 = 0
        mediabox.y0 = 0
        mediabox.x1 = 612
        mediabox.y1 = 792

    page_mediabox = mupdf.FzRect(
            mupdf.fz_min(mediabox.x0, mediabox.x1),
            mupdf.fz_min(mediabox.y0, mediabox.y1),
            mupdf.fz_max(mediabox.x0, mediabox.x1),
            mupdf.fz_max(mediabox.y0, mediabox.y1),
            )

    if (page_mediabox.x1 - page_mediabox.x0 < 1
            or page_mediabox.y1 - page_mediabox.y0 < 1
            ):
        page_mediabox = mupdf.FzRect(mupdf.FzRect.Fixed_UNIT)

    return page_mediabox


def JM_merge_range(
        doc_des,
        doc_src,
        spage,
        epage,
        apage,
        rotate,
        links,
        annots,
        show_progress,
        graft_map,
        ):
    '''
    Copy a range of pages (spage, epage) from a source PDF to a specified
    location (apage) of the target PDF.
    If spage > epage, the sequence of source pages is reversed.
    '''
    if g_use_extra:
        return extra.JM_merge_range(
                doc_des,
                doc_src,
                spage,
                epage,
                apage,
                rotate,
                links,
                annots,
                show_progress,
                graft_map,
                )
    afterpage = apage
    counter = 0  # copied pages counter
    total = mupdf.fz_absi(epage - spage) + 1   # total pages to copy

    if spage < epage:
        page = spage
        while page <= epage:
            page_merge(doc_des, doc_src, page, afterpage, rotate, links, annots, graft_map)
            counter += 1
            if show_progress > 0 and counter % show_progress == 0:
                message(f"Inserted {counter} of {total} pages.")
            page += 1
            afterpage += 1
    else:
        page = spage
        while page >= epage:
            page_merge(doc_des, doc_src, page, afterpage, rotate, links, annots, graft_map)
            counter += 1
            if show_progress > 0 and counter % show_progress == 0:
                message(f"Inserted {counter} of {total} pages.")
            page -= 1
            afterpage += 1


def JM_merge_resources( page, temp_res):
    '''
    Merge the /Resources object created by a text pdf device into the page.
    The device may have created multiple /ExtGState/Alp? and /Font/F? objects.
    These need to be renamed (renumbered) to not overwrite existing page
    objects from previous executions.
    Returns the next available numbers n, m for objects /Alp<n>, /F<m>.
    '''
    # page objects /Resources, /Resources/ExtGState, /Resources/Font
    resources = mupdf.pdf_dict_get(page.obj(), PDF_NAME('Resources'))
    main_extg = mupdf.pdf_dict_get(resources, PDF_NAME('ExtGState'))
    main_fonts = mupdf.pdf_dict_get(resources, PDF_NAME('Font'))

    # text pdf device objects /ExtGState, /Font
    temp_extg = mupdf.pdf_dict_get(temp_res, PDF_NAME('ExtGState'))
    temp_fonts = mupdf.pdf_dict_get(temp_res, PDF_NAME('Font'))

    max_alp = -1
    max_fonts = -1

    # Handle /Alp objects
    if mupdf.pdf_is_dict(temp_extg):   # any created at all?
        n = mupdf.pdf_dict_len(temp_extg)
        if mupdf.pdf_is_dict(main_extg):   # does page have /ExtGState yet?
            for i in range(mupdf.pdf_dict_len(main_extg)):
                # get highest number of objects named /Alpxxx
                alp = mupdf.pdf_to_name( mupdf.pdf_dict_get_key(main_extg, i))
                if not alp.startswith('Alp'):
                    continue
                j = mupdf.fz_atoi(alp[3:])
                if j > max_alp:
                    max_alp = j
        else:   # create a /ExtGState for the page
            main_extg = mupdf.pdf_dict_put_dict(resources, PDF_NAME('ExtGState'), n)

        max_alp += 1
        for i in range(n):  # copy over renumbered /Alp objects
            alp = mupdf.pdf_to_name( mupdf.pdf_dict_get_key( temp_extg, i))
            j = mupdf.fz_atoi(alp[3:]) + max_alp
            text = f'Alp{j}'
            val = mupdf.pdf_dict_get_val( temp_extg, i)
            mupdf.pdf_dict_puts(main_extg, text, val)

    if mupdf.pdf_is_dict(main_fonts):  # has page any fonts yet?
        for i in range(mupdf.pdf_dict_len(main_fonts)):    # get max font number
            font = mupdf.pdf_to_name( mupdf.pdf_dict_get_key( main_fonts, i))
            if not font.startswith("F"):
                continue
            j = mupdf.fz_atoi(font[1:])
            if j > max_fonts:
                max_fonts = j
    else:   # create a Resources/Font for the page
        main_fonts = mupdf.pdf_dict_put_dict(resources, PDF_NAME('Font'), 2)

    max_fonts += 1
    for i in range(mupdf.pdf_dict_len(temp_fonts)):    # copy renumbered fonts
        font = mupdf.pdf_to_name( mupdf.pdf_dict_get_key( temp_fonts, i))
        j = mupdf.fz_atoi(font[1:]) + max_fonts
        text = f'F{j}'
        val = mupdf.pdf_dict_get_val(temp_fonts, i)
        mupdf.pdf_dict_puts(main_fonts, text, val)
    return (max_alp, max_fonts) # next available numbers


def JM_mupdf_warning( text):
    '''
    redirect MuPDF warnings
    '''
    JM_mupdf_warnings_store.append(text)
    if JM_mupdf_show_warnings:
        message(f'MuPDF warning: {text}')


def JM_mupdf_error( text):
    JM_mupdf_warnings_store.append(text)
    if JM_mupdf_show_errors:
        message(f'MuPDF error: {text}\n')


def JM_new_bbox_device(rc, inc_layers):
    assert isinstance(rc, list)
    return JM_new_bbox_device_Device( rc, inc_layers)


def JM_new_buffer_from_stext_page(page):
    '''
    make a buffer from an stext_page's text
    '''
    assert isinstance(page, mupdf.FzStextPage)
    rect = mupdf.FzRect(page.m_internal.mediabox)
    buf = mupdf.fz_new_buffer(256)
    for block in page:
        if block.m_internal.type == mupdf.FZ_STEXT_BLOCK_TEXT:
            for line in block:
                for ch in line:
                    if (not JM_rects_overlap(rect, JM_char_bbox(line, ch))
                            and not mupdf.fz_is_infinite_rect(rect)
                            ):
                        continue
                    mupdf.fz_append_rune(buf, ch.m_internal.c)
                mupdf.fz_append_byte(buf, ord('\n'))
            mupdf.fz_append_byte(buf, ord('\n'))
    return buf


def JM_new_javascript(pdf, value):
    '''
    make new PDF action object from JavaScript source
    Parameters are a PDF document and a Python string.
    Returns a PDF action object.
    '''
    if value is None:
        # no argument given
        return
    data = JM_StrAsChar(value)
    if data is None:
        # not convertible to char*
        return

    res = mupdf.fz_new_buffer_from_copied_data(data.encode('utf8'))
    source = mupdf.pdf_add_stream(pdf, res, mupdf.PdfObj(), 0)
    newaction = mupdf.pdf_add_new_dict(pdf, 4)
    mupdf.pdf_dict_put(newaction, PDF_NAME('S'), mupdf.pdf_new_name('JavaScript'))
    mupdf.pdf_dict_put(newaction, PDF_NAME('JS'), source)
    return newaction


def JM_new_output_fileptr(bio):
    return JM_new_output_fileptr_Output( bio)


def JM_norm_rotation(rotate):
    '''
    # return normalized /Rotate value:one of 0, 90, 180, 270
    '''
    while rotate < 0:
        rotate += 360
    while rotate >= 360:
        rotate -= 360
    if rotate % 90 != 0:
        return 0
    return rotate


def JM_object_to_buffer(what, compress, ascii):
    res = mupdf.fz_new_buffer(512)
    out = mupdf.FzOutput(res)
    mupdf.pdf_print_obj(out, what, compress, ascii)
    out.fz_close_output()
    mupdf.fz_terminate_buffer(res)
    return res


def JM_outline_xrefs(obj, xrefs):
    '''
    Return list of outline xref numbers. Recursive function. Arguments:
    'obj' first OL item
    'xrefs' empty Python list
    '''
    if not obj.m_internal:
        return xrefs
    thisobj = obj
    while thisobj.m_internal:
        newxref = mupdf.pdf_to_num( thisobj)
        if newxref in xrefs or mupdf.pdf_dict_get( thisobj, PDF_NAME('Type')).m_internal:
            # circular ref or top of chain: terminate
            break
        xrefs.append( newxref)
        first = mupdf.pdf_dict_get( thisobj, PDF_NAME('First'))    # try go down
        if mupdf.pdf_is_dict( first):
            xrefs = JM_outline_xrefs( first, xrefs)
        thisobj = mupdf.pdf_dict_get( thisobj, PDF_NAME('Next'))   # try go next
        parent = mupdf.pdf_dict_get( thisobj, PDF_NAME('Parent'))  # get parent
        if not mupdf.pdf_is_dict( thisobj):
            thisobj = parent
    return xrefs


def JM_page_rotation(page):
    '''
    return a PDF page's /Rotate value: one of (0, 90, 180, 270)
    '''
    rotate = 0

    obj = mupdf.pdf_dict_get_inheritable( page.obj(), mupdf.PDF_ENUM_NAME_Rotate)
    rotate = mupdf.pdf_to_int(obj)
    rotate = JM_norm_rotation(rotate)
    return rotate


def JM_pdf_obj_from_str(doc, src):
    '''
    create PDF object from given string (new in v1.14.0: MuPDF dropped it)
    '''
    # fixme: seems inefficient to convert to bytes instance then make another
    # copy inside fz_new_buffer_from_copied_data(), but no other way?
    #
    buffer_ = mupdf.fz_new_buffer_from_copied_data(bytes(src, 'utf8'))
    stream = mupdf.fz_open_buffer(buffer_)
    lexbuf = mupdf.PdfLexbuf(mupdf.PDF_LEXBUF_SMALL)
    result = mupdf.pdf_parse_stm_obj(doc, stream, lexbuf)
    return result


def JM_pixmap_from_display_list(
        list_,
        ctm,
        cs,
        alpha,
        clip,
        seps,
        ):
    '''
    Version of fz_new_pixmap_from_display_list (util.c) to also support
    rendering of only the 'clip' part of the displaylist rectangle
    '''
    assert isinstance(list_, mupdf.FzDisplayList)
    if seps is None:
        seps = mupdf.FzSeparations()
    assert seps is None or isinstance(seps, mupdf.FzSeparations), f'{type(seps)=}: {seps}'

    rect = mupdf.fz_bound_display_list(list_)
    matrix = JM_matrix_from_py(ctm)
    rclip = JM_rect_from_py(clip)
    rect = mupdf.fz_intersect_rect(rect, rclip)    # no-op if clip is not given

    rect = mupdf.fz_transform_rect(rect, matrix)
    irect = mupdf.fz_round_rect(rect)

    assert isinstance( cs, mupdf.FzColorspace)

    pix = mupdf.fz_new_pixmap_with_bbox(cs, irect, seps, alpha)
    if alpha:
        mupdf.fz_clear_pixmap(pix)
    else:
        mupdf.fz_clear_pixmap_with_value(pix, 0xFF)

    if not mupdf.fz_is_infinite_rect(rclip):
        dev = mupdf.fz_new_draw_device_with_bbox(matrix, pix, irect)
        mupdf.fz_run_display_list(list_, dev, mupdf.FzMatrix(), rclip, mupdf.FzCookie())
    else:
        dev = mupdf.fz_new_draw_device(matrix, pix)
        mupdf.fz_run_display_list(list_, dev, mupdf.FzMatrix(), mupdf.FzRect(mupdf.FzRect.Fixed_INFINITE), mupdf.FzCookie())

    mupdf.fz_close_device(dev)
    # Use special raw Pixmap constructor so we don't set alpha to true.
    return Pixmap( 'raw', pix)


def JM_point_from_py(p):
    '''
    PySequence to fz_point. Default: (FZ_MIN_INF_RECT, FZ_MIN_INF_RECT)
    '''
    if isinstance(p, mupdf.FzPoint):
        return p
    if isinstance(p, Point):
        return mupdf.FzPoint(p.x, p.y)
    if g_use_extra:
        return extra.JM_point_from_py( p)
    
    p0 = mupdf.FzPoint(0, 0)
    x = JM_FLOAT_ITEM(p, 0)
    y = JM_FLOAT_ITEM(p, 1)
    if x is None or y is None:
        return p0
    x = max( x, FZ_MIN_INF_RECT)
    y = max( y, FZ_MIN_INF_RECT)
    x = min( x, FZ_MAX_INF_RECT)
    y = min( y, FZ_MAX_INF_RECT)
    return mupdf.FzPoint(x, y)


def JM_print_stext_page_as_text(res, page):
    '''
    Plain text output. An identical copy of fz_print_stext_page_as_text,
    but lines within a block are concatenated by space instead a new-line
    character (which else leads to 2 new-lines).
    '''
    if 1 and g_use_extra:
        return extra.JM_print_stext_page_as_text(res, page)
    
    assert isinstance(res, mupdf.FzBuffer)
    assert isinstance(page, mupdf.FzStextPage)
    rect = mupdf.FzRect(page.m_internal.mediabox)
    last_char = 0

    n_blocks = 0
    n_lines = 0
    n_chars = 0
    for n_blocks2, block in enumerate( page):
        if block.m_internal.type == mupdf.FZ_STEXT_BLOCK_TEXT:
            for n_lines2, line in enumerate( block):
                for n_chars2, ch in enumerate( line):
                    pass
                n_chars += n_chars2
            n_lines += n_lines2
        n_blocks += n_blocks2
    
    for block in page:
        if block.m_internal.type == mupdf.FZ_STEXT_BLOCK_TEXT:
            for line in block:
                last_char = 0
                for ch in line:
                    chbbox = JM_char_bbox(line, ch)
                    if (mupdf.fz_is_infinite_rect(rect)
                            or JM_rects_overlap(rect, chbbox)
                            ):
                        #raw += chr(ch.m_internal.c)
                        last_char = ch.m_internal.c
                        #log( '{=last_char!r utf!r}')
                        JM_append_rune(res, last_char)
                if last_char != 10 and last_char > 0:
                    mupdf.fz_append_string(res, "\n")


def JM_put_script(annot_obj, key1, key2, value):
    '''
    Create a JavaScript PDF action.
    Usable for all object types which support PDF actions, even if the
    argument name suggests annotations. Up to 2 key values can be specified, so
    JavaScript actions can be stored for '/A' and '/AA/?' keys.
    '''
    key1_obj = mupdf.pdf_dict_get(annot_obj, key1)
    pdf = mupdf.pdf_get_bound_document(annot_obj)  # owning PDF

    # if no new script given, just delete corresponding key
    if not value:
        if key2 is None or not key2.m_internal:
            mupdf.pdf_dict_del(annot_obj, key1)
        elif key1_obj.m_internal:
            mupdf.pdf_dict_del(key1_obj, key2)
        return

    # read any existing script as a PyUnicode string
    if not key2.m_internal or not key1_obj.m_internal:
        script = JM_get_script(key1_obj)
    else:
        script = JM_get_script(mupdf.pdf_dict_get(key1_obj, key2))

    # replace old script, if different from new one
    if value != script:
        newaction = JM_new_javascript(pdf, value)
        if not key2.m_internal:
            mupdf.pdf_dict_put(annot_obj, key1, newaction)
        else:
            mupdf.pdf_dict_putl(annot_obj, newaction, key1, key2)


def JM_py_from_irect(r):
    return r.x0, r.y0, r.x1, r.y1


def JM_py_from_matrix(m):
    return m.a, m.b, m.c, m.d, m.e, m.f


def JM_py_from_point(p):
    return p.x, p.y


def JM_py_from_quad(q):
    '''
    PySequence from fz_quad.
    '''
    return (
            (q.ul.x, q.ul.y),
            (q.ur.x, q.ur.y),
            (q.ll.x, q.ll.y),
            (q.lr.x, q.lr.y),
            )


def JM_py_from_rect(r):
    return r.x0, r.y0, r.x1, r.y1


def JM_quad_from_py(r):
    if isinstance(r, mupdf.FzQuad):
        return r
    # cover all cases of 4-float-sequences
    if hasattr(r, "__getitem__") and len(r) == 4 and hasattr(r[0], "__float__"):
        r = mupdf.FzRect(*tuple(r))
    if isinstance( r, mupdf.FzRect):
        return mupdf.fz_quad_from_rect( r)
    if isinstance( r, Quad):
        return mupdf.fz_make_quad(
                r.ul.x, r.ul.y,
                r.ur.x, r.ur.y,
                r.ll.x, r.ll.y,
                r.lr.x, r.lr.y,
                )
    q = mupdf.fz_make_quad(0, 0, 0, 0, 0, 0, 0, 0)
    p = [0,0,0,0]
    if not r or not isinstance(r, (tuple, list)) or len(r) != 4:
        return q

    if JM_FLOAT_ITEM(r, 0) is None:
        return mupdf.fz_quad_from_rect(JM_rect_from_py(r))

    for i in range(4):
        if i >= len(r):
            return q    # invalid: cancel the rest
        obj = r[i]  # next point item
        if not PySequence_Check(obj) or PySequence_Size(obj) != 2:
            return q    # invalid: cancel the rest

        p[i].x = JM_FLOAT_ITEM(obj, 0)
        p[i].y = JM_FLOAT_ITEM(obj, 1)
        if p[i].x is None or p[i].y is None:
            return q
        p[i].x = max( p[i].x, FZ_MIN_INF_RECT)
        p[i].y = max( p[i].y, FZ_MIN_INF_RECT)
        p[i].x = min( p[i].x, FZ_MAX_INF_RECT)
        p[i].y = min( p[i].y, FZ_MAX_INF_RECT)
    q.ul = p[0]
    q.ur = p[1]
    q.ll = p[2]
    q.lr = p[3]
    return q


def JM_read_contents(pageref):
    '''
    Read and concatenate a PDF page's /Contents object(s) in a buffer
    '''
    assert isinstance(pageref, mupdf.PdfObj), f'{type(pageref)}'
    contents = mupdf.pdf_dict_get(pageref, mupdf.PDF_ENUM_NAME_Contents)
    if mupdf.pdf_is_array(contents):
        res = mupdf.FzBuffer(1024)
        for i in range(mupdf.pdf_array_len(contents)):
            if i > 0:
                mupdf.fz_append_byte(res, 32)
            obj = mupdf.pdf_array_get(contents, i)
            if mupdf.pdf_is_stream(obj):
                nres = mupdf.pdf_load_stream(obj)
                mupdf.fz_append_buffer(res, nres)
    elif contents.m_internal:
        res = mupdf.pdf_load_stream(contents)
    else:
        res = b""
    return res


def JM_rect_from_py(r):
    if isinstance(r, mupdf.FzRect):
        return r
    if isinstance(r, mupdf.FzIrect):
        return mupdf.FzRect(r)
    if isinstance(r, Rect):
        return mupdf.fz_make_rect(r.x0, r.y0, r.x1, r.y1)
    if isinstance(r, IRect):
        return mupdf.fz_make_rect(r.x0, r.y0, r.x1, r.y1)
    if not r or not PySequence_Check(r) or PySequence_Size(r) != 4:
        return mupdf.FzRect(mupdf.FzRect.Fixed_INFINITE)
    f = [0, 0, 0, 0]
    for i in range(4):
        f[i] = JM_FLOAT_ITEM(r, i)
        if f[i] is None:
            return mupdf.FzRect(mupdf.FzRect.Fixed_INFINITE)
        if f[i] < FZ_MIN_INF_RECT:
            f[i] = FZ_MIN_INF_RECT
        if f[i] > FZ_MAX_INF_RECT:
            f[i] = FZ_MAX_INF_RECT
    return mupdf.fz_make_rect(f[0], f[1], f[2], f[3])


def JM_rects_overlap(a, b):
    if (0
            or a.x0 >= b.x1
            or a.y0 >= b.y1
            or a.x1 <= b.x0
            or a.y1 <= b.y0
            ):
        return 0
    return 1


def JM_refresh_links( page):
    '''
    refreshes the link and annotation tables of a page
    '''
    if page is None or not page.m_internal:
        return
    obj = mupdf.pdf_dict_get( page.obj(), PDF_NAME('Annots'))
    if obj.m_internal:
        pdf = page.doc()
        number = mupdf.pdf_lookup_page_number( pdf, page.obj())
        page_mediabox = mupdf.FzRect()
        page_ctm = mupdf.FzMatrix()
        mupdf.pdf_page_transform( page, page_mediabox, page_ctm)
        link = mupdf.pdf_load_link_annots( pdf, page, obj, number, page_ctm)
        page.m_internal.links = mupdf.ll_fz_keep_link( link.m_internal)


def JM_rotate_page_matrix(page):
    '''
    calculate page rotation matrices
    '''
    if not page.m_internal:
        return mupdf.FzMatrix()  # no valid pdf page given
    rotation = JM_page_rotation(page)
    #log( '{rotation=}')
    if rotation == 0:
        return mupdf.FzMatrix()  # no rotation
    cb_size = JM_cropbox_size(page.obj())
    w = cb_size.x
    h = cb_size.y
    #log( '{=h w}')
    if rotation == 90:
        m = mupdf.fz_make_matrix(0, 1, -1, 0, h, 0)
    elif rotation == 180:
        m = mupdf.fz_make_matrix(-1, 0, 0, -1, w, h)
    else:
        m = mupdf.fz_make_matrix(0, -1, 1, 0, 0, w)
    #log( 'returning {m=}')
    return m


def JM_search_stext_page(page, needle):
    if g_use_extra:
        return extra.JM_search_stext_page(page.m_internal, needle)
    
    rect = mupdf.FzRect(page.m_internal.mediabox)
    if not needle:
        return
    quads = []
    class Hits:
        def __str__(self):
            return f'Hits(len={self.len} quads={self.quads} hfuzz={self.hfuzz} vfuzz={self.vfuzz}'
    hits = Hits()
    hits.len = 0
    hits.quads = quads
    hits.hfuzz = 0.2    # merge kerns but not large gaps
    hits.vfuzz = 0.1

    buffer_ = JM_new_buffer_from_stext_page(page)
    haystack_string = mupdf.fz_string_from_buffer(buffer_)
    haystack = 0
    begin, end = find_string(haystack_string[haystack:], needle)
    if begin is None:
        #goto no_more_matches;
        return quads

    begin += haystack
    end += haystack
    inside = 0
    i = 0
    for block in page:
        if block.m_internal.type != mupdf.FZ_STEXT_BLOCK_TEXT:
            continue
        for line in block:
            for ch in line:
                i += 1
                if not mupdf.fz_is_infinite_rect(rect):
                    r = JM_char_bbox(line, ch)
                    if not JM_rects_overlap(rect, r):
                        #goto next_char;
                        continue
                while 1:
                    #try_new_match:
                    if not inside:
                        if haystack >= begin:
                            inside = 1
                    if inside:
                        if haystack < end:
                            on_highlight_char(hits, line, ch)
                            break
                        else:
                            inside = 0
                            begin, end = find_string(haystack_string[haystack:], needle)
                            if begin is None:
                                #goto no_more_matches;
                                return quads
                            else:
                                #goto try_new_match;
                                begin += haystack
                                end += haystack
                                continue
                    break
                haystack += 1
                #next_char:;
            assert haystack_string[haystack] == '\n', \
                    f'{haystack=} {haystack_string[haystack]=}'
            haystack += 1
        assert haystack_string[haystack] == '\n', \
                f'{haystack=} {haystack_string[haystack]=}'
        haystack += 1
    #no_more_matches:;
    return quads


def JM_scan_resources(pdf, rsrc, liste, what, stream_xref, tracer):
    '''
    Step through /Resources, looking up image, xobject or font information
    '''
    if mupdf.pdf_mark_obj(rsrc):
        mupdf.fz_warn('Circular dependencies! Consider page cleaning.')
        return  # Circular dependencies!
    try:
        xobj = mupdf.pdf_dict_get(rsrc, mupdf.PDF_ENUM_NAME_XObject)

        if what == 1:   # lookup fonts
            font = mupdf.pdf_dict_get(rsrc, mupdf.PDF_ENUM_NAME_Font)
            JM_gather_fonts(pdf, font, liste, stream_xref)
        elif what == 2: # look up images
            JM_gather_images(pdf, xobj, liste, stream_xref)
        elif what == 3: # look up form xobjects
            JM_gather_forms(pdf, xobj, liste, stream_xref)
        else:   # should never happen
            return

        # check if we need to recurse into Form XObjects
        n = mupdf.pdf_dict_len(xobj)
        for i in range(n):
            obj = mupdf.pdf_dict_get_val(xobj, i)
            if mupdf.pdf_is_stream(obj):
                sxref = mupdf.pdf_to_num(obj)
            else:
                sxref = 0
            subrsrc = mupdf.pdf_dict_get(obj, mupdf.PDF_ENUM_NAME_Resources)
            if subrsrc.m_internal:
                sxref_t = sxref
                if sxref_t not in tracer:
                    tracer.append(sxref_t)
                    JM_scan_resources( pdf, subrsrc, liste, what, sxref, tracer)
                else:
                    mupdf.fz_warn('Circular dependencies! Consider page cleaning.')
                    return
    finally:
        mupdf.pdf_unmark_obj(rsrc)


def JM_set_choice_options(annot, liste):
    '''
    set ListBox / ComboBox values
    '''
    if not liste:
        return
    assert isinstance( liste, (tuple, list))
    n = len( liste)
    if n == 0:
        return
    annot_obj = mupdf.pdf_annot_obj( annot)
    pdf = mupdf.pdf_get_bound_document( annot_obj)
    optarr = mupdf.pdf_new_array( pdf, n)
    for i in range(n):
        val = liste[i]
        opt = val
        if isinstance(opt, str):
            mupdf.pdf_array_push_text_string( optarr, opt)
        else:
            assert isinstance( val, (tuple, list)) and len( val) == 2, 'bad choice field list'
            opt1, opt2 = val
            assert opt1 and opt2, 'bad choice field list'
            optarrsub = mupdf.pdf_array_push_array( optarr, 2)
            mupdf.pdf_array_push_text_string( optarrsub, opt1)
            mupdf.pdf_array_push_text_string( optarrsub, opt2)
    mupdf.pdf_dict_put( annot_obj, PDF_NAME('Opt'), optarr)


def JM_set_field_type(doc, obj, type):
    '''
    Set the field type
    '''
    setbits = 0
    clearbits = 0
    typename = None
    if type == mupdf.PDF_WIDGET_TYPE_BUTTON:
        typename = PDF_NAME('Btn')
        setbits = mupdf.PDF_BTN_FIELD_IS_PUSHBUTTON
    elif type == mupdf.PDF_WIDGET_TYPE_RADIOBUTTON:
        typename = PDF_NAME('Btn')
        clearbits = mupdf.PDF_BTN_FIELD_IS_PUSHBUTTON
        setbits = mupdf.PDF_BTN_FIELD_IS_RADIO
    elif type == mupdf.PDF_WIDGET_TYPE_CHECKBOX:
        typename = PDF_NAME('Btn')
        clearbits = (mupdf.PDF_BTN_FIELD_IS_PUSHBUTTON | mupdf.PDF_BTN_FIELD_IS_RADIO)
    elif type == mupdf.PDF_WIDGET_TYPE_TEXT:
        typename = PDF_NAME('Tx')
    elif type == mupdf.PDF_WIDGET_TYPE_LISTBOX:
        typename = PDF_NAME('Ch')
        clearbits = mupdf.PDF_CH_FIELD_IS_COMBO
    elif type == mupdf.PDF_WIDGET_TYPE_COMBOBOX:
        typename = PDF_NAME('Ch')
        setbits = mupdf.PDF_CH_FIELD_IS_COMBO
    elif type == mupdf.PDF_WIDGET_TYPE_SIGNATURE:
        typename = PDF_NAME('Sig')

    if typename is not None and typename.m_internal:
        mupdf.pdf_dict_put(obj, PDF_NAME('FT'), typename)

    if setbits != 0 or clearbits != 0:
        bits = mupdf.pdf_dict_get_int(obj, PDF_NAME('Ff'))
        bits &= ~clearbits
        bits |= setbits
        mupdf.pdf_dict_put_int(obj, PDF_NAME('Ff'), bits)


def JM_set_object_value(obj, key, value):
    '''
    Set a PDF dict key to some value
    '''
    eyecatcher = "fitz: replace me!"
    pdf = mupdf.pdf_get_bound_document(obj)
    # split PDF key at path seps and take last key part
    list_ = key.split('/')
    len_ = len(list_)
    i = len_ - 1
    skey = list_[i]

    del list_[i]    # del the last sub-key
    len_ = len(list_)   # remaining length
    testkey = mupdf.pdf_dict_getp(obj, key)    # check if key already exists
    if not testkey.m_internal:
        #No, it will be created here. But we cannot allow this happening if
        #indirect objects are referenced. So we check all higher level
        #sub-paths for indirect references.
        while len_ > 0:
            t = '/'.join(list_) # next high level
            if mupdf.pdf_is_indirect(mupdf.pdf_dict_getp(obj, JM_StrAsChar(t))):
                raise Exception("path to '%s' has indirects", JM_StrAsChar(skey))
            del list_[len_ - 1]   # del last sub-key
            len_ = len(list_)   # remaining length
    # Insert our eyecatcher. Will create all sub-paths in the chain, or
    # respectively remove old value of key-path.
    mupdf.pdf_dict_putp(obj, key, mupdf.pdf_new_text_string(eyecatcher))
    testkey = mupdf.pdf_dict_getp(obj, key)
    if not mupdf.pdf_is_string(testkey):
        raise Exception("cannot insert value for '%s'", key)
    temp = mupdf.pdf_to_text_string(testkey)
    if temp != eyecatcher:
        raise Exception("cannot insert value for '%s'", key)
    # read the result as a string
    res = JM_object_to_buffer(obj, 1, 0)
    objstr = JM_EscapeStrFromBuffer(res)

    # replace 'eyecatcher' by desired 'value'
    nullval = "/%s(%s)" % ( skey, eyecatcher)
    newval = "/%s %s" % (skey, value)
    newstr = objstr.replace(nullval, newval, 1)

    # make PDF object from resulting string
    new_obj = JM_pdf_obj_from_str(pdf, newstr)
    return new_obj


def JM_set_ocg_arrays(conf, basestate, on, off, rbgroups, locked):
    if basestate:
        mupdf.pdf_dict_put_name( conf, PDF_NAME('BaseState'), basestate)

    if on is not None:
        mupdf.pdf_dict_del( conf, PDF_NAME('ON'))
        if on:
            arr = mupdf.pdf_dict_put_array( conf, PDF_NAME('ON'), 1)
            JM_set_ocg_arrays_imp( arr, on)
    if off is not None:
        mupdf.pdf_dict_del( conf, PDF_NAME('OFF'))
        if off:
            arr = mupdf.pdf_dict_put_array( conf, PDF_NAME('OFF'), 1)
            JM_set_ocg_arrays_imp( arr, off)
    if locked is not None:
        mupdf.pdf_dict_del( conf, PDF_NAME('Locked'))
        if locked:
            arr = mupdf.pdf_dict_put_array( conf, PDF_NAME('Locked'), 1)
            JM_set_ocg_arrays_imp( arr, locked)
    if rbgroups is not None:
        mupdf.pdf_dict_del( conf, PDF_NAME('RBGroups'))
        if rbgroups:
            arr = mupdf.pdf_dict_put_array( conf, PDF_NAME('RBGroups'), 1)
            n =len(rbgroups)
            for i in range(n):
                item0 = rbgroups[i]
                obj = mupdf.pdf_array_push_array( arr, 1)
                JM_set_ocg_arrays_imp( obj, item0)


def JM_set_ocg_arrays_imp(arr, list_):
    '''
    Set OCG arrays from dict of Python lists
    Works with dict like {"basestate":name, "on":list, "off":list, "rbg":list}
    '''
    pdf = mupdf.pdf_get_bound_document(arr)
    for xref in list_:
        obj = mupdf.pdf_new_indirect(pdf, xref, 0)
        mupdf.pdf_array_push(arr, obj)


def JM_set_resource_property(ref, name, xref):
    '''
    Insert an item into Resources/Properties (used for Marked Content)
    Arguments:
    (1) e.g. page object, Form XObject
    (2) marked content name
    (3) xref of the referenced object (insert as indirect reference)
    '''
    pdf = mupdf.pdf_get_bound_document(ref)
    ind = mupdf.pdf_new_indirect(pdf, xref, 0)
    if not ind.m_internal:
        RAISEPY(MSG_BAD_XREF, PyExc_ValueError)
    resources = mupdf.pdf_dict_get(ref, PDF_NAME('Resources'))
    if not resources.m_internal:
        resources = mupdf.pdf_dict_put_dict(ref, PDF_NAME('Resources'), 1)
    properties = mupdf.pdf_dict_get(resources, PDF_NAME('Properties'))
    if not properties.m_internal:
        properties = mupdf.pdf_dict_put_dict(resources, PDF_NAME('Properties'), 1)
    mupdf.pdf_dict_put(properties, mupdf.pdf_new_name(name), ind)


def JM_set_widget_properties(annot, Widget):
    '''
    Update the PDF form field with the properties from a Python Widget object.
    Called by "Page.add_widget" and "Annot.update_widget".
    '''
    if isinstance( annot, Annot):
        annot = annot.this
    assert isinstance( annot, mupdf.PdfAnnot), f'{type(annot)=} {type=}'
    page = _pdf_annot_page(annot)
    assert page.m_internal, 'Annot is not bound to a page'
    annot_obj = mupdf.pdf_annot_obj(annot)
    pdf = page.doc()
    def GETATTR(name):
        return getattr(Widget, name, None)

    value = GETATTR("field_type")
    field_type = value

    # rectangle --------------------------------------------------------------
    value = GETATTR("rect")
    rect = JM_rect_from_py(value)
    rot_mat = JM_rotate_page_matrix(page)
    rect = mupdf.fz_transform_rect(rect, rot_mat)
    mupdf.pdf_set_annot_rect(annot, rect)

    # fill color -------------------------------------------------------------
    value = GETATTR("fill_color")
    if value and PySequence_Check(value):
        n = len(value)
        fill_col = mupdf.pdf_new_array(pdf, n)
        col = 0
        for i in range(n):
            col = value[i]
            mupdf.pdf_array_push_real(fill_col, col)
        mupdf.pdf_field_set_fill_color(annot_obj, fill_col)

    # dashes -----------------------------------------------------------------
    value = GETATTR("border_dashes")
    if value and PySequence_Check(value):
        n = len(value)
        dashes = mupdf.pdf_new_array(pdf, n)
        for i in range(n):
            mupdf.pdf_array_push_int(dashes, value[i])
        mupdf.pdf_dict_putl(annot_obj, dashes, PDF_NAME('BS'), PDF_NAME('D'))

    # border color -----------------------------------------------------------
    value = GETATTR("border_color")
    if value and PySequence_Check(value):
        n = len(value)
        border_col = mupdf.pdf_new_array(pdf, n)
        col = 0
        for i in range(n):
            col = value[i]
            mupdf.pdf_array_push_real(border_col, col)
        mupdf.pdf_dict_putl(annot_obj, border_col, PDF_NAME('MK'), PDF_NAME('BC'))

    # entry ignored - may be used later
    #
    #int text_format = (int) PyInt_AsLong(GETATTR("text_format"));
    #

    # field label -----------------------------------------------------------
    value = GETATTR("field_label")
    if value is not None:
        label = JM_StrAsChar(value)
        mupdf.pdf_dict_put_text_string(annot_obj, PDF_NAME('TU'), label)

    # field name -------------------------------------------------------------
    value = GETATTR("field_name")
    if value is not None:
        name = JM_StrAsChar(value)
        old_name = mupdf.pdf_load_field_name(annot_obj)
        if name != old_name:
            mupdf.pdf_dict_put_text_string(annot_obj, PDF_NAME('T'), name)

    # max text len -----------------------------------------------------------
    if field_type == mupdf.PDF_WIDGET_TYPE_TEXT:
        value = GETATTR("text_maxlen")
        text_maxlen = value
        if text_maxlen:
            mupdf.pdf_dict_put_int(annot_obj, PDF_NAME('MaxLen'), text_maxlen)
    value = GETATTR("field_display")
    d = value
    mupdf.pdf_field_set_display(annot_obj, d)

    # choice values ----------------------------------------------------------
    if field_type in (mupdf.PDF_WIDGET_TYPE_LISTBOX, mupdf.PDF_WIDGET_TYPE_COMBOBOX):
        value = GETATTR("choice_values")
        JM_set_choice_options(annot, value)

    # border style -----------------------------------------------------------
    value = GETATTR("border_style")
    val = JM_get_border_style(value)
    mupdf.pdf_dict_putl(annot_obj, val, PDF_NAME('BS'), PDF_NAME('S'))

    # border width -----------------------------------------------------------
    value = GETATTR("border_width")
    border_width = value
    mupdf.pdf_dict_putl(
            annot_obj,
            mupdf.pdf_new_real(border_width),
            PDF_NAME('BS'),
            PDF_NAME('W'),
            )

    # /DA string -------------------------------------------------------------
    value = GETATTR("_text_da")
    da = JM_StrAsChar(value)
    mupdf.pdf_dict_put_text_string(annot_obj, PDF_NAME('DA'), da)
    mupdf.pdf_dict_del(annot_obj, PDF_NAME('DS'))  # not supported by MuPDF
    mupdf.pdf_dict_del(annot_obj, PDF_NAME('RC'))  # not supported by MuPDF

    # field flags ------------------------------------------------------------
    field_flags = GETATTR("field_flags")
    if field_flags is not None:
        if field_type == mupdf.PDF_WIDGET_TYPE_COMBOBOX:
            field_flags |= mupdf.PDF_CH_FIELD_IS_COMBO
        elif field_type == mupdf.PDF_WIDGET_TYPE_RADIOBUTTON:
            field_flags |= mupdf.PDF_BTN_FIELD_IS_RADIO
        elif field_type == mupdf.PDF_WIDGET_TYPE_BUTTON:
            field_flags |= mupdf.PDF_BTN_FIELD_IS_PUSHBUTTON
        mupdf.pdf_dict_put_int( annot_obj, PDF_NAME('Ff'), field_flags)

    # button caption ---------------------------------------------------------
    value = GETATTR("button_caption")
    ca = JM_StrAsChar(value)
    if ca:
        mupdf.pdf_field_set_button_caption(annot_obj, ca)

    # script (/A) -------------------------------------------------------
    value = GETATTR("script")
    JM_put_script(annot_obj, PDF_NAME('A'), mupdf.PdfObj(), value)

    # script (/AA/K) -------------------------------------------------------
    value = GETATTR("script_stroke")
    JM_put_script(annot_obj, PDF_NAME('AA'), PDF_NAME('K'), value)

    # script (/AA/F) -------------------------------------------------------
    value = GETATTR("script_format")
    JM_put_script(annot_obj, PDF_NAME('AA'), PDF_NAME('F'), value)

    # script (/AA/V) -------------------------------------------------------
    value = GETATTR("script_change")
    JM_put_script(annot_obj, PDF_NAME('AA'), PDF_NAME('V'), value)

    # script (/AA/C) -------------------------------------------------------
    value = GETATTR("script_calc")
    JM_put_script(annot_obj, PDF_NAME('AA'), PDF_NAME('C'), value)

    # script (/AA/Bl) -------------------------------------------------------
    value = GETATTR("script_blur")
    JM_put_script(annot_obj, PDF_NAME('AA'), mupdf.pdf_new_name('Bl'), value)

    # script (/AA/Fo) codespell:ignore --------------------------------------
    value = GETATTR("script_focus")
    JM_put_script(annot_obj, PDF_NAME('AA'), mupdf.pdf_new_name('Fo'), value)

    # field value ------------------------------------------------------------
    value = GETATTR("field_value")  # field value
    text = JM_StrAsChar(value)  # convert to text (may fail!)
    if field_type == mupdf.PDF_WIDGET_TYPE_RADIOBUTTON:
        if not value:
            mupdf.pdf_set_field_value(pdf, annot_obj, "Off", 1)
            mupdf.pdf_dict_put_name(annot_obj, PDF_NAME('AS'), "Off")
        else:
            # TODO check if another button in the group is ON and if so set it Off
            onstate = mupdf.pdf_button_field_on_state(annot_obj)
            if onstate.m_internal:
                on = mupdf.pdf_to_name(onstate)
                mupdf.pdf_set_field_value(pdf, annot_obj, on, 1)
                mupdf.pdf_dict_put_name(annot_obj, PDF_NAME('AS'), on)
            elif text:
                mupdf.pdf_dict_put_name(annot_obj, PDF_NAME('AS'), text)
    elif field_type == mupdf.PDF_WIDGET_TYPE_CHECKBOX:
        onstate = mupdf.pdf_button_field_on_state(annot_obj)
        on = onstate.pdf_to_name()
        if value in (True, on) or text == 'Yes':
            mupdf.pdf_set_field_value(pdf, annot_obj, on, 1)
            mupdf.pdf_dict_put_name(annot_obj, PDF_NAME('AS'), on)
            mupdf.pdf_dict_put_name(annot_obj, PDF_NAME('V'), on)
        else:
            mupdf.pdf_dict_put_name( annot_obj, PDF_NAME('AS'), 'Off')
            mupdf.pdf_dict_put_name( annot_obj, PDF_NAME('V'), 'Off')
    else:
        if text:
            mupdf.pdf_set_field_value(pdf, annot_obj, text, 1)
            if field_type in (mupdf.PDF_WIDGET_TYPE_COMBOBOX, mupdf.PDF_WIDGET_TYPE_LISTBOX):
                mupdf.pdf_dict_del(annot_obj, PDF_NAME('I'))
    mupdf.pdf_dirty_annot(annot)
    mupdf.pdf_set_annot_hot(annot, 1)
    mupdf.pdf_set_annot_active(annot, 1)
    mupdf.pdf_update_annot(annot)


def JM_show_string_cs(
        text,
        user_font,
        trm,
        s,
        wmode,
        bidi_level,
        markup_dir,
        language,
        ):
    i = 0
    while i < len(s):
        l, ucs = mupdf.fz_chartorune(s[i:])
        i += l
        gid = mupdf.fz_encode_character_sc(user_font, ucs)
        if gid == 0:
            gid, font = mupdf.fz_encode_character_with_fallback(user_font, ucs, 0, language)
        else:
            font = user_font
        mupdf.fz_show_glyph(text, font, trm, gid, ucs, wmode, bidi_level, markup_dir, language)
        adv = mupdf.fz_advance_glyph(font, gid, wmode)
        if wmode == 0:
            trm = mupdf.fz_pre_translate(trm, adv, 0)
        else:
            trm = mupdf.fz_pre_translate(trm, 0, -adv)
    return trm


def JM_UnicodeFromBuffer(buff):
    buff_bytes = mupdf.fz_buffer_extract_copy(buff)
    val = buff_bytes.decode(errors='replace')
    z = val.find(chr(0))
    if z >= 0:
        val = val[:z]
    return val


def message_warning(text):
    '''
    Generate a warning.
    '''
    message(f'warning: {text}')


def JM_update_stream(doc, obj, buffer_, compress):
    '''
    update a stream object
    compress stream when beneficial
    '''
    if compress:
        length, _ = mupdf.fz_buffer_storage(buffer_)
        if length > 30:   # ignore small stuff
            buffer_compressed = JM_compress_buffer(buffer_)
            assert isinstance(buffer_compressed, mupdf.FzBuffer)
            if buffer_compressed.m_internal:
                length_compressed, _ = mupdf.fz_buffer_storage(buffer_compressed)
                if length_compressed < length:  # was it worth the effort?
                    mupdf.pdf_dict_put(
                            obj,
                            mupdf.PDF_ENUM_NAME_Filter,
                            mupdf.PDF_ENUM_NAME_FlateDecode,
                            )
                    mupdf.pdf_update_stream(doc, obj, buffer_compressed, 1)
                    return
    
    mupdf.pdf_update_stream(doc, obj, buffer_, 0)


def JM_xobject_from_page(pdfout, fsrcpage, xref, gmap):
    '''
    Make an XObject from a PDF page
    For a positive xref assume that its object can be used instead
    '''
    assert isinstance(gmap, mupdf.PdfGraftMap), f'{type(gmap)=}'
    if xref > 0:
        xobj1 = mupdf.pdf_new_indirect(pdfout, xref, 0)
    else:
        srcpage = _as_pdf_page(fsrcpage.this)
        spageref = srcpage.obj()
        mediabox = mupdf.pdf_to_rect(mupdf.pdf_dict_get_inheritable(spageref, PDF_NAME('MediaBox')))
        # Deep-copy resources object of source page
        o = mupdf.pdf_dict_get_inheritable(spageref, PDF_NAME('Resources'))
        if gmap.m_internal:
            # use graftmap when possible
            resources = mupdf.pdf_graft_mapped_object(gmap, o)
        else:
            resources = mupdf.pdf_graft_object(pdfout, o)

        # get spgage contents source
        res = JM_read_contents(spageref)

        #-------------------------------------------------------------
        # create XObject representing the source page
        #-------------------------------------------------------------
        xobj1 = mupdf.pdf_new_xobject(pdfout, mediabox, mupdf.FzMatrix(), mupdf.PdfObj(0), res)
        # store spage contents
        JM_update_stream(pdfout, xobj1, res, 1)

        # store spage resources
        mupdf.pdf_dict_put(xobj1, PDF_NAME('Resources'), resources)
    return xobj1


def PySequence_Check(s):
    return isinstance(s, (tuple, list))


def PySequence_Size(s):
    return len(s)


# constants: error messages. These are also in extra.i.
#
MSG_BAD_ANNOT_TYPE = "bad annot type"
MSG_BAD_APN = "bad or missing annot AP/N"
MSG_BAD_ARG_INK_ANNOT = "arg must be seq of seq of float pairs"
MSG_BAD_ARG_POINTS = "bad seq of points"
MSG_BAD_BUFFER = "bad type: 'buffer'"
MSG_BAD_COLOR_SEQ = "bad color sequence"
MSG_BAD_DOCUMENT = "cannot open broken document"
MSG_BAD_FILETYPE = "bad filetype"
MSG_BAD_LOCATION = "bad location"
MSG_BAD_OC_CONFIG = "bad config number"
MSG_BAD_OC_LAYER = "bad layer number"
MSG_BAD_OC_REF = "bad 'oc' reference"
MSG_BAD_PAGEID = "bad page id"
MSG_BAD_PAGENO = "bad page number(s)"
MSG_BAD_PDFROOT = "PDF has no root"
MSG_BAD_RECT = "rect is infinite or empty"
MSG_BAD_TEXT = "bad type: 'text'"
MSG_BAD_XREF = "bad xref"
MSG_COLOR_COUNT_FAILED = "color count failed"
MSG_FILE_OR_BUFFER = "need font file or buffer"
MSG_FONT_FAILED = "cannot create font"
MSG_IS_NO_ANNOT = "is no annotation"
MSG_IS_NO_IMAGE = "is no image"
MSG_IS_NO_PDF = "is no PDF"
MSG_IS_NO_DICT = "object is no PDF dict"
MSG_PIX_NOALPHA = "source pixmap has no alpha"
MSG_PIXEL_OUTSIDE = "pixel(s) outside image"


JM_Exc_FileDataError = 'FileDataError'
PyExc_ValueError = 'ValueError'

def RAISEPY( msg, exc):
    #JM_Exc_CurrentException=exc
    #fz_throw(context, FZ_ERROR_GENERIC, msg)
    raise Exception( msg)


def PyUnicode_DecodeRawUnicodeEscape(s, errors='strict'):
    # FIXED: handle raw unicode escape sequences
    if not s:
        return ""
    if isinstance(s, str):
        rc = s.encode("utf8", errors=errors)
    elif isinstance(s, bytes):
        rc = s[:]
    ret = rc.decode('raw_unicode_escape', errors=errors)
    return ret


def CheckColor(c: OptSeq):
    if c:
        if (
            type(c) not in (list, tuple)
            or len(c) not in (1, 3, 4)
            or min(c) < 0
            or max(c) > 1
        ):
            raise ValueError("need 1, 3 or 4 color components in range 0 to 1")


def CheckFont(page: Page, fontname: str) -> tuple:
    """Return an entry in the page's font list if reference name matches.
    """
    for f in page.get_fonts():
        if f[4] == fontname:
            return f


def CheckFontInfo(doc: Document, xref: int) -> list:
    """Return a font info if present in the document.
    """
    for f in doc.FontInfos:
        if xref == f[0]:
            return f


def CheckMarkerArg(quads: typing.Any) -> tuple:
    if CheckRect(quads):
        r = Rect(quads)
        return (r.quad,)
    if CheckQuad(quads):
        return (quads,)
    for q in quads:
        if not (CheckRect(q) or CheckQuad(q)):
            raise ValueError("bad quads entry")
    return quads


def CheckMorph(o: typing.Any) -> bool:
    if not bool(o):
        return False
    if not (type(o) in (list, tuple) and len(o) == 2):
        raise ValueError("morph must be a sequence of length 2")
    if not (len(o[0]) == 2 and len(o[1]) == 6):
        raise ValueError("invalid morph param 0")
    if not o[1][4] == o[1][5] == 0:
        raise ValueError("invalid morph param 1")
    return True


def CheckParent(o: typing.Any):
    return
    if not hasattr(o, "parent") or o.parent is None:
        raise ValueError(f"orphaned object {type(o)=}: parent is None")


def CheckQuad(q: typing.Any) -> bool:
    """Check whether an object is convex, not empty  quad-like.

    It must be a sequence of 4 number pairs.
    """
    try:
        q0 = Quad(q)
    except Exception:
        if g_exceptions_verbose > 1:    exception_info()
        return False
    return q0.is_convex


def CheckRect(r: typing.Any) -> bool:
    """Check whether an object is non-degenerate rect-like.

    It must be a sequence of 4 numbers.
    """
    try:
        r = Rect(r)
    except Exception:
        if g_exceptions_verbose > 1:    exception_info()
        return False
    return not (r.is_empty or r.is_infinite)


def ColorCode(c: typing.Union[list, tuple, float, None], f: str) -> str:
    if not c:
        return ""
    if hasattr(c, "__float__"):
        c = (c,)
    CheckColor(c)
    if len(c) == 1:
        s = _format_g(c[0]) + " "
        return s + "G " if f == "c" else s + "g "

    if len(c) == 3:
        s = _format_g(tuple(c)) + " "
        return s + "RG " if f == "c" else s + "rg "

    s = _format_g(tuple(c)) + " "
    return s + "K " if f == "c" else s + "k "


def Page__add_text_marker(self, quads, annot_type):
    pdfpage = self._pdf_page()
    rotation = JM_page_rotation(pdfpage)
    def final():
        if rotation != 0:
            mupdf.pdf_dict_put_int(pdfpage.obj(), PDF_NAME('Rotate'), rotation)
    try:
        if rotation != 0:
            mupdf.pdf_dict_put_int(pdfpage.obj(), PDF_NAME('Rotate'), 0)
        annot = mupdf.pdf_create_annot(pdfpage, annot_type)
        for item in quads:
            q = JM_quad_from_py(item)
            mupdf.pdf_add_annot_quad_point(annot, q)
        mupdf.pdf_update_annot(annot)
        JM_add_annot_id(annot, "A")
        final()
    except Exception:
        if g_exceptions_verbose:    exception_info()
        final()
        return
    return Annot(annot)


def PDF_NAME(x):
    assert isinstance(x, str)
    return getattr(mupdf, f'PDF_ENUM_NAME_{x}')


def UpdateFontInfo(doc: Document, info: typing.Sequence):
    xref = info[0]
    found = False
    for i, fi in enumerate(doc.FontInfos):
        if fi[0] == xref:
            found = True
            break
    if found:
        doc.FontInfos[i] = info
    else:
        doc.FontInfos.append(info)


def args_match(args, *types):
    '''
    Returns true if <args> matches <types>.

    Each item in <types> is a type or tuple of types. Any of these types will
    match an item in <args>. `None` will match anything in <args>. `type(None)`
    will match an arg whose value is `None`.
    '''
    j = 0
    for i in range(len(types)):
        type_ = types[i]
        if j >= len(args):
            if isinstance(type_, tuple) and None in type_:
                # arg is missing but has default value.
                continue
            else:
                return False
        if type_ is not None and not isinstance(args[j], type_):
            return False
        j += 1
    if j != len(args):
        return False
    return True


def calc_image_matrix(width, height, tr, rotate, keep):
    '''
    # compute image insertion matrix
    '''
    trect = JM_rect_from_py(tr)
    rot = mupdf.fz_rotate(rotate)
    trw = trect.x1 - trect.x0
    trh = trect.y1 - trect.y0
    w = trw
    h = trh
    if keep:
        large = max(width, height)
        fw = width / large
        fh = height / large
    else:
        fw = fh = 1
    small = min(fw, fh)
    if rotate != 0 and rotate != 180:
        f = fw
        fw = fh
        fh = f
    if fw < 1:
        if trw / fw > trh / fh:
            w = trh * small
            h = trh
        else:
            w = trw
            h = trw / small
    elif fw != fh:
        if trw / fw > trh / fh:
            w = trh / small
            h = trh
        else:
            w = trw
            h = trw * small
    else:
        w = trw
        h = trh
    tmp = mupdf.fz_make_point(
            (trect.x0 + trect.x1) / 2,
            (trect.y0 + trect.y1) / 2,
            )
    mat = mupdf.fz_make_matrix(1, 0, 0, 1, -0.5, -0.5)
    mat = mupdf.fz_concat(mat, rot)
    mat = mupdf.fz_concat(mat, mupdf.fz_scale(w, h))
    mat = mupdf.fz_concat(mat, mupdf.fz_translate(tmp.x, tmp.y))
    return mat


def detect_super_script(line, ch):
    if line.m_internal.wmode == 0 and line.m_internal.dir.x == 1 and line.m_internal.dir.y == 0:
        return ch.m_internal.origin.y < line.m_internal.first_char.origin.y - ch.m_internal.size * 0.1
    return 0


def dir_str(x):
    ret = f'{x} {type(x)} ({len(dir(x))}):\n'
    for i in dir(x):
        ret += f'    {i}\n'
    return ret


def getTJstr(text: str, glyphs: typing.Union[list, tuple, None], simple: bool, ordering: int) -> str:
    """ Return a PDF string enclosed in [] brackets, suitable for the PDF TJ
    operator.

    Notes:
        The input string is converted to either 2 or 4 hex digits per character.
    Args:
        simple: no glyphs: 2-chars, use char codes as the glyph
                glyphs: 2-chars, use glyphs instead of char codes (Symbol,
                ZapfDingbats)
        not simple: ordering < 0: 4-chars, use glyphs not char codes
                    ordering >=0: a CJK font! 4 chars, use char codes as glyphs
    """
    if text.startswith("[<") and text.endswith(">]"):  # already done
        return text

    if not bool(text):
        return "[<>]"

    if simple:  # each char or its glyph is coded as a 2-byte hex
        if glyphs is None:  # not Symbol, not ZapfDingbats: use char code
            otxt = "".join(["%02x" % ord(c) if ord(c) < 256 else "b7" for c in text])
        else:  # Symbol or ZapfDingbats: use glyphs
            otxt = "".join(
                ["%02x" % glyphs[ord(c)][0] if ord(c) < 256 else "b7" for c in text]
            )
        return "[<" + otxt + ">]"

    # non-simple fonts: each char or its glyph is coded as 4-byte hex
    if ordering < 0:  # not a CJK font: use the glyphs
        otxt = "".join(["%04x" % glyphs[ord(c)][0] for c in text])
    else:  # CJK: use the char codes
        otxt = "".join(["%04x" % ord(c) for c in text])

    return "[<" + otxt + ">]"


def get_pdf_str(s: str) -> str:
    """ Return a PDF string depending on its coding.

    Notes:
        Returns a string bracketed with either "()" or "<>" for hex values.
        If only ascii then "(original)" is returned, else if only 8 bit chars
        then "(original)" with interspersed octal strings \nnn is returned,
        else a string "<FEFF[hexstring]>" is returned, where [hexstring] is the
        UTF-16BE encoding of the original.
    """
    if not bool(s):
        return "()"

    def make_utf16be(s):
        r = bytearray([254, 255]) + bytearray(s, "UTF-16BE")
        return "<" + r.hex() + ">"  # brackets indicate hex

    # The following either returns the original string with mixed-in
    # octal numbers \nnn for chars outside the ASCII range, or returns
    # the UTF-16BE BOM version of the string.
    r = ""
    for c in s:
        oc = ord(c)
        if oc > 255:  # shortcut if beyond 8-bit code range
            return make_utf16be(s)

        if oc > 31 and oc < 127:  # in ASCII range
            if c in ("(", ")", "\\"):  # these need to be escaped
                r += "\\"
            r += c
            continue

        if oc > 127:  # beyond ASCII
            r += "\\%03o" % oc
            continue

        # now the white spaces
        if oc == 8:  # backspace
            r += "\\b"
        elif oc == 9:  # tab
            r += "\\t"
        elif oc == 10:  # line feed
            r += "\\n"
        elif oc == 12:  # form feed
            r += "\\f"
        elif oc == 13:  # carriage return
            r += "\\r"
        else:
            r += "\\267"  # unsupported: replace by 0xB7

    return "(" + r + ")"


def get_tessdata(tessdata=None):
    """Detect Tesseract language support folder.

    This function is used to enable OCR via Tesseract even if the language
    support folder is not specified directly or in environment variable
    TESSDATA_PREFIX.

    * If <tessdata> is set we return it directly.
    
    * Otherwise we return `os.environ['TESSDATA_PREFIX']` if set.
    
    * Otherwise we search for a Tesseract installation and return its language
      support folder.

    * Otherwise we raise an exception.
    """
    if tessdata:
        return tessdata
    tessdata = os.getenv("TESSDATA_PREFIX")
    if tessdata:  # use environment variable if set
        return tessdata

    # Try to locate the tesseract-ocr installation.
    
    import subprocess
    # Windows systems:
    if sys.platform == "win32":
        cp = subprocess.run("where tesseract", shell=1, capture_output=1, check=0, text=True)
        response = cp.stdout.strip()
        if cp.returncode or not response:
            raise RuntimeError("No tessdata specified and Tesseract is not installed")
        dirname = os.path.dirname(response)  # path of tesseract.exe
        tessdata = os.path.join(dirname, "tessdata")  # language support
        if os.path.exists(tessdata):  # all ok?
            return tessdata
        else:  # should not happen!
            raise RuntimeError("No tessdata specified and Tesseract installation has no {tessdata} folder")

    # Unix-like systems:
    cp = subprocess.run("whereis tesseract-ocr", shell=1, capture_output=1, check=0, text=True)
    response = cp.stdout.strip().split()
    if cp.returncode or len(response) != 2:  # if not 2 tokens: no tesseract-ocr
        raise RuntimeError("No tessdata specified and Tesseract is not installed")

    # search tessdata in folder structure
    dirname = response[1]  # contains tesseract-ocr installation folder
    pattern = f"{dirname}/*/tessdata"
    tessdatas = glob.glob(pattern)
    tessdatas.sort()
    if tessdatas:
        return tessdatas[-1]
    else:
        raise RuntimeError("No tessdata specified and Tesseract installation has no {pattern} folder.")


def css_for_pymupdf_font(
    fontcode: str, *, CSS: OptStr = None, archive: AnyType = None, name: OptStr = None
) -> str:
    """Create @font-face items for the given fontcode of pymupdf-fonts.

    Adds @font-face support for fonts contained in package pymupdf-fonts.

    Creates a CSS font-family for all fonts starting with string 'fontcode'.

    Note:
        The font naming convention in package pymupdf-fonts is "fontcode<sf>",
        where the suffix "sf" is either empty or one of "it", "bo" or "bi".
        These suffixes thus represent the regular, italic, bold or bold-italic
        variants of a font. For example, font code "notos" refers to fonts
        "notos" - "Noto Sans Regular"
        "notosit" - "Noto Sans Italic"
        "notosbo" - "Noto Sans Bold"
        "notosbi" - "Noto Sans Bold Italic"

        This function creates four CSS @font-face definitions and collectively
        assigns the font-family name "notos" to them (or the "name" value).

    All fitting font buffers of the pymupdf-fonts package are placed / added
    to the archive provided as parameter.
    To use the font in pymupdf.Story, execute 'set_font(fontcode)'. The correct
    font weight (bold) or style (italic) will automatically be selected.
    Expects and returns the CSS source, with the new CSS definitions appended.

    Args:
        fontcode: (str) font code for naming the font variants to include.
                  E.g. "fig" adds notos, notosi, notosb, notosbi fonts.
                  A maximum of 4 font variants is accepted.
        CSS: (str) CSS string to add @font-face definitions to.
        archive: (Archive, mandatory) where to place the font buffers.
        name: (str) use this as family-name instead of 'fontcode'.
    Returns:
        Modified CSS, with appended @font-face statements for each font variant
        of fontcode.
        Fontbuffers associated with "fontcode" will be added to 'archive'.
    """
    # @font-face template string
    CSSFONT = "\n@font-face {font-family: %s; src: url(%s);%s%s}\n"

    if not type(archive) is Archive:
        raise ValueError("'archive' must be an Archive")
    if CSS is None:
        CSS = ""

    # select font codes starting with the pass-in string
    font_keys = [k for k in fitz_fontdescriptors.keys() if k.startswith(fontcode)]
    if font_keys == []:
        raise ValueError(f"No font code '{fontcode}' found in pymupdf-fonts.")
    if len(font_keys) > 4:
        raise ValueError("fontcode too short")
    if name is None:  # use this name for font-family
        name = fontcode

    for fkey in font_keys:
        font = fitz_fontdescriptors[fkey]
        bold = font["bold"]  # determine font property
        italic = font["italic"]  # determine font property
        fbuff = font["loader"]()  # load the fontbuffer
        archive.add(fbuff, fkey)  # update the archive
        bold_text = "font-weight: bold;" if bold else ""
        italic_text = "font-style: italic;" if italic else ""
        CSS += CSSFONT % (name, fkey, bold_text, italic_text)
    return CSS


def get_text_length(text: str, fontname: str ="helv", fontsize: float =11, encoding: int =0) -> float:
    """Calculate length of a string for a built-in font.

    Args:
        fontname: name of the font.
        fontsize: font size points.
        encoding: encoding to use, 0=Latin (default), 1=Greek, 2=Cyrillic.
    Returns:
        (float) length of text.
    """
    fontname = fontname.lower()
    basename = Base14_fontdict.get(fontname, None)

    glyphs = None
    if basename == "Symbol":
        glyphs = symbol_glyphs
    if basename == "ZapfDingbats":
        glyphs = zapf_glyphs
    if glyphs is not None:
        w = sum([glyphs[ord(c)][1] if ord(c) < 256 else glyphs[183][1] for c in text])
        return w * fontsize

    if fontname in Base14_fontdict.keys():
        return util_measure_string(
            text, Base14_fontdict[fontname], fontsize, encoding
        )

    if fontname in (
        "china-t",
        "china-s",
        "china-ts",
        "china-ss",
        "japan",
        "japan-s",
        "korea",
        "korea-s",
    ):
        return len(text) * fontsize

    raise ValueError("Font '%s' is unsupported" % fontname)


def image_profile(img: typing.ByteString) -> dict:
    """ Return basic properties of an image.

    Args:
        img: bytes, bytearray, io.BytesIO object or an opened image file.
    Returns:
        A dictionary with keys width, height, colorspace.n, bpc, type, ext and size,
        where 'type' is the MuPDF image type (0 to 14) and 'ext' the suitable
        file extension.
    """
    if type(img) is io.BytesIO:
        stream = img.getvalue()
    elif hasattr(img, "read"):
        stream = img.read()
    elif type(img) in (bytes, bytearray):
        stream = img
    else:
        raise ValueError("bad argument 'img'")

    return TOOLS.image_profile(stream)


def jm_append_merge(dev):
    '''
    Append current path to list or merge into last path of the list.
    (1) Append if first path, different item lists or not a 'stroke' version
        of previous path
    (2) If new path has the same items, merge its content into previous path
        and change path["type"] to "fs".
    (3) If "out" is callable, skip the previous and pass dictionary to it.
    '''
    #log(f'{getattr(dev, "pathdict", None)=}')
    assert isinstance(dev.out, list)
    #log( f'{dev.out=}')
    
    if callable(dev.method) or dev.method:  # function or method
        # callback.
        if dev.method is None:
            # fixme, this surely cannot happen?
            assert 0
            #resp = PyObject_CallFunctionObjArgs(out, dev.pathdict, NULL)
        else:
            #log(f'calling {dev.out=} {dev.method=} {dev.pathdict=}')
            resp = getattr(dev.out, dev.method)(dev.pathdict)
        if not resp:
            message("calling cdrawings callback function/method failed!")
        dev.pathdict = None
        return
    
    def append():
        #log(f'jm_append_merge(): clearing dev.pathdict')
        dev.out.append(dev.pathdict.copy())
        dev.pathdict.clear()
    assert isinstance(dev.out, list)
    len_ = len(dev.out) # len of output list so far
    #log('{len_=}')
    if len_ == 0:   # always append first path
        return append()
    #log(f'{getattr(dev, "pathdict", None)=}')
    thistype = dev.pathdict[ dictkey_type]
    #log(f'{thistype=}')
    if thistype != 's': # if not stroke, then append
        return append()
    prev = dev.out[ len_-1] # get prev path
    #log( f'{prev=}')
    prevtype = prev[ dictkey_type]
    #log( f'{prevtype=}')
    if prevtype != 'f': # if previous not fill, append
        return append()
    # last check: there must be the same list of items for "f" and "s".
    previtems = prev[ dictkey_items]
    thisitems = dev.pathdict[ dictkey_items]
    if previtems != thisitems:
        return append()
    
    #rc = PyDict_Merge(prev, dev.pathdict, 0);  // merge with no override
    try:
        for k, v in dev.pathdict.items():
            if k not in prev:
                prev[k] = v
        rc = 0
    except Exception:
        if g_exceptions_verbose:    exception_info()
        #raise
        rc = -1
    if rc == 0:
        prev[ dictkey_type] = 'fs'
        dev.pathdict.clear()
    else:
        message("could not merge stroke and fill path")
        append()


def jm_bbox_add_rect( dev, ctx, rect, code):
    if not dev.layers:
        dev.result.append( (code, JM_py_from_rect(rect)))
    else:
        dev.result.append( (code, JM_py_from_rect(rect), dev.layer_name))


def jm_bbox_fill_image( dev, ctx, image, ctm, alpha, color_params):
    r = mupdf.FzRect(mupdf.FzRect.Fixed_UNIT)
    r = mupdf.ll_fz_transform_rect( r.internal(), ctm)
    jm_bbox_add_rect( dev, ctx, r, "fill-image")


def jm_bbox_fill_image_mask( dev, ctx, image, ctm, colorspace, color, alpha, color_params):
    try:
        jm_bbox_add_rect( dev, ctx, mupdf.ll_fz_transform_rect(mupdf.fz_unit_rect, ctm), "fill-imgmask")
    except Exception:
        if g_exceptions_verbose:    exception_info()
        raise


def jm_bbox_fill_path( dev, ctx, path, even_odd, ctm, colorspace, color, alpha, color_params):
    even_odd = True if even_odd else False
    try:
        jm_bbox_add_rect( dev, ctx, mupdf.ll_fz_bound_path(path, None, ctm), "fill-path")
    except Exception:
        if g_exceptions_verbose:    exception_info()
        raise


def jm_bbox_fill_shade( dev, ctx, shade, ctm, alpha, color_params):
    try:
        jm_bbox_add_rect( dev, ctx, mupdf.ll_fz_bound_shade( shade, ctm), "fill-shade")
    except Exception:
        if g_exceptions_verbose:    exception_info()
        raise


def jm_bbox_stroke_text( dev, ctx, text, stroke, ctm, *args):
    try:
        jm_bbox_add_rect( dev, ctx, mupdf.ll_fz_bound_text( text, stroke, ctm), "stroke-text")
    except Exception:
        if g_exceptions_verbose:    exception_info()
        raise


def jm_bbox_fill_text( dev, ctx, text, ctm, *args):
    try:
        jm_bbox_add_rect( dev, ctx, mupdf.ll_fz_bound_text( text, None, ctm), "fill-text")
    except Exception:
        if g_exceptions_verbose:    exception_info()
        raise


def jm_bbox_ignore_text( dev, ctx, text, ctm):
    jm_bbox_add_rect( dev, ctx, mupdf.ll_fz_bound_text(text, None, ctm), "ignore-text")


def jm_bbox_stroke_path( dev, ctx, path, stroke, ctm, colorspace, color, alpha, color_params):
    try:
        jm_bbox_add_rect( dev, ctx, mupdf.ll_fz_bound_path( path, stroke, ctm), "stroke-path")
    except Exception:
        if g_exceptions_verbose:    exception_info()
        raise


def jm_checkquad(dev):
    '''
    Check whether the last 4 lines represent a quad.
    Because of how we count, the lines are a polyline already, i.e. last point
    of a line equals 1st point of next line.
    So we check for a polygon (last line's end point equals start point).
    If not true we return 0.
    '''
    #log(f'{getattr(dev, "pathdict", None)=}')
    items = dev.pathdict[ dictkey_items]
    len_ = len(items)
    f = [0] * 8 # coordinates of the 4 corners
    # fill the 8 floats in f, start from items[-4:]
    for i in range( 4): # store line start points
        line = items[ len_ - 4 + i]
        temp = JM_point_from_py( line[1])
        f[i * 2] = temp.x
        f[i * 2 + 1] = temp.y
        lp = JM_point_from_py( line[ 2])
    if lp.x != f[0] or lp.y != f[1]:
        # not a polygon!
        #dev.linecount -= 1
        return 0
    
    # we have detected a quad
    dev.linecount = 0   # reset this
    # a quad item is ("qu", (ul, ur, ll, lr)), where the tuple items
    # are pairs of floats representing a quad corner each.
    
    # relationship of float array to quad points:
    # (0, 1) = ul, (2, 3) = ll, (6, 7) = ur, (4, 5) = lr
    q = mupdf.fz_make_quad(f[0], f[1], f[6], f[7], f[2], f[3], f[4], f[5])
    rect = ('qu', JM_py_from_quad(q))
    
    items[ len_ - 4] = rect  # replace item -4 by rect
    del items[ len_ - 3 : len_]  # delete remaining 3 items
    return 1


def jm_checkrect(dev):
    '''
    Check whether the last 3 path items represent a rectangle.
    Returns 1 if we have modified the path, otherwise 0.
    '''
    #log(f'{getattr(dev, "pathdict", None)=}')
    dev.linecount = 0   # reset line count
    orientation = 0 # area orientation of rectangle
    items = dev.pathdict[ dictkey_items]
    len_ = len(items)

    line0 = items[ len_ - 3]
    ll = JM_point_from_py( line0[ 1])
    lr = JM_point_from_py( line0[ 2])

    # no need to extract "line1"!
    line2 = items[ len_ - 1]
    ur = JM_point_from_py( line2[ 1])
    ul = JM_point_from_py( line2[ 2])

    # Assumption:
    # When decomposing rects, MuPDF always starts with a horizontal line,
    # followed by a vertical line, followed by a horizontal line.
    # First line: (ll, lr), third line: (ul, ur).
    # If 1st line is below 3rd line, we record anti-clockwise (+1), else
    # clockwise (-1) orientation.
    
    if (0
            or ll.y != lr.y
            or ll.x != ul.x
            or ur.y != ul.y
            or ur.x != lr.x
            ):
        return 0 # not a rectangle
    
    # we have a rect, replace last 3 "l" items by one "re" item.
    if ul.y < lr.y:
        r = mupdf.fz_make_rect(ul.x, ul.y, lr.x, lr.y)
        orientation = 1
    else:
        r = mupdf.fz_make_rect(ll.x, ll.y, ur.x, ur.y)
        orientation = -1
    
    rect = ( 're', JM_py_from_rect(r), orientation)
    items[ len_ - 3] = rect # replace item -3 by rect
    del items[ len_ - 2 : len_] # delete remaining 2 items
    return 1


def jm_trace_text( dev, text, type_, ctm, colorspace, color, alpha, seqno):
    span = text.head
    while 1:
        if not span:
            break
        jm_trace_text_span( dev, span, type_, ctm, colorspace, color, alpha, seqno)
        span = span.next


def jm_trace_text_span(dev, span, type_, ctm, colorspace, color, alpha, seqno):
    '''
    jm_trace_text_span(fz_context *ctx, PyObject *out, fz_text_span *span, int type, fz_matrix ctm, fz_colorspace *colorspace, const float *color, float alpha, size_t seqno)
    '''
    out_font = None
    assert isinstance( span, mupdf.fz_text_span)
    span = mupdf.FzTextSpan( span)
    assert isinstance( ctm, mupdf.fz_matrix)
    ctm = mupdf.FzMatrix( ctm)
    fontname = JM_font_name( span.font())
    #float rgb[3];
    #PyObject *chars = PyTuple_New(span->len);
    
    mat = mupdf.fz_concat(span.trm(), ctm)  # text transformation matrix
    dir = mupdf.fz_transform_vector(mupdf.fz_make_point(1, 0), mat) # writing direction
    fsize = math.sqrt(dir.x * dir.x + dir.y * dir.y) # font size

    dir = mupdf.fz_normalize_vector(dir)

    space_adv = 0
    asc = JM_font_ascender( span.font())
    dsc = JM_font_descender( span.font())
    if asc < 1e-3:  # probably Tesseract font
        dsc = -0.1
        asc = 0.9

    # compute effective ascender / descender
    ascsize = asc * fsize / (asc - dsc)
    dscsize = dsc * fsize / (asc - dsc)
    fflags = 0  # font flags
    mono = mupdf.fz_font_is_monospaced( span.font())
    fflags += mono * TEXT_FONT_MONOSPACED
    fflags += mupdf.fz_font_is_italic( span.font()) * TEXT_FONT_ITALIC
    fflags += mupdf.fz_font_is_serif( span.font()) * TEXT_FONT_SERIFED
    fflags += mupdf.fz_font_is_bold( span.font()) * TEXT_FONT_BOLD

    last_adv = 0

    # walk through characters of span
    span_bbox = mupdf.FzRect()
    rot = mupdf.fz_make_matrix(dir.x, dir.y, -dir.y, dir.x, 0, 0)
    if dir.x == -1: # left-right flip
        rot.d = 1

    chars = []
    for i in range( span.m_internal.len):
        adv = 0
        if span.items(i).gid >= 0:
            adv = mupdf.fz_advance_glyph( span.font(), span.items(i).gid, span.m_internal.wmode)
        adv *= fsize
        last_adv = adv
        if span.items(i).ucs == 32:
            space_adv = adv
        char_orig = mupdf.fz_make_point(span.items(i).x, span.items(i).y)
        char_orig = mupdf.fz_transform_point(char_orig, ctm)
        m1 = mupdf.fz_make_matrix(1, 0, 0, 1, -char_orig.x, -char_orig.y)
        m1 = mupdf.fz_concat(m1, rot)
        m1 = mupdf.fz_concat(m1, mupdf.FzMatrix(1, 0, 0, 1, char_orig.x, char_orig.y))
        x0 = char_orig.x
        x1 = x0 + adv
        if (
                (mat.d > 0 and (dir.x == 1 or dir.x == -1))
                or
                (mat.b != 0 and mat.b == -mat.c)
                ):  # up-down flip
            y0 = char_orig.y + dscsize
            y1 = char_orig.y + ascsize
        else:
            y0 = char_orig.y - ascsize
            y1 = char_orig.y - dscsize
        char_bbox = mupdf.fz_make_rect(x0, y0, x1, y1)
        char_bbox = mupdf.fz_transform_rect(char_bbox, m1)
        chars.append(
                (
                    span.items(i).ucs,
                    span.items(i).gid,
                    (
                        char_orig.x,
                        char_orig.y,
                    ),
                    (
                        char_bbox.x0,
                        char_bbox.y0,
                        char_bbox.x1,
                        char_bbox.y1,
                    ),
                )
                )
        if i > 0:
            span_bbox = mupdf.fz_union_rect(span_bbox, char_bbox)
        else:
            span_bbox = char_bbox
    chars = tuple(chars)
    
    if not space_adv:
        if not (fflags & TEXT_FONT_MONOSPACED):
            c, out_font = mupdf.fz_encode_character_with_fallback( span.font(), 32, 0, 0)
            space_adv = mupdf.fz_advance_glyph(
                    span.font(),
                    c,
                    span.m_internal.wmode,
                    )
            space_adv *= fsize
            if not space_adv:
                space_adv = last_adv
        else:
            space_adv = last_adv    # for mono, any char width suffices

    # make the span dictionary
    span_dict = dict()
    span_dict[ 'dir'] = JM_py_from_point(dir)
    span_dict[ 'font'] = JM_EscapeStrFromStr(fontname)
    span_dict[ 'wmode'] = span.m_internal.wmode
    span_dict[ 'flags'] =fflags
    span_dict[ "bidi_lvl"] =span.m_internal.bidi_level
    span_dict[ "bidi_dir"] = span.m_internal.markup_dir
    span_dict[ 'ascender'] = asc
    span_dict[ 'descender'] = dsc
    span_dict[ 'colorspace'] = 3
    
    if colorspace:
        rgb = mupdf.fz_convert_color(
                mupdf.FzColorspace( mupdf.ll_fz_keep_colorspace( colorspace)),
                color,
                mupdf.fz_device_rgb(),
                mupdf.FzColorspace(),
                mupdf.FzColorParams(),
                )
        rgb = rgb[:3]   # mupdf.fz_convert_color() always returns 4 items.
    else:
        rgb = (0, 0, 0)
    
    if dev.linewidth > 0:   # width of character border
        linewidth = dev.linewidth
    else:
        linewidth = fsize * 0.05    # default: 5% of font size
    #log(f'{dev.linewidth=:.4f} {fsize=:.4f} {linewidth=:.4f}')
    
    span_dict[ 'color'] = rgb
    span_dict[ 'size'] = fsize
    span_dict[ "opacity"] = alpha
    span_dict[ "linewidth"] = linewidth
    span_dict[ "spacewidth"] = space_adv
    span_dict[ 'type'] = type_
    span_dict[ 'bbox'] = JM_py_from_rect(span_bbox)
    span_dict[ 'layer'] = dev.layer_name
    span_dict[ "seqno"] = seqno
    span_dict[ 'chars'] = chars
    #log(f'{span_dict=}')
    dev.out.append( span_dict)


def jm_lineart_color(colorspace, color):
    #log(f' ')
    if colorspace:
        try:
            # Need to be careful to use a named Python object to ensure
            # that the `params` we pass to mupdf.ll_fz_convert_color() is
            # valid. E.g. doing:
            #
            #   rgb = mupdf.ll_fz_convert_color(..., mupdf.FzColorParams().internal())
            #
            # - seems to end up with a corrupted `params`.
            #
            cs = mupdf.FzColorspace( mupdf.FzColorspace.Fixed_RGB)
            cp = mupdf.FzColorParams()
            rgb = mupdf.ll_fz_convert_color(
                    colorspace,
                    color,
                    cs.m_internal,
                    None,
                    cp.internal(),
                    )
        except Exception:
            if g_exceptions_verbose:    exception_info()
            raise
        return rgb[:3]
    return ()


def jm_lineart_drop_device(dev, ctx):
    if isinstance(dev.out, list):
        dev.out = []
    dev.scissors = []
 
 
def jm_lineart_fill_path( dev, ctx, path, even_odd, ctm, colorspace, color, alpha, color_params):
    #log(f'{getattr(dev, "pathdict", None)=}')
    #log(f'jm_lineart_fill_path(): {dev.seqno=}')
    even_odd = True if even_odd else False
    try:
        assert isinstance( ctm, mupdf.fz_matrix)
        dev.ctm = mupdf.FzMatrix( ctm)  # fz_concat(ctm, dev_ptm);
        dev.path_type = trace_device_FILL_PATH
        jm_lineart_path( dev, ctx, path)
        if dev.pathdict is None:
            return
        #item_count = len(dev.pathdict[ dictkey_items])
        #if item_count == 0:
        #    return
        dev.pathdict[ dictkey_type] ="f"
        dev.pathdict[ "even_odd"] = even_odd
        dev.pathdict[ "fill_opacity"] = alpha
        #log(f'setting dev.pathdict[ "closePath"] to false')
        #dev.pathdict[ "closePath"] = False
        dev.pathdict[ "fill"] = jm_lineart_color( colorspace, color)
        dev.pathdict[ dictkey_rect] = JM_py_from_rect(dev.pathrect)
        dev.pathdict[ "seqno"] = dev.seqno
        #jm_append_merge(dev)
        dev.pathdict[ 'layer'] = dev.layer_name
        if dev.clips:
            dev.pathdict[ 'level'] = dev.depth
        jm_append_merge(dev)
        dev.seqno += 1
        #log(f'jm_lineart_fill_path() end: {getattr(dev, "pathdict", None)=}')
    except Exception:
        if g_exceptions_verbose:    exception_info()
        raise


# There are 3 text trace types:
# 0 - fill text (PDF Tr 0)
# 1 - stroke text (PDF Tr 1)
# 3 - ignore text (PDF Tr 3)

def jm_lineart_fill_text( dev, ctx, text, ctm, colorspace, color, alpha, color_params):
    if 0:
        log(f'{type(ctx)=} {ctx=}')
        log(f'{type(dev)=} {dev=}')
        log(f'{type(text)=} {text=}')
        log(f'{type(ctm)=} {ctm=}')
        log(f'{type(colorspace)=} {colorspace=}')
        log(f'{type(color)=} {color=}')
        log(f'{type(alpha)=} {alpha=}')
        log(f'{type(color_params)=} {color_params=}')
    jm_trace_text(dev, text, 0, ctm, colorspace, color, alpha, dev.seqno)
    dev.seqno += 1


def jm_lineart_ignore_text(dev, text, ctm):
    #log(f'{getattr(dev, "pathdict", None)=}')
    jm_trace_text(dev, text, 3, ctm, None, None, 1, dev.seqno)
    dev.seqno += 1


class Walker(mupdf.FzPathWalker2):

    def __init__(self, dev):
        super().__init__()
        self.use_virtual_moveto()
        self.use_virtual_lineto()
        self.use_virtual_curveto()
        self.use_virtual_closepath()
        self.dev = dev

    def closepath(self, ctx):    # trace_close().
        #log(f'Walker(): {self.dev.pathdict=}')
        try:
            if self.dev.linecount == 3:
                if jm_checkrect(self.dev):
                    #log(f'end1: {self.dev.pathdict=}')
                    return
            self.dev.linecount = 0   # reset # of consec. lines

            if self.dev.havemove:
                if self.dev.lastpoint != self.dev.firstpoint:
                    item = ("l", JM_py_from_point(self.dev.lastpoint),
                                 JM_py_from_point(self.dev.firstpoint))
                    self.dev.pathdict[dictkey_items].append(item)
                    self.dev.lastpoint = self.dev.firstpoint
                self.dev.pathdict["closePath"] = False

            else:
                #log('setting self.dev.pathdict[ "closePath"] to true')
                self.dev.pathdict[ "closePath"] = True
                #log(f'end2: {self.dev.pathdict=}')

            self.dev.havemove = 0

        except Exception:
            if g_exceptions_verbose:    exception_info()
            raise

    def curveto(self, ctx, x1, y1, x2, y2, x3, y3):   # trace_curveto().
        #log(f'Walker(): {self.dev.pathdict=}')
        try:
            self.dev.linecount = 0  # reset # of consec. lines
            p1 = mupdf.fz_make_point(x1, y1)
            p2 = mupdf.fz_make_point(x2, y2)
            p3 = mupdf.fz_make_point(x3, y3)
            p1 = mupdf.fz_transform_point(p1, self.dev.ctm)
            p2 = mupdf.fz_transform_point(p2, self.dev.ctm)
            p3 = mupdf.fz_transform_point(p3, self.dev.ctm)
            self.dev.pathrect = mupdf.fz_include_point_in_rect(self.dev.pathrect, p1)
            self.dev.pathrect = mupdf.fz_include_point_in_rect(self.dev.pathrect, p2)
            self.dev.pathrect = mupdf.fz_include_point_in_rect(self.dev.pathrect, p3)

            list_ = (
                    "c",
                    JM_py_from_point(self.dev.lastpoint),
                    JM_py_from_point(p1),
                    JM_py_from_point(p2),
                    JM_py_from_point(p3),
                    )
            self.dev.lastpoint = p3
            self.dev.pathdict[ dictkey_items].append( list_)
        except Exception:
            if g_exceptions_verbose:    exception_info()
            raise

    def lineto(self, ctx, x, y):   # trace_lineto().
        #log(f'Walker(): {self.dev.pathdict=}')
        try:
            p1 = mupdf.fz_transform_point( mupdf.fz_make_point(x, y), self.dev.ctm)
            self.dev.pathrect = mupdf.fz_include_point_in_rect( self.dev.pathrect, p1)
            list_ = (
                    'l',
                    JM_py_from_point( self.dev.lastpoint),
                    JM_py_from_point(p1),
                    )
            self.dev.lastpoint = p1
            items = self.dev.pathdict[ dictkey_items]
            items.append( list_)
            self.dev.linecount += 1 # counts consecutive lines
            if self.dev.linecount == 4 and self.dev.path_type != trace_device_FILL_PATH:
                # shrink to "re" or "qu" item
                jm_checkquad(self.dev)
        except Exception:
            if g_exceptions_verbose:    exception_info()
            raise

    def moveto(self, ctx, x, y):   # trace_moveto().
        if 0 and isinstance(self.dev.pathdict, dict):
            log(f'self.dev.pathdict:')
            for n, v in self.dev.pathdict.items():
                log( '    {type(n)=} {len(n)=} {n!r} {n}: {v!r}: {v}')

        #log(f'Walker(): {type(self.dev.pathdict)=} {self.dev.pathdict=}')

        try:
            #log( '{=dev.ctm type(dev.ctm)}')
            self.dev.lastpoint = mupdf.fz_transform_point(
                    mupdf.fz_make_point(x, y),
                    self.dev.ctm,
                    )
            if mupdf.fz_is_infinite_rect( self.dev.pathrect):
                self.dev.pathrect = mupdf.fz_make_rect(
                        self.dev.lastpoint.x,
                        self.dev.lastpoint.y,
                        self.dev.lastpoint.x,
                        self.dev.lastpoint.y,
                        )
            self.dev.firstpoint = self.dev.lastpoint
            self.dev.havemove = 1
            self.dev.linecount = 0  # reset # of consec. lines
        except Exception:
            if g_exceptions_verbose:    exception_info()
            raise


def jm_lineart_path(dev, ctx, path):
    '''
    Create the "items" list of the path dictionary
    * either create or empty the path dictionary
    * reset the end point of the path
    * reset count of consecutive lines
    * invoke fz_walk_path(), which create the single items
    * if no items detected, empty path dict again
    '''
    #log(f'{getattr(dev, "pathdict", None)=}')
    try:
        dev.pathrect = mupdf.FzRect( mupdf.FzRect.Fixed_INFINITE)
        dev.linecount = 0
        dev.lastpoint = mupdf.FzPoint( 0, 0)
        dev.pathdict = dict()
        dev.pathdict[ dictkey_items] = []
        
        # First time we create a Walker instance is slow, e.g. 0.3s, then later
        # times run in around 0.01ms. If Walker is defined locally instead of
        # globally, each time takes 0.3s.
        #
        walker = Walker(dev)
        # Unlike fz_run_page(), fz_path_walker callbacks are not passed
        # a pointer to the struct, instead they get an arbitrary
        # void*. The underlying C++ Director callbacks use this void* to
        # identify the fz_path_walker instance so in turn we need to pass
        # arg=walker.m_internal.
        mupdf.fz_walk_path( mupdf.FzPath(mupdf.ll_fz_keep_path(path)), walker, walker.m_internal)
        # Check if any items were added ...
        if not dev.pathdict[ dictkey_items]:
            dev.pathdict = None
    except Exception:
        if g_exceptions_verbose:    exception_info()
        raise


def jm_lineart_stroke_path( dev, ctx, path, stroke, ctm, colorspace, color, alpha, color_params):
    #log(f'{dev.pathdict=} {dev.clips=}')
    try:
        assert isinstance( ctm, mupdf.fz_matrix)
        dev.pathfactor = 1
        if ctm.a != 0 and abs(ctm.a) == abs(ctm.d):
            dev.pathfactor = abs(ctm.a)
        elif ctm.b != 0 and abs(ctm.b) == abs(ctm.c):
            dev.pathfactor = abs(ctm.b)
        dev.ctm = mupdf.FzMatrix( ctm)  # fz_concat(ctm, dev_ptm);
        dev.path_type = trace_device_STROKE_PATH

        jm_lineart_path( dev, ctx, path)
        if dev.pathdict is None:
            return
        dev.pathdict[ dictkey_type] = 's'
        dev.pathdict[ 'stroke_opacity'] = alpha
        dev.pathdict[ 'color'] = jm_lineart_color( colorspace, color)
        dev.pathdict[ dictkey_width] = dev.pathfactor * stroke.linewidth
        dev.pathdict[ 'lineCap'] = (
                stroke.start_cap,
                stroke.dash_cap,
                stroke.end_cap,
                )
        dev.pathdict[ 'lineJoin'] = dev.pathfactor * stroke.linejoin
        if 'closePath' not in dev.pathdict:
            #log('setting dev.pathdict["closePath"] to false')
            dev.pathdict['closePath'] = False

        # output the "dashes" string
        if stroke.dash_len:
            buff = mupdf.fz_new_buffer( 256)
            mupdf.fz_append_string( buff, "[ ") # left bracket
            for i in range( stroke.dash_len):
                # We use mupdf python's SWIG-generated floats_getitem() fn to
                # access float *stroke.dash_list[].
                value = mupdf.floats_getitem( stroke.dash_list, i)  # stroke.dash_list[i].
                mupdf.fz_append_string( buff, f'{_format_g(dev.pathfactor * value)} ')
            mupdf.fz_append_string( buff, f'] {_format_g(dev.pathfactor * stroke.dash_phase)}')
            dev.pathdict[ 'dashes'] = buff
        else:
            dev.pathdict[ 'dashes'] = '[] 0'
        dev.pathdict[ dictkey_rect] = JM_py_from_rect(dev.pathrect)
        dev.pathdict['layer'] = dev.layer_name
        dev.pathdict[ 'seqno'] = dev.seqno
        if dev.clips:
            dev.pathdict[ 'level'] = dev.depth
        jm_append_merge(dev)
        dev.seqno += 1
    
    except Exception:
        if g_exceptions_verbose:    exception_info()
        raise


def jm_lineart_clip_path(dev, ctx, path, even_odd, ctm, scissor):
    if not dev.clips:
        return
    dev.ctm = mupdf.FzMatrix(ctm)    # fz_concat(ctm, trace_device_ptm);
    dev.path_type = trace_device_CLIP_PATH
    jm_lineart_path(dev, ctx, path)
    if dev.pathdict is None:
        return
    dev.pathdict[ dictkey_type] = 'clip'
    dev.pathdict[ 'even_odd'] = bool(even_odd)
    if 'closePath' not in dev.pathdict:
        #log(f'setting dev.pathdict["closePath"] to False')
        dev.pathdict['closePath'] = False
   
    dev.pathdict['scissor'] = JM_py_from_rect(compute_scissor(dev))
    dev.pathdict['level'] = dev.depth
    dev.pathdict['layer'] = dev.layer_name
    jm_append_merge(dev)
    dev.depth += 1


def jm_lineart_clip_stroke_path(dev, ctx, path, stroke, ctm, scissor):
    if not dev.clips:
        return
    dev.ctm = mupdf.FzMatrix(ctm)    # fz_concat(ctm, trace_device_ptm);
    dev.path_type = trace_device_CLIP_STROKE_PATH
    jm_lineart_path(dev, ctx, path)
    if dev.pathdict is None:
        return
    dev.pathdict['dictkey_type'] = 'clip'
    dev.pathdict['even_odd'] = None
    if 'closePath' not in dev.pathdict:
        #log(f'setting dev.pathdict["closePath"] to False')
        dev.pathdict['closePath'] = False
    dev.pathdict['scissor'] = JM_py_from_rect(compute_scissor(dev))
    dev.pathdict['level'] = dev.depth
    dev.pathdict['layer'] = dev.layer_name
    jm_append_merge(dev)
    dev.depth += 1


def jm_lineart_clip_stroke_text(dev, ctx, text, stroke, ctm, scissor):
    if not dev.clips:
        return
    compute_scissor(dev)
    dev.depth += 1


def jm_lineart_clip_text(dev, ctx, text, ctm, scissor):
    if not dev.clips:
        return
    compute_scissor(dev)
    dev.depth += 1


def jm_lineart_clip_image_mask( dev, ctx, image, ctm, scissor):
    if not dev.clips:
        return
    compute_scissor(dev)
    dev.depth += 1
 

def jm_lineart_pop_clip(dev, ctx):
    if not dev.clips or not dev.scissors:
        return
    len_ = len(dev.scissors)
    if len_ < 1:
        return
    del dev.scissors[-1]
    dev.depth -= 1


def jm_lineart_begin_layer(dev, ctx, name):
    if name:
        dev.layer_name = name
    else:
        dev.layer_name = ""


def jm_lineart_end_layer(dev, ctx):
    dev.layer_name = ""


def jm_lineart_begin_group(dev, ctx, bbox, cs, isolated, knockout, blendmode, alpha):
    #log(f'{dev.pathdict=} {dev.clips=}')
    if not dev.clips:
        return
    dev.pathdict = { # Py_BuildValue("{s:s,s:N,s:N,s:N,s:s,s:f,s:i,s:N}",
            "type": "group",
            "rect": JM_py_from_rect(bbox),
            "isolated": bool(isolated),
            "knockout": bool(knockout),
            "blendmode": mupdf.fz_blendmode_name(blendmode),
            "opacity": alpha,
            "level": dev.depth,
            "layer": dev.layer_name
            }
    jm_append_merge(dev)
    dev.depth += 1


def jm_lineart_end_group(dev, ctx):
    #log(f'{dev.pathdict=} {dev.clips=}')
    if not dev.clips:
        return
    dev.depth -= 1


def jm_lineart_stroke_text(dev, ctx, text, stroke, ctm, colorspace, color, alpha, color_params):
    jm_trace_text(dev, text, 1, ctm, colorspace, color, alpha, dev.seqno)
    dev.seqno += 1


def jm_dev_linewidth( dev, ctx, path, stroke, matrix, colorspace, color, alpha, color_params):
    dev.linewidth = stroke.linewidth
    jm_increase_seqno( dev, ctx)


def jm_increase_seqno( dev, ctx, *vargs):
    try:
        dev.seqno += 1
    except Exception:
        if g_exceptions_verbose:    exception_info()
        raise


def planish_line(p1: point_like, p2: point_like) -> Matrix:
    """Compute matrix which maps line from p1 to p2 to the x-axis, such that it
    maintains its length and p1 * matrix = Point(0, 0).

    Args:
        p1, p2: point_like
    Returns:
        Matrix which maps p1 to Point(0, 0) and p2 to a point on the x axis at
        the same distance to Point(0,0). Will always combine a rotation and a
        transformation.
    """
    p1 = Point(p1)
    p2 = Point(p2)
    return Matrix(util_hor_matrix(p1, p2))


class JM_image_reporter_Filter(mupdf.PdfFilterOptions2):
    def __init__(self):
        super().__init__()
        self.use_virtual_image_filter()

    def image_filter( self, ctx, ctm, name, image):
        assert isinstance(ctm, mupdf.fz_matrix)
        JM_image_filter(self, mupdf.FzMatrix(ctm), name, image)
        if mupdf_cppyy:
            # cppyy doesn't appear to treat returned None as nullptr,
            # resulting in obscure 'python exception' exception.
            return 0


class JM_new_bbox_device_Device(mupdf.FzDevice2):
    def __init__(self, result, layers):
        super().__init__()
        self.result = result
        self.layers = layers
        self.use_virtual_fill_path()
        self.use_virtual_stroke_path()
        self.use_virtual_fill_text()
        self.use_virtual_stroke_text()
        self.use_virtual_ignore_text()
        self.use_virtual_fill_shade()
        self.use_virtual_fill_image()
        self.use_virtual_fill_image_mask()
        
        self.use_virtual_begin_layer()
        self.use_virtual_end_layer()

    begin_layer = jm_lineart_begin_layer
    end_layer = jm_lineart_end_layer
    
    fill_path = jm_bbox_fill_path
    stroke_path = jm_bbox_stroke_path
    fill_text = jm_bbox_fill_text
    stroke_text = jm_bbox_stroke_text
    ignore_text = jm_bbox_ignore_text
    fill_shade = jm_bbox_fill_shade
    fill_image = jm_bbox_fill_image
    fill_image_mask = jm_bbox_fill_image_mask
    

class JM_new_output_fileptr_Output(mupdf.FzOutput2):
    def __init__(self, bio):
        super().__init__()
        self.bio = bio
        self.use_virtual_write()
        self.use_virtual_seek()
        self.use_virtual_tell()
        self.use_virtual_truncate()
    
    def seek( self, ctx, offset, whence):
        return self.bio.seek( offset, whence)
    
    def tell( self, ctx):
        ret = self.bio.tell()
        return ret
    
    def truncate( self, ctx):
        return self.bio.truncate()
    
    def write(self, ctx, data_raw, data_length):
        data = mupdf.raw_to_python_bytes(data_raw, data_length)
        return self.bio.write(data)


def compute_scissor(dev):
    '''
    Every scissor of a clip is a sub rectangle of the preceding clip scissor
    if the clip level is larger.
    '''
    if dev.scissors is None:
        dev.scissors = list()
    num_scissors = len(dev.scissors)
    if num_scissors > 0:
        last_scissor = dev.scissors[num_scissors-1]
        scissor = JM_rect_from_py(last_scissor)
        scissor = mupdf.fz_intersect_rect(scissor, dev.pathrect)
    else:
        scissor = dev.pathrect
    dev.scissors.append(JM_py_from_rect(scissor))
    return scissor


class JM_new_lineart_device_Device(mupdf.FzDevice2):
    '''
    LINEART device for Python method Page.get_cdrawings()
    '''
    #log(f'JM_new_lineart_device_Device()')
    def __init__(self, out, clips, method):
        #log(f'JM_new_lineart_device_Device.__init__()')
        super().__init__()
        # fixme: this results in "Unexpected call of unimplemented virtual_fnptrs fn FzDevice2::drop_device().".
        #self.use_virtual_drop_device()
        self.use_virtual_fill_path()
        self.use_virtual_stroke_path()
        self.use_virtual_clip_path()
        self.use_virtual_clip_image_mask()
        self.use_virtual_clip_stroke_path()
        self.use_virtual_clip_stroke_text()
        self.use_virtual_clip_text()
        
        self.use_virtual_fill_text
        self.use_virtual_stroke_text
        self.use_virtual_ignore_text
        
        self.use_virtual_fill_shade()
        self.use_virtual_fill_image()
        self.use_virtual_fill_image_mask()
        
        self.use_virtual_pop_clip()
        
        self.use_virtual_begin_group()
        self.use_virtual_end_group()
        
        self.use_virtual_begin_layer()
        self.use_virtual_end_layer()
        
        self.out = out
        self.seqno = 0
        self.depth = 0
        self.clips = clips
        self.method = method
        
        self.scissors = None
        self.layer_name = ""  # optional content name
        self.pathrect = None
        
        self.linewidth = 0
        self.ptm = mupdf.FzMatrix()
        self.ctm = mupdf.FzMatrix()
        self.rot = mupdf.FzMatrix()
        self.lastpoint = mupdf.FzPoint()
        self.firstpoint = mupdf.FzPoint()
        self.havemove = 0
        self.pathrect = mupdf.FzRect()
        self.pathfactor = 0
        self.linecount = 0
        self.path_type = 0
    
    #drop_device = jm_lineart_drop_device
    
    fill_path           = jm_lineart_fill_path
    stroke_path         = jm_lineart_stroke_path
    clip_image_mask     = jm_lineart_clip_image_mask
    clip_path           = jm_lineart_clip_path
    clip_stroke_path    = jm_lineart_clip_stroke_path
    clip_text           = jm_lineart_clip_text
    clip_stroke_text    = jm_lineart_clip_stroke_text
    
    fill_text           = jm_increase_seqno
    stroke_text         = jm_increase_seqno
    ignore_text         = jm_increase_seqno
    
    fill_shade          = jm_increase_seqno
    fill_image          = jm_increase_seqno
    fill_image_mask     = jm_increase_seqno
    
    pop_clip            = jm_lineart_pop_clip
    
    begin_group         = jm_lineart_begin_group
    end_group           = jm_lineart_end_group
    
    begin_layer         = jm_lineart_begin_layer
    end_layer           = jm_lineart_end_layer
    

class JM_new_texttrace_device(mupdf.FzDevice2):
    '''
    Trace TEXT device for Python method Page.get_texttrace()
    '''

    def __init__(self, out):
        super().__init__()
        self.use_virtual_fill_path()
        self.use_virtual_stroke_path()
        self.use_virtual_fill_text()
        self.use_virtual_stroke_text()
        self.use_virtual_ignore_text()
        self.use_virtual_fill_shade()
        self.use_virtual_fill_image()
        self.use_virtual_fill_image_mask()
        
        self.use_virtual_begin_layer()
        self.use_virtual_end_layer()
        
        self.out = out
        
        self.seqno = 0
        self.depth = 0
        self.clips = 0
        self.method = None
        
        self.seqno = 0

        self.pathdict = dict()
        self.scissors = list()
        self.linewidth = 0
        self.ptm = mupdf.FzMatrix()
        self.ctm = mupdf.FzMatrix()
        self.rot = mupdf.FzMatrix()
        self.lastpoint = mupdf.FzPoint()
        self.pathrect = mupdf.FzRect()
        self.pathfactor = 0
        self.linecount = 0
        self.path_type = 0
        self.layer_name = ""
    
    fill_path = jm_increase_seqno
    stroke_path = jm_dev_linewidth
    fill_text = jm_lineart_fill_text
    stroke_text = jm_lineart_stroke_text
    ignore_text = jm_lineart_ignore_text
    fill_shade = jm_increase_seqno
    fill_image = jm_increase_seqno
    fill_image_mask = jm_increase_seqno
    
    begin_layer = jm_lineart_begin_layer
    end_layer = jm_lineart_end_layer


def ConversionHeader(i: str, filename: OptStr ="unknown"):
    t = i.lower()
    import textwrap
    html = textwrap.dedent("""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
            body{background-color:gray}
            div{position:relative;background-color:white;margin:1em auto}
            p{position:absolute;margin:0}
            img{position:absolute}
            </style>
            </head>
            <body>
            """)

    xml = textwrap.dedent("""
            <?xml version="1.0"?>
            <document name="%s">
            """
            % filename
            )

    xhtml = textwrap.dedent("""
            <?xml version="1.0"?>
            <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
            <html xmlns="http://www.w3.org/1999/xhtml">
            <head>
            <style>
            body{background-color:gray}
            div{background-color:white;margin:1em;padding:1em}
            p{white-space:pre-wrap}
            </style>
            </head>
            <body>
            """)

    text = ""
    json = '{"document": "%s", "pages": [\n' % filename
    if t == "html":
        r = html
    elif t == "json":
        r = json
    elif t == "xml":
        r = xml
    elif t == "xhtml":
        r = xhtml
    else:
        r = text

    return r


def ConversionTrailer(i: str):
    t = i.lower()
    text = ""
    json = "]\n}"
    html = "</body>\n</html>\n"
    xml = "</document>\n"
    xhtml = html
    if t == "html":
        r = html
    elif t == "json":
        r = json
    elif t == "xml":
        r = xml
    elif t == "xhtml":
        r = xhtml
    else:
        r = text

    return r


def annot_preprocess(page: "Page") -> int:
    """Prepare for annotation insertion on the page.

    Returns:
        Old page rotation value. Temporarily sets rotation to 0 when required.
    """
    CheckParent(page)
    if not page.parent.is_pdf:
        raise ValueError("is no PDF")
    old_rotation = page.rotation
    if old_rotation != 0:
        page.set_rotation(0)
    return old_rotation


def annot_postprocess(page: "Page", annot: "Annot") -> None:
    """Clean up after annotation insertion.

    Set ownership flag and store annotation in page annotation dictionary.
    """
    #annot.parent = weakref.proxy(page)
    assert isinstance( page, Page)
    assert isinstance( annot, Annot)
    annot.parent = page
    page._annot_refs[id(annot)] = annot
    annot.thisown = True


def canon(c):
    assert isinstance(c, int)
    # TODO: proper unicode case folding
    # TODO: character equivalence (a matches ä, etc)
    if c == 0xA0 or c == 0x2028 or c == 0x2029:
        return ord(' ')
    if c == ord('\r') or c == ord('\n') or c == ord('\t'):
        return ord(' ')
    if c >= ord('A') and c <= ord('Z'):
        return c - ord('A') + ord('a')
    return c


def chartocanon(s):
    assert isinstance(s, str)
    n, c = mupdf.fz_chartorune(s)
    c = canon(c)
    return n, c


def dest_is_valid(o, page_count, page_object_nums, names_list):
    p = mupdf.pdf_dict_get( o, PDF_NAME('A'))
    if (
            mupdf.pdf_name_eq(
                mupdf.pdf_dict_get( p, PDF_NAME('S')),
                PDF_NAME('GoTo')
                )
            and not string_in_names_list(
                mupdf.pdf_dict_get( p, PDF_NAME('D')),
                names_list
                )
            ):
        return 0

    p = mupdf.pdf_dict_get( o, PDF_NAME('Dest'))
    if not p.m_internal:
        pass
    elif mupdf.pdf_is_string( p):
        return string_in_names_list( p, names_list)
    elif not dest_is_valid_page(
            mupdf.pdf_array_get( p, 0),
            page_object_nums,
            page_count,
            ):
        return 0
    return 1


def dest_is_valid_page(obj, page_object_nums, pagecount):
    num = mupdf.pdf_to_num(obj)

    if num == 0:
        return 0
    for i in range(pagecount):
        if page_object_nums[i] == num:
            return 1
    return 0


def find_string(s, needle):
    assert isinstance(s, str)
    for i in range(len(s)):
        end = match_string(s[i:], needle)
        if end is not None:
            end += i
            return i, end
    return None, None


def get_pdf_now() -> str:
    '''
    "Now" timestamp in PDF Format
    '''
    import time
    tz = "%s'%s'" % (
        str(abs(time.altzone // 3600)).rjust(2, "0"),
        str((abs(time.altzone // 60) % 60)).rjust(2, "0"),
    )
    tstamp = time.strftime("D:%Y%m%d%H%M%S", time.localtime())
    if time.altzone > 0:
        tstamp += "-" + tz
    elif time.altzone < 0:
        tstamp += "+" + tz
    else:
        pass
    return tstamp


class ElementPosition(object):
    """Convert a dictionary with element position information to an object."""

    def __init__(self):
        pass


def make_story_elpos():
    return ElementPosition()

 
def get_highlight_selection(page, start: point_like =None, stop: point_like =None, clip: rect_like =None) -> list:
    """Return rectangles of text lines between two points.

    Notes:
        The default of 'start' is top-left of 'clip'. The default of 'stop'
        is bottom-reight of 'clip'.

    Args:
        start: start point_like
        stop: end point_like, must be 'below' start
        clip: consider this rect_like only, default is page rectangle
    Returns:
        List of line bbox intersections with the area established by the
        parameters.
    """
    # validate and normalize arguments
    if clip is None:
        clip = page.rect
    clip = Rect(clip)
    if start is None:
        start = clip.tl
    if stop is None:
        stop = clip.br
    clip.y0 = start.y
    clip.y1 = stop.y
    if clip.is_empty or clip.is_infinite:
        return []

    # extract text of page, clip only, no images, expand ligatures
    blocks = page.get_text(
        "dict", flags=0, clip=clip,
    )["blocks"]

    lines = []  # will return this list of rectangles
    for b in blocks:
        bbox = Rect(b["bbox"])
        if bbox.is_infinite or bbox.is_empty:
            continue
        for line in b["lines"]:
            bbox = Rect(line["bbox"])
            if bbox.is_infinite or bbox.is_empty:
                continue
            lines.append(bbox)

    if lines == []:  # did not select anything
        return lines

    lines.sort(key=lambda bbox: bbox.y1)  # sort by vertical positions

    # cut off prefix from first line if start point is close to its top
    bboxf = lines.pop(0)
    if bboxf.y0 - start.y <= 0.1 * bboxf.height:  # close enough?
        r = Rect(start.x, bboxf.y0, bboxf.br)  # intersection rectangle
        if not (r.is_empty or r.is_infinite):
            lines.insert(0, r)  # insert again if not empty
    else:
        lines.insert(0, bboxf)  # insert again

    if lines == []:  # the list might have been emptied
        return lines

    # cut off suffix from last line if stop point is close to its bottom
    bboxl = lines.pop()
    if stop.y - bboxl.y1 <= 0.1 * bboxl.height:  # close enough?
        r = Rect(bboxl.tl, stop.x, bboxl.y1)  # intersection rectangle
        if not (r.is_empty or r.is_infinite):
            lines.append(r)  # append if not empty
    else:
        lines.append(bboxl)  # append again

    return lines


def glyph_name_to_unicode(name: str) -> int:
    """Convenience function accessing unicodedata."""
    import unicodedata
    try:
        unc = ord(unicodedata.lookup(name))
    except Exception:
        unc = 65533
    return unc


def hdist(dir, a, b):
    dx = b.x - a.x
    dy = b.y - a.y
    return mupdf.fz_abs(dx * dir.x + dy * dir.y)


def make_table(rect: rect_like =(0, 0, 1, 1), cols: int =1, rows: int =1) -> list:
    """Return a list of (rows x cols) equal sized rectangles.

    Notes:
        A utility to fill a given area with table cells of equal size.
    Args:
        rect: rect_like to use as the table area
        rows: number of rows
        cols: number of columns
    Returns:
        A list with <rows> items, where each item is a list of <cols>
        PyMuPDF Rect objects of equal sizes.
    """
    rect = Rect(rect)  # ensure this is a Rect
    if rect.is_empty or rect.is_infinite:
        raise ValueError("rect must be finite and not empty")
    tl = rect.tl

    height = rect.height / rows  # height of one table cell
    width = rect.width / cols  # width of one table cell
    delta_h = (width, 0, width, 0)  # diff to next right rect
    delta_v = (0, height, 0, height)  # diff to next lower rect

    r = Rect(tl, tl.x + width, tl.y + height)  # first rectangle

    # make the first row
    row = [r]
    for i in range(1, cols):
        r += delta_h  # build next rect to the right
        row.append(r)

    # make result, starts with first row
    rects = [row]
    for i in range(1, rows):
        row = rects[i - 1]  # take previously appended row
        nrow = []  # the new row to append
        for r in row:  # for each previous cell add its downward copy
            nrow.append(r + delta_v)
        rects.append(nrow)  # append new row to result

    return rects


def util_ensure_widget_calc(annot):
    '''
    Ensure that widgets with /AA/C JavaScript are in array AcroForm/CO
    '''
    annot_obj = mupdf.pdf_annot_obj(annot.this)
    pdf = mupdf.pdf_get_bound_document(annot_obj)
    PDFNAME_CO = mupdf.pdf_new_name("CO")    # = PDF_NAME(CO)
    acro = mupdf.pdf_dict_getl(  # get AcroForm dict
            mupdf.pdf_trailer(pdf),
            PDF_NAME('Root'),
            PDF_NAME('AcroForm'),
            )

    CO = mupdf.pdf_dict_get(acro, PDFNAME_CO)  # = AcroForm/CO
    if not mupdf.pdf_is_array(CO):
        CO = mupdf.pdf_dict_put_array(acro, PDFNAME_CO, 2)
    n = mupdf.pdf_array_len(CO)
    found = 0
    xref = mupdf.pdf_to_num(annot_obj)
    for i in range(n):
        nxref = mupdf.pdf_to_num(mupdf.pdf_array_get(CO, i))
        if xref == nxref:
            found = 1
            break
    if not found:
        mupdf.pdf_array_push(CO, mupdf.pdf_new_indirect(pdf, xref, 0))


def util_make_rect( *args, p0=None, p1=None, x0=None, y0=None, x1=None, y1=None):
    '''
    Helper for initialising rectangle classes.
    
    2022-09-02: This is quite different from PyMuPDF's util_make_rect(), which
    uses `goto` in ways that don't easily translate to Python.

    Returns (x0, y0, x1, y1) derived from <args>, then override with p0, p1,
    x0, y0, x1, y1 if they are not None.

    Accepts following forms for <args>:
        () returns all zeros.
        (top-left, bottom-right)
        (top-left, x1, y1)
        (x0, y0, bottom-right)
        (x0, y0, x1, y1)
        (rect)

    Where top-left and bottom-right are (x, y) or something with .x, .y
    members; rect is something with .x0, .y0, .x1, and .y1 members.

    2023-11-18: we now override with p0, p1, x0, y0, x1, y1 if not None.
    '''
    def get_xy( arg):
        if isinstance( arg, (list, tuple)) and len( arg) == 2:
            return arg[0], arg[1]
        if isinstance( arg, (Point, mupdf.FzPoint, mupdf.fz_point)):
            return arg.x, arg.y
        return None, None
    def make_tuple( a):
        if isinstance( a, tuple):
            return a
        if isinstance( a, Point):
            return a.x, a.y
        elif isinstance( a, (Rect, IRect, mupdf.FzRect, mupdf.fz_rect)):
            return a.x0, a.y0, a.x1, a.y1
        if not isinstance( a, (list, tuple)):
            a = a,
        return a
    def handle_args():
        if len(args) == 0:
            return 0, 0, 0, 0
        elif len(args) == 1:
            arg = args[0]
            if isinstance( arg, (list, tuple)) and len( arg) == 2:
                p1, p2 = arg
                return *p1, *p2
            if isinstance( arg, (list, tuple)) and len( arg) == 3:
                a, b, c = arg
                a = make_tuple(a)
                b = make_tuple(b)
                c = make_tuple(c)
                ret = *a, *b, *c
                return ret
            arg = make_tuple( arg)
            return arg
        elif len(args) == 2:
            return get_xy( args[0]) + get_xy( args[1])
        elif len(args) == 3:
            x0, y0 = get_xy( args[0])
            if (x0, y0) != (None, None):
                return x0, y0, args[1], args[2]
            x1, y1 = get_xy( args[2])
            if (x1, y1) != (None, None):
                return args[0], args[1], x1, y1
        elif len(args) == 4:
            return args[0], args[1], args[2], args[3]
        raise Exception( f'Unrecognised args: {args}')
    ret_x0, ret_y0, ret_x1, ret_y1 = handle_args()
    if p0 is not None:  ret_x0, ret_y0 = get_xy(p0)
    if p1 is not None:  ret_x1, ret_y1 = get_xy(p1)
    if x0 is not None:  ret_x0 = x0
    if y0 is not None:  ret_y0 = y0
    if x1 is not None:  ret_x1 = x1
    if y1 is not None:  ret_y1 = y1
    return ret_x0, ret_y0, ret_x1, ret_y1


def util_make_irect( *args, p0=None, p1=None, x0=None, y0=None, x1=None, y1=None):
    a, b, c, d = util_make_rect( *args, p0=p0, p1=p1, x0=x0, y0=y0, x1=x1, y1=y1)
    def convert(x, ceil):
        if ceil:
            return int(math.ceil(x))
        else:
            return int(math.floor(x))
    a = convert(a, False)
    b = convert(b, False)
    c = convert(c, True)
    d = convert(d, True)
    return a, b, c, d


def util_round_rect( rect):
    return JM_py_from_irect(mupdf.fz_round_rect(JM_rect_from_py(rect)))


def util_transform_rect( rect, matrix):
    if g_use_extra:
        return extra.util_transform_rect( rect, matrix)
    return JM_py_from_rect(mupdf.fz_transform_rect(JM_rect_from_py(rect), JM_matrix_from_py(matrix)))


def util_intersect_rect( r1, r2):
    return JM_py_from_rect(
            mupdf.fz_intersect_rect(
                JM_rect_from_py(r1),
                JM_rect_from_py(r2),
                )
            )


def util_is_point_in_rect( p, r):
    return mupdf.fz_is_point_inside_rect(
                JM_point_from_py(p),
                JM_rect_from_py(r),
                )

def util_include_point_in_rect( r, p):
    return JM_py_from_rect(
            mupdf.fz_include_point_in_rect(
                JM_rect_from_py(r),
                JM_point_from_py(p),
                )
            )


def util_point_in_quad( P, Q):
    p = JM_point_from_py(P)
    q = JM_quad_from_py(Q)
    return mupdf.fz_is_point_inside_quad(p, q)


def util_transform_point( point, matrix):
    return JM_py_from_point(
            mupdf.fz_transform_point(
                JM_point_from_py(point),
                JM_matrix_from_py(matrix),
                )
            )


def util_union_rect( r1, r2):
    return JM_py_from_rect(
            mupdf.fz_union_rect(
                JM_rect_from_py(r1),
                JM_rect_from_py(r2),
                )
            )


def util_concat_matrix( m1, m2):
    return JM_py_from_matrix(
            mupdf.fz_concat(
                JM_matrix_from_py(m1),
                JM_matrix_from_py(m2),
                )
            )


def util_invert_matrix(matrix):
    if 0:
        # Use MuPDF's fz_invert_matrix().
        if isinstance( matrix, (tuple, list)):
            matrix = mupdf.FzMatrix( *matrix)
        elif isinstance( matrix, mupdf.fz_matrix):
            matrix = mupdf.FzMatrix( matrix)
        elif isinstance( matrix, Matrix):
            matrix = mupdf.FzMatrix( matrix.a, matrix.b, matrix.c, matrix.d, matrix.e, matrix.f)
        assert isinstance( matrix, mupdf.FzMatrix), f'{type(matrix)=}: {matrix}'
        ret = mupdf.fz_invert_matrix( matrix)
        if ret == matrix and (0
                or abs( matrix.a - 1) >= sys.float_info.epsilon
                or abs( matrix.b - 0) >= sys.float_info.epsilon
                or abs( matrix.c - 0) >= sys.float_info.epsilon
                or abs( matrix.d - 1) >= sys.float_info.epsilon
                ):
            # Inversion not possible.
            return 1, ()
        return 0, (ret.a, ret.b, ret.c, ret.d, ret.e, ret.f)
    # Do inversion in python.
    src = JM_matrix_from_py(matrix)
    a = src.a
    det = a * src.d - src.b * src.c
    if det < -sys.float_info.epsilon or det > sys.float_info.epsilon:
        dst = mupdf.FzMatrix()
        rdet = 1 / det
        dst.a = src.d * rdet
        dst.b = -src.b * rdet
        dst.c = -src.c * rdet
        dst.d = a * rdet
        a = -src.e * dst.a - src.f * dst.c
        dst.f = -src.e * dst.b - src.f * dst.d
        dst.e = a
        return 0, (dst.a, dst.b, dst.c, dst.d, dst.e, dst.f)

    return 1, ()


def util_measure_string( text, fontname, fontsize, encoding):
    font = mupdf.fz_new_base14_font(fontname)
    w = 0
    pos = 0
    while pos < len(text):
        t, c = mupdf.fz_chartorune(text[pos:])
        pos += t
        if encoding == mupdf.PDF_SIMPLE_ENCODING_GREEK:
            c = mupdf.fz_iso8859_7_from_unicode(c)
        elif encoding == mupdf.PDF_SIMPLE_ENCODING_CYRILLIC:
            c = mupdf.fz_windows_1251_from_unicode(c)
        else:
            c = mupdf.fz_windows_1252_from_unicode(c)
        if c < 0:
            c = 0xB7
        g = mupdf.fz_encode_character(font, c)
        dw = mupdf.fz_advance_glyph(font, g, 0)
        w += dw
    ret = w * fontsize
    return ret


def util_sine_between(C, P, Q):
    # for points C, P, Q compute the sine between lines CP and QP
    c = JM_point_from_py(C)
    p = JM_point_from_py(P)
    q = JM_point_from_py(Q)
    s = mupdf.fz_normalize_vector(mupdf.fz_make_point(q.x - p.x, q.y - p.y))
    m1 = mupdf.fz_make_matrix(1, 0, 0, 1, -p.x, -p.y)
    m2 = mupdf.fz_make_matrix(s.x, -s.y, s.y, s.x, 0, 0)
    m1 = mupdf.fz_concat(m1, m2)
    c = mupdf.fz_transform_point(c, m1)
    c = mupdf.fz_normalize_vector(c)
    return c.y


def util_hor_matrix(C, P):
    '''
    Return the matrix that maps two points C, P to the x-axis such that
    C -> (0,0) and the image of P have the same distance.
    '''
    c = JM_point_from_py(C)
    p = JM_point_from_py(P)
    
    # compute (cosine, sine) of vector P-C with double precision:
    s = mupdf.fz_normalize_vector(mupdf.fz_make_point(p.x - c.x, p.y - c.y))
    
    m1 = mupdf.fz_make_matrix(1, 0, 0, 1, -c.x, -c.y)
    m2 = mupdf.fz_make_matrix(s.x, -s.y, s.y, s.x, 0, 0)
    return JM_py_from_matrix(mupdf.fz_concat(m1, m2))


def match_string(h0, n0):
    h = 0
    n = 0
    e = h
    delta_h, hc = chartocanon(h0[h:])
    h += delta_h
    delta_n, nc = chartocanon(n0[n:])
    n += delta_n
    while hc == nc:
        e = h
        if hc == ord(' '):
            while 1:
                delta_h, hc = chartocanon(h0[h:])
                h += delta_h
                if hc != ord(' '):
                    break
        else:
            delta_h, hc = chartocanon(h0[h:])
            h += delta_h
        if nc == ord(' '):
            while 1:
                delta_n, nc = chartocanon(n0[n:])
                n += delta_n
                if nc != ord(' '):
                    break
        else:
            delta_n, nc = chartocanon(n0[n:])
            n += delta_n
    return None if nc != 0 else e


def on_highlight_char(hits, line, ch):
    assert hits
    assert isinstance(line, mupdf.FzStextLine)
    assert isinstance(ch, mupdf.FzStextChar)
    vfuzz = ch.m_internal.size * hits.vfuzz
    hfuzz = ch.m_internal.size * hits.hfuzz
    ch_quad = JM_char_quad(line, ch)
    if hits.len > 0:
        # fixme: end = hits.quads[-1]
        quad = hits.quads[hits.len - 1]
        end = JM_quad_from_py(quad)
        if ( 1
                and hdist(line.m_internal.dir, end.lr, ch_quad.ll) < hfuzz
                and vdist(line.m_internal.dir, end.lr, ch_quad.ll) < vfuzz
                and hdist(line.m_internal.dir, end.ur, ch_quad.ul) < hfuzz
                and vdist(line.m_internal.dir, end.ur, ch_quad.ul) < vfuzz
                ):
            end.ur = ch_quad.ur
            end.lr = ch_quad.lr
            assert hits.quads[-1] == end
            return
    hits.quads.append(ch_quad)
    hits.len += 1


def page_merge(doc_des, doc_src, page_from, page_to, rotate, links, copy_annots, graft_map):
    '''
    Deep-copies a source page to the target.
    Modified version of function of pdfmerge.c: we also copy annotations, but
    we skip some subtypes. In addition we rotate output.
    '''
    if g_use_extra:
        #log( 'Calling C++ extra.page_merge()')
        return extra.page_merge( doc_des, doc_src, page_from, page_to, rotate, links, copy_annots, graft_map)
    
    # list of object types (per page) we want to copy
    known_page_objs = [
        PDF_NAME('Contents'),
        PDF_NAME('Resources'),
        PDF_NAME('MediaBox'),
        PDF_NAME('CropBox'),
        PDF_NAME('BleedBox'),
        PDF_NAME('TrimBox'),
        PDF_NAME('ArtBox'),
        PDF_NAME('Rotate'),
        PDF_NAME('UserUnit'),
        ]
    page_ref = mupdf.pdf_lookup_page_obj(doc_src, page_from)

    # make new page dict in dest doc
    page_dict = mupdf.pdf_new_dict(doc_des, 4)
    mupdf.pdf_dict_put(page_dict, PDF_NAME('Type'), PDF_NAME('Page'))

    # copy objects of source page into it
    for i in range( len(known_page_objs)):
        obj = mupdf.pdf_dict_get_inheritable( page_ref, known_page_objs[i])
        if obj.m_internal:
            #log( '{=type(graft_map) type(graft_map.this)}')
            mupdf.pdf_dict_put( page_dict, known_page_objs[i], mupdf.pdf_graft_mapped_object(graft_map.this, obj))

    # Copy annotations, but skip Link, Popup, IRT, Widget types
    # If selected, remove dict keys P (parent) and Popup
    if copy_annots:
        old_annots = mupdf.pdf_dict_get( page_ref, PDF_NAME('Annots'))
        n = mupdf.pdf_array_len( old_annots)
        if n > 0:
            new_annots = mupdf.pdf_dict_put_array( page_dict, PDF_NAME('Annots'), n)
            for i in range(n):
                o = mupdf.pdf_array_get( old_annots, i)
                if not o.m_internal or not mupdf.pdf_is_dict(o):
                    continue    # skip non-dict items
                if mupdf.pdf_dict_gets( o, "IRT").m_internal:
                    continue
                subtype = mupdf.pdf_dict_get( o, PDF_NAME('Subtype'))
                if mupdf.pdf_name_eq( subtype, PDF_NAME('Link')):
                    continue
                if mupdf.pdf_name_eq( subtype, PDF_NAME('Popup')):
                    continue
                if mupdf.pdf_name_eq( subtype, PDF_NAME('Widget')):
                    mupdf.fz_warn( "skipping widget annotation")
                    continue
                if mupdf.pdf_name_eq(subtype, PDF_NAME('Widget')):
                    continue
                mupdf.pdf_dict_del( o, PDF_NAME('Popup'))
                mupdf.pdf_dict_del( o, PDF_NAME('P'))
                copy_o = mupdf.pdf_graft_mapped_object( graft_map.this, o)
                annot = mupdf.pdf_new_indirect( doc_des, mupdf.pdf_to_num( copy_o), 0)
                mupdf.pdf_array_push( new_annots, annot)

    # rotate the page
    if rotate != -1:
        mupdf.pdf_dict_put_int( page_dict, PDF_NAME('Rotate'), rotate)
    # Now add the page dictionary to dest PDF
    ref = mupdf.pdf_add_object( doc_des, page_dict)

    # Insert new page at specified location
    mupdf.pdf_insert_page( doc_des, page_to, ref)


def paper_rect(s: str) -> Rect:
    """Return a Rect for the paper size indicated in string 's'. Must conform to the argument of method 'PaperSize', which will be invoked.
    """
    width, height = paper_size(s)
    return Rect(0.0, 0.0, width, height)


def paper_size(s: str) -> tuple:
    """Return a tuple (width, height) for a given paper format string.

    Notes:
        'A4-L' will return (842, 595), the values for A4 landscape.
        Suffix '-P' and no suffix return the portrait tuple.
    """
    size = s.lower()
    f = "p"
    if size.endswith("-l"):
        f = "l"
        size = size[:-2]
    if size.endswith("-p"):
        size = size[:-2]
    rc = paper_sizes().get(size, (-1, -1))
    if f == "p":
        return rc
    return (rc[1], rc[0])


def paper_sizes():
    """Known paper formats @ 72 dpi as a dictionary. Key is the format string
    like "a4" for ISO-A4. Value is the tuple (width, height).

    Information taken from the following web sites:
    www.din-formate.de
    www.din-formate.info/amerikanische-formate.html
    www.directtools.de/wissen/normen/iso.htm
    """
    return {
        "a0": (2384, 3370),
        "a1": (1684, 2384),
        "a10": (74, 105),
        "a2": (1191, 1684),
        "a3": (842, 1191),
        "a4": (595, 842),
        "a5": (420, 595),
        "a6": (298, 420),
        "a7": (210, 298),
        "a8": (147, 210),
        "a9": (105, 147),
        "b0": (2835, 4008),
        "b1": (2004, 2835),
        "b10": (88, 125),
        "b2": (1417, 2004),
        "b3": (1001, 1417),
        "b4": (709, 1001),
        "b5": (499, 709),
        "b6": (354, 499),
        "b7": (249, 354),
        "b8": (176, 249),
        "b9": (125, 176),
        "c0": (2599, 3677),
        "c1": (1837, 2599),
        "c10": (79, 113),
        "c2": (1298, 1837),
        "c3": (918, 1298),
        "c4": (649, 918),
        "c5": (459, 649),
        "c6": (323, 459),
        "c7": (230, 323),
        "c8": (162, 230),
        "c9": (113, 162),
        "card-4x6": (288, 432),
        "card-5x7": (360, 504),
        "commercial": (297, 684),
        "executive": (522, 756),
        "invoice": (396, 612),
        "ledger": (792, 1224),
        "legal": (612, 1008),
        "legal-13": (612, 936),
        "letter": (612, 792),
        "monarch": (279, 540),
        "tabloid-extra": (864, 1296),
        }

def pdf_lookup_page_loc(doc, needle):
    return mupdf.pdf_lookup_page_loc(doc, needle)


def pdfobj_string(o, prefix=''):
    '''
    Returns description of mupdf.PdfObj (wrapper for pdf_obj) <o>.
    '''
    assert 0, 'use mupdf.pdf_debug_obj() ?'
    ret = ''
    if mupdf.pdf_is_array(o):
        l = mupdf.pdf_array_len(o)
        ret += f'array {l}\n'
        for i in range(l):
            oo = mupdf.pdf_array_get(o, i)
            ret += pdfobj_string(oo, prefix + '    ')
            ret += '\n'
    elif mupdf.pdf_is_bool(o):
        ret += f'bool: {o.array_get_bool()}\n'
    elif mupdf.pdf_is_dict(o):
        l = mupdf.pdf_dict_len(o)
        ret += f'dict {l}\n'
        for i in range(l):
            key = mupdf.pdf_dict_get_key(o, i)
            value = mupdf.pdf_dict_get( o, key)
            ret += f'{prefix} {key}: '
            ret += pdfobj_string( value, prefix + '    ')
            ret += '\n'
    elif mupdf.pdf_is_embedded_file(o):
        ret += f'embedded_file: {o.embedded_file_name()}\n'
    elif mupdf.pdf_is_indirect(o):
        ret += f'indirect: ...\n'
    elif mupdf.pdf_is_int(o):
        ret += f'int: {mupdf.pdf_to_int(o)}\n'
    elif mupdf.pdf_is_jpx_image(o):
        ret += f'jpx_image:\n'
    elif mupdf.pdf_is_name(o):
        ret += f'name: {mupdf.pdf_to_name(o)}\n'
    elif o.pdf_is_null:
        ret += f'null\n'
    #elif o.pdf_is_number:
    #    ret += f'number\n'
    elif o.pdf_is_real:
        ret += f'real: {o.pdf_to_real()}\n'
    elif mupdf.pdf_is_stream(o):
        ret += f'stream\n'
    elif mupdf.pdf_is_string(o):
        ret += f'string: {mupdf.pdf_to_string(o)}\n'
    else:
        ret += '<>\n'

    return ret


def repair_mono_font(page: "Page", font: "Font") -> None:
    """Repair character spacing for mono fonts.

    Notes:
        Some mono-spaced fonts are displayed with a too large character
        distance, e.g. "a b c" instead of "abc". This utility adds an entry
        "/W[0 65535 w]" to the descendent font(s) of font. The float w is
        taken to be the width of 0x20 (space).
        This should enforce viewers to use 'w' as the character width.

    Args:
        page: pymupdf.Page object.
        font: pymupdf.Font object.
    """
    if not font.flags["mono"]:  # font not flagged as monospaced
        return None
    doc = page.parent  # the document
    fontlist = page.get_fonts()  # list of fonts on page
    xrefs = [  # list of objects referring to font
        f[0]
        for f in fontlist
        if (f[3] == font.name and f[4].startswith("F") and f[5].startswith("Identity"))
    ]
    if xrefs == []:  # our font does not occur
        return
    xrefs = set(xrefs)  # drop any double counts
    width = int(round((font.glyph_advance(32) * 1000)))
    for xref in xrefs:
        if not TOOLS.set_font_width(doc, xref, width):
            log("Cannot set width for '%s' in xref %i" % (font.name, xref))


def sRGB_to_pdf(srgb: int) -> tuple:
    """Convert sRGB color code to a PDF color triple.

    There is **no error checking** for performance reasons!

    Args:
        srgb: (int) RRGGBB (red, green, blue), each color in range(255).
    Returns:
        Tuple (red, green, blue) each item in interval 0 <= item <= 1.
    """
    t = sRGB_to_rgb(srgb)
    return t[0] / 255.0, t[1] / 255.0, t[2] / 255.0


def sRGB_to_rgb(srgb: int) -> tuple:
    """Convert sRGB color code to an RGB color triple.

    There is **no error checking** for performance reasons!

    Args:
        srgb: (int) SSRRGGBB (red, green, blue), each color in range(255).
        With MuPDF < 1.26, `s` is always 0.
    Returns:
        Tuple (red, green, blue) each item in interval 0 <= item <= 255.
    """
    srgb &= 0xffffff
    r = srgb >> 16
    g = (srgb - (r << 16)) >> 8
    b = srgb - (r << 16) - (g << 8)
    return (r, g, b)


def string_in_names_list(p, names_list):
    n = mupdf.pdf_array_len( names_list) if names_list else 0
    str_ = mupdf.pdf_to_text_string( p)
    for i in range(0, n, 2):
        if mupdf.pdf_to_text_string( mupdf.pdf_array_get( names_list, i)) == str_:
            return 1
    return 0


def strip_outline(doc, outlines, page_count, page_object_nums, names_list):
    '''
    Returns (count, first, prev).
    '''
    first = None
    count = 0
    current = outlines
    prev = None
    while current.m_internal:
        # Strip any children to start with. This takes care of
        # First / Last / Count for us.
        nc = strip_outlines(doc, current, page_count, page_object_nums, names_list)

        if not dest_is_valid(current, page_count, page_object_nums, names_list):
            if nc == 0:
                # Outline with invalid dest and no children. Drop it by
                # pulling the next one in here.
                next = mupdf.pdf_dict_get(current, PDF_NAME('Next'))
                if not next.m_internal:
                    # There is no next one to pull in
                    if prev.m_internal:
                        mupdf.pdf_dict_del(prev, PDF_NAME('Next'))
                elif prev.m_internal:
                    mupdf.pdf_dict_put(prev, PDF_NAME('Next'), next)
                    mupdf.pdf_dict_put(next, PDF_NAME('Prev'), prev)
                else:
                    mupdf.pdf_dict_del(next, PDF_NAME('Prev'))
                current = next
            else:
                # Outline with invalid dest, but children. Just drop the dest.
                mupdf.pdf_dict_del(current, PDF_NAME('Dest'))
                mupdf.pdf_dict_del(current, PDF_NAME('A'))
                current = mupdf.pdf_dict_get(current, PDF_NAME('Next'))
        else:
            # Keep this one
            if not first or not first.m_internal:
                first = current
            prev = current
            current = mupdf.pdf_dict_get(current, PDF_NAME('Next'))
            count += 1

    return count, first, prev


def strip_outlines(doc, outlines, page_count, page_object_nums, names_list):
    if not outlines.m_internal:
        return 0

    first = mupdf.pdf_dict_get(outlines, PDF_NAME('First'))
    if not first.m_internal:
        nc = 0
    else:
        nc, first, last = strip_outline(doc, first, page_count, page_object_nums, names_list)

    if nc == 0:
        mupdf.pdf_dict_del(outlines, PDF_NAME('First'))
        mupdf.pdf_dict_del(outlines, PDF_NAME('Last'))
        mupdf.pdf_dict_del(outlines, PDF_NAME('Count'))
    else:
        old_count = mupdf.pdf_to_int(mupdf.pdf_dict_get(outlines, PDF_NAME('Count')))
        mupdf.pdf_dict_put(outlines, PDF_NAME('First'), first)
        mupdf.pdf_dict_put(outlines, PDF_NAME('Last'), last)
        mupdf.pdf_dict_put(outlines, PDF_NAME('Count'), mupdf.pdf_new_int(nc if old_count > 0 else -nc))
    return nc


trace_device_FILL_PATH = 1
trace_device_STROKE_PATH = 2
trace_device_CLIP_PATH = 3
trace_device_CLIP_STROKE_PATH = 4


def unicode_to_glyph_name(ch: int) -> str:
    """
    Convenience function accessing unicodedata.
    """
    import unicodedata
    try:
        name = unicodedata.name(chr(ch))
    except ValueError:
        name = ".notdef"
    return name


def vdist(dir, a, b):
    dx = b.x - a.x
    dy = b.y - a.y
    return mupdf.fz_abs(dx * dir.y + dy * dir.x)


def apply_pages(
        path,
        pagefn,
        *,
        pagefn_args=(),
        pagefn_kwargs=dict(),
        initfn=None,
        initfn_args=(),
        initfn_kwargs=dict(),
        pages=None,
        method='single',
        concurrency=None,
        _stats=False,
        ):
    '''
    Returns list of results from `pagefn()`, optionally using concurrency for
    speed.
    
    Args:
        path:
            Path of document.
        pagefn:
            Function to call for each page; is passed (page, *pagefn_args,
            **pagefn_kwargs). Return value is added to list that we return. If
            `method` is not 'single', must be a top-level function - nested
            functions don't work with concurrency.
        pagefn_args
        pagefn_kwargs:
            Additional args to pass to `pagefn`. Must be picklable.
        initfn:
            If true, called once in each worker process; is passed
            (*initfn_args, **initfn_kwargs).
        initfn_args
        initfn_kwargs:
            Args to pass to initfn. Must be picklable.
        pages:
            List of page numbers to process, or None to include all pages.
        method:
            'single'
                Do not use concurrency.
            'mp'
                Operate concurrently using Python's `multiprocessing` module.
            'fork'
                 Operate concurrently using custom implementation with
                 `os.fork()`. Does not work on Windows.
        concurrency:
            Number of worker processes to use when operating concurrently. If
            None, we use the number of available CPUs.
        _stats:
            Internal, may change or be removed. If true, we output simple
            timing diagnostics.
    
    Note: We require a file path rather than a Document, because Document
    instances do not work properly after a fork - internal file descriptor
    offsets are shared between the parent and child processes.
    '''
    if _stats:
        t0 = time.time()
    
    if method == 'single':
        if initfn:
            initfn(*initfn_args, **initfn_kwargs)
        ret = list()
        document = Document(path)
        for page in document:
            r = pagefn(page, *pagefn_args, **initfn_kwargs)
            ret.append(r)
    
    else:
        # Use concurrency.
        #
        from . import _apply_pages
    
        if pages is None:
            if _stats:
                t = time.time()
            with Document(path) as document:
                num_pages = len(document)
                pages = list(range(num_pages))
            if _stats:
                t = time.time() - t
                log(f'{t:.2f}s: count pages.')
    
        if _stats:
            t = time.time()
        
        if method == 'mp':
            ret = _apply_pages._multiprocessing(
                    path,
                    pages,
                    pagefn,
                    pagefn_args,
                    pagefn_kwargs,
                    initfn,
                    initfn_args,
                    initfn_kwargs,
                    concurrency,
                    _stats,
                    )
    
        elif method == 'fork':
            ret = _apply_pages._fork(
                    path,
                    pages,
                    pagefn,
                    pagefn_args,
                    pagefn_kwargs,
                    initfn,
                    initfn_args,
                    initfn_kwargs,
                    concurrency,
                    _stats,
                    )
        
        else:
            assert 0, f'Unrecognised {method=}.'
        
        if _stats:
            t = time.time() - t
            log(f'{t:.2f}s: work.')

    if _stats:
        t = time.time() - t0
        log(f'{t:.2f}s: total.')
    return ret


def get_text(
        path,
        *,
        pages=None,
        method='single',
        concurrency=None,
        
        option='text',
        clip=None,
        flags=None,
        textpage=None,
        sort=False,
        delimiters=None,
        
        _stats=False,
        ):
    '''
    Returns list of results from `Page.get_text()`, optionally using
    concurrency for speed.
    
    Args:
        path:
            Path of document.
        pages:
            List of page numbers to process, or None to include all pages.
        method:
            'single'
                Do not use concurrency.
            'mp'
                Operate concurrently using Python's `multiprocessing` module.
            'fork'
                 Operate concurrently using custom implementation with
                 `os.fork`. Does not work on Windows.
        concurrency:
            Number of worker processes to use when operating concurrently. If
            None, we use the number of available CPUs.
        option
        clip
        flags
        textpage
        sort
        delimiters:
            Passed to internal calls to `Page.get_text()`.
    '''
    args_dict = dict(
            option=option,
            clip=clip,
            flags=flags,
            textpage=textpage,
            sort=sort,
            delimiters=delimiters,
            )
    
    return apply_pages(
            path,
            Page.get_text,
            pagefn_kwargs=args_dict,
            pages=pages,
            method=method,
            concurrency=concurrency,
            _stats=_stats,
            )


class TOOLS:
    '''
    We use @staticmethod to avoid the need to create an instance of this class.
    '''

    def _derotate_matrix(page):
        if isinstance(page, mupdf.PdfPage):
            return JM_py_from_matrix(JM_derotate_page_matrix(page))
        else:
            return JM_py_from_matrix(mupdf.FzMatrix())

    @staticmethod
    def _fill_widget(annot, widget):
        val = JM_get_widget_properties(annot, widget)

        widget.rect = Rect(annot.rect)
        widget.xref = annot.xref
        widget.parent = annot.parent
        widget._annot = annot  # backpointer to annot object
        if not widget.script:
            widget.script = None
        if not widget.script_stroke:
            widget.script_stroke = None
        if not widget.script_format:
            widget.script_format = None
        if not widget.script_change:
            widget.script_change = None
        if not widget.script_calc:
            widget.script_calc = None
        if not widget.script_blur:
            widget.script_blur = None
        if not widget.script_focus:
            widget.script_focus = None
        return val

    @staticmethod
    def _get_all_contents(page):
        page = _as_pdf_page(page.this)
        res = JM_read_contents(page.obj())
        result = JM_BinFromBuffer( res)
        return result

    @staticmethod
    def _insert_contents(page, newcont, overlay=1):
        """Add bytes as a new /Contents object for a page, and return its xref."""
        pdfpage = _as_pdf_page(page, required=1)
        contbuf = JM_BufferFromBytes(newcont)
        xref = JM_insert_contents(pdfpage.doc(), pdfpage.obj(), contbuf, overlay)
        #fixme: pdfpage->doc->dirty = 1;
        return xref

    @staticmethod
    def _le_annot_parms(annot, p1, p2, fill_color):
        """Get common parameters for making annot line end symbols.

        Returns:
            m: matrix that maps p1, p2 to points L, P on the x-axis
            im: its inverse
            L, P: transformed p1, p2
            w: line width
            scol: stroke color string
            fcol: fill color store_shrink
            opacity: opacity string (gs command)
        """
        w = annot.border["width"]  # line width
        sc = annot.colors["stroke"]  # stroke color
        if not sc:  # black if missing
            sc = (0,0,0)
        scol = " ".join(map(str, sc)) + " RG\n"
        if fill_color:
            fc = fill_color
        else:
            fc = annot.colors["fill"]  # fill color
        if not fc:
            fc = (1,1,1)  # white if missing
        fcol = " ".join(map(str, fc)) + " rg\n"
        # nr = annot.rect
        np1 = p1                   # point coord relative to annot rect
        np2 = p2                   # point coord relative to annot rect
        m = Matrix(util_hor_matrix(np1, np2))  # matrix makes the line horizontal
        im = ~m                            # inverted matrix
        L = np1 * m                        # converted start (left) point
        R = np2 * m                        # converted end (right) point
        if 0 <= annot.opacity < 1:
            opacity = "/H gs\n"
        else:
            opacity = ""
        return m, im, L, R, w, scol, fcol, opacity

    @staticmethod
    def _le_butt(annot, p1, p2, lr, fill_color):
        """Make stream commands for butt line end symbol. "lr" denotes left (False) or right point.
        """
        m, im, L, R, w, scol, fcol, opacity = TOOLS._le_annot_parms(annot, p1, p2, fill_color)
        shift = 3
        d = shift * max(1, w)
        M = R if lr else L
        top = (M + (0, -d/2.)) * im
        bot = (M + (0, d/2.)) * im
        ap = "\nq\n%s%f %f m\n" % (opacity, top.x, top.y)
        ap += "%f %f l\n" % (bot.x, bot.y)
        ap += _format_g(w) + " w\n"
        ap += scol + "s\nQ\n"
        return ap

    @staticmethod
    def _le_circle(annot, p1, p2, lr, fill_color):
        """Make stream commands for circle line end symbol. "lr" denotes left (False) or right point.
        """
        m, im, L, R, w, scol, fcol, opacity = TOOLS._le_annot_parms(annot, p1, p2, fill_color)
        shift = 2.5             # 2*shift*width = length of square edge
        d = shift * max(1, w)
        M = R - (d/2., 0) if lr else L + (d/2., 0)
        r = Rect(M, M) + (-d, -d, d, d)         # the square
        ap = "q\n" + opacity + TOOLS._oval_string(r.tl * im, r.tr * im, r.br * im, r.bl * im)
        ap += _format_g(w) + " w\n"
        ap += scol + fcol + "b\nQ\n"
        return ap

    @staticmethod
    def _le_closedarrow(annot, p1, p2, lr, fill_color):
        """Make stream commands for closed arrow line end symbol. "lr" denotes left (False) or right point.
        """
        m, im, L, R, w, scol, fcol, opacity = TOOLS._le_annot_parms(annot, p1, p2, fill_color)
        shift = 2.5
        d = shift * max(1, w)
        p2 = R + (d/2., 0) if lr else L - (d/2., 0)
        p1 = p2 + (-2*d, -d) if lr else p2 + (2*d, -d)
        p3 = p2 + (-2*d, d) if lr else p2 + (2*d, d)
        p1 *= im
        p2 *= im
        p3 *= im
        ap = "\nq\n%s%f %f m\n" % (opacity, p1.x, p1.y)
        ap += "%f %f l\n" % (p2.x, p2.y)
        ap += "%f %f l\n" % (p3.x, p3.y)
        ap += _format_g(w) + " w\n"
        ap += scol + fcol + "b\nQ\n"
        return ap

    @staticmethod
    def _le_diamond(annot, p1, p2, lr, fill_color):
        """Make stream commands for diamond line end symbol. "lr" denotes left (False) or right point.
        """
        m, im, L, R, w, scol, fcol, opacity = TOOLS._le_annot_parms(annot, p1, p2, fill_color)
        shift = 2.5             # 2*shift*width = length of square edge
        d = shift * max(1, w)
        M = R - (d/2., 0) if lr else L + (d/2., 0)
        r = Rect(M, M) + (-d, -d, d, d)         # the square
        # the square makes line longer by (2*shift - 1)*width
        p = (r.tl + (r.bl - r.tl) * 0.5) * im
        ap = "q\n%s%f %f m\n" % (opacity, p.x, p.y)
        p = (r.tl + (r.tr - r.tl) * 0.5) * im
        ap += "%f %f l\n"   % (p.x, p.y)
        p = (r.tr + (r.br - r.tr) * 0.5) * im
        ap += "%f %f l\n"   % (p.x, p.y)
        p = (r.br + (r.bl - r.br) * 0.5) * im
        ap += "%f %f l\n"   % (p.x, p.y)
        ap += _format_g(w) + " w\n"
        ap += scol + fcol + "b\nQ\n"
        return ap

    @staticmethod
    def _le_openarrow(annot, p1, p2, lr, fill_color):
        """Make stream commands for open arrow line end symbol. "lr" denotes left (False) or right point.
        """
        m, im, L, R, w, scol, fcol, opacity = TOOLS._le_annot_parms(annot, p1, p2, fill_color)
        shift = 2.5
        d = shift * max(1, w)
        p2 = R + (d/2., 0) if lr else L - (d/2., 0)
        p1 = p2 + (-2*d, -d) if lr else p2 + (2*d, -d)
        p3 = p2 + (-2*d, d) if lr else p2 + (2*d, d)
        p1 *= im
        p2 *= im
        p3 *= im
        ap = "\nq\n%s%f %f m\n" % (opacity, p1.x, p1.y)
        ap += "%f %f l\n" % (p2.x, p2.y)
        ap += "%f %f l\n" % (p3.x, p3.y)
        ap += _format_g(w) + " w\n"
        ap += scol + "S\nQ\n"
        return ap

    @staticmethod
    def _le_rclosedarrow(annot, p1, p2, lr, fill_color):
        """Make stream commands for right closed arrow line end symbol. "lr" denotes left (False) or right point.
        """
        m, im, L, R, w, scol, fcol, opacity = TOOLS._le_annot_parms(annot, p1, p2, fill_color)
        shift = 2.5
        d = shift * max(1, w)
        p2 = R - (2*d, 0) if lr else L + (2*d, 0)
        p1 = p2 + (2*d, -d) if lr else p2 + (-2*d, -d)
        p3 = p2 + (2*d, d) if lr else p2 + (-2*d, d)
        p1 *= im
        p2 *= im
        p3 *= im
        ap = "\nq\n%s%f %f m\n" % (opacity, p1.x, p1.y)
        ap += "%f %f l\n" % (p2.x, p2.y)
        ap += "%f %f l\n" % (p3.x, p3.y)
        ap += _format_g(w) + " w\n"
        ap += scol + fcol + "b\nQ\n"
        return ap

    @staticmethod
    def _le_ropenarrow(annot, p1, p2, lr, fill_color):
        """Make stream commands for right open arrow line end symbol. "lr" denotes left (False) or right point.
        """
        m, im, L, R, w, scol, fcol, opacity = TOOLS._le_annot_parms(annot, p1, p2, fill_color)
        shift = 2.5
        d = shift * max(1, w)
        p2 = R - (d/3., 0) if lr else L + (d/3., 0)
        p1 = p2 + (2*d, -d) if lr else p2 + (-2*d, -d)
        p3 = p2 + (2*d, d) if lr else p2 + (-2*d, d)
        p1 *= im
        p2 *= im
        p3 *= im
        ap = "\nq\n%s%f %f m\n" % (opacity, p1.x, p1.y)
        ap += "%f %f l\n" % (p2.x, p2.y)
        ap += "%f %f l\n" % (p3.x, p3.y)
        ap += _format_g(w) + " w\n"
        ap += scol + fcol + "S\nQ\n"
        return ap

    @staticmethod
    def _le_slash(annot, p1, p2, lr, fill_color):
        """Make stream commands for slash line end symbol. "lr" denotes left (False) or right point.
        """
        m, im, L, R, w, scol, fcol, opacity = TOOLS._le_annot_parms(annot, p1, p2, fill_color)
        rw = 1.1547 * max(1, w) * 1.0         # makes rect diagonal a 30 deg inclination
        M = R if lr else L
        r = Rect(M.x - rw, M.y - 2 * w, M.x + rw, M.y + 2 * w)
        top = r.tl * im
        bot = r.br * im
        ap = "\nq\n%s%f %f m\n" % (opacity, top.x, top.y)
        ap += "%f %f l\n" % (bot.x, bot.y)
        ap += _format_g(w) + " w\n"
        ap += scol + "s\nQ\n"
        return ap

    @staticmethod
    def _le_square(annot, p1, p2, lr, fill_color):
        """Make stream commands for square line end symbol. "lr" denotes left (False) or right point.
        """
        m, im, L, R, w, scol, fcol, opacity = TOOLS._le_annot_parms(annot, p1, p2, fill_color)
        shift = 2.5             # 2*shift*width = length of square edge
        d = shift * max(1, w)
        M = R - (d/2., 0) if lr else L + (d/2., 0)
        r = Rect(M, M) + (-d, -d, d, d)         # the square
        # the square makes line longer by (2*shift - 1)*width
        p = r.tl * im
        ap = "q\n%s%f %f m\n" % (opacity, p.x, p.y)
        p = r.tr * im
        ap += "%f %f l\n"   % (p.x, p.y)
        p = r.br * im
        ap += "%f %f l\n"   % (p.x, p.y)
        p = r.bl * im
        ap += "%f %f l\n"   % (p.x, p.y)
        ap += _format_g(w) + " w\n"
        ap += scol + fcol + "b\nQ\n"
        return ap

    @staticmethod
    def _oval_string(p1, p2, p3, p4):
        """Return /AP string defining an oval within a 4-polygon provided as points
        """
        def bezier(p, q, r):
            f = "%f %f %f %f %f %f c\n"
            return f % (p.x, p.y, q.x, q.y, r.x, r.y)

        kappa = 0.55228474983              # magic number
        ml = p1 + (p4 - p1) * 0.5          # middle points ...
        mo = p1 + (p2 - p1) * 0.5          # for each ...
        mr = p2 + (p3 - p2) * 0.5          # polygon ...
        mu = p4 + (p3 - p4) * 0.5          # side
        ol1 = ml + (p1 - ml) * kappa       # the 8 bezier
        ol2 = mo + (p1 - mo) * kappa       # helper points
        or1 = mo + (p2 - mo) * kappa
        or2 = mr + (p2 - mr) * kappa
        ur1 = mr + (p3 - mr) * kappa
        ur2 = mu + (p3 - mu) * kappa
        ul1 = mu + (p4 - mu) * kappa
        ul2 = ml + (p4 - ml) * kappa
        # now draw, starting from middle point of left side
        ap = "%f %f m\n" % (ml.x, ml.y)
        ap += bezier(ol1, ol2, mo)
        ap += bezier(or1, or2, mr)
        ap += bezier(ur1, ur2, mu)
        ap += bezier(ul1, ul2, ml)
        return ap

    @staticmethod
    def _parse_da(annot):

        if g_use_extra:
            val = extra.Tools_parse_da( annot.this)
        else:
            def Tools__parse_da(annot):
                this_annot = annot.this
                assert isinstance(this_annot, mupdf.PdfAnnot)
                this_annot_obj = mupdf.pdf_annot_obj( this_annot)
                pdf = mupdf.pdf_get_bound_document( this_annot_obj)
                try:
                    da = mupdf.pdf_dict_get_inheritable( this_annot_obj, PDF_NAME('DA'))
                    if not da.m_internal:
                        trailer = mupdf.pdf_trailer(pdf)
                        da = mupdf.pdf_dict_getl(trailer,
                                PDF_NAME('Root'),
                                PDF_NAME('AcroForm'),
                                PDF_NAME('DA'),
                                )
                    da_str = mupdf.pdf_to_text_string(da)
                except Exception:
                    if g_exceptions_verbose:    exception_info()
                    return
                return da_str
            val = Tools__parse_da(annot)

        if not val:
            return ((0,), "", 0)
        font = "Helv"
        fsize = 12
        col = (0, 0, 0)
        dat = val.split()  # split on any whitespace
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
            if item == "k":           # CMYK colored text
                col = [float(f) for f in dat[i - 4:i]]
                dat[i] = dat[i-1] = dat[i-2] = dat[i-3] = dat[i-4] = ""
                continue

        val = (col, font, fsize)
        return val

    @staticmethod
    def _reset_widget(annot):
        this_annot = annot
        this_annot_obj = mupdf.pdf_annot_obj(this_annot)
        pdf = mupdf.pdf_get_bound_document(this_annot_obj)
        mupdf.pdf_field_reset(pdf, this_annot_obj)

    @staticmethod
    def _rotate_matrix(page):
        pdfpage = page._pdf_page(required=False)
        if not pdfpage.m_internal:
            return JM_py_from_matrix(mupdf.FzMatrix())
        return JM_py_from_matrix(JM_rotate_page_matrix(pdfpage))

    @staticmethod
    def _save_widget(annot, widget):
        JM_set_widget_properties(annot, widget)

    def _update_da(annot, da_str):
        if g_use_extra:
            extra.Tools_update_da( annot.this, da_str)
        else:
            try:
                this_annot = annot.this
                assert isinstance(this_annot, mupdf.PdfAnnot)
                mupdf.pdf_dict_put_text_string(mupdf.pdf_annot_obj(this_annot), PDF_NAME('DA'), da_str)
                mupdf.pdf_dict_del(mupdf.pdf_annot_obj(this_annot), PDF_NAME('DS'))    # /* not supported */
                mupdf.pdf_dict_del(mupdf.pdf_annot_obj(this_annot), PDF_NAME('RC'))    # /* not supported */
            except Exception:
                if g_exceptions_verbose:    exception_info()
                return
            return
    
    @staticmethod
    def gen_id():
        global TOOLS_JM_UNIQUE_ID
        TOOLS_JM_UNIQUE_ID += 1
        return TOOLS_JM_UNIQUE_ID

    @staticmethod
    def glyph_cache_empty():
        '''
        Empty the glyph cache.
        '''
        mupdf.fz_purge_glyph_cache()

    @staticmethod
    def image_profile(stream, keep_image=0):
        '''
        Metadata of an image binary stream.
        '''
        return JM_image_profile(stream, keep_image)
    
    @staticmethod
    def mupdf_display_errors(on=None):
        '''
        Set MuPDF error display to True or False.
        '''
        global JM_mupdf_show_errors
        if on is not None:
            JM_mupdf_show_errors = bool(on)
        return JM_mupdf_show_errors

    @staticmethod
    def mupdf_display_warnings(on=None):
        '''
        Set MuPDF warnings display to True or False.
        '''
        global JM_mupdf_show_warnings
        if on is not None:
            JM_mupdf_show_warnings = bool(on)
        return JM_mupdf_show_warnings

    @staticmethod
    def mupdf_version():
        '''Get version of MuPDF binary build.'''
        return mupdf.FZ_VERSION

    @staticmethod
    def mupdf_warnings(reset=1):
        '''
        Get the MuPDF warnings/errors with optional reset (default).
        '''
        # Get any trailing `... repeated <N> times...` message.
        mupdf.fz_flush_warnings()
        ret = '\n'.join( JM_mupdf_warnings_store)
        if reset:
            TOOLS.reset_mupdf_warnings()
        return ret

    @staticmethod
    def reset_mupdf_warnings():
        global JM_mupdf_warnings_store
        JM_mupdf_warnings_store = list()
        
    @staticmethod
    def set_aa_level(level):
        '''
        Set anti-aliasing level.
        '''
        mupdf.fz_set_aa_level(level)
    
    @staticmethod
    def set_annot_stem( stem=None):
        global JM_annot_id_stem
        if stem is None:
            return JM_annot_id_stem
        len_ = len(stem) + 1
        if len_ > 50:
            len_ = 50
        JM_annot_id_stem = stem[:50]
        return JM_annot_id_stem

    @staticmethod
    def set_font_width(doc, xref, width):
        pdf = _as_pdf_document(doc, required=0)
        if not pdf.m_internal:
            return False
        font = mupdf.pdf_load_object(pdf, xref)
        dfonts = mupdf.pdf_dict_get(font, PDF_NAME('DescendantFonts'))
        if mupdf.pdf_is_array(dfonts):
            n = mupdf.pdf_array_len(dfonts)
            for i in range(n):
                dfont = mupdf.pdf_array_get(dfonts, i)
                warray = mupdf.pdf_new_array(pdf, 3)
                mupdf.pdf_array_push(warray, mupdf.pdf_new_int(0))
                mupdf.pdf_array_push(warray, mupdf.pdf_new_int(65535))
                mupdf.pdf_array_push(warray, mupdf.pdf_new_int(width))
                mupdf.pdf_dict_put(dfont, PDF_NAME('W'), warray)
        return True

    @staticmethod
    def set_graphics_min_line_width(min_line_width):
        '''
        Set the graphics minimum line width.
        '''
        mupdf.fz_set_graphics_min_line_width(min_line_width)

    @staticmethod
    def set_icc( on=0):
        """Set ICC color handling on or off."""
        if on:
            if mupdf.FZ_ENABLE_ICC:
                mupdf.fz_enable_icc()
            else:
                RAISEPY( "MuPDF built w/o ICC support",PyExc_ValueError)
        elif mupdf.FZ_ENABLE_ICC:
            mupdf.fz_disable_icc()
 
    @staticmethod
    def set_low_memory( on=None):
        """Set / unset MuPDF device caching."""
        if on is not None:
            _globals.no_device_caching = bool(on)
        return _globals.no_device_caching

    @staticmethod
    def set_small_glyph_heights(on=None):
        """Set / unset small glyph heights."""
        if on is not None:
            _globals.small_glyph_heights = bool(on)
            if g_use_extra:
                extra.set_small_glyph_heights(_globals.small_glyph_heights)
        return _globals.small_glyph_heights
    
    @staticmethod
    def set_subset_fontnames(on=None):
        '''
        Set / unset returning fontnames with their subset prefix.
        '''
        if on is not None:
            _globals.subset_fontnames = bool(on)
            if g_use_extra:
                extra.set_subset_fontnames(_globals.subset_fontnames)
        return _globals.subset_fontnames
    
    @staticmethod
    def show_aa_level():
        '''
        Show anti-aliasing values.
        '''
        return dict(
                graphics = mupdf.fz_graphics_aa_level(),
                text = mupdf.fz_text_aa_level(),
                graphics_min_line_width = mupdf.fz_graphics_min_line_width(),
                )

    @staticmethod
    def store_maxsize():
        '''
        MuPDF store size limit.
        '''
        # fixme: return gctx->store->max.
        return None

    @staticmethod
    def store_shrink(percent):
        '''
        Free 'percent' of current store size.
        '''
        if percent >= 100:
            mupdf.fz_empty_store()
            return 0
        if percent > 0:
            mupdf.fz_shrink_store( 100 - percent)
        # fixme: return gctx->store->size.
    
    @staticmethod
    def store_size():
        '''
        MuPDF current store size.
        '''
        # fixme: return gctx->store->size.
        return None
    
    @staticmethod
    def unset_quad_corrections(on=None):
        '''
        Set ascender / descender corrections on or off.
        '''
        if on is not None:
            _globals.skip_quad_corrections = bool(on)
            if g_use_extra:
                extra.set_skip_quad_corrections(_globals.skip_quad_corrections)
        return _globals.skip_quad_corrections

    # fixme: also defined at top-level.
    JM_annot_id_stem = 'fitz'

    fitz_config = JM_fitz_config()


# We cannot import utils earlier because it imports this .py file itself and
# uses some pymupdf.* types in function typing.
#
from . import utils


pdfcolor = dict(
        [
            (k, (r / 255, g / 255, b / 255))
            for k, (r, g, b) in utils.getColorInfoDict().items()
        ]
        )


# Callbacks not yet supported with cppyy.
if not mupdf_cppyy:
    mupdf.fz_set_warning_callback(JM_mupdf_warning)
    mupdf.fz_set_error_callback(JM_mupdf_error)


# If there are pending warnings when we exit, we end up in this sequence:
#
#   atexit()
#   -> mupdf::internal_thread_state::~internal_thread_state()
#   -> fz_drop_context()
#   -> fz_flush_warnings()
#   -> SWIG Director code
#   -> Python calling JM_mupdf_warning().
#
# Unfortunately this causes a SEGV, seemingly because the SWIG Director code has
# already been torn down.
#
# So we use a Python atexit handler to explicitly call fz_flush_warnings();
# this appears to happen early enough for the Director machinery to still
# work. So in the sequence above, fz_flush_warnings() will find that there are
# no pending warnings and will not attempt to call JM_mupdf_warning().
#
def _atexit():
    #log( 'PyMuPDF/src/__init__.py:_atexit() called')
    mupdf.fz_flush_warnings()
    mupdf.fz_set_warning_callback(None)
    mupdf.fz_set_error_callback(None)
    #log( '_atexit() returning')
atexit.register( _atexit)


# Use utils.*() fns for some class methods.
#
recover_bbox_quad           = utils.recover_bbox_quad
recover_char_quad           = utils.recover_char_quad
recover_line_quad           = utils.recover_line_quad
recover_quad                = utils.recover_quad
recover_span_quad           = utils.recover_span_quad

Annot.get_text              = utils.get_text
Annot.get_textbox           = utils.get_textbox

Document._do_links          = utils.do_links
Document.del_toc_item       = utils.del_toc_item
Document.get_char_widths    = utils.get_char_widths
Document.get_oc             = utils.get_oc
Document.get_ocmd           = utils.get_ocmd
Document.get_page_labels    = utils.get_page_labels
Document.get_page_numbers   = utils.get_page_numbers
Document.get_page_pixmap    = utils.get_page_pixmap
Document.get_page_text      = utils.get_page_text
Document.get_toc            = utils.get_toc
Document.has_annots         = utils.has_annots
Document.has_links          = utils.has_links
Document.insert_page        = utils.insert_page
Document.new_page           = utils.new_page
Document.scrub              = utils.scrub
Document.search_page_for    = utils.search_page_for
Document.set_metadata       = utils.set_metadata
Document.set_oc             = utils.set_oc
Document.set_ocmd           = utils.set_ocmd
Document.set_page_labels    = utils.set_page_labels
Document.set_toc            = utils.set_toc
Document.set_toc_item       = utils.set_toc_item
Document.subset_fonts       = utils.subset_fonts
Document.tobytes            = Document.write
Document.xref_copy          = utils.xref_copy

IRect.get_area              = utils.get_area

Page.apply_redactions       = utils.apply_redactions
Page.delete_image           = utils.delete_image
Page.delete_widget          = utils.delete_widget
Page.draw_bezier            = utils.draw_bezier
Page.draw_circle            = utils.draw_circle
Page.draw_curve             = utils.draw_curve
Page.draw_line              = utils.draw_line
Page.draw_oval              = utils.draw_oval
Page.draw_polyline          = utils.draw_polyline
Page.draw_quad              = utils.draw_quad
Page.draw_rect              = utils.draw_rect
Page.draw_sector            = utils.draw_sector
Page.draw_squiggle          = utils.draw_squiggle
Page.draw_zigzag            = utils.draw_zigzag
Page.get_image_info         = utils.get_image_info
Page.get_image_rects        = utils.get_image_rects
Page.get_label              = utils.get_label
Page.get_links              = utils.get_links
Page.get_pixmap             = utils.get_pixmap
Page.get_text               = utils.get_text
Page.get_text_blocks        = utils.get_text_blocks
Page.get_text_selection     = utils.get_text_selection
Page.get_text_words         = utils.get_text_words
Page.get_textbox            = utils.get_textbox
Page.get_textpage_ocr       = utils.get_textpage_ocr
Page.insert_image           = utils.insert_image
Page.insert_link            = utils.insert_link
Page.insert_text            = utils.insert_text
Page.insert_textbox         = utils.insert_textbox
Page.insert_htmlbox         = utils.insert_htmlbox
Page.new_shape              = lambda x: utils.Shape(x)
Page.replace_image          = utils.replace_image
Page.search_for             = utils.search_for
Page.show_pdf_page          = utils.show_pdf_page
Page.update_link            = utils.update_link
Page.write_text             = utils.write_text
from .table import find_tables

Page.find_tables = find_tables

Rect.get_area               = utils.get_area

TextWriter.fill_textbox     = utils.fill_textbox


class FitzDeprecation(DeprecationWarning):
    pass

def restore_aliases():
    warnings.filterwarnings( "once", category=FitzDeprecation)

    def showthis(msg, cat, filename, lineno, file=None, line=None):
        text = warnings.formatwarning(msg, cat, filename, lineno, line=line)
        s = text.find("FitzDeprecation")
        if s < 0:
            log(text)
            return
        text = text[s:].splitlines()[0][4:]
        log(text)

    warnings.showwarning = showthis

    def _alias(class_, new_name, legacy_name=None):
        '''
        Adds an alias for a class_ or module item clled <class_>.<new>.

        class_:
            Class/module to modify; use None for the current module.
        new_name:
            String name of existing item, e.g. name of method.
        legacy_name:
            Name of legacy object to create in <class_>. If None, we generate
            from <item> by removing underscores and capitalising the next
            letter.
        '''
        if class_ is None:
            class_ = sys.modules[__name__]
        if not legacy_name:
            legacy_name = ''
            capitalise_next = False
            for c in new_name:
                if c == '_':
                    capitalise_next = True
                elif capitalise_next:
                    legacy_name += c.upper()
                    capitalise_next = False
                else:
                    legacy_name += c
        new_object = getattr( class_, new_name)
        assert not getattr( class_, legacy_name, None), f'class {class_} already has {legacy_name}'
        if callable( new_object):
            def deprecated_function( *args, **kwargs):
                warnings.warn(
                        f'"{legacy_name=}" removed from {class_} after v1.19.0 - use "{new_name}".',
                        category=FitzDeprecation,
                        )
                return new_object( *args, **kwargs)
            setattr( class_, legacy_name, deprecated_function)
            deprecated_function.__doc__ = (
                    f'*** Deprecated and removed in version after v1.19.0 - use "{new_name}". ***\n'
                    f'{new_object.__doc__}'
                    )
        else:
            setattr( class_, legacy_name, new_object)

    _alias( Annot, 'get_file',              'fileGet')
    _alias( Annot, 'get_pixmap')
    _alias( Annot, 'get_sound',             'soundGet')
    _alias( Annot, 'get_text')
    _alias( Annot, 'get_textbox')
    _alias( Annot, 'get_textpage',          'getTextPage')
    _alias( Annot, 'line_ends')
    _alias( Annot, 'set_blendmode',         'setBlendMode')
    _alias( Annot, 'set_border')
    _alias( Annot, 'set_colors')
    _alias( Annot, 'set_flags')
    _alias( Annot, 'set_info')
    _alias( Annot, 'set_line_ends')
    _alias( Annot, 'set_name')
    _alias( Annot, 'set_oc', 'setOC')
    _alias( Annot, 'set_opacity')
    _alias( Annot, 'set_rect')
    _alias( Annot, 'update_file',           'fileUpd')
    _alias( DisplayList, 'get_pixmap')
    _alias( DisplayList, 'get_textpage',    'getTextPage')
    _alias( Document, 'chapter_count')
    _alias( Document, 'chapter_page_count')
    _alias( Document, 'convert_to_pdf',     'convertToPDF')
    _alias( Document, 'copy_page')
    _alias( Document, 'delete_page')
    _alias( Document, 'delete_pages',       'deletePageRange')
    _alias( Document, 'embfile_add',        'embeddedFileAdd')
    _alias( Document, 'embfile_count',      'embeddedFileCount')
    _alias( Document, 'embfile_del',        'embeddedFileDel')
    _alias( Document, 'embfile_get',        'embeddedFileGet')
    _alias( Document, 'embfile_info',       'embeddedFileInfo')
    _alias( Document, 'embfile_names',      'embeddedFileNames')
    _alias( Document, 'embfile_upd',        'embeddedFileUpd')
    _alias( Document, 'extract_font')
    _alias( Document, 'extract_image')
    _alias( Document, 'find_bookmark')
    _alias( Document, 'fullcopy_page')
    _alias( Document, 'get_char_widths')
    _alias( Document, 'get_ocgs',           'getOCGs')
    _alias( Document, 'get_page_fonts',     'getPageFontList')
    _alias( Document, 'get_page_images',    'getPageImageList')
    _alias( Document, 'get_page_pixmap')
    _alias( Document, 'get_page_text')
    _alias( Document, 'get_page_xobjects',  'getPageXObjectList')
    _alias( Document, 'get_sigflags',       'getSigFlags')
    _alias( Document, 'get_toc', 'getToC')
    _alias( Document, 'get_xml_metadata')
    _alias( Document, 'insert_page')
    _alias( Document, 'insert_pdf',         'insertPDF')
    _alias( Document, 'is_dirty')
    _alias( Document, 'is_form_pdf',        'isFormPDF')
    _alias( Document, 'is_pdf', 'isPDF')
    _alias( Document, 'is_reflowable')
    _alias( Document, 'is_repaired')
    _alias( Document, 'last_location')
    _alias( Document, 'load_page')
    _alias( Document, 'make_bookmark')
    _alias( Document, 'move_page')
    _alias( Document, 'needs_pass')
    _alias( Document, 'new_page')
    _alias( Document, 'next_location')
    _alias( Document, 'page_count')
    _alias( Document, 'page_cropbox',       'pageCropBox')
    _alias( Document, 'page_xref')
    _alias( Document, 'pdf_catalog',        'PDFCatalog')
    _alias( Document, 'pdf_trailer',        'PDFTrailer')
    _alias( Document, 'prev_location',      'previousLocation')
    _alias( Document, 'resolve_link')
    _alias( Document, 'search_page_for')
    _alias( Document, 'set_language')
    _alias( Document, 'set_metadata')
    _alias( Document, 'set_toc', 'setToC')
    _alias( Document, 'set_xml_metadata')
    _alias( Document, 'update_object')
    _alias( Document, 'update_stream')
    _alias( Document, 'xref_is_stream',     'isStream')
    _alias( Document, 'xref_length')
    _alias( Document, 'xref_object')
    _alias( Document, 'xref_stream')
    _alias( Document, 'xref_stream_raw')
    _alias( Document, 'xref_xml_metadata',  'metadataXML')
    _alias( IRect, 'get_area')
    _alias( IRect, 'get_area',              'getRectArea')
    _alias( IRect, 'include_point')
    _alias( IRect, 'include_rect')
    _alias( IRect, 'is_empty')
    _alias( IRect, 'is_infinite')
    _alias( Link, 'is_external')
    _alias( Link, 'set_border')
    _alias( Link, 'set_colors')
    _alias( Matrix, 'is_rectilinear')
    _alias( Matrix, 'prerotate',            'preRotate')
    _alias( Matrix, 'prescale',             'preScale')
    _alias( Matrix, 'preshear',             'preShear')
    _alias( Matrix, 'pretranslate',         'preTranslate')
    _alias( None, 'get_pdf_now',            'getPDFnow')
    _alias( None, 'get_pdf_str',            'getPDFstr')
    _alias( None, 'get_text_length')
    _alias( None, 'get_text_length',        'getTextlength')
    _alias( None, 'image_profile',          'ImageProperties')
    _alias( None, 'paper_rect',             'PaperRect')
    _alias( None, 'paper_size',             'PaperSize')
    _alias( None, 'paper_sizes')
    _alias( None, 'planish_line')
    _alias( Outline, 'is_external')
    _alias( Outline, 'is_open')
    _alias( Page, 'add_caret_annot')
    _alias( Page, 'add_circle_annot')
    _alias( Page, 'add_file_annot')
    _alias( Page, 'add_freetext_annot')
    _alias( Page, 'add_highlight_annot')
    _alias( Page, 'add_ink_annot')
    _alias( Page, 'add_line_annot')
    _alias( Page, 'add_polygon_annot')
    _alias( Page, 'add_polyline_annot')
    _alias( Page, 'add_rect_annot')
    _alias( Page, 'add_redact_annot')
    _alias( Page, 'add_squiggly_annot')
    _alias( Page, 'add_stamp_annot')
    _alias( Page, 'add_strikeout_annot')
    _alias( Page, 'add_text_annot')
    _alias( Page, 'add_underline_annot')
    _alias( Page, 'add_widget')
    _alias( Page, 'clean_contents')
    _alias( Page, 'cropbox',                'CropBox')
    _alias( Page, 'cropbox_position',       'CropBoxPosition')
    _alias( Page, 'delete_annot')
    _alias( Page, 'delete_link')
    _alias( Page, 'delete_widget')
    _alias( Page, 'derotation_matrix')
    _alias( Page, 'draw_bezier')
    _alias( Page, 'draw_circle')
    _alias( Page, 'draw_curve')
    _alias( Page, 'draw_line')
    _alias( Page, 'draw_oval')
    _alias( Page, 'draw_polyline')
    _alias( Page, 'draw_quad')
    _alias( Page, 'draw_rect')
    _alias( Page, 'draw_sector')
    _alias( Page, 'draw_squiggle')
    _alias( Page, 'draw_zigzag')
    _alias( Page, 'first_annot')
    _alias( Page, 'first_link')
    _alias( Page, 'first_widget')
    _alias( Page, 'get_contents')
    _alias( Page, 'get_displaylist',        'getDisplayList')
    _alias( Page, 'get_drawings')
    _alias( Page, 'get_fonts',              'getFontList')
    _alias( Page, 'get_image_bbox')
    _alias( Page, 'get_images',             'getImageList')
    _alias( Page, 'get_links')
    _alias( Page, 'get_pixmap')
    _alias( Page, 'get_svg_image',          'getSVGimage')
    _alias( Page, 'get_text')
    _alias( Page, 'get_text_blocks')
    _alias( Page, 'get_text_words')
    _alias( Page, 'get_textbox')
    _alias( Page, 'get_textpage',           'getTextPage')
    _alias( Page, 'insert_font')
    _alias( Page, 'insert_image')
    _alias( Page, 'insert_link')
    _alias( Page, 'insert_text')
    _alias( Page, 'insert_textbox')
    _alias( Page, 'is_wrapped',             '_isWrapped')
    _alias( Page, 'load_annot')
    _alias( Page, 'load_links')
    _alias( Page, 'mediabox',               'MediaBox')
    _alias( Page, 'mediabox_size',          'MediaBoxSize')
    _alias( Page, 'new_shape')
    _alias( Page, 'read_contents')
    _alias( Page, 'rotation_matrix')
    _alias( Page, 'search_for')
    _alias( Page, 'set_cropbox',            'setCropBox')
    _alias( Page, 'set_mediabox',           'setMediaBox')
    _alias( Page, 'set_rotation')
    _alias( Page, 'show_pdf_page',          'showPDFpage')
    _alias( Page, 'transformation_matrix')
    _alias( Page, 'update_link')
    _alias( Page, 'wrap_contents')
    _alias( Page, 'write_text')
    _alias( Pixmap, 'clear_with')
    _alias( Pixmap, 'copy',                 'copyPixmap')
    _alias( Pixmap, 'gamma_with')
    _alias( Pixmap, 'invert_irect',         'invertIRect')
    _alias( Pixmap, 'pil_save',             'pillowWrite')
    _alias( Pixmap, 'pil_tobytes',          'pillowData')
    _alias( Pixmap, 'save',                 'writeImage')
    _alias( Pixmap, 'save',                 'writePNG')
    _alias( Pixmap, 'set_alpha')
    _alias( Pixmap, 'set_dpi',              'setResolution')
    _alias( Pixmap, 'set_origin')
    _alias( Pixmap, 'set_pixel')
    _alias( Pixmap, 'set_rect')
    _alias( Pixmap, 'tint_with')
    _alias( Pixmap, 'tobytes',              'getImageData')
    _alias( Pixmap, 'tobytes',              'getPNGData')
    _alias( Pixmap, 'tobytes',              'getPNGdata')
    _alias( Quad, 'is_convex')
    _alias( Quad, 'is_empty')
    _alias( Quad, 'is_rectangular')
    _alias( Rect, 'get_area')
    _alias( Rect, 'get_area',               'getRectArea')
    _alias( Rect, 'include_point')
    _alias( Rect, 'include_rect')
    _alias( Rect, 'is_empty')
    _alias( Rect, 'is_infinite')
    _alias( TextWriter, 'fill_textbox')
    _alias( TextWriter, 'write_text')
    _alias( utils.Shape, 'draw_bezier')
    _alias( utils.Shape, 'draw_circle')
    _alias( utils.Shape, 'draw_curve')
    _alias( utils.Shape, 'draw_line')
    _alias( utils.Shape, 'draw_oval')
    _alias( utils.Shape, 'draw_polyline')
    _alias( utils.Shape, 'draw_quad')
    _alias( utils.Shape, 'draw_rect')
    _alias( utils.Shape, 'draw_sector')
    _alias( utils.Shape, 'draw_squiggle')
    _alias( utils.Shape, 'draw_zigzag')
    _alias( utils.Shape, 'insert_text')
    _alias( utils.Shape, 'insert_textbox')

if 0:
    restore_aliases()

__version__ = VersionBind
__doc__ = (
        f'PyMuPDF {VersionBind}: Python bindings for the MuPDF {VersionFitz} library (rebased implementation).\n'
        f'Python {sys.version_info[0]}.{sys.version_info[1]} running on {sys.platform} ({64 if sys.maxsize > 2**32 else 32}-bit).\n'
        )
