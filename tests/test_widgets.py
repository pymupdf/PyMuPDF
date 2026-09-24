# -*- coding: utf-8 -*-
"""
Test PDF field (widget) insertion.
"""
import gc
import pymupdf
import os
from pymupdf import mupdf

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "widgettest.pdf")
file_2333 = os.path.join(scriptdir, "resources", "test-2333.pdf")
file_4055 = os.path.join(scriptdir, "resources", "test-4055.pdf")


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
    # Check #2350 - setting checkbox to readonly.
    #
    widget.field_flags |= pymupdf.PDF_FIELD_IS_READ_ONLY
    page.add_widget(widget)  # create the field
    field = page.first_widget
    assert field.field_type_string == "CheckBox"

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
        assert values() == set(("/Off", f"/{i}"))
    w.field_value = False
    w.update()
    assert values() == {"/Off"}


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
        assert CO.pdf_array_len() == i + 1

        # last item in the /CO array is that of the last widget's parent
        last_xref = CO.pdf_array_get(i).pdf_to_num()
        obj = pymupdf.mupdf.pdf_load_object(pdf, w.xref)
        parent_xref = obj.pdf_dict_get(pymupdf.PDF_NAME("Parent")).pdf_to_num()
        assert last_xref == parent_xref


def test_3950():
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3950.pdf')
    items = list()
    with pymupdf.open(path) as document:
        for page in document:
            for widget in page.widgets():
                items.append(widget.field_label)
                print(f'test_3950(): {widget.field_label=}.')
    assert items == [
            '{{ named_insured }}',
            '{{ policy_period_start_date }}',
            '{{ policy_period_end_date }}',
            '{{ insurance_line }}',
            ]


def test_4004():
    import collections
    
    def get_widgets_by_name(doc):
        """
        Extracts and returns a dictionary of widgets indexed by their names.
        """
        widgets_by_name = collections.defaultdict(list)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            for field in page.widgets():
                widgets_by_name[field.field_name].append({
                    "page_num": page_num,
                    "widget": field
                })
        return widgets_by_name

    # Open document and get widgets
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_4004.pdf')
    doc = pymupdf.open(path)
    widgets_by_name = get_widgets_by_name(doc)

    # Print widget information
    for name, widgets in widgets_by_name.items():
        print(f"Widget Name: {name}")
        for entry in widgets:
            widget = entry["widget"]
            page_num = entry["page_num"]
            print(f"  Page: {page_num + 1}, Type: {widget.field_type}, Value: {widget.field_value}, Rect: {widget.rect}")

    # Attempt to update field value
    w = widgets_by_name["Text1"][0]
    field = w['widget']
    field.value = "1234567890"
    try:
        field.update()
    except Exception as e:
        assert str(e) == 'Annot is not bound to a page'

    doc.close()


def test_4055():
    """Check correct setting of CheckBox "Yes" values.

    Test scope:
    * setting on with any of 'True' / 'Yes' / built-in values works
    * setting off with any of 'False' or 'Off' works
    """

    # this PDF has digits as "Yes" values.
    doc = pymupdf.open(file_4055)
    page = doc[0]

    # Round 1: confirm all check boxes are off
    for w in page.widgets(types=[2]):
        # check that this file doesn't use the "Yes" standard
        assert w.on_state() != "Yes"
        assert w.field_value == "Off"  # all check boxes are off
        w.field_value = w.on_state()
        w.update()

    page = doc.reload_page(page)  # reload page to make sure we start fresh

    # Round 2: confirm that fields contain the PDF's own on values
    for w in page.widgets(types=[2]):
        # confirm each value coincides with the "Yes" value
        assert w.field_value == w.on_state()
        w.field_value = False  # switch to "Off" using False
        w.update()

    page = doc.reload_page(page)

    # Round 3: confirm that 'False' achieved "Off" values
    for w in page.widgets(types=[2]):
        assert w.field_value == "Off"
        w.field_value = True  # use True for the next round
        w.update()

    page = doc.reload_page(page)

    # Round 4: confirm that setting to True also worked
    for w in page.widgets(types=[2]):
        assert w.field_value == w.on_state()
        w.field_value = "Off"  # set off again
        w.update()
        w.field_value = "Yes"
        w.update()

    page = doc.reload_page(page)

    # Round 5: final check: setting to "Yes" also does work
    for w in page.widgets(types=[2]):
        assert w.field_value == w.on_state()


