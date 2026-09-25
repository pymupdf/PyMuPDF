"""
Check approx. equality of search quads versus quads recovered from
text extractions.
"""
import os

import pymupdf

import util


scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "quad-calc-0.pdf")


def test_quadcalc():
    text = " angle 327"  # search for this text
    doc = pymupdf.open(filename)
    page = doc[0]
    # This special page has one block with one line, and
    # its last span contains the searched text.
    block = page.get_text("dict", flags=0)["blocks"][0]
    line = block["lines"][0]
    # compute quad of last span in line
    lineq = pymupdf.recover_line_quad(line, spans=line["spans"][-1:])

    # let text search find the text returning quad coordinates
    rl = page.search_for(text, quads=True)
    searchq = rl[0]
    if util._use_4llm():
        # 4llm changes skip_quad_corrections.
        assert abs(searchq.ul - lineq.ul) <= 4
        assert abs(searchq.ur - lineq.ur) <= 4
        assert abs(searchq.ll - lineq.ll) <= 4
        assert abs(searchq.lr - lineq.lr) <= 4
    else:
        assert abs(searchq.ul - lineq.ul) <= 1e-4
        assert abs(searchq.ur - lineq.ur) <= 1e-4
        assert abs(searchq.ll - lineq.ll) <= 1e-4
        assert abs(searchq.lr - lineq.lr) <= 1e-4
