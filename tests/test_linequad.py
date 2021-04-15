"""
Check approx. equality of search quads versus recovered quads from
text extractions.
"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "quad-calc-0.pdf")


def test_quadcalc():
    text = " angle 327"
    doc = fitz.open(filename)
    page = doc[0]
    block = page.get_text("dict", flags=0)["blocks"][0]
    line = block["lines"][0]
    lineq = fitz.recover_line_quad(line, spans=line["spans"][-1:])
    rl = page.search_for(text, quads=True)
    searchq = rl[0]
    for i in range(4):
        assert abs(searchq.ul - lineq.ul) <= 1e-4
        assert abs(searchq.ur - lineq.ur) <= 1e-4
        assert abs(searchq.ll - lineq.ll) <= 1e-4
        assert abs(searchq.lr - lineq.lr) <= 1e-4
