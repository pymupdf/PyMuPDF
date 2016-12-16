#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
www.din-formate.de
www.din-formate.info/amerikanische-formate.html
www.directtools.de/wissen/normen/iso.htm
'''
def FindFit(w, h):
    PaperSizes = {                     # known paper formats @ 72 dpi
            'A0': [2384, 3370],
            'A1': [1684, 2384],
            'A2': [1191, 1684],
            'A3': [842, 1191],
            'A4': [595, 842],
            'A5': [420, 595],
            'A6': [298, 420],
            'A7': [210, 298],
            'A8': [147, 210],
            'A9': [105, 147],
            'A10': [74, 105],
            'B0': [2835, 4008],
            'B1': [2004, 2835],
            'B2': [1417, 2004],
            'B3': [1001, 1417],
            'B4': [709, 1001],
            'B5': [499, 709],
            'B6': [354, 499],
            'B7': [249, 354],
            'B8': [176, 249],
            'B9': [125, 176],
            'B10': [88, 125],
            'C0': [2599, 3677],
            'C1': [1837, 2599],
            'C2': [1298, 1837],
            'C3': [918, 1298],
            'C4': [649, 918],
            'C5': [459, 649],
            'C6': [323, 459],
            'C7': [230, 323],
            'C8': [162, 230],
            'C9': [113, 162],
            'C10': [79, 113],
            'Tabloid Extra': [864, 1296],
            'Legal-13': [612, 936],
            'Commercial': [297, 684],
            'Monarch': [279, 540],
            'Card-5x7': [360, 504],
            'Card-4x6': [288, 432],
            'Invoice': [396, 612],
            'Executive': [522, 756],
            'Letter': [612, 792],
            'Legal': [612, 1008],
            'Ledger': [792, 1224],
            }

    wi = int(round(w, 0))              # round parameters
    hi = int(round(h, 0))
    if w <= h:                         # create copy with width <= height
        w1 = wi
        h1 = hi
    else:
        w1 = hi
        h1 = wi

    sw = str(w1)                       # string versions
    sh = str(h1)
    
    # deviation of input from existing forms
    stab = [abs(w1-s[0])+abs(h1-s[1]) for s in PaperSizes.values()]
    small = min(stab)                  # minimum deviation
    idx = stab.index(small)            # its index
    f = list(PaperSizes.keys())[idx]   # name of found paper format

    if w <= h:                         # if input width <= height,
        ff = f + "-P"                  # it is a portait
        ss = str(PaperSizes[f][0]) + " x " + str(PaperSizes[f][1])
    else:
        ff = f + "-L"                  # else landscape
        ss = str(PaperSizes[f][1]) + " x " + str(PaperSizes[f][0])

    if small < 2:                      # exact fit - allow rounnding errors
        return ff                      # done
    rtxt = "%s x %s (other), closest: %s = %s"   # else show best fit
    rtxt = rtxt % (sw, sh, ff, ss)
    return rtxt