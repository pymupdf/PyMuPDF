from __future__ import print_function
"""
A demo showing all PDF form fields of a document.
"""
import sys
import fitz

def print_widget(w):
    if not w:
        return
    d = w.__dict__
    print("".ljust(80, "-"))
    for k in d.keys():
        if k.startswith("_"):
            continue
        print(k, "=", repr(d[k]))
    print("")

doc = fitz.open(sys.argv[1])
if not doc.isFormPDF:
    raise SystemExit("'%s' has no form fields." % doc.name)
print("".ljust(80, "-"))
print("Form field synopsis of file '%s'" % sys.argv[1])
print("".ljust(80, "-"))
for page in doc:
    a = page.firstAnnot
    header_shown = False

    while a:
        if not header_shown:
            print("\nShowing the form fields of page", page.number)
            header_shown = True
        print_widget(a.widget)
        a = a.next

"""
Above script produces the following type of output:

Showing the form fields of page 0
--------------------------------------------------------------------------------

border_color = None
border_style = Solid
border_width = 1.0
list_ismultiselect = 0
list_values = None
field_name = Textfeld-1
field_value =
field_flags = 0
fill_color = [1.0, 1.0, 0.0]
pb_caption = None
rect = fitz.Rect(50.0, 100.0, 250.0, 115.0)
text_color = None
text_font = None
text_fontsize = None
text_maxlen = 40
text_type = 0
text_da = 0 0 1 rg /Helvetica 11 Tf
field_type = 3
field_type_string = Text

"""
