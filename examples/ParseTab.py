#!/usr/bin/python
# -*- coding: utf-8 -*-
#==============================================================================
# Function ParseTab - parse a document table into a Python list of lists
#==============================================================================
def ParseTab(doc, page, bbox, columns = None):
    ''' Returns the parsed table of a page in a PDF / (open) XPS / EPUB document.
    Parameters:
    doc: a fitz.Document
    page: integer page number (0-based)
    bbox: containing rectangle, list of numbers [xmin, ymin, xmax, ymax]
    columns: optional list of column coordinates. If None, columns are generated
    Returns the parsed table as a list of lists of strings.
    The number of columns and rows are determined automatically
    from parsing the specified rectangle.
    '''
    import json
    import sqlite3
    xmin, ymin, xmax, ymax = bbox                # rectangle coordinates
    if not (xmin < xmax and ymin < ymax):
        print("Warning: incorrect rectangle coordinates!")
        return []

    if type(page) == type(1):
        txt = doc.getPageText(page, output="json") # page text in JSON format
    else:
        txt = page.getText(output = "json")

    blocks = json.loads(txt)["blocks"]             # get list of blocks
    if not blocks:
        print("Warning: page contains no text")
        return []
    db = sqlite3.connect(":memory:")        # create RAM database
    cur = db.cursor()
    # create a table for the spans (text pieces)
    cur.execute("CREATE TABLE `spans` (`x0` REAL,`y0` REAL, `text` TEXT)")

#==============================================================================
#   Function spanout - store a table entry in database
#==============================================================================
    def spanout(s, y0):
        x0  = s["bbox"][0]
        txt = s["text"]          # the text piece
        cur.execute("insert into spans values (?,?,?)", (int(x0), int(y0), txt))
        return
#==============================================================================
    # populate database with all spans in the requested bbox
    for block in blocks:
        for line in block["lines"]:
            y0 = line["bbox"][1]            # top-left y-coord
            y1 = line["bbox"][3]            # bottom-right y-coord
            if y0 < ymin or y1 > ymax:      # line outside bbox limits - skip it
                continue
            spans = []                      # sort spans by their left coord's
            for s in line["spans"]:
                if s["bbox"][0] >= xmin and s["bbox"][2] <= xmax:
                    spans.append([s["bbox"][0], s])
            if spans:                       # any spans left at all?
                spans.sort()                # sort them
            else:
                continue
            # concatenate spans that are close to each other
            for i, s in enumerate(spans):
                span = s[1]
                if i == 0:
                    s0 = span                    # memorize 1st span
                    continue
                x0  = span["bbox"][0]            # left borger of span
                x1  = span["bbox"][2]            # right border of span
                txt = span["text"]               # text of this span
                if abs(x0 - s0["bbox"][2]) > 3:  # if more than 3 pixels away
                    spanout(s0, y0)              # from previous span, output it
                    s0 = span                    # store this one as new 1st
                    continue
                s0["text"] += txt                # join current span with prev
                s0["bbox"][2] = x1               # save new right border
            spanout(s0, y0)                      # output the orphan

    # create a list of all the begin coordinates (used for column indices).

    if columns:                        # list of columns provided by caller
        coltab = columns
        coltab.sort()                  # sort it to be sure
        if coltab[0] > xmin:
            coltab = [xmin] + coltab   # left rect border is a valid delimiter
    else:
        cur.execute("select distinct x0 from spans order by x0")
        coltab = [t[0] for t in cur.fetchall()]

    # now read all text pieces from top to bottom.
    cur.execute("select x0, y0, text from spans order by y0")
    alltxt = cur.fetchall()
    db.close()                              # do not need database anymore

    # create the matrix
    spantab = []

    try:
        y0 = alltxt[0][1]                   # y-coord of first line
    except IndexError:                      # nothing there:
        print("Warning: no text found within rectangle!")
        return []

    zeile = [""] * len(coltab)

    for c in alltxt:
        c_idx = len(coltab) - 1
        while c[0] < coltab[c_idx]:         # col number of the text piece
            c_idx = c_idx - 1
        if y0 < c[1]:                       # new line?
            # output old line
            spantab.append(zeile)
            # create new line skeleton
            y0 = c[1]
            zeile = [""] * len(coltab)
        if not zeile[c_idx] or zeile[c_idx].endswith(" ") or\
                               c[2].startswith(" "):
            zeile[c_idx] += c[2]
        else:
            zeile[c_idx] += " " + c[2]

    # output last line
    spantab.append(zeile)
    return spantab
