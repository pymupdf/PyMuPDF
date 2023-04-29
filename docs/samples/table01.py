"""
Demo script for basic HTML table support in Story objects

Outputs a table with three columns that fits on one Letter page.
The content of each row is filled via the Story's template mechanism.
Column widths and row heights are automatically computed by MuPDF.
Some styling via a CSS source is also demonstrated:

- The table header row has a gray background
- Each cell shows a border at its top
- The Story's body uses the sans-serif font family
- The text of one of the columns is set to blue

Dependencies
-------------
PyMuPDF v1.22.0 or later
"""
import fitz

table_text = (  # the content of each table row
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
    (
        "FDecodeParms",
        "dictionary or array",
        """(Optional; PDF 1.2) A parameter dictionary, or an array of such dictionaries, used by the filters specified by FFilter. The same rules apply as for DecodeParms.""",
    ),
    (
        "DecodeParms",
        "dictionary or array",
        """(Optional) A parameter dictionary or an array of such dictionaries, used by the filters specified by Filter. If there is only one filter and that filter has parameters, DecodeParms must be set to the filter's parameter dictionary unless all the filter's parameters have their default values, in which case the DecodeParms entry may be omitted. If there are multiple filters and any of the filters has parameters set to nondefault values, DecodeParms must be an array with one entry for each filter: either the parameter dictionary for that filter, or the null object if that filter has no parameters (or if all of its parameters have their default values). If none of the filters have parameters, or if all their parameters have default values, the DecodeParms entry may be omitted. (See implementation note 7 in Appendix H.)""",
    ),
    (
        "DL",
        "integer",
        """(Optional; PDF 1.5) A non-negative integer representing the number of bytes in the decoded (defiltered) stream. It can be used to determine, for example, whether enough disk space is available to write a stream to a file.\nThis value should be considered a hint only; for some stream filters, it may not be possible to determine this value precisely.""",
    ),
    (
        "F",
        "file specification",
        """(Optional; PDF 1.2) The file containing the stream data. If this entry is present, the bytes between stream and endstream are ignored, the filters are specified by FFilter rather than Filter, and the filter parameters are specified by FDecodeParms rather than DecodeParms. However, the Length entry should still specify the number of those bytes. (Usually, there are no bytes and Length is 0.) (See implementation note 46 in Appendix H.)""",
    ),
)

# Only a minimal HTML source is required to provide the Story's working
HTML = """
<html>
<body><h2>TABLE 3.4 Entries common to all stream dictionaries</h2>
<table>
    <tr>
        <th>KEY</th><th>TYPE</th><th>VALUE</th>
    </tr>
    <tr id="row">
        <td id="col0"></td><td id="col1"></td><td id="col2"></td>
    </tr>
"""

"""
---------------------------------------------------------------------
Just for demo purposes, set:
- header cell background to gray
- text color in col1 to blue
- a border line at the top of all table cells
- all text to the sans-serif font
---------------------------------------------------------------------
"""
CSS = """th {
    background-color: #aaa;
}

td[id="col1"] {
    color: blue;
}

td, tr {
    border: 1px solid black;
    border-right-width: 0px;
    border-left-width: 0px;
    border-bottom-width: 0px;
}
body {
    font-family: sans-serif;
}
"""

story = fitz.Story(HTML, user_css=CSS)  # define the Story
body = story.body  # access the HTML <body> of it
template = body.find(None, "id", "row")  # find the template with name "row"
parent = template.parent  # access its parent i.e., the <table>

for col0, col1, col2 in table_text:
    row = template.clone()  # make a clone of the row template
    # add text to each cell in the duplicated row
    row.find(None, "id", "col0").add_text(col0)
    row.find(None, "id", "col1").add_text(col1)
    row.find(None, "id", "col2").add_text(col2)
    parent.append_child(row)  # add new row to <table>
template.remove()  # remove the template

# Story is ready - output it via a writer
writer = fitz.DocumentWriter(__file__.replace(".py", ".pdf"), "compress")
mediabox = fitz.paper_rect("letter")  # size of one output page
where = mediabox + (36, 36, -36, -36)  # use this sub-area for the content

more = True  # detects end of output
while more:
    dev = writer.begin_page(mediabox)  # start a page, returning a device
    more, filled = story.place(where)  # compute content fitting into "where"
    story.draw(dev)  # output it to the page
    writer.end_page()  # finalize the page
writer.close()  # close the output