def test_4965():
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_4965.pdf')
    with pymupdf.open(path) as document:
        for page in document:
            print(f'test_4965(): {page.number=}')
            # Iterate over all form fields (widgets) on the page
            for widget_i, field in enumerate(page.widgets()):
                # Access field properties
                name = field.field_name       # The internal name of the field
                value = field.field_value     # The data currently in the field
                f_type = field.field_type      # Integer representing the field type
                print(f'     {widget_i=}')
                print(f'        {name=}')
                print(f'        {value=}')
                print(f'        {f_type=}')


def test_4114():
    print()
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_4114.pdf')
    path_out = os.path.normpath(f'{__file__}/../../tests/test_4114_out.pdf')
    expected_values = [' - Select One - ', '  ', 'Cincinnati, OH 45999', 'Memphis, TN 37501', 'Ogden, UT 84201', 'Philadelphia, PA 19255']
    expected_values2 = [expected_values, expected_values]
    values = list()
    with pymupdf.open(path) as document:
        for page_i, page in enumerate(document):
            for widget in page.widgets():
                if widget.field_type_string == 'ComboBox':
                    print(f'test_4114(): {page_i=} {widget.choice_values=}')
                    values.append(widget.choice_values)
                widget.update()
        document.save(path_out)
    assert values == expected_values2


def test_4950():
    with pymupdf.open() as document:
        page = document.new_page()
        page.set_rotation(90)

        # Simulate an existing invisible signature field with a zero-dimension
        # rectangle. Creating such a widget through add_widget() is rejected by
        # validation, so create a valid widget first and then modify the PDF
        # object directly.
        widget = pymupdf.Widget()
        widget.field_name = "Signature"
        widget.field_type = pymupdf.PDF_WIDGET_TYPE_SIGNATURE
        widget.rect = pymupdf.Rect(0, 0, 10, 10)
        page.add_widget(widget)
        document.xref_set_key(page.first_widget.xref, "Rect", "[0 0 0 0]")
        page = document.reload_page(page)

        page.remove_rotation()
        assert page.rotation == 0


def test_hierarchy():
    # Create a new PDF document
    doc = pymupdf.open()
    pdfdoc = pymupdf._as_pdf_document(doc)

    def chain_upwards(w):
        """Check the names climbing up the hierarchy."""
        xref = w.xref
        parts = w.field_name.split(".")
        obj = mupdf.pdf_load_object(pdfdoc, xref)  # the widget object
        assert obj.pdf_dict_get(pymupdf.PDF_NAME("T")).pdf_is_null()
        items = list()
        while 1:
            obj = obj.pdf_dict_get(pymupdf.PDF_NAME("Parent"))
            if not obj or obj.pdf_is_null():
                break
            pdf_name = obj.pdf_dict_get(pymupdf.PDF_NAME("T")).pdf_to_string()
            items.insert(0, pdf_name[0])
        assert items == parts, f'\n{items=}\n{parts=}'
                
    # Add a page to the document
    page = doc.new_page()
    r = pymupdf.Rect(100, 100, 200, 120)
    w = pymupdf.Widget()
    w.field_name = "Person.Name.First"
    w.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    w.rect = r
    w.field_value = "John"
    w.border_width = 1
    page.add_widget(w)
    r += (0, 30, 0, 30)

    w = pymupdf.Widget()
    w.field_name = "Person.Name.Last"
    w.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    w.rect = r
    w.field_value = "Doe"
    w.border_width = 1
    page.add_widget(w)

    field_names = ["Person.Name.First", "Person.Name.Last"]
    root = mupdf.pdf_dict_get(mupdf.pdf_trailer(pdfdoc), pymupdf.PDF_NAME("Root"))
    acro = root.pdf_dict_get(pymupdf.PDF_NAME("AcroForm"))
    fields = acro.pdf_dict_get(pymupdf.PDF_NAME("Fields"))
    assert fields.pdf_array_len() == 1, "must have exactly 1 root field"
    for i, w in enumerate(page.widgets()):
        field_name = w.field_name  # the field name is a concatenation
        assert field_name == field_names[i]
        chain_upwards(w)  # confirm the hierarchy is correct


def test_5101():
    print()
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_5101.pdf')
    with pymupdf.open(path) as document:
        print(f'{len(document)=}')
        if pymupdf.mupdf_version_tuple >= (1, 28, 5):
            page = document[0]
            wt = pymupdf.TOOLS.mupdf_warnings()
            print(f'{wt=}')
            if pymupdf.mupdf_version_tuple >= (1, 28, 5):
                assert wt == 'cycle in parent chain\nfixed bad Parent in AcroForm tree\n... repeated 2 times...'
            else:
                assert wt == 'fixed bad Parent in AcroForm tree\n... repeated 2 times...'
            document2 = pymupdf.open()
            document2.insert_pdf(document, annots=False, widgets=False, links=True)
        else:
            try:
                page = document[0]
            except pymupdf.mupdf.FzErrorFormat as e:
                print(f'Received expected exception: {e}')
                assert 'cycle in resources' in str(e)
            else:
                assert 0, 'test_5101(): Expected exception from document[0].'
            
            document2 = pymupdf.open()
            try:
                document2.insert_pdf(document, annots=False, widgets=False, links=True)
            except pymupdf.mupdf.FzErrorFormat as e:
                print(f'Received expected exception: {e}')
                assert 'cycle in resources' in str(e)
            else:
                assert 0, 'test_5101(): Expected exception from document2.insert_pdf.'
            

