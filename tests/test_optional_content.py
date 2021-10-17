"""
Test of Optional Content code.
"""
import os

import fitz

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "joined.pdf")


def test_oc1():
    """Arbitrary calls to OC code to get coverage."""
    doc = fitz.open()
    ocg1 = doc.add_ocg("ocg1")
    ocg2 = doc.add_ocg("ocg2")
    ocg3 = doc.add_ocg("ocg3")
    ocmd1 = doc.set_ocmd(xref=0, ocgs=(ocg1, ocg2))
    doc.set_layer(-1)
    doc.add_layer("layer1")
    test = doc.get_layer()
    test = doc.get_layers()
    test = doc.get_ocgs()
    test = doc.layer_ui_configs()
    doc.switch_layer(0)


def test_oc2():
    # source file with at least 4 pages
    src = fitz.open(filename)

    # new PDF with one page
    doc = fitz.open()
    page = doc.new_page()

    # define the 4 rectangle quadrants to receive the source pages
    r0 = page.rect / 2
    r1 = r0 + (r0.width, 0, r0.width, 0)
    r2 = r0 + (0, r0.height, 0, r0.height)
    r3 = r2 + (r2.width, 0, r2.width, 0)

    # make 4 OCGs - one for each source page image.
    # only first is ON initially
    ocg0 = doc.add_ocg("ocg0", on=True)
    ocg1 = doc.add_ocg("ocg1", on=False)
    ocg2 = doc.add_ocg("ocg2", on=False)
    ocg3 = doc.add_ocg("ocg3", on=False)

    ocmd0 = doc.set_ocmd(ve=["and", ocg0, ["not", ["or", ocg1, ocg2, ocg3]]])
    ocmd1 = doc.set_ocmd(ve=["and", ocg1, ["not", ["or", ocg0, ocg2, ocg3]]])
    ocmd2 = doc.set_ocmd(ve=["and", ocg2, ["not", ["or", ocg1, ocg0, ocg3]]])
    ocmd3 = doc.set_ocmd(ve=["and", ocg3, ["not", ["or", ocg1, ocg2, ocg0]]])
    ocmds = (ocmd0, ocmd1, ocmd2, ocmd3)
    # insert the 4 source page images, each connected to one OCG
    page.show_pdf_page(r0, src, 0, oc=ocmd0)
    page.show_pdf_page(r1, src, 1, oc=ocmd1)
    page.show_pdf_page(r2, src, 2, oc=ocmd2)
    page.show_pdf_page(r3, src, 3, oc=ocmd3)
    xobj_ocmds = [doc.get_oc(item[0]) for item in page.get_xobjects() if item[1] != 0]
    assert set(ocmds) <= set(xobj_ocmds)
    assert set((ocg0, ocg1, ocg2, ocg3)) == set(tuple(doc.get_ocgs().keys()))
    doc.get_ocmd(ocmd0)
    page.get_oc_items()
