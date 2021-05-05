"""
Problem: Since MuPDF v1.16 a 'Freetext' annotation font is restricted to the
"normal" versions (no bold, no italics) of Times-Roman, Helvetica, Courier.
It is impossible to use PyMuPDF to modify this.

Solution: Using Adobe's JavaScript API, it is possible to manipulate properties
of Freetext annotations. Check out these references:
https://www.adobe.com/content/dam/acom/en/devnet/acrobat/pdfs/js_api_reference.pdf,
or https://www.adobe.com/devnet/acrobat/documentation.html.

Function 'this.getAnnots()'  will return all annotations  as an array. We loop
over this array to set the properties of the text through the 'richContents'
attribute.
There is no explicit property to set text to bold, but it is possible to set
fontWeight=800 (400 is the normal size) of richContents.
Other attributes, like color, italics, etc. can also be set via richContents.

If we have 'FreeText' annotations created with PyMuPDF, we can make use of this
JavaScript feature to modify the font - thus circumventing the above restriction.

Use PyMuPDF v1.16.12 to create a push button that executes a Javascript
containing the desired code. This is what this program does.
Then open the resulting file with Adobe reader (!).
After clicking on the button, all Freetext annotations will be bold, and the
file can be saved.
If desired, the button can be removed again, using free tools like PyMuPDF or
PDF XChange editor.

Note / Caution:
---------------
The JavaScript will **only** work if the file is opened with Adobe Acrobat reader!
When using other PDF viewers, the reaction is unforeseeable.
"""
import sys

import fitz

# this JavaScript will execute when the button is clicked:
jscript = """
var annt = this.getAnnots();
annt.forEach(function (item, index) {
    try {
        var span = item.richContents;
        span.forEach(function (it, dx) {
            it.fontWeight = 800;
        })
        item.richContents = span;
    } catch (err) {}
});
app.alert('Done');
"""
i_fn = sys.argv[1]  # input file name
o_fn = "bold-" + i_fn  # output filename
doc = fitz.open(i_fn)  # open input
page = doc[0]  # get desired page

# ------------------------------------------------
# make a push button for invoking the JavaScript
# ------------------------------------------------

widget = fitz.Widget()  # create widget

# make it a 'PushButton'
widget.field_type = fitz.PDF_WIDGET_TYPE_BUTTON
widget.field_flags = fitz.PDF_BTN_FIELD_IS_PUSHBUTTON

widget.rect = fitz.Rect(5, 5, 20, 20)  # button position

widget.script = jscript  # fill in JavaScript source text
widget.field_name = "Make bold"  # arbitrary name
widget.field_value = "Off"  # arbitrary value
widget.fill_color = (0, 0, 1)  # make button visible

annot = page.add_widget(widget)  # add the widget to the page
doc.save(o_fn)  # output the file