def test_delete_all():
    """Confirm: Deleting all widgets converts to a Non-Form-PDF."""
    path = os.path.normpath(f"{__file__}/../../tests/resources/test_hierarchy.pdf")
    doc = pymupdf.open(path)
    assert doc.is_form_pdf
    widgets = 0
    for page in doc:
        w = page.first_widget
        while w:
            widgets += 1
            w = page.delete_widget(w)
    print(f"Deleted {widgets} widgets")
    assert not doc.is_form_pdf
    

def test_3478():
    print()
    print(f'test_3478(): {pymupdf.version=}')
    path = os.path.normpath(f'{__file__}/../../tests/resources/test_3478.pdf')
    path_out = os.path.normpath(f'{__file__}/../../tests/test_3478_out.pdf')
    path_out2 = os.path.normpath(f'{__file__}/../../tests/test_3478_out2.pdf')
    
    def get_acro_names(document):
        ret = list()
        obj = mupdf.pdf_dict_getl(
                mupdf.pdf_trailer(pymupdf._as_pdf_document(document)),
                pymupdf.PDF_NAME('Root'),
                pymupdf.PDF_NAME('AcroForm'),
                pymupdf.PDF_NAME('Fields'),
                )
        assert pymupdf.mupdf.pdf_is_array(obj)
        l = pymupdf.mupdf.pdf_array_len(obj)
        for i in range(l):
            field = pymupdf.mupdf.pdf_array_get(obj, i)
            assert pymupdf.mupdf.pdf_is_dict(field)
            T = mupdf.pdf_dict_getp(field, 'T').pdf_to_text_string()
            ret.append(T)
        return ret
    
    with pymupdf.open(path) as document:
        
        print(f'test_3478(): Root/AcroForm/Fields/[]/T:')
        acro_names = get_acro_names(document)
        for acro_name in acro_names:
            if acro_name.startswith('sig') or acro_name.startswith('init'):
                print(f'test_3478():     {acro_name}')
        
        print(f'test_3478(): Page widgets:')
        for page in document:
            # iterate the fields on this page.
            widget = page.first_widget
            while widget:
                name = widget.field_name
                # If it's a signature, remove it.
                if name.startswith('sig') or name.startswith('init'):
                    xref = widget.xref
                    print(f'test_3478():     Calling page.delete_widget() for {name=}.')
                    widget = page.delete_widget(widget)
                else:
                    widget = widget.next
        
        document.save(path_out2)
        document.ez_save(path_out)
    
    # 2026-09-10: page.delete_widget() introduces a cyclic dependency which
    # results in us leaving a fd open and a warning from conftest.py, so do a
    # collection here to keep output clean.
    gc.collect()
    
    
    # In the ez_save()'d document:
    #
    # * Check that deleted widget fields are not in page widgets.
    #   (This has always been ok.)
    # * Check that deleted widget fields are not in Root/AcroForm/Fields[]/T.
    #   (This appears to have been fixed in pymupdf-1.25.3.)
    #
    print(f'test_3478(): looking at ez_save document.')
    num_still_present = 0
    num_still_present_acro = 0
    
    with pymupdf.open(path_out) as document:
        
        print(f'test_3478(): Page widgets:')
        for page_i, page in enumerate(document):
            for (widget_i, widget) in enumerate(page.widgets()):
                name = widget.field_name
                if name.startswith('sig') or name.startswith('init'):
                    print(f'test_3478():     {page_i=} {widget_i=}: {name}')
                    num_still_present += 1
        print(f'test_3478(): {num_still_present=}')
        
        acro_names = get_acro_names(document)
        for acro_name in acro_names:
            if acro_name.startswith('sig') or acro_name.startswith('init'):
                print(f'test_3478():     {i}: {acro_name}')
                num_still_present_acro += 1
        print(f'test_3478(): {num_still_present_acro=}')
    
    assert num_still_present == 0, f'{num_still_present=}'
    assert num_still_present_acro == 0, f'{num_still_present_acro=}'
