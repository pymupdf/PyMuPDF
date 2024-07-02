.. include:: header.rst

.. _RecipesOptionalContent:

==============================
Optional Content Support
==============================

This document explains PyMuPDF's support of the PDF concept **"Optional Content"**.

Introduction: The Optional Content Concept
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*Optional Content* in PDF is a way to show or hide parts of a document based on certain conditions: Parameters that can be set to ON or to OFF when using a supporting PDF consumer (viewer), or programmatically.

This capability is useful in items such as CAD drawings, layered artwork, maps, and multi-language documents. Typical uses include showing or hiding details of complex vector graphics like geographical maps, technical devices, architectural designs and similar, including automatically switching between different zooming levels. Other use cases may be to automatically show different detail levels when displaying a document on screen as opposed to printing it.

Special PDF objects, so-called **Optional Content Groups** (OCGs) are used to define these different *layers* of content.

Assigning an OCG to a "normal" PDF object (like a text or an image) causes that object to be visible or hidden, depending on the current state of the assigned OCG.

To ease definition of the overall configuration of a PDF's Optional Content, OCGs can be organized in higher level groupings, called **OC Configurations**. Each configuration being a collection of OCGs, together with each OCG's desired initial visibility state. Selecting one of these configurations (via the PDF viewer or programmatically) causes a corresponding visibility change of all affected PDF objects throughout the document.

Except for the default one, OC Configurations are optional.

For more explanations and additional background please refer to PDF specification manuals.

PyMuPDF Support for PDF Optional Content
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PyMuPDF offers full support for viewing, defining, changing and deleting Option Content Groups, Configurations, maintaining the assignment of OCGs to PDF objects and programmatically switching between OC Configurations and the visibility states of each single OCG.

How to Add Optional Content
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This is as simple as adding an Optional Content Group, OCG, to a PDF: :meth:`Document.add_ocg`.

If previously the PDF had no OC support at all, the required setup (like defining the default OC Configuration) will be done at this point automatically.

The method returns an :data:`xref` of the created OCG. Use this xref to associate (mark) any PDF object with it, that you want to make dependent on this OCG's state. For example, you can insert an image on a page and refer to the xref like this::

    img_xref = page.insert_image(rect, filename="image.file", oc=xref)

If you want to put an **existing** image under the control of an OCG, you must first find out the image's xref number (called `img_xref` here) and then do `doc.set_oc(img_xref, xref)`. After this, the image will be (in-) visible everywhere throughout the document if the OCG's state is "ON", respectively "OFF". You can also assign a different OCG with this method.

To **remove** an OCG from an image, do `doc.set_oc(img_xref, 0)`.

One single OCG can be assigned to multiple PDF objects to control their visibility.

How to Define Complex Optional Content Conditions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sophisticated logical conditions can be established to address complex visibility needs.

For example, you might want to create a multi-language document, so the user may switch between languages as required.

Please have a look at `this Jupyter Notebook`_ and execute it as desired.

Certainly, your requirements may even be more complex and involve multiple OCGs with ON/OFF states that are connected by some kind of logical relationship -- but it should give you an impression of what is possible and how to plan your next steps.

.. include:: footer.rst

.. External Links:

.. _this Jupyter Notebook: https://github.com/pymupdf/PyMuPDF-Utilities/blob/master/jupyter-notebooks/optional-content.ipynb



