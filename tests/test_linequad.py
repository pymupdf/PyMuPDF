"""
Check approx. equality of search quads versus quads recovered from
text extractions.
"""

import os

import pymupdf

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "quad-calc-0.pdf")


def test_quadcalc():
    old_settings = pymupdf.TOOLS.unset_quad_corrections()
    pymupdf.TOOLS.unset_quad_corrections(False)
    text = " angle 327"  # search for this text
    doc = pymupdf.open(filename)
    page = doc[0]
    # This special page has one block with one line, and
    # its last span contains the searched text.
    block = page.get_text("dict")["blocks"][0]
    line = block["lines"][0]
    # compute quad of last span in line
    lineq = pymupdf.recover_line_quad(line, spans=line["spans"][-1:])

    # let text search find the text returning quad coordinates
    rl = page.search_for(text, quads=True)
    searchq = rl[0]
    assert abs(searchq.ul - lineq.ul) <= 1e-4
    assert abs(searchq.ur - lineq.ur) <= 1e-4
    assert abs(searchq.ll - lineq.ll) <= 1e-4
    assert abs(searchq.lr - lineq.lr) <= 1e-4
    pymupdf.TOOLS.unset_quad_corrections(old_settings)
