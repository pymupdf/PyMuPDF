from __future__ import print_function
"""
A demo showing all PDF form fields of a document.
"""
import sys
print("Python", sys.version, "on", sys.platform)
import fitz
print(fitz.__doc__)
import time
t0 = time.clock() if str is bytes else time.process_time()

def flag_values(ff):
    Ff_text = [
    "ReadOnly", # 0
    "Required", # 1
    "NoExport", # 2
    "", # 3
    "", # 4
    "", # 5
    "", # 6
    "", # 7
    "", # 8
    "", # 9
    "", # 10
    "", # 11
    "Multiline", # 12
    "Password", # 13
    "NoToggleToOff", # 14
    "Radio", # 15
    "Pushbutton", # 16
    "Combo", # 17
    "Edit", # 18
    "Sort", # 19
    "FileSelect", # 20
    "MultiSelect", # 21
    "DoNotSpellCheck", # 22
    "DoNotScroll", # 23
    "Comb", # 24
    "RichText", # 25
    "CommitOnSelCHange", # 26
    "", # 27
    "", # 28
    "", # 29
    "", # 30
    "", # 31
    ]

    if ff <=0:
        return "(none)"
    rc = ""
    ffb = bin(ff)[2:]
    l = len(ffb)
    for i in range(l):
        if ffb[i] == "1":
            rc += Ff_text[l - i - 1] + " "
    return "(" + rc.strip().replace(" ", ", ") + ")"

def print_widget(w):
    if not w:
        return
    d = w.__dict__
    print("".ljust(80, "-"))
    for k in d.keys():
        if k.startswith("_"):
            continue
        if k != "field_flags":
            print(k, "=", repr(d[k]))
        else:
            print(k, "=", d[k], flag_values(d[k]))
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
doc.close()
t1 = time.clock() if str is bytes else time.process_time()
print("total CPU time %g" % (t1-t0))
"""
Above script produces the following type of output:

Form field synopsis of file 'widgettest.pdf'
--------------------------------------------------------------------------------

Showing the form fields of page 0
--------------------------------------------------------------------------------

border_color = None
border_style = 'Solid'
border_width = 1.0
border_dashes = None
choice_values = None
field_name = 'textfield-2'
field_value = 'this\ris\ra\rmulti-\rline\rtext.'
field_flags = 4096 (Multiline)
fill_color = [0.8999999761581421, 0.8999999761581421, 0.8999999761581421]
button_caption = None
rect = fitz.Rect(50.0, 235.0, 545.0, 792.0)
text_color = [0.0, 0.0, 1.0]
text_font = 'TiRo'
text_fontsize = 11.0
text_maxlen = 0
text_type = 0
field_type = 3
field_type_string = 'Text'

"""