import pymupdf

"""Use rich text for FreeText annotations"""

# define an overall styling
ds = """font-size: 11pt; font-family: sans-serif;"""

# some special characters
bullet = chr(0x2610) + chr(0x2611) + chr(0x2612)

# the annotation text with HTML and styling syntax
text = f"""<p style="text-align:justify;margin-top:-25px;">
PyMuPDF <span style="color: red;">འདི་ ཡིག་ཆ་བཀྲམ་སྤེལ་གྱི་དོན་ལུ་ པའི་ཐོན་ཐུམ་སྒྲིལ་དྲག་ཤོས་དང་མགྱོགས་ཤོས་ཅིག་ཨིན།</span>
<span style="color:blue;">Here is some <b>bold</b> and <i>italic</i> text, followed by <b><i>bold-italic</i></b>. Text-based check boxes: {bullet}.</span>
 </p>"""

# here are some colors
gold = (1, 1, 0)
green = (0, 1, 0)

# new/empty PDF
doc = pymupdf.open()

# make a page in ISO-A4 format
page = doc.new_page()

# text goes into this:
rect = pymupdf.Rect(100, 100, 350, 200)

# define some points for callout lines
p2 = rect.tr + (50, 30)
p3 = p2 + (0, 30)

# define the annotation
annot = page.add_freetext_annot(
    rect,
    text,
    fill_color=gold,  # fill color
    opacity=1,  # non-transparent
    rotate=0,  # no rotation
    border_width=1,  # border and callout line width
    dashes=None,  # no dashing
    richtext=True,  # this is rich text
    style=ds,  # my styling default
    callout=(p3, p2, rect.tr),  # define end, knee, start points
    line_end=pymupdf.PDF_ANNOT_LE_OPEN_ARROW,  # symbol shown at p3
    border_color=green,
)

doc.save(__file__.replace(".py", ".pdf"), pretty=True)
