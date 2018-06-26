# -*- coding: utf-8 -*-
"""
Demo script: Create a simple Form PDF
-----------------------------------------

Features:
---------
Create a new PDF and insert 5 PDF Form fields, so-called "widgets" on the
page.

Using a suitable PDF Viewer, these fields can be modified und the PDF
then saved.

Focus is to demonstrates what can be done - not creating a Form that
makes any particular sense.

Note that the output PDF is very small. On Windows, viewers like Adobe Reader,
Nitro PDF Reader and PDF-XChange display the fields correctly, while SumatraPDF
will only show them, after they have been filled by some capable viewer. The reason
for this is, that SumatraPDF is currently based on a backlevel MuPDF version,
which ignores widgets without an appearance stream (so-called /AP object).

Dependencies
--------------
PyMuPDF v1.13.11
"""
import fitz
doc = fitz.open()
page = doc.newPage()
gold = (1, 1, 0)                                 # define some colors
blue = (0, 0, 1)
gray = (0.9, 0.9, 0.9)
fontsize = 11                                    # define a fontsize
lineheight = fontsize + 4

#------------------------------------------------------------------------------
# Field 1: Simple Text
#------------------------------------------------------------------------------
r11 = fitz.Rect(50, 100, 200, 100 + lineheight)  # rect of field label
r12 = r11 + (r11.width+2, 0, 2 * r11.width+2, 0) # rect of field value
page.insertTextbox(r11, "simple Text field:", align = fitz.TEXT_ALIGN_RIGHT)

widget = fitz.Widget()                           # create a widget object
widget.border_color = blue                       # border color
widget.border_width = 0.3                        # border width
widget.border_style = "d"
widget.border_dashes = [2, 3]
widget.field_name = "textfield-1"                # field name
widget.field_type = fitz.ANNOT_WG_TEXT           # field type
widget.fill_color = gold                         # field background
widget.rect = r12                                # set field rectangle
widget.text_color = blue                         # rext color
widget.text_font = "tibo"                        # use font Times-Bold
widget.text_fontsize = fontsize                  # set fontsize
widget.text_maxlen = 40                          # restrict to 40 characters
widget.field_value = "Times-Roman-Bold, 40 char."
annot = page.addWidget(widget)                   # create the field

#------------------------------------------------------------------------------
# Field 2: CheckBox
#------------------------------------------------------------------------------
r21 = r11 + (0, 2 * lineheight, 0, 2 * lineheight)
r22 = r21 + (r21.width+2, 0, lineheight, 0)
page.insertTextbox(r21, "CheckBox:", align = fitz.TEXT_ALIGN_RIGHT)

widget = fitz.Widget()
widget.border_style = "b"
widget.field_name = "Button-1"
widget.field_type = fitz.ANNOT_WG_CHECKBOX
widget.fill_color = gold
widget.rect = r22
widget.text_color = blue
widget.text_font = "ZaDb"
widget.field_value = True
annot = page.addWidget(widget)

#------------------------------------------------------------------------------
# Field 3: ListBox
#------------------------------------------------------------------------------
r31 = r21 + (0, 2 * lineheight, 0, 2 * lineheight)
r32 = r31 + (r31.width+2, 0, r31.width+2, 0)
page.insertTextbox(r31, "ListBox:", align = fitz.TEXT_ALIGN_RIGHT)

widget = fitz.Widget()
widget.field_name = "ListBox-1"
widget.field_type = fitz.ANNOT_WG_LISTBOX
widget.fill_color = gold
widget.choice_values = ["Frankfurt", "Hamburg", "Stuttgart", "Hannover", "Berlin", "München", "Köln", "Potsdam"]
widget.choice_values.sort()                        # sort the choices 
widget.rect = r32
widget.text_color = blue
widget.text_fontsize = fontsize
widget.field_flags = fitz.WIDGET_Ff_CommitOnSelCHange
widget.field_value = widget.choice_values[-1]
annot = page.addWidget(widget)

#------------------------------------------------------------------------------
# Field 4: ComboBox
#------------------------------------------------------------------------------
r41 = r31 + (0, 2 * lineheight, 0, 2 * lineheight)
r42 = r41 + (r41.width+2, 0, r41.width+2, 0)
page.insertTextbox(r41, "ComboBox, editable:", align = fitz.TEXT_ALIGN_RIGHT)
widget = fitz.Widget()
widget.field_flags = fitz.WIDGET_Ff_Edit         # make field editable
widget.field_name = "ComboBox-1"
widget.field_type = fitz.ANNOT_WG_COMBOBOX
widget.fill_color = gold
widget.choice_values = ["Spanien", "Frankreich", "Holland", "Dänemark", "Schweden", "Norwegen", "England", "Polen", "Russland", "Italien", "Portugal", "Griechenland"]
widget.choice_values.sort()                      # sort the choices
widget.rect = r42
widget.text_color = blue
widget.text_fontsize = fontsize
widget.field_flags = fitz.WIDGET_Ff_CommitOnSelCHange
widget.field_value = widget.choice_values[-1]
annot = page.addWidget(widget)

#------------------------------------------------------------------------------
# Field 5: Large Text field, covering rest of page, allows multiple lines.
#------------------------------------------------------------------------------
r51 = r41 + (0, 2 * lineheight, 0, 2 * lineheight)
r52 = fitz.Rect(r51.bl, page.rect.width - 50, page.rect.height - 50)
page.insertTextbox(r51, "multiline Text field:")
widget = fitz.Widget()
widget.field_name = "textfield-2"
widget.field_flags = fitz.WIDGET_Ff_Multiline
widget.field_type = fitz.ANNOT_WG_TEXT
widget.fill_color = gray
widget.rect = r52
widget.text_color = blue
widget.text_font = "TiRo"
widget.text_fontsize = fontsize
widget.field_value = "this\nis\na\nmulti-\nline\ntext."
annot = page.addWidget(widget)

doc.save("widgettest.pdf", clean = True, garbage = 4)
