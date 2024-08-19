import math
import pymupdf

#------------------------------------------------------------------------------
# preliminary stuff: create function value lists for sine and cosine
#------------------------------------------------------------------------------
w360 = math.pi * 2  # go through full circle
deg = w360 / 360  # 1 degree as radians
rect = pymupdf.Rect(100,200, 300, 300)  # use this rectangle
first_x = rect.x0  # x starts from left
first_y = rect.y0 + rect.height / 2.  # rect middle means y = 0
x_step = rect.width / 360  # rect width means 360 degrees
y_scale = rect.height / 2.  # rect height means 2
sin_points = []  # sine values go here
cos_points = []  # cosine values go here
for x in range(362):  # now fill in the values
    x_coord = x * x_step + first_x  # current x coordinate
    y = -math.sin(x * deg)  # sine
    p = (x_coord, y * y_scale + first_y)  # corresponding point
    sin_points.append(p)  # append
    y = -math.cos(x * deg)  # cosine
    p = (x_coord, y * y_scale + first_y)  # corresponding point
    cos_points.append(p)  # append

#------------------------------------------------------------------------------
# create the document with one page
#------------------------------------------------------------------------------
doc = pymupdf.open()  # make new PDF
page = doc.new_page()  # give it a page

#------------------------------------------------------------------------------
# add the Ink annotation, consisting of 2 curve segments
#------------------------------------------------------------------------------
annot = page.add_ink_annot((sin_points, cos_points))
# let it look a little nicer
annot.set_border(width=0.3, dashes=[1,])  # line thickness, some dashing
annot.set_colors(stroke=(0,0,1))  # make the lines blue
annot.update()  # update the appearance

page.draw_rect(rect, width=0.3)  # only to demonstrate we did OK

doc.save("a-inktest.pdf")
