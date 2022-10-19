"""
This is a demo script for using PyMuPDF with its "Story" feature.

The following aspects are being covered here:

* The script produces a report of films that are stored in an SQL database
* The report format is provided as a HTML template

The SQL database contains two tables:
1. Table "films" which has the columns "title" (film title, str), "director"
   (str) and "year" (year of release, int).
2. Table "actors" which has the columns "name" (actor name, str) and "title"
   (the film title where the actor had been casted, str).

The script reads all content of the "films" table. For each film title it
reads all rows from table "actors" which took part in that film.

Comment 1
---------
To keep things easy and free from pesky technical detail, the relevant file
names inherit the name of this script:
- the database's filename is the script name with ".py" extension replaced
  by ".db".
- the output PDF similarly has script file name with extension ".pdf".

Comment 2
---------
The SQLITE database has been created using https://sqlitebrowser.org/, a free
multi-platform tool to maintain or manipulate SQLITE databases.
"""
import os
import sqlite3

import fitz

# ----------------------------------------------------------------------
# HTML template for the film report
# There are four placeholders coded as "id" attributes.
# One "id" allows locating the template part itself, the other three
# indicate where database text should be inserted.
# ----------------------------------------------------------------------
festival_template = (
    "<html><head><title>Just some arbitrary text</title></head>"
    '<body><h1 style="text-align:center">Hook Norton Film Festival</h1>'
    "<ol>"
    '<li id="filmtemplate">'
    '<b id="filmtitle"></b>'
    "<dl>"
    '<dt>Director<dd id="director">'
    '<dt>Release Year<dd id="filmyear">'
    '<dt>Cast<dd id="cast">'
    "</dl>"
    "</li>"
    "</ol>"
    "</body></html"
)

# -------------------------------------------------------------------
# define database access
# -------------------------------------------------------------------
dbfilename = __file__.replace(".py", ".db")  # the SQLITE database file name
assert os.path.isfile(dbfilename), f'{dbfilename}'
database = sqlite3.connect(dbfilename)  # open database
cursor_films = database.cursor()  # cursor for selecting the films
cursor_casts = database.cursor()  # cursor for selecting actors per film

# select statement for the films - let SQL also sort it for us
select_films = """SELECT title, director, year FROM films ORDER BY title"""

# select stament for actors, a skeleton: sub-select by film title
select_casts = """SELECT name FROM actors WHERE film = "%s" ORDER BY name"""

# -------------------------------------------------------------------
# define the HTML Story and fill it with database data
# -------------------------------------------------------------------
story = fitz.Story(festival_template)
body = story.body  # access the HTML body detail
template = body.find(None, "id", "filmtemplate")  # find the template part

# read the films from the database and put them all in one Python list
# NOTE: instead we might fetch rows one by one (advisable for large volumes)
cursor_films.execute(select_films)  # execute cursor, and ...
films = cursor_films.fetchall()  # read out what was found

for title, director, year in films:  # iterate through the films
    film = template.clone()  # clone template to report each film
    film.find(None, "id", "filmtitle").add_text(title)  # put title in templ
    film.find(None, "id", "director").add_text(director)  # put director
    film.find(None, "id", "filmyear").add_text(str(year))  # put year

    # the actors reside in their own table - find the ones for this film title
    cursor_casts.execute(select_casts % title)  # execute cursor
    casts = cursor_casts.fetchall()  # read actors for the film
    # each actor name appears in its own tuple, so extract it from there
    film.find(None, "id", "cast").add_text("\n".join([c[0] for c in casts]))
    body.append_child(film)

template.remove()  # remove the template

# -------------------------------------------------------------------
# generate the PDF
# -------------------------------------------------------------------
writer = fitz.DocumentWriter(__file__.replace(".py", ".pdf"), "compress")
mediabox = fitz.paper_rect("a4")  # use pages in ISO-A4 format
where = mediabox + (72, 36, -36, -72)  # leave page borders

more = 1  # end of output indicator

while more:
    dev = writer.begin_page(mediabox)  # make a new page
    more, filled = story.place(where)  # arrange content for this page
    story.draw(dev, None)  # write content to page
    writer.end_page()  # finish the page

writer.close()  # close the PDF
