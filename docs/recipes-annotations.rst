.. include:: header.rst

.. _RecipesAnnotations:

==============================
Annotations
==============================

.. _RecipesAnnotations_A:

How to Add and Modify Annotations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In |PyMuPDF|, new annotations can be added via :ref:`Page` methods. Once an annotation exists, it can be modified to a large extent using methods of the :ref:`Annot` class.

Annotations can **only** be inserted in |PDF| pages - other document types do not support annotation insertion.

In contrast to many other tools, initial insert of annotations happens with a minimum number of properties. We leave it to the programmer to e.g. set attributes like author, creation date or subject.

As an overview for these capabilities, look at the following script that fills a PDF page with most of the available annotations. Look in the next sections for more special situations:

.. literalinclude:: samples/new-annots.py
   :language: python


This script should lead to the following output:

.. image:: images/img-annots.*
   :scale: 80

------------------------------

.. _RecipesAnnotations_B:

How to Use FreeText
~~~~~~~~~~~~~~~~~~~~~
This script shows a couple of ways to deal with 'FreeText' annotations::

    # -*- coding: utf-8 -*-
    import fitz

    # some colors
    blue  = (0,0,1)
    green = (0,1,0)
    red   = (1,0,0)
    gold  = (1,1,0)

    # a new PDF with 1 page
    doc = fitz.open()
    page = doc.new_page()

    # 3 rectangles, same size, above each other
    r1 = fitz.Rect(100,100,200,150)
    r2 = r1 + (0,75,0,75)
    r3 = r2 + (0,75,0,75)

    # the text, Latin alphabet
    t = "¡Un pequeño texto para practicar!"

    # add 3 annots, modify the last one somewhat
    a1 = page.add_freetext_annot(r1, t, color=red)
    a2 = page.add_freetext_annot(r2, t, fontname="Ti", color=blue)
    a3 = page.add_freetext_annot(r3, t, fontname="Co", color=blue, rotate=90)
    a3.set_border(width=0)
    a3.update(fontsize=8, fill_color=gold)

    # save the PDF
    doc.save("a-freetext.pdf")

The result looks like this:

.. image:: images/img-freetext.*
   :scale: 80

------------------------------




Using Buttons and JavaScript
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Since MuPDF v1.16, 'FreeText' annotations no longer support bold or italic versions of the Times-Roman, Helvetica or Courier fonts.

A big **thank you** to our user `@kurokawaikki <https://github.com/kurokawaikki>`_, who contributed the following script to **circumvent this restriction**.

.. literalinclude:: samples/make-bold.py
   :language: python

--------------------------


.. _RecipesAnnotations_C:

How to Use Ink Annotations
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ink annotations are used to contain freehand scribbling. A typical example may be an image of your signature consisting of first name and last name. Technically an ink annotation is implemented as a **list of lists of points**. Each point list is regarded as a continuous line connecting the points. Different point lists represent independent line segments of the annotation.

The following script creates an ink annotation with two mathematical curves (sine and cosine function graphs) as line segments::

    import math
    import fitz

    #------------------------------------------------------------------------------
    # preliminary stuff: create function value lists for sine and cosine
    #------------------------------------------------------------------------------
    w360 = math.pi * 2  # go through full circle
    deg = w360 / 360  # 1 degree as radians
    rect = fitz.Rect(100,200, 300, 300)  # use this rectangle
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
    doc = fitz.open()  # make new PDF
    page = doc.new_page()  # give it a page

    #------------------------------------------------------------------------------
    # add the Ink annotation, consisting of 2 curve segments
    #------------------------------------------------------------------------------
    annot = page.addInkAnnot((sin_points, cos_points))
    # let it look a little nicer
    annot.set_border(width=0.3, dashes=[1,])  # line thickness, some dashing
    annot.set_colors(stroke=(0,0,1))  # make the lines blue
    annot.update()  # update the appearance

    page.draw_rect(rect, width=0.3)  # only to demonstrate we did OK

    doc.save("a-inktest.pdf")

This is the result:

.. image:: images/img-inkannot.*
    :scale: 50

.. include:: footer.rst
