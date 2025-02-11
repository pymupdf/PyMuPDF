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
This script shows a couple of basic ways to deal with 'FreeText' annotations:

.. literalinclude:: samples/annotations-freetext1.py

The result looks like this:

.. image:: images/img-freetext1.*
   :scale: 80

Here is an example for using rich text and call-out lines:

.. literalinclude:: samples/annotations-freetext2.py

The result looks like this:

.. image:: images/img-freetext2.*
   :scale: 80


------------------------------



.. _RecipesAnnotations_C:

How to Use Ink Annotations
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ink annotations are used to contain freehand scribbling. A typical example may be an image of your signature consisting of first name and last name. Technically an ink annotation is implemented as a **list of lists of points**. Each point list is regarded as a continuous line connecting the points. Different point lists represent independent line segments of the annotation.

The following script creates an ink annotation with two mathematical curves (sine and cosine function graphs) as line segments:

.. literalinclude:: samples/annotations-ink.py

This is the result:

.. image:: images/img-inkannot.*
    :scale: 50

.. include:: footer.rst
