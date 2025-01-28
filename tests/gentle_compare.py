import math

import pymupdf


def gentle_compare(w0, w1):
    """Check lists of "words" extractions for approximate equality.

    * both lists must have same length
    * word items must contain same word strings
    * word rectangles must be approximately equal
    """
    tolerance = 1e-3  # maximum (Euclidean) norm of difference rectangle
    word_count = len(w0)  # number of words
    if word_count != len(w1):
        print(f"different number of words: {word_count}/{len(w1)}")
        return False
    for i in range(word_count):
        if w0[i][4] != w1[i][4]:  # word strings must be the same
            print(f"word {i} mismatch")
            return False
        r0 = pymupdf.Rect(w0[i][:4])  # rect of first word
        r1 = pymupdf.Rect(w1[i][:4])  # rect of second word
        delta = (r1 - r0).norm()  # norm of difference rectangle
        if delta > tolerance:
            print(f"word {i}: rectangle mismatch {delta}")
            return False
    return True


def rms(a, b):
    '''
    Returns RMS diff of raw bytes of two sequences.
    '''
    assert len(a) == len(b)
    e = 0
    for aa, bb in zip(a, b):
        e += (aa - bb) ** 2
    rms = math.sqrt(e / len(a))
    return rms


def pixmaps_rms(a, b, out_prefix=''):
    '''
    Returns RMS diff of raw bytes of two pixmaps.

    We assert that the pixmaps/sequences are the same size.

    <a> and <b> can each be a pymupdf.Pixmap or path of a bitmap file.
    '''
    if isinstance(a, str):
        print(f'{out_prefix}pixmaps_rms(): reading pixmap from {a=}.')
        a = pymupdf.Pixmap(a)
    if isinstance(b, str):
        print(f'{out_prefix}pixmaps_rms(): reading pixmap from {b=}.')
        b = pymupdf.Pixmap(b)
    assert a.irect == b.irect, f'Differing rects: {a.irect=} {b.irect=}.'
    a_mv = a.samples_mv
    b_mv = b.samples_mv
    assert len(a_mv) == len(b_mv)
    e = 0
    for i, (a_byte, b_byte) in enumerate(zip(a_mv, b_mv)):
        if i % 100000 == 0:
            print(f'{out_prefix}compare_pixmaps(): {i=} {e=} {a_byte=} {b_byte=}.')
        e += (a_byte - b_byte) ** 2
    rms = math.sqrt(e / len(a_mv))
    print(f'{out_prefix}compare_pixmaps(): {e=} {rms=}.')
    return rms


def pixmaps_diff(a, b, out_prefix=''):
    '''
    Returns a pymupdf.Pixmap that represents the difference between pixmaps <a>
    and <b>.
    
    Each byte in the returned pixmap is `128 + (b_byte - a_byte) // 2`.
    '''
    if isinstance(a, str):
        print(f'{out_prefix}pixmaps_rms(): reading pixmap from {a=}.')
        a = pymupdf.Pixmap(a)
    if isinstance(b, str):
        print(f'{out_prefix}pixmaps_rms(): reading pixmap from {b=}.')
        b = pymupdf.Pixmap(b)
    assert a.irect == b.irect, f'Differing rects: {a.irect=} {b.irect=}.'
    a_mv = a.samples_mv
    b_mv = b.samples_mv
    c = pymupdf.Pixmap(a.tobytes())
    c_mv = c.samples_mv
    assert len(a_mv) == len(b_mv) == len(c_mv)
    if 1:
        print(f'{len(a_mv)=}')
        for i, (a_byte, b_byte, c_byte) in enumerate(zip(a_mv, b_mv, c_mv)):
            assert 0 <= a_byte < 256
            assert 0 <= b_byte < 256
            assert 0 <= c_byte < 256
            # Set byte to 128 plus half the diff so we represent the full
            # -255..+255 range.
            c_mv[i] = 128 + (b_byte - a_byte) // 2
    return c    
