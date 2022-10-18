import fitz

table_text = (
    (
        "Length",
        "integer",
        """(Required) The number of bytes from the beginning of the line following the keyword stream to the last byte just before the keyword endstream. (There may be an additional EOL marker, preceding endstream, that is not included in the count and is not logically part of the stream data.) See “Stream Extent,” above, for further discussion.""",
    ),
    (
        "Filter",
        "name or array",
        """(Optional) The name of a filter to be applied in processing the stream data found between the keywords stream and endstream, or an array of such names. Multiple filters should be specified in the order in which they are to be applied.""",
    ),
    (
        "FFilter",
        "name or array",
        """(Optional; PDF 1.2) The name of a filter to be applied in processing the data found in the stream's external file, or an array of such names. The same rules apply as for Filter.""",
    ),
)

HTML = """
<html>
<body><h2>TABLE 3.4 Entries common to all stream dictionaries</h2>
<table style="width: 100%">
    <tr>
        <th class="w25">KEY
        <th class="w25">TYPE
        <th class="w50">VALUE
    </tr>
    <tr id="rowtemplate">
        <td id="col0" class="w25"></td>
        <td id="col1" class="w25"></td>
        <td id="col2" class="w50"></td>
    </tr>
"""
CSS = """
body {font-family: sans-serif;}
th {text-align: left;}
td {font-size: 8px;}
.w25 {width: 50px;}
.w50 {width: 300px;}
"""

story = fitz.Story(HTML, user_css=CSS)
body = story.body
template = body.find(None, "id", "rowtemplate")
parent = template.parent

for col0, col1, col2 in table_text:
    row = template.clone()
    row.find(None, "id", "col0").add_text("\n" + col0)
    row.find(None, "id", "col1").add_text("\n" + col1)
    row.find(None, "id", "col2").add_text("\n" + col2)
    parent.append_child(row)
template.remove()

writer = fitz.DocumentWriter(__file__.replace(".py", ".pdf"), "compress")
mediabox = fitz.paper_rect("letter")
where = mediabox + (36, 36, -36, -36)

more = 1
while more:
    dev = writer.begin_page(mediabox)
    more, filled = story.place(where)
    story.draw(dev, None)
    writer.end_page()
writer.close()
