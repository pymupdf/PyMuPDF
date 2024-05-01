# -*- coding: utf-8 -*-
"""
Test PDF field (widget) insertion.
"""
import pymupdf
import os

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "widgettest.pdf")
file_2333 = os.path.join(scriptdir, "resources", "test-2333.pdf")


doc = pymupdf.open()
page = doc.new_page()
gold = (1, 1, 0)  # define some colors
blue = (0, 0, 1)
gray = (0.9, 0.9, 0.9)
fontsize = 11.0  # define a fontsize
lineheight = fontsize + 4.0
rect = pymupdf.Rect(50, 72, 400, 200)


def test_text():
    doc = pymupdf.open()
    page = doc.new_page()
    widget = pymupdf.Widget()  # create a widget object
    widget.border_color = blue  # border color
    widget.border_width = 0.3  # border width
    widget.border_style = "d"
    widget.border_dashes = (2, 3)
    widget.field_name = "Textfield-1"  # field name
    widget.field_label = "arbitrary text - e.g. to help filling the field"
    widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT  # field type
    widget.fill_color = gold  # field background
    widget.rect = rect  # set field rectangle
    widget.text_color = blue  # rext color
    widget.text_font = "TiRo"  # use font Times-Roman
    widget.text_fontsize = fontsize  # set fontsize
    widget.text_maxlen = 50  # restrict number of characters
    widget.field_value = "Times-Roman"
    page.add_widget(widget)  # create the field
    field = page.first_widget
    assert field.field_type_string == "Text"


def test_checkbox():
    doc = pymupdf.open()
    page = doc.new_page()
    widget = pymupdf.Widget()
    widget.border_style = "b"
    widget.field_name = "Button-1"
    widget.field_label = "a simple check box button"
    widget.field_type = pymupdf.PDF_WIDGET_TYPE_CHECKBOX
    widget.fill_color = gold
    widget.rect = rect
    widget.text_color = blue
    widget.text_font = "ZaDb"
    widget.field_value = True
    page.add_widget(widget)  # create the field
    field = page.first_widget
    assert field.field_type_string == "CheckBox"

    # Check #2350 - setting checkbox to readonly.
    #
    widget.field_flags |= pymupdf.PDF_FIELD_IS_READ_ONLY
    widget.update()
    path = f"{scriptdir}/test_checkbox.pdf"
    doc.save(path)

    doc = pymupdf.open(path)
    page = doc[0]
    widget = page.first_widget
    assert widget
    assert widget.field_flags == pymupdf.PDF_FIELD_IS_READ_ONLY


def test_listbox():
    doc = pymupdf.open()
    page = doc.new_page()
    widget = pymupdf.Widget()
    widget.field_name = "ListBox-1"
    widget.field_label = "is not a drop down: scroll with cursor in field"
    widget.field_type = pymupdf.PDF_WIDGET_TYPE_LISTBOX
    widget.field_flags = pymupdf.PDF_CH_FIELD_IS_COMMIT_ON_SEL_CHANGE
    widget.fill_color = gold
    widget.choice_values = (
        "Frankfurt",
        "Hamburg",
        "Stuttgart",
        "Hannover",
        "Berlin",
        "München",
        "Köln",
        "Potsdam",
    )
    widget.rect = rect
    widget.text_color = blue
    widget.text_fontsize = fontsize
    widget.field_value = widget.choice_values[-1]
    print("About to add '%s'" % widget.field_name)
    page.add_widget(widget)  # create the field
    field = page.first_widget
    assert field.field_type_string == "ListBox"


def test_combobox():
    doc = pymupdf.open()
    page = doc.new_page()
    widget = pymupdf.Widget()
    widget.field_name = "ComboBox-1"
    widget.field_label = "an editable combo box ..."
    widget.field_type = pymupdf.PDF_WIDGET_TYPE_COMBOBOX
    widget.field_flags = (
        pymupdf.PDF_CH_FIELD_IS_COMMIT_ON_SEL_CHANGE | pymupdf.PDF_CH_FIELD_IS_EDIT
    )
    widget.fill_color = gold
    widget.choice_values = (
        "Spanien",
        "Frankreich",
        "Holland",
        "Dänemark",
        "Schweden",
        "Norwegen",
        "England",
        "Polen",
        "Russland",
        "Italien",
        "Portugal",
        "Griechenland",
    )
    widget.rect = rect
    widget.text_color = blue
    widget.text_fontsize = fontsize
    widget.field_value = widget.choice_values[-1]
    page.add_widget(widget)  # create the field
    field = page.first_widget
    assert field.field_type_string == "ComboBox"


def test_text2():
    doc = pymupdf.open()
    doc.new_page()
    page = [p for p in doc.pages()][0]
    widget = pymupdf.Widget()
    widget.field_name = "textfield-2"
    widget.field_label = "multi-line text with tabs is also possible!"
    widget.field_flags = pymupdf.PDF_TX_FIELD_IS_MULTILINE
    widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    widget.fill_color = gray
    widget.rect = rect
    widget.text_color = blue
    widget.text_font = "TiRo"
    widget.text_fontsize = fontsize
    widget.field_value = "This\n\tis\n\t\ta\n\t\t\tmulti-\n\t\tline\n\ttext."
    page.add_widget(widget)  # create the field
    widgets = [w for w in page.widgets()]
    field = widgets[0]
    assert field.field_type_string == "Text"


