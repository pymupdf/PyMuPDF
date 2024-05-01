import pymupdf

import difflib
import json
import os
import pprint


def test_2634():
    if not hasattr(pymupdf, 'mupdf'):
        print('test_2634(): Not running on classic.')
        return
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_2634.pdf')
    with pymupdf.open(path) as pdf, pymupdf.open() as new:
        new.insert_pdf(pdf)
        new.set_toc(pdf.get_toc(simple=False))
        toc_pdf = pdf.get_toc(simple=False)
        toc_new = new.get_toc(simple=False)

        def clear_xref(toc):
            '''
            Clear toc items that naturally differ.
            '''
            for item in toc:
                d = item[3]
                if 'collapse' in d:
                    d['collapse'] = 'dummy'
                if 'xref' in d:
                    d['xref'] = 'dummy'

        clear_xref(toc_pdf)
        clear_xref(toc_new)

        print('toc_pdf')
        for item in toc_pdf: print(item)
        print()
        print('toc_new')
        for item in toc_new: print(item)

        toc_text_pdf = pprint.pformat(toc_pdf, indent=4).split('\n')
        toc_text_new = pprint.pformat(toc_new, indent=4).split('\n')

        diff = difflib.unified_diff(
                toc_text_pdf,
                toc_text_new,
                lineterm='',
                )
        print('\n'.join(diff))

        # Check 'to' points are identical apart from rounding errors.
        #
        assert len(toc_new) == len(toc_pdf)
        for a, b in zip(toc_pdf, toc_new):
            a_dict = a[3]
            b_dict = b[3]
            if 'to' in a_dict:
                assert 'to' in b_dict
                a_to = a_dict['to']
                b_to = b_dict['to']
                assert isinstance(a_to, pymupdf.Point)
                assert isinstance(b_to, pymupdf.Point)
                if a_to != b_to:
                    print(f'Points not identical: {a_to=} {b_to=}.')
                assert abs(a_to.x - b_to.x) < 0.01
                assert abs(a_to.y - b_to.y) < 0.01
