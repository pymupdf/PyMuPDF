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
