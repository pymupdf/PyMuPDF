"""
A demo showing all PDF form fields of a document.
"""
import sys
import fitz
doc = fitz.open(sys.argv[1])
if not doc.isFormPDF:
    raise SystemExit("PDF has no form fields.")
for page in doc:
    a = page.firstAnnot
    header_shown = False

    while a:
        if a.type[0] != fitz.ANNOT_WIDGET:
            a = a.next
            continue
        if not header_shown:
            print("\nShowing the form fields of page", page.number)
            print("".ljust(80, "-"))
            header_shown = True
        print("\nField type '%s', name '%s', value '%s'" % (a.widget_type[1],
        a.widget_name, a.widget_value))
        if a.widget_type[0] in (4, 5):      # listbox / combobox
            print("... from possible values:", a.widget_choices, "\n")
        a = a.next

"""
Example output of above script:

Showing the form fields of page 0
--------------------------------------------------------------------------------

Field type 'Text', name 'Given Name Text Box', value 'Jorj X.'

Field type 'Text', name 'Family Name Text Box', value 'McKie'

Field type 'Text', name 'Address 1 Text Box', value 'House near the Beach'

Field type 'Text', name 'House nr Text Box', value '4711'

Field type 'Text', name 'Address 2 Text Box', value 'A Secret Place'

Field type 'Text', name 'Postcode Text Box', value '314159'

Field type 'Text', name 'City Text Box', value 'Valetta'

Field type 'ComboBox', name 'Country Combo Box', value 'Malta'
... from possible values: ['Austria', 'Belgium', 'Britain', 'Bulgaria', 'Croatia', 'Cyprus', 'Czech-Republic', 'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 'Malta', 'Netherlands', 'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain', 'Sweden']


Field type 'ComboBox', name 'Gender List Box', value 'Man'
... from possible values: ['Man', 'Woman']


Field type 'Text', name 'Height Formatted Field', value '180'

Field type 'CheckBox', name 'Driving License Check Box', value 'True'

Field type 'CheckBox', name 'Language 1 Check Box', value 'True'

Field type 'CheckBox', name 'Language 2 Check Box', value 'True'

Field type 'CheckBox', name 'Language 3 Check Box', value 'False'

Field type 'CheckBox', name 'Language 4 Check Box', value 'False'

Field type 'CheckBox', name 'Language 5 Check Box', value 'False'

Field type 'ComboBox', name 'Favourite Colour List Box', value 'Blue'
... from possible values: ['Black', 'Brown', 'Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Violet', 'Grey', 'White']
"""