def test_2333():
    doc = pymupdf.open(file_2333)
    page = doc[0]

    def values():
        return set(
            (
                doc.xref_get_key(635, "AS")[1],
                doc.xref_get_key(636, "AS")[1],
                doc.xref_get_key(637, "AS")[1],
                doc.xref_get_key(638, "AS")[1],
                doc.xref_get_key(127, "V")[1],
            )
        )

    for i, xref in enumerate((635, 636, 637, 638)):
        w = page.load_widget(xref)
        w.field_value = True
        w.update()
        assert values() == set(("/Off", f"{i}", f"/{i}"))
    w.field_value = False
    w.update()
    assert values() == set(("Off", "/Off"))


def test_2411():
    """Add combobox values in different formats."""
    doc = pymupdf.open()
    page = doc.new_page()
    rect = pymupdf.Rect(100, 100, 300, 200)

    widget = pymupdf.Widget()
    widget.field_flags = (
        pymupdf.PDF_CH_FIELD_IS_COMBO
        | pymupdf.PDF_CH_FIELD_IS_EDIT
        | pymupdf.PDF_CH_FIELD_IS_COMMIT_ON_SEL_CHANGE
    )
    widget.field_name = "ComboBox-1"
    widget.field_label = "an editable combo box ..."
    widget.field_type = pymupdf.PDF_WIDGET_TYPE_COMBOBOX
    widget.fill_color = pymupdf.pdfcolor["gold"]
    widget.rect = rect
    widget.choice_values = [
        ["Spain", "ES"],  # double value as list
        ("Italy", "I"),  # double value as tuple
        "Portugal",  # single value
    ]
    page.add_widget(widget)


def test_2391():
    """Confirm that multiple times setting a checkbox to ON/True/Yes will work."""
    doc = pymupdf.open(f"{scriptdir}/resources/widgettest.pdf")
    page = doc[0]
    # its work when we update first-time
    for field in page.widgets(types=[pymupdf.PDF_WIDGET_TYPE_CHECKBOX]):
        field.field_value = True
        field.update()

    for i in range(5):
        pdfdata = doc.tobytes()
        doc.close()
        doc = pymupdf.open("pdf", pdfdata)
        page = doc[0]
        for field in page.widgets(types=[pymupdf.PDF_WIDGET_TYPE_CHECKBOX]):
            assert field.field_value == field.on_state()
            field_field_value = field.on_state()
            field.update()


def test_3216():
    document = pymupdf.open(filename)
    for page in document:
        while 1:
            w = page.first_widget
            print(f"{w=}")
            if not w:
                break
            page.delete_widget(w)


def test_add_widget():
    doc = pymupdf.open()
    page = doc.new_page()
    w = pymupdf.Widget()
    w.field_type = pymupdf.PDF_WIDGET_TYPE_BUTTON
    w.rect = pymupdf.Rect(5, 5, 20, 20)
    w.field_flags = pymupdf.PDF_BTN_FIELD_IS_PUSHBUTTON
    w.field_name = "button"
    w.fill_color = (0, 0, 1)
    w.script = "app.alert('Hello, PDF!');"
    page.add_widget(w)


def test_interfield_calculation():
    """Confirm correct working of interfield calculations.

    We are going to create three pages with a computed result field each.

    Tests the fix for https://github.com/pymupdf/PyMuPDF/issues/3402.
    """
    # Field bboxes (same on each page)
    r1 = pymupdf.Rect(100, 100, 300, 120)
    r2 = pymupdf.Rect(100, 130, 300, 150)
    r3 = pymupdf.Rect(100, 180, 300, 200)

    doc = pymupdf.open()
    pdf = pymupdf._as_pdf_document(doc)  # we need underlying PDF document

    # Make PDF name object for "CO" because it is not defined in MuPDF.
    CO_name = pymupdf.mupdf.pdf_new_name("CO")  # = PDF_NAME(CO)
    for i in range(3):
        page = doc.new_page()
        w = pymupdf.Widget()
        w.field_name = f"NUM1{page.number}"
        w.rect = r1
        w.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
        w.field_value = f"{i*100+1}"
        w.field_flags = 2
        page.add_widget(w)

        w = pymupdf.Widget()
        w.field_name = f"NUM2{page.number}"
        w.rect = r2
        w.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
        w.field_value = "200"
        w.field_flags = 2
        page.add_widget(w)

        w = pymupdf.Widget()
        w.field_name = f"RESULT{page.number}"
        w.rect = r3
        w.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
        w.field_value = "Result?"
        # Script that adds previous two fields.
        w.script_calc = f"""AFSimple_Calculate("SUM",
        new Array("NUM1{page.number}", "NUM2{page.number}"));"""
        page.add_widget(w)

        # Access the inter-field calculation array. It contains a reference to
        # all fields which have a JavaScript stored in their "script_calc"
        # property, i.e. an "AA/C" entry.
        # Every iteration adds another such field, so this array's length must
        # always equal the loop index.
        if i == 0:  # only need to execute this on first time through
            CO = pymupdf.mupdf.pdf_dict_getl(
                pymupdf.mupdf.pdf_trailer(pdf),
                pymupdf.PDF_NAME("Root"),
                pymupdf.PDF_NAME("AcroForm"),
                CO_name,
            )
        # we confirm CO is an array of foreseeable length
        assert pymupdf.mupdf.pdf_array_len(CO) == i + 1

        # the xref of the i-th item must equal that of the last widget
        assert (
            pymupdf.mupdf.pdf_to_num(pymupdf.mupdf.pdf_array_get(CO, i))
            == list(page.widgets())[-1].xref
        )
