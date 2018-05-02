import fitz
import sys
"""
Demo script
-----------
For a form PDF, print all fields per page (field type, name, text content).

Requires
---------
PyMuPDF v1.13.2+
"""
if not (list(map(int, fitz.VersionBind.split("."))) >= [1,13,2]):
    raise SystemExit("insufficient PyMuPDF version")
fn = sys.argv[1]
doc = fitz.open(fn)
if doc.isFormPDF:
    for page in doc:
        annot = page.firstAnnot
        if annot:
            print("\n\nDocument '%s', fields on page %i\n" % (doc.name, page.number))
            print("Type       Name                      Value")
            print("".ljust(80, "-"))
            while annot:
                print(str(annot.widget_type).ljust(10), annot.widget_name.ljust(25), annot.widget_text)
                annot = annot.next
else:
    print("Document '%s' has no form object." % doc.name)