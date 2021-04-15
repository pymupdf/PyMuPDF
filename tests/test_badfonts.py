"""
Ensure we can deal with non-Latin font names.
"""
import os

import fitz


def test_survive_names():
    scriptdir = os.path.abspath(os.path.dirname(__file__))
    filename = os.path.join(scriptdir, "resources", "has-bad-fonts.pdf")
    doc = fitz.open(filename)
    print("File '%s' uses the following fonts on page 0:" % doc.name)
    for f in doc.getPageFontList(0):
        print(f)
