"""
Test of Optional Content code.
"""

import os

import pymupdf

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "joined.pdf")


def test_oc1():
    """Arbitrary calls to OC code to get coverage."""
    doc = pymupdf.open()
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
    src = pymupdf.open(filename)

    # new PDF with one page
    doc = pymupdf.open()
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


def test_3143():
    """Support for non-ascii layer names."""
    doc = pymupdf.open(os.path.join(scriptdir, "resources", "test-3143.pdf"))
    page = doc[0]
    set0 = set([l["text"] for l in doc.layer_ui_configs()])
    set1 = set([p["layer"] for p in page.get_drawings()])
    set2 = set([b[2] for b in page.get_bboxlog(layers=True)])
    assert set0 == set1 == set2


def test_3180():
    doc = pymupdf.open()
    page = doc.new_page()

    # Define the items for the combo box
    combo_items = ['first', 'second', 'third']

    # Create a combo box field
    combo_box = pymupdf.Widget()  # create a new widget
    combo_box.field_type = pymupdf.PDF_WIDGET_TYPE_COMBOBOX
    combo_box.field_name = "myComboBox"
    combo_box.field_value = combo_items[0]
    combo_box.choice_values = combo_items
    combo_box.rect = pymupdf.Rect(50, 50, 200, 75)  # position of the combo box
    combo_box.script_change = """
    var value = event.value;
    app.alert('You selected: ' + value);

    //var group_id = optional_content_group_ids[value];

    """

    # Insert the combo box into the page
    # https://pymupdf.readthedocs.io/en/latest/page.html#Page.add_widget
    page.add_widget(combo_box)

    # Create optional content groups
    # https://github.com/pymupdf/PyMuPDF-Utilities/blob/master/jupyter-notebooks/optional-content.ipynb


    # Load images and create OCGs for each
    optional_content_group_ids = {}
    for i, item in enumerate(combo_items):
        optional_content_group_id = doc.add_ocg(item, on=False)
        optional_content_group_ids[item] = optional_content_group_id
        rect = pymupdf.Rect(50, 100, 250, 300)
        image_file_name = f'{item}.png'
        # xref = page.insert_image(
        #    rect,
        #    filename=image_file_name,
        #    oc=optional_content_group_id,
        # )


    first_id = optional_content_group_ids['first']
    second_id = optional_content_group_ids['second']
    third_id = optional_content_group_ids['third']

    # https://pymupdf.readthedocs.io/en/latest/document.html#Document.set_layer


    doc.set_layer(-1, basestate="OFF")
    layers = doc.get_layer()
    doc.set_layer(config=-1, on=[first_id])

    # https://pymupdf.readthedocs.io/en/latest/document.html#Document.set_layer_ui_config
    # configs = doc.layer_ui_configs()
    # doc.set_layer_ui_config(0, pymupdf.PDF_OC_ON)
    # doc.set_layer_ui_config('third', action=2)

    # Save the PDF
    doc.save(os.path.abspath(f'{__file__}/../../tests/test_3180.pdf'))
    doc.close()
