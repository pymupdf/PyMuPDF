import pymupdf

MEDIABOX = pymupdf.paper_rect("letter")  # output page format: Letter
GRIDSPACE = pymupdf.Rect(100, 100, 400, 400)
GRID = pymupdf.make_table(GRIDSPACE, rows=2, cols=2)
CELLS = [GRID[i][j] for i in range(2) for j in range(2)]
text_table = ("A", "B", "C", "D")
writer = pymupdf.DocumentWriter(__file__.replace(".py", ".pdf"))  # create the writer

device = writer.begin_page(MEDIABOX)  # make new page
for i, text in enumerate(text_table):
    story = pymupdf.Story(em=1)
    body = story.body
    with body.add_paragraph() as para:
        para.set_bgcolor("#ecc")
        para.set_pagebreak_after()  # fills whole cell with bgcolor
        para.set_align("center")
        para.set_fontsize(16)
        para.add_text(f"\n\n\n{text}")
    story.place(CELLS[i])
    story.draw(device)
    del story

writer.end_page()  # finish page

writer.close()  # close output file
