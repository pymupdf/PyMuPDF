"""
Demo / Experimental: Replace the fonts in a PDF.

"""
import fitz
import sys

fname = sys.argv[1]

doc = fitz.open(fname)  # input PDF
out = fitz.open()  # output PDF
csv = open("fonts.csv").read().splitlines()
all_fonts = []  # will contain: (old basefont name, Base14 name)
for f in csv:
    all_fonts.append(f.split(";"))


def pdf_color(srgb):
    """Create a PDF color triple from a given sRGB color integer.
    """
    b = (srgb % 256) / 255
    srgb /= 256
    g = (srgb % 256) / 255
    srgb /= 256
    r = srgb / 255
    return (r, g, b)


def get_font(fontname):
    """Lookup base fontname and return one of the "reserved" Base14 fontnames.
    """
    for f in all_fonts:
        if f[0] in fontname:  # fontname may look like "ABCDEF+fontname..."
            return f[1]
    return "helv"  # default: Helvetica


for page in doc:
    if page.number % 10 == 0:  # just entertainment messages every 10 pages
        print("Processed %i pages" % page.number)
    if not page._isWrapped:  # check if input page geometry is dubious
        page._wrapContents()
    # for each input page create an output with same dimensions
    outpage = out.newPage(width=page.rect.width, height=page.rect.height)

    # create a shape to write the output text to.
    shape = outpage.newShape()
    text_blocks = []
    image_blocks = []
    for block in page.getText("dict")["blocks"]:
        if block["type"] == 0:
            text_blocks.append(block)
        else:
            image_blocks.append(block)

    # insert the images first, so any text appears in foreground
    for block in image_blocks:
        outpage.insertImage(block["bbox"], stream=block["image"])
        print("Inserted an image on page", page.number)

    for block in text_blocks:  # read text blocks
        shape.drawRect(block["bbox"])  # draw all text on white background,
        # because images may cover same area

        for line in block["lines"]:  # for each line in the block ...
            for span in line["spans"]:  # for each span in the line ...
                fontname = get_font(span["font"])  # get replacing fontname
                fontsize = span["size"]
                text = span["text"]
                bbox = fitz.Rect(span["bbox"])  # text rectangle on input
                text_size = fitz.getTextlength(  # measure text length on output
                    text, fontname=fontname, fontsize=fontsize
                )

                # adjust fontsize if text is too long with new the font
                if text_size > bbox.width:
                    fontsize *= bbox.width / text_size
                try:
                    shape.insertText(  # copy text to output page
                        bbox.bl,  # insertion point on output page
                        text,  # the text to insert
                        fontsize=fontsize,  # fontsize
                        # decide on output font here: the place for sophistication!
                        fontname=fontname,
                        color=pdf_color(span["color"]),
                    )
                except ValueError:
                    print("Method 'insertText' failed:")
                    print(
                        "page:",
                        page.number,
                        "at",
                        span["bbox"][:2],
                        "text:",
                        span["text"],
                    )
        shape.finish(color=None, fill=(1, 1, 1))  # white for the text background
    shape.commit()  # write everything to the output page

"""
Several other features can be added, like:
- copy over the input metadata dictionary
- copy over the input table of contents
"""
out.save("new-" + fname, deflate=True, garbage=4)
