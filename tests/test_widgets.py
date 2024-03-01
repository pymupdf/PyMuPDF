# -*- coding: utf-8 -*-
"""
Test PDF field (widget) insertion.
"""
import fitz
import os

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "widgettest.pdf")
file_2333 = os.path.join(scriptdir, "resources", "test-2333.pdf")


doc = fitz.open()
page = doc.new_page()
gold = (1, 1, 0)  # define some colors
blue = (0, 0, 1)
gray = (0.9, 0.9, 0.9)
fontsize = 11.0  # define a fontsize
lineheight = fontsize + 4.0
rect = fitz.Rect(50, 72, 400, 200)


def test_text():
    doc = fitz.open()
    page = doc.new_page()
    widget = fitz.Widget()  # create a widget object
    widget.border_color = blue  # border color
    widget.border_width = 0.3  # border width
    widget.border_style = "d"
    widget.border_dashes = (2, 3)
    widget.field_name = "Textfield-1"  # field name
    widget.field_label = "arbitrary text - e.g. to help filling the field"
    widget.field_type = fitz.PDF_WIDGET_TYPE_TEXT  # field type
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
    doc = fitz.open()
    page = doc.new_page()
    widget = fitz.Widget()
    widget.border_style = "b"
    widget.field_name = "Button-1"
    widget.field_label = "a simple check box button"
    widget.field_type = fitz.PDF_WIDGET_TYPE_CHECKBOX
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
    widget.field_flags |= fitz.PDF_FIELD_IS_READ_ONLY
    widget.update()
    path = f'{scriptdir}/test_checkbox.pdf'
    doc.save(path)
    
    doc = fitz.open(path)
    page = doc[0]
    widget = page.first_widget
    assert widget
    assert widget.field_flags == fitz.PDF_FIELD_IS_READ_ONLY


def test_listbox():
    doc = fitz.open()
    page = doc.new_page()
    widget = fitz.Widget()
    widget.field_name = "ListBox-1"
    widget.field_label = "is not a drop down: scroll with cursor in field"
    widget.field_type = fitz.PDF_WIDGET_TYPE_LISTBOX
    widget.field_flags = fitz.PDF_CH_FIELD_IS_COMMIT_ON_SEL_CHANGE
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
    doc = fitz.open()
    page = doc.new_page()
    widget = fitz.Widget()
    widget.field_name = "ComboBox-1"
    widget.field_label = "an editable combo box ..."
    widget.field_type = fitz.PDF_WIDGET_TYPE_COMBOBOX
    widget.field_flags = (
        fitz.PDF_CH_FIELD_IS_COMMIT_ON_SEL_CHANGE
        | fitz.PDF_CH_FIELD_IS_EDIT
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
    doc = fitz.open()
    doc.new_page()
    page = [p for p in doc.pages()][0]
    widget = fitz.Widget()
    widget.field_name = "textfield-2"
    widget.field_label = "multi-line text with tabs is also possible!"
    widget.field_flags = fitz.PDF_TX_FIELD_IS_MULTILINE
    widget.field_type = fitz.PDF_WIDGET_TYPE_TEXT
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
    doc = fitz.open(file_2333)
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
    w.field_value=False
    w.update()
    assert values() == set(("Off", "/Off"))

    
def test_2411():
    """Add combobox values in different formats."""
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(100, 100, 300, 200)

    widget = fitz.Widget()
    widget.field_flags = (
        fitz.PDF_CH_FIELD_IS_COMBO
        | fitz.PDF_CH_FIELD_IS_EDIT
        | fitz.PDF_CH_FIELD_IS_COMMIT_ON_SEL_CHANGE
    )
    widget.field_name = "ComboBox-1"
    widget.field_label = "an editable combo box ..."
    widget.field_type = fitz.PDF_WIDGET_TYPE_COMBOBOX
    widget.fill_color = fitz.pdfcolor["gold"]
    widget.rect = rect
    widget.choice_values = [
        ["Spain", "ES"],  # double value as list
        ("Italy", "I"),  # double value as tuple
        "Portugal",  # single value
    ]
    page.add_widget(widget)
    
def test_2391():
    """Confirm that multiple times setting a checkbox to ON/True/Yes will work."""
    doc = fitz.open(f'{scriptdir}/resources/widgettest.pdf')
    page = doc[0]
    # its work when we update first-time
    for field in page.widgets(types=[fitz.PDF_WIDGET_TYPE_CHECKBOX]):
        field.field_value = True
        field.update()

    for i in range(5):
        pdfdata = doc.tobytes()
        doc.close()
        doc = fitz.open("pdf", pdfdata)
        page = doc[0]
        for field in page.widgets(types=[fitz.PDF_WIDGET_TYPE_CHECKBOX]):
            assert field.field_value == field.on_state()
            field_field_value = field.on_state()
            field.update()

def test_3216():
    document = fitz.open(filename)
    for page in document:
        while 1:
            w = page.first_widget
            print(f'{w=}')
            if not w:
                break
            page.delete_widget(w)


def test_add_widget():
    doc = fitz.open()
    page = doc.new_page()
    w = fitz.Widget()
    w.field_type = fitz.PDF_WIDGET_TYPE_BUTTON
    w.rect = fitz.Rect(5, 5, 20, 20)
    w.field_flags = fitz.PDF_BTN_FIELD_IS_PUSHBUTTON
    w.field_name = "button"
    w.fill_color = (0, 0, 1)
    w.script = "app.alert('Hello, PDF!');"
    page.add_widget(w)